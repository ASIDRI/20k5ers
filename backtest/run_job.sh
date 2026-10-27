#!/bin/bash
# Start a long test or optimisation WITHOUT any time limit, detached from the terminal/session.
#
#   backtest/run_job.sh <name> <command ...>
#   backtest/run_job.sh screen2019 .venv/bin/python backtest/src/live_screen.py run 2019-01-02 2019-12-31
#
# - No timeout anywhere: the job runs until it is finished.
# - Detached (setsid + nohup): closing the terminal or the session does not stop it.
# - Resumable: the study scripts skip runs that already have results, so after a machine restart
#   the same command continues where it stopped.
# Log: backtest/output/jobs/<name>.log   Done marker (with exit code): backtest/output/jobs/<name>.done
set -u
cd "$(dirname "$0")/.."
name="$1"; shift
dir=backtest/output/jobs
mkdir -p "$dir"
rm -f "$dir/$name.done"
setsid nohup bash -c '"$@" >> "'"$dir/$name.log"'" 2>&1; echo "exit=$? $(date -u +%FT%TZ)" > "'"$dir/$name.done"'"' _ "$@" > /dev/null 2>&1 < /dev/null &
echo "started $name (pid $!), log: $dir/$name.log"
