# rubrics — 个人价值评价基因组（v0.3）

保存“谁在什么情境下，看到什么触发证据，出于什么，作出了怎样的价值评价”。目标是忠实表达评价，而不是把历史要求全部升级为永久指令。

- `DESIGN.md`：ontology、认识论、适用性和验证设计。
- `schema.json`：唯一的基因组 schema；`src/genome.py` 校验该 schema 使用的子集。
- `episodes/`：对话原始证据（本地私有）。
- `data/criteria.json`：基因组、原文引用、适用性与生命周期。
- `data/history/`：每次写入前的完整旧数据快照。
- `data/backups/pre-genome-v03/`：升级前源码与数据备份。
- `tests/`：合成边界回归；不是用户效果评测。

旧 89 条完整保留在 legacy，缺乏精确证据的字段不自动填充；少量真实 episode 的重建示范以新 draft 保存并指向前身。`seed/`、`system/2026-10-13-v0.md` 是历史产物，不是当前有效标准清单。

## 日常流程

从 rubrics 目录执行：

```sh
# 1. 本地准备：采集原文，按消息时间选最近三天，完整分批，不调用模型
python3 src/build.py --days 3
# 2. 可选：明确把准备好的对话交给配置的 DeepSeek 模型；会产生模型调用
python3 src/build.py --generate data/builds/<生成目录名>
# 或导入自己准备的符合 schema 的结果；导入后始终为 draft
python3 src/build.py --import-result /path/to/result.json
# 3. 检查原始证据和字段归纳；缺信息的可以一直保持 draft
python3 src/manage.py audit
# 4. 人工复核基因组后确认（这不等于允许跨情境应用）
python3 src/manage.py confirm --id r-2026-0090 --note '核对了原话和归纳，未知项保持未知'
# 5. applicability 也需单独复核：policy.json 按 schema 填写完整的 applicability 对象
python3 src/manage.py review-policy --id r-2026-0090 --policy-file policy.json --note '已核实必要条件和例外'
# 项目规范必须有 project 等值条件；未知、草稿、任务型条目不注入
python3 src/mount.py render '{"project":"research","task":"cookbook"}'
# 6. 明确过时的条目退休；历史仍可找回
python3 src/manage.py retire --id r-2026-0090 --note '需求已变更，旧范围不再成立'
```

`mounted` 是渲染接口开关，不能证明外部工作流已经调用该接口。已接入 CLI 全局指令、Research 项目指令、morning 摘要与 knowledge 的共享生成入口（含深读、问答、专题、cookbook、proposal）。反射层常驻文本与检索条目分离。

`build.py` 保留既有 DeepSeek profile 选择；本次升级没有实际调用模型，也没有重新抽取全部私人对话。若要自动化生成，需要显式选择模型外发路径。每日 observe 保留原始发言供构建，不再按评价关键词提前筛掉素材。

## 验证

```sh
python3 -B -m unittest discover -s tests -v
python3 src/evaluate.py --memory frozen-memory.json --cases heldout-cases.json --episodes frozen-episodes.json
```

`cases` 是 JSON 数组，每条含 id、cutoff、snapshot、expected_ids，可加 category。memory 与 episodes 均为冻结 JSON 数组。所有证据、创建和确认时间必须早于 cutoff；不能把回答后形成的记忆用于预测这次回答。

下一阶段必须收集独立用户评价，比较无记忆、人工偏好说明、基因组方案。没有用户效果数据前，不声称“已更懂用户”或“实现 RSI”。


## CLI / Obsidian 接入（2026-10-15）

- 全局 CLI 指令：~/.codex/AGENTS.md；新交互任务读取 bridge.py 的适用上下文。既有 TUI 会话可能需要重启才能重新加载指令。
- 项目指令：Research/AGENTS.md；Research/scripts/rubrics_bridge.py 隔离调用本模块，避免模块名冲突。
- 每日观察：复用已加载的 local.research.rubrics（03:00）；observe 保存 episode 后刷新 activity。morning 每日首次运行也刷新，不依赖外部源成功。
- Obsidian 页面：研究路线/近期关注、当前路线、审视记录、评价体系；首页有入口。
- 路线审视：Codex heartbeat research，每周一、四 09:30 Asia/Shanghai，在本聊天执行。只有新且可行动的发现才提醒。
- publish_review.py 只同步本功能页面，手写路线与反馈按共同版本合并；冲突不覆盖。sync_cloud 已对路线页使用此入口，并排除 rubrics 原始对话与运行数据的新同步。
- 通过本轮用户明确请求新增两条有来源的已确认标准；旧草稿没有批量确认。自动注入的 AGENTS 指令标识为 injected_context，不能用来证明用户的新价值评价。
- 挂载开关控制评价注入；关闭注入不会自动关闭每日采集或路线 heartbeat，二者独立。


## Hourglass workflow (2026-10-29)

The runtime source of truth is `配置/洞察标准/阶段卡.json`. Each call loads three common rules and one stage card. Detailed references and raw rubric genomes stay outside runtime prompts.

Stages: scope, scan, select, verify, synthesize, deliver. Inspect one stage using bridge.py with task=industry_insight and stage=verify; no stage returns navigation only.

All discovered candidates and intermediate artifacts are preserved under `.research/industry/runs/`. Deep-review budgets are not statistical sample sizes. Supplied --web-file evidence is not automatically fetched again.

The five previously proposed improvements are now approved and stage-scoped. Model calls increase from two to six to isolate tasks; total cost and report quality have not been benchmarked. Tests passed: 37. Standard context: 243-325 characters per stage versus 5513 previously, excluding other instructions, payloads and output schemas.


## 依赖图、版本与可见进度（2026-10-29）

业界洞察六阶段使用 `scripts/industry_graph.py` 保留不可变产物与真实依赖。支持失效、修正、撤销、历史恢复与增量续跑；未采用来源的正文改变不会让整份报告重做。当前按阶段构图，尚未细分为每条主张。

Git 管理实现、schema 与标准；私有运行材料不入公开代码仓库。每次模型阶段保存当时 Git 和文件哈希。`graph.json` 分开记录执行状态与产物有效性，保留事件、起止时间、耗时和错误类型。模型请求、阶段标准、输出及日志留在本地 attempts 目录。

Obsidian 今日简报顶部的「运行总览」展示真实运行记录；暂无运行时明确显示未运行，不把测试或旧报告冒充上线验收。图状态变更刷新本地页，activity 与 publish_review 也刷新；后者同步到 iCloud，保留手写内容。代码入口 `python3 -B scripts/industry_status.py`；局部操作见 `配置/洞察标准/依赖图与局部重做.md`。

CLI 是 AGENTS 指令约定调用桥接器；生成脚本是在调用前程序化注入阶段标准；Obsidian 是文件入口与展示。没有安装新的模型插件或外部编排器。已查官方文档比较 Prefect / Dagster / DVC，服务化时优先验证 Prefect；当前官方版需 Python 3.11+，本机默认 3.9，尚未安装。

本轮 58 项本地测试通过，覆盖失效传播、分支复用、恢复、失败保留、竞态提交、状态展示与同步保护。没有为本轮检查调用模型或生成新市场报告；真实六环节端到端效果仍待验收。
