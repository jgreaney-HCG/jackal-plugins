# JKL-21: R6 — Promote operational lessons from director memory into skill text

**Status:** In Progress
**Complexity:** Standard
**Part of:** #17 (Director-Loop Hardening)

## Summary

Migrate three corrective operational lessons out of director-private memory and into skill text —
the only substrate reliably shared with subagents. The GL-347 mis-ranking happened precisely because
the nested supervisor lacked a lesson the director's memory already implied. First VERIFY empirically
whether spawned agents even receive MEMORY.md; if not, treat memory as director-private and skills as
the sole cross-agent channel.

Design reference: `docs/design-plans/director-loop-hardening-design.md` (R6). #18 (merged) is the
canonical source for the honest-stopping-point clause and sleep<timeout rule this issue promotes —
reference that wording, do not re-author it divergently.

## Acceptance Criteria

- [ ] VERIFY step first: empirically confirm whether spawned agents receive the memory index; record the finding in the PR.
- [ ] Merged-PR gate migrated into the jackal-supervisor sweep procedure: for every candidate OPEN issue, run a merged-PR cross-check (e.g. `gh pr list --state merged --search '<#>'`) before ranking, and produce a separate stale-open-close-these list.
- [ ] Honest-stopping-point clause present in supervisor + implementor agent definitions (R2.1 output from #18 — reference, don't duplicate divergently).
- [ ] Sleep<timeout rule present in the execute skill (R1.3 output from #18).
- [ ] AC6.1: the three lessons appear in the corresponding plugin skill/agent files, versioned (jackal-supervisor bump from current 3.1.0).
- [ ] AC6.2 (MANUAL/OBSERVATIONAL — not CI): a fresh sweep on a repo with a known stale-open merged issue does not rank it, with no director-side correction.
- [ ] Rule-of-thumb text added: memory is for project facts/preferences; any lesson that changes AGENT PROCEDURE gets written into the owning skill in the same session, with the memory entry cross-referencing the skill change and stale entries superseded.
- [ ] ruff-format lesson (from adjacent-notes): add "run `uv run ruff format` before committing" to the implementor prompt (same migration logic as R6) — the ruff pre-commit rev must match uv.lock.
- [ ] Version + marketplace.json + CHANGELOG.md sync for jackal-supervisor (and any other plugin touched).

## Scope

**In scope:**
- `plugins/jackal-supervisor/skills/jackal-sweep/SKILL.md` (merged-PR gate)
- `plugins/jackal-supervisor/agents/jackal-supervisor.md` + `plugins/jackal-plan-and-execute/agents/implementor.md` (honest-stopping-point — reference #18 output; ruff-format line for implementor)
- `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` (sleep<timeout rule — reference #18)
- `plugins/jackal-supervisor/.claude-plugin/plugin.json` version bump + marketplace.json + CHANGELOG.md

**Out of scope:** designing the watcher/liveness mechanism (#18 owns it — R6 only promotes its text outputs); topology (#19); tiering (#22).

## Module

supervisor + plan-and-execute

## Dependencies

- Blocked by: #18 (MERGED — honest-stopping-point clause + sleep<timeout rule authored there)
- Blocks: None
- Part of #17

## Technical Notes

- #18 is merged into main, so this worktree already contains the canonical honest-stopping-point + sleep-rule text. R6 mostly ADDS the merged-PR sweep gate, the VERIFY finding, the rule-of-thumb text, and the ruff-format line — and confirms/cross-references the #18 outputs rather than re-authoring them.
- No-nesting rule intact; no Agent tool granted to workers.
- Route: Standard -> jackal-supervisor:jackal-impl-plan.

## Worktree

- branch: feat/21-promote-lessons-to-skills
- path: .worktrees/21-promote-lessons-to-skills
- created: 2026-07-12
