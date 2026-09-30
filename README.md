# 科研早报

双击桌面「科研早报」即可在 Obsidian 打开 [[今日简报]]。Obsidian 已安装于 `~/Applications/Obsidian.app`，已连接本仓库，首页标签已固定。

## 每天怎样看

北京时间 8:30 开始生成，目标 9:00 可阅读。后台不依赖 Obsidian 打开；数据直接写到本地 Markdown。电脑需要登录、联网且处于可运行状态。休眠/关机期间无法生成，恢复后补跑；网络或额度失败会显示状态并重试，不承诺断网时 9:00 可用。

HF 当次抓取返回的论文全部列出，每篇一句中文概述；标题本身就是论文链接，另附 arXiv PDF 链接，★ 标出你可能更感兴趣的重点。跨日重复仍显示。数量代表抓取时的快照，不代表当天后续不再上新。当天为空时展示最近可用日期并明确标注；抓取失败不会伪装成空列表。

首页下半部分是**小红书 · tabris**（小红书号 2608032230）。他常发英文论文截图，所以按「一张截图一条」处理：读主页 → 发现新笔记 → 下载截图 → 本机 OCR（macOS Vision，不联网）→ 从截图里认 arXiv 编号（识别不到就按标题检索 arXiv）→ 拉论文摘要 → 按 HF 那版同款写法给一句中文、标签、论文与 PDF 链接，另附小红书本帖入口；认不出论文的截图按原帖处理。编号 X1、X2 连续排。归档时能对上论文的按 arXiv 编号存（和 HF 归档同一篇合并），否则存成 `xhs-...`。

小红书要网页端登录才能读，登录态和抓取工具在 `~/.local/share/research-xhs/`，配置和排障见 [[配置/小红书]]。抓不动时早报会标注「小红书部分本次未更新」，不影响上面的 HF 部分。

中文由已登录的 Codex CLI 以只读模式生成，使用现有账户额度；输入为公开论文摘要。所有条目均标记摘要级，不宣称精读或复现。机器摘要可能有误，重要结论需要回到原文核对。

- [[今日简报]]：自动更新的固定首页。
- `日报/`：按日期保存的完整列表。
- `论文/`：仅在你点击「归档」后保存的笔记，每篇一篇，tags 写在正文前的属性区。
- [[索引/标签]]：按标签查归档，每次归档后自动重建。
- [[索引/目录]]：历史目录，按日期和来源两个维度索引所有日报、归档、专题页和问答记录，每次早报后自动重建。
- [[配置/标签]]：归档用的固定标签词表；要加减标签改这里。
- `专题/`：主题知识体系页（RSI、Harness、后训练…），归档后自动重建；你自己的「我的想法」段落不会被覆盖。
- `收件箱/我的链接.md`：你自己贴链接的入口，处理成同款条目。
- [[配置/研究偏好]]：RSI、Harness、后训练及机构偏好。
- `专题/`、`附件/`、`收件箱/`：阅读问题、附件和社交线索。

每篇下面有「归档」按钮：点一下就把这篇存进 `论文/`；想补两句就先点「加备注」，填完再归档，已归档的条目会变成「已归档 · 打开」和「补充备注」。也可以在对话里说“归档 9 月 25 日第 2、4 篇”按编号处理。编号发布后保留，新条目只追加。日报与首页为自动生成文件，请把个人批注放在论文笔记中；更新前会备份日报旧版。

找论文时按标签走：首页上的「按标签查归档」进 [[索引/标签]]，里面按标签分组列出所有归档笔记；也可以直接点笔记正文里的 `#标签`，或左侧的标签面板筛选。想手动重建索引，用 Obsidian 命令面板的「重建标签索引」，或运行下面的 `index` 命令。

## 归档之后：深读与知识体系

点「归档」或说「归档今天第 2 篇」之后，会多两步：

1. **深读 takeaway**：独立跑一次模型，抓这篇论文的 arXiv 正文（拿不到正文就用摘要页；小红书来源会连截图 OCR 一起读），在笔记里写入「## 深读 takeaway」——核心做法、关键机制、证据、可复用点、疑点、与同主题工作的关系，并标明这次读到的是「正文级」还是「摘要级」。
2. **主题体系**：把该主题（RSI / Harness / 后训练）下所有归档笔记合成 `专题/<主题>.md`：定位、概念地图（按解决的同类问题分组）、交叉观察（哪些论文在讲同一件事的不同侧面、哪些互补、哪些说法冲突）、开放问题，最后是归档索引。页里的「## 我的想法」是留给你写的，脚本重建时会原样保留。

模型只依据抓到的材料写，材料里没有的数字和结论不会编；深读是模型独立阅读的结果，不代表你看过或复现过。

## 边看边问

每条下面都有「提问」按钮。问题会带着这篇的 arXiv 正文（拿不到正文就用摘要；小红书条目用截图 OCR）去问，回答直接显示在弹窗里，同时写进 `问答/<条目 ID>.md`。每次回答都会附一句「沉淀」——把这次问答压成一句结论：

- 已归档的条目：沉淀会自动追加到笔记的「## 问答沉淀」，话题重建时也一起喂给专题页，所以你自己问出来的东西会进入知识体系，而不是散在聊天记录里。
- 还没归档的条目：问答先存在 `问答/`，归档后自动接上。
- 回答只依据论文材料，材料里没有的会直接说「材料里没有」，并标注依据是正文级还是摘要级。

快捷键：在提问框里按 `Cmd+Enter` 直接提交。

## 自己贴链接

除了 HF 和小红书这两个固定来源，你自己刷到的好东西可以贴进 [[收件箱/我的链接]]，**一行一个**。贴完：

- 在 Obsidian 命令面板运行「读取我的链接」，或等第二天早报自动处理（每次最多 10 条）。
- 结果写进当天的 `日报/<日期>-我的链接.md`，并出现在 [[今日简报]] 的「我的链接」段落，编号 M1、M2，一样带「提问 / 归档」按钮。

按链接类型分流：arXiv（abs/pdf/html 或裸编号）→ 取标题摘要当论文处理，归档时用 arXiv 编号，和 HF/小红书里的同一篇合并；小红书笔记链接 → 走截图 OCR + 逐张认论文那条路；其他网页 → 抓正文按内容写简介，归档成 `link-<哈希>`。处理过的链接记在 `.research/inbox/seen.json`，不会重复处理；同一素材多次追加链接时，编号继续往后排。

## 问归档（对话入口）

左侧栏的问号图标，或命令面板的「归档问答」，可以对着**全部归档内容**搜和问——检索范围是归档笔记的标题、标签、一句话简介、深读 takeaway、你自己的问答沉淀，以及所有专题体系页。

- **搜索**：本地关键词检索，秒回，列出命中的笔记（带相关度），点开即看。
- **提问**：先挑出最相关的几篇，再带着它们的深读和问答沉淀回答；句末用 `[[论文/编号|标题]]` 标注来源，并单独给出「缺口」——归档里还缺哪类材料才能回答得更完整。
- 每次提问记录在 [[问答/知识助手]]，方便回看自己问过什么。

## 官方博客与研究发布

除 HF、小红书和你自己贴的链接外，每天还会扫这 6 个公司官方源，结果写进 `日报/<日期>-博客.md` 和首页「官方博客与研究发布」段落（编号 B1、B2…），同样是「提问 / 归档」可用的条目：

| 源 | 抓取方式 |
|---|---|
| OpenAI（[news rss](https://openai.com/news/rss.xml)）| RSS（官网有机器人校验，用 feed 绕开）|
| Anthropic [Research](https://www.anthropic.com/research) / [Engineering](https://www.anthropic.com/engineering) | 列表页 + 文章页 |
| [Google Research Blog](https://research.google/blog/) | RSS |
| [Microsoft Research Blog](https://www.microsoft.com/en-us/research/blog/) | RSS |
| [ByteDance Seed](https://seed.bytedance.com/en/research) | 本机 Chrome 渲染（页面是前端渲染的）|

每个源默认只取最新 2 条，其余标记为已见（首次接入不会把历史文章一次性刷进来）。手动补跑：

```sh
python3 /Users/zhangshuo/Research/scripts/blogs.py process --per-source 3
```

已见列表在 `.research/blogs/seen.json`；抓取失败会写进早报状态，不影响其他段落。

「归档」按钮由资料库自带的本地插件 `research-archive` 提供（`.obsidian/plugins/research-archive`，已写入 `community-plugins.json` 启用）。如果按钮变成一行普通链接或提示“无法识别的 URI”，说明插件没加载：重启一次 Obsidian，或到「设置 → 第三方插件」确认它已启用（关闭受限模式后勾选「科研论文归档」）。

## 运行与维护

后台：macOS LaunchAgent `local.research.morning`。每日 8:30 触发，并每 15 分钟检查是否需要补跑；失败至少间隔 30 分钟重试。上午成功后当天不重复生成；当天较早的手动试跑不会阻止 8:30 刷新。

```sh
# 立即刷新今天的早报
python3 /Users/zhangshuo/Research/scripts/morning.py --force
# 只按已有中文 JSON 重排今天日报版式（不联网、不重跑翻译）
python3 /Users/zhangshuo/Research/scripts/research.py render --date 2026-09-25
# 按 论文/ 里的归档笔记重建标签索引
python3 /Users/zhangshuo/Research/scripts/research.py index --date 2026-09-25
# 手动补跑小红书（--limit 控制本次最多几篇，--force 会重做已见过的）
python3 /Users/zhangshuo/Research/scripts/xhs.py run --date 2026-09-25 --limit 3
# 给还没深读的归档论文补 takeaway（--force 全部重做）
python3 /Users/zhangshuo/Research/scripts/knowledge.py deepen --limit 3
# 重建主题知识体系页（不带 --topic 就重建所有有内容的主题）
python3 /Users/zhangshuo/Research/scripts/knowledge.py rebuild
# 对某条内容提问（答案写进 问答/，已归档的顺带沉淀到笔记）
python3 /Users/zhangshuo/Research/scripts/knowledge.py ask --id 2609.29892 --question "CARE 的三档 reward 具体怎么切换？"
# 处理你自己贴的链接（--limit 控制本次最多几条）
python3 /Users/zhangshuo/Research/scripts/inbox.py process --limit 5
# 搜归档 / 问归档
python3 /Users/zhangshuo/Research/scripts/library.py search --query "harness reward 归因"
python3 /Users/zhangshuo/Research/scripts/library.py ask --question "这批工作里 harness 的改进落在哪几处？"
# 重建历史目录
python3 /Users/zhangshuo/Research/scripts/catalog.py
# 仅在选中之后按编号归档
python3 /Users/zhangshuo/Research/scripts/research.py archive --date 2026-09-25 --numbers 2 4
```

任务配置：`~/Library/LaunchAgents/local.research.morning.plist`。
运行状态：`.research/morning-status.json`；日志：`.research/logs/`。
原始快照、候选、中文 JSON、编号映射位于 `.research/`。
暂停任务可运行 `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/local.research.morning.plist`；要避免下次登录自动加载，可将该 plist 移回本库 `.research/`。

当前来源：HF Daily Papers + 小红书 tabris（2608032230）+ 你自己贴的链接。X 尚未接入。

实现依据：[Codex 非交互运行](https://learn.chatgpt.com/docs/non-interactive-mode)、[Obsidian 官方下载](https://obsidian.md/download)。
