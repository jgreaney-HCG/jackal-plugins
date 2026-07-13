# Phase 4: Version bump + marketplace + CHANGELOG sync

**Goal:** Bump the version of both touched plugins, sync `marketplace.json`, and add CHANGELOG entries — satisfying the shared AC and the CI version-sync gate.
**AC Coverage:** shared AC "Version + marketplace.json + CHANGELOG.md sync for every plugin touched."

---

## Context

Two plugins were modified in Phases 1-3:
- **jackal-plan-and-execute** — execute/plan/review/design/finish skills + implementor.md. Current version **3.2.1** (verified on disk).
- **jackal-supervisor** — jackal-supervisor.md. Current version **3.1.1** (verified on disk).

CLAUDE.md's "Version Updates Require Marketplace and Changelog Sync" convention requires all three files updated together. `scripts/check-version-sync.py` enforces plugin.json == marketplace.json (verified: it does NOT parse CHANGELOG prose), and CI runs it — so a version bump with mismatched marketplace.json fails CI. The CHANGELOG sync is a convention (not script-enforced) but is mandatory per CLAUDE.md.

These are additive skill/agent-text changes (new params, new sections, new prose) — no breaking behavior change. Bump the **minor** version for each: plan-and-execute 3.2.1 → **3.3.0**, supervisor 3.1.1 → **3.2.0**. (Minor, not patch: model-tier enforcement and the pre-flight/commit-early clauses are new features of the harness behavior, not bug fixes.)

Verified locations:
- `plugins/jackal-plan-and-execute/.claude-plugin/plugin.json` → `"version": "3.2.1"`
- `plugins/jackal-supervisor/.claude-plugin/plugin.json` → `"version": "3.1.1"`
- `.claude-plugin/marketplace.json` → `jackal-plan-and-execute` entry `"version": "3.2.1"` (around line 28), `jackal-supervisor` entry `"version": "3.1.1"` (around line 43). The marketplace top-level `"version": "4.0.0"` (line 4) is the marketplace's own version — do NOT change it.

## Implementation

### Bump plugin.json versions

**Files:**
- Modify: `plugins/jackal-plan-and-execute/.claude-plugin/plugin.json` — `"version": "3.2.1"` → `"3.3.0"`
- Modify: `plugins/jackal-supervisor/.claude-plugin/plugin.json` — `"version": "3.1.1"` → `"3.2.0"`

### Sync marketplace.json

**File:**
- Modify: `.claude-plugin/marketplace.json`

**What to implement:**

Update the two plugin entries' `version` fields to match the plugin.json bumps:
- `jackal-plan-and-execute` entry: `"version": "3.2.1"` → `"3.3.0"`
- `jackal-supervisor` entry: `"version": "3.1.1"` → `"3.2.0"`

Do not touch the top-level marketplace `"version": "4.0.0"` or any other plugin entry.

### Add CHANGELOG entries

**File:**
- Modify: `CHANGELOG.md`

**What to implement:**

Add two new entries at the **top** of the file, immediately after the `# Changelog` heading and before the current top entry (`## [jackal-supervisor] 3.1.1`). Newest first. Follow the existing entry format (heading `## [plugin-name] version`, one-line summary, `**New:**`/`**Changed:**` bullets — only sections that apply). Reference issue #22.

Suggested content (adjust wording to match what actually landed):

```markdown
## [jackal-plan-and-execute] 3.3.0

Enforce explicit model tiering + credential pre-flight + commit-early (#22, R4/R5).

**New:**
- Model Tier Table added to the `execute` skill (planner=Opus, implementor=Sonnet, reviewer=Sonnet, reviewer-deep=Opus, contract-sentinel=Sonnet, lexicon-warden=Sonnet, research/doc-render=Sonnet), plus verdict-spot-check guidance for downgraded (Opus→Sonnet) tiers.
- Credential pre-flight snippet (`aws sts get-caller-identity` + remaining-lifetime check) required before any dispatch expected to run >10 min; framed as guidance for downstream AWS projects, not a gate on this repo.
- `implementor.md`: commit-early clause — commit at every green intermediate state within a phase (WIP commits fine; squash-merge collapses them), complementing the honest-stopping-point clause.

**Changed:**
- All five Agent dispatch blocks in the `execute`, `plan`, `review`, `design`, and `finish` skills now carry an explicit `<parameter name="model">`; a model-unspecified dispatch is declared a defect in skill text. The `review` skill's deep-reviewer substitution note now swaps `model` together with `subagent_type`.

## [jackal-supervisor] 3.2.0

Model tiering + credential pre-flight, supervisor side (#22, R4/R5).

**New:**
- Model Tiers table mirrored into `jackal-supervisor.md` (identical to the `execute` skill copy), with the frontmatter-reconciliation footnote noting contract-sentinel/lexicon-warden are `model: haiku` in `jackal-director` frontmatter but promoted to Sonnet at dispatch.
- Credential pre-flight snippet (downstream-AWS guidance, >10-min dispatches) and an explicit "every dispatch specifies model" rule alongside the existing "workers never spawn workers" callout.
```

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`
Expected: **all pass** — critically `check-version-sync.py` prints "Version sync OK" (plugin.json now equals marketplace.json for both bumped plugins). This is the phase that makes the full suite green; if version-sync fails here, the plugin.json/marketplace.json values are out of sync.

Manual: confirm both CHANGELOG entries are present and reference #22.

## Commit

`chore(release): bump plan-and-execute 3.3.0, supervisor 3.2.0 + changelog (#22)`
