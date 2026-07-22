---
description: Run the contract-sentinel and lexicon-warden agents against the current branch's diff and assemble a merge-gate report
argument-hint: "[base-ref, default: main]"
---

> **⚠️ TEMPORARILY DISABLED.** The `contract-sentinel` and `lexicon-warden`
> agents are disabled pending a cost fix (an uncapped run consumed ~14M tokens
> over 23 minutes; see CHANGELOG). **Do not dispatch either agent.** When this
> command is invoked, tell the user the conformance gate is temporarily
> disabled and stop — do not run the steps below. They are retained for when
> the agents are re-enabled.

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

Do not dispatch or invoke any subagents - do the work directly with your own
tools.
</parameter>
</invoke>
<invoke name="Agent">
<parameter name="subagent_type">jackal-director:lexicon-warden</parameter>
<parameter name="description">Vocabulary drift check</parameter>
<parameter name="prompt">
Check the diff range [base]...HEAD against docs/canon/glossary.md.
Working directory: [repo root]

Do not dispatch or invoke any subagents - do the work directly with your own
tools.
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

5. If the registry header carries a `Boundary enforcement:` line (the repo
   machine-enforces component boundaries with import-linter, ESLint boundary
   rules, or similar), say so in your summary: canon is the authority and
   that linter is its enforcement arm, so the sentinel's C3 is a second
   witness, not the primary gate. A C3 FLAG on an import the linter permits
   — or a linter failure on an import C3 passed — means the two rule sets
   have drifted; that disagreement itself belongs in the next director
   packet.

Never edit the agents' verdicts. If you disagree with a FLAG, say so in your
summary to the user - but the report file keeps the raw record.
