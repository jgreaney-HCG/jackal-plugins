---
name: director-loop
description: How the Software Director review loop works - canon documents, haiku conformance agents, packets, and memos. Consult this skill whenever working on design plans or implementation plans in a repo that has docs/canon/, whenever files under the contracts package change, whenever the user mentions the Director, Fable review, contract registry, glossary, impact statements, or director packets, and before merging any branch in a repo where this plugin is installed.
---

# The Director Loop

This repo is governed by a two-tier review architecture. The harness (you,
in Claude Code) does research, planning, and implementation. A **Software
Director** - a stronger model in a separate chat session with **no repo
access** - reviews the system's evolution against canon and issues
directives. The two tiers communicate only through markdown documents. Your
obligations are: keep canon honest, produce the documents mechanically, and
apply directives faithfully.

## Canon (docs/canon/)

- `charter.md` - what the system is, its components, design theory,
  invariants. The Director's constitution.
- `registry.md` - every inter-component contract, generated/audited against
  the Pydantic models in the contracts package. **Code is the source of
  truth; the registry is the audited map.**
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
3. **Before the PR:** run `/contract-check` (execute's final review does this
   when canon exists). CLEAN or explained-FLAGGED is the bar.
4. **Never edit canon casually.** Charter and glossary changes go through
   the Director (packet -> memo -> `/ingest-directive`) or an explicit human
   decision recorded as an ADR. Registry sections may be updated to track
   code, since code is the source of truth there.

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

- Per branch: `/contract-check` before the PR.
- Per cycle (weekly, or every ~5 closed issues — the jackal-supervisor
  prompts when a packet is due): `/director-packet`, human uploads the packet
  to the Director session, brings back the memo, runs `/ingest-directive`.
- The Director's standing constraints land in
  `.jackal/design-guidance.md` / `.jackal/implementation-guidance.md`,
  which the jackal design and planning skills already consume - so Director
  directives automatically constrain the *next* epic's planning. That closing
  of the loop is the entire point.
