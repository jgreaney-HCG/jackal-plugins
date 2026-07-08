# #10 — Execute efficiency: implementor continuation, Simple review, report-cap fix, routing carve-out

**Status:** In Progress
**Design plan:** [docs/design-plans/2026-07-08-fable-free-tiering-and-efficiency.md](../design-plans/2026-07-08-fable-free-tiering-and-efficiency.md) (sections C3-C6)
**Epic:** Part of #8

## Summary

Four dispatch efficiency/calibration gaps in jackal-plan-and-execute: stateless one-shot
implementors re-derive context on every phase (C3); Simple issues in backlog mode ship with
no machine review (C4); the reviewer's hard 40-line cap can silently drop Critical/Important
findings (C5); and the orchestrator's "never read the codebase" rule forces a subagent
dispatch even for a one-file routing peek (C6).

## Acceptance Criteria

- [ ] AC1: `execute` Mode 1 dispatches the implementor with a `name` on phase 1 and
      continues it via `SendMessage` for phases 2..N, with fallback to fresh dispatch when
      continuation fails, a review cycle found Critical issues, or
      `.jackal/harness-guidance.md` sets `implementor_continuation: off` (C3).
- [ ] AC2: Continuation scope is per-issue only — a new issue always gets a new
      implementor; parallel issues keep separate named agents; the reviewer is never
      continued (C3).
- [ ] AC3: `agents/implementor.md` acknowledges follow-up phases may arrive in the same
      session and treats each phase file as the complete spec for that phase (C3).
- [ ] AC4: Simple issues in backlog mode go implementor → `reviewer` (Sonnet) → finish by
      default; verdict feeds the existing fix loop (3 cycles then stop); overridable via
      `simple_review: off` in `.jackal/harness-guidance.md` (C4).
- [ ] AC5: `reviewer.md` and `reviewer-deep.md` report-cap rule changed so a Critical or
      Important finding can never be omitted to satisfy the length target; Minor findings may
      compress to one line or a count (C5).
- [ ] AC6: `execute/SKILL.md` Delegation Rules (and README) gain the single-named-file
      routing-read exception, scoped so it doesn't cover multi-file or search-driven reads
      (C6).
- [ ] AC7: `jackal-plan-and-execute` version bumped in its `plugin.json`, mirrored in
      `.claude-plugin/marketplace.json`, with a `CHANGELOG.md` entry (repo convention).
- [ ] AC8: One Standard issue run end-to-end with continuation on, confirming the phase-2
      dispatch shows cache reads rather than a cold context; one Simple issue run confirming
      the Sonnet review fires.

## Scope

**In scope:** `plugins/jackal-plan-and-execute/skills/execute/SKILL.md`,
`plugins/jackal-plan-and-execute/agents/implementor.md`,
`plugins/jackal-plan-and-execute/agents/reviewer.md`,
`plugins/jackal-plan-and-execute/agents/reviewer-deep.md`,
`plugins/jackal-plan-and-execute/README.md`,
`plugins/jackal-plan-and-execute/.claude-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `CHANGELOG.md`.
Root `README.md` update rides with whichever of #9 or #10 lands second (design doc Rollout
step 3) — #9 already merged without touching root README.md, so **this issue picks it up**.

**Out of scope:** Director loop changes (already shipped in #9); moving any worker off its
assigned model tier; effort-level tuning per agent; any change to the PR-only completion
path.

## Module

plan-and-execute

## Complexity

Complex

## Dependencies

- Blocked by: None
- Blocks: None
- Part of #8

## Technical Notes

Full rationale and exact copy for each change are in the design plan, sections "C3" through
"C6". Risk section flags C3 context-contamination (mitigated by the review-cycle reset +
kill-switch) and C4 cost creep on high-churn backlogs (mitigated by the guidance override).

AC8's live continuation/review verification has the same structural constraint #9's AC6 hit:
a worker/reviewer subagent has no Agent-tool access, so cache-read behavior on a continued
dispatch can only be observed by the orchestrator (main session) actually running a real
issue through Mode 1, not simulated by a worker. Plan for this to be verified by the
orchestrator directly, not delegated.

## Worktree

- branch: feat/10-execute-efficiency-continuation-review
- path: .worktrees/10-execute-efficiency-continuation-review
- created: 2026-07-08
