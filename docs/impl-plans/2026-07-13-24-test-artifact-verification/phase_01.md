# Phase 1: Implementor emits a per-phase test-report artifact

**Goal:** Add downstream-facing guidance to the implementor agent so it emits a worktree-local, gitignored per-phase test-report artifact as part of its verify/commit step.
**AC Coverage:** AC1 (implementor half), AC3 (format + location decision).

---

## Context

Before this phase, `plugins/jackal-plan-and-execute/agents/implementor.md` (on disk, v3.5.0) has a
"### 4. Verify" step that runs the project's test/build/lint commands and iterates until green, and
a "### 5. Commit" step. Nothing tells the implementor to persist a machine-readable record of the
test run.

This phase adds that: when the downstream project has a real test suite, the implementor writes a
per-phase test-report artifact to a worktree-local, gitignored path so the same-cycle per-phase
review can verify the run without re-executing the entire suite. This is **downstream guidance** —
this plugins repo's own suite (trace-deps + version-sync + frontmatter) is cheap and needs no
artifact, so the text must say the artifact is for downstream projects with real, expensive suites
and is skipped when the suite is trivial.

The decision is fixed by the issue doc (human, 2026-07-13): **worktree-local, `--junitxml` as a
format-agnostic example**, written uncommitted (e.g. `.jackal/phase-<N>-report.xml`, gitignored),
NOT committed to the branch.

## Implementation

### Implementor verify step — artifact emission

**Files:**
- Modify: `plugins/jackal-plan-and-execute/agents/implementor.md`

**What to implement:**

Extend the "### 4. Verify" section (currently ending after the Formatting paragraph, around lines
87–102) with a new subsection titled **"Per-phase test-report artifact (downstream projects)."** It
must state, in the implementor's own instructional voice:

1. **When it applies.** When the downstream project has a real, non-trivial test suite (the kind of
   suite where a full re-run is expensive — hundreds/thousands of tests), the implementor SHOULD
   write a machine-readable test-report artifact for the phase's test run. When the suite is trivial
   or cheap to re-run (like this plugins repo's own `trace-deps` / `version-sync` / `frontmatter`
   checks), skip the artifact — it buys nothing. Do not add or install test tooling solely to
   produce an artifact; only emit one if the project's existing test runner can produce it.

2. **Where it goes (location decision, verbatim intent).** Write it worktree-local and uncommitted,
   to a gitignored path — the canonical example is `.jackal/phase-<N>-report.xml` where `<N>` is the
   phase number. It is NOT committed to the branch: it only needs to survive long enough for the
   same-cycle per-phase review to read it; a squash-merge would erase it anyway, and committing it
   would pollute the diff/history. If `.jackal/` (or whatever path is used) is not already gitignored
   in the downstream repo, ensure it is ignored before writing, so the artifact never lands in a
   commit.

3. **What format (format-agnostic, junitxml example).** The format is up to the project's test
   runner — JUnit XML via `--junitxml` is the canonical example (`pytest --junitxml=.jackal/phase-<N>-report.xml`),
   but any machine-readable format the runner emits (JSON report, TAP, etc.) is fine. What matters is
   that it records, per the run: the pass/fail outcome, the count of tests, and enough identity
   (test ids / suite scope) that a reviewer can tell WHAT ran, not just that something ran.

4. **Relationship to the commit.** The artifact records the same green run that gates the commit
   (step 5). Because it is gitignored, it is not part of any commit; it is a side output of the
   verify step. If the implementor stops early (see "Honest stopping point"), the artifact reflects
   the last run it actually executed — never fabricate or hand-edit it.

Keep the prose tight and in the same register as the surrounding steps. Do not touch the
`disallowedTools: Agent` frontmatter, the no-subagents rule, or the report cap.

**Tests:**

No unit tests — this repo's suite is text/structural. Verification is:
- The frontmatter checker (`scripts/check-frontmatter.py`) still passes (frontmatter untouched and
  valid).
- Manual read-through confirms the new subsection states all four points above, names
  `.jackal/phase-<N>-report.xml` as the example path, says worktree-local + gitignored + not
  committed, says `--junitxml` is an example and the guidance is format-agnostic, and frames it as
  downstream-only (skipped for trivial suites).
- `disallowedTools: Agent` remains in the implementor frontmatter (grep confirms).

---

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`
Expected: all three pass. (version-sync passes here because Phase 3 does the bump; if run before
Phase 3, version-sync still passes since nothing changed versions yet.)

Also confirm manually:
- `Grep` for `disallowedTools: Agent` in `implementor.md` → still present.
- `Grep` for `phase-<N>-report.xml` and `junitxml` in `implementor.md` → present.

## Commit

`feat(plan-and-execute): implementor emits worktree-local per-phase test-report artifact`
