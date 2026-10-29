#!/usr/bin/env python3
"""Read-only context bridge for interactive CLI and research batch prompts."""
import argparse
import json
from pathlib import Path
import sys
import config
import core
import mount

ROOT = Path(__file__).resolve().parents[2]


def context(snapshot):
    if not config.is_mounted():
        return ''
    if snapshot.get('task') == 'industry_insight':
        import insight_policy
        return insight_policy.render(snapshot.get('stage'))
    result = mount.render(snapshot)
    if snapshot.get('project') == 'research':
        result += '\n科研路线：归档、提问、灵感是主动信号；日报采集不等于个人关注。不得凭无记录判断没有做。'
        result += '\n用户允许定期审视并提出路线调整建议，不能未经确认改写研究目标。'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', help='JSON string; omit to read JSON from stdin')
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot if args.snapshot is not None else sys.stdin.read())
    if not isinstance(snapshot, dict):
        raise ValueError('snapshot must be an object')
    print(context(snapshot))
