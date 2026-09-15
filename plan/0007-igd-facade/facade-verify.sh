#!/bin/sh
# facade-verify.sh — the plan/0007 #facade live verification battery.
#
# Runs on the router (pushed via ssh from the dev box) against a deployed
# facade build: SSDP discovery + the full upnpc verb set, M-POST parity via
# curl, GENA subscribe/renew/unsubscribe with a callback catcher in the
# probe container, and an SSDP/SOAP capture on the router. The UDP and TCP
# data-through-the-mapping legs are driven separately (external vantage +
# sink responder, see the results record).
#
# Prereqs on the router: /tmp/gena-catcher.py (scp'd next to this script);
# the dslp-probe container has upnpc and python3.
#
# Usage: sh /tmp/facade-verify.sh
SINK_IP=192.168.21.12
SINK_PORT=4444
PROBE_IP=192.168.21.11
EXT_TCP=14567
EXT_UDP=14568
CB_PORT=18080
P=192.168.21.1:49152
OUT=/tmp/facade-live
rm -rf "$OUT"; mkdir -p "$OUT"

# Service name map for the SOAP actions (IPConn -> WANIPConnection etc).
svc_name() { [ "$1" = IPConn ] && echo WANIPConnection || echo WANPPPConnection; }

echo "== capture on br-lan (ssdp 1900 + upnp 49152) =="
tcpdump -i br-lan -n -s 0 -w "$OUT/facade-battery.pcap" \
  'udp port 1900 or tcp port 49152 or (udp and port 14500-15000)' >/dev/null 2>&1 &
CAP_PID=$!
sleep 1

echo "== upnpc -l (baseline) =="
lxc-attach -n dslp-probe -- upnpc -l 2>&1 | tee "$OUT/upnpc-l-baseline.txt"

echo "== upnpc -a TCP / UDP =="
lxc-attach -n dslp-probe -- upnpc -a "$SINK_IP" "$SINK_PORT" "$EXT_TCP" TCP 2>&1 | tee "$OUT/upnpc-a-tcp.txt"
lxc-attach -n dslp-probe -- upnpc -a "$SINK_IP" "$SINK_PORT" "$EXT_UDP" UDP 2>&1 | tee "$OUT/upnpc-a-udp.txt"

echo "== upnpc -l (after adds) =="
lxc-attach -n dslp-probe -- upnpc -l 2>&1 | tee "$OUT/upnpc-l-grants.txt"

echo "== upnpc -d TCP and UDP =="
lxc-attach -n dslp-probe -- upnpc -d "$EXT_TCP" TCP 2>&1 | tee "$OUT/upnpc-d-tcp.txt"
lxc-attach -n dslp-probe -- upnpc -d "$EXT_UDP" UDP 2>&1 | tee "$OUT/upnpc-d-udp.txt"

echo "== M-POST parity (POST vs M-POST, both services) =="
for svc in IPConn PPPConn; do
  NAME=$(svc_name "$svc")
  BODY='<?xml version="1.0"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body><u:GetStatusInfo xmlns:u="urn:schemas-upnp-org:service:'"$NAME"':1"/></s:Body></s:Envelope>'
  curl -s -X POST "http://$P/ctl/$svc" \
    -H 'Content-Type: text/xml; charset="utf-8"' \
    -H "SOAPACTION: \"urn:schemas-upnp-org:service:$NAME:1#GetStatusInfo\"" \
    -d "$BODY" > "$OUT/post-$svc.txt"
  curl -s -X M-POST "http://$P/ctl/$svc" \
    -H 'MAN: "http://schemas.xmlsoap.org/soap/envelope/";ns=01' \
    -H 'Content-Type: text/xml; charset="utf-8"' \
    -H "01-SOAPACTION: \"urn:schemas-upnp-org:service:$NAME:1#GetStatusInfo\"" \
    -d "$BODY" > "$OUT/mpost-$svc.txt"
  if cmp -s "$OUT/post-$svc.txt" "$OUT/mpost-$svc.txt"; then
    echo "M-POST parity $NAME: IDENTICAL" | tee -a "$OUT/parity.txt"
  else
    echo "M-POST parity $NAME: DIFFER" | tee -a "$OUT/parity.txt"
  fi
done

echo "== GENA: subscribe/renew/unsubscribe with a callback catcher =="
lxc-attach -n dslp-probe -- sh -c 'cat > /tmp/gena-catcher.py' < /tmp/gena-catcher.py
lxc-attach -n dslp-probe -- sh -c 'nohup python3 -u /tmp/gena-catcher.py '"$CB_PORT"' >/tmp/gena-catcher.log 2>&1 & echo $! > /tmp/gena-catcher.pid; sleep 1'
lxc-attach -n dslp-probe -- sh -c '
SID=$(curl -s -D - -o /dev/null -X SUBSCRIBE "http://'"$P"'/ctl/IPConn" \
  -H "CALLBACK: <http://'"$PROBE_IP"':'"$CB_PORT"'/evt>" \
  -H "NT: upnp:event" -H "TIMEOUT: Second-120" | grep -i "^SID:" | tr -d "\r" | cut -d" " -f2)
echo "$SID" > /tmp/gena-sid.txt
sleep 2
curl -s -D - -o /dev/null -X SUBSCRIBE "http://'"$P"'/ctl/IPConn" -H "SID: $SID" -H "TIMEOUT: Second-300" | head -1 > /tmp/gena-renew.txt
curl -s -o /dev/null -X UNSUBSCRIBE "http://'"$P"'/ctl/IPConn" -H "SID: $SID"
'
echo "-- subscribe response --"
cat /tmp/gena-sid.txt 2>/dev/null | tee "$OUT/gena-sid.txt"
echo "-- renewal response --"
cat /tmp/gena-renew.txt 2>/dev/null | tee "$OUT/gena-renew.txt"
echo "-- catcher log (initial NOTIFY with SEQ 0) --"
sleep 2
lxc-attach -n dslp-probe -- cat /tmp/gena-catcher.log 2>/dev/null | tee "$OUT/gena-catcher.log"
lxc-attach -n dslp-probe -- sh -c 'kill $(cat /tmp/gena-catcher.pid 2>/dev/null) 2>/dev/null'

echo "== stop capture =="
kill "$CAP_PID" 2>/dev/null
sleep 1
ls -la "$OUT"
echo "== done =="