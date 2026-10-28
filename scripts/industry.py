#!/usr/bin/env python3
"""业界洞察：联网找竞品，看它们具体做了什么、差异在哪。

流程（先找竞品，再看做法）：
  1) 拆题：模型给出竞品检索词 + 要重点看的厂商 + 典型场景；
  2) 联网：DuckDuckGo HTML 搜竞品与产品功能，抓前几条结果页的正文；
  3) 本地补充：官方博客与论文（.research/blogs、.research/digests）里的实践证据；
  4) 对比：模型输出「竞品清单 → 每家做了什么 → 场景差异 → 空白与机会」。

  python3 scripts/industry.py "多模态交互"
  python3 scripts/industry.py "agent harness" --slug harness --pages 10
"""
import argparse
import base64
import datetime as dt
import html as html_mod
import json
import re
import sys
import urllib.parse
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import knowledge
import research

ROOT = research.ROOT
STATE = ROOT / '.research/industry'
OUT = ROOT / '业界洞察'
TZ = ZoneInfo('Asia/Shanghai')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36'


def plan(topic, seed=''):
    prompt = '''你在帮一位 AI Lab 研究员做「业界洞察」。先拆出要搜的东西。
要求：
- players：这个方向上值得重点看的公司/产品（6–10 个，写大家熟悉的名字）；
- web_queries：4–6 条中文检索词，专门用来找竞品（例如「<topic> 竞品」「<topic> 产品 功能」「手机 摄像头 视觉问答 产品」）；
- scenarios：这类技术通常落在哪些用户场景。
只输出 JSON。'''
    schema = {'type': 'object', 'properties': {
        'players': {'type': 'array', 'items': {'type': 'string'}},
        'web_queries': {'type': 'array', 'items': {'type': 'string'}},
        'scenarios': {'type': 'array', 'items': {'type': 'string'}}},
        'required': ['players', 'web_queries', 'scenarios'], 'additionalProperties': False}
    return knowledge.codex_json(prompt, {'topic': topic, 'hint': seed}, schema,
        STATE / 'plan.json', STATE / 'logs' / 'plan.log')


def unwrap_ddg(href):
    if 'uddg=' in href:
        return urllib.parse.unquote(href.split('uddg=', 1)[1].split('&', 1)[0])
    if href.startswith('//'):
        return 'https:' + href
    return href


def unwrap_bing(link):
    """Bing 的结果链接是 bing.com/ck/a?...&u=a1<base64url>，解出真实地址。"""
    if 'bing.com/ck/a' not in link:
        return link
    params = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
    raw = (params.get('u') or [''])[0]
    if raw.startswith('a1'):
        raw = raw[2:]
    if not raw:
        return link
    try:
        return base64.urlsafe_b64decode(raw + '=' * (-len(raw) % 4)).decode('utf-8', 'replace')
    except Exception:
        return link


def clean_html(text):
    return re.sub(r'\s+', ' ', html_mod.unescape(re.sub(r'<[^>]+>', '', text or ''))).strip()


def web_search(query, limit=8):
    """先用 Bing 网页搜索（实测可解析），失败再退回 DuckDuckGo HTML。"""
    url = 'https://www.bing.com/search?' + urllib.parse.urlencode(
        {'q': query, 'setlang': 'zh-CN', 'count': 30})
    try:
        page = knowledge.http_get(url, timeout=30)
    except Exception as error:
        print(f'  搜索失败（{query}）：{type(error).__name__}', flush=True)
        return []
    rows = []
    for block in page.split('<li class="b_algo"')[1:]:
        head = re.search(r'<h2[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        if not head:
            continue
        link = unwrap_bing(html_mod.unescape(head.group(1)))
        if not link.startswith('http'):
            continue
        snippet = re.search(r'<p[^>]*>(.*?)</p>', block, re.S)
        rows.append({'title': clean_html(head.group(2)), 'url': link,
            'snippet': clean_html(snippet.group(1) if snippet else ''), 'query': query})
        if len(rows) >= limit:
            break
    return rows


def page_text(url, limit=6000):
    try:
        text = knowledge.plain_text(knowledge.http_get(url, timeout=30), limit * 3)
    except Exception:
        return ''
    return re.sub(r'\s+', ' ', text)[:limit]


def gather_web(queries, pages=10):
    hits, seen = [], set()
    for query in queries:
        found = web_search(query)
        print(f'  搜索「{query}」→ {len(found)} 条', flush=True)
        for item in found:
            key = re.sub(r'\W+', '', item['title'].lower())[:60]
            if not key or key in seen:
                continue
            seen.add(key)
            hits.append(item)
    ordered = sorted(hits, key=lambda it: -len(it.get('snippet') or ''))[:pages]
    evidence = []
    for index, item in enumerate(ordered, 1):
        text = page_text(item['url'])
        evidence.append({'id': f'web-{index}', 'kind': 'web', 'title': item['title'], 'url': item['url'],
            'company': '', 'date': '', 'summary': item['snippet'], 'text': text, 'query': item['query']})
        print(f'  读取 {item["url"][:70]}（{len(text)} 字）', flush=True)
    return evidence


def gather_local(days=120):
    since = (dt.datetime.now(TZ).date() - dt.timedelta(days=days)).isoformat()
    items = []
    for path in sorted((ROOT / '.research/blogs/digests').glob('*.json')):
        if path.stem < since:
            continue
        for item in research.load(path).get('papers') or []:
            items.append({'id': item.get('id'), 'kind': 'blog', 'company': item.get('origin_name') or '',
                'title': item.get('title') or '', 'summary': item.get('summary') or '',
                'tags': item.get('tags') or [], 'url': item.get('url') or '', 'date': item.get('date') or path.stem})
    for path in sorted((ROOT / '.research/digests').glob('*.json')):
        if path.stem < since:
            continue
        for item in research.load(path).get('papers') or []:
            items.append({'id': item.get('id'), 'kind': 'paper', 'company': item.get('hf_organization') or '未知',
                'title': item.get('title') or '', 'summary': item.get('abstract') or '',
                'tags': item.get('tags') or [], 'url': item.get('url') or '', 'date': path.stem})
    return items


def pick_local(items, players, limit=40):
    words = [p.lower() for p in players]
    scored = []
    for item in items:
        text = (item['title'] + ' ' + item['summary'] + ' ' + ' '.join(item['tags'])).lower()
        hits = sum(1 for word in words if word and word in text)
        if hits:
            scored.append((hits, item))
    scored.sort(key=lambda pair: (-pair[0], pair[1].get('date') or ''))
    return [item for _score, item in scored[:limit]]


def insight(topic, planned, web, local):
    prompt = '''你在给一位 AI Lab 研究员写「业界洞察」。必须先回答“有哪些竞品”，再说每家具体做了什么、差异在哪。

要求：
1. competitors：逐个竞品（产品/公司）写清楚——形态（手机助手/独立 App/眼镜/系统级）、具体能做什么、
   怎么交互（拍照/实时视频/指向/圈选/语音）、面向什么场景、成熟度（已上线/内测/研究）。
   evidence 只能引用给定条目的 id；优先用 web 条目。
2. differences：横向比出真实差异（实时还是静态、是否主动引导、是否有系统数据权限、硬件载体、目标人群、语言/地区）。
3. scenarios：竞品各自押的场景，以及同一场景下做法差异。
4. gaps / opportunities：这些竞品还没做好什么；结合一位 NLP 博士做 RSI / harness / 后训练的背景，哪里能切入。
5. watchlist：接下来值得盯的信号。
材料里没有写的（例如具体模型、准确率、上线时间）就写「材料未说明」，不要补。
只输出 JSON。'''
    schema = {'type': 'object', 'properties': {
        'answer': {'type': 'string'},
        'competitors': {'type': 'array', 'items': {'type': 'object', 'properties': {
            'name': {'type': 'string'}, 'company': {'type': 'string'}, 'form': {'type': 'string'},
            'what': {'type': 'string'}, 'interaction': {'type': 'string'}, 'scenario': {'type': 'string'},
            'maturity': {'type': 'string'},
            'evidence': {'type': 'array', 'items': {'type': 'object', 'properties': {
                'id': {'type': 'string'}, 'claim': {'type': 'string'}},
                'required': ['id', 'claim'], 'additionalProperties': False}}},
            'required': ['name', 'company', 'form', 'what', 'interaction', 'scenario', 'maturity', 'evidence'],
            'additionalProperties': False}},
        'differences': {'type': 'array', 'items': {'type': 'string'}},
        'scenarios': {'type': 'array', 'items': {'type': 'object', 'properties': {
            'scenario': {'type': 'string'}, 'who': {'type': 'string'}, 'difference': {'type': 'string'}},
            'required': ['scenario', 'who', 'difference'], 'additionalProperties': False}},
        'gaps': {'type': 'array', 'items': {'type': 'string'}},
        'opportunities': {'type': 'array', 'items': {'type': 'string'}},
        'watchlist': {'type': 'array', 'items': {'type': 'string'}}},
        'required': ['answer', 'competitors', 'differences', 'scenarios', 'gaps', 'opportunities', 'watchlist'],
        'additionalProperties': False}
    payload = {'topic': topic, 'players': planned['players'], 'web_evidence': web, 'local_evidence': local}
    return knowledge.codex_json(prompt, payload, schema, STATE / 'answer.json', STATE / 'logs' / 'answer.log')


def render(topic, planned, web, local, data, slug):
    date = dt.datetime.now(TZ).date().isoformat()
    by_id = {item['id']: item for item in web + local}
    lines = [f'---\ndate: {date}\ntype: industry-insight\ntopic: "{topic}"\n---', '',
        f'# 业界洞察：{topic}', '',
        f'联网检索 {len(web)} 个页面 + 本机博客/论文 {len(local)} 条。', '',
        '## 一句话结论', '', data['answer'], '', '## 竞品清单', '',
        '| 竞品 | 公司 | 形态 | 具体做什么 | 交互方式 | 场景 | 成熟度 |', '|---|---|---|---|---|---|---|']
    for row in data['competitors']:
        lines.append(f'| {row["name"]} | {row["company"]} | {row["form"]} | {row["what"]} | '
            f'{row["interaction"]} | {row["scenario"]} | {row["maturity"]} |')
    lines += ['', '## 差异在哪', '']
    lines += [f'- {item}' for item in data['differences']]
    lines += ['', '## 场景拆解', '']
    for row in data['scenarios']:
        lines += [f'### {row["scenario"]}', '', f'- 谁在做：{row["who"]}', f'- 做法差异：{row["difference"]}', '']
    lines += ['## 空白与机会', '']
    lines += [f'- **空白**：{item}' for item in data['gaps']]
    lines += [f'- **机会**：{item}' for item in data['opportunities']]
    lines += ['', '## 接下来盯什么', ''] + [f'- {item}' for item in data['watchlist']]
    lines += ['', '## 竞品证据', '']
    for row in data['competitors']:
        lines.append(f'### {row["name"]}')
        for ev in row['evidence']:
            item = by_id.get(ev['id']) or {}
            link = f'[{item.get("title", ev["id"])}]({item["url"]})' if item.get('url') else item.get('title', ev['id'])
            lines.append(f'- {ev["claim"]}（{link}）')
        lines.append('')
    lines += ['## 全部来源', '']
    for item in web:
        lines.append(f'- 网页 `{item["id"]}` [{item["title"]}]({item["url"]})')
    for item in local:
        lines.append(f'- 本地 {item["kind"]} `{item["id"]}` [{item["title"]}]({item["url"]}) · {item.get("company")}')
    lines += ['', f'检索词：{"；".join(planned["web_queries"])}']
    path = OUT / f'{date}-{slug}.md'
    research.replace(path, '\n'.join(lines) + '\n')
    build_index()
    return path


def build_index():
    files = sorted(OUT.glob('2*.md'))
    lines = ['# 业界洞察索引', '', f'共 {len(files)} 份。', '']
    for path in reversed(files):
        fields, _ = research.frontmatter(path)
        lines.append(f'- [[业界洞察/{path.stem}]] {fields.get("topic", "")}')
    research.replace(ROOT / '索引/业界洞察.md', '\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('topic')
    parser.add_argument('--days', type=int, default=120)
    parser.add_argument('--slug', default='')
    parser.add_argument('--pages', type=int, default=8)
    parser.add_argument('--local-limit', type=int, default=40)
    parser.add_argument('--seed', default='', help='点名要覆盖的竞品/厂商，逗号分隔，如「小艺看世界,Gemini Live」')
    parser.add_argument('--web-file', help='用已经搜好并落盘的网页证据 JSON（[{id,title,url,company,summary}]）')
    args = parser.parse_args()
    STATE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    print('[1/4] 拆竞品检索词', flush=True)
    planned = plan(args.topic, args.seed)
    if args.seed:
        planned['players'] = list(dict.fromkeys([p.strip() for p in args.seed.split(',') if p.strip()] + planned['players']))
    print('  玩家：' + '、'.join(planned['players']), flush=True)
    print('  检索：' + '；'.join(planned['web_queries']), flush=True)
    print('[2/4] 联网找竞品', flush=True)
    if args.web_file:
        web = json.loads(Path(args.web_file).read_text(encoding='utf-8'))
        for item in web:
            item.setdefault('kind', 'web')
            item.setdefault('text', '')
        print(f'  读取网页证据 {len(web)} 条（来自 {args.web_file}）', flush=True)
    else:
        web = gather_web(planned['web_queries'], args.pages)
    print('[3/4] 补本地证据', flush=True)
    local = pick_local(gather_local(args.days), planned['players'], args.local_limit)
    print(f'  本地相关 {len(local)} 条', flush=True)
    print('[4/4] 写对比报告', flush=True)
    data = insight(args.topic, planned, web, local)
    slug = args.slug or re.sub(r'\W+', '-', args.topic)[:40].strip('-')
    print('完成 →', render(args.topic, planned, web, local, data, slug), flush=True)


if __name__ == '__main__':
    main()
