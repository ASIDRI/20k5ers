"""Test 2: zone with confluence on the daily chart, entry only after a 4h REACTION in the zone (video 7).

    python research/strategy/test2.py SYM [SYM ...] --start 2015-03-01

Daily (point in time, swings used once confirmed): break of structure -> impulse top confirmed -> zone =
golden pocket 0.618-0.796 of the swing (fib 1 = swing extreme wick, 0 = impulse top wick).
Confluence tags: a monthly/weekly S/R level in the zone; the daily order block (body of the last opposite
candle before the first fair value gap of the impulse) or that FVG overlapping the zone.
4h (only bars that open after the daily candle that completed the setup): wait for price to trade into
the zone; entry at the close of the first 4h REJECTION candle inside it (long: low in the zone, close in
the upper half of its range and above its open; mirror for short). SL just beyond the lowest low (highest
high) since price entered the zone. Setup void when a 4h candle closes beyond fib 1, when -0.25 trades
before entry, or after 20 days. Management: half at -0.25, SL to entry, rest at -0.65 or the next S/R level.
Costs per symbol (spread + slippage, as in the live simulator) are taken off every trade in R.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "backtest" / "src"))
from setup_study import load, Levels  # noqa: E402
from candle_avail import complete_times  # noqa: E402

N_SWING, FORCE, FORCE_N = 2, 1.5, 10
SL_BUF_ATR4 = 0.2       # SL buffer in 4h ATR
EXPIRY_DAYS = 20
STRUCT_TF, ENTRY_TF = "D1", "H4"  # test 4: W1 / D1 (--struct-tf, --entry-tf)
COST = json.loads((HERE.parent / "costs.json").read_text())  # adverse pips per symbol (spread + slippage)


def cost_price(sym):
    u = sym.replace("_", "").upper()
    pips = next((v for k, v in sorted(COST.items(), key=lambda kv: -len(kv[0])) if k in u), 1.5)
    pip = (0.01 if ("JPY" in u or u.startswith(("XTI", "XAG"))) else 0.1 if u.startswith("XAU")
           else 1.0 if u.startswith(("UK100", "NAS100", "SPX500", "US500")) else 0.0001)
    return 2 * pips * pip  # entry and exit


def daily_zones(sym, start, end):
    d = load(sym, STRUCT_TF)
    d["done"] = complete_times(d["time"], STRUCT_TF)
    lv = Levels(sym)
    o, h, l, c = (d[k].values for k in ("open", "high", "low", "close"))
    body = np.abs(c - o)
    tr = np.r_[h[0] - l[0], np.maximum(h[1:], c[:-1]) - np.minimum(l[1:], c[:-1])]
    atr = pd.Series(tr).rolling(14).mean().values
    highs, lows, waiting, zones = [], [], [], []
    t0, t1 = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    for i in range(60, len(d)):
        t = d["time"][i]
        if t >= t1:
            break
        k = i - N_SWING
        if h[k] == h[k - N_SWING:k + N_SWING + 1].max():
            highs.append(k)
        if l[k] == l[k - N_SWING:k + N_SWING + 1].min():
            lows.append(k)
        for w in list(waiting):
            dirn = w["dir"]
            if (c[i] < w["ext"]) if dirn == 1 else (c[i] > w["ext"]):
                waiting.remove(w); continue
            sw = [x for x in (highs if dirn == 1 else lows) if x >= w["bos_i"]]
            if not sw:
                continue
            waiting.remove(w)
            top_i = sw[0]
            top = h[top_i] if dirn == 1 else l[top_i]
            ext = w["ext"]
            rng = abs(top - ext)
            if rng <= 0 or t < t0:
                continue
            z1, z2 = top - dirn * 0.618 * rng, top - dirn * 0.796 * rng
            zlo, zhi = min(z1, z2), max(z1, z2)
            levs = lv.at(d["done"][i])
            lvl_in = any(zlo - 0.1 * atr[i] <= p <= zhi + 0.1 * atr[i] for p, _ in levs)
            # first FVG of the impulse (ext_i .. top_i) and its order block
            fvg = ob = None
            for j in range(w["ext_i"] + 2, top_i + 1):
                gap = (l[j] > h[j - 2]) if dirn == 1 else (h[j] < l[j - 2])
                if gap:
                    fvg = (h[j - 2], l[j]) if dirn == 1 else (h[j], l[j - 2])
                    for m in range(j - 2, w["ext_i"] - 1, -1):
                        if (c[m] < o[m]) if dirn == 1 else (c[m] > o[m]):
                            ob = (min(o[m], c[m]), max(o[m], c[m]))
                            break
                    break
            ov = lambda a: a is not None and a[0] <= zhi and a[1] >= zlo  # noqa: E731
            nxt = [p for p, _ in levs if (p - (top + dirn * 0.25 * rng)) * dirn > 0 and (p - (top + dirn * 0.65 * rng)) * dirn < 0]
            tp2 = (min(nxt) if dirn == 1 else max(nxt)) if nxt else top + dirn * 0.65 * rng
            zones.append(dict(sym=sym, dir=dirn, kind=w["kind"], date=str(t.date()), ready=d["done"][i],
                              key=w["key"], key_t=d["time"][w["key_i"]], bos_t=d["time"][w["bos_i"]],
                              ext_t=d["time"][w["ext_i"]], top_t=d["time"][top_i],
                              z1=z1, z2=z2, ext=ext, top=top, tp1=top + dirn * 0.25 * rng, tp2=tp2,
                              lvl=lvl_in, ob=ov(ob), fvg=ov(fvg), wk=lv.trend(d["done"][i], "W1") * dirn,
                              mn=lv.trend(d["done"][i], "MN") * dirn, atr=atr[i]))
        if len(highs) < 2 or len(lows) < 2 or np.isnan(atr[i]):
            continue
        forceful = body[i] >= FORCE * body[i - FORCE_N:i].mean()
        for dirn in (1, -1):
            if dirn == 1:
                key_i = [x for x in highs if x < i][-1]
                broke = c[i] > h[key_i] and c[i - 1] <= h[key_i] and c[i] > o[i] and forceful
                ext_i = int(l[key_i:i + 1].argmin()) + key_i
                ext = l[ext_i]
                rev = not any(z for z in [w for w in waiting if w["dir"] == 1])
            else:
                key_i = [x for x in lows if x < i][-1]
                broke = c[i] < l[key_i] and c[i - 1] >= l[key_i] and c[i] < o[i] and forceful
                ext_i = int(h[key_i:i + 1].argmax()) + key_i
                ext = h[ext_i]
            if broke:
                waiting = [x for x in waiting if x["dir"] != dirn]
                waiting.append(dict(dir=dirn, ext=ext, ext_i=ext_i, bos_i=i, kind="bos", key_i=key_i,
                                    key=h[key_i] if dirn == 1 else l[key_i]))
    return zones


def trade_zone(z, h4):
    """Walk the 4h bars after the setup was complete; returns a result dict."""
    dirn = z["dir"]
    a = int(np.searchsorted(h4["time"].values, np.datetime64(z["ready"].tz_convert(None))))
    end = z["ready"] + pd.Timedelta(days=EXPIRY_DAYS)
    o, h, l, c, t = (h4[k].values for k in ("open", "high", "low", "close", "time"))
    atr4 = h4["atr"].values
    zlo, zhi = min(z["z1"], z["z2"]), max(z["z1"], z["z2"])
    inside_ext = None
    for i in range(a, len(h4)):
        if pd.Timestamp(t[i]).tz_localize("UTC") > end:
            return dict(result="verlopen")
        if (h[i] >= z["tp1"]) if dirn == 1 else (l[i] <= z["tp1"]):
            return dict(result="weggelopen")
        if (c[i] < z["ext"]) if dirn == 1 else (c[i] > z["ext"]):
            return dict(result="ongeldig")
        touched = (l[i] <= zhi) if dirn == 1 else (h[i] >= zlo)
        if not touched and inside_ext is None:
            continue
        ext_now = l[i] if dirn == 1 else h[i]
        inside_ext = ext_now if inside_ext is None else (min(inside_ext, ext_now) if dirn == 1 else max(inside_ext, ext_now))
        rngc = h[i] - l[i]
        if rngc <= 0:
            continue
        if dirn == 1:
            react = l[i] <= zhi and c[i] > o[i] and (c[i] - l[i]) / rngc >= 0.5
        else:
            react = h[i] >= zlo and c[i] < o[i] and (h[i] - c[i]) / rngc >= 0.5
        if react:
            entry = c[i]
            sl = inside_ext - dirn * SL_BUF_ATR4 * atr4[i]
            risk = abs(entry - sl)
            if risk <= 0 or (z["tp1"] - entry) * dirn <= 0:
                return dict(result="ongeldig")
            rr1 = abs(z["tp1"] - entry) / risk
            return dict(result="gevuld", entry=entry, sl=sl, risk=risk, rr1=rr1, fill=str(pd.Timestamp(t[i]).date()),
                        R_c=ladder(dirn, entry, sl, risk, z, h, l, i + 1),
                        **manage(dirn, entry, sl, risk, z, h, l, i + 1))
    return dict(result="open")


def manage(dirn, entry, sl, risk, z, h, l, start):
    R, left, tp1_hit = 0.0, 1.0, False
    for i in range(start, len(h)):
        adv, fav = (l[i], h[i]) if dirn == 1 else (h[i], l[i])
        if (adv <= sl) if dirn == 1 else (adv >= sl):
            return dict(R=R + left * (sl - entry) / risk * dirn, tp1_hit=tp1_hit)
        if not tp1_hit and ((fav >= z["tp1"]) if dirn == 1 else (fav <= z["tp1"])):
            R += 0.5 * abs(z["tp1"] - entry) / risk; left = 0.5; tp1_hit = True; sl = entry
        if tp1_hit and ((fav >= z["tp2"]) if dirn == 1 else (fav <= z["tp2"])):
            return dict(R=R + 0.5 * abs(z["tp2"] - entry) / risk, tp1_hit=True)
    return dict(R=R, tp1_hit=tp1_hit)


LADDER = (0.25, 0.5, 0.618, 1.0)  # exit (c): equal parts at these fib extensions


def ladder(dirn, entry, sl, risk, z, h, l, start):
    """Exit (c): a quarter at each of -0.25/-0.5/-0.618/-1; after the first target SL to entry, after each further
    target SL to the previous target. A bar reaching a target and the stop counts as the stop (the safe side)."""
    rng = abs(z["top"] - z["ext"])
    tps = [z["top"] + dirn * e * rng for e in LADDER]
    part = 1.0 / len(tps)
    R, k, stop = 0.0, 0, sl
    for i in range(start, len(h)):
        adv, fav = (l[i], h[i]) if dirn == 1 else (h[i], l[i])
        if (adv <= stop) if dirn == 1 else (adv >= stop):
            return R + (1 - k * part) * (stop - entry) / risk * dirn
        while k < len(tps) and ((fav >= tps[k]) if dirn == 1 else (fav <= tps[k])):
            R += part * abs(tps[k] - entry) / risk
            stop = entry if k == 0 else tps[k - 1]
            k += 1
        if k == len(tps):
            return R
    return R


def run(sym, start, end):
    h4 = load(sym, ENTRY_TF)
    tr = np.r_[np.nan, np.maximum(h4.high.values[1:], h4.close.values[:-1]) - np.minimum(h4.low.values[1:], h4.close.values[:-1])]
    h4["atr"] = pd.Series(tr).rolling(14).mean().values
    rows = []
    cp = cost_price(sym)
    for z in daily_zones(sym, start, end):
        r = trade_zone(z, h4)
        z = dict(z, **r)
        if r["result"] == "gevuld":
            z["R_cost"] = cp / r["risk"]
            z["Rnet"] = r["R"] - z["R_cost"]  # exit (b): half at -0.25, SL to entry, rest at -0.65 / next level
            z["win"] = bool(r["tp1_hit"])  # winning setup: -0.25 reached before the SL
            z["Rnet_a"] = (r["rr1"] if r["tp1_hit"] else -1.0) - z["R_cost"]  # exit (a): all out at -0.25
            z["Rnet_c"] = r["R_c"] - z["R_cost"]  # exit (c): fib ladder -0.25/-0.5/-0.618/-1
        rows.append(z)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--start", default="2015-03-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--struct-tf", default="D1", choices=["D1", "W1"])
    ap.add_argument("--entry-tf", default="H4", choices=["H4", "D1"])
    ap.add_argument("--expiry-days", type=int, default=20)
    ap.add_argument("--prefix", default="", help="prefix for the output files (keeps other runs)")
    a = ap.parse_args()
    STRUCT_TF, ENTRY_TF, EXPIRY_DAYS = a.struct_tf, a.entry_tf, a.expiry_days
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    allz = []
    for s in a.symbols:
        try:
            df = run(s, a.start, a.end)
        except Exception as e:  # noqa
            print(f"{s}: overgeslagen ({type(e).__name__}: {e})", flush=True)
            continue
        df.to_csv(out / f"{a.prefix}test2_{s}.csv", index=False)
        print(f"{s}: {len(df)} zones, {int((df.result == 'gevuld').sum())} trades", flush=True)
        allz.append(df)
    df = pd.concat(allz)
    f = df[df.result == "gevuld"].copy()
    f["half"] = np.where(f.date.str[:4] <= "2020", "2015-20", "2021-25")
    f["samenloop"] = np.where(f.lvl | f.ob | f.fvg, "ja", "nee")
    f["htf_mee"] = np.where((f.wk == 1) & (f.mn == 1), "week+maand mee", np.where((f.wk == 1) | (f.mn == 1), "een van beide", "tegen"))
    pd.set_option("display.width", 200)
    print(f"\n##### {len(allz)} assets: {len(df)} zones, {len(f)} trades")
    print(df.result.value_counts().to_dict())
    print("\nalles (na kosten):", f.groupby("half")["Rnet"].agg(["count", "mean", "sum"]).round(3).to_dict("index"))
    print(f"mediaan risico in R-kosten: {f.R_cost.median():.3f}R; TP1 gehaald: {f.tp1_hit.mean()*100:.0f}%")
    for col in ["samenloop", "htf_mee", "lvl", "ob", "fvg", "dir"]:
        print(f"\n--- {col}")
        print(f.groupby([col, "half"])["Rnet"].agg(["count", "mean"]).unstack("half").round(3).to_string())
    print("\n--- samenloop ja + week+maand mee")
    m = (f.samenloop == "ja") & (f.htf_mee == "week+maand mee")
    print(f[m].groupby("half")["Rnet"].agg(["count", "mean", "sum"]).round(3).to_string())
    print("\nper jaar (som Rnet, trades):", f.assign(y=f.date.str[:4]).groupby("y")["Rnet"].agg(["sum", "count"]).round(1).to_dict("index"))

    print("\n##### OORDEEL (criteria test 4; winnend = -0,25 vóór SL)")
    for half, g in f.groupby("half"):
        n, win = len(g), g["win"].mean()
        be = 1 / (1 + g["rr1"].mean())
        pf = lambda x: x[x > 0].sum() / -x[x < 0].sum()  # noqa: E731
        ma, mb = g["Rnet_a"].mean(), g["Rnet"].mean()
        ok = [n >= 100 and max(ma, mb) >= 0.10, win > be, max(pf(g["Rnet_a"]), pf(g["Rnet"])) >= 1.2]
        print(f"{half}: trades {n}, winnend {win*100:.1f}% (break-even {be*100:.1f}%, gem. winst/risico op -0,25 {g['rr1'].mean():.2f}), "
              f"uitstap a {ma:+.3f}R (PF {pf(g['Rnet_a']):.2f}), uitstap b {mb:+.3f}R (PF {pf(g['Rnet']):.2f}), "
              f"[nieuw] ladder c {g['Rnet_c'].mean():+.3f}R (PF {pf(g['Rnet_c']):.2f}) -> "
              f"{'ok' if all(ok) else 'niet gehaald'} {ok}")
    for col in ["samenloop", "htf_mee"]:
        print(f"\n--- {col} (winnend % / uitstap a / uitstap b)")
        print(f.groupby([col, "half"]).agg(n=("win", "size"), winnend=("win", "mean"), a=("Rnet_a", "mean"), b=("Rnet", "mean"), c=("Rnet_c", "mean")).round(3).to_string())
