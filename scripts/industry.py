#!/usr/bin/env python3
"""业界洞察：联网找竞品，看它们具体做了什么、差异在哪。

流程（按沙漏分阶段，标准每次只加载当前卡）：
  定题 → 广搜候选 → 按目标筛选 → 聚焦核验 → 综合关系与体验 → 展开决策。
  所有候选与阶段产物保存在 .research/industry/runs/，原始候选不删除。

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


def insight_standards(stage=None):
    """Introspection helper; live generation injects this once via the shared bridge."""
    import rubrics_bridge
    return rubrics_bridge.context('industry_insight', stage=stage)


def plan(topic, seed=''):
    import industry_workflow
    return industry_workflow.plan(topic, seed)


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
    # Wide collection keeps every discovered candidate; page reading happens after selection.
    hits, seen = [], set()
    for query in queries:
        found = web_search(query)
        print(f'  搜索「{query}」→ {len(found)} 条', flush=True)
        for item in found:
            key = item['url'].split('#', 1)[0]
            if key in seen:
                continue
            seen.add(key)
            hits.append(item)
    return [{'id': f'web-{n}', 'kind': 'web', 'title': item['title'], 'url': item['url'],
             'company': '', 'date': '', 'summary': item['snippet'], 'text': '',
             'query': item['query'], 'read_level': 'search_snippet_only'}
            for n, item in enumerate(hits, 1)]


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


def insight(topic, planned, web, local, deep_limit=6, fetcher=None, force=None):
    import industry_workflow
    return industry_workflow.insight(topic, planned, web, local, deep_limit, fetcher, force=force)


def render(topic, planned, web, local, data, slug):
    workflow = data.get('_workflow') or {}
    if not workflow.get('graph'):
        return _render_snapshot(topic, planned, web, local, data, slug)
    from industry_graph import Graph, StaleInput
    graph = Graph(workflow['run_dir'])
    with graph.locked() as state:
        expected = workflow['graph']['deliver']['revision']
        if graph.status_in(state, 'deliver') != 'fresh' or state['nodes']['deliver']['head'] != expected:
            raise StaleInput('Report is outdated; resume this graph before publishing')
        return _render_snapshot(topic, planned, web, local, data, slug)


def _render_snapshot(topic, planned, web, local, data, slug):
    date = dt.datetime.now(TZ).date().isoformat()
    by_id = {item['id']: item for item in web + local}
    graph_meta = data.get('_workflow') or {}
    graph_stamp = ''
    if graph_meta.get('graph'):
        graph_stamp = f'run_graph: {graph_meta["run_dir"]}/graph.json\nartifact_revision: {graph_meta["graph"]["deliver"]["revision"]}\n'
    lines = [f'---\ndate: {date}\ntype: industry-insight\ntopic: "{topic}"\n{graph_stamp}---', '',
        f'# 业界洞察：{topic}', '',
        f'联网检索候选 {len(web)} 条 + 本机博客/论文 {len(local)} 条；正文读取范围见筛选与核验记录。', '',
        '## 一句话结论与关系变化', '', data['answer'], '',
        '## 核心体验变化、技术支撑与取舍', '']
    lines += [f'- {item}' for item in data['differences']]
    lines += ['', '## 竞品清单（对比底稿）', '',
        '| 竞品 | 公司 | 形态 | 具体做什么 | 交互方式 | 场景 | 成熟度 |', '|---|---|---|---|---|---|---|']
    for row in data['competitors']:
        lines.append(f'| {row["name"]} | {row["company"]} | {row["form"]} | {row["what"]} | '
            f'{row["interaction"]} | {row["scenario"]} | {row["maturity"]} |')
    lines += ['', '## 场景拆解', '']
    for row in data['scenarios']:
        lines += [f'### {row["scenario"]}', '', f'- 谁在做：{row["who"]}', f'- 做法差异：{row["difference"]}', '']
    lines += ['## 怎么变现', '', '| 模式 | 代表 | 谁付钱 | 证据 |', '|---|---|---|---|']
    for row in data['business_models']:
        lines.append(f'| {row["model"]} | {row["examples"]} | {row["who_pays"]} | '
            + '、'.join(row['evidence_ids']) + ' |')
    lines += ['', '## 可商用变现的切入点（待验证）', '']
    for row in data['commercial_bets']:
        lines += [f'### {row["idea"]}', '', f'- 目标客户：{row["customer"]}', f'- 为什么现在能做：{row["why_now"]}',
            f'- 怎么收钱：{row["revenue"]}', f'- 壁垒：{row["moat"]}', f'- 风险：{row["risk"]}', '']
    lines += ['## 空白与机会', '']
    lines += [f'- **空白**：{item}' for item in data['gaps']]
    lines += [f'- **机会**：{item}' for item in data['opportunities']]
    workflow = data.get('_workflow')
    if workflow:
        lines += ['', '## 本轮收口与待补证据', '',
                  f'候选证据 {workflow["candidate_count"]} 条；深核 {workflow["deep_count"]} 条。未选条目保留，不表示被证伪。',
                  '此处是材料核验，不表示实际运行产品测试。', '']
        for row in workflow['selection']['selected']:
            lines.append(f'- 深核 `{row["id"]}`：{row["reason"]}')
        for row in workflow['selection']['deferred']:
            lines.append(f'- 暂缓 `{row["id"]}`：{row["reason"]}')
        lines += ['', '### 仍未解决', '']
        lines += [f'- {gap}' for gap in workflow['verification']['gaps']]
        lines += [f'- {claim["claim"]}：{claim["limitations"]}' for claim in workflow['verification']['claims'] if claim['status'] == 'unresolved']
        lines += [f'- {item}' for item in workflow['synthesis']['unresolved']]
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


def collect_candidates(planned, settings):
    print('[2/6] 广搜候选（保留原始池）', flush=True)
    if settings.get('web_file'):
        web = json.loads(Path(settings['web_file']).read_text(encoding='utf-8'))
        for item in web:
            item.setdefault('kind', 'web'); item.setdefault('text', '')
    else:
        web = gather_web(planned['web_queries'], settings['pages'])
    local = pick_local(gather_local(settings['days']), planned['players'], settings['local_limit'])
    return web, local


def main():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('topic', nargs='?')
    parser.add_argument('--resume', type=Path, help='复用已有依赖图，仅重建失效环节')
    parser.add_argument('--force', choices=['scope','scan','select','selected_evidence','verify','synthesize','deliver'], help='显式重做一个节点；失败保留旧版本')
    parser.add_argument('--days', type=int, default=120)
    parser.add_argument('--slug', default='')
    parser.add_argument('--pages', type=int, default=8)
    parser.add_argument('--deep-limit', type=int, default=6, help='本轮深核的证据条目上限；不是行业结论的样本分母')
    parser.add_argument('--local-limit', type=int, default=40)
    parser.add_argument('--seed', default='', help='点名要覆盖的竞品/厂商，逗号分隔，如「小艺看世界,Gemini Live」')
    parser.add_argument('--web-file', help='用已经搜好并落盘的网页证据 JSON（[{id,title,url,company,summary}]）')
    args = parser.parse_args()
    if args.resume:
        import industry_workflow
        from industry_graph import Graph
        graph = Graph(args.resume)
        settings = graph.load()['meta'].get('acquisition')
        def acquire(planned):
            return collect_candidates(planned, settings)
        planned, web, local, data = industry_workflow.resume(args.resume,
            acquire=acquire if settings else None,
            fetcher=None if settings and settings.get('web_file') else page_text,
            force=args.force)
        topic = graph.read('request')['topic']
        slug = args.slug or graph.load()['meta'].get('slug') or re.sub(r'\W+', '-', topic)[:40].strip('-')
        print('完成 →', render(topic, planned, web, local, data, slug), flush=True)
        return
    if not args.topic:
        parser.error('topic or --resume is required')
    if args.pages < 1 or args.deep_limit < 1:
        parser.error('--pages and --deep-limit must be positive')
    STATE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    print('[1–2/6] 定题与广搜计划', flush=True)
    planned = plan(args.topic, args.seed)
    if args.seed:
        planned['players'] = list(dict.fromkeys([p.strip() for p in args.seed.split(',') if p.strip()] + planned['players']))
    print('  玩家：' + '、'.join(planned['players']), flush=True)
    print('  检索：' + '；'.join(planned['web_queries']), flush=True)
    from industry_graph import Graph
    settings = {'days': args.days, 'pages': args.pages, 'local_limit': args.local_limit,
                'web_file': str(Path(args.web_file).resolve()) if args.web_file else None}
    Graph(planned['_run_dir']).set_meta(acquisition=settings, slug=args.slug)
    web, local = collect_candidates(planned, settings)
    print('[3–6/6] 筛选、深核、综合与决策', flush=True)
    data = insight(args.topic, planned, web, local, min(args.pages, args.deep_limit),
                   fetcher=None if args.web_file else page_text, force=args.force)
    slug = args.slug or re.sub(r'\W+', '-', args.topic)[:40].strip('-')
    print('完成 →', render(args.topic, planned, web, local, data, slug), flush=True)


if __name__ == '__main__':
    main()
