#!/usr/bin/env python3
"""补齐 HF 日报里缺的论文。

HF 的「某天的列表」不是一次给全的，它在那一天里陆续发布：10-15 早上只抓到 7 篇，
当天下午同一接口已经 44 篇。所以当天的日报只能算初版，之后要再补。

本脚本对最近几天重新抓取，只给「新出现的」和「摘要变了的」论文写中文简介，再按原有
编号追加进当天的日报——已经发布的编号、你做过的归档和备注都不动（publish --update
会保留旧条目，只把新条目排在后面）。

  python3 scripts/settle.py                 # 补齐今天和昨天
  python3 scripts/settle.py --days 3        # 最近三天
  python3 scripts/settle.py --date 2026-10-14
  python3 scripts/settle.py --dry-run       # 只看差多少，不写任何东西
"""
import argparse
import datetime as dt
import fcntl
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import morning
import research

ROOT = research.ROOT
STATE = ROOT / '.research'
BATCH = 12


def digest_papers(day):
    path = STATE / 'digests' / (day + '.json')
    return research.load(path)['papers'] if path.exists() else []


def candidate_papers(day):
    path = STATE / 'candidates' / (day + '.json')
    return research.load(path)['papers'] if path.exists() else []


def summarize_batch(papers, day, collect):
    """给一批论文写简介，累积到 collect 里；返回这一批没写成功的 id。"""
    path = morning.summarize(papers, day, tolerant=True, name='.topup')
    for paper in research.load(path)['papers']:
        collect[paper['id']] = paper
    return [p['id'] for p in papers if p['id'] not in collect]


def settle_day(day, dry_run=False):
    if not (STATE / 'digests' / (day + '.json')).exists():
        print(f'{day}: 还没有正式日报，跳过（历史补跑由 backfill 负责）', flush=True)
        return 0
    research.collect(SimpleNamespace(date=day, input=None, refresh=True), ROOT)
    papers = candidate_papers(day)
    published = {p['id']: p for p in digest_papers(day)}
    def fingerprint(paper):
        return (paper.get('title'), paper.get('abstract'))
    pending = [p for p in papers if p['id'] not in published
        or fingerprint(p) != fingerprint(published[p['id']])]
    if not pending:
        print(f'{day}: 没有新增（接口 {len(papers)} 篇，日报 {len(published)} 篇）', flush=True)
        return 0
    if dry_run:
        print(f'{day}: 待补 {len(pending)} 篇（接口 {len(papers)} 篇，日报 {len(published)} 篇）', flush=True)
        return len(pending)
    reviews = {}
    for start in range(0, len(pending), BATCH):
        summarize_batch(pending[start:start + BATCH], day, reviews)
    missed = [p for p in pending if p['id'] not in reviews]
    if missed:  # 模型偶尔漏篇：再试一轮，还漏就让 publish 拒绝发布，日报保持原样
        summarize_batch(missed, day, reviews)
    review_file = STATE / 'reviews' / (day + '.topup.json')
    research.replace(review_file, {'papers': list(reviews.values())})
    research.publish(SimpleNamespace(date=day, reviews=str(review_file), update=True), ROOT)
    print(f'{day}: 补入 {len(pending)} 篇 → 日报共 {len(papers)} 篇', flush=True)
    return len(pending)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--date', action='append', help='指定日期（可重复）；默认最近 N 天')
    parser.add_argument('--days', type=int, default=2, help='默认补齐最近几天，含今天（默认 2）')
    parser.add_argument('--dry-run', action='store_true', help='只统计差多少，不写文件')
    args = parser.parse_args()
    today = dt.date.today()
    days = args.date or [(today - dt.timedelta(days=offset)).isoformat() for offset in range(args.days)]
    total = 0
    for day in sorted(days):
        try:
            total += settle_day(day, args.dry_run) or 0
        except Exception as error:
            print(f'{day}: 补齐失败 {type(error).__name__} {error}', flush=True)
    if not args.dry_run:
        stamps = [p.stem for p in (STATE / 'digests').glob('*.json') if len(p.stem) == 10]
        if total and stamps:
            morning.homepage(today.isoformat(), max(stamps))
            print(f'今日简报已刷新（数据日期 {max(stamps)}）', flush=True)
            try:
                import catalog
                research.build_index(ROOT)
                catalog.build()
            except Exception as error:
                print(f'目录索引刷新失败 {type(error).__name__} {error}', flush=True)


if __name__ == '__main__':
    STATE.mkdir(exist_ok=True)
    # 和早报任务共用一把锁：早报正在跑（它自己会重抓补齐）时就不重复抓一遍。
    with (STATE / 'morning.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('早报任务正在运行，本次补齐跳过', flush=True)
        else:
            main()
