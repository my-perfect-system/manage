#!/usr/bin/env python3
"""Rename `mps.*` namespace to `odem.*` across the whole repo.

Substitution rules:
  Collection directory names + path segments:
    odem-base     -> odem-base
    odem-os       -> odem-os
    odem-users    -> odem-users
    odem-optimize -> odem-optimize
    odem-terminal -> odem-terminal
    odem-development  -> odem-development
    odem-desktop  -> odem-desktop
    odem-hardening -> odem-hardening
    odem-backup   -> odem-backup

  Collection file references (mps-X/something):
    odem-base/path  -> odem-base/path  (path-segment-only substitution)

  Galaxy namespace field:
    namespace: mps         -> namespace: odem     (YAML literal — exact match)
    "namespace": "mps"      -> "namespace": "odem" (other variants)
    dependencies: odem.base  -> dependencies: odem.base
    dependencies: odem.os    -> dependencies: odem.os
    etc.

  Fully-qualified role references:
    odem.base.identity     -> odem.base.identity
    odem.os.package_manager -> odem.os.package_manager
    ... (any mps.X.Y form)
    used in: task files, converge.yml, requirements.yml, READMEs,
    AGENTS.md, changelog fragments

  Custom filter plugin name:
    odem_filter_users       -> odem_filter_users
    used in: filter plugin code, any place that calls the filter

  Special handling:
    - `mps.*` references inside backtick-quoted Markdown links
      ([[...](file.md)]) are also renamed.
    - Whole-word replacements to avoid hitting false positives
      inside words like 'imports', 'ramps', etc.

Idempotent: re-running after a completed run is a no-op (all matches
already migrated).
"""

import re
import shutil
import sys
from pathlib import Path

ROOT = Path("/home/jb/repo/github/my-perfect-system")

# Files that should be skipped from the rename (they intentionally reference
# the old namespace, e.g. the rename script itself which documents what it did,
# or future-use case studies).
SKIP_RENAMES = {
    ROOT / "manage" / "rename_namespace.py",
}

# Collection paths: old dir name -> new dir name.
DIR_RENAMES = {
    "odem-base": "odem-base",
    "odem-os": "odem-os",
    "odem-users": "odem-users",
    "odem-optimize": "odem-optimize",
    "odem-terminal": "odem-terminal",
    "odem-development": "odem-development",
    "odem-desktop": "odem-desktop",
    "odem-hardening": "odem-hardening",
    "odem-backup": "odem-backup",
}

# File-name renames (file basenames only) — only odem_filter_users.py for now.
FILE_RENAMES = {
    "odem_filter_users.py": "odem_filter_users.py",
}

# Text replacements applied inside files. Order matters — most specific first.
TEXT_REPLACEMENTS = [
    # Galaxy YAML namespace field — accept backticks / quotes / plain EOL.
    # Allow markdown **bold** markers between `namespace` and the `:` (e.g.
    # lines like `- **namespace**: \`mps\``). Use a backreference so the
    # surrounding `**` and backticks are preserved.
    (
        re.compile(r"(\bnamespace\*?\*?:\s*['\"`]?)mps(['\"`]?\s*$)", re.MULTILINE),
        r"\1odem\2",
    ),
    # Filter function name (whole-word)
    (re.compile(r"\bmps_filter_users\b"), "odem_filter_users"),
    # Collection path / dir-name segment (word-bounded) — `odem-base`, `odem-os`, etc.
    # Done as path-segment substitutions below; not in the file contents themselves
    # except when quoted as part of a path.
    # Generic FQN: mps.<coll>.<role>
    (re.compile(r"\bmps\.([a-z]+)\.([a-z][a-z0-9_]*)\b"), r"odem.\1.\2"),
    # Word-bounded `mps.<coll>` (e.g. references like `odem.base` without role)
    (re.compile(r"\bmps\.([a-z]+)\b"), r"odem.\1"),
    # Collection directory name as a whole word (matches `odem-base`, `odem-os`, etc.)
    (re.compile(r"\bmps-([a-z]+)\b"), r"odem-\1"),
    # Tarball glob pattern `odem-*.tar.gz` -> `odem-*.tar.gz`
    (re.compile(r"mps-\*\.tar\.gz"), r"odem-*.tar.gz"),
    # GitHub repo URL (move from old my-perfect-system/mps-X to odem/odem-X)
    (
        re.compile(r"https?://github\.com/my-perfect-system/mps-([a-z]+)"),
        r"https://github.com/odem/odem-\1",
    ),
    # Galaxy YAML tag value: `- mps` -> `- odem` (in the `tags:` list)
    (re.compile(r"^(\s*-\s*)mps(\s*)$", re.MULTILINE), r"\1odem\2"),
]


def migrate_text(text):
    """Apply all text substitutions; return new text and number of changes."""
    changes = 0
    for pat, repl in TEXT_REPLACEMENTS:
        new_text, n = pat.subn(repl, text)
        if n:
            text = new_text
            changes += n
    return text, changes


def rewrite_file(path):
    """Apply substitutions to a single file. Returns number of changes."""
    try:
        text = path.read_text()
    except Exception:
        return 0
    new_text, n = migrate_text(text)
    if n and new_text != text:
        path.write_text(new_text)
        return n
    return 0


def rewrite_directory_files(root):
    """Rewrite every text file under `root` (recursively)."""
    skip_dirs = {
        ".git",
        ".ansible",
        "__pycache__",
        "node_modules",
        ".github/workflows",
        ".venv",
        "venv",
    }
    total = 0
    files_touched = 0
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        # skip binaries — text-mode only
        if path.suffix in {
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".pdf",
            ".zip",
            ".tar",
            ".gz",
            ".bz2",
            ".xz",
            ".so",
            ".o",
            ".pyc",
            ".pyo",
        }:
            continue
        # skip paths inside skip_dirs (use relative check)
        rel = path.relative_to(root)
        if any(part in skip_dirs for part in rel.parts):
            continue
        n = rewrite_file(path)
        if n:
            total += n
            files_touched += 1
    return total, files_touched


def rename_collections_dirs():
    """mv /my-perfect-system/mps-X -> /my-perfect-system/odem-X.

    Also deletes stale `odem-*.tar.gz` build artifacts inside each
    renamed dir — they're from the previous namespace and would be
    overwritten on the next build under the `odem-*` prefix anyway.
    """
    for old, new in DIR_RENAMES.items():
        old_path = ROOT / old
        new_path = ROOT / new
        if old_path.exists() and not new_path.exists():
            shutil.move(str(old_path), str(new_path))
            print(f"  dir rename: {old} -> {new}")
        # Drop stale tarball artifacts of the old namespace.
        for tar in old_path.glob("odem-*.tar.gz") if old_path.exists() else []:
            tar.unlink()
            print(f"  rm stale tarball: {tar.name} (in {old})")
        # And inside the (potentially already-renamed) new dir too.
        for tar in new_path.glob("odem-*.tar.gz"):
            tar.unlink()
            print(f"  rm stale tarball: {tar.name}")


def main():
    if not ROOT.is_dir():
        print(f"ERROR: {ROOT} not found", file=sys.stderr)
        sys.exit(1)

    # 1. Rename collections *under* ROOT so subsequent walks see new names.
    print("Step 1: rename collection directories")
    rename_collections_dirs()

    # 2. For each renamed dir (and now examples/ + manage/), rewrite files.
    targets = [ROOT / d for d in DIR_RENAMES.values()] + [
        ROOT / "examples",
        ROOT / "manage",
    ]
    print("Step 2: rewrite files in each target")
    for t in targets:
        if not t.is_dir():
            continue
        total, files = rewrite_directory_files(t)
        print(f"  {t.relative_to(ROOT)}: {files} files, {total} string changes")

    # 3. Rename the filter plugin *file* basename inside odem-base/filter_plugins/.
    #    (We can't do this in step 1 because the .py contains `odem_filter_users`
    #    references that we'd want renamed by the text substitution first.
    #    Order is: text rewrite -> file rename -> import-update not needed
    #    because callers use the function name, not the file basename directly.)
    print("Step 3: rename filter-plugin file basenames")
    for old_name, new_name in FILE_RENAMES.items():
        for d in DIR_RENAMES.values():
            fp = ROOT / d / "filter_plugins" / old_name
            if fp.exists():
                fp.rename(fp.parent / new_name)
                print(f"  mv {fp.relative_to(ROOT)} -> {new_name}")
                # Also rename __pycache__/ entry if any
                pycache = fp.parent / "__pycache__" / old_name.replace(".py", ".pyc")
                if pycache.exists():
                    pycache.rename(
                        fp.parent / "__pycache__" / new_name.replace(".py", ".pyc")
                    )

    # 4. Remove stale .pyc bytecode.
    print("Step 4: clear .pyc caches")
    for d in DIR_RENAMES.values():
        cache = ROOT / d / "filter_plugins" / "__pycache__"
        if cache.is_dir():
            shutil.rmtree(cache)
            print(f"  rm {cache.relative_to(ROOT)}")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
