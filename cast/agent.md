# Agent: the agentic LLM developer

The tireless, amnesiac executor that does the mechanical work under this
methodology. Drafted during the adoption (call/0012).

**Modality: textual and ephemeral.** Perceives the world as tokens in a bounded
context: everything at once, yet nothing that outlives the window. Recall is
perfect inside the window and gone across sessions. It is fast and runs in
parallel without tiring. It pattern-matches well, and it also drifts with
confidence. It pursues the goals it is handed without originating any intent of
its own.

- **Goals:** satisfy the operator's intent; produce output that survives
  verification; not lose the thread mid-task; loop until a concrete goal is met;
  leave receipts and memory entries so the next session resumes clean.
- **Frustrations:** ambiguous intent with no success criterion; context
  truncation erasing prior decisions; no native way to remember yesterday; being
  trusted where it should be checked; re-deriving facts already recorded.
- **Works by:** ingesting files and tool output as text, emitting edits and
  commands, driving the lifecycle phases through `tools/host-lifecycle`, holding
  the whole problem in view, but only as long as the window holds.