# `manage` repository

Cross-repo orchestration for the `mps.*` Ansible collection ecosystem.
Holds the Justfile that drives `git-status`, `git-pull`, `git-commit`,
`run-example`, `install-forced`, and `lint` across every collection,
plus documentation and per-collection doc-generation scripts.

## Galaxy

This is not an Ansible collection — it's a tool / docs repo.

## Layout

```
manage/
├── AGENTS.md                                # cross-collection conventions + per-collection overview table
├── Justfile                                 # cross-repo targets (see below)
├── .ansible-lint / .yamllint                # local lint configs (the canonical source for propagation)
└── *.py                                     # Python helpers — see table below
```

## Quick start

```bash
# Show all targets
just --list

# Lint everything
just lint

# Cross-collection ops
just git-status          # show git status -sb per collection + latest commit
just git-pull            # git pull --ff-only per repo; skip dirty
just git-commit 'msg'     # git add -A && commit -m 'msg' && push, every dirty repo

# Apply a playbook against an example inventory
just run-example home local bootstrap.yml

# Build + install every mps.* collection into ../.ansible/ansible_collections/
just install-forced
```

See [`Justfile`](Justfile) for the full target list.

## Cross-repo scripts

Three Python scripts live here. Each is idempotent and re-runnable:

| Script | Purpose |
|---|---|
| `propagate_lint_configs.py` | Copies `mps-base/.ansible-lint` + `mps-base/.yamllint` into every collection's root, registers them in `galaxy.yml build_ignore`, and fixes missing trailing newlines. |
| `gen_molecule_scenarios.py` | Writes a 4-file Molecule scenario (`molecule.yml` + `converge.yml` + `verify.yml` + `requirements.yml`) into every role under every collection. |
| `gen_changelog_fragments.py` | Writes `changelogs/changelog.yaml` + per-change fragments under `changelogs/fragments/*.yml` into every collection. |

Each is referenced from the modified file's commit message; rerunning
after editing the canonical source in `mps-base` keeps every consumer
in sync.

## Conventions

This is the **canonical source of truth** for cross-collection conventions. See `AGENTS.md` for:

- Role structure (`install` / `facts` / `configure` sub-step pattern)
- Task naming (bare action phrases — no `<ROLE> -` prefix)
- Toggle variable pattern (`<role>_enable_<component>: bool`)
- Per-user opt-in via `user_roles.<key>: true` in `users_catalog`
- Identity model (single source of truth in `mps.base.identity`)

Any change that touches multiple collections belongs here first.

## See also

- Each leaf collection's own `AGENTS.md` and `README.md`
- `examples/AGENTS.md` and `examples/README.md` for the inventory pattern

## License

GPL-3.0-or-later
