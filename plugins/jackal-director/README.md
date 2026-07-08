# jackal-director

Haiku-powered document manufacturing for a two-tier review architecture: the
jackal harness (Sonnet/Opus on Bedrock) does the work; a **Software Director**
— a fresh-context reviewer with no repo access, run on the strongest model
available (Fable in a chat session when you have it, otherwise any
strong-model chat) — reviews the system's evolution against canon documents
and issues directives. Its authority comes from independence, not model tier.
This plugin produces the paper that makes that possible, and closes the loop
back into the harness.

Director directives land in `.jackal/design-guidance.md` /
`.jackal/implementation-guidance.md`, which the jackal design and planning
skills already read — so a directive issued this cycle constrains the next
epic's planning automatically.

## Contents

**Agents:** four run on `model: haiku` with `tools: Bash, Read, Grep, Glob` — detection
and extraction only, mandatory evidence citations, never judgment, never subagents. The
fifth, `director`, is the Software Director itself — `model: opus`, `tools: Read` only (no
Bash/Grep/Glob/Write: no repo access, by design), used only by the automated review path:

| Agent | Input | Output |
|---|---|---|
| `delta-scribe` | git range | fixed-format delta digest |
| `contract-sentinel` | branch diff + registry | PASS/FLAG/ESCALATE checklist (C1-C5) |
| `lexicon-warden` | diff/doc + glossary | NEW/CONFLICT/SYNONYM-DRIFT table |
| `registry-drift-checker` | exported contract schemas + registry | IN-SYNC/STALE/UNDOCUMENTED/ORPHANED |
| `director` | canon docs + a director packet | numbered review memo (directives) |

**Commands:**

- `/jackal-director:canon-init` — scaffold `docs/canon/` (charter, registry, glossary, ADRs,
  impact statements)
- `/jackal-director:contract-check [base]` — pre-PR gate: sentinel + warden in parallel,
  report filed to `docs/canon/reports/`
- `/jackal-director:director-packet [since]` — assemble the cycle packet (digest + drift +
  open flags + canon changelog + your questions) for upload to the Director
- `/jackal-director:director-review [packet]` — automated Director path: dispatches the
  read-only `director` agent and writes its memo; ingestion into canon stays human-gated via
  `ingest-directive`
- `/jackal-director:ingest-directive <memo.md>` — classify the Director's memo into ADR
  stubs, `.jackal/` guidance bullets, glossary proposals, impact stubs, and
  GitHub issues — with human confirmation before anything is written

(Marketplace-installed commands are always namespaced `plugin:command`; a bare
`/canon-init` will not resolve.)

**Skill:** `director-loop` — standing obligations that wire the loop into
design/plan/execute work (read canon before designing, impact statements with
the plan, `/jackal-director:contract-check` before the PR).

## Contracts: Python and TypeScript

The registry header names the contracts package and the schema exporter; both
can also be set project-wide in `## Jackal Config`:

```
contracts_pkg: contracts/           # or ui/src/contracts/
schema_export_cmd: python -m contracts.export_schemas   # or: npm run export-schemas
```

Any exporter works as long as it emits one JSON Schema per contract model —
`model_json_schema()` for Pydantic, a typebox/zod export script for TypeScript.
The drift checker compares JSON Schemas; it never parses source.

## Setup

In the target repo:

```
/jackal-director:canon-init
```

Then hand-author the three documents that need a human: the charter, the
component map, and glossary confirmation. Draft the charter *with* the
Director — paste your README plus the charter template into the Director
session (Fable chat if you have it, otherwise any strong-model chat) and let
it interview you.

## Bedrock note

Agent frontmatter uses `model: haiku`, which Claude Code resolves through your
model configuration. On Bedrock, make sure the small/fast model maps to Haiku
4.5 (`ANTHROPIC_SMALL_FAST_MODEL` / `ANTHROPIC_DEFAULT_HAIKU_MODEL`, or your
settings.json model mapping; for cost attribution, point it at a Haiku
application inference profile ARN).

## Design rationale

The haiku agents are prompted as **court reporters, not commentators**: fixed
output templates, hard length caps, `path:line`/sha citations on every claim,
and an ESCALATE verdict instead of guessing. Anything requiring judgment routes
upward — to the PR review, to you, or to the Director packet. If you find
yourself wanting a haiku agent to "use its judgment," that item belongs to a
different tier.

Canon has a strict truth hierarchy: code is the source of truth for contracts
(the registry is an audited map); the charter and glossary are the source of
truth for intent and language (code drifting from them is the bug). The two
checkers point in opposite directions on purpose.
