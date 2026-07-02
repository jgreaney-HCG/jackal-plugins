---
description: Scaffold the docs/canon/ document tree (charter, registry, glossary, ADR log, impact statements) that the director-loop agents depend on
argument-hint: "[contracts package path, default: contracts/]"
---

Bootstrap the canon that every director-loop agent reads. Create the
following, skipping anything that already exists (never overwrite):

```
docs/canon/
├── charter.md
├── registry.md
├── glossary.md
├── adr/0001-record-architecture-decisions.md
├── impact/README.md
├── reports/
└── packets/
```

Templates:

**charter.md** - headings only, for the human (with Director help) to fill:
`# System Charter`, `## What this system is`, `## Components` (name, one
sentence, root path each), `## Design theory` (seed it with any principles
already evident in the repo or CLAUDE.md - e.g. a rule like "the LLM
decides, deterministic code computes" belongs here), `## Invariants`,
`## Out of scope`.

**registry.md** - header block first, then sections. Resolve the contracts
package from `$ARGUMENTS`, else `contracts_pkg` in the project's `## Jackal
Config`, else `contracts/`. Resolve the exporter from `schema_export_cmd` in
Jackal Config, else the Python default shown (for a TypeScript contracts
package, point it at the project's typebox/zod JSON-schema export script,
e.g. `npm run export-schemas`):

```markdown
# Contract Registry
Contracts package: <resolved path>
Schema exporter: <resolved command, e.g. python -m contracts.export_schemas or npm run export-schemas>
Generated sections below are maintained per-contract; the registry-drift-checker
agent audits them against the code. Code is the source of truth.

## Component Map
| Component | Root path | Owns contracts |
|-----------|-----------|----------------|

## <ContractName>
Owned by: <component> | Consumed by: <components>
| Field | Type | Required | Meaning |
```

Then, if the contracts package exists, enumerate its contract models (Pydantic
classes, or typebox/zod schemas in TypeScript) and create one stub section per
model with the fields table filled from the model definitions. If no contracts
package exists yet, note that in the file and move on - do not invent
contracts.

**glossary.md** - format contract at top, then seed entries:

```markdown
# Glossary
One `##` heading per term. Optional lines: `Aliases:` (accepted synonyms),
`Never:` (forbidden synonyms - the lexicon-warden flags these on sight).
```

Seed it by grepping the repo for candidate domain nouns (model names, enum
members, prominent docstring terms) and creating DRAFT-marked entries for
the ten most frequent, for the human to confirm or delete.

**adr/0001** - the standard "we will record architecture decisions" ADR,
plus the numbering and status conventions (Proposed/Accepted/Superseded).

**impact/README.md** - two paragraphs: an impact statement is required for
any change to the contracts package; filename is the branch or epic slug;
required sections are `## Contracts touched`, `## Change`, `## Consumers
affected`, `## ADR` (link or "none - non-breaking").

Finish by telling the user the three documents that need human authorship
before the loop is worth running (charter, glossary confirmation, component
map) and suggest drafting the charter WITH the Director: paste the repo's
README and this template into the Fable session and let the Director
interview them.
