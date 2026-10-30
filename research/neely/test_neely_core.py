from neely_core import *


def test_monowaves():
    prices = [10, 11, 12, 11.5, 11, 12.5, 14, 13]
    mw = find_monowaves(prices)
    assert [(w.i0, w.i1) for w in mw] == [(0, 2), (2, 4), (4, 6), (6, 7)], mw
    assert mw[0].up and not mw[1].up


def test_equal_points_continue_wave():
    mw = find_monowaves([1, 2, 2, 3, 2])
    assert [(w.i0, w.i1) for w in mw] == [(0, 3), (3, 4)]


def test_rule_ids():
    assert rule_id(0.2) == 1
    assert rule_id(0.5) == 2
    assert rule_id(0.62) == 3
    assert rule_id(0.8) == 4
    assert rule_id(1.0) == 5
    assert rule_id(1.7) == 6
    assert rule_id(2.618) == 6   # 161.8% t/m 261.8% inclusief
    assert rule_id(3.0) == 7


def test_conditions():
    assert condition_id(1, 0.5) == "a" and condition_id(1, 1.618) == "c" and condition_id(1, 2.0) == "d"
    assert condition_id(3, 3.0) == "f"
    assert condition_id(4, 0.5) == "b" and condition_id(4, 3.0) == "e"
    assert condition_id(5, 0.9) == "a" and condition_id(7, 2.7) == "d"
    assert category_id(1.0) == "i" and category_id(2.0) == "ii" and category_id(3.0) == "iii"


def test_classify_monowave():
    # m0 omlaag (10->8), m1 omhoog (8->12), m2 omlaag (12->10.4): m2/m1 = 0.4 => R2, m0/m1 = 0.5 => b
    prices = [10, 9, 8, 10, 12, 11, 10.4, 11, 13]
    mw = find_monowaves(prices)
    lab = classify_monowave(prices, mw[1])
    assert lab == "R-2b", lab


def test_impulse_cases():
    # B: goede trending impuls, golf 3 verlengd
    ok = impulse_check([0, 10, 6, 30, 22, 36])
    assert ok["ok"] and ok["kind"] == "trending" and ok["extended"] == "3", ok
    # A: golf 2 neemt golf 1 volledig terug
    assert "R3" in impulse_check([0, 10, -1, 30, 22, 36])["failures"]
    # G: golf 4 neemt golf 3 volledig terug
    assert "R5" in impulse_check([0, 10, 6, 30, 5, 36])["failures"]
    # E: golf 3 is de kortste
    assert "R7" in impulse_check([0, 20, 12, 25, 22, 50])["failures"]
    # K: golf 3 niet langer dan golf 2
    assert "R4" in impulse_check([0, 10, 2, 9, 5, 20])["failures"]
    # Terminal: golf 4 overlapt golf 2
    t = impulse_check([0, 10, 4, 20, 9, 45])
    assert t["ok"] and t["kind"] == "terminal", t
    # geen extension
    assert "EXT" in impulse_check([0, 10, 6, 19, 14, 24])["failures"]


def test_abc():
    assert abc_classify([0, 10, 4, 14])["variant"] == "normal"          # zigzag
    assert abc_classify([0, 10, 4, 25])["variant"] == "elongated"
    assert abc_classify([0, 10, 4, 7])["family"] != "zigzag"
    assert abc_classify([0, 10, 1, 10.5])["variant"] in ("common", "elongated", "c_failure", "irregular")
    # flat: b 90% van a, c = 105% van b => common
    f = abc_classify([0, 10, 1, 10.45])
    assert f["family"] == "flat" and f["variant"] == "common", f
    # strong b 120%, c bijna 100% => irregular
    f = abc_classify([0, 10, -2, 10.2])
    assert f["family"] == "flat", f


def test_triangle():
    # contracting horizontal: a=10,b=8,c=6.4... pivots
    pts = [0, 10, 2, 8, 3.5, 6.5]
    t = triangle_check(pts)
    assert t["ok"] and t["variant"] == "contracting_horizontal", t
    assert abs(t["thrust_min"] - 0.75 * 10) < 1e-9
    bad = triangle_check([0, 10, 3.82, 9, 5, 7])  # b = 61.8% van a
    assert not bad["ok"]


def test_similarity():
    a = Monowave(0, 5, 0, 10)
    b = Monowave(5, 6, 10, 2)
    assert similar(a, b)      # prijs 8 vs 10 => 80%, dus gelijkwaardig
    c = Monowave(6, 7, 2, 3)
    assert not similar(a, c)  # prijs 10%, tijd 20% => kleinere Degree
