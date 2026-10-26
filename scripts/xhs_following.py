#!/usr/bin/env python3
"""从小红书「关注」流和「收藏」页每天找 AI 论文相关笔记，抓下来做成中文简报。

你自己在平台上关注谁、收藏什么就行，这里只做三件事：
  1) 用已登录的浏览器打开「关注」流 / 我的收藏页，取当天这批笔记（标题 + 作者 + xsecToken）；
  2) 用关键词先筛一遍，只留下看着像论文/研究内容的（paper、arxiv、agent、RL、评测…）；
  3) 新的、相关的交给 tabris 那条同样的流水线：逐张截图 OCR → 认出论文 → 中文简介。

产物：日报/<日期>-关注.md、日报/<日期>-收藏.md（两个独立分栏）。
清单在 .research/xhs/following|favorites/<日期>.json，处理过的笔记记在各自的 seen 文件。

  python3 scripts/xhs_following.py                     # 关注 + 收藏
  python3 scripts/xhs_following.py --source favorites  # 只抓收藏
  python3 scripts/xhs_following.py --dry-run           # 只列候选，不抓正文
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import research
import xhs

ROOT = research.ROOT
STATE = ROOT / '.research/xhs'
OUT = ROOT / '日报'
TZ = ZoneInfo('Asia/Shanghai')
ME = STATE / 'me.json'
FOLLOW_URL = 'https://www.xiaohongshu.com/explore?channel_id=homefeed.follow'

SOURCES = {
    'following': {'label': '关注流', 'suffix': '关注', 'prefix': 'F', 'url': FOLLOW_URL,
        'seen': STATE / 'following-seen.json', 'digests': STATE / 'following'},
    'favorites': {'label': '收藏', 'suffix': '收藏', 'prefix': 'C', 'url': None,
        'seen': STATE / 'favorites-seen.json', 'digests': STATE / 'favorites'},
}
STRONG = ['paper', '论文', 'arxiv', 'llm', '大模型', 'agent', 'agentic', 'harness', 'rsi',
    'reinforcement learning', '强化学习', '后训练', '蒸馏', 'distill', 'moe', 'diffusion', 'transformer',
    'benchmark', '评测', '基准', '多模态', 'world model', 'worldmodel', '视频生成', 'reasoning', '推理',
    '数据合成', 'sft', 'dpo', 'grpo', 'embedding', 'rag', '检索', 'self-improv', '自进化', '自我改进']
WEAK = ['推荐', '合集', 'blog', '研究', '模型', '训练', '视觉', '生成', 'bench', 'read']
BLOCK = ['抽奖', '招聘', '带货', '优惠券', '内推', 'join us', '面试', '校招', '社招']


def fetch_dom(url, out_base, timeout=180):
    """用已登录的浏览器把页面 DOM 落盘（内嵌数据里带 xsecToken）。"""
    env = dict(os.environ, XHS_BROWSER_BIN=xhs.CHROME, TZ='Asia/Shanghai')
    started = time.time()
    process = subprocess.Popen([str(xhs.FETCH), 'dom', url, str(out_base)],
        cwd=str(xhs.TOOL_HOME), env=env, text=True, errors='replace',
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        out, err = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        out, err = process.communicate()
        print('  浏览器关闭超时，先看页面是否已经落盘', flush=True)
    path = Path(str(out_base) + '.html')
    if path.exists() and path.stat().st_size > 50000 and path.stat().st_mtime >= started - 5:
        return path
    if process.returncode or not path.exists():
        raise RuntimeError((err or out or '页面抓取失败').strip()[-300:])
    return path


def my_user_id(html_path):
    if ME.exists():
        stored = research.load(ME).get('user_id')
        if stored:
            return stored
    state = xhs.state_from_html(html_path)
    info = xhs.unwrap((state.get('user') or {}).get('userInfo')) or {}
    ident = info.get('userId')
    if ident:
        research.replace(ME, {'user_id': ident, 'nickname': info.get('nickname'),
            'updated_at': dt.datetime.now(TZ).isoformat()})
    return ident


def feed_notes(html_path, source):
    state = xhs.state_from_html(html_path)
    if source == 'following':
        feeds = xhs.find_key(state, 'feeds') or []
    else:
        pages = ((state.get('user') or {}).get('notes') or [])
        feeds = [item for page in pages if isinstance(page, list) for item in page]
    notes = []
    for item in feeds if isinstance(feeds, list) else []:
        card = (item or {}).get('noteCard') or {}
        ident = item.get('id') or card.get('noteId')
        if not ident:
            continue
        notes.append({'id': ident, 'xsec_token': item.get('xsecToken') or '',
            'title': (card.get('displayTitle') or '').strip(),
            'desc': (card.get('desc') or '').strip(),
            'author': ((card.get('user') or {}).get('nickName') or '').strip(),
            'type': card.get('type') or ''})
    return notes


def score(note):
    text = (note['title'] + ' ' + note['desc']).lower()
    if any(word in text for word in BLOCK):
        return 0
    strong = sum(1 for word in STRONG if word in text)
    weak = sum(1 for word in WEAK if word in text)
    return strong * 2 + weak


def render(source, date, records):
    spec = SOURCES[source]
    for record in records:
        record['date'] = date
    path = OUT / f'{date}-{spec["suffix"]}.md'
    lines = [f'---\ndate: {date}\ntype: xhs-digest\nsource: xiaohongshu-{source}\n---\n\n',
        f'# {date} 小红书 · {spec["label"]} · AI 论文\n\n', f'共 {len(records)} 条\n\n']
    for number, record in enumerate(records, 1):
        lines.append(f'## {spec["prefix"]}{number}. [{record["title"]}]({record["url"]})\n\n')
        lines.append(xhs.card(record) + '\n')
        lines.append(f'来源：{record.get("author", "")} · {record.get("note_title", "")}\n\n')
    if not records:
        lines.append(f'{spec["label"]}里今天没有识别到新的 AI 论文内容。\n')
    research.replace(path, ''.join(lines))
    research.replace(spec['digests'] / f'{date}.json', {'date': date, 'source': 'xiaohongshu-' + source,
        'style_version': 2, 'papers': [dict(record, number=n) for n, record in enumerate(records, 1)]})
    return path


def run_source(source, date, limit, dry_run, html=None):
    spec = SOURCES[source]
    if html:
        page_path = Path(html)
    elif source == 'following':
        page_path = fetch_dom(FOLLOW_URL, STATE / 'following')
    else:
        uid = my_user_id(STATE / 'following.html')
        url = f'https://www.xiaohongshu.com/user/profile/{uid}?tab=fav&subTab=note'
        page_path = fetch_dom(url, STATE / 'favorites')
    if source == 'following':
        my_user_id(page_path)
    notes = feed_notes(page_path, source)
    seen_path = spec['seen']
    state = research.load(seen_path) if seen_path.exists() else {'seen': []}
    seen = set(state.get('seen') or [])
    ranked = sorted((n for n in notes if n['id'] not in seen), key=score, reverse=True)
    candidates = [n for n in ranked if score(n) >= 2][:limit]
    print(f'{spec["label"]} {len(notes)} 条，未读 {len(ranked)} 条，其中 AI 相关候选 {len(candidates)} 条', flush=True)
    for note in candidates:
        print(f'  [{score(note)}] {note["author"]}：{note["title"][:50]}', flush=True)
    if dry_run:
        return None
    partial = spec['digests'] / f'{date}.json'
    records = list(research.load(partial).get('papers') or []) if partial.exists() else []
    for note in candidates:
        try:
            picked = xhs.process_note({'id': note['id'], 'title': note['title'],
                'xsec_token': note['xsec_token'], 'type': note['type'], 'time': 0},
                {'nickname': note['author'] or spec['label'], 'xsec_token': note['xsec_token']})
        except Exception as error:
            print(f'  处理失败 {note["id"]}: {type(error).__name__} {error}', flush=True)
            continue
        for record in picked:
            record['author'] = note['author'] or spec['label']
            records.append(record)
        seen.add(note['id'])
        state['seen'] = sorted(seen)
        state['updated_at'] = dt.datetime.now(TZ).isoformat()
        research.replace(seen_path, state)
        research.replace(partial, {'date': date, 'source': 'xiaohongshu-' + source,
            'style_version': 2, 'papers': [dict(record, number=n) for n, record in enumerate(records, 1)]})
        print(f'  已处理 {note["id"]}（{note["title"][:24]}）→ {len(picked)} 条', flush=True)
    path = render(source, date, records)
    print(f'{spec["label"]}：{len(records)} 条 -> {path}', flush=True)
    if records:
        try:
            import notify
            day = dt.date.fromisoformat(date)
            notify.send(f'{spec["label"]}更新 · {day.month}月{day.day}日',
                f'{spec["label"]}里有 {len(candidates)} 条 AI 相关内容，认出 {len(records)} 条论文。\n\n'
                f'打开 日报/{date}-{spec["suffix"]}.md 查看。')
        except Exception as error:
            print('推送失败:', type(error).__name__, error, flush=True)
    return path


def run(date=None, limit=8, dry_run=False, html=None, source='both'):
    date = date or dt.datetime.now(TZ).date().isoformat()
    STATE.mkdir(parents=True, exist_ok=True)
    for name in (['following', 'favorites'] if source == 'both' else [source]):
        SOURCES[name]['digests'].mkdir(parents=True, exist_ok=True)
        run_source(name, date, limit, dry_run, html if source != 'both' else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--date')
    parser.add_argument('--limit', type=int, default=8)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--html', help='复用已抓好的页面快照（单来源时有效）')
    parser.add_argument('--source', choices=['both', 'following', 'favorites'], default='both')
    args = parser.parse_args()
    run(args.date, args.limit, args.dry_run, args.html, args.source)


if __name__ == '__main__':
    main()
