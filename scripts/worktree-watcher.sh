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
