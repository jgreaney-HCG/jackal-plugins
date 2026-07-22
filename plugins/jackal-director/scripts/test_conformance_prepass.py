#!/usr/bin/env python3
"""Tests for conformance_prepass.py.

Builds throwaway git repos in a temp dir and runs the pre-pass against them.
Run: python3 test_conformance_prepass.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "conformance_prepass.py"

passed = 0
failed = 0
errors: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        errors.append(f"{name}: {detail}")


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def init_repo(repo: Path) -> None:
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@t.t")
    git(repo, "config", "user.name", "t")
    git(repo, "commit", "-q", "--allow-empty", "-m", "root")


def write(repo: Path, rel: str, content: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def run_prepass(repo: Path, *extra: str) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(repo), "--base", "main", *extra],
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"_raw": result.stdout, "_stderr": result.stderr}
    return result.returncode, payload


REGISTRY = """# Contract Registry
Contracts: per-component

## Component Map
| Component | Root path | Contract source | Exporter |
|-----------|-----------|-----------------|----------|
| gallery | `packages/gallery/` | `gallery/api/contracts.py` | `Foo` |
| workbench | `packages/workbench/` | `workbench/api/contracts.py` | `Bar` |
| shared | `packages/shared/` | none (consumer) | — |
"""

GLOSSARY = """# Glossary
One `##` heading per term.

## Module
An independent package.
Aliases: domain module
Never: microservice, plugin

## Principal
The authenticated identity.
"""


def scenario_base(repo: Path) -> None:
    """Canon + a committed baseline on main."""
    init_repo(repo)
    write(repo, "docs/canon/registry.md", REGISTRY)
    write(repo, "docs/canon/glossary.md", GLOSSARY)
    write(repo, "docs/canon/impact/README.md", "impact statements go here")
    write(
        repo,
        "packages/gallery/api/contracts.py",
        "class Foo:\n    id: int\n    name: str\n",
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "baseline")


# ---------------------------------------------------------------------------
# Test: no registry -> ESCALATE, exit 2
# ---------------------------------------------------------------------------
def test_no_registry() -> None:
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        init_repo(repo)
        write(repo, "foo.txt", "x")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "c")
        git(repo, "checkout", "-q", "-b", "feature/x")
        write(repo, "foo.txt", "y")
        git(repo, "commit", "-q", "-am", "change")
        code, out = run_prepass(repo)
        check("no_registry status", out.get("status") == "ESCALATE", str(out))
        check("no_registry exit code", code == 2, f"exit={code}")


# ---------------------------------------------------------------------------
# Test: oversized diff -> ESCALATE before any check
# ---------------------------------------------------------------------------
def test_diff_cap() -> None:
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        scenario_base(repo)
        git(repo, "checkout", "-q", "-b", "feature/big")
        write(repo, "packages/shared/big.py", "\n".join(f"x{i} = {i}" for i in range(50)))
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "big")
        code, out = run_prepass(repo, "--max-diff-lines", "10")
        check("diff_cap status", out.get("status") == "ESCALATE", str(out))
        check("diff_cap exit code", code == 2, f"exit={code}")
        check("diff_cap reason mentions size", "too large" in out.get("reason", ""), str(out))


# ---------------------------------------------------------------------------
# Test: clean small change -> OK, no deterministic findings
# ---------------------------------------------------------------------------
def test_clean_change() -> None:
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        scenario_base(repo)
        git(repo, "checkout", "-q", "-b", "feature/clean")
        write(repo, "packages/shared/util.py", "def helper():\n    return 1\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "add helper (non-contract)")
        code, out = run_prepass(repo)
        check("clean status", out.get("status") == "OK", str(out))
        check("clean exit code", code == 0, f"exit={code}")
        check(
            "clean no deterministic findings",
            out.get("deterministic_findings") == [],
            str(out.get("deterministic_findings")),
        )
        check("clean parsed 3 components", len(out.get("components", [])) == 3, str(out.get("components")))


# ---------------------------------------------------------------------------
# Test: C1 — contract source touched, no impact statement -> FLAG
# ---------------------------------------------------------------------------
def test_c1_missing_impact() -> None:
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        scenario_base(repo)
        git(repo, "checkout", "-q", "-b", "feature/no-impact")
        write(
            repo,
            "packages/gallery/api/contracts.py",
            "class Foo:\n    id: int\n    name: str\n    extra: bool\n",
        )
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "add field, forgot impact")
        code, out = run_prepass(repo)
        checks = {f["check"] for f in out.get("deterministic_findings", [])}
        check("c1 flagged", "C1" in checks, str(out.get("deterministic_findings")))


# ---------------------------------------------------------------------------
# Test: C1 satisfied when impact statement references branch
# ---------------------------------------------------------------------------
def test_c1_present() -> None:
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        scenario_base(repo)
        git(repo, "checkout", "-q", "-b", "feature/has-impact")
        write(repo, "docs/canon/impact/feature/has-impact.md", "## Contracts touched\nFoo")
        write(
            repo,
            "packages/gallery/api/contracts.py",
            "class Foo:\n    id: int\n    name: str\n    extra: bool\n",
        )
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "add field with impact")
        code, out = run_prepass(repo)
        checks = {f["check"] for f in out.get("deterministic_findings", [])}
        check("c1 not flagged when impact present", "C1" not in checks, str(out.get("deterministic_findings")))


# ---------------------------------------------------------------------------
# Test: C5 — removed field without ADR -> FLAG; and C2 candidates populated
# ---------------------------------------------------------------------------
def test_c5_breaking_without_adr() -> None:
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        scenario_base(repo)
        git(repo, "checkout", "-q", "-b", "feature/break")
        write(repo, "docs/canon/impact/feature/break.md", "## Change\nremoved name")
        # remove the 'name' field
        write(repo, "packages/gallery/api/contracts.py", "class Foo:\n    id: int\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "remove name field")
        code, out = run_prepass(repo)
        checks = {f["check"] for f in out.get("deterministic_findings", [])}
        check("c5 flagged breaking-without-adr", "C5" in checks, str(out.get("deterministic_findings")))
        c2 = out.get("sentinel_candidates", {}).get("c2_surface_changes", [])
        check("c2 candidates populated", any(c.get("field") == "name" for c in c2), str(c2))


# ---------------------------------------------------------------------------
# Test: C5 suppressed when an ADR is referenced in commit message
# ---------------------------------------------------------------------------
def test_c5_with_adr() -> None:
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        scenario_base(repo)
        git(repo, "checkout", "-q", "-b", "feature/break-adr")
        write(repo, "docs/canon/impact/feature/break-adr.md", "## ADR\nADR-0007")
        write(repo, "packages/gallery/api/contracts.py", "class Foo:\n    id: int\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "remove name field per ADR-0007")
        code, out = run_prepass(repo)
        checks = {f["check"] for f in out.get("deterministic_findings", [])}
        check("c5 suppressed with ADR ref", "C5" not in checks, str(out.get("deterministic_findings")))


# ---------------------------------------------------------------------------
# Test: L1/L3 lexicon candidates
# ---------------------------------------------------------------------------
def test_lexicon_candidates() -> None:
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        scenario_base(repo)
        git(repo, "checkout", "-q", "-b", "feature/vocab")
        write(repo, "docs/canon/impact/feature/vocab.md", "## Change\nnew stuff")
        # 'Widget' is a new domain term; 'microservice' is a forbidden synonym for Module
        write(
            repo,
            "packages/shared/thing.py",
            "class Widget:\n    pass\n\n# we run this as a microservice\n",
        )
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "vocab")
        code, out = run_prepass(repo)
        lex = out.get("lexicon_candidates", {})
        new_terms = {c["term"] for c in lex.get("new_term_candidates", [])}
        check("l1 new term Widget", "Widget" in new_terms, str(lex.get("new_term_candidates")))
        forbidden = {c["forbidden"].lower() for c in lex.get("forbidden_synonym_hits", [])}
        check("l3 forbidden synonym microservice", "microservice" in forbidden, str(lex.get("forbidden_synonym_hits")))


# ---------------------------------------------------------------------------
# Test: known glossary term is NOT flagged as new
# ---------------------------------------------------------------------------
def test_known_term_not_new() -> None:
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        scenario_base(repo)
        git(repo, "checkout", "-q", "-b", "feature/known")
        write(repo, "docs/canon/impact/feature/known.md", "x")
        write(repo, "packages/shared/mod.py", "class Module:\n    pass\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "known term")
        code, out = run_prepass(repo)
        new_terms = {c["term"] for c in out.get("lexicon_candidates", {}).get("new_term_candidates", [])}
        check("known term Module not flagged new", "Module" not in new_terms, str(new_terms))


# ---------------------------------------------------------------------------
# Test (regression): long lines are snipped so the packet stays bounded
# ---------------------------------------------------------------------------
def test_long_line_snipped() -> None:
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        scenario_base(repo)
        git(repo, "checkout", "-q", "-b", "feature/hugeline")
        write(repo, "docs/canon/impact/feature/hugeline.md", "x")
        # one enormous added line in a contract source (under the file/line caps)
        blob = "x" * 500_000
        write(repo, "packages/gallery/api/contracts.py", f"class Foo:\n    id: int\n    name: str\n    # {blob}\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "huge line")
        code, out = run_prepass(repo)
        packet_size = len(json.dumps(out))
        check("huge line packet stays small", packet_size < 20_000, f"packet={packet_size} chars")
        # every embedded text field must be capped
        texts = []
        for f in out.get("deterministic_findings", []):
            ev = f.get("evidence", {})
            if isinstance(ev.get("text"), str):
                texts.append(ev["text"])
        for c in out.get("sentinel_candidates", {}).get("c2_surface_changes", []):
            texts.append(c.get("text", ""))
        check("no embedded text exceeds cap", all(len(t) <= 210 for t in texts), f"max={max((len(t) for t in texts), default=0)}")


# ---------------------------------------------------------------------------
# Test (regression): numeric issue slug must not substring-match a longer number
# ---------------------------------------------------------------------------
def test_slug_no_false_positive() -> None:
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        scenario_base(repo)
        git(repo, "checkout", "-q", "-b", "feature/nomatch")
        # an unrelated pre-existing impact file whose number *contains* our slug
        write(repo, "docs/canon/impact/121-legacy-migration.md", "old work")
        write(
            repo,
            "packages/gallery/api/contracts.py",
            "class Foo:\n    id: int\n    name: str\n    extra: bool\n",
        )
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "add field, closes #21")
        code, out = run_prepass(repo)
        checks = {f["check"] for f in out.get("deterministic_findings", [])}
        check(
            "c1 flagged despite 121 impact file (slug 21 != 121)",
            "C1" in checks,
            str(out.get("deterministic_findings")),
        )


# ---------------------------------------------------------------------------
# Test (regression): numeric slug still matches its own impact file
# ---------------------------------------------------------------------------
def test_slug_true_positive() -> None:
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        scenario_base(repo)
        git(repo, "checkout", "-q", "-b", "feature/match")
        write(repo, "docs/canon/impact/21-the-feature.md", "## Contracts touched\nFoo")
        write(
            repo,
            "packages/gallery/api/contracts.py",
            "class Foo:\n    id: int\n    name: str\n    extra: bool\n",
        )
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "add field, closes #21")
        code, out = run_prepass(repo)
        checks = {f["check"] for f in out.get("deterministic_findings", [])}
        check("c1 satisfied by 21-*.md for slug 21", "C1" not in checks, str(out.get("deterministic_findings")))


# ---------------------------------------------------------------------------
# Test (regression): docstring labels are not treated as contract fields
# ---------------------------------------------------------------------------
def test_docstring_labels_not_fields() -> None:
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        scenario_base(repo)
        git(repo, "checkout", "-q", "-b", "feature/doc")
        write(repo, "docs/canon/impact/feature/doc.md", "x")
        # add only a docstring with section labels; remove nothing real
        write(
            repo,
            "packages/gallery/api/contracts.py",
            'class Foo:\n    """Summary.\n\n    Args:\n        note: whatever\n    Returns:\n        thing\n    """\n    id: int\n    name: str\n',
        )
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "add docstring")
        code, out = run_prepass(repo)
        c2 = out.get("sentinel_candidates", {}).get("c2_surface_changes", [])
        fields = {c["field"] for c in c2}
        check("docstring 'Args' not a field", "Args" not in fields and "args" not in fields, str(fields))
        check("docstring 'Returns' not a field", "Returns" not in fields, str(fields))


def main() -> int:
    for fn in [
        test_no_registry,
        test_diff_cap,
        test_clean_change,
        test_c1_missing_impact,
        test_c1_present,
        test_c5_breaking_without_adr,
        test_c5_with_adr,
        test_lexicon_candidates,
        test_known_term_not_new,
        test_long_line_snipped,
        test_slug_no_false_positive,
        test_slug_true_positive,
        test_docstring_labels_not_fields,
    ]:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            global failed
            failed += 1
            errors.append(f"{fn.__name__}: raised {type(e).__name__}: {e}")

    print(f"\n{passed}/{passed + failed} checks passed, {failed} failed")
    if errors:
        print("\nFailures:")
        for e in errors:
            print(f"  - {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
