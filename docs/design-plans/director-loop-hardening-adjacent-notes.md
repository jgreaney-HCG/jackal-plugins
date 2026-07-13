# Director-Loop Hardening — Adjacent Notes (from the Fable audit)

Companion to `director-loop-hardening-design.md`. These items surfaced in the audit but were
**deliberately not specified to AC-level** in the design doc. Per the Fable agent's instruction,
they are **candidates to raise with the director — not scope any implementor may self-authorize.**

## Candidate R8 — Test-artifact verification (cuts redundant full-suite runs)

Today implementor, reviewer, and deep-reviewer each independently run the full ~2,240-test fast
suite per issue. Proposal:
- implementor commits the pytest report artifact (`--junitxml` or equivalent) with each phase;
- per-phase review does targeted re-runs of touched-area tests **plus** artifact verification;
- only the deep review does one full independent suite run.

Preserves the untrusted-claims posture (review still verifies), cuts 2–3 full suite executions per
issue. **Open decision:** artifact format and location (committed vs. worktree-local).
Complexity: Standard. Note: this is a mitch-GL-specific test-count observation; in *this* plugins
repo the "suite" is `scripts/trace-deps.sh` + version/frontmatter checks, so R8's value here is
smaller — its real home may be the mitch-GL project, not jackal-plugins. Flag when triaging.

## Candidate R9 — Phase-independence classification (free parallelism)

The planner doesn't mark whether phases are parallel-safe, so even independent phases run serially.
Proposal: add a `depends_on:` field to the phase-file schema; execute fans out phases with no unmet
dependencies. GL-488's phases were correctly serial (buys nothing there), but it's free speed on
issues with independent test/docs/plumbing phases. Complexity: Standard–Complex (touches planner
output schema + execute fan-out). Directly relevant to *this* repo's plan-and-execute plugin.

## Folds into #21 (R6) — ruff pre-commit rev drift

The ruff pre-commit rev must match `uv.lock` (a phase failed on `ruff-format: files were modified by
hook` in the audited session). Since R6 already migrates operational lessons into the implementor
prompt, add "run `uv run ruff format` before committing" there rather than leaving it memory-only.
Same migration logic as R6 → tracked as an addition to #21's scope, not a new issue.

## Standing caution (baked into #18 design as a reinforced non-goal)

Every item here and in the design doc trades mechanical cost for nothing else. If an implementation
choice would have the director accept any claim **without a disk-verified observation**, that choice
is wrong even if it's faster. When in doubt, keep the redundant check and flag the tension rather
than resolving it unilaterally. This mirrors the design doc's Non-goals and is being carried into
#18's design as an explicit guardrail.
