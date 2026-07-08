# #9 — Capability-relative Director framing + automated director-review path

**Status:** In Progress
**Design plan:** [docs/design-plans/2026-07-08-fable-free-tiering-and-efficiency.md](../design-plans/2026-07-08-fable-free-tiering-and-efficiency.md) (sections C1, C2)
**Epic:** Part of #8

## Summary

The Director loop is documented as review by "a stronger model" (Fable, in chat). In
environments where Fable chat access is unavailable, this reads as a hard dependency and
the "stronger" framing is stale. Reframe the Director in capability-relative terms
everywhere it's described, and add an automated `director-review` fallback path so the loop
runs end-to-end without any Fable session.

## Acceptance Criteria

- [ ] AC1: No skill, command, agent, or README in the marketplace assumes Fable
      availability; Director described as "a fresh-context reviewer on the strongest model
      available," Fable named only as the preferred option when present (C1).
- [ ] AC2: New Opus agent `jackal-director:director` (`agents/director.md`) exists with
      `disallowedTools: Agent`, tools limited to `Read`, restricted (by prompt + tool
      restriction) to `docs/canon/` and the packet file passed in its prompt — no Bash, Grep,
      or Glob (C2).
- [ ] AC3: New command `/jackal-director:director-review` (`commands/director-review.md`)
      runs `director-packet` if no fresh packet exists, dispatches the director agent,
      writes the memo to `docs/canon/packets/YYYY-MM-DD-memo.md`, and tells the human to run
      `/jackal-director:ingest-directive` (which keeps its existing confirmation gates) (C2).
- [ ] AC4: `director-loop` cadence section documents the fallback ladder: Fable chat
      (preferred) → other strong-model chat → `/jackal-director:director-review`.
- [ ] AC5: `jackal-director` version bumped in its `plugin.json`, mirrored in
      `.claude-plugin/marketplace.json`, with a `CHANGELOG.md` entry (repo convention).
- [ ] AC6: `/jackal-director:director-review` runs end-to-end against this repo's own
      packet and the memo ingests cleanly via `ingest-directive`.

## Scope

**In scope:** `plugins/jackal-director/skills/director-loop/SKILL.md`,
`plugins/jackal-director/commands/director-packet.md`,
`plugins/jackal-director/commands/ingest-directive.md`,
`plugins/jackal-director/commands/director-review.md` (new),
`plugins/jackal-director/agents/director.md` (new),
`plugins/jackal-director/README.md`,
`plugins/jackal-director/.claude-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `CHANGELOG.md`.
Root `README.md` update rides with whichever of #9 or #10 lands second (design doc Rollout
step 3) — do not duplicate it in both.

**Out of scope:** any change to `ingest-directive`'s human confirmation gates; execute/review
efficiency changes (tracked in #10).

## Module

director

## Complexity

Complex

## Dependencies

- Blocked by: None
- Blocks: None
- Part of #8

## Technical Notes

Full rationale, the no-Fable operating model table, and the exact reframing copy are in
the design plan, sections "C1" and "C2". Belt-and-braces note: frontmatter tool
restrictions have known enforcement gaps in some contexts, so the dispatch prompt must
repeat "no repo access by design" per repo convention on worker-agent prohibitions.

## Worktree

- branch: feat/9-director-fable-free-review-path
- path: .worktrees/9-director-fable-free-review-path
- created: 2026-07-08
