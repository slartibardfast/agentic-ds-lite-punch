# The line forwards a stranger's datagram to a held mapping

- Date: 2026-09-20
- Milestone: plan/0010 (the carrier's filtering, proved and watched), the task
  `#eif-now`
- Component: `ds-lite-punch`, pin `9b860c6`, binary on the router `ab0f9bd5`
- Ground truth: `MEMORY.md` entries of this date win where this file and a plan
  document disagree

## What was measured

A client inside the router's own `dslp-probe` container (`192.168.21.11`) asked
the daemon for a PCP mapping and then went silent. The daemon held the mapping.
The recorded vantage (`170.9.238.141`) then sent an unsolicited datagram to the
learned external tuple from a source the mapping had never spoken to, at four
windows of the client's silence.

This is the test the earlier records could not make. The 2026-09-18 acceptance
proved the mapping outlives its client's silence, and its prober was a host the
mapping's own flow was never aimed at, which is the same shape as this one. The
difference this time is the source tuple, named exactly, and the code state:
the read below is from the pin that carries today's README, with the
`collided()` fix and the accept-set datapath in it.

Two mappings were asked for, one at a time, each with a 600 s lifetime, on
internal ports 3074 and 3075 of the same client. The client was silent from its
MAP request onward. The daemon confirmed both slots:

```host-lint:ignore
{"event":"churn","detail":"slot 40001 confirmed 37.228.213.83:59323"}
{"event":"churn","detail":"slot 40002 confirmed 37.228.213.83:59292"}
```

Every probe sent was received at the router's WAN. The prober's address and
port, `170.9.238.141.54372`, were used for the four windows of the second
mapping, and the mapping's own flow had been toward `192.0.2.1:45678`.

```host-lint:ignore
1789905112.873698 IP 170.9.238.141.54372 > 192.168.0.21.40002: UDP, length 14
1789905139.073906 IP 170.9.238.141.54372 > 192.168.0.21.40002: UDP, length 14
1789905199.073132 IP 170.9.238.141.54372 > 192.168.0.21.40002: UDP, length 14
1789905379.073219 IP 170.9.238.141.54372 > 192.168.0.21.40002: UDP, length 14
```

The windows, and the send time each arrival answered, from the vantage's own
clock:

| window | sent | arrived on eth1 | lag |
|---|---|---|---|
| 30 s | `1789905112.801` | `1789905112.873698` | 0.073 s |
| 60 s | `1789905139.000` | `1789905139.073906` | 0.074 s |
| 120 s | `1789905199.000` | `1789905199.073132` | 0.073 s |
| 300 s | `1789905379.000` | `1789905379.073219` | 0.073 s |

The 30 s probe left 3.8 s late, because the schedule was armed after the lease
existed. The other three left on the second. Three further probes sent by hand
afterwards arrived as well:

```host-lint:ignore
1789905462.642428 IP 170.9.238.141.33712 > 192.168.0.21.40002: UDP, length 16
1789905507.507256 IP 170.9.238.141.40735 > 192.168.0.21.40002: UDP, length 16
1789905532.560484 IP 170.9.238.141.42531 > 192.168.0.21.40002: UDP, length 17
```

## What this settles

The AFTR's filtering is endpoint-independent today, at the windows that matter
for a client in a lobby: a datagram from an address and port the mapping never
used reached the router's WAN at thirty, sixty, one hundred and twenty, and
three hundred seconds of the client's silence. The design's first assumption
holds on this line, read from outside rather than inferred from inside.

## The trap, hit again

On eth1 the arrival's destination port is the router's own slot port
(`40002`), because the AFTR translates the destination back before the packet
reaches this router. A capture read by the CGNAT tuple finds nothing. The
2026-09-18 record says exactly this, and this run still lost a round to it: the
capture was searched for `59292`, the tuple the vantage sent to, and the
arrivals sat under `40002` the whole time. Read the capture by the slot port.

## The difference from the 2026-09-18 acceptance, and the defect it exposes

That run delivered every arrival to the client's own socket, which is the
stronger form of the evidence. This run did not. Three readings say so:

- the client's socket log ends at `HOLDING`, with no received datagram;
- the LAN capture holds no arrival for `192.168.21.11:3075`;
- `snat_map` is empty, while the accept set holds the two slot ports.

The daemon logged one error, at the moment the second lease was granted:

```host-lint:ignore
Sun Sep 20 11:51:18 2026 daemon.err ds-lite-punch[12490]: Error: Could not process rule: No such file or directory
Sun Sep 20 11:51:18 2026 daemon.err ds-lite-punch[12490]: delete element ip dslp snat_map { 192.168.21.11 . 3074 }
```

The reading that fits every observation: one client asking twice leaves the
datapath uninstalled. The second grant revokes the first, the revoke deletes an
element that is already gone, and the surviving lease's element is absent, so
an arrival reaches the port with nothing that maps it to the client's own
tuple. The 2026-09-18 acceptance asked for its two mappings one at a time, so
it never met this shape.

The defect is recorded, not dispositioned. A fix owes a failing test first, in
the shape `call/0022` fixed for the port label: one client, two internal ports.

## Method notes worth keeping

- **The policy rule needs its priority.** `ip rule add from 192.168.21.11
  lookup 1000` lands at the default priority, behind the firewall's mark rule
  at `30000`, and the flow then leaves by the wrong WAN. Written the way the
  console rules are written, with an explicit priority above `25000`, the flow
  leaves by `eth1` and the mirror sees it. This cost one round.
- **`pkill -f <script>.py` kills the caller.** The pattern matches the shell
  that carries the script's path in its own command line, twice in one session.
  The bracket form (`p[c]p-probe.py`) is what works.
- **`ash` has no brace expansion.** A staged-file removal written with braces
  silently removes nothing. Name the files.
- **The vantage needs root for a capture**, and `sudo -n` is available there.
  Its egress interface for the AFTR's address is `enp0s6`, and its own
  OpenVPN server's traffic crosses the same interface, so a capture filter on
  the destination host alone fills with that flow and misses the probe.

## Cleanup

The harness is gone: the ip rule, the allowlist entry, the client, the sink
listener and the captures. The two captures are kept at
`/mnt/nvme/captures/eif-2026-09-20/` with `sha256sums.txt`:

```host-lint:ignore
a8e8f69a4a281e0f9047da54a780f483aca32695df97fc1e2d83c2481e428f64  eif-lan.pcap
d5028f459e2c67830d2df4f98e890a7c7dc37fd489f5d34caea973bf0b52467b  eif.pcap
```

One capture on the router is not mine and was not touched: pids `14409` and
`24104`, a wrapper loop capturing `192.168.21.138` traffic. It predates this
work and the operator should decide its fate.

## Still open

- The lease datapath defect above wants a failing test first.
- The delivered-to-client form of today's measurement wants a single-lease
  repeat, which is the shape the 2026-09-18 file already carries.