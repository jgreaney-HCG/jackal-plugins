# Fable-Free Tiering & Dispatch Efficiency — Design Plan

**Date:** 2026-07-08
**Status:** Draft — awaiting review
**Scope:** `jackal-plugins` only (`jackal-plan-and-execute`, `jackal-director`, `jackal-supervisor`, root docs)

---

## Summary

A July 2026 evaluation of the harness against current model pricing, capability data, and
community practice found the architecture sound: the orchestrator/worker split, Sonnet 5
workhorse, Haiku conformance linters, and risk-proportional review all match the consensus
pattern that emerged after Fable 5 and Sonnet 5 shipped. But it surfaced two classes of
problem:

1. **Fable coupling.** The Director loop is documented as review by "a stronger model"
   (Fable, in chat). In environments where Claude Code cannot run Fable — and Fable chat
   access is uncertain — that framing is wrong twice over: the loop looks broken when Fable
   is absent, and the rationale ("stronger") was already stale once a Fable session *could*
   run the harness itself. The loop's real value is **fresh context and a canon-only view**,
   which doesn't depend on any particular model tier.
2. **Dispatch inefficiency and calibration gaps.** Stateless one-shot implementors re-derive
   project context on every phase; Simple issues in backlog mode ship with no machine review;
   the reviewer's hard 40-line report cap can suppress findings (Sonnet 5 follows output
   constraints literally); and the orchestrator's "never read the codebase" rule forces a
   subagent dispatch even for a one-file routing peek.

This plan removes the Fable dependency from the Director loop, re-states model tiering in
capability-relative terms, and fixes the four efficiency/calibration gaps.

### The no-Fable operating model (context for every change below)

The target environment's strongest Claude Code model is **Opus 4.8**. The harness under this
plan runs as:

| Role | Model | Unchanged? |
|---|---|---|
| Main session / orchestrator | Opus 4.8 (strongest available) | Yes — the harness never hardcoded the session model |
| `planner`, `reviewer-deep`, `jackal-supervisor` | `opus` alias | Yes |
| `implementor`, `reviewer` | `sonnet` alias | Yes |
| Director conformance agents | `haiku` alias | Yes |
| Software Director | **Strongest fresh-context reviewer available**: Fable chat if the human has it → any strong-model chat → automated Opus agent (new, C2) | **Changed** |

Nothing in the worker tiers changes. Only the Director's definition and the documentation's
assumptions change.

### Decisions locked at design time

- **The Director loop stays.** Fresh-context review against canon is worth keeping even when
  the reviewer is the *same* tier as the harness — Anthropic's own long-running-agent guidance
  notes fresh-context verifiers outperform self-critique. We reframe, we don't delete.
- **The packet format doesn't change.** The same markdown packet works for a human uploading
  to a chat session and for an automated agent dispatch. This is what makes the fallback
  ladder cheap to build.
- **`ingest-directive` keeps its human confirmation gates.** Automating the *review* is fine;
  automating the *acceptance of directives into canon* is not. Canon changes remain
  human-approved regardless of which path produced the memo.
- **The planner stays on `opus`.** With an Opus session model, planner and orchestrator are
  the same tier, which is fine — the planner exists for context hygiene (heavy codebase
  investigation in a disposable context), not for extra capability.
- **Reviewer stays fresh-context always.** Implementor continuation (C3) never extends to the
  reviewer: a reviewer that shares context with the implementor inherits its blind spots.

---

## Definition of Done

- No skill, command, agent, or README in the marketplace assumes Fable availability. The
  Director is described in capability-relative terms ("a fresh-context reviewer on the
  strongest model available"), with Fable named only as the *preferred* option when present.
- The Director loop runs end-to-end in an environment whose strongest model is Opus 4.8:
  packet → automated director review → memo file → `/jackal-director:ingest-directive`,
  with no step requiring a Fable session.
- `execute` Mode 1 reuses a single implementor across an issue's phases via agent
  continuation, with a documented fallback to fresh-per-phase dispatch.
- Simple issues in backlog mode get a `reviewer` (Sonnet) pass before the PR by default,
  overridable in `.jackal/harness-guidance.md`.
- The reviewer report cap cannot cause a Critical or Important finding to be omitted.
- The orchestrator delegation rules permit a single-named-file read for routing decisions.
- Plugin versions bumped in each touched `.claude-plugin/plugin.json`, mirrored in
  `.claude-plugin/marketplace.json`, with `CHANGELOG.md` entries — per repo convention.

### Out of scope

- Moving the planner or any worker to the session model, or adding Fable-specific tiers.
- Any change to the PR-only completion path or protected-main invariant.
- Changes to upstream `ed3d-plugins` (dependencies stay as declared).
- Removing the human from `ingest-directive` — directive acceptance stays gated.
- Effort-level (`output_config.effort`) tuning per agent — revisit when frontmatter support
  and measured need both exist.

---

## Change items

### C1 — Capability-relative Director framing (jackal-director, root README)

**Problem:** `director-loop/SKILL.md` opens with "a **Software Director** — a stronger model
in a separate chat session"; `director-packet.md` and `ingest-directive.md` name Fable
directly; the root README says "a Software Director (Fable, in chat, no repo access)". In a
no-Fable environment this reads as a hard dependency, and the "stronger" claim was already
wrong for Fable-session users.

**Change:** Rewrite the Director's definition everywhere it appears:

> The Software Director is a **fresh-context reviewer with no repo access** — it sees only
> canon and the packet, never the code or the conversation that produced it. Run it on the
> strongest model you have: Fable in a chat session when available, any strong-model chat
> otherwise, or the automated `director-review` path (C2). Its authority comes from
> independence, not from outranking the harness.

Files: `plugins/jackal-director/skills/director-loop/SKILL.md`,
`plugins/jackal-director/commands/director-packet.md`,
`plugins/jackal-director/commands/ingest-directive.md`,
`plugins/jackal-director/README.md`, root `README.md`.

### C2 — Automated Director review path (jackal-director)

**Problem:** The only Director path is manual: human uploads the packet to a chat session,
copies the memo back. With no Fable chat, there's no defined way to run the loop at all.

**Change:** Add an Opus worker agent `jackal-director:director` and a command
`/jackal-director:director-review`.

- **Agent** (`agents/director.md`): `model: opus`, `disallowedTools: Agent`, and — this is
  the load-bearing constraint — **tools limited to `Read`**, allowed to read only
  `docs/canon/` and the packet file passed in its prompt. No Bash, no Grep, no Glob. The
  "no repo access" property is enforced by tool restriction plus prompt instruction, the
  same belt-and-braces used for the no-nesting rule. The agent's body defines the memo
  format (directives, glossary rulings, standing constraints) identical to what
  `ingest-directive` already expects, so the ingestion path needs no changes.
- **Command** (`commands/director-review.md`): runs `/jackal-director:director-packet` if no
  fresh packet exists, dispatches the director agent with the packet path, writes the memo
  to `docs/canon/packets/YYYY-MM-DD-memo.md`, and tells the human to review it and run
  `/jackal-director:ingest-directive` — which keeps its confirmation gates (locked decision).
- **Docs**: `director-loop` cadence section gains the fallback ladder — Fable chat
  (preferred: strongest reviewer, human in the loop end-to-end) → other strong-model chat →
  `/jackal-director:director-review` (automated review, human-gated ingestion).

The dispatch prompt repeats the no-subagents prohibition per repo convention, and adds:
"You have no repo access by design. Base every finding on the packet and canon documents
only; if the packet lacks the evidence for a judgment, say so in the memo rather than
guessing."

### C3 — Implementor continuation across phases (jackal-plan-and-execute)

**Problem:** `execute` Mode 1 dispatches a fresh implementor per phase ("no memory of prior
dispatches"). Each dispatch re-reads the project's structure, conventions, and the code the
previous phase just wrote. That was the only option when the harness was written; the Agent
tool now supports continuing a named agent (`SendMessage`), and long-lived workers that keep
context across subtasks beat spawn-and-block on both cost (cache reads) and coherence.

**Change:** In `execute` Mode 1:

- Phase 1 dispatches the implementor with a `name` (e.g. `impl-<issue#>`).
- Phases 2..N send the next phase file to the same agent via `SendMessage`, with the same
  per-phase content the fresh dispatch would have carried (phase path, working directory,
  no-subagents line).
- **Fallback to fresh dispatch** when: the continuation fails or the agent is gone; a review
  cycle found Critical issues (fix dispatches start clean so the fix isn't anchored on the
  reasoning that produced the bug); or `.jackal/harness-guidance.md` sets
  `implementor_continuation: off`.
- Scope boundary: continuation is **per issue**. A new issue always gets a new implementor.
  Parallel issues keep separate named agents. The reviewer is never continued (locked
  decision).

Files: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` (Mode 1 + Context
Strategy), `agents/implementor.md` (acknowledge follow-up phases may arrive in the same
session; treat each phase file as the complete spec for that phase),
`README.md` (architecture note: "stateless" becomes "stateless per issue").

### C4 — Sonnet review for Simple issues in backlog mode (jackal-plan-and-execute)

**Problem:** Backlog-mode Simple issues go implementor → PR with no machine review unless
security-sensitive. That economy made sense when review implied an Opus pass; at Sonnet 5
pricing a review pass on a Simple diff costs cents, and an unreviewed diff otherwise relies
entirely on downstream human PR review.

**Change:** In `execute` Step 5, Simple becomes: implementor → `reviewer` (Sonnet) → finish.
The review verdict feeds the existing fix loop (3 cycles then stop). Projects that want the
old behavior set `simple_review: off` in `.jackal/harness-guidance.md`. Update the Review
Routing table and the README's "Review is proportional to risk" principle (Simple → Sonnet
review, not none).

Files: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md`, `README.md`.

### C5 — Report cap can't eat findings (jackal-plan-and-execute)

**Problem:** `reviewer.md` says "**Report cap: 40 lines.**" Sonnet 5 follows output
constraints literally: on a large diff it will drop findings to satisfy the cap rather than
exceed it, and it won't tell you it did.

**Change:** Replace the cap rule in `reviewer.md` and `reviewer-deep.md` with:

> Keep the report tight — every line states a verdict, cites an issue with file:line, or
> reports a command result. Target 40 lines, but **never omit a Critical or Important
> finding to stay short**; the completeness of findings outranks the length target. Compress
> Minor findings to one line each or a count if space demands it.

Files: `plugins/jackal-plan-and-execute/agents/reviewer.md`, `agents/reviewer-deep.md`.

### C6 — Single-file routing read carve-out (jackal-plan-and-execute)

**Problem:** The delegation rule ("about to grep — stop and dispatch") is right as a default
but forces a full subagent spin-up when the orchestrator needs one named file to make a
routing decision (e.g. checking whether an issue's scope file exists or what a config key
says).

**Change:** Add one line to the Delegation Rules in `execute/SKILL.md` and the plugin
README:

> Exception: reading a **single, already-named file** to make a routing decision is fine.
> The line is investigation — if you'd need to search, follow references, or read a second
> file to understand the first, dispatch instead.

Files: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md`, `README.md`.

---

## Rollout

1. C1 + C2 together (one version bump of `jackal-director`): the reframing and the fallback
   path are one coherent story.
2. C3–C6 together (one version bump of `jackal-plan-and-execute`): all four touch the
   execute/review path and should be tested as a unit against a real backlog issue.
3. Root `README.md` update rides whichever lands second.
4. Each bump: `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` +
   `CHANGELOG.md` entry, per repo convention.

Verification: run one Standard issue end-to-end with continuation on (C3) and confirm the
phase-2 dispatch shows cache reads rather than a cold context; run one Simple issue and
confirm the Sonnet review fires (C4); run `/jackal-director:director-review` against this
repo's own packet and confirm the memo ingests cleanly (C2).

## Risks

- **C3 context contamination:** a confused implementor stays confused across phases. The
  review-cycle reset and the guidance kill-switch bound the blast radius; if it still causes
  trouble in practice, the fallback (fresh per phase) is one config line away.
- **C2 tool-restriction gaps:** frontmatter tool restrictions have known enforcement gaps in
  some contexts (same reason the no-nesting rule is doubled in prompts). The prompt-level
  "no repo access by design" instruction is the second layer; the memo format's mandatory
  evidence citations (packet section references) make violations visible.
- **C4 cost creep on high-churn backlogs:** many Simple issues × review pass adds spend.
  It's Sonnet-priced and capped at one pass per issue; the guidance override exists for
  projects that measure and disagree.
