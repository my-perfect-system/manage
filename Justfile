REPOS := "../mps-base ../mps-os ../mps-users ../mps-optimize ../mps-terminal ../mps-development ../mps-desktop ../mps-hardening ../mps-backup ../examples"

default: status

# Show git status of every collection repo
status:
    #!/usr/bin/env bash
    set -uo pipefail
    for repo in {{REPOS}}; do
        echo "==> $repo"
        if ! git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
            echo "  SKIP: not a git repo"
        else
            git -C "$repo" status -sb
            git -C "$repo" log --pretty=oneline | head -n 1 | awk '{$1=""; sub(/^ /,""); print}'
        fi
        echo
    done

# Fast-forward pull every repo; skip dirty working trees
pull:
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
commit msg:
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
        if ! git -C "$repo" remote get-url origin >/dev/null 2>&1; then
            if git -C "$repo" add -A && git -C "$repo" commit -m "{{msg}}"; then
                echo "  COMMITTED LOCALLY (no remote) — run \`just init-remote\` to push"
                failed=$((failed + 1))
            else
                echo "  ERROR: add/commit failed"
                failed=$((failed + 1))
            fi
            echo
            continue
        fi
        if git -C "$repo" add -A \
        && git -C "$repo" commit -m "{{msg}}" \
        && git -C "$repo" push; then
            committed=$((committed + 1))
        else
            echo "  ERROR: add/commit/push failed"
            failed=$((failed + 1))
        fi
        echo
    done
    echo "Summary: $committed committed+pushed, $skipped clean, $failed failed"

