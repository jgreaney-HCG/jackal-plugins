# JKL-24: R8 — Test-artifact verification (cut redundant full-suite runs)

**Status:** In Progress
**Complexity:** Standard
**Part of:** #17 (Director-Loop Hardening)

## Summary

Reduce redundant full-suite runs across the plan-execute loop. The implementor emits a per-phase
test-report artifact; per-phase review does targeted re-runs of touched-area tests PLUS verification
of that artifact; only the deep/final review does one full independent suite run. Preserves
verify-don't-trust: review still verifies independently — it never trusts the artifact alone.

Design reference: `docs/design-plans/director-loop-hardening-adjacent-notes.md` (R8).

## Scope caveat (payoff is mostly downstream)

Originates from a mitch-GL ~2,240-test observation. In THIS repo the "suite" is just trace-deps +
version-sync + frontmatter (cheap), so payoff here is small. Primary beneficiaries are downstream
projects using these skills. Deliverable is reviewer/implementor SKILL.md + agent-prompt TEXT
describing artifact-based verification — NOT repo-specific test tooling. Do not build test infra here.

## DECISION (human, 2026-07-13): artifact format + location

**Worktree-local, `--junitxml` as a format-agnostic example.** The artifact is written uncommitted
into the worktree (e.g. `.jackal/phase-<N>-report.xml`, gitignored); it only needs to survive long
enough for the same-cycle per-phase review to verify it. NOT committed to the branch (avoids
diff/history pollution; squash-merge would erase it anyway). `--junitxml` is shown as the canonical
example, but the guidance is format-agnostic (JSON etc. fine).

## Acceptance Criteria

- [ ] Reviewer + implementor skill/agent text describes the artifact-based verification protocol: implementor emits a per-phase test-report artifact (worktree-local); per-phase review does targeted re-runs of touched-area tests + artifact verification; full independent suite run reserved for deep/final review.
- [ ] Text explicitly states review NEVER accepts an artifact without its own independent verification (verify-don't-trust preserved).
- [ ] The artifact format + location decision (worktree-local, junitxml example, format-agnostic) is documented in the skill text.
- [ ] (MANUAL/OBSERVATIONAL — not CI) In a downstream cycle, per-phase reviews run targeted subsets + artifact checks rather than full suites; full suite only at deep/final review.
- [ ] Version + marketplace.json + CHANGELOG.md sync for any plugin whose version bumps.

## Scope

**In scope:**
- `plugins/jackal-plan-and-execute/agents/reviewer.md` and/or `reviewer-deep.md` (artifact-verification protocol)
- `plugins/jackal-plan-and-execute/agents/implementor.md` (emit per-phase test-report artifact)
- possibly `plugins/jackal-plan-and-execute/skills/review/SKILL.md` (review routing text) — coordinate to avoid execute/SKILL.md conflicts
- version + marketplace.json + CHANGELOG.md sync

**Out of scope:** any repo-specific test tooling for jackal-plugins; #18 wait/liveness; #22 tiering; #19 topology; #25 phase-independence.

## Module

plan-and-execute

## Dependencies

- Blocked by: None. Branched off #25's tip — STACK: #22 → #19 → #25 → #24 merge in order.
- Part of #17

## Technical Notes

- No-nesting: reviewer/implementor stay `disallowedTools: Agent`; never grant Agent.
- Verify-don't-trust is a hard invariant — the artifact is an optimization, not a substitute for independent verification.
- Route: Standard -> jackal-supervisor:jackal-impl-plan.

## Worktree

- branch: feat/24-test-artifact-verification
- path: .worktrees/24-test-artifact-verification
- created: 2026-07-13
- base: feat/25-phase-independence (stack: #22 → #19 → #25 → #24)
