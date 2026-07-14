# Phase 1: Topology Policy in the execute skill

**Goal:** State flat topology (director → workers) as the default and require a written one-sentence justification before any middle supervisor tier is used, in `execute/SKILL.md`, cross-referencing R2's liveness contract for the stricter EXPECT windows.

**AC Coverage:**
- "Skill text states flat topology (director → workers) as the default; the GL-488 per-phase warm-context SendMessage pattern is named as the reference implementation."
- "A middle supervisor tier requires a one-sentence written justification in the Agent dispatch prompt (what the tier provides that flat dispatch + memory cannot)."
- "AC3.2: guidance requires any nested-supervisor dispatch to include the justification sentence."
- "When a middle tier IS used, R2's liveness contract applies with stricter (shorter) EXPECT windows — cross-reference it."
- "Reconciliation with CLAUDE.md's sole-orchestrator rule is written down explicitly in the changed skill text (flat-by-default + documented exception, per the decision above)."

---

## Context

This is a pure policy-text issue (issue #19 / R3 of the Director-Loop Hardening epic #17). There is
NO code, no pytest — the repo's test suite is the structural gate `TEST_CMD` (dependency trace,
version-sync between `plugin.json` and `marketplace.json`, frontmatter validity). Verification for
this phase is that the added prose satisfies each AC and the structural gate still passes.

**The decision is already made** (human, recorded in the issue doc §DECISION): flat-by-default +
documented exception. CLAUDE.md's "jackal-supervisor is the SOLE orchestrator tier" rule stays the
default. R3 adds the one-sentence-justification carve-out as the explicit, sanctioned exception. The
reconciliation is **written into the skill text** — CLAUDE.md itself is **NOT edited** (out of
scope). Do not plan or make any edit to CLAUDE.md.

**What already exists on disk** (this worktree is stacked on #22, so it already contains #18, #21,
and #22's merged/pending text — build on all of it; do not duplicate or restate it):
- `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` already contains:
  - The **"Subagent discipline"** block (workers never spawn workers) at lines ~14-16.
  - The **"Model discipline"** block and the **Model Tier Table** (from #22).
  - The **Named Continuation** section (lines ~156-249) — the cold-dispatch-then-`SendMessage`
    warm-context pattern, phase 1 cold / phases 2..N via `SendMessage`. **This is the GL-488
    per-phase warm-context SendMessage pattern.** It already exists; Phase 1 only needs to *name* it
    as the reference implementation for flat topology, not re-describe it.
  - The **"Waiting for async work"** section (lines ~527-563) — the R2 (#18) liveness contract: the
    watcher, the `EXPECT: commit a resumable checkpoint within <expect-seconds>` clause in the
    dispatch templates, and the `STALLED` verify-disk → commit-and-report → resume-from-disk
    procedure. **This is R2's liveness contract.** Cross-reference it; do NOT duplicate it.
- `docs/canon/` does **not** exist in this repo, so no impact statement is required.

CRITICAL invariants (do not violate, do not weaken):
- No new orchestrator agents.
- Do NOT grant the `Agent` tool to any worker. `jackal-supervisor` remains the sole `Agent` holder;
  workers keep `disallowedTools: Agent`.
- Never weaken verify-don't-trust (the relay rule / `verification-before-completion` posture).

## Implementation

### Topology Policy section in execute/SKILL.md

**Files:**
- Modify: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md`

**What to implement:**

Add one new top-level section titled **`## Orchestration Topology`**. Place it immediately after the
**`## Delegation Rules`** section and before **`## Model Tier Table`** (topology is a delegation-shaped
policy and belongs adjacent to the delegation rules; it must precede the Named Continuation section
it references so a reader meets the policy before the mechanism).

The section must state, in this order:

1. **Flat is the default.** The default orchestration shape is flat: the director/orchestrator
   dispatches worker agents (`implementor`, `reviewer`, `planner`, research) directly. There is no
   intermediate supervisor tier between the orchestrator and its workers by default.

2. **Name the reference implementation.** State explicitly that the **GL-488 per-phase warm-context
   `SendMessage` pattern** — the named-continuation mechanism documented in **"Implementor Dispatch:
   Named Continuation"** (Mode 1) — is the reference implementation of flat topology: a single named
   worker dispatched cold on phase 1 and resumed via `SendMessage` for phases 2..N, keeping context
   warm without a supervisor tier. Cross-reference that section by name; do not re-describe the
   mechanism.

3. **The middle-tier exception requires written justification.** A middle supervisor tier (an
   `Agent`-holding orchestrator dispatched *by* the orchestrator, i.e. a nested supervisor) is a
   deliberate exception, not a default. Before using one, the dispatching orchestrator MUST write a
   **one-sentence justification in the Agent dispatch prompt itself** stating **what that tier
   provides that flat dispatch + memory cannot** (e.g. genuinely independent multi-issue fan-out that
   exceeds what parallel named workers plus accumulated orchestrator memory can coordinate). A
   nested-supervisor dispatch **without** that justification sentence in the prompt is a **defect**,
   in the same sense the model-omission and unbacked-relay lapses are defects elsewhere in this
   skill — not a stylistic lapse. (This satisfies AC3.2: any nested-supervisor dispatch must carry
   the justification sentence.)

4. **When a middle tier IS used, R2's liveness contract applies with stricter windows.** Cross-
   reference the **"Waiting for async work"** section (R2 / #18) for the liveness mechanism (watcher,
   `EXPECT` checkpoint clause, `STALLED` recovery). State that a nested-supervisor dispatch uses a
   **stricter (shorter) `EXPECT` window** than a leaf worker dispatch, because a mistake in a middle
   tier compounds down to every worker it fans out to (the audited sweep session's nested Opus
   supervisor produced a wrong first deliverable and is where the "lost agent" stall arose), so it
   must prove liveness sooner. Do NOT duplicate the watcher/EXPECT/STALLED text — reference it.

5. **CLAUDE.md reconciliation (written here, not in CLAUDE.md).** Add an explicit note stating: the
   repo `CLAUDE.md` rule that **`jackal-supervisor` is the sole orchestrator tier** remains the
   default and is unchanged; this topology policy is the **documented exception** to it —
   flat-by-default, with the narrow, justification-gated nested-supervisor tier as the single
   sanctioned exception. State that the two documents **agree**: CLAUDE.md sets the default, this
   section defines the one narrow carve-out and its guard (the written justification). Explicitly
   note that no new orchestrator agent is introduced and no worker gains the `Agent` tool — the only
   `Agent`-holder remains `jackal-supervisor`.

Keep the section tight (roughly 12-20 lines of prose). Match the existing house voice in this file:
declarative, "defect"-framed guards, cross-references by section name rather than duplication. Use
glossary terms consistent with the rest of the file (orchestrator, worker, dispatch, `SendMessage`,
named continuation).

**Tests:**

No unit tests (documentation/policy change; repo has no pytest). Verification is:
- Structural gate passes (see Verification below) — the edit must not break frontmatter or introduce
  a dangling cross-reference.
- Manual AC check (recorded in `test-requirements.md`): the five ACs listed above are each satisfied
  by specific sentences in the new section — flat default stated; GL-488 named-continuation named as
  reference impl; one-sentence justification required in the dispatch prompt; stricter EXPECT window
  cross-referencing R2; CLAUDE.md reconciliation written into the skill text.

---

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`

Expected: exit 0 for all three (no DANGLING refs introduced by the new cross-references; version-sync
unaffected by this phase — versions bump in Phase 3; frontmatter unchanged and valid).

Additionally re-read the new `## Orchestration Topology` section and confirm each of the five ACs
above maps to explicit text.

## Commit

`docs(execute): flat topology default + justification-gated middle tier (#19)`
