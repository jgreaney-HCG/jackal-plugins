# Test Requirements — JKL-22 (R4 + R5)

This repo has **no pytest suite**. The full test suite is the TEST_CMD:
`bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`
(mirrors `.github/workflows/ci.yml`). These are structural/lint gates, not behavioral unit
tests. Most ACs for this issue are documentation/prompt-text changes verified by grep and
by manual/observational review of a live issue cycle (the ACs themselves mark several as
MANUAL/OBSERVATIONAL — not CI).

## AC → Phase → Verification map

| Acceptance Criterion | Phase | Verified by | Manual? |
|---|---|---|---|
| R4: Every `<invoke name="Agent">` dispatch in execute/plan/review/design/finish carries explicit `<parameter name="model">`; model-unspecified dispatch declared a defect in skill text | 1 | `grep -rn 'name="Agent"'` = 5 blocks AND `grep -rn 'name="model"'` = 5 params across the five skills; defect-declaration text present (grep "defect") | Grep (structural), not CI-enforced |
| R4: Tier table added to execute + jackal-supervisor (planner=Opus, implementor=Sonnet, reviewer=Sonnet, reviewer-deep=Opus, contract-sentinel=Sonnet, lexicon-warden=Sonnet, doc-render/research=Sonnet) | 2 | Table present in both files; two copies identical; footnote records sentinel/warden frontmatter=haiku discrepancy | Manual (read both tables) |
| R4 AC4.1: zero model-unspecified dispatches in a full issue cycle | 1, 2 | Observational — inspect transcript of a real issue cycle; every dispatch shows a `model` param | MANUAL/OBSERVATIONAL (per AC) |
| R4 AC4.2: guidance to spot-check a Sonnet sentinel/warden verdict vs prior Opus baseline (GL-488: 12 terms) and log contradicted Sonnet reviewer verdicts | 2 | Verdict-spot-check subsection present under the tier table in execute skill | Manual (read) |
| R5: Credential pre-flight snippet (`aws sts get-caller-identity` + remaining-lifetime), required before any >10-min dispatch; re-auth-before-dispatch decision rule; if lifetime < duration+margin, tell human to re-auth first | 3 | Section present in execute skill AND jackal-supervisor; contains the bash snippet + decision rule; framed as downstream-AWS-only, not a gate on this repo | Manual (read) |
| R5: Commit-early clause in implementor prompt (commit at every green intermediate state; WIP fine; squash-merge erases them) | 3 | `grep "Commit early" plugins/jackal-plan-and-execute/agents/implementor.md`; clause complements (does not replace) the existing honest-stopping-point clause | Grep + manual |
| R5 AC5.1: every >=10-min dispatch preceded by a credential check in the transcript | 3 | Observational — inspect transcript of a real long-dispatch cycle | MANUAL/OBSERVATIONAL (per AC) |
| R5 AC5.2: an implementor phase touching >=3 files shows intermediate commits, not one end-of-phase commit | 3 | Observational — inspect `git log` of a real multi-file implementor phase | MANUAL/OBSERVATIONAL (per AC) |
| Shared: version + marketplace.json + CHANGELOG.md sync for every plugin touched | 4 | `python3 scripts/check-version-sync.py` prints "Version sync OK" (plugin.json == marketplace.json for both bumped plugins); both CHANGELOG entries present referencing #22 | CI-enforced (version-sync); CHANGELOG is convention/manual |

## Full-suite gate (run at the end of each phase)

```
bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py
```

- **Phases 1-3:** suite must stay green. No version bump yet, so `check-version-sync.py` passes on the unchanged (still-matching) versions. `check-frontmatter.py` passes because no frontmatter is edited (implementor keeps `disallowedTools: Agent` + `model: sonnet`; supervisor keeps `Agent` + `model: opus`).
- **Phase 4:** the bump lands; `check-version-sync.py` is the gate that confirms plugin.json/marketplace.json parity for 3.3.0 and 3.2.0.

## Invariants to re-verify before finish (not new tests, but must hold)

- Every worker agent still carries `disallowedTools: Agent` (implementor unchanged; no worker gained Agent).
- `jackal-supervisor` still carries `Agent` in its `tools:` list (sole orchestrator).
- Verify-don't-trust / honest-stopping-point / relay rules are unchanged (commit-early is additive, not a weakening).
- No director agent frontmatter was edited (contract-sentinel/lexicon-warden stay `model: haiku`; reconciliation is footnoted, deferred to a jackal-director follow-up).
