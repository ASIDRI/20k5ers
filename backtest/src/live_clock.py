"""
The LIVE bot's own clock rules, loaded from main_live_bot.py itself (not copied), so the backtest
cannot drift from them: broker time (New York + DST), rollover window, nightly de-risk window and
the server time used for the daily scan.

LIVE_TIMING=1 (default) makes the backtest use these; LIVE_TIMING=0 restores the old fixed-UTC timing.
"""
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

_SRC = (Path(__file__).resolve().parent.parent.parent / "main_live_bot.py").read_text(encoding="utf-8")
_NS = {"os": os, "datetime": datetime, "timedelta": timedelta, "timezone": timezone}

# constants + helper functions, verbatim from the live source
_a = _SRC.index('W5_BROKER_TZ = os.getenv("W5_BROKER_TZ"')
_b = _SRC.index("def _w5_set_clock_corr(")
exec(_SRC[_a:_b], _NS)
for _name in ("_w5_server_tz",):
    _m = re.search(rf"^def {_name}\(.*?(?=\n\n\n)", _SRC, re.S | re.M)
    exec(_m.group(0), _NS)

in_rollover = _NS["_w5_in_rollover"]
derisk_now = _NS["_w5_derisk_now"]
broker_now = _NS["_w5_broker_now"]
server_tz = _NS["_w5_server_tz"]


def enabled():
    return os.getenv("LIVE_TIMING", "1").strip().lower() not in ("0", "false", "no", "off")


def server_time(t):
    return t.astimezone(server_tz(t))


def is_scan_bar(t):
    """The live schedule (get_next_scan_time): 00:15 server time Tue-Fri, 01:00 server time Monday."""
    s = server_time(t)
    if s.weekday() >= 5:
        return False
    if s.weekday() == 0:
        return s.hour == 1 and s.minute == 0
    return s.hour == 0 and s.minute == 15
