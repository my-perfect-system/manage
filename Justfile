REPOS := "../manage ../mps-base ../mps-os ../mps-users ../mps-optimize ../mps-terminal ../mps-development ../mps-desktop ../mps-hardening ../mps-backup ../examples"

default: usage

usage:
    #!/usr/bin/env bash
    set -uo pipefail
    just --list

# Lists all installed collections
list-collections inventory="home":
    #!/usr/bin/env bash
    set -uo pipefail
    cd ../examples/inventories/{{inventory}} \
        && ansible-galaxy collection list

# Lists every role in every collection with its description
list-roles:
    #!/usr/bin/env bash
    set -uo pipefail
    for repo in {{REPOS}}; do
        if [ "$(basename "$repo")" = "examples" ]; then
            continue
        fi
        if [ ! -d "$repo/roles" ]; then
            continue
        fi
        col_name=$(basename "$repo")
        echo "==> $col_name"
        for role_dir in "$repo/roles"/*/; do
            [ -d "$role_dir" ] || continue
            role_name=$(basename "$role_dir")
            meta="$role_dir/meta/main.yml"
            if [ -f "$meta" ]; then
                desc=$(python3 -c "import yaml,sys; d=yaml.safe_load(open('$meta')) or {}; print(d.get('galaxy_info',{}).get('description',''))" 2>/dev/null || echo "")
                printf "  %-22s %s\n" "$role_name" "$desc"
            else
                printf "  %-22s (no meta)\n" "$role_name"
            fi
        done
        echo
    done

# Show git status of every collection repo
git-status:
    #!/usr/bin/env bash
    set -uo pipefail
    for repo in {{REPOS}}; do
        echo "==> $repo"
        if ! git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
            echo "  SKIP: not a git repo"
        else
            git -C "$repo" status -sb
            git -C "$repo" log --pretty=oneline \
                | head -n 1 \
                | awk '{$1=""; sub(/^ /,""); print}'
        fi
        echo
    done

# Fast-forward pull every repo; skip dirty working trees
git-pull:
    #!/usr/bin/env bash
    set -uo pipefail
    for repo in {{REPOS}}; do
        echo "==> $repo"
        if ! git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
            echo "  SKIP: not a git repo"
            echo
            continue
        fi
        if ! git -C "$repo" diff --quiet HEAD 2>/dev/null; then
            echo "  SKIP: working tree dirty — commit or stash first"
            echo
            continue
        fi
        git -C "$repo" pull --ff-only || echo "  ERROR: pull failed"
        echo
    done

# Add, commit (with MSG), and push every dirty repo
git-commit msg:
    #!/usr/bin/env bash
    set -uo pipefail
    committed=0
    skipped=0
    failed=0
    for repo in {{REPOS}}; do
        echo "==> $repo"
        if ! git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
            echo "  SKIP: not a git repo"
            skipped=$((skipped + 1))
            echo
            continue
        fi
        if [ -z "$(git -C "$repo" status --porcelain)" ]; then
            echo "  SKIP: clean"
            skipped=$((skipped + 1))
            echo
            continue
        fi
        if git -C "$repo" add -A \
        && git -C "$repo" commit -m "{{msg}}" \
        && git -C "$repo" push; then
            echo " COMMIT: add/commit/push successful"
            committed=$((committed + 1))
        else
            echo "  ERROR: add/commit/push failed"
            failed=$((failed + 1))
        fi
        echo
    done
    echo "Summary: $committed committed+pushed, $skipped clean, $failed failed"

# Show git status of every collection repo
run-example name inventory playbook:
    #!/usr/bin/env bash
    set -uo pipefail
    export ANSIBLE_NOCOWS=1
    cd ../examples/inventories/{{name}} \
        && ansible-playbook \
            -i inventory_{{inventory}}.ini \
            playbooks/{{playbook}}.yml

# Force build every collection tarball and force-install to the local collections path
install-forced collections_path="../.ansible/ansible_collections":
    #!/usr/bin/env bash
    set -uo pipefail
    mkdir -p "{{collections_path}}"
    built=0
    installed=0
    failed=0
    for repo in {{REPOS}}; do
        if [ "$(basename "$repo")" = "examples" ]; then
            continue
        fi
        if [ "$(basename "$repo")" = "manage" ]; then
            continue
        fi
        echo "==> $repo"
        if (cd "$repo" && ansible-galaxy collection build --force 2>&1 | tail -2); then
            built=$((built + 1))
        else
            echo "  ERROR: build failed"
            failed=$((failed + 1))
            echo
            continue
        fi
        tarball=$(ls -t "$repo"/mps-*.tar.gz 2>/dev/null | head -1)
        if [ -z "$tarball" ]; then
            echo "  ERROR: no tarball after build"
            failed=$((failed + 1))
            echo
            continue
        fi
        if ansible-galaxy collection install "$tarball" --force -p "{{collections_path}}" 2>&1 | tail -2; then
            installed=$((installed + 1))
        else
            echo "  ERROR: install failed"
            failed=$((failed + 1))
        fi
        echo
    done
    echo "Summary: $built built, $installed installed, $failed failed"

# Run ansible-lint and yamllint on every mps.* collection.
# Skips `manage` (Python/tools only) and `examples` (sample inventory, not
# a collection source). Exits non-zero if any collection fails. Use
# `just install-forced` first so cross-collection dependencies
# (mps.base.identity, community.crypto, community.general) resolve.
lint:
    #!/usr/bin/env bash
    set -uo pipefail
    passed=0
    failed=0
    skipped=0
    for repo in {{REPOS}}; do
        name=$(basename "$repo")
        case "$name" in
            manage|examples) skipped=$((skipped + 1)); continue ;;
        esac
        if [ ! -f "$repo/.ansible-lint" ] || [ ! -f "$repo/.yamllint" ]; then
            echo "==> $name: SKIP (no lint configs found — run propagate_lint_configs.py)"
            skipped=$((skipped + 1))
            continue
        fi
        echo "==> $name"
        cd "$repo"
        yamllint_out=$(yamllint -c .yamllint . 2>&1)
        yamllint_status=$?
        ansible_lint_out=$(ansible-lint --offline 2>&1)
        ansible_lint_status=$?
        if [ "$yamllint_status" -eq 0 ] && [ "$ansible_lint_status" -eq 0 ]; then
            echo "  PASS"
            passed=$((passed + 1))
        else
            echo "  FAIL (yamllint exit=$yamllint_status, ansible-lint exit=$ansible_lint_status)"
            if [ "$yamllint_status" -ne 0 ]; then
                echo "$yamllint_out" | sed 's/^/    yamllint:    /' | head -10
            fi
            if [ "$ansible_lint_status" -ne 0 ]; then
                echo "$ansible_lint_out" | sed 's/^/    ansible-lint: /' | head -10
            fi
            failed=$((failed + 1))
        fi
        cd - > /dev/null
    done
    echo
    echo "Summary: $passed passed, $failed failed, $skipped skipped"
    [ "$failed" -eq 0 ]

