#!/usr/bin/env python3
"""把历史补跑版日报里「只有标题没有简介」的论文逐天补全（可中断、可重复运行）。"""
import argparse
import sys
import time

import research

ROOT = research.ROOT
DIGESTS = ROOT / '.research/digests'


def pending_days():
    days = []
    for path in sorted(DIGESTS.glob('*.json')):
        try:
            data = research.load(path)
        except Exception:
            continue
        if not data.get('backfill'):
            continue
        if any(paper.get('lite') for paper in data.get('papers', [])):
            days.append(path.stem)
    return days


def fill(date):
    import backfill
    for attempt in range(3):
        summarized, total = backfill.backfill_day(date, full=True, force=(attempt == 0))
        data = research.load(DIGESTS / f'{date}.json')
        lite = sum(1 for paper in data['papers'] if paper.get('lite'))
        print(f'{date} 第 {attempt + 1} 轮：新增简介 {summarized} 篇，剩余 {lite} 篇', flush=True)
        if lite == 0:
            return True
        time.sleep(5)
    return False


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    days = pending_days()
    print(f'待补全 {len(days)} 天：{days[:5]} …', flush=True)
    done = 0
    for date in days:
        try:
            if fill(date):
                done += 1
        except Exception as error:
            print(f'{date} 失败：{type(error).__name__} {error}', flush=True)
    print(f'完成 {done}/{len(days)} 天', flush=True)
    try:
        import catalog
        catalog.build()
        import research as r
        r.build_index(ROOT)
    except Exception:
        pass


if __name__ == '__main__':
    main()
