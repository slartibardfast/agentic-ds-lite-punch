# The router's name on the LAN

**Status:** claimed 11 November 2026. The name's paths are measured, the household
vantage is named (iCloud Private Relay), and the fix shape is settled by the
measurement: republish the name's public record as its LAN address. The flip waits on
the operator's word, because the record is public state.

## What this milestone is

`router.d07yx58.net` must reach the router's interface from LAN hosts, on every
resolution path. The measurement ([the note](results/NOTE-2026-11-11-the-name-paths.md))
found the router answering its name correctly through dnsmasq, with the interface
served by nginx under a valid ACME certificate, while the paths that bypass dnsmasq
receive the public record 84.203.115.61: a browser that resolves for itself over DoH,
or the uk and us media groups whose port 53 the nft rules send to the VPN resolvers.
The public record's web ports are redirected, by a persistent fw4 include, to the api
box, whose nginx holds no block for the name; the default block answers with a stock
404, the page the household reported as nginx standing where the interface should be.

The vantage that reported the 404 is iCloud Private Relay, which resolves publicly and
also carries the connection through a third-party egress, so no rule keyed on the
connection's source can recognize the household member in it. Apple's relay is
documented to step aside for a name that is not a public internet name: the Overview
says a proxy or ODoH server that detects such a name instructs the device to try the
server directly over the local network. The fix is therefore the zone: republish
`router.d07yx58.net` (with its IDN sibling) as 192.168.21.1, which serves the
interface to every vantage at once, with dnsmasq's local zone unchanged.

## Build sequence

### Record the name's paths {#name-paths}

- verify: test -f results/NOTE-2026-11-11-the-name-paths.md
- inputs: results/NOTE-2026-11-11-the-name-paths.md

Done the day the milestone was claimed: every path's answer, where the public answer
lands (the api box's default block, with the api certificate and the stock 404), the
router's own two blocks with the ACME certificate, the ACME renewal's independence
from the web ports (DNS-01 through ClouDNS), the vantage curiosity (the router's own
connection to the public address is denied by `restrict_locally`, so proofs run from
a LAN host), and the relay vantage with the zone facts that settled the shape.

### Republish the name as its LAN address {#republish-the-record}

- depends: #name-paths
- verify: ssh root@192.168.21.1 'nslookup router.d07yx58.net 1.1.1.1 | grep -q 192.168.21.1'

The ClouDNS record for the name becomes 192.168.21.1 (it was 84.203.115.61), changed
through the same API the certificate renewal uses, and the IDN sibling (TTL 900)
flips with it; `yarn.d07yx58.net` and the api name keep the public address. Every
resolver path then lands on the interface:

- dnsmasq's local zone answers as before, unchanged.
- unbound's recursion and the uk and us groups' VPN resolvers now receive the LAN
  address, as does every browser DoH; each connects directly.
- A relayed Apple device is instructed to go direct (the Overview's rule), so the
  relay stops standing between the household member and the interface.
- Strangers stop finding the name at all; nothing outside used it (the interface
  answers them with 403 today).

The flip is one edit in public state, so the operator's word precedes it. The record's
TTL 3600 bounds how long a resolver may hold the old answer.

### Make the box's other resolver agree {#resolver-consistency}

- depends: #republish-the-record
- verify: ssh root@192.168.21.1 'nslookup router.d07yx58.net 127.0.0.1:1053 | grep -q 192.168.21.1'

unbound at port 1053 answered the name with the public record because it recursed and
the zone said so; after the flip its recursion lands on the LAN address once its cache
drains. The task records why `/var/lib/unbound/conf.d` is empty although the UCI
declares `dhcp_link 'dnsmasq'`, and whether unbound should hold the zone locally
anyway; the verify passes when its answer agrees with dnsmasq's.

### Prove it from the LAN {#lan-proof}

- depends: #republish-the-record
- verify: attested operator

The proof a household member would notice: an Apple device with Private Relay
enabled and a firetv of the uk group each load `https://router.d07yx58.net/` and
reach the interface with a valid certificate chain, each with its own DNS settings
untouched.

## The retired shapes and why

The first measurement suggested two shapes: a local-source exemption ahead of the api
box's dnat, or a name block on the api box proxying to the router. Both work for a
client that connects for itself, and the relay retires both, because a relayed
connection arrives from a third-party egress address that carries no mark of the
household. Teaching every bypassing resolver the local answer cannot work either,
because the zone's public half is served by ClouDNS and browsers can carry their own
resolver. The zone is the only lever every vantage must pass through, and Private
Relay is documented to step aside for a name whose record is not a public internet
address.
