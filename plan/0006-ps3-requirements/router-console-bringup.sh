#!/bin/sh
# router-console-bringup.sh: route the PS3's whole traffic via eth1, the
# Virgin line, so its PSN flows reach the relay pin (call/0013). The
# default route egresses pppoe-vdsl4 (metric 16); a policy rule keyed on
# the console's reserved source address overrides that for the console
# alone. Add-or-ignore; run with `down` for the documented rollback.
set -eu

CONSOLE=192.168.21.138
TABLE=1000
GW=192.168.0.1
DEV=eth1
PRIO=25000

case "${1:-up}" in
  down)
    ip rule del from "$CONSOLE" lookup "$TABLE" prio "$PRIO" 2>/dev/null || true
    ip route flush table "$TABLE" 2>/dev/null || true
    echo "console pbr route removed (table $TABLE flushed)"
    ;;
  *)
    ip route replace default via "$GW" dev "$DEV" table "$TABLE"
    ip rule add from "$CONSOLE" lookup "$TABLE" prio "$PRIO" 2>/dev/null || true
    echo "console pbr route up: from $CONSOLE lookup $TABLE (via $GW dev $DEV)"
    ;;
esac