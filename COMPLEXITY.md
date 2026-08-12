# Complexity Overview — my-perfect-system

Snapshot of every role across all 9 Ansible collections in `my-perfect-system/`,
categorized by complexity. Used to plan refactor passes for simplification.

Generated from a full read of `roles/*/tasks/*.yml` and a glance at
`templates/`, `files/`, `handlers/`, `defaults/` for each role.

## Complexity scale

- **1 — Simple**: install + copy, no logic. Few tasks (<10), no loops, no
  conditional gating beyond a top-level toggle.
- **2 — Medium**: per-user loops, conditional logic, multiple sub-steps,
  multi-file templates with a few Jinja variables, integration of one or
  two external modules. 10–30 tasks.
- **3 — Complex**: heavy Jinja templating (loops/conditionals inside
  templates), many sub-tasks, complex `set_fact` chains, multi-step
  orchestration, multiple handler chains, cross-collection data flow.

## Tally

| Complexity | Count | % |
|---|---|---|
| 1 — Simple | 21 | 43% |
| 2 — Medium | 19 | 39% |
| 3 — Complex |  9 | 18% |
| **Total**    | **49** | **100%** |

## mps-base

| Role     | Tasks | Cx | Notes |
|----------|-------|----|-------|
| identity | 1 file × 4 tasks | **3** | Pure data orchestration: nested Jinja `combine` / `selectattr` / `unique` in a 3-step `set_fact` chain. Canonical single source of truth for every per-user role in the `mps.*` ecosystem. |

## mps-os

| Role            | Tasks | Cx | Notes |
|-----------------|-------|----|-------|
| package_manager | 4 files / 13 tasks | **2** | Conditional Jinja `sources.list` (4 pockets × components × deb-src), unattended-upgrades, 4 feature toggles |
| system_settings | 5 files / 14 tasks | **2** | locale/keyboard/console/time, 4-handler chain, timezone `register`/`when`, inline `copy` content |
| system_tools    | 8 files / 9 tasks  | **1** | Pure apt-by-category; only `core.yml` adds a `tasksel install standard` shell step |

## mps-users

| Role   | Tasks | Cx | Notes |
|--------|-------|----|-------|
| users  | 4 files / 12 tasks | **3** | Root-special-path idempotency (`chpasswd` / `chsh` / `chfn` / `chage` with `stdout.split`), `password_hash` filter chain, `lookup('password')` |
| sudo   | 3 files / 7 tasks  | **3** | Jinja loops in `sudoers` template, `visudo -c -f` validation chain, mixed `user` + `gpasswd` logic with custom `failed_when` |
| ssh    | 4 files / 8 tasks  | **2** | `subelements` loop, nested `include_tasks`, `lookup('file')` |
| groups | 4 files / 5 tasks  | **2** | `rejectattr` / `selectattr` filter chain for group extraction |

## mps-terminal

| Role     | Tasks | Cx | Notes |
|----------|-------|----|-------|
| nvim     | 4 files            | **3** | apt + npm tools + upstream tarball extract/symlink + per-user venv + pip + cargo installs + yazi tool pipeline |
| fonts    | 1 file + handler   | **3** | `get_url` → `unarchive` → `copy` → cleanup loop with `zip + stat` combo + `fc-cache` handler |
| bash     | 3 files / 11 tasks | **2** | Per-user copy + legacy stat/migrate cleanup loops |
| python   | 3 files / 7 tasks  | **2** | Per-user venv + pip + `.bashrc` `lineinfile` + recurse permission fix |
| rust     | 3 files / 9 tasks  | **2** | Per-user rustup via `command`, toolchain reset, 2 `.bashrc` lineinfile entries, ownership sweep |
| kitty    | 1 file             | **1** | apt + `update-alternatives` + per-user dotfile tree copy (inlined) |
| tmux     | 1 file             | **1** | apt + per-user copy of `tmux` + `tmuxinator` configs (inlined) |
| vim      | 1 file             | **1** | conditional apt groups + per-user copy of `.vimrc` + `.NERDTreeBookmarks` (inlined) |
| skeletons| 1 file             | **1** | single `file` + `copy` to `/etc/mps/skeletons` (inlined) |
| scripts  | 1 file             | **1** | per-user `.local/bin` copy (inlined; install.yml stub deleted) |

## mps-desktop

| Role        | Tasks | Cx | Notes |
|-------------|-------|----|-------|
| qtile       | 4 files | **3** | 21 jinja2 templates (some with loops), heavy `set_fact` chains, pip venv + git clone |
| kanata      | 1 file  | **3** | per-user rustup / cargo install, udev rules, systemd user service, `enable-linger` loop (inlined) |
| essentials  | 4 files | **2** | per-user dotfile copy loops + per-user fact builders |
| rofi        | 4 files | **2** | per-user dotfile + script copy loops + `set_fact` builders |
| thunar      | 4 files | **2** | per-user dotfile copy loop + `set_fact` |
| wm          | 4 files | **2** | per-user copy loops with `item.src` gating + `set_fact` |
| brave       | 2 files | **1** | apt + GPG keyring + repo add (configure.yml stub deleted) |
| firefox     | 2 files | **1** | single apt install (configure.yml stub deleted) |
| gnometools  | 2 files | **1** | single package install with inline list (configure.yml stub deleted) |
| grubmenu    | 2 files | **1** | file copies + `/etc/default/grub` lineinfile + `update-grub` (configure.yml stub deleted) |
| lightdm     | 2 files | **1** | directory ensure + single lineinfile to greeter conf (configure.yml stub deleted) |
| plymouth    | 2 files | **1** | package install + theme copy + `replace` in `.plymouth` (configure.yml stub deleted) |
| spotify     | 2 files | **1** | GPG key download/dearmor + apt repo + install (configure.yml stub deleted) |
| thunderbird | 2 files | **1** | single package install (configure.yml stub deleted) |
| x11         | 2 files | **1** | single package install (configure.yml stub deleted) |

## mps-development

| Role     | Tasks | Cx | Notes |
|----------|-------|----|-------|
| espidf   | 1 file            | **2** | multi-version loop (`espidf_versions`), per-user bash clone + install + exports, per-version activator copy (inlined with `block:`) |
| lmstudio | 1 file            | **2** | stat-gated idempotency, get_url + sudo run, appimage download, inline `.desktop` template (inlined with `block:`) |
| opencode | 1 file            | **2** | stat-gated installer, 2× `synchronize` dotfile syncs, ownership fixups (inlined with `block:`) |
| unity    | 1 file            | **2** | GPG keyring + `apt_repository` with inline `signed-by`, VS Code `dpkg -s` detection + deb install gated by `unity_enable_vscode` (inlined with `block:`) |
| dotnet   | 1 file            | **1** | download + run installer, mkdir, cleanup (inlined with `block:`) |
| java     | 1 file            | **1** | single `apt` task; per-user loop with role toggle (inlined with `block:`) |
| latex    | 1 file            | **1** | single `apt` task (`texlive-full`); per-user loop with role toggle (inlined with `block:`) |

## mps-hardening

| Role     | Tasks | Cx | Notes |
|----------|-------|----|-------|
| firewall | 1 file        | **3** | `rules.v4.j2` has 2 for-loops + 2 if-blocks, conditional sysctl, service-unit template |
| lockdown | 1 file        | **3** | git clone external repo, crypto SSH keypair, slurp + authorized_key, 5 regex `lineinfile` overrides into external CIS defaults, **sub-playbook invocation** with `become_user` (inlined) |
| auditd   | 1 file / 6 tasks    | **2** | apt install, 2 dir ensures, 2 templates (`auditd.conf` with ~13 vars, systemd override) |
| aide     | 1 file              | **1** | apt install + mkdir + small static template |
| apparmor | 1 file              | **1** | apt install + `synchronize` profiles from `files/` + chmod/chown |

## mps-optimize

| Role    | Tasks | Cx | Notes |
|---------|-------|----|-------|
| ramdisks| 3 files | **2** | backup → unmount → mount → restore, set_fact, block-gated `when:` with marker file |
| kmscon  | 1 file  | **1** | apt + mkdir + static config copy |
| zram    | 1 file  | **1** | apt + small blockinfile + service restart |

## mps-backup

| Role  | Tasks | Cx | Notes |
|-------|-------|----|-------|
| backup| 1 file | **2** | per-user loop with `become_user`, `synchronize` module, one feature toggle (`backup_enable_persist_brave`), cross-collection data dependency on `mps.base.identity` (inlined) |

---

# Tier composition (post-`mps-meta` collapse)

The `mps-meta` collection was deleted. Composition is now expressed by 7
playbooks in `examples/inventories/home/playbooks/`:

| Playbook | Imports | Plus roles |
|---|---|---|
| `bootstrap.yml`         | —                                                | 8 base roles (identity + 3 os + 4 users) |
| `terminal_minimal.yml`  | `bootstrap.yml`                                  | bash, vim, tmux |
| `terminal_full.yml`     | `bootstrap.yml`                                  | bash, vim, nvim, tmux, kitty, fonts, python, rust, scripts, skeletons |
| `desktop_minimal.yml`   | `terminal_minimal.yml`                           | x11, wm, qtile, rofi, thunar, essentials, lightdm, gnometools, brave |
| `desktop_full.yml`      | `terminal_full.yml`                              | x11, wm, qtile, rofi, thunar, essentials, kanata, lightdm, plymouth, grubmenu, gnometools, firefox, thunderbird, brave, spotify |
| `workstation_minimal.yml` | `desktop_full.yml`                             | zram, ramdisks, kmscon, opencode, firewall, apparmor, auditd, aide, lockdown |
| `workstation_full.yml`  | `desktop_full.yml`                               | zram, ramdisks, kmscon, opencode, java, dotnet, espidf, latex, lmstudio, unity, firewall, apparmor, auditd, aide, lockdown |

---

# Refactor TODO tracker

This is the live checklist. Use `git diff` on this section to see what
changed since the last review.

## Status at a glance

| Category | Done | Open | Total |
|---|---|---|---|
| Stub + indirection collapse (high-leverage) | **3** | 0 | 3 |
| Medium-leverage (logic simplification)       | **4** | 0 | 4 |
| High-touch (architecture)                    | **3** | 0 | 3 |
| Cross-cutting                                | **1** | 0 | 1 |
| Deferred (out of scope here)                 | 0 | 6 | 6 |
| **Total**                                    | **11** | **6** | **17** |

## Detailed checklist

### Stub + indirection collapse (high-leverage, mechanical)

- [x] **Stub `configure.yml` collapse** — 9 desktop + 1 scripts `install.yml`
      stub deleted; include line in main.yml removed.
- [x] **mps-meta → playbooks** — `mps-meta/` collection deleted; 7 tier
      playbooks in `examples/inventories/home/playbooks/` replace all meta
      roles. Old playbooks (`terminals.yml`, `desktops.yml`,
      `workstations.yml`) replaced; the `mps.meta.workstation.minimal` typo
      is fixed.
- [x] **Main.yml `include_tasks` indirection** — 6 single-include roles
      (backup, kitty, tmux, vim, skeletons, lockdown) + 2 two-include roles
      (kanata, scripts) + 7 dev roles flattened. ~30% fewer YAML files.

### Medium-leverage (logic simplification, behavior-preserving)

- [x] **Auditd systemd override → `files/`** — override.conf.j2 had a single
      Jinja var (`auditd_localstatedir`) with a fixed default of `/var`.
      Moved to `files/usr/lib/systemd/system/auditd.service.d/override.conf`,
      `template:` → `copy:`. Deleted the now-empty `templates/usr/` tree.
- [x] **`users/add.yml` root special-path consolidation** — the 4 ch* tasks
      (`chpasswd` / `chsh` / `chfn` / `chage`) plus the 2 `getent` reads
      were guarded by 6 individual `when: ... selectattr('name', 'equalto',
      'root') | list | length > 0` clauses. Wrapped in a single `block:`
      with one shared `when:`. Same semantics, fewer guard repetitions.
- [x] **Per-user loop boilerplate → filter plugin** — created
      `mps-base/filter_plugins/mps_filter_users.py` (~35 lines). Filter
      signature: `mps_filter_users(users, role_key, state='present')`.
      Skips empty dicts internally (replaces the `user != {}` defensive
      guard). All 7 `mps-development` roles now use:
      `loop: "{{ identity_users_resolved | mps_filter_users('development_X') }}"`
      Each role dropped 2 lines of `when:` boilerplate (~14 lines saved
      total). Filter is reusable for any future per-user role.
- [x] **`sudoers` validation** — replaced `template: validate: visudo` with
      `community.general.sudoers` module. The module writes per-user
      `/etc/sudoers.d/<name>` files directly (`sudoers_path` defaults to
      `/etc/sudoers.d`) and validates via `visudo` internally
      (`validation: required`). The `Cmnd_Alias` indirection is gone —
      `entity.sudo.macros` is resolved inline to a flat command list per
      user via Jinja `map('extract', sudo_macros) | flatten | unique`.
      Deleted `templates/sudoers.j2` + `templates/macro.j2`. Added
      `community.general: ">=1.0.0"` to `mps-users/galaxy.yml` dependencies.
      `argument_specs.yml` description updated to reflect the new model.

### High-touch (architecture, needs design decision)

- [x] **mps-base/identity** — moved the heavy Jinja data-shaping into
      the `mps.base.identity` filter plugin surface. Two new filters
      added: `mps_resolve_users(users_list, users_catalog)` (produces
      `identity_users_resolved`) and `mps_user_groups(users)` (produces
      `identity_user_groups`). `tasks/main.yml` shrank from 70 to 51
      lines and is now pure orchestration. Filters are unit-testable
      from plain Python.
- [x] **mps-hardening/firewall + lockdown** — **OBSOLETE / accepted**.
      Both roles are domain specialists with template-internal
      complexity (firewall: iptables rules.v4.j2 with for-loops;
      lockdown: external CIS playbook invocation). The complexity is
      load-bearing — refactoring would mean rewriting iptables / CIS
      orchestration from scratch for marginal gain. **Decision: keep
      both as-is.**
- [x] **mps-terminal/nvim + mps-terminal/fonts** — **OBSOLETE /
      accepted**. nvim has a sprawling task graph (apt + npm + tarball
      + per-user venv + pip + cargo + yazi). fonts has a tight
      get_url → unarchive → copy → cleanup loop. Both are toolkit
      install roles where the apparent complexity IS the product.
      Splitting into `nvim-core` + `nvim-extras` would add indirection
      without reducing real LoC. **Decision: keep both as-is.**

### Cross-cutting

- [x] **Bucket-D multi-phase roles** — reviewed per-role:
  - **Flattened** (4): `mps-terminal/{bash,python,rust,nvim}` were
    pure install+configure shims; inlined into main.yml. nvim also
    absorbed `tools.yml`. Per-user loops switched to the
    `mps_filter_users` filter plugin.
  - **Kept multi-file** (12): `mps-desktop/{essentials,qtile,rofi,
    thunar,wm}` keep their `facts.yml` set_fact phase; `mps-os/
    {package_manager,system_settings,system_tools}` keep their
    sub-area organization (locale/keyboard/console/time; 7 tool
    buckets; configure/install/upgrades); `mps-users/
    {groups,ssh,sudo,users}` keep distinct add/del/facts operations.
  - **Extracted** the byte-identical `Assert Debian 13 target`
    block from **7 role main.ymls** into a new shared role
    `mps.base.assert_debian13`. All 7 roles now declare it in their
    `meta/main.yml` `dependencies:` block. Single source of truth;
    behavior identical (assert runs before each role's own tasks).

### Deferred (out of scope here — regenerate in dedicated sessions)

- [ ] Per-role / per-collection **README.md** files
- [ ] **AGENTS.md** files inside individual collection subdirectories
- [ ] **Molecule** tests for every role
- [ ] **Lint configs** (`.ansible-lint`, `.yamllint`) — currently absent in new repos; old `mps-collections/` keeps them as reference
- [ ] `mps-collections/AGENTS.md` and `mps-examples/AGENTS.md` updates reflecting the new repo split
- [ ] New changelog fragments (will be added once the refactor work is wrapped up)
