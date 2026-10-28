"""Audit phase 0: unpack every named bot version (V1..V10) next to the current code.

    python backtest/src/audit_versions.py list
    python backtest/src/audit_versions.py extract V3 [--git-dir PATH]
    python backtest/src/audit_versions.py inventory V3
    python backtest/src/audit_versions.py prepare V3      (hook for run B: completed candles only)

Each version lands in backtest/output/audit/<V>/code, never over the current code. Price files that are
byte-identical to the current data/ohlcv are symlinked; files that differ or no longer exist are written
from git. inventory.json records which backtest engine, params and MT5 candle call the version has, and
how its candle filter treats the bar that is still forming (the look-ahead found on 2026-10-27).

The checkout of this repo is shallow. Old versions need the full history, e.g. a partial clone:
    git clone --bare --filter=blob:none https://github.com/NinaFal/20k5ers <dir>   (then --git-dir <dir>)
See docs/AUDIT_PLAN.md.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tarfile
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "backtest" / "output" / "audit"

VERSIONS = {
    "V1": ("912d1a2", "2026-01-09", "Initial commit; ftmo_challenge_analyzer + strategy_core.simulate_trades (D1)"),
    "V2": ("97de18e", "2026-01-20", "PR #7 daily-close scan, live/backtest/simulator alignment"),
    "V3": ("9e6fc4a", "2026-02-03", "5-TP exit + Trial 10 params; first main_live_bot_backtest + csv_mt5_simulator"),
    "V4": ("147bd0d", "2026-02-11", "Risk 0.7% after 3 JPY stops in one day (live in February)"),
    "V5": ("16023cb", "2026-03-22", "PR #26, March optimisations, risk 1.1%"),
    "V6": ("dcd50b6", "2026-05-19", "PR #31-#34, 50k account"),
    "V7": ("d5a9789", "2026-07-03", "PR #36"),
    "V8": ("befa205", "2026-10-23", "Climb cap live, report with the $4M backtest"),
    "V9": ("be58da1", "2026-10-27", "Live/backtest parity fixes (candle leak still present)"),
    "V10": ("HEAD", "current", "Leak closed (HTF_NO_LOOKAHEAD=1), live timing in the backtest"),
}


def _git(git_dir, *args, binary=False):
    out = subprocess.run(["git", "--git-dir", str(git_dir), *args], capture_output=True, check=True)
    return out.stdout if binary else out.stdout.decode()


def _blob_hash(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def extract(name, git_dir):
    commit = VERSIONS[name][0]
    dest = OUT / name / "code"
    if dest.exists():
        print(f"{name}: {dest} exists, leaving it as is")
        return dest
    dest.mkdir(parents=True)
    tar = _git(git_dir, "archive", commit, binary=True)
    with tarfile.open(fileobj=io.BytesIO(tar)) as tf:
        members = [m for m in tf.getmembers() if not m.name.startswith("data/ohlcv/")]
        tf.extractall(dest, members=members)
    data_dir = dest / "data" / "ohlcv"
    data_dir.mkdir(parents=True, exist_ok=True)
    linked = written = 0
    for line in _git(git_dir, "ls-tree", "-r", commit, "data/ohlcv").splitlines():
        meta, path = line.split("\t", 1)
        blob = meta.split()[2]
        cur = ROOT / path
        target = data_dir / Path(path).name
        if cur.is_file() and _blob_hash(cur) == blob:
            target.symlink_to(cur)
            linked += 1
        else:
            target.write_bytes(_git(git_dir, "cat-file", "-p", blob, binary=True))
            written += 1
    print(f"{name}: code in {dest}; price files identical to now: {linked}, written from git: {written}")
    return dest


def inventory(name):
    code = OUT / name / "code"
    if not code.exists():
        sys.exit(f"{name}: run 'extract {name}' first")
    sim = code / "backtest" / "src" / "csv_mt5_simulator.py"
    info = {
        "version": name,
        "commit": VERSIONS[name][0],
        "date": VERSIONS[name][1],
        "what": VERSIONS[name][2],
        "engine": "main_live_bot_backtest + csv_mt5_simulator" if sim.exists()
                  else "ftmo_challenge_analyzer + strategy_core.simulate_trades",
        "params_file": "params/current_params.json" if (code / "params" / "current_params.json").exists() else None,
    }
    if sim.exists():
        s = sim.read_text(errors="replace")
        info["sim_candle_filter"] = sorted(set(re.findall(r"df\[['\"]time['\"]\]\s*<=?\s*end_ts", s)))
        info["sim_drops_forming_bar"] = "_drop_forming_bar" in s
    live_calls = []
    for p in code.rglob("*.py"):
        if "_deprecated" in p.parts:
            continue
        for m in re.finditer(r"copy_rates_from_pos\([^)]*\)", p.read_text(errors="replace")):
            live_calls.append(f"{p.relative_to(code)}: {m.group(0)}")
    info["live_mt5_candle_calls"] = live_calls
    (OUT / name / "inventory.json").write_text(json.dumps(info, indent=2))
    print(json.dumps(info, indent=2))


PATCH_LINE = "        df = df[df['time'] < end_ts]\n"
PATCH_HOOK = ("        if __import__('os').getenv('AUDIT_CANDLES') == 'exact':  # audit run B: the shared MT5 referee\n"
              "            import sys as _s; _s.path.append(%r)\n"
              "            from candle_avail import filter_completed as _fc\n"
              "            df = _fc(self, df, symbol, tf, end_ts)\n")


def prepare(name):
    """Add the run-B hook to an unpacked version's simulator. With AUDIT_CANDLES unset the old code runs
    exactly as it was (run A); with AUDIT_CANDLES=exact it sees completed candles only, judged by the same
    candle_avail.py as the current engine (run B). Nothing else in the old code changes."""
    sim = OUT / name / "code" / "backtest" / "src" / "csv_mt5_simulator.py"
    if not sim.exists():
        sys.exit(f"{name}: no csv_mt5_simulator.py (engine without the MT5 simulator, see inventory)")
    s = sim.read_text()
    if "AUDIT_CANDLES" in s:
        print(f"{name}: hook already present")
        return
    if s.count(PATCH_LINE) != 2:
        sys.exit(f"{name}: candle filter not found as expected; patch by hand")
    s = s.replace(PATCH_LINE, PATCH_LINE + PATCH_HOOK % str(Path(__file__).resolve().parent))
    sim.write_text(s)
    print(f"{name}: run-B hook added to {sim.relative_to(ROOT)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "extract", "inventory", "prepare"])
    ap.add_argument("version", nargs="?")
    ap.add_argument("--git-dir", default=str(ROOT / ".git"))
    a = ap.parse_args()
    if a.cmd == "list":
        for k, (c, d, w) in VERSIONS.items():
            print(f"{k:4} {d:10} {c:8} {w}")
        return
    names = list(VERSIONS) if a.version == "all" else [a.version]
    for n in names:
        if n not in VERSIONS:
            sys.exit(f"unknown version {n}")
        if a.cmd == "extract":
            if VERSIONS[n][0] == "HEAD":
                print(f"{n}: the current code is the working tree itself")
                continue
            extract(n, a.git_dir)
        elif a.cmd == "prepare":
            prepare(n)
        else:
            inventory(n)


if __name__ == "__main__":
    main()
