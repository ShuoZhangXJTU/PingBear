#!/usr/bin/env python3
"""归档论文的收藏与「最近操作」索引。

star/unstar：给 论文/ 下的笔记打上 starred: true/false（frontmatter）
build：生成 索引/收藏.md（收藏夹）与 索引/最近.md（最近操作过的，按打开/修改时间）
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import research

ROOT = research.ROOT
NOTES = ROOT / '论文'
STAR_INDEX = ROOT / '索引/收藏.md'
RECENT_INDEX = ROOT / '索引/最近.md'


def notes():
    items = []
    for path in sorted(NOTES.rglob('*.md')):
        fields, _ = research.frontmatter(path)
        items.append({
            'path': path, 'rel': str(path.relative_to(ROOT).with_suffix('')),
            'title': fields.get('title') or path.stem, 'topic': path.parent.name,
            'arxiv': fields.get('arxiv') or fields.get('entry_id') or '',
            'starred': str(fields.get('starred', '')).lower() == 'true',
            'starred_at': fields.get('starred_at') or '',
            'selected_from': fields.get('selected_from') or '',
            'opened': fields.get('opened') or '',
            'status': fields.get('status') or 'to-read',
            'mtime': path.stat().st_mtime,
        })
    return items


def match(query):
    """按 arXiv 编号 / 文件名 / 标题片段找笔记。"""
    key = query.strip().lower()
    hits = [item for item in notes()
        if key == item['arxiv'].lower() or key in item['title'].lower() or key in item['path'].stem.lower()]
    return hits


def set_star(query, value=True):
    hits = match(query)
    if not hits:
        return None
    if len(hits) > 1:
        return hits
    item = hits[0]
    research.replace_path = None
    text = item['path'].read_text(encoding='utf-8')
    stamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
    if text.startswith('---\n'):
        head, rest = text.split('---\n', 2)[1], text.split('---\n', 2)[2]
        head = re.sub(r'(?m)^starred:.*\n?', '', head)
        head = re.sub(r'(?m)^starred_at:.*\n?', '', head)
        head += f'starred: {str(value).lower()}\n'
        if value:
            head += f'starred_at: "{stamp}"\n'
        research.replace(item['path'], f'---\n{head}---\n{rest}')
    return item


def build():
    items = notes()
    starred = [item for item in items if item['starred']]
    starred.sort(key=lambda item: item['starred_at'], reverse=True)
    lines = ['# 收藏夹', '', f'共 {len(starred)} 篇 · 更新 {dt.datetime.now():%Y-%m-%d %H:%M}', '',
        '在聊天里说「收藏 <论文名片段>」，或在 Obsidian 命令面板用「收藏当前论文」/「取消收藏」。', '']
    if not starred:
        lines.append('还没有收藏。')
    for item in starred:
        lines.append(f"- [[{item['rel']}|{item['title']}]]　<sub>{item['topic']}"
            + (f" · {item['starred_at'][:10]}" if item['starred_at'] else '') + '</sub>')
    research.replace(STAR_INDEX, '\n'.join(lines) + '\n')

    recent = sorted(items, key=lambda item: max(item['mtime'],
        dt.datetime.fromisoformat(item['opened']).timestamp() if re.fullmatch(r'\d{4}-\d{2}-\d{2}', item['opened'] or '') else 0),
        reverse=True)[:60]
    lines = ['# 最近操作过的归档', '', '按你最近**打开/修改**的时间排序（打开笔记会自动记录）。', '',
        f'共 {len(items)} 篇归档 · 更新 {dt.datetime.now():%Y-%m-%d %H:%M}', '']
    for item in recent:
        when = item['opened'] or dt.datetime.fromtimestamp(item['mtime']).strftime('%Y-%m-%d')
        mark = '⭐️ ' if item['starred'] else ''
        state = '已读' if item['status'] == 'read' else '未读'
        lines.append(f"- {mark}[[{item['rel']}|{item['title']}]]　<sub>{item['topic']} · {state} · {when}</sub>")
    research.replace(RECENT_INDEX, '\n'.join(lines) + '\n')
    print(f'收藏 {len(starred)} 篇 -> {STAR_INDEX}')
    print(f'最近操作 {len(recent)} 篇 -> {RECENT_INDEX}')
    return len(starred)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ['star', 'unstar']:
        cmd = sub.add_parser(name)
        cmd.add_argument('query')
    sub.add_parser('build')
    args = parser.parse_args()
    if args.command == 'build':
        build()
        return
    result = set_star(args.query, value=(args.command == 'star'))
    if result is None:
        print(f'没找到匹配「{args.query}」的归档')
    elif isinstance(result, list):
        print('匹配到多篇，请说得更具体：')
        for item in result[:6]:
            print('  ', item['title'][:60])
    else:
        print(('已收藏：' if args.command == 'star' else '已取消收藏：') + result['title'])
    build()


if __name__ == '__main__':
    main()
