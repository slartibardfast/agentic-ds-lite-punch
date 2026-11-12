# Client: the remote member of the household

The person who reaches the household's published service from outside the line.
Drafted 2026-11-12, in the discussion that scoped the front door's manual
([plan/0016](../plan/0016-the-carrier-environment/README.md)); the manual's client
half is written against this profile.

**Modality: intermittent and off-site.** Connects from outside the line on whatever
device is at hand: a household member's phone, the operator's roaming laptop, a
friend's borrowed one, an agent's scripted call. Holds one credential the operator
minted, and no access to the router or the front. Expects a name to work the way a
utility works: silently, until it stops.

- **Goals:** reach the household's published service by name from anywhere; carry
  one credential across every device they roam with; tell within a minute whether
  a failure belongs to their device or to the line.
- **Frustrations:** a certificate ceremony that differs per device; a hang whose
  cause is invisible from where they stand; a name that worked yesterday and
  stopped today; instructions that assume ssh access they do not hold.
- **Works by:** following one recipe end to end without improvising; verifying
  with one page load or one command; trusting the recipe over their own diagnosis;
  after two failed tries, stopping and reporting exactly what they saw, which is
  the input the operator's own pages need.

**Boundary:** the client learns the published names and holds a certificate. The
carrier's tuple and the two hosts behind the names stay out of view. The
passthrough name serves the service's own certificate; the protected name demands
theirs.
