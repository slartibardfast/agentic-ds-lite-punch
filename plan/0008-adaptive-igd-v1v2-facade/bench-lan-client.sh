#!/bin/sh
# T4 bench, the LAN vantage. Runs ON the router, so its source address is
# br-lan (192.168.21.1) and the facade sees a same-LAN control point: the
# only vantage that can drive the mapping engine, because a mapping request
# must name an address in the LAN (containment, and the engine's own check).
#
# It creates one entry, reads it back, and (with "clean") deletes it. Usage:
#   sh bench-lan-client.sh create   # AddPortMapping + GetGeneric(0)
#   sh bench-lan-client.sh clean    # DeletePortMapping + GetGeneric(0)
set -e
BASE=http://192.168.21.1:49152
URN1=urn:schemas-upnp-org:service:WANIPConnection:1
EXT=${EXT:-34999}
INT=${INT:-34998}

soap() {
    action=$1; args=$2
    curl -s -m 8 -o /tmp/bench.out -w "%{http_code}" -X POST "$BASE/ctl/IPConn" \
        -H "SOAPACTION: \"$URN1#$action\"" -H 'Content-Type: text/xml; charset="utf-8"' \
        --data-binary "<?xml version=\"1.0\"?><s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"><s:Body><u:$action xmlns:u=\"$URN1\">$args</u:$action></s:Body></s:Envelope>"
    echo "  body: $(cat /tmp/bench.out)"
}

echo "== LAN vantage: source $(ip -4 -o addr show br-lan | awk '{print $4}') =="
case "$1" in
create)
    echo "-- AddPortMapping ext=$EXT int=$INT client=192.168.21.1"
    code=$(soap AddPortMapping "<NewRemoteHost></NewRemoteHost><NewExternalPort>$EXT</NewExternalPort><NewProtocol>UDP</NewProtocol><NewInternalPort>$INT</NewInternalPort><NewInternalClient>192.168.21.1</NewInternalClient><NewEnabled>1</NewEnabled><NewPortMappingDescription>bench-lan</NewPortMappingDescription><NewLeaseDuration>3600</NewLeaseDuration>")
    echo "  http=$code"
    echo "-- GetGenericPortMappingEntry index 0"
    code=$(soap GetGenericPortMappingEntry "<NewPortMappingIndex>0</NewPortMappingIndex>")
    echo "  http=$code"
    ;;
clean)
    echo "-- DeletePortMapping ext=$EXT"
    code=$(soap DeletePortMapping "<NewRemoteHost></NewRemoteHost><NewExternalPort>$EXT</NewExternalPort><NewProtocol>UDP</NewProtocol>")
    echo "  http=$code"
    echo "-- GetGenericPortMappingEntry index 0 (expect 714 after)"
    code=$(soap GetGenericPortMappingEntry "<NewPortMappingIndex>0</NewPortMappingIndex>")
    echo "  http=$code"
    ;;
*)
    echo "usage: $0 create|clean"; exit 2;;
esac