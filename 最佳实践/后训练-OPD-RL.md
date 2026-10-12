# 后训练-OPD-RL 最佳实践手册

> 后训练里的蒸馏（OPD/on-policy distillation）与强化学习（RL/RLHF/GRPO）：怎么把信号变成能力。

自动积累，只增不减；「我的补充」是你自己写的地方，脚本永不覆盖。

## 目标与产出
- 把项目产出定义成三段闭环的产物，而不是只改一处的补丁：先用脚手架把能力逼出来，再把成功轨迹做成训练数据，最后把能力写进权重并撤掉脚手架，让上下文开销回落；数据、脚手架、权重各自成层、共用一个循环内核。（来源：[[论文/RSI/MetaRSI RSI2 A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems T|MetaRSI / RSI2: A Meta-Recursive Sel]]）
- 训练数据要产出完整轨迹而不是只留正确解：跑错和掉分的那一轮一起保留，损失只加在真正往前走的那几步，重复轮询、无新观测的调用和系统消息一律不加。这样模型学的是「出错之后怎么改」，AREX-2 在 MLE-bench Lite 拿到 81.8，比最强公开基线高 8.1 分。（来源：[[论文/RSI/AREX-2 Advancing Self-Improving Agents through Long-Horizon Reflective Tasks|AREX-2: Advancing Self-Improving Age]]）
- 选题前先把候选任务的判对错方式列出来并分级（能跑测试到只能请专家打分），优先做判分成本低的那一档：普查的 55 个已闭合自改进循环里，53 个卡在前三级。（来源：[[论文/RSI/MetaRSI RSI2 A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems T|MetaRSI / RSI2: A Meta-Recursive Sel]]）
- 造环境时的产出物要成对交付：先解出数理模型的最优值和一个默认策略的分数，再把决策过程做成有状态工具环境，奖励把实际收益夹在最优值和默认值之间归一成 0–1，让环境动态和评分来自同一份解。（来源：[[论文/其他/Verifiable Hidden Dynamics Play Generating Agentic RL Environments from Solved Mechanisms|Verifiable Hidden Dynamics Play: Gen]]）
- 要测行为合规时，产出物是从真实部署记录剪出来的接续式考题：剪到出错前那一步就该让被测模型接下一句，不重放环境，这样内部工具和 MCP 服务器的记录也能拿来出题。（来源：[[论文/RSI/TraceDance An Automated System for Building Agent Behavior Benchmarks from Real-World Agen|TraceDance: An Automated System for ]]）
- 把智能体外面那层组织调用和工具的干活程序当成可训练对象：proposer 输入任务描述、当前 harness 代码和执行报告，输出结构化编辑（替换哪一段、换成什么），奖励用改完后在新题上的真实跑分算；训练时 solver 冻结，改程序模型单独用 GRPO 学。（来源：[[论文/Harness/Harness Learning Enables Generalizable Test-Time Adaptation|Harness Learning Enables Generalizab]]）
- 小模型蒸馏的产出物要从「照抄带 harness 提示的老师」改成「学会看提示后改动作」：同一老师带提示和不带提示各问一遍，只让学生偏向带提示时更可能选的动作，并在算偏好前丢掉与 harness 记录硬矛盾的动作对。（来源：[[论文/Harness/Harness-Aware Distillation for Small Language Model Agents|Harness-Aware Distillation for Small]]）
- 逐轮自蒸馏的产出物要包含「挑步器 + 特权保留项」：用同一模型带提示与不带提示两种输入的 JSD 给每一步打分，只学 top-ρ 步，同时用 KL 把「带提示那一面」钉在冻结老师上，否则第三周期会掉。（来源：[[论文/RSI/ReSAIL Mitigating Collapse in Iterative Agent Self-Distillation|ReSAIL: Mitigating Collapse in Itera]]）
- 师生同源时，别只把老师当终点：把老师减初始模型的逐层隐藏状态残差当 RL 方向，监督目标设成 h_T+(λ−1)(h_T−h_B)，λ 取 1.25 左右，把学生往这个方向外推，而不是在出词概率上硬推。（来源：[[论文/后训练/The Teacher Is a Direction, Not a Destination Extrapolating RL-Induced Representation Resi|The Teacher Is a Direction, Not a De]]）
- 把「一个能力」定义成后训练模型相对它前身 checkpoint 的 log 概率变化，在学生自己生成的每一步上把多个专家的 log 比按权重相加，变成明确的目标分布再蒸馏；这样能在同一个学生身上同时调准确率和回答长度。（来源：[[论文/后训练/Lightning Weave Improving the Accuracy-Efficiency Frontier of Reasoning Models through Cap|Lightning Weave: Improving the Accur]]）
- 自演化出题的产出物不能只有题目和答案一致性检查，还要有成立性判断和新题型判断：答题模型每轮混入一成初始数据复习判题，出题奖励写成坏题直接扣分、好题才拿难度分，并按「同一类题」去重。（来源：[[论文/RSI/Questioning the Questions Sustaining Self-Evolution in Reasoning Models|Questioning the Questions: Sustainin]]）
- 长程任务 RL 可以先不急着做智能体侧 SFT 热身，而是把环境反馈做成可干预对象：前段给动作提示、后段补观测信息，以 0.5 概率注入，200 步训练在第 100 步从动作提示切到观测补充。（来源：[[论文/强化学习/Environments as Scaffold Enriching Feedback to Bootstrap Self-Evolving Agents in Long-Hori|Environments as Scaffold: Enriching ]]）
- 在线 RL 的产出物按五件套定义：任务、能动手的软件环境、检查答案也检查中间步骤的 verifier、可反复试跑的 rollout、按分数发奖励；卡点通常先在环境和打分器，不在算法。（来源：[[论文/强化学习/Online RL Task + Environment + Verifier + Rollout + Reward|Online RL: Task + Environment + Veri]]）
- 把网上现成的 Agent Skills 自动改造成 RL-ready 终端任务包：用 Harbor task format 输出 instruction.md、容器环境、rubric，每条任务要求 oracle 能过、NOP 必失败、静态检查通过并钉住基础镜像。（来源：[[论文/强化学习/Skill2Env|Skill2Env]]）
- 工具智能体后训练可先按两段式骨架立项：9B 级学生先用冷启动 SFT 打底，再放进带工具的真实环境做 on-policy RL，奖励给到整条轨迹而不是只给最后一步。（来源：[[论文/后训练/Pistis Technical Report|Pistis Technical Report]]）
## 动手前必须想清楚的
- 训练库入库前先跑两条环境准入检查：参考解必须能跑出分数、朴素基线必须明显更低，任一不过就丢掉；同时把通过/不通过换成通过测试比例这类连续分，让每一轮改进都有可学的信息。（来源：[[论文/RSI/AREX-2 Advancing Self-Improving Agents through Long-Horizon Reflective Tasks|AREX-2: Advancing Self-Improving Age]]）
- 先写明损失是按 token 平均还是按回答平均，因为平均规则等于隐式加权：所有 token 平等平均时，长度约 3 倍的数学回答会白拿约 44% 的损失权重；改成先定领域权重、领域内按回答平均后，数学降 3.0 分、科学升 2.1 分。（来源：[[论文/后训练/From Gradients to Capabilities Understanding Multi-Teacher On-Policy Distillation|From Gradients to Capabilities: Unde]]）
- 把「是否带一阶动量」当作对照变量先定下来：同一学生参数、同一批回答下，三种平均规则的原始梯度余弦只有 0.68，过一遍 Adam 后升到 0.96，清掉一阶动量后不同老师的更新余弦掉到接近 0；学生边练边换前缀时动量记着旧梯度会拖慢适应，同样跑 500 步无动量 SGD 的平均分全面更高（39.94、39.46、39.26 对 38.91、38.63、38.79）。（来源：[[论文/后训练/From Gradients to Capabilities Understanding Multi-Teacher On-Policy Distillation|From Gradients to Capabilities: Unde]]）
- 统计「改了多少参数」时同时看 FP32 主权重和 BF16 权重，别只数 BF16：FP32 里约 97% 的参数都变了，四舍五入成 BF16 后只剩 7–11%；FP32 里三分之一参数承担 90% 平方变化，BF16 只要 4%。（来源：[[论文/后训练/From Gradients to Capabilities Understanding Multi-Teacher On-Policy Distillation|From Gradients to Capabilities: Unde]]）
- 记忆默认原样存整条轨迹、把整理推迟到读取时，而不是任务做完就压成固定笔记：同样用 Gemini 整理，读时整理不训练就有 WebShop 61.0，写入时的 SkillOS 只有 41.0，因为写入时要提前猜未来任务，猜错就永久丢信息。（来源：[[论文/其他/Just-in-Time Memory Learning to Curate Task-Adaptive Memory for LLM Agents|Just-in-Time Memory: Learning to Cur]]）
- 做中间表示对齐前先用逐层 CKA 判断这对师生适不适合：同血缘、层能对上的一对（CKA 对角线 0.983）全程开着不崩、最高 87.22，跨尺寸时按相对深度配对的层在做不同的事，只能对两边送进 LM head 的最后一层动手。（来源：[[论文/后训练/LastOPD Taming Collapse in Latent On-Policy Distillation|LastOPD: Taming Collapse in Latent O]]）
- 先决定是否区分「通过但写得差」：同组里只要测试通过就发一样多的奖励，通过的轨迹会拿到完全相同的优势，模型学不到哪份实现更值得留；要区分就得先准备好组内质量排名和优势重分配的方案。（来源：[[论文/后训练/Groupwise Agentic Grading and Advantage Redistribution for Code Agent RL|Groupwise Agentic Grading and Advant]]）
- 先定 KL 方向再开训：同分布成绩主要看 forward KL 还是 reverse KL，而不是数据由谁生成；同一套流程里 forward KL 在两档学习率、两种 rollout 下稳在 71%–73%，reverse KL 会从 35% 跳到 72%。（来源：[[论文/后训练/On-Policy or Off-Policy Learning A Systematic Study of Distillation Dynamics|On-Policy or Off-Policy Learning? A ]]）
- 蒸馏换差距算法等于给学生输出熵设方向：想让学生发散用 forward KL，想保守用 reverse KL；把学生平均熵和损失一起打日志，熵明显低于损失说明还没训到位，截断方式本身也会改变熵。（来源：[[论文/后训练/Divergence controls entropy in distillation|Divergence controls entropy in disti]]）
- 别把「老师不同意学生的词」当成「学生做错了」：只看 OPD 逐词概率差时，区分回答对错的 AUROC 只有约 0.50；要引入判题器或 verifier 来定义哪条回答该补课。（来源：[[论文/后训练/DiffGate Difficulty-Gated Teacher Guidance for On-Policy Distillation|DiffGate: Difficulty-Gated Teacher G]]）
- 多任务 OPD 里反馈的正负应由学生自己对错决定，而不是由老师逐词偏好决定；旧 OPD 即使学生答对，老师给的对数比平均仍是负的（Qwen3 −1.31、Llama −0.22），会把正确回答往下压。（来源：[[论文/后训练/DuoOPD Learning from Joint Teacher-Student Outcomes for Multi-Task On-Policy Distillation|DuoOPD: Learning from Joint Teacher-]]）
- on-policy 不是天然更好：同分布主成绩 on-policy 72%、off-policy 73%；on-policy 的稳定优势只出现在迁移到更难题目时，pass@k 高 10–15 个点。立项时要把 off-policy 当标准基线。（来源：[[论文/后训练/On-Policy or Off-Policy Learning A Systematic Study of Distillation Dynamics|On-Policy or Off-Policy Learning? A ]]）
- 开放题先上 rubric RL 前，先做一轮只让老师看 rubric、学生看不到的逐词 OPD 热身；直接用固定答案 SFT 会把学生词元熵压低，接上 RL 后更容易练崩或学会说空话。（来源：[[论文/后训练/OPD Before RL Warm-Starting Rubric-Based RL with On-Policy Distillation|OPD Before RL: Warm-Starting Rubric-]]）
- 长文本自我训练前先决定更新是否落盘：让模型生成文本再把更新永久写进权重会越学越坏，同样文本只读不写就没事；落盘前要有一份独立真实文本或任务指标验证候选更新。（来源：[[论文/后训练/Self-Generated Feedback Destabilizes Test-Time Training A Causal Decomposition of Long-Hor|Self-Generated Feedback Destabilizes]]）
- 多轮 agent 训练前先做关键错步诊断：ALFWorld 262 条失败轨迹里 155 条（59%）只是某一步走错，平均在第 8–12 轮，之后还白走 18–21 轮；把错误步换成标准动作成功率能从 8% 升到 59%。（来源：[[论文/后训练/PivotOPD Learning to Recover from Pivotal Mistakes in Multi-Turn Agents|PivotOPD: Learning to Recover from P]]）
- 跨词表蒸馏先量对齐覆盖，不要用静态词表重叠下结论：静态 Jaccard 只有 39.49%–64.87%，但学生轨迹上严格一对一配上的 token 占 85.57%–96.98%，严格对齐位置共享词表保留老师 99.69%–99.90% 的概率质量。（来源：[[论文/后训练/Rethinking Cross-Tokenizer On-Policy Distillation From Alignment Coverage to Supervision R|Rethinking Cross-Tokenizer On-Policy]]）
- 稀疏 OPD 选 token 不能只看 usefulness，还要估梯度估计可靠性：用 IER 做候选集近似，再和已有 usefulness 分数组合，0.1%–1% 的 token 预算就能追平或超过全量 OPD。（来源：[[论文/后训练/1% of Tokens Can Be Enough On Gradient Estimation in On-Policy Distillation|1% of Tokens Can Be Enough: On Gradi]]）
- 多奖励训练先算每个奖励在批内的活跃组比例：一个奖励越少出现「同组内有对有错」，它对总优势的推力越小；长度、格式这类接近饱和的奖励会先没信号，需要在聚合时按密度补偿。（来源：[[论文/强化学习/Make Sparse Rewards Count Density-Aware Reward Aggregation for Multi-Reward RL|Make Sparse Rewards Count: Density-A]]）
- 后训练前先设好覆盖率指标：只报 pass@1 会把「后训练把多试才过的题挤向必过或必挂」藏起来；同一预算下基础模型加脚手架在 WebShop 可过 85%，同族后训练模型只有 56%。（来源：[[论文/后训练/Sharpening Tax in Post-Training|Sharpening Tax in Post-Training]]）
- RL 后训练评估必须同时报 pass@1 和 pass@1024：RL 会让解法路线数从平均 3.24 降到 2.66，数学常见是 Pass@1 涨、Pass@1024 跌，而低基线 BoxNet 上 Pass@1 从 3.8% 升到 9.9%、Pass@1024 从 34.0% 升到 51.0%。（来源：[[论文/强化学习/How RL Reshapes LLM Reasoning Transferability, Coverage, and Scaling Laws|How RL Reshapes LLM Reasoning: Trans]]）
- 偏好蒸馏的反面答案不要优先用学生自己的错答案；用严格更小的冻结模型生成、并验证为错的答案，14B 学生上小模型比例从 0% 加到 100%，代码 avg@4 从 59.73% 升到 63.28%。（来源：[[论文/后训练/Smaller Models, Better Rejects Preference Distillation Scaling|Smaller Models, Better Rejects: Pref]]）
- 挑 SFT 数据不能只看答案对不对，要看解题路线像不像：同样数据量下选差得最远的路线，OLMo3-7B 在没见过的环境上 pass@8 高 16.9 个点；路线指纹只用文本和固定随机投影，不用 GPU。（来源：[[论文/后训练/Selecting Diverse SFT Traces Improves Post-RL Generalization|Selecting Diverse SFT Traces Improve]]）
- 用奖励模型或评分器前先查它偏爱什么表面特征：常见毛病落在最后一层线性打分权重上，只改线性头、按每批数据挑要修的毛病，五个模型三个榜单平均涨 8.3、18.0、6.9 个百分点。（来源：[[论文/后训练/BiasReducer Adaptive Bias Mitigation for Reward Models|BiasReducer: Adaptive Bias Mitigatio]]）
- 直接给档位的模型要提前检查档位使用率：有序评分任务只用到 67%–76% 的有效档位，无序分类能用 87%–102%；评测时除准确率外要报有效档位使用率 R 和 TVD。（来源：[[论文/评测/More Choices, Fewer Decisions Ordinal-Scale Bias in JEV-like Direct-Decision Models|More Choices, Fewer Decisions: Ordin]]）
## 常见坑与解决办法
- 自己出题自己答会互相「对暗号」，分数看着涨其实没真变强。解决：把出题和解题拆成两个角色、解题者看不到答案，并让出题模型和答题模型看不同资料；盲解结果一致才收进数据集，代价是只能保证前后自洽。（来源：[[论文/RSI/False Frontiers Diagnosing and Mitigating Co-Cheating in Self-Evolving Search Agents|False Frontiers: Diagnosing and Miti]] · [[论文/RSI/MetaRSI RSI2 A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems T|MetaRSI / RSI2: A Meta-Recursive Sel]]）
- 别让自改进循环把「什么算成功」也一起改掉，否则分数会白涨。解决：把评价器、题库和预算账本挪到所有可改范围之外，规定模型只负责提议、固定代码负责判定。（来源：[[论文/RSI/MetaRSI RSI2 A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems T|MetaRSI / RSI2: A Meta-Recursive Sel]]）
- 多轮蒸馏里老师信号会断在学生第一次做错那一步，错位之后的分数不可靠、梯度会被带偏。解决：用每回合老师平均 log 概率当在线 OOD 探针，跌破阈值就停，并把触发早停的那一回合保留进 loss 当负信号。（来源：[[论文/后训练/Know When to Stop, Where to Restart Accelerating Multi-Turn Agentic On-Policy Distillation|Know When to Stop, Where to Restart:]]）
- 前缀复用时把带错的前缀一起存下来，学生会从错误状态继续走、训练很快崩。解决：加前缀质量门槛 α=-0.8，关掉门槛曲线会迅速崩掉；复用时只对新生成本回合算累积和，别把历史回合算进去。（来源：[[论文/后训练/Know When to Stop, Where to Restart Accelerating Multi-Turn Agentic On-Policy Distillation|Know When to Stop, Where to Restart:]]）
- 中间表示对齐不是越久越好：全层一直对齐时 MATH-500 从 46 掉到 11.3，且中层 CKA 0.99、投影余弦从 0.97 涨到 0.98 的同时分数掉了约 35 分，「对齐分数在涨」不能当「学得更好」。解决：只对最后一层、前 10 步把中间表示权重从 1 线性降到 0、token 权重从 0 升到 1；别硬切，硬切只有 50.45，比完全不用中间表示还差。（来源：[[论文/后训练/LastOPD Taming Collapse in Latent On-Policy Distillation|LastOPD: Taming Collapse in Latent O]]）
- 带 harness 痕迹的成功轨迹直接拿去微调会掉分：Terminal-Bench 2 上直接微调从 57.0 掉到 53.4，重写后升到 74.2。解决：先让模型把成功过程写成一页 runbook（只写关键步骤和检查点、不许写最终答案），挑掉泄题的，再在全新沙箱里照着重做。注意这组对比的数据量不同（约 2,001 对 11,094 条），不能把涨分全归给重写。（来源：[[论文/RSI/Scaling Trajectories for Complex Tasks through Recursive Self-Rewrite|Scaling Trajectories for Complex Tas]]）
- 把差代码的奖励直接调小等于削掉总奖励，训练会被带偏：只调小那一版第 20 步从 56.5% 掉到 48.8%，策略熵从 0.359 涨到 0.905、平均长度从 47.1k 涨到 114.1k。解决：把扣下来的奖励按比例补给同组其他通过的代码，保持组内优势总和不变。（来源：[[论文/后训练/Groupwise Agentic Grading and Advantage Redistribution for Code Agent RL|Groupwise Agentic Grading and Advant]]）
- 只留做对的解答当训练数据，等于把「出错后怎么办」整段丢掉。解决：整条轨迹一起留，跑错和掉分都不删，损失只加在真正推进的决策步上。（来源：[[论文/RSI/AREX-2 Advancing Self-Improving Agents through Long-Horizon Reflective Tasks|AREX-2: Advancing Self-Improving Age]]）
- 组内归一化会把效率项的相对权重抹掉，只调权重系数不管用：整组几乎全做对时，哪怕效率权重只给 0.1，效率高低的信号也能和成败一样大。解决：给优势的分母加下限。（来源：[[论文/RSI/Qwen-Planner-Agent A Closed-Loop AI-for-AI Framework for Real-World Mobile Planner Agents|Qwen-Planner-Agent: A Closed-Loop AI]]）
- 微调会按任务形状分涨跌：会反复改答案的模型微调后短题和挑工具变强，长推理和终端任务反而变差。解决：评测按任务形状分组报分，短题/工具一档、长推理/终端一档，别只报一个总平均分，否则涨跌互相抵消。（来源：[[论文/后训练/Fine-Tuning DiffusionGemma What Works, What Breaks|Fine-Tuning DiffusionGemma: What Wor]]）
- 定性编码时码本越长、待打码片段越长，初步打标越不准。解决：预处理先让模型只抽相关片段再编码，并优先压缩码本长度，别把整段长文直接塞进去。（来源：[[论文/其他/How AI Coders Discuss, Disagree, and Reach Consensus Challenges and Opportunities for LLM-|How AI Coders Discuss, Disagree, and]]）
- OPD 在整组全错时没有梯度，老师逐词信号也不知道对错。解决：只在判错的回答上请老师逐词补，整组做对越少补得越狠，更新写成 λ(1−p)^γ(1−R_i)·2tanh(Δ/2)，λ=0 退回 GRPO，γ=0 就是平摊版。（来源：[[论文/后训练/DiffGate Difficulty-Gated Teacher Guidance for On-Policy Distillation|DiffGate: Difficulty-Gated Teacher G]]）
- 老师逐词偏好会把学生已经答对的题往下压，只把方向改成跟学生走还不够。解决：老师单独答对时把验证过的正确答案塞进老师上下文再打分；学生单独答对时整条回答共用一个任务内平均权重，不让老师逐词改淡。（来源：[[论文/后训练/DuoOPD Learning from Joint Teacher-Student Outcomes for Multi-Task On-Policy Distillation|DuoOPD: Learning from Joint Teacher-]]）
- 逐轮自蒸馏会越教越差：只学不带提示那一面时，看提示那一面也会跟着漂移，下一轮老师示范变差。解决：只学老师带提示与不带提示差别最大的 top 5% 步，并用 KL 把看提示那一面钉在冻结老师上，λ 取 0.5。（来源：[[论文/RSI/ReSAIL Mitigating Collapse in Iterative Agent Self-Distillation|ReSAIL: Mitigating Collapse in Itera]]）
- 自蒸馏模仿知道答案的老师会压掉犹豫和自我纠错。解决：让同一模型换一句提示扮粗心解题者，再把它的话推开；门控用 max(0, π_neg−π_ref)，只罚被反面提示推高的词，惩罚用 G/(2−π_θ) 封顶，并加按 π_ref 加权的 KL，α=0.01。（来源：[[论文/后训练/Negative Self-Distillation Learning to Reason by Avoiding Flaws|Negative Self-Distillation: Learning]]）
- 反面例子必须真弱：把出答案的一方换成比学生更强或老师自己，成绩会掉；Qwen3-1.7B 学生配 Qwen3-0.6B 负模型，数学平均从 48.3 升到 56.3，负模型答案预生成后训练时间从 9 小时 19 分降到 3 小时 34 分。（来源：[[论文/后训练/On-Policy Distillation with Negative-Policy Rollouts|On-Policy Distillation with Negative]]）
- 多轮失败常只差关键一步，但普通 OPD 教不到出错后的局面。解决：用大老师回看轨迹挑关键步，在关键步用正确动作纠偏，再让老师写之后几轮恢复回复；恢复预算 K 在需要长串细动作的任务取 2，其余取 1，验收看成功率。（来源：[[论文/后训练/PivotOPD Learning to Recover from Pivotal Mistakes in Multi-Turn Agents|PivotOPD: Learning to Recover from P]]）
- 离线缓存老师分数会在学生离开旧策略后不准、训练收不住。解决：把缓存的能力变化量先变成一个明确的目标分布，让学生对齐；学生等于它时损失和梯度都为零。（来源：[[论文/后训练/Lightning Weave Improving the Accuracy-Efficiency Frontier of Reasoning Models through Cap|Lightning Weave: Improving the Accur]]）
- 跨词表蒸馏把对不上的片段补上 MSE 会掉分：18 个正权重设置全部比不加时低 0.27–1.20 个百分点。解决：只在严格 1:1 位置把两边分布限制到共享词表上重新归一化，用反向 KL 训；只保留学生自己挑的前 16 个共享词。（来源：[[论文/后训练/Rethinking Cross-Tokenizer On-Policy Distillation From Alignment Coverage to Supervision R|Rethinking Cross-Tokenizer On-Policy]]）
- reverse KL 在能模仿时压低熵，在老师分布太平或任务太难时反而推高熵，不能只看差距名字。解决：把 KL 方向、采样来源两个开关拆开做对照；要稳用 forward KL，要保守用 reverse KL，并记录学生平均熵与损失曲线。（来源：[[论文/后训练/Divergence controls entropy in distillation|Divergence controls entropy in disti]] · [[论文/后训练/On-Policy or Off-Policy Learning A Systematic Study of Distillation Dynamics|On-Policy or Off-Policy Learning? A ]]）
- Test-time training 里模型自己写、又学自己写的内容会形成自我加强闭环。解决：把读和写拆成两份对照；冻住生成器做 Fixed Generation 对照；更新落盘前先在独立真实文本上比 W 和 W+δ 的损失，只收不亏的更新，真文本要少而均匀地穿插。（来源：[[论文/后训练/Self-Generated Feedback Destabilizes Test-Time Training A Causal Decomposition of Long-Hor|Self-Generated Feedback Destabilizes]]）
- GRPO 在整组全错时优势为零，难题永远学不到。解决：每题先只采 K=4，全对就丢，全错按 p=0.95 继续采到做对；做对后把最近 4 步内的历史答案并成一个大 GRPO 组算优势。（来源：[[论文/强化学习/Learning to Solve Hard Problems in RL for LLMs by Never Giving Up|Learning to Solve Hard Problems in R]]）
- 多奖励直接相加时，数值波动大的奖励会主导优势分母。解决：保留分子总奖励，分母改成相关系数矩阵求和后开根号，零方差维度行列置 0，再取 max(·,0)。（来源：[[论文/强化学习/CorrGRPO Correlation-Normalized GRPO for Multi-Reward Learning|CorrGRPO: Correlation-Normalized GRP]]）
- 稀疏奖励在接近饱和时会被淹没。解决：保留逐奖励组内归一化，在聚合前按本批估计每个奖励的活跃组比例 π_k，权重取 min(5, √(π_ref/π_k))，只作用在正优势上；每组采样数调到 16–32 可白拿一部分密度。（来源：[[论文/强化学习/Make Sparse Rewards Count Density-Aware Reward Aggregation for Multi-Reward RL|Make Sparse Rewards Count: Density-A]]）
- PPO critic 不稳会把 actor 带崩。解决：critic 保留超长截断样本，只对 actor 做超长过滤；按同题一组 rollout 的得分标准差做逆权归一化；critic 一批拆成 4 个小批，每批算完梯度裁剪再更新。（来源：[[论文/强化学习/EasyPPO Stabilizing the Critic Is Key|EasyPPO: Stabilizing the Critic Is K]]）
- critic 不必等答案写完才能用，但不能整题一起信。解决：以 1 万 token 为一个动作块，只对逐题确认够准的前缀用 critic 估价；不够准就照旧写完整条；被判可信的题仍有 1/4 概率跑完整条审计。（来源：[[论文/强化学习/Trust the Critic More|Trust the Critic More]]）
- 智能体评测里的 reward hacking 不是单次工具调用毛病，而是观察—行动—交接—评分—发奖整条链路的权限越界。解决：静态形式化模型先找污点路径，运行时用基础设施侧资源交接和分数来源证据判定，语义问题交独立审计。（来源：[[论文/智能体安全/BenchShield Formal Model-Backed Instrumentation for Reward Integrity in LLM-Agent Evaluati|BenchShield: Formal Model-Backed Ins]]）
- SFT 后给每个示范词配非负权重只能缩放，不能反向修正已经学歪的方向。解决：冻住基座与 SFT 增量，只学一组带符号门控；λ=1 不动，0 到 1 削弱，小于 0 反向，大于 1 加强，零初始化精确还原第一阶段模型。（来源：[[论文/后训练/Rethinking Token Reweighting for SFT Suppress, Reverse, and Extrapolate Learned Features|Rethinking Token Reweighting for SFT]]）
- SFT+RL 容易学会说空话骗分。解决：rubric 只放老师上下文，学生侧不出现；第一阶段用 forward KL 只对齐老师 top-256；第二阶段用 DAPO 式 GRPO，并要求裁判必须引用原文才给内容分。（来源：[[论文/后训练/OPD Before RL Warm-Starting Rubric-Based RL with On-Policy Distillation|OPD Before RL: Warm-Starting Rubric-]]）
- 已答对的知识里，答案实体被越多事实指向的越容易被邻近微调改坏。解决：按答案实体入度给知识风险打分；LoRA 微调时用 5–100 条热门事实当回放锚点，加 KL 约束保持旧模型输出，权重 0.1。（来源：[[论文/后训练/Popular Knowledge Propagates More Errors in LLM Knowledge Updating|Popular Knowledge Propagates More Er]]）
- 长链推理坏在分支太多和终点奖励太稀疏两件事。解决：用「这一步消掉多少残差」偏置采样，只在训练时偏置、推理时不剪枝；再用双曲空间里离目标结构的距离做密集结构奖励，两者一起用。（来源：[[论文/推理/SAGE Mitigating Long-Horizon Reasoning Biases via Topological Guidance|SAGE: Mitigating Long-Horizon Reason]]）
- 数学题做不出常常不是算不动，而是开头想不出关键数学结构。解决：把完整解答给模型看后让它说关键思路；补课时只给一句结构化关键思路，并用只夹住一边的 reverse KL 减少漂移，而不是灌整篇解答。（来源：[[论文/推理/The Missing Primitive Diagnosing and Repairing Mathematical Reasoning in Large Language Mo|The Missing Primitive: Diagnosing an]]）
- 预训练模型顺着上下文引用链只可靠跟 1.4–3.6 行，加参数规模也不解决。解决：先量冻结模型的截止层，再在附近中间层加 rank-8 LoRA，1200 步、AdamW、学习率 1e-3、批 16，并加 KL 拉住原分布。（来源：[[论文/推理/Transformers Stop Thinking Too Early, and a Tiny LoRA Fixes It|Transformers Stop Thinking Too Early]]）
- 直接给档位的模型爱挤在中间几档，这是训练学出来的决策偏好。解决：评测时打乱候选顺序、报有效档位使用率 R 和 TVD；用带偏差校正的 LoRA 在压缩最重的档位补训练，档位使用率可从约 47% 升到 86%。（来源：[[论文/评测/More Choices, Fewer Decisions Ordinal-Scale Bias in JEV-like Direct-Decision Models|More Choices, Fewer Decisions: Ordin]]）
## 可复制配方
- 可整段照搬的自改进训练配方：环境准入两条检查；把通过/不通过换成通过比例这类连续分；整条轨迹保留失败轮；损失只加在推进决策上；给模型显式的轮数预算让它先建基线再改；评测按轮数扫一条曲线看什么时候不再涨。（来源：[[论文/RSI/AREX-2 Advancing Self-Improving Agents through Long-Horizon Reflective Tasks|AREX-2: Advancing Self-Improving Age]]）
- 跨 harness 经验重写配方：每题采 K=4 个 runbook，先做 schema 之类硬检查，再让 critic 只看公开任务描述来筛；每个留下的 runbook 在通用 harness 下用温度 0.7 重跑 M=4 次，只留通过验证的；训练数据里删掉 runbook 和 critic 对话，只留任务、环境观察和模型自己的动作。runbook 固定写五块：目标终态、关键里程碑、有用检查、恢复策略、常见坑。（来源：[[论文/RSI/Scaling Trajectories for Complex Tasks through Recursive Self-Rewrite|Scaling Trajectories for Complex Tas]]）
- 读时整理记忆的训练配置：记忆库只存原始轨迹、只用成功轨迹；检索用 BM25 按任务描述；整理者输出一段短简报塞进执行者提示词；训练用 Qwen3-8B、GRPO 100 步、学习率 1e-6、batch 32、组大小 8，只给任务成败奖励，执行者全程冻结；一个整理器可直接配 Qwen3-8B、Gemini-2.5-Pro、GPT-5.4 三个执行者。（来源：[[论文/其他/Just-in-Time Memory Learning to Curate Task-Adaptive Memory for LLM Agents|Just-in-Time Memory: Learning to Cur]]）
- PACT 的三处改动可以直接搬：评论家损失从 MSE 换成 BCE、价值用 sigmoid 当概率输出；GAE 的 λ 设为 1，优势直接写成 R 减前缀价值；训练顺序改成先 actor 后 critic，用一次额外前向算新旧策略比并对评论家目标重加权，比值落在 [0,6] 外的样本丢掉。（来源：[[论文/其他/PACT From Credit Assignment to Critic Alignment|PACT: From Credit Assignment to Crit]]）
- 把 OPD 当 KL 正则 RL 来省采样：奖励写成 log(π_E/π_ref)，用带 Huber 截断的平方损失加熵奖励，在回放池上更新；超参每批 64 条提问、每题 4 条回答、每批更新 4 次起步，回放版每批 256 步优化。（来源：[[论文/后训练/An RL View of OPD Least Square Policy Distillation for Sample-Efficient LLM Reasoning|An RL View of OPD: Least Square Poli]]）
- 邻近老师自蒸馏的可搬配置：1,000 道挑选题、500 个随机种子加 M0 共 501 个候选、按边际 filtered PTA 贪心选 K=25、路由 q=0.75、SCGate 阈值 0.99、κ_sel=κ=0.06、全词表 forward-KL、100 步、全参数训练；噪声半径 8B 用 σ=0.002，1.7B/4B 用 0.0006/0.0012。显存不够时先流式跑一遍只存路由元数据，第二遍一次只展开一个老师的分布。（来源：[[论文/后训练/Better Supervision Is Nearby Neighborhood On-Policy Self-Distillation|Better Supervision Is Nearby: Neighb]]）
- 多老师潜在蒸馏的配方：先算师生各层 CKA 再决定对齐哪几层；同门老师对齐最后三层，跨家族只对最后一层；潜在监督用交叉淡出 α=min(1,u/Tw) 上升、β=max(0,1−u/Tw) 下降，同门 Tw=10、跨家族 Tw=7；多层损失先按层平均；一次参数更新只装一个领域的样本、三个领域轮流来；只存选中的三层状态。（来源：[[论文/后训练/Latent-MOPD Latent Multi-Teacher On-Policy Distillation|Latent-MOPD: Latent Multi-Teacher On]]）
- 代码智能体的组内质量打分表：只对通过的候选打分，按策略是否对路、改动是否精确、是否最小、有没有副作用、是否符合仓库风格五项加权，权重分别 0.30、0.25、0.20、0.15、0.10；分三档给折扣，最好档 1.0 和 0.9，中间档 0.85 到 0.4 线性铺开，最差档 0.2；重分配倍数上限取 1.5；只对既有通过又有失败的组做这件事，打分与生成异步重叠，打分结果不完整就退回原来的奖励。（来源：[[论文/后训练/Groupwise Agentic Grading and Advantage Redistribution for Code Agent RL|Groupwise Agentic Grading and Advant]]）
- 在线奖励分段配方：按一组题当前做对的比例分三段——做对少就补中间步骤分，做对一半只看最后成不成，几乎全对才压执行成本；同时给优势的分母加下限，防止高效率项被归一化抹平。（来源：[[论文/RSI/Qwen-Planner-Agent A Closed-Loop AI-for-AI Framework for Real-World Mobile Planner Agents|Qwen-Planner-Agent: A Closed-Loop AI]]）
- 多轮 on-policy 蒸馏的早停配方：用每回合老师平均 log 概率当在线 OOD 探针，阈值 λ 按任务域单独调；早停触发的那一回合保留进 loss 当负信号；前缀质量门槛取 α=-0.8；复用时只对新生成本回合算累积和；指标用 mean@16/pass@16。单轮任务没有回合概念时，临时把回合换成按 token 累积打分，并关掉 α 过滤。（来源：[[论文/后训练/Know When to Stop, Where to Restart Accelerating Multi-Turn Agentic On-Policy Distillation|Know When to Stop, Where to Restart:]]）
- 从生产轨迹批量建行为题：先用 CPU 锚点按工具报错、参数、事件顺序这类硬信号扫全量记录，只把少量候选交给便宜模型确认；按动作、失败、声明三类切点剪上下文；每题配 0 到 5 分评分表，平均至少 4 分才算过。（来源：[[论文/RSI/TraceDance An Automated System for Building Agent Behavior Benchmarks from Real-World Agen|TraceDance: An Automated System for ]]）
- 多智能体定性编码 harness：两个模型先各自独立打标，只对冲突案例辩论，再用讨论出的规则重打全量；每轮只放一个码、编码温度 0、讨论温度 0.7，用 Cohen's Kappa 看一致性、F1 看准确率；三轮没有共识就记为 disagreed；预处理先让模型只抽相关片段再编码。（来源：[[论文/其他/How AI Coders Discuss, Disagree, and Reach Consensus Challenges and Opportunities for LLM-|How AI Coders Discuss, Disagree, and]]）
- 脚手架自优化拆成五个可单独下手的槽位：系统提示词、记忆、内置工具、技能、MCP；改动都写成打补丁而不是重写整个程序；给脚手架设复杂度上限，只有比历史最好更好才留下。（来源：[[论文/RSI/MetaRSI RSI2 A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems T|MetaRSI / RSI2: A Meta-Recursive Sel]]）
- 终端智能体可以先让模型多写几条候选命令，再挑一条最靠谱的执行；在挑得准的前提下，同一个模型的终端任务成功率能明显上去。（来源：[[论文/Harness/Mid-Harness Scaling Actions Between Model and Harness for Terminal Agents|Mid-Harness: Scaling Actions Between]]）
- 往多轮对话里挂一个小参谋时，不要学所有建议，只保留那些真能改变最终结果的意见；用这些信号做定向多轮自蒸馏，在需要调工具的任务上比只按结果硬调更有效。（来源：[[论文/后训练/AdviSD Learning to Advise Frontier LLMs via Targeted Multi-Turn Self-Distillation|AdviSD: Learning to Advise Frontier ]]）
- DiffGate 配方：在 GRPO 优势上加 λ(1−p)^γ(1−R_i)·2tanh(Δ/2)；Δ 是老师与学生 log 概率差，R_i 是回答对错，p 是组内做对比例；λ 取 0.25–1、代码在 0.5 附近最好，γ 取 1–3 不敏感；同一批 16 条生成同时算 avg@8 和 pass@8。（来源：[[论文/后训练/DiffGate Difficulty-Gated Teacher Guidance for On-Policy Distillation|DiffGate: Difficulty-Gated Teacher G]]）
- DuoOPD 配方：每题先缓存并验证一份老师回答（温度 1、top-p=1、seed 42、1024 token），跨学生和 seed 复用；四种对错组合决定反馈力度，符号看学生自己的对错；老师单独答对时把参考塞进老师上下文，学生单独答对时整条回答共用任务内平均权重，并用 Softplus 保留非零反馈。（来源：[[论文/后训练/DuoOPD Learning from Joint Teacher-Student Outcomes for Multi-Task On-Policy Distillation|DuoOPD: Learning from Joint Teacher-]]）
- ReSAIL 配方：用同一模型有提示和无提示两种输入的 JSD 给每一步打分，只在冻结老师上算；按分数取 top-ρ，agent 逐步训练取 0.05，轨迹短、批小可到 0.25；损失先按轨迹内平均再按整批平均；保留项对看提示输出做 KL，λ 取 0.5。（来源：[[论文/RSI/ReSAIL Mitigating Collapse in Iterative Agent Self-Distillation|ReSAIL: Mitigating Collapse in Itera]]）
- Negative Self-Distillation 配方：用同一模型换反面提示生成反面老师；门控 max(0, π_neg−π_ref)，只罚被推高的词；封顶惩罚 G/(2−π_θ)；按 π_ref 加权的逐词 KL，α=0.01；MATH 训 2 个 epoch，batch 32、top-k 32、最长 4096，评测 Avg@8、温度 0.6、top-p 0.95。（来源：[[论文/后训练/Negative Self-Distillation Learning to Reason by Avoiding Flaws|Negative Self-Distillation: Learning]]）
- 负策略 rollout 配方：负模型选同家族、参数更小、整体更弱的档位，1.7B 学生配 0.6B 负模型；α 取 1.0 或 0.5；batch 256、lr 5e-6、100 步、rollout 上限 16k、采样温度 1.0；负模型答案预先生成并复用。（来源：[[论文/后训练/On-Policy Distillation with Negative-Policy Rollouts|On-Policy Distillation with Negative]]）
- HAD 配方：harness 做成任务无关的一小套，只往观察里加文字、不拦动作，包含可用动作清单、位置加背包、访问历史、步数预算、重复失败和卡住报警；偏好项只对动作 token 求平均对数似然，用学生自己的推理前缀打分；λ 每 minibatch 按梯度范数自动定，让偏好梯度约为蒸馏梯度的一半，β=0.5。（来源：[[论文/Harness/Harness-Aware Distillation for Small Language Model Agents|Harness-Aware Distillation for Small]]）
- ASCENT 配方：用冻结的初始模型当老师，把验证通过的完整轨迹当特权信息；用 forward KL 对齐整词表分布；用环境返回的能不能执行做免费过滤；LoRA 适配器跨任务累积，环境验证成功才更新；评测按单遍任务流，先打分再更新，同时报平均轮数。（来源：[[论文/后训练/ASCENT Online Test-Time Training of Long-Horizon Agents via Self-Distillation of Verified |ASCENT: Online Test-Time Training of]]）
- OPD Before RL 配方：第一阶段细则只放老师上下文，学生侧不出现；forward KL 只对齐老师 top-256，lr 1e-5、全局批 512、回答长度上限 1024–2048；第二阶段用 DAPO 式 GRPO，lr 1e-6、每题 8 条、actor KL 系数 0.001，并按训练与推理概率比过滤对不上的 rollout。（来源：[[论文/后训练/OPD Before RL Warm-Starting Rubric-Based RL with On-Policy Distillation|OPD Before RL: Warm-Starting Rubric-]]）
- 跨词表 OPD 配方：按两边 tokenizer 公共边界切出 1:1 组和跨 token 组；只在严格 1:1 位置把两边分布限制到共享词表上重新归一化并用反向 KL 训；训练时只保留学生自己挑的前 16 个共享词；配置为 100 轮、batch 512、lr 1e-6、温度 1.0、top-p 0.95。（来源：[[论文/后训练/Rethinking Cross-Tokenizer On-Policy Distillation From Alignment Coverage to Supervision R|Rethinking Cross-Tokenizer On-Policy]]）
- LER-OPD 配方：用 IER 做候选集近似后选 token，并和已有 usefulness 分数组合；训练目标仍保留采样得到的 reverse-KL，不做额外接口改动；优先报稀疏 0.1%–1% token 预算和全量 OPD 的对照。（来源：[[论文/后训练/1% of Tokens Can Be Enough On Gradient Estimation in On-Policy Distillation|1% of Tokens Can Be Enough: On Gradi]]）
- On-Policy Parameter Update Direction 配方：先跑 50 步 GRPO，用 sign(θ_on−θ_base) 取方向；SFT 时先按方向掩掉梯度，再在优化器更新后把跑反的参数拉回来；数据可用 DeepMath 难度 ≥6 的 57K 题，老师 Qwen3-30B-A3B 温度 0.6 采样，只用验证器判对的 44,810 条。（来源：[[论文/后训练/On-Policy Parameter Update Direction Underlies Generalization in LLM Post-Training|On-Policy Parameter Update Direction]]）
- Divergence controls entropy 配方：把学生平均熵和损失一起打日志；想发散用 forward KL，想保守用 reverse KL；自蒸馏可抄 λ=0.5 的广义 JS、老师用衰减 0.95 的指数移动平均、只算学生前 100 个词并把尾部合成一个桶；想让熵不随 k 变化就用重新归一化截断。（来源：[[论文/后训练/Divergence controls entropy in distillation|Divergence controls entropy in disti]]）
- RGPO 配方：把参考解按字符或 token 切成 N 段当前缀提示，做错就多露一段、做对就收回一段；引导回答只有严格高于本轮无提示最好分（δ=0）才收进辅助缓冲；监督只在原题上算；Qwen2.5-3B、batch 256、prompt 1024、response 4096、每题 8 条 rollout、lr 1e-6、FSDP2+bfloat16。（来源：[[论文/强化学习/Rationale-Guided Policy Optimization Learning to Reason with Adaptive Rationale Scaffoldin|Rationale-Guided Policy Optimization]]）
- X-Tree 配方：把动作按「动词+作用对象」规范化再统计相邻对子；合并判据用频率×长度×成功率，频率至少 4 次、环境内技能上限 80–256 条、最小成功率过滤；训练时把树上节点当一道题，前面用金标准动作接续，按长度给部分匹配奖励，节点越深加成越大，λ0=0.75。（来源：[[论文/强化学习/X-Tree Tokenizing Reusable Experience for Efficient Agent Generalization|X-Tree: Tokenizing Reusable Experien]]）
- Environments as Scaffold 配方：把环境反馈定义成对观测空间的一次干预，训练时以 0.5 概率注入；200 步训练，第 100 步从动作提示切到观测补充；每 5 步在标准环境上评一次，评测题和训练题严格不重叠；同时盯策略熵、按难度分层的 avg@8，并用选择题探针检查提示有没有被写进权重。（来源：[[论文/强化学习/Environments as Scaffold Enriching Feedback to Bootstrap Self-Evolving Agents in Long-Hori|Environments as Scaffold: Enriching ]]）
- Harness Learning 配方：proposer 输入任务描述、当前 harness 代码、执行报告，输出结构化编辑；推理任务保留候选的条件是开发集分数变高，QA 是抽 8 个、跑不起来的记零分、取最高分那个；开发集 25 题、留出 75 题，反馈题、打分题、评测题分开放；给能解析、能执行加额外奖励。（来源：[[论文/Harness/Harness Learning Enables Generalizable Test-Time Adaptation|Harness Learning Enables Generalizab]]）
- Questioning the Questions 配方：把判题能力做成答题模型的一次中间训练，用「把好题误判成坏题」来罚，数据从五轮自我进化的题去重后每轮抽 460 条；出题奖励写成坏题直接扣分、好题才拿难度分；去重时每题只抽 K=8 个同批题两两比，K=16 反而掉分。（来源：[[论文/RSI/Questioning the Questions Sustaining Self-Evolution in Reasoning Models|Questioning the Questions: Sustainin]]）
- Skill2Env 配方：先爬取 Agent Skills，再 Create、Verify、Testing & Filtering；每条任务做静态检查、oracle must pass、NOP must fail、Pinned bare image、Diversify 采样与关键词注入；最终输出 Harbor Task Format with Rubrics，目录含 instruction.md、container、data。（来源：[[论文/强化学习/Skill2Env|Skill2Env]]）
- Rubrics as Rewards 配方：先写标准答案，再拆成三到五条能判定对错的检查项；必须做到的 5 分，重要的 4–3 分，可选的 2 分；同一份清单既当训练奖励，也当人工或模型评审的评分表。（来源：[[论文/后训练/Rubrics as Rewards (RaR)|Rubrics as Rewards (RaR)]]）
- Rubric Rewards from Item Response Theory 配方：用题目和规则原文训一个网络预测每条规则的难度与区分度；奖励用全量对错表的最大后验估计 + 高斯先验 + 高斯累积分布，再二分求最大值；选规则时按 Fisher 信息排序，每问完一条就更新水平估计；部署侧额外算力约原步骤 0.123%。（来源：[[论文/强化学习/Rubric Rewards from Item Response Theory|Rubric Rewards from Item Response Th]]）
- BiasReducer 配方：只改最后一层线性打分权重，其他参数全冻住；沿「分数与属性激活的协方差方向」减掉 λ 倍投影，λ 在源验证集上卡住偏好准确率跌幅；属性表用长度、啰嗦、格式、表情、自信、含糊、讨好用户七项；新数据只要 100–200 条就能选出和全量基本一致的修法。（来源：[[论文/后训练/BiasReducer Adaptive Bias Mitigation for Reward Models|BiasReducer: Adaptive Bias Mitigatio]]）
- Bellman Policy Optimization 配方：权重写成 (1+ε−μ)/(1+ε−π)，只看被采样那一个 token 的概率，ε=0.1、权重封顶 C=3.0；该题平均得分 V 直接用组内 16 条奖励的均值估计，配合同组内算出的 Â 归一化；主线设置 256 prompt×16 回答、最长 16384、每次 rollout 后 8 次 minibatch 更新、400 步、不要 KL 惩罚、熵系数 0、恒定学习率 1e-6。（来源：[[论文/强化学习/Bellman Policy Optimization|Bellman Policy Optimization]]）
- On KL-Regularized Policy Optimization 配方：把 KL 项锚到真正采样数据的策略上；对 log-ratio 最优性条件做最小二乘，回归截距单独消掉，换成采样端均值加采样到训练的 KL；工程上每题只跑一条 rollout，不要 critic、不要组内基线。（来源：[[论文/强化学习/On KL-Regularized Policy Optimization|On KL-Regularized Policy Optimizatio]]）
- EasyPPO 配方：critic 保留截断样本、只对 actor 做超长过滤；按同题一组 rollout 的得分标准差做逆权归一化，权重批内归一为均值 1；离散奖励用 ε=Δ/(2√n) 兜底；critic 一批拆成 4 个小批，每个小批算完梯度裁剪一次再更新，换小批量时按 η∝1/√K 调学习率。（来源：[[论文/强化学习/EasyPPO Stabilizing the Critic Is Key|EasyPPO: Stabilizing the Critic Is K]]）
- Trust the Critic More 配方：动作块取 1 万 token、每组 16 条；被判为可信的题仍有 1/4 概率跑完整条审计；critic 不另接打分头，而用策略模型加提示输出 0 到 1 的离散分数；可信度判据为最近五步平均误差低于全局阈值、上一步单题误差低于更严局部阈值、且该题至少出过一次正确答案。（来源：[[论文/强化学习/Trust the Critic More|Trust the Critic More]]）
- Never Give Up 配方：每题先只采 K=4，全对就丢，全错按 p=0.95 继续采到做对；做对后把最近 4 步内的历史答案并成一个大 GRPO 组算优势；用 n+/n-(1-r̄) 重缩放负面答案优势，保证一组优势和为零；前提是异步 RL。（来源：[[论文/强化学习/Learning to Solve Hard Problems in RL for LLMs by Never Giving Up|Learning to Solve Hard Problems in R]]）
- SAGE 配方：用投影到算子子空间的能量占比 ||P_Sj r||²/||r||² 当软打分，只在训练时偏置采样、推理时不剪枝；用 Poincaré 双曲嵌入到目标结构的距离做密集结构奖励；结构分只加进 advantage（R̃=终点奖励+η·平均 Ψ），推理时不加开销；AC 数据用 1190 个 n≤7、|w|≤7 的 presentation。（来源：[[论文/推理/SAGE Mitigating Long-Horizon Reasoning Biases via Topological Guidance|SAGE: Mitigating Long-Horizon Reason]]）
- The Missing Primitive 配方：把「找思路」和「解题」拆成两场分开的考试，用「给了思路能不能救回失败题」判断短板；老师额外信息从整篇参考解答换成一句结构化关键思路；用只夹住一边的 reverse KL 训练，减少把学生既有想法推歪。（来源：[[论文/推理/The Missing Primitive Diagnosing and Repairing Mathematical Reasoning in Large Language Mo|The Missing Primitive: Diagnosing an]]）
- 引用链深度配方：每行一个赋值，名字和名词随机换，按层或交错排列，用「可靠跟到第几行」当指标；LoRA 用 rank-8、1200 步、AdamW、学习率 1e-3、批 16，再加 KL 项拉住原分布；放置上先量冻结模型的截止层，再只在附近试一两层。（来源：[[论文/推理/Transformers Stop Thinking Too Early, and a Tiny LoRA Fixes It|Transformers Stop Thinking Too Early]]）
- SCALE 配方：第一阶段按标准 SFT 训 LoRA，rank 16、alpha 16、无 dropout、覆盖全部线性层、1 个 epoch、总 batch 128、AdamW，数学 lr 5e-4、代码 lr 5e-5、cosine 加 10% warmup；第二阶段冻住基座和适配器，只学每个模块一个线性门 w·h+b，目标只用响应位置 top-100 预测熵；门控写成 λ=1+(1−L)·min(v,0)+(U−1)·max(v,0)，v=tanh(g/τ)。（来源：[[论文/后训练/Rethinking Token Reweighting for SFT Suppress, Reverse, and Extrapolate Learned Features|Rethinking Token Reweighting for SFT]]）
- Pivot-SD 配方：信息增益打分 g(t) 用「这一步造成的剩余掩码位平均熵降幅」；按步排序取前 K=10，排除块边界步和结尾符；把部分掩码状态 M_t、位置 p、写入的 y_p、轨迹对错缓存成离线数据；λ_neg 按正负轨迹比例定，MATH 取 1、GSM8K 取 5，代码降到 0.02。（来源：[[论文/后训练/Pivot-SD Efficient Self-Distillation for Masked Diffusion Language Models|Pivot-SD: Efficient Self-Distillatio]]）
- 国际象棋专家编码器配方：把 Leela 编码器用交叉注意力接进语言模型，只训练中间连接层；先上四步课程（静态当前→动态当前→静态未来→动态未来），每步回放少量旧数据防遗忘；加 64 个格子 token 和 12 个棋子 token；用搜索展开孩子局面、合并成解释再蒸馏回去自改进。（来源：[[论文/推理/Language Models that Play Chess and Explain Their Moves|Language Models that Play Chess and ]]）
- Workspace Models 配方：用 DETR 式集合重建损失，解码器出 m 个槽位，用匈牙利匹配对齐到数量可变的关键图像块，再算特征重建加占用交叉熵；标注用 Qwen3-VL 逐帧判断事件、滑动窗口去重，MolmoPoint 给持续跟踪物体和关键帧物体坐标，再映射成 DINO 图像块；评测把失败拆成记忆错和控制错两类。（来源：[[论文/机器人/Workspace Models Lightweight Robotic Memory via Saliency-Driven Supervision|Workspace Models: Lightweight Roboti]]）
- 参数化记忆综述给出的定位法：用「写在哪一层 × 什么时候写」两张标签给每篇记忆论文定位；三道筛选门槛为是不是参数、有没有独立写入动作、部署时会不会插入前向计算；要按内容检索就放注意力层，要改具体事实就放 FFN，最省事放输入层。（来源：[[论文/记忆/Towards In-Parameter Memory Augmentation for Large Language Models|Towards In-Parameter Memory Augmenta]]）
## 评测与验证
- 把轮数当成给模型的预算来评测，按轮数扫一条曲线看什么时候不再涨：AREX-2 在 Frontier-CS 上一小时 54.4、五小时 70.7，最后两小时还涨 4.8 分。（来源：[[论文/RSI/AREX-2 Advancing Self-Improving Agents through Long-Horizon Reflective Tasks|AREX-2: Advancing Self-Improving Age]]）
- 要验证没有外部判分时模型能不能自己重评，就在完全不给对错提示的设置下测：AREX-2 在 BrowseComp 上把轮数从 47 加到 143，准确率从 64.8 涨到 84.0。（来源：[[论文/RSI/AREX-2 Advancing Self-Improving Agents through Long-Horizon Reflective Tasks|AREX-2: Advancing Self-Improving Age]]）
- 蒸馏评测同时报 Avg@16 和 Pass@16，并把 Pass@k 拉到 64，否则看不出解法覆盖的变化：去掉熵奖励后 Pass@16 平均掉 1.95 分，Avg@16 只掉 0.46 分。（来源：[[论文/后训练/An RL View of OPD Least Square Policy Distillation for Sample-Efficient LLM Reasoning|An RL View of OPD: Least Square Poli]]）
- 加速类方法要按域分别报分、别只挑赢的说：零售上 3.73 倍速到 0.475 追平全量蒸馏 0.477，但电信域最快只到 0.849，仍低于基线 0.853；速度按纯训练每步时间算，端到端还要扣掉评测开销。（来源：[[论文/后训练/Know When to Stop, Where to Restart Accelerating Multi-Turn Agentic On-Policy Distillation|Know When to Stop, Where to Restart:]]）
- 测行为合规要用两步：先用自动题跑大样本通过率，再用「同一道题上不同模型第一步选择不同」来归因。参考水位：九个前沿模型平均只有 26.7% 过关，「先检查再动手」类只有 8.1%，而「工具调用格式正确」有 67.9%，说明模型会写格式却常跳过动手前的检查。（来源：[[论文/RSI/TraceDance An Automated System for Building Agent Behavior Benchmarks from Real-World Agen|TraceDance: An Automated System for ]]）
- 自动造的题要抽检有效性：随机抽 100 道让两人独立检查，只有 84 道确认原记录真出现了目标坏行为；评分表质量 4 分以上的占 90%、平均 4.75 分。约 16% 的题底子不干净，不能直接全信。（来源：[[论文/RSI/TraceDance An Automated System for Building Agent Behavior Benchmarks from Real-World Agen|TraceDance: An Automated System for ]]）
- 跨基准的分数不能横着摆：HLE 带星号的是全量集、不带的是纯文本子集；Avg@16 与 pass@1 不能比；BFCL 无权重平均和电商结余也不是同一协议。报告时把配置和口径一起写清。（来源：[[论文/RSI/AREX-2 Advancing Self-Improving Agents through Long-Horizon Reflective Tasks|AREX-2: Advancing Self-Improving Age]] · [[论文/其他/PACT From Credit Assignment to Critic Alignment|PACT: From Credit Assignment to Crit]] · [[论文/其他/Verifiable Hidden Dynamics Play Generating Agentic RL Environments from Solved Mechanisms|Verifiable Hidden Dynamics Play: Gen]]）
- 两组可照抄的评测口径：数学用 Avg@16，代码用 SWE-bench Verified pass@1；报结果时至少给多个种子或标准差，主曲线不要只做单次报告。邻近老师那篇每个尺度跑三次并给标准差，是值得照搬的做法。（来源：[[论文/其他/PACT From Credit Assignment to Critic Alignment|PACT: From Credit Assignment to Crit]] · [[论文/后训练/Better Supervision Is Nearby Neighborhood On-Policy Self-Distillation|Better Supervision Is Nearby: Neighb]]）
- 验证 OPD 与 GRPO 结合时，同一批 16 条生成同时算 avg@8 和 pass@8（温度 0.6、重复惩罚 1.15、最长 16384），并盯全错组占比、判错轨迹上的师生词差、梯度范数和策略熵；DiffGate 主要提升 pass@8，数学 avg@8 反而略低 0.3–0.5 分，不能读成更会做数学题。（来源：[[论文/后训练/DiffGate Difficulty-Gated Teacher Guidance for On-Policy Distillation|DiffGate: Difficulty-Gated Teacher G]]）
- 多任务 OPD 主表用 avg@8、开发曲线用 avg@4；各方法三次训练标准差 0.26–1.37，不能把不同师生对的绝对分横着比；同时报学生正确回答是否被旧蒸馏压下去的对数比。（来源：[[论文/后训练/DuoOPD Learning from Joint Teacher-Student Outcomes for Multi-Task On-Policy Distillation|DuoOPD: Learning from Joint Teacher-]]）
- 测逐轮自蒸馏有没有让「老师那一面」退化：固定任务和固定提示，只换 checkpoint 测带提示成功率；ReSAIL 的保留项要把看提示输出对齐冻结老师上，第三周期平均高出 22.5 个百分点。（来源：[[论文/RSI/ReSAIL Mitigating Collapse in Iterative Agent Self-Distillation|ReSAIL: Mitigating Collapse in Itera]]）
- 蒸馏评测的稳健口径：同分布 pass@1 + 七项 OOD 平均分 + 参数变化小于 1e-6 的占比；学习率从 1e-5 提到 5e-5 时 OOD 最多掉 11–14 分、更新稀疏度从 85%–90% 降到 52%–60%。（来源：[[论文/后训练/On-Policy or Off-Policy Learning A Systematic Study of Distillation Dynamics|On-Policy or Off-Policy Learning? A ]]）
- 把精化税和 pass@1 一起报：精化税是同一预算下基础模型和后训练模型「多试几次能多解多少」的差值；先用 K=8、一半任务估算，成本很低；14 组模型对乘 3 个基准共 42 个组合，36 个在 128 次预算下税为正。（来源：[[论文/后训练/Sharpening Tax in Post-Training|Sharpening Tax in Post-Training]]）
- RL 覆盖率评测用 pass@1 加 pass@1024，并监控解法路线数；解法路线测量可照抄 6 个基准共 240 题、每题两个模型各 16 条回答、用 LLM 抽取路线描述后归组、按可识别回答数取等量样本再平均。（来源：[[论文/强化学习/How RL Reshapes LLM Reasoning Transferability, Coverage, and Scaling Laws|How RL Reshapes LLM Reasoning: Trans]]）
- 稀疏 OPD 选 token 的实验要同时报稀疏和全量 OPD 的分数、token 预算与选择器消融；只报最终分数看不出是 usefulness 还是梯度估计可靠性在起作用。（来源：[[论文/后训练/1% of Tokens Can Be Enough On Gradient Estimation in On-Policy Distillation|1% of Tokens Can Be Enough: On Gradi]]）
- 跨词表蒸馏诊断用梯度余弦加范数比，并把严格位置随机分两半当对照；补出来的片段和严格损失方向几乎不重合甚至相反，一致性低于随机对照，且相对大小越练越大。（来源：[[论文/后训练/Rethinking Cross-Tokenizer On-Policy Distillation From Alignment Coverage to Supervision R|Rethinking Cross-Tokenizer On-Policy]]）
- 奖励模型纠偏评测要分开口径：表 1 是成对偏好准确率，表 2 是另一个模型打的质量分和长度统计，不能混比；Arena 原始分只有 32.8%，涨 18 个点有底分低的水分。（来源：[[论文/后训练/BiasReducer Adaptive Bias Mitigation for Reward Models|BiasReducer: Adaptive Bias Mitigatio]]）
- 评分规则选择评测可照搬留一规则的 ROC-AUC，以及「与全问优势值相关到 95% 时最少要问几条」；只问一半规则时平均分只比全问低 0.1 分，裁判耗时少 49%。（来源：[[论文/强化学习/Rubric Rewards from Item Response Theory|Rubric Rewards from Item Response Th]]）
- 有序评分任务除准确率外要报「相对金标的有效档位使用率 R」和 TVD；每道题多跑几个随机候选顺序；用同一批题、同一套分数做档数从 2 到 14 的加密测试，并让金标和正确选项位置都均衡。（来源：[[论文/评测/More Choices, Fewer Decisions Ordinal-Scale Bias in JEV-like Direct-Decision Models|More Choices, Fewer Decisions: Ordin]]）
- 智能体评测完整性检查用 I1–I7 七类：I1–I6 管权限，I7 管交的东西是否真答对题；任务绑定字段分资源、网络、交接点、语义义务；判定用 Checked、VectorExposed、AgentViolation、Inconclusive 四态；证据包把动作、生命周期事件、产物和奖励来源封在一起可离线重放。（来源：[[论文/智能体安全/BenchShield Formal Model-Backed Instrumentation for Reward Integrity in LLM-Agent Evaluati|BenchShield: Formal Model-Backed Ins]]）
- 机器人记忆评测要同时报延迟和成功率：关键帧每步 302 毫秒、普通策略 49.2 毫秒；四个记忆任务平均成功率 workspace 91.5%、关键帧 66.8%；失败拆成记忆错和控制错两类，真机样本量要交代。（来源：[[论文/机器人/Workspace Models Lightweight Robotic Memory via Saliency-Driven Supervision|Workspace Models: Lightweight Roboti]]）
- CVaR 策略评估的预算分配要单独设计：先用均匀小样本给每个核拟合条件分布，再按尾部影响尺度分配剩余预算，并保留约 N 的负四分之一次方均匀下限、每组至少两次主采样；尾部影响份额与均值影响份额的总变差距离约 ≥0.21 时用锚定 TIS。（来源：[[论文/强化学习/Tail-Influence Sampling for CVaR Policy Evaluation|Tail-Influence Sampling for CVaR Pol]]）
- 最小 witness 任务评测不能只看找到几个答案，要报组内覆盖和多余答案是否得零分：论文里按覆盖给分能找回 12.1 个最小答案，单独按对错只找到 1.3 个，按长度惩罚只找到 1 个。（来源：[[论文/强化学习/Minimal Witness Reinforcement Learning|Minimal Witness Reinforcement Learni]]）
- CoT 可解释性评测用 CIA：把 CoT 里是否出现目标策略和探针是否读到目标策略各记 0/1，再算宏 F1，并保留「忠实但答错」的 (0,0) 格；后训练用答对分加 1 倍一致分，27 个模型任务组合里 25 个一致性上升，答对率掉幅不超过 1.5 个百分点。（来源：[[论文/推理/Making LLMs Say What They Think Measuring and Improving CoT-Interpretability Alignment|Making LLMs Say What They Think: Mea]]）
- 长链推理和数学诊断要分开报「找思路」和「解题」两场考试：Qwen3.6-27B 与 gpt-5.4-mini 直接解题接近（52.75 对 50.55），自己找思路却差 34 个百分点；解题失败里 83.6% 发生在想不出思路时。（来源：[[论文/推理/The Missing Primitive Diagnosing and Repairing Mathematical Reasoning in Large Language Mo|The Missing Primitive: Diagnosing an]]）
- RL 难易诊断要按模型适应 prompt/harness 后的难度分桶，而不是只看初始难度；Manufactoria 上按初始难度看不出马太效应，先用模型跑 100 步适应 prompt 之后再评就出现了。（来源：[[论文/强化学习/Learning to Solve Hard Problems in RL for LLMs by Never Giving Up|Learning to Solve Hard Problems in R]]）
- PPO critic 诊断盯两个指标：裁剪前的 critic 梯度范数和值预测的解释方差；EasyPPO 在 FrontierCS 上不加噪声归一化时拆 4 批会崩，拆 1 批还能自己缓过来。（来源：[[论文/强化学习/EasyPPO Stabilizing the Critic Is Key|EasyPPO: Stabilizing the Critic Is K]]）
- 前缀 critic 评测要把打分员误差和真实平均得分分开看：AC2 第 80 步 256 个前缀上，直接猜前缀分数误差 0.211，对同题 16 条续写终点值取平均误差只有 0.065。（来源：[[论文/强化学习/Trust the Critic More|Trust the Critic More]]）
## 成本与预算
- 先解标准答案再生成环境很便宜：3,300 个有状态环境每个只花一两美分，环境动态和评分来自同一份解。（来源：[[论文/其他/Verifiable Hidden Dynamics Play Generating Agentic RL Environments from Solved Mechanisms|Verifiable Hidden Dynamics Play: Gen]]）
- 代码 RL 的打分成本可以这样压：用 Claude Opus 5 打分每组约 2,000 秒，换成自己 SFT 训过的 MiMo 打分模型降到约 600 秒，再把打分和 rollout 生成错峰。注意这只算了打分本身，不等于端到端训练成本。（来源：[[论文/后训练/Groupwise Agentic Grading and Advantage Redistribution for Code Agent RL|Groupwise Agentic Grading and Advant]]）
- 读时整理记忆的 token 账单：JitMem-base 只比不加记忆多约 1.9K 输入 token，ReasoningBank 多 10.7K、SkillOS-base 多 13.4K；训练后输入 token 再省约 10%、输出 token 省 13%、步数省 12%。多出来的那次整理调用没算进 token 统计，做预算时要单独加上。（来源：[[论文/其他/Just-in-Time Memory Learning to Curate Task-Adaptive Memory for LLM Agents|Just-in-Time Memory: Learning to Cur]]）
- 复用旧轨迹能把采样步数压下来：同一批轨迹只更 1 次，AIME24/25 要 50 步以上才到顶；每批更 4 次以上约 30 步到顶；把旧轨迹放进回放池反复抽着学，10 步就到顶，而基线要 40 步以上。注意 10 步和 40 步不是同预算对照。（来源：[[论文/后训练/An RL View of OPD Least Square Policy Distillation for Sample-Efficient LLM Reasoning|An RL View of OPD: Least Square Poli]]）
- 潜在监督的显存要按层裁剪：只存选中的三层状态，在 16,384 个位置下占用从 2.63 GiB 降到 0.28 GiB；若一层不裁，多老师场景很容易先撞显存墙。（来源：[[论文/后训练/Latent-MOPD Latent Multi-Teacher On-Policy Distillation|Latent-MOPD: Latent Multi-Teacher On]]）
- 邻近老师方案的额外训练开销约为 OPSD+SCGate 的 1.42 倍；每个模型尺度都要重新校准噪声半径，偏离 σ=0.002 就会明显掉分，调参成本要算进预算。（来源：[[论文/后训练/Better Supervision Is Nearby Neighborhood On-Policy Self-Distillation|Better Supervision Is Nearby: Neighb]]）
- 行为题生成的检索成本可用粗筛压下去：每条成功查询要扫 12.8 万条会话，只让大模型确认 706 个候选，整条流程平均 552 次调用；不先做 CPU 锚点粗筛就得把全部会话送给大模型。（来源：[[论文/RSI/TraceDance An Automated System for Building Agent Behavior Benchmarks from Real-World Agen|TraceDance: An Automated System for ]]）
- 跨 harness 重写会把数据量放大：2,001 条成功轨迹经过 runbook 重写和新沙箱重跑变成 11,094 条可用轨迹。数据变多本身也是收益来源，做预算和归因时要把它和「重写」分开。（来源：[[论文/RSI/Scaling Trajectories for Complex Tasks through Recursive Self-Rewrite|Scaling Trajectories for Complex Tas]]）
- 多轮蒸馏的加速倍率要按纯训练每步时间算：零售 3.73 倍、4.51 倍，单轮数学 5.10 倍、3.08 倍；加上评测后的端到端收益会更小。（来源：[[论文/后训练/Know When to Stop, Where to Restart Accelerating Multi-Turn Agentic On-Policy Distillation|Know When to Stop, Where to Restart:]]）
- DuoOPD 的老师参考答案要缓存并复用：成本占一次 OPD 循环的 30%（Qwen）或 23%（Llama），摊到 3 次运行降到 +9.2%/+15%；训练时只有 13%–23% 的回答要带参考重打分。（来源：[[论文/后训练/DuoOPD Learning from Joint Teacher-Student Outcomes for Multi-Task On-Policy Distillation|DuoOPD: Learning from Joint Teacher-]]）
- 负策略蒸馏的负模型答案预先生成并复用后，Qwen3-1.7B 思考模式训练时间从 9 小时 19 分降到 3 小时 34 分；反面例子必须真弱，且这套做法不改奖励公式，能叠在 ExOPD、OPD² 等奖励上。（来源：[[论文/后训练/On-Policy Distillation with Negative-Policy Rollouts|On-Policy Distillation with Negative]]）
- harness 学习的隐藏成本是每改一轮都要把 harness 在开发题上重跑；论文留下 25 题开发集、75 题留出集，并把反馈题、打分题、评测题分开，做预算时要单独加上这轮重跑和重打分。（来源：[[论文/Harness/Harness Learning Enables Generalizable Test-Time Adaptation|Harness Learning Enables Generalizab]]）
- PivotOPD 的恢复训练依赖环境能重放：先前动作得在副本里一模一样跑一遍，读网页、调真实接口这类任务不一定做得到；立项时要把环境可重放性当硬前提。（来源：[[论文/后训练/PivotOPD Learning to Recover from Pivotal Mistakes in Multi-Turn Agents|PivotOPD: Learning to Recover from P]]）
- Sherpa 的成本结构是 1.7B 冻结学生加同族 Qwen3-8B 判对错和闸门；真人实验只比讲解哪版好，没测真人学生是否学得更好，别把 79.6% 的讲解胜率当成真人学习收益。（来源：[[论文/强化学习/Sherpa Teaching LLMs to Teach Adaptively|Sherpa: Teaching LLMs to Teach Adapt]]）
- Rubric Rewards from Item Response Theory 部署侧不增加参数量，额外算力约原步骤的 0.123%；预热预测难度与区分度的网络要 0.89–7.64 GPU 小时。（来源：[[论文/强化学习/Rubric Rewards from Item Response Theory|Rubric Rewards from Item Response Th]]）
- BiasReducer 在新目标分布上只需 100–200 条样本，就能选出和全量基本一致的修法；但它依赖能看见这批数据的回答、只是不知道哪个更好，真上线看不到目标分布时不能直接套。（来源：[[论文/后训练/BiasReducer Adaptive Bias Mitigation for Reward Models|BiasReducer: Adaptive Bias Mitigatio]]）
- OPD Before RL 多出来的老师推理开销没有被系统计入；立项时要把第一阶段老师逐词蒸馏的推理成本和第二阶段 rubric 判分成本分开预算。（来源：[[论文/后训练/OPD Before RL Warm-Starting Rubric-Based RL with On-Policy Distillation|OPD Before RL: Warm-Starting Rubric-]]）
- Skill2Env 的落地门槛是 Linux 主机能跑 Docker（docker info 可用）、Python 3.12+，以及容器内 Codex agent 要用的 ~/.codex/auth.json；生成任务后还要付静态检查、oracle 跑通和 NOP 失败验证的成本。（来源：[[论文/强化学习/Skill2Env|Skill2Env]]）
- 在线 RL 五件套的成本大头在环境和 verifier：每个任务要配可复原 sandbox，verifier 反馈要单独记成奖励来源，尽可能多存 rollout 轨迹；评测还要按 OCR、元素定位、界面语义理解三类拆开算分。（来源：[[论文/强化学习/Online RL Task + Environment + Verifier + Rollout + Reward|Online RL: Task + Environment + Veri]]）
## 开放问题
- 「长时反思是跨领域元技能」还只是假设，没有只在单一领域训练的对照；MLE-Lite 的成绩依赖把技能塞进上下文，但技能怎么写、写多少没交代；主曲线是单次报告没方差；HLE 各家评测集不一致；也没和强化学习类后训练在同一设置下比过。（来源：[[论文/RSI/AREX-2 Advancing Self-Improving Agents through Long-Horizon Reflective Tasks|AREX-2: Advancing Self-Improving Age]]）
- MetaRSI 抓到的材料只到方法一节，实验、消融和讨论都没有，只能判断框架设计，判断不了是否真跑赢基线；数据算子的认证靠同一个模型盲解比对，只能说前后自洽；五级台阶和普查口径由作者自己划定。（来源：[[论文/RSI/MetaRSI RSI2 A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems T|MetaRSI / RSI2: A Meta-Recursive Sel]]）
- LastOPD 的 10 步窗口是用 MATH-500 选的，而 MATH-500 又当主指标报告，等于拿一部分测试信号调参；同血缘那组过渡反而更差（83.42 对 87.22），说明固定 10 步不是所有情况最优。（来源：[[论文/后训练/LastOPD Taming Collapse in Latent On-Policy Distillation|LastOPD: Taming Collapse in Latent O]]）
- 所谓「跨家族」的多老师其实都是 Qwen 骨架、都是 28 层，只是规模和后训练不同，真正的异构架构没试；学生只做了 1.5B 一档；全程只有蒸馏、没有 verifier 奖励，也没和 RL 混着跑；结果只取第 62 步快照，没报不同 checkpoint 的波动。（来源：[[论文/后训练/Latent-MOPD Latent Multi-Teacher On-Policy Distillation|Latent-MOPD: Latent Multi-Teacher On]]）
- STRIDE 只在 τ²-bench 的零售/电信两域和 Qwen3 系列上验证，长轨迹上方法会退化（电信域始终没超过基线）；数学实验里单轮没有回合概念，是临时把回合换成 token 且要关掉过滤。（来源：[[论文/后训练/Know When to Stop, Where to Restart Accelerating Multi-Turn Agentic On-Policy Distillation|Know When to Stop, Where to Restart:]]）
- LSPD 的验证面偏窄：只用 Qwen3 家族、只做数学推理、老师还是非思考模式；理论上被证明的是理想乐观版本，实际跑的 Huber 截断加熵项那版没有保证；AIME24/25 的 Pass@1 上 LSPD 还低于 KD 和 OPD，它换到的是多采样覆盖而不是单次更准。（来源：[[论文/后训练/An RL View of OPD Least Square Policy Distillation for Sample-Efficient LLM Reasoning|An RL View of OPD: Least Square Poli]]）
- 「吵得越凶越准」很可能是因为难案例本来讨论就更久，不是争吵本身导致变准；统计关系不能直接当因果；实验只试了 gpt-4o-mini、四个英文数据集和每库五个标签，换模型/语言/码本规模未必成立。（来源：[[论文/其他/How AI Coders Discuss, Disagree, and Reach Consensus Challenges and Opportunities for LLM-|How AI Coders Discuss, Disagree, and]]）
- JitMem 在 τ²-bench 没有标准训练集，只试了不训练版本，多轮工具对话能不能靠 RL 训出来没验证；入库用执行者自己当裁判判成败，可能把错的当对的收进去；BM25 在更大库里会不会拖后腿也没测。（来源：[[论文/其他/Just-in-Time Memory Learning to Curate Task-Adaptive Memory for LLM Agents|Just-in-Time Memory: Learning to Cur]]）
- Gagar 的打分器是受训模型同家族的 SFT 版本，等于自己评自己的近亲，论文没给打分器和人类判断的一致率；质量评估只有 30 道题、一个评审模型；折扣系数、三档阈值、1.5 的倍数上限都是手调，没有敏感性分析，也只验证了代码任务。（来源：[[论文/后训练/Groupwise Agentic Grading and Advantage Redistribution for Code Agent RL|Groupwise Agentic Grading and Advant]]）
- 跨 harness 重写全程只试了一个 27B 模型，基准多半是自己造的：TB2 只有 89 道题、TB3/TB4 只有 74/66 道，SWR100 上 3%→6% 其实是多对 3 道题，LHTB 三组都是 0/46；同一个 runbook 还有的跑通有的跑挂。（来源：[[论文/RSI/Scaling Trajectories for Complex Tasks through Recursive Self-Rewrite|Scaling Trajectories for Complex Tas]]）
- 多老师梯度分析的主实验只有 Qwen3-1.7B 加四个同源 RL 老师，作者承认模型族和规模有限；「SGD 比 Adam 好」的优势只有 0.3–1.0 分、只跑 500 步一套配方；文中极端长度差引自别的工作，往更长回答外推要谨慎。（来源：[[论文/后训练/From Gradients to Capabilities Understanding Multi-Teacher On-Policy Distillation|From Gradients to Capabilities: Unde]]）
- 扩散式文字模型的微调结论目前只有摘要级证据：没有数字、没写清全量还是 LoRA、数据量和题量，来源还是指向个人博客的截图；「改成按结果好坏来教」是未验证的主张，要用得先补原始博客或论文正文。（来源：[[论文/后训练/Fine-Tuning DiffusionGemma What Works, What Breaks|Fine-Tuning DiffusionGemma: What Wor]]）
- Qwen-Planner-Agent 的材料里没有实验表，只有「总分最高」「成本更低」这类说法，27B 具体和哪些模型比、成本怎么估都不清楚；人工把关具体审什么、大模型控制器调阈值是否比固定阈值更好，正文也没交代。（来源：[[论文/RSI/Qwen-Planner-Agent A Closed-Loop AI-for-AI Framework for Real-World Mobile Planner Agents|Qwen-Planner-Agent: A Closed-Loop AI]]）
- Harness Learning 只在 solver 冻结、单一 35B 老师、奖励只看单次改动的设置下验证，没有跨轮信用分配；推理任务里反馈和打分还用同一批开发题，存在选择偏差，solver 随机性也会让分数抖。（来源：[[论文/Harness/Harness Learning Enables Generalizable Test-Time Adaptation|Harness Learning Enables Generalizab]]）
- HAD 只在 ALFWorld、WebShop、ScienceWorld 这类文本环境验证，学生不超过 2B、老师不超过 30B，工具调用和软件智能体还没试；harness 是手写的，自动学出来的 harness 是否一样有效不清楚。（来源：[[论文/Harness/Harness-Aware Distillation for Small Language Model Agents|Harness-Aware Distillation for Small]]）
- Questioning the Questions 的成立性、同类型判定、修题和参考答案都用 GPT-5.6-Sol 生成，标签本身可能带偏差；K=8、九条回答多数投票这些超参只在小模型上试过，换任务要重调。（来源：[[论文/RSI/Questioning the Questions Sustaining Self-Evolution in Reasoning Models|Questioning the Questions: Sustainin]]）
- ReSAIL 只跑了 Qwen3-4B/8B、三个基准、三个周期、每周期 30 次更新；选步比例和保留权重直接看测试集挑，没有验证集；完整方法多花约 23% 训练时间。（来源：[[论文/RSI/ReSAIL Mitigating Collapse in Iterative Agent Self-Distillation|ReSAIL: Mitigating Collapse in Itera]]）
- IER 稀疏 OPD 的材料只到摘要和引言 OCR，数学与医学以外的任务、不同师生对、不同 token 预算下的稳定性都还需要原文实验确认。（来源：[[论文/后训练/1% of Tokens Can Be Enough On Gradient Estimation in On-Policy Distillation|1% of Tokens Can Be Enough: On Gradi]]）
- ASCENT 只用开权重模型，闭源 API 拿不到整词表分布；验证只有回合末 0/1，所有轮同等权重，没有逐轮信用；过滤和观测内容的最优选择在 4B 与 9B 上相反。（来源：[[论文/后训练/ASCENT Online Test-Time Training of Long-Horizon Agents via Self-Distillation of Verified |ASCENT: Online Test-Time Training of]]）
- DuoOPD 需要二值验证器，开放写作类任务用不了；缓存老师参考答案固定，若本身错或学生变强后过时，参考就帮不上忙；三个混合都是同一批任务训练加测试，没测没见过的任务。（来源：[[论文/后训练/DuoOPD Learning from Joint Teacher-Student Outcomes for Multi-Task On-Policy Distillation|DuoOPD: Learning from Joint Teacher-]]）
- RIDE 只在数学推理、一套 JustRL 配方、四个 2B 级模型上试过；作者承认学生会被拉向「没有模型真正产生过」的隐藏状态，可能把老师偏差一起放大；最优 λ=1.25 是扫出来的，换模型要重扫。（来源：[[论文/后训练/The Teacher Is a Direction, Not a Destination Extrapolating RL-Induced Representation Resi|The Teacher Is a Direction, Not a De]]）
- Lightning Weave 只在 1.5B–8B、数学和代码上做；每个专家都必须有对应的前身 checkpoint，拿不到就定义不了变化量；效率只用平均回答 token 数衡量，没有延迟和吞吐，也没算锚点打分成本。（来源：[[论文/后训练/Lightning Weave Improving the Accuracy-Efficiency Frontier of Reasoning Models through Cap|Lightning Weave: Improving the Accur]]）
- 跨词表 OPD 只在数学和代码、三对模型、100 轮在线蒸馏、每个 prompt 只采一条回复的条件下验证；新增监督只试了片段 MSE 一种写法，梯度诊断只是相关性观察。（来源：[[论文/后训练/Rethinking Cross-Tokenizer On-Policy Distillation From Alignment Coverage to Supervision R|Rethinking Cross-Tokenizer On-Policy]]）
- On-Policy Parameter Update Direction 的方向要先跑 GRPO 算出来，换基座或换学生模型要不要重算没测；跨数据集复用只在同一模型链上验证，跨域直接拿来用会掉分；任务全是数学和代码。（来源：[[论文/后训练/On-Policy Parameter Update Direction Underlies Generalization in LLM Post-Training|On-Policy Parameter Update Direction]]）
- Divergence controls entropy 的反向 KL 膨胀只在玩具模型和极限推导里出现，大模型平均意义上没看到；熵等于损失要求收敛到驻点；每条曲线只跑一个随机种子，自蒸馏只在化学题和 GSM8K 上试过。（来源：[[论文/后训练/Divergence controls entropy in distillation|Divergence controls entropy in disti]]）
- Self-Generated Feedback 的闭环有害证据主要来自 PG-19 英文书 NLL 和 105 段生成流；Settlement 要求手边有可信真实文本或任务指标，接受率极低（125M 只有 22/936、760M 只有 18/312），不能当线上选择器。（来源：[[论文/后训练/Self-Generated Feedback Destabilizes Test-Time Training A Causal Decomposition of Long-Hor|Self-Generated Feedback Destabilizes]]）
- Sharpening Tax 整个分析是观察性的，预训练和后训练数据都没公开；基础模型给了脚手架、后训练模型没给，而脚手架对后训练模型有害，这个不对称可能放大或缩小差距；PTGS 只在 Sokoban 和 FrozenLake 验证。（来源：[[论文/后训练/Sharpening Tax in Post-Training|Sharpening Tax in Post-Training]]）
- How RL Reshapes 的理论依赖正交特征、过参数化和 KL 系数趋近 0；缩放律推导把训练集简化成 1 条提示；经验部分只覆盖 Qwen3-14B-Base 与 Gemma-3-12B-IT、48K 数学题、200–350 步，路线分类由 LLM 完成且无人工标注校验。（来源：[[论文/强化学习/How RL Reshapes LLM Reasoning Transferability, Coverage, and Scaling Laws|How RL Reshapes LLM Reasoning: Trans]]）
- Never Give Up 基本集中在数学（GSM8k 0.5B、Deepscaler 4B）和一个编码游戏 Manufactoria，没试多步智能体和更长轨迹；NGU 依赖异步 RL 才能省算力，p_NGU 和 staleness 阈值 T 都是调出来的。（来源：[[论文/强化学习/Learning to Solve Hard Problems in RL for LLMs by Never Giving Up|Learning to Solve Hard Problems in R]]）
- Bellman Policy Optimization 的定理只保证残差平方目标和原 PMD 等价；真正训练的损失还经过线性化、16 条奖励均值估初始价值、二值 KL、平滑和截断，这几步近似没有理论保证；实验只在 Qwen3-30B-A3B-Base、DAPO-Math 英语子集上做。（来源：[[论文/强化学习/Bellman Policy Optimization|Bellman Policy Optimization]]）
- On KL-Regularized Policy Optimization 目前只有摘要，没有正文实验、消融和讨论；无偏性只证到 KL 项用独立蒙特卡洛估计这一层，实际采样数很少时会怎样没有交代，真实长回合 agent 上是否稳定未知。（来源：[[论文/强化学习/On KL-Regularized Policy Optimization|On KL-Regularized Policy Optimizatio]]）
- EasyPPO 的权重估计和 critic 训练用同一组 rollout，作者承认会带偏差；σ 用整题回答的得分标准差近似每个前缀方差，理论上只给了一个上界；全部实验是 9B 的 Qwen3.5 加 verl、严格 on-policy，更大规模和离策略没验。（来源：[[论文/强化学习/EasyPPO Stabilizing the Critic Is Key|EasyPPO: Stabilizing the Critic Is K]]）
- Trust the Critic More 的 local readiness 需要反复跑同一批训练题，还要靠完整轨迹算真值误差，作者承认在只能过一遍数据的大规模场景里并不现实；主实验只有一个 4B 模型、一个证明数据集和一个评测集。（来源：[[论文/强化学习/Trust the Critic More|Trust the Critic More]]）
- CorrGRPO 只在自家奖励设计和自家数据划分上验证；7B 在 AgentDojo 的干净用处从 90.48 掉到 85.71；论文公式把 ε 放在根号外、公开代码放在根号内；安全结论只覆盖基准里的注入攻击，不等于真实环境安全。（来源：[[论文/强化学习/CorrGRPO Correlation-Normalized GRPO for Multi-Reward Learning|CorrGRPO: Correlation-Normalized GRP]]）
- DARA 的公式建立在 ε=τ=0、用 G−1 做分母、无分歧组能量为零的理想化假设上；实验只试了 2–3 个格式、长度类奖励，所有方法练完后的准确率都低于原始模型，收益主要是收敛更快。（来源：[[论文/强化学习/Make Sparse Rewards Count Density-Aware Reward Aggregation for Multi-Reward RL|Make Sparse Rewards Count: Density-A]]）
- SAGE 的局部合法性只在符号系统里精确，数学题和自由文本要靠残差、目标锚点这类代理，代理准不准没单独验证；双曲嵌入怎么训、目标结构 g 怎么定只在附录；AC 近 8 倍是相对低基数基础模型的倍数。（来源：[[论文/推理/SAGE Mitigating Long-Horizon Reasoning Biases via Topological Guidance|SAGE: Mitigating Long-Horizon Reason]]）
- The Missing Primitive 的 Absorb 只在 Qwen3.5 三个尺寸上试过，训练数据是 709 道数学博士资格考题，能否推广到代码、物理没验证；Prim 只有 182 题，评分门槛由作者定。（来源：[[论文/推理/The Missing Primitive Diagnosing and Repairing Mathematical Reasoning in Large Language Mo|The Missing Primitive: Diagnosing an]]）
- 引用链深度论文的机制几乎都在合成引用链任务上做，只有 Qwen3-8B 和 Ouro-1.4B 有完整追踪；截止层预测平均差两层多；LoRA 每个任务格式都要单独训，长链结果大多用两链加层序排列，交错排只剩 76.5%。（来源：[[论文/推理/Transformers Stop Thinking Too Early, and a Tiny LoRA Fixes It|Transformers Stop Thinking Too Early]]）
- BiasReducer 是「能看见这批数据的回答、只是不知道哪个更好」的设定，真上线看不到目标分布就得另说；能修的只有预先定好的七个表面毛病，事实错误和版权偏见没覆盖，方法只适用于最后一层是线性头的标量打分模型。（来源：[[论文/后训练/BiasReducer Adaptive Bias Mitigation for Reward Models|BiasReducer: Adaptive Bias Mitigatio]]）
- Rubric Rewards from Item Response Theory 要求每条规则都是同一个水平的单调指标、给定水平后互不相关；论文自己的诊断显示文字相近的规则仍有额外冗余；每个条件只跑一次训练，裁判是 GPT-5.5 且只有 1.27% 分歧。（来源：[[论文/强化学习/Rubric Rewards from Item Response Theory|Rubric Rewards from Item Response Th]]）
- Rubrics as Rewards 的材料只有小红书截图 OCR，能看到的正文级内容只有一条医学例题；训练后更稳、比只看最终答案好都只是转述主张，没有实验数字；分值 5/4/3/2 和换权重的影响都没写。（来源：[[论文/后训练/Rubrics as Rewards (RaR)|Rubrics as Rewards (RaR)]]）
- Pistis 截图里没有对比数字、老师、学生底模、训练步数、评测集和涨幅；两段比只抄一遍好目前只是作者主张，奖励怎么设计、在哪些任务上试过都看不到。（来源：[[论文/后训练/Pistis Technical Report|Pistis Technical Report]]）
- Online RL 五件套只有一张截图加一句中文总结，400x、反馈量、H24 口径不明；不确定这是单篇论文还是工程流水线，也不确定 ScaleCUA、Qwen-UI-Agent 是本文结果还是引用对比对象。（来源：[[论文/强化学习/Online RL Task + Environment + Verifier + Rollout + Reward|Online RL: Task + Environment + Veri]]）
- BenchShield 仍有 43% 的触发条件没被分类；有一个漏洞在基准之外的沙箱控制面，静态检查看不见；两个语义案例只有结构性通道无法归因；运行时判定依赖 ACP 工具调用流和 shell 语法解析，模糊命令会走到 Inconclusive。（来源：[[论文/智能体安全/BenchShield Formal Model-Backed Instrumentation for Reward Integrity in LLM-Agent Evaluati|BenchShield: Formal Model-Backed Ins]]）
- Skill2Env 目前是 README 和截图，缺少实验数据；只能确认任务格式、静态检查、oracle/NOP 要求、Docker 和 Codex 登录门槛，生成后的任务成功率、成本和对下游 RL 的收益都没给。（来源：[[论文/强化学习/Skill2Env|Skill2Env]]）
- More Choices 的有序/无序是二分之一刀切，没有连续量衡量语义接近；档数扫描只覆盖三个有序来源，只测了一个托管模型和一个基座系列；迁移在 0.8B 上反而从 75% 掉到 73%。（来源：[[论文/评测/More Choices, Fewer Decisions Ordinal-Scale Bias in JEV-like Direct-Decision Models|More Choices, Fewer Decisions: Ordin]]）
- Workspace Models 的关键线索由 VLM 标注，作者承认标注不一定真的和动作有关，也没用任务奖励校准；编码器完全自回归，历史很长时会变贵；真机只测一个任务二十次，对照方法还额外加了腕部相机。（来源：[[论文/机器人/Workspace Models Lightweight Robotic Memory via Saliency-Driven Supervision|Workspace Models: Lightweight Roboti]]）
- Towards In-Parameter Memory 是综述，自己没做实验，取舍都是机制推出来的定性判断；来源论文很少给可比的算力或延迟数字；覆盖范围只限文本模态，也没算上 MLA、MLE 这类新架构。（来源：[[论文/记忆/Towards In-Parameter Memory Augmentation for Large Language Models|Towards In-Parameter Memory Augmenta]]）
- 国际象棋论文的通用配方只在象棋试过，概念连贯性只有 2.76 分，Elo 只用 32 盘估计、方差偏大；递归最多走到第五层，连贯性分数由 GPT-5.6 当裁判，换裁判可能不同。（来源：[[论文/推理/Language Models that Play Chess and Explain Their Moves|Language Models that Play Chess and ]]）
## 记忆与上下文管理

- 记忆库默认只存原始轨迹，检索用 BM25 按任务描述；把整理推迟到读取时，按当前任务现场写一段短简报塞进执行者提示词，让整理者能直接拿本次任务的成败当奖励训练。
- 失败轨迹不要入库：把失败轨迹也存进去（就算标了成功还是失败）ALFWorld 再掉 1.5–2.9 分、WebShop 再掉 2.3–3.4 分，失败样本会污染检索到的例子。
- 把存进去的原始轨迹换成写入时压好的笔记，ALFWorld 掉 1.7–2.9 分、WebShop 掉 6.8–8.2 分，说明写入时丢掉的细节读的时候补不回来。
- 记忆按用途分成稳定偏好、事件细节、长期事实、以后要做的事四层，每条带出处、新证据能顶掉旧说法；取用时只当证据给模型、不当命令执行。
- 把当前任务描述从整理者输入里拿掉，它就退化成任务无关的总结器：不训练时 ALFWorld 最多掉 3.1 分，训练后最多掉 11.4 分，WebShop 训练后掉 10.4 分，说明 RL 学的是抓「这道题要什么」。

## 自造任务与环境生成

- 先解出数理模型的最优值和默认策略分数，再照着决策过程生成有状态工具环境，让环境动态和评分同源；奖励按实际收益夹在最优与默认之间归一成 0–1。
- 用三条准入检查过滤生成的环境：能执行、默认值在合理区间、最优值和参考对得上；生成失败的样本重做或丢掉。
- 挑现成运筹模型（库存、路径、背包、LP/QP）按参数批量抽题，用解题器算最优值和默认值；冻结 35B 当 setter，用真实文档做场景种子。
- 从真实部署记录挖题时不重放环境：用 CPU 锚点按硬信号粗筛、便宜模型确认候选，再剪到出错前那一步让被测模型接下一句，这样内部工具和 MCP 服务器的记录也能出题。

## 多角色分工与防共谋

- 出题和解题必须是两个角色：解题者看不到答案，出题与答题模型看不同资料，盲解结果一致才收进数据集，避免自演化里的假涨分。
- 自改进循环里把评价器、题库和预算账本锁在所有可改范围之外，模型只负责提议、固定代码负责判定，别让循环把「什么算成功」也改掉。
- 打分角色要和被训模型保持距离：盲评质量时用另一个模型、并报告与人类判断的一致率；用自家族 SFT 打分器会带来自己评自己的风险，且质量评估至少要多题多评审。
- 让小模型当参谋时，只学那些真能改变最终结果的意见做定向多轮自蒸馏，不要把参谋的所有建议都拿来训练。
- 定性编码用两个模型分头打标、只吵冲突项、三轮没共识记 disagreed，再把讨论出的规则写回全量重打；讨论后「无法判断」剩得越少、冲突压得越低，提升越大。

## 数值与优化器细节

- 同一份学生参数下，三种平均规则的原始梯度余弦只有 0.68，过一遍 Adam 后升到 0.96，清掉一阶动量后不同老师的更新余弦接近 0；动量会把不同监督的差别抹平，无动量 SGD 值得当对照基线。
- 统计参数改动量要同时看 FP32 主权重和 BF16 权重：FP32 约 97% 的参数变了，BF16 只剩 7–11%，只数 BF16 会大幅低估实际变化。
- 用 top-64 交集 KL 代替只采样一个 token 的 PG 损失，在 Qwen 上梯度几乎等同全词表梯度（被截掉的 token 概率之和不到 0.1%），不用改教师接口就能降方差；但梯度更准不等于所有能力都涨，要按平均规则分别验证。

## 低精度与分布式训练工程

- FP4/低精度 RL 掉点往往不是两边各自压得不准，而是 sampler 和 learner 取整到了不同格子：让生成端的码字决定训练端取整，训练端只在相邻两个格子中挑更接近生成端码字的那个；TRACE 在 35B 四个推理基准平均从 QUADS 的 68.8 升到 75.3，128K 输出解码吞吐是 BF16 的 5.4 倍、端到端每步只多 7.4%。（来源：TRACE: Rollout-Guided Quantization-Aware Training for FP4 Reinforcement Learning of MoE Language Models）
- 低精度 RL 要监控「优势符号 × 概率差符号」：同号时差距会被越推越大。NVFP4 跑 GRPO 时这类同号 token 权重占比从 1.02 涨到 2.32，答案按 64 token 一段切后，排前 5% 的段装走约四分之一坏 token；只对负奖励且差距为负的 token 加权，再按 w 除以 w̄ 归一化，修补项用 pseudo-Huber。（来源：TRIAGE: Direction-Aware Mismatch Stabilization of Native NVFP4 Reinforcement Learning）
- 省显存的 RL 后训练可以用低秩梯度草图：LoGRA 只存 rank-256 梯度草图再写回权重，7B 平均显存从 31.82 降到 17.29 GiB，准确率 72.33% 对 72.48%；27B 用稠密 Adam 一步就爆显存，换 LoGRA 在一台八卡机器跑 1100 多步。注意 LoRA 基线 13.21 GiB 比 LoGRA 7.18 GiB 更耗显存，但 70.45% 正确率和单步速度更高。（来源：LoGRA: Scaling LLM Reinforcement Learning with Low-Rank Gradient Sketches）
- 跨区权重同步可以只传真正变了的位：NeMo-DCR 用 HF checkpoint 坐标加原生 loader，变化检测比存储位，XOR 掩码加 zstd，任何重试统一降级成绝对覆盖；实测每步只有 0.6%–1.2% 的 BF16 值会变，1T 在 3% 变化率下从 87.5 分钟压到 150 秒，并保持和全量 refit 逐位相同。（来源：NeMo-DCR: Bit-Exact Delta-Compressed Refit for Scalable Agentic RL at Trillion-Parameter Scale）
- 异步 GRPO 可以把采样和训练拆到两批机器，用共享文件夹或对象存储传 LoRA 增量，完全不走 GPU 间 NCCL；同一 500 步从 3 小时 27 分缩到 53 分钟。代价是材料只给一个数学任务设置，模型规模、机器数、bucket 实现和真实带宽都没给，换环境不一定成立。（来源：Async GRPO with LoRA across HF Jobs: a bucket, a proxy, and no NCCL）
- 训练框架可以先看吞吐和显存：Halo 在同一套代码支持预训练、SFT、偏好优化、全异步多轮 RL，8×B300 上比 stock TRL 最高约 2.8 倍训练吞吐，ZeRO-3 分片时约 2.7 倍且峰值显存少 25%；但这是仓库基准，不是独立复现实验。（来源：Halo）
- 后训练量化不掉点可用两条机制解释：预训练模型每层新误差会和上一层传下来的误差反向抵消，Qwen3-32B 前 48 层抵消 50.2% 新误差；输出头优先保住高分 token，最高分词被换掉只有 8.3%–12.7%。诊断用逐层隐藏误差、误差与输入误差余弦、Flip@1、Ret@K；不要把随机初始化模型的结论外推。（来源：Why Does Post-Training Quantization Work?）

## 持续学习与遗忘控制

- 防遗忘不一定要旧数据回放：Local Support Learning 给每个权重矩阵配一个高斯混合门，只在输入落进当前训练数据范围时才加新权重；旧本事保留率从 76.6% 升到 96.6%，加滑动平均后误开从约 16% 降到 5%、保留率到 98.8%。代价是适配器不能合并回原权重，推理成本随阶段数线性增长。（来源：Local Support Learning）
- LoRA 持续学习里固定小学习率不合理：PaLoRA 按历史知识有效秩 R 自动放缓，B 的梯度除以 √(R/C)，ImageNet-R 五十任务后 76.56%，比 LoRA-DRS 高 4.09 点；α=0.5 的平方根节奏实测最好，换成 1、2 学新任务太慢，换成 0.125、0.25 旧任务忘得更多。理论只在单层线性模型成立，实验只做图像分类。（来源：PaLoRA: Paced Low-Rank Adaptation for Continual Learning）
- 已经答对的知识里，答案实体被越多事实指向的越容易被邻近微调改坏；改热门来源时错误沿知识链传播更远。做法：按答案实体入度给更新前风险打分，LoRA 微调时用 5–100 条热门事实做回放锚点并加 KL 约束，权重 0.1。（来源：Popular Knowledge Propagates More Errors in LLM Knowledge Updating）
- 参数化记忆可用「写在哪一层 × 什么时候写」定位：写入由独立动作生成、推理时作为独立对象插进前向；要按内容检索放注意力层，要改事实放 FFN，最省事放输入层。需要原句引用、出处、精确删除或人工改一条时仍要保留原文上下文；这篇是综述，没有实测结论。（来源：Towards In-Parameter Memory Augmentation for Large Language Models）
- 机器人长程记忆可把大模型查询挪到训练时：训练阶段用 VLM 标出关键线索，蒸馏成一个轻量 workspace token，部署时只跑轻量编码器；关键帧每步 302 毫秒、普通策略 49.2 毫秒，四个记忆任务平均成功率 91.5% 对关键帧 66.8%。标注不一定真的和动作有关，真机只有 N=20。（来源：Workspace Models: Lightweight Robotic Memory via Saliency-Driven Supervision）

## SFT 数据选择与偏好蒸馏

- 挑 SFT 数据时固定数据量、优先选路线差得最远的样本：用固定规则标出步骤、再用固定随机投影压成定长向量做路线指纹，先聚类、每簇按比例分名额、簇内反复挑离已选最远的；OLMo3-7B 在没见过的环境上 pass@8 高 16.9 个点，挑 210 万条只花一台 CPU 三小时、不用 GPU。（来源：Selecting Diverse SFT Traces Improves Post-RL Generalization）
- 偏好蒸馏的 reject 优先用严格更小的冻结模型生成并验证为错：small-model reject 比学生自己的错答案更好，14B 学生上小模型比例从 0% 加到 100%，代码 avg@4 从 59.73% 升到 63.28%；同一个 prompt 采 8 个候选，按参考模型长度归一化 log 似然排序，挑最低的那批。DPO 可用 lr 5e-7、β=0.1、batch 256、序列长 2560。（来源：Smaller Models, Better Rejects: Preference Distillation Scaling）
- SFT 后不要只缩放示范词权重：SCALE 冻住基座和 LoRA 增量，只学一个线性门，λ=1 不动、0 到 1 削弱、小于 0 反向、大于 1 加强；数学上 Qwen2.5-Math-1.5B 从 DFT 的 32.81 升到 37.84，代码 HumanEval 平均从 30.19 提到 34.72。表里的 Ours 是 42 组上下界中最好的值，部署时能否保住这部分收益不清楚。（来源：Rethinking Token Reweighting for SFT: Suppress, Reverse, and Extrapolate Learned Features）
- SFT 数据选择还要在 RL 前做体检：多路线那版平均分略低，但有 54.7% 的题有的答对有的答错，相似版只有 46.9%；同一道题一组采样里有没有对有错，比单看 SFT 准确率更能预测后续 RL 有没有学习信号。（来源：Selecting Diverse SFT Traces Improves Post-RL Generalization）

## 奖励模型与评分可靠性

- 奖励模型的长度、自信、讨好用户等偏见主要落在最后一层线性打分头上：只改这个线性头、其他参数全冻住，按本批数据选要修的偏见，五个模型三个榜单平均涨 8.3、18.0、6.9 个百分点；沿协方差方向减 λ 倍投影，而不是用稀疏编码器解码向量。新数据 100–200 条即可选修法，但事实错误和版权偏见没覆盖。（来源：BiasReducer: Adaptive Bias Mitigation for Reward Models）
- 开放题打分别把规则分简单相加：把整张对错表当成一道测量题，反推隐藏水平分当奖励，答对条数相同的两张表也能排开；用高斯累积分布能拆开并列对，按 Fisher 信息挑规则，只问一半规则时平均分只比全问低 0.1 分、裁判耗时少 49%。（来源：Rubric Rewards from Item Response Theory）
- 先写标准答案，再拆成三到五条能判定对错的检查项；必须做到的 5 分、重要的 4–3 分、可选的 2 分；同一份清单既当训练奖励，也当人工或模型评审表。这篇材料只有一条医学例题和截图 OCR，没有对照实验数字。（来源：Rubrics as Rewards (RaR)）
- 直接给档位的 JEV 类模型会挤在中间档：有序任务只用到 67%–76% 的有效档位，无序任务能用 87%–102%；用带偏差校正的 LoRA 在压缩最重的档位补训练，档位使用率从约 47% 升到 86%、准确率涨 13–15 分，但迁移到 0.8B 反而变差。（来源：More Choices, Fewer Decisions: Ordinal-Scale Bias in JEV-like Direct-Decision Models）
- 评测奖励完整性要把静态路径和运行时证据接起来：静态污点分析找权限漏洞，运行时用资源交接和分数来源证据判断这次是否真走了漏洞；人工标注 456 条运行中 314 条偷过分、共 419 段作弊，第一次尝试中位在 60% 处、成功在 76% 处，完整作弊链召回从 23%–94% 升到 77%–100%，运行时判定准确率从文本 36% 升到 96%。（来源：BenchShield: Formal Model-Backed Instrumentation for Reward Integrity in LLM-Agent Evaluation Infrastructure）
- 让 CoT 和内部计算对齐可以当成奖励信号：用探针读中间层实际用了哪招，再和 CoT 里写的策略算宏 F1；后训练用答对分加 1 倍一致分，27 个模型任务组合里 25 个一致性上升、答对率掉幅不超过 1.5 个百分点。只有乘法任务里因果影响率从 29% 升到 72%，事实题和提示干扰主要只是改说法。（来源：Making LLMs Say What They Think: Measuring and Improving CoT-Interpretability Alignment）

## Agent 环境与经验复用

- 长期任务 RL 卡在奖励稀疏时，先改环境反馈而不是只给智能体做 SFT 热身：前段把下一步可行动作写进反馈，后段把隐藏状态写出来；以 0.5 概率注入，200 步里第 100 步从动作提示切到观测补充，SciWorld 和 BFCL 平均涨 2.82 分，但 AppWorld 上加反馈仍全是零分。（来源：Environments as Scaffold: Enriching Feedback to Bootstrap Self-Evolving Agents in Long-Horizon Tasks）
- 从轨迹里挖可复用经验时，把动作按动词加作用对象规范化，再用频率×长度×成功率合并成经验树；每个节点当一道练习题，前面用金标准动作接续，按长度给部分匹配奖励、节点越深加成越大，λ0=0.75。WebArena 成功率 18.4%→22.9%，把 X-Score 换成随机合并会掉到 17.9%。（来源：X-Tree: Tokenizing Reusable Experience for Efficient Agent Generalization）
- 把 Agent Skills 变成 RL 任务时，每条任务必须过 oracle must pass、NOP must fail、静态检查和 Pinned bare image；最终用 Harbor Task Format with Rubrics 输出，目录含 instruction.md、container、data。落地门槛是 Linux Docker、Python 3.12+ 和容器内 Codex 登录文件。（来源：Skill2Env）
- 多步决策迁移可以用「固定局面、换目标重排同一批动作」逼出可迁移知识：状态、历史、可选动作全部按住不动，只换目标，让候选动作重新排序；ALFWorld 没见过的关卡从 82.8% 升到 91.8%，每局步数从 16.0 降到 11.4，监督只用了初始示范的 9.1%。（来源：EVOKE: Eliciting World Knowledge in Agents for Transferable Decision-Making）
- 长程机器人记忆可把大模型查询挪到训练时，部署只跑轻量编码器；但 VLM 标的「关键线索」不一定和动作有关，也没用任务奖励校准，历史很长时自回归编码器还会变贵。（来源：Workspace Models: Lightweight Robotic Memory via Saliency-Driven Supervision）

## 长链推理诊断与深度调用

- 数学题做不出先把「自己找思路」和「直接解题」拆开考：12 个模型被直接给出正确思路后全都涨，最少涨 17.58 个点、最多涨 29.67 个点；解题失败里 83.6% 发生在找不出思路上。补课只挑「自己找不出但给思路会做」的题，Absorb 比整篇解答硬灌更安全。（来源：The Missing Primitive: Diagnosing and Repairing Mathematical Reasoning in Large Language Models）
- 长链推理的探索偏置和累积偏置要分开治：用「这一步消掉多少未解决结构」偏置采样（只训练时偏置、推理不剪枝），再用双曲空间里离目标结构的距离做密集奖励；只加一个组件会在 BBH-H 或代数任务上掉分，两个一起用才回到 45.31。（来源：SAGE: Mitigating Long-Horizon Reasoning Biases via Topological Guidance）
- 预训练模型顺引用链只可靠跟 1.4–3.6 行，把 OLMo-3 从 7B 加到 32B 仍停在约 2.6 行；在中间某层加 rank-8 LoRA、其余冻结，Qwen3-8B 第 14 层把 24 行链从 15.5% 提到 99%，同一 LoRA 从第 20 层挪到第 21 层就从 20.5 行掉到 5.2 行。（来源：Transformers Stop Thinking Too Early, and a Tiny LoRA Fixes It）
- 要区分「没学会算法」和「会算但不说」：用探针从中间层读实际策略，再和 CoT 写的策略算一致率；两步查事实题上 Gemma2 最准却最不忠实，乘法上 Qwen3 最准却不如 Gemma2 忠实，说明答得准和说得实是两件事。（来源：Making LLMs Say What They Think: Measuring and Improving CoT-Interpretability Alignment）
- 会算的哑专家接语言模型时，先上四步课程（静态当前→动态当前→静态未来→动态未来），再把引擎表示用交叉注意力接进中间层；4B 模型打出 2697 分，比 GPT-5.6-Sol 的 2071 高 600 多分，但 Elo 只用 32 盘估计，概念连贯性只有 2.76 分。（来源：Language Models that Play Chess and Explain Their Moves）

## 在线 RL 目标与优势估计

- 只按整条回答给最终分时，可以用贝尔曼等式把中间价值消掉：权重写成 (1+ε−μ)/(1+ε−π)，只看被采样那一个 token 的概率，ε=0.1、上限 C=3.0；AIME 平均 50.5%，比 GRPO-ClipHigher 高 11 分，但 50.5% 是挑出的最高点，训练满 400 步是 49.4%。（来源：Bellman Policy Optimization）
- 异步 RL 可以把 KL 惩罚锚到真正生成数据的策略上：更新有闭式解、不用重要性权重、不用 critic、不必一道题采一组回答；配分函数换成采样端均值加采样到训练端的 KL。目前只有摘要，没有实验数字。（来源：On KL-Regularized Policy Optimization）
- 多奖励大小不一时，GRPO 的分母用协方差会放大数值波动大的奖励；CorrGRPO 改成相关系数矩阵求和后开根号，分子仍是总奖励，代码四个模型平均 Pass@1 高 0.8–4.2 个点，工具调用完整正确率 Qwen2.5-7B 从 63.38 升到 67.61。（来源：CorrGRPO: Correlation-Normalized GRPO for Multi-Reward Learning）
- 稀疏奖励接近饱和时按密度补偿：保留逐奖励组内归一化，在聚合前按本批估计活跃组比例 π_k，权重取 min(5, √(π_ref/π_k))，只作用正优势；格式奖励到 0.8 的中位步数，GRPO 要 34 步、GDPO 19 步、DARA 14–15 步，但所有方法练完准确率都低于原始模型。（来源：Make Sparse Rewards Count: Density-Aware Reward Aggregation for Multi-Reward RL）
- GRPO 全错组没有梯度，可用 Never Give Up：先采 K=4，全错按 p=0.95 继续采到做对，再把最近 4 步历史答案并成一个大组算优势；用 n+/n-(1-r̄) 重缩放负面答案优势。它依赖异步 RL，且只在数学和一个编码游戏上验证。（来源：Learning to Solve Hard Problems in RL for LLMs by Never Giving Up）
- 想多关注少见高分样本时，可以把优势换成随机阈值过线概率的对数：保留原训练框架，只改 advantage，不换网络、不重写流程；论文说这等价于很多个 Best-of-k 梯度混合，但材料只有摘要和引言开头，没有四类任务的具体数字。（来源：Tail-Likelihood Reinforcement Learning）
- 只靠裁判对错反馈也能学出全部最小充分条件：把每条答案的分数写成「去掉它以后整组认可范围少多少」，用 l1o 和 l2o 估计；逻辑题上按组覆盖能找回 12.1 个最小答案，单独按对错只找到 1.3 个，按长度惩罚只找到 1 个。（来源：Minimal Witness Reinforcement Learning）
- 长链推理可以把结构分只加进 advantage：用投影到算子子空间的能量占比偏置采样，用 Poincaré 双曲距离做密集奖励；奥数分从 38.82 升到 41.59，BBH-H 从 39.06 回到 45.31，2B/9B/35B 三个尺度分别高 1.83/3.02/2.49 分。（来源：SAGE: Mitigating Long-Horizon Reasoning Biases via Topological Guidance）

## 多模态与生成模型 RL

- 给流模型做奖励后训练时，先按同一条提示在组内给奖励封顶（75% 分位），再沿梯度试三个固定长度（0.1、0.2、0.4）的候选，挑「封顶奖励减距离²/(2τ)」最高的那个，原地不动也在候选里；MEND 100 次更新 PickScore 23.70，Flow-GRPO 约 4000 次才 23.52，但前提是奖励可求导。（来源：MEND: RL For Flow Models via Proximal Velocity Matching）
- 音视频联合生成的多奖励路由可以动态决定改哪里和权重：把跨模态注意力回应范数当重要性指针，层路由用 X̃=α·sg(X)+(1−α)X 只缩梯度不改前向；奖励侧用先验保底、冲突残差修正和热身期；训练奖励和评测奖励基本同批模型，提升幅度不大且没做显著性检验。（来源：Adaptive Reward Routing: Dynamic Multi-Reward Optimization for Joint Audio-Video Diffusion via Forward-Process RL）
- VLA 策略光看当前动作安不安全不够：在动作反复失败、撞过东西或过不了终点检查时触发警铃，从 top-12 候选里按原概率加局部安全加很小历史修正项重排，不批准就退回原动作；六个 Safety-CHORES 设置安全代价降 1.9%–57.5%、成功率几乎不掉，但警铃直接放行的死路进不了重排，损失可以无限大。（来源：A Safe Action Is Not Enough: Feasible-Future Decoding for Vision-Language-Action Policies）

## 我的补充
