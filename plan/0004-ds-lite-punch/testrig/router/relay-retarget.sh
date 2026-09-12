#!/bin/sh
# relay-retarget.sh — point the relay's forward target at dslp-sink for the
# campaign, and revert to the router sink afterwards. The reload restarts
# the relay: one port-reuse observation at retarget, another at revert.

set -e
ENV_FILE=/etc/ds-lite-punch.env
SINK=192.168.21.12:40002
ROUTER_SINK=192.168.21.1:40001

case "$1" in
  to-sink)
    sed -i 's/^TARGET=.*/TARGET='"$SINK"'/' "$ENV_FILE"
    ;;
  to-router)
    sed -i 's/^TARGET=.*/TARGET='"$ROUTER_SINK"'/' "$ENV_FILE"
    ;;
  *)
    echo "usage: $0 to-sink|to-router" >&2
    exit 2
    ;;
esac

service ds-lite-punch reload
sleep 1
# The tuple republishes only on change; re-read after the restart settles.
grep '^TARGET' "$ENV_FILE"
cat /run/ds-lite-punch/tuple