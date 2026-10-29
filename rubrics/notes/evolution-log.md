# 演进日志

## v0.1（seed，2026-10-13）

- 定稿三层 taxonomy：评价本体（强度/判据形态/正反例）、情境五轴、动机四元。
- 核心匹配可用：`core.py` 提供 add / match / scoped_update，独立无依赖。
- 种子条目 3 条：结论冲突（veto）、费曼式表达（must）、成本与排期（prefer）。

## 待办（下一轮）

- `evolve.py`：观察 → 提出 → 验证 → 沉淀的循环骨架（当前只有设计，代码未写）。
- 把「归档/收藏/备注/灵感」作为第一个 observe 来源接进来（只读外部文件，不 import 外部代码）。
- 为 match() 加"匹配不上 → 返回空并提示问询"的显式分支。
- taxonomy 本身的第一轮回看：跑几轮后检查五根轴取值是否要收窄。

## v0.3（2026-10-15，genome ontology）

- 用户明确目标：为每个 rubric 建立充分表达当时情境、trigger、动机与价值评价的基因组。
- 替换五轴平面标准为七组证据标注位点；历史描述与未来适用性分离，不设置信度。
- 严格 schema + 精确引文校验；explicit/inferred/unknown；动机区分真实代价和预期代价。
- 修复 scoped_update 丢新条目；事务锁、原子替换、旧版本快照；草稿与退休条目不注入。
- 89 条旧数据保留为 legacy；从真实 episode 重建 3 条后继 draft，不自动确认。
- 构建以 episode 为来源，按消息时间选择、无静默截断；默认只本地准备，保留显式 DeepSeek 生成入口。
- 新增离线边界评测与时间泄漏拒绝，用户效果实验仍待收集独立数据。
- 上方 v0.1 待办属于历史；当前进度以 v0.3 README 和 DESIGN 为准。


## v0.3 integration（2026-10-15）

- 接入 CLI 全局 AGENTS 和 Research 项目上下文；研究批处理在发起模型调用前实际注入适用评价。
- 每日关注证据与 Obsidian 页面已生成，初次读取 277 条行动/归档证据，其中近14天主动灵感10条、问题2条（不包含自动日报）。
- 每周一、四09:30路线审视 heartbeat 已激活（id: research），首条审视已落盘。
- 本地与 iCloud 路线页已同步，保护手写内容；旧的全量镜像不再覆盖路线页，也不新增同步 rubrics 原始对话。
- 29 项测试通过；已实际执行 CLI/Research 桥接、observe 采集与关注刷新及定向同步。未为测试触发全量日报或外部生成。


## 洞察标准第一轮（2026-10-28）

- 保存用户完整原话，9条忠实归纳确认；其中机构来源偏好只记录，未来适用性未自动复核。
- 5条助手补强维持draft，明确区分用户判断与专家新增建议。
- 形成配置/洞察标准.md，业界洞察规划和分析读取用户明确标准；历史竞品档案保留，后续输出先呈现关系与体验变化。
- industry任务映射已接入rubrics；7条洞察专用规则不会泄漏到daily_brief。
- 33项测试通过，已验证原话引用与存储结构；本轮未重新生成市场报告、未提交或推送Git。


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
