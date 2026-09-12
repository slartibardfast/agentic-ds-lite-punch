#!/bin/sh
# router-nft-bringup.sh - router-side rules for the test rig. Idempotent.
# Review before apply. Revert: run with REVERT=1, or delete the named table.
#
# No fwmark rule: the probe matches no pbr_output rule, so it already
# falls through to the main-table default via pppoe-vdsl4 (metric 16).
# The two rules below are both load-bearing:
#   masq:  the router has no masquerade at all, so the probe's v4 egress is
#          built here (its source becomes the vdsl4 public IP).
#   pin:   the sink's replies egress eth1 as the relay tuple, the A1 reply
#          path. Verify precedence on-wire against fw4's fixed eth1 snat
#          and the live ip dslp snat_map (plan/0005 checklist item 4).

set -e
PROBE_IP=192.168.21.11
SINK_IP=192.168.21.12
SINK_PORT=40002
RELAY_TUPLE=192.168.0.21:40000
[ -n "$REVERT" ] && ACTION="-D" || ACTION="-A"

apply_rule() {
  nft add rule "$@" 2>/dev/null || true
}
del_rule() {
  nft delete rule "$@" 2>/dev/null || true
}

if [ -n "$REVERT" ]; then
  del_rule ip dslp-test nat-postrouting oifname pppoe-vdsl4 udp ip saddr "$PROBE_IP" masquerade
  del_rule ip dslp-test nat-postrouting oifname eth1 udp ip saddr "$SINK_IP" udp sport "$SINK_PORT" snat to "$RELAY_TUPLE"
  nft delete chain ip dslp-test nat-postrouting 2>/dev/null || true
  nft delete table ip dslp-test 2>/dev/null || true
  echo "reverted"
  exit 0
fi

# One table, one nat chain carrying both rules.
nft add table ip dslp-test 2>/dev/null || true
nft add chain ip dslp-test nat-postrouting "{ type nat hook postrouting priority srcnat; }" 2>/dev/null || true

# 1. Probe public source: masquerade the probe's UDP on the vdsl4 uplink.
apply_rule ip dslp-test nat-postrouting oifname pppoe-vdsl4 udp ip saddr "$PROBE_IP" masquerade
# 2. Sink reply path: replies leave eth1 as the relay tuple (A1 pin).
apply_rule ip dslp-test nat-postrouting oifname eth1 udp ip saddr "$SINK_IP" udp sport "$SINK_PORT" snat to "$RELAY_TUPLE"

echo "applied"
nft list table ip dslp-test