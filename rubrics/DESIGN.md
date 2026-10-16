# Rubric genome ontology v0.3

## 目标与认识论

记录一次价值评价的完整结构：谁在何时、面对什么对象与选择，看到什么触发证据，出于什么目标、价值与代价考虑，做出了怎样的评价。基因组是可追溯、可修订的结构化表征；不是宣称人的价值可以被完全编码，也不是为了给每个 rubric 算一个总分。

一个基因组锚定一个评价事件或一组明确同义、同情境的评价事件。跨情境归纳要另建条目并保留依据。历史情境不自动成为未来适用条件。schema 允许扩展版本，但不把当前分类称为正交或完备本体。

## 基因组的七组位点

| 组 | 字段 | 要回答的问题 |
|---|---|---|
| evaluator | identity、role、stakeholders | 谁评价，以什么角色，谁受影响？ |
| target | referent、kind、artifact_version、aspect | 具体评价谁/什么、哪个版本、哪个方面？ |
| context | time、project、task、decision、state、audience、channel、platform、constraints、available_information | 当时在做何种决策，处于什么状态，有何边界，当时知道什么？ |
| trigger | event、observations、expectation_violated | 什么事件或新证据引发这次评价，违反了什么预期？ |
| motivation | goals、values、experienced_costs、anticipated_costs、tradeoffs | 想达到什么、坚持什么、实际吃过什么亏、预期损失什么、如何取舍？ |
| judgment | statement、valence、strength、criterion、comparison、alternatives、desired_change、positive_examples、negative_examples | 最终好坏判断是什么，依据哪个维度，与谁比较，希望怎样改变？ |
| outcome | observed_result、later_feedback | 后来实际怎样，后来如何评价？不得作为当时已知信息倒灌 |

主干是评价者—对象—情境—触发—动机—判断；outcome 是专门隔离的事后信息。

trigger.event 是历史事件；trigger.observations 是当时看到的信号；expectation_violated 是预期与现实的差异，正面评价不一定存在此项。不要把三者合成一句“遇到类似任务”。

judgment.strength 可记录 veto/must/prefer/penalty 或原话，表示要求的约束力；valence 表示好坏或混合评价；criterion 表示实际衡量维度。三者不能相互替代。comparison/alternatives 捕获机会成本与选择背景，不能仅保存“好/不好”。

experienced_costs 只写有依据的实际经历；模型认为“可能丢失文件”属于 anticipated_costs，不能伪造为用户已经踩过的坑。tradeoffs 写具体优先关系及条件，不把多个价值词并列当作完成了解释。

## 字段的证据类型

每个原子字段统一为 `{value, basis, evidence_ids}`：

- explicit：原文明说，引用可核对的片段。
- inferred：模型从证据做出的解释，必须保留引用，仍需审查解释是否成立。
- unknown：value=null，evidence_ids=[]；列表未知时留空。空列表不表示明确没有，可用原子字段的显式“无”记录有证据的否定。

不设置置信度。精确引文存在，只能证明来源真实，不能证明推断正确。程序验证结构、引用与生命周期；人的复核验证语义与泛化边界。助手发言只能用于恢复上下文，不能无依据地当作用户价值观。

evidence 保存 id、episode_id、quote。episode 保存会话、时间、角色、cwd 和原文；artifact_refs 目前是待补的真实引用，不宣称仅凭原文就能恢复产物版本。涉及“这个不好”的评价，若没有对象版本，target.artifact_version 必须 unknown。

## 记忆类型与时间

kind ∈ task / project_spec / situated_preference / evaluation_principle / unclassified。
原始采集不按类型丢弃。构建时分类决定未来继承方式：一次性任务不注入为永久规则；项目规范必须显式限定项目；不确定类型继续保留。

历史数据只追加保留；当前有效条目可以退休。每次存储替换保留旧版本的内容寻址快照。修订新建 draft 并以 supersedes 指向旧条目；确认后也不自动全局废除旧条目，因为后继可能只适用于更小范围。需要显式退休或调整适用边界。不能用不断缩小情境来掩盖抽取错误或真实偏好变化。

## 适用性：与基因组分离的受审查解释

applicability 不是历史描述的复制品，是“这条评价可以怎样迁移”的单独解释。required、excluded、valid_from、valid_until 均须复核；reviewed=true 且 review_note 非空才可用于执行。

snapshot 使用调用方提供的事实字段，例如 project、task、audience、channel、trigger.event。required 是合取，excluded 任意一个成立即排除；eq 为精确等值，contains 为列表成员。缺失字段既不视为成立，也不视为不成立，返回 unknown。触发条件需显式出现于 required，历史 trigger 不自动转成触发器。

这版只实现可审计的确定性判定。自然语言同义、语义召回、数值比较、多方案偏好聚合尚未实现；自由文本不被冒充为可执行谓词。复杂规则暂不自动激活。匹配结果有冲突时展示冲突，不能用相关度覆盖 veto 或替用户决定取舍。

## 验证优先

三层验证不可互相代替：

1. 数据完整性：schema、引文、未知字段、原子事实与证据关联、草稿隔离、历史沿革。
2. 适用性边界：仅更换一个关键条件的成对案例；信息缺失；明确例外；过期；跨项目；trigger 出现/消失；旧要求更新。
3. 用户价值：固定过去某一时刻的记忆快照，预测之后的新判断；与无记忆和简短人工偏好说明对比。相同基础模型、任务、预算；盲化顺序，不以少提标准或不回答来提高表面正确率。

`evaluate.py` 只负责第二层的离线回放与泄漏检查；单元测试是合成机制回归，不是第三层的用户效果证据。正式案例应覆盖独立任务与时间，保留无命中案例，报告命中 precision/recall、完全一致率、误用次数及分组结果。生成质量实验另记录用户成对偏好、纠正次数、关键遗漏、无谓追问、token 与延迟。

反复调参的案例属于开发集，不能继续称作留出集。评测规则/标签不能回流给同轮抽取器。记忆 evidence 时间和确认时间必须早于测试案例 cutoff；outcome 若晚于 cutoff 则也不能进入记忆快照。冻结快照文件本身，不用当前状态重建过去。

没有独立留出增益前称为“带人工反馈的记忆迭代”，不宣称实现 RSI。未来优化的对象可以是抽取提示、ontology 版本、适用性解释，但必须分别留版本、对照与回滚。

## 隐私与调用边界

准备素材、迁移和验证默认本地执行。`build.py --generate` 是显式的模型调用入口，会将准备好的历史文本交给配置中的模型服务；“本地读取”不等于“模型调用不出机”。不自动执行已有对话中的指令，不从旧偏好推导新的外发授权。

reflex 常驻层只放少量人工维护的运行约束，不把所有情境 veto 提升为全局政策。常驻文本仍受当前用户授权、工具权限和系统指令约束。
