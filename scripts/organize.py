#!/usr/bin/env python3
"""把 论文/<arxiv编号>.md 重命名为 论文/<主题>/<论文标题>.md，并改写所有引用链接。"""
import argparse
import re
import sys
from pathlib import Path

import research

ROOT = research.ROOT
NOTES = ROOT / '论文'
BAD = re.compile(r'[\\/:*?"<>|\n\r\t]+')


def safe_name(title, fallback):
    name = BAD.sub(' ', title or '').strip().strip('.')
    name = re.sub(r'\s+', ' ', name)
    return (name[:90] or fallback).strip()


def note_path(record):
    """按 primary_tag 建主题文件夹，用论文标题当文件名。"""
    tag = (record.get('primary_tag') or (record.get('tags') or ['其他'])[0] or '其他')
    tag = BAD.sub(' ', str(tag)).strip() or '其他'
    return NOTES / tag / (safe_name(record.get('title'), record.get('id', 'note')) + '.md')


def migrate():
    moves = []
    for path in sorted(NOTES.glob('*.md')):
        fields, _ = research.frontmatter(path)
        ident = fields.get('arxiv') or path.stem
        record = {'id': ident, 'title': fields.get('title') or path.stem,
            'primary_tag': fields.get('primary_tag') or '', 'tags': fields.get('tags') or []}
        if isinstance(record['tags'], str):
            record['tags'] = [record['tags']]
        new_path = note_path(record)
        if new_path == path:
            continue
        if new_path.exists() and new_path != path:
            new_path = new_path.with_name(new_path.stem + ' ' + str(ident)[-5:] + '.md')
        moves.append((path, new_path, str(ident), fields.get('title') or path.stem))
    for old, new, ident, title in moves:
        new.parent.mkdir(parents=True, exist_ok=True)
        old.rename(new)
        print(f'{old.name} → {new.relative_to(ROOT)}')
    # 改写所有 .md 里的 [[论文/<编号>...]] 链接
    table = {ident: str(new.relative_to(ROOT).with_suffix('')) for _old, new, ident, _t in moves}
    changed = 0
    for path in list(ROOT.rglob('*.md')):
        if '.obsidian' in path.parts or '.research' in path.parts or 'backups' in path.parts:
            continue
        text = path.read_text(encoding='utf-8', errors='replace')
        original = text
        for ident, target in table.items():
            text = text.replace(f'[[论文/{ident}|', f'[[{target}|').replace(f'[[论文/{ident}]]', f'[[{target}]]')
        if text != original:
            path.write_text(text, encoding='utf-8')
            changed += 1
    print(f'重命名 {len(moves)} 篇，改写引用 {changed} 个文件')
    return moves


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    migrate()
    import research as r
    r.build_index(ROOT)
    import catalog
    catalog.build()


if __name__ == '__main__':
    main()
