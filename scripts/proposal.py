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
FOCUS_CONFIG = ROOT / '配置/自动科研关注.json'
TZ = ZoneInfo('Asia/Shanghai')


def proposal_schema(focus=None):
    properties = {
        'title': {'type': 'string'}, 'problem': {'type': 'string'}, 'hypothesis': {'type': 'string'},
        'method': {'type': 'string'}, 'evidence': {'type': 'array', 'items': {'type': 'string'}},
        'idea_sources': {'type': 'array', 'items': {'type': 'string'}},
        'minimal_experiment': {'type': 'string'}, 'metric': {'type': 'string'}, 'falsify': {'type': 'string'},
        'risks': {'type': 'string'}, 'tags': {'type': 'array', 'items': {'type': 'string', 'enum': list(research.TAGS)}}}
    required = ['title', 'problem', 'hypothesis', 'method', 'evidence', 'idea_sources',
        'minimal_experiment', 'metric', 'falsify', 'risks', 'tags']
    if focus:
        properties['focus_angle'] = {'type': 'string'}
        required.append('focus_angle')
    return {'type': 'object', 'properties': {'proposals': {'type': 'array', 'items': {
        'type': 'object', 'properties': properties, 'required': required,
        'additionalProperties': False}}},
        'required': ['proposals'], 'additionalProperties': False}


SCHEMA = proposal_schema()


def focus_profile(date):
    """Return the latest configured research focus active on this date."""
    if not FOCUS_CONFIG.exists():
        return None
    try:
        data = json.loads(FOCUS_CONFIG.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    day = str(date)
    eligible = [item for item in data.get('focuses', [])
        if isinstance(item, dict) and str(item.get('start_date') or '') <= day]
    return max(eligible, key=lambda item: item.get('start_date', '')) if eligible else None


def focus_score(text, focus):
    if not focus:
        return 0
    value = str(text or '').casefold()
    score = 0
    for keyword in focus.get('keywords', []):
        keyword = str(keyword).casefold().strip()
        if keyword and keyword in value:
            score += min(value.count(keyword), 3)
    return score


def _focus_ranked(records, focus, text_fn, limit):
    if not focus:
        return records[:limit]
    scored = []
    for index, record in enumerate(records):
        score = focus_score(text_fn(record), focus)
        tags = set(record.get('tags') or []) if isinstance(record, dict) else set()
        score += 4 * len(tags & set(focus.get('tags') or []))
        scored.append((score, index, record))
    focused = [(score, record) for score, index, record in scored if score > 0]
    focused.sort(key=lambda pair: pair[0], reverse=True)
    chosen = [record for _, record in focused[:limit]]
    if len(chosen) < limit:
        used = {id(record) for record in chosen}
        chosen += [record for _, _, record in scored[:] if id(record) not in used][:limit-len(chosen)]
    for _, index, record in scored:
        if isinstance(record, dict):
            record['focus_score'] = next(score for score, i, item in scored if i == index)
    return chosen


def idea_pool(focus=None):
    lines = []
    for path in [ROOT / '灵感/收件箱.md'] + sorted((ROOT / '灵感').glob('*.md')):
        if not path.exists() or path.name == '收件箱.md':
            continue
        for line in path.read_text(encoding='utf-8').splitlines():
            if line.strip().startswith('- '):
                lines.append(line.strip()[2:])
    lines = list(dict.fromkeys(lines))
    if not focus:
        return lines
    focused = sorted(lines, key=lambda line: focus_score(line, focus), reverse=True)
    return focused


def paper_pool(limit=40, focus=None):
    notes = knowledge.archived_notes()
    notes.sort(key=lambda note: (note['date'] or ''), reverse=True)
    records = [{'title': note['title'], 'summary': note['summary'], 'tags': note['tags'],
        'takeaway': knowledge.section_text(note['body'], '## 深读 takeaway')[:700],
        'archived_from': note['date']} for note in notes]
    return _focus_ranked(records, focus,
        lambda item: ' '.join([item.get('title', ''), item.get('summary', ''),
            ' '.join(item.get('tags', [])), item.get('takeaway', '')]), limit)


def cookbook_pool(focus=None):
    pool = []
    for path in sorted((ROOT / '最佳实践').glob('*.md')) if (ROOT / '最佳实践').exists() else []:
        text = path.read_text(encoding='utf-8')
        open_q = knowledge.section_text(text, '## 开放问题')
        pool.append({'topic': path.stem, 'open_questions': open_q[:2000]})
    return _focus_ranked(pool, focus,
        lambda item: item.get('topic', '') + ' ' + item.get('open_questions', ''), len(pool))


def focus_material_pool(focus, limit=6):
    if not focus:
        return []
    records = []
    for path in (ROOT / '业界洞察').rglob('*.md'):
        try:
            text = path.read_text(encoding='utf-8')
        except OSError:
            continue
        score = focus_score(path.stem + '\n' + text[:12000], focus)
        if score:
            records.append((score, path.stat().st_mtime, path, text))
    records.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [{'title': path.stem, 'path': str(path.relative_to(ROOT)), 'excerpt': text[:2500]}
        for _, _, path, text in records[:limit]]


def generate(date, limit_per_run=6):
    focus = focus_profile(date)
    ideas = idea_pool(focus)
    papers = paper_pool(focus=focus)
    books = cookbook_pool(focus)
    if not ideas and not papers:
        print('素材不足（既没有灵感也没有归档论文）')
        return []
    focus_block = ''
    if focus:
        focus_block = f'''

【当前主攻方向：{focus.get("label")}（从 {focus.get("start_date")} 起）】
{focus.get("summary")}

这批提案必须优先围绕这个方向展开，不能把 RSI、后训练、Harness 或通用 agent 当成主题，再在末尾补一句音视频场景。
- 默认所有提案都要直接推进全双工音视频对话；只有能明确改善它的在线时序、视听状态、训练信号、评测或部署时，跨方向方法才可保留。
- 每条必须用 focus_angle 说明：它改变了“系统在看/听什么、什么时候接话/等待/打断/行动、怎样边生成边理解”中的哪一环。
- 优先覆盖这些子方向：{'；'.join(focus.get('subdirections', []))}。
- 避免：{'；'.join(focus.get('avoid', []))}。
- 最小实验必须包含连续音视频流、交互时机和因果延迟；只有离线单轮准确率不算完整验收。
'''
    prompt = f'''你在帮一位大厂 AI Lab 的 NLP 博士，用他自己积累的素材提出可落地的研究提案。
主要素材是他的灵感清单、归档论文（含深读 takeaways）和主题手册开放问题；近期业界洞察只用来补充当前主攻方向的语境，不能替代论文证据。
{focus_block}

要求：
1. **列举式，不要筛选**：给出所有你能站得住的提案，不要挑"最好的几个"，也不要为了凑数编造。
2. **证据锚定**：每条提案的 evidence 必须是他归档论文的**标题原文**（能对上号），idea_sources 是他灵感清单的原文片段（可以短引用）。没有证据支撑的联想不要写。
3. **可证伪**：falsify 要写清"出现什么结果就说明这个想法错了"，metric 写用什么指标判断。
4. **最小实验**：minimal_experiment 要具体到 1–2 周能做完的程度（数据、baseline、训练/评测设置）。
5. 说人话：像给同行讲思路，不要翻译腔，不要抽象口号。
6. 只输出 JSON，不要解释文字，不要 Markdown 代码块。
'''
    example = {'title': '…', 'problem': '他想解决的具体问题', 'hypothesis': '一句话假设（可证伪）',
        'method': '怎么做（含关键机制）', 'evidence': ['归档论文标题'], 'idea_sources': ['灵感原文片段'],
        'minimal_experiment': '1–2 周最小实验', 'metric': '判断指标', 'falsify': '什么结果算想法被推翻',
        'risks': '风险与和已有工作的关系', 'tags': ['固定词表里的标签']}
    if focus:
        example['focus_angle'] = '这个提案怎样改变看/听/说/行动的实时时序'
    prompt += '输出结构：\n' + json.dumps({'proposals': [example]}, ensure_ascii=False)
    payload = {'date': date, 'my_ideas': ideas[:40], 'my_papers': papers, 'handbook_open_questions': books,
        'focus': focus, 'focus_materials': focus_material_pool(focus), 'tag_vocabulary': list(research.TAGS)}
    data = knowledge.codex_json(prompt, payload, proposal_schema(focus), STATE / f'{date}.json',
        ROOT / '.research/logs' / f'proposal-{date}.log', timeout=3600)
    proposals = data.get('proposals', [])[:limit_per_run] if limit_per_run else data.get('proposals', [])
    return proposals


def render(date, proposals):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f'{date}.md'
    focus = focus_profile(date)
    focus_line = f'本批主攻：**{focus.get("label")}**。' if focus else ''
    lines = [f'---\ndate: {date}\ntype: proposals\n---\n\n',
        f'# {date} 科研提案（列举式）\n\n',
        f'{focus_line}共 {len(proposals)} 条。素材来自你的灵感清单 + 归档论文 + 主题手册开放问题；'
        '每条都要求挂真实证据、可证伪的判负条件和 1–2 周最小实验。\n\n']
    for index, item in enumerate(proposals, 1):
        tags = ' '.join('#' + t for t in item.get('tags', []) if t)
        lines += [f"## P{index}. {item.get('title','')}\n\n"]
        if item.get('focus_angle'):
            lines.append(f"- **全双工切入角度**：{item.get('focus_angle')}\n")
        lines += [
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
