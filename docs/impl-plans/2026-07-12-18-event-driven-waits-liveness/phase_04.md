# Phase 4: Version + changelog sync

**Goal:** Bump the version of every plugin this branch touched, mirror those versions into `marketplace.json`, and prepend matching `CHANGELOG.md` entries — so `check-version-sync` passes and the marketplace/changelog stay coherent.
**AC Coverage:** 18-event-driven-waits-liveness.AC3.3

---

## Context

**Before this phase:** Phases 1–3 landed the watcher script and skill/agent text but changed **no**
versions. The touched plugins are:
- **jackal-plan-and-execute** — Phase 2 (`execute/SKILL.md`), Phase 3 (`implementor.md`,
  `execute/SKILL.md`).
- **jackal-director** — Phase 2 + Phase 3 (`director-loop/SKILL.md`).
- **jackal-supervisor** — Phase 3 (`jackal-supervisor.md`).

`scripts/worktree-watcher.sh` (Phase 1) lives under `scripts/`, not under any plugin, so it does not
by itself require a plugin bump — but the two skills that reference it do, and they are already in
the touched-plugin list above.

**On-disk baseline versions in this worktree (verified this session):**
- jackal-plan-and-execute: `3.1.1` (both plugin.json and marketplace.json)
- jackal-supervisor: `3.0.3` (both)
- jackal-director: **`1.2.0`** (both) — **note:** the design/context references `1.3.0` because PR
  #23 bumped director on `main`. This worktree was branched **before** #23 merged, so its baseline
  is `1.2.0`. Bump from whatever the branch's current baseline is at implementation time. If the
  branch has since been rebased onto `main` and director now reads `1.3.0`, bump from `1.3.0`
  instead. **The implementor must read the current on-disk version first** (`plugin.json`) and bump
  from that — do not hard-code a "from" version from this doc. This is called out in Notes for the
  human.

**What this phase adds:** the version/marketplace/CHANGELOG sync, in one pass, for the three touched
plugins. CI enforces plugin.json↔marketplace.json agreement via `check-version-sync.py`
(CHANGELOG prose is a human/reviewer check, not gated — but CLAUDE.md requires it, so add it).

## Implementation

### Version bumps (minor bump — new additive feature, no breaking change)

Each of these is a feature addition (new watcher pattern, new clauses, new rules), so bump the
**minor** version. For each touched plugin, edit **both** files to the same new version:

**Files:**
- Modify: `plugins/jackal-plan-and-execute/.claude-plugin/plugin.json` — `3.1.1` → `3.2.0`
- Modify: `plugins/jackal-director/.claude-plugin/plugin.json` — current baseline (`1.2.0`, or
  `1.3.0` if rebased) → next minor (`1.3.0`, or `1.4.0` if rebased)
- Modify: `plugins/jackal-supervisor/.claude-plugin/plugin.json` — `3.0.3` → `3.1.0`
- Modify: `.claude-plugin/marketplace.json` — set the `version` field of each of the three plugin
  entries (`jackal-plan-and-execute`, `jackal-director`, `jackal-supervisor`) to the **same** new
  value chosen above. Leave `jackal-house-style`, `ed3d-hook-security-hardening`, and the top-level
  marketplace `version` untouched (this branch does not touch them).

The implementor must read each plugin.json's current version first and bump from the real on-disk
value (see the director note above), keeping plugin.json and its marketplace.json entry identical —
that identity is exactly what `check-version-sync.py` asserts.

### CHANGELOG entries (prepend, newest first, after the `# Changelog` heading)

**Files:**
- Modify: `CHANGELOG.md`

Prepend one entry per bumped plugin, at the very top (immediately after the `# Changelog` line),
following the repo's established format (see the existing `## [jackal-director] 1.2.0` entry as the
template — heading `## [plugin-name] version`, a one-line summary, then `**New:**` / `**Changed:**`
sections as applicable). Draft entries:

```markdown
## [jackal-plan-and-execute] 3.2.0

Event-driven waits + subagent liveness contract (#18).

**New:**
- `execute` skill documents the event-driven watcher (`scripts/worktree-watcher.sh`), the
  sleep<timeout hard rule (foreground sleeps ≤100s under the 120s Bash timeout), the batched-status
  rule, and the STALLED stall-response procedure (verify disk → instruct commit-and-report → resume
  from disk).
- Honest-stopping-point clause added to `implementor.md` and both `execute` dispatch templates;
  EXPECT/heartbeat expectation set at dispatch; relay rule forbidding unbacked progress claims,
  cross-referencing `verification-before-completion`.

## [jackal-supervisor] 3.1.0

Subagent liveness contract (#18).

**New:**
- Honest-stopping-point clause added to `jackal-supervisor.md` alongside the "workers never spawn
  workers" rule (belt-and-braces prompt-level enforcement). Supervisor retains the `Agent` tool as
  the sole orchestrator.

## [jackal-director] 1.3.0

Event-driven waits + liveness, director-side (#18).

**New:**
- `director-loop` skill mirrors the event-driven wait / STALLED stall-response summary and the
  relay rule (no relayed subagent progress claim without a cited same-turn disk observation),
  referencing the `execute` skill for the canonical procedure.
```

If director's baseline turns out to be `1.3.0` (post-rebase), use `## [jackal-director] 1.4.0`
instead and keep the body — match the heading to the actual bumped version.

**What to implement:** the version edits + CHANGELOG prepend. Keep the top-level `# Changelog`
heading as the first line; entries go directly beneath it in the order above.

**Tests:**
No pytest suite. Verification is the two relevant CI checks:
- `python3 scripts/check-version-sync.py` prints `Version sync OK: N plugins checked.` (proves each
  bumped plugin.json matches its marketplace.json entry — AC3.3).
- `python3 scripts/check-frontmatter.py` prints `Frontmatter lint OK` (proves no frontmatter was
  disturbed; the worker-agent `disallowedTools: Agent` / supervisor `Agent` frontmatter from Phase 3
  still parse — AC3.3's no-nesting-intact clause).
- Manual: implementor greps `CHANGELOG.md` to confirm one new heading per bumped plugin at the top.

---

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`

Expected: all three green — `trace-deps` PASS, `check-version-sync` `Version sync OK`,
`check-frontmatter` `Frontmatter lint OK`. This is the full repo test suite (TEST_CMD); its passing
is the branch's Success condition per the design's Definition of Done.

## Commit

`chore(release): bump plan-and-execute, supervisor, director; sync marketplace + changelog`
