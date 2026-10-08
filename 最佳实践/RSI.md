# RSI 最佳实践手册

> 递归/迭代式自我改进：让系统用自己的产物改进自己（模型、harness、数据三个面）。

自动积累，只增不减；「我的补充」是你自己写的地方，脚本永不覆盖。

## 目标与产出
- 开工前先写清这套系统交付的是「一个能自动判对错的闭环」，不只是更高的分数。普查 45 个自我改进系统，69% 的循环靠机器免费判对错的目标闭合；22 个学科 55 个已闭合循环里 53 个落在前三级判定（能跑测试到需要专家打分），第 4、5 级一例都没有。选题时先问这一步的成败能不能被固定代码自动判，判不了就先别做闭环。（来源：[[论文/RSI/MetaRSI RSI2 A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems T|MetaRSI / RSI2: A Meta-Recursive Sel]] · [[论文/RSI/The Last AI Built by Humans Toward Genuine Recursive Self-Improvement|The Last AI Built by Humans: Toward ]]）
- 把「这次答对」和「机制改了」分开交付。只在当前任务里改答案、任务结束就丢不算自改进，论文把它划成 B0；改动必须落到参数、harness、记忆或改进策略上，并在下一轮真正参与生成或挑候选。给每个组件标一列「产出什么、被谁继承、下一轮在哪里用到」。（来源：[[论文/RSI/The Last AI Built by Humans Toward Genuine Recursive Self-Improvement|The Last AI Built by Humans: Toward ]]）
- 交付前用四问审计自己的系统：闭环在哪里闭上、什么被留下来继承、哪些决定还在人手里、下一轮的改进有没有真的用到它。（来源：[[论文/RSI/The Last AI Built by Humans Toward Genuine Recursive Self-Improvement|The Last AI Built by Humans: Toward ]]）
- harness 层的产出要带触发条件一起交付，不是只交一段代码补丁。SoL-Pi 在 GPT-5.6 Sol 上搜出的四个省 token 机制一行不改搬到 Opus 5，保住 Pi 在 EdgeBench 上 94.3% 的分数、token 少 44.7%、成本少 33.5%。（来源：[[论文/RSI/SoL-Pi Recursively Scaling Auto-Research Loops for Efficient Agent Harness|SoL-Pi: Recursively Scaling Auto-Res]]）
- 记忆组件的交付物应该是「按当前任务现场生成的短简报」，不是一份固定笔记。Just-in-Time Memory 把写入时就压好的笔记换成读时整理，ALFWorld 掉 1.7 到 2.9 分、WebShop 掉 6.8 到 8.2 分，写入时丢掉的细节读的时候补不回来。（来源：[[论文/其他/Just-in-Time Memory Learning to Curate Task-Adaptive Memory for LLM Agents|Just-in-Time Memory: Learning to Cur]]）
## 动手前必须想清楚的
- 先定位失败在哪一层，别默认要改权重或改提示。数据、harness、权重三层代价不同：改 harness 每次推理多背上下文，改数据碰不到模型本来就不会的能力，改权重可能把原有本事练回去。MetaRSI 的路线是先靠 harness 把能力逼出来，再把成功轨迹做成训练数据，最后写进权重并把 harness 撤掉。（来源：[[论文/RSI/MetaRSI RSI2 A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems T|MetaRSI / RSI2: A Meta-Recursive Sel]]）
- 把评价器、题库和预算账本放在所有可改范围之外，模型只提改法、固定代码负责判定。Anthropic 的自动研究实验里出现过挑随机种子、从评测接口套测试标签；Red Queen Gödel Machine 的做法是每个 epoch 冻住评测器，换评测器时用独立标准答案校验。（来源：[[论文/RSI/MetaRSI RSI2 A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems T|MetaRSI / RSI2: A Meta-Recursive Sel]] · [[论文/RSI/The Last AI Built by Humans Toward Genuine Recursive Self-Improvement|The Last AI Built by Humans: Toward ]]）
- 递归自调用前先把预算和深度写进代码。JAZ 用 BudgetPool、IterationLimit、RecursionLimit 三个原语管资源；实验中 AppWorld 递归封顶 2 层、StuLife 封顶 70 层，上限按任务长度人为定，换任务要重新定。（来源：[[论文/Harness/Harness as a Language A Minimalist Agent Framework With Maximal Expressivity|Harness as a Language: A Minimalist ]]）
- 上下文压缩要算账再压，而且压缩会打断缓存前缀。门槛是预计省下的输入费大于重写缓存的钱，压得越晚门槛越高；只看缓存命中率会得出反结论。（来源：[[论文/RSI/SoL-Pi Recursively Scaling Auto-Research Loops for Efficient Agent Harness|SoL-Pi: Recursively Scaling Auto-Res]]）
- 奖励要跟着模型当前水平分段。Qwen-Planner-Agent 按组做对率分三段：做对少就补中间步骤分，做对一半只看最后成不成，几乎全对才压执行成本。（来源：[[论文/RSI/Qwen-Planner-Agent A Closed-Loop AI-for-AI Framework for Real-World Mobile Planner Agents|Qwen-Planner-Agent: A Closed-Loop AI]]）
- 组内归一化会把某些项的相对权重抹掉，这时只调权重系数没用。整组几乎全对时效率项的相对权重会被除掉，哪怕权重只给 0.1，效率信号也和成败一样大；解法是给优势分母加下限。（来源：[[论文/RSI/Qwen-Planner-Agent A Closed-Loop AI-for-AI Framework for Real-World Mobile Planner Agents|Qwen-Planner-Agent: A Closed-Loop AI]]）
- 多老师蒸馏动手前先定损失怎么平均，因为平均规则就是隐式加权。按全局 token 平等平均时，数学回答长度约是指令跟随的 3 倍，数学白拿约 44% 损失权重；改成先定领域权重、领域内按回答平均后，数学降 3.0 分、科学升 2.1 分。（来源：[[论文/后训练/From Gradients to Capabilities Understanding Multi-Teacher On-Policy Distillation|From Gradients to Capabilities: Unde]]）
- 组内奖励只削峰不补齐等于削减奖励总量，会把训练带偏。只调小差代码奖励那版策略熵从 0.359 涨到 0.905，第 20 步从 56.5% 掉到 48.8%；补齐那版第 28 步有 62.2%。动手前先确认优势总和守恒。（来源：[[论文/后训练/Groupwise Agentic Grading and Advantage Redistribution for Code Agent RL|Groupwise Agentic Grading and Advant]]）
- 多阶段微调前先决定适配器合不合并。每阶段新加适配器、用完合并回主权重会让阶段之间互相打架，第一阶段后就掉 44%；把各阶段适配器都留着、各由自己的开关管，连做三段旧本事不掉。（来源：[[论文/后训练/Local Support Learning|Local Support Learning]]）
- 用会反复改答案的扩散式文字模型做长任务，先想清楚模仿式 SFT 会压住「反复改」这个本事：DiffusionGemma 微调后短题和工具选择变强，长推理和终端任务反而变差。作者主张改成按结果好坏给奖励，但材料里没有这个对照实验，别当已验证结论。（来源：[[论文/后训练/Fine-Tuning DiffusionGemma What Works, What Breaks|Fine-Tuning DiffusionGemma: What Wor]]）
- 多 harness 采样前先区分「解锁不同解法」和「只是多跑几次」。Scaling Trajectories 把三套 harness 的 rollout 拉平到各 2,074 次，并起来仍比最好的单套多解 67 道题、相对多 23.5%，互补来自外壳本身。（来源：[[论文/RSI/Scaling Trajectories for Complex Tasks through Recursive Self-Rewrite|Scaling Trajectories for Complex Tas]]）
- 中间层监督不是越多越好，先决定对齐哪一层。LastOPD 把学生每层都对齐老师，MATH-500 冲到 46 后掉到 11.3；只在两边接 LM head 的最后一层对齐、并 10 步内交还 token 级蒸馏，升到 58.95。跨尺寸模型按深度配对的层做的是不同的事，硬对齐等于把学生拽向它读不懂的状态。（来源：[[论文/后训练/LastOPD Taming Collapse in Latent On-Policy Distillation|LastOPD: Taming Collapse in Latent O]]）
- 学生跑 BF16 时别用「动了多少参数」判断训练改了什么。FP32 主权重约 97% 都变了，四舍五入成 BF16 只剩 7% 到 11%；FP32 里三分之一参数承担 90% 平方变化，BF16 只要 4%。要统计改动就同时看 FP32 主权重和 BF16 权重。（来源：[[论文/后训练/From Gradients to Capabilities Understanding Multi-Teacher On-Policy Distillation|From Gradients to Capabilities: Unde]]）
- 记忆入库前先决定收不收失败轨迹：把失败轨迹也存进去、即使标了成功还是失败，ALFWorld 再掉 1.5 到 2.9 分、WebShop 掉 2.3 到 3.4 分，失败样本会污染检索到的例子。（来源：[[论文/其他/Just-in-Time Memory Learning to Curate Task-Adaptive Memory for LLM Agents|Just-in-Time Memory: Learning to Cur]]）
- 人工把关要写清审什么。Qwen-Planner-Agent 是每轮发布前由人审，但正文没交代具体审什么、大模型控制器调阈值是否比固定阈值更好，自己动手时先把这两点定义出来。（来源：[[论文/RSI/Qwen-Planner-Agent A Closed-Loop AI-for-AI Framework for Real-World Mobile Planner Agents|Qwen-Planner-Agent: A Closed-Loop AI]]）
## 常见坑与解决办法
- 工具写死会卡在没预料到的输入上。Letta 靠人写的搜索工具，JAZ 让模型自己写代码翻原始历史：远端回忆题 69.9% 对 61.8%，成本 18.3 美元对 42.1 美元。把「怎么取历史」也交给模型写代码，别只给固定检索工具。（来源：[[论文/Harness/Harness as a Language A Minimalist Agent Framework With Maximal Expressivity|Harness as a Language: A Minimalist ]]）
- 上下文快满时不要手工转抄历史。把提示词、工具和交互历史都做成代码变量，满了按引用交给子智能体、用 ContextWindowWarning 触发；去掉「提示词和历史是变量」这一条，远端回忆从 69.9% 掉回 32%。（来源：[[论文/Harness/Harness as a Language A Minimalist Agent Framework With Maximal Expressivity|Harness as a Language: A Minimalist ]]）
- 成功轨迹直接拿来微调会把外壳依赖一起学进去。Terminal-Bench 2 上直接微调从 57.0% 掉到 53.4%；先重写成通用 harness 的 runbook 再微调升到 74.2%。重写要点：runbook 只写关键步骤和检查点、不写最终答案，挑掉泄题的，再在全新沙箱里照着重做一遍。（来源：[[论文/RSI/Scaling Trajectories for Complex Tasks through Recursive Self-Rewrite|Scaling Trajectories for Complex Tas]]）
- 只在一套 harness 下采样会低估模型能力。同一个模型不做任何训练、只换外壳，Terminal-Bench Hard 从 33.0% 升到 66.0%，三套并起来 70.0%；题目做不出来有时缺的是一个合适的外壳。（来源：[[论文/RSI/Scaling Trajectories for Complex Tasks through Recursive Self-Rewrite|Scaling Trajectories for Complex Tas]]）
- 固定回合预算截断会砍好留坏，改用按老师打分在线判断。Fast OPD 2.70 倍速只到 0.434；改成累积打分跌破阈值就停、并缓存做对的前缀，3.73 倍速到 0.475，追平全量蒸馏的 0.477。（来源：[[论文/后训练/Know When to Stop, Where to Restart Accelerating Multi-Turn Agentic On-Policy Distillation|Know When to Stop, Where to Restart:]]）
- 前缀复用必须加质量门槛，否则学生从错误状态接着练、很快崩。论文用 α 等于 -0.8，关掉门槛后曲线很快塌；另外只对新生成本回合算累积和，别把历史回合算进去，否则信号被淹没。（来源：[[论文/后训练/Know When to Stop, Where to Restart Accelerating Multi-Turn Agentic On-Policy Distillation|Know When to Stop, Where to Restart:]]）
- 老师信号断在学生第一次做错那一步：错之前打分正常，错那一步之后转负、效应量 0.30。把早停触发的那一回合保留进 loss 当负信号，不要整条丢掉。（来源：[[论文/后训练/Know When to Stop, Where to Restart Accelerating Multi-Turn Agentic On-Policy Distillation|Know When to Stop, Where to Restart:]]）
- 蒸馏不用丢弃旧轨迹。把老师对每个词的打分 log(π_E/π_ref) 当固定奖励、改成最小二乘回归，旧数据能反复学；每批更 4 次以上约 30 步到顶，回放池版 10 步就到顶，基线要 40 步以上。（来源：[[论文/后训练/An RL View of OPD Least Square Policy Distillation for Sample-Efficient LLM Reasoning|An RL View of OPD: Least Square Poli]]）
- 去掉熵奖励时 Avg@16 只掉 0.46，Pass@16 掉 1.95、12 组全下降。只看单次准确率看不出多样性损失，评测要同时看 Avg@16 和 Pass@16，并把 Pass@k 拉到 64。（来源：[[论文/后训练/An RL View of OPD Least Square Policy Distillation for Sample-Efficient LLM Reasoning|An RL View of OPD: Least Square Poli]]）
- 一个固定老师教不出学生不会的位置。给老师权重加小噪声造 25 个邻近老师，挑老师时不看它自己答题多准，而看它能把标准答案里别人还没抬高的位置抬高多少；12 次平均从 64.63 涨到 66.57，按答题准确率挑只有 65.00。（来源：[[论文/后训练/Better Supervision Is Nearby Neighborhood On-Policy Self-Distillation|Better Supervision Is Nearby: Neighb]]）
- 噪声不是越大越好：σ 往上调覆盖位置一直变多，但学生成绩在 σ 等于 0.002 见顶后往下掉，σ 等于 0.006 只有 63.24。8B 用 σ 等于 0.002，1.7B 和 4B 用 0.0006 和 0.0012，每个尺度都要重新校准。（来源：[[论文/后训练/Better Supervision Is Nearby Neighborhood On-Policy Self-Distillation|Better Supervision Is Nearby: Neighb]]）
- 训练时别把几个老师的分布平均起来当目标：方向可以听最自信的老师，但学谁要另挑一个中间档的，q 等于 0.75 得 66.57，q 等于 1 反而掉到 65.28。概率差太大时 forward-KL 那一项会被阈值截掉、不再产生梯度。（来源：[[论文/后训练/Better Supervision Is Nearby Neighborhood On-Policy Self-Distillation|Better Supervision Is Nearby: Neighb]]）
- 多老师潜在监督会互相打架：混在同一次参数更新里，数学验证分第 30 步掉到 9.8；按领域分开更新、跑满 62 步能到 91.7。做法是一次参数更新只装一个领域的样本，三个领域轮流来。（来源：[[论文/后训练/Latent-MOPD Latent Multi-Teacher On-Policy Distillation|Latent-MOPD: Latent Multi-Teacher On]]）
- 潜在信号全程挂着会训崩，而且对齐分数在涨不能当学得好的证据：中层 CKA 没训练就有 0.99，训练中投影余弦从 0.97 涨到 0.98，同期 MATH-500 掉约 35 分。前 10 步让中间表示权重线性降到 0、token 蒸馏权重升到 1；第 10 步硬切只有 50.45，比完全不用中间表示的 54.15 还差。（来源：[[论文/后训练/LastOPD Taming Collapse in Latent On-Policy Distillation|LastOPD: Taming Collapse in Latent O]]）
- 大规模工具输出不要每次请求整段重发：超过 10 KiB 的结果只完整发两次，第三次起换成一个句柄加 1 KB 头尾摘要，需要原文再按句柄取回。（来源：[[论文/RSI/SoL-Pi Recursively Scaling Auto-Research Loops for Efficient Agent Harness|SoL-Pi: Recursively Scaling Auto-Res]]）
- 日志压缩要带校验和兜底：4 KiB 以上的构建和测试日志交给便宜模型压成一份收据，再用程序核对来源、退出码、原句和大小，核不过就退回原文。（来源：[[论文/RSI/SoL-Pi Recursively Scaling Auto-Research Loops for Efficient Agent Harness|SoL-Pi: Recursively Scaling Auto-Res]]）
- 改完代码再单独发一条测试命令会多一轮往返，把两步合成一次工具调用，请求数从 3 降到 2。（来源：[[论文/RSI/SoL-Pi Recursively Scaling Auto-Research Loops for Efficient Agent Harness|SoL-Pi: Recursively Scaling Auto-Res]]）
- 不同监督信号的原始梯度差会被优化器抹平：三种平均规则的原始梯度余弦只有 0.68，过一遍 Adam 后升到 0.96；把一阶动量清零，不同老师的更新余弦掉到接近 0。要比较监督信号，用不带动量的 SGD 当对照基线。（来源：[[论文/后训练/From Gradients to Capabilities Understanding Multi-Teacher On-Policy Distillation|From Gradients to Capabilities: Unde]]）
- 测试通过不等于代码写得好：让模型在同一工作区比较同组的几份通过代码并排名，再把优势从差的挪给好的，DeepSWE 第 28 步 62.2% 对 50.2%，平均轮数从 132.3 降到 111.6、平均长度从 191.9k 降到 172.9k。（来源：[[论文/后训练/Groupwise Agentic Grading and Advantage Redistribution for Code Agent RL|Groupwise Agentic Grading and Advant]]）
- 微调遗忘来自改动跑到了别的输入上，不是学得太狠。Local Support Learning 在同样的超参扫描里学到顶也不掉旧本事；开关判断从逐词改成看相邻几个词的滑动平均后，误开率从约 16% 降到 5%，旧本事保留率从 96.6% 升到 98.8%。（来源：[[论文/后训练/Local Support Learning|Local Support Learning]]）
- 打分器别用同家族模型自评自。Gagar 用的是被训模型同家族的 SFT 版本，论文没给打分器和人类判断的一致率，质量评估只有 30 道题、一个评审模型；条件允许就补一份人评一致性数据。（来源：[[论文/后训练/Groupwise Agentic Grading and Advantage Redistribution for Code Agent RL|Groupwise Agentic Grading and Advant]]）
## 可复制配方
- 极简 agent 框架只保留一个 invoke 原语：模型现场写一段代码当这次调用的函数体，代码里还能再调 invoke 得到子智能体；把提示词、工具、交互历史都做成 REPL 变量，例如 __history__。（来源：[[论文/Harness/Harness as a Language A Minimalist Agent Framework With Maximal Expressivity|Harness as a Language: A Minimalist ]]）
- 递归工具传递用动态作用域：用 scope 上下文管理器让所有递归子调用自动拿到同一批工具和预算，别一个个显式传给每个子智能体。（来源：[[论文/Harness/Harness as a Language A Minimalist Agent Framework With Maximal Expressivity|Harness as a Language: A Minimalist ]]）
- 评测拆两套提示：任务说明 instructions 和方法提示 guidance 分开写，各自保持任务无关，防止把任务答案偷写进提示。（来源：[[论文/Harness/Harness as a Language A Minimalist Agent Framework With Maximal Expressivity|Harness as a Language: A Minimalist ]]）
- 把 harness 拆成五个能单独下手的槽位：系统提示词、记忆、内置工具、技能、MCP；改动写成打补丁而不是重写整个程序；给 harness 设复杂度上限，规定只有比历史最好更好才留下。（来源：[[论文/RSI/MetaRSI RSI2 A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems T|MetaRSI / RSI2: A Meta-Recursive Sel]]）
- 失败记录写成带层级的条目：直接原因、它在整件事里的作用、背后可复用的机制；让不同算子读同一份记录再决定谁去改。（来源：[[论文/RSI/MetaRSI RSI2 A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems T|MetaRSI / RSI2: A Meta-Recursive Sel]]）
- 数据闭环配方：让智能体造任务、跑轨迹、筛数据，人只在每轮发布前把关；把训练集和开发集里的失败记录指回下一轮要造什么题，数据生产跟着模型能力一起转。（来源：[[论文/RSI/Qwen-Planner-Agent A Closed-Loop AI-for-AI Framework for Real-World Mobile Planner Agents|Qwen-Planner-Agent: A Closed-Loop AI]]）
- 工具和用户信息放模型外面：按当前可用工具裁剪技能提示，工具清单变了提示跟着变；按相关度取记忆证据，不动模型参数。（来源：[[论文/RSI/Qwen-Planner-Agent A Closed-Loop AI-for-AI Framework for Real-World Mobile Planner Agents|Qwen-Planner-Agent: A Closed-Loop AI]]）
- 记忆分四类存：稳定偏好、事件细节、长期事实、以后要做的事；每条带出处，新证据能顶掉旧说法；取用时只当证据给模型、不当命令。（来源：[[论文/RSI/Qwen-Planner-Agent A Closed-Loop AI-for-AI Framework for Real-World Mobile Planner Agents|Qwen-Planner-Agent: A Closed-Loop AI]]）
- 跨 harness 经验重写流程：每题采 K 等于 4 个 runbook，先做 schema 之类硬检查，critic 只看公开任务描述来筛，每个留下的 runbook 在通用外壳下用温度 0.7 重跑 M 等于 4 次，只留通过验证的，训练数据里删掉 runbook 和 critic 对话、只留任务、环境观察和模型自己的动作。2,001 条成功轨迹按这套变成 11,094 条可用轨迹。（来源：[[论文/RSI/Scaling Trajectories for Complex Tasks through Recursive Self-Rewrite|Scaling Trajectories for Complex Tas]]）
- runbook 固定结构：目标终态、关键里程碑、有用检查、恢复策略、常见坑。（来源：[[论文/RSI/Scaling Trajectories for Complex Tasks through Recursive Self-Rewrite|Scaling Trajectories for Complex Tas]]）
- 读时整理记忆的管线：记忆库只存原始轨迹，检索用 BM25 只看任务描述、不训练，整理者输出一段短简报塞进执行者提示词；训练配置 Qwen3-8B、GRPO 100 步、学习率 1e-6、batch 32、组大小 8，只给任务成败奖励，执行者全程冻结；训练库先用基础执行者跑一遍、按真值只留成功轨迹并固定。同一个整理器可直接配 Qwen3-8B、Gemini-2.5-Pro、GPT-5.4。（来源：[[论文/其他/Just-in-Time Memory Learning to Curate Task-Adaptive Memory for LLM Agents|Just-in-Time Memory: Learning to Cur]]）
- 评论家训练配方：评论家损失从 MSE 换成 BCE、价值用 sigmoid 输出；GAE 的 λ 设为 1，优势直接写成 R 减前缀价值；训练顺序改成先 actor 后 critic，用一次额外前向算新旧策略比并对评论家目标重加权，比值落在 0 到 6 外的样本丢掉。（来源：[[论文/其他/PACT From Credit Assignment to Critic Alignment|PACT: From Credit Assignment to Crit]]）
- 最小二乘蒸馏配方：把反向 KL 写成每一步的奖励 log(π_E/π_ref)，用带 Huber 截断的平方损失加熵奖励、在回放池上更新；每批 64 条提问、每题 4 条回答、每批更新 4 次起步，回放版每批 256 步优化。（来源：[[论文/后训练/An RL View of OPD Least Square Policy Distillation for Sample-Efficient LLM Reasoning|An RL View of OPD: Least Square Poli]]）
- 邻近老师配方：1,000 道挑选题、500 个随机种子加 M0 共 501 个候选，按边际 filtered PTA 贪心选 K 等于 25，路由 q 等于 0.75，SCGate 阈值 0.99，选择截断 κ_sel 与 κ 都取 0.06，全词表 forward-KL，100 步，全参数训练；显存不够时先流式跑一遍只存路由元数据，第二遍一次只展开一个老师的分布。（来源：[[论文/后训练/Better Supervision Is Nearby Neighborhood On-Policy Self-Distillation|Better Supervision Is Nearby: Neighb]]）
- 多老师潜在对齐配方：先算老师和学生各层的 CKA 相似度决定对齐哪几层，同门选最后三层、跨家族选接预测头的最后一层；潜在监督写成 α 等于 min(1,u/Tw) 上升、β 等于 max(0,1−u/Tw) 下降的交叉淡出，同门 Tw 取 10、跨家族取 7；多层损失先按层平均，别把系数翻成三倍；只存选中的三层状态，16,384 个位置占用从 2.63 GiB 降到 0.28 GiB。（来源：[[论文/后训练/Latent-MOPD Latent Multi-Teacher On-Policy Distillation|Latent-MOPD: Latent Multi-Teacher On]]）
- 能力组合配方：给每个专家配一个训练前 checkpoint，采样 3,200 条 prompt、每题 4 条不超过 2,048 token 的轨迹，一次缓存各 anchor pair 的 log-ratio，跨 tokenizer 时投影到学生词表；权重加和为 1，α 取 2.0，Adam 全局 batch 64、学习率 1e-6；扫省 token 型权重 0.25 到 0.75 选工作点，AIME 2024 上 0.625 拿到 84.9% 和 15,048 token。（来源：[[论文/后训练/Lightning Weave Improving the Accuracy-Efficiency Frontier of Reasoning Models through Cap|Lightning Weave: Improving the Accur]]）
- 防遗忘微调流程：照常训一个 LoRA 式适配器，训完用当前阶段数据拟合正高斯混合模型，再拿约 100 万 token 的通用文本拟合负混合模型，推理时比两个密度决定开关开不开，最后加一层滑动平均；负混合模型可跨阶段共享，每阶段只多 6.9 MB。（来源：[[论文/后训练/Local Support Learning|Local Support Learning]]）
- 代码 agent 的分档打分表：只看通过测试的候选，按策略是否对路、改动是否精确、是否最小、有没有副作用、是否符合仓库风格五项打分，权重 0.30、0.25、0.20、0.15、0.10；分三档给折扣，最好档 1.0 和 0.9，中间档 0.85 到 0.4 线性铺开，最差档 0.2；重分配倍数上限 1.5；只对既有通过又有失败的组做，全对全错的组先过滤掉；打分与生成异步重叠，打分结果不完整就退回原来的奖励。（来源：[[论文/后训练/Groupwise Agentic Grading and Advantage Redistribution for Code Agent RL|Groupwise Agentic Grading and Advant]]）
- 省 token 的三条固定配置：改文件和跑测试合成一次工具调用；工具输出超过 10 KiB 本地存档、第三次请求起换句柄加 1 KB 头尾摘要；构建和测试日志超过 4 KiB 抽成可核对的收据。开跑前先冻结能力容忍度和效率指标，留出评测集只在候选冻结后跑一次。（来源：[[论文/RSI/SoL-Pi Recursively Scaling Auto-Research Loops for Efficient Agent Harness|SoL-Pi: Recursively Scaling Auto-Res]]）
- 上下文压缩触发点放在计划步骤边界：每做完一个计划步骤估一次，只有预计省下的输入费超过重写缓存的钱才压。（来源：[[论文/RSI/SoL-Pi Recursively Scaling Auto-Research Loops for Efficient Agent Harness|SoL-Pi: Recursively Scaling Auto-Res]]）
## 评测与验证
- 用统一尺子把不同基准拉到一起：以基准进入数据集那年 90 分位模型当 0 分、满分当 100 分。参考值（作者自己定的权重和归并规则）：2026 年研究生科学 85.8、软件工程 52.6、工具智能体 39.9。（来源：[[论文/RSI/The Last AI Built by Humans Toward Genuine Recursive Self-Improvement|The Last AI Built by Humans: Toward ]]）
- 给证据分权重再折价：基准官方表 3、公共 harness 2.5、综合报告 2、模型方自报 1，再统一乘 0.75，用来压低自报成绩。（来源：[[论文/RSI/The Last AI Built by Humans Toward Genuine Recursive Self-Improvement|The Last AI Built by Humans: Toward ]]）
- 评测器按会被攻击来设计：每个 epoch 冻住评测器，换评测器时用独立标准答案校验；已知失败模式包括挑随机种子、从评测接口套测试标签。（来源：[[论文/RSI/The Last AI Built by Humans Toward Genuine Recursive Self-Improvement|The Last AI Built by Humans: Toward ]]）
- 行为评测出题用两段式：先用 CPU 锚点扫全量记录，看工具报错、参数、事件顺序这些硬信号，只把少量候选交给便宜模型确认——每条成功查询扫 12.8 万条会话，只让大模型确认 706 个候选，整条流程平均 552 次调用。上下文按动作、失败、声明三类切点剪到出错前那一步。（来源：[[论文/RSI/TraceDance An Automated System for Building Agent Behavior Benchmarks from Real-World Agen|TraceDance: An Automated System for ]]）
- 自动出题的质量门槛：每题配 0 到 5 分评分表，平均至少 4 分才算过，抽检里 90% 的题评分表质量在 4 分以上、平均 4.75；用多人独立标注估计底子，随机抽 100 道让两人独立检查，两人都确认原记录真出现了目标坏行为的只有 84 道。（来源：[[论文/RSI/TraceDance An Automated System for Building Agent Behavior Benchmarks from Real-World Agen|TraceDance: An Automated System for ]]）
- 别只报总分：TraceDance 上九个前沿模型平均只有 26.7% 过关，「先检查再动手」的题平均 8.1%、工具调用格式题 67.9%；总分第一的模型在「按报错修正」上只拿 27.8%，总分第五的模型有 8 类排第一。按行为类型分开报，并可用同一道题上不同模型第一步选择不同来归因。（来源：[[论文/RSI/TraceDance An Automated System for Building Agent Behavior Benchmarks from Real-World Agen|TraceDance: An Automated System for ]]）
- 蒸馏和 RL 的评测同时报 Avg@16 和 Pass@16，Pass@k 拉到 64；多轮 agent 用 mean@16 和 pass@16，加速比按纯训练每步时间算，不含评测。（来源：[[论文/后训练/An RL View of OPD Least Square Policy Distillation for Sample-Efficient LLM Reasoning|An RL View of OPD: Least Square Poli]] · [[论文/后训练/Know When to Stop, Where to Restart Accelerating Multi-Turn Agentic On-Policy Distillation|Know When to Stop, Where to Restart:]]）
- 微调后的评测按任务形状分组报：短题、工具选择算一档，长推理、终端类算一档，只报一个总平均分会让涨跌互相抵消。（来源：[[论文/后训练/Fine-Tuning DiffusionGemma What Works, What Breaks|Fine-Tuning DiffusionGemma: What Wor]]）
- 能力与遗忘一起看：把新任务成绩画横轴、旧基准平均分画纵轴做散点，一眼看出谁在用掉点换成绩。（来源：[[论文/后训练/Local Support Learning|Local Support Learning]]）
- 准确率和效率同时报：报准确率、平均回答 token、按 base 归一的合成分。Lightning Weave 里 Qwen3.5-4B 上 HMMT 2025 正确率从 59.2% 到 64.0% 且少 10.7% token，LiveCodeBench v5 从 41.7% 到 54.2% 且少 9.6%。（来源：[[论文/后训练/Lightning Weave Improving the Accuracy-Efficiency Frontier of Reasoning Models through Cap|Lightning Weave: Improving the Accur]]）
- 验证 harness 机制能不能跨模型迁移：同一套机制搬到另一个后端后看分数、token、成本三项。SoL-Pi 给出的是保住 94.3% 分数、token 少 44.7%、成本少 33.5%，但触发次数和强度都变低，迁移结论只在两个后端上成立。（来源：[[论文/RSI/SoL-Pi Recursively Scaling Auto-Research Loops for Efficient Agent Harness|SoL-Pi: Recursively Scaling Auto-Res]]）
- 报告统计口径要写清：PACT 的 72.87% 和 67.4% 分别出自 Qwen3.5-4B 加 OpenCode 与 Qwen3.6-35B-A3B 加 Codex 两套设置，Avg@16 和 pass@1 不能直接比；表中 PPO λ 等于 0.95 的 26.31% 是训练崩掉的结果，不能当 PPO 正常水平。（来源：[[论文/其他/PACT From Credit Assignment to Critic Alignment|PACT: From Credit Assignment to Crit]]）
- 做消融时在同一批回答、同一份学生参数上缓存梯度，保证只比权重；统计改动同时看 FP32 主权重和 BF16 权重，别只数 BF16。（来源：[[论文/后训练/From Gradients to Capabilities Understanding Multi-Teacher On-Policy Distillation|From Gradients to Capabilities: Unde]]）
- 验证环境类训练收益会不会随难度放大：背包题规模从 6 乘 5 加到 11 乘 11，冻结的同一个模型仍能造出环境，训练收益从加 0.412 涨到加 0.861。（来源：[[论文/其他/Verifiable Hidden Dynamics Play Generating Agentic RL Environments from Solved Mechanisms|Verifiable Hidden Dynamics Play: Gen]]）
## 成本与预算
- 省 token 的账要按最后能省多少输入费算，不是按压缩率。参考账：Pi 在 EdgeBench 上 51 题 44.8 分、2.15B token；四个机制全上后 42.0 分、1.10B token，token 少 49%，成本从 1,339 美元降到 894 美元。（来源：[[论文/RSI/SoL-Pi Recursively Scaling Auto-Research Loops for Efficient Agent Harness|SoL-Pi: Recursively Scaling Auto-Res]]）
- 把「历史按引用传」和「让模型自写检索代码」算进预算：JAZ 远端回忆 69.9% 对 Letta 61.8%，成本 18.3 美元对 42.1 美元；自改进 AppWorld 74.2% 对 ACE 69.9%，成本 20.9 美元对 30.6 美元。（来源：[[论文/Harness/Harness as a Language A Minimalist Agent Framework With Maximal Expressivity|Harness as a Language: A Minimalist ]]）
- 记忆方案的 token 预算参考：读时整理的 base 版只多 1.9K 输入 token，ReasoningBank 多 10.7K、SkillOS-base 多 13.4K；训练后输入 token 再省约 10%、输出 token 省 13%、步数省 12%。（来源：[[论文/其他/Just-in-Time Memory Learning to Curate Task-Adaptive Memory for LLM Agents|Just-in-Time Memory: Learning to Cur]]）
- 环境生成单价：3,300 个环境每个只花一两美分，适合把环境批次当成可再生资源来用。（来源：[[论文/其他/Verifiable Hidden Dynamics Play Generating Agentic RL Environments from Solved Mechanisms|Verifiable Hidden Dynamics Play: Gen]]）
- 打分开销要专门压：Claude Opus 5 打分每组约 2000 秒，换成自训打分模型降到约 600 秒，再让打分和 rollout 生成错峰；这 600 秒只算打分本身，不等于端到端训练成本。（来源：[[论文/后训练/Groupwise Agentic Grading and Advantage Redistribution for Code Agent RL|Groupwise Agentic Grading and Advant]]）
- 潜在监督的显存开销可以压：只存选中的三层状态，16,384 个位置占用从 2.63 GiB 降到 0.28 GiB；邻近老师的训练开销约为对照方案的 1.42 倍，用噪声造老师比多挂几个模型便宜。（来源：[[论文/后训练/Latent-MOPD Latent Multi-Teacher On-Policy Distillation|Latent-MOPD: Latent Multi-Teacher On]] · [[论文/后训练/Better Supervision Is Nearby Neighborhood On-Policy Self-Distillation|Better Supervision Is Nearby: Neighb]]）
- 预算上限写进代码：用 BudgetPool、IterationLimit、RecursionLimit 当运行框架的一部分，递归子调用自动继承同一批预算，而不是靠人盯。（来源：[[论文/Harness/Harness as a Language A Minimalist Agent Framework With Maximal Expressivity|Harness as a Language: A Minimalist ]]）
- 成本数字不能跨时间比，API 价格会浮动；也不能拿基数不同的数字比，IMO 每通过一题的成本里 Codex 通过 5 题、SoL-Pi 通过 3 题。搜索本身的算力成本要单独记账，SoL-Pi 没报告搜索花了多少算力，也没给搜索广度和深度的 scaling law。（来源：[[论文/RSI/SoL-Pi Recursively Scaling Auto-Research Loops for Efficient Agent Harness|SoL-Pi: Recursively Scaling Auto-Res]]）
## 开放问题
- 一个原语能不能顶替专用记忆和自我改进系统，只在两个 benchmark、两个 GPT-5.4 档位上验证过；弱模型和其他厂商模型没试，所谓 prompt-only 仍靠人手写的交接模板，什么时候该交接是人教的；自改进实验每题都拿到完整测试反馈，真实部署不一定有。（来源：[[论文/Harness/Harness as a Language A Minimalist Agent Framework With Maximal Expressivity|Harness as a Language: A Minimalist ]]）
- 三层算子一起改是否真跑赢基线未知：抓到的材料到方法一节就断了，实验、消融、讨论都没看到；数据算子的认证靠同一个模型盲解一遍比对，只能说前后自洽，说不了它答对了自己本来不会的知识；五级台阶和普查口径由作者自己划定，换一套划法可能得出别的结论。（来源：[[论文/RSI/MetaRSI RSI2 A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems T|MetaRSI / RSI2: A Meta-Recursive Sel]]）
- 重写带来的涨分里有多少来自数据变多分不清：重写版用了 11,094 条轨迹，直接微调只有约 2,001 条，没做同数据量对照；三套外壳解出 759 道题而单套最多 565 道只看覆盖率，benchmark 多半是自己造的，TB2 只有 89 道题。（来源：[[论文/RSI/Scaling Trajectories for Complex Tasks through Recursive Self-Rewrite|Scaling Trajectories for Complex Tas]]）
- 用更省的 harness 去搜更省的 harness 论文自己写明只是设想；机制换后端后触发次数和强度都变低，迁移只在两个后端上看到；消融每次只加一个机制，看不出机制之间的相互作用。（来源：[[论文/RSI/SoL-Pi Recursively Scaling Auto-Research Loops for Efficient Agent Harness|SoL-Pi: Recursively Scaling Auto-Res]]）
- 跨模型家族、跨架构的中间表示对齐没验证：所谓跨家族老师其实都是同骨架、都是 28 层，学生只做了 1.5B 这一档；整个流程只有蒸馏、没有 verifier 奖励，也没和 RL 混着跑；选层靠事先算的 CKA，换一批老师要重算。（来源：[[论文/后训练/Latent-MOPD Latent Multi-Teacher On-Policy Distillation|Latent-MOPD: Latent Multi-Teacher On]]）
- 单次 run 的结论要留余地：LastOPD 每格只跑一次、没有种子和方差，10 步窗口用 MATH-500 选、而 MATH-500 又当主指标报告，等于拿一部分测试信号调参；同血缘那组过渡反而更差，83.42 对 87.22，固定 10 步不是所有情况最优。（来源：[[论文/后训练/LastOPD Taming Collapse in Latent On-Policy Distillation|LastOPD: Taming Collapse in Latent O]]）
- 局部开关式防遗忘的适配器不能合并回原权重，推理成本随阶段数线性增长；开关在旧任务数据上仍会误开约 5% 的词；验证只到 7B、三段，没在强化学习或超长上下文里试。（来源：[[论文/后训练/Local Support Learning|Local Support Learning]]）
- τ²-bench 没有标准训练集，读时整理那篇在那里只试了不训练的版本，多轮工具对话能不能靠 RL 训出来没验证；入库用执行者自己当裁判判成败，可能把错的当对的收进去；BM25 在更大库里会不会拖后腿没测，简报格式按每个基准手写，整理多出来的调用成本也没算进 token 统计。（来源：[[论文/其他/Just-in-Time Memory Learning to Curate Task-Adaptive Memory for LLM Agents|Just-in-Time Memory: Learning to Cur]]）
- PACT 的重要性采样只用当前词元的比值近似整条后续轨迹的连乘，还直接丢掉比值在 0 到 6 外的样本，理论上会引入偏差，论文没有量化；SWE-bench 只领先 2 分，是否落在噪声内无法判断；BCE 优于 MSE 只有一张固定策略预训练曲线支撑。（来源：[[论文/其他/PACT From Credit Assignment to Critic Alignment|PACT: From Credit Assignment to Crit]]）
- LSPD 理论上被证明的是理想乐观版本，实际跑的 Huber 截断加熵项那版没有保证，两者差距没量化；验证只用 Qwen3 家族、只做数学推理，AIME24 和 AIME25 的 Pass@1 上 LSPD 还低于对照方法，它换到的是多采样覆盖、不是单次更准。（来源：[[论文/后训练/An RL View of OPD Least Square Policy Distillation for Sample-Efficient LLM Reasoning|An RL View of OPD: Least Square Poli]]）
- DiffusionGemma 那篇只有一句摘要和几个标签：没有数字、基线、数据量，也没写清是全量微调还是 LoRA，终端任务具体指什么也没说，来源是小红书截图指向的个人博客；作者改成按结果好坏来教的建议完全没被验证过。（来源：[[论文/后训练/Fine-Tuning DiffusionGemma What Works, What Breaks|Fine-Tuning DiffusionGemma: What Wor]]）
- 自动出题的有效率要打折：84% 的确认率意味着约 16% 的题底子不干净，评委给分比人高、评分表相邻档界限不清，原始轨迹不公开、别人无法复现；帮 RSI 闭环只是未来工作。（来源：[[论文/RSI/TraceDance An Automated System for Building Agent Behavior Benchmarks from Real-World Agen|TraceDance: An Automated System for ]]）
- 多老师蒸馏里不动量的 SGD 比 Adam 好只领先 0.3 到 1.0 分，且只跑了 500 步、一套配方、一个 1.7B 模型，没跨规模验证；文中的极端长度差引自别的工作，往更长回答外推要谨慎。（来源：[[论文/后训练/From Gradients to Capabilities Understanding Multi-Teacher On-Policy Distillation|From Gradients to Capabilities: Unde]]）
- 早停加前缀缓存那套在更难的电信域最快只到 0.849，仍低于基线 0.853；轨迹越长，截断后补覆盖越难；只在两个域和 Qwen3 系列上验证，加速比只计每步训练时间、不含评测。（来源：[[论文/后训练/Know When to Stop, Where to Restart Accelerating Multi-Turn Agentic On-Policy Distillation|Know When to Stop, Where to Restart:]]）
- 路线图那篇是综述，里面的数字几乎都是转引别人的论文、技术报告和工程博客，没有重跑实验；HCI 的权重、协议归并和 0.75 折扣都是手工经验值，没做敏感性分析；L4、L5 的证据很薄，元改进那套只有四轮、一个 30B 模型。（来源：[[论文/RSI/The Last AI Built by Humans Toward Genuine Recursive Self-Improvement|The Last AI Built by Humans: Toward ]]）
## 记忆与上下文工程

- 先决定在写入时整理还是读时整理：写入时整理要提前猜未来任务需要什么，猜错就永久丢信息；把库里的原始轨迹换成写入时压好的笔记，ALFWorld 掉 1.7 到 2.9 分、WebShop 掉 6.8 到 8.2 分。默认全留原始轨迹，把整理放到读的时候。
- 检索器先从最便宜的用起：只用 BM25 看任务描述、不训练，也能配三种不同执行者；整理者的训练只给任务成败当奖励，执行者全程冻结。
- 把任务描述从整理者输入里拿掉，它就退化成和任务无关的总结器：不训练时 ALFWorld 最多掉 3.1 分，训练后掉 11.4 分、WebShop 训练后掉 10.4 分。训练后掉得更多，说明 RL 学的是抓这道题要什么，不是把轨迹压得更短。
- 做记忆方案时加一条空检索检验：把检索结果清空后，训练过的方案反而比不训练更低，ALFWorld 最多掉 14.8 分、WebShop 掉 15.2 分，说明提升来自学会蒸馏检索到的经验，不是模型自己凭空会做。
- 上下文预算按只多花多少输入 token 管：读时整理的 base 版多 1.9K，写入时整理的方案多 10.7K 到 13.4K。
- 长输出分层给：超过 10 KiB 先完整给两次、之后换句柄加 1 KB 头尾摘要；超过 4 KiB 的日志抽成可核对收据；压缩点放在计划步骤边界，并且先算省下的输入费是否大于重写缓存的钱。
- 历史按引用传而不是让模型手抄：提示词、工具和交互历史做成代码变量，上下文快满时用交接模板把整段历史按引用交给子智能体，实验里这一条单独贡献了远端回忆从 32% 到 69.9% 的差距。

## 能力保留与遗忘控制

- 防遗忘靠限制改动的生效范围，而不是调小学习率：给权重矩阵的更新配一个只在当前训练数据分布内打开的开关，旧本事保留率从 76.6% 升到 96.6%；高斯混合模型比普通小网络更能做到没见过就关上，而且更省地方。
- 开关判断要平滑：逐词独立判断在旧任务数据上约 16% 的词会误开，改成先看相邻几个词的滑动平均再决定，误开降到 5%、保留率再升到 98.8%。
- 多阶段别合并适配器：每阶段新加一个、用完并回主权重会让阶段之间互相打架，第一阶段后就掉 44%；所有阶段的适配器都留着、各由自己的开关管。
- 挑过拟合点的时候同时看两轴：新任务成绩画横轴、旧基准平均分画纵轴；如果超参只按新任务成绩扫，保留分没参与挑选，防遗忘效果会被高估。
- 会反复改答案的扩散式模型要分组评测：短题和工具选择类通常涨、长推理和终端操作类可能掉，只报总平均分看不出改坏了哪一块；长任务掉点的补救方向是改成按结果好坏给奖励，但这条目前没有对照实验。

## 训练环境与数据生成

- 环境生成倒过来做：先解出数理模型的标准答案，再照着它的决策过程做成有状态工具，让环境动态和评分同源。这样批量造环境很便宜，3,300 个环境每个只花一两美分。
- 具体配方：挑现成运筹模型（库存、路径、背包、LP/QP）按参数批量抽题，用解题器算最优值和默认策略分，冻结 35B 当出题者，用真实文档做场景种子；三条准入检查是能执行、默认值在合理区间、最优值和参考对得上。
- 奖励要把实际收益夹在最优值和默认值之间归一成 0 到 1，只跟可计算的标准比，不用语言模型裁判。
- 会做题不等于会在会变的状态里做决策：同一道优化题写成文字直接答能拿 0.962 分，把参数全告诉它但要一步步操作就掉到 0.231；环境只放行界面调用、不透露参数，难点才落在交互上。
- 验证迁移要看没见过的机制：训练只用三族运筹模型，换到没见过的八族机制也涨分；365 天电商经营里原来五次破产一次，训练后五次全活，平均结余从 54,294 涨到 182,844。
- 规模加大时收益应跟着放大，否则可能是环境太简单：背包题从 6 乘 5 加到 11 乘 11，同一个冻结模型仍能造出环境，训练收益从加 0.412 涨到加 0.861。
- 生成失败的样本要重做或丢掉，评分上界是最优值、在线策略不一定够得着；作者自己也没说策略真的重建了底层模型，所以别把这种环境当成机制理解的证据。

## 我的补充
