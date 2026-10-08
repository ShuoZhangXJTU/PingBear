#!/bin/bash
# 科研早报 / research-inbox 一键安装（macOS）
set -euo pipefail

VAULT="$(cd "$(dirname "$0")" && pwd)"
DRY_RUN=""
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1
say() { printf '\033[1m%s\033[0m\n' "$*"; }
warn() { printf '\033[33m%s\033[0m\n' "$*"; }

say "1/6 检查依赖"
PYTHON="$(command -v python3 || true)"
[ -n "$PYTHON" ] || { warn "缺少 python3，请先安装（macOS 自带即可）"; exit 1; }
CODEX="${HOME}/.local/bin/codex"
[ -x "$CODEX" ] || warn "未找到 Codex CLI（$CODEX）——中文简介/深读/问答会不可用；安装后重新运行本脚本"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
[ -x "$CHROME" ] || warn "未找到 Google Chrome——小红书与部分博客源会不可用"
echo "   vault : $VAULT"
echo "   python: $PYTHON"
echo "   codex : $([ -x "$CODEX" ] && echo ok || echo missing)"
echo "   chrome: $([ -x "$CHROME" ] && echo ok || echo missing)"

say "2/6 初始化目录"
mkdir -p "$VAULT/.research/logs" "$VAULT/.research/requests" "$VAULT/.research/responses"
mkdir -p "$VAULT/日报" "$VAULT/论文" "$VAULT/专题" "$VAULT/问答" "$VAULT/灵感" "$VAULT/索引" "$VAULT/收件箱" "$VAULT/最佳实践"
[ -n "$DRY_RUN" ] || python3 "$VAULT/scripts/ideas.py" add --text "安装完成：这是灵感速记的第一条测试" >/dev/null 2>&1 || true

say "3/6 安装 Obsidian 插件"
PLUGIN_DIR="$VAULT/.obsidian/plugins/research-archive"
mkdir -p "$PLUGIN_DIR" "$VAULT/.obsidian"
cp "$VAULT/.obsidian/plugins/research-archive/"*.js "$PLUGIN_DIR/" 2>/dev/null || true
cp "$VAULT/.obsidian/plugins/research-archive/"*.json "$PLUGIN_DIR/" 2>/dev/null || true
cp "$VAULT/.obsidian/plugins/research-archive/"*.css "$PLUGIN_DIR/" 2>/dev/null || true
echo '["research-archive"]' > "$VAULT/.obsidian/community-plugins.json"
[ -f "$VAULT/.obsidian/app.json" ] || echo '{"attachmentFolderPath": "附件", "defaultViewMode": "preview"}' > "$VAULT/.obsidian/app.json"
echo "   → 打开 Obsidian 选这个文件夹作为仓库；到「设置 → 第三方插件」关闭受限模式并勾选「科研论文归档」"

say "4/6 编译本机 OCR（macOS Vision，小红书截图用）"
if command -v swiftc >/dev/null 2>&1; then
  mkdir -p "$HOME/.local/bin"
  [ -n "$DRY_RUN" ] || swiftc -O "$VAULT/scripts/ocr.swift" -o "$HOME/.local/bin/ocr" 2>/dev/null || warn "OCR 编译失败（可选功能）"
  echo "   → $HOME/.local/bin/ocr"
else
  warn "未找到 swiftc（需要 Xcode Command Line Tools）：xcode-select --install"
fi

say "5/6 安装定时任务（launchd）"
AGENTS="$HOME/Library/LaunchAgents"
mkdir -p "$AGENTS"
BIN_PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
install_plist() {
  local name="$1" template="$VAULT/templates/$1.plist.tmpl"
  [ -f "$template" ] || return 0
  local target="$AGENTS/$1.plist"
  [ -f "$target" ] && cp "$target" "$target.bak-$(date +%s)"
  sed -e "s|__VAULT__|$VAULT|g" -e "s|__PYTHON__|$PYTHON|g" -e "s|__BIN_PATH__|$BIN_PATH|g" \
      "$template" > "$target"
  if [ -z "$DRY_RUN" ]; then
    launchctl bootout "gui/$(id -u)/$name" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$target" && echo "   ✅ $name"
  else
    echo "   (dry-run) 会安装 $name"
  fi
}
install_plist local.research.morning
install_plist local.research.cookbook

say "6/6 自检"
if [ -z "$DRY_RUN" ]; then
  (cd "$VAULT" && python3 scripts/catalog.py >/dev/null && echo "   ✅ 目录生成正常")
  (cd "$VAULT" && python3 -m unittest discover -s tests >/dev/null 2>&1 && echo "   ✅ 单元测试通过")
fi

cat <<EOF

安装完成 🎉

接下来：
  1) 打开 Obsidian → 打开文件夹作为仓库 → 选 $VAULT
  2) 命令面板搜「读取我的链接」/「重建标签索引」/「归档问答」体验功能
  3) 想接小红书：见 配置/小红书.md（需要扫码一次）
  4) 想接微信：见 配置/微信接入.md（需要扫码绑定，且该接口有会话窗口限制）

每天 8:30 自动生成早报（launchd：local.research.morning），00:30 更新最佳实践手册。
EOF
