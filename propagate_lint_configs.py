#!/usr/bin/env python3
"""Propagate .ansible-lint and .yamllint configs across all mps.* collections.

For each of the 9 collections:
  - copy .ansible-lint and .yamllint from the canonical source
    (mps-base) into the collection root
  - ensure galaxy.yml's build_ignore includes .ansible-lint and .yamllint
  - add a trailing newline to any .yml file under roles/ that's missing one
"""

import shutil
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

SRC_ANSIBLE_LINT = ROOT / "mps-base" / ".ansible-lint"
SRC_YAMLLINT = ROOT / "mps-base" / ".yamllint"


def ensure_trailing_newline(path: Path):
    """Add a final newline to a file if it doesn't have one."""
    if path.suffix not in (".yml", ".yaml"):
        return
    text = path.read_text()
    if text and not text.endswith("\n"):
        path.write_text(text + "\n")


def update_build_ignore(coll_dir: Path):
    """Ensure galaxy.yml's build_ignore includes the lint configs."""
    galaxy_yml = coll_dir / "galaxy.yml"
    if not galaxy_yml.exists():
        return
    text = galaxy_yml.read_text()

    needed = []
    if ".ansible-lint" not in text:
        needed.append(".ansible-lint")
    if ".yamllint" not in text:
        needed.append(".yamllint")

    if not needed:
        return

    # Find `build_ignore:` and append our entries to the list.
    # Crude but reliable: split by `build_ignore:` and look for the indented list.
    lines = text.split("\n")
    out = []
    in_build_ignore = False
    saw_entry = False
    inserted = False
    for i, line in enumerate(lines):
        out.append(line)
        stripped = line.rstrip()
        # detect `build_ignore:` with no value (the YAML list-form)
        if stripped.startswith("build_ignore:"):
            in_build_ignore = True
            # peek: is the list on the same line or following?
            tail = stripped[len("build_ignore:") :].strip()
            if tail == "":
                saw_entry = False
            else:
                saw_entry = True
            continue
        if in_build_ignore:
            # stop when we hit a non-list entry
            if line.startswith(" ") or line == "":
                # it's still in the indented list block
                if not inserted and (line.strip() != "" or saw_entry):
                    # insert before this position
                    out.pop()
                    indent = "  "
                    for item in needed:
                        out.append(f"{indent}{item}")
                    inserted = True
                    out.append(line)
                continue
            else:
                in_build_ignore = False
                if not inserted:
                    # need to insert above as a new block? unusual — galaxy.yml
                    # always ends build_ignore list at EOF
                    for item in needed:
                        out.insert(-1, f"  {item}")
                    inserted = True

    new_text = "\n".join(out)
    if new_text != text:
        galaxy_yml.write_text(new_text)
        return True
    return False


def fix_trailing_newlines(coll_dir: Path):
    """Walk the collection and add trailing newlines to all roles/*/*.yml files."""
    roles_dir = coll_dir / "roles"
    if not roles_dir.is_dir():
        return 0
    count = 0
    for path in roles_dir.rglob("*.yml"):
        before = path.read_text()
        if before and not before.endswith("\n"):
            path.write_text(before + "\n")
            count += 1
    return count


def propagate_coll(coll_name):
    coll_dir = ROOT / coll_name

    # Copy lint configs (always overwrite to ensure canonical content),
    # but skip when src and dst are the same file (we're iterating mps-base
    # itself as the source of truth).
    target_ansible_lint = coll_dir / ".ansible-lint"
    target_yamllint = coll_dir / ".yamllint"
    if target_ansible_lint.exists() and target_ansible_lint.samefile(SRC_ANSIBLE_LINT):
        pass  # source == target; skip
    else:
        shutil.copy(SRC_ANSIBLE_LINT, target_ansible_lint)
    if target_yamllint.exists() and target_yamllint.samefile(SRC_YAMLLINT):
        pass
    else:
        shutil.copy(SRC_YAMLLINT, target_yamllint)

    # Update galaxy.yml build_ignore.
    gal_changed = update_build_ignore(coll_dir)

    # Fix trailing newlines.
    n_newlines = fix_trailing_newlines(coll_dir)

    return gal_changed, n_newlines


def main():
    print("Propagating lint configs to all 9 collections...")
    for coll in COLLECTIONS:
        gal_changed, n_newlines = propagate_coll(coll)
        print(
            f"  {coll}: galaxy.yml {'updated' if gal_changed else 'unchanged'}, "
            f"{n_newlines} files given trailing newlines"
        )

    # Also copy to manage/ (no galaxy.yml there).
    manage_dir = ROOT / "manage"
    if manage_dir.is_dir():
        shutil.copy(SRC_ANSIBLE_LINT, manage_dir / ".ansible-lint")
        shutil.copy(SRC_YAMLLINT, manage_dir / ".yamllint")
        print(f"  manage: configs copied (no galaxy.yml update)")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
