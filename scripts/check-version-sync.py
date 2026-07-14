#!/usr/bin/env python3
"""Verify every plugin's plugin.json version matches its marketplace.json entry.

Does not attempt to parse CHANGELOG.md prose (entry formats vary too much to
regex reliably) -- that stays a human/reviewer check.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    marketplace = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    failures = []

    for entry in marketplace["plugins"]:
        name = entry["name"]
        mp_version = entry.get("version")
        source = entry.get("source", "")
        if not isinstance(source, str) or not source.startswith("./"):
            continue  # external/non-local plugin entries have no local plugin.json to check

        plugin_json_path = ROOT / source.lstrip("./") / ".claude-plugin" / "plugin.json"
        if not plugin_json_path.exists():
            rel = plugin_json_path.relative_to(ROOT)
            failures.append(
                f"{name}: marketplace.json points at {source}, but {rel} does not exist"
            )
            continue

        plugin_version = json.loads(plugin_json_path.read_text()).get("version")
        if plugin_version != mp_version:
            failures.append(
                f"{name}: marketplace.json says {mp_version!r}, "
                f"{plugin_json_path.relative_to(ROOT)} says {plugin_version!r}"
            )

    if failures:
        print("Version sync FAILED:")
        for f in failures:
            print(f"  - {f}")
        print(
            "\nFix: bump both files to the same version (see the maintaining-a-marketplace skill)."
        )
        return 1

    print(f"Version sync OK: {len(marketplace['plugins'])} plugins checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
