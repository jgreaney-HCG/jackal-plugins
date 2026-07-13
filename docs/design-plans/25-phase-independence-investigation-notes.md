# #25 (R9) Phase-Independence — Pre-Design Investigation Notes

Read-only investigation done ahead of #25's design phase (while #22 implements). Source of truth for
the design doc so it needn't re-investigate. Verify line numbers against current main before editing.

## Current state (verified)

- **Phase-file schema** (`planner.md:56–99`): fields are `# Phase N: [Title]`, `**Goal:**`,
  `**AC Coverage:**`, then Context / Implementation / Verification / Commit sections. **No**
  `depends_on:` or any dependency/parallel field today. Ordering is implicit in `phase_NN.md`
  numbering.
- **Execute loop** (`execute/SKILL.md` Mode 1, ~lines 74–101): "For each phase **sequentially**" via
  named-continuation — one `implementor-<ISSUE_NUMBER>`, resumed via `SendMessage` for phases 2..N,
  keeping context warm.
- **Existing Parallel Dispatch** (~lines 416–436): parallelizes independent **issues** (separate
  named implementors, separate worktrees, non-merging transcripts) — NOT phases within one issue.
- **Watcher** (from #18, ~lines 439–475): per-worktree, fires on NEW_COMMIT / STALLED. Not per-phase.
- **Plugin:** jackal-plan-and-execute, on-disk **3.2.1** (post #21).
- **Backward compat:** absent `depends_on:` must default to sequential; field is additive, no old
  phase file breaks.

## THE design decision R9 must resolve (framed, not solved)

Phase-level parallelism within one issue conflicts with the warm-context named-continuation model:
one named `implementor-<N>` cannot hold two concurrent conversations. Options surfaced:

- **A — per-phase named agents** (`implementor-<N>-p2`, `-p3`): consistent with the issue-level
  parallel pattern; but only the trunk/first phase keeps warm context, parallel leaf phases cold-start
  (lose prompt-cache/plan re-read). Likely acceptable because independent phases (tests, docs, lint)
  are usually leaf work that doesn't consume prior-phase output. The issue's own Technical Notes lean
  this way ("separate named implementors per parallel stream, non-merging transcripts").
- **B — implementor self-dispatches parallel sub-tasks**: reverses the "orchestrator decides
  parallelism" model AND would need the worker to hold the Agent tool → violates no-nesting. Reject.
- Same-branch/same-worktree writes: parallel phases share one branch HEAD; watcher can't attribute a
  commit to a specific phase. Fine for short leaf phases; note it, likely out of scope to fix per-phase
  timeout attribution.

**Recommendation to carry into design:** Option A, dependency-aware scheduling layered on the existing
issue-level parallel model. Keep the trunk warm; cold-start parallel leaves; default `depends_on:`
absent = sequential.

## Files for the design/plan
- `plugins/jackal-plan-and-execute/agents/planner.md` (phase template — add `depends_on:`)
- `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` (fan-out scheduling, Parallel Dispatch,
  watcher interaction)
