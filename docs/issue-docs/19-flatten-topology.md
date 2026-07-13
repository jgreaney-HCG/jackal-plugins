# JKL-19: R3 — Flatten orchestration topology; justify any middle tier

**Status:** In Progress
**Complexity:** Standard
**Part of:** #17 (Director-Loop Hardening)

## Summary

Make flat topology (director → worker agents) the default in the skills, and require a written
one-sentence justification at dispatch time before any middle supervisor tier is used. The audited
sweep session ran a nested Opus supervisor whose first deliverable was wrong and where the "lost
agent" stall arose. This issue is a policy statement in skill text.

Design reference: `docs/design-plans/director-loop-hardening-design.md` (R3).

## DECISION (resolved by human 2026-07-13)

**Flat-by-default + documented exception.** Keep CLAUDE.md's "jackal-supervisor is the SOLE
orchestrator tier" rule as the default; R3 adds the one-sentence-justification carve-out as the
explicit exception. This ALIGNS the two docs — it does NOT change CLAUDE.md wording. The skill text
states the reconciliation; CLAUDE.md is not edited (out of scope). If implementation reveals a need
to change CLAUDE.md's rule, STOP and surface it — do not edit it as routine work.

## Acceptance Criteria

- [ ] Skill text states flat topology (director → workers) as the default; the GL-488 per-phase warm-context SendMessage pattern is named as the reference implementation.
- [ ] A middle supervisor tier requires a one-sentence written justification in the Agent dispatch prompt (what the tier provides that flat dispatch + memory cannot).
- [ ] AC3.1: guidance directs backlog sweeps to run as direct director work or a single Sonnet research dispatch, not a nested Opus supervisor, unless justified.
- [ ] AC3.2: guidance requires any nested-supervisor dispatch to include the justification sentence.
- [ ] When a middle tier IS used, R2's liveness contract applies with stricter (shorter) EXPECT windows — cross-reference it.
- [ ] Reconciliation with CLAUDE.md's sole-orchestrator rule is written down explicitly in the changed skill text (flat-by-default + documented exception, per the decision above).
- [ ] Version + marketplace.json + CHANGELOG.md sync for any plugin touched.

## Scope

**In scope:**
- `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` and/or `plugins/jackal-director/skills/director-loop/SKILL.md` (topology policy)
- `plugins/jackal-supervisor/skills/jackal-sweep/SKILL.md` (sweep runs flat / single Sonnet research dispatch)
- version + marketplace.json + CHANGELOG.md sync

**Out of scope:** editing CLAUDE.md's sole-orchestrator rule (human decision if needed — not required by the chosen decision); the watcher/liveness mechanism itself (#18).

## Module

plan-and-execute + director + supervisor

## Dependencies

- Blocked by: None (references R2 from #18, merged). NOTE: branched off #22's tip because it shares execute/SKILL.md — #22 must merge before this PR (stack).
- Blocks: None
- Part of #17

## Technical Notes

- No new orchestrator agents. Do not grant the Agent tool to any worker.
- Route: Standard -> jackal-supervisor:jackal-impl-plan.

## Worktree

- branch: feat/19-flatten-topology
- path: .worktrees/19-flatten-topology
- created: 2026-07-13
- base: feat/22-model-tiering-sso-preflight (PR stack — #22 merges first)
