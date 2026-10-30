"""Broker/server clock of the 5ers MT5 server (New York + 7 h, with US DST): rollover window, nightly
de-risk window and server time. Taken over verbatim from the retired main_live_bot.py (2026-10-29) so the
test environment (backtest/src/live_clock.py) and the next live bot share one definition."""
import os
from datetime import datetime, timedelta, timezone


W5_BROKER_TZ = os.getenv("W5_BROKER_TZ", "America/New_York")
W5_ROLL_HOUR_LOCAL = int(os.getenv("W5_ROLL_HOUR_LOCAL", "17"))   # 17:00 New York

# Zelfcorrectie tegen de ECHTE serverklok, in hele uren. Normaal 0. De bot meet
# bij opstart en bij elke dagelijkse scan de offset van de 5ers-server (uit de
# tijdstempel van een live tick) en vergelijkt die met wat hij zelf uitrekent.
# Wijkt het af, dan wordt het verschil hier gezet en volgt ALLES — serverdag,
# daglimiet-reset, scan, middernacht-sync, rolvenster, de-risk — de server in
# plaats van de eigen berekening. Zie _w5_check_server_clock().
_W5_CLOCK_CORR_H = 0


def _w5_broker_now(now_utc=None):
    """now_utc omgerekend naar brokertijd. Valt terug op UTC+2 als de
    tijdzonedatabase ontbreekt — dan is het gedrag identiek aan het oude,
    in plaats van een crash."""
    from datetime import timedelta as _td
    n = now_utc or datetime.now(timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        b = n.astimezone(ZoneInfo(W5_BROKER_TZ))
    except Exception:
        # Zonder tijdzonedatabase: vaste UTC-5 (EST). Dan is het gedrag gelijk aan
        # de winterstand in plaats van een crash — mis in de zomer, maar
        # voorspelbaar mis. De zelfcorrectie hieronder vangt dat alsnog op.
        b = n.astimezone(timezone(_td(hours=-5)))
    return b + _td(hours=_W5_CLOCK_CORR_H) if _W5_CLOCK_CORR_H else b


# Het rolvenster in MINUTEN NA MIDDERNACHT BROKERTIJD, als enige bron van
# waarheid: 23:30 tot 00:30. In UTC is dat 21:30-22:30 in de winter en
# 20:30-21:30 in de zomer. De de-risk leidt zijn eigen grens hiervan af, zodat
# de twee niet los van elkaar kunnen verschuiven.
W5_ROLL_START_MIN = W5_ROLL_HOUR_LOCAL * 60 - 30   # 16:30 New York
W5_ROLL_END_MIN = W5_ROLL_HOUR_LOCAL * 60 + 30    # 17:30 New York
# Hoeveel minuten de de-risk VOOR het rolvenster klaar moet zijn. Het afvlakken
# zelf kost tijd — tot twintig posities sluiten, met drie herpogingen per order —
# dus eindigen op de minuut voor de rollover betekent dat de laatste sluitingen
# er gegarandeerd in vallen.
W5_DERISK_GUARD_MIN = int(os.getenv("W5_DERISK_GUARD_MIN", "15"))


def _w5_broker_minutes(now_utc=None):
    """Minuten na middernacht brokertijd."""
    b = _w5_broker_now(now_utc)
    return b.hour * 60 + b.minute


def _w5_in_rollover(now_utc=None):
    """Het rolvenster rond de dagovergang: 16:30-17:30 New York.
    Dat is 21:30-22:30 UTC in de winter en 20:30-21:30 UTC in de zomer."""
    m = _w5_broker_minutes(now_utc)
    for start, end in ((W5_ROLL_START_MIN, W5_ROLL_END_MIN),):
        if start <= m < end or start <= m + 1440 < end:
            return True
    return False


def _w5_derisk_now(now_utc=None):
    """Draait de nachtelijke de-risk op dit moment?

    NIGHTLY_DERISK_BROKER_HOUR is het uur in BROKERTIJD en is DST-vast. Default
    23 = een uur voor de brokerdag sluit, ruim voor het rolvenster.

    NIGHTLY_DERISK_HOUR (UTC) blijft bestaan om oude backtestresultaten exact te
    kunnen reproduceren: zet W5_DERISK_UTC=1 en het oude gedrag komt terug."""
    if os.getenv("W5_DERISK_UTC", "0").strip().lower() in ("1", "true", "yes", "on"):
        n = now_utc or datetime.now(timezone.utc)
        return n.hour == int(os.getenv("NIGHTLY_DERISK_HOUR", "21"))
    m = _w5_broker_minutes(now_utc)
    start = int(os.getenv("NIGHTLY_DERISK_BROKER_HOUR", "16")) * 60
    # Sluiten moet KLAAR zijn voor het rolvenster, niet er net voor beginnen. Het
    # uur 23:00-23:59 overlapt de rollover vanaf 23:30, en de de-risk draait op
    # het moment dat de lus hem voor het eerst ziet — dat kan 16:29 zijn, waarna
    # de laatste van twintig sluitingen er alsnog in valt. Het venster loopt
    # daarom tot 15 minuten voor de rollover (16:00-16:14 New York), en die
    # grens wordt AFGELEID van het rolvenster zodat ze niet los kunnen lopen.
    eind = W5_ROLL_START_MIN - W5_DERISK_GUARD_MIN
    return start <= m < min(start + 60, eind)


def _w5_server_tz(now_utc=None):
    """De MT5-serverzone op DIT moment: UTC+2 in de winter, UTC+3 in de zomer.

    Afgeleid van America/New_York, want de FX-dag rolt op 17:00 New York en de
    data volgt de Amerikaanse zomertijddata (gemeten: 22 van de 22 overgangen
    over elf jaar). Server = New York + 7 uur, dus -5+7 = +2 in EST en
    -4+7 = +3 in EDT.

    SERVER_TZ blijft bestaan als terugval zonder tijdzonedatabase: dan is het
    gedrag gelijk aan het oude vaste UTC+2 in plaats van een crash.
    """
    from datetime import timedelta as _td
    n = now_utc or datetime.now(timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        ny = n.astimezone(ZoneInfo(os.getenv("W5_BROKER_TZ", "America/New_York")))
        return timezone(ny.utcoffset() + _td(hours=7 + _W5_CLOCK_CORR_H))
    except Exception:
        return timezone(_td(hours=2 + _W5_CLOCK_CORR_H))
