#!/usr/bin/env python3
"""Sync only rubric-facing notes; protect manual edits with a stored merge base.
No rsync of raw conversations, no model call, no notification side effects.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
from activity import replace_block, START, END

ROOT = Path(__file__).resolve().parents[2]
CLOUD = Path.home() / 'Library/Mobile Documents/iCloud~md~obsidian/Documents/research'


def merge_manual(base, local, remote):
    if local == remote:
        return local
    if base is not None:
        if local == base:
            return remote
        if remote == base:
            return local
        if local.startswith(base) and remote.startswith(base):
            a, b = local[len(base):], remote[len(base):]
            return base + a + ('' if b == a else b)
    raise ValueError('both versions changed; manual merge required')


def publish(root=ROOT, cloud=CLOUD):
    if not cloud.exists():
        raise FileNotFoundError('iCloud research vault is unavailable')
    state_path = root / '.research/rubrics/cloud-sync.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    conflicts = []
    for name in ('当前路线.md', '审视记录.md'):
        local, remote = root / '研究路线' / name, cloud / '研究路线' / name
        if not local.exists():
            continue
        remote.parent.mkdir(parents=True, exist_ok=True)
        a = local.read_text()
        try:
            value = merge_manual(state.get(name), a, remote.read_text()) if remote.exists() else a
        except ValueError:
            digest = hashlib.sha256((a + remote.read_text()).encode()).hexdigest()[:12]
            directory = root / '.research/rubrics/conflicts' / digest
            directory.mkdir(parents=True, exist_ok=True)
            (directory / ('local-' + name)).write_text(a)
            (directory / ('cloud-' + name)).write_text(remote.read_text())
            conflicts.append(name)
            continue
        local.write_text(value)
        remote.write_text(value)
        state[name] = value
    # 每个页面用各自的区块标记：近期关注/评价体系 用 attention 标记，飞轮页用自己的。
    blocks = {'近期关注.md': (START, END), '评价体系.md': (START, END),
        '飞轮.md': ('<!-- flywheel:start -->', '<!-- flywheel:end -->')}
    for name in blocks:
        local, remote = root / '研究路线' / name, cloud / '研究路线' / name
        if local.exists():
            text = local.read_text()
            start, end = blocks[name]
            if start not in text or end not in text:
                print(f'跳过 {name}：找不到区块标记')
                continue
            content = text.split(start, 1)[1].split(end, 1)[0].strip()
            replace_block(remote, content, '# ' + name[:-3])
    links = ('[[研究路线/飞轮|科研飞轮]] · [[研究路线/近期关注|近期关注]] · [[研究路线/当前路线|当前路线]] · '
        '[[研究路线/审视记录|路线审视]] · [[研究路线/评价体系|评价体系]]')
    for home in (root / '今日简报.md', cloud / '今日简报.md'):
        if home.exists():
            replace_block(home, links)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    if conflicts:
        raise ValueError('保留双方版本，未覆盖冲突页面：' + '、'.join(conflicts))
    print('已同步路线页面至 iCloud；个人编辑保留，原始对话未复制。')


if __name__ == '__main__':
    publish()
