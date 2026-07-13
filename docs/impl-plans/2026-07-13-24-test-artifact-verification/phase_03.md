# Phase 3: Version bump + marketplace + CHANGELOG sync

**Goal:** Bump `jackal-plan-and-execute` from 3.5.0 → 3.6.0 and sync `marketplace.json` + `CHANGELOG.md`, describing ONLY R8 (this issue), not the other stacked issues.
**AC Coverage:** AC5 (version + marketplace.json + CHANGELOG sync).

---

## Context

The repo CLAUDE.md requires that any plugin version bump be mirrored in
`.claude-plugin/marketplace.json` and get a `CHANGELOG.md` entry. Phases 1–2 changed
`jackal-plan-and-execute` agent text, so this plugin's version must bump.

On disk in this stacked worktree, `jackal-plan-and-execute` is at **3.5.0** (verified:
`plugins/jackal-plan-and-execute/.claude-plugin/plugin.json` and the matching entry in
`.claude-plugin/marketplace.json`). Bump to **3.6.0** (minor — new downstream-facing behavior, no
breaking change).

`scripts/check-version-sync.py` enforces that `plugin.json` and `marketplace.json` agree; the CI /
TEST_CMD runs it. The CHANGELOG entry must describe ONLY R8 (test-artifact verification) — the
stacked issues #22/#19/#25 already have their own entries at the top of the file and must not be
restated.

## Implementation

### plugin.json version bump

**Files:**
- Modify: `plugins/jackal-plan-and-execute/.claude-plugin/plugin.json`

**What to implement:**
Change `"version": "3.5.0"` → `"version": "3.6.0"`. Nothing else in the file changes.

### marketplace.json sync

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**What to implement:**
In the `jackal-plan-and-execute` plugin entry (the one with
`"source": "./plugins/jackal-plan-and-execute"`), change `"version": "3.5.0"` → `"version": "3.6.0"`.
Do NOT change any other plugin's version and do NOT change the top-level marketplace `version`
(`4.0.0`).

### CHANGELOG entry (R8 only)

**Files:**
- Modify: `CHANGELOG.md`

**What to implement:**
Insert a new entry immediately after the `# Changelog` heading (line 1), above the existing
`## [jackal-plan-and-execute] 3.5.0` entry. Describe ONLY R8. Use the repo's changelog format:

```markdown
## [jackal-plan-and-execute] 3.6.0

Test-artifact verification: cut redundant full-suite runs across the plan-execute loop (#24, R8).

**New:**
- `implementor` agent emits a per-phase test-report artifact for downstream projects with a real,
  expensive suite — worktree-local and gitignored (canonical example `.jackal/phase-<N>-report.xml`),
  never committed to the branch. Format-agnostic (`--junitxml` is the example; JSON/TAP fine). Skipped
  when the project's suite is trivial to re-run.
- `reviewer` per-phase reviews now re-run only the touched-area tests plus verify the implementor's
  per-phase artifact; the single full independent suite run is reserved for `reviewer-deep`'s
  final/deep review.

**Changed:**
- Verify-don't-trust is stated explicitly for artifacts: review NEVER accepts a test-report artifact
  in place of its own independent verification — the artifact is an optimization that scopes the
  reviewer's re-run, never a substitute for it. `reviewer` and `reviewer-deep` "never trust reports"
  rule now names test-report artifacts.
```

Do not alter existing changelog entries.

**Tests:**

- `python3 scripts/check-version-sync.py` passes (plugin.json and marketplace.json now agree at
  3.6.0).
- `python3 scripts/check-frontmatter.py` passes.
- `bash scripts/trace-deps.sh` passes.

---

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`
Expected: all pass — version-sync specifically confirms the 3.6.0 bump is mirrored.

Also confirm manually:
- `plugin.json` and the `jackal-plan-and-execute` marketplace entry both read `3.6.0`.
- Top-level marketplace `version` is still `4.0.0`; no other plugin version changed.
- The new CHANGELOG entry is at the top and mentions #24/R8 only.

## Commit

`chore(plan-and-execute): bump to 3.6.0 (test-artifact verification) + marketplace/changelog sync`
