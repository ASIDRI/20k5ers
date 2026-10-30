"""
neely_core.py
Deterministic kern van de Neely-methode (hoofdstuk 2 t/m 5 van "Mastering Elliott Wave").
Bevat alleen wat hard in code te gieten is. Geen handelslogica.

Alle ratio's zijn fracties (0.618 = 61.8%).
Tolerantie voor "ongeveer Fibonacci": zie TOL_FIB (boek: ongeveer 58% tot 66% voor 61.8%).
"""
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple, Dict

TOL_FIB = 0.04  # absolute marge rond 0.618 (boek, hoofdstuk 3, blz. 3-34)


# ---------------------------------------------------------------- data prep
def midpoint_series(highs: Sequence[float], lows: Sequence[float]) -> List[float]:
    """1 prijs per tijdseenheid: (H+L)/2. Boek: nooit alleen slotkoersen gebruiken."""
    return [(h + l) / 2.0 for h, l in zip(highs, lows)]


def ordered_series(bars: Sequence[Tuple[float, float, bool]]) -> List[float]:
    """2 prijzen per tijdseenheid, in volgorde van optreden. bar = (high, low, high_first)."""
    out: List[float] = []
    for h, l, high_first in bars:
        out.extend([h, l] if high_first else [l, h])
    return out


# ---------------------------------------------------------------- monowaves
@dataclass
class Monowave:
    i0: int          # index startpunt
    i1: int          # index eindpunt (de "dot")
    p0: float
    p1: float

    @property
    def up(self) -> bool:
        return self.p1 > self.p0

    @property
    def size(self) -> float:
        return abs(self.p1 - self.p0)

    @property
    def time(self) -> int:
        return self.i1 - self.i0


def find_monowaves(prices: Sequence[float]) -> List[Monowave]:
    """Een monowave eindigt zodra een datapunt de richting omkeert (hoe klein ook).
    Gelijke opeenvolgende punten tellen als doorlopen van de huidige golf (de dot komt op het laatste punt).
    De Rule of Neutrality wordt hier NIET toegepast (zie apply_neutrality_flags)."""
    n = len(prices)
    if n < 2:
        return []
    waves: List[Monowave] = []
    start = 0
    direction = 0
    last = 0
    for i in range(1, n):
        d = (prices[i] > prices[i - 1]) - (prices[i] < prices[i - 1])
        if d == 0:
            continue
        if direction == 0:
            direction = d
            last = i
        elif d == direction:
            last = i
        else:
            end = i - 1
            # laatste punt van een gelijke reeks is de dot
            waves.append(Monowave(start, end, prices[start], prices[end]))
            start = end
            direction = d
            last = i
    waves.append(Monowave(start, n - 1, prices[start], prices[n - 1]))
    return waves


def apply_neutrality_flags(waves: List[Monowave], price_scale: float, time_scale: float) -> List[Dict]:
    """Markeert monowaves die onder de Rule of Neutrality kunnen vallen: hoek < 45 graden
    nadat de grafiek volgens de Rule of Proportion geschaald is.
    price_scale / time_scale = eenheden op de assen zodat een directionele beweging een vierkant vult
    (bijv. price_scale = totale prijsrange, time_scale = totale tijdsduur).
    Geeft per golf: angle_deg en candidate (bool). De eigenlijke Aspect 1/2 afhandeling is in
    de strategie beschreven en vraagt context (zie doc, sectie 5)."""
    import math
    out = []
    for w in waves:
        dy = w.size / price_scale if price_scale else 0.0
        dx = max(w.time, 1) / time_scale if time_scale else 1.0
        ang = math.degrees(math.atan2(dy, dx))
        out.append({"wave": w, "angle_deg": ang, "candidate": ang < 45.0})
    return out


# ---------------------------------------------------------------- m0 / m2 (Rules of Observation)
def _m2_end(prices: Sequence[float], w: Monowave) -> Optional[int]:
    """Index van het eind van m2 als de high of low van m1 doorbroken is, anders None."""
    hi, lo = max(w.p0, w.p1), min(w.p0, w.p1)
    n = len(prices)
    for j in range(w.i1 + 1, n):
        if prices[j] > hi or prices[j] < lo:
            seg = range(w.i1 + 1, j)
            if not seg:
                return None
            if w.up:
                if prices[j] > hi:
                    return min(seg, key=lambda k: prices[k])           # laagste punt tussen
                # low van m1 gebroken tijdens m2: eerste keer omhoog na de break
                for k in range(j + 1, n):
                    if prices[k] > prices[k - 1]:
                        return k - 1
                return None
            else:
                if prices[j] < lo:
                    return max(seg, key=lambda k: prices[k])
                for k in range(j + 1, n):
                    if prices[k] < prices[k - 1]:
                        return k - 1
                return None
    return None


def _m0_start(prices: Sequence[float], w: Monowave) -> Optional[int]:
    """Spiegelbeeld achterwaarts in de tijd. TE VERIFIEREN tegen figuren 3-20b en 3-22 in het boek."""
    hi, lo = max(w.p0, w.p1), min(w.p0, w.p1)
    for j in range(w.i0 - 1, -1, -1):
        if prices[j] > hi or prices[j] < lo:
            seg = range(j, w.i0 + 1)
            return (max(seg, key=lambda k: prices[k]) if w.up else min(seg, key=lambda k: prices[k]))
    # data begint binnen de range van m1: gebruik de extreme binnen de beschikbare data (onvolledig, zie m0_complete)
    if w.i0 == 0:
        return None
    seg = range(0, w.i0 + 1)
    return (max(seg, key=lambda k: prices[k]) if w.up else min(seg, key=lambda k: prices[k]))


def retracement_ratios(prices: Sequence[float], w: Monowave) -> Dict[str, Optional[float]]:
    e2 = _m2_end(prices, w)
    s0 = _m0_start(prices, w)
    m2 = abs(prices[e2] - w.p1) / w.size if e2 is not None and w.size else None
    m0 = abs(prices[s0] - w.p0) / w.size if s0 is not None and w.size else None
    return {"m2_over_m1": m2, "m0_over_m1": m0, "m2_end": e2, "m0_start": s0}
    # LET OP: m0 kan onvolledig zijn als de data te kort is; bot moet dan Rule/Conditie als "voorlopig" markeren


# ---------------------------------------------------------------- Retracement Rules (hoofdstuk 3, blz. 3-22 t/m 3-30)
def rule_id(m2: float, tol: float = TOL_FIB) -> int:
    if abs(m2 - 0.618) <= tol:
        return 3
    if m2 < 0.382:
        return 1
    if m2 < 0.618:
        return 2
    if m2 < 1.0:
        return 4
    if m2 < 1.618:
        return 5
    if m2 <= 2.618:
        return 6
    return 7


def condition_id(rule: int, m0: float) -> str:
    """Conditie a, b, c ... op basis van m0/m1 (blz. 3-23 t/m 3-30).
    Elke rij: (bovengrens, label, bovengrens_inclusief). Inclusief waar het boek 'inclusive' vermeldt."""
    if rule == 1:
        rows = [(0.618, "a", False), (1.0, "b", False), (1.618, "c", True)]
        tail = "d"
    elif rule == 2:
        rows = [(0.382, "a", False), (0.618, "b", False), (1.0, "c", False), (1.618, "d", True)]
        tail = "e"
    elif rule == 3:
        rows = [(0.382, "a", False), (0.618, "b", False), (1.0, "c", False), (1.618, "d", False), (2.618, "e", True)]
        tail = "f"
    elif rule == 4:
        rows = [(0.382, "a", False), (1.0, "b", False), (1.618, "c", False), (2.618, "d", True)]
        tail = "e"
    else:  # 5, 6, 7
        rows = [(1.0, "a", False), (1.618, "b", False), (2.618, "c", True)]
        tail = "d"
    for edge, label, inclusive in rows:
        if m0 < edge or (inclusive and abs(m0 - edge) < 1e-9):
            return label
    return tail


def category_id(m3_over_m2: float) -> str:
    """Alleen voor Rule 4 (blz. 3-25)."""
    if m3_over_m2 < 1.618:
        return "i"
    if m3_over_m2 <= 2.618:
        return "ii"
    return "iii"


def classify_monowave(prices: Sequence[float], w: Monowave) -> Optional[str]:
    r = retracement_ratios(prices, w)
    if r["m2_over_m1"] is None or r["m0_over_m1"] is None:
        return None
    rule = rule_id(r["m2_over_m1"])
    return f"R-{rule}{condition_id(rule, r['m0_over_m1'])}"


# ---------------------------------------------------------------- Impulse test (hoofdstuk 5, blz. 5-2 t/m 5-8)
def impulse_check(p: Sequence[float], allow_exceptions: bool = False) -> Dict:
    """p = 6 pivotprijzen [p0..p5] van vijf opeenvolgende segmenten.
    Geeft dict met 'ok', 'kind' (trending/terminal/None), 'failures' (lijst regelnummers) en 'extended'."""
    if len(p) != 6:
        return {"ok": False, "kind": None, "failures": ["R1"], "extended": None}
    sgn = 1 if p[1] > p[0] else -1
    seg = [abs(p[i + 1] - p[i]) for i in range(5)]
    w1, w2, w3, w4, w5 = seg
    fails = []
    # richting: 1,3,5 in trendrichting, 2,4 ertegen
    for i in range(5):
        up = p[i + 1] > p[i]
        if (i % 2 == 0 and up != (sgn == 1)) or (i % 2 == 1 and up == (sgn == 1)):
            fails.append("R2")  # 3 segmenten in 1 richting
            break
    if w2 >= w1:
        fails.append("R3")      # golf 2 mag golf 1 niet volledig terugnemen
    if w3 <= w2:
        fails.append("R4")
    if w4 >= w3:
        fails.append("R5")
    if w5 < 0.382 * w4:
        fails.append("R6")
    if w3 < w1 and w3 < w5:
        fails.append("R7")      # golf 3 mag niet de kortste van 1,3,5 zijn
    legs = {"1": w1, "3": w3, "5": w5}
    ordered = sorted(legs.items(), key=lambda kv: kv[1], reverse=True)
    longest, second = ordered[0], ordered[1]
    extended = longest[0] if longest[1] >= 1.618 * second[1] else None
    exception1 = False
    if extended is None and longest[0] == "1":
        beyond = (p[3] - p[1]) if sgn == 1 else (p[1] - p[3])
        # uitzondering 1 (blz. 5-4): golf 1 is de langste, net onder 161.8% van golf 3,
        # en golf 3 eindigt niet meer dan 61.8% voorbij het eind van golf 1
        exception1 = beyond <= 0.618 * w1
    if extended is None and not (exception1 and allow_exceptions):
        fails.append("EXT")
    if extended is None and exception1 and allow_exceptions:
        extended = "1(uitzondering)"
    overlap = (p[4] < p[1]) if sgn == 1 else (p[4] > p[1])
    kind = "terminal" if overlap else "trending"
    ok = not fails
    return {"ok": ok, "kind": kind if ok else None, "failures": fails,
            "extended": extended, "w5_failure": w5 < w4, "exception1_candidate": exception1}


# ---------------------------------------------------------------- Flats en Zigzags (blz. 5-16 t/m 5-23)
def abc_classify(p: Sequence[float]) -> Dict:
    """p = [p0, p1, p2, p3] pivots van a, b, c. Geeft familie en variant."""
    a = abs(p[1] - p[0])
    b = abs(p[2] - p[1])
    c = abs(p[3] - p[2])
    if a == 0 or b == 0:
        return {"family": None}
    a_up = p[1] > p[0]
    b_ret = b / a
    c_beyond_a = (p[3] > p[1]) if a_up else (p[3] < p[1])
    # Zigzag: b <= 61.8% van a (min 1%), c voorbij het eind van a
    if 0.01 <= b_ret <= 0.618 + 1e-9 and c_beyond_a:
        ratio = c / a
        if ratio > 1.618:
            return {"family": "zigzag", "variant": "elongated",
                    "confirm": "na afloop > 61.8% terugkeer van c, anders is het een impuls"}
        if ratio >= 0.618:
            return {"family": "zigzag", "variant": "normal"}
        if ratio >= 0.382:
            return {"family": "zigzag", "variant": "truncated",
                    "confirm": "markt moet >= 81% (liefst 100%+) van de hele zigzag terugnemen"}
        return {"family": None}
    # Flat: b >= 61.8% van a, c >= 38.2% van a
    if b_ret >= 0.618 - 1e-9 and c >= 0.382 * a:
        lo, hi = min(p[0], p[1]), max(p[0], p[1])
        c_lo, c_hi = min(p[2], p[3]), max(p[2], p[3])
        c_in_range = not (c_hi < lo or c_lo > hi)
        cb = c / b
        if b_ret > 1.0:   # strong b
            if b_ret <= 1.236:
                if cb >= 1.0:
                    return {"family": "flat", "variant": "elongated" if c / a > 1.618 else "irregular"}
                return {"family": "flat", "variant": "irregular_failure" if c_in_range else "running"}
            if cb >= 1.0 and b_ret <= 1.382:
                return {"family": "flat", "variant": "irregular"}
            return {"family": "flat", "variant": "irregular_failure" if c_in_range else "running"}
        if b_ret >= 0.81:  # normal b
            if cb < 1.0:
                return {"family": "flat", "variant": "c_failure"}
            return {"family": "flat", "variant": "common" if cb <= 1.382 else "elongated"}
        # weak b (61.8% tot 80%)
        if cb < 1.0:
            return {"family": "flat", "variant": "double_failure"}
        return {"family": "flat", "variant": "b_failure" if cb <= 1.382 else "elongated"}
    return {"family": None}


# ---------------------------------------------------------------- Triangle (blz. 5-22 t/m 5-33)
def triangle_check(p: Sequence[float]) -> Dict:
    """p = 6 pivots [p0..p5] = begin a, einde a, b, c, d, e. Hard-minimum controles en variant."""
    if len(p) != 6:
        return {"ok": False, "reason": "6 pivots nodig"}
    s = [abs(p[i + 1] - p[i]) for i in range(5)]
    a, b, c, d, e = s
    fails = []
    if not (0.382 <= b / a <= 2.618):
        fails.append("b/a buiten 38.2%-261.8%")
    retr = [s[i + 1] / s[i] for i in range(4)]       # b/a, c/b, d/c, e/d
    if sum(1 for r in retr if r >= 0.5) < 3:
        fails.append("minder dan 3 van 4 retracements >= 50%")
    if abs(b / a - 0.618) <= TOL_FIB:
        fails.append("b is ~61.8% van a: waarschijnlijk geen triangle")
    contracting = e < d < c or (c < b and e < d)
    expanding = e > d > c or (e == max(s))
    variant = None
    if contracting and e == min(s):
        if b < a and d < c:
            variant = "contracting_horizontal"
        elif b > a and c < b and d < c and e < d:
            variant = "contracting_irregular"
        elif b == max(s) and c < b and d > c and e < d:
            variant = "contracting_running"
    elif expanding and min(a, b) == min(s) and e == max(s):
        variant = "expanding"
    if variant is None:
        fails.append("geen herkende variant")
    widest = max(s)
    out = {"ok": not fails, "variant": variant, "failures": fails, "widest": widest}
    if variant and variant.startswith("contracting"):
        out["thrust_min"] = 0.75 * widest
        out["thrust_normal_max"] = 1.25 * widest
        if variant.endswith("running"):
            out["thrust_max"] = 2.518 * widest   # boek noemt "251.8%" (OCR, verifieer)
    return out


# ---------------------------------------------------------------- Similarity and Balance (blz. 4-3)
def similar(w_a: Monowave, w_b: Monowave) -> bool:
    """Dezelfde Degree-kandidaten: kleinste >= 1/3 van grootste in prijs OF in tijd."""
    pr = min(w_a.size, w_b.size) / max(w_a.size, w_b.size) if max(w_a.size, w_b.size) else 0
    ti = min(w_a.time, w_b.time) / max(w_a.time, w_b.time) if max(w_a.time, w_b.time) else 0
    return pr >= 1 / 3 or ti >= 1 / 3
