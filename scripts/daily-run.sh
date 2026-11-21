#!/usr/bin/env bash
# Horizon daily run + deploy to GitHub Pages
# Usage: ./scripts/daily-run.sh
# Cron:  0 8 * * * /path/to/horizon/scripts/daily-run.sh >> /path/to/horizon/logs/cron.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_PREFIX="[$(date '+%Y-%m-%d %H:%M:%S')]"

retry() {
    local attempt
    for attempt in 1 2 3; do
        if "$@"; then
            return 0
        fi
        if (( attempt < 3 )); then
            echo "$LOG_PREFIX Command failed (attempt $attempt/3); retrying in 15 seconds..." >&2
            sleep 15
        fi
    done
    return 1
}

cd "$PROJECT_DIR"

# Use the repo-scoped deploy key for both manual and systemd runs.
export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -i /root/.ssh/horizon_deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new}"

echo "$LOG_PREFIX Starting Horizon daily run (PUBLISH_ONLY=${PUBLISH_ONLY:-0})..."

if [ "${PUBLISH_ONLY:-0}" != "1" ]; then
    # 1. Discard server-generated lockfile changes, then update to the latest main
    retry git fetch --quiet origin main
    git restore --source=HEAD -- uv.lock
    git merge --ff-only origin/main

    # 2. Install/update dependencies using the committed lockfile
    uv sync --locked --quiet

    # 3. Run Horizon
    uv run --locked horizon --hours 24
fi

# 4. Deploy docs to gh-pages
echo "$LOG_PREFIX Deploying to gh-pages..."

# Use a temporary worktree to update gh-pages without switching branches
TMPDIR=$(mktemp -d)
cleanup() {
    cd "$PROJECT_DIR"
    git worktree remove --force "$TMPDIR" 2>/dev/null || rm -rf "$TMPDIR"
}
trap cleanup EXIT

git worktree prune
retry git fetch --quiet origin gh-pages

git worktree add --detach "$TMPDIR" origin/gh-pages
cp -r docs/* "$TMPDIR/"

cd "$TMPDIR"
git add -A
if git diff --cached --quiet; then
    echo "$LOG_PREFIX Nothing to commit."
    exit 0
fi
git commit -m "Daily Summary: $(date '+%Y-%m-%d')"
retry git push origin HEAD:gh-pages

echo "$LOG_PREFIX Done."
