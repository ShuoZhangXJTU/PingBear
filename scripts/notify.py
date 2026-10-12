#!/usr/bin/env python3
"""主动通知通道：PushPlus（推到微信，不受会话窗口限制）。

token 存在 ~/.config/research-inbox/config.json 的 pushplus_token，或用环境变量 PUSHPLUS_TOKEN。
用途：每天 9:00 推送完整日报；早报失败/某段失败时推送告警。
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

import research

ROOT = research.ROOT
CONFIG = Path.home() / '.config/research-inbox/config.json'
API = 'https://www.pushplus.plus/send'
TZ = ZoneInfo('Asia/Shanghai')


def token():
    if os.environ.get('PUSHPLUS_TOKEN'):
        return os.environ['PUSHPLUS_TOKEN']
    if CONFIG.exists():
        try:
            return (research.load(CONFIG).get('pushplus_token') or '').strip()
        except Exception:
            return ''
    return ''


def save_token(value):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    data = research.load(CONFIG) if CONFIG.exists() else {}
    data['pushplus_token'] = value.strip()
    research.replace(CONFIG, data)
    return CONFIG


def send(title, content, retries=2):
    key = token()
    if not key:
        raise RuntimeError('还没有配置 PushPlus token（放到 ~/.config/research-inbox/config.json 的 pushplus_token）')
    payload = urllib.parse.urlencode({'token': key, 'title': title[:100], 'content': content,
        'template': 'markdown', 'channel': 'wechat'}).encode()
    last = ''
    for _ in range(retries + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(API, data=payload), timeout=30) as response:
                result = json.load(response)
            if result.get('code') == 200:
                return True
            last = str(result)[:200]
        except Exception as error:
            last = f'{type(error).__name__}: {error}'
    raise RuntimeError('PushPlus 发送失败：' + last)


def brief_text(date=None):
    """复用微信通道那套「完整日报」拼装逻辑，保证两边内容一致。"""
    sys.path.insert(0, str(ROOT / 'scripts'))
    import weixin_bridge
    return weixin_bridge.brief_text(date)


def flatten_headings(text):
    """PushPlus 里 # 标题字太大：把标题降成加粗普通字号，正文和链接保持原样。"""
    lines = []
    for line in text.splitlines():
        if line.startswith('#'):
            title = line.lstrip('#').strip()
            lines.append(f'**{title}**' if title else '')
        else:
            lines.append(line)
    return '\n'.join(lines)


def push_brief(date=None, wait=True):
    if wait:
        sys.path.insert(0, str(ROOT / 'scripts'))
        import weixin_bridge
        day = date or dt.datetime.now(TZ).date().isoformat()
        weixin_bridge.wait_for_brief(day)
    text = brief_text(date)
    try:
        import unread
        text += f"\n\n📕 未读归档论文：{unread.count()} 篇（Obsidian 命令面板搜「未读论文清单」）"
    except Exception:
        pass
    day = date or dt.datetime.now(TZ).date().isoformat()
    send(f'科研早报 {day}', flatten_headings(text))
    research.replace(ROOT / '.research/push-state.json',
        {'last_date': day, 'at': dt.datetime.now(TZ).isoformat(), 'chars': len(text), 'channel': 'pushplus'})
    print(f'已通过 PushPlus 推送 {day} 日报（{len(text)} 字）', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('brief', help='推送当天完整日报').add_argument('--date')
    sub.add_parser('token', help='写入 PushPlus token').add_argument('--value', required=True)
    one = sub.add_parser('send')
    one.add_argument('--title', required=True)
    one.add_argument('--content', required=True)
    args = parser.parse_args()
    if args.command == 'token':
        print('已保存到', save_token(args.value))
    elif args.command == 'send':
        send(args.title, args.content)
        print('已发送')
    else:
        push_brief(getattr(args, 'date', None))


if __name__ == '__main__':
    main()
