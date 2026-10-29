#!/usr/bin/env python3
"""安静的待办管家：事情压在本地，只在临近或有风险时才提醒。

  python3 scripts/reminders.py add "周五下午三点交材料" --due "2026-10-31 15:00"
  python3 scripts/reminders.py sync --init      # 首次把 things 清单静默并入本地
  python3 scripts/reminders.py scan --dry-run   # 看会提醒什么，不发
  python3 scripts/reminders.py scan             # 到点/有风险才提醒（默认由 launchd 每 10 分钟跑）

提醒规则：
  - 到期前 24 小时内：把这件事写进 Apple「things」清单，手机到点响；
  - 到期前 2 小时或已逾期：额外发一条微信/PushPlus；
  - 航班、面试、考试、提交、截止、医院等高风险词：提前 24 小时就发一次；
  - 其余事情只存在本地，不打扰。
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import research
import things

ROOT = research.ROOT
STORE = ROOT / '.research/reminders/store.json'
TZ = ZoneInfo('Asia/Shanghai')
RISK_WORDS = ['航班', '飞机', '机场', '面试', '考试', '提交', '截止', '医院', '挂号', '签证', '报到', '答辩', '签约', '缴费', '快递']


def now():
    return dt.datetime.now(TZ).replace(tzinfo=None)


def load():
    return research.load(STORE) if STORE.exists() else {'tasks': [], 'alerts': {}, 'init_at': ''}


def save(data):
    research.replace(STORE, data)


def parse_due(text):
    if not text:
        return None
    for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'):
        try:
            return dt.datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def add_task(title, due='', notes='', source='local', ident=None):
    data = load()
    due_at = parse_due(due)
    if not due_at:
        raise SystemExit('需要 --due "YYYY-MM-DD HH:MM"')
    task = {'id': ident or 'local-' + dt.datetime.now().strftime('%Y%m%d%H%M%S%f'),
        'title': title, 'due': due_at.strftime('%Y-%m-%d %H:%M'), 'notes': notes,
        'status': 'open', 'source': source, 'reminder_id': '', 'created_at': now().isoformat(timespec='seconds')}
    data['tasks'].append(task)
    save(data)
    return task


def sync(initial=False):
    data = load()
    rows = things.dump('things')
    index = {(t['title'], t['due']): t for t in data['tasks']}
    added = 0
    for row in rows:
        due = row.get('due') or ''
        key = (row['title'], due)
        if key in index:
            task = index[key]
            task['reminder_id'] = row['id']
            if row['completed']:
                task['status'] = 'done'
            continue
        if row['completed']:
            continue
        task = {'id': 'things-' + row['id'], 'title': row['title'], 'due': due,
            'notes': row.get('notes', ''), 'status': 'open', 'source': 'things',
            'reminder_id': row['id'], 'created_at': now().isoformat(timespec='seconds')}
        data['tasks'].append(task)
        index[key] = task
        added += 1
    if initial or not data.get('init_at'):
        data['init_at'] = now().isoformat(timespec='seconds')
    save(data)
    print(f'things 同步：{len(rows)} 条，新增 {added} 条，本地共 {len(data["tasks"])} 条')


def alert(data, task, kind, message):
    day = now().date().isoformat()
    key = f'{task["id"]}:{kind}:{day}'
    if key in data.get('alerts', {}):
        return False
    try:
        import notify
        notify.send('待办提醒', message)
    except Exception as error:
        print('提醒发送失败:', type(error).__name__, error, flush=True)
        return False
    data.setdefault('alerts', {})[key] = now().isoformat(timespec='seconds')
    return True


def scan(dry_run=False):
    data = load()
    current = now()
    created = alerted = 0
    for task in data['tasks']:
        if task.get('status') != 'open':
            continue
        due_at = parse_due(task.get('due'))
        if not due_at:
            continue
        minutes = (due_at - current).total_seconds() / 60
        risky = any(word in (task['title'] + ' ' + task.get('notes', '')) for word in RISK_WORDS)
        if minutes <= 24 * 60 and not task.get('reminder_id'):
            if dry_run:
                print(f'[dry] 会写入 Reminders：{task["title"]} @ {task["due"]}')
            else:
                task['reminder_id'] = things.add(task['title'], task['due'], task.get('notes', ''), 'things')
                created += 1
        if minutes < 0:
            message = f'已经过了时间：{task["title"]}（{task["due"]}）。要延期还是已经做完了？'
            if dry_run:
                print('[dry] 会提醒逾期：', task['title'])
            elif alert(data, task, 'overdue', message):
                alerted += 1
        elif minutes <= 120 or (risky and minutes <= 24 * 60):
            message = f'{task["title"]}：{task["due"]} 就到期了（还有 {int(minutes)} 分钟）。'
            if dry_run:
                print('[dry] 会提醒临近：', task['title'], f'{int(minutes)} 分钟')
            elif alert(data, task, 'soon', message):
                alerted += 1
    if not dry_run:
        save(data)
    print(f'扫描完成：写入手机提醒 {created} 条，发出提醒 {alerted} 条（共 {len(data["tasks"])} 条本地任务）')


def main():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='action', required=True)
    add = sub.add_parser('add')
    add.add_argument('title')
    add.add_argument('--due', required=True)
    add.add_argument('--notes', default='')
    sync_p = sub.add_parser('sync')
    sync_p.add_argument('--init', action='store_true')
    scan_p = sub.add_parser('scan')
    scan_p.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    STORE.parent.mkdir(parents=True, exist_ok=True)
    if args.action == 'add':
        task = add_task(args.title, args.due, args.notes)
        print(json.dumps(task, ensure_ascii=False))
    elif args.action == 'sync':
        sync(args.init)
    else:
        scan(args.dry_run)


if __name__ == '__main__':
    main()
