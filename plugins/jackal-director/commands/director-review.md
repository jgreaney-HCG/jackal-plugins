---
description: Run the automated Director path — build a packet if none is fresh, dispatch the read-only director agent, write its memo to docs/canon/packets/, and hand off to ingest-directive
argument-hint: "[packet path; default: newest in docs/canon/packets/, else build one]"
---

Run the automated Director path: a fresh-context, read-only Opus agent
reviews the current packet against canon and returns a numbered memo, for
when no Fable or other strong-model chat session is available this cycle.

1. **Confirm canon exists.** Check that `docs/canon/registry.md` (or the
   `docs/canon/` directory) exists. If not, stop and tell the user to run
   `/jackal-director:canon-init` first — the director agent has nothing to
   review without canon.

2. **Resolve the packet.**
   - If `$ARGUMENTS` names a packet path, use it.
   - Else find the newest `docs/canon/packets/packet-*.md`.
   - If none exists, or the newest one predates the latest canon/commit
     activity and is therefore stale, run `/jackal-director:director-packet`
     first to build a fresh one, then use its path.
   - State which packet path is being used before dispatching the agent.

3. **Dispatch the director agent** with the packet path, using an XML
   `<invoke>` block. The prompt MUST repeat both the no-subagents
   prohibition and the no-repo-access instruction (belt-and-braces with the
   agent's own frontmatter/body):

```xml
<invoke name="Agent">
<parameter name="subagent_type">jackal-director:director</parameter>
<parameter name="description">Automated Director review of the cycle packet</parameter>
<parameter name="prompt">
Packet path: [resolved packet path]
Working directory: [repo root]

Read the packet at the path above and the canon documents under docs/canon/
(charter, registry, glossary, adr). Review the system's evolution against
canon and emit your numbered review memo in the exact format your
instructions define.

You have no repo access by design. Base every finding on the packet and
canon documents only; if the packet lacks the evidence for a judgment, say
so in the memo rather than guessing.

Never dispatch or invoke other subagents.
</parameter>
</invoke>
```

4. **Write the memo.** Take the agent's returned memo text and write it
   verbatim to `docs/canon/packets/YYYY-MM-DD-memo.md` (today's date). Do
   not edit the agent's verdicts.

5. **Hand off.** Tell the human: the memo is at `<path>`; review it, then
   run `/jackal-director:ingest-directive <path>` to apply its directives.
   State explicitly that this automates the *review*, never the *acceptance
   into canon* — `ingest-directive`'s human-confirmation gates are
   unchanged, so the memo never auto-applies.
