"""Strategy v2 trades on a 5ers 50k account with the scaling of the previous bot (backtest/src/csv_mt5_simulator.py).

    python research/strategy/v2_fiveers_sim.py --prefix v2n37_ [--risk 0.6] [--from 2016-01-01] [--to 2026-01-01]

Risk per trade = a fixed % of the balance at entry (previous bot: 0.6%); at most 7 open trades and 5% open risk.
5ers scaling: at +10% on the funded level the profit is paid out (split 80% below 175k, 85% from 175k, 90% from
250k, 100% from 350k) and the account moves up a level (50k, 60k, 70k, 80k, 100k, 125k, ...). Breach: balance below
90% of the funded level. A trade's result is booked at its exit day (partial exits at T1/T2 are booked there too).
"""
import argparse
import glob
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
LEVELS = [50_000, 60_000, 70_000, 80_000, 100_000, 125_000, 150_000, 175_000, 200_000, 250_000, 300_000, 350_000,
          400_000, 450_000, 500_000, 600_000, 700_000, 800_000, 1_000_000, 1_250_000, 1_500_000, 1_750_000, 2_000_000,
          2_500_000, 3_000_000, 3_500_000, 4_000_000]


def split(level):
    return 1.0 if level >= 350_000 else 0.9 if level >= 250_000 else 0.85 if level >= 175_000 else 0.8


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="v2n37_")
    ap.add_argument("--risk", type=float, default=0.6)
    ap.add_argument("--ladder", action="store_true", help="previous bot: 1.8%% below 300k (0.6%% above), risk down "
                    "to 0.4 / 0.25 / 0.15%% from 1.5 / 2.5 / 5.5%% total drawdown, 3.5%% open-risk cap")
    ap.add_argument("--from", dest="start", default="2016-01-01")
    ap.add_argument("--to", dest="end", default="2026-01-01")
    a = ap.parse_args()
    f = pd.concat([pd.read_csv(p) for p in glob.glob(str(HERE / "out" / f"{a.prefix}*.csv")) if open(p).read().strip()])
    f = f[(f.entry_day >= a.start) & (f.entry_day < a.end)].copy()
    f["exit_day"] = f.exit_day.fillna(a.end)
    ev = [(r.entry_day, 1, i) for i, r in f.iterrows()] + [(r.exit_day, 2, i) for i, r in f.iterrows()]
    f = f.reset_index(drop=True)
    ev = sorted([(r.entry_day, 1, i) for i, r in f.iterrows()] + [(r.exit_day, 2, i) for i, r in f.iterrows()])
    level, bal, paid, open_, skipped, log, peak_level = 50_000.0, 50_000.0, 0.0, {}, 0, [], 50_000.0
    for day, kind, i in ev:
        if kind == 1:
            pct = a.risk
            if a.ladder:
                pct = 1.8 if level < 300_000 else 0.6
                dd = (level - bal) / level * 100  # total drawdown vs the level's start
                pct = 0.15 if dd >= 5.5 else 0.25 if dd >= 2.5 else 0.4 if dd >= 1.5 else pct
            risk = bal * pct / 100
            cap = 0.035 if a.ladder else 0.05
            if len(open_) >= 7 or sum(open_.values()) + risk > cap * bal:
                skipped += 1
                continue
            open_[i] = risk
        elif i in open_:
            bal += open_.pop(i) * f.R[i]
            if bal < 0.9 * level:
                log.append((day, f"BREACH: saldo {bal:,.0f} onder 90% van {level:,.0f}"))
                break
            if bal >= 1.1 * level:
                pay = (bal - level) * split(level)
                paid += pay
                nxt = next((x for x in LEVELS if x > level + 1), level)
                log.append((day, f"+10% op {level:,.0f}: uitbetaling {pay:,.0f}, account naar {nxt:,.0f}"))
                level, bal = nxt, nxt
                peak_level = max(peak_level, level)
    yrs = (pd.Timestamp(a.end) - pd.Timestamp(a.start)).days / 365.25
    print(f"{a.prefix} {a.start} - {a.end}, risico {'1.8% met trappen (vorige bot)' if a.ladder else str(a.risk) + '%'} per trade: {len(f)} trades ({skipped} overgeslagen: "
          f"max 7 open / 5% open risico)")
    for day, msg in log:
        print(f"  {day} {msg}")
    print(f"  uitbetaald aan de trader: {paid:,.0f} (± {paid / yrs:,.0f} per jaar); account nu {level:,.0f}, saldo "
          f"{bal:,.0f}")


if __name__ == "__main__":
    main()
