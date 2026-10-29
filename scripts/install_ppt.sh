#!/bin/bash
# Install the PPT-only brainstorm skill and ppt-master runtime.
set -euo pipefail

VAULT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
SKILL_INSTALLER="$SKILLS_DIR/.system/skill-installer/scripts/install-skill-from-github.py"
PPT_VENV="$HOME/.local/share/ppt-master/venv"

say() { printf '\033[1m%s\033[0m\n' "$*"; }
die() { printf '\033[31m%s\033[0m\n' "$*" >&2; exit 1; }

find_python() {
  local candidate
  for candidate in \
    "$(command -v python3.13 2>/dev/null || true)" \
    "$(command -v python3.12 2>/dev/null || true)" \
    /usr/local/bin/python3.12 \
    /opt/homebrew/bin/python3.12; do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

say "1/5 检查 Python 3.12+"
PYTHON="$(find_python || true)"
if [ -z "$PYTHON" ]; then
  command -v brew >/dev/null 2>&1 || die "缺少 Python 3.12+，也找不到 Homebrew"
  say "安装 Python 3.12（Intel Mac 可能需要源码编译）"
  brew install python@3.12
  PYTHON="$(find_python || true)"
fi
[ -n "$PYTHON" ] || die "Python 3.12+ 安装后仍找不到"
echo "   → $PYTHON"

say "2/5 安装 skills"
mkdir -p "$SKILLS_DIR"
if [ ! -f "$SKILLS_DIR/ppt-master/SKILL.md" ]; then
  [ -f "$SKILL_INSTALLER" ] || die "缺少 Codex skill-installer：$SKILL_INSTALLER"
  python3 "$SKILL_INSTALLER" \
    --repo hugohe3/ppt-master \
    --path skills/ppt-master \
    --method download
fi
mkdir -p "$SKILLS_DIR/brainstorm"
cp "$VAULT/skills/brainstorm/SKILL.md" "$SKILLS_DIR/brainstorm/SKILL.md"
echo "   → brainstorm（仅 PPT）"
echo "   → ppt-master"

say "3/5 创建隔离环境"
if [ ! -x "$PPT_VENV/bin/python" ]; then
  "$PYTHON" -m venv "$PPT_VENV"
fi
"$PPT_VENV/bin/python" -m pip install --upgrade pip

say "4/5 安装 PPT 依赖"
"$PPT_VENV/bin/python" -m pip install \
  -r "$VAULT/配置/ppt-master-requirements.txt"

say "5/5 自检"
"$PPT_VENV/bin/python" "$SKILLS_DIR/ppt-master/scripts/attribution_guard.py"
"$PPT_VENV/bin/python" "$SKILLS_DIR/ppt-master/scripts/svg_to_pptx.py" --help >/dev/null
echo "   ✅ ppt-master 可运行"

cat <<EOF

PPT 工作流安装完成。
解释器：$PPT_VENV/bin/python
流程：brainstorm 先确认逐页提纲，再由 ppt-master 生成可编辑 PPTX。
EOF
