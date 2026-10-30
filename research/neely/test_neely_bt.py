"""No look-ahead in neely_bt: cutting the data off at a bar must not change any setup that was filled before it."""
import numpy as np
import pandas as pd
import pytest

from neely_core import find_monowaves
import neely_bt

COLS = ["setup", "family", "variant", "dir", "fill", "entry", "sl", "tp1", "tp2", "htf", "lab_ok", "lab_n"]


def test_monowaves_stable_under_cut():
    rng = np.random.default_rng(1)
    pts = np.round(np.cumsum(rng.normal(size=600)), 1).tolist()
    full = find_monowaves(pts)
    for n in (50, 211, 400, 599):
        part = find_monowaves(pts[:n])
        done = [(w.i0, w.i1) for w in part[:-1]]  # the last one is still running
        assert done == [(w.i0, w.i1) for w in full[:len(done)]]


@pytest.mark.parametrize("sym,tf,cut", [("EURUSD", "D1", "2012-06-04"), ("GBPJPY", "D1", "2019-03-13"),
                                        ("EURUSD", "W1", "2016-09-07"), ("XAUUSD", "D1", "2024-05-15")])
def test_cut_changes_nothing_before_it(sym, tf, cut):
    cut = pd.Timestamp(cut, tz="UTC")
    full = neely_bt.run(sym, tf, "2005-01-01", "2025-12-31")
    part = neely_bt.run(sym, tf, "2005-01-01", "2025-12-31", cut=cut)
    last = str((cut - pd.Timedelta(days=8 if tf == "W1" else 2)).date())
    a = full[(full.result == "gevuld") & (full.fill < last)][COLS].reset_index(drop=True)
    b = part[(part.result == "gevuld") & (part.fill < last)][COLS].reset_index(drop=True)
    assert len(a) > 0
    pd.testing.assert_frame_equal(a, b)


@pytest.mark.parametrize("tf,cut", [("D1", "2013-09-18"), ("D1", "2022-02-02"), ("W1", "2017-05-10")])
def test_counter_cut_changes_nothing_before_it(tf, cut):
    import neely_count
    cut = pd.Timestamp(cut, tz="UTC")
    full, _, _ = neely_count.run("EURUSD", tf=tf)
    part, _, _ = neely_count.run("EURUSD", tf=tf, cut=cut)
    last = str((cut - pd.Timedelta(days=8 if tf == "W1" else 2)).date())
    cols = ["name", "cx", "dir", "op_tijd", "start_t", "end_t", "fill", "p0", "p1", "result"]
    a = full[full.fill < last][cols].reset_index(drop=True)
    b = part[part.fill < last][cols].reset_index(drop=True)
    assert len(a) > 0
    pd.testing.assert_frame_equal(a, b)
