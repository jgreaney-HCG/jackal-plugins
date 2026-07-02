#!/usr/bin/env python3
"""Validate YAML frontmatter on every command, agent, and skill file.

Checks: frontmatter block present and parses as YAML; required keys present
and non-empty. Does not validate description content quality -- that's a
review-time judgment, not a CI-time one.
"""
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML not installed -- CI installs it via pip. For local runs: pip install pyyaml")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)

CHECKS = [
    ("commands/*.md", ["description"]),
    ("agents/*.md", ["name", "description"]),
    ("skills/*/SKILL.md", ["name", "description"]),
]


def check_file(path: Path, required: list[str]) -> list[str]:
    text = path.read_text()
    match = FRONTMATTER_RE.match(text)
    rel = path.relative_to(ROOT)
    if not match:
        return [f"{rel}: no YAML frontmatter block (must start with '---')"]

    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        return [f"{rel}: frontmatter is not valid YAML ({e})"]

    if not isinstance(data, dict):
        return [f"{rel}: frontmatter did not parse to a mapping"]

    errors = []
    for key in required:
        value = data.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"{rel}: missing or empty required frontmatter key '{key}'")

    name = data.get("name")
    if name and not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", str(name)):
        errors.append(f"{rel}: name '{name}' is not kebab-case")

    return errors


def main() -> int:
    all_errors = []
    for pattern, required in CHECKS:
        for path in sorted(ROOT.glob(f"plugins/*/{pattern}")):
            all_errors.extend(check_file(path, required))

    if all_errors:
        print("Frontmatter lint FAILED:")
        for e in all_errors:
            print(f"  - {e}")
        return 1

    total = sum(len(list(ROOT.glob(f"plugins/*/{p}"))) for p, _ in CHECKS)
    print(f"Frontmatter lint OK: {total} files checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
