# 后训练-OPD-RL 最佳实践手册

> 后训练里的蒸馏（OPD/on-policy distillation）与强化学习（RL/RLHF/GRPO）：怎么把信号变成能力。

自动积累，只增不减；「我的补充」是你自己写的地方，脚本永不覆盖。

## 目标与产出
- 把项目产出定义成三段闭环的产物，而不是只改一处的补丁：先用脚手架把能力逼出来，再把成功轨迹做成训练数据，最后把能力写进权重并撤掉脚手架，让上下文开销回落；数据、脚手架、权重各自成层、共用一个循环内核。（来源：[[论文/RSI/MetaRSI RSI2 A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems T|MetaRSI / RSI2: A Meta-Recursive Sel]]）
- 训练数据要产出完整轨迹而不是只留正确解：跑错和掉分的那一轮一起保留，损失只加在真正往前走的那几步，重复轮询、无新观测的调用和系统消息一律不加。这样模型学的是「出错之后怎么改」，AREX-2 在 MLE-bench Lite 拿到 81.8，比最强公开基线高 8.1 分。（来源：[[论文/RSI/AREX-2 Advancing Self-Improving Agents through Long-Horizon Reflective Tasks|AREX-2: Advancing Self-Improving Age]]）
- 选题前先把候选任务的判对错方式列出来并分级（能跑测试到只能请专家打分），优先做判分成本低的那一档：普查的 55 个已闭合自改进循环里，53 个卡在前三级。（来源：[[论文/RSI/MetaRSI RSI2 A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems T|MetaRSI / RSI2: A Meta-Recursive Sel]]）
- 造环境时的产出物要成对交付：先解出数理模型的最优值和一个默认策略的分数，再把决策过程做成有状态工具环境，奖励把实际收益夹在最优值和默认值之间归一成 0–1，让环境动态和评分来自同一份解。（来源：[[论文/其他/Verifiable Hidden Dynamics Play Generating Agentic RL Environments from Solved Mechanisms|Verifiable Hidden Dynamics Play: Gen]]）
- 要测行为合规时，产出物是从真实部署记录剪出来的接续式考题：剪到出错前那一步就该让被测模型接下一句，不重放环境，这样内部工具和 MCP 服务器的记录也能拿来出题。（来源：[[论文/RSI/TraceDance An Automated System for Building Agent Behavior Benchmarks from Real-World Agen|TraceDance: An Automated System for ]]）
## 动手前必须想清楚的
- 训练库入库前先跑两条环境准入检查：参考解必须能跑出分数、朴素基线必须明显更低，任一不过就丢掉；同时把通过/不通过换成通过测试比例这类连续分，让每一轮改进都有可学的信息。（来源：[[论文/RSI/AREX-2 Advancing Self-Improving Agents through Long-Horizon Reflective Tasks|AREX-2: Advancing Self-Improving Age]]）
- 先写明损失是按 token 平均还是按回答平均，因为平均规则等于隐式加权：所有 token 平等平均时，长度约 3 倍的数学回答会白拿约 44% 的损失权重；改成先定领域权重、领域内按回答平均后，数学降 3.0 分、科学升 2.1 分。（来源：[[论文/后训练/From Gradients to Capabilities Understanding Multi-Teacher On-Policy Distillation|From Gradients to Capabilities: Unde]]）
- 把「是否带一阶动量」当作对照变量先定下来：同一学生参数、同一批回答下，三种平均规则的原始梯度余弦只有 0.68，过一遍 Adam 后升到 0.96，清掉一阶动量后不同老师的更新余弦掉到接近 0；学生边练边换前缀时动量记着旧梯度会拖慢适应，同样跑 500 步无动量 SGD 的平均分全面更高（39.94、39.46、39.26 对 38.91、38.63、38.79）。（来源：[[论文/后训练/From Gradients to Capabilities Understanding Multi-Teacher On-Policy Distillation|From Gradients to Capabilities: Unde]]）
- 统计「改了多少参数」时同时看 FP32 主权重和 BF16 权重，别只数 BF16：FP32 里约 97% 的参数都变了，四舍五入成 BF16 后只剩 7–11%；FP32 里三分之一参数承担 90% 平方变化，BF16 只要 4%。（来源：[[论文/后训练/From Gradients to Capabilities Understanding Multi-Teacher On-Policy Distillation|From Gradients to Capabilities: Unde]]）
- 记忆默认原样存整条轨迹、把整理推迟到读取时，而不是任务做完就压成固定笔记：同样用 Gemini 整理，读时整理不训练就有 WebShop 61.0，写入时的 SkillOS 只有 41.0，因为写入时要提前猜未来任务，猜错就永久丢信息。（来源：[[论文/其他/Just-in-Time Memory Learning to Curate Task-Adaptive Memory for LLM Agents|Just-in-Time Memory: Learning to Cur]]）
- 做中间表示对齐前先用逐层 CKA 判断这对师生适不适合：同血缘、层能对上的一对（CKA 对角线 0.983）全程开着不崩、最高 87.22，跨尺寸时按相对深度配对的层在做不同的事，只能对两边送进 LM head 的最后一层动手。（来源：[[论文/后训练/LastOPD Taming Collapse in Latent On-Policy Distillation|LastOPD: Taming Collapse in Latent O]]）
- 先决定是否区分「通过但写得差」：同组里只要测试通过就发一样多的奖励，通过的轨迹会拿到完全相同的优势，模型学不到哪份实现更值得留；要区分就得先准备好组内质量排名和优势重分配的方案。（来源：[[论文/后训练/Groupwise Agentic Grading and Advantage Redistribution for Code Agent RL|Groupwise Agentic Grading and Advant]]）
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
## 评测与验证
- 把轮数当成给模型的预算来评测，按轮数扫一条曲线看什么时候不再涨：AREX-2 在 Frontier-CS 上一小时 54.4、五小时 70.7，最后两小时还涨 4.8 分。（来源：[[论文/RSI/AREX-2 Advancing Self-Improving Agents through Long-Horizon Reflective Tasks|AREX-2: Advancing Self-Improving Age]]）
- 要验证没有外部判分时模型能不能自己重评，就在完全不给对错提示的设置下测：AREX-2 在 BrowseComp 上把轮数从 47 加到 143，准确率从 64.8 涨到 84.0。（来源：[[论文/RSI/AREX-2 Advancing Self-Improving Agents through Long-Horizon Reflective Tasks|AREX-2: Advancing Self-Improving Age]]）
- 蒸馏评测同时报 Avg@16 和 Pass@16，并把 Pass@k 拉到 64，否则看不出解法覆盖的变化：去掉熵奖励后 Pass@16 平均掉 1.95 分，Avg@16 只掉 0.46 分。（来源：[[论文/后训练/An RL View of OPD Least Square Policy Distillation for Sample-Efficient LLM Reasoning|An RL View of OPD: Least Square Poli]]）
- 加速类方法要按域分别报分、别只挑赢的说：零售上 3.73 倍速到 0.475 追平全量蒸馏 0.477，但电信域最快只到 0.849，仍低于基线 0.853；速度按纯训练每步时间算，端到端还要扣掉评测开销。（来源：[[论文/后训练/Know When to Stop, Where to Restart Accelerating Multi-Turn Agentic On-Policy Distillation|Know When to Stop, Where to Restart:]]）
- 测行为合规要用两步：先用自动题跑大样本通过率，再用「同一道题上不同模型第一步选择不同」来归因。参考水位：九个前沿模型平均只有 26.7% 过关，「先检查再动手」类只有 8.1%，而「工具调用格式正确」有 67.9%，说明模型会写格式却常跳过动手前的检查。（来源：[[论文/RSI/TraceDance An Automated System for Building Agent Behavior Benchmarks from Real-World Agen|TraceDance: An Automated System for ]]）
- 自动造的题要抽检有效性：随机抽 100 道让两人独立检查，只有 84 道确认原记录真出现了目标坏行为；评分表质量 4 分以上的占 90%、平均 4.75 分。约 16% 的题底子不干净，不能直接全信。（来源：[[论文/RSI/TraceDance An Automated System for Building Agent Behavior Benchmarks from Real-World Agen|TraceDance: An Automated System for ]]）
- 跨基准的分数不能横着摆：HLE 带星号的是全量集、不带的是纯文本子集；Avg@16 与 pass@1 不能比；BFCL 无权重平均和电商结余也不是同一协议。报告时把配置和口径一起写清。（来源：[[论文/RSI/AREX-2 Advancing Self-Improving Agents through Long-Horizon Reflective Tasks|AREX-2: Advancing Self-Improving Age]] · [[论文/其他/PACT From Credit Assignment to Critic Alignment|PACT: From Credit Assignment to Crit]] · [[论文/其他/Verifiable Hidden Dynamics Play Generating Agentic RL Environments from Solved Mechanisms|Verifiable Hidden Dynamics Play: Gen]]）
- 两组可照抄的评测口径：数学用 Avg@16，代码用 SWE-bench Verified pass@1；报结果时至少给多个种子或标准差，主曲线不要只做单次报告。邻近老师那篇每个尺度跑三次并给标准差，是值得照搬的做法。（来源：[[论文/其他/PACT From Credit Assignment to Critic Alignment|PACT: From Credit Assignment to Crit]] · [[论文/后训练/Better Supervision Is Nearby Neighborhood On-Policy Self-Distillation|Better Supervision Is Nearby: Neighb]]）
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

## 我的补充
