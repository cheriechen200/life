#!/usr/bin/env bash
# life-os 仓库根目录定位（环境无关）
#
# 设计原则
#   仓库内所有路径一律相对「仓库根」书写，不绑定任何机器的绝对路径。
#   仓库根 = 同时包含 domains/ 与 skills/ 的那一层（automations/ 的上级）。
#   需要绝对路径时（脚本里 cd、定时任务拼路径），用本脚本推导，而不是写死。
#
# 用法（推荐直接执行，跨 shell 最稳）
#   cd "$(scripts/repo-root.sh)"
#   cd "$(bash scripts/repo-root.sh)"
# 用法（bash 内复用变量）
#   source scripts/repo-root.sh && cd "$LIFE_OS_ROOT"
#
# 推导顺序
#   1. 以本脚本自身位置为基准上溯一级 —— 任何机器、任何克隆路径都成立
#   2. 若取不到（如被非 bash 的 shell source），从当前工作目录逐级向上查找仓库根
#   3. 校验命中目录确实含 domains/ 与 skills/，避免静默跑错目录

set -euo pipefail

_is_root() {
  [[ -d "${1}/domains" && -d "${1}/skills" ]]
}

LIFE_OS_ROOT=""

# 1) 基于脚本自身位置推导
_LIFE_OS_SELF="${BASH_SOURCE[0]:-$0}"
if [[ -n "${_LIFE_OS_SELF}" && -f "${_LIFE_OS_SELF}" ]]; then
  _candidate="$(cd "$(dirname "${_LIFE_OS_SELF}")" && pwd)"
  _candidate="$(cd "${_candidate}/.." && pwd)"
  if _is_root "${_candidate}"; then
    LIFE_OS_ROOT="${_candidate}"
  fi
fi

# 2) 回退：从当前工作目录逐级向上查找（最多 5 层）
if [[ -z "${LIFE_OS_ROOT}" ]]; then
  _candidate="$(pwd)"
  for _ in 1 2 3 4 5; do
    if _is_root "${_candidate}"; then
      LIFE_OS_ROOT="${_candidate}"
      break
    fi
    _parent="$(dirname "${_candidate}")"
    [[ "${_parent}" == "${_candidate}" ]] && break
    _candidate="${_parent}"
  done
fi

# 3) 校验
if [[ -z "${LIFE_OS_ROOT}" ]]; then
  echo "错误：未定位到 life-os 仓库根（当前目录及其上级 5 层内均无 domains/ 与 skills/）：$(pwd)" >&2
  exit 1
fi

export LIFE_OS_ROOT
echo "${LIFE_OS_ROOT}"
