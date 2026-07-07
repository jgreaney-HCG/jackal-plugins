---
description: Run the contract-sentinel and lexicon-warden agents against the current branch's diff and assemble a merge-gate report
argument-hint: "[base-ref, default: main]"
---

Run the pre-merge conformance gate for this branch.

Base ref: use `$ARGUMENTS` if provided, otherwise `main`.

1. Confirm the working tree is a git repo and `docs/canon/registry.md`
   exists. If the registry is missing, stop and tell the user to run
   `/jackal-director:canon-init` first - do not improvise checks without canon.

2. Launch **both** of the following as subagents, in a single message so they
   run in parallel:

```xml
<invoke name="Agent">
<parameter name="subagent_type">jackal-director:contract-sentinel</parameter>
<parameter name="description">Contract conformance check</parameter>
<parameter name="prompt">
Base ref: [base]
Working directory: [repo root]
Run your checklist against the diff and emit the verdict table.
</parameter>
</invoke>
<invoke name="Agent">
<parameter name="subagent_type">jackal-director:lexicon-warden</parameter>
<parameter name="description">Vocabulary drift check</parameter>
<parameter name="prompt">
Check the diff range [base]...HEAD against docs/canon/glossary.md.
Working directory: [repo root]
</parameter>
</invoke>
```

3. Assemble their two reports, verbatim and unedited, into
   `docs/canon/reports/contract-check-<branch-slug>-<YYYYMMDD>.md`, prefixed
   with a four-line header: branch, base, date, and a single overall status
   line computed as follows:
   - any ESCALATE in either report -> `ESCALATE`
   - else any FLAG / CONFLICT / SYNONYM-DRIFT -> `FLAGGED`
   - else -> `CLEAN`

4. Tell the user the overall status and, if FLAGGED or ESCALATE, list the
   findings briefly. Do not resolve findings yourself in this command; that
   is a separate decision. If the finding implicates canon itself (a
   contract that seems wrong, a glossary definition that no longer fits),
   note that it belongs in the next director packet rather than being fixed
   ad hoc.

Never edit the agents' verdicts. If you disagree with a FLAG, say so in your
summary to the user - but the report file keeps the raw record.
