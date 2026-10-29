#!/usr/bin/env python3
"""读写 Apple「提醒事项」里的 things 清单，供 Codex 做安静的待办管家。

  python3 scripts/things.py dump                 # 输出 JSON（内部同步用，不直接给用户看）
  python3 scripts/things.py add "标题" --due "2026-10-30 15:00" [--notes "..."]
  python3 scripts/things.py complete <id>

默认清单是 things；--list 可以换成别的清单。
"""
import argparse
import datetime as dt
import json
import subprocess
import sys


def run_applescript(script):
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip()[:400])
    return result.stdout.strip()


def dump(list_name='things'):
    # 用分隔符输出，避免 AppleScript 返回的日期/名称里混着逗号
    script = f'''
set out to ""
tell application "Reminders"
  set theList to list "{list_name}"
  repeat with r in reminders of theList
    set dn to "none"
    try
      set dd to due date of r
      if dd is not missing value then set dn to (year of dd as integer) & "-" & (month of dd as integer) & "-" & (day of dd as integer) & " " & (hours of dd as integer) & ":" & (minutes of dd as integer)
    end try
    set out to out & (id of r) & "\\t" & (name of r) & "\\t" & dn & "\\t" & (completed of r) & "\\t" & (body of r) & linefeed
  end repeat
end tell
return out
'''
    rows = []
    for line in run_applescript(script).splitlines():
        parts = line.split('\t')
        if len(parts) < 4:
            continue
        ident, name, due, done = parts[0], parts[1], parts[2], parts[3]
        notes = '\t'.join(parts[4:]) if len(parts) > 4 else ''
        rows.append({'id': ident, 'title': name, 'due': '' if due == 'none' else due,
            'completed': done.lower() == 'true', 'notes': notes})
    return rows


def add(title, due='', notes='', list_name='things', alarm_minutes=10):
    due_block = ''
    display_title = title
    if due:
        parsed = dt.datetime.strptime(due, '%Y-%m-%d %H:%M')
        alarm = parsed - dt.timedelta(minutes=alarm_minutes)
        if alarm_minutes:
            display_title = f'{title}（截止 {parsed:%m-%d %H:%M}）'
        due_block = f'''
  set dd to current date
  set year of dd to {alarm.year}
  set month of dd to {alarm.month}
  set day of dd to {alarm.day}
  set hours of dd to {alarm.hour}
  set minutes of dd to {alarm.minute}
  set seconds of dd to 0
  set due date of r to dd
  set remind me date of r to dd
'''
    safe_title = display_title.replace('"', '\\"')
    safe_notes = notes.replace('"', '\\"')
    script = f'''
tell application "Reminders"
  set theList to list "{list_name}"
  set r to make new reminder at end of theList with properties {{name:"{safe_title}", body:"{safe_notes}"}}
{due_block}
  return id of r
end tell
'''
    return run_applescript(script)


def complete(ident):
    script = f'''
tell application "Reminders"
  set r to first reminder whose id is "{ident}"
  set completed of r to true
  return name of r
end tell
'''
    return run_applescript(script)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['dump', 'add', 'complete'])
    parser.add_argument('value', nargs='?')
    parser.add_argument('--due', default='')
    parser.add_argument('--notes', default='')
    parser.add_argument('--list', default='things')
    args = parser.parse_args()
    if args.action == 'dump':
        print(json.dumps(dump(args.list), ensure_ascii=False, indent=2))
    elif args.action == 'add':
        if not args.value:
            raise SystemExit('add 需要标题')
        print(add(args.value, args.due, args.notes, args.list))
    else:
        if not args.value:
            raise SystemExit('complete 需要 id')
        print(complete(args.value))


if __name__ == '__main__':
    main()
