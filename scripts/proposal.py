#!/usr/bin/env python3
"""自动科研提案（列举式，不筛选）。

结合三样东西：你自己的灵感（灵感/）、归档论文（论文/）、主题手册与专题（最佳实践/、专题/）。
流程参考 HypoForge（问题形式化 → 证据归纳 → 假设生成 → 研究计划 → 质量评审）
与 CausalSmith 的教训（不要相信模型自评：每条提案必须挂真实证据 + 可证伪的判负条件）。

产物：提案/<日期>.md（当天全部候选）+ .research/proposals/<日期>.json（结构化，供检索与归档）。
闲时运行（凌晨错峰），不筛选、全列。
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import knowledge
import research

ROOT = research.ROOT
OUT_DIR = ROOT / '提案'
STATE = ROOT / '.research/proposals'
TZ = ZoneInfo('Asia/Shanghai')
SCHEMA = {'type': 'object', 'properties': {'proposals': {'type': 'array', 'items': {
    'type': 'object', 'properties': {
        'title': {'type': 'string'}, 'problem': {'type': 'string'}, 'hypothesis': {'type': 'string'},
        'method': {'type': 'string'}, 'evidence': {'type': 'array', 'items': {'type': 'string'}},
        'idea_sources': {'type': 'array', 'items': {'type': 'string'}},
        'minimal_experiment': {'type': 'string'}, 'metric': {'type': 'string'}, 'falsify': {'type': 'string'},
        'risks': {'type': 'string'}, 'tags': {'type': 'array', 'items': {'type': 'string', 'enum': list(research.TAGS)}}},
    'required': ['title', 'problem', 'hypothesis', 'method', 'evidence', 'idea_sources',
        'minimal_experiment', 'metric', 'falsify', 'risks', 'tags'],
    'additionalProperties': False}}},
    'required': ['proposals'], 'additionalProperties': False}


def idea_pool():
    lines = []
    for path in [ROOT / '灵感/收件箱.md'] + sorted((ROOT / '灵感').glob('*.md')):
        if not path.exists() or path.name == '收件箱.md':
            continue
        for line in path.read_text(encoding='utf-8').splitlines():
            if line.strip().startswith('- '):
                lines.append(line.strip()[2:])
    return list(dict.fromkeys(lines))


def paper_pool(limit=80):
    notes = knowledge.archived_notes()
    notes.sort(key=lambda note: (note['date'] or ''), reverse=True)
    return [{'title': note['title'], 'summary': note['summary'], 'tags': note['tags'],
        'takeaway': knowledge.section_text(note['body'], '## 深读 takeaway')[:1200]} for note in notes[:limit]]


def cookbook_pool():
    pool = []
    for path in sorted((ROOT / '最佳实践').glob('*.md')) if (ROOT / '最佳实践').exists() else []:
        text = path.read_text(encoding='utf-8')
        open_q = knowledge.section_text(text, '## 开放问题')
        pool.append({'topic': path.stem, 'open_questions': open_q[:2000]})
    return pool


def generate(date, limit_per_run=6):
    ideas = idea_pool()
    papers = paper_pool()
    books = cookbook_pool()
    if not ideas and not papers:
        print('素材不足（既没有灵感也没有归档论文）')
        return []
    prompt = '''你在帮一位大厂 AI Lab 的 NLP 博士，用他自己积累的素材提出可落地的研究提案。
素材来源只有三处：他自己的灵感清单、他归档的论文（含深读 takeaways）、他的主题手册里的开放问题。

要求：
1. **列举式，不要筛选**：给出所有你能站得住的提案，不要挑"最好的几个"，也不要为了凑数编造。
2. **证据锚定**：每条提案的 evidence 必须是他归档论文的**标题原文**（能对上号），idea_sources 是他灵感清单的原文片段（可以短引用）。没有证据支撑的联想不要写。
3. **可证伪**：falsify 要写清"出现什么结果就说明这个想法错了"，metric 写用什么指标判断。
4. **最小实验**：minimal_experiment 要具体到 1–2 周能做完的程度（数据、baseline、训练/评测设置）。
5. 说人话：像给同行讲思路，不要翻译腔，不要抽象口号。
6. 只输出 JSON，不要解释文字，不要 Markdown 代码块。

输出结构：
{"proposals":[{"title":"…","problem":"他想解决的具体问题","hypothesis":"一句话假设（可证伪）",
"method":"怎么做（含关键机制）","evidence":["归档论文标题"],"idea_sources":["灵感原文片段"],
"minimal_experiment":"1–2 周最小实验","metric":"判断指标","falsify":"什么结果算想法被推翻",
"risks":"风险与和已有工作的关系","tags":["固定词表里的标签"]}]}
'''
    payload = {'date': date, 'my_ideas': ideas[:60], 'my_papers': papers, 'handbook_open_questions': books,
        'tag_vocabulary': list(research.TAGS)}
    data = knowledge.codex_json(prompt, payload, SCHEMA, STATE / f'{date}.json',
        ROOT / '.research/logs' / f'proposal-{date}.log', timeout=3600)
    proposals = data.get('proposals', [])[:limit_per_run] if limit_per_run else data.get('proposals', [])
    return proposals


def render(date, proposals):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f'{date}.md'
    lines = [f'---\ndate: {date}\ntype: proposals\n---\n\n',
        f'# {date} 科研提案（列举式）\n\n',
        f'共 {len(proposals)} 条。素材来自你的灵感清单 + 归档论文 + 主题手册开放问题；'
        '每条都要求挂真实证据、可证伪的判负条件和 1–2 周最小实验。\n\n']
    for index, item in enumerate(proposals, 1):
        tags = ' '.join('#' + t for t in item.get('tags', []) if t)
        lines += [f"## P{index}. {item.get('title','')}\n\n",
            f"- **要解决的问题**：{item.get('problem','')}\n",
            f"- **假设**：{item.get('hypothesis','')}\n",
            f"- **做法**：{item.get('method','')}\n",
            f"- **最小实验**：{item.get('minimal_experiment','')}\n",
            f"- **指标**：{item.get('metric','')}\n",
            f"- **判负条件**：{item.get('falsify','')}\n",
            f"- **风险 / 与已有工作**：{item.get('risks','')}\n",
            f"- **证据**：{ ' · '.join(item.get('evidence', [])) or '（无）'}\n",
            f"- **来自你的灵感**：{ ' · '.join(item.get('idea_sources', [])) or '（无）'}\n\n",
            f"{tags}\n\n"]
    research.replace(path, ''.join(lines))
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date')
    parser.add_argument('--limit', type=int, default=6, help='0 表示全部')
    args = parser.parse_args()
    date = args.date or dt.datetime.now(TZ).date().isoformat()
    STATE.mkdir(parents=True, exist_ok=True)
    try:
        proposals = generate(date, limit_per_run=args.limit or None)
    except Exception as error:
        try:
            import alert
            alert.send(f'⚠️ 科研提案没生成出来：{type(error).__name__} {error}\n'
                '（01:30/05:30 那次没跑成，明天会自动重试）', key='proposal-failed:' + date)
        except Exception:
            pass
        raise
    if proposals:
        path = render(date, proposals)
        print(f'生成 {len(proposals)} 条提案 -> {path}')


if __name__ == '__main__':
    main()
