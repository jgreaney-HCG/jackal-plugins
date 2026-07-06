# Jackal Config Reference

Every Jackal-managed project declares a `## Jackal Config` section in its
`CLAUDE.md`. Skills read this at the start of every run — this is the
canonical list of every key any skill or agent consumes. If you're adding a
new key, add it here too.

## Minimal example

```markdown
## Jackal Config

- gh_repo: your-org/your-repo
- test_cmd: pytest
```

Everything else has a sane default. Most projects only need those two lines
plus `modules` and `ui_path` if applicable.

## Keys

| Key | Default | Required | Read by | Meaning |
|---|---|---|---|---|
| `gh_repo` | — | **Yes** | supervisor agent, all wrapper skills, `execute` Backlog mode | `owner/repo` — GitHub Issues is the only backlog backend; the harness fails loudly if this is unset. |
| `test_cmd` | — | Recommended | `plan`, `execute`, `finish`, `jackal-impl-plan`, `jackal-finish-branch` | The command that runs the project's test suite. Used for baseline checks, pre-rebase/pre-PR verification, and review. |
| `label_style` | `slash` | No | supervisor agent, all wrapper skills | `slash` or `colon` — the separator in status/complexity/priority labels (`status/ready` vs `status:ready`). Derive once, apply consistently. |
| `repo_root` | `$(git rev-parse --show-toplevel)` | No | supervisor agent, all wrapper skills | Where conflict-gate git commands run from. |
| `issue_docs` | — | No | supervisor agent, all wrapper skills, `jackal-ui-verify` | Path to rich issue docs on disk (e.g. `docs/issues`), if the project mirrors GitHub issue bodies there. |
| `issue_prefix` | — | No | `jackal-design-plan`, `jackal-impl-plan`, `jackal-pause-session` | Legacy issue-doc filename prefix (`PREFIX-XXX`). Only relevant for projects still on the legacy `PREFIX-NN` scheme rather than bare GitHub issue numbers. |
| `design_plans` | `docs/design-plans` | No | `design` skill, `jackal-design-plan`, `jackal-impl-plan` | Where design documents are written. |
| `impl_plans` | `docs/impl-plans` | No | `plan`/`planner`, `execute`, `jackal-impl-plan`, `jackal-pause-session` | Where implementation phase files are written. **Must be read from config, never hardcoded** — this was the 3.5.0 handoff bug (see CHANGELOG). |
| `modules` | — | No | supervisor agent, `execute` | Module short-name map, used in branch naming and module-scoped commit prefixes. |
| `protected_main` | auto-detect via `gh` | No | `finish`, `jackal-finish-branch` | Whether `main` is protected. As of 4.0.0 the PR path is always taken regardless of this value — it's now informational only, kept for `gh`-detection-unavailable environments. |
| `git_remote` | `origin` | No | `finish`, `jackal-finish-branch` | Remote to push to. |
| `push_cmd` | `git push` | No | `finish`, `jackal-finish-branch` | Override the push command (e.g. a wrapper that also updates a deploy hook). |
| `pr_method` | `gh` | No | `finish`, `jackal-finish-branch` | Set to a CodeCommit-style value to get an `aws codecommit create-pull-request` command instead of `gh pr create`. |
| `ui_path` | — | No | `finish`, `jackal-finish-branch`, `jackal-ui-verify` | Path prefix identifying UI files. If a branch touches this path, `jackal-ui-verify` is required before finish. |
| `ui_port` | — | If `ui_path` set | `jackal-ui-verify` | Local dev port for the UI server. |
| `api_port` | — | If `ui_path` set | `jackal-ui-verify` | Local dev port for the API server. |
| `ui_dev_cmd` | — | If `ui_path` set | `jackal-ui-verify` | Command to start the UI dev server from the worktree. |
| `api_dev_cmd` | — | If `ui_path` set | `jackal-ui-verify` | Command to start the API dev server from the worktree. |
| `e2e_cmd` | — (skip e2e if unset) | No | `jackal-ui-verify` | The project's e2e test command. Omit the key entirely if there's no e2e suite. |
| `contracts_pkg` | `contracts/` | No | `jackal-director` agents, `/canon-init` | Path to the contracts package. Works for a Pydantic package or a TypeScript models directory — the drift checker only cares about the exported JSON Schema. |
| `schema_export_cmd` | `python -m contracts.export_schemas` | No | `jackal-director:registry-drift-checker`, `/canon-init` | Command that dumps one JSON Schema per contract model. TypeScript projects point this at a typebox/zod export script, e.g. `npm run export-schemas`. |

## `.jackal/` guidance files

These live in the project repo, not in `## Jackal Config`, and are resolved by
walking up from the working directory to the repo root (nearest-wins, so a
monorepo can scope overrides per module):

| File | Purpose | Written by |
|---|---|---|
| `.jackal/harness-guidance.md` | Review policy, parallel execution policy, stop conditions | Human, or `/ingest-directive` for standing constraints that don't fit design/implementation guidance specifically |
| `.jackal/design-guidance.md` | Domain terminology, architectural constraints for the `design` skill | Human, or `/ingest-directive` (Director standing constraints) |
| `.jackal/implementation-guidance.md` | Coding standards, testing requirements for `planner`/`execute`/review | Human, or `/ingest-directive` |

Legacy `.ed3d/*-guidance.md` files are no longer read as a fallback — projects
still on those paths should rename to `.jackal/`.

## Canon (`docs/canon/`)

Only relevant once a project has run `/canon-init` (from `jackal-director`).
Not a config key — a directory the harness checks for existence before
enabling canon-aware behavior (design reads charter/glossary, execute runs
`/contract-check`, finish gates on it). See
[plugins/jackal-director/README.md](../plugins/jackal-director/README.md).
