#!/usr/bin/env python3
"""公司博客/官方发布源：Anthropic、Google Research、OpenAI、Microsoft Research、ByteDance Seed。

首选 RSS（标题/日期/摘要齐全），没有 RSS 的抓列表页 + 文章页，SPA 站点用本机 Chrome 渲染。
新文章按早报同款写成一句中文 + tags + 链接，可归档、可提问，并进入知识体系。
"""
import argparse
import datetime as dt
import hashlib
import html as html_mod
import json
import os
import re
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo

import knowledge
import research
import xhs

ROOT = research.ROOT
STATE = ROOT / '.research/blogs'
DIGESTS = STATE / 'digests'
SEEN = STATE / 'seen.json'
TOOL_HOME = Path.home() / '.local/share/research-xhs'
FETCH = TOOL_HOME / 'xhsfetch'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
TZ = ZoneInfo('Asia/Shanghai')
LOCAL_PROXY = os.environ.get('RESEARCH_PROXY', 'http://127.0.0.1:7890')
ARXIV_LINK = re.compile(r'(?:arxiv\.org/(?:abs|pdf)/|huggingface\.co/papers/)(\d{4}\.\d{4,5})', re.I)
SOURCES = [
    {'id': 'openai', 'name': 'OpenAI', 'feed': 'https://openai.com/news/rss.xml'},
    {'id': 'anthropic-research', 'name': 'Anthropic Research',
     'listing': 'https://www.anthropic.com/research', 'pattern': r'/research/[A-Za-z0-9\-]+',
     'base': 'https://www.anthropic.com'},
    {'id': 'anthropic-eng', 'name': 'Anthropic Engineering',
     'listing': 'https://www.anthropic.com/engineering', 'pattern': r'/engineering/[A-Za-z0-9\-]+',
     'base': 'https://www.anthropic.com'},
    {'id': 'google', 'name': 'Google Research', 'feed': 'https://research.google/blog/rss/'},
    {'id': 'msr', 'name': 'Microsoft Research', 'feed': 'https://www.microsoft.com/en-us/research/feed/'},
    {'id': 'seed', 'name': 'ByteDance Seed', 'listing': 'https://seed.bytedance.com/en/research',
     'pattern': r'/en/blog/[a-z0-9\-]+', 'base': 'https://seed.bytedance.com', 'render': True},
]


def http_get(url, timeout=45):
    try:
        return knowledge.http_get(url, timeout=timeout)
    except Exception:
        return ''


def render_page(url, base):
    base.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, XHS_BROWSER_BIN=CHROME, TZ='Asia/Shanghai')
    subprocess.run([str(FETCH), 'dom', url, str(base)], cwd=str(TOOL_HOME), env=env,
        text=True, errors='replace', capture_output=True, timeout=300)
    path = Path(str(base) + '.html')
    return path.read_text(encoding='utf-8', errors='replace') if path.exists() else ''


def get_html(url, render=False, cache=None):
    if render:
        return render_page(url, cache or (STATE / 'cache' / hashlib.sha1(url.encode()).hexdigest()))
    html = http_get(url)
    if len(html) > 2000 or not render:
        return html
    return render_page(url, cache or (STATE / 'cache' / hashlib.sha1(url.encode()).hexdigest()))


def text_of(html, limit=8000):
    return knowledge.plain_text(html, limit)


def meta(html, name):
    for pattern in [rf'(?is)<meta[^>]+(?:property|name)="{name}"[^>]+content="([^"]*)"',
                    rf'(?is)<meta[^>]+content="([^"]*)"[^>]+(?:property|name)="{name}"']:
        found = re.search(pattern, html)
        if found:
            return html_mod.unescape(found.group(1)).strip()
    return ''


def feed_items(source):
    xml = http_get(source['feed'])
    if not xml.strip().startswith('<?xml'):
        return []
    try:
        root = ET.fromstring(xml.encode('utf-8'))
    except ET.ParseError:
        return []
    ns = {'content': 'http://purl.org/rss/1.0/modules/content/', 'dc': 'http://purl.org/dc/elements/1.1/'}
    items = []
    for node in root.findall('.//item'):
        link = (node.findtext('link') or '').strip()
        title = html_mod.unescape((node.findtext('title') or '').strip())
        summary = node.findtext('description') or node.findtext('content:encoded', default='', namespaces=ns) or ''
        date = node.findtext('pubDate') or node.findtext('dc:date', default='', namespaces=ns) or ''
        if link and title:
            items.append({'url': link, 'title': title, 'text': text_of(summary, 6000), 'date': date.strip()})
    return items


def listing_items(source):
    """只解析列表页：拿到链接顺序和锚文本，正文等选中了再抓。"""
    html = get_html(source['listing'], render=source.get('render', False),
        cache=STATE / 'cache' / source['id'])
    if not html:
        return []
    items = []
    seen = set()
    for match in re.finditer(r'(?is)<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html):
        href, inner = match.group(1), match.group(2)
        path = urllib.parse.urlparse(href).path.rstrip('/')
        if not re.fullmatch(source['pattern'], path):
            continue
        # 列表页里的分类/标签/年份归档不是文章
        if re.search(r'/(label|page|category|team|tag|tags|author)/', path) or re.fullmatch(r'.*/\d{4}', path):
            continue
        url = urllib.parse.urljoin(source['base'], href.split('?')[0].rstrip('/'))
        if url in seen:
            continue
        seen.add(url)
        title = re.sub(r'\s+', ' ', html_mod.unescape(re.sub(r'(?is)<[^>]+>', ' ', inner))).strip()
        items.append({'url': url, 'title': title[:160], 'text': '', 'date': ''})
        if len(items) >= 25:
            break
    return items


def enrich(item, source):
    """选中后再抓文章页，补标题、日期和正文。"""
    if item.get('text') and len(item['text']) > 400:
        return item
    page = get_html(item['url'], render=source.get('render', False),
        cache=STATE / 'cache' / hashlib.sha1(item['url'].encode()).hexdigest())
    if not page:
        return item
    title = meta(page, 'og:title') or meta(page, 'twitter:title')
    if not title:
        match = re.search(r'(?is)<title[^>]*>(.*?)</title>', page)
        title = re.split(r'\s*[\\|–-]\s*', html_mod.unescape(match.group(1)).strip())[0] if match else item['title']
    item['title'] = (title or item['title']).strip()
    item['date'] = meta(page, 'article:published_time') or item.get('date', '')
    item['text'] = (meta(page, 'og:description') + '\n' + text_of(page, 8000)).strip()
    return item


def summarize(items, source):
    schema = {'type': 'object', 'properties': {'papers': {'type': 'array', 'items': {
        'type': 'object', 'properties': {
            'index': {'type': 'integer'}, 'title': {'type': 'string'}, 'summary': {'type': 'string'},
            'tags': {'type': 'array', 'items': {'type': 'string', 'enum': list(research.TAGS)},
                'minItems': 2, 'maxItems': 5}},
        'required': ['index', 'title', 'summary', 'tags'], 'additionalProperties': False}}},
        'required': ['papers'], 'additionalProperties': False}
    prompt = '''你在帮一位 NLP 博士跟踪 AI 公司的官方发布与研究博客。用户是大厂 AI Lab 的 NLP 博士，关注 RSI、agent harness、后训练、评测。
下面是同一家公司的几条新内容，请逐条给简报：index 与输入一一对应，title 用原文标题，summary 一句 35–90 字中文说清“发了什么、有什么用”，避免翻译腔和概念堆叠。
这条只用来快速筛选，必须用讲给小学生听的方式：不用专业术语，用日常词、短句，一眼能看懂在干啥。
只依据给定材料，材料里没有的数字和结论不要写；如果材料太短看不出技术细节，summary 就直说它是哪方面的发布或讨论。tags 从固定词表原样挑 2–5 个：'''
    prompt += '、'.join(research.TAGS) + '。只输出 JSON，不要解释文字。'
    payload = {'source': source['name'], 'items': [
        {'index': index, 'title': item['title'], 'url': item['url'], 'text': item['text'][:6000]}
        for index, item in enumerate(items, 1)]}
    data = knowledge.codex_json(prompt, payload, schema, STATE / 'reviews' / f'{source["id"]}.json',
        STATE / 'logs' / f'{source["id"]}.log')
    return {int(item['index']): item for item in data['papers']}


def collect(date, per_source=2, force=False):
    state = research.load(SEEN) if SEEN.exists() else {'seen': []}
    seen = set(state.get('seen') or [])
    records, failures = [], []
    for source in SOURCES:
        try:
            items = feed_items(source) if source.get('feed') else listing_items(source)
        except Exception as error:
            failures.append(f'{source["id"]}: {type(error).__name__} {error}')
            continue
        fresh = [item for item in items if item['url'] not in seen]
        chosen = fresh[:per_source]
        seen.update(item['url'] for item in items)
        if not chosen:
            print(f'{source["name"]}: 没有新内容（列表 {len(items)} 条）', flush=True)
            continue
        chosen = [enrich(item, source) for item in chosen]
        try:
            reviews = summarize(chosen, source)
        except Exception as error:
            failures.append(f'{source["id"]} 简介失败: {type(error).__name__} {error}')
            continue
        for index, item in enumerate(chosen, 1):
            review = reviews.get(index, {})
            found = ARXIV_LINK.search(item['url'] + ' ' + item['text'])
            arxiv = found.group(1) if found else ''
            ident = arxiv or 'blog-' + hashlib.sha1(item['url'].encode()).hexdigest()[:12]
            records.append({'id': ident, 'source': 'blog', 'origin': source['id'], 'origin_name': source['name'],
                'title': review.get('title') or item['title'], 'summary': review.get('summary', ''),
                'tags': [t for t in review.get('tags', []) if t in research.TAGS][:5],
                'url': f'https://arxiv.org/abs/{arxiv}' if arxiv else item['url'],
                'pdf': f'https://arxiv.org/pdf/{arxiv}' if arxiv else '',
                'origin_url': item['url'], 'arxiv': arxiv, 'published': item.get('date', ''),
                'images': [], 'ocr': item['text'][:8000]})
        print(f'{source["name"]}: 处理 {len(chosen)} 条 / 列表 {len(items)} 条', flush=True)
    research.replace(SEEN, {'seen': sorted(seen), 'updated_at': dt.datetime.now(TZ).isoformat(),
        'last_error': failures[-1] if failures else ''})
    return records, failures


def card(record, date):
    tags = ' '.join('#' + t for t in record.get('tags', []))
    links = []
    if record.get('arxiv'):
        links.append(f"[论文]({record['url']})")
        links.append(f"[PDF]({record['pdf']})")
    links.append(f"[原文]({record['origin_url']})")
    links.append(f"[归档](obsidian://research-archive?date={date}&id={record['id']})")
    origin = f"来源：{record.get('origin_name','')}" + (f" · {record['published'][:16]}" if record.get('published') else '')
    return f"{record['summary']}\n\n{tags}\n\n" + ' · '.join(links) + f"\n\n<sub>{origin}</sub>\n"


def render(date, records):
    path = ROOT / '日报' / f'{date}-博客.md'
    lines = [f'---\ndate: {date}\ntype: blog-digest\nsource: company-blogs\n---\n\n',
        f'# {date} 官方博客与研究发布\n\n', f'共 {len(records)} 条\n\n']
    for number, record in enumerate(records, 1):
        lines.append(f'## B{number}. [{record["title"]}]({record["url"]})\n\n')
        lines.append(card(record, date) + '\n')
    if not records:
        lines.append('这次没有新发布。\n')
    research.replace(path, ''.join(lines))
    existing = {}
    digest_path = DIGESTS / f'{date}.json'
    if digest_path.exists():
        for record in research.load(digest_path).get('papers') or []:
            existing[record['id']] = record
    for record in records:
        existing.setdefault(record['id'], dict(record, date=date))
    research.replace(digest_path, {'date': date, 'source': 'company-blogs', 'style_version': 1,
        'papers': [dict(record, number=number) for number, record in enumerate(existing.values(), 1)]})
    return path


def process(date, per_source=2, force=False):
    records, failures = collect(date, per_source=per_source, force=force)
    path = render(date, records)
    if failures:
        print('失败：' + '；'.join(failures[:3]), flush=True)
    print(f'官方博客：本次 {len(records)} 条 -> {path}', flush=True)
    return path, len(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['process'], nargs='?', default='process')
    parser.add_argument('--date', type=research.valid_date)
    parser.add_argument('--per-source', type=int, default=2)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    date = args.date or dt.datetime.now(TZ).date().isoformat()
    STATE.mkdir(parents=True, exist_ok=True)
    process(date, per_source=args.per_source, force=args.force)


if __name__ == '__main__':
    main()
