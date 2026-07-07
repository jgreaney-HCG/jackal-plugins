# jackal-plan-and-execute

Model-adaptive planning and execution harness for Claude Code.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  MAIN CONVERSATION (the session model, 1M context)      │
│                                                         │
│  Skills: design, plan, execute, review, finish, debug   │
│                                                         │
│  Holds full session state. Never clears.                │
│  Dispatches stateless workers via Agent tool.           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Workers (stateless, one-shot, no nested subagents):    │
│                                                         │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌───────────┐ │
│  │ Planner  │ │Implementor│ │ Reviewer │ │ Reviewer-  │ │
│  │ (Opus)   │ │ (Sonnet)  │ │ (Sonnet) │ │ deep(Opus)│ │
│  └──────────┘ └───────────┘ └──────────┘ └───────────┘ │
│                                                         │
│  Coordination: git (worktrees, commits) + GitHub issues │
└─────────────────────────────────────────────────────────┘
```

On Bedrock, `sonnet`/`opus`/`haiku` in agent frontmatter resolve through your
model mapping — point `sonnet` at Sonnet 5 and `haiku` at Haiku 4.5 to get the
intended cost/capability tiers.

## Design Principles

1. **Sonnet is the workhorse.** Implementation and standard review use Sonnet. Opus for planning and deep review only.
2. **Phase = unit of work.** No micro-task splitting. One phase, one dispatch.
3. **Review is proportional to risk.** Simple → none. Standard → final only (Sonnet). Complex or security/contract-touching → per-phase + deep final review (Opus).
4. **Review happens before the PR, not after.** The PR that opens has already passed tests, review, and (when canon exists) contract-check. Post-PR feedback is welcome; routine post-PR re-review is not part of the loop.
5. **Workers never spawn workers.** Every agent denies the Agent tool (`disallowedTools: Agent`) and every dispatch prompt repeats the prohibition. Only the orchestrator dispatches.
6. **Self-review before external review.** Implementor checks its own output.
7. **Continuous execution.** Orchestrator churns through the backlog until genuinely stuck.
8. **Reports are receipts, not essays.** Workers have hard line caps; the orchestrator relays 3-line summaries.
9. **Parallel when possible.** Independent issues dispatch concurrently.

## Skills

| Skill | Purpose | User-invocable |
|-------|---------|----------------|
| `design` | Full design workflow (Complex issues); reads canon when present | Yes |
| `plan` | Generate implementation plan + worktree | Yes |
| `execute` | Execute plan or drive continuous backlog | Yes |
| `review` | Dispatch reviewer (tiered), manage fix loop | No (called by execute) |
| `finish` | Rebase if behind → push → PR → issue updates | Yes |
| `debug` | Systematic root-cause debugging | No (activated on failures) |

## Agents

| Agent | Model | Role |
|-------|-------|------|
| `planner` | Opus | Generates implementation phase files from design docs |
| `implementor` | Sonnet | Executes one phase or one Simple issue completely |
| `reviewer` | Sonnet | Validates code against requirements, returns structured verdict |
| `reviewer-deep` | Opus | Deep review: Complex issues, auth/payments/user-data/crypto/contract diffs |

All agents carry `disallowedTools: Agent` — subagents cannot nest.

## Delegation Model

The main conversation (orchestrator) manages state and makes decisions. It **never** writes code, runs tests for correctness, or investigates the codebase directly.

| Do directly (orchestrator) | Delegate to subagent |
|---|---|
| Read/write backlog state and issue docs | Write code and tests → `implementor` |
| Run conflict gate (git commands) | Generate phase files → `planner` |
| Create/remove worktrees | Validate code → `reviewer` / `reviewer-deep` |
| Route by complexity, decide whether to review | Investigate codebase patterns → `ed3d-research-agents:codebase-investigator` |
| Rebase, push, open PRs, update backlog | Research external deps/APIs → `ed3d-research-agents:combined-researcher` |
| Report to human | |

**The rule:** If a task produces an artifact (code, phase files, a review verdict, research findings), delegate it. If a task reads or updates shared state (backlog, git, issue docs) or requires a routing decision, do it directly.

## Complexity Routing

| Complexity | Pipeline |
|---|---|
| Simple | implementor directly (no plan, no design) |
| Standard | plan → execute (no design phase) |
| Complex | design → plan → execute |

## Continuous Execution (Backlog Mode)

```
/jackal-plan-and-execute:execute (no arguments)
```

(Marketplace-installed commands are namespaced `plugin:command` — a bare
`/execute` will not resolve.)

The orchestrator:
1. Reads the GitHub Issues backlog
2. Finds unblocked issues
3. Runs conflict gate
4. Dispatches work (parallel when independent)
5. Finishes each issue: rebase if behind → push → PR
6. Reports one-liner
7. Loops until stuck

Stops for: human decisions, all blocked, review failures (3x), ambiguity.

## Director Loop Integration

When the repo has `docs/canon/` (see the `jackal-director` plugin):
- `design` reads the charter and glossary before brainstorming and adds a
  Contract Impact section when contract models are touched.
- `planner` drafts impact statements alongside phases that change contracts.
- `execute`'s final review runs `/jackal-director:contract-check` in parallel with the reviewer.
- `finish` requires contract-check CLEAN (or explained-FLAGGED) before the PR.

## Harness Guidance

Create `.jackal/harness-guidance.md` in your project root to customize orchestrator behavior across all skills. This file is read at the start of every skill run and takes precedence over built-in defaults. Resolution walks up from the working directory to the repo root (nearest-wins), so a monorepo can scope guidance per module.

Typical contents:
- **Delegation overrides** — e.g., "always review auth phases even if not the final phase"
- **Test command** — override the auto-detected test command
- **Stop conditions** — e.g., "pause after each issue rather than looping"
- **Parallel execution policy** — e.g., "never dispatch in parallel (shared DB state)"

If the file doesn't exist, all defaults apply.
