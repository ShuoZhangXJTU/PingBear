#!/usr/bin/env python3
"""把当天「自动科研」和 rubrics 做了什么写成一节，供今日简报引用。

数据全部来自已经落盘的产物，不额外调用模型：
  - 提案/<日期>.md（自动科研当天列出的提案）
  - rubrics/proposals/<日期>.md（当天收进候选的完整发言条数）
  - rubrics/data/criteria.json（基因组草稿/确认/今日新增）
  - 研究路线/飞轮.md（飞轮这一轮各阶段结果）
  - 最佳实践/、专题/（当天更新过的文件和主题）

产物：日报/<日期>-研究.md
"""
import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import research

ROOT = research.ROOT
TZ = dt.timezone(dt.timedelta(hours=8))


def proposal_digest(date):
    path = ROOT / '提案' / f'{date}.md'
    if not path.exists():
        return 0, []
    text = path.read_text(encoding='utf-8')
    titles = [line[3:].strip() for line in text.splitlines() if line.startswith('## P')]
    return len(titles), titles


def rubric_digest(date):
    path = ROOT / 'rubrics/proposals' / f'{date}.md'
    candidates = 0
    if path.exists():
        candidates = sum(1 for line in path.read_text(encoding='utf-8').splitlines() if line.startswith('## C'))
    counts = {'items': 0, 'draft': 0, 'confirmed': 0, 'with_evidence': 0, 'created_today': 0}
    store = ROOT / 'rubrics/data/criteria.json'
    if store.exists():
        try:
            items = json.loads(store.read_text(encoding='utf-8'))
        except ValueError:
            items = []
        counts['items'] = len(items)
        for item in items:
            lifecycle = item.get('lifecycle') or {}
            status = lifecycle.get('status') or ''
            counts['confirmed' if status == 'confirmed' else 'draft'] += 1
            if item.get('evidence'):
                counts['with_evidence'] += 1
            if str(lifecycle.get('created_at') or '').startswith(date):
                counts['created_today'] += 1
    return candidates, counts


def flywheel_digest():
    path = ROOT / '研究路线/飞轮.md'
    if not path.exists():
        return []
    text = path.read_text(encoding='utf-8')
    if '## 这一轮跑了什么' not in text:
        return []
    block = text.split('## 这一轮跑了什么', 1)[1].split('\n## ', 1)[0]
    return [line.strip('- ').strip() for line in block.splitlines() if line.strip().startswith('- ')]


def touched_today(folder, date):
    out = []
    for path in sorted((ROOT / folder).glob('*.md')):
        stamp = dt.datetime.fromtimestamp(path.stat().st_mtime, TZ).date().isoformat()
        if stamp == date:
            out.append(path.stem)
    return out


JOBS = ['morning', 'cookbook', 'flywheel', 'settle', 'settle-sweep', 'sync',
    'xhs-check', 'xhs-following', 'weixin', 'requests']


def job_health():
    """看每个定时任务最近一次的退出码；只把失败列出来，避免每天刷屏。"""
    bad, unknown = [], []
    for name in JOBS:
        label = 'local.research.' + name
        try:
            text = subprocess.run(['launchctl', 'print', 'gui/501/' + label],
                capture_output=True, text=True, timeout=10).stdout
        except Exception:
            unknown.append(name)
            continue
        if not text:
            unknown.append(name)
            continue
        match = re.search(r'last exit code = (\d+)', text)
        if match and match.group(1) != '0':
            bad.append(f'{name}（退出码 {match.group(1)}）')
    return bad, unknown


def write(date=None):
    date = date or dt.datetime.now(TZ).date().isoformat()
    count, titles = proposal_digest(date)
    candidates, counts = rubric_digest(date)
    stages = flywheel_digest()
    books = touched_today('最佳实践', date)
    topics = touched_today('专题', date)
    lines = [f'---\ndate: {date}\ntype: research-digest\n---\n\n',
        f'# {date} 自动科研 · rubrics\n\n', '## 自动科研（RSI 提案）\n\n']
    if count:
        lines.append(f'- 今天列出 {count} 条提案，全部写在 `提案/{date}.md`。')
        lines += [f'- {title}' for title in titles[:6]]
        if count > 6:
            lines.append(f'- ……其余 {count - 6} 条见文件')
    else:
        lines.append('- 今天没有生成提案（可能素材不足或任务未跑）。')
    lines += ['', '## rubrics（评价体系）\n\n',
        f'- 今天收进 {candidates} 条完整发言作为候选材料。',
        f'- 基因组共 {counts["items"]} 条：草稿 {counts["draft"]}、已确认 {counts["confirmed"]}，'
        f'其中有精确出处 {counts["with_evidence"]} 条，今天新增 {counts["created_today"]} 条。']
    if stages:
        lines += ['', '## 飞轮这一轮\n'] + [f'- {stage}' for stage in stages]
    if books or topics:
        lines += ['', '## 知识沉淀\n']
        if books:
            lines.append('- 今天更新的最佳实践：' + '、'.join(books))
        if topics:
            lines.append('- 今天重建的专题：' + '、'.join(topics))
    bad, unknown = job_health()
    lines += ['', '## 定时任务健康\n']
    if bad:
        lines.append('- 最近一次失败：' + '、'.join(bad) + '（日志在 .research/logs/）')
    if unknown:
        lines.append('- 查不到状态：' + '、'.join(unknown))
    if not bad and not unknown:
        lines.append('- 最近一次运行全部正常。')
    path = ROOT / '日报' / f'{date}-研究.md'
    research.replace(path, '\n'.join(lines) + '\n')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--date')
    args = parser.parse_args()
    print(write(args.date))


if __name__ == '__main__':
    main()
