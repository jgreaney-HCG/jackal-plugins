# Phase-Independence Classification Design (R9)

**Issue:** #25 (R9) · Part of Epic #17 (Director-Loop Hardening)
**Design ref:** `docs/design-plans/director-loop-hardening-adjacent-notes.md` (R9)
**Investigation:** `docs/design-plans/25-phase-independence-investigation-notes.md`

## Summary

Let the planner mark which phases are parallel-safe (`depends_on:` in the phase-file schema) and let
the execute skill fan out phases whose dependencies are all satisfied, instead of always running
phases strictly sequentially. Independent phases (tests, docs, plumbing) run concurrently; the
default with no `depends_on:` stays sequential (backward-compatible). All deliverables are
skill/agent **text** — no application code.

## Definition of Done

1. `depends_on:` field added to the phase-file schema (planner.md template + a schema note).
2. Execute skill documents dependency-aware fan-out: after a phase completes, dispatch any phase
   whose `depends_on:` set is fully satisfied; independent phases run in parallel.
3. Parallel phases use **Option A** dispatch (decided with the human): the trunk keeps warm context;
   independent leaf phases run as separate named cold agents (`implementor-<N>-pX`) on the same
   branch, non-merging transcripts — layered on the existing issue-level Parallel Dispatch model,
   not a new concurrency mechanism.
4. Backward compatibility: absent `depends_on:` ⇒ phase depends on all prior phases ⇒ sequential,
   exactly as today. No existing phase file breaks.
5. The watcher (from #18) runs per parallel phase stream where a phase is long-running; short leaf
   phases need no watcher. Cross-reference, don't duplicate.
6. Version + marketplace.json + CHANGELOG sync for jackal-plan-and-execute (the only plugin touched).
Success = text lands and CI (`trace-deps` + `check-version-sync` + `check-frontmatter`) stays green.
The actual parallel speedup is **manual/observational** — provable only in a live multi-phase cycle,
not in this repo's CI.

## Acceptance Criteria

### 25-phase-independence.AC1: Schema
- **AC1.1 Success:** planner.md's phase template documents an optional `depends_on: [phase_0N, ...]`
  field, with prose that absent ⇒ "depends on all prior phases" (sequential default).
- **AC1.2 Failure:** a phase file with a malformed `depends_on:` (e.g. naming a non-existent phase)
  is defined as a planner defect the execute skill must surface, not silently ignore.

### 25-phase-independence.AC2: Fan-out scheduling
- **AC2.1 Success:** execute/SKILL.md Mode 1 describes dependency-aware scheduling — maintain a set
  of completed phases; a phase is dispatchable when every id in its `depends_on:` is complete;
  dispatch all currently-dispatchable phases in parallel.
- **AC2.2 Success:** parallel phases use Option A (trunk warm; leaves cold `implementor-<N>-pX`; same
  branch; non-merging transcripts), explicitly building on the existing "Parallel Dispatch" section.
- **AC2.3 Failure/guard:** if all phases are sequential (no `depends_on:` anywhere), behavior is
  byte-for-byte the current named-continuation loop — no cold-start regression for the common case.

### 25-phase-independence.AC3: Safety + invariants
- **AC3.1 Success:** two parallel phases writing the same branch is called out; the review + verify
  posture is unchanged (each phase's work is still disk-verified). Merge/commit-ordering note included.
- **AC3.2 Success:** workers keep `disallowedTools: Agent`; no worker gains the Agent tool; the
  orchestrator (not the implementor) makes all fan-out decisions — no self-dispatch.
- **AC3.3 Success:** version bumped + marketplace + CHANGELOG synced; checks pass.

## Architecture

**Chosen: Option A + `depends_on:` schema (human-decided).**

```
Phase files carry:  depends_on: [phase_01]      (optional; absent ⇒ all-prior ⇒ sequential)

execute Mode 1 scheduler:
  completed = {}
  loop until all phases done:
    ready = { p : p not done AND depends_on(p) ⊆ completed }
    if |ready| == 1 → dispatch on the warm trunk agent (implementor-<N>) as today
    if |ready| > 1  → trunk keeps one; the rest dispatch as cold implementor-<N>-pX in parallel
                      (existing Parallel Dispatch model: separate named agents, same branch,
                       non-merging transcripts)
    await completions (watcher for long phases); move finished → completed
```

Why Option A over alternatives (from investigation):
- **Rejected — implementor self-dispatches sub-tasks:** would require the worker to hold the Agent
  tool → violates the no-nesting invariant. Hard no.
- **Rejected — one named agent, two concurrent conversations:** not possible; a named agent has one
  transcript.
- **Accepted tradeoff:** parallel leaf phases lose warm context (cold-start re-read). This is
  acceptable because independent phases are by definition leaf work (tests, docs, lint, plumbing)
  that don't consume a prior phase's in-context output — the design plan already told them what to do.

Same-branch writes: parallel phases commit to one branch HEAD. That's fine — commits are additive and
each phase's diff is disjoint by construction (independent phases touch different files). The watcher
fires on any commit; per-phase timeout attribution is **out of scope** (noted, not solved) since leaf
phases are short.

## Existing patterns (extend, don't duplicate)

- Phase template: `planner.md:56-99` — add `depends_on:` after `**AC Coverage:**`.
- Sequential loop: `execute/SKILL.md` Mode 1 "For each phase sequentially" — generalize to the
  dependency-aware scheduler; keep the sequential path as the `depends_on`-absent default.
- Parallel Dispatch (issue-level): `execute/SKILL.md` — R9 layers phase-level fan-out on this exact
  model (separate named agents, non-merging transcripts).
- Watcher: `execute/SKILL.md` "Waiting for async work" (from #18) — cross-reference for long phases.
- Topology (from #19, this stack): fan-out is still flat (orchestrator → parallel workers); no middle
  tier — consistent with the Orchestration Topology section.

## Implementation Phases

### Phase 1: `depends_on:` schema in the planner
**Goal:** add the optional `depends_on:` field + absent-⇒-sequential prose to planner.md's template;
define a malformed-`depends_on` as a planner defect.
**Components:** planner.md. **Done when:** AC1.1, AC1.2.

### Phase 2: dependency-aware fan-out in execute
**Goal:** generalize Mode 1's loop to the scheduler above; document Option A parallel dispatch on top
of the existing Parallel Dispatch section; preserve the sequential default byte-for-byte; cross-ref
the watcher and the #19 topology section.
**Components:** execute/SKILL.md. **Done when:** AC2.1, AC2.2, AC2.3, AC3.1, AC3.2.

### Phase 3: version + changelog sync
**Goal:** bump jackal-plan-and-execute (on-disk 3.4.0 in this stack → 3.5.0), mirror marketplace,
prepend an R9-only CHANGELOG entry.
**Components:** plugin.json, marketplace.json, CHANGELOG.md. **Done when:** AC3.3.

## Glossary

- **`depends_on:`** — optional phase-file field listing the phase ids that must complete before this
  phase may start. Absent ⇒ depends on all prior phases (sequential default).
- **Trunk / leaf phases** — the trunk is the warm named implementor carrying context from phase 1;
  leaves are independent phases dispatched cold in parallel.
- **Dispatchable** — a phase all of whose `depends_on:` ids are in the completed set.
