# Test Requirements — #25 R9 Phase-Independence Classification

**Nature of this work:** all deliverables are skill/agent **text** in the `jackal-plan-and-execute`
plugin. This repo has **no pytest**. The CI/test suite (per Jackal Config `test_cmd`) is:

```
bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py
```

There are therefore **no per-AC unit tests**. Each behavioral AC is verified by (a) the mechanical
checks staying green and (b) a reviewer read against the AC text. The real parallel speedup is, as the
design states, **manual/observational** — provable only in a live multi-phase cycle, not in this
repo's CI.

## AC → Phase → Verification map

| AC | Phase | Verified by | Manual? |
|---|---|---|---|
| **AC1.1** planner.md template documents optional `depends_on:` + absent-⇒-sequential prose | Phase 1 | `check-frontmatter.py` green (frontmatter untouched) + reviewer read of `planner.md` phase template & schema note | Reviewer read (prose) |
| **AC1.2** malformed `depends_on:` defined as a planner defect the execute skill must surface | Phase 1 (definition) + Phase 2 (execute-side surfacing) | Reviewer confirms Phase 1 schema note declares it a defect AND Phase 2 scheduler validates + halts/reports (does not silently ignore or fall back to sequential) | Reviewer read (prose) |
| **AC2.1** execute Mode 1 describes dependency-aware scheduling (completed set; ready = `depends_on` ⊆ completed; dispatch all ready in parallel) | Phase 2 | Reviewer read of Mode 1 step 3 scheduler + `trace-deps`/`check-frontmatter` green | Reviewer read (prose) |
| **AC2.2** parallel phases use Option A (warm trunk; cold `implementor-<N>-pX` leaves; same branch; non-merging transcripts) built on the existing Parallel Dispatch section | Phase 2 | Reviewer confirms "Phase-level fan-out (Option A)" subsection + leaf dispatch template (model=sonnet, no-nesting line, same worktree) + cross-ref to Parallel Dispatch | Reviewer read (prose) |
| **AC2.3** no-`depends_on:` behavior is byte-for-byte the current named-continuation loop (no cold-start regression) | Phase 2 | Reviewer confirms the explicit "Sequential default is byte-for-byte preserved" guard sentence; scheduler reduces to single-ready trunk continuation | Reviewer read (prose) |
| **AC3.1** same-branch write safety called out; review + verify posture unchanged; merge/commit-ordering note | Phase 2 | Reviewer confirms "Same-branch write safety" note (disjoint-by-construction, additive commits, per-phase attribution out of scope) + explicit statement that verify-don't-trust / `verification-before-completion` is unchanged | Reviewer read (prose) |
| **AC3.2** workers keep `disallowedTools: Agent`; no worker gains Agent; orchestrator (not implementor) makes all fan-out decisions — no self-dispatch | Phase 1 (planner unchanged) + Phase 2 (execute statement) | Reviewer confirms leaf agents are `jackal-plan-and-execute:implementor` (Agent-denied), each dispatch template carries the "Do not dispatch or invoke any subagents" line, and the explicit orchestrator-dispatches / sole-supervisor-holder statement is present | Reviewer read (prose) |
| **AC3.3** version bumped + marketplace + CHANGELOG synced; checks pass | Phase 3 | `check-version-sync.py` reports jackal-plan-and-execute at 3.5.0 in sync (mechanical) + reviewer confirms R9-only CHANGELOG entry, no #22/#19 entries altered | Partly mechanical (`check-version-sync.py`), CHANGELOG scope is reviewer read |

## Design DoD items not tied to a numbered AC

| DoD item | Phase | Verification |
|---|---|---|
| Watcher runs per parallel phase stream for long phases; short leaves need none; cross-reference not duplicate (DoD #5) | Phase 2 (section D) | Reviewer confirms the watcher cross-reference to "Waiting for async work" with no duplication of the mechanism |
| Topology stays flat, consistent with #19 Orchestration Topology; not the nested-supervisor exception (design "Existing patterns") | Phase 2 (section E) | Reviewer confirms the flat-topology cross-reference |

## Full-suite gate (all phases)

After every phase, and before finish, the whole suite must be green:

```
bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py
```

- **Phase 1 & 2:** `check-version-sync.py` still passes on the pre-bump versions; `check-frontmatter.py`
  and `trace-deps.sh` pass (body-only text edits, no frontmatter or dependency-graph change).
- **Phase 3:** `check-version-sync.py` passes with jackal-plan-and-execute at 3.5.0.

## Manual / observational verification (cannot be automated in this repo)

- **Live fan-out speedup:** actual parallel execution of independent phases (and the trunk/leaf
  `implementor-<N>-pX` behavior) is provable only by running a real multi-phase plan that declares
  `depends_on:`. Out of scope for this repo's CI; note it for the first downstream project that
  authors a plan with independent phases.
- **Sequential no-regression:** confirmed by reading the guard sentence (AC2.3); a live confirmation
  would be running any existing `depends_on:`-free plan and observing identical named-continuation
  behavior.
