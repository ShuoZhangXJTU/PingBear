#!/usr/bin/env python3
"""科研飞轮：每晚把「观察 → 提炼 → 提案 → 状态」串成一条闭环。

一台数字科学家要能自己转，靠的不是某一次问答，而是这条链每天都在跑：

  1) 观察  把最近的对话原文收进 rubrics 的 episode 库，补出候选材料与关注快照
  2) 提炼  让模型从候选材料里提出带出处的 rubric 基因组草稿（draft，不激活）
  3) 提案  结合你的灵感、归档论文与手册开放问题，列出可落地的研究提案
  4) 状态  把今天跑了什么、产出什么、要你复核什么，写成一页 研究路线/飞轮.md

飞轮只生产草稿：确认永远留给人。模型自己的解释不会被自动升格成你的价值观，
一条 rubric 要经你确认、并单独复核适用范围之后，才会影响后续执行。

  python3 scripts/flywheel.py            # 跑一遍
  python3 scripts/flywheel.py --dry-run  # 只看会跑哪些阶段，不执行
"""
import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import research

ROOT = Path(__file__).resolve().parents[1]
RUBRICS = ROOT / 'rubrics'
STATE = ROOT / '.research'
TZ = ZoneInfo('Asia/Shanghai')
PYTHON = sys.executable or '/usr/bin/python3'

START, END = '<!-- flywheel:start -->', '<!-- flywheel:end -->'
LOG_JOBS = [('早报', 'scheduler.log'), ('手册', 'cookbook.log'), ('提案', 'proposal.log'),
    ('rubrics', 'rubrics.log'), ('补齐', 'settle.log'), ('云盘同步', 'sync.log')]


def stage(name, command, timeout=5400, skip=None):
    """跑一个阶段。skip 命中就跳过（比如今天已经跑过），失败不抛，留到最后统一告警。"""
    if skip:
        print(f'[飞轮] {name}：跳过（{skip}）', flush=True)
        return {'stage': name, 'ok': True, 'skipped': skip, 'note': skip}
    try:
        result = subprocess.run([str(part) for part in command], cwd=str(ROOT),
            capture_output=True, text=True, timeout=timeout)
        lines = [line for line in (result.stdout or '').strip().splitlines() if line.strip()]
        note = lines[-1][:200] if lines else ''
        ok = result.returncode == 0
        if not ok:
            tail = (result.stderr or note).strip().splitlines()
            note = f'退出码 {result.returncode}｜{(tail[-1] if tail else "")[:160]}'
    except Exception as error:
        ok, note = False, f'{type(error).__name__}: {error}'[:200]
    print(f'[飞轮] {name}：{"完成" if ok else "失败"} {note}', flush=True)
    return {'stage': name, 'ok': ok, 'note': note}


def newest_drafts(limit=6):
    """刚提出来的 rubric 草稿。只取一句话结论，不把原始对话写进要同步到云盘的页面。"""
    path = RUBRICS / 'data/criteria.json'
    if not path.exists():
        return []
    try:
        items = json.loads(path.read_text(encoding='utf-8'))
    except ValueError:
        return []
    rows = []
    for item in items:
        if ((item.get('lifecycle') or {}).get('status') or '') != 'draft':
            continue
        judgment = ((item.get('genome') or {}).get('judgment') or {})
        def field(name):
            value = judgment.get(name) if isinstance(judgment, dict) else None
            return (value.get('value') or '') if isinstance(value, dict) else (value or '')
        text = (field('statement') or field('desired_change') or field('criterion') or '').strip()
        rows.append({'id': item.get('id'), 'kind': item.get('kind'), 'text': text,
            'evidence': len(item.get('evidence') or [])})
    return rows[-limit:][::-1]


def genome_counts():
    counts = {'items': 0, 'draft': 0, 'confirmed': 0, 'with_evidence': 0}
    path = RUBRICS / 'data/criteria.json'
    if not path.exists():
        return counts
    try:
        items = json.loads(path.read_text(encoding='utf-8'))
    except ValueError:
        return counts
    counts['items'] = len(items)
    for item in items:
        status = ((item.get('lifecycle') or {}).get('status') or '')
        counts['confirmed' if status == 'confirmed' else 'draft'] += 1
        if item.get('evidence'):
            counts['with_evidence'] += 1
    return counts


def newest_proposals(limit=6):
    files = sorted((ROOT / '提案').glob('2*.md'))
    if not files:
        return None, [], 0
    text = files[-1].read_text(encoding='utf-8')
    titles = [line[3:].strip() for line in text.splitlines() if line.startswith('## P')]
    return files[-1].stem, titles[:limit], len(titles)


def engine_health():
    rows = []
    for name, log in LOG_JOBS:
        path = STATE / 'logs' / log
        if not path.exists():
            rows.append((name, '没有日志', ''))
            continue
        when = dt.datetime.fromtimestamp(path.stat().st_mtime, TZ)
        age = (dt.datetime.now(TZ) - when).total_seconds() / 3600
        rows.append((name, when.strftime('%m-%d %H:%M'), f'已 {age/24:.0f} 天没动' if age > 26 else ''))
    return rows


def write_status(date, results, started):
    counts = genome_counts()
    proposal_date, titles, proposal_total = newest_proposals()
    drafts = newest_drafts()
    episodes = 0
    for path in (RUBRICS / 'episodes').glob('*.jsonl'):
        episodes += sum(1 for line in path.read_text(encoding='utf-8', errors='replace').splitlines() if line.strip())
    archived = len(list((ROOT / '论文').glob('*/*.md')))
    failed = [row for row in results if not row['ok']]
    lines = ['# 科研飞轮', '', START, '',
        f'最近一次运行：{started:%Y-%m-%d %H:%M}（北京时间）· 数据日期 {date} · '
        + ('全部阶段正常' if not failed else f'有 {len(failed)} 个阶段失败'), '',
        '## 这一轮跑了什么', '']
    for row in results:
        mark = '正常' if row['ok'] else '失败'
        detail = row.get('skipped') or row.get('note') or ''
        lines.append(f'- {row["stage"]}：{mark}{"（" + detail + "）" if detail else ""}')
    lines += ['', '## 要你复核的（飞轮只出草稿）', '',
        f'- rubric 草稿 {counts["draft"]} 条 / 已确认 {counts["confirmed"]} 条'
        f'（其中有出处的 {counts["with_evidence"]} 条）',
        '- 复核入口：`python3 rubrics/src/manage.py audit`；确认用 '
        '`python3 rubrics/src/manage.py confirm --id <编号> --note "..."`',
        '- 草稿不影响任何执行；确认、并且单独复核适用范围之后才会生效。', '']
    if drafts:
        lines += ['最近提出的草稿：', '']
        for row in drafts:
            text = row['text'] or f'待提炼（{row["kind"]}，出处 {row["evidence"]} 条）'
            lines.append(f'- `{row["id"]}` {text[:90]}')
        lines.append('')
    if proposal_date:
        lines += [f'## 最新提案', '',
            f'`提案/{proposal_date}.md`，这一批共 {proposal_total} 条，下面是前几条：', '']
        lines += [f'- {title}' for title in titles] or ['- （这一批还没有内容）']
        lines.append('')
    else:
        lines += ['## 最新提案', '', '- 还没有提案文件', '']
    lines += ['## 引擎健康（最近一次动作时间）', '']
    lines += [f'- {name}：{when}{"　" + warn if warn else ""}' for name, when, warn in engine_health()]
    lines += ['', '## 复利指标', '',
        f'- episode 原文 {episodes} 条 · rubric 条目 {counts["items"]} 条',
        f'- 归档论文 {archived} 篇 · 提案 {len(list((ROOT / "提案").glob("2*.md")))} 批', '', END, '']
    research.replace(ROOT / '研究路线/飞轮.md', '\n'.join(lines))
    return ROOT / '研究路线/飞轮.md'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--skip-distill', action='store_true', help='只观察与提案，不调模型提炼')
    args = parser.parse_args()
    now = dt.datetime.now(TZ)
    date = now.date().isoformat()
    label = 'nightly-' + date
    build_dir = RUBRICS / 'data/builds' / label
    prepared = '今天已经准备过' if build_dir.exists() else None
    plan = [('观察对话原文', [PYTHON, RUBRICS / 'src/observe.py', '--days', '2'], None),
        ('提炼草稿（准备材料）', [PYTHON, RUBRICS / 'src/build.py', '--days', '2', '--label', label], prepared),
        ('提炼草稿（模型生成）', [PYTHON, RUBRICS / 'src/build.py', '--generate', build_dir], prepared),
        ('列出研究提案', [PYTHON, ROOT / 'scripts/proposal.py', '--limit', '0'],
            '今天已经生成' if (ROOT / '提案' / f'{date}.md').exists() else None)]
    if args.skip_distill:
        plan = [row for row in plan if '提炼' not in row[0]]
    if args.dry_run:
        for name, command, skip in plan:
            shown = f'跳过（{skip}）' if skip else ' '.join(str(part) for part in command[1:])
            print(f'[dry-run] {name}: {shown}')
        return
    results = [stage(name, command, skip=skip) for name, command, skip in plan]
    path = write_status(date, results, now)
    print(f'[飞轮] 状态页 -> {path}', flush=True)
    failures = [row for row in results if not row['ok']]
    if failures:
        try:
            import alert
            alert.send('⚠️ 科研飞轮有阶段没跑成：\n'
                + '\n'.join(f'· {row["stage"]}：{row["note"]}' for row in failures)
                + '\n（其余阶段正常，明天会自动重试）', key='flywheel-failed:' + date)
        except Exception as error:
            print('[飞轮] 告警发送失败:', type(error).__name__, error, flush=True)
        raise SystemExit(1)


if __name__ == '__main__':
    STATE.mkdir(exist_ok=True)
    main()
