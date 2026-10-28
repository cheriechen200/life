#!/usr/bin/env bash
# life-os 数据同步脚本
# 用法：./scripts/sync.sh "提交说明"
# 作用：把当天数据改动提交并推送到 GitHub。

set -euo pipefail

# 仓库根由 repo-root.sh 统一推导：不写死任何机器的绝对路径
source "$(dirname "${BASH_SOURCE[0]}")/repo-root.sh" >/dev/null
cd "$LIFE_OS_ROOT"

MSG="${1:-chore: daily sync $(date +%Y-%m-%d)}"

if [[ -z "$(git status --porcelain)" ]]; then
  echo "没有需要同步的改动。"
  exit 0
fi

git add -A
git commit -m "$MSG"
git push origin main

echo "已同步：$MSG"