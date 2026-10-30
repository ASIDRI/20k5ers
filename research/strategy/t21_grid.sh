#!/bin/bash
# Test 21 grid: test20 for every REV x LEG x BAND on the 34 instruments; 4 runs in parallel. Output out/g21_<cfg>_<SYM>.csv
cd "$(dirname "$0")/../.."
SYMS="$(ls research/strategy/out/s1_* | sed 's/.*s1_//;s/.csv//' | tr '\n' ' ') XAUUSD XAGUSD NAS100USD SPX500USD"
for rev in 2 2.5 3 4; do for leg in 4 6 8; do for band in 0.5,0.786 0.382,0.786 0.5,0.886; do
  echo "$rev $leg $band"
done; done; done | xargs -P 4 -L 1 bash -c 'python research/strategy/test20.py '"$SYMS"' --rev $0 --leg $1 --band $2 --prefix g21_r$0_l$1_b${2/,/-}_ > /dev/null 2>&1; echo "klaar r$0 l$1 b$2"'
