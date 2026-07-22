#!/usr/bin/env python3
"""Deterministic pre-pass for the director conformance gate.

This script does the O(repo) work of the contract-sentinel and lexicon-warden
agents *once, cheaply, with no model*: it computes the branch diff, enforces a
hard size cap, parses the contract registry and glossary, runs the checks that
are fully deterministic, and extracts a small, bounded "evidence packet" of
candidates for the handful of checks that genuinely need a model to adjudicate.

The packet it prints on stdout (JSON) is what a read-only Haiku agent receives
inline — so the agent never greps the repo, never grows its context, and cannot
turn into a 23-minute, 14-million-token grind. If the diff is too large the
script emits status ESCALATE and the caller must not dispatch any agent.

Deterministic checks done here (no model):
  C1  impact statement present for touched contract sources
  C3  cross-component imports in added lines (Python, best-effort via Component Map)
  C5  breaking contract change (removed/renamed field) without an ADR reference

Candidates extracted here, adjudicated by the agent (model):
  C2  contract-surface changes  -> changed field/annotation lines per model
  L1  new domain term           -> new class / model / enum names in added lines
  L2  term used vs definition    -> glossary terms + the added lines that mention them
  L3  synonym drift              -> glossary Never: entries + added lines that hit them

Stdlib only. Python 3.10+.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# --- caps -------------------------------------------------------------------
# These bound the work *before* any model is involved. A branch that exceeds
# them is a review-by-human situation, not a linter situation.
DEFAULT_MAX_FILES = 60
DEFAULT_MAX_DIFF_LINES = 4000
# Bounds on the evidence packet handed to the agent, so its input can't blow up
# even on a diff that squeaks under the diff cap.
MAX_CANDIDATES_PER_CHECK = 40
MAX_SNIPPET_LINES = 200


@dataclass
class Component:
    name: str
    root: str  # repo-relative, no trailing slash
    contract_sources: list[str] = field(default_factory=list)


@dataclass
class GlossaryTerm:
    term: str
    aliases: list[str] = field(default_factory=list)
    never: list[str] = field(default_factory=list)


# --- git --------------------------------------------------------------------


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def merge_base(repo_root: Path, base: str) -> str:
    return _git(repo_root, "merge-base", base, "HEAD").strip()


def changed_files(repo_root: Path, mbase: str) -> list[str]:
    out = _git(repo_root, "diff", "--name-only", f"{mbase}..HEAD")
    return [line for line in out.splitlines() if line.strip()]


def diff_stat(repo_root: Path, mbase: str) -> tuple[int, int]:
    """Return (files_changed, total_lines_changed) from --numstat."""
    out = _git(repo_root, "diff", "--numstat", f"{mbase}..HEAD")
    files = 0
    lines = 0
    for row in out.splitlines():
        parts = row.split("\t")
        if len(parts) < 3:
            continue
        files += 1
        added, removed = parts[0], parts[1]
        # binary files show "-"; count them as a file but 0 lines
        lines += (int(added) if added.isdigit() else 0) + (
            int(removed) if removed.isdigit() else 0
        )
    return files, lines


def added_lines(repo_root: Path, mbase: str, pathspec: list[str] | None = None) -> dict[str, list[tuple[int, str]]]:
    """Map each changed file -> list of (new_line_number, added_line_text).

    Only '+' lines (added/modified), never context or '-' lines. This is the
    exact surface both agents were *supposed* to check.
    """
    args = ["diff", "--unified=0", f"{mbase}..HEAD"]
    if pathspec:
        args += ["--", *pathspec]
    out = _git(repo_root, *args)
    result: dict[str, list[tuple[int, str]]] = {}
    cur: str | None = None
    new_ln = 0
    for line in out.splitlines():
        if line.startswith("diff --git "):
            cur = None
            continue
        if line.startswith("+++ "):
            path = line[4:].strip()
            if path == "/dev/null":
                cur = None
            else:
                cur = path[2:] if path.startswith("b/") else path
                result.setdefault(cur, [])
            continue
        if line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            new_ln = int(m.group(1)) if m else 0
            continue
        if cur is None:
            continue
        if line.startswith("+"):
            result[cur].append((new_ln, line[1:]))
            new_ln += 1
    return result


# --- registry / glossary parsing -------------------------------------------


def _unbacktick(cell: str) -> str:
    return cell.strip().strip("`").strip()


def parse_component_map(registry_text: str) -> list[Component]:
    """Parse the '## Component Map' markdown table.

    Columns: Component | Root path | Contract source | Exporter.
    'none (...)' or '-' in Contract source means no owned contract file.
    """
    lines = registry_text.splitlines()
    comps: list[Component] = []
    in_map = False
    header_seen = False
    for line in lines:
        if line.strip().lower().startswith("## component map"):
            in_map = True
            continue
        if in_map and line.startswith("## "):
            break  # next section
        if not in_map:
            continue
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        joined = "".join(cells).replace(" ", "").replace("-", "")
        if not header_seen:
            # skip the header row and the |---|---| separator
            if "component" in cells[0].lower():
                header_seen = True
                continue
            if joined == "":
                header_seen = True
                continue
        if set("".join(cells)) <= set("-: |"):
            continue  # separator row
        name = cells[0].strip()
        root = _unbacktick(cells[1]).rstrip("/")
        src_cell = cells[2].strip()
        sources: list[str] = []
        low = src_cell.lower()
        if not (low.startswith("none") or src_cell in {"-", "—", ""}):
            # a cell may list several backticked paths joined by '+' or ','
            for tok in re.findall(r"`([^`]+)`", src_cell):
                tok = tok.strip()
                # keep only path-ish tokens (skip prose like 'catalog.json format')
                if "/" in tok or tok.endswith((".py", ".ts", ".json")):
                    sources.append(tok)
        if name and root:
            comps.append(Component(name=name, root=root, contract_sources=sources))
    return comps


def parse_glossary(glossary_text: str) -> list[GlossaryTerm]:
    terms: list[GlossaryTerm] = []
    cur: GlossaryTerm | None = None
    for line in glossary_text.splitlines():
        if line.startswith("## "):
            cur = GlossaryTerm(term=line[3:].strip())
            terms.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r"\s*Aliases:\s*(.+)", line)
        if m:
            cur.aliases = [a.strip() for a in re.split(r"[,;]", m.group(1)) if a.strip()]
            continue
        m = re.match(r"\s*Never:\s*(.+)", line)
        if m:
            cur.never = [a.strip() for a in re.split(r"[,;]", m.group(1)) if a.strip()]
    return terms


# --- component resolution ---------------------------------------------------


def component_of_path(path: str, comps: list[Component]) -> str | None:
    """Longest-root-prefix match."""
    best: str | None = None
    best_len = -1
    for c in comps:
        root = c.root + "/" if c.root else ""
        if path == c.root or (root and path.startswith(root)):
            if len(c.root) > best_len:
                best = c.name
                best_len = len(c.root)
    return best


def _is_contract_source(path: str, comps: list[Component]) -> bool:
    for c in comps:
        for src in c.contract_sources:
            full = f"{c.root}/{src}" if c.root and not src.startswith(c.root) else src
            if path == full or path == src or path.endswith("/" + src):
                return True
    return False


# --- deterministic checks ---------------------------------------------------

IMPORT_RE = re.compile(r"^\s*(?:from\s+([.\w]+)\s+import\b|import\s+([.\w]+))")
# breaking-change signals in a contract source's *removed* lines are computed
# from the diff separately; here we scan added lines for the field-level shape.
FIELD_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*[:=]")
CLASS_RE = re.compile(r"^\s*class\s+([A-Za-z_]\w*)")
ENUM_MEMBER_RE = re.compile(r"^\s*([A-Z][A-Z0-9_]+)\s*=")


def check_c1_impact(
    changed: list[str], comps: list[Component], impact_dir: Path, branch: str, commit_slugs: list[str]
) -> list[dict]:
    touched_sources = [p for p in changed if _is_contract_source(p, comps)]
    if not touched_sources:
        return []
    # An impact statement whose filename or header references the branch/epic.
    # Match the branch slug (last path component) as well as the full name, so
    # a `feature/foo` branch matches a flat `foo.md` impact file.
    slugs = {branch, branch.split("/")[-1], *commit_slugs}
    slugs = {s for s in slugs if s}
    found = False
    if impact_dir.is_dir():
        for f in impact_dir.rglob("*.md"):
            stem = f.stem
            if any(s and (s in stem or stem in s) for s in slugs):
                found = True
                break
            try:
                head = f.read_text(encoding="utf-8", errors="replace")[:500]
            except OSError:
                head = ""
            if any(s and s in head for s in slugs):
                found = True
                break
    if found:
        return []
    return [
        {
            "check": "C1",
            "verdict": "FLAG",
            "summary": "contract source(s) modified but no impact statement references this branch/epic",
            "evidence": {"touched_sources": touched_sources[:MAX_CANDIDATES_PER_CHECK], "branch": branch},
        }
    ]


def check_c3_cross_component(
    adds: dict[str, list[tuple[int, str]]], comps: list[Component]
) -> list[dict]:
    """Best-effort: flag added Python imports whose target module maps to a
    different component's root than the importing file. Marked confidence LOW
    because import->path resolution is heuristic; a human/agent confirms."""
    findings: list[dict] = []
    # crude module->component map from roots (dotted form of the root path)
    for path, lines in adds.items():
        if not path.endswith(".py"):
            continue
        src_comp = component_of_path(path, comps)
        if not src_comp:
            continue
        for ln, text in lines:
            m = IMPORT_RE.match(text)
            if not m:
                continue
            mod = (m.group(1) or m.group(2) or "").strip()
            if not mod or mod.startswith("."):
                continue  # relative import stays in-component
            top = mod.split(".")[0]
            # does this top-level package name correspond to another component?
            for c in comps:
                if c.name == src_comp:
                    continue
                root_last = c.root.rstrip("/").split("/")[-1]
                if top == root_last or top.replace("_", "") == root_last.replace("_", ""):
                    if _is_contract_source_module(mod, c):
                        continue  # importing a contract surface is allowed
                    findings.append(
                        {
                            "check": "C3",
                            "verdict": "FLAG",
                            "confidence": "LOW",
                            "summary": f"{src_comp} imports {mod} (looks like {c.name})",
                            "evidence": {"path": path, "line": ln, "text": text.strip()},
                        }
                    )
                    break
            if len(findings) >= MAX_CANDIDATES_PER_CHECK:
                return findings
    return findings


def _is_contract_source_module(mod: str, comp: Component) -> bool:
    for src in comp.contract_sources:
        stem = src.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        if stem and stem in mod:
            return True
    return False


def check_c5_breaking_without_adr(
    repo_root: Path,
    mbase: str,
    changed: list[str],
    comps: list[Component],
    impact_dir: Path,
    branch: str,
    commit_msgs: str,
) -> tuple[list[dict], list[dict]]:
    """Detect removed/renamed field lines in contract sources (breaking) and,
    if present, require an ADR reference somewhere in impact/ or commit msgs.

    Returns (c5_findings, c2_candidates) — the removed/added field lines double
    as the C2 surface-change candidates the agent describes."""
    sources = [p for p in changed if _is_contract_source(p, comps)]
    if not sources:
        return [], []
    removed: list[dict] = []
    added: list[dict] = []
    out = _git(repo_root, "diff", "--unified=0", f"{mbase}..HEAD", "--", *sources)
    cur = None
    for line in out.splitlines():
        if line.startswith("+++ "):
            p = line[4:].strip()
            cur = p[2:] if p.startswith("b/") else p
            continue
        if cur is None or line.startswith("@@") or line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("-"):
            fm = FIELD_RE.match(line[1:])
            if fm:
                removed.append({"path": cur, "field": fm.group(1), "text": line[1:].strip()})
        elif line.startswith("+"):
            fm = FIELD_RE.match(line[1:])
            if fm:
                added.append({"path": cur, "field": fm.group(1), "text": line[1:].strip()})
    c2_candidates = (removed + added)[:MAX_CANDIDATES_PER_CHECK]
    if not removed:
        return [], c2_candidates
    # a removed field = potential breaking change; look for an ADR reference
    adr_re = re.compile(r"ADR-\d|docs/canon/adr/")
    has_adr = bool(adr_re.search(commit_msgs))
    branch_slug = branch.split("/")[-1]
    if not has_adr and impact_dir.is_dir():
        for f in impact_dir.rglob("*.md"):
            if branch_slug and branch_slug in f.stem:
                try:
                    if adr_re.search(f.read_text(encoding="utf-8", errors="replace")):
                        has_adr = True
                        break
                except OSError:
                    pass
    if has_adr:
        return [], c2_candidates
    return (
        [
            {
                "check": "C5",
                "verdict": "FLAG",
                "summary": "field(s) removed from a contract source (potential breaking change) with no ADR reference",
                "evidence": {"removed_fields": removed[:MAX_CANDIDATES_PER_CHECK]},
            }
        ],
        c2_candidates,
    )


# --- candidate extraction for the agent (L1/L2/L3) --------------------------


def extract_lexicon_candidates(
    adds: dict[str, list[tuple[int, str]]], glossary: list[GlossaryTerm]
) -> dict:
    known: set[str] = set()
    for t in glossary:
        known.add(t.term.lower())
        for a in t.aliases:
            known.add(a.lower())
    never_map: list[dict] = []
    for t in glossary:
        for n in t.never:
            never_map.append({"forbidden": n, "term": t.term})

    l1_candidates: list[dict] = []
    seen_terms: set[str] = set()
    for path, lines in adds.items():
        for ln, text in lines:
            for rx in (CLASS_RE, ENUM_MEMBER_RE):
                m = rx.match(text)
                if not m:
                    continue
                name = m.group(1)
                if name.lower() in known or name.lower() in seen_terms:
                    continue
                seen_terms.add(name.lower())
                l1_candidates.append({"term": name, "path": path, "line": ln, "text": text.strip()})
                break
            if len(l1_candidates) >= MAX_CANDIDATES_PER_CHECK:
                break

    # L3: added lines that literally contain a forbidden synonym
    l3_hits: list[dict] = []
    for path, lines in adds.items():
        for ln, text in lines:
            for entry in never_map:
                if re.search(rf"\b{re.escape(entry['forbidden'])}\b", text, re.IGNORECASE):
                    l3_hits.append(
                        {
                            "forbidden": entry["forbidden"],
                            "canonical_term": entry["term"],
                            "path": path,
                            "line": ln,
                            "text": text.strip(),
                        }
                    )
            if len(l3_hits) >= MAX_CANDIDATES_PER_CHECK:
                break

    return {
        "new_term_candidates": l1_candidates[:MAX_CANDIDATES_PER_CHECK],
        "forbidden_synonym_hits": l3_hits[:MAX_CANDIDATES_PER_CHECK],
        "glossary_terms": [t.term for t in glossary],
    }


# --- main -------------------------------------------------------------------


def build_packet(repo_root: Path, base: str, max_files: int, max_lines: int) -> dict:
    canon = repo_root / "docs" / "canon"
    registry = canon / "registry.md"
    glossary_path = canon / "glossary.md"
    impact_dir = canon / "impact"

    if not registry.is_file():
        return {
            "status": "ESCALATE",
            "reason": "no contract registry at docs/canon/registry.md — run /jackal-director:canon-init",
        }

    mbase = merge_base(repo_root, base)
    files, lines = diff_stat(repo_root, mbase)
    head = _git(repo_root, "rev-parse", "--short", "HEAD").strip()
    branch = _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD").strip()

    if files > max_files or lines > max_lines:
        return {
            "status": "ESCALATE",
            "reason": f"diff too large for a linter pass: {files} files / {lines} lines "
            f"(caps: {max_files} files / {max_lines} lines). Review by a human or stronger model.",
            "base": base,
            "head": head,
            "diff": {"files": files, "lines": lines},
        }

    changed = changed_files(repo_root, mbase)
    comps = parse_component_map(registry.read_text(encoding="utf-8", errors="replace"))
    glossary = (
        parse_glossary(glossary_path.read_text(encoding="utf-8", errors="replace"))
        if glossary_path.is_file()
        else []
    )
    commit_msgs = _git(repo_root, "log", "--format=%s%n%b", f"{mbase}..HEAD")
    commit_slugs = re.findall(r"#(\d+)", commit_msgs)

    adds = added_lines(repo_root, mbase)

    deterministic: list[dict] = []
    deterministic += check_c1_impact(changed, comps, impact_dir, branch, commit_slugs)
    deterministic += check_c3_cross_component(adds, comps)
    c5, c2_candidates = check_c5_breaking_without_adr(
        repo_root, mbase, changed, comps, impact_dir, branch, commit_msgs
    )
    deterministic += c5

    packet = {
        "status": "OK",
        "base": base,
        "head": head,
        "branch": branch,
        "diff": {"files": files, "lines": lines},
        "components": [{"name": c.name, "root": c.root, "contract_sources": c.contract_sources} for c in comps],
        "glossary_present": glossary_path.is_file(),
        "deterministic_findings": deterministic,
        "sentinel_candidates": {"c2_surface_changes": c2_candidates},
        "lexicon_candidates": extract_lexicon_candidates(adds, glossary) if glossary else {
            "note": "no glossary at docs/canon/glossary.md — lexicon checks skipped"
        },
    }
    return packet


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Deterministic pre-pass for the director conformance gate.")
    ap.add_argument("--base", default="main", help="base ref (default: main)")
    ap.add_argument("--repo-root", default=".", help="repo root (default: cwd)")
    ap.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    ap.add_argument("--max-diff-lines", type=int, default=DEFAULT_MAX_DIFF_LINES)
    args = ap.parse_args(argv)

    try:
        packet = build_packet(Path(args.repo_root).resolve(), args.base, args.max_files, args.max_diff_lines)
    except RuntimeError as e:
        packet = {"status": "ESCALATE", "reason": str(e)}

    json.dump(packet, sys.stdout, indent=2)
    sys.stdout.write("\n")
    # exit 2 on ESCALATE so a shell caller can branch without parsing JSON
    return 2 if packet.get("status") == "ESCALATE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
