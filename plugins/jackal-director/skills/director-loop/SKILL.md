---
name: director-loop
description: How the Software Director review loop works - canon documents, haiku conformance agents, packets, and memos. Consult this skill whenever working on design plans or implementation plans in a repo that has docs/canon/, whenever files under the contracts package change, whenever the user mentions the Director, Fable review, contract registry, glossary, impact statements, or director packets, and before merging any branch in a repo where this plugin is installed.
---

# The Director Loop

This repo is governed by a two-tier review architecture. The harness (you,
in Claude Code) does research, planning, and implementation. A **Software
Director** - a fresh-context reviewer with **no repo access**, run on the
strongest model available - reviews the system's evolution against canon and
issues directives. It sees only canon and the packet, never the code or the
conversation that produced it; its authority comes from that independence,
not from outranking the harness. The two tiers communicate only through
markdown documents. Your obligations are: keep canon honest, produce the
documents mechanically, and apply directives faithfully.

## Canon (docs/canon/)

There is exactly one canon per repo, at the repo root — a monorepo included.
The loop polices the seams *between* components, which per-component canons
cannot see; components keep their contract detail in their own code and docs
and appear in the one registry's Component Map.

- `charter.md` - what the system is, its components, design theory,
  invariants. The Director's constitution.
- `registry.md` - every inter-component contract, audited against the typed
  contract models it names: a single contracts package, or per-component
  contract sources listed in its Component Map. Sections are either detailed
  field tables (shared contracts with no better home) or index references to
  the owning component's model file. **Code is the source of truth; the
  registry is the audited map.**
- `glossary.md` - the ubiquitous language. `Never:` lines list forbidden
  synonyms.
- `adr/` - architecture decision records.
- `impact/` - one impact statement per branch/epic that touches contracts.
- `reports/`, `packets/` - machine output: conformance reports, director
  packets, review memos.

## Standing obligations during design/plan/execute work

1. **Design phase:** read charter.md and glossary.md before writing any
   design document (the jackal `design` skill does this when canon exists).
   Use glossary terms exactly; if the design needs a concept the glossary
   lacks, say so explicitly in the design doc rather than coining a term
   silently.
2. **Implementation planning:** if the plan touches any contract model, draft
   the impact statement in `docs/canon/impact/` as part of the plan, not
   after. A contract change without an impact statement will be flagged by
   contract-sentinel and stall the PR.
3. **Before the PR:** run `/jackal-director:contract-check` (execute's final review does this
   when canon exists). CLEAN or explained-FLAGGED is the bar.
4. **Never edit canon casually.** Charter and glossary changes go through
   the Director (packet -> memo -> `/jackal-director:ingest-directive`) or an explicit human
   decision recorded as an ADR. Registry sections may be updated to track
   code, since code is the source of truth there.

### Waiting for async work

When the director waits on dispatched async work, it uses the event-driven
watcher (`scripts/worktree-watcher.sh`), never scheduled foreground polling.
Foreground sleeps are ≤100s, comfortably under the Bash tool's 120s timeout.
Status is batched — no "still waiting" turns. A `STALLED` signal triggers the
verify-disk → instruct commit-and-report → resume-from-disk procedure documented
in full in the `execute` skill's "Waiting for async work" section — this is a
summary, not the canonical version.

### Relay rule and reinforced non-goal

The director never relays a subagent's progress or success claim without a
same-turn, cited disk observation backing it — this is
`verification-before-completion` applied to delegated work. No director message
asserts progress unbacked by a same-turn disk-verified observation, even when
skipping the check would be faster. The full relay rule lives in the `execute`
skill's Mode 1 Process step 3c; this is a summary, not the canonical version.

## The haiku agents (detection layer)

Four agents run on the small/fast model. They are deliberately confined to
**extraction and detection with mandatory evidence citations**; they never
judge, fix, or update canon. Their outputs feed either the merge gate or
the Director packet:

- `delta-scribe` - git range -> fixed-format digest
- `contract-sentinel` - diff vs registry -> PASS/FLAG/ESCALATE checklist
- `lexicon-warden` - diff/doc vs glossary -> NEW/CONFLICT/SYNONYM-DRIFT table
- `registry-drift-checker` - exported schemas vs registry prose ->
  IN-SYNC/STALE/UNDOCUMENTED/ORPHANED

Treat a FLAG from these agents as a fact to be dispositioned, not an
opinion to argue with. If a FLAG is wrong, the fix is usually to make canon
more precise, and that is itself worth recording.

## Cadence

- Per branch: `/jackal-director:contract-check` before the PR.
- Per cycle (weekly, or every ~5 closed issues — the jackal-supervisor
  prompts when a packet is due): `/jackal-director:director-packet`, then the review path,
  preferred first:
  1. **Fable chat (preferred):** strongest reviewer, human in the loop
     end-to-end — human uploads the packet to the Fable session, brings
     back the memo.
  2. **Other strong-model chat:** same manual flow, any strong-model chat
     session, when Fable is unavailable.
  3. **`/jackal-director:director-review` (automated):** the read-only
     director agent produces the memo itself, for when no human-run chat
     session is available this cycle.
  All three converge on the same next step: review the memo, then run
  `/jackal-director:ingest-directive`, which keeps its human-confirmation
  gates regardless of which path produced the memo.
- The Director's standing constraints land in
  `.jackal/design-guidance.md` / `.jackal/implementation-guidance.md`,
  which the jackal design and planning skills already consume - so Director
  directives automatically constrain the *next* epic's planning. That closing
  of the loop is the entire point.

## Operating discipline (autonomous cycles)

### Metadata-commit routing (preventive)

Backlog-metadata and issue-doc commits (labels, TODO.md bookkeeping, issue-doc
edits) still need a clear route to main. This is preventive, not a fix: an
audit of two full director sessions found zero direct-to-main pushes — every
push went through a feature branch, and this repo already has branch
protection on. The point is to decide the route *before* any further
tightening (e.g. `enforce_admins`-style admin-enforced protection), not after
it breaks something.

- Pick one: a fast-tracked PR for metadata-only changes, or a deliberately
  scoped and loudly-documented exception path. Either is fine; silence is not.
- Whatever is chosen must not reintroduce a direct-to-main fast path, and must
  preserve the "PR is the only completion path" invariant from the repo
  CLAUDE.md (`finish` / `jackal-finish-branch` never merge locally). If a
  bot/metadata exception is ever adopted, it must be a loud, explicit
  opt-out — consistent with that same CLAUDE.md note — not a quiet default.

### `/clear` context-growth discipline

The director loop accumulates a large transcript over an autonomous run
(audited median ~397K context per turn). At natural boundaries — a PR opens,
or an issue closes — prefer `/clear` and re-invoking the relevant skill with
the issue ID over continuing on a fat context, unless warm context is
actively needed for the immediately-next issue.
