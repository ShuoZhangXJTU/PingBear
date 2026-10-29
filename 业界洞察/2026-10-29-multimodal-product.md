---
date: 2026-10-29
type: industry-insight
topic: "多模态交互的产品层"
run_graph: .research/industry/runs/20261029T025851-10edecfb/graph.json
artifact_revision: rev-56a95e9fe86f4a909f5a4d8f7163fcfd
---

# 业界洞察：多模态交互的产品层

> **2026-10-29 增补**：Meta Muse 的持久上下文、后台执行、支付与 Agent 协作改变了产品层边界，见 [[业界洞察/2026-10-29-multimodal-meta-muse-update]]。

联网检索候选 40 条 + 本机博客/论文 40 条；正文读取范围见筛选与核验记录。

## 一句话结论与关系变化

结论：本轮不立项、不投资、不选最终产品路线；把“多模态交互产品层”保留为研究方向。若必须选一个进入下一轮深挖的轨道，只建议选“任务限定的实时视觉指导”：共享当前画面，用语音描述，并在取景不佳时指导用户调整。理由不是它已被证明更优，而是现有材料中只有这一类证据同时展示了具体任务和可操作的纠错回路（web-5、web-7）；屏幕辅助只做到理解与高亮，操作仍由用户完成（web-20），人工服务与视觉检索接口则分别存在服务模式和接口形态，但缺少效果与商业结果（web-30、web-33）。

优先路径 A：实时视觉指导原型。前提是先选定一个任务，例如读取眼前小字或在当前场景中找物，并确认用户愿意持续共享画面。代价是设备设置、权限与隐私授权、用户反复调整镜头，以及需要人工观察失败恢复。最小验证是在同一任务、同一用户条件下，与拍照后检索或上传处理、文字搜索及适用时的人工求助对照；记录设置成功率、首次完成、耗时、调整次数、是否发现错答、何时转人工、放弃和再次使用。先测基线，再定义成功门槛；不得现在虚构目标。若把设置、纠正和核验计入后没有显示相对价值，或用户无法判断何时不该信任结果，则停止该轨道。

备选路径 B：保留用户操作权的屏幕或工作辅助。前提是明确产品只“理解并指向”，用户接受继续点击和输入。代价是人工执行、中断和误解高亮。最小验证应看高亮是否促成正确操作、是否减少查找，同时是否引入新错误；若净负担没有改善，则暂缓。路径 C：人工接管服务或视觉检索接口。只有在自动路径频繁失败、任务足够复杂，或已有合作应用需要检索能力时才验证。分别测升级等待、上下文移交、责任边界、检索覆盖与结果质量；若人工或接入成本吞掉价值，或用户不愿为结果付费，则保持观察。

关键判断是：现有证据尚未排除“便利主要来自少打字或生态预装”“受控演示优于真实环境”“用户控制是风险设计而非技术限制”等替代解释。候选清单中的其他产品没有被给定证据覆盖，不能据此判断其优劣或不存在能力。

## 核心体验变化、技术支撑与取舍

- 实时视觉指导改变的是“用户如何让系统看见当前场景”：系统可指出取景问题并让用户现场纠正（web-5），而拍照后检索通常先完成拍摄再处理；材料没有证明实时方式在相同任务上更快或更准。
- Copilot Vision 的产品边界体现在“理解与指向”和“用户执行”之间：高亮可帮助定位，但操作权仍归用户（web-20）。这降低误操作责任，却保留点击、输入、核验和中断成本。
- Gemini Live 与 Copilot Vision 都使用视觉上下文和语音交互，但前者强调取景纠错与实时描述，后者强调工作数据、屏幕理解和高亮（web-5、web-20）；两者不是同一交互闭环。
- Be My Eyes 展示了软件平台与人工代理并存的兜底模式（web-30），但不清楚何时从自动流程升级、等待多久、代理是否继承同一上下文；其体验不能由厂商功能材料直接推出。
- 拍立淘把视觉输入封装成供应用调用的检索接口（web-33），技术形态更接近能力供应层；检索结果如何被解释、比较并用于购买决策属于下游产品，当前没有覆盖。
- 潜在的体验收益减少口头描述和界面切换，但新增设置、权限、镜头对准、监督、纠正、人工执行和结果核验等成本；现有证据没有在同一任务下把这些成本与收益一起计量。
- 即时反馈不等于任务完成；自动执行也不一定优于用户保留控制。材料没有对照“全手动、系统指向、系统执行”的责任与体验边界，因此不能断言某一种配置总体更好。
- 来源独立性不足：Google 两项材料来自同一厂商和同一功能说明体系，最多互补，不能互相作为独立验证（web-5、web-7）；其他材料也主要是厂商或平台说明。

## 竞品清单（对比底稿）

| 竞品 | 公司 | 形态 | 具体做什么 | 交互方式 | 场景 | 成熟度 |
|---|---|---|---|---|---|---|
| Gemini Live Guided Vision | Google | 在实时摄像头共享中提供语音描述与取景指导的助手功能。 | 看见当前画面后用语音解释，并在画面取景不佳时要求用户移动设备。 | 用户共享摄像头画面；系统用自然语言提示横向平移、下倾或后退，形成“判断画面是否可用—提示调整—用户移动设备”的回路。 | 材料列出的示例包括读取食品标签小字、分辨颜色、在昏暗菜单上点单和寻找家中物品。 | 厂商功能说明，摘要级证据；没有独立复现、真实用户样本、时延、成功率或失败条件。 |
| Microsoft 365 Copilot Vision | Microsoft | 结合共享摄像头或桌面画面和工作数据的语音辅助功能。 | 理解用户共享的画面与工作数据，回答相关问题，并高亮屏幕区域。 | 用户在语音会话中共享画面；系统可高亮所指区域，但明确不代替用户点击或输入。 | 适用于需要理解当前屏幕或工作画面、再由用户执行操作的辅助任务。 | 厂商功能说明，摘要级证据；支持理解与指向，不支持据此认定自动任务闭环。 |
| Be My Eyes Workplace | Be My Eyes | 个人端免费、企业端付费的无障碍管理与远程人工代理服务。 | 通过企业授权平台和经过培训的远程人工代理提供人工协助兜底。 | 材料确认存在远程人工代理与企业服务，但没有说明具体呼叫、视频、升级、等待和上下文移交流程。 | 面向需要人工帮助完成视觉相关任务的企业与个人服务场景。 | 企业官网模式说明，摘要级证据；没有客户数、付费转化、留存、人工成本、等待时间或效果数据。 |
| 拍立淘图片搜索 API | 阿里 | 把图片作为输入、返回同款或相似商品检索能力的开放接口。 | 为其他应用提供以图搜商品能力。 | 材料只说明图片可被转换为同款或相似商品检索结果；接入条件、调用限制、结果解释和用户决策流程未给出。 | 材料列出的用途包括跨境选品、货源溯源、竞品情报和同款比价。 | 平台生态说明，摘要级证据；接口存在不等于检索质量、用户价值或商业收益已经验证。 |

## 场景拆解

### 读取食品标签、分辨颜色、查看昏暗菜单或寻找物品

- 谁在做：需要即时理解眼前信息、又不便先手动输入或拍照检索的人；这是由示例任务作出的用户假设，不是已核验的细分用户。
- 做法差异：共享画面加语音描述可能省去把场景口头转述的问题化步骤，系统还可能在画面不可用时指导调整（web-5、web-7）；相对现有替代方案的效果仍未对照。

### 理解当前屏幕或工作画面后指导下一步操作

- 谁在做：能够在系统中共享屏幕或摄像头、并愿意自己完成点击和输入的用户。
- 做法差异：系统可结合画面与工作数据回答并高亮区域，但不会代用户操作（web-20），价值取决于高亮是否真正减少查找和错误。

### 复杂、模糊或高风险的视觉求助

- 谁在做：需要人工判断或难以仅靠自动识别完成任务的人。
- 做法差异：人工代理可作为自动路径失败后的兜底，但现有材料只证明企业服务与收费形式存在，未证明升级时机、等待、质量或责任承担（web-30）。

### 应用内以图检索商品

- 谁在做：需要选品、溯源、比价的应用开发者与业务操作者；最终消费者任务未在材料中展开。
- 做法差异：图片可转化为同款或相似商品结果（web-33），但商品覆盖、检索质量、调用成本和下游比较决策均缺少证据。

## 怎么变现

| 模式 | 代表 | 谁付钱 | 证据 |
|---|---|---|---|
| 嵌入厂商产品的助手功能；收费和变现方式材料未说明 | Gemini Live、Microsoft 365 Copilot Vision | 材料中未说明；不能推断为订阅、设备或企业授权收入。 | web-5、web-7、web-20 |
| 个人端免费、企业端授权平台加远程人工代理 | Be My Eyes Workplace | 企业客户为无障碍管理平台和人工服务授权付费；具体价格与合同条款未给出。 | web-30 |
| 向应用提供视觉检索接口 | 拍立淘图片搜索 API | 材料未说明收费主体、价格或调用费用；仅可确认接口面向外部应用使用。 | web-33 |

## 可商用变现的切入点（待验证）

## 空白与机会

- **空白**：未解决：真正要支持的是机会排序、立项、预算分配还是具体方案取舍；这决定比较对象、用户范围和成功标准。
- **空白**：未解决：目标用户、使用情境、核心待办和最重要的用户结果尚未定义。
- **空白**：未解决：“产品层”的边界未确认，交互编排、上下文记忆、能力调用、反馈方式、动作执行和设备形态是否全部纳入仍不清楚。
- **空白**：未解决：材料没有同一用户、同一任务、同一结果指标下，将多模态产品与触屏文字搜索、普通语音助手、拍照后检索、人工求助或独立 App 进行对照。
- **空白**：未解决：共享画面开启成功率、理解准确率、纠正后恢复率、响应时延、错答发现率及停止使用原因均未量化。
- **空白**：未解决：动作理解、跨轮上下文、跨会话记忆、执行后校验和失败恢复没有形成端到端证据，“看见并解释”与“完成任务”之间存在关键缺口。
- **空白**：未解决：Google 与 Microsoft 材料主要是厂商功能说明，不能当作独立实测；Google 两项材料来源也不独立（web-5、web-7）。
- **空白**：未解决：第三方手机无障碍横评缺少测试日期、设备与系统版本、任务脚本、样本和原始记录，不能据此判断各品牌当前总体能力或形成排名（web-14）。
- **空白**：未解决：Be My Eyes 的客户数、付费转化、留存、人工成本、等待时间和用户结果未给出（web-30）。
- **空白**：未解决：拍立淘接口的接入资质、调用限制、费用、检索质量、商品覆盖和客户结果未给出（web-33）。
- **空白**：未排除替代解释：便利可能主要来自减少打字或界面切换，而非视觉理解更强。
- **空白**：未排除替代解释：采用可能来自设备预装、生态渠道、品牌信任或免费入口，而非多模态体验优势。
- **空白**：未排除替代解释：Copilot 不代用户点击或输入可能是有意控制风险，而非技术无法执行。
- **空白**：未排除替代解释：第三方横评中的品牌差异可能来自版本、设备、任务设计或测试误差。
- **空白**：材料包未包含独立失败案例或相反结果；没有实测证据不等于产品失败，也不等于产品有效。
- **空白**：候选清单中的 Ray-Ban Meta、Android XR、Snap Specs、理想同学、NOMI、小度等未被给定证据覆盖，因此本轮不能比较其交互、价值或成熟度。
- **机会**：进入下一轮深挖的唯一优先轨道是任务限定的实时视觉指导：先固定一个具体任务，验证系统看见画面、提示纠正、用户调整后能否完成，以及失败时如何恢复（web-5、web-7）。
- **机会**：该轨道必须先建立现有替代方案的基线，再决定成功门槛；最小测试应包含设置、共享画面、纠正、错答发现、人工接管和重复使用，而不只测模型回答是否看起来有用。
- **机会**：若首批观察显示设置与纠正成本吞掉描述便利，或用户无法判断系统何时不可信，应停止该轨道，转回重新定义任务和用户。
- **机会**：屏幕与工作辅助只作为条件性备选：当用户明确接受“系统理解并高亮、自己执行”的责任分配时，才验证高亮是否促成正确操作并减少查找（web-20）。
- **机会**：人工接管服务只作为自动路径失败后的待测配置：必须同时验证升级判断、等待、上下文移交、代理权限、责任归属和人工成本（web-30）。
- **机会**：视觉检索接口只作为开发者接入备选：必须同时验证接入条件、商品覆盖、检索质量、调用费用和下游决策结果（web-33）。
- **机会**：商业假设本轮留空：没有证据支持具体付费客户、价格、留存或单位经济性，因此不提出商业切入点排序。

## 本轮收口与待补证据

候选证据 80 条；深核 6 条。未选条目保留，不表示被证伪。
此处是材料核验，不表示实际运行产品测试。

- 深核 `web-5`：入选：官方材料给出了一个很具体的产品层机制——模型会根据实时画面主动纠正取景角度。它直接触及“看得见但看不清楚”造成的使用失败，并体现实时反馈、语音引导和任务推进的组合，适合深核其真实成功率、延迟和适用范围。需核清这是演示能力还是稳定可用的用户体验。
- 深核 `web-7`：入选：列出了读小字、辨颜色、昏暗环境下点单和找家中物品等具体任务，能帮助识别用户、使用情境和可感知价值。它也可作为无障碍辅助场景的价值样本；深核时要区分官方能力描述、用户实际结果和当前替代方案，不能只用功能清单证明价值。
- 深核 `web-14`：入选：提供手机无障碍产品的横向比较，尤其指出“描述丰富但偏静态识别”“有视频识别但入口未适配”等体验差异，可作为反例检验产品是否真的形成连续交互。属于第三方来源，必须核实测试方法、版本和时间，结论只能暂作待验证线索，不能当既成事实。
- 深核 `web-20`：入选：展示了把摄像头或桌面画面与工作资料结合回答的产品路径，同时明确“能高亮、不能代替点击或输入”，正好暴露从理解到任务闭环的边界。深核重点是减少查找成本是否足以构成价值、哪些步骤仍需用户完成，以及这种边界是否反而带来更清晰的责任划分。
- 深核 `web-30`：入选：同时提供人工远程帮助这一关键替代方案，以及个人免费、企业按授权收费的商业形态。它可用于回答用户为何选择机器、何时仍需真人，以及产品能否在不损害信任的前提下形成收入；企业介绍页可能偏营销，价格、服务边界和真实转化都需另行核验。
- 深核 `web-33`：入选：代表已经商业化的视觉搜索闭环：看图找同款、比价、选品和溯源，而不是只做画面问答。它可作为成熟价值与商业基线，检验新型多模态助手是否真的优于“拍照后搜索”。需深核接口限制、识别误差、使用成本和供应商文章之外的真实采用情况。
- 暂缓 `web-1`：暂缓保留：官方操作流程清楚，但基本摄像头对话已由 web-5 更深地覆盖；可留作华为路径的背景材料，当前不占深核名额。
- 暂缓 `web-2`：暂缓保留：“指哪问哪”是值得关注的不同输入方式，但目前只有功能说明，缺少用户测试；若后续聚焦免手操作或空间指代，应优先回捞。
- 暂缓 `web-3`：暂缓保留：眼镜上的视觉问答与手机入口相近，材料更偏功能罗列，且会把讨论引向设备形态；待明确是否研究穿戴式交互后再补。
- 暂缓 `web-4`：暂缓保留：这是覆盖视觉、系统服务和无障碍的官方总览，适合做能力地图，但主张较宽、缺少失败和结果证据，不能支撑择优。
- 暂缓 `web-6`：暂缓保留：补充了摄像头与屏幕共享的具体入口，但与 web-5、web-7 同属 Gemini Live 路径，信息增量较小，留作流程核对材料。
- 暂缓 `web-8`：暂缓保留：确认语音模式可以同时开启实时视频，是必要的基础事实，但没有说明哪些任务成功、哪些失败，单独深核价值不足。
- 暂缓 `web-9`：暂缓保留：演示了连续追问和环境互动，与现有路径重复；若需要比较 Open、Google、华为三家的连续性，再作为补充证据。
- 暂缓 `web-10`：暂缓保留：展示了地点、翻译、识别和外部搜索等多目的地，可作为手机视觉入口竞品；但交互更偏一次唤起、多按钮选择，暂不及 web-5 能暴露连续交互差异。
- 暂缓 `web-11`：暂缓保留：能证明相机、相册、文档和圈屏等多种输入并存，但材料主要描述入口，未说明用户怎样完成任务，暂不占深核预算。
- 暂缓 `web-12`：暂缓保留：官网覆盖图片、文档、屏幕、陪伴等能力，范围广但宣传性强；需要真实使用证据后才能判断产品层差异。
- 暂缓 `web-13`：暂缓保留：横向测试有直接的体验差异线索，但来源、样本和测试过程尚不清楚；已选 web-14 作为同类反例，后续需要两篇交叉核验，不能同时扩大低可信材料权重。
- 暂缓 `web-15`：暂缓保留：手机智能体测评提供了视觉处理、单应用自动化和本地检索的分工线索，可能与“看懂了却做不完”有关；但尚未核验其任务集和评分方法，留待任务闭环环节。
- 暂缓 `web-16`：暂缓保留：证明眼镜支持看后提问、连续追问和个人记录，是重要竞品路径；但目前与手机样本相比没有明显的决策增量，且材料偏功能发布。
- 暂缓 `web-17`：暂缓保留：镜片显示、实时字幕和手势输入带来明显的体验差异，可能形成隐私和免手的独特价值；当前边界强调产品层而非设备形态，若确定穿戴式形态应优先补入。
- 暂缓 `web-18`：暂缓保留：第一视角共享与镜片字幕翻译代表性较强，但主要依赖 XR 平台和硬件条件；暂不适合用来判断跨设备通用的产品层机会。
- 暂缓 `web-19`：暂缓保留：“预先提示”是区别于问答式助手的方向，但新闻稿主张跨设备且很宽，缺乏用户任务、触发条件、误报和采用证据，当前无法判断价值。
- 暂缓 `web-21`：暂缓保留：电视屏幕内容问答和点选搜索属于屏幕理解场景，但主要解决信息获取，和移动环境中的连续任务闭环差异较大；家居/电视成为重点时再回捞。
- 暂缓 `web-22`：暂缓保留：摄像头看护有明确任务和安全价值，但核心风险转到家庭监测、隐私与误报，适合独立的安全可行性研究，不宜与通用助手机会混合。
- 暂缓 `web-23`：暂缓保留：材料以模型接入、万物识别和场景画质为主，缺少具体交互流程与结果，当前更像技术营销而非产品层证据。
- 暂缓 `web-24`：暂缓保留：多音区、空间感知和“谁、在哪、指向什么”很具体，但座舱依赖专用传感器与车辆系统；待目标场景明确为座舱后再深核。
- 暂缓 `web-25`：暂缓保留：融合图像、音频和车身传感器，体现座舱语境，但信息来自二手报道且偏能力宣称；当前不具备跨场景外推条件。
- 暂缓 `web-26`：暂缓保留：实时描述、多轮对话、物品查找和辅助拍摄与最终产品层机会高度相关，是 web-7 的强替代样本；因名额限制暂缓，若深入无障碍应替换 web-33 或 web-17 类样本。
- 暂缓 `web-27`：暂缓保留：近眼导航、支付、搜同款和出行服务展示了最能闭合任务链的眼镜方案，很有价值；但材料是媒体发布报道，需核验真实可用流程、生态依赖和售价外成本，当前先留在高优先保留池。
- 暂缓 `web-28`：暂缓保留：音视频全双工属于重要的技术可行性基础，但当前排除模型架构和训练问题；待产品需求明确后再判断低延迟是否构成必要能力。
- 暂缓 `web-29`：暂缓保留：家庭智能体覆盖看护、陪伴和娱乐，领域代表性强，但发布材料宽泛且依赖家庭设备生态；若聚焦家居应单独组织用户任务与隐私证据。
- 暂缓 `web-31`：暂缓保留：免费公共服务形态是 web-30 的重要对照，能帮助比较机器免费供给与人工网络，但功能层级较窄；当前先深核更完整的价值/商业模式样本。
- 暂缓 `web-32`：暂缓保留：按量付费的视频理解 API 提供了企业侧可行性和收入模型，但与个人实时交互的产品层距离较远；若转向企业视频分析再纳入。
- 暂缓 `gh-1`：暂缓保留：仓库已废弃且转向文档抽取，不能代表当前路线；保留仅作视觉 Agent 工具演进的反例，不占产品机会深核。
- 暂缓 `gh-2`：暂缓保留：低延迟视频 Agent 框架与技术可行性相关，但尚未绑定用户任务；只能在已确定实时交互需求后评估。
- 暂缓 `gh-3`：暂缓保留：流式视觉模型属于模型能力与基础设施，当前阶段优先产品层证据，暂不展开。
- 暂缓 `gh-4`：暂缓保留：实时音视频传输是实现层候选，可支持后续技术可行性核验，但不能回答用户价值和场景选择。
- 暂缓 `gh-5`：暂缓保留：自托管语音 Agent 平台属于部署方案，当前没有明确渠道、成本或合规问题，暂不进入深核。
- 暂缓 `gh-6`：暂缓保留：多模态 Agent 框架与未来工程实现相关，但项目描述没有证据说明终端产品体验，留作可行阶段材料。
- 暂缓 `gh-7`：暂缓保留：与 gh-6 同为实时 Agent 框架路线，技术基础价值高但当前决策不确定；待功能需求明确后再二选一深核。
- 暂缓 `2606.19271`：暂缓保留：研究流式视频生成的服务调度，和“看见并理解环境、完成任务”的用户价值不在当前范围内。
- 暂缓 `2607.01793`：暂缓保留：关注 Agent 安全测试和大规模验证，不涉及多模态交互产品流程；若选中的产品会自主调用工具，再转为安全可行性证据。
- 暂缓 `2607.08768`：暂缓保留：虽覆盖主动 Agent、真实世界任务和多模态理解，但主要是模型与框架能力评测，不能直接解释用户任务或替代方案。
- 暂缓 `2607.11881`：暂缓保留：元认知综述与可靠性有关，但目标仍是模型能力，无法区分用户体验差异或产品价值。
- 暂缓 `2607.13491`：暂缓保留：循环 Transformer 的深度缩放属于模型架构，明确在当前研究边界外。
- 暂缓 `2607.15263`：暂缓保留：成本感知的安全 Agent 评测有商业可行性方法可借鉴，但任务域是攻防安全，和消费者多模态交互缺少直接对应。
- 暂缓 `2607.13918`：暂缓保留：验证器级联理论可用于未来质量控制，但不直接解释摄像头、语音和任务闭环的产品差异。
- 暂缓 `2607.18722`：暂缓保留：异步强化学习稳定性属于后训练，不服务本轮用户价值和场景选择。
- 暂缓 `2607.20092`：暂缓保留：视觉语言模型语境偏移会带来理解风险，可做安全或质量补充证据；当前不占产品机会深核名额。
- 暂缓 `2605.09635`：暂缓保留：教育知识图谱与多模态教材评测是垂直模型任务，和本次跨场景产品层决策相关性不足。
- 暂缓 `2607.21503`：暂缓保留：上下文生命周期管理对长期助手很关键，可作为连续上下文的架构依据；但它没有直接回答用户是谁、现有替代方案为何不足，暂留下轮。
- 暂缓 `2607.24241`：暂缓保留：电影级视频生成评测不属于多模态交互产品层，也不对应候选终端任务。
- 暂缓 `2607.25857`：暂缓保留：多模态安全分类器可服务内容审核，但当前还没有明确产品渠道和合规约束要求深核。
- 暂缓 `2607.27155`：暂缓保留：办公 Agent 的长时任务和经济价值评测较相关，可作为“任务能否做完”的测量参考；但输入与交付形态不是本轮重点的现场视觉交互。
- 暂缓 `2607.28802`：暂缓保留：交互中心故障分类非常适合后续定位“看错、不会用或不会执行”，但当前仍是框架与评测方法，缺少具体用户场景。
- 暂缓 `2608.03457`：暂缓保留：MoE 扩散语言模型属于模型规模与训练路线，明确不进入本轮产品层筛选。
- 暂缓 `2608.03764`：暂缓保留：Agent 自演化评测与产品体验有距离；若后续研究持续改进能力，可再评估。
- 暂缓 `2608.06301`：暂缓保留：优化 Agent 框架本身属于工程能力，当前尚不知道需要优化哪一种用户任务流程。
- 暂缓 `2608.06020`：暂缓保留：经济世界模型与模拟环境是 Agent 训练和仿真基础设施，不直接回答现场交互的用户价值。
- 暂缓 `2608.00675`：暂缓保留：扩散模型自测误差的信号很巧妙，但它服务于生成模型可靠性，不构成本轮产品层证据。
- 暂缓 `2608.09900`：暂缓保留：解码期压力测试关注模型鲁棒性，不能帮助确定目标用户、替代方案或任务价值。
- 暂缓 `2608.11951`：暂缓保留：极端事件数据增强面向航班运营预测，与多模态交互产品层没有直接关系。
- 暂缓 `2608.12571`：暂缓保留：法律引证支持核验说明“找得到材料不等于能验证”，可作为可信助手设计原则；但垂直度和输入形态均偏离当前候选。
- 暂缓 `2608.14614`：暂缓保留：二手 GPU 推理与绿色计算属于基础设施和单位经济性问题，只有在技术方案与成本边界明确后才相关。
- 暂缓 `2608.14639`：暂缓保留：文档字段的选择性风险控制可借鉴“何时交给人工复核”的机制；当前优先研究完整交互流程，暂不展开统计保证。
- 暂缓 `2608.19776`：暂缓保留：灵巧抓取是机器人执行技术，和产品层的视觉、语音、上下文组合缺少直接对应。
- 暂缓 `2608.22614`：暂缓保留：星系模型解释性研究不涉及本次产品机会。
- 暂缓 `2608.26737`：暂缓保留：LiDAR 场景补全属于空间感知模型，可能用于未来具身场景，但不是当前用户任务与商业价值证据。
- 暂缓 `2608.30428`：暂缓保留：具身 VLM Agent 的欺骗实验与安全评测有关，但不能说明正常消费者交互的体验差异。
- 暂缓 `2608.29681`：暂缓保留：多语言多模态虚假信息分类是内容安全垂直问题，当前产品层边界尚未确定。
- 暂缓 `2609.01453`：暂缓保留：模仿学习在不同执行速度下的鲁棒性属于机器人策略研究，不在本轮范围。
- 暂缓 `2608.30391`：暂缓保留：Agent 轨迹的扎根理论分析可用于理解真实失败，但需要先拿到目标产品的大量轨迹；当前先选场景证据更合适。
- 暂缓 `2609.02750`：暂缓保留：多 Agent 协调与反思理论可以支持工程可靠性，却无法替代用户任务、替代方案和产品价值证据。
- 暂缓 `2609.09134`：暂缓保留：Harness 与模型共同演化属于后训练和 Agent 工程，当前不进入机会筛选。
- 暂缓 `blog-b07b0b2b4d66`：暂缓保留：展示了用自然语言完成营销、周边商品和网站工作的效率案例，可作为办公型任务闭环参照；但与实时看环境的交互样本差异较大，且是厂商案例。
- 暂缓 `blog-98769dd27a53`：暂缓保留：跨人群基因风险迁移与多模态交互产品无关。
- 暂缓 `blog-305f03a4aa6a`：暂缓保留：图像生成质量和个性化属于生成能力，不是本轮摄像头/语音交互的任务闭环。
- 暂缓 `blog-014159943e4d`：暂缓保留：Codex 与 ChatGPT 用于科研搜索是专业工作流代表，但不涉及环境感知或多模态实时交互。
- 暂缓 `blog-4d4e7920d8a7`：暂缓保留：企业数据分析和看板展示了从自然语言到交付物的方向，可作为工作型产品参照；当前样本没有现场视觉与连续交互特征。
- 暂缓 `blog-016c3ec9b775`：暂缓保留：金融服务助手有明确专业场景，但当前重点是产品层交互机制；其价值证据主要来自发布材料，暂不占深核名额。

### 仍未解决

- 下一轮要支持的具体决策仍未明确：机会排序、是否立项、预算分配或具体方案取舍，会改变证据筛选和评价指标。
- 目标用户、使用情境、核心待办和最重要的用户结果尚未定义，无法判断这些产品能力对谁有价值。
- “产品层”的边界未确认，交互编排、上下文记忆、能力调用、反馈形式和设备形态是否全部纳入仍不清楚。
- 当前替代方案的痛点缺少用户证据；材料没有触屏搜索、语音助手、拍照检索、人工求助和专用 App 的可比数据。
- 所有功能材料均为摘要级，缺少设备、软件版本、地区、权限、发布时间、时延、成功率、失败率和失败恢复信息。
- Google 与 Microsoft 材料是厂商承诺，不能当作独立实测；同一厂商的多篇材料不能相互构成独立验证。
- 第三方手机无障碍横评缺少测试方法、样本、分母、版本和原始记录，不能推广为品牌总体结论。
- 差评和第三方差异只能揭示可能的失败机制，当前没有足够样本判断其代表性和发生频率。
- Be My Eyes 和拍立淘材料只说明服务或接口存在，没有收入、成本、付费转化、留存、调用质量或客户结果数据。
- 没有找到相反结果或独立复现；“未找到反例”不等于产品已被证明有效。
- 尚无端到端证据证明看环境、接语音或动作、保存上下文并交付可执行结果能够稳定形成任务闭环。
- 隐私、合规、渠道和单位经济性只在可能改变产品层可行性时纳入，但当前材料没有足够信息判断哪些约束会构成否决条件。
- 不能用候选品牌列表推断产品交互流程，也不能声称任何产品已经实测通过、已复现或已下载 PDF。
- 上述第三方横评是否准确反映当前各手机产品的实际能力，仍无法核验。：版本漂移、产品状态变化、评测激励和选择偏差均未知；不能据此形成品牌排名或总体优劣判断。
- Be My Eyes 的企业模式是否已经证明可持续盈利、真实付费需求或优于人工求助方案，材料无法支持。：不能把“存在付费产品”当成“商业验证通过”，也不能从一家无障碍服务推断其他多模态场景的付费意愿。
- 拍立淘接口已经被证据证明为成熟、可盈利或商业验证通过的视觉检索模式，材料不足。：没有版本、日期、样本和分母，不能把接口存在与商业成功混为一谈。
- 现有材料不足以证明任一候选“多模态产品层”相对触屏与文字搜索、普通语音助手、拍照后检索、人工求助或独立 App 形成了可验证的用户价值优势。：没有满意度、任务完成率、耗时、错误恢复、重复使用或业务结果等实测数据；不能据此完成机会排序或立项判断。
- 现有证据不能支持“看见环境、接住语音和动作、保留上下文、给出可执行结果”这一完整能力组合已经形成经过验证的任务闭环。：材料没有提供动作输入、连续任务、跨会话记忆、执行后校验或用户最终完成任务的测试，不能由单项能力拼接推断整体闭环。
- 当前可以把“多模态交互产品层”列为待继续核验的候选方向，但不能据此作出立项、投资、预算分配或最终产品路线决定。：用户提出的三项定题问题尚未得到回答；缺少这些条件会使所有产品层价值判断改变适用范围，因此方向只能保留为候选。
- 真正的业务决策尚不明确：是机会排序、是否立项、预算分配还是具体方案取舍；这决定了比较对象和成功标准，当前无法完成优先级结论。
- 目标用户、使用情境、核心任务和最重要的用户结果尚未定义，因而无法判断减少描述成本或增加人工接管对谁真正有价值。
- “产品层”的边界未确认，交互编排、上下文记忆、能力调用、反馈方式、动作执行和设备形态是否同时纳入仍不清楚。
- 现有材料没有同一目标用户、同一任务和同一结果指标下，将多模态产品与触屏文字搜索、普通语音助手、拍照后检索、人工求助或独立 App 进行对照的独立实测。
- Google、Microsoft 和平台材料主要是厂商功能说明或宣传性描述；缺少独立复现、真实用户样本、失败率和版本适用条件，不能把官方承诺当作体验已实现。
- Google 两项材料来自同一厂商和同一功能说明体系，内容可以互补，但不能作为两个独立验证（web-5、web-7）。
- 第三方无障碍横评缺少测试日期、设备与系统版本、任务脚本、样本量、分母和原始记录，无法判断其结论是否仍适用于当前产品（web-14）。
- 现有证据没有量化端到端中的关键环节：共享画面开启成功率、识别准确性、纠错后恢复率、响应时延、误答发现率，以及用户何时选择停止信任系统。
- 动作理解、跨轮上下文、跨会话记忆、执行后校验和失败恢复没有形成完整证据；“看见并解释”与“完成任务”之间仍存在关键缺口。
- Be My Eyes 的人工代理数量、排班、等待、培训质量、客户数、付费转化、留存、人工成本和实际用户结果均未给出（web-30）。
- 拍立淘接口的接入资质、调用限制、费用、检索质量、商品覆盖和客户结果均未给出（web-33），不能据此认定该形态成熟或商业验证通过。
- 隐私、合规、渠道和单位经济性会如何改变产品可行性尚不清楚，尤其对实时共享画面和人工接管场景缺少具体约束证据。
- 材料包没有包含相反结果或失败案例的独立实测记录。“未找到这些证据”不能解释为“产品无效”，也不能解释为“产品有效”。

## 接下来盯什么

- 同一目标用户和同一核心任务下，与现有替代方案进行对照的独立用户测试。
- 实时视觉指导在真实环境中完成设置、纠正和恢复任务的证据，而非受控演示。
- 用户何时信任或停止信任结果，以及错答能否被及时发现。
- 从理解、指向到动作执行的任务闭环、确认、日志与撤销/接管机制。
- 跨轮上下文和跨会话记忆是否真正降低重复解释，而非仅增加功能描述。
- 人工接管的等待、培训一致性、上下文继承、责任边界与人工成本。
- 图片检索接口的商品覆盖、检索质量、调用限制、费用与下游用户结果。
- 实时共享画面的隐私授权、合规和渠道约束是否会成为产品否决条件。
- Be My Eyes 的付费转化、留存和客户结果，以及拍立淘接口的实际客户使用结果。
- 被当前材料遗漏的候选产品是否出现可核验的交互流程、替代方案对照或真实用户结果。

## 竞品证据

### Gemini Live Guided Vision
- Gemini Live 在共享摄像头画面取景不佳时，会用自然语言提示用户横向平移、下倾或后退。（[Guided Vision launches in Gemini Live](https://blog.google/innovation-and-ai/products/gemini-app/guided-vision-gemini-live/)）
- Guided Vision 的实时语音描述示例包括读取食品标签、分辨颜色、查看昏暗菜单和寻找家中物品。（[Get audio descriptions with Guided Vision in Gemini Live](https://support.google.com/gemini/answer/18365638)）

### Microsoft 365 Copilot Vision
- Copilot Vision 可结合共享画面和工作数据回答，并高亮屏幕区域，但不会替用户点击或输入。（[Microsoft Copilot Vision](https://support.microsoft.com/en-us/microsoft-365-copilot/use-vision-microsoft-365-copilot)）

### Be My Eyes Workplace
- Be My Eyes 个人端免费，企业端通过无障碍管理平台按企业授权收费，并可提供经过培训的远程人工代理。（[Be My Eyes Workplace](https://www.bemyeyes.com/business/workplace/)）

### 拍立淘图片搜索 API
- 拍立淘提供以图搜同款或相似商品的开放接口，并列出跨境选品、货源溯源、竞品情报和同款比价等用途。（[淘宝拍立淘图片搜索 API](https://developer.aliyun.com/article/1752711)）

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
- 本地 paper `2606.19271` [TurboServe: Serving Streaming Video Generation Efficiently and Economically](https://arxiv.org/abs/2606.19271) · Tsinghua University
- 本地 paper `2607.01793` [Safety Testing LLM Agents at Scale: From Risk Discovery to Evidence-Grounded Verification](https://arxiv.org/abs/2607.01793) · Ant Group
- 本地 paper `2607.08768` [UniClawBench: A Universal Benchmark for Proactive Agents on Real-World Tasks](https://arxiv.org/abs/2607.08768) · The University of Hong Kong
- 本地 paper `2607.11881` [Metacognition in LLMs: Foundations, Progress, and Opportunities](https://arxiv.org/abs/2607.11881) · Yale NLP Lab
- 本地 paper `2607.13491` [DeepLoop: Depth Scaling for Looped Transformers](https://arxiv.org/abs/2607.13491) · math-ai
- 本地 paper `2607.15263` [Beyond Success Rate: Cost-Aware Evaluation of Offensive and Defensive Security Agents](https://arxiv.org/abs/2607.15263) · 未知
- 本地 paper `2607.13918` [Partially Correlated Verifier Cascades in LLM Harnesses: Concave Log-Odds, Polynomial Reliability, and Blind-Spot Ceilings](https://arxiv.org/abs/2607.13918) · 未知
- 本地 paper `2607.18722` [Stale but Stable: Staleness-Adaptive Trust Regions for Stabilizing Asynchronous Reinforcement Learning](https://arxiv.org/abs/2607.18722) · Tencent Hunyuan
- 本地 paper `2607.20092` [ENTRAP-VL: A Taxonomic Probe for Dual Contextual Entrainment in Vision-Language Models](https://arxiv.org/abs/2607.20092) · 未知
- 本地 paper `2605.09635` [K12-KGraph: A Curriculum-Aligned Knowledge Graph for Benchmarking and Training Educational LLMs](https://arxiv.org/abs/2605.09635) · Peking University
- 本地 paper `2607.21503` [Agentic Context Management: Solving Agent Memory and Cost by Treating Them as Lifecycle and Architecture Problems](https://arxiv.org/abs/2607.21503) · Maximem AI
- 本地 paper `2607.24241` [FilmBench: A Film-Grade Benchmark for Cinematic Video Generation](https://arxiv.org/abs/2607.24241) · 未知
- 本地 paper `2607.25857` [Shieldstral](https://arxiv.org/abs/2607.25857) · Mistral AI_
- 本地 paper `2607.27155` [OmegaUse-OfficeVal: Benchmarking LLM Agents on Long-Horizon Office-Suite Tasks with Economic Grounding](https://arxiv.org/abs/2607.27155) · 未知
- 本地 paper `2607.28802` [Model or Harness? An Interaction-Centric Taxonomy for Localizing Agent Failures](https://arxiv.org/abs/2607.28802) · Scale AI
- 本地 paper `2608.03457` [LLaDA MoE v2: Scaling Mixture-of-Experts Diffusion Language Models](https://arxiv.org/abs/2608.03457) · GSAI-ML
- 本地 paper `2608.03764` [GDPevo: Evaluating Agent Self-Evolution on Real Business Tasks](https://arxiv.org/abs/2608.03764) · Prism Shadow
- 本地 paper `2608.06301` [HarnessOpt-Bench: Evaluating LLMs at Harness Optimization](https://arxiv.org/abs/2608.06301) · Scale AI
- 本地 paper `2608.06020` [From Economic Agents to Agentic Economies: A Systems Blueprint for Economic World Models](https://arxiv.org/abs/2608.06020) · FreedomAI
- 本地 paper `2608.00675` [Round-Trip Consistency: Bidirectional Diffusion Models Can Predict Their Own Rollout Errors](https://arxiv.org/abs/2608.00675) · 未知
- 本地 paper `2608.09900` [Decoding-Level Taboo: A Diagnostic Stress Test for LLM Robustness](https://arxiv.org/abs/2608.09900) · 未知
- 本地 paper `2608.11951` [TailBooster: A Dual-Layer Generative Framework for Extreme Value Augmentation with Operational Validity Enforcement](https://arxiv.org/abs/2608.11951) · Technology University of Delft
- 本地 paper `2608.12571` [Is this Citation on Point?](https://arxiv.org/abs/2608.12571) · Bloomberg
- 本地 paper `2608.14614` [DumpsterCluster: From Dumpster Diving to Serving LLaMA-70B on $60 GPUs](https://arxiv.org/abs/2608.14614) · University of Oxford
- 本地 paper `2608.14639` [Valid Per-Field Selective Risk Control for Document Extraction: Three Failure Modes, a Validity Ladder, and When Conditioning Pays](https://arxiv.org/abs/2608.14639) · 未知
- 本地 paper `2608.19776` [CoToGrasp: Contact-Topology-Conditioned Dexterous Grasp Synthesis via Canonical Workspace Learning](https://arxiv.org/abs/2608.19776) · 未知
- 本地 paper `2608.22614` [What AstroPT knows about galaxies, and what that can teach us about LLMs](https://arxiv.org/abs/2608.22614) · 未知
- 本地 paper `2608.26737` [Generative Semantic Scene Completion](https://arxiv.org/abs/2608.26737) · 未知
- 本地 paper `2608.30428` [Lies We Can See: Joint Verbal and Non-Verbal Deception by VLM Agents in Embodied Social Interactions](https://arxiv.org/abs/2608.30428) · Seoul National University
- 本地 paper `2608.29681` [MMMMM: A Unified Taxonomy for Investigating the Mechanisms of Multilingual MultiModal Misinformation](https://arxiv.org/abs/2608.29681) · CopeNLU
- 本地 blog `blog-b07b0b2b4d66` [ATV Big Air Tour turned 3 days of work into 3 hours with ChatGPT](https://openai.com/index/atv-big-air-tour) · OpenAI
- 本地 paper `2609.01453` [Does Imitation Learning Preserve Temporal Robustness in Dexterous Manipulation? An Expert-Learner Comparison Across Task Execution Speeds](https://arxiv.org/abs/2609.01453) · University of Maryland College Park
- 本地 blog `blog-98769dd27a53` [Transfer learning for genomic prediction in underrepresented populations](https://research.google/blog/transfer-learning-for-genomic-prediction-in-underrepresented-populations/) · Google Research
- 本地 paper `2608.30391` [Using Grounded Theory for Agent Behavior Analysis at Scale](https://arxiv.org/abs/2608.30391) · Purdue University
- 本地 paper `2609.02750` [Bilevel Coordinated Reflection: A Game-Theoretic Approach to Multi-Agent LLM Systems](https://arxiv.org/abs/2609.02750) · 未知
- 本地 blog `blog-305f03a4aa6a` [Introducing ChatGPT Images 2.5](https://openai.com/index/introducing-chatgpt-images-2-5) · OpenAI
- 本地 blog `blog-014159943e4d` [How a researcher uses Codex and ChatGPT to search for new antimicrobial molecules](https://openai.com/index/using-codex-chatgpt-to-search-for-new-antimicrobials) · OpenAI
- 本地 blog `blog-4d4e7920d8a7` [Now everyone can put data to work](https://openai.com/index/put-data-to-work) · OpenAI
- 本地 blog `blog-016c3ec9b775` [Introducing ChatGPT for Financial Services](https://openai.com/index/introducing-chatgpt-financial-services) · OpenAI
- 本地 paper `2609.09134` [Co-Evolving Harnesses and Models: On-Policy Correction Helps Weaker Models Catch Up Where Imitation Fails](https://arxiv.org/abs/2609.09134) · Salesforce

检索词：小艺看世界 官方 支持 使用场景 限制 评测 差评；Gemini Live camera screen share official help limitations independent review；ChatGPT camera screen share voice official help real-world review failure；Apple Visual Intelligence official help camera screen limitations reviews；Ray-Ban Meta multimodal AI official help privacy limitations long-term review；Copilot Vision official help use cases limitations independent hands-on；Bixby Samsung Vision AI official use cases user complaints；海信 语音 视觉 多模态 交互 官方 使用说明 用户评价；理想同学 NOMI 多模态 座舱 官方 功能 用户反馈 驾驶员分心；vivo看见 无障碍 官方 使用说明 视障 用户 评测 局限；夸克AI眼镜 官方 功能 使用体验 续航 隐私 评测 差评；SeedRealtime official product demo use cases latency limitations；小度 多模态 语音 视觉 官方 使用场景 用户评价；Be My Eyes Be My AI official user stories limitations independent review；TwelveLabs official video understanding customers deployment limitations；拍立淘 官方 使用说明 识别失败 用户评价 使用场景；Google Lens 微信扫一扫 拍立淘 视觉搜索 使用体验 对比；real-time multimodal assistant independent hands-on comparison camera voice；multimodal AI assistant accessibility user study blind low-vision；AI glasses independent review bystander privacy usability abandonment；voice visual assistant task completion failure recovery field study；smart home multimodal camera voice assistant user experience review；in-car multimodal assistant distraction safety independent evaluation；visual search shopping real user behavior conversion retention；enterprise video understanding customer case deployment limitations ROI；multimodal assistant App Store Google Play reviews complaints retention；Google Glass consumer failure postmortem user experience；Humane AI Pin review failure postmortem usability latency；Rabbit R1 hands-on review criticism actual task completion；multimodal interaction alternatives touch search human help comparative study
