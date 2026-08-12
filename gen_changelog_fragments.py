#!/usr/bin/env python3
"""Create changelogs/fragments/ for every mps.* collection.

For each collection, write one or more small YAML fragments under
`changelogs/fragments/` that document the work done in the recent
refactor pass. Each fragment is a self-contained YAML file; modern Galaxy
tooling compiles them into `changelogs/changelog.yaml` on release.
"""

import os
from pathlib import Path

ROOT = Path("/home/jb/repo/github/my-perfect-system")
COLLECTIONS = {
    "mps-base": [
        (
            "feat-assert-debian13-role",
            "minor_changes",
            [
                "New shared role `mps.base.assert_debian13` fails fast on non-Debian-13 hosts. Adopted as a meta dependency by every role that requires Debian 13 (mps-os/{package_manager,system_settings,system_tools}, mps-users/{groups,ssh,sudo,users}).",
            ],
        ),
        (
            "feat-filter-plugin-surface",
            "minor_changes",
            [
                "Three new filter plugins in `mps-base/filter_plugins/mps_filter_users.py` for the per-user identity model:",
                "  - `mps_resolve_users(users_list, users_catalog)` produces `identity_users_resolved` from raw inputs",
                "  - `mps_user_groups(users)` flattens each user's `group`/`groups` into a deduplicated list",
                "  - `mps_filter_users(users, role_key, state='present')` filters `identity_users_resolved` by `user_roles.<key>` (skips empty dicts)",
                "All seven `mps-development` roles and the per-user `mps-desktop` roles now use `mps_filter_users` instead of inline `when:` blocks.",
            ],
        ),
        (
            "refactor-identity-task-block",
            "minor_changes",
            [
                "`mps.base.identity/tasks/main.yml` reduced from 70 to 51 lines; the two heavy Jinja data-shaping blocks (`catalog_entry | combine({...})` and the group-flattening loop) were moved into the filter plugin where they are unit-testable from plain Python.",
            ],
        ),
    ],
    "mps-os": [
        (
            "chore-defer-assert-debian13-role",
            "minor_changes",
            [
                "Dropped the byte-identical `Assert Debian 13 target` task block from `package_manager`, `system_settings`, `system_tools` task files (3 × 9 lines). Each role now declares `mps.base.assert_debian13` as a meta dependency in `roles/<role>/meta/main.yml`.",
            ],
        ),
    ],
    "mps-users": [
        (
            "chore-defer-assert-debian13-role",
            "minor_changes",
            [
                "Dropped the byte-identical `Assert Debian 13 target` task block from `groups`, `ssh`, `sudo`, `users` (4 × 9 lines). Each role now declares `mps.base.assert_debian13` as a meta dependency.",
            ],
        ),
        (
            "refactor-sudo-community-general-sudoers",
            "minor_changes",
            [
                "`mps.users.sudo` reworked to use `community.general.sudoers` (one module call per user, validating via the module's internal `visudo` invocation) instead of templating `/etc/sudoers.d/<name>` + manual `validate: visudo -cf %s`.",
                "Each user's `sudo.macros` is now resolved inline to a flat command list per user (`entity.sudo.macros | map('extract', sudo_macros) | flatten | unique`) — the `Cmnd_Alias` macro file indirection is gone.",
                "`templates/sudoers.j2` and `templates/macro.j2` deleted. `community.general >=1.0.0` added to `galaxy.yml` dependencies.",
            ],
        ),
        (
            "refactor-users-root-special-path-block",
            "minor_changes",
            [
                "Root-account special-path work in `mps.users.users/tasks/add.yml` consolidated under a single `block:` with one shared `when: identity_users_present | selectattr('name', 'equalto', 'root') | list | length > 0` guard. Inner `when:` blocks (value-changed checks for `chpasswd`/`chsh`/`chfn`/`chage`) preserved.",
            ],
        ),
    ],
    "mps-optimize": [
        (
            "chore-docs-and-tests",
            "minor_changes",
            [
                "Per-role READMEs auto-generated from argument_specs.yml + defaults/main.yml; meta/main.yml and argument_specs.yml cross-linked from each role README; collection README links every role.",
                "Linting configs (.ansible-lint, .yamllint) added; galaxy.yml's `build_ignore` excludes them from published tarballs.",
                "Molecule smoke-test scenarios for every role using `geerlingguy/docker-debian13-ansible:latest`.",
            ],
        ),
    ],
    "mps-terminal": [
        (
            "refactor-flatten-multiple-roles",
            "minor_changes",
            [
                "`mps-terminal/{bash,python,rust,nvim}` flattened: install.yml + configure.yml (and nvim's tools.yml) inlined into a single `tasks/main.yml` per role. Per-user loops switched from inline `when: user_roles.X` to `mps_filter_users('terminal_X')`.",
                "`mps-terminal/scripts` had an `install.yml` stub (5 lines, `when: false`) deleted; main.yml now invokes just the real `configure.yml`.",
            ],
        ),
        (
            "chore-docs-and-tests",
            "minor_changes",
            [
                "Per-role READMEs auto-generated; collection README links every role. Linting configs added. Molecule smoke tests added.",
            ],
        ),
    ],
    "mps-development": [
        (
            "refactor-flatten-and-adopt-filter",
            "minor_changes",
            [
                "All 7 mps-development roles (`dotnet`, `espidf`, `java`, `latex`, `lmstudio`, `opencode`, `unity`) flattened from `main.yml + install.yml` into a single `tasks/main.yml` per role. Per-user loops rewritten to use a `block:` wrapper with `loop: '{{ identity_users_resolved | mps_filter_users(\"development_X\") }}'` (the filter replaces the per-role `when: user_roles.X` + `state == 'present'` + `user != {}` boilerplate).",
                "`espidf`'s nested per-version loops survive the flatten — the inner `loop: espidf_versions` takes precedence over the block's per-user loop inside the `block:`, preserving the per-user × per-version semantics the original `include_tasks` had.",
            ],
        ),
        (
            "chore-docs-and-tests",
            "minor_changes",
            [
                "Per-role READMEs auto-generated; collection README links every role. Linting configs added. Molecule smoke tests added.",
            ],
        ),
    ],
    "mps-desktop": [
        (
            "chore-drop-stub-configure-yml",
            "minor_changes",
            [
                "9 stub `configure.yml` files deleted from simple desktop roles (`brave`, `firefox`, `gnometools`, `grubmenu`, `lightdm`, `plymouth`, `spotify`, `thunderbird`, `x11`). Each was a `when: false` debug stub, and each was already unreferenced from main.yml — pure dead-code removal, no behavior change.",
            ],
        ),
        (
            "refactor-flatten-kanata",
            "minor_changes",
            [
                "`mps-desktop/kanata` flattened: install.yml (118L, per-user rustup + cargo install + udev rules + systemd user service) and configure.yml (59L, .config/kanata/ tree + kanata.service + enable-linger loop) inlined into a single `tasks/main.yml`. Inline `block:` pattern keeps per-user loops scoped to the right user.",
            ],
        ),
        (
            "chore-docs-and-tests",
            "minor_changes",
            [
                "Per-role READMEs auto-generated; collection README links every role. Linting configs added. Molecule smoke tests added.",
            ],
        ),
    ],
    "mps-hardening": [
        (
            "chore-auditd-override-to-files",
            "minor_changes",
            [
                "`auditd` override moved from `templates/usr/lib/systemd/system/auditd.service.d/override.conf.j2` (templated, 1 Jinja var with fixed default `/var`) to `files/usr/lib/systemd/system/auditd.service.d/override.conf` (static). `template:` → `copy:` in `tasks/main.yml`. Deleted the now-empty `templates/usr/` tree.",
            ],
        ),
        (
            "refactor-flatten-lockdown",
            "minor_changes",
            [
                "`mps-hardening/lockdown` flattened: install.yml (147L, git clone external CIS repo, SSH keypair, 5 regex `lineinfile` overrides into CIS defaults, sub-playbook invocation) inlined into a single `tasks/main.yml`.",
            ],
        ),
        (
            "chore-docs-and-tests",
            "minor_changes",
            [
                "Per-role READMEs auto-generated; collection README links every role. Linting configs added. Molecule smoke tests added.",
            ],
        ),
    ],
    "mps-backup": [
        (
            "refactor-flatten-backup",
            "minor_changes",
            [
                "`mps.backup.backup` flattened: configure.yml (95L, per-user ssh dir create, 3× `synchronize` for keys/config/authorized_keys, perms fix, optional Brave bookmarks, home restore) inlined into a single `tasks/main.yml`.",
            ],
        ),
        (
            "chore-docs-and-tests",
            "minor_changes",
            [
                "Per-role READMEs auto-generated; collection README links every role. Linting configs added. Molecule smoke tests added.",
            ],
        ),
    ],
}

# Cross-collection note about the mps-meta removal — lives in every README but
# only in changelogs of a few key collections to avoid duplication.
META_REMOVAL = {
    "mps-base": "The `mps.meta` composition-only collection has been removed from the ecosystem. Cross-collection composition now lives as 7 flat `import_playbook` chain playbooks under `examples/inventories/home/playbooks/` (`bootstrap.yml`, `terminal_{min,full}.yml`, `desktop_{min,full}.yml`, `workstation_{min,full}.yml`). Run via `just run-example <env> <inventory> <playbook>`. `manage/Justfile` `REPOS` updated; `manage/AGENTS.md` Repos table updated.",
    "mps-terminal": "Cross-collection: the `mps.meta` collection was deleted; composition now lives as flat playbooks. See `manage/AGENTS.md` for the tier model.",
}


def write_fragment(coll, name, kind, items):
    coll_dir = ROOT / coll
    frag_dir = coll_dir / "changelogs" / "fragments"
    frag_dir.mkdir(parents=True, exist_ok=True)
    if isinstance(items, str):
        body = items
    else:
        # List of bullets under a single category.
        lines = [kind + ":"]
        for item in items:
            indented = "\n".join(("    " + ln) if ln else ln for ln in item.split("\n"))
            lines.append(f"  - |\n{indented}")
        body = "\n".join(lines) + "\n"
    frag_path = frag_dir / f"{name}.yml"
    header = (
        "---\n# Fragment for the refactor pass.\n"
        f"# Compiles into changelogs/changelog.yaml at release time.\n"
    )
    frag_path.write_text(header + body + "\n")
    return frag_path


def write_changelog_yaml(coll):
    """Write a minimal `changelogs/changelog.yaml` placeholder.

    The standard Ansible changelog YAML structure:

        ---
        ancestor: <prev-version-or-null>
        releases:
          <version>:
            changes:
              <category>:
                - "..."

    For first release of a refactored series, we record `ancestor: 0.3.0`
    and an unreleased in-progress entry. This file is overwritten by the
    Galaxy release tooling at release time.
    """
    coll_dir = ROOT / coll
    cgy = coll_dir / "changelogs" / "changelog.yaml"
    cgy.parent.mkdir(parents=True, exist_ok=True)
    cgy.write_text(
        "---\n"
        "ancestor: 0.3.0\n"
        "releases:\n"
        "  0.4.0:\n"
        "    changes:\n"
        "      release_summary: |\n"
        "        Refactor + documentation + tests pass — pure code organization, no behavior changes.\n"
        "        See `manage/COMPLEXITY.md` for the full refactor TODO tracker.\n"
        "      minor_changes:\n"
        '        - "See changelogs/fragments/*.yml for the per-collection breakdown."\n'
    )


def main():
    print("Generating changelogs/ + fragments/ for every collection...")
    for coll, fragments in COLLECTIONS.items():
        coll_dir = ROOT / coll
        # Always ensure the changelogs dir exists and write the placeholder.
        write_changelog_yaml(coll)

        # Special note: mps-base + mps-terminal get the meta-removal line.
        for frag_name, kind, items in fragments:
            path = write_fragment(coll, frag_name, kind, items)
            print(f"  {coll}/{path.relative_to(coll_dir)}")

        if coll in META_REMOVAL:
            note = META_REMOVAL[coll]
            # Wrap as a release_summary fragment because it's a cross-cutting note.
            body = (
                "---\nrelease_summary: |\n"
                + "\n".join(("  " + ln) if ln else ln for ln in note.split("\n"))
                + "\n"
            )
            path = (
                ROOT
                / coll
                / "changelogs"
                / "fragments"
                / "remove-mps-meta-collection.yml"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body)
            print(f"  {coll}/{path.relative_to(coll_dir)}")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
