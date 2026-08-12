REPOS := ". ../mps-base ../mps-meta ../mps-os ../mps-users ../mps-optimize ../mps-terminal ../mps-development ../mps-desktop ../mps-hardening ../mps-backup ../examples"

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

