# The fold is installed and inert, and the lead is in the daemon's own log

Date: 2026-10-06. Task: `plan/0014#the-fold`. What the fold does, what it does not, and where the next
look goes.

## What is installed

The daemon installs the fold for each configured slot, from
[call/0047](../../call/0047-a-front-door-slot-folds-its-services-replies.md), and the box shows both
halves in place:

```
map ip dslp snat_map: elements = { 192.168.21.12 . 40003 : 192.168.0.21 . 40000 }
chain postrouting:    oifname "eth1" snat ip to ip saddr . udp sport map @snat_map
```

The service's answer still leaves unfolded, on a fresh flow, by the right line:

```
15:13:30.261080 br-lan In  IP 192.168.21.12.40003 > 170.9.238.141.8443: UDP, length 31
15:13:30.261094 eth1  Out IP 192.168.21.12.40003 > 170.9.238.141.8443: UDP, length 31
```

So the rule's match is satisfied (the source, the port, the interface all agree with the element) and
the statement does not fire. The egress rule the operator page names was added for the service and is
doing its part: without it the answer left by `pppoe-vdsl4`, and with it by `eth1`.

## The lead

The same run's log carries a daemon warning that names the mechanism:

```
warn: cdc(nft): list flow_obs failed: nft list set flow_obs -> exit status: 1
```

The datapath keeps a set the pins are read against, and reading it fails. A pin that the datapath
cannot see is a pin that never applies, which would leave exactly this picture: the element present,
the rule matching, and no translation. The next look goes there, at what maintains `flow_obs` and why
listing it fails, before any more of the fold is believed.

The run also showed two things worth keeping. A flow's NAT decision is cached in conntrack when the
flow is created, so a fold added afterwards does not reach an established flow, and the relay's own
poke acknowledgement keeps a service's flow warm indefinitely, which is why the service's port had to
move for a clean test. And the poke's dial on the TCP side fails with `Operation not permitted`, which
belongs with the TCP leg's task rather than this one.