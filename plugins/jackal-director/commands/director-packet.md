---
description: Assemble a director packet - delta digest, drift report, open flags, canon changelog - as a single markdown file to hand to the Software Director, a fresh-context reviewer with no repo access (Fable chat when available, else any strong-model chat or the automated director-review path)
argument-hint: "[since, e.g. '2026-06-24' or a ref; default: date of last packet, else 7 days]"
---

Build the director packet: the single document the human will upload to the
Software Director - whichever review path this cycle uses (Fable chat,
another strong-model chat, or the automated `director-review` agent). The
Director has no repo access - this packet, plus the canon documents already
in its project knowledge, is everything it sees. Completeness and honesty of
the packet is therefore the whole ballgame.

Determine the range:
- If `$ARGUMENTS` is given, use it as the start (date or ref) to HEAD.
- Else find the newest file in `docs/canon/packets/` and use its date.
- Else default to the last 7 days:
  `$(git rev-list -1 --before="7 days ago" main)..main`.

Then:

1. Launch as subagents, in a single message so they run in parallel:

```xml
<invoke name="Agent">
<parameter name="subagent_type">jackal-director:delta-scribe</parameter>
<parameter name="description">Delta digest for director packet</parameter>
<parameter name="prompt">
Range: [range]
Working directory: [repo root]
Emit the fixed-format delta digest.
</parameter>
</invoke>
<invoke name="Agent">
<parameter name="subagent_type">jackal-director:registry-drift-checker</parameter>
<parameter name="description">Registry drift for director packet</parameter>
<parameter name="prompt">
Working directory: [repo root]
Compare exported contract schemas against docs/canon/registry.md.
</parameter>
</invoke>
```

2. While they run, gather (yourself, main model):
   - **Open flags:** scan `docs/canon/reports/` for contract-check reports
     since the range start; extract every FLAG/ESCALATE not marked resolved.
   - **Canon changelog:** `git log --oneline <range> -- docs/canon/` so the
     Director knows if the charter/registry/glossary it has in project
     knowledge is stale and needs re-uploading. If any canon file changed,
     say so prominently.
   - **Questions for the Director:** ask the user if they have specific
     questions to pose this cycle (design tensions, upcoming epics, anything
     that felt "off"). Include them verbatim in their own section.

3. Write `docs/canon/packets/packet-<YYYY-MM-DD>.md` with this structure:

   ```markdown
   # Director Packet - <date>
   Range: <range> | Canon changed this cycle: yes/no (list)

   ## How to read this packet
   (three fixed sentences:) This packet was assembled mechanically from git
   history and automated conformance checks; narrative sections are
   extractive, not evaluative. Sections marked ESCALATE are items the
   automation could not classify. Your standing brief: review against the
   charter, registry, glossary, and ADR log in project knowledge; flag
   contradictions with canon, silent contract redefinitions, vocabulary
   drift, and divergence between components; respond with a review memo
   containing numbered directives.

   ## Questions from the developer
   ## Delta digest        (delta-scribe output, verbatim)
   ## Registry drift      (registry-drift-checker output, verbatim)
   ## Open flags          (from step 2)
   ## Canon changelog     (from step 2)
   ```

4. Report the packet path to the user and remind them: if canon changed this
   cycle, re-upload the changed canon files to the Director's project
   knowledge *before* uploading the packet.

Do not editorialize inside the packet beyond the fixed "How to read"
section. Do not omit unflattering findings; the Director reviewing a
sanitized record is worse than no Director at all.
