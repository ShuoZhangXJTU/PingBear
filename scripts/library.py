#!/usr/bin/env python3
"""归档对话入口：在已归档笔记（含深读、问答沉淀）与专题体系页上做检索和提问。

search 只做本地检索，秒回，列出命中的笔记。
ask    先用检索挑出最相关的几篇，再让模型带着它们的深读和问答沉淀回答，并给出引用。
"""
import argparse
import datetime as dt
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from zoneinfo import ZoneInfo

import knowledge
import research

ROOT = research.ROOT
STATE = ROOT / '.research/knowledge'
LOG = ROOT / '问答/知识助手.md'
TZ = ZoneInfo('Asia/Shanghai')
ASCII = re.compile(r'[a-z0-9][a-z0-9\-_.]{1,}')
CJK = re.compile(r'[\u4e00-\u9fff]+')
FIELDS = [('title', 3.0), ('tags', 3.0), ('summary', 2.0), ('takeaways', 2.2), ('qa', 2.2), ('body', 1.0)]
MARKER = re.compile(r'<!--.*?-->', re.S)


def tokens(text):
    text = (text or '').lower()
    found = ASCII.findall(text)
    for chunk in CJK.findall(text):
        found.extend(chunk[index:index + 2] for index in range(len(chunk) - 1))
        if len(chunk) == 1:
            found.append(chunk)
    return found


def documents():
    docs = []
    for note in knowledge.archived_notes():
        docs.append({'id': note['id'], 'path': str(note['path'].relative_to(ROOT)), 'title': note['title'],
            'tags': ' '.join(note['tags']), 'summary': note['summary'],
            'takeaways': MARKER.sub(' ', knowledge.section_text(note['body'], '## 深读 takeaway')),
            'qa': knowledge.section_text(note['body'], '## 问答沉淀'),
            'body': note['body'][:20000], 'kind': '论文'})
    topics_dir = ROOT / '专题'
    if topics_dir.exists():
        for path in sorted(topics_dir.glob('*.md')):
            text = path.read_text(encoding='utf-8')
            docs.append({'id': f'专题/{path.stem}', 'path': str(path.relative_to(ROOT)), 'title': f'专题 · {path.stem}',
                'tags': path.stem, 'summary': text[:400], 'takeaways': text[:8000], 'qa': '', 'body': text[:20000],
                'kind': '专题页'})
    return docs


def search(query, limit=8):
    query_tokens = Counter(tokens(query))
    if not query_tokens:
        return []
    scored = []
    for doc in documents():
        score = 0.0
        for name, weight in FIELDS:
            counts = Counter(tokens(doc.get(name, '')))
            if not counts:
                continue
            for token, query_count in query_tokens.items():
                hits = counts.get(token, 0)
                if hits:
                    score += weight * math.log(1 + hits) * min(query_count, 3)
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda item: -item[0])
    return [dict(doc, score=round(score, 2)) for score, doc in scored[:limit]]


def ask(question, limit=6):
    hits = search(question, limit=limit)
    prompt = '''你在帮一位 NLP 博士翻他自己的论文归档库（含深读 takeaways、他自己提问沉淀的要点）。
只依据下面给出的归档材料回答；归档里没有的，直接说“归档里没有”，可以顺带说明还需要补什么类型的论文，但不要编造论文、数字或结论。
回答用中文，先给结论再给依据，必要时分点；凡是引用了某篇归档，就在句末用 [[论文/编号|标题]] 的形式标注来源。answer 控制在 600 字内。
按费曼学习法写：外行也能看懂，短句，术语当场用一句白话解释，不要堆抽象名词。
'''
    payload = {'question': question, 'hits': [
        {'id': hit['id'], 'title': hit['title'], 'tags': hit['tags'], 'summary': hit['summary'],
         'takeaways': hit['takeaways'][:4000], 'qa_points': hit['qa'][:2000]} for hit in hits]}
    schema = {'type': 'object', 'properties': {
        'answer': {'type': 'string'},
        'used': {'type': 'array', 'items': {'type': 'string'}},
        'gaps': {'type': 'string'}},
        'required': ['answer', 'used', 'gaps'], 'additionalProperties': False}
    data = knowledge.codex_json(prompt, payload, schema, STATE / 'ask' / 'archive.json',
        STATE / 'logs' / 'archive-ask.log')
    stamp = f'{dt.datetime.now(TZ):%Y-%m-%d %H:%M}'
    if LOG.exists():
        research.replace(LOG, LOG.read_text(encoding='utf-8').rstrip('\n') + '\n\n' +
            f'## {stamp}\n\n**问**：{question}\n\n**答**：{data["answer"].strip()}\n\n' +
            (f'**缺口**：{data["gaps"].strip()}\n' if data.get('gaps') else ''))
    else:
        research.replace(LOG, f'# 知识助手对话记录\n\n自动记录每次对归档的提问；新问题在 Obsidian 里用命令面板的「归档问答」。\n\n'
            f'## {stamp}\n\n**问**：{question}\n\n**答**：{data["answer"].strip()}\n\n' +
            (f'**缺口**：{data["gaps"].strip()}\n' if data.get('gaps') else ''))
    answers = STATE / 'answers'
    answers.mkdir(parents=True, exist_ok=True)
    research.replace(answers / 'archive.json', {'at': dt.datetime.now(TZ).isoformat(), 'question': question,
        'answer': data['answer'].strip(), 'used': data.get('used', []), 'gaps': data.get('gaps', ''),
        'hits': [{'id': hit['id'], 'title': hit['title'], 'path': hit['path'], 'score': hit['score']} for hit in hits]})
    return data, hits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    find = sub.add_parser('search')
    find.add_argument('--query', required=True)
    find.add_argument('--limit', type=int, default=8)
    ask_parser = sub.add_parser('ask')
    ask_parser.add_argument('--question', required=True)
    args = parser.parse_args()
    STATE.mkdir(parents=True, exist_ok=True)
    if args.command == 'search':
        hits = search(args.query, limit=args.limit)
        answers = STATE / 'answers'
        answers.mkdir(parents=True, exist_ok=True)
        research.replace(answers / 'archive-search.json', {'at': dt.datetime.now(TZ).isoformat(),
            'query': args.query, 'hits': [{'id': hit['id'], 'title': hit['title'], 'path': hit['path'],
                'score': hit['score'], 'summary': hit['summary']} for hit in hits]})
        for hit in hits:
            print(f"{hit['score']:>6}  {hit['id']}  {hit['title'][:70]}  [{hit['kind']}]")
    else:
        data, hits = ask(args.question)
        print(data['answer'])


if __name__ == '__main__':
    main()
