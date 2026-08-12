#!/usr/bin/env python3
"""Replace `mps.X.Y` references in collection README tables with links
to the per-role README.

Scans each collection's top-level README.md for table rows where one
cell starts with a backtick-quoted FQN like `` `mps.os.package_manager` ``.
Replaces the FQN cell with a Markdown link to `roles/<role>/README.md`.

Usage:  python3 manage/link_role_readmes.py
"""

import re
from pathlib import Path

ROOT = Path("/home/jb/repo/github/my-perfect-system")
COLLECTIONS = [
    "mps-base",
    "mps-os",
    "mps-users",
    "mps-optimize",
    "mps-terminal",
    "mps-development",
    "mps-desktop",
    "mps-hardening",
    "mps-backup",
]


FQN_PATTERN = re.compile(
    r"^(\|\s*)`?(mps\.[a-z]+\.[a-z0-9_]+)`?(\s*\|.*)$",
    re.MULTILINE,
)


def transform_collection_readme(coll_name):
    readme = ROOT / coll_name / "README.md"
    if not readme.exists():
        return 0, "no README.md"

    text = readme.read_text()
    role_link_substitutions = 0

    def replace_fqn_in_cell(match):
        nonlocal role_link_substitutions
        prefix = match.group(1)
        fqn = match.group(2)
        suffix = match.group(3)
        ns, col, role = fqn.split(".")
        link = f"{prefix}[`{fqn}`](roles/{role}/README.md){suffix}"
        role_link_substitutions += 1
        return link

    new_text = FQN_PATTERN.sub(replace_fqn_in_cell, text)

    if new_text != text:
        readme.write_text(new_text)
        return role_link_substitutions, "updated"
    return 0, "no change"


def main():
    total = 0
    for coll in COLLECTIONS:
        n, status = transform_collection_readme(coll)
        total += n
        print(f"  {coll}: {n} link(s) added ({status})")
    print(f"\nTotal: {total} role-FQN cells linked to roles/<role>/README.md")


if __name__ == "__main__":
    main()
