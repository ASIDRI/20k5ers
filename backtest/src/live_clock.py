"""
The live clock rules from server_clock.py (shared with the live bot), so the backtest cannot drift from them: broker time (New York + DST), rollover window, nightly de-risk window and
the server time used for the daily scan.

LIVE_TIMING=1 (default) makes the backtest use these; LIVE_TIMING=0 restores the old fixed-UTC timing.
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import server_clock as _sc  # noqa: E402  (one definition for the test environment and the live bot)

_NS = vars(_sc)
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
