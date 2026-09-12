#!/bin/sh
# snapshot.sh — 1 Hz router-side observation for one run.
# Writes tab-separated lines: monotonic_ms tuple relay_pid dir_entries.
# tuple is "" while the file is absent at a restart boundary. The tuple is
# republished only on change, so a timestamp delta marks the republish.

set -e
RUN_DIR=$1
OUT=$RUN_DIR/snapshot.tsv
: > "$OUT"
while true; do
  ms=$(awk '{printf "%d", $1 * 1000}' /proc/uptime)
  tup=$(cat /run/ds-lite-punch/tuple 2>/dev/null || echo "absent")
  pid=$(pgrep -f ds-lite-punch | head -1)
  ents=$(ls /run/ds-lite-punch 2>/dev/null | tr '\n' ',')
  printf '%s\t%s\t%s\t%s\n' "$ms" "$tup" "$pid" "$ents" >> "$OUT"
  sleep 1
done