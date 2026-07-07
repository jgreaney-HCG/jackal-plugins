# jackal-supervisor

Project supervisor for the Jackal harness — backlog management, epics,
conflict gates, complexity routing, and lifecycle orchestration, wrapping
`jackal-plan-and-execute` with project-specific configuration.

## What this plugin adds over the raw lifecycle

`jackal-plan-and-execute` gives you `design`/`plan`/`execute`/`finish` as
standalone commands. This plugin wraps them with:

- **Backlog ownership** — the `jackal-supervisor` agent creates issues (with
  dedup search and full label application at creation), groups them into
  epics, tracks status, and runs the conflict gate before any work is assigned.
- **Single-owner worktree handoff** — `jackal-design-plan` creates the
  worktree for Complex issues and persists it to the issue doc; `jackal-impl-plan`
  reads it back rather than re-deriving it, which is what fixed the historical
  "could not find worktree" failure between the two phases.
- **Project-config wrapping** — every wrapper skill reads `## Jackal Config`
  from the target project's `CLAUDE.md` before doing anything, so the same
  plugin behaves correctly across projects with different repos, test
  commands, and label conventions.
- **Hygiene** — `jackal-sweep` for worktree/branch reclamation and PR rebase
  flags, and a backlog-groom workflow for catching mislabeled/orphaned/
  unprioritized issues before they rot.

## Agent

| Agent | Model | Role |
|---|---|---|
| `jackal-supervisor` | Opus | Backlog CRUD, epics, conflict gate, status reporting, hygiene grooming, Director-cadence reminders. The only orchestrating tier — it's the one agent in this marketplace that keeps the Agent tool. |

## Commands and skills

Marketplace-installed commands are namespaced `plugin:command` — type them with the `jackal-supervisor:` prefix (a bare `/jackal-design-plan` will not resolve).

| Command | Skill | Purpose |
|---|---|---|
| `/jackal-supervisor:jackal-design-plan` | `jackal-design-plan` | Start design for a Complex issue — conflict gate, worktree creation, invokes `design`. |
| `/jackal-supervisor:jackal-impl-plan` | `jackal-impl-plan` | Create an implementation plan — reuses the design worktree (Complex) or creates one (Standard), invokes `plan`. |
| `/jackal-supervisor:jackal-finish-branch` | `jackal-finish-branch` | Rebase if behind → push → PR → issue updates. Wraps `finish` with project config. |
| `/jackal-supervisor:jackal-pause-session` | `jackal-pause-session` | Record a resumable checkpoint (reads the live task list first, falls back to git evidence). |
| `/jackal-supervisor:jackal-ui-verify` | `jackal-ui-verify` | E2E tests + live Playwright verification against acceptance criteria, for branches touching `ui_path`. |
| `/jackal-supervisor:jackal-sweep` | `jackal-sweep` | Reclaim worktrees/branches for merged PRs (worktree first, then branch), flag PRs needing rebase, fast-forward main. |

## Epics and backlog hygiene

Larger bodies of work are tracked as `epic`-labeled GitHub issues with a task
list of child issues (`Part of #<epic>` linkage on each child). The
supervisor keeps both ends in sync at create/close time. Ask it to "groom the
backlog" for an audit of mislabeled-ready, orphaned in-progress, zombie
worktrees, unprioritized issues, epic drift, and PRs needing rebase — see the
agent definition's Backlog Groom section for the full checklist.

## Director cadence

If the project has `docs/canon/` (see `jackal-director`), the supervisor
prompts for a `/jackal-director:director-packet` after roughly every 5 closed issues or when
7+ days have passed since the last one, and routes returning review memos to
`/jackal-director:ingest-directive`.

## Configuration

Full key-by-key reference: [docs/jackal-config-reference.md](../../docs/jackal-config-reference.md).
