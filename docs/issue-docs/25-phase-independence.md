# JKL-25: R9 — Phase-independence classification (parallel-safe phase fan-out)

**Status:** In Progress
**Complexity:** Complex
**Part of:** #17 (Director-Loop Hardening)

## Summary

Add a `depends_on:` field to the phase-file schema so the execute skill can fan out parallel-safe
phases instead of running them all serially. Independent phases (tests, docs, plumbing) run
concurrently; absent `depends_on:` stays sequential (backward-compatible).

Design: `docs/design-plans/2026-07-13-25-phase-independence.md`. Investigation:
`docs/design-plans/25-phase-independence-investigation-notes.md`.

## Decision (human, 2026-07-13)

**Option A + `depends_on:` schema.** Trunk keeps warm context; independent leaf phases run as
separate named cold agents (`implementor-<N>-pX`) on the same branch, non-merging transcripts —
layered on the existing issue-level Parallel Dispatch model. Not a new concurrency mechanism, and no
worker gains the Agent tool.

## Acceptance Criteria

See design doc for full AC list (25-phase-independence.AC1–AC3). Summary:
- [ ] `depends_on:` in planner.md phase template; absent ⇒ sequential; malformed ⇒ surfaced defect.
- [ ] execute/SKILL.md dependency-aware fan-out scheduler; Option A parallel dispatch; sequential default preserved byte-for-byte.
- [ ] Same-branch write safety noted; verify-don't-trust unchanged; workers keep `disallowedTools: Agent`; orchestrator makes fan-out decisions.
- [ ] Parallel speedup is MANUAL/OBSERVATIONAL (not CI).
- [ ] Version + marketplace.json + CHANGELOG sync (jackal-plan-and-execute).

## Scope

**In scope:**
- `plugins/jackal-plan-and-execute/agents/planner.md` (`depends_on:` schema)
- `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` (fan-out scheduler)
- version + marketplace.json + CHANGELOG.md sync

**Out of scope:** per-phase watcher timeout attribution (noted, not solved); the watcher mechanism itself (#18); topology policy (#19).

## Module

plan-and-execute

## Dependencies

- Blocked by: None (references #18 watcher + #19 topology, both in this stack). Branched off #19's tip — STACK: #22 → #19 → #25 merge in order.
- Part of #17

## Technical Notes

- No new orchestrator agents; no worker gains Agent tool.
- Route: Complex -> design (done) -> impl-plan -> execute.

## Worktree

- branch: feat/25-phase-independence
- path: .worktrees/25-phase-independence
- created: 2026-07-13
- base: feat/19-flatten-topology (stack: #22 → #19 → #25)
