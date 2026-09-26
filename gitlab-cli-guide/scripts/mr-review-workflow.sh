#!/bin/bash
# MR 评审工作流脚本
# 自动执行：检出 MR → 运行测试 → 将结果发布为评论 → 若通过则批准

set -e

MR_ID="$1"
TEST_COMMAND="${2:-npm test}"

if [ -z "$MR_ID" ]; then
    echo "Usage: $0 <MR_ID> [test_command]"
    echo "Example: $0 123"
    echo "Example: $0 123 'pnpm test'"
    exit 1
fi

# 验证 MR_ID 是否为数值，以防止注入。
if ! [[ "$MR_ID" =~ ^[0-9]+$ ]]; then
    echo "❌ Error: MR_ID must be a numeric value (got: $MR_ID)" >&2
    exit 1
fi

# 对照白名单校验 TEST_COMMAND，以防止任意代码执行。
# 此处有意不使用 eval——详见 SECURITY.md 了解原因。
ALLOWED_COMMANDS=("npm test" "pnpm test" "yarn test" "make test" "cargo test" "go test ./..." "bundle exec rspec" "pytest" "mvn test" "gradle test")
COMMAND_ALLOWED=false
for allowed in "${ALLOWED_COMMANDS[@]}"; do
    if [[ "$TEST_COMMAND" == "$allowed" ]]; then
        COMMAND_ALLOWED=true
        break
    fi
done

if [ "$COMMAND_ALLOWED" = false ]; then
    echo "❌ Error: Test command not in allowlist: '$TEST_COMMAND'" >&2
    echo "" >&2
    echo "Allowed commands:" >&2
    for cmd in "${ALLOWED_COMMANDS[@]}"; do
        echo "  - $cmd" >&2
    done
    echo "" >&2
    echo "To add a new command, update the ALLOWED_COMMANDS array in this script." >&2
    exit 1
fi

echo "🔄 Checking out MR !$MR_ID..."
glab mr checkout "$MR_ID"

echo "🧪 Running tests: $TEST_COMMAND"
if $TEST_COMMAND; then
    echo "✅ Tests passed!"

    echo "📝 Adding approval comment..."
    glab mr note "$MR_ID" -m "✅ Tests passed locally - approving"

    echo "👍 Approving MR..."
    glab mr approve "$MR_ID"

    echo "✨ Review complete - MR approved"
else
    echo "❌ Tests failed!"

    echo "📝 Adding failure comment..."
    glab mr note "$MR_ID" -m "❌ Tests failed locally - please review

Test command: \`$TEST_COMMAND\`

See output above for details."

    echo "⚠️  Review complete - MR not approved due to test failures"
    exit 1
fi
