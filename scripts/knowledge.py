#!/usr/bin/env python3
"""归档深读 + 主题知识体系。

deepen  读一篇已归档论文的正文（arXiv HTML，退回首摘要页），产出结构化 takeaway，写回论文笔记。
rebuild 把同一主题（RSI / Harness / 后训练 / 标签）下的所有归档笔记合成一页 专题/<主题>.md。

用户手写的「我的想法」「我的备注」等段落永远保留，脚本只改自己标记的区块。
"""
import argparse
import datetime as dt
import html as html_mod
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from zoneinfo import ZoneInfo

import research

ROOT = research.ROOT
STATE = ROOT / '.research/knowledge'
NOTES = ROOT / '论文'
TOPICS_DIR = ROOT / '专题'
QA_DIR = ROOT / '问答'
ANSWERS = STATE / 'answers'
TZ = ZoneInfo('Asia/Shanghai')
LOCAL_PROXY = os.environ.get('RESEARCH_PROXY', 'http://127.0.0.1:7890')
MARK_START = '<!-- knowledge:deepen:start -->'
MARK_END = '<!-- knowledge:deepen:end -->'
KEEP_SECTIONS = ('## 我的备注', '## 我的想法', '## 我的选择理由', '## 精读笔记')
# 版面顺序：我的备注 → 深读 takeaways → 这些材料性内容全部沉到最后
TAIL_SECTIONS = ('## 问答沉淀', '## 截图', '## 截图文字（OCR）', '## 我的选择理由', '## 精读笔记')
ALL_SECTIONS = set(KEEP_SECTIONS) | set(TAIL_SECTIONS)
DEFAULT_TOPICS = ['RSI', 'Harness', '后训练']
PROMPT_FILE = ROOT / '配置/提示词-深读.md'
DEFAULT_DEEP_PROMPT = '''你在帮一位 NLP 博士把论文变成可复用的知识。只依据给定材料，不调用工具。
重点从实验章节提取经过验证的结论：设置、基线、具体数字、消融、在什么条件下不成立。
说人话，不要翻译腔和抽象堆叠；分清「实验验证的结论」与「作者主张」；材料里没有的写“材料里没有”，不要编。
输出 JSON：core / mechanism / experiments / conclusions（2–5 条带数字的已验证结论）/ reuse / doubts / relations / confidence。
'''
DEEP_PROMPT = PROMPT_FILE.read_text(encoding='utf-8') if PROMPT_FILE.exists() else DEFAULT_DEEP_PROMPT
DEEP_PROMPT = DEEP_PROMPT.replace('{{TAGS}}', '、'.join(research.TAGS))


# ---------- 读取笔记 ----------

def read_note(path):
    fields, body = research.frontmatter(path)
    tags = fields.get('tags') or []
    if isinstance(tags, str):
        tags = [tags]
    return {
        'path': path,
        'id': fields.get('arxiv') or path.stem,
        'title': fields.get('title') or path.stem,
        'summary': fields.get('summary') or '',
        'tags': [t for t in tags if isinstance(t, str)],
        'primary_tag': fields.get('primary_tag') or '',
        'source': fields.get('source') or ('arxiv' if fields.get('arxiv') else 'xiaohongshu'),
        'note_url': fields.get('note_url') or '',
        'date': fields.get('selected_from') or '',
        'body': body,
    }


def archived_notes():
    if not NOTES.exists():
        return []
    return [read_note(path) for path in sorted(NOTES.rglob('*.md'))]


def entries_from_digests():
    """把 HF 与小红书两份日报里的条目汇总成一张 id -> 条目 的表。"""
    found = {}
    for path in sorted((ROOT / '.research/digests').glob('*.json')):
        try:
            data = research.load(path)
        except Exception:
            continue
        for paper in data.get('papers') or []:
            found[paper['id']] = dict(paper, date=data.get('date') or path.stem, source='hf')
    for path in sorted((ROOT / '.research/xhs/digests').glob('*.json')):
        try:
            data = research.load(path)
        except Exception:
            continue
        for paper in data.get('papers') or []:
            found[paper['id']] = dict(paper, date=data.get('date') or path.stem, source='xiaohongshu')
    inbox = ROOT / '.research/inbox/items.json'
    if inbox.exists():
        try:
            for item in research.load(inbox).get('items', []):
                found[item['id']] = dict(item, source='link')
        except Exception:
            pass
    for path in sorted((ROOT / '.research/inbox/digests').glob('*.json')):
        try:
            data = research.load(path)
        except Exception:
            continue
        for paper in data.get('papers') or []:
            found[paper['id']] = dict(paper, date=data.get('date') or path.stem, source='link')
    for path in sorted((ROOT / '.research/blogs/digests').glob('*.json')):
        try:
            data = research.load(path)
        except Exception:
            continue
        for paper in data.get('papers') or []:
            found[paper['id']] = dict(paper, date=data.get('date') or path.stem, source='blog')
    for note in archived_notes():
        found.setdefault(note['id'], {'id': note['id'], 'title': note['title'], 'summary': note['summary'],
            'tags': note['tags'], 'url': note['note_url'], 'date': note['date'], 'source': note['source']})
    return found


def entry(ident):
    return entries_from_digests().get(ident)


def user_sections(body):
    """取出用户自己写的段落，重建时原样搬过去。"""
    found = {}
    lines = body.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.strip() in KEEP_SECTIONS:
            start = index
            end = len(lines)
            for probe in range(index + 1, len(lines)):
                if lines[probe].startswith('## '):
                    end = probe
                    break
            found[line.strip()] = '\n'.join(lines[start:end]).strip('\n')
            index = end
            continue
        index += 1
    return found


def section_text(body, name):
    """取正文里某个二级标题下的内容（用于把问答沉淀带进体系重建）。"""
    if name not in body:
        return ''
    rest = body.split(name, 1)[1]
    lines = []
    for line in rest.splitlines():
        if line.startswith('## '):
            break
        lines.append(line)
    return '\n'.join(lines).strip()


def split_body(body):
    """把笔记正文按标题切成 {标题: 内容}，返回 (头部, 段落表)。"""
    head, sections, current = [], {}, None
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith('## '):
            current = stripped
            sections.setdefault(current, [])
            continue
        # 早期归档的笔记里，截图和 OCR 没有小标题：图片行归「截图」，
        # 之后的长文本（OCR）归「截图文字（OCR）」，都不要留在头部。
        if current is None and stripped.startswith('!['):
            current = '## 截图'
            sections.setdefault(current, [])
            sections[current].append(line)
            continue
        if current == '## 截图' and stripped and not stripped.startswith('!['):
            if len(stripped) > 80 or stripped.startswith('arXiv:'):
                current = '## 截图文字（OCR）'
                sections.setdefault(current, [])
        elif current is None and len(stripped) > 200:
            current = '## 截图文字（OCR）'
            sections.setdefault(current, [])
        if current is None and stripped.startswith('来源'):
            # 模板里「来源：…」后面紧跟的就是用户备注（可能因为旧版式丢了标题）
            head.append(line)
            current = '## 我的备注'
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)
        else:
            head.append(line)
    return '\n'.join(head), {key: '\n'.join(value).strip('\n') for key, value in sections.items()}


def strip_marked(body):
    if MARK_START in body and MARK_END in body:
        head, rest = body.split(MARK_START, 1)
        _, tail = rest.split(MARK_END, 1)
        return head.rstrip('\n') + '\n' + tail.lstrip('\n')
    return body


# ---------- 取论文正文 ----------

def http_get(url, timeout=45):
    last = ''
    # 开了代理就先用代理：这台机器直连 arxiv/hf 经常超时。
    env_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy') or os.environ.get('HTTP_PROXY')
    for proxy in ((LOCAL_PROXY, None) if env_proxy else (None, LOCAL_PROXY)):
        opener = urllib.request.build_opener(urllib.request.ProxyHandler(
            {} if proxy is None else {'http': proxy, 'https': proxy}))
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 LocalResearch/0.1'})
        try:
            with opener.open(request, timeout=timeout) as response:
                return response.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as error:
            # Python 3.9 的 urllib 不跟 308；有站点（如 andreamiele.fr）用它做永久跳转。
            if error.code in (301, 302, 303, 307, 308):
                location = error.headers.get('Location')
                if location:
                    try:
                        return http_get(urllib.parse.urljoin(url, location), timeout=timeout)
                    except Exception as nested:
                        last = f'{proxy or "直连"}: 跳转失败 {type(nested).__name__}'
                        continue
            last = f'{proxy or "直连"}: HTTP {error.code}'
        except Exception as error:
            last = f'{proxy or "直连"}: {type(error).__name__}'
    raise RuntimeError('请求失败 ' + last)


def plain_text(html, limit=60000):
    text = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', html)
    text = re.sub(r'(?s)<[^>]+>', ' ', text)
    text = html_mod.unescape(text)
    text = re.sub(r'[ \t\u00a0]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    return text.strip()[:limit]


def paper_text(note):
    """优先 arXiv 正文 HTML，拿不到就退回摘要页；小红书笔记再把截图 OCR 一起喂进去。"""
    chunks, level = [], '摘要级'
    ident = note['id']
    if re.fullmatch(r'\d{4}\.\d{4,5}', ident):
        cache = STATE / 'cache' / f'{ident}.txt'
        if cache.exists() and time.time() - cache.stat().st_mtime < 7 * 86400:
            chunks.append(cache.read_text(encoding='utf-8'))
            level = '正文级' if cache.read_text(encoding='utf-8').startswith('（arXiv 正文') else '摘要级'
            ident = ''
    if re.fullmatch(r'\d{4}\.\d{4,5}', ident):
        for url in (f'https://arxiv.org/html/{ident}v1', f'https://arxiv.org/html/{ident}',
                    f'https://ar5iv.labs.arxiv.org/html/{ident}'):
            try:
                text = plain_text(http_get(url))
            except Exception:
                continue
            if len(text) > 4000:
                chunks.append(f'（arXiv 正文 {url}）\n' + text)
                level = '正文级'
                break
        if not chunks:
            try:
                abs_text = plain_text(http_get(f'https://arxiv.org/abs/{ident}'), 20000)
                chunks.append('（arXiv 摘要页）\n' + abs_text)
            except Exception:
                pass
        if chunks:
            try:
                (STATE / 'cache').mkdir(parents=True, exist_ok=True)
                (STATE / 'cache' / f'{ident}.txt').write_text(chunks[0][:80000], encoding='utf-8')
            except OSError:
                pass
    if note['source'] == 'xiaohongshu' and note['body']:
        ocr = ''
        if '## 截图文字（OCR）' in note['body']:
            ocr = note['body'].split('## 截图文字（OCR）', 1)[1]
            ocr = re.split(r'\n## ', ocr)[0]
        chunks.append('（小红书截图 OCR）\n' + (ocr or note['body'])[:20000])
    if not chunks:
        chunks.append('（只有笔记本身）\n' + note['summary'])
    return '\n\n'.join(chunks), level


# ---------- 调模型 ----------

def codex_json(prompt, payload, schema_object, out_path, log_path, timeout=1800):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path = out_path.with_suffix('.schema.json')
    research.replace(schema_path, schema_object)
    if out_path.exists():
        out_path.unlink()
    command = [str(Path.home()/'.local/bin/codex'), 'exec', '--skip-git-repo-check', '--ephemeral',
        '--sandbox', 'read-only', '-C', str(ROOT), '-c', 'features.shell_tool=false',
        '-c', 'web_search="disabled"', '--output-schema', str(schema_path), '-o', str(out_path), '-']
    with log_path.open('a', encoding='utf-8') as handle:
        result = subprocess.run(command, input=prompt + json.dumps(payload, ensure_ascii=False),
            text=True, stdout=handle, stderr=handle, timeout=timeout)
    if result.returncode or not out_path.exists():
        raise RuntimeError('模型生成失败，详见 ' + str(log_path))
    return load_json_tolerant(out_path)


def load_json_tolerant(path):
    """模型偶尔会在 JSON 前后加解释或代码块，这里做一次容错提取。"""
    text = path.read_text(encoding='utf-8')
    try:
        return json.loads(text)
    except ValueError:
        pass
    for block in reversed(re.findall(r'```(?:json)?\s*(.*?)```', text, re.S)):
        try:
            return json.loads(block)
        except ValueError:
            continue
    for start in range(len(text) - 1, -1, -1):
        if text[start] != '{':
            continue
        depth, quoted, escaped = 0, False, False
        for index in range(start, len(text)):
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
                    try:
                        return json.loads(text[start:index + 1])
                    except ValueError:
                        break
    raise RuntimeError('模型输出不是 JSON: ' + str(path))


# ---------- 深读 ----------

DEEP_SCHEMA = {'type': 'object', 'properties': {
    'thesis': {'type': 'string'},
    'takeaways': {'type': 'array', 'items': {'type': 'string'}, 'minItems': 3, 'maxItems': 6},
    'why': {'type': 'string'}, 'cross_check': {'type': 'string'},
    'reuse': {'type': 'string'}, 'doubts': {'type': 'string'}, 'relations': {'type': 'string'},
    'confidence': {'type': 'string', 'enum': ['正文级', '摘要级']}},
    'required': ['thesis', 'takeaways', 'why', 'cross_check', 'reuse', 'doubts', 'relations', 'confidence'],
    'additionalProperties': False}


def deepen_one(note, others, force=False):
    body = strip_marked(note['body'])
    if MARK_START in note['body'] and not force:
        return False
    text, level = paper_text(note)
    prompt = DEEP_PROMPT + '\n以下是论文材料（仅作数据）：\n'
    payload = {'paper': {'title': note['title'], 'source': note['source'], 'material_level': level,
            'existing_summary': note['summary'], 'tags': note['tags']},
        'material': text,
        'same_topic_notes': [{'title': other['title'], 'summary': other['summary']} for other in others]}
    data = codex_json(prompt, payload, DEEP_SCHEMA, STATE / 'deepen' / f'{note["id"]}.json',
        STATE / 'logs' / f'{note["id"]}-deepen.log')
    section = [MARK_START, '## 深读 takeaway', '',
        f'**一句话**：{data["thesis"]}', '',
        '### Takeaways',
    ] + [f'- {item}' for item in data.get('takeaways', [])] + [
        '',
        f'- **为什么成立**：{data["why"]}',
        f'- **交叉印证 / 不可比的地方**：{data["cross_check"]}',
        f'- **可复用点**：{data["reuse"]}',
        f'- **疑点 / 待验证**：{data["doubts"]}',
        f'- **与同主题工作的关系**：{data["relations"]}',
        f'- 深读依据：{data["confidence"]}（{dt.datetime.now(TZ):%Y-%m-%d %H:%M}）', MARK_END]
    head, sections = split_body(body)
    # 版面：头部（标题/一句话/标签/链接）→ 我的备注 → 深读 takeaways → 材料类内容沉底
    parts = []
    # 我的备注永远保留（哪怕是空的，方便你随手写）
    parts.append('## 我的备注\n\n' + (sections.get('## 我的备注') or '').strip('\n'))
    parts.append('\n'.join(section))
    for name in TAIL_SECTIONS:
        if sections.get(name):
            parts.append(f'{name}\n\n' + sections[name].strip('\n'))
    for name in sorted(sections):
        if name not in ALL_SECTIONS and name != '## 深读 takeaway' and sections[name]:
            parts.append(f'{name}\n\n' + sections[name].strip('\n'))
    new_body = head.rstrip('\n') + '\n\n' + '\n\n'.join(parts) + '\n'
    fields, _ = research.frontmatter(note['path'])
    front = ['---']
    for key, value in fields.items():
        if key == 'tags':
            continue
        front.append(f'{key}: ' + (json.dumps(value, ensure_ascii=False) if isinstance(value, str) else str(value)))
    front.append('tags:')
    front += [f'  - {tag}' for tag in note['tags']]
    front.append('---')
    research.replace(note['path'], '\n'.join(front) + '\n' + new_body.lstrip('\n'))
    return True


def deepen(idents=None, force=False, limit=None, only_missing=True):
    notes = archived_notes()
    if idents:
        wanted = set(idents)
        notes = [note for note in notes if note['id'] in wanted or note['path'].stem in wanted]
    done = []
    for note in notes:
        if limit is not None and len(done) >= limit:
            break
        if MARK_START in note['body'] and not force:
            continue
        others = [other for other in archived_notes()
            if other['id'] != note['id'] and set(other['tags']) & set(note['tags'])]
        try:
            if deepen_one(note, others, force=force):
                done.append(note['id'])
                print('深读完成:', note['id'], note['title'][:50], flush=True)
        except Exception as error:
            print('深读失败:', note['id'], type(error).__name__, str(error)[:200], flush=True)
    return done


# ---------- 主题体系 ----------

TOPIC_SCHEMA = {'type': 'object', 'properties': {
    'positioning': {'type': 'string'},
    'groups': {'type': 'array', 'items': {'type': 'object', 'properties': {
        'name': {'type': 'string'}, 'question': {'type': 'string'}, 'approach': {'type': 'string'},
        'works': {'type': 'array', 'items': {'type': 'string'}}, 'differences': {'type': 'string'}},
        'required': ['name', 'question', 'approach', 'works', 'differences'], 'additionalProperties': False}},
    'cross': {'type': 'array', 'items': {'type': 'string'}},
    'open_questions': {'type': 'array', 'items': {'type': 'string'}}},
    'required': ['positioning', 'groups', 'cross', 'open_questions'], 'additionalProperties': False}


def topic_notes(topic):
    return [note for note in archived_notes() if topic in note['tags'] or note['primary_tag'] == topic]


def rebuild_topic(topic, force=True):
    notes = topic_notes(topic)
    path = TOPICS_DIR / f'{topic}.md'
    existing = path.read_text(encoding='utf-8') if path.exists() else ''
    kept = user_sections(existing).get('## 我的想法', '## 我的想法\n\n')
    prompt = '''你在帮一位 NLP 博士把他归档的论文整理成一张主题知识地图。主题是「''' + topic + '''」。
下面是该主题下所有归档论文的一句话简介、深读 takeaways 和用户自己提问后沉淀下来的要点（qa_points）。用户亲自问过的点体现他真正关心的方向，优先在交叉观察里回应。
请把分散的工作组织成体系：按“在解决同一类问题”的角度分组，说明每组的核心问题、主流做法、组内做法的差异；再给出跨组的交叉观察（哪些论文其实在讲同一件事的不同侧面、哪些信息互补、哪些说法互相冲突）；最后列出还没被解决的开放问题。
只依据给定材料，不编造论文、数字或结论；works 里只写给定材料的标题原文。用中文，密度高、少套话。
用费曼学习法写：外行也能看懂的大白话，短句，术语当场解释；不要出现「跨模型评审的路由收益」这类看不懂的说法。
只输出 JSON 本身，不要任何解释文字，不要 Markdown 代码块。
'''
    payload = [{'title': note['title'], 'tags': note['tags'], 'summary': note['summary'],
        'takeaways': note['body'].split(MARK_START, 1)[1].split(MARK_END, 1)[0] if MARK_START in note['body'] else '',
        'qa_points': section_text(note['body'], '## 问答沉淀')}
        for note in notes]
    data = codex_json(prompt, payload, TOPIC_SCHEMA, STATE / 'topics' / f'{topic}.json',
        STATE / 'logs' / f'topic-{topic}.log')
    lookup = {note['title']: note for note in notes}
    def link(title):
        note = lookup.get(title)
        if not note:
            for candidate in notes:
                if title[:24].lower() in candidate['title'].lower() or candidate['title'][:24].lower() in title.lower():
                    note = candidate
                    break
        return f"[[论文/{note['id']}|{note['title']}]]" if note else title
    lines = [f'# {topic}', '', '自动生成的体系页；「我的想法」由你自己写，重建时不会覆盖。', '',
        f'归档笔记 {len(notes)} 篇 · 最近重建 {dt.datetime.now(TZ):%Y-%m-%d %H:%M}', '',
        '## 定位', '', data['positioning'], '', '## 概念地图', '']
    for group in data['groups']:
        lines += [f"### {group['name']}", '', f"- 解决什么问题：{group['question']}",
            f"- 通行做法：{group['approach']}",
            f"- 组内差异：{group['differences']}",
            '- 代表工作：' + ' · '.join(link(title) for title in group['works']), '']
    lines += ['## 交叉观察', ''] + [f'- {item}' for item in data['cross']] + ['']
    lines += ['## 开放问题', ''] + [f'- {item}' for item in data['open_questions']] + ['']
    lines += [kept.strip('\n'), '', '## 归档索引', '']
    for note in notes:
        marker = '' if MARK_START in note['body'] else '（待深读）'
        lines.append(f"- [[论文/{note['id']}|{note['title']}]] {marker} — {note['summary']}")
    lines.append('')
    research.replace(path, '\n'.join(lines))
    return path, len(notes)


def rebuild(topics=None):
    topics = topics or DEFAULT_TOPICS
    if 'all' in topics or not topics:
        known = {tag for note in archived_notes() for tag in note['tags']}
        topics = [topic for topic in DEFAULT_TOPICS if topic in known] or DEFAULT_TOPICS
    done = []
    for topic in topics:
        if not topic_notes(topic):
            continue
        path, count = rebuild_topic(topic)
        done.append(topic)
        print(f'体系页更新: {topic}（{count} 篇）-> {path}', flush=True)
    return done


def after(ident):
    """归档后调用：先给这篇补深读，再重建它涉及的专题页。"""
    notes = [note for note in archived_notes() if note['id'] == ident or note['path'].stem == ident]
    if not notes:
        return
    deepen([ident])
    topics = [tag for tag in notes[0]['tags'] if tag in DEFAULT_TOPICS]
    if not topics and notes[0]['primary_tag'] in DEFAULT_TOPICS:
        topics = [notes[0]['primary_tag']]
    rebuild(topics or DEFAULT_TOPICS)


# ---------- 逐条提问 ----------

ASK_SCHEMA = {'type': 'object', 'properties': {
    'answer': {'type': 'string'}, 'point': {'type': 'string'},
    'confidence': {'type': 'string', 'enum': ['正文级', '摘要级', '材料中没有']}},
    'required': ['answer', 'point', 'confidence'], 'additionalProperties': False}


def ask(ident, question):
    item = entry(ident)
    if not item:
        raise RuntimeError('没有找到这条内容：' + ident)
    note_path = NOTES / f'{ident}.md'
    note_body = read_note(note_path)['body'] if note_path.exists() else ''
    if not note_body and item.get('ocr'):
        note_body = '## 截图文字（OCR）\n' + str(item['ocr'])[:20000]
    note_like = {'id': ident, 'title': item.get('title') or ident, 'summary': item.get('summary') or '',
        'source': 'xiaohongshu' if item.get('source') == 'xiaohongshu' else 'arxiv',
        'body': note_body, 'tags': item.get('tags') or [], 'note_url': item.get('note_url') or item.get('url') or ''}
    material, level = paper_text(note_like)
    qa_path = QA_DIR / f'{ident}.md'
    history = qa_path.read_text(encoding='utf-8') if qa_path.exists() else ''
    prompt = '''你在帮一位 NLP 博士读一篇论文。他只问自己关心的点，请直接回答，不要复述全文。
只依据给定材料（论文正文/摘要、以及这条内容的截图 OCR 和已有问答）回答；材料里没有的信息必须说“材料里没有”，不要用常识补。可以用材料里的数字和术语。
answer 用中文，先给结论再给依据，150–400 字，必要时用短列表；point 是把这次问答沉淀成知识体系用的一句话（30–60 字，写清“这件事的结论是什么”）。
confidence 选一个：正文级（读到正文）、摘要级（只有摘要）、材料中没有（问题超出材料）。
'''
    payload = {'entry': {'title': note_like['title'], 'summary': note_like['summary'], 'material_level': level},
        'question': question, 'previous_qa': history[-6000:], 'material': material}
    data = codex_json(prompt, payload, ASK_SCHEMA, STATE / 'ask' / f'{ident}.json',
        STATE / 'logs' / f'{ident}-ask.log')
    stamp = f'{dt.datetime.now(TZ):%Y-%m-%d %H:%M}'
    number = history.count('\n## Q') + 1
    block = [f'\n## Q{number}（{stamp}）', '', question.strip(), '', '### 答', '', data['answer'].strip(), '',
        f"**沉淀**：{data['point'].strip()}　（依据：{data['confidence']}）", '']
    if not history:
        head = ['---', f'title: {json.dumps(note_like["title"], ensure_ascii=False)}', f'entry: {ident}',
            f'url: {json.dumps(item.get("url") or "", ensure_ascii=False)}', f'source: {item.get("source","")}', '---', '',
            f'# 问答 · {note_like["title"]}', '']
        research.replace(qa_path, '\n'.join(head) + '\n'.join(block).lstrip('\n'))
    else:
        research.replace(qa_path, history.rstrip('\n') + '\n' + '\n'.join(block))
    if note_path.exists():
        fold_qa(note_path, data['point'].strip(), f'Q{number}', stamp)
    ANSWERS.mkdir(parents=True, exist_ok=True)
    research.replace(ANSWERS / f'{ident}.json', {'at': dt.datetime.now(TZ).isoformat(), 'id': ident,
        'title': note_like['title'], 'question': question.strip(), 'answer': data['answer'].strip(),
        'point': data['point'].strip(), 'confidence': data['confidence'], 'qa_path': str(qa_path.relative_to(ROOT))})
    return data


def fold_qa(note_path, point, label, stamp):
    """把问答沉淀追加进归档笔记的「## 问答沉淀」段落。"""
    text = note_path.read_text(encoding='utf-8')
    line = f'- {point}（{label} · {stamp}）'
    if '## 问答沉淀' in text:
        head, rest = text.split('## 问答沉淀', 1)
        tail = ''
        for name in KEEP_SECTIONS:
            if name in rest:
                rest, tail = rest.split(name, 1)
                tail = name + tail
                break
        research.replace(note_path, head.rstrip('\n') + '\n\n## 问答沉淀\n\n' + rest.strip('\n') + '\n' + line + '\n'
            + (('\n' + tail.strip('\n') + '\n') if tail else ''))
        return
    head = text
    tail = ''
    for name in KEEP_SECTIONS:
        if name in head:
            head, rest = head.split(name, 1)
            tail = name + rest
            break
    research.replace(note_path, head.rstrip('\n') + '\n\n## 问答沉淀\n\n' + line + '\n'
        + (('\n' + tail.strip('\n') + '\n') if tail else ''))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    deep = sub.add_parser('deepen', help='给归档论文补深读 takeaway')
    deep.add_argument('--id', action='append', dest='ids')
    deep.add_argument('--force', action='store_true')
    deep.add_argument('--limit', type=int)
    build = sub.add_parser('rebuild', help='重建主题体系页')
    build.add_argument('--topic', action='append', dest='topics')
    post = sub.add_parser('after', help='归档后：深读这一篇并重建相关专题页')
    post.add_argument('--id', required=True, dest='ident')
    ask_parser = sub.add_parser('ask', help='对某条内容提问，答案写进 问答/ 并沉淀到笔记')
    ask_parser.add_argument('--id', required=True, dest='ident')
    ask_parser.add_argument('--question', required=True)
    args = parser.parse_args()
    STATE.mkdir(parents=True, exist_ok=True)
    if args.command == 'deepen':
        deepen(args.ids, force=args.force, limit=args.limit)
    elif args.command == 'after':
        after(args.ident)
    elif args.command == 'ask':
        print(ask(args.ident, args.question)['answer'])
    else:
        rebuild(args.topics)


if __name__ == '__main__':
    main()
