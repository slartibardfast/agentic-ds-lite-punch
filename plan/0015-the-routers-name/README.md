# The router's name on the LAN

**Status:** claimed 11 November 2026. The name's paths are measured and recorded; the
fix waits on the operator's choice between the two shapes the fork names.

## What this milestone is

`router.d07yx58.net` must reach the router's interface from LAN hosts, on every
resolution path. The measurement ([the note](results/NOTE-2026-11-11-the-name-paths.md))
found the router answering its name correctly through dnsmasq, with the interface
served by nginx under a valid ACME certificate, while the paths that bypass dnsmasq
receive the public record 84.203.115.61: a browser that resolves for itself over DoH,
or the uk and us media groups whose port 53 the nft rules send to the VPN resolvers.
The public record's web ports are redirected, by a persistent fw4 include, to the api
box, whose nginx has no block for the name; its default block answers with a stock
404, which is the page reported as browsers hitting nginx instead of the router's
interface.

The fix is to make the public record's port serve the interface for local sources, so
even a client that resolves the name publicly lands on its router. When the shape is
picked it gets its own decision record, as the fork below expects.

## Build sequence

### Record the name's paths {#name-paths}

- verify: test -f results/NOTE-2026-11-11-the-name-paths.md
- inputs: results/NOTE-2026-11-11-the-name-paths.md

Done the day the milestone was claimed: every path's answer, where the public answer
lands (the api box's default block, with the api certificate and the stock 404), the
router's own two blocks with the ACME certificate, the ACME renewal's independence
from the web ports (DNS-01 through ClouDNS), and the vantage curiosity: the router's
own connection to the public address is denied by `restrict_locally`, so proofs run
from a LAN host.

### Land the public record on the interface for local sources {#hairpin-lands}

- depends: #name-paths
- verify: curl -sk --max-time 8 --resolve router.d07yx58.net:443:84.203.115.61 https://router.d07yx58.net/ | grep -q cgi-bin/luci

The chosen shape makes a local-source connection to 84.203.115.61's web port reach
the router's interface instead of the api box's default block. The verify runs from a
LAN vantage (this workstation's public path crosses the box, as the note records),
and it passes when the public record's page is the LuCI entry whichever resolver the
client used.

### Make the box's other resolver agree {#resolver-consistency}

- depends: #name-paths
- verify: ssh root@192.168.21.1 'nslookup router.d07yx58.net 127.0.0.1:1053 2>/dev/null | grep -q 192.168.21.1'

unbound listens on every interface at port 1053 and answers the name with the public
record, because it holds no local zone: its UCI declares `dhcp_link 'dnsmasq'` yet
`/var/lib/unbound/conf.d` is empty. Either it serves the name locally (the verify
above) or it stops answering LAN clients at all; which one is the operator's word,
since nothing on the LAN is configured to use it.

### Prove it from the LAN {#lan-proof}

- depends: #hairpin-lands
- verify: attested operator

The proof a household member would notice: a phone on the wireless and a firetv of
the uk group each load `https://router.d07yx58.net/` and reach the interface with a
valid certificate chain, each with its own DNS settings untouched.

## The fork the plan cannot decide alone

Two shapes close the same defect, and both leave strangers on the page they get
today:

- The router keeps its web ports for local sources: a rule ahead of the dnat in the
  fw4 include sends local-source connections to the router's own nginx, which already
  serves the name with a valid certificate. The include
  (`/etc/nftables.d/12-dslp-yarn.nft`) is persistent, so the change persists with it.
  Nothing on the LAN is known to reach the api vhost through the public record
  (internal api clients resolve to 192.168.21.10 through dnsmasq), but a client that
  did, with a public resolver, would reach the router instead.
- The api box holds a block for the name: nginx on 192.168.21.10 gains a server block
  for `router.d07yx58.net` that proxies to the router's interface, restricted to
  local sources, with a certificate the box renews the way it renews the api one. The
  dnat stays untouched and the api name's public path is unchanged.

There is also a shape that fixes DNS alone, teaching every bypassing resolver the
local answer, and the measurement says it cannot work: the zone's public half is
served by ClouDNS, browsers can carry their own resolver, and the uk and us groups'
resolvers belong to the tunnel endpoints. Landing the public record on the interface
covers them all.
