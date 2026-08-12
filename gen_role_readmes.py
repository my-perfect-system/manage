#!/usr/bin/env python3
"""Generate per-role README.md files from existing role data.

Each role's README is derived from:
  - roles/<role>/meta/argument_specs.yml (short_description + per-option descriptions)
  - roles/<role>/defaults/main.yml (variable defaults)
  - roles/<role>/meta/main.yml (galaxy_info + dependencies)

Usage:
  python3 manage/gen_role_readmes.py
"""

import os
import re
import sys
import yaml
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
COLLECTION_DESC = {
    "mps-base": "Anchor collection (shared conventions, identity model)",
    "mps-os": "Operating system init",
    "mps-users": "User accounts, groups, SSH, sudoers",
    "mps-optimize": "System-level performance tuning",
    "mps-terminal": "Terminal / shell / editor environment",
    "mps-development": "Per-user development tooling",
    "mps-desktop": "Desktop GUI / window manager",
    "mps-hardening": "System-level security hardening",
    "mps-backup": "Per-user backup restore",
}


def render_role_yml(coll_name, role):
    """Render a README for a single role."""
    role_dir = ROOT / coll_name / "roles" / role
    argspec_path = role_dir / "meta" / "argument_specs.yml"
    defaults_path = role_dir / "defaults" / "main.yml"
    meta_path = role_dir / "meta" / "main.yml"
    main_path = role_dir / "tasks" / "main.yml"

    # --- argument_specs ---
    short_desc = ""
    options = {}
    if argspec_path.exists():
        try:
            with open(argspec_path) as f:
                spec = yaml.safe_load(f) or {}
            main_spec = (spec.get("argument_specs") or {}).get("main") or {}
            short_desc = (main_spec.get("short_description") or "").strip()
            options = main_spec.get("options") or {}
        except Exception:
            pass

    # --- defaults ---
    defaults = {}
    if defaults_path.exists():
        try:
            with open(defaults_path) as f:
                defaults = yaml.safe_load(f) or {}
        except Exception:
            pass

    # --- dependencies + galaxy_info ---
    deps = []
    min_ansible = ""
    license_str = ""
    platforms = []
    if meta_path.exists():
        try:
            with open(meta_path) as f:
                meta = yaml.safe_load(f) or {}
            gi = meta.get("galaxy_info") or {}
            min_ansible = gi.get("min_ansible_version", "")
            license_str = ", ".join(gi.get("license") or [])
            platforms = gi.get("platforms") or []
            deps = meta.get("dependencies") or []
        except Exception:
            pass

    # --- task line count ---
    task_lines = 0
    if main_path.exists():
        with open(main_path) as f:
            task_lines = sum(1 for _ in f)

    # --- compose ---
    lines = []
    # Front matter (YAML for tooling / galaxy)
    lines.append("---")
    lines.append(f"# Reference doc — auto-generated, do not edit by hand.")
    lines.append(f"# Regenerate via: python3 manage/gen_role_readmes.py")
    lines.append(f"namespace: mps")
    lines.append(f"collection: {coll_name.replace('mps-', '')}")
    lines.append(f"role: {role}")
    lines.append("---")
    lines.append("")
    lines.append(f"# `mps.{coll_name.replace('mps-', '')}.{role}`")
    lines.append("")
    if short_desc:
        lines.append(short_desc)
    else:
        lines.append(f"Role from the **{coll_name}** collection.")
    lines.append("")

    # Variables section
    if defaults:
        lines.append("## Default variables")
        lines.append("")
        lines.append("| Variable | Default | Description |")
        lines.append("|---|---|---|")
        for var in sorted(defaults.keys()):
            value = defaults[var]
            desc = ""
            if isinstance(options, dict) and var in options:
                opt = options[var]
                if isinstance(opt, dict):
                    raw_desc = opt.get("description") or ""
                    if isinstance(raw_desc, list):
                        raw_desc = " ".join(str(d) for d in raw_desc)
                    desc = str(raw_desc).replace("\n", " ").strip()
                    if not desc and "default" in opt:
                        desc = f"Default: `{opt['default']}`"
            # Format the value
            if isinstance(value, list):
                if len(value) > 4:
                    val_str = f"[{len(value)} items]"
                else:
                    val_str = (
                        yaml.safe_dump(value, default_flow_style=False)
                        .strip()
                        .replace("\n", "<br>")
                    )
            elif isinstance(value, dict):
                val_str = (
                    "{ " + ", ".join(f"{k}: …" for k in list(value.keys())[:3]) + " }"
                )
            elif isinstance(value, str):
                val_str = value
            elif isinstance(value, bool):
                val_str = "true" if value else "false"
            else:
                val_str = str(value)
            lines.append(f"| `{var}` | `{val_str}` | {desc} |")
        lines.append("")

    # Dependencies
    lines.append("## Dependencies")
    lines.append("")
    if deps:
        for d in deps:
            if isinstance(d, dict):
                rname = d.get("role", str(d))
                lines.append(f"- `{rname}`")
            else:
                lines.append(f"- `{d}`")
    else:
        lines.append("None.")
    lines.append("")

    # Example
    lines.append("## Example usage")
    lines.append("")
    lines.append("```yaml")
    lines.append("- hosts: all")
    lines.append("  roles:")
    lines.append(f"    - mps.{coll_name.replace('mps-', '')}.{role}")
    lines.append("```")
    lines.append("")

    # Meta
    lines.append("## Role metadata")
    lines.append("")
    if min_ansible:
        lines.append(f"- **Min Ansible version**: `{min_ansible}`")
    if license_str:
        lines.append(f"- **License**: {license_str}")
    if platforms:
        plat_str = ", ".join(
            f"{p.get('name', '?')} ({', '.join(p.get('versions', [])) or 'any'})"
            for p in platforms
        )
        lines.append(f"- **Platforms**: {plat_str}")
    lines.append(f"- **Tasks file lines**: {task_lines}")
    lines.append("")

    return "\n".join(lines)


def main():
    count = 0
    for coll in COLLECTIONS:
        roles_dir = ROOT / coll / "roles"
        if not roles_dir.is_dir():
            continue
        for role_dir in sorted(roles_dir.iterdir()):
            if not role_dir.is_dir():
                continue
            role = role_dir.name
            content = render_role_yml(coll, role)
            out = role_dir / "README.md"
            out.write_text(content)
            count += 1
            print(f"wrote {out.relative_to(ROOT)}")
    print()
    print(f"Total: {count} role READMEs generated.")


if __name__ == "__main__":
    main()
