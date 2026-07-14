# Phase 2: Sweep Guidance in the jackal-sweep skill

**Goal:** Direct backlog sweeps to run as direct director work OR a single Sonnet research dispatch — never a nested Opus supervisor — unless justified per the Phase 1 topology policy.

**AC Coverage:**
- "AC3.1: guidance directs backlog sweeps to run as direct director work or a single Sonnet research dispatch, not a nested Opus supervisor, unless justified."
- (Reinforces) "AC3.2: guidance requires any nested-supervisor dispatch to include the justification sentence." — the sweep cross-references the Phase 1 policy for the justification requirement.

---

## Context

Phase 1 established the topology policy in `execute/SKILL.md`. This phase applies it to the concrete
case the audit flagged: the sweep session that ran a **nested Opus supervisor** whose first
deliverable was wrong and where the "lost agent" stall arose. The sweep skill is where that mistake
happened, so the corrective guidance goes here.

**What already exists on disk** (`plugins/jackal-supervisor/skills/jackal-sweep/SKILL.md`):
- Steps 0-5: fetch/inventory, classify branches, reclaim merged/closed/gone worktrees, fast-forward
  main, rebase flags, report. It is branch/worktree hygiene work.
- A **"Stale-open issues"** callout at the end cross-referencing the Merged-PR gate.
- The skill today says nothing about *how* the sweep itself should be executed (flat vs nested) —
  that is the gap this phase closes.

Note: the sweep is invoked from `jackal-supervisor` (the sole `Agent`-holder). The point of AC3.1 is
that even the supervisor, when sweeping, should do the reclaim/hygiene work **directly** (it is git
plumbing) or fan out at most a **single Sonnet research dispatch** for any investigation — and must
NOT spin up a nested Opus supervisor to run the sweep. Preserve the invariant: no new orchestrator,
no worker gains `Agent`, `jackal-supervisor` stays the sole `Agent`-holder.

## Implementation

### Sweep execution-topology note in jackal-sweep/SKILL.md

**Files:**
- Modify: `plugins/jackal-supervisor/skills/jackal-sweep/SKILL.md`

**What to implement:**

Add a short subsection (or a bolded callout) titled **"How to run the sweep (flat)"** near the top of
the skill body — after the intro paragraph and the "Announce at start" line, before **`## Step 0`** —
so a reader sees the execution posture before the mechanics.

The note must state:

1. **Sweep runs flat.** The sweep is branch/worktree/git hygiene — do it as **direct director work**
   (the git commands in Steps 0-5 are run directly, not delegated to a nested tier).

2. **At most one Sonnet research dispatch.** If any part of the sweep needs investigation beyond the
   git plumbing (e.g. determining whether a delivered-but-open issue was truly closed by a merged
   PR), fan out **at most a single Sonnet research dispatch** (the `codebase-investigator` /
   research tier from the Model Tier Table — Sonnet). Do not chain multiple dispatches for it.

3. **Never a nested Opus supervisor — unless justified.** Explicitly forbid running the sweep under a
   **nested Opus supervisor tier**. State that this is the direct lesson of the audited sweep session
   (nested Opus supervisor → wrong first deliverable → "lost agent" stall). If a middle supervisor
   tier is genuinely needed for a sweep, it is the **justification-gated exception** — cross-reference
   the **`## Orchestration Topology`** section in the `execute` skill (added in Phase 1): the
   one-sentence written justification in the Agent dispatch prompt, plus the stricter R2 liveness
   `EXPECT` window, both apply. Reference it by name; do not restate the policy.

Keep it to ~6-10 lines. Match the file's voice (imperative, table-adjacent callouts, `>`-quoted
notes where it already uses them).

**Tests:**

No unit tests (policy/documentation; no pytest). Verification is:
- Structural gate passes (the cross-reference to the execute skill's Orchestration Topology section
  must not be a dangling plugin-qualified ref — it is a same-marketplace reference to a section, not
  a subagent/skill invocation, so `trace-deps.sh` is unaffected, but re-run to confirm).
- Manual AC check (in `test-requirements.md`): AC3.1 satisfied (sweep = direct work or single Sonnet
  research dispatch, not nested Opus, unless justified); AC3.2 reinforced (points at Phase 1's
  justification requirement).

---

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`

Expected: exit 0 for all three. Re-read the new sweep callout and confirm AC3.1 text is present and
it cross-references the Phase 1 topology policy.

## Commit

`docs(sweep): run sweeps flat — direct work or one Sonnet dispatch, not nested Opus (#19)`
