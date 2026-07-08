---
description: Ingest a review memo from the Software Director - turn its directives into ADR stubs, glossary entries, and .jackal guidance updates, with human confirmation at each step
argument-hint: "<path to the Director's review memo .md>"
---

Close the Director loop: take the review memo the user brought back from the
Director - a Fable chat, another strong-model chat, or the automated
`/jackal-director:director-review` path - and merge its directives into the places the harness
actually reads. This command is path-agnostic: it ingests a memo file
regardless of which path produced it. This is a judgment task -
run it yourself on the main model, never delegate it to a haiku agent.

Input: the memo at `$ARGUMENTS`. If no path given, ask for one.

1. Read the memo. Extract its numbered directives. For each, classify:
   - **ARCHITECTURE DECISION** -> becomes an ADR stub in `docs/canon/adr/`
     (next number, status: Proposed, context quoted from the memo, decision
     as stated, consequences left for the human to complete)
   - **STANDING CONSTRAINT** -> becomes a bullet in
     `.jackal/design-guidance.md` and/or
     `.jackal/implementation-guidance.md` (choose based on whether it
     constrains design or implementation; quote the memo and date it)
   - **VOCABULARY RULING** -> becomes a glossary edit proposal (new entry,
     amended definition, or a `Never:` line)
   - **CONTRACT CHANGE** -> becomes an entry in a new impact statement stub
     in `docs/canon/impact/` plus a note that the Pydantic model change is
     implementation work for a future issue - do not change contract code
     from this command
   - **TASK** -> list it for the user, and offer to create it as a GitHub
     issue via the supervisor's create workflow (dedup search, labels, epic
     linkage); do not silently absorb work items into guidance files

2. Present the full classification to the user as a table BEFORE writing
   anything. The Director advises; the human decides. Ask which items to
   apply (default: all, but the user may strike any).

3. Apply only the approved items. Show a diff summary of every file touched.
   Do not commit; leave staging and committing to the user.

4. Flag conflicts explicitly: if a directive contradicts an existing ADR,
   glossary entry, or guidance bullet, do not overwrite - present both texts
   side by side and ask. A Director memo does not automatically outrank
   prior canon; contradictions between the two are precisely the signal this
   whole system exists to surface.

5. File the memo itself at `docs/canon/packets/memo-<date-of-packet>.md` if
   it is not already inside the repo, so the packet/memo pairs form a
   complete correspondence record over time.
