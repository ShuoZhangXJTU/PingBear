#!/usr/bin/env python3
"""三个月冷启动补跑。

阶段一 hf：按天抓 HF Daily Papers，挑出和你方向相关的 top-k 用模型写中文简介，
           其余论文以「标题 + 标签 + 链接 + 归档」的轻量条目留在当天日报里，保证历史完整可检索。
阶段二 blog：把 6 个官方源三个月内的文章按发布日期补成历史日报。
阶段三 xhs：把 tabris 三个月内的历史笔记补进来（需要滚动加载，见 --scroll）。

可中断、可续跑：进度记在 .research/backfill.json，重复运行只会补没跑过的部分。
"""
import argparse
import datetime as dt
import email.utils
import json
import re
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import research

ROOT = research.ROOT
STATE = ROOT / '.research/backfill.json'
DAILY = ROOT / '日报'
TZ = ZoneInfo('Asia/Shanghai')


def state():
    return research.load(STATE) if STATE.exists() else {'hf': [], 'blog': [], 'xhs': [], 'started': None}


def save_state(value):
    research.replace(STATE, value)


def daterange(start, end):
    day = start
    while day <= end:
        yield day.isoformat()
        day += dt.timedelta(days=1)


def tags_from_candidate(candidate):
    tags = []
    for topic, terms in (candidate.get('keyword_matches') or {}).items():
        if terms and topic in research.TAGS:
            tags.append(topic)
    return (tags or ['其他'])[:5]


def backfill_day(date, per_day=3, force=False, full=False):
    """抓一天的 HF，挑 top-k 让模型写简介，其余写成轻量条目。"""
    digest = ROOT / '.research/digests' / f'{date}.json'
    if digest.exists() and not force:
        data = research.load(digest)
        if not data.get('backfill'):
            raise RuntimeError('SKIP 已有正式日报')
    research.collect(SimpleNamespace(date=date, input=None, refresh=True), ROOT)
    papers = research.load(ROOT / '.research/candidates' / f'{date}.json')['papers']
    if not papers:
        return 0, 0
    ranked = sorted(papers, key=lambda p: -p.get('score', 0))
    # full=True：这一天全部论文都写中文简介（历史补跑补全用）
    chosen = ranked if full else [p for p in ranked if p.get('score', 0) > 0][:per_day]
    summarized = {}
    import morning
    if chosen:
        if full:
            # 分批调用（每批 12 篇），避免单次 prompt 过大
            for start in range(0, len(chosen), 12):
                batch = chosen[start:start + 12]
                review_path = morning.summarize(batch, date, tolerant=True)
                for paper in research.load(review_path)['papers']:
                    summarized[paper['id']] = paper
        else:
            review_path = morning.summarize(chosen, date)
            for paper in research.load(review_path)['papers']:
                summarized[paper['id']] = paper
    entries, number = [], 0
    for paper in ranked:
        number += 1
        review = summarized.get(paper['id'])
        if review:
            entries.append(dict(paper, number=number, summary=review['summary'], tags=review['tags'],
                title_zh=review.get('title_zh', ''), highlight=True, lite=False))
        else:
            entries.append(dict(paper, number=number, summary='', highlight=False, lite=True,
                tags=tags_from_candidate(paper)))
    lines = [f"---\ndate: {date}\ntype: digest\nbackfill: true\n---\n\n# {date} 科研速读（补跑）\n\n",
        f'共 {len(entries)} 篇 · 其中 {len(summarized)} 篇写了中文简介，其余为轻量条目（标题 + 标签，归档后可深读）\n\n']
    for entry in entries:
        if entry['lite']:
            tagline = ' '.join('#' + tag for tag in entry['tags'])
            lines.append(f"- [{entry['title']}]({entry['url']}) · {tagline} · "
                f"[归档](obsidian://research-archive?date={date}&id={entry['id']})\n")
        else:
            lines.append(f"## {entry['number']}. [{entry['title']}]({entry['url']})\n\n")
            lines.append(research.card(entry))
            lines.append(f"\n[归档](obsidian://research-archive?date={date}&id={entry['id']})\n\n")
    research.replace(DAILY / f'{date}.md', ''.join(lines))
    existing = ROOT / '.research/digests' / f'{date}.json'
    if existing.exists():
        research.backup(existing)
    research.replace(existing, {'date': date, 'style_version': research.STYLE_VERSION, 'backfill': True,
        'papers': entries})
    return len(summarized), len(entries)


def run_hf(start, end, per_day=3, days=None):
    progress = state()
    done = set(progress.get('hf') or [])
    progress.setdefault('started', dt.datetime.now(TZ).isoformat())
    save_state(progress)
    count = 0
    for date in daterange(start, end):
        if date in done:
            continue
        if days is not None and count >= days:
            break
        try:
            summarized, total = backfill_day(date, per_day=per_day)
            done.add(date)
            progress['hf'] = sorted(done)
            progress['last'] = f'{date}: {summarized}/{total}'
            save_state(progress)
            print(f'[hf] {date}: 简介 {summarized} 篇 / 共 {total} 篇', flush=True)
        except Exception as error:
            if 'SKIP' in str(error):
                done.add(date)
                progress['hf'] = sorted(done)
                save_state(progress)
                print(f'[hf] {date}: 已有正式日报，跳过', flush=True)
                count += 1
                continue
            print(f'[hf] {date} 失败: {type(error).__name__} {error}', flush=True)
            time.sleep(20)
        count += 1
    print(f'[hf] 完成 {len(done)} 天', flush=True)


def run_blog(start, end):
    import blogs
    progress = state()
    done = set(progress.get('blog') or [])
    for source in blogs.SOURCES:
        if source['id'] in done:
            continue
        try:
            items = blogs.feed_items(source) if source.get('feed') else blogs.listing_items(source)
        except Exception as error:
            print(f'[blog] {source["id"]} 列表失败: {type(error).__name__} {error}', flush=True)
            continue
        def published(item):
            raw = (item.get('date') or '').strip()
            if not raw:
                return None
            try:
                return email.utils.parsedate_to_datetime(raw).date()
            except (TypeError, ValueError):
                pass
            try:
                return dt.date.fromisoformat(raw[:10])
            except ValueError:
                return None
        picked = []
        for item in items:
            day = published(item)
            if day and start <= day <= end:
                picked.append(item)
        picked = picked[:60]
        by_day = {}
        for item in picked:
            day = published(item)
            by_day.setdefault(day.isoformat(), []).append(item)
        total = 0
        for day, day_items in sorted(by_day.items()):
            day_items = [blogs.enrich(item, source) for item in day_items[:10]]
            try:
                reviews = blogs.summarize(day_items, source)
            except Exception as error:
                print(f'[blog] {source["id"]} {day} 简介失败: {type(error).__name__}', flush=True)
                continue
            records = []
            for index, item in enumerate(day_items, 1):
                review = reviews.get(index, {})
                found = blogs.ARXIV_LINK.search(item['url'] + ' ' + item['text'])
                arxiv = found.group(1) if found else ''
                ident = arxiv or 'blog-' + __import__('hashlib').sha1(item['url'].encode()).hexdigest()[:12]
                records.append({'id': ident, 'source': 'blog', 'origin': source['id'],
                    'origin_name': source['name'], 'title': review.get('title') or item['title'],
                    'summary': review.get('summary', ''),
                    'tags': [t for t in review.get('tags', []) if t in research.TAGS][:5],
                    'url': f'https://arxiv.org/abs/{arxiv}' if arxiv else item['url'],
                    'pdf': f'https://arxiv.org/pdf/{arxiv}' if arxiv else '',
                    'origin_url': item['url'], 'arxiv': arxiv, 'published': item.get('date', ''),
                    'images': [], 'ocr': item['text'][:8000]})
            blogs.render(day, records)
            total += len(records)
            print(f'[blog] {source["name"]} {day}: {len(records)} 条', flush=True)
        done.add(source['id'])
        progress['blog'] = sorted(done)
        save_state(progress)
        print(f'[blog] {source["name"]} 完成，共 {total} 条', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--days', type=int, default=90)
    parser.add_argument('--start')
    parser.add_argument('--end')
    parser.add_argument('--per-day', type=int, default=3)
    parser.add_argument('--phase-batch', type=int, default=None, help='本次最多处理几天（分批跑用）')
    parser.add_argument('--only', choices=['hf', 'blog', 'all'], default='all')
    args = parser.parse_args()
    end = dt.date.fromisoformat(args.end) if args.end else dt.date.today() - dt.timedelta(days=1)
    start = dt.date.fromisoformat(args.start) if args.start else end - dt.timedelta(days=args.days - 1)
    print(f'补跑区间 {start} → {end}', flush=True)
    if args.only in ('hf', 'all'):
        run_hf(start, end, per_day=args.per_day, days=args.phase_batch)
    if args.only in ('blog', 'all'):
        run_blog(start, end)
    import catalog
    catalog.build()
    import knowledge
    knowledge.rebuild()


if __name__ == '__main__':
    main()
