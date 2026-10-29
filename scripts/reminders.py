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
EXAM_WORDS = ['考试', '科目', '面试', '答辩', '航班', '机场', '医院', '签证']


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


def add_task(title, due='', notes='', source='local', ident=None, data=None, persist=True):
    data = data or load()
    due_at = parse_due(due)
    if not due_at:
        raise SystemExit('需要 --due "YYYY-MM-DD HH:MM"')
    task = {'id': ident or 'local-' + dt.datetime.now().strftime('%Y%m%d%H%M%S%f'),
        'title': title, 'due': due_at.strftime('%Y-%m-%d %H:%M'), 'notes': notes,
        'status': 'open', 'source': source, 'reminder_id': '', 'created_at': now().isoformat(timespec='seconds')}
    data['tasks'].append(task)
    if persist:
        save(data)
    return task


def conflicts(due_at, exclude_id=None, data=None, window_minutes=180):
    """找出和新任务时间接近的已有事项；考试/航班/面试这类即使差得远也算同日风险。"""
    data = data or load()
    found = []
    for task in data.get('tasks') or []:
        if task.get('status') != 'open' or task.get('id') == exclude_id:
            continue
        other = parse_due(task.get('due'))
        if not other:
            continue
        minutes = (other - due_at).total_seconds() / 60
        exam = any(word in task['title'] for word in EXAM_WORDS)
        if abs(minutes) <= window_minutes or (exam and other.date() == due_at.date()):
            found.append((task, int(minutes), exam))
    found.sort(key=lambda item: abs(item[1]))
    return found


def capture(text, dry_run=False):
    """把微信里 nnn 开头的一段话变成本地任务；重要的直接进 things。"""
    import knowledge
    today = now().date().isoformat()
    prompt = f'''用户从微信发来一条要做的事，可能带日期、时间、依赖或风险。今天是 {today}。
请提取成 JSON：
- title：一句话说清要做什么（不要带「提醒我」）；
- due：截止/要做的时间，格式 YYYY-MM-DD HH:MM；只说了日期没说时间就补 09:00；完全没提时间就留空字符串；
- importance：high 或 normal（有明确截止、涉及别人、错过代价大 → high）；
- milestones：中间节点数组，每项 {{"title":"…","due":"YYYY-MM-DD HH:MM"}}，没有就空数组；
- risk：你能看出的一两句潜在风险（时间太紧、依赖别人、和别的安排冲突、信息不足），没有就空字符串。
只输出 JSON。'''
    schema = {'type': 'object', 'properties': {
        'title': {'type': 'string'}, 'due': {'type': 'string'},
        'importance': {'type': 'string', 'enum': ['high', 'normal']},
        'milestones': {'type': 'array', 'items': {'type': 'object', 'properties': {
            'title': {'type': 'string'}, 'due': {'type': 'string'}},
            'required': ['title', 'due'], 'additionalProperties': False}},
        'risk': {'type': 'string'}},
        'required': ['title', 'due', 'importance', 'milestones', 'risk'], 'additionalProperties': False}
    data = knowledge.codex_json(prompt, {'text': text}, schema,
        STORE.parent / 'capture.json', STORE.parent / 'logs' / 'capture.log')
    due = (data.get('due') or '').strip()
    if due and len(due) == 10:
        due += ' 09:00'
    due_at = parse_due(due) if due else None
    near = conflicts(due_at) if due_at else []
    if near:
        names = '、'.join(task['title'][:24] for task, _minutes, _exam in near[:2])
        extra = f'和已有安排「{names}」时间接近，注意岔开'
        data['risk'] = (data.get('risk') or '').strip('；')
        data['risk'] = (data['risk'] + '；' + extra) if data['risk'] else extra
    if dry_run:
        return {'parsed': data, 'would_add': [data.get('title')], 'due': due,
            'nearby': [task['title'] for task, _m, _e in near]}
    store = load()
    alarm = 10
    task = add_task(data.get('title') or text, due, data.get('risk') or '', source='wechat', data=store, persist=False)
    created = 0
    if data.get('importance') == 'high' and due:
        alarm = 120 if any(exam for _t, _m, exam in near) else 10
        task['reminder_id'] = things.add(task['title'], due, task.get('notes', ''), 'things', alarm_minutes=alarm)
        created += 1
    for milestone in data.get('milestones') or []:
        m_due = (milestone.get('due') or '').strip()
        if len(m_due) == 10:
            m_due += ' 09:00'
        m = add_task(milestone.get('title') or task['title'], m_due, '来自：' + task['title'],
            source='wechat', data=store, persist=False)
        if data.get('importance') == 'high' and m_due:
            m['reminder_id'] = things.add(m['title'], m_due, m.get('notes', ''), 'things', alarm_minutes=alarm)
            created += 1
    save(store)
    parts = [f'已记下：{task["title"]}']
    if due:
        parts.append(f'时间 {due}')
    if data.get('importance') == 'high':
        parts.append('重要的，已经放到手机 things')
    if data.get('risk'):
        parts.append('风险：' + data['risk'])
    return '；'.join(parts) + '。其余我先压在本地，临近再提醒。'


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
        near = conflicts(due_at, exclude_id=task['id'], data=data)
        hint = ''
        if near:
            other, gap, _exam = near[0]
            hint = f'（附近还有「{other["title"][:24]}」，相差约 {abs(gap)} 分钟，注意岔开）'
        if minutes <= 24 * 60 and not task.get('reminder_id'):
            if dry_run:
                print(f'[dry] 会写入 Reminders：{task["title"]} @ {task["due"]}')
            else:
                task['reminder_id'] = things.add(task['title'], task['due'], task.get('notes', ''), 'things')
                created += 1
        if minutes < 0:
            message = f'已经过了时间：{task["title"]}（{task["due"]}）。要延期还是已经做完了？{hint}'
            if dry_run:
                print('[dry] 会提醒逾期：', task['title'])
            elif alert(data, task, 'overdue', message):
                alerted += 1
        elif minutes <= 120 or (risky and minutes <= 24 * 60):
            message = f'{task["title"]}：{task["due"]} 就到期了（还有 {int(minutes)} 分钟）。{hint}'
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
    cap = sub.add_parser('capture')
    cap.add_argument('text')
    cap.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    STORE.parent.mkdir(parents=True, exist_ok=True)
    if args.action == 'add':
        task = add_task(args.title, args.due, args.notes)
        print(json.dumps(task, ensure_ascii=False))
    elif args.action == 'sync':
        sync(args.init)
    elif args.action == 'capture':
        result = capture(args.text, args.dry_run)
        print(result if isinstance(result, str) else json.dumps(result, ensure_ascii=False))
    else:
        scan(args.dry_run)


if __name__ == '__main__':
    main()
