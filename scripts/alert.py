#!/usr/bin/env python3
"""运行故障 → 微信告警。

同一天同一个故障只发一次；微信推送窗口过期时进入队列，等用户下次跟机器人说话时补发。
"""
import argparse
import datetime as dt
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import research

ROOT = research.ROOT
STATE = ROOT / '.research/alerts.json'
QUEUE = ROOT / '.research/alert-queue.json'
TZ = ZoneInfo('Asia/Shanghai')


def sent_today(key, day):
    state = research.load(STATE) if STATE.exists() else {}
    return state.get(key) == day


def mark(key, day):
    state = research.load(STATE) if STATE.exists() else {}
    state[key] = day
    research.replace(STATE, state)


def enqueue(text):
    items = research.load(QUEUE) if QUEUE.exists() else []
    items.append({'at': dt.datetime.now(TZ).isoformat(), 'text': text})
    research.replace(QUEUE, items[-20:])


def send(text, key=None, force=False):
    day = dt.datetime.now(TZ).date().isoformat()
    if key and not force and sent_today(key, day):
        print(f'（{key} 今天已告警过，跳过）')
        return False
    sys.path.insert(0, str(ROOT / 'scripts'))
    import weixin_bridge
    try:
        ok = weixin_bridge.push_text(text)
    except Exception as error:
        print('告警发送失败:', type(error).__name__, error)
        ok = False
    if ok:
        if key:
            mark(key, day)
        print('✅ 已发微信告警')
    else:
        enqueue(text)
        if key:
            mark(key, day)
        print('⚠️ 微信暂时发不出去，已排队（你下次和机器人说话时会自动收到）')
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--text', required=True)
    parser.add_argument('--key')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    send(args.text, args.key, force=args.force)


if __name__ == '__main__':
    main()
