# Test Requirements — JKL-19 (R3: Flatten orchestration topology)

This is a pure policy-text issue. The repo has **no pytest**; the automated suite is the structural
gate `TEST_CMD`:

```
bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py
```

That gate validates cross-reference integrity (no DANGLING refs), plugin.json↔marketplace.json
version agreement, and frontmatter validity. It does **not** verify prose meaning. Every acceptance
criterion below is therefore verified by (a) the structural gate staying green and (b) a manual
read-back of the changed skill text against the AC. No AC has a runnable unit test — this is expected
for a documentation/policy change.

| # | Acceptance Criterion | Phase | Verified by | Manual? |
|---|---|---|---|---|
| AC1 | Skill text states flat topology (director → workers) as the default; the GL-488 per-phase warm-context SendMessage pattern is named as the reference implementation. | 1 | Read-back of `execute/SKILL.md` `## Orchestration Topology` — flat-default sentence + GL-488 named-continuation named as reference impl. | Yes |
| AC2 | A middle supervisor tier requires a one-sentence written justification in the Agent dispatch prompt (what the tier provides that flat dispatch + memory cannot). | 1 | Read-back: the "defect if missing" justification-in-prompt clause in the topology section. | Yes |
| AC3.1 | Guidance directs backlog sweeps to run as direct director work or a single Sonnet research dispatch, not a nested Opus supervisor, unless justified. | 2 | Read-back of `jackal-sweep/SKILL.md` "How to run the sweep (flat)" callout. | Yes |
| AC3.2 | Guidance requires any nested-supervisor dispatch to include the justification sentence. | 1 (defined), 2 (reinforced) | Read-back: topology section states the justification-sentence requirement; sweep callout cross-references it. | Yes |
| AC4 | When a middle tier IS used, R2's liveness contract applies with stricter (shorter) EXPECT windows — cross-reference it. | 1 | Read-back: stricter-EXPECT clause cross-referencing the "Waiting for async work" (R2/#18) section; no duplication of watcher/STALLED text. | Yes |
| AC5 | Reconciliation with CLAUDE.md's sole-orchestrator rule is written down explicitly in the changed skill text (flat-by-default + documented exception). | 1 | Read-back: the CLAUDE.md-reconciliation note inside the topology section. Confirm CLAUDE.md itself is unchanged (`git diff -- CLAUDE.md` empty). | Yes |
| AC6 | Version + marketplace.json + CHANGELOG.md sync for any plugin touched. | 3 | `python3 scripts/check-version-sync.py` passes at plan-and-execute 3.4.0 / supervisor 3.3.0; CHANGELOG has two new R3-only entries; jackal-director unchanged at 1.4.0. | Partly (version-sync automated; CHANGELOG prose manual) |

## Invariant checks (must hold after all phases)

- No new orchestrator agents added (`git diff --stat` shows no new files under any `agents/`).
- No worker gains the `Agent` tool: `grep -rn 'disallowedTools' plugins/*/agents/` unchanged; only
  `jackal-supervisor.md` retains `Agent` in its `tools:` list.
- `CLAUDE.md` is not edited (`git diff origin/main -- CLAUDE.md` empty, allowing for the #22 stack
  base — confirm no R3-attributable change).
- Verify-don't-trust / relay-rule text is untouched (this issue only *cross-references* it).
