# The name's paths, measured

Measured on the router on 11 November 2026, from the workstation and from the box
itself, all read-only. The symptom as reported: browsers on LAN hosts that ask for
`router.d07yx58.net` reach an nginx 404 page instead of the router's interface, and
the name is said to point at an external IPv4.

## What each path answers for the name

| The path | The answer | What a browser on it gets |
| --- | --- | --- |
| dnsmasq on the router, port 53, asked from loopback and from the workstation (whose Windows resolver is 192.168.21.1) | 192.168.21.1, and fdd7:2524:58::1 | the interface, over the name's ACME certificate |
| unbound on the router, port 1053, asked directly | 84.203.115.61 | the api box's default block, a stock 404 |
| a public resolver (measured with 1.1.1.1 and the Digiweb resolver 83.147.160.2); a browser resolving for itself over DoH lands here | 84.203.115.61 | the api box's default block, a stock 404 |
| the uk group (firetv-uk, firetv-wifi-uk), whose port 53 the nft rules redirect to 192.168.44.1 | the VPN resolver's answer, the public one | the same 404 through the public record |
| the us group (androidtv-us, Lumia950), whose port 53 the nft rules redirect to 192.168.224.1 | the VPN resolver's answer, the public one | the same 404 through the public record |

The public zone is hosted at ClouDNS (pns21 through pns24) and maps the name, with
`api.d07yx58.net`, to 84.203.115.61, the static Digiweb IPv4 that pppoe-vdsl4 holds.

## Where the public answer lands

The redirect lives in `/etc/nftables.d/12-dslp-yarn.nft`, a persistent fw4 include,
not in UCI (which knows only the surface-rdp redirect):

```
ip daddr 84.203.115.61 tcp dport 443 dnat ip to 192.168.21.10
ip daddr 84.203.115.61 udp dport 443 dnat ip to 192.168.21.10
ip daddr 84.203.115.61 tcp dport 80 dnat ip to 192.168.21.10
ip daddr 84.203.115.61 udp dport 80 dnat ip to 192.168.21.10
```

with reflection that snats local sources to 192.168.21.1. The api box (192.168.21.10)
runs nginx with no server block for this name, so its default block answers: the
certificate it presents for the name is `CN = api.d07yx58.net` (Let's Encrypt, issued
26 October 2026), and the page at `/` is the stock nginx 404. Reproduced from the
workstation through the public record and from the router against 192.168.21.10 with
the name in the SNI.

## The router's own listener

The router's nginx holds 0.0.0.0:80 and 0.0.0.0:443 with two blocks that matter:
`_lan`, the default, and `router.d07yx58.net`, which carries the ACME certificate
from `/etc/acme/router.d07yx58.net_ecc` and the LuCI uwsgi locations. Both include
`restrict_locally`, which allows the private ranges 192.168.0.0/16 and 172.16.0.0/12
plus the local IPv6 ranges, and denies the rest. Asked with the name in the SNI at
192.168.21.1, the interface answers with the LuCI entry page over HTTP 200.

One curiosity measured with it: a connection the router itself opens to 84.203.115.61
bypasses the redirect (it never crosses the prerouting dnat) and lands on its own
nginx with a WAN source address, which `restrict_locally` denies, so it answers 403.
Harmless, and it says any proof of the fix has to come from a LAN vantage, not from
the box.

The certificate renews through acme.sh with `Le_Webroot='dns_cloudns'`, a DNS-01
validation, so renewal does not depend on the web ports.

## The defect

The router answers its name correctly, with a valid certificate, for every client
that asks its dnsmasq, and that covers most of the LAN. The paths that bypass dnsmasq
receive the public record: a browser that resolves for itself over DoH, the uk and us
media groups whose port 53 the nft rules send to the VPN resolvers, or anything
pointed at unbound's port 1053 (which holds no local zone although its UCI declares
`dhcp_link 'dnsmasq'`; `/var/lib/unbound/conf.d` is empty). The public record's web
ports belong to the api box, whose default block answers with a 404. Nothing inside
the router's DNS points anywhere wrong; the public half of the name's life is
incomplete.
