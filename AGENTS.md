# AGENTS.md — my-perfect-system

This folder hosts the source for every Ansible collection in the
`mps.*` ecosystem. Each subdirectory is intended to become its own Git
repository (one per collection) and to be published to Ansible Galaxy
as the long-term distribution path. Currently the repos are local
git checkouts, with the old `mps-collections/` repo kept as reference.

## Repos

| Repo | Galaxy name | Version | Depends on | Purpose |
|---|---|---|---|---|
| `mps-base/` | `mps.base` | 0.1.0 | — | Anchor collection. Holds the shared `mps.base.identity` role and the documentation of the cross-collection conventions. All leaves depend on it. |
| `mps-os/` | `mps.os` | 0.3.0 | mps.base, ansible.posix | Operating system init — package sources, unattended-upgrades, locale/keyboard/timezone, core CLI tooling. Platform-agnostic naming; content is still Debian 13 (trixie) focused. |
| `mps-users/` | `mps.users` | 0.3.0 | mps.base, ansible.posix | User accounts, groups, SSH keys, sudoers. Per-user data model (catalog + list) lives in `mps.base.identity`. |
| `mps-optimize/` | `mps.optimize` | 0.3.0 | mps.base, ansible.posix | System-level performance tuning — zram, tmpfs ramdisks, kmscon userspace console. |
| `mps-terminal/` | `mps.terminal` | 0.3.0 | mps.base, ansible.posix | Shell and editor environment — bash, vim, nvim, tmux, kitty, fonts, python, rust, scripts, skeletons. Mostly per-user. |
| `mps-development/` | `mps.development` | 0.3.0 | mps.base, ansible.posix | Per-user development tooling — opencode, java, dotnet, espidf, latex, lmstudio, unity. |
| `mps-desktop/` | `mps.desktop` | 0.3.0 | mps.base, ansible.posix | Desktop GUI / window manager environment — x11, gnometools, grubmenu, lightdm, plymouth, plus per-user qtile/rofi/thunar/wm/essentials/kanata and system-level firefox/thunderbird/brave/spotify. |
| `mps-hardening/` | `mps.hardening` | 0.3.0 | mps.base, ansible.posix, community.crypto | System-level hardening — firewall (iptables), apparmor, auditd, AIDE, CIS lockdown (clones `ansible-lockdown/DEBIAN13-CIS`). |
| `mps-backup/` | `mps.backup` | 0.3.0 | mps.base, ansible.posix | Per-user backup restore — SSH keys, config, brave bookmarks, home directory. |
| `mps-meta/` | `mps.meta` | 0.1.0 | mps.base + all 8 leaves above | Composition-only meta roles that bundle leaf roles from the other collections into host classes (`bootstrap`, `terminal_full`/`terminal_minimal`, `desktop_full`/`desktop_minimal`, `workstation_full`/`workstation_minimal`). Each role is `meta/main.yml` listing `dependencies:` + a no-op `tasks/main.yml`. No own tasks. |

`manage/` hosts the cross-repo `Justfile` (status / pull / commit / force-install across all leaf collections — see [Build, install, run](#build-install-run)). `examples/` hosts reference inventory layouts under `examples/inventories/<env>/`.

## Per-repo layout

```
mps-<col>/
├── galaxy.yml                  # collection metadata + dependencies
├── changelogs/                 # changelog fragments + compiled changelog.yaml
├── meta/                       # collection-level runtime.yml
└── roles/                      # the actual roles
    └── <role>/
        ├── defaults/main.yml   # role-specific defaults + per-role toggle vars
        ├── files/              # static files deployed to hosts (optional)
        ├── meta/
        │   ├── main.yml        # galaxy_info + role dependencies
        │   └── argument_specs.yml
        └── tasks/
            ├── main.yml        # orchestrator: include install.yml / facts.yml / configure.yml etc.
            ├── install.yml     # system package installation
            ├── configure.yml   # per-user config deployment
            └── facts.yml       # role-internal set_fact computations (see below)
```

## Role structure conventions

Every role follows the same flow inside `tasks/main.yml`:

```yaml
- include_tasks: install.yml      # system-level installation
- include_tasks: facts.yml        # role-internal set_fact computations
- include_tasks: configure.yml    # per-user config deployment
```

Some roles also include:

- `convert.yml` (e.g. `mps.optimize.ramdisks`) — multi-step inline operations too large for a single task block.

## Task naming convention

Every `name:` field in `tasks/*.yml` and `handlers/*.yml` is a **bare action phrase** describing what the task does — no role-name prefix, no quoted string wrappers.

Examples:

```yaml
- name: Install bash-completion when enabled
- name: Deploy per-user .bashrc
- name: Configure net.ipv4.ip_forward for NAT
- name: Rebuild font cache
```

Rules:
- No `<ROLE>_MAIN - …`, no `<ROLE> - …`, no `DESK_BRAVE_INSTALL - …`. The role context is already implied by the file path.
- Names are unquoted (no `"..."`).
- They correspond 1:1 to the action — quick to scan in ansible-playbook output.
- `notify:` references match the bare name of the handler task. Handler files (`handlers/main.yml`) follow the same convention.

Do **not** reintroduce the historical `<ROLE_NAME> - <message>` prefix. The first thing a future reader of a play log needs is the action, not the file path.

## `mps.base.identity` — shared identity model

`mps.base.identity` is the **single source of truth** for the per-user identity data model and resolve protocol. Every per-user role declares it as a `meta/main.yml` dependency — there is no per-role `resolve.yml` step.

It produces four facts:

| Fact | Description |
|---|---|
| `identity_users_resolved` | List of dicts, one per `users_list` entry: `id`, `name`, `state`, `user_roles`, plus every other field from the matching `users_catalog` entry. |
| `identity_users_present` | `identity_users_resolved` filtered to `state == 'present'`. |
| `identity_users_absent` | `identity_users_resolved` filtered to `state == 'absent'`. |
| `identity_user_groups` | Flat, deduplicated list of all group names referenced by present users (sourced from each user's `group` and `groups` fields). |

Each consuming role filters `identity_users_resolved` by its own `user_roles.<key>` flag inline in its task loops:

```yaml
loop: "{{ identity_users_resolved }}"
loop_control:
  loop_var: entity
when:
  - entity.state == 'present'
  - entity.user_roles.terminal_bash | default(false)   # <-- the per-role key
```

### `users_catalog` and `users_list` — single source of truth

Both inputs to the identity model are declared and defaulted **exactly once** in `mps-base/roles/identity/`:

- `mps-base/roles/identity/meta/argument_specs.yml` — canonical spec, including the **full single-entity schema** for a `users_catalog` entry (every supported field: `name`, `uid`, `group`, `groups`, `append_groups`, `comment`, `shell`, `home`, `create_home`, `system`, `expires`, `password`, `ssh_keys`, `authorized_keys`, `sudo`, `user_roles`).
- `mps-base/roles/identity/defaults/main.yml` — canonical defaults, including sensible per-user field defaults (`user_shell`, `user_create_home`, `user_system`, `user_expires`, `user_groups`, `admin_groups`, `user_append_groups`, `user_password`), two role-set profiles (`user_roles_default`, `user_roles_minimal`), and empty `users_catalog: {}` / `users_list: []` ready to be overridden per host.

Per-user roles **do not** declare `users_catalog` or `users_list` in their own `argument_specs.yml` or `defaults/main.yml` — they flow through the play scope to the identity role via the dependency chain. Re-declaring them would duplicate the schema and risk drift.

### Identity resolution protocol

The historical per-role `resolve.yml` was removed from every role. The steps now live exclusively in `mps.base.identity`:

1. **Validate** — assert `item.name in users_catalog` for each present user
2. **Resolve** — combine catalog entry with id/name/state/user_roles into `identity_users_resolved`
3. **Split** — filter into present/absent lists
4. **Extract** — flatten each present user's `group` and `groups` fields into `identity_user_groups`

Per-user roles no longer need a resolve step. The `<role>_users_present` / `<role>_users_absent` variables that used to be set per-role are gone — `identity_users_resolved` is filtered inline per role.

## Toggle variable pattern

Every yes/no subcomponent toggle is named `<role>_enable_<component>: bool`. Lists and config values keep their existing names; their execution is gated by the corresponding `enable_*` toggle.

Examples:

```yaml
bash_enable_bash_completion: true      # was: bash_install_bash_completion
bash_enable_aliases: true              # was: bash_install_aliases
bash_enable_fun_packages: true         # new gate for the bash_fun_packages list
firewall_enable_icmp: true             # was: firewall_allow_icmp
firewall_enable_nat_ip_forwarding: false # was: firewall_nat_enable_ip_forwarding
lockdown_enable_execute: false         # was: lockdown_execute
package_manager_enable_repos_main: true
system_tools_enable_archives: true
```

Role `defaults/main.yml` lists the toggles. Tasks apply them via `when:` clauses. `meta/argument_specs.yml` documents them for runtime validation.

## Identity user roles (denylist model)

Per-user roles are **disabled by default**. Users opt in via `user_roles.<key>: true` in their catalog entry. Keys are prefixed with the collection name:

```yaml
users_catalog:
  user01:
    user_roles:
      terminal_bash: true
      terminal_vim: true
      desktop_qtile: true
      desktop_rofi: true
      development_opencode: true
      backup_backup: true
```

The convention is: `user_roles_default` defines the global default per-user role set in `mps-base/roles/identity/defaults/main.yml`, and per-user catalog entries reference it via `"{{ user_roles_default }}"`. A second preset `user_roles_minimal` is provided for restricted users.

## Build, install, run

From the sibling `mps-examples/` directory (currently at `/home/jb/repo/github/mps/mps-examples/`):

```bash
make install            # build + install every collection from local sources
make install-galaxy     # install every collection from Galaxy (requires publishing first)
make install-<col>      # build + install single collection from local source
make list-roles         # list every role with its tier/type/description
make play-<col>.<tier>  # run a single playbook (base / common / full)
make play-base          # run every base playbook
make clean              # remove tarballs + installed collections
```

### Cross-repo `Justfile` (`manage/Justfile`)

Targets that span all 9 leaf + meta collections — run from `manage/` (path-relative to the sibling collections):

```bash
just                          # default → usage (just --list)
just list-collections [inv]   # list installed collections in examples/inventories/<inv>
just list-roles               # list every role in every collection with its description
just git-status               # git status -sb per collection, plus latest commit
just git-pull                 # git pull --ff-only per repo; skip dirty
just git-commit 'msg'         # git add -A && commit -m 'msg' && push, every dirty repo
just run-example <name> <inv> <playbook>  # run playbooks/<playbook>.yml against examples/inventories/<name>/inventory_<inv>.ini
just install-forced           # ansible-galaxy collection build --force + install --force into ../.ansible/ansible_collections/
```

Repositories iterated are listed in the `REPOS` variable at the top of the Justfile. The default install path (`../.ansible/ansible_collections`) matches the first `collections_path` entry in `examples/inventories/home/ansible.cfg`.

## Publishing path to Galaxy

Currently every collection is built locally and installed into `mps-collections/.ansible/ansible_collections/mps/`. To publish:

1. Push each subdirectory of `my-perfect-system/` to GitHub under `my-perfect-system/mps-<col>` (one repo per collection).
2. Configure Galaxy import on each repo.
3. Tag a release (e.g. `0.3.0`) — Galaxy auto-builds the tarball and publishes.
4. Consumers then run `ansible-galaxy collection install mps.base mps.os mps.users ...` (or use `make install-galaxy` in `mps-examples/`).

Until publishing is configured, `make install` in `mps-examples/` does the local build+install chain.

## Recent refactoring notes

The following cleanup passes have been committed to the local repos:

- **Task name prefix removed** — every `name:` field in `tasks/*.yml` and `handlers/*.yml` across all 9 collections had its `<ROLE> -` prefix stripped (140 files, 429 names). `notify:` references rewired to the new bare names.
- **Dead options removed** from `argument_specs.yml` + matching defaults:
  - `mps-desktop/qtile`: `qtile_keepass_bin`, `qtile_keepass_db_path`, `qtile_screenlayout_hive_cmd` (keepass integration dropped; screenlayout cmd unused).
  - `mps-hardening/aide`: `aide_conf_file` (never referenced).
  - `mps-hardening/lockdown`: `lockdown_ssh_port`, `lockdown_cis_vars` (ssh_port hardcoded in `hosts.j2`; cis_vars.yml wiring was missing).
- **`users_catalog` / `users_list` centralised** — removed from every per-user role's `argument_specs.yml`. The canonical home is now `mps-base/roles/identity/meta/argument_specs.yml` (with full single-entity schema) and `mps-base/roles/identity/defaults/main.yml` (with sensible defaults and example shapes).
- **`changelogs/` folders removed** from all 9 collections — they will be repopulated after the broader refactoring work is complete.
- **`mps-meta` collection added** — composition-only meta roles (`bootstrap`, `terminal_full`/`terminal_minimal`, `desktop_full`/`desktop_minimal`, `workstation_full`/`workstation_minimal`) that bundle leaf roles from the other collections into host classes. Each meta role is a `meta/main.yml` listing `dependencies:` plus a no-op `tasks/main.yml`. Cross-class composition: `desktop_*` and `workstation_*` depend on `mps.meta.terminal_*`; `workstation_full` additionally lists every `mps.optimize.*` / `mps.development.*` / `mps.hardening.*` leaf explicitly.
- **`manage/Justfile` added** — cross-repo git ops (`git-status`, `git-pull`, `git-commit`), example runner (`run-example`), and force build/install (`install-forced` → `ansible-galaxy collection build --force && install --force` into `../.ansible/ansible_collections/`). Replaces the prior `mps-examples/` Make for local development loops.
- **Feature toggles hoisted to top of `defaults/main.yml`** — every role defaults file with `<rolename>_enable_*` toggles was restructured to put the toggles in a top section under `# Feature toggles — naming pattern: <rolename>_enable_<feature>`, followed by a `# Regular configuration` section. 13 of 49 role defaults files were affected (the rest have no toggles yet). Toggle grouping is now visually consistent across roles.
- **`examples/inventories/home/` reorganised** — `host_vars/testvm.yml` holds the host-specific `ansible_host`; `group_vars/all.yml` holds `ansible_user: deploy` (shared by every host); `group_vars/all/mps_*.yml` are commented-out reference dumps of every collection's role defaults, so users can see what they have available to override.

## Deferred (regenerate in dedicated sessions)

- Per-role / per-collection **README.md** files
- **AGENTS.md** files inside individual collection subdirectories
- **Molecule** tests for every role
- **Lint configs** (`.ansible-lint`, `.yamllint`) — currently absent in new repos; old `mps-collections/` keeps them as reference
- `mps-collections/AGENTS.md` and `mps-examples/AGENTS.md` updates reflecting the new repo split
- Cross-collection tier model (base / common / optional) — currently each leaf carries its own 3-tier playbook structure; future design may consolidate
- New changelog fragments (will be added once the refactor work is wrapped up)
