# agentic-ds-lite-punch

The planning and investigation record for the **ds-lite-punch** project (code
lives in the sibling repo `slartibardfast/ds-lite-punch`). Moved here verbatim
from the rope-agentic monorepo — plain docs, no agentic-host template adoption.

- `plan/0004-ds-lite-punch/` — the milestone plan: CGNAT-aware UDP relay holding
  VM-line mappings alive via STUN, PCP/UPnP IGDv1 facades, observation rescue
  engine, phased acceptance and gates.
- `DSLITE.md` — the 800+ line possibility-space investigation of the Virgin
  Media ds-lite AFTR that fed the plan (ground truth: EIM+EIF, no PCP/UPnP on
  the AFTR, measured CGNAT timeouts).
- `call/0011-redesign-vm-line-57-pd.md` — the ADR that created the problem
  space: /57 delegation + DHCPv6-PD redesign, router-side ds-lite retired.