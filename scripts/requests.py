#!/usr/bin/env python3
"""处理来自手机（或任何设备）的请求队列。

手机端 Obsidian 点「提问 / 归档问答 / 记一条灵感」时，插件会在
.research/requests/ 写一个 JSON 请求；iCloud 同步到本机后，这个脚本执行它，
并把结果写进 .research/responses/<id>.json 与对应的笔记（问答/<id>.md、灵感/收件箱.md），
手机同步后即可看到。
"""
import argparse
import datetime as dt
import json
import sys
import traceback
from pathlib import Path
from zoneinfo import ZoneInfo

import research

ROOT = research.ROOT
QUEUE = ROOT / '.research/requests'
DONE = ROOT / '.research/responses'
TZ = ZoneInfo('Asia/Shanghai')


def handle(request):
    action = request.get('action')
    if action == 'ask':
        import knowledge
        data = knowledge.ask(request['id'], request['question'])
        return {'answer': data.get('answer', ''), 'point': data.get('point', ''),
            'confidence': data.get('confidence', ''), 'note': f"问答/{request['id']}.md"}
    if action == 'idea':
        import ideas
        ideas.capture(request.get('text', ''))
        return {'saved': request.get('text', ''), 'note': '灵感/收件箱.md'}
    if action == 'library':
        import library
        if request.get('mode') == 'search':
            hits = library.search(request.get('text', ''), limit=8)
            return {'hits': [{'title': hit['title'], 'path': hit['path'], 'score': hit['score']} for hit in hits]}
        data, _hits = library.ask(request.get('text', ''))
        return {'answer': data.get('answer', ''), 'gaps': data.get('gaps', ''), 'note': '问答/知识助手.md'}
    if action in ('inbox', 'process-inbox'):
        import inbox
        if action == 'process-inbox':
            _, count = inbox.process(dt.datetime.now(TZ).date().isoformat())
            return {'processed': count, 'note': '日报/<日期>-我的链接.md'}
        urls = request.get('urls') or []
        body = inbox.INBOX.read_text(encoding='utf-8') if inbox.INBOX.exists() else inbox.INBOX_TEMPLATE
        added = [url for url in urls if url not in body]
        body = body.rstrip('\n') + '\n' + '\n'.join(added) + '\n'
        research.replace(inbox.INBOX, body)
        return {'added': added, 'note': '收件箱/我的链接.md'}
    if action == 'deepen':
        import knowledge
        knowledge.deepen([request['id']], force=True)
        return {'done': request['id']}
    if action == 'rebuild':
        import knowledge
        return {'topics': knowledge.rebuild()}
    if action == 'catalog':
        import catalog
        catalog.build()
        return {'note': '索引/目录.md'}
    raise ValueError('未知请求: ' + str(action))


def process():
    QUEUE.mkdir(parents=True, exist_ok=True)
    DONE.mkdir(parents=True, exist_ok=True)
    count = 0
    for path in sorted(QUEUE.glob('*.json')):
        try:
            request = research.load(path)
        except Exception:
            continue
        result = {'id': path.stem, 'action': request.get('action'), 'at': dt.datetime.now(TZ).isoformat()}
        try:
            result.update({'ok': True, 'result': handle(request)})
            count += 1
            print(f"完成 {request.get('action')}: {path.stem}", flush=True)
        except Exception as error:
            result.update({'ok': False, 'error': f'{type(error).__name__}: {error}',
                'trace': traceback.format_exc()[-800:]})
            print(f"失败 {request.get('action')}: {path.stem} {error}", flush=True)
        research.replace(DONE / path.name, result)
        path.unlink()
    if not count:
        print('没有待处理请求', flush=True)
    return count


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    process()


if __name__ == '__main__':
    main()
