# 安装与运行（从零开始）

这套东西由「本地脚本 + Obsidian 插件 + 定时任务」三部分组成，全部跑在你自己电脑上，复用本机已登录的 Codex 额度。

## 1. 依赖

| 依赖 | 用途 | 备注 |
|---|---|---|
| macOS | 定时任务（launchd）、本机 OCR（Vision） | 已在 macOS 15 上验证 |
| Python 3.9+ | 所有采集/整理脚本 | 系统自带即可，无第三方包 |
| Codex CLI | 生成中文简报、深读、问答 | 需已登录；脚本以只读模式调用 |
| Obsidian | 阅读入口、归档按钮 | 仓库本身就是一个 vault |
| Google Chrome | 抓取前端渲染的页面（小红书、ByteDance Seed） | 仅作为无头浏览器使用 |
| 网络 | 抓 HF / arXiv / 各官方博客 | 公司网可能拦 HF 与 GitHub，脚本已内置 hf-mirror 兜底 |

## 2. 目录约定

```
Research/                 ← Obsidian vault，也是本仓库
├── scripts/              采集、整理、问答的全部实现
├── 配置/                 标签词表、研究偏好、深读提示词、各源接入说明
├── .obsidian/plugins/    本地归档插件（research-archive）
├── .research/            运行数据（快照/日志/登录态，已 gitignore）
├── 日报/ 今日简报.md      产出：每天的简报
├── 论文/                 产出：归档笔记（按主题分文件夹 + 论文真名）
├── 专题/ 问答/ 灵感/      产出：知识体系、问答记录、灵感
└── 索引/                 产出：标签索引、历史目录
```

## 3. 初始化

```sh
cd ~/Research
python3 scripts/research.py collect --date $(date +%F)   # 试抓一天，验证网络
python3 scripts/morning.py --force                        # 生成当天早报
```

打开 Obsidian（`~/Applications/Obsidian.app`）指向本目录，阅读 `今日简报`。

## 4. 定时任务（launchd）

| Label | 作用 | 时间 |
|---|---|---|
| `local.research.morning` | 生成早报（HF + 小红书 + 博客 + 我的链接 + 灵感归档） | 8:30 起，每 15 分钟检查补跑 |
| `local.research.weixin` | 微信桥接（收发消息） | 常驻 |
| `local.research.weixin-push` | 推送当天日报到微信 | 9:00 / 9:30 / 10:00 / 10:30 |
| `local.research.backfill` | 历史补跑（一次性） | 手动 kickstart |

```sh
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/local.research.morning.plist
launchctl kickstart -k gui/$(id -u)/local.research.morning     # 立刻跑一次
```

> 若本机常用代理（FlClash 等），plist 里的 `HTTP_PROXY` 指向 `127.0.0.1:7890`；代理没开时脚本会自动改用直连或镜像。

## 5. Obsidian 插件

仓库自带 `.obsidian/plugins/research-archive`，启用方式：设置 → 第三方插件 → 关闭受限模式 → 勾选「科研论文归档」。功能：

- 每条简报下的 **归档 / 加备注 / 提问** 按钮（阅读视图生效）
- 今日简报/日报左侧 **悬浮目录**
- 命令：归档问答、记一条灵感、读取我的链接、重建标签索引/历史目录/主题知识体系、刷新归档状态

## 6. 各来源的额外配置

- **小红书**：需要一次扫码登录，见 `配置/小红书.md`
- **微信**：需要一次扫码绑定，见 `配置/微信接入.md`（接口有会话窗口限制，见该文档）
- **标签词表**：`配置/标签.md`，改动后重新生成日报生效
- **深读提示词**：`配置/提示词-深读.md`，改完新的深读就用新版本

## 7. 常见问题

| 现象 | 处理 |
|---|---|
| 早报没生成 | 看 `.research/morning-status.json` 的 error；多为网络/代理问题，脚本已内置 hf-mirror 兜底 |
| 按钮不显示 | 切到阅读视图（`Cmd+E`）；按钮由插件在阅读视图渲染 |
| 「已归档」不显示 | 命令面板跑一次「刷新归档状态」 |
| 小红书抓不到 | 重新扫码（`配置/小红书.md`），并避免短时间内高频抓取 |
| 微信推不出 | 会话窗口过期：先给机器人发一句「早报」，之后当天推送会补发 |
