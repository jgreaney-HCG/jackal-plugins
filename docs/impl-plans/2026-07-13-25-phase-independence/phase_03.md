# Phase 3: version + marketplace + CHANGELOG sync

**Goal:** Bump jackal-plan-and-execute from 3.4.0 → 3.5.0 in plugin.json, mirror it in marketplace.json, and prepend an R9-only CHANGELOG entry.
**AC Coverage:** 25-phase-independence.AC3.3

---

## Context

**Before this phase:** Phases 1–2 changed skill/agent text only; no version has been bumped. Verified on disk in this stacked worktree:

- `plugins/jackal-plan-and-execute/.claude-plugin/plugin.json` → `"version": "3.4.0"`.
- `.claude-plugin/marketplace.json` → the `jackal-plan-and-execute` entry → `"version": "3.4.0"`.
- `CHANGELOG.md` top entry is `## [jackal-plan-and-execute] 3.4.0` (the #19 R3 flat-topology release).

Per CLAUDE.md ("Version Updates Require Marketplace and Changelog Sync"), a plugin version bump must update all three: plugin.json, marketplace.json, and CHANGELOG.md. `scripts/check-version-sync.py` mechanically enforces that plugin.json and marketplace.json agree (CHANGELOG prose is a human/reviewer check).

**IMPORTANT — stacked-branch CHANGELOG scope.** This branch is stacked on #22 and #19, so its diff versus `origin/main` also contains their changes. The new CHANGELOG entry must describe **only R9's additions** (phase-independence / `depends_on:` / fan-out). Do NOT restate #22 or #19 content, and do NOT modify or remove their existing CHANGELOG entries — they already sit below where the new entry goes.

**What this phase adds:** the 3.5.0 version in both JSON files and a single new CHANGELOG entry at the top. This is an infrastructure/config phase — verified operationally by `check-version-sync.py`, not by unit tests.

## Implementation

### Bump plugin.json

**Files:**
- Modify: `plugins/jackal-plan-and-execute/.claude-plugin/plugin.json` — `"version": "3.4.0"` → `"version": "3.5.0"`. Change nothing else in the file.

### Mirror in marketplace.json

**Files:**
- Modify: `.claude-plugin/marketplace.json` — in the `plugins` array, the entry whose `"name": "jackal-plan-and-execute"` (currently `"version": "3.4.0"`, `"source": "./plugins/jackal-plan-and-execute"`) → set `"version": "3.5.0"`. Do NOT touch any other plugin entry (jackal-supervisor 3.3.0, jackal-director 1.4.0, jackal-house-style 1.0.6, ed3d-hook-security-hardening 1.0.1, or the marketplace's own top-level `"version": "4.0.0"`).

### Prepend R9 CHANGELOG entry

**Files:**
- Modify: `CHANGELOG.md` — insert a new entry immediately after the `# Changelog` heading (line 1) and before the current top entry `## [jackal-plan-and-execute] 3.4.0`.

**What to implement:**

Insert exactly this block (R9 scope only), keeping a blank line before the existing `## [jackal-plan-and-execute] 3.4.0` entry:

```markdown
## [jackal-plan-and-execute] 3.5.0

Dependency-aware phase fan-out: independent phases run in parallel; sequential stays the default (#25, R9).

**New:**
- `planner` phase-file template gains an optional `**Depends on:**` (`depends_on:`) field: a phase lists
  the prior phase ids that must complete before it may start. Absent ⇒ depends on all prior phases ⇒
  strictly sequential, exactly as before (backward-compatible). A malformed `depends_on:` (non-existent
  phase, self-reference, or cycle) is declared a planner defect the execute skill must surface.
- `execute` skill Mode 1 generalizes "for each phase sequentially" into a dependency-aware scheduler:
  it tracks completed phases and dispatches every phase whose `depends_on:` set is fully satisfied,
  running independent phases in parallel.
- Phase-level fan-out uses Option A on the existing Parallel Dispatch model — the warm trunk agent
  `implementor-<N>` keeps context while additional ready phases dispatch as cold leaf agents
  `implementor-<N>-pX` on the same branch, non-merging transcripts. No worker gains the `Agent` tool;
  the orchestrator makes every fan-out decision (no self-dispatch), and `jackal-supervisor` remains the
  sole `Agent`-holder.
- Same-branch write-safety note (independent phases are file-disjoint by construction; per-phase
  timeout attribution out of scope), watcher cross-reference for long parallel streams, and flat-topology
  consistency with the Orchestration Topology section. The review + verify-don't-trust posture is
  unchanged — fan-out changes when phases run, never whether their output is disk-verified.

**Changed:**
- When no phase declares `depends_on:`, scheduling is byte-for-byte the current named-continuation loop —
  no cold-start regression for the common sequential case.
```

**Tests:**
This is a config/infrastructure phase — no unit tests (repo has no pytest). Verification is operational:
- `check-version-sync.py` must report `jackal-plan-and-execute` in sync at 3.5.0 (plugin.json and marketplace.json agree) and all other plugins unchanged.
- Reviewer confirms the CHANGELOG entry describes R9 only and did not alter #22/#19 entries.
- Map to `test-requirements.md`: AC3.3 is verified by `check-version-sync.py` (mechanical) plus a reviewer read of the CHANGELOG (prose scope).

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`
Expected: all three pass; `check-version-sync.py` prints "Version sync OK" with jackal-plan-and-execute at 3.5.0.

Also confirm: `git diff` shows only the three intended files changed in this phase (plugin.json, marketplace.json, CHANGELOG.md), the new CHANGELOG entry is R9-scoped, and no other plugin's version moved.

## Commit

`chore: bump jackal-plan-and-execute to 3.5.0 (#25 R9)`
