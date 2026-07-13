# Test Requirements — #21 Promote operational lessons into skill text

This repo has **no pytest / unit-test suite**. The entire automated suite is:

```
bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py
```

(mirrors `.github/workflows/ci.yml`; `check-version-sync.py` enforces plugin.json↔marketplace.json;
`check-frontmatter.py` validates command/agent/skill frontmatter; `trace-deps.sh` checks dependency
references.) All changes here are prompt/skill/agent **text** — they are verified by the CI checks
staying green plus observational/manual confirmation. There is nothing to unit-test.

## AC → phase → verification map

| Acceptance Criterion | Phase | Verified by |
|---|---|---|
| VERIFY step first: empirically confirm whether spawned agents receive the memory index; record in PR | Phase 1 | `VERIFY-memory-propagation.md` (finding doc) + PR body records the finding. Empirical, not CI. |
| Merged-PR gate migrated into supervisor sweep procedure: cross-check every candidate OPEN issue before ranking; produce stale-open-close-these list | Phase 2 | Text present in `jackal-supervisor.md` ("Reading the backlog" gate + Groom item), `execute` SKILL Step 4, `jackal-sweep` report cross-ref. CI green. **Manual/observational** (AC6.2 below). |
| Honest-stopping-point clause present in supervisor + implementor agent definitions (reference #18, don't duplicate divergently) | Phase 1 (VERIFY) | Grep confirms present in `implementor.md`, `jackal-supervisor.md`, `execute` SKILL (from merged #18). Finding doc records locations. No re-authoring. |
| Sleep<timeout rule present in the execute skill (R1.3 from #18) | Phase 1 (VERIFY) | Grep confirms present in `execute` SKILL "Waiting for async work" (≤100s under 120s). Finding doc records location. |
| AC6.1: the three lessons appear in the corresponding plugin skill/agent files, versioned (jackal-supervisor ≥ bump from current) | Phases 2, 3, 4, 5 | Text present (Phases 2-4); versions bumped supervisor 3.1.0→3.1.1, plan-and-execute 3.2.0→3.2.1 (Phase 5). `check-version-sync.py` green. NB: issue's "3.0.3" baseline is stale; true current is 3.1.0. |
| AC6.2 (MANUAL/OBSERVATIONAL — not CI): a fresh sweep on a repo with a known stale-open merged issue does not rank it, with no director-side correction | Phase 2 | **Manual.** Cannot be unit-tested — it is emergent behavior of the orchestrator following the new prompt text. Verified by observing (or reasoning through) a backlog read on a repo with a delivered-but-open issue: the merged-PR gate lists it under "stale-open" and excludes it from ranking. Record the observation in the PR body. |
| Rule-of-thumb text added (memory=facts/prefs; procedure lessons→owning skill same session; memory cross-references; supersede stale) | Phase 4 | Text present in `jackal-supervisor.md` "Recording lessons: memory vs. skills". CI green. |
| Version + marketplace.json + CHANGELOG.md sync for jackal-supervisor (and any other plugin touched) | Phase 5 | `check-version-sync.py` passes (plugin.json↔marketplace.json); CHANGELOG entries present for both bumped plugins. |

## Manual / observational items (not covered by CI)

1. **VERIFY finding (Phase 1)** — empirical investigation; result recorded in `VERIFY-memory-propagation.md` and the PR body. Planner's finding: spawned agents do **not** receive the memory index (no plugin forwards it; it is a host-level main-conversation file). If a future harness behaves differently, record the actual result.
2. **AC6.2 stale-open non-ranking (Phase 2)** — behavioral; verified by observation/reasoning, recorded in the PR. Not automatable in this repo.

## Invariants to re-check before finish (CI + review)

- Every worker agent keeps `disallowedTools: Agent` and its "never dispatch subagents" rule (`implementor.md` frontmatter untouched in Phase 3). `check-frontmatter.py` guards frontmatter validity.
- `jackal-supervisor` keeps the `Agent` tool (it is the sole orchestrator) — Phases 2 and 4 edit its body only, never its `tools` frontmatter.
- Verify-don't-trust text is not weakened — Phases only ADD gates/notes; they must not remove or soften the existing relay rule, honest-stopping-point, or sleep<timeout text.
- All three of plugin.json / marketplace.json / CHANGELOG.md agree for every bumped plugin (Phase 5).
