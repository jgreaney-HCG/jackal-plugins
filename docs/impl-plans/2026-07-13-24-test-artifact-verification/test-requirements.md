# Test Requirements — JKL-24 (R8: Test-artifact verification)

This issue writes downstream-facing GUIDANCE TEXT into agent files; it adds no repo-specific test
tooling. The jackal-plugins suite is text/structural only:
`bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`.
There is no pytest here, so ACs are verified by structural checks (frontmatter/version-sync/trace-deps),
targeted content greps, and manual read-through — plus one AC that is explicitly manual/observational
per the issue doc.

| AC | Phase | Verified by | Manual? |
|----|-------|-------------|---------|
| **AC1** — Reviewer + implementor text describes the artifact-based protocol: implementor emits a per-phase worktree-local artifact; per-phase review does targeted touched-area re-runs + artifact verification; full independent suite reserved for deep/final review. | 1 (implementor half), 2 (reviewer half) | `check-frontmatter.py` (frontmatter valid); `Grep` in `implementor.md` for `phase-<N>-report.xml`; `Grep` in `reviewer.md`/`reviewer-deep.md` for touched-area re-run + full-suite-at-deep wording; manual read-through. | Read-through only (no executable test). |
| **AC2** — Text explicitly states review NEVER accepts an artifact without its own independent verification (verify-don't-trust preserved). | 2 | Manual read-through of `reviewer.md` and `reviewer-deep.md` confirming the explicit "never accepts the artifact in place of its own verification" statement and the reworded "Never trust reports — or test-report artifacts" Rules line; `Grep` for `test-report artifacts` in both. | Read-through only. |
| **AC3** — Artifact format + location decision (worktree-local, junitxml example, format-agnostic) documented in the text. | 1 (primary), 2 (referenced) | `Grep` in `implementor.md` for `.jackal/phase-<N>-report.xml`, `junitxml`, `gitignored`, `format-agnostic`/`format is up to`; manual confirm not-committed language present; reviewer text references the same artifact location. | Read-through only. |
| **AC4** — (MANUAL/OBSERVATIONAL) In a downstream cycle, per-phase reviews run targeted subsets + artifact checks rather than full suites; full suite only at deep/final review. | 1+2 (behavior described) | Observe a real downstream execute cycle after these agents are in use: per-phase `reviewer` dispatches re-run touched-area tests + artifact, `reviewer-deep` runs the full suite. Not verifiable in this repo's CI. | **Yes — manual/observational**, per issue doc. Cannot be CI-gated; the plugins repo's own suite is trivial so it does not exercise the downstream path. |
| **AC5** — Version + marketplace.json + CHANGELOG sync for any plugin whose version bumps. | 3 | `python3 scripts/check-version-sync.py` (enforces plugin.json ↔ marketplace.json agree at 3.6.0); manual confirm CHANGELOG top entry describes #24/R8 only and top-level marketplace version stays 4.0.0. | version-sync is automated; CHANGELOG content is manual read-through. |

## Invariant checks (all phases)

- `disallowedTools: Agent` remains in `implementor.md`, `reviewer.md`, `reviewer-deep.md` — verify by
  `Grep` after each phase. No worker is granted `Agent`.
- `git diff --name-only $BASE_SHA...HEAD` must NOT include
  `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` (Phase 2 avoids it; keeps #24 diff clean).
- Full TEST_CMD passes after every phase (each phase is independently green).
