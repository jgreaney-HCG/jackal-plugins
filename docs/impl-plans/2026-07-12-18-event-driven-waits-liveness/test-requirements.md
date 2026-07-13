# Test Requirements — #18 Event-Driven Waits + Liveness Contract

This repo has **no application code and no pytest suite**. The full automated suite is the
TEST_CMD trio: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3
scripts/check-frontmatter.py`. Text/behavior claims beyond those checks are verified by **Grep
assertions** on the edited files and **operational** checks on the script — there is no unit-test
framework to add tests to, and inventing one would be wrong for this repo.

Per the design's Definition of Done, **AC1.1, AC1.3, and AC2.2 are MANUAL/OBSERVATIONAL** — they can
only be proven in a future live director cycle and are **never gated in this repo's CI**. They are
listed here for completeness with their manual verification method.

| AC | Implemented in | Verified by | Manual? |
|---|---|---|---|
| **AC1.1** Full Complex-issue cycle completes with zero foreground sleep-poll turns | Phase 2 (guardrails that prevent the behavior) | Observational — inspect a future live director transcript for foreground sleep-poll turns | **YES — not CI** |
| **AC1.2** `execute` states sleep<timeout rule (≤100s/120s) + documents 120s timeout; no scheduled sleep yields exit-143 | Phase 2 | Grep `execute/SKILL.md` for `120`, `≤100`/`<=100`, watcher reference; grep confirms **no** foreground `sleep >=120` snippet (Failure guard) | No |
| **AC1.3** Wait-attributable turns/issue drop ≥50% vs GL-488 baseline | Phase 2 | Observational — compare a future live cycle's wait turns to the GL-488 baseline | **YES — not CI** |
| **AC2.1** Honest-stopping-point clause verbatim in both agent defs **and** both dispatch templates | Phase 3 | Grep clause's distinctive sentence in `implementor.md`, `jackal-supervisor.md`, and twice in `execute/SKILL.md` (cold + continuation); diff the copies for byte-identity. Single-location = Failure | No |
| **AC2.2** Deliberately-stalled test agent produces STALLED notification + director recovery, no human prompt | Phases 1+3 (mechanism + procedure) | Observational — run a deliberately-stalled test agent in a live cycle and confirm STALLED notification + autonomous recovery | **YES — not CI** |
| **AC2.3** `execute`/`director-loop` codify no unbacked subagent-progress assertion, cross-referencing verification-before-completion | Phase 3 | Grep `execute/SKILL.md` + `director-loop/SKILL.md` for the relay rule and a `verification-before-completion` citation; confirm no relay guidance permits restating a claim without a cited disk check (Failure guard) | No |
| **AC3.1** `scripts/worktree-watcher.sh` exists, trace-deps-clean, wakes on new commit, emits `STALLED <agent> <window>` on EXPECT | Phase 1 | `bash -n` syntax check; operational check in a temp git repo: NEW_COMMIT on commit, STALLED on EXPECT elapse (signal-file contents captured as evidence); `trace-deps.sh` PASS | No (operational) |
| **AC3.2** Stall-response procedure (verify disk → instruct commit-and-report → resume from disk) in `execute` | Phase 2 | Grep `execute/SKILL.md` for the three-step procedure and its `verification-before-completion` citation | No |
| **AC3.3** Versions bumped + marketplace.json + CHANGELOG synced; check-version-sync + check-frontmatter pass; workers keep `disallowedTools: Agent` | Phase 4 (bump/sync) + Phase 3 (invariant preserved) | `check-version-sync.py` `Version sync OK`; `check-frontmatter.py` `Frontmatter lint OK`; grep confirms `implementor.md` retains `disallowedTools: Agent` and `jackal-supervisor.md` retains `Agent` in `tools:` | No |

## Notes on verification approach

- **No test files are created.** Correct for this repo — the deliverable is skill/agent text + one
  script, and the "suite" is the three static-check scripts already in `scripts/`.
- **Grep assertions** are the practical stand-in for unit tests on prose ACs (AC1.2, AC2.1, AC2.3,
  AC3.2). The implementor runs them and reports the match counts as evidence, per
  `verification-before-completion`.
- **The three MANUAL/OBSERVATIONAL ACs (AC1.1, AC1.3, AC2.2)** must not block this branch's PR. The
  branch is done when the text/script land and the TEST_CMD trio is green; the observational ACs are
  proven later in a live director cycle.
