#!/bin/bash
# 同步 Fork 脚本
# 自动执行：fetch upstream → merge into current branch → push to origin

set -e

BRANCH="${1:-main}"
UPSTREAM_REMOTE="${2:-upstream}"

echo "🔄 Syncing fork with upstream..."
echo "  Branch: $BRANCH"
echo "  Upstream remote: $UPSTREAM_REMOTE"
echo ""

# 检查上游远程仓库是否存在
if ! git remote get-url "$UPSTREAM_REMOTE" >/dev/null 2>&1; then
    echo "❌ Upstream remote '$UPSTREAM_REMOTE' not found"
    echo ""
    echo "Add upstream remote first:"
    echo "  git remote add upstream <upstream-repo-url>"
    echo ""
    echo "Example:"
    echo "  git remote add upstream https://gitlab.com/group/project.git"
    exit 1
fi

UPSTREAM_URL=$(git remote get-url "$UPSTREAM_REMOTE")
echo "Upstream: $UPSTREAM_URL"
echo ""

# 保存当前分支
CURRENT_BRANCH=$(git branch --show-current)

# 检出目标分支
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
    echo "📍 Switching to $BRANCH..."
    git checkout "$BRANCH"
fi

# 获取上游
echo "⬇️  Fetching from upstream..."
git fetch "$UPSTREAM_REMOTE"

# 合并上游更改
echo "🔀 Merging upstream/$BRANCH into $BRANCH..."
if git merge "$UPSTREAM_REMOTE/$BRANCH" --ff-only; then
    echo "✅ Fast-forward merge successful"
else
    echo "⚠️  Fast-forward merge failed - attempting regular merge..."
    
    if git merge "$UPSTREAM_REMOTE/$BRANCH"; then
        echo "✅ Merge successful (with merge commit)"
    else
        echo "❌ Merge failed - conflicts detected"
        echo ""
        echo "Resolve conflicts manually, then:"
        echo "  git add ."
        echo "  git commit"
        echo "  git push origin $BRANCH"
        exit 1
    fi
fi

# 推送到 origin
echo "⬆️  Pushing to origin/$BRANCH..."
git push origin "$BRANCH"

echo ""
echo "✨ Fork synced successfully!"
echo ""

# 如果不同则返回原始分支
if [ "$CURRENT_BRANCH" != "$BRANCH" ] && [ -n "$CURRENT_BRANCH" ]; then
    echo "📍 Returning to $CURRENT_BRANCH..."
    git checkout "$CURRENT_BRANCH"
fi

echo "Summary:"
echo "  ✅ Fetched from $UPSTREAM_REMOTE"
echo "  ✅ Merged upstream/$BRANCH into local $BRANCH"
echo "  ✅ Pushed to origin/$BRANCH"
