# Phase 1: Watcher helper script

**Goal:** Land `scripts/worktree-watcher.sh` implementing the wake-on-change + STALLED contract.
**AC Coverage:** 18-event-driven-waits-liveness.AC3.1

---

## Context

**Before this phase:** `scripts/` holds `trace-deps.sh`, `check-version-sync.py`, and
`check-frontmatter.py`. There is no watcher/signal-file pattern anywhere in the repo (verified —
this is net-new). This is a plugins/skills repo with **no application code and no pytest suite**;
the entire test suite is `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py &&
python3 scripts/check-frontmatter.py`.

**What this phase adds:** one committed bash helper, `scripts/worktree-watcher.sh`, that a director
launches as a background task. It polls a worktree's `HEAD` on an interval and writes a signal file
on either outcome (new commit, or stall past the EXPECT window), then exits. Its completion is what
generates the harness task-notification that wakes the director — replacing scheduled foreground
polling.

**Verification reality:** `trace-deps.sh` scans plugin markdown under `plugins/**` for
cross-references; it does **not** scan `scripts/`. So the new script needs no registration and
cannot introduce a DANGLING reference. The only Phase 1 gate is that the script is syntactically
valid bash and the existing `trace-deps.sh` run stays green (it will — the script lives outside its
scan path).

## Implementation

### The watcher script

**Files:**
- Create: `scripts/worktree-watcher.sh`

**Contract (from the design's Watcher contract, verbatim intent):**
- **Args:** `<worktree-path> <signal-file> <expect-seconds>`.
  - `<worktree-path>` — absolute path to the worktree whose `HEAD` is watched.
  - `<signal-file>` — path the watcher writes its single-line result to.
  - `<expect-seconds>` — the EXPECT window: max seconds the dispatch may go without a qualifying
    state change (a new commit) before the watcher declares `STALLED`.
- **Poll interval:** compares `HEAD` **every 60s inside the background task**. This 60s poll is
  internal to the background task and is explicitly **not** a director foreground sleep, so the
  sleep<timeout rule (Phase 2) does not bind it. Do not confuse the two.
- **Wake-on-change:** when `HEAD` differs from the SHA captured at launch, write
  `NEW_COMMIT <sha>` (the new full SHA) to the signal file and exit `0`.
- **Stall:** when `expect-seconds` elapses with no qualifying change, write
  `STALLED <agent> <window>` to the signal file and exit. Derive `<agent>` from the worktree
  basename (that is the only identifier the script has); `<window>` is the EXPECT value in seconds.
- **Completion is the event:** the script's exit is what generates the task-notification. The
  director's context is touched only when the script completes — never on a schedule.

**What to implement:**

A POSIX-friendly bash script. Suggested shape (the implementor may refine, but must preserve the
arg order, the two exact signal-line prefixes `NEW_COMMIT ` / `STALLED `, the 60s internal poll,
and the EXPECT-bounded stall behavior):

```bash
#!/usr/bin/env bash
# worktree-watcher.sh — wake-on-state-change watcher for director-dispatched async work.
#
# Launched as a BACKGROUND task by the director. Polls a worktree's HEAD every
# POLL_INTERVAL seconds. Writes exactly one signal line and exits:
#   NEW_COMMIT <sha>          — HEAD advanced (qualifying state change); exit 0
#   STALLED <agent> <window>  — EXPECT elapsed with no new commit; exit 0
# The script's completion is the event that generates the director's task-notification.
# The 60s internal poll is NOT a director foreground sleep — the sleep<timeout rule
# (see the execute skill) governs only foreground director sleeps, never this loop.
set -uo pipefail

WORKTREE="${1:?usage: worktree-watcher.sh <worktree-path> <signal-file> <expect-seconds>}"
SIGNAL="${2:?usage: worktree-watcher.sh <worktree-path> <signal-file> <expect-seconds>}"
EXPECT="${3:?usage: worktree-watcher.sh <worktree-path> <signal-file> <expect-seconds>}"

POLL_INTERVAL=60
AGENT="$(basename "$WORKTREE")"

head_sha() { git -C "$WORKTREE" rev-parse HEAD 2>/dev/null; }

start_sha="$(head_sha)"
elapsed=0

while :; do
  sleep "$POLL_INTERVAL"
  elapsed=$((elapsed + POLL_INTERVAL))

  current="$(head_sha)"
  if [ -n "$current" ] && [ "$current" != "$start_sha" ]; then
    printf 'NEW_COMMIT %s\n' "$current" > "$SIGNAL"
    exit 0
  fi

  if [ "$elapsed" -ge "$EXPECT" ]; then
    printf 'STALLED %s %s\n' "$AGENT" "$EXPECT" > "$SIGNAL"
    exit 0
  fi
done
```

Requirements the implementor must satisfy:
- The file is executable (`chmod +x`).
- Missing/blank args produce a clear usage error and non-zero exit (the `${N:?...}` form above does
  this).
- The signal file contains exactly one line, prefixed `NEW_COMMIT ` or `STALLED `, matching the
  contract the skills in Phase 2/3 reference.
- No brace expansion, no `sed`/`cat`/`head`/`tail` for reading (house rule).

**Tests:**

There is no pytest suite in this repo, so verification is operational (matches how `trace-deps.sh`
etc. are themselves verified). The implementor must demonstrate the contract with a temporary
throwaway git repo and short EXPECT values, capturing output — do NOT commit any test harness or
fixture, only the script:

1. **Syntax:** `bash -n scripts/worktree-watcher.sh` exits 0.
2. **Usage guard:** running with fewer than 3 args prints usage and exits non-zero.
3. **Wake-on-change:** in a temp git repo, launch the watcher backgrounded with a small EXPECT
   (e.g. 600), make a commit, and confirm within ~2 poll intervals the signal file reads
   `NEW_COMMIT <sha>` and the process exited 0. (To make this fast without waiting 60s, the
   implementor may temporarily set a smaller `POLL_INTERVAL` via a local edit **only for the manual
   check**, then restore 60s before committing — the committed default is 60s.)
4. **Stall:** in a temp git repo with no commits, a short EXPECT (e.g. equal to one shortened poll)
   yields a signal file reading `STALLED <worktree-basename> <expect>` and the process exits.

Record the observed signal-file contents in the implementor report as evidence (per
`verification-before-completion` — an operational claim needs shown output, not "it should work").

---

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`
Also run: `bash -n scripts/worktree-watcher.sh`

Expected: `bash -n` exits 0; `trace-deps` prints `PASS: every cross-reference resolves.`;
version-sync and frontmatter both OK (this phase changes no versions or frontmatter, so they must
still pass unchanged). Manual watcher checks (wake-on-change, stall) produce the exact signal lines
above.

## Commit

`feat(scripts): add worktree-watcher.sh wake-on-change + STALLED helper`
