#!/bin/sh
# session_bootstrap.sh <project_dir>
# Idempotent environment self-check for long-running sandbox projects.
# Fixes: (1) root/uid-999 write-permission conflicts, (2) missing pytest
# after sandbox reset, (3) missing/invalid .git after sandbox reset,
# including git "dubious ownership" (safe.directory) failures.
set -u

DIR="${1:-}"
if [ -z "$DIR" ] || [ ! -d "$DIR" ]; then
    echo "usage: $0 <existing project directory>" >&2
    exit 2
fi

# 1. Permissions: shell runs as root, ipython runs as uid 999 (kimi).
#    Make the whole tree writable by uid 999 so both tools can write.
if [ "$(id -u)" = "0" ]; then
    chown -R 999:999 "$DIR" 2>/dev/null && echo "[bootstrap] chown -R 999:999 $DIR ok"
else
    echo "[bootstrap] not root; skipping chown"
fi

# 2. pytest (lost on sandbox reset)
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "[bootstrap] pytest missing -> installing"
    pip install -q pytest 2>&1 | tail -1
else
    echo "[bootstrap] pytest present: $(python3 -c 'import pytest; print(pytest.__version__)')"
fi

# 3. git repo: root operating on a uid-999-owned tree triggers
#    "detected dubious ownership" / "fatal: not in a git directory".
#    Whitelist the path first, then (re)init, then VERIFY.
git config --global --add safe.directory "$DIR" 2>/dev/null
if ! git -C "$DIR" rev-parse --git-dir >/dev/null 2>&1; then
    echo "[bootstrap] .git missing/invalid -> re-init"
    git -C "$DIR" init 2>&1 | tail -1
    git -C "$DIR" config user.name "sandbox-project"
    git -C "$DIR" config user.email "local@sandbox"
    echo "[bootstrap] NOTE: re-create pre-commit hooks per project docs if any"
else
    echo "[bootstrap] .git present"
fi
# Hard verification: never trust `git init -q && ...` chains blindly.
if git -C "$DIR" rev-parse --git-dir >/dev/null 2>&1; then
    echo "[bootstrap] git repo verified: $(git -C "$DIR" rev-parse --git-dir)"
else
    echo "[bootstrap] ERROR: git repo still invalid after init" >&2
    exit 1
fi

echo "[bootstrap] done"
