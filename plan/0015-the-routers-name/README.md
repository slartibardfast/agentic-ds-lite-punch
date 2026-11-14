# The router's name on the LAN

**Status:** claimed 11 November 2026, and the fix landed the same day: the record is
republished (the router name alone; the IDN sibling is the explicitly-outside name
and keeps the public address, by the operator's word), unbound agrees through a
rebinding exception, and the LAN proof waits on the operator's devices.

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

- verify: test -f plan/0015-the-routers-name/results/NOTE-2026-11-11-the-name-paths.md
- inputs: plan/0015-the-routers-name/results/NOTE-2026-11-11-the-name-paths.md

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
through the same API the certificate renewal uses; `yarn.d07yx58.net` and the api
name keep the public address, and the IDN sibling keeps it too, by the operator's
word: it is explicitly the outside name. Every resolver path then lands on the
interface:

Done, 11 November 2026: the API edit (record id 480026278) answered Success, all
four authoritative nameservers serve the LAN address, and the public resolvers
(Cloudflare, Google, Quad9) followed within the hour the record's TTL 3600 bounds.
Strangers stop finding the name; `xn--um8h.d07yx58.net` still serves them the
public address, as it always did.

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
the zone said so; after the flip its recursion landed on the LAN address, which
unbound's own rebinding filter then stripped (an empty answer, the `private-address`
list with no exception for the zone). The remedy is the exception: a `server:` clause
in `/etc/unbound/unbound_ext.conf` carries `private-domain: "d07yx58.net."`, and
unbound answers the LAN address. Placing the line in `unbound_srv.conf` instead broke
the service start (no logged error, and the box carries no checkconf binary to ask);
that placement was reverted the same minute and the outage it caused, about two
minutes of dead upstream recursion on the LAN, was closed by the revert. The UCI's
`domain 'd07yx58.net'` does not reach the generated conf on this build; the ext conf
is the channel that works, and `/var/lib/unbound/conf.d` stays empty with the
generator's reason unestablished. The verify passes with dnsmasq's answer agreeing.

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
