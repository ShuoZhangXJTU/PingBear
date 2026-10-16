#!/usr/bin/env python3
"""Local research attention evidence; never equate feed coverage with personal interest."""
import argparse
from collections import Counter
import datetime as dt
import fcntl
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo
import core
import episodes

ROOT = Path(__file__).resolve().parents[2]
TZ = ZoneInfo('Asia/Shanghai')
START = '<!-- rubrics:attention:start -->'
END = '<!-- rubrics:attention:end -->'
RULES = {
    'RSI': r'\brsi\b|自我改进|自优化|自改进|self.improv',
    'Harness/记忆': r'\bharness\b|\bmemory\b|记忆|上下文|\btrigger\b|\bstate\b|rubric',
    '后训练': r'后训练|\brl\b|\bgrpo\b|\bppo\b|\bopd\b|蒸馏|distill|post.train',
    '评测/验证': r'评测|验证|消融|归因|benchmark|\beval\b|verif',
    '环境/世界模型': r'环境|世界模型|\benv\b|world model',
}


def topics(text):
    return [name for name, pattern in RULES.items() if re.search(pattern, text, re.I)] or ['未分类']


def replace_block(path, generated, title=''):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = path.read_text() if path.exists() else title + '\n\n'
    block = START + '\n' + generated.rstrip() + '\n' + END
    if START in body:
        if body.count(START) != 1 or body.count(END) != 1:
            raise ValueError(f'broken managed markers: {path}')
        head, tail = body.split(START, 1)
        _, rest = tail.split(END, 1)
        body = head + block + rest
    else:
        body = body.rstrip() + '\n\n' + block + '\n'
    path.write_text(body)


def metadata(text):
    fields = {}
    if not text.startswith('---\n'):
        return fields
    for line in text.split('---\n', 2)[1].splitlines():
        if ':' in line and not line.startswith(' '):
            key, val = line.split(':', 1)
            fields[key] = val.strip().strip('"')
    return fields


def collect(root=ROOT):
    """Return identifiable actions and undated holdings, with source line references."""
    events = []
    def add(kind, date, text, path, line, key=None, date_basis='explicit'):
        text = text.strip()
        if not text:
            return
        if date and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
            date = None
        # A duplicated idea in multiple topic files is one action, not two interests.
        identity = key or f'{kind}|{date}|{text}'
        ident = hashlib.sha256(identity.encode()).hexdigest()[:20]
        event = {'id': ident, 'kind': kind, 'date': date, 'date_basis': date_basis if date else 'unknown',
                 'text': text, 'topics': topics(text), 'source': str(path.relative_to(root)), 'line': line}
        events.append(event)
    for path in sorted((root / '灵感').glob('*.md')):
        for n, line in enumerate(path.read_text().splitlines(), 1):
            match = re.match(r'^- (\d{4}-\d{2}-\d{2})\s+\d{2}:\d{2}[\s\u3000]+(.+)', line)
            if match:
                add('idea', match[1], match[2], path, n)
    for path in sorted((root / '问答').glob('*.md')):
        body = path.read_text()
        # Separate question from generated answer; only the question is a personal signal.
        pattern = r'^## (?:Q\d+（)?(\d{4}-\d{2}-\d{2})[^\n]*\n(.*?)(?=^## |\Z)'
        for match in re.finditer(pattern, body, re.M | re.S):
            block = match[2]
            if '**问**' in block:
                question = block.split('**问**', 1)[1].split('**答**', 1)[0].lstrip('：: \n')
            else:
                question = block.split('### 答', 1)[0].strip()
            add('question', match[1], question, path, body[:match.start()].count('\n') + 1)
    for path in sorted((root / '论文').rglob('*.md')):
        body = path.read_text()
        meta = metadata(body)
        title = meta.get('title') or path.stem
        identity = meta.get('entry_id') or meta.get('arxiv') or str(path.relative_to(root))
        add('archived', None, title, path, 1, key='archived|' + identity)
        if meta.get('opened'):
            add('opened', meta['opened'], title, path, 1, key='opened|' + identity + '|' + meta['opened'])
        for match in re.finditer(r'^## (我的备注|我的想法|我的选择理由|精读笔记)\s*\n(.*?)(?=^## |<!-- knowledge:|\Z)', body, re.M | re.S):
            note = match[2].strip()
            if note and note not in ('（无）', '无', '暂无'):
                add('personal_note', None, note, path, body[:match.start()].count('\n') + 1, key='note|' + identity + '|' + note)
    seen = {}
    for event in events:
        seen.setdefault(event['id'], event)
    return list(seen.values())


def recent_events(events, day, days=14):
    since = day - dt.timedelta(days=days - 1)
    return [e for e in events if e['date'] and since.isoformat() <= e['date'] <= day.isoformat()]


def run(root=ROOT, day=None):
    day = day or dt.datetime.now(TZ).date()
    state_dir = root / '.research/rubrics'
    state_dir.mkdir(parents=True, exist_ok=True)
    with (state_dir / 'attention.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        events = collect(root)
        state_path = state_dir / 'attention.json'
        prior = json.loads(state_path.read_text()) if state_path.exists() else {'events': []}
        old = {e['id']: e for e in prior['events']}
        for event in events:
            event['first_seen_at'] = old.get(event['id'], {}).get('first_seen_at') or dt.datetime.now(TZ).isoformat()
            event['new_since_last_scan'] = bool(old) and event['id'] not in old
        recent = recent_events(events, day)
        personal = [e for e in recent if e['kind'] in ('idea', 'question')]
        counts = Counter(t for e in personal for t in e['topics'])
        # Content digest excludes timestamps and computed first-seen flags.
        digest = hashlib.sha256(json.dumps([{k: e[k] for k in ('id', 'kind', 'date', 'text')} for e in events], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        state = {'updated_at': dt.datetime.now(TZ).isoformat(), 'fingerprint': digest, 'events': events,
                 'recent_personal_topics': dict(counts), 'window_days': 14,
                 'limits': ['No feed-to-interest inference', 'selected_from is source date, never action time',
                            'No experiment progress inferred from note modification time']}
        tmp = state_path.with_suffix('.tmp'); tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2)); tmp.replace(state_path)
        lines = [f'更新：{state["updated_at"]}；窗口：最近 14 个自然日。', '',
                 '这里只记录可观察行为，不以采集数量推断兴趣，也不把没有记录等同于没有做。', '',
                 '## 主动表达的关注', '',
                 f'带日期的灵感 {sum(e["kind"] == "idea" for e in recent)} 条；主动问题 {sum(e["kind"] == "question" for e in recent)} 条。', '',
                 '关键词标签用于导航，一条记录可以属于多个主题；不表示主题重要性排名。', '']
        lines += [f'- {topic}：{count} 条主动表达提及。' for topic, count in counts.most_common()]
        lines += ['', '## 可核对的近期原话', '']
        for event in sorted(personal, key=lambda e: (e['date'], e['id']), reverse=True)[:25]:
            title = '灵感' if event['kind'] == 'idea' else '提问'
            excerpt = event['text'].replace('\n', ' ')
            excerpt = excerpt[:450] + ('…（全文见来源）' if len(excerpt) > 450 else '')
            lines.append(f'- {event["date"]} · {title}：{excerpt} — [[{event["source"][:-3]}|来源]]（第 {event["line"]} 行）')
        lines += ['', '## 归档与打开记录', '',
                  f'当前归档 {sum(e["kind"] == "archived" for e in events)} 篇；窗口内明确记录打开 {sum(e["kind"] == "opened" for e in recent)} 篇。打开不等于读完。',
                  '归档的 selected_from 是来源日报日期，未当作归档日期。未注明时间的个人备注只作背景。', '',
                  '## 路线审视入口', '',
                  '[[研究路线/当前路线|当前路线与实验承诺]] · [[研究路线/审视记录|审视记录]] · [[研究路线/评价体系|评价体系状态]]', '',
                  '每周一、四 09:30（北京时间）在 Codex 执行路线审视；没有新的可行动证据不重复提醒。']
        replace_block(root / '研究路线/近期关注.md', '\n'.join(lines), '# 近期关注')
        items = core.load()
        confirmed = [i for i in items if i.get('lifecycle', {}).get('status') == 'confirmed']
        summary = ['CLI 与 Research 使用同一份本地 rubrics 数据。', '',
                   f'共 {len(items)} 条；已确认 {len(confirmed)} 条；其余草稿或退休条目不会作为执行规则注入。', '',
                   '## 已确认条目', '']
        for item in confirmed:
            summary.append(f'- `{item["id"]}`：{item["genome"]["judgment"]["statement"]["value"]}')
        summary += ['', '原始对话和完整基因组不复制到此页面。草稿可以辅助理解，但不能当作已确认偏好。',
                    '当前新建规则只来自本次明确授权，历史 89 条没有被批量确认。']
        replace_block(root / '研究路线/评价体系.md', '\n'.join(summary), '# 评价体系')
        print(f'关注快照：{len(events)} 条证据，近14天主动表达 {len(personal)} 条；{root / "研究路线/近期关注.md"}')
        return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    run(args.root)


if __name__ == '__main__':
    main()
