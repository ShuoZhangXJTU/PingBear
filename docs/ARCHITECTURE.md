# 架构说明

## 一句话

把「多个信息源」变成「每天一份可归档、可提问、能长成知识体系的中文简报」，全流程本地运行。

```
来源            采集                理解                    产出
─────────────────────────────────────────────────────────────────────
HF Daily Papers ┐
小红书 tabris    │   scripts/*.py    Codex（只读）       日报/今日简报
官方博客 ×5      ├─→ 抓取/OCR/去重 ─→ 一句话简介        → 论文/<主题>/
我的链接（手工）  │                   深读 takeaways         → 专题/<主题>
微信转发         ┘                   逐条问答                → 问答/ 灵感/ 索引/
```

## 组件

| 模块 | 职责 | 关键点 |
|---|---|---|
| `research.py` | 底座：抓 HF、候选打分、发布日报、归档、标签索引 | `fetch_rows()` 直连/代理/镜像三路兜底 |
| `morning.py` | 每日调度：HF → 小红书 → 博客 → 我的链接 → 灵感 → 目录 → 知识体系 | 任一段失败不影响其他段；状态写 `morning-status.json` |
| `xhs.py` | 小红书：主页 → 新笔记 → 截图 OCR → 逐张认论文 → 卡片 | 一条笔记内的重复截图按标题骨架合并 |
| `blogs.py` | 官方博客：RSS 优先，SPA 用 Chrome 渲染 | 每源每日取最新 N 条，其余标记已见 |
| `inbox.py` | 我的链接：arXiv / 小红书（含短链）/ 任意网页 | 去重靠 `seen.json`，失败不标记以便重试 |
| `knowledge.py` | 深读 takeaways、主题体系页、逐条问答 | 提示词外置在 `配置/提示词-深读.md`；「我的备注」永不覆盖 |
| `library.py` | 归档问答：本地检索 + 带引用作答 | 检索范围含深读、问答沉淀、专题页 |
| `ideas.py` | 灵感速记：一句话 → 按主题归档 | 词表规则分类，纯本地 |
| `catalog.py` | 历史目录：按日期 + 按来源 | 每次早报后重建 |
| `organize.py` | 归档迁移：编号 → 论文真名 + 主题文件夹 | 一次性迁移工具，保留引用改写 |
| `backfill.py` | 冷启动补跑：HF 按天、博客按发布日 | 可中断续跑，进度在 `backfill.json` |
| `weixin_bridge.py` | 微信通道：问答、归档、hhh 记灵感、转发链接入队、日报分发 | 会话窗口限制 + 暂存补发 |
| `.obsidian/plugins/research-archive` | Obsidian 侧交互 | 三个按钮、悬浮目录、问答/灵感面板 |

## 数据流与状态

```
.research/
├── raw/<date>.json          HF 原始快照（含来源、抓取时间、用的直连/代理/镜像）
├── candidates/<date>.json   候选论文（含关键词命中的主题与打分）
├── digests/<date>.json      已发布的编号映射（归档靠它反查）
├── reviews/<date>.*.json    模型产出的中文 JSON
├── xhs/                     target.json(用户+token)、seen.json、digests、images、notes
├── blogs/                   seen.json、digests、cache
├── inbox/                   seen.json、digests、items.json
├── knowledge/               deepen/ topics/ ask/ answers/ cache/ logs/
├── ideas.json  backfill.json  morning-status.json
└── logs/
```

**归档 ID 规则**（插件与脚本共用）：

| 来源 | ID | 归档文件名 |
|---|---|---|
| 论文 | arXiv 编号 `2609.12345` | `论文/<主题>/<论文标题>.md` |
| 小红书 | `xhs-<笔记ID>` 或 `xhs-<笔记ID>-<序号>` | 同上（认出论文时用 arXiv 编号） |
| 我的链接（网页） | `link-<哈希>` | 同上 |
| 官方博客 | `blog-<哈希>`（含 arXiv 链接时用编号） | 同上 |

## 两档语言标准

- **日报/采集卡片**：面向快速筛选，写成**小学生也能看懂**的大白话，不用术语。
- **归档后的深读**：面向复用，**费曼式**——「做了什么 → 结果 → 说明什么」，专业词当场解释。

## 可扩展点

1. **加来源**：`blogs.py` 的 `SOURCES` 加一条（RSS 或列表页 + 渲染开关）；或新写一个采集脚本，产出与其他源一致的 digest 结构即可。
2. **改语言风格**：改 `配置/提示词-深读.md` 与各脚本里的 prompt 段。
3. **换模型**：所有模型调用都走 `~/.local/bin/codex exec`，换 provider 只改 Codex 配置。
4. **接新出口**：`weixin_bridge.py` 的 `push()` 是出口抽象，接邮件/iMessage 只需加一个函数。
