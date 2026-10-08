#!/usr/bin/env python3
"""最佳实践手册（best-practice accumulator）。

按主题（RSI / 后训练 OPD·RL / …）把已归档论文的 takeaways 持续积累成一本「拿来就能用」的手册：
动手前要想清楚什么、常见坑与解决办法、可复制配方、评测与成本、开放问题。

只增不减：每次把新归档论文的增量条目追加到已有手册里，不重写、不覆盖「我的补充」。
状态记在 .research/cookbook.json（每个主题已并入过哪些论文）。
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
STATE = ROOT / '.research/cookbook.json'
OUT = ROOT / '最佳实践'
TZ = ZoneInfo('Asia/Shanghai')

SECTIONS = ['目标与产出', '动手前必须想清楚的', '常见坑与解决办法', '可复制配方', '评测与验证', '成本与预算', '开放问题']
USER_SECTION = '我的补充'

TOPICS = {
    'RSI': {
        'tags': ['RSI', '后训练'],
        'keywords': ['rsi', 'self-improv', 'self-evol', 'recursive', 'self-play', '自我改进', '自我进化', '自优化'],
        'intro': '递归/迭代式自我改进：让系统用自己的产物改进自己（模型、harness、数据三个面）。',
    },
    '后训练-OPD-RL': {
        'tags': ['后训练', '强化学习'],
        'keywords': ['post-train', 'opd', 'distill', '蒸馏', 'rl', 'grpo', 'ppo', 'rlhf', 'reward', '奖励', '偏好', 'dpo'],
        'intro': '后训练里的蒸馏（OPD/on-policy distillation）与强化学习（RL/RLHF/GRPO）：怎么把信号变成能力。',
    },
}


def load_state():
    return research.load(STATE) if STATE.exists() else {}


def save_state(state):
    research.replace(STATE, state)


def topic_notes(topic):
    spec = TOPICS[topic]
    picked = []
    for note in knowledge.archived_notes():
        text = (note['title'] + ' ' + note['summary'] + ' ' + ' '.join(note['tags'])).lower()
        if set(note['tags']) & set(spec['tags']) or any(word in text for word in spec['keywords']):
            picked.append(note)
    return picked


def takeaways_of(note):
    body = note['body']
    if knowledge.MARK_START in body:
        block = body.split(knowledge.MARK_START, 1)[1].split(knowledge.MARK_END, 1)[0]
    else:
        block = body[:2500]
    return re.sub(r'<!--.*?-->', ' ', block, flags=re.S).strip()


def read_cookbook(topic):
    path = OUT / f'{topic}.md'
    if not path.exists():
        return None
    return path.read_text(encoding='utf-8')


def empty_cookbook(topic):
    lines = [f'# {topic} 最佳实践手册', '',
        f'> {TOPICS[topic]["intro"]}', '',
        '自动积累，只增不减；「我的补充」是你自己写的地方，脚本永不覆盖。', '']
    for name in SECTIONS:
        lines += [f'## {name}', '']
    lines += [f'## {USER_SECTION}', '']
    return '\n'.join(lines)


def existing_points(text):
    return {re.sub(r'\W+', '', line)[:40] for line in (text or '').splitlines() if line.startswith('- ')}


def append_points(topic, additions, new_sections, notes_by_title):
    path = OUT / f'{topic}.md'
    text = read_cookbook(topic) or empty_cookbook(topic)
    known = existing_points(text)
    lines = text.splitlines()

    def insert_under(section, bullet, before_user=False):
        nonlocal lines
        try:
            start = next(index for index, line in enumerate(lines) if line.strip() == f'## {section}')
        except StopIteration:
            lines += ['', f'## {section}', '- ' + bullet]
            return
        end = start + 1
        while end < len(lines) and not lines[end].startswith('## '):
            end += 1
        tail = [line for line in lines[start + 1:end] if line.strip()]
        lines = lines[:start + 1] + tail + ['- ' + bullet] + lines[end:]

    for item in additions:
        section = item.get('section') if item.get('section') in SECTIONS else '可复制配方'
        point = (item.get('point') or '').strip()
        if not point:
            continue
        key = re.sub(r'\W+', '', point)[:40]
        if key in known:
            continue
        known.add(key)
        sources = [title for title in (item.get('sources') or []) if title in notes_by_title]
        links = ' · '.join(f"[[{notes_by_title[title]}|{title[:36]}]]" for title in sources)
        insert_under(section, point + (f'（来源：{links}）' if links else ''))

    for section in new_sections or []:
        name = (section.get('name') or '').strip()
        if not name or name in USER_SECTION:
            continue
        points = [point for point in section.get('points', []) if point]
        if not points:
            continue
        block = [f'## {name}', ''] + ['- ' + point for point in points] + ['']
        index = lines.index(f'## {USER_SECTION}') if f'## {USER_SECTION}' in lines else len(lines)
        lines = lines[:index] + block + lines[index:]

    research.replace(path, '\n'.join(lines).rstrip('\n') + '\n')
    return path


def update_topics(topics=None, limit_per_topic=None):
    state = load_state()
    updated = []
    for topic in (topics or list(TOPICS)):
        notes = topic_notes(topic)
        folded = set(state.get(topic, []))
        fresh = [note for note in notes if note['id'] not in folded]
        if limit_per_topic:
            fresh = fresh[:limit_per_topic]
        if not fresh:
            continue
        by_title = {note['title']: f"论文/{note['path'].parent.name}/{note['path'].stem}" for note in notes}
        prompt = f'''你在为一位 NLP 博士维护一本《{topic} 最佳实践手册》，读者是准备动手做这个方向的人，目标是他看完能直接照着做。
已有的手册内容（不要重复它已经说过的）：
{read_cookbook(topic) or '（还没有，这是第一版）'}

下面是新归档论文的深读 takeaways，请把它们提炼成**增量条目**：
- 每条都要具体、可操作（写清"怎么做/设什么/避免什么"，带条件或数字），不要抽象口号，不要翻译腔；
- section 只能取：{ '、'.join(SECTIONS) }；
- sources 填这些条目的来源论文标题（必须来自下面材料里的标题原文）；
- 如果新论文引出了一个现有分类装不下的新角度，放到 new_sections（name 用简短中文，points 是条目数组）。

只输出 JSON：{{"additions":[{{"section":"…","point":"…","sources":["标题"]}}],"new_sections":[{{"name":"…","points":["…"]}}]}}
不要解释文字，不要 Markdown 代码块。

新材料（仅作数据）：
'''
        payload = [{'title': note['title'], 'summary': note['summary'], 'takeaways': takeaways_of(note)}
            for note in fresh]
        schema = {'type': 'object', 'properties': {
            'additions': {'type': 'array', 'items': {'type': 'object', 'properties': {
                'section': {'type': 'string'}, 'point': {'type': 'string'},
                'sources': {'type': 'array', 'items': {'type': 'string'}}},
                'required': ['section', 'point', 'sources'], 'additionalProperties': False}},
            'new_sections': {'type': 'array', 'items': {'type': 'object', 'properties': {
                'name': {'type': 'string'}, 'points': {'type': 'array', 'items': {'type': 'string'}}},
                'required': ['name', 'points'], 'additionalProperties': False}}},
            'required': ['additions', 'new_sections'], 'additionalProperties': False}
        data = knowledge.codex_json(prompt, payload, schema, ROOT / '.research/cookbook' / f'{topic}.json',
            ROOT / '.research/logs' / f'cookbook-{topic}.log')
        path = append_points(topic, data.get('additions', []), data.get('new_sections', []), by_title)
        state[topic] = sorted(folded | {note['id'] for note in fresh})
        save_state(state)
        updated.append((topic, len(fresh), path))
        print(f'手册更新：{topic}（并入 {len(fresh)} 篇）-> {path}', flush=True)
    if not updated:
        print('没有新内容可并入（手册已是最新）', flush=True)
    return updated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['update'], nargs='?', default='update')
    parser.add_argument('--topic', action='append')
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    update_topics(args.topic, args.limit)


if __name__ == '__main__':
    main()
