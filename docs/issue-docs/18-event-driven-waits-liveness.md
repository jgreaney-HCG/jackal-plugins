# JKL-18: R1+R2 — Event-driven waits + subagent liveness contract

**Status:** In Progress
**Complexity:** Complex
**Part of:** #17 (Director-Loop Hardening)

## Summary

Replace sleep-polling in the director loop with event-driven waits backed by a deterministic
background watcher, and give long-running subagents a liveness contract so the loop (not the human)
detects stalls. R1 and R2 are one issue because they share the watcher/signal-file mechanism. This is
the linchpin of the hardening epic and the largest cost saving (transcript-verified: 93 sleep-poll
commands / ~166 min in the audited session — if anything larger than the design doc's 85/~156).

Design reference: `docs/design-plans/director-loop-hardening-design.md` (R1, R2).

## Acceptance Criteria

- [ ] AC1.1 (MANUAL/OBSERVATIONAL — not CI): a full Complex-issue cycle completes with zero foreground sleep-poll turns in the director transcript.
- [ ] AC1.2: no Bash tool-timeout (exit 143) errors from scheduled sleeps; the sleep<timeout hard rule is encoded in the execute skill text.
- [ ] AC1.3 (MANUAL/OBSERVATIONAL — not CI): director wait-attributable turns per issue drop >=50% vs the GL-488 baseline.
- [ ] AC2.1: the dispatch template for supervisor/implementor agents contains the honest-stopping-point clause verbatim, in the agent-definition/skill files (applies to every dispatch, not per-message).
- [ ] AC2.2 (MANUAL/OBSERVATIONAL — not CI): a deliberately-stalled test agent produces a STALLED notification and director recovery without human prompting.
- [ ] AC2.3: the execute/director skill text codifies that no director message to the human asserts subagent progress not backed by a same-turn on-disk observation.
- [ ] Watcher pattern (wake-on-state-change, background bash, signal file -> task-notification) is documented in the execute skill and, where director-side, in the director-loop skill.
- [ ] Stall-response procedure (verify disk state -> instruct commit-and-report -> resume from disk if unrecoverable) added to the execute skill.
- [ ] Any plugin version bumped also updates .claude-plugin/marketplace.json and CHANGELOG.md.

## Scope

**In scope:**
- `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` (wait mechanism, sleep<timeout rule, stall-response procedure, batched status)
- `plugins/jackal-director/skills/director-loop/SKILL.md` (director-side watcher/stall procedure)
- `plugins/jackal-supervisor/agents/jackal-supervisor.md` and `plugins/jackal-plan-and-execute/agents/implementor.md` (honest-stopping-point clause + heartbeat/EXPECT expectation)
- version + marketplace.json + CHANGELOG.md sync for any plugin touched

**Out of scope:** application code (none in this repo); model tiering (R4 → #22); topology policy (R3 → #19); memory-to-skill migration (R6 → #21, which consumes this issue's honest-stopping-point + sleep-rule outputs).

## Module

plan-and-execute + director + supervisor (cross-plugin)

## Dependencies

- Blocked by: None
- Blocks: #21 (R6 — honest-stopping-point clause + sleep<timeout rule are outputs promoted by R6)
- Part of #17

## Technical Notes

- No-nesting rule: honest-stopping-point clause goes into worker agent prompts, but workers keep `disallowedTools: Agent` — do not grant Agent.
- The watcher is a background bash task whose completion generates a task-notification; the director's context is touched only on real state change. Reference watcher snippet is in the design doc R1.
- Do NOT weaken verify-don't-trust: disk-verification of teammate claims stays mandatory (design Non-goals).
- Route: Complex -> jackal-supervisor:jackal-design-plan (design skill first).

## Worktree

- branch: feat/18-event-driven-waits-liveness
- path: .worktrees/18-event-driven-waits-liveness
- created: 2026-07-12
