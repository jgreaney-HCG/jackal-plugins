# Phase 5: Version bump + marketplace.json + CHANGELOG sync

**Goal:** Bump the versions of every plugin whose files this issue changed, keep `plugin.json` and `marketplace.json` in lockstep (CI enforces), and add matching CHANGELOG entries.

**AC Coverage:**
- "AC6.1: ... versioned (jackal-supervisor >= 3.0.4, or equivalent bump from current 3.0.3)."
  **Note:** the issue text's "current 3.0.3" is stale — the actual current version on disk is **3.1.0** (verified in `plugins/jackal-supervisor/.claude-plugin/plugin.json`). The AC's intent is a version bump; bump from the true current version.
- "Version + marketplace.json + CHANGELOG.md sync for jackal-supervisor (and any other plugin touched)."

---

## Context

CI (`scripts/check-version-sync.py`) fails the build if any plugin's `plugin.json` version differs from its `marketplace.json` entry. Project CLAUDE.md additionally requires a CHANGELOG entry for every version bump. This phase is the release-metadata phase — run it last, after Phases 2-4 have made all content changes.

**Plugins touched by this issue (bump each):**
- **`jackal-supervisor`** — Phase 2 (merged-PR gate in `jackal-supervisor.md` + `jackal-sweep/SKILL.md`), Phase 4 (rule-of-thumb in `jackal-supervisor.md`). Current **3.1.0** → bump to **3.1.1** (patch: additive prompt/skill text, no breaking change).
- **`jackal-plan-and-execute`** — Phase 2 (merged-PR gate in `execute/SKILL.md`), Phase 3 (ruff-format in `implementor.md`). Current **3.2.0** → bump to **3.2.1** (patch: additive prompt text).

`jackal-director` is NOT touched by this issue — do not bump it.

Verified current versions (re-confirm before editing, in case a parallel branch changed them):
- `plugins/jackal-supervisor/.claude-plugin/plugin.json`: `3.1.0`
- `plugins/jackal-plan-and-execute/.claude-plugin/plugin.json`: `3.2.0`
- `.claude-plugin/marketplace.json`: supervisor `3.1.0` (line ~43), plan-and-execute `3.2.0`.

## Implementation

### A. Bump plugin.json versions

**Files:**
- Modify: `plugins/jackal-supervisor/.claude-plugin/plugin.json` — `"version": "3.1.0"` → `"3.1.1"`
- Modify: `plugins/jackal-plan-and-execute/.claude-plugin/plugin.json` — `"version": "3.2.0"` → `"3.2.1"`

If a re-read shows a different current version (parallel branch drift), bump the patch component of whatever is actually there and adjust the CHANGELOG entries to match — the invariant is "both files agree + CHANGELOG entry exists," not the specific number.

### B. Sync marketplace.json

**Files:**
- Modify: `.claude-plugin/marketplace.json`

Update the `version` field in the `jackal-supervisor` entry (→ `3.1.1`) and the `jackal-plan-and-execute` entry (→ `3.2.1`). These must exactly match the `plugin.json` values or `check-version-sync.py` fails.

### C. Add CHANGELOG entries

**Files:**
- Modify: `CHANGELOG.md`

Entries go at the **top** (newest-first), right after the `# Changelog` heading and above the existing `## [jackal-plan-and-execute] 3.2.0` entry. Add both:

```markdown
## [jackal-supervisor] 3.1.1

Promote operational lessons from director memory into shared skill/agent text (#21).

**New:**
- Merged-PR gate: `jackal-supervisor.md` "Reading the backlog" and Backlog Groom now cross-check every candidate OPEN issue against merged PRs (`gh pr list --state merged`) before ranking, routing delivered-but-open issues to a separate "stale-open — close these" list (prevents the GL-347 mis-ranking). `jackal-sweep` report surfaces the stale-open list and points to the gate.
- Rule of thumb: memory is for project facts/preferences; any lesson that changes agent procedure goes into the owning skill/agent definition the same session, memory cross-references it, and stale entries are superseded.

## [jackal-plan-and-execute] 3.2.1

Promote operational lessons into shared skill/agent text (#21).

**New:**
- `execute` skill Step 4 (backlog select): merged-PR gate drops candidates already delivered by a merged PR before priority ordering.
- `implementor.md` Verify step: run `ruff format`/`ruff check --fix` before committing when the project uses Ruff (conditional; no-op for non-ruff repos).
```

Keep entries concise; only the sections that apply (all are "New" here). Do not alter existing entries.

**Tests:**
`check-version-sync.py` is the real test for this phase — it passes only when all three files agree. No unit tests.

---

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`
Expected: `Version sync OK: N plugins checked.` and all other checks pass.

Confirm: `plugin.json`, `marketplace.json`, and `CHANGELOG.md` all reflect supervisor 3.1.1 and plan-and-execute 3.2.1; no other plugin versions changed.

## Commit

`chore: bump jackal-supervisor 3.1.1 + jackal-plan-and-execute 3.2.1 (#21), sync marketplace + changelog`
