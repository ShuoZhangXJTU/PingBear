#!/usr/bin/env python3
"""每日 GitHub 热门：抓日榜里 star 暴涨的项目，用一句中文讲清是啥。

  python3 scripts/github_trending.py            # 今天
  python3 scripts/github_trending.py --date 2026-10-29 --limit 8

产物：日报/<日期>-GitHub.md，并在今日简报里单独一节。
"""
import argparse
import datetime as dt
import html as html_mod
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import knowledge
import research

ROOT = research.ROOT
OUT = ROOT / '日报'
TZ = ZoneInfo('Asia/Shanghai')
TREND = 'https://github.com/trending?since=daily'


def clean(text):
    return re.sub(r'\s+', ' ', html_mod.unescape(re.sub(r'<[^>]+>', '', text or ''))).strip()


def fetch(limit=12):
    page = knowledge.http_get(TREND, timeout=45)
    rows = []
    for block in page.split('<article class="Box-row"')[1:]:
        name = re.search(r'<h2[^>]*>.*?<a[^>]*href="/([^"/]+/[^"]+)"', block, re.S)
        if not name:
            continue
        repo = html_mod.unescape(name.group(1)).strip()
        desc = re.search(r'<p class="col-9[^"]*">(.*?)</p>', block, re.S)
        today = re.search(r'([\d,]+)\s*stars today', block)
        total = re.search(r'href="/' + re.escape(repo) + r'/stargazers"[^>]*>.*?([\d,]+)</a>', block, re.S)
        lang = re.search(r'<span itemprop="programmingLanguage">(.*?)</span>', block)
        rows.append({'repo': repo, 'description': clean(desc.group(1)) if desc else '',
            'today': int((today.group(1) if today else '0').replace(',', '')),
            'stars': int((total.group(1) if total else '0').replace(',', '')),
            'language': clean(lang.group(1)) if lang else '',
            'url': 'https://github.com/' + repo})
        if len(rows) >= limit:
            break
    return rows


def explain(rows):
    prompt = '''下面是一些今天在 GitHub 上 star 增长很快的项目。请给每个项目写一句中文说明：
- 30–60 字，像给同事随口介绍：这是什么东西、能拿来干嘛；
- 不许用「赋能/生态/范式」这类空话，不要吹，不要编造描述里没有的功能；
- 按给定 repo 原样返回顺序，只输出 JSON。'''
    schema = {'type': 'object', 'properties': {'items': {'type': 'array', 'items': {
        'type': 'object', 'properties': {'repo': {'type': 'string'}, 'summary': {'type': 'string'}},
        'required': ['repo', 'summary'], 'additionalProperties': False}}},
        'required': ['items'], 'additionalProperties': False}
    data = knowledge.codex_json(prompt, {'repos': rows}, schema,
        ROOT / '.research/github/answer.json', ROOT / '.research/github/logs/summarize.log')
    by_repo = {item['repo']: item.get('summary', '') for item in data.get('items') or []}
    for row in rows:
        row['summary'] = by_repo.get(row['repo']) or row['description'] or '（项目没有写简介）'
    return rows


def render(date, rows):
    lines = [f'---\ndate: {date}\ntype: github-digest\nsource: github\n---\n\n',
        f'# {date} GitHub 热门\n\n', f'源：GitHub Trending 日榜（按今日新增 star），共 {len(rows)} 个。\n\n']
    for n, row in enumerate(rows, 1):
        lines += [f'## G{n}. [{row["repo"]}]({row["url"]})\n\n',
            f'{row["summary"]}\n\n',
            f'今日 +{row["today"]} star · 总 {row["stars"]} star'
            + (f' · {row["language"]}' if row['language'] else '') + '\n\n']
    path = OUT / f'{date}-GitHub.md'
    research.replace(path, ''.join(lines))
    research.replace(ROOT / '.research/github/digests' / f'{date}.json',
        {'date': date, 'source': 'github', 'repos': rows})
    return path


def process(date=None, limit=8):
    date = date or dt.datetime.now(TZ).date().isoformat()
    rows = fetch(limit)
    if not rows:
        raise RuntimeError('GitHub Trending 页面没解析出条目')
    rows = explain(rows)
    return render(date, rows), len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--date')
    parser.add_argument('--limit', type=int, default=8)
    args = parser.parse_args()
    path, count = process(args.date, args.limit)
    print(f'GitHub 热门：{count} 个 -> {path}')


if __name__ == '__main__':
    main()
