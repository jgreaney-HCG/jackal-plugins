# Phase 3: Version + Marketplace + Changelog Sync

**Goal:** Bump the version of every plugin touched (jackal-plan-and-execute, jackal-supervisor), sync `marketplace.json`, and add CHANGELOG entries describing ONLY R3's additions.

**AC Coverage:**
- "Version + marketplace.json + CHANGELOG.md sync for any plugin touched."

---

## Context

Phases 1-2 edited exactly two plugins:
- `jackal-plan-and-execute` — `execute/SKILL.md` (Phase 1).
- `jackal-supervisor` — `jackal-sweep/SKILL.md` (Phase 2).

`jackal-director` was **NOT** edited (Phase 1 only cross-*references* `director-loop`; it does not
modify it), so **do not bump jackal-director**. Do not bump any other plugin.

**On-disk baselines in THIS worktree** (verified — the worktree is stacked on #22, so these already
reflect #22's bumps):
- `jackal-plan-and-execute`: currently **3.3.0** (plugin.json and marketplace.json agree).
- `jackal-supervisor`: currently **3.2.0** (plugin.json and marketplace.json agree).

Bump each by a **minor** version (this is a new policy/behavior addition, consistent with how #18/#21/
#22 bumped for skill-text policy changes):
- `jackal-plan-and-execute`: **3.3.0 → 3.4.0**.
- `jackal-supervisor`: **3.2.0 → 3.3.0**.

**CHANGELOG scope warning (important):** this branch is stacked on #22, so its diff vs `origin/main`
includes #22's changes too. The CHANGELOG entries added in this phase must describe **ONLY R3's
additions** (topology policy + sweep guidance) — do NOT re-describe #22's model-tiering / credential
pre-flight work, which already has its own `3.3.0` / `3.2.0` entries at the top of the CHANGELOG.

The version-sync gate (`scripts/check-version-sync.py`) enforces plugin.json ==
marketplace.json for every locally-sourced plugin; it does **not** parse CHANGELOG prose. So the hard
gate is plugin.json/marketplace.json agreement; the CHANGELOG entry is a human/reviewer convention
(required by CLAUDE.md's "Version Updates Require Marketplace and Changelog Sync" rule).

## Implementation

### Bump jackal-plan-and-execute to 3.4.0

**Files:**
- Modify: `plugins/jackal-plan-and-execute/.claude-plugin/plugin.json` — `"version": "3.3.0"` → `"3.4.0"`.
- Modify: `.claude-plugin/marketplace.json` — the `jackal-plan-and-execute` entry `"version": "3.3.0"` → `"3.4.0"`.

### Bump jackal-supervisor to 3.3.0

**Files:**
- Modify: `plugins/jackal-supervisor/.claude-plugin/plugin.json` — `"version": "3.2.0"` → `"3.3.0"`.
- Modify: `.claude-plugin/marketplace.json` — the `jackal-supervisor` entry `"version": "3.2.0"` → `"3.3.0"`.

**Note on marketplace.json:** both plugins currently show `3.3.0` (plan-and-execute) and `3.2.0`
(supervisor) at distinct entries. When editing, target the correct entry by its `"name"` — do not
edit the wrong plugin's version. After editing, confirm each plugin's marketplace entry matches its
plugin.json.

### CHANGELOG entries (R3 only)

**Files:**
- Modify: `CHANGELOG.md` — add two new entries at the **top** (immediately after the `# Changelog`
  heading, above the existing `## [jackal-plan-and-execute] 3.3.0` entry), newest first.

Add these entries (follow the existing house format — heading `## [plugin] version`, one-line summary,
then a `**New:**` list). Describe ONLY R3:

```markdown
## [jackal-plan-and-execute] 3.4.0

Flat orchestration topology by default; justification-gated middle tier (#19, R3).

**New:**
- `execute` skill gains an `## Orchestration Topology` section: flat (director → workers) is the
  default, with the GL-488 per-phase warm-context `SendMessage` named-continuation pattern named as
  the reference implementation.
- A middle supervisor tier now requires a one-sentence written justification in the Agent dispatch
  prompt (what the tier provides that flat dispatch + memory cannot); a nested-supervisor dispatch
  without it is declared a defect.
- When a middle tier is used, R2's liveness contract applies with a stricter (shorter) `EXPECT`
  window — cross-referenced, not duplicated.
- Explicit reconciliation with the repo CLAUDE.md sole-orchestrator rule, written into the skill
  text: flat-by-default + the narrow, justification-gated nested-supervisor tier as the documented
  exception (CLAUDE.md itself unchanged).

## [jackal-supervisor] 3.3.0

Sweeps run flat, not under a nested Opus supervisor (#19, R3).

**New:**
- `jackal-sweep` skill directs backlog sweeps to run as direct director work or at most a single
  Sonnet research dispatch — never a nested Opus supervisor — unless justified per the `execute`
  skill's Orchestration Topology policy (one-sentence justification + stricter liveness window).
```

**Tests:**

No unit tests. The version-sync gate is the enforced check; the CHANGELOG is a convention check.

---

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`

Expected: exit 0 for all three. In particular `check-version-sync.py` must pass, proving
plugin.json and marketplace.json agree at 3.4.0 (plan-and-execute) and 3.3.0 (supervisor).

Manually confirm: CHANGELOG has two new top entries describing only R3 (no #22 restatement), and
`jackal-director` version is unchanged (1.4.0).

## Commit

`chore: bump plan-and-execute 3.4.0 + supervisor 3.3.0; changelog (#19)`
