# The admission rules, so far

Date: 2026-10-06. Task: `plan/0014#admission-rules`. What the first passes establish, and the method
fix the later passes need.

## What is established

**A refused poke does not admit the peer.** With the poke aimed at a closed port on the vantage
(`170.9.238.141:9999`), the vantage answered every UDP poke with ICMP port-unreachable, and neither
arrival crossed:

```
11:09:40.775044 IP 192.168.0.21.40000 > 170.9.238.141.9999: UDP, length 9
11:09:40.905146 IP 170.9.238.141 > 192.168.0.21: ICMP 170.9.238.141 udp port 9999 unreachable

inbound to the TCP tuple 59214: 0 packets
inbound to the UDP tuple 59348: 0 packets
```

The TCP attempts, from the poke's own port and from another, both came back refused, and the UDP
datagrams were sent and vanished. So the carrier does not admit a peer whose poke drew a refusal,
whichever port the arrival uses. That is the rule the design needs, and it explains why the front's
poke has never taught it anything on this vantage: the port the daemon aims at is not forwarded by
the edge, so the poke draws nothing at all, and the front's socket never sees it.

## What the later passes need

The paired measurement, an *absorbed* poke with a matched and an unmatched arrival, needs a slot
whose live tuple is known at the moment of the attempt. The rig did not give one. The file
`/run/ds-lite-punch/tuple-40000` is empty while the log names `37.228.213.83:59348` for that slot,
`tuple-40002` does not exist for the slot the generic `tuple` file names, and stale slots from
earlier grants are still present. Aiming at a tuple read twenty minutes earlier, the first pass
measured nothing at all.

So the task gains a step ahead of its remaining measurements: leave the daemon with one slot per
protocol, read that slot's tuple immediately before the attempt, and read it again afterwards, so a
mapping that moves mid-test becomes visible instead of silently fatal. The rig was put back as it was
found after these passes: `POKE` at `170.9.238.141:41001`, and the captures stopped.