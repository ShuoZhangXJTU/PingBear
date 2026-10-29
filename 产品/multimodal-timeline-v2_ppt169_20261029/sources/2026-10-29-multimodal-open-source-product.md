---
date: 2026-10-29
type: industry-insight
topic: "多模态交互的开源产品化与垂直场景"
run_graph: /Users/zhangshuo/Research/.research/industry/runs/20261029T033608-0618a604/graph.json
artifact_revision: rev-e276a4ad424144a295b0ab74eec0b79f
---

# 业界洞察：多模态交互的开源产品化与垂直场景

> **2026-10-29 增补**：Meta Muse 提供闭源全栈 Agent 对照，包含 Secure VM、应用权限、行动审计、支付与 Agent 协议，见 [[业界洞察/2026-10-29-multimodal-meta-muse-update]]。

联网检索候选 40 条 + 本机博客/论文 0 条；正文读取范围见筛选与核验记录。

## 一句话结论与关系变化

决策：暂不投入完整产品建设，只进入低成本的需求与付费验证；下一轮优先调查“企业职场无障碍中的实时视觉协助与远程人工接管”，但它是当前最值得调查的场景假设，不是已经选定的垂直赛道。

依据是：华为、Google、字节已经公开了摄像头问答、镜头引导或音视频连续交互，说明“边看边说、边做边纠正”的产品形态正在形成（web-1、web-5、web-28）；但这些仍是厂商能力与上线信息，没有证明用户会为 AI 的视频理解单独付费。与此同时，Be My Eyes 显示出更接近购买的形态：个人端免费，企业侧由组织购买无障碍管理平台，并可获得远程人工代理（web-30）；Microsoft Seeing AI 又提供了免费视觉辅助基线（web-31）。因此，通用“看画面问答”容易被设备或平台内置能力覆盖，值得先研究的是工作流程、管理能力、人工接管与责任边界是否产生额外价值。

开源路线的优势目前不成立，至少未经同条件验证。Vision-Agents 和 Dograh 的存在只证明技术供给增加（gh-2、gh-5）；还不能证明开源在端到端时延、模型成本、部署可靠性、隐私和总运维成本上优于 Gemini Live 等托管方案（web-5、gh-2）。如果“开源”不是硬约束，应先以托管服务作为产品验证基线；如果它是硬约束，也要等真实任务测试证明控制权或定制化带来的收益足以覆盖自建成本。

下一步只验证三个问题：谁在工作中需要实时看和听、哪类任务用文字/语音/固定界面/人工远程协助解决不好、哪一个组织愿意为什么额外价值买单。若同一任务下替代方案效果相当，或企业只为人工服务和管理平台付费而不为 AI 视觉能力付费，应停止产品化并转做服务工具或继续原型。

## 核心体验变化、技术支撑与取舍

- 体验目标正在从“用户先把现场描述成文字或语音，再得到答案”转向“系统直接共享现场上下文，并在用户行动过程中调整提示”（web-1、web-5、web-28）。这是产品形态变化，不等于需求或付费已经验证。
- 持续协作与单次识别不是同一能力。镜头引导体现了根据新画面继续纠错的方向，但华为官方画面问答与第三方“偏静态识别”评价存在冲突，不能据此确认消费产品已经稳定完成动态任务闭环（web-1、web-5、web-14）。
- 消费端能力多由手机、模型平台或免费应用承载，开发者或终端平台可能更容易通过入口、预装和品牌分发获得使用；企业端则出现组织授权和人工代理，二者购买者与责任边界不同（web-1、web-28、web-30、web-31）。
- 企业无障碍场景的差异不只来自画面理解，还包括组织管理、培训、远程人工接管和工作流程；免费个人应用覆盖了基础视觉辅助，因此付费方案必须证明管理、支持或可靠性带来的额外价值（web-30、web-31）。
- 开源框架提供模型、数据和部署控制的可能性，但把视频传输、模型兼容、安全更新、并发运维、断线恢复和现场支持责任一并交给建设方；托管能力降低集成门槛，却增加供应商与数据边界依赖，当前没有同条件比较（web-5、gh-2、gh-5）。
- 整体成本不能只比较模型调用，还要看设备、网络、实时传输、实施配置、人员培训、误判纠正、人工接管、合规与客服；这些成本尚无数据，不能声称开源更便宜（gh-2、web-30）。
- 产品层级已经并行出现：消费端应用、企业付费平台、免费公共服务、开源开发框架和自托管工具。现有材料没有证明必须依次经历“组件—开发者工具—垂直应用”，因此不能把同时存在误读为演化顺序（web-30、web-31、gh-2、gh-5）。
- 技术能力供给和市场价值必须分开判断：仓库存在、产品上线或演示成功只能证明“能做”，不能证明用户重复使用、组织购买或形成产品市场匹配（web-1、web-5、gh-2、gh-5）。

## 竞品清单（对比底稿）

| 竞品 | 公司 | 形态 | 具体做什么 | 交互方式 | 场景 | 成熟度 |
|---|---|---|---|---|---|---|
| 小艺看世界 | 华为 | 手机消费端内置的多模态助手功能 | 打开摄像头后，对准对象并直接说话，助手按画面内容回复。 | 用户持机对准现场，以自然语言发问；官方说明展示的是一问一答式画面协助。 | 消费用户在真实环境中识别、理解和咨询画面对象。 | 已有公开消费产品帮助页；持续理解动态画面和实时纠错能力存在来源冲突，尚未核验。 |
| Guided Vision in Gemini Live | Google | 托管式实时多模态助手能力 | 在摄像头实时流中理解画面，并通过自然语言指导用户调整镜头。 | 系统根据当前画面提示横向平移、下倾或后退，用户调整后再继续互动。 | 需要“看现场并帮助用户取得可用画面”的实时视觉协助。 | Google 博客显示已推出；独立任务成功率、端到端时延和不同网络条件下的表现未知。 |
| SeedRealtime / 豆包 | 字节跳动 | 融合音频、视频和文本的全双工模型与消费应用能力 | 在连续多模态流上做到边看、边听、边说。 | 用户以连续音视频交互，系统边接收现场信息边回应。 | 连续多模态自然交互及消费级实时陪伴、协助。 | 厂商博客称已在豆包 App 全量上线；实际覆盖、稳定性、任务效果和付费价值未独立验证。 |
| Be My Eyes Workplace | Be My Eyes | 企业无障碍管理平台，叠加远程人工代理服务 | 个人端免费；企业端以组织授权方式提供无障碍管理，并可配置受过培训的远程人工代理。 | 使用者在工作场景请求视觉协助；组织负责采购、配置和管理，人工代理可在需要时接管。 | 企业职场无障碍、远程视觉协助和组织级支持流程。 | 公开存在企业收费形态和人工服务；价格、客户数、续费、服务工时及 AI 与人工收入占比未知。 |
| Seeing AI | Microsoft | 免费消费级视觉辅助应用 | 通过摄像头为视障用户朗读文字、人物、物体和场景。 | 用户用摄像头扫描周围内容，应用将视觉信息转为语音。 | 个人视觉无障碍与日常环境理解。 | 公开免费应用；使用频率、任务效果、用户留存和商业影响未给出。 |
| Vision-Agents | Stream | 开源视频理解 Agent 框架 | 提供构建语音和视觉 Agent 的积木，宣称支持任意模型和视频源，并依托边缘网络提供低延迟体验。 | 开发者自行接入模型、视频源和业务逻辑，组装可观看和理解的 Agent。 | 团队自建实时视频 Agent 或快速搭建多模态参考实现。 | 仓库及其定位可见；独立延迟、并发、可靠性、许可证、部署成本和生产案例未验证。 |
| Dograh | Dograh | 可自托管的开源语音 Agent 平台 | 提供可视化工作流、快速测试，并可通过 MCP 让编码助手设计或修改语音 Agent。 | 开发或运营人员配置语音工作流、测试 Agent，并通过编码助手迭代。 | 自托管语音 Agent，以及托管语音服务的开源替代。 | 仅能作为语音工作流和自托管路线的参考；不是摄像头实时理解能力的直接证据。 |

## 场景拆解

### 企业职场无障碍中的实时视觉协助与远程人工接管

- 谁在做：最终使用者是需要在工作中读取资料、识别环境或理解现场的员工；付费方是企业无障碍、人事或相关业务管理者；交付方负责组织配置、培训和人工接管。
- 做法差异：当前材料中唯一同时显示真实使用任务、组织采购形态和人工兜底角色的候选。其价值假设是组织愿意为无障碍工作流程、管理能力和可靠接管付费，而不一定为通用画面问答付费。

### 消费用户日常看物体、问环境、获得镜头引导

- 谁在做：手机或应用用户；付费方可能是设备或平台厂商，材料未明确最终由谁为 AI 能力单独付费。
- 做法差异：已有多个厂商展示或上线相关能力，并存在免费视觉辅助基线；体验已可见，但独立需求、重复使用和商业变现证据不足。

### 开发者基于开源框架搭建视频 Agent

- 谁在做：负责模型接入、实时音视频、工具调用和运维的开发者团队；最终采购者和付费者未知。
- 做法差异：开源构件和自托管平台已经存在，适合作为技术路线参考；仓库热度与架构说明不能证明客户愿意购买，也不能证明比托管服务总成本更低。

## 怎么变现

| 模式 | 代表 | 谁付钱 | 证据 |
|---|---|---|---|
| 个人端免费，企业端按组织授权提供无障碍管理平台，并叠加远程人工代理 | Be My Eyes Workplace | 采购无障碍服务的企业或组织 | web-30 |
| 设备或消费应用内置视觉能力；是否单独收费材料未说明 | 华为小艺看世界、Gemini Live、豆包/SeedRealtime、Microsoft Seeing AI | 材料中未说明；可能来自设备、平台或免费公共服务，不能认定用户为 AI 视觉功能单独付费 | web-1、web-5、web-28、web-31 |
| 开源框架或自托管工具，由开发者自行集成和运营；收费与可持续收入方式材料未说明 | Stream Vision-Agents、Dograh | 材料中未说明 | gh-2、gh-5 |

## 可商用变现的切入点（待验证）

### 先围绕企业职场无障碍做小规模“AI 实时视觉协助 + 人工接管”验证，而不是先做通用实时多模态平台

- 目标客户：企业无障碍或人事等采购团队付费；职场中的视觉辅助使用者使用；运营团队负责配置、管理和人工接管。
- 为什么现在能做：已有企业组织付费和无障碍管理形态，同时免费个人应用构成现实基线，消费设备已展示摄像头交互；这个组合适合低成本检验企业是否愿意为 AI 增量价值付费，但目前只是调查优先级。
- 怎么收钱：可验证的候选收费路径是组织授权、无障碍管理和远程人工协助；材料没有价格、合同、续费或 AI 与人工服务的收入拆分，不能视为已验证收入。
- 壁垒：可能的壁垒是企业工作流程整合、权限与配置、人员培训及人工接管能力；模型和开源代码本身是否构成壁垒尚未证明。
- 风险：企业可能主要因合规、管理或人工帮助付费，而非 AI 视觉理解；免费个人产品可能已经满足基础需求；误判、隐私、可靠性和人工接管责任会扩大交付成本。

## 空白与机会

- **空白**：缺少目标客户的访谈原声和任务日志，无法确认实时看与听相比文字、语音、固定界面和人工流程到底解决了什么额外问题。
- **空白**：缺少任务频率、单次耗时、错误代价、当前做法和切换阻碍，不能判断哪类痛点足够频繁或昂贵。
- **空白**：厂商展示的摄像头交互与第三方“偏静态识别”评价可能对应不同版本、设备或任务；缺少横评全文、时间、样本、任务设计和评分方法。
- **空白**：没有独立测试端到端时延、理解成功率、连续工作时间、断线率、误解纠正次数和人工接管率。
- **空白**：缺少真实报价、合同金额、购买者身份、续费、流失、销售周期、实施工时和支持成本，尚未形成付费与复购证据链。
- **空白**：没有在同一任务、模型和网络条件下比较开源框架、托管服务、通用框架自建和内部原型，开源路线的实际优势未知。
- **空白**：产品应做垂直应用、开发者工具还是底层组件尚未确定；候选场景的客户入口、购买责任和交付边界也不清楚。
- **空白**：“开源”是否为硬约束、内部是否有客户入口和试用资源，以及预算、人员、时间窗口、目标市场和 Go/No-Go 条件均未知。
- **空白**：中国与全球市场是否应共用需求、监管和付费假设尚未说明，不能直接迁移案例。
- **机会**：P0 场景调查：分别访谈最终使用者、企业采购方和运营交付团队，先还原当前工作流程、失败案例、替代方案和采购理由。前提是只做需求验证；代价是访谈和流程记录投入；最小验证是小样本真实任务追踪；若实时多模态与既有方案解决效果相当，或组织只愿购买人工服务，就停止向产品化推进。
- **机会**：P0 同任务对照：让候选职场任务分别经过实时多模态、纯文字、纯语音、固定界面和人工远程协助，记录完成情况、耗时、误解与纠正次数、接管次数和最终结果。该对照直接决定“必须实时看和听”的假设能否成立；若差异不稳定，则回到任务筛选。
- **机会**：P0 付费拆分：向采购方确认无障碍管理、AI 协助和人工代理分别解决什么问题，并收集真实报价或合同类型。若组织无法说明 AI 的额外价值，应把机会降级为管理或人工服务工具；若确认 AI 带来可重复的工作结果，再讨论产品形态。
- **机会**：P1 路线基准：在开源不是硬约束时，先使用一个托管实时能力作为体验基线，再比较 Vision-Agents 等开源方案的控制权、隐私、定制化和总交付成本。只有在同任务下获得可测的净收益时才值得继续开源产品化（web-5、gh-2）。
- **机会**：P1 边界决策：先取得团队对“开源是否为硬约束”的明确答复，并补充内部客户入口、已有试用数据和投入边界。缺少这些条件时，不能把场景调查直接升级成产品建设。
- **机会**：暂缓通用实时多模态平台、通用开发者工具和垂直赛道承诺。当前证据只支持验证企业职场无障碍优先级，不支持宣布该赛道胜出或设定市场成功门槛。

## 本轮收口与待补证据

候选证据 40 条；深核 8 条。未选条目保留，不表示被证伪。
此处是材料核验，不表示实际运行产品测试。

- 深核 `web-1`：入选（需求与替代方案）—[华为官方说明](https://consumer.huawei.com/cn/support/content/zh-cn16053374/)描述了摄像头实时音视频对话、识别对象，以及用户可在回答过程中打断并改变目标。这是“持续看＋说＋修正任务”的直接实例；深核应验证真实高频任务、设备覆盖，以及免费系统能力对独立产品的挤压。
- 深核 `web-5`：入选（垂直任务必要性）—[Guided Vision](https://blog.google/innovation-and-ai/products/gemini-app/guided-vision-gemini-live/)面向视障用户，覆盖读小字、找物、辨色，并在镜头不对时主动提示调整方向。固定拍照问答难以完成该闭环；需核验误报、实际可用性及人工协助的不可替代部分。
- 深核 `web-14`：入选（体验差异与证据缺口）—候选摘要称该跨品牌测试发现华为偏静态识别、OPPO支持视频通话识别、小米缺少环境识别；当前可抓正文未完整呈现这部分，需回看原始视频和测试方法，作为“实时多模态是否真的优于静态视觉”的反例核验。
- 深核 `web-28`：入选（托管方案与竞争水位）—[SeedRealtime](https://seed.bytedance.com/zh/blog/seedrealtime-audio-visual-full-duplex-llm-released-toward-omni-modal-natural-interaction)官方称其原生音视频全双工并已在豆包全量上线，展示菜单翻译、设备操作纠错和嘈杂环境对话。深核其评测方法、延迟、接入方式和价格，判断开源路线的真实差异是否只剩自托管与数据控制。
- 深核 `web-30`：入选（付费与交付路径）—[Be My Eyes Workplace](https://www.bemyeyes.com/business/workplace/)把 AI、人工兜底、SSO、SOC 2和远程协助组合成企业无障碍服务，接近可收费的完整交付而非单点模型。页面未披露价格和续费，需进一步核查合同、客户结果、服务工时及复购。
- 深核 `web-31`：入选（价格天花板与反例）—[Seeing AI](https://www.seeingai.com/)明确以免费应用提供环境朗读、阅读、照片描述和商品识别。它用于检验免费公共服务是否已经覆盖主要任务，以及付费产品究竟必须额外提供什么价值。
- 深核 `gh-2`：入选（开源能力边界）—[Vision-Agents](https://github.com/getstream/Vision-Agents)可组合任意模型和视频源构建语音视觉 Agent，但页面同时强调依赖 Stream 的边缘网络。深核许可证、实际依赖、集成和运维成本；仓库热度不作为需求证据。
- 深核 `gh-5`：入选（开源产品化类比）—[Dograh](https://github.com/dograh-hq/dograh)以自托管方式对标 Vapi/Retell，包含可视工作流、BYOK、MCP和电话能力，可检验开源开发者产品的部署、服务与收费模式；但其范围是语音而非视频，不能直接证明多模态产品机会。
- 暂缓 `web-2`：暂缓—“指哪问哪”是有价值的交互形态，但单一功能不足以区分必要需求与演示效果；若 web-5、web-14证实空间指代是关键门槛，再补入。
- 暂缓 `web-3`：暂缓—AI 眼镜形态与 web-27、web-16 重叠，且当前证据偏识别功能，缺少持续协作和用户收益，保留作设备端样本。
- 暂缓 `web-4`：暂缓—系统级助手与跨设备服务能说明渠道和捆绑优势，但 web-1 已更具体地证明实时对话及打断；本轮不重复深核功能清单，保留作下一轮渠道比较。
- 暂缓 `web-6`：暂缓—基础操作说明只证明入口存在，不能证明需求、付费或持续使用，保留作可用性复核材料。
- 暂缓 `web-7`：暂缓—与 web-5 同属 Guided Vision，任务清单有边际价值但无明显独立证据；深核 web-5 时用于核对限制与适用人群。
- 暂缓 `web-8`：暂缓—通用实时视频能力未绑定具体任务、痛点或收费方式，保留作托管服务能力基线。
- 暂缓 `web-9`：暂缓—演示可证明交互存在，但不能证明愿意付钱，也无法替代本轮对交付成本和复购证据的选择。
- 暂缓 `web-10`：暂缓—Apple 视觉智能偏系统入口和工具箱，缺少持续双向协作证据，保留作手机厂商替代方案。
- 暂缓 `web-11`：暂缓—多模态功能清单不能说明哪个任务必须实时看和听；作为静态图片、相机输入和圈屏方案的边界样本保留。
- 暂缓 `web-12`：暂缓—视觉、文档、屏幕等入口过宽，当前无法判断是捆绑功能还是可独立收费的任务，保留作中国替代样本。
- 暂缓 `web-13`：暂缓—二手横评提供体验差异线索，但测试方法、样本和引用透明度有限；先深核更贴近具体任务的 web-14，再决定是否回补。
- 暂缓 `web-15`：暂缓—重点是手机智能体任务执行，不是实时音视频协作；可帮助区分“会看图”与“持续看着用户做事”的能力边界。
- 暂缓 `web-16`：暂缓—代表性较强，但消费硬件价格与功能采用不等于愿意为多模态软件付费；若下轮优先评估眼镜渠道，应提升优先级。
- 暂缓 `web-17`：暂缓—显示和手势是重要设备演进，但离本轮“实时看听协作是否值得产品验证”较远，保留作长期渠道信号。
- 暂缓 `web-18`：暂缓—平台级且生态尚早，短期难回答交付和付费；保留作长期渠道与生态竞争反例。
- 暂缓 `web-19`：暂缓—主动式 AI 超出当前的实时协作范围，并引入更高可信度、打扰和隐私要求；保留作产品边界反例。
- 暂缓 `web-20`：暂缓—结合屏幕和工作数据的企业能力很强，但不是物理环境摄像头任务；保留用于区分屏幕上下文与真实场景视觉。
- 暂缓 `web-21`：暂缓—主要是电视内容问答，往往可用遥控、搜索或固定界面替代，不能证明实时多模态的必要性。
- 暂缓 `web-22`：暂缓—摄像头看护偏持续感知和异常监控，而非双向协作，是重要边界反例；若以后扩展到家庭监控场景再深核。
- 暂缓 `web-23`：暂缓—电视功能与模型接入偏展示，缺少可辨别的高频任务、体验差异和收费路径。
- 暂缓 `web-24`：暂缓—车内空间感知对应高频任务，但强绑定整车传感器和 OEM 集成；若优先汽车场景，可直接升级为重点。
- 暂缓 `web-25`：暂缓—与 web-24 同属车载、强绑定车身传感器；先保留一家代表，避免重复消耗深核预算。
- 暂缓 `web-26`：暂缓—与 web-5、web-30、web-31 同属视觉无障碍，且当前页面抓取无可读正文；先通过三个代表验证需求，再回补国内产品差异。
- 暂缓 `web-27`：暂缓—3999元硬件和生态功能说明存在消费渠道，但硬件售价不能证明用户愿为实时多模态单独付费；保留作终端捆绑方案。
- 暂缓 `web-29`：暂缓—家庭智能体覆盖过宽，缺少具体任务结果和支付证据，保留作家庭场景候补。
- 暂缓 `web-32`：暂缓—按量收费可帮助估算 API 交付成本，但主要处理上传视频，不是实时打断式协作；后续用作成本基线。
- 暂缓 `web-33`：暂缓—成熟的以图搜商品是一步式固定任务，恰好可作窄替代方案；不能回答持续对话、本地部署或实时指导价值。
- 暂缓 `gh-1`：暂缓并排除出技术路线深核—仓库已标记 deprecated，不能作为可维护的开源底座；仅保留作失败与迁移案例。
- 暂缓 `gh-3`：暂缓—技术相关性强，但现有证据主要是研究目标和试用平台，缺少许可证、维护、集成与商业采用证据；待验证技术路线后再回补。
- 暂缓 `gh-4`：暂缓—它是实时音视频传输基础设施，不是完整产品；保留为延迟、并发、带宽和运营成本核验对象。
- 暂缓 `gh-6`：暂缓—与 gh-2、gh-4 能力重叠，当前先用 Vision-Agents 判断开源能力边界；需要模型组合和运行时细节时再展开。
- 暂缓 `gh-7`：暂缓—通用编排框架适合比较自建路线，但单凭框架无法判断垂直机会；保留作 Vision-Agents 之外的 self-build 对照。

### 仍未解决

- 缺少目标客户的访谈原声、当前工作流程、任务频率、失败成本和切换阻碍，无法判断哪类垂直任务具有高价值。
- 缺少可获得、可核验的试用日志和任务级指标，包括识别或理解成功率、持续工作时间、断线率、人工接管率及不同网络条件下的表现。
- 没有实际运行测试或独立复现，厂商页面的能力说明与第三方横评的负面发现之间无法完成版本化对账。
- 缺少真实报价、合同金额、购买者身份、续费、流失、销售周期和实施工时，无法建立付费、复购与交付可行性证据链。
- 缺少开源方案与托管服务在相同任务、模型和网络条件下的端到端时延、调用成本、并发能力、隐私和合规比较。
- 应澄清“开源”是硬约束还是可选实现方式；该选择会改变托管服务与自托管路线的比较优先级。
- 需要补充内部业务入口、现有客户资源及预算、人员和时间边界；在这些信息缺失时，不能判断是否值得投入产品开发。
- 当前最多支持继续做低成本需求验证：选择少量候选任务，补充用户访谈和小规模试用，并按事先约定的结果记录市场证据。现有材料不足以证明产品市场匹配，也不足以直接排除需求。
- 华为小艺看世界是否已经达到持续理解动态画面并完成实时协作，存在来源冲突，当前不能下确定结论。：缺少第三方横评全文、测试时间、软件版本、样本、任务设计和评分方法，无法判断“偏静态”的严重程度、发生条件或是否适用于当前版本。
- 当前材料尚不能证明某类垂直任务“必须依赖”实时多模态交互，也不能证明这类痛点足够高频或昂贵。：缺少任务频率、单次耗时、失败成本、人工成本、用户当前做法和切换意愿。仅凭产品存在不能证明需求刚性。
- 产品应采用垂直应用、开发者工具还是底层组件，以及应优先进入哪类垂直场景，现有证据不足以决定。：没有定义候选场景的筛选标准、内部业务入口、客户类型或授权范围，不能合理指定垂直赛道胜者。
- 开源视频 Agent 路线相比直接采购 Gemini Live 等托管服务、基于通用框架自建或继续使用内部原型，是否具有实际优势，当前无法核验。：缺少可比版本、报价、自托管成本、模型调用费用、并发限制、端到端时延、合规边界、许可证和故障处置数据。
- 是否存在可验证的付费、复购、交付成本和服务能力路径，材料尚不能确认。：缺少付费方、使用频率、续费原因、获客成本、部署周期、支持成本、SLA 责任和毛利数据。
- 这批材料不支持把仓库热度、公开演示或产品上线当作产品市场匹配或实际付费证据。：无法据此排除潜在需求，只能说明需求、付费意愿和商业可持续性仍未解决。
- 尚无同一任务下实时多模态、纯文本、纯语音、固定界面和人工流程的比较，因此不能证明任何垂直任务必须依赖实时看和听。
- 缺少任务频率、单次耗时、失败成本、用户当前做法、切换阻碍和重复使用情况，无法判断痛点是否足够频繁或昂贵。
- 厂商展示的摄像头交互与第三方“偏静态识别”评价可能对应不同版本、设备和任务；缺少全文、测试时间、样本和评分方法，无法完成版本化对账。
- 没有端到端时延、理解成功率、连续工作时间、断线率、人工接管率及不同网络条件下的独立测试，无法确认体验机制能够稳定成立。
- 缺少真实客户身份、合同金额、报价、购买者、销售周期、续费、流失、实施工时和服务毛利，付费与复购路径仍未验证。
- 尚未在相同模型、网络和任务条件下比较开源框架、托管服务、通用框架自建和内部原型，开源路线的实际优势及成立条件未知。
- 产品应做垂直应用、开发者工具还是底层组件尚未确定；候选场景的客户入口、购买责任、交付边界和竞争壁垒也没有充分材料。
- 是否已有内部客户、试用日志和业务入口未知，预算、人员、时间窗口、目标市场及 Go/No-Go 门槛也未给出，因此不能据此判断值得投入产品开发。

## 接下来盯什么

- 出现企业为 AI 实时视觉协助本身单独报价、采购或续费的证据；若始终只有组织和人工服务可收费，应下调 AI 产品假设（web-30）。
- 真实任务显示持续纠错比单帧识别显著改变行动结果；若只能做一次性识别，应回到文字、图片上传或固定流程方案（web-5、web-14）。
- 人工接管比例、响应时间和支持成本被披露；若商业价值主要来自人工服务，产品路径可能应转为服务与管理工具（web-30）。
- 华为、Google 或字节推出可核验的新版动态理解能力，并能解决第三方对静态识别的质疑；这会提高消费能力基线，也可能压低独立产品空间（web-1、web-5、web-14、web-28）。
- 免费视觉辅助产品扩展到组织管理或更强实时协助；这会直接改变企业付费方案相对免费基线的差异（web-31）。
- Vision-Agents 或同类开源方案出现独立延迟、并发、部署成本和生产案例证据；只有可维护的总成本得到证明，开源优势才可能成立（gh-2）。
- Dograh 或同类工具增加视觉能力并公布自托管总成本；当前材料只能把它当语音工作流参考，不能外推到摄像头实时理解（gh-5）。
- 获得真实试用日志或合同数据，显示重复使用、购买和续费。出现该证据时应重新审视“只做验证、不建设产品”的当前决定。

## 竞品证据

### 小艺看世界
- 华为官方说明支持打开摄像头、对准对象并进行画面问答。（[小艺看世界：边聊边看陪你看世界](https://consumer.huawei.com/cn/support/content/zh-cn16053374/)）
- 第三方横评摘要称其描述丰富但偏静态识别；缺少全文、版本、样本和评分方法。（[六大品牌手机无障碍横评（第三方）](https://ishare.ifeng.com/c/s/v002fU5TbWRcghloX-_0jPg--3ktGbq904BJ95hOTm5GQb6VI__)）

### Guided Vision in Gemini Live
- Gemini Live 在摄像头实时流上提供自然语言镜头调整引导。（[Guided Vision launches in Gemini Live](https://blog.google/innovation-and-ai/products/gemini-app/guided-vision-gemini-live/)）

### SeedRealtime / 豆包
- SeedRealtime 宣称融合音频、视频、文本并已在豆包 App 全量上线。（[SeedRealtime 音视频全双工](https://seed.bytedance.com/zh/blog/seedrealtime-audio-visual-full-duplex-llm-released-toward-omni-modal-natural-interaction)）

### Be My Eyes Workplace
- Be My Eyes 个人端免费，企业端按组织授权提供无障碍管理平台和远程人工代理。（[Be My Eyes Workplace](https://www.bemyeyes.com/business/workplace/)）

### Seeing AI
- Seeing AI 以免费公共服务形态用摄像头为视障用户朗读文字、人物、物体和场景。（[Seeing AI](https://www.seeingai.com/)）

### Vision-Agents
- Stream 将 Vision-Agents 定位为可使用多种模型和视频源的开源视频 Agent 框架。（[getstream/Vision-Agents](https://github.com/getstream/Vision-Agents)）

### Dograh
- Dograh 自称可自托管的 Vapi/Retell 替代，功能重心是语音 Agent。（[dograh-hq/dograh](https://github.com/dograh-hq/dograh)）

## 全部来源

- 网页 `web-1` [小艺看世界：边聊边看陪你看世界](https://consumer.huawei.com/cn/support/content/zh-cn16053374/)
- 网页 `web-2` [小艺看世界支持指向问答](https://consumer.huawei.com/cn/support/content/zh-cn16093813/)
- 网页 `web-3` [华为 AI 眼镜小艺看世界功能](https://consumer.huawei.com/cn/support/content/zh-cn16089939/)
- 网页 `web-4` [华为小艺官方介绍](https://consumer.huawei.com/cn/mobileservices/celia/)
- 网页 `web-5` [Guided Vision launches in Gemini Live](https://blog.google/innovation-and-ai/products/gemini-app/guided-vision-gemini-live/)
- 网页 `web-6` [How to use your Gemini Live camera](https://blog.google/products-and-platforms/products/gemini/gemini-live-camera-how-to/)
- 网页 `web-7` [Get audio descriptions with Guided Vision in Gemini Live](https://support.google.com/gemini/answer/18365638)
- 网页 `web-8` [ChatGPT Voice mode with live video](https://m.chatgpt.com/features/voice-with-video/)
- 网页 `web-9` [Vision and voice in ChatGPT](https://academy.openai.com/en/public/videos/vision-and-voice-in-chatgpt-2025-04-11)
- 网页 `web-10` [Use visual intelligence on iPhone](https://support.apple.com/guide/iphone/use-visual-intelligence-iph12eb1545e/ios)
- 网页 `web-11` [Bixby 的多模态交互方式](https://www.samsung.com.cn/support/mobile-devices/how-to-use-multimodal-interaction-on-bixby/)
- 网页 `web-12` [小爱同学（超级小爱）官网](https://hyperxiaoai.xiaomi.com/)
- 网页 `web-13` [手机 AI 功能横评（第三方）](https://k.sina.com.cn/article_7879776378_1d5abd87a06801gjq4.html)
- 网页 `web-14` [六大品牌手机无障碍横评（第三方）](https://ishare.ifeng.com/c/s/v002fU5TbWRcghloX-_0jPg--3ktGbq904BJ95hOTm5GQb6VI__)
- 网页 `web-15` [复旦系统软件与安全实验室手机智能体测评](https://security.fudan.edu.cn/news/content/2026-04-23-002/)
- 网页 `web-16` [Ray-Ban Meta：Hey Meta, look and...](https://about.fb.com/news/2024/09/ray-ban-meta-glasses-new-ai-features-and-partner-integrations/)
- 网页 `web-17` [Meta Ray-Ban Display + Neural Band](https://about.fb.com/news/2025/09/meta-ray-ban-display-ai-glasses-emg-wristband/)
- 网页 `web-18` [Android XR glasses with Gemini](https://blog.google/products-and-platforms/platforms/android/android-xr-gemini-glasses-headsets/)
- 网页 `web-19` [Snap SPECS Intelligence](https://investor.snap.com/news/news-details/2026/Snap-Inc--Introduces-SPECS-Intelligence-an-Anticipatory-AI-Service/default.aspx)
- 网页 `web-20` [Microsoft Copilot Vision](https://support.microsoft.com/en-us/microsoft-365-copilot/use-vision-microsoft-365-copilot)
- 网页 `web-21` [Samsung TV Vision AI Companion](https://news.samsung.com/global/samsung-unveils-vision-ai-companion-at-ifa-2025-launching-a-new-era-of-ai-powered-displays)
- 网页 `web-22` [Samsung TV 摄像头看护](https://www.sammobile.com/news/2025-samsung-tvs-monitor-pets-family-inbuilt-camera/)
- 网页 `web-23` [海信电视星海大模型 + DeepSeek](https://www.hisense.com/news/1156.html)
- 网页 `web-24` [理想同学：空间多模态感知](https://tech.ifeng.com/c/8VQsbCGqsHR)
- 网页 `web-25` [蔚来 NOMI GPT 端云多模态](https://auto.gasgoo.com/news/202404/12I70388757C601.shtml)
- 网页 `web-26` [vivo 看见](https://accessibility.vivo.com/accessibility/see)
- 网页 `web-27` [夸克 AI 眼镜 S1](https://www.ithome.com/0/891/932.htm)
- 网页 `web-28` [SeedRealtime 音视频全双工](https://seed.bytedance.com/zh/blog/seedrealtime-audio-visual-full-duplex-llm-released-toward-omni-modal-natural-interaction)
- 网页 `web-29` [小度「超能小度」家庭智能体](https://www3.xinhuanet.com/tech/20260908/c5c845b67dde4903b490ceadd743eb37/c.html)
- 网页 `web-30` [Be My Eyes Workplace](https://www.bemyeyes.com/business/workplace/)
- 网页 `web-31` [Seeing AI](https://www.seeingai.com/)
- 网页 `web-32` [TwelveLabs 视频理解 API](https://www.twelvelabs.io/pricing)
- 网页 `web-33` [淘宝拍立淘图片搜索 API](https://developer.aliyun.com/article/1752711)
- 网页 `gh-1` [landing-ai/vision-agent](https://github.com/landing-ai/vision-agent)
- 网页 `gh-2` [getstream/Vision-Agents](https://github.com/getstream/Vision-Agents)
- 网页 `gh-3` [om-ai-lab/VLX-Flow](https://github.com/om-ai-lab/VLX-Flow)
- 网页 `gh-4` [livekit/livekit](https://github.com/livekit/livekit)
- 网页 `gh-5` [dograh-hq/dograh](https://github.com/dograh-hq/dograh)
- 网页 `gh-6` [livekit/agents](https://github.com/livekit/agents)
- 网页 `gh-7` [pipecat-ai/pipecat](https://github.com/pipecat-ai/pipecat)

检索词：官方能力：site:docs.livekit.io agents vision video turn-taking pricing self-host；官方能力：site:github.com/pipecat-ai/pipecat README video vision interruption license releases；官方能力：site:getstream.io vision-agents camera video edge pricing dependencies；官方能力：site:github.com/om-ai-lab/VLX-Flow streaming VLM latency benchmark limitations；官方能力：site:dograh.com multimodal vision video self-host BYOK；转型与失败：site:github.com/landing-ai/vision-agent deprecated replacement issues；官方能力：site:docs.cloud.google.com Gemini Live API video latency limitations pricing；官方能力：site:developers.openai.com realtime video WebRTC pricing regional availability；官方能力：site:learn.microsoft.com Voice Live API vision video multimodal；官方能力：site:docs.aws.amazon.com Nova Sonic bidirectional streaming video；官方能力：site:agora.io conversational AI video vision pricing SLA；官方能力：site:vapi.ai pricing concurrency HIPAA observability status；官方能力：site:retellai.com pricing concurrency HIPAA observability status；官方能力：site:consumer.huawei.com 小艺看世界 实时视觉 隐私 识别错误 机型；官方能力：site:about.fb.com Ray-Ban Display Be My Eyes live captions translation；官方能力：site:rokid.com Glasses AI assistant real-time translation battery review；垂直需求：site:teamviewer.com Frontline remote assistance downtime case study；垂直需求：site:frontline.io remote assist manufacturing field service case study；垂直需求：site:sightcall.com field service remote support first-time fix avoided truck roll；垂直需求：site:librestream.com remote expert low bandwidth inspection case study；无障碍付费：site:bemyeyes.com B2B integration live video accessible visual assistance；无障碍付费：Aira visual interpreting enterprise university airport subscription procurement；真实评价：site:reddit.com LiveKit Pipecat Vision-Agents production latency video issues；真实评价：site:github.com/livekit/agents/issues latency video barge-in outage；真实评价：site:github.com/pipecat-ai/pipecat/issues video production deployment latency；真实评价：site:trustpilot.com OR site:producthunt.com Vapi Retell reliability latency support；真实评价："Vapi" outage latency support complaints production；真实评价："Retell" outage latency support complaints production；真实评价："小艺看世界" 识别错误 慢 隐私 用户 评价；独立实测：site:tomsguide.com OR site:wired.com AI glasses real-time latency battery privacy；市场行为：remote visual assistance procurement contract renewal first-time fix rate；市场行为：AI vision agent field service paid pilot customer renewal case study；市场行为：real-time multimodal assistant enterprise contract deployment customer count；成本证据：realtime video AI cost per session minute bandwidth inference human escalation；安全合规：AI glasses video assistant privacy data retention enterprise China GDPR；开源风险：realtime multimodal agent open source license security maintenance workload CVE；历史失败：Google Glass Enterprise discontinued reasons adoption price privacy；历史失败：Humane AI Pin discontinuation server shutdown refunds complaints；历史失败：Rabbit R1 latency battery return rate initial review；禁止捷径：排除只含 star 数、演示视频、厂商广告、无付款或使用证据的材料作为商业结论
