"""Is a 5ers challenge worth buying with a given strategy? Pass probabilities and expected payouts.

    python research/rnd/prop_ev.py --fee 0.005 --vols 0.06,0.10,0.15,0.20

Model (5ers High Stakes, docs/5ERS_COMPLIANCE.md): step 1 +8%, step 2 +5%, both on the starting balance; breach if
equity falls 10% below the starting balance (static) or 5% below the day's start (max of equity and balance at
server midnight). No time limit. Funded: every time equity is +W% above the funded start, 80% of that profit is paid
out and the account starts again from the funded balance; the account is lost at -10%. Horizon: H trading days funded.
Intraday: the daily loss is checked on the day's close plus an intraday allowance (the day's adverse move is assumed
up to `--intraday` times the close-to-close loss), so a day can breach before it closes.

Strategies: daily portfolio returns (after costs) from systematic.py, rescaled point in time to a target annual
volatility (60-day realised volatility of the portfolio, known at t). 'zero' = the buy-and-hold basket with its mean
removed: same volatility and fat tails, no drift (the pure barrier effect).
Paths: every start date in 2015-2025 (real order of days, as far as the data reaches) and block bootstrap (20-day
blocks) for long horizons. Results in units of the account size: fee and payouts as a fraction of the account.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "strategy")]
import systematic as S  # noqa: E402

BASKET = ["SPX500_USD", "NAS100_USD", "UK100_USD", "XAU_USD", "XAG_USD"]


def strategy_returns(start, end, basket=None, from_m15=True):
    basket = basket or BASKET
    orig = S.positions

    def pos(d):
        o = orig(d)
        c = d["close"]
        return {"buyhold": pd.Series(1.0, index=c.index), "trend_long": o["mom252"].clip(lower=0),
                "pullback_long": o["pullback"].clip(lower=0), "mom126_ls": o["mom126"]}
    S.positions = pos
    res = S.run(start, end, basket, set(basket) if from_m15 else set())
    S.positions = orig
    out = {k: df.mean(axis=1, skipna=True).dropna() for k, df in res.items()}
    out["zero"] = out["buyhold"] - out["buyhold"].mean()
    return out


def scale(r, target):
    vol = r.rolling(60).std().shift(1) * np.sqrt(252)
    return (r * (target / vol).clip(upper=10)).dropna()


def challenge(path, intraday):
    """Steps 1 and 2 on one path of daily returns; returns (passed, days_used) and the index where it stopped."""
    i = 0
    for target in (0.08, 0.05):
        eq = 1.0
        while True:
            if i >= len(path):
                return False, i, "einde data"
            day_start = eq
            r = path[i]
            i += 1
            low = eq * (1 + min(r, 0) * intraday)
            eq *= 1 + r
            if low <= 0.90 or low <= day_start * 0.95:
                return False, i, "breach"
            if eq >= 1 + target:
                break
    return True, i, "geslaagd"


def funded(path, intraday, w, split=0.8):
    """Total payouts (fraction of the account) until the account is lost or the path ends."""
    paid, eq = 0.0, 1.0
    for r in path:
        day_start = eq
        low = eq * (1 + min(r, 0) * intraday)
        eq *= 1 + r
        if low <= 0.90 or low <= day_start * 0.95:
            return paid, True
        if eq >= 1 + w:
            paid += split * (eq - 1)
            eq = 1.0
    return paid, False


def bootstrap(r, n, block=20, rng=None):
    idx = []
    while len(idx) < n:
        s = rng.integers(0, len(r) - block)
        idx.extend(range(s, s + block))
    return r[np.array(idx[:n])]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2015-06-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--vols", default="0.06,0.10,0.15,0.20")
    ap.add_argument("--fee", type=float, default=0.005, help="challenge fee as a fraction of the account (0.005 = $500 on $100k)")
    ap.add_argument("--withdraw", type=float, default=0.04, help="funded: take profit out every +W")
    ap.add_argument("--horizon", type=int, default=504, help="funded trading days simulated (504 = 2 years)")
    ap.add_argument("--intraday", type=float, default=1.5)
    ap.add_argument("--sims", type=int, default=2000)
    ap.add_argument("--basket", default=",".join(BASKET))
    ap.add_argument("--stored-d1", action="store_true", help="use the stored D1 files (history before 2015) instead of D1 from M15")
    a = ap.parse_args()
    rets = strategy_returns(a.start, a.end, a.basket.split(","), not a.stored_d1)
    rng = np.random.default_rng(7)
    rows = []
    for name, r0 in rets.items():
        for v in map(float, a.vols.split(",")):
            r = scale(r0, v).values
            # real order: every 5th start date, challenge then funded on the following days
            real = []
            for s in range(0, len(r) - 260, 5):
                ok, used, _ = challenge(r[s:], a.intraday)
                real.append((ok, used))
            p_real = np.mean([x[0] for x in real])
            # bootstrap: challenge + funded horizon
            ok_n, days, pays = 0, [], []
            for _ in range(a.sims):
                path = bootstrap(r, 2520 + a.horizon, rng=rng)
                ok, used, _ = challenge(path, a.intraday)
                if ok:
                    ok_n += 1
                    days.append(used)
                    pays.append(funded(path[used:used + a.horizon], a.intraday, a.withdraw)[0])
                else:
                    pays.append(0.0)
            p = ok_n / a.sims
            ev = np.mean(pays) - a.fee
            rows.append(dict(strategie=name, vol=v, pass_echt=round(p_real * 100, 1), pass_boot=round(p * 100, 1),
                             dagen_mediaan=int(np.median(days)) if days else None,
                             uitbet_als_funded=round(np.mean([x for x in pays if x > 0] or [0]) * 100, 2),
                             EV_per_challenge=round(ev * 100, 2)))
    t = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(f"fee {a.fee*100:.2f}% van het account, uitbetaling bij +{a.withdraw*100:.0f}%, funded horizon {a.horizon} dagen, "
          f"intraday-factor {a.intraday}")
    print(t.to_string(index=False))
    t.to_csv(HERE / "out" / "prop_ev.csv", index=False)
