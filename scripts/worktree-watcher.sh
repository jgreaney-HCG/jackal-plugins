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

case "$EXPECT" in
  ''|*[!0-9]*|0)
    echo "usage: worktree-watcher.sh <worktree-path> <signal-file> <expect-seconds>" >&2
    echo "error: <expect-seconds> must be a positive integer, got: $EXPECT" >&2
    exit 1
    ;;
esac

POLL_INTERVAL=60
AGENT="$(basename "$WORKTREE")"

head_sha() { git -C "$WORKTREE" rev-parse HEAD 2>/dev/null; }

write_signal() {
  # Atomic write: build the line in a temp file, then mv into place, so any
  # reader of $SIGNAL never observes a zero-length or partially written file.
  printf '%s\n' "$1" > "$SIGNAL.tmp"
  mv "$SIGNAL.tmp" "$SIGNAL"
}

start_sha="$(head_sha)"
elapsed=0

while :; do
  sleep "$POLL_INTERVAL"
  elapsed=$((elapsed + POLL_INTERVAL))

  current="$(head_sha)"
  if [ -n "$current" ] && [ "$current" != "$start_sha" ]; then
    write_signal "NEW_COMMIT $current"
    exit 0
  fi

  if [ "$elapsed" -ge "$EXPECT" ]; then
    write_signal "STALLED $AGENT $EXPECT"
    exit 0
  fi
done
