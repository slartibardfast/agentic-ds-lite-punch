#!/bin/sh
# nft-bringup.sh — router-side rules for the test rig. Idempotent. Review
# before apply. Revert: run with REVERT=1, or delete the named chains.

set -e
PROBE_IP=192.168.21.11
SINK_IP=192.168.21.12
SINK_PORT=40002
RELAY_TUPLE=192.168.0.21:40000
PBR_MARK=0x00010000        # vdsl4 selector nibble (ip rule 30000)
PBR_MASK=0x00ff0000
[ -n "$REVERT" ] && ACTION="-D" || ACTION="-A"

apply_rule() {
  nft add rule "$@" 2>/dev/null || true
}
del_rule() {
  nft delete rule "$@" 2>/dev/null || true
}

if [ -n "$REVERT" ]; then
  del_rule ip dslp-test mangle-prerouting udp ip saddr "$PROBE_IP" meta mark set "$PBR_MARK/$PBR_MASK"
  del_rule ip dslp-test nat-postrouting oifname pppoe-vdsl4 udp ip saddr "$PROBE_IP" masquerade
  del_rule ip dslp-test nat-postrouting oifname eth1 udp ip saddr "$SINK_IP" udp sport "$SINK_PORT" snat to "$RELAY_TUPLE"
  nft delete chain ip dslp-test mangle-prerouting 2>/dev/null || true
  nft delete chain ip dslp-test nat-postrouting 2>/dev/null || true
  nft delete table ip dslp-test 2>/dev/null || true
  echo "reverted"
  exit 0
fi

# Table + chains. mangle/prerouting marks the probe into the vdsl4 table;
# ip nat postrouting carries the probe masquerade and the sink reply pin.
nft add table ip dslp-test 2>/dev/null || true
nft add chain ip dslp-test mangle-prerouting "{ type filter hook prerouting priority mangle; }" 2>/dev/null || true
nft add chain ip dslp-test nat-postrouting "{ type nat hook postrouting priority srcnat; }" 2>/dev/null || true

# 1. Probe egress: mark UDP from the probe into the vdsl4 nibble.
apply_rule ip dslp-test mangle-prerouting udp ip saddr "$PROBE_IP" meta mark set "$PBR_MARK/$PBR_MASK"
# 2. Probe public source: masquerade that traffic on the vdsl4 uplink.
apply_rule ip dslp-test nat-postrouting oifname pppoe-vdsl4 udp ip saddr "$PROBE_IP" masquerade
# 3. Sink reply path: replies leave as the relay tuple (A1 pin).
apply_rule ip dslp-test nat-postrouting oifname eth1 udp ip saddr "$SINK_IP" udp sport "$SINK_PORT" snat to "$RELAY_TUPLE"

echo "applied"
nft list table ip dslp-test