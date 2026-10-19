---
date: 2026-10-19
type: survey
question: "现有效果最好的最方便工业级应用的数据难度判断方法或指标是什么"
---

# 调研：现有效果最好的最方便工业级应用的数据难度判断方法或指标是什么

检索 174 篇候选（8 条检索式），深读 5 篇。

## 一句话答案

分场景，没有单一最优：指令微调（SFT）先试 T-SHIRT，预训练先试 125M 小模型困惑度剪枝，偏好对齐用 DPO 隐式奖励差；压缩率、MTLD、Flesch 是最便宜的预训练难度信号，但主要带来收敛加速，最终分数提升有限。单看报告的数字，T-SHIRT 的下游增幅最大（5% 数据、8 个基准平均最多比全量高 5.48 分），打分成本也最低（GPT-2、52k 样本单卡约 40 分钟），所以如果团队只做指令微调，它是第一选择。预训练里，125M 困惑度剪枝有明确的 1B/3B 下游收益和 1.14–1.45× 步数缩减，但最佳档位随数据域翻转；BLISS 的 1.7× 加速更强，代价是双层优化和代理模型训练，适合已有预训练基础设施的团队。以上数字来自不同数据、模型和预算，不能当成同一实验下的排名。

## 候选与取舍

### T-SHIRT（2506.01317）— 指令微调首选

- 为什么选它：本候选池里最接近「效果和落地成本兼顾」的 IFT 方法。它把 IFD 从样本级细化到 token 级，只用信息量高的 token 算 S-IFD，避免少量关键 token 被长回答平均掉；再加 embedding 扰动做近邻一致性，降低同义替换这类表面变化造成的误选。打分不需要 reference model，GPT-2 级别的小模型即可，代码公开。
- 前提：已有指令微调数据；能用 GPT-2 或同级小模型对回复 token 算 log-prob；接受对每个样本做 M 次扰动来算邻居分数；保留比例要在自己的验证集上校准；目标是指令微调，不是预训练或偏好对齐。
- 什么时候不 work：直接套到预训练或偏好数据上不成立；标签噪声多时，模型学习困难可能把噪声误当高信息样本（这是机制推断，节选没有噪声标签实验）；M 次扰动的额外开销节选没有量化，数据到百万级时要重新算账；摘要只给「相对全量最多 +5.48」和「优于已有 SOTA」，没有逐基准数字和固定预算下相对随机选择的逐项差额，不能保证每个任务都涨。
- 证据（2506.01317 T-SHIRT: Token-Selective Hierarchical Data Selection for Instruction T）：仅用 5% 数据做指令微调，在 8 个基准上平均最多比全量数据训练高 5.48 分。
- 证据（2506.01317 T-SHIRT: Token-Selective Hierarchical Data Selection for Instruction T）：用 GPT-2 打分，52k 条样本在单张 GPU 上约 40 分钟；代码公开。
- 证据（2506.01317 T-SHIRT: Token-Selective Hierarchical Data Selection for Instruction T）：S-IFD 不需要 reference model；约 22%–28% 的回复 token 的 |Δ_t|≤0.01，被当作无信息 token 排除。
- 证据（2506.01317 T-SHIRT: Token-Selective Hierarchical Data Selection for Instruction T）：作者报告跨多种 LLM 和训练集规模一致超过已有 SOTA 选择方法。

### 小模型困惑度剪枝（2405.20541）— 预训练首选

- 为什么选它：预训练里最成熟、最容易复现的一类难度打分：用 125M 参考模型逐文档算困惑度，再按低/中/高困惑度分档和保留率剪枝。不需要人工标注，也不需要训练额外打分器；已有 1B/3B 下游数字和达到基线所需步数，适合作为预训练数据管线的第一版。
- 前提：有完整候选语料；能训练或获得一个约 125M 的参考模型（论文在随机子集上训 26B token）；对每个文档做前向算 PPL；按经验 CDF 在低、中、高三档中选一档并扫选择率；最终模型从头训练；需要有代表性的域内验证集来定档位。
- 什么时候不 work：数据域组成一变，最佳档位会翻转：Pile 上选高困惑度 50% 最好，Dolma 上选中困惑度 50% 最好；5× 过训练时增益从 1.51 降到 0.84；超过 4 次重复后收益可忽略；高 PPL 既可能是真难，也可能是噪声或分布外文本；作者也承认上游测试集困惑度不是可靠的下游代理，有的干预困惑度更高但下游更好。
- 证据（2405.20541 Perplexed by Perplexity: Perplexity-Based Data Pruning With Small Refe）：3B 模型在 Pile 上平均归一化准确率从 18.63 提到 20.67（+2.04）；1B Pile 从 13.73 提到 15.62（+1.89）。
- 证据（2405.20541 Perplexed by Perplexity: Perplexity-Based Data Pruning With Small Refe）：达到基线同等性能所需 step 分别少 1.31×（Pile 1B）、1.45×（Pile 3B）、1.29×（Dolma 1B）、1.14×（Dolma 3B）。
- 证据（2405.20541 Perplexed by Perplexity: Perplexity-Based Data Pruning With Small Refe）：最优设置是 Pile 选高困惑度 50%、Dolma 选中困惑度 50%；5× 过训练时增益为 Pile 1.74、Dolma 0.84。
- 证据（2405.20541 Perplexed by Perplexity: Perplexity-Based Data Pruning With Small Refe）：参考模型 125M、训练 26B token；最终模型按 Chinchilla 最优的 20× 参数量 token 训练。

### 压缩率 / MTLD / Flesch 课程信号（2506.11300）— 最便宜的预训练难度指标

- 为什么选它：如果连额外神经模型都不想加，这是接入成本最低的方案：压缩率、词汇多样性 MTLD、可读性 Flesch 都可以直接用分词器、压缩器和文本统计算，不需要 GPU 打分。论文在 200 多个模型、最多 100B token 上验证，达到基线所需 step 减少 18%–45%，作为随机采样前的 warmup 还有最高 3.5% 的持续提升。
- 前提：预训练语料；分词器和压缩器；能按难度排序，或把数据分成若干难度组做 pacing；需要调课程长度、token 预算和领域配比；最适合当 warmup 或早中期训练策略，而不是永久替代随机采样。
- 什么时候不 work：它不是数据筛选器，不会直接去掉噪声、重复或低质样本；优势主要集中在训练早中期，后期收敛或只略高；困惑度排序早期收益强但后期明显回落；实验只覆盖 0.5B/1B、CulturaX 英文子集，跨域和更大规模没有证明；Flesch 严格排序在初期低于基线。
- 证据（2506.11300 Beyond Random Sampling: Efficient Language Model Pretraining via Curri）：训练 200 多个模型、最多 100B token，在 8 个基准和三种数据场景下，达到基线性能所需 step 减少 18%–45%。
- 证据（2506.11300 Beyond Random Sampling: Efficient Language Model Pretraining via Curri）：课程作为标准随机采样前的 warmup，可带来最高 3.5% 的持续提升。
- 证据（2506.11300 Beyond Random Sampling: Efficient Language Model Pretraining via Curri）：压缩率 pacing 少 39.5% step 达到基线峰值；MTLD 少 31.7%；Fertility 用少 45.3% step 达到基线最佳性能的 99.5%。
- 证据（2506.11300 Beyond Random Sampling: Efficient Language Model Pretraining via Curri）：严格按 MTLD 排序比基线高 1.8%、少用 17.9% step；按 token 数排序性能相近但少 27.5% step。

### DPO 隐式奖励差（2508.04149）— 偏好对齐专用

- 为什么选它：偏好数据有现成的 DPO 流水线时，这是边际成本最低的难度信号：直接用策略模型和参考模型的 log-prob 算隐式奖励差，差值越小越难，按 gap 升序选 10%–15%。只用 10% 数据，在多个数据集和两类对齐任务上稳定优于 5 个强基线，并在超过 67.5% 的情况超过全量数据训练。
- 前提：已有成对偏好数据；已有 DPO 策略模型和参考模型；能算 β log(π_θ/π_ref) 的差；按 gap 升序取低于阈值的子集；选择率约 10%–15%；最好本来就在跑 DPO，否则要多维护两套模型。
- 什么时候不 work：预训练和普通 SFT 不能直接套用；没有现成 DPO 模型时，打分要额外维护策略/参考模型；摘要没有给绝对准确率，也没有给打分耗时和显存；跨模型规模结果未报告；难度依赖当前策略，策略更新后同一批数据的分数会漂移，需要重新打分。
- 证据（2508.04149 Difficulty-Based Preference Data Selection by DPO Implicit Reward Gap）：只用原数据 10%，在多个数据集和对齐任务上稳定优于 5 个强基线。
- 证据（2508.04149 Difficulty-Based Preference Data Selection by DPO Implicit Reward Gap）：在超过 67.5% 的情况下超过全量数据训练；最优选择率为 10%–15%。
- 证据（2508.04149 Difficulty-Based Preference Data Selection by DPO Implicit Reward Gap）：覆盖 SHP、Skywork、UltraFeedback、RLHFlow 四个偏好数据集，以及奖励模型训练和 DPO 策略对齐两类任务。
- 证据（2508.04149 Difficulty-Based Preference Data Selection by DPO Implicit Reward Gap）：难度定义为 DPO 隐式奖励差 Δr_DPO，差值越小越难；不做长度归一化仍有效。

### BLISS（2510.06048）— 预训练效果更强但更重

- 为什么选它：不依赖外部预训练 oracle，用小 proxy 模型估计样本训练到收敛后的长期影响，再用双层优化训练 score model。1B 设置下达到与 MATES 同等性能快 1.7×；用 1B 选出的数据扩到 2.8B 预训练，每轮都优于 MATES，平均高 1.4%。适合已经有预训练基础设施、愿意为长期影响估计多付训练算力的团队。
- 前提：有验证集作为上层目标；有小 proxy 模型和 score model；能做双层优化和隐式微分；流程包含约 10k step warmup、双层训练、Top-20% 选择和约 10k step 重训；全量 P_i 归一化要用分布式部分求和近似；需要能反复跑预训练实验。
- 什么时候不 work：小团队或单卡不划算：proxy、score model、warmup 和重训都要算力；验证集分布决定选择方向，验证集偏了选择就偏；双层优化调参和稳定性成本高；摘要没有给固定预算下相对随机基线的逐项差额；节选没有 5.5 节的具体成本数字；也没有代码可用信息，复现门槛高于前三种。
- 证据（2510.06048 BLISS: A Lightweight Bilevel Influence Scoring Method for Data Selecti）：1B 设置下达到与 SOTA 方法 MATES 同等性能快 1.7×；2.8B 上每轮都优于 MATES，平均高 1.4%。
- 证据（2510.06048 BLISS: A Lightweight Bilevel Influence Scoring Method for Data Selecti）：在 C4 上预训练 410M/1B/2.8B Pythia 和 LLaMA-0.5B；选择率为 Top-20%。
- 证据（2510.06048 BLISS: A Lightweight Bilevel Influence Scoring Method for Data Selecti）：流程为 warmup 约 10k step、双层训练 score/proxy、全量打分、Top-20% 重训约 10k step，可多轮。

## 横向对比

| 方法 | 需要什么 | 成本量级 | 效果证据 | 成熟度 |
|---|---|---|---|---|
| T-SHIRT（2506.01317） | 指令微调数据；GPT-2 级打分模型；token log-prob；M 次 embedding 扰动；保留比例校准 | 低：52k 样本单卡约 40 分钟；另加 M 次扰动，具体开销未披露 | 5% 数据在 8 个基准上平均最多 +5.48（相对全量）；代码公开 | 较成熟；IFT 单场景；有公开代码 |
| 125M 困惑度剪枝（2405.20541） | 完整语料；125M 参考模型；逐文档 PPL；低/中/高分组；选择率扫描；最终预训练 | 中：参考模型训 26B token + 全语料推理 + 最终模型训练 | 3B Pile +2.04；1B/3B 达到基线少 1.14–1.45× step；Dolma 3B 仅 +0.59 | 方法简单、复现门槛低；对数据域敏感 |
| 压缩率 / MTLD / Flesch 课程（2506.11300） | 分词器、压缩器、文本统计；难度排序或分组 pacing；课程长度和 token 预算调参 | 低：打分不需要额外 GPU；但课程策略要多次预训练验证 | 达到基线少 18%–45% step；warmup 最高 +3.5% 持续提升 | 指标简单；研究阶段；主要买收敛速度 |
| DPO 隐式奖励差（2508.04149） | 偏好对；DPO 策略模型 + 参考模型；log-prob；按 gap 升序选 10%–15% | 低–中：每样本两次前向；耗时未披露；已有 DPO 流水线时最省 | 10% 数据，>67.5% 情况超全量；稳定胜 5 个基线 | 依赖现有 DPO 流水线；报告不完整，适合对齐阶段 |
| BLISS（2510.06048） | 验证集；proxy + score model；双层优化；warmup + 重训；Top-20%；分布式归一化 | 高：代理模型和打分模型都要训练，双层优化 + 多轮预训练 | 1B 比 MATES 快 1.7×；2.8B 平均 +1.4% | 研究级；流水线重；适合有预训练基础设施的团队 |

## 还缺什么

- 没有同一数据、同一 token/算力预算下的头对头比较；+5.48、+2.04、1.7×、18%–45% 这些数字不能直接排序。
- 难度定义仍然混在一起：T-SHIRT 衡量模型学习难度，困惑度衡量分布惊讶度，课程指标衡量语言统计复杂度；没有方法把噪声、重复、分布偏移和真正难学单独拆开，并用带 ground truth 的数据验证。
- 跨域和跨规模证据不完整：困惑度剪枝的最佳档位随数据组成翻转；课程实验只在 0.5B/1B、CulturaX 英文上做；T-SHIRT 声称跨 LLM 但节选没有逐基准数字；DPO 没有跨模型规模结果。
- 成本报告不全：T-SHIRT 的 M 次扰动开销、DPO 的打分耗时和显存、BLISS 的 5.5 节具体成本都缺失。
- 固定预算下相对随机选择的逐项差额，多数摘要没有给；DPO 只有胜率，没有绝对分数；T-SHIRT 的 +5.48 是「相对全量」的最高值，不是每个基准都涨。
- 选择比例和阈值如何随数据量、模型规模、训练时长变化，没有系统结论；与 data mixture、持续训练、重复 epoch 的交互也没解决。
- 工业接入缺延迟、吞吐和失败模式证据；没有噪声标签下的选择精度，也没有跨领域部署后的回归测试。

## 下一步能做的验证

- 第 1 周先做 SFT A/B：取 5–10 万条内部指令数据，另加 10% 人工注入的错标/低质样本做压力测试；基线用随机 5%/10%、全量和样本级 IFD；方法用 GPT-2 算 S-IFD，再加 M=5 次 embedding 扰动做近邻一致性，扫 5%/10%/20% 保留率。指标看同一 token 预算下 8 个基准或内部评测均分、相对基线的胜率、打分墙钟时间、跨 seed 选择重叠率，以及错标样本入选率。
- 第 1–2 周做预训练代理实验：用 C4 英文加一个内部领域混合，固定 5B–20B token；先用 410M 模型跑，最佳设置再用 1B 复现。基线包括随机采样、125M 困惑度低/中/高 50% 三档、压缩率/MTLD/Flesch 课程 warmup；指标看验证 loss、8 个下游 0-shot 均分、达到随机基线所需 step、2× 过训练后的增益，以及换领域组成后最佳档位是否翻转。BLISS 先不进第一轮，等这条基线建立后再比。

## 候选论文清单（只列粗读后进入比较的）

- `2506.01317` [T-SHIRT: Token-Selective Hierarchical Data Selection for Instruction Tuning](https://arxiv.org/abs/2506.01317)（已引用） · 
- `2405.20541` [Perplexed by Perplexity: Perplexity-Based Data Pruning With Small Reference Models](https://arxiv.org/abs/2405.20541)（已引用） · 
- `2506.11300` [Beyond Random Sampling: Efficient Language Model Pretraining via Curriculum Learning](https://arxiv.org/abs/2506.11300)（已引用） · 
- `2508.04149` [Difficulty-Based Preference Data Selection by DPO Implicit Reward Gap](https://arxiv.org/abs/2508.04149)（已引用） · 
- `2510.06048` [BLISS: A Lightweight Bilevel Influence Scoring Method for Data Selection in Language Model Pretraining](https://arxiv.org/abs/2510.06048)（已引用） · 

检索共命中 174 篇，其余 169 篇与问题关系不大，未进入比较。

## 检索过程

- 检索式：data difficulty metric language model training；hard example selection instruction tuning；data pruning perplexity score LLM；curriculum learning difficulty estimator pretraining；benchmark difficulty prediction item response theory；coreset selection data quality LLM；example difficulty estimation few-shot benchmark；pairwise comparison data difficulty scoring
- 纳入：给出可计算的难度分数或判定规则，并说明计算所需的数据、模型和算力；用可复现实验证明该指标与下游效果、学习顺序或数据筛选收益相关；与随机选择及至少一种常见基线比较，并报告固定预算下的收益或代价；说明跨模型、跨领域或跨规模的适用性，或明确适用边界
- 排除：纯理论分析，没有可执行指标或实验验证；只针对单一数据集刷分，不能迁移到一般训练流程；依赖闭源数据、不可复现实验或未披露关键实现；仅发布数据集或工具，没有难度判断方法和效果证据；只做排行榜评测，不讨论训练数据选择或工业落地成本
- 读的时候盯：难度的定义是否清晰，是否把噪声、重复、分布偏移和真正难学混在一起；打分成本、延迟和工程接入方式，能否离线预处理或用小模型完成；固定算力下的下游收益、消融结果和跨模型稳健性，而不只看相关性
