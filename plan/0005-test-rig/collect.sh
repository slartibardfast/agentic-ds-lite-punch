#!/bin/sh
# collect.sh — pull a run directory from the router to the host results
# store (gitignored raw; the derived results.md commits as the record).
# Usage: collect.sh <run-name>   (run-name = the directory under
# /mnt/nvme/runs/2026-09-12/ on the router)

set -e
RUN=$1
[ -n "$RUN" ] || { echo "usage: $0 <run-name>"; exit 2; }
DEST="plan/0005-test-rig/results/$RUN"
mkdir -p "$DEST"
scp -r -o BatchMode=yes "root@192.168.21.1:/mnt/nvme/runs/2026-09-12/$RUN/." "$DEST/"
echo "collected to $DEST"