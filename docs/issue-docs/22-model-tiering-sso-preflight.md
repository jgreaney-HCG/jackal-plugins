# JKL-22: R4+R5 — Enforce explicit model tiering + SSO pre-flight + commit-early

**Status:** In Progress
**Complexity:** Standard
**Part of:** #17 (Director-Loop Hardening)

## Summary

Two paired, mostly-mechanical hardening items the design doc groups in rollout. R4: make every Agent
dispatch specify `model` explicitly (24 of 28 dispatches in the audited session had model=null) and
add a tier table. R5: add a credential-lifetime pre-flight before any >10-min dispatch and a
commit-early clause to the implementor prompt so credential expiry can't destroy uncommitted work.

Design reference: `docs/design-plans/director-loop-hardening-design.md` (R4, R5).

## Acceptance Criteria — R4

- [ ] Every `<invoke name="Agent">` dispatch block in the execute, plan, review, design, and finish skills carries an explicit `<parameter name="model">`. A model-unspecified dispatch is declared a defect in the skill text.
- [ ] Tier table added to the execute + jackal-supervisor skills: planner=Opus, implementor=Sonnet, reviewer=Sonnet, reviewer-deep=Opus, contract-sentinel=Sonnet, lexicon-warden=Sonnet, doc-render/research=Sonnet.
- [ ] AC4.1 (MANUAL/OBSERVATIONAL — not CI): zero model-unspecified dispatches in a full issue cycle.
- [ ] AC4.2: guidance to spot-check a Sonnet sentinel/warden verdict against a prior Opus baseline (GL-488 warden: 12 glossary terms) and to log any case where a Sonnet reviewer verdict is later contradicted (evidence to re-promote a tier).

## Acceptance Criteria — R5

- [ ] Credential pre-flight snippet (aws sts get-caller-identity + remaining-lifetime check where obtainable) added to the execute/supervisor skill, required before any dispatch expected to run >10 min; if remaining lifetime < task duration + margin, tell the human to re-auth BEFORE dispatching.
- [ ] Commit-early clause added to the implementor agent prompt: commit at every green intermediate state within a phase (WIP commits fine; squash-merge erases them).
- [ ] AC5.1 (MANUAL/OBSERVATIONAL — not CI): every >=10-min dispatch is preceded by a credential check in the transcript.
- [ ] AC5.2 (MANUAL/OBSERVATIONAL — not CI): an implementor phase touching >=3 files shows intermediate commits, not one end-of-phase commit.

## Acceptance Criteria — shared

- [ ] Version + marketplace.json + CHANGELOG.md sync for every plugin touched.

## Scope

**In scope:**
- `plugins/jackal-plan-and-execute/skills/execute/SKILL.md`, `.../plan/SKILL.md`, `.../review/SKILL.md`, `.../design/SKILL.md`, `.../finish/SKILL.md` (explicit model on each Agent dispatch)
- `plugins/jackal-supervisor/agents/jackal-supervisor.md` (tier table + dispatch-model rule + pre-flight)
- `plugins/jackal-plan-and-execute/agents/implementor.md` (commit-early clause)
- version + marketplace.json + CHANGELOG.md sync

**Out of scope:** the watcher/liveness mechanism (#18); topology (#19); memory-to-skill migration (#21).

## Module

plan-and-execute + supervisor

## Dependencies

- Blocked by: None
- Blocks: None
- Part of #17

## Technical Notes

- The SSO/AWS pre-flight is generic operational guidance in skill text; this plugins repo has no AWS creds of its own — the snippet is for the downstream projects the loop operates on.
- No-nesting rule intact; commit-early clause goes in the implementor prompt but the implementor keeps `disallowedTools: Agent`.
- Route: Standard -> jackal-supervisor:jackal-impl-plan.

## Worktree

- branch: feat/22-model-tiering-sso-preflight
- path: .worktrees/22-model-tiering-sso-preflight
- created: 2026-07-13
