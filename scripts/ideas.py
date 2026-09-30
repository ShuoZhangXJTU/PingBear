#!/usr/bin/env python3
"""把「灵感/收件箱.md」里的一句话按主题归档到 灵感/<主题>.md。"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import research

ROOT = research.ROOT
INBOX = ROOT / '灵感/收件箱.md'
FILED = ROOT / '灵感'
STATE = ROOT / '.research/ideas.json'
TZ = ZoneInfo('Asia/Shanghai')
# 关键词 → 主题（先匹配到的算数；都没命中就归「其他」）
RULES = [
    ('RSI', ['rsi', '自改进', '自优化', '自我进化', 'self-improv', 'self-evol', 'recursive', '课程']),
    ('Harness', ['harness', '智能体', 'agent', '工具调用', '上下文', '记忆', 'memory', '轨迹', '编排',
        'router', 'controller', '路由', '控制器', 'skill', '工作流', 'workflow']),
    ('后训练', ['后训练', 'post-train', 'rl', '强化', 'grpo', 'ppo', '蒸馏', 'distill', '奖励', 'reward', '偏好', 'dpo']),
    ('评测', ['评测', '基准', 'benchmark', 'eval', '指标']),
    ('数据合成', ['数据', '合成', 'data', '语料']),
    ('推理', ['推理', 'reasoning', 'cot', '思维链', '长思考']),
]


def topics_of(line):
    low = line.lower()
    hits = [name for name, keys in RULES if any(key in low for key in keys)]
    return hits[:2] or ['其他']


def pending():
    if not INBOX.exists():
        return []
    return [line.strip() for line in INBOX.read_text(encoding='utf-8').splitlines()
        if line.strip().startswith('- ') and not line.strip().startswith('<!--')]


def file_ideas():
    lines = pending()
    if not lines:
        print('灵感收件箱是空的')
        return 0
    stamp = dt.datetime.now(TZ).strftime('%Y-%m-%d %H:%M')
    count = 0
    for line in lines:
        text = re.sub(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s*', '', line.lstrip('- ').strip())
        for topic in topics_of(text):
            target = FILED / f'{topic}.md'
            if target.exists():
                body = target.read_text(encoding='utf-8').rstrip('\n')
            else:
                body = f'# {topic} · 灵感\n\n'
            body += f'\n- {stamp}　{text}\n'
            research.replace(target, body)
        count += 1
    template = INBOX.read_text(encoding='utf-8')
    head = template.split('<!-- 新的一行会插到下面 -->')[0]
    research.replace(INBOX, head + '<!-- 新的一行会插到下面 -->\n')
    research.replace(STATE, {'filed': count, 'at': dt.datetime.now(TZ).isoformat(),
        'topics': sorted({t for line in lines for t in topics_of(line)})})
    print(f'已归档 {count} 条灵感')
    return count


def capture(text):
    line = f'- {dt.datetime.now(TZ):%Y-%m-%d %H:%M}　{text.strip()}\n'
    body = INBOX.read_text(encoding='utf-8') if INBOX.exists() else '# 灵感速记\n'
    marker = '<!-- 新的一行会插到下面 -->'
    if marker in body:
        head, tail = body.split(marker, 1)
        body = head + marker + '\n' + line + tail.lstrip('\n')
    else:
        body = body.rstrip('\n') + '\n' + line
    research.replace(INBOX, body)
    return line.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['file', 'add'], nargs='?', default='file')
    parser.add_argument('--text')
    args = parser.parse_args()
    if args.action == 'add':
        print(capture(args.text or ''))
    else:
        file_ideas()


if __name__ == '__main__':
    main()
