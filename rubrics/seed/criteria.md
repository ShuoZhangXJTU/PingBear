# 种子条目（人工确认）

## 关于结论冲突

```yaml
id: r-2026-0001
judgment:
  text: 新论文推翻旧结论时，必须写清双方各自成立的条件，不许把冲突抹平
  strength: veto
  mode: mechanical
  negative_examples: ["把两边罗列了事", "写成『现有方法各有利弊』而没说条件"]
situation:
  object: 结果
  decision: 信不信结果
  state: 出现冲突
  trigger: 新材料声称某方法有效，而库里已有相反结论
motivation:
  goal: 建长期能力
  value: 真理优先、拒绝假共识
  cost: 曾经因忽略实验条件差异而误判过方法好坏
  role: 研究者
lineage:
  created: 2026-10-13
  source: 对话中明确要求（"分歧推翻很重要"）
```

## 关于表达

```yaml
id: r-2026-0002
judgment:
  text: 表述要"做了什么 → 结果 → 说明什么"，外行也能看懂
  strength: must
  mode: heuristic
  positive_examples: ["原来…改成…，结果…，说明…"]
  negative_examples: ["只有分数没有因果", "『换一个模型当裁判』这种没有前后对比的空话"]
situation:
  object: 写作
  decision: 怎么表达
  state: 结果已出
  constraints: ["读者可能不是同方向专家"]
motivation:
  goal: 让知识可复用
  value: 费曼式表达：讲不清楚就是没真懂
  role: 研究者
lineage:
  created: 2026-10-13
  source: 对话中对日报/深读措辞的多次修正
```

## 关于成本与排期

```yaml
id: r-2026-0003
judgment:
  text: 重活尽量放到错峰/闲时跑，且要给用户能看到的花费估算
  strength: prefer
  mode: mechanical
situation:
  object: 工具流程
  decision: 怎么表达 -> 何时做
  state: 未开始
  constraints: ["模型按 token 计费", "有错峰折扣窗口"]
  trigger: 任务会大量调用模型时
motivation:
  goal: 落地
  value: 成本意识
  role: 工程 owner
lineage:
  created: 2026-10-13
  source: 对话中要求"费劲的都在闲时跑、看下 API 收费"
```
