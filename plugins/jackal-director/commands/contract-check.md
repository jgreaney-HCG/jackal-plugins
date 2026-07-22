---
description: Run the deterministic conformance pre-pass, then adjudicate its evidence packet with the contract-sentinel and lexicon-warden agents
argument-hint: "[base-ref, default: main]"
---

Run the pre-merge conformance gate for this branch. The heavy scanning is done
once, deterministically, by a script; the agents only adjudicate its bounded
output. This keeps the gate cheap and prevents the repo-wide crawls that once
made it run for 20+ minutes.

Base ref: use `$ARGUMENTS` if provided, otherwise `main`.

1. **Run the pre-pass.** From the repo root:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/conformance_prepass.py" --base <base> --repo-root .
   ```

   The script computes the diff, enforces a hard size cap, parses
   `docs/canon/registry.md` + `docs/canon/glossary.md`, runs the deterministic
   checks (C1/C3/C5), and prints a JSON **evidence packet** on stdout. Capture
   that JSON — it is the sole input to both agents.

2. **Branch on `status`:**
   - `status: "ESCALATE"` (also exit code 2) → do **not** dispatch any agent.
     Report the packet's `reason` to the user and stop. Two common reasons:
     no registry (tell them to run `/jackal-director:canon-init` first), or the
     diff exceeds the linter caps (this is a human/stronger-model review, not a
     linter pass — say so, with the file/line counts).
   - `status: "OK"` → continue.

3. **Dispatch both agents in a single message so they run in parallel.** Paste
   the **entire evidence packet JSON** into each prompt — the agents are
   read-only adjudicators and must not crawl the repo. Both run on **Haiku**:

```xml
<invoke name="Agent">
<parameter name="subagent_type">jackal-director:contract-sentinel</parameter>
<parameter name="description">Adjudicate contract evidence packet</parameter>
<parameter name="model">haiku</parameter>
<parameter name="prompt">
You are adjudicating a pre-computed contract evidence packet. Do NOT search,
grep, git, or crawl the repo — you have only Read, for opening a specific cited
path:line if a finding is ambiguous. Do not dispatch subagents.

Evidence packet (JSON):
[paste the full JSON from step 1 here]

Confirm the deterministic C1/C3/C5 findings and describe the C2 surface changes,
then emit your verdict table exactly as your agent definition specifies.
</parameter>
</invoke>
<invoke name="Agent">
<parameter name="subagent_type">jackal-director:lexicon-warden</parameter>
<parameter name="description">Adjudicate lexicon evidence packet</parameter>
<parameter name="model">haiku</parameter>
<parameter name="prompt">
You are adjudicating a pre-computed lexicon evidence packet. Do NOT search,
grep, git, or crawl the repo — you have only Read, for opening docs/canon/glossary.md
to quote a definition when adjudicating an L2 conflict. Do not dispatch subagents.

Evidence packet (JSON):
[paste the full JSON from step 1 here]

Adjudicate the new-term (L1), conflict (L2), and forbidden-synonym (L3)
candidates and emit your report exactly as your agent definition specifies.
</parameter>
</invoke>
```

4. Assemble their two reports, verbatim and unedited, into
   `docs/canon/reports/contract-check-<branch-slug>-<YYYYMMDD>.md`, prefixed
   with a four-line header: branch, base, date, and a single overall status
   line computed as follows:
   - the pre-pass returned ESCALATE (handled in step 2) → `ESCALATE`
   - else any FLAG / CONFLICT / SYNONYM-DRIFT in either report → `FLAGGED`
   - else → `CLEAN`

5. Tell the user the overall status and, if FLAGGED, list the findings
   briefly. Do not resolve findings yourself in this command; that is a
   separate decision. If a finding implicates canon itself (a contract that
   seems wrong, a glossary definition that no longer fits), note that it
   belongs in the next director packet rather than being fixed ad hoc.

6. If the registry header carries a `Boundary enforcement:` line (the repo
   machine-enforces component boundaries with import-linter, ESLint boundary
   rules, or similar), say so in your summary: canon is the authority and that
   linter is its enforcement arm, so the sentinel's C3 is a second witness, not
   the primary gate. A C3 FLAG on an import the linter permits — or a linter
   failure on an import C3 passed — means the two rule sets have drifted; that
   disagreement itself belongs in the next director packet. (C3 findings are
   heuristic and marked `confidence: LOW` for this reason.)

Never edit the agents' verdicts. If you disagree with a FLAG, say so in your
summary to the user — but the report file keeps the raw record.
