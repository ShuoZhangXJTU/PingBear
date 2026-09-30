#!/usr/bin/env python3
"""小红书 tabris 简报：主页 → 新笔记 → 每张截图 OCR → 认论文/原帖 → 一篇一张卡片。"""
import argparse
import datetime as dt
import difflib
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo

import research

ROOT = research.ROOT
STATE = ROOT / '.research/xhs'
DIGESTS = STATE / 'digests'
SEEN = STATE / 'seen.json'
TARGET = STATE / 'target.json'
IMAGES = STATE / 'images'
TOOL_HOME = Path.home() / '.local/share/research-xhs'
FETCH = TOOL_HOME / 'xhsfetch'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
OCR_BIN = Path.home() / '.local/bin/ocr'
OCR_SWIFT = ROOT / 'scripts/ocr.swift'
TZ = ZoneInfo('Asia/Shanghai')
LOCAL_PROXY = os.environ.get('RESEARCH_PROXY', 'http://127.0.0.1:7890')
DEFAULT_TARGET = {'nickname': 'tabris 🗝', 'user_id': '60a72ded000000000101de6e',
    'xsec_token': 'ABefmD1xXh-KfJZ2Y1VsePD3nXKUTqZ9y-p5LQ5mnwc-k%3D', 'red_id': '2608032230',
    'profile_url': 'https://www.xiaohongshu.com/user/profile/60a72ded000000000101de6e'}
ARXIV_ID = re.compile(r'(?<!\d)(\d{4}\.\d{4,5})(?:v\d+)?(?!\d)')
HF_PAPER = re.compile(r'huggingface\.co/papers/(\d{4}\.\d{4,5})', re.I)


# ---------- 基础工具 ----------

def load_target():
    target = dict(DEFAULT_TARGET)
    if TARGET.exists():
        target.update(research.load(TARGET) or {})
    return target


def unwrap(value):
    if isinstance(value, dict):
        if 'value' in value:
            return value['value']
        if '_value' in value:
            return value['_value']
    return value


def find_key(node, key, depth=0):
    """在解析出的页面状态里递归找某个键（小红书改版后路径会变）。"""
    if depth > 8:
        return None
    if isinstance(node, dict):
        if node.get(key):
            return node[key]
        for value in node.values():
            found = find_key(value, key, depth + 1)
            if found:
                return found
    elif isinstance(node, list):
        for value in node[:60]:
            found = find_key(value, key, depth + 1)
            if found:
                return found
    return None


def http_get(url, data=None, timeout=25):
    """直连优先、本机代理兜底；不读环境里的代理变量，避免死代理拖垮任务。"""
    last = ''
    for proxy in (None, LOCAL_PROXY):
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({} if proxy is None else {'http': proxy, 'https': proxy}))
        request = urllib.request.Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0 LocalResearch/0.1'})
        try:
            with opener.open(request, timeout=timeout) as response:
                return response.read()
        except Exception as error:
            last = f'{proxy or "直连"}: {type(error).__name__}'
    raise RuntimeError('请求失败 ' + last)


def state_from_html(path):
    """页面内嵌 SSR 状态是 JS 不是 JSON（含 new Set([])），先做替换再解析。"""
    text = path.read_text(encoding='utf-8', errors='replace')
    start = text.find('window.__INITIAL_STATE__')
    if start < 0:
        return None
    begin = text.find('{', start)
    depth, quoted, escaped, end = 0, False, False, None
    for index in range(begin, len(text)):
        char = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    if end is None:
        return None
    raw = text[begin:end]
    raw = re.sub(r'new Set\([^)]*\)', '[]', raw)
    raw = re.sub(r'new Map\([^)]*\)', '{}', raw)
    raw = re.sub(r'\bundefined\b', 'null', raw)
    raw = re.sub(r'\bNaN\b', 'null', raw)
    try:
        return json.loads(raw)
    except ValueError:
        return None


def fetch_page(mode, ident, token, base):
    base.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, XHS_BROWSER_BIN=CHROME, TZ='Asia/Shanghai')
    result = subprocess.run([str(FETCH), mode, ident, token, str(base)], cwd=str(TOOL_HOME),
        env=env, text=True, errors='replace', capture_output=True, timeout=300)
    path = Path(str(base) + '.html')
    if result.returncode or not path.exists():
        raise RuntimeError((result.stderr or result.stdout or 'xhsfetch 失败').strip()[:400])
    return path


# ---------- 小红书页面 ----------

def cover_url(card):
    cover = card.get('cover') or {}
    for info in cover.get('infoList') or []:
        if info.get('imageScene') == 'WB_PRV' and info.get('url'):
            return info['url']
    return cover.get('urlDefault') or cover.get('url') or ''


def profile_page(target):
    path = fetch_page('profile', target['user_id'], target['xsec_token'], STATE / 'profile')
    state = state_from_html(path)
    if not state:
        raise RuntimeError('主页页面没有内嵌数据（可能触发风控或登录失效）')
    user = state.get('user') or {}
    info = unwrap(user.get('userPageData')) or {}
    pages = unwrap(user.get('notes')) or []
    notes = []
    for page in pages if isinstance(pages, list) else []:
        for item in page or []:
            card = (item or {}).get('noteCard') or {}
            if not card:
                continue
            notes.append({'id': item.get('id') or card.get('noteId'), 'title': card.get('displayTitle') or '',
                'type': card.get('type') or '', 'time': card.get('time') or 0,
                'xsec_token': item.get('xsecToken') or card.get('xsecToken') or '',
                'liked': ((card.get('interactInfo') or {}).get('likedCount') or ''), 'cover': cover_url(card)})
    return info, notes


def image_urls(image):
    pairs = [(info.get('imageScene'), info.get('url')) for info in image.get('infoList') or []]
    pick = next((url for scene, url in pairs if scene == 'WB_PRV' and url), '')
    pick = pick or next((url for scene, url in pairs if scene == 'CRD_WM_WEBP' and url), '')
    return pick or image.get('urlDefault') or image.get('url') or ''


def note_detail(note, target):
    base = STATE / 'notes' / note['id']
    path = fetch_page('note', note['id'], note.get('xsec_token') or target['xsec_token'], base)
    state = state_from_html(path)
    if not state:
        raise RuntimeError('笔记页面没有内嵌数据')
    # 小红书改版后 noteDetailMap 不在固定路径上，递归找一遍再兜底。
    detail_map = (state.get('note') or {}).get('noteDetailMap') or find_key(state, 'noteDetailMap') or {}
    for value in detail_map.values():
        if isinstance(value, dict) and value.get('note'):
            data = value['note']
            return {'id': data.get('noteId') or note['id'], 'title': data.get('title') or note.get('title') or '',
                'desc': data.get('desc') or '', 'type': data.get('type') or note.get('type') or '',
                'time': data.get('time') or note.get('time') or 0,
                'images': [u for u in (image_urls(i) for i in data.get('imageList') or []) if u]}
    raise RuntimeError('笔记详情为空')


def note_url(note_id, token):
    return f'https://www.xiaohongshu.com/explore/{note_id}?xsec_token={token}&xsec_source=pc_user'


# ---------- 截图 → 论文 ----------

def download(url, path):
    path.write_bytes(http_get(url, timeout=60))
    return path


def ocr_image(path, languages='en-US,zh-Hans'):
    command = [str(OCR_BIN), str(path), languages] if OCR_BIN.exists() else \
        ['/usr/bin/swift', str(OCR_SWIFT), str(path), languages]
    result = subprocess.run(command, text=True, errors='replace', capture_output=True, timeout=600)
    return result.stdout.strip() if result.returncode == 0 else ''


def normalize_title(text):
    return re.sub(r'[^a-z0-9]+', ' ', (text or '').lower()).strip()


def parse_arxiv(xml_bytes):
    root = ET.fromstring(xml_bytes)
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    papers = {}
    for entry in root.findall('a:entry', ns):
        ident = (entry.findtext('a:id', default='', namespaces=ns) or '').rstrip('/').split('/')[-1]
        ident = re.sub(r'v\d+$', '', ident)
        title = ' '.join((entry.findtext('a:title', default='', namespaces=ns) or '').split())
        abstract = ' '.join((entry.findtext('a:summary', default='', namespaces=ns) or '').split())
        if ident and title:
            papers[ident] = {'arxiv': ident, 'title': title, 'abstract': abstract}
    return papers


def arxiv_lookup(ids):
    if not ids:
        return {}
    url = 'https://export.arxiv.org/api/query?max_results=50&id_list=' + urllib.parse.quote(','.join(
        dict.fromkeys(ids)))
    return parse_arxiv(http_get(url))


def arxiv_search(title):
    query = 'ti:"%s"' % re.sub(r'[\"]', ' ', title)[:180]
    url = 'https://export.arxiv.org/api/query?max_results=5&search_query=' + urllib.parse.quote(query)
    try:
        return list(parse_arxiv(http_get(url)).values())
    except Exception:
        return []


def title_from_ocr(text):
    """论文截图的标题一般在最前面，取头几行里最像标题的一行。"""
    lines = [line.strip() for line in (text or '').splitlines() if line.strip()]
    for index, line in enumerate(lines[:8]):
        if index == 0 and re.match(r'^(arxiv|preprint|paper|note)', line, re.I):
            continue
        words = line.split()
        letters = sum(c.isalpha() for c in line)
        if len(words) >= 3 and letters >= 3 * len(words) and 10 <= len(line) <= 160:
            candidate = line
            if index + 1 < len(lines):
                nxt = lines[index + 1]
                if len(candidate) < 70 and len(nxt.split()) >= 3 and sum(c.isalpha() for c in nxt) >= 3 * len(nxt.split()) \
                        and len(nxt) <= 120 and not re.search(r'\d{4}', nxt):
                    candidate = candidate + ' ' + nxt
            return candidate[:200]
    return ''


def resolve_image(text):
    """返回 (arxiv id, title, abstract, how)。识别不到论文时返回 None。"""
    found = HF_PAPER.findall(text or '')
    # OCR 常把编号断行/断空格（例如 "arXiv:2609" + "11716v1"），先接回来再匹配。
    flat = re.sub(r'(\d{4})\s*[.\u3002:，,]\s*(\d{4,5})', r'\1.\2', re.sub(r'\s+', ' ', text or ''))
    flat = re.sub(r'(?<!\d)(\d{4}) (\d{4,5})(v\d)?(?!\d)', r'\1.\2\3', flat)
    if not found:
        found = [m.group(1) for m in ARXIV_ID.finditer(flat)]
    if found:
        try:
            papers = arxiv_lookup(found[:3])
        except Exception:
            papers = {}
        for ident in found:
            if ident in papers:
                return papers[ident]['arxiv'], papers[ident]['title'], papers[ident]['abstract'], 'arXiv 编号'
        candidate = title_from_ocr(text)
        if candidate:
            for hit in arxiv_search(candidate):
                if hit['arxiv'] == found[0]:
                    return hit['arxiv'], hit['title'], hit['abstract'], 'arXiv 编号（标题补全）'
        return found[0], '', '', 'arXiv 编号（未取到摘要）'
    candidate = title_from_ocr(text)
    if not candidate:
        return None
    hits = arxiv_search(candidate)
    best, score = None, 0.0
    normalized = normalize_title(candidate)
    for hit in hits:
        ratio = difflib.SequenceMatcher(None, normalized, normalize_title(hit['title'])).ratio()
        if ratio > score:
            best, score = hit, ratio
    if best and score >= 0.75:
        return best['arxiv'], best['title'], best['abstract'], f'标题检索（{score:.2f}）'
    return None


def fallback_title(text, note_title, index):
    candidate = title_from_ocr(text)
    return candidate or f'{note_title or "笔记"}（第 {index} 张截图）'


# ---------- 生成简报 ----------

def summarize(note, entries, note_ref):
    """一次调用覆盖整条笔记的所有截图，保持与 HF 简报同一口吻。"""
    schema = STATE / 'review.schema.json'
    research.replace(schema, {'type': 'object', 'properties': {'papers': {'type': 'array', 'items': {
        'type': 'object', 'properties': {
            'index': {'type': 'integer'},
            'title': {'type': 'string'},
            'summary': {'type': 'string'},
            'tags': {'type': 'array', 'items': {'type': 'string', 'enum': list(research.TAGS)}, 'minItems': 2, 'maxItems': 5}},
        'required': ['index', 'title', 'summary', 'tags'], 'additionalProperties': False}}},
        'required': ['papers'], 'additionalProperties': False})
    out = STATE / 'reviews' / (note['id'] + '.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    prompt = '''你是科研中文简报生成器。下面是一条小红书笔记里每张英文截图的 OCR 文本，以及（能查到时）它对应的 arXiv 论文标题和摘要。
请逐张给一条简报，只输出 JSON：{"papers":[{"index":1,"title":"...","summary":"...","tags":[...]}, ...]}，index 必须与输入一一对应，不要漏也不要多。
summary 只写一句日常、顺口的话，35–90 字，说清“干了什么、有什么用”，像给同事随口介绍；不要翻译腔、不要堆概念、不写机构、不写阅读依据。
这条只用来快速筛选，必须用讲给小学生听的方式：不用专业术语，用日常词、短句，一眼能看懂在干啥。
title 用论文原标题（英文原样保留）；如果这张截图不是论文（比如 blog、推文、榜单、闲聊），就用截图里最显眼的标题当 title，summary 说明这是什么内容、讲了什么。
（arXiv 元数据）里的信息比 OCR 更可靠，优先按它写；OCR 里没有的结论不要编，识别不出的细节不要猜。tags 从这个固定词表原样挑 2–5 个：''' + '、'.join(research.TAGS) + '''。
小红书笔记标题（仅供参考）：''' + (note.get('title') or '') + '\n笔记正文（仅供参考）：' + (note.get('desc') or '')[:1500] + '\n'
    log = STATE / 'logs' / (note['id'] + '-summary.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    command = [str(Path.home()/'.local/bin/codex'), 'exec', '--skip-git-repo-check', '--ephemeral',
        '--sandbox', 'read-only', '-C', str(ROOT), '-c', 'features.shell_tool=false',
        '-c', 'web_search="disabled"', '--output-schema', str(schema), '-o', str(out), '-']
    payload = [{k: v for k, v in entry.items() if k in ('index', 'resolved_title', 'abstract', 'ocr')} for entry in entries]
    with log.open('a', encoding='utf-8') as handle:
        result = subprocess.run(command, input=prompt + json.dumps(payload, ensure_ascii=False),
            text=True, stdout=handle, stderr=handle, timeout=1200)
    if result.returncode or not out.exists():
        raise RuntimeError('中文生成失败，详见 ' + str(log))
    return {int(item['index']): item for item in research.load(out)['papers']}


def collect(date, limit=8, force=False):
    target = load_target()
    info, notes = profile_page(target)
    basic = info.get('basicInfo') or {}
    if basic.get('nickname'):
        target['nickname'] = basic['nickname']
    if basic.get('redId'):
        target['red_id'] = basic['redId']
    state = research.load(SEEN) if SEEN.exists() else {'seen': []}
    seen = set(state.get('seen') or [])
    fresh = [n for n in notes if n.get('id') and (force or n['id'] not in seen)]
    fresh = sorted(fresh, key=lambda n: n.get('time') or 0, reverse=True)[:limit]
    records, failures = [], []
    for note in fresh:
        try:
            records.extend(process_note(note, target))
            seen.add(note['id'])
        except Exception as error:
            failures.append(f'{note["id"]}: {type(error).__name__} {error}')
    state['seen'] = sorted(seen)
    state['updated_at'] = dt.datetime.now(TZ).isoformat()
    if failures:
        state['last_error'] = failures[-1]
    research.replace(SEEN, state)
    research.replace(TARGET, target)
    if failures and not records:
        raise RuntimeError('；'.join(failures))
    return records, target


def process_note(note, target):
    detail = note_detail(note, target)
    link = note_url(detail['id'], note.get('xsec_token') or target['xsec_token'])
    note_dir = IMAGES / detail['id']
    note_dir.mkdir(parents=True, exist_ok=True)
    shots = []
    for index, url in enumerate(detail['images'][:15], 1):
        path = note_dir / f'{index:02d}.jpg'
        try:
            download(url, path)
            text = ocr_image(path)
        except Exception as error:
            shots.append({'index': index, 'url': url, 'file': str(path), 'ocr': '',
                'error': f'{type(error).__name__}'})
            continue
        shots.append({'index': index, 'url': url, 'file': str(path), 'ocr': text, 'error': ''})

    pages = [shot for shot in shots if shot['ocr'].strip()]
    by_id = {}
    for shot in pages:
        shot['found'] = resolve_image(shot['ocr'])
        if shot['found'] and shot['found'][0] not in by_id:
            by_id[shot['found'][0]] = shot
    entries = []
    seen_titles = {}
    for shot in pages:
        found = shot['found']
        if found and by_id.get(found[0]) is not shot:
            continue  # 同一篇论文出现在多张截图里，只留信息最全的那张
        # 认不出 arXiv 的截图（比如封面页/同一篇的续页）按标题去重，避免一条笔记刷出一堆重复
        title_key = re.sub(r'[^a-z0-9\u4e00-\u9fff]+', '', (found[1] if found else '') .lower()
            or re.sub(r'[^a-z0-9\u4e00-\u9fff]+', '', (shot['ocr'][:80]).lower()))
        if len(title_key) > 12:
            if title_key in seen_titles:
                continue
            seen_titles[title_key] = shot['index']
        entries.append({'index': shot['index'], 'shot': shot,
            'arxiv': found[0] if found else '', 'resolved_title': found[1] if found else '',
            'abstract': found[2] if found else '', 'how': found[3] if found else '',
            'ocr': shot['ocr'][:6000]})
    for shot in pages:
        shot.pop('found', None)
    if not entries:
        return []
    reviews = summarize(detail, entries, link)
    records = []
    for entry in entries:
        review = reviews.get(entry['index'], {})
        tags = [t for t in review.get('tags', []) if t in research.TAGS][:5]
        if len(tags) < 2:
            tags = list(dict.fromkeys(tags + ['其他']))[:2]
        arxiv = entry['arxiv']
        title = review.get('title') or entry['resolved_title'] or fallback_title(entry['ocr'], detail['title'], entry['index'])
        ident = arxiv if arxiv else f'xhs-{detail["id"]}-{entry["index"]}'
        notes_link = link
        records.append({
            'id': ident,
            'source': 'xiaohongshu',
            'author': target.get('nickname'),
            'note_id': detail['id'],
            'note_title': detail['title'],
            'note_url': notes_link,
            'shot_index': entry['index'],
            'title': title,
            'summary': review.get('summary', ''),
            'tags': tags,
            'arxiv': arxiv,
            'url': f'https://arxiv.org/abs/{arxiv}' if arxiv else notes_link,
            'pdf': f'https://arxiv.org/pdf/{arxiv}' if arxiv else '',
            'matched_by': entry['how'],
            'images': [{'url': entry['shot']['url'], 'file': entry['shot']['file']}],
            'ocr': entry['ocr'],
            'published_at': dt.datetime.fromtimestamp((detail.get('time') or 0)/1000, TZ).isoformat() if detail.get('time') else '',
        })
    return records


# ---------- 输出 ----------

def card(record):
    tags = ' '.join('#' + t for t in record.get('tags', []))
    links = []
    if record.get('arxiv'):
        links.append(f"[论文]({record['url']})")
        links.append(f"[PDF]({record['pdf']})")
    links.append(f"[原帖]({record['note_url']})")
    links.append(f"[归档](obsidian://research-archive?date={record['date']}&id={record['id']})")
    origin = f"来自 tabris 的笔记《{record.get('note_title') or ''}》第 {record.get('shot_index')} 张截图"
    return f"{record['summary']}\n\n{tags}\n\n" + ' · '.join(links) + f"\n\n<sub>{origin}</sub>\n"


def latest(date):
    return DIGESTS / f'{date}.json'


def render(date, records, target):
    for record in records:
        record['date'] = date
    path = ROOT / '日报' / f'{date}-小红书.md'
    lines = [f'---\ndate: {date}\ntype: xhs-digest\nsource: xiaohongshu\n---\n\n',
        f'# {date} 小红书 · {target.get("nickname","tabris")}\n\n',
        f'共 {len(records)} 条\n\n']
    for number, record in enumerate(records, 1):
        lines.append(f'## X{number}. [{record["title"]}]({record["url"]})\n\n')
        lines.append(card(record) + '\n')
    if not records:
        lines.append('今天没有新内容。\n')
    research.replace(path, ''.join(lines))
    research.replace(latest(date), {'date': date, 'source': 'xiaohongshu', 'author': target.get('nickname'),
        'style_version': 2, 'papers': [dict(record, number=number) for number, record in enumerate(records, 1)]})
    return path


def run(date, force=False, limit=8):
    records, target = collect(date, limit=limit, force=force)
    existing = research.load(latest(date)) if latest(date).exists() else {}
    if not records and existing.get('papers'):
        records = existing['papers']
    path = render(date, records, target)
    print(f'小红书 {target.get("nickname")}: {len(records)} 条 -> {path}')
    return path


def history(limit=20, scrolls=14):
    """冷启动：把主页带 xsec_token 的笔记逐条补成对应日期的 小红书 分栏。

    注：滚动加载拿到的老笔记链接里没有 xsec_token（小红书现在的列表 DOM 不带），
    所以这里用主页内嵌数据里那批（约 31 条，覆盖数月到一年）向前补。
    """
    target = load_target()
    _, notes = profile_page(target)
    state = research.load(SEEN) if SEEN.exists() else {'seen': []}
    seen = set(state.get('seen') or [])
    done = set(state.get('processed') or [])
    fresh = [note for note in notes if note.get('xsec_token') and note['id'] not in done][:limit]
    print(f'主页可处理 {len(notes)} 条，已补 {len(done)} 条，本次处理 {len(fresh)} 条', flush=True)
    by_date = {}
    for note in fresh:
        try:
            records = process_note({'id': note['id'], 'title': note.get('title', ''),
                'xsec_token': note.get('token') or target['xsec_token'], 'type': '', 'time': 0}, target)
        except Exception as error:
            print(f'  失败 {note["id"]}: {type(error).__name__} {error}', flush=True)
            continue
        for record in records:
            day = (record.get('published_at') or dt.datetime.now(TZ).date().isoformat())[:10]
            by_date.setdefault(day, []).append(record)
        seen.add(note['id'])
        done.add(note['id'])
        print(f'  已处理 {note["id"]}（{note.get("title","")[:24]}）→ {len(records)} 条', flush=True)
        state['seen'] = sorted(seen)
        state['processed'] = sorted(done)
        state['updated_at'] = dt.datetime.now(TZ).isoformat()
        research.replace(SEEN, state)
    for day, records in sorted(by_date.items()):
        path = DIGESTS / f'{day}.json'
        merged = {}
        if path.exists():
            for record in research.load(path).get('papers') or []:
                merged[record['id']] = record
        for record in records:
            merged.setdefault(record['id'], record)
        render(day, list(merged.values()), target)
        print(f'  写回 {day}：{len(merged)} 条', flush=True)
    print(f'历史补跑完成：{len(fresh)} 条笔记 → {len(by_date)} 天', flush=True)
    return by_date


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['run'], nargs='?', default='run')
    parser.add_argument('--date', type=research.valid_date)
    parser.add_argument('--force', action='store_true', help='重新处理已见过的笔记')
    parser.add_argument('--limit', type=int, default=8, help='本次最多处理几条笔记')
    parser.add_argument('--history', action='store_true', help='冷启动：滚动加载历史笔记')
    parser.add_argument('--scrolls', type=int, default=14)
    args = parser.parse_args()
    date = args.date or dt.datetime.now(TZ).date().isoformat()
    STATE.mkdir(parents=True, exist_ok=True)
    if args.history:
        history(limit=args.limit if args.limit != 8 else 20, scrolls=args.scrolls)
    else:
        run(date, force=args.force, limit=args.limit)


if __name__ == '__main__':
    main()
