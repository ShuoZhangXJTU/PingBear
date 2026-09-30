#!/usr/bin/env python3
"""历史目录：把每天的日报按日期和来源索引成一页，顺带统计归档与专题。"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import research

ROOT = research.ROOT
DAILY = ROOT / '日报'
OUT = ROOT / '索引/目录.md'
TZ = ZoneInfo('Asia/Shanghai')
SOURCES = [
    ('hf', 'HF Daily Papers', '', 'digest', r'^## \d+\.'),
    ('xhs', '小红书 · tabris', '-小红书', 'xhs-digest', r'^## X\d+\.'),
    ('inbox', '我的链接', '-我的链接', 'inbox-digest', r'^## M\d+\.'),
    ('blog', '官方博客与研究发布', '-博客', 'blog-digest', r'^## B\d+\.'),
]


def load(path):
    fields, body = research.frontmatter(path)
    title = ''
    match = re.search(r'^#\s+(.+)$', body, re.M)
    if match:
        title = match.group(1).strip()
    return fields, body, title


def scan():
    days = {}
    for key, name, suffix, kind, counter in SOURCES:
        pattern = re.compile(counter, re.M)
        for path in sorted(DAILY.glob(f'????-??-??{suffix}.md')):
            date = path.name[:10]
            fields, body, title = load(path)
            days.setdefault(date, {})[key] = {
                'date': date, 'path': path.name, 'name': name, 'kind': kind, 'title': title,
                'count': len(pattern.findall(body)),
            }
    archived = {}
    for path in sorted((ROOT / '论文').rglob('*.md')):
        fields, _ = research.frontmatter(path)
        day = (fields.get('selected_from') or '')[:10]
        if day:
            archived.setdefault(day, []).append(str(path.relative_to(ROOT).with_suffix('')))
    return days, archived


def build():
    days, archived = scan()
    topics = []
    for path in sorted((ROOT / '专题').glob('*.md')):
        text = path.read_text(encoding='utf-8')
        topics.append((path.stem, text.count('- [[论文/')))
    lines = ['# 历史目录', '', '自动生成，改动会被覆盖。按日期和来源两个维度索引所有日报。', '',
        f'日报 {len(days)} 天 · 归档 {sum(len(v) for v in archived.values())} 篇 · 专题页 {len(topics)} 个 · 重建 {dt.datetime.now(TZ):%Y-%m-%d %H:%M}', '',
        '其他入口：[[今日简报]] · [[索引/标签|按标签查归档]] · [[问答/知识助手|归档问答记录]] · [[收件箱/我的链接|我的链接入口]] · [[配置/研究偏好|研究偏好]]', '',
        '## 按日期', '']
    for date in sorted(days, reverse=True):
        entries = days[date]
        notes = archived.get(date)
        total = sum(item['count'] for item in entries.values())
        lines.append(f"### {date}（{total} 条{'，归档 ' + str(len(notes)) + ' 篇' if notes else ''}）")
        lines.append('')
        for key, name, _suffix, _kind, _counter in SOURCES:
            item = entries.get(key)
            if not item:
                continue
            label = item['title'] or name
            lines.append(f"- {name}（{item['count']} 条）：[[日报/{item['path'][:-3]}|{label}]]")
        if notes:
            lines.append('- 当天归档：' + ' · '.join(f'[[{note}]]' for note in notes))
        lines.append('')
    lines += ['## 按来源', '']
    for key, name, _suffix, _kind, _counter in SOURCES:
        items = [(date, entries[key]) for date, entries in sorted(days.items(), reverse=True) if key in entries]
        total = sum(item['count'] for _date, item in items)
        lines += [f'### {name}（{len(items)} 天 / {total} 条）', '']
        if not items:
            lines.append('- 暂无记录')
        for date, item in items:
            lines.append(f"- {date}（{item['count']} 条）：[[日报/{item['path'][:-3]}]]")
        lines.append('')
    lines += ['## 知识体系', '']
    if topics:
        for name, count in topics:
            lines.append(f'- [[专题/{name}]]（关联 {count} 篇归档）')
    else:
        lines.append('- 还没有专题页')
    qa_dir = ROOT / '问答'
    qa_files = sorted(qa_dir.glob('*.md')) if qa_dir.exists() else []
    lines += ['', f'## 问答记录（{len(qa_files)} 个）', '']
    for path in qa_files[:40]:
        lines.append(f'- [[问答/{path.stem}]]')
    lines.append('')
    research.replace(OUT, '\n'.join(lines))
    print(f'目录已更新：{len(days)} 天 / {len(topics)} 个专题 -> {OUT}')
    return OUT


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    build()


if __name__ == '__main__':
    main()
