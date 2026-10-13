#!/usr/bin/env python3
"""上午检查小红书有没有新笔记（半夜早报之后发的也算）。

有新笔记 → 立刻处理进当天日报并推送；抓取失败（登录过期/风控）→ PushPlus 告警。
"""
import datetime as dt
import sys

import research
import xhs

TZ = dt.timezone(dt.timedelta(hours=8))


def main():
    today = dt.datetime.now(TZ).date().isoformat()
    try:
        info, notes = xhs.profile_page(xhs.load_target())
    except Exception as error:
        try:
            import alert
            alert.send(f'⚠️ 小红书抓取失败：{type(error).__name__}: {error}\n'
                '多半是登录态过期，回我一句「重登小红书」我给你弹扫码。',
                key='xhs-check:' + today)
        except Exception:
            pass
        print('抓取失败:', type(error).__name__, error, flush=True)
        return 1
    seen = set(research.load(xhs.SEEN).get('seen', [])) if xhs.SEEN.exists() else set()
    fresh = [note for note in notes if note['id'] not in seen]
    print(f'主页 {len(notes)} 条，其中新笔记 {len(fresh)} 条', flush=True)
    if not fresh:
        return 0
    xhs.run(today, limit=12)
    try:
        import notify
        path = xhs.latest(today)
        count = len(research.load(path)['papers']) if path.exists() else len(fresh)
        notify.send(f'小红书更新 · {dt.date.fromisoformat(today).month}月{dt.date.fromisoformat(today).day}日',
            f'tabris 发了 {len(fresh)} 条新笔记，已处理 {count} 条进当天日报。\n\n'
            '打开 Obsidian 的「今日简报」→ 小红书那一段，或直接看 日报/<日期>-小红书.md。')
    except Exception as error:
        print('推送失败:', type(error).__name__, error, flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
