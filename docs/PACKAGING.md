# 拆包方案（走向产品）

目标：把「能跑的一套脚本」拆成**可安装、可复用、边界清晰**的两块——核心库 + Obsidian 前端。

## 目标形态

```
research-inbox/                    ← 独立仓库（可开源）
├── pyproject.toml                 包配置与 CLI 入口
├── src/research_inbox/
│   ├── config.py                  路径、时区、标签词表、提示词加载
│   ├── net.py                     直连/代理/镜像三段式抓取
│   ├── sources/
│   │   ├── hf.py                  HF Daily Papers
│   │   ├── xiaohongshu.py         主页解析 + 截图 OCR + 逐张认论文
│   │   ├── blogs.py               RSS / 列表页 / SPA 渲染
│   │   └── inbox.py               手工链接（arXiv / 短链 / 任意网页）
│   ├── summarize.py               两档语言标准 + 批处理 + JSON 校验
│   ├── ocr.py                     封装 macOS Vision（scripts/ocr.swift）
│   ├── archive.py                 归档（主题文件夹 + 论文名 + entry_id）
│   ├── knowledge/
│   │   ├── deepen.py              takeaway 提示词引擎
│   │   ├── topics.py              专题体系重建
│   │   ├── library.py             归档检索 + 带引用问答
│   │   └── ideas.py               灵感分类
│   ├── render.py                  日报/首页/目录/标签索引渲染
│   └── cli.py                     `research-inbox morning|backfill|ask|idea|inbox …`
├── prompts/deep-read.md           提示词（与仓库里的同名文件保持一致）
├── docs/ARCHITECTURE.md
└── tests/                         至少覆盖：去重、编号稳定、归档路径、渲染快照

research-archive-ob/               ← Obsidian 插件独立仓库（可上架社区插件）
```

## 迁移映射

| 现在 | 将来 |
|---|---|
| `scripts/research.py` | `core` + `sources/hf.py` + `archive.py` + `render.py` |
| `scripts/morning.py` | `cli.py:morning`（调度） |
| `scripts/xhs.py` | `sources/xiaohongshu.py` |
| `scripts/blogs.py` | `sources/blogs.py` |
| `scripts/inbox.py` | `sources/inbox.py` |
| `scripts/knowledge.py` | `knowledge/deepen.py` + `knowledge/topics.py` |
| `scripts/library.py` | `knowledge/library.py` |
| `scripts/ideas.py` | `knowledge/ideas.py` |
| `scripts/catalog.py` `organize.py` `backfill.py` | `render.py` 与 `cli.py` 的子命令 |
| `scripts/ocr.swift` | `ocr.py` 里调用的本机二进制（首次运行自动编译到 `~/.local/bin/ocr`） |
| `.obsidian/plugins/research-archive` | 拆成独立插件仓库，去掉对具体 vault 路径的硬编码 |

## 拆包要解决的三个耦合

1. **路径耦合**：脚本现在用 `Path(__file__).parents[1]` 认定 vault；改成 `config.py` 从环境变量/参数读取 root。
2. **Codex 耦合**：所有模型调用都拼 `codex exec` 命令行；抽成 `summarize.py` 的一个函数，未来可换 API。
3. **私有数据耦合**：`.research/` 与个人目录天然隔离，拆包时用 `--root` 指向任意目录即可（`research.py` 已支持 `--root`）。

## 建议顺序

1. 加测试与 `--root` 打通（保证拆完行为不变）；
2. 抽 `net.py` / `summarize.py` / `archive.py` 三个无状态模块；
3. 再搬 sources 与 knowledge；
4. 最后拆 Obsidian 插件，并把 README/INSTALL 写成面向外部用户。

## 产品化要点（先记下来）

- **首次体验**：一条命令装完 → 打开 Obsidian 就能看到当天简报；扫码只在需要小红书/微信时才要求。
- **失败可见**：每个来源独立状态，早报里明确写「某段本次未更新」，不静默失败。
- **成本可见**：每次模型调用次数与来源都写日志，用户在设置里能看到当天花了多少次。
- **隐私默认**：所有数据留在本地；登录态文件永不进仓库（`.gitignore` 已覆盖）。
