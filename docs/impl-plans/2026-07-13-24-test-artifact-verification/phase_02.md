# Phase 2: Reviewer artifact-verification protocol (verify-don't-trust preserved)

**Goal:** Teach the reviewer and reviewer-deep agents the artifact-based verification protocol — per-phase review does targeted re-runs of touched-area tests PLUS artifact verification, the full independent suite run is reserved for deep/final review, and review NEVER accepts the artifact without its own independent verification.
**AC Coverage:** AC1 (reviewer half), AC2 (verify-don't-trust explicit), AC3 (location decision referenced in review text).

---

## Context

Before this phase:
- `plugins/jackal-plan-and-execute/agents/reviewer.md` (Sonnet, per-phase + Simple/Standard default)
  has "### 1. Verify It Runs" which tells it to run the project test/build/lint commands wholesale.
- `plugins/jackal-plan-and-execute/agents/reviewer-deep.md` (Opus, final review of Complex /
  high-risk) has step "1. Verify it runs." doing the same.
- `plugins/jackal-plan-and-execute/skills/review/SKILL.md` routes to the tiers and describes when
  each is used. Per issue instructions, edit the AGENT files primarily; touch `review/SKILL.md` only
  minimally (one localized routing sentence), and do NOT touch `execute/SKILL.md` at all.

Phase 1 makes the implementor emit a per-phase artifact. This phase makes review consume it
correctly. The core distinction the text must draw:

- **Per-phase review (`reviewer`, Sonnet):** does NOT re-run the whole downstream suite. It (a)
  independently re-runs the tests covering the touched area (the tests exercising the files in the
  diff), and (b) verifies the per-phase artifact the implementor emitted. Both are the reviewer's
  own independent actions — the artifact is cross-checked, never trusted blind.
- **Deep / final review (`reviewer-deep`, Opus):** runs one full independent suite pass for the
  whole issue. This is where the single expensive full run lives.

**Hard invariant (AC2):** review NEVER accepts an artifact in place of its own verification. The
artifact is an optimization that tells the reviewer WHAT the implementor claims ran and lets it
scope its independent re-run intelligently; it is not a substitute for running tests. A reviewer
that reads the artifact and passes without independently executing the touched-area tests is
committing a verify-don't-trust violation.

## Implementation

### reviewer.md — targeted re-run + artifact verification

**Files:**
- Modify: `plugins/jackal-plan-and-execute/agents/reviewer.md`

**What to implement:**

Revise "### 1. Verify It Runs" so it distinguishes per-phase (this agent's job) from full-suite
(the deep reviewer's job), and folds in artifact verification. Keep the existing BLOCKED-on-failure
behavior. The revised section must state:

1. **Scope of this tier's run.** As the per-phase / Standard-default reviewer, independently re-run
   the tests that cover the touched area — the tests exercising the files in
   `git diff $BASE_SHA...$HEAD_SHA` — rather than the entire downstream suite. The full independent
   suite pass is the deep/final reviewer's responsibility (`reviewer-deep`), not this per-phase run.
   (For a cheap suite like this plugins repo's own, just run the whole thing — the targeting only
   matters when the full suite is expensive.)

2. **Artifact verification.** If the implementor emitted a per-phase test-report artifact
   (worktree-local, gitignored — canonical example `.jackal/phase-<N>-report.xml`, format-agnostic:
   JUnit XML / JSON / etc.), locate and inspect it: confirm it exists, that it records a passing run,
   and that what it claims ran is consistent with what the reviewer independently observed in step 1.
   A missing artifact where one was expected, an artifact showing failures, or an artifact whose
   claimed scope contradicts the reviewer's own run is a reason to dig in (and to return
   ISSUES_FOUND / BLOCKED as appropriate).

3. **Verify-don't-trust (state explicitly).** The reviewer NEVER accepts the artifact in place of
   its own verification. The artifact tells the reviewer what the implementor claims happened and
   lets it scope its independent re-run; it is never a substitute for actually running the
   touched-area tests. Passing a phase on the strength of the artifact alone, without an independent
   run, is a verify-don't-trust violation. Reword the existing "Never trust reports." rule (in the
   Rules section) to explicitly include the artifact: "Run verification commands yourself. Never
   trust reports — or test-report artifacts — as a substitute for your own run."

Keep the BLOCKED verdict block, the diff review steps, and everything downstream unchanged. Do not
touch `disallowedTools: Agent` or the no-subagents rule.

### reviewer-deep.md — full independent suite is the deep tier's job

**Files:**
- Modify: `plugins/jackal-plan-and-execute/agents/reviewer-deep.md`

**What to implement:**

Revise step "1. Verify it runs." to make explicit that the deep/final reviewer is where the ONE full
independent suite run happens (per-phase reviewers do targeted subsets). It must state:

1. As the deep/final reviewer, run the project's **full** test/build/lint suite independently — a
   complete pass over the whole issue's changes, not a touched-area subset. This is the single
   full-suite run the loop reserves for final review; the per-phase `reviewer` deliberately does not
   do it.
2. If per-phase artifacts exist, they may inform where to look, but the deep reviewer still runs the
   full suite itself and never accepts any artifact as a substitute for that run (verify-don't-trust
   applies with equal force at this tier). Add/adjust wording in its Rules section mirroring
   reviewer.md's "Never trust reports — or test-report artifacts — as a substitute for your own run."

Keep the BLOCKED-on-failure behavior, the deeper-dimensions list, and the frontmatter
(`model: opus`, `disallowedTools: Agent`) unchanged.

### review/SKILL.md — minimal routing note

**Files:**
- Modify: `plugins/jackal-plan-and-execute/skills/review/SKILL.md` (minimal, localized)

**What to implement:**

In the existing "## Choose the Tier" section, append at most one sentence to the `reviewer` bullet
and one to the `reviewer-deep` bullet clarifying the run-scope split, e.g.:
- `reviewer` bullet: "Per-phase reviews re-run only the touched-area tests plus verify the
  implementor's per-phase artifact — they do not re-run the full suite."
- `reviewer-deep` bullet: "The one full independent suite run is reserved for this tier's
  final/deep review."

Do NOT restructure the skill, do NOT add new sections, and do NOT touch `execute/SKILL.md`. Keep the
diff to these two bullet lines so #24's diff stays clean over the stacked #18/#22/#19/#25 edits.

**Tests:**

No unit tests — text/structural change. Verification:
- `scripts/check-frontmatter.py` passes (frontmatter of both agents untouched and valid).
- Manual read-through of `reviewer.md` and `reviewer-deep.md`:
  - reviewer says per-phase = touched-area re-run + artifact verification; full suite is deep tier's.
  - reviewer says explicitly it NEVER accepts the artifact without its own independent run
    (AC2), and its Rules line names test-report artifacts.
  - reviewer-deep says the one full independent suite run lives at the deep tier and still never
    trusts artifacts.
  - both reference the worktree-local / gitignored / format-agnostic artifact (AC3 in review text).
- `Grep` confirms `disallowedTools: Agent` still present in both agent files.
- `review/SKILL.md` diff is limited to the two bullet lines; `execute/SKILL.md` is unchanged
  (`git diff --name-only` must NOT list `skills/execute/SKILL.md`).

---

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`
Expected: all pass.

Also:
- `Grep` for `disallowedTools: Agent` in `reviewer.md` and `reviewer-deep.md` → present in both.
- `git diff --name-only $BASE_SHA...HEAD` → does NOT include
  `plugins/jackal-plan-and-execute/skills/execute/SKILL.md`.

## Commit

`feat(plan-and-execute): reviewers verify per-phase artifacts without trusting them; full suite reserved for deep review`
