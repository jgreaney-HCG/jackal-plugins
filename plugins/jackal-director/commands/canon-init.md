---
description: Scaffold the docs/canon/ document tree (charter, registry, glossary, ADR log, impact statements) that the director-loop agents depend on
argument-hint: "[contracts package path, default: autodetect]"
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
├── reports/.gitkeep
└── packets/.gitkeep
```

`reports/` and `packets/` start empty and git does not track empty
directories — the `.gitkeep` files keep the tree intact across a fresh clone.

**One canon per repo.** A monorepo still gets exactly one canon, at the repo
root. The loop polices the seams *between* components — cross-component
imports, shared vocabulary, consumers outside the component — and per-module
canons are blind to exactly those seams; N glossaries also drift apart, which
is the disease lexicon-warden treats. Components keep their contract detail in
their own code and docs; the registry's per-component rows (below) are the
monorepo affordance. Component-specific decisions escalate as scoped ADRs in
the one `adr/` tree.

# Survey the repo first

Before writing templates, determine two things:

**How contracts are published** — this picks the registry mode:

- **Single contracts package:** one package (e.g. `contracts/`,
  `ui/src/contracts/`) owns every cross-component model. Resolve it from
  `$ARGUMENTS`, else `contracts_pkg` in the project's `## Jackal Config`
  (CLAUDE.md), else a `contracts/` directory if one exists.
- **Per-component contracts:** no single package; each component owns its
  published models (e.g. `packages/modules/*/…/api/contracts.py` in a
  monorepo). Use this mode when you find typed contract models living inside
  the components themselves.

**Whether boundaries are already machine-enforced** — look for import-linter
(`[tool.importlinter]` in pyproject.toml), ESLint boundary rules, Nx module
boundaries, or similar in CI. If found, the canon must cross-reference it
rather than restate it: the canon is the human-readable authority, the linter
is its enforcement arm for the invariants it can check. Two systems silently
asserting the same rule drift apart; a cross-reference keeps one of them
authoritative.

Likewise, if the repo already has curated standards docs (`docs/standards/`
or equivalent), the canon layers on top of them — governance and review in
`docs/canon/`, durable how-to conventions where they already live. Do not
migrate or duplicate their content.

# Templates

**charter.md** - headings only, for the human (with Director help) to fill:
`# System Charter`, `## What this system is`, `## Components` (name, one
sentence, root path each), `## Design theory` (seed it with any principles
already evident in the repo or CLAUDE.md - e.g. a rule like "the LLM
decides, deterministic code computes" belongs here), `## Invariants`,
`## Out of scope`. If boundaries are machine-enforced, seed `## Invariants`
with a cross-reference line, e.g. "Module independence — declared here,
enforced by lint-imports (root pyproject.toml)".

**registry.md** - header block, then the Component Map, then one section per
contract. The header has two forms.

Single-package repos:

```markdown
# Contract Registry
Contracts package: <resolved path>
Schema exporter: <resolved command, e.g. python -m contracts.export_schemas or npm run export-schemas>
```

(Resolve the exporter from `schema_export_cmd` in Jackal Config, else the
Python default shown; for a TypeScript contracts package, point it at the
project's typebox/zod JSON-schema export script.)

Per-component repos:

```markdown
# Contract Registry
Contracts: per-component (see Component Map)
```

Either form, when boundaries are machine-enforced, adds:

```markdown
Boundary enforcement: <tool> (<config path>)
```

Then, in both forms:

```markdown
Code is the source of truth; the registry is the audited map — the
registry-drift-checker agent audits it against the code.

## Component Map
| Component | Root path | Contract source | Exporter |
|-----------|-----------|-----------------|----------|
```

`Contract source` is the file or package where that component's published
models live; `Exporter` is an optional per-component schema export command
(`-` means the drift checker imports the models directly). Single-package
repos put `-` in both columns and rely on the header lines.

Contract sections come in two forms — choose per contract:

- **Detailed** — full field table, for shared/platform contracts that have no
  better home than the registry:

```markdown
## <ContractName>
Owned by: <component> | Consumed by: <components>
| Field | Type | Required | Meaning |
```

- **Index** — a reference to the typed model file, which stays the source of
  truth. This is the norm for per-component repos: transcribing fields the
  component already owns duplicates the model and *creates* the drift the
  checker exists to catch.

```markdown
## <ContractName>
Owned by: <component> | Consumed by: <components>
Source: <path to the defining model file>
```

Finally, enumerate the actual contract models (Pydantic classes, or
typebox/zod schemas in TypeScript) found in the contract sources and create
one section per model — detailed stubs with fields filled from the model
definitions in single-package mode, index sections in per-component mode. If
no contract sources exist yet, note that in the file and move on - do not
invent contracts.

**glossary.md** - format contract at top, then seed entries:

```markdown
# Glossary
One `##` heading per term. Optional lines: `Aliases:` (accepted synonyms),
`Never:` (forbidden synonyms - the lexicon-warden flags these on sight).
```

Seed it from the most curated sources first: existing standards docs
(`docs/standards/`, ADRs) and the `Contracts` / `Invariants` sections of root
and per-component CLAUDE.md files — terms defined there are already
human-vetted, so carry the definition over and cite the source doc. Only then
grep the repo for candidate domain nouns (model names, enum members,
prominent docstring terms) to round out roughly ten entries. Mark every entry
DRAFT for the human to confirm or delete; a frequency grep alone produces
noise and misses distinctions between similarly named concepts.

**adr/0001** - the standard "we will record architecture decisions" ADR,
plus the numbering and status conventions (Proposed/Accepted/Superseded).

**impact/README.md** - two paragraphs: an impact statement is required for
any change to a contract source (the contracts package, or any path in the
Component Map's `Contract source` column); filename is the branch or epic
slug; required sections are `## Contracts touched`, `## Change`,
`## Consumers affected`, `## ADR` (link or "none - non-breaking").

Finish by telling the user the three documents that need human authorship
before the loop is worth running (charter, glossary confirmation, component
map) and suggest drafting the charter WITH the Director: paste the repo's
README and this template into the Director session (Fable chat if you have
it, otherwise any strong-model chat) and let it interview them.
