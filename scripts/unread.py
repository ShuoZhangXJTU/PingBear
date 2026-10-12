#!/usr/bin/env python3
"""未读论文清单：没打开过的归档 = 未读（等价于微信小红点）。"""
import argparse
import collections
import datetime as dt

import research

ROOT = research.ROOT
NOTES = ROOT / '论文'
OUT = ROOT / '索引/未读.md'


def scan():
    unread, read = [], []
    for path in sorted(NOTES.rglob('*.md')):
        fields, _ = research.frontmatter(path)
        item = {'path': str(path.relative_to(ROOT).with_suffix('')),
            'title': fields.get('title') or path.stem, 'topic': path.parent.name,
            'date': fields.get('selected_from') or '', 'status': fields.get('status') or 'to-read'}
        (read if item['status'] == 'read' else unread).append(item)
    return unread, read


def build():
    unread, read = scan()
    grouped = collections.defaultdict(list)
    for item in unread:
        grouped[item['topic']].append(item)
    lines = ['# 未读论文', '', '打开过的会自动标记已读（`status: read`），这里列的是还没点开的。', '',
        f'未读 **{len(unread)}** 篇 · 已读 {len(read)} 篇 · 更新 {dt.datetime.now():%Y-%m-%d %H:%M}', '']
    if not unread:
        lines.append('🎉 全部读过了。')
    for topic, items in sorted(grouped.items(), key=lambda kv: -len(kv[1])):
        lines += [f'## {topic}（{len(items)}）', '']
        for item in sorted(items, key=lambda x: x['date'], reverse=True):
            lines.append(f"- [[{item['path']}|{item['title']}]]" + (f'　<sub>{item["date"]}</sub>' if item['date'] else ''))
        lines.append('')
    research.replace(OUT, '\n'.join(lines))
    print(f'未读 {len(unread)} 篇 / 已读 {len(read)} 篇 -> {OUT}')
    return len(unread)


def count():
    return len(scan()[0])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['build', 'count'], nargs='?', default='build')
    args = parser.parse_args()
    print(count() if args.action == 'count' else '')
    if args.action == 'build':
        build()


if __name__ == '__main__':
    main()
