#!/usr/bin/env python3
"""调研：给一个问题，多轮检索论文 → 比对 → 读全文取证 → 给出可用结论。

流程（每一轮都有单独的模型调用和中间产物，避免一次生成糊一个答案）：
  1) 拆题   模型给出 4–6 个检索式、纳入/排除标准
  2) 检索   arXiv API 逐个检索并去重，再用 Semantic Scholar 补引用数和发表处
  3) 粗读   模型给候选排序，抽「做法 / 需要什么 / 报告的数字 / 工业可行性」
  4) 深读   对排在前面的几篇取正文，核对数字与限制条件
  5) 结论   首选 + 备选 + 适用条件 + 还缺什么，全部挂到具体论文

产物：调研/<日期>-<slug>.md（人读）+ 索引/调研.md（清单）

  python3 scripts/survey.py "现有效果最好的数据难度判断方法是什么" --slug difficulty
"""
import argparse
import datetime as dt
import json
import re
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import knowledge
import research

ROOT = knowledge.ROOT
STATE = ROOT / '.research/survey'
OUT = ROOT / '调研'
TZ = ZoneInfo('Asia/Shanghai')
ARXIV = 'http://export.arxiv.org/api/query?'
S2 = 'https://api.semanticscholar.org/graph/v1/paper/search?'
NS = {'a': 'http://www.w3.org/2005/Atom'}


def plan(question):
    prompt = '''你在帮一位 NLP 博士做文献调研。先把问题拆成可执行的检索计划。
要求：
- queries：6–8 条英文检索式，**换角度覆盖**：不同任务（预训练/指令/偏好/评测题目）、
  不同方法族（免模型的启发式、需要小模型打分、需要成对比较、用基准题反推）、不同说法（同义词、上位词、工程视角）。
  每条都短、适合放进 arXiv 的 all: 字段；不要都挤在一个子领域里。
- must_have：判断一篇论文「值得进候选」的必要条件（例如必须给出可复现的指标或数据）；
- exclude：应该排除的（例如纯理论、只讲某个具体数据集不做通用指标）；
- reading_focus：读这些论文时最该盯住的三件事。
只输出 JSON。'''
    schema = {'type': 'object', 'properties': {
        'queries': {'type': 'array', 'items': {'type': 'string'}},
        'must_have': {'type': 'array', 'items': {'type': 'string'}},
        'exclude': {'type': 'array', 'items': {'type': 'string'}},
        'reading_focus': {'type': 'array', 'items': {'type': 'string'}}},
        'required': ['queries', 'must_have', 'exclude', 'reading_focus'], 'additionalProperties': False}
    return knowledge.codex_json(prompt, {'question': question}, schema,
        STATE / 'plan.json', STATE / 'logs' / 'plan.log')


def arxiv_search(query, limit=25):
    # 模型有时会把 arXiv 的字段前缀一起写进来（all:xxx），这里去掉再拼。
    query = re.sub(r'^\s*(all|ti|abs):\s*', '', str(query)).strip()
    url = ARXIV + urllib.parse.urlencode({'search_query': f'all:{query}', 'start': 0,
        'max_results': limit, 'sortBy': 'relevance'})
    try:
        xml = knowledge.http_get(url)
    except Exception as error:
        print(f'  arXiv 检索失败（{query}）：{type(error).__name__}', flush=True)
        return []
    rows = []
    for entry in ET.fromstring(xml).findall('a:entry', NS):
        link = (entry.findtext('a:id', '', NS) or '').strip()
        ident = re.sub(r'^https?://arxiv.org/abs/', '', link)
        # arXiv 返回的是 2506.01317v2 这种带版本号的 id，去掉版本号才能拼正文地址。
        match = re.match(r'^(\d{4}\.\d{4,5})', ident)
        if not match:
            continue
        ident = match.group(1)
        rows.append({'id': ident, 'title': ' '.join((entry.findtext('a:title', '', NS) or '').split()),
            'abstract': ' '.join((entry.findtext('a:summary', '', NS) or '').split()),
            'published': (entry.findtext('a:published', '', NS) or '')[:10],
            'authors': [a.findtext('a:name', '', NS) for a in entry.findall('a:author', NS)][:6],
            'url': 'https://arxiv.org/abs/' + ident})
    return rows


def citations(ids, batch=40):
    """Semantic Scholar 补引用数与发表处；失败不影响主流程。"""
    found = {}
    ids = list(ids)
    for start in range(0, len(ids), batch):
        chunk = ids[start:start + batch]
        body = {'ids': ['ARXIV:' + ident for ident in chunk]}
        try:
            import urllib.request
            request = urllib.request.Request('https://api.semanticscholar.org/graph/v1/paper/batch?fields=title,citationCount,venue,year,externalIds',
                data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
            opener = urllib.request.build_opener(urllib.request.ProxyHandler(
                {'http': knowledge.LOCAL_PROXY, 'https': knowledge.LOCAL_PROXY}))
            with opener.open(request, timeout=45) as response:
                rows = json.load(response)
            for row in rows or []:
                if not row:
                    continue
                ident = ((row.get('externalIds') or {}).get('ArXiv') or '')
                if ident:
                    found[ident] = {'citations': row.get('citationCount'), 'venue': row.get('venue') or ''}
        except Exception as error:
            print(f'  Semanticscholar 查询失败：{type(error).__name__}（不影响后续）', flush=True)
        time.sleep(1.2)
    return found


def collect(question, planned, per_query=20):
    papers = {}
    for query in planned['queries']:
        rows = arxiv_search(query, per_query)
        print(f'  检索「{query}」→ {len(rows)} 篇', flush=True)
        for row in rows:
            papers.setdefault(row['id'], row)
        time.sleep(1)
    extra = citations(papers)
    for ident, row in papers.items():
        row.update(extra.get(ident) or {'citations': None, 'venue': ''})
    return list(papers.values())


def shortlist(question, planned, papers, limit=14):
    prompt = '''下面是一次文献检索的候选池。请挑出**最能回答这个问题**的论文，并按主题分组。
对每篇给出：它到底做了什么、需要什么（标注/训练/额外模型）、报告了什么可核对的结果、工业化难度（高/中/低，理由一句）、是否值得深读。
不要为了凑数塞进不相关的；也不要把没读过正文就当成定论，用给出的标题和摘要判断。
只输出 JSON。'''
    schema = {'type': 'object', 'properties': {'papers': {'type': 'array', 'items': {'type': 'object', 'properties': {
        'id': {'type': 'string'}, 'method': {'type': 'string'}, 'needs': {'type': 'string'},
        'reported': {'type': 'string'}, 'industrial': {'type': 'string'},
        'deep_read': {'type': 'boolean'}}, 'required': ['id', 'method', 'needs', 'reported', 'industrial', 'deep_read'],
        'additionalProperties': False}}}, 'required': ['papers'], 'additionalProperties': False}
    payload = {'question': question, 'must_have': planned['must_have'], 'exclude': planned['exclude'],
        'reading_focus': planned['reading_focus'],
        'candidates': [{k: p.get(k) for k in ('id', 'title', 'abstract', 'published', 'citations', 'venue')}
            for p in papers]}
    return knowledge.codex_json(prompt, payload, schema, STATE / 'shortlist.json', STATE / 'logs' / 'shortlist.log')


def expand(question, planned, papers, top=30):
    """第二轮：先看第一轮撞到了什么，再补第一轮没覆盖到的方向。"""
    words = {word for query in planned['queries'] for word in re.findall(r'[a-zA-Z]{4,}', query.lower())}
    def score(paper):
        text = (paper['title'] + ' ' + paper.get('abstract', '')).lower()
        return sum(1 for word in words if word in text)
    sample = sorted(papers, key=score, reverse=True)[:top]
    prompt = '''这是第一轮检索到的论文。请判断：要回答这个问题，还有哪些常见做法/说法没有被覆盖？
给出 3–4 条**新的**英文检索式去补这些缺口（换术语、换子领域、找综述或基准评测）。
不要重复已有的检索式；宁可少而准。
只输出 JSON。'''
    schema = {'type': 'object', 'properties': {
        'missing': {'type': 'array', 'items': {'type': 'string'}},
        'queries': {'type': 'array', 'items': {'type': 'string'}}},
        'required': ['missing', 'queries'], 'additionalProperties': False}
    payload = {'question': question, 'used_queries': planned['queries'],
        'papers': [{'id': p['id'], 'title': p['title'], 'abstract': p.get('abstract', '')[:400]} for p in sample]}
    return knowledge.codex_json(prompt, payload, schema, STATE / 'expand.json', STATE / 'logs' / 'expand.log')


def deep_read(question, chosen, limit=4):
    facts = []
    for paper in chosen[:limit]:
        try:
            note = {'id': paper['id'], 'title': paper['title'], 'source': 'arxiv',
                'body': '', 'summary': paper.get('abstract', '')}
            text, level = knowledge.paper_text(note)
        except Exception as error:
            facts.append({'id': paper['id'], 'title': paper['title'], 'text': '',
                'note': f'正文获取失败 {type(error).__name__}'})
            continue
        excerpt = (text or '')[:24000]
        facts.append({'id': paper['id'], 'title': paper['title'], 'text': excerpt, 'note': level})
        print(f'  深读 {paper["id"]}：{level} {len(excerpt)} 字', flush=True)
    if not facts:
        return {'papers': []}
    prompt = '''下面几篇论文的正文节选（可能不完整）。只依据这些文字，提取与问题直接相关的事实：
每个方法「怎么做」「需要什么成本」「在什么设置下报告了哪些具体数字」「作者自己承认的局限」。
写不清就写「正文里没有」；不要用摘要之外的知识补数字。
只输出 JSON。'''
    schema = {'type': 'object', 'properties': {'papers': {'type': 'array', 'items': {'type': 'object', 'properties': {
        'id': {'type': 'string'}, 'how': {'type': 'string'}, 'cost': {'type': 'string'},
        'numbers': {'type': 'string'}, 'limits': {'type': 'string'}},
        'required': ['id', 'how', 'cost', 'numbers', 'limits'], 'additionalProperties': False}}},
        'required': ['papers'], 'additionalProperties': False}
    return knowledge.codex_json(prompt, {'question': question, 'papers': facts}, schema,
        STATE / 'deep.json', STATE / 'logs' / 'deep.log')


def synthesize(question, planned, shortlisted, facts):
    prompt = '''你在为一个工业界 AI Lab 的研究者写调研结论。读者要拿去决定「先试哪个」。
必须做到：
1. 先给一句话答案：现有效果最好且最适合工业落地的，是哪一个（或哪一类）；分不开就分场景说清。
2. picks：逐个候选写清「为什么选它 / 需要什么前提 / 什么情况下它不work / 证据出处」；证据只能引用给定的论文 id 和它报告过的数字。
3. comparison：一张能直接比的表（方法、需要什么、成本量级、效果证据、成熟度）。
4. gaps：现有文献还没解决什么，缺什么才能下更硬的结论。
5. next_steps：1–2 周能做的验证实验（数据、基线、指标）。
说话要直白具体，不要翻译腔，不要「值得关注」「具有重要意义」这类空话；没有证据就说没有证据。
只输出 JSON。'''
    schema = {'type': 'object', 'properties': {
        'answer': {'type': 'string'},
        'picks': {'type': 'array', 'items': {'type': 'object', 'properties': {
            'name': {'type': 'string'}, 'why': {'type': 'string'}, 'conditions': {'type': 'string'},
            'fails_when': {'type': 'string'}, 'evidence': {'type': 'array', 'items': {'type': 'object', 'properties': {
                'id': {'type': 'string'}, 'claim': {'type': 'string'}},
                'required': ['id', 'claim'], 'additionalProperties': False}}},
            'required': ['name', 'why', 'conditions', 'fails_when', 'evidence'], 'additionalProperties': False}},
        'comparison': {'type': 'array', 'items': {'type': 'object', 'properties': {
            'method': {'type': 'string'}, 'needs': {'type': 'string'}, 'cost': {'type': 'string'},
            'effect': {'type': 'string'}, 'maturity': {'type': 'string'}},
            'required': ['method', 'needs', 'cost', 'effect', 'maturity'], 'additionalProperties': False}},
        'gaps': {'type': 'array', 'items': {'type': 'string'}},
        'next_steps': {'type': 'array', 'items': {'type': 'string'}}},
        'required': ['answer', 'picks', 'comparison', 'gaps', 'next_steps'], 'additionalProperties': False}
    payload = {'question': question, 'criteria': {'must_have': planned['must_have'],
        'exclude': planned['exclude'], 'reading_focus': planned['reading_focus']},
        'candidates': shortlisted, 'fulltext_facts': facts}
    return knowledge.codex_json(prompt, payload, schema, STATE / 'answer.json', STATE / 'logs' / 'answer.log')


def render(question, planned, papers, shortlisted, facts, answer, slug):
    date = dt.datetime.now(TZ).date().isoformat()
    by_id = {p['id']: p for p in papers}
    lines = [f'---\ndate: {date}\ntype: survey\nquestion: "{question}"\n---', '',
        f'# 调研：{question}', '',
        f'检索 {len(papers)} 篇候选（{len(planned["queries"])} 条检索式），深读 {len(facts.get("papers") or [])} 篇。',
        '', '## 一句话答案', '', answer['answer'], '', '## 候选与取舍', '']
    for item in answer['picks']:
        lines += [f'### {item["name"]}', '',
            f'- 为什么选它：{item["why"]}', f'- 前提：{item["conditions"]}',
            f'- 什么时候不 work：{item["fails_when"]}']
        for evidence in item['evidence']:
            paper = by_id.get(evidence['id']) or {}
            lines.append(f'- 证据（{evidence["id"]} {paper.get("title", "")[:70]}）：{evidence["claim"]}')
        lines.append('')
    lines += ['## 横向对比', '', '| 方法 | 需要什么 | 成本量级 | 效果证据 | 成熟度 |', '|---|---|---|---|---|']
    for row in answer['comparison']:
        lines.append(f'| {row["method"]} | {row["needs"]} | {row["cost"]} | {row["effect"]} | {row["maturity"]} |')
    lines += ['', '## 还缺什么', ''] + [f'- {item}' for item in answer['gaps']]
    lines += ['', '## 下一步能做的验证', ''] + [f'- {item}' for item in answer['next_steps']]
    lines += ['', '## 候选论文清单（只列粗读后进入比较的）', '']
    for paper in shortlisted:
        used = any(paper['id'] == e['id'] for item in answer['picks'] for e in item['evidence'])
        mark = '（已引用）' if used else ''
        lines.append(f'- `{paper["id"]}` [{paper["title"]}]({paper["url"]}){mark} · {paper.get("published", "")}'
            + (f' · {paper["citations"]} 引用' if paper.get('citations') is not None else ''))
    lines += ['', f'检索共命中 {len(papers)} 篇，其余 {max(len(papers) - len(shortlisted), 0)} 篇与问题关系不大，未进入比较。']
    lines += ['', '## 检索过程', '', f'- 检索式：{"；".join(planned["queries"])}',
        f'- 纳入：{"；".join(planned["must_have"])}', f'- 排除：{"；".join(planned["exclude"])}',
        f'- 读的时候盯：{"；".join(planned["reading_focus"])}']
    path = OUT / f'{date}-{slug}.md'
    research.replace(path, '\n'.join(lines) + '\n')
    build_index()
    return path


def build_index():
    files = sorted(OUT.glob('2*.md'))
    lines = ['# 调研索引', '', f'共 {len(files)} 份。每次调研的完整过程与证据都在各自文件里。', '']
    for path in reversed(files):
        text = path.read_text(encoding='utf-8')
        fields, _ = research.frontmatter(path)
        lines.append(f'- [[调研/{path.stem}]] {fields.get("question", "")}')
    research.replace(ROOT / '索引/调研.md', '\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('question')
    parser.add_argument('--slug', default='')
    parser.add_argument('--per-query', type=int, default=20)
    parser.add_argument('--deep', type=int, default=4)
    parser.add_argument('--render-only', action='store_true', help='用上次的中间产物重写报告，不再检索/调模型')
    args = parser.parse_args()
    STATE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    slug = args.slug or re.sub(r'\W+', '-', args.question)[:40].strip('-')
    if args.render_only:
        planned = research.load(STATE / 'plan.json')
        papers = research.load(STATE / 'papers.json')['papers']
        short = research.load(STATE / 'shortlist.json')
        index = {p['id']: p for p in papers}
        picks = [dict(index[item['id']], **item) for item in short['papers'] if item['id'] in index]
        facts = research.load(STATE / 'deep.json') if (STATE / 'deep.json').exists() else {'papers': []}
        answer = research.load(STATE / 'answer.json')
        print('重写报告 →', render(args.question, planned, papers, picks, facts, answer, slug), flush=True)
        return
    print('[1/5] 拆题', flush=True)
    planned = plan(args.question)
    print('  检索式：' + '；'.join(planned['queries']), flush=True)
    print('[2/5] 检索', flush=True)
    papers = collect(args.question, planned, args.per_query)
    if not papers:
        raise SystemExit('检索为空；检查网络或代理')
    print(f'  去重后 {len(papers)} 篇', flush=True)
    print('[3/6] 第二轮：看结果补检索', flush=True)
    more = expand(args.question, planned, papers)
    print('  补检索式：' + '；'.join(more['queries']), flush=True)
    if more['queries']:
        fresh = collect(args.question, {'queries': more['queries']}, args.per_query)
        new_ids = [row['id'] for row in fresh if row['id'] not in {p['id'] for p in papers}]
        papers += [row for row in fresh if row['id'] in set(new_ids)]
        print(f'  新增 {len(new_ids)} 篇，累计 {len(papers)} 篇', flush=True)
    research.replace(STATE / 'papers.json', {'papers': papers})
    print('[4/6] 粗读与排序', flush=True)
    short = shortlist(args.question, planned, papers)
    index = {p['id']: p for p in papers}
    picks = [dict(index[item['id']], **item) for item in short['papers'] if item['id'] in index]
    deep = [p for p in picks if p.get('deep_read')] or picks
    print('[5/6] 深读正文', flush=True)
    facts = deep_read(args.question, deep, args.deep)
    print('[6/6] 写结论', flush=True)
    answer = synthesize(args.question, planned, picks, facts)
    path = render(args.question, planned, papers, picks, facts, answer, slug)
    print(f'完成 → {path}', flush=True)


if __name__ == '__main__':
    main()
