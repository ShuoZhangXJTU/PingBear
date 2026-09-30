#!/usr/bin/env python3
"""Local research inbox: fetch HF, publish reviewed digests, archive selections."""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.request
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLE_VERSION = 2
TOPICS = {
    'RSI': ['self-improv', 'self-evol', 'recursive', 'self-play', 'curriculum', 'experimental understanding', 'environment generation', 'generating agentic', 'past experience'],
    'Harness': ['harness', 'agent', 'memory', 'tool use', 'tool-use', 'swe-bench', 'trajectory', 'trajectories', 'context management'],
    '后训练': ['post-training', 'reinforcement learning', 'policy optimization', 'grpo', 'ppo', 'distillation', 'credit assignment', 'critic', 'reward', 'rlvr'],
}
ORGS = ['google', 'deepmind', 'openai', 'anthropic', 'meta', 'microsoft', 'nvidia', 'amazon', 'apple', 'salesforce', 'alibaba', 'qwen', 'bytedance', 'tencent', 'huawei', 'baidu', 'deepseek', 'stanford', 'massachusetts institute', 'berkeley', 'carnegie', 'princeton', 'oxford', 'cambridge', 'tsinghua', 'peking', 'jiao tong', 'zhejiang', 'science and technology of china', 'hong kong']
# Fixed tag vocabulary: one canonical set so 论文/ stays searchable by tag.
# 配置/标签.md is the editable source; this list is the fallback if that file is missing.
DEFAULT_TAGS = ['RSI', 'Harness', '后训练', '强化学习', '记忆', '上下文管理', '工具调用', '评测', '基准',
    '智能体安全', '代码智能体', '深度搜索', '世界模型', '多模态', '具身智能', '机器人',
    '视频生成', '生成模型', '数据合成', '推理', '高效训练', '视觉', '其他']


def load_tags(root=ROOT):
    path = root / '配置/标签.md'
    if path.exists():
        found = re.findall(r'^\s*[-*]\s+(\S+)', path.read_text(encoding='utf-8'), re.M)
        if len(found) >= 5:
            return list(dict.fromkeys(found))
    return DEFAULT_TAGS


TAGS = load_tags()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        f.write(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def valid_date(value):
    if dt.date.fromisoformat(value).isoformat() != value:
        raise ValueError('Use YYYY-MM-DD')
    return value


def canonical(value):
    if not re.fullmatch(r'\d{4}\.\d{4,5}(v\d+)?', value):
        raise ValueError('Invalid arXiv ID: ' + value)
    return re.sub(r'v\d+$', '', value)


def reported(root, before):
    found = set()
    for path in (root / '.research/digests').glob('*.json'):
        if path.stem < before:
            found.update(p['id'] for p in load(path)['papers'])
    return found


# Local proxy is only a fallback: a dead proxy must not break the daily job, and the
# HF page is reachable directly on this machine most of the time.
LOCAL_PROXY = os.environ.get('RESEARCH_PROXY', 'http://127.0.0.1:7890')


def fetch_rows(url, timeout=45):
    """Fetch the HF daily-papers JSON. Ambient *_proxy variables are ignored so the
    connection plan is explicit: direct first, local proxy second."""
    errors = []
    # 如果 shell 里开了代理（proxy_on），说明这台机器直连 HF 不可用，优先走代理。
    env_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy') or os.environ.get('HTTP_PROXY')
    mirror = url.replace('huggingface.co', 'hf-mirror.com')
    order = [(LOCAL_PROXY, url), (None, url), (None, mirror), (LOCAL_PROXY, mirror)] if env_proxy else \
        [(None, url), (LOCAL_PROXY, url), (None, mirror), (LOCAL_PROXY, mirror)]
    seen = set()
    for proxy, target in order:
        if (proxy, target) in seen:
            continue
        seen.add((proxy, target))
        handler = urllib.request.ProxyHandler({} if proxy is None else {'http': proxy, 'https': proxy})
        opener = urllib.request.build_opener(handler)
        request = urllib.request.Request(target, headers={'User-Agent': 'LocalResearchInbox/0.1'})
        try:
            with opener.open(request, timeout=timeout) as response:
                rows = json.load(response)
            if isinstance(rows, list):
                return rows, (proxy or '直连') + ('' if target == url else '（hf-mirror 镜像）')
        except (OSError, ValueError) as error:
            errors.append(f'{proxy or "直连"}{"" if target == url else "·镜像"}: {type(error).__name__} {error}')
    raise RuntimeError('HF 抓取失败（' + '；'.join(errors) + '）')


def frontmatter(path):
    """Read the leading YAML block of a note; returns (fields, rest_of_text)."""
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        return {}, text
    parts = text.split('---\n', 2)
    if len(parts) < 3:
        return {}, text
    fields, key = {}, None
    for line in parts[1].splitlines():
        if not line.strip():
            continue
        if line.startswith(('  - ', '- ')) and key:
            fields[key].append(line.split('- ', 1)[1].strip().strip('"'))
            continue
        if ':' not in line:
            continue
        key, value = (part.strip() for part in line.split(':', 1))
        if not value:
            fields[key] = []
            continue
        if value.startswith('['):
            try:
                fields[key] = json.loads(value.replace("'", '"'))
            except ValueError:
                fields[key] = [v.strip().strip('"') for v in value[1:-1].split(',') if v.strip()]
        else:
            fields[key] = value.strip('"')
    return fields, parts[2]


def note_fields(p, date):
    """Canonical frontmatter for one archived paper."""
    tags = [t for t in p.get('tags', p.get('topics', [])) if t in TAGS]
    if not tags:
        tags = [t for t in p.get('topics', []) if t in TAGS] or ['其他']
    lines = ['---', f'arxiv: "{p["id"]}"', 'title: ' + json.dumps(p['title'], ensure_ascii=False),
        'summary: ' + json.dumps(p.get('summary', ''), ensure_ascii=False), f'selected_from: {date}',
        'status: to-read', f'primary_tag: {tags[0]}', 'tags:'] + ['  - ' + t for t in tags] + ['---']
    return '\n'.join(lines) + '\n', tags


_BAD_NAME = re.compile(r'[\\/:*?"<>|\n\r\t]+')


def note_path(root, paper):
    """论文笔记落盘位置：论文/<主题>/<论文标题>.md（主题取 primary_tag）。"""
    tags = [t for t in paper.get('tags', paper.get('topics', [])) if t in TAGS]
    tag = _BAD_NAME.sub(' ', str(tags[0] if tags else '其他')).strip() or '其他'
    name = _BAD_NAME.sub(' ', str(paper.get('title') or paper['id'])).strip().strip('.')
    name = re.sub(r'\s+', ' ', name)[:90] or str(paper['id'])
    return root / '论文' / tag / (name + '.md')


def build_index(root):
    """Regenerate 索引/标签.md from the archived notes so papers stay findable by tag."""
    entries = []
    notes_dir = root / '论文'
    for path in sorted(notes_dir.rglob('*.md')) if notes_dir.exists() else []:
        fields, _ = frontmatter(path)
        tags = fields.get('tags') or []
        if isinstance(tags, str):
            tags = [tags]
        rel = str(path.relative_to(root).with_suffix(''))
        entries.append({'id': fields.get('arxiv') or path.stem, 'path': rel,
            'title': fields.get('title') or path.stem,
            'date': fields.get('selected_from') or '', 'summary': fields.get('summary') or '',
            'tags': [t for t in tags if isinstance(t, str) and t.strip()]})
    grouped = {}
    for entry in entries:
        for tag in entry['tags']:
            grouped.setdefault(tag, []).append(entry)
    lines = ['# 标签索引', '', '自动生成，改动会被覆盖：归档后由「归档」按钮或 '
        '`python3 scripts/research.py index --date <日期>` 刷新。', '',
        f'已归档 {len(entries)} 篇，覆盖 {len(grouped)} 个标签。', '']
    if not entries:
        lines.append('还没有归档的论文。')
    for tag, items in sorted(grouped.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        lines += [f'## {tag}（{len(items)}）', '']
        for item in sorted(items, key=lambda x: x['date'], reverse=True):
            tail = ' · '.join(x for x in [item['date'], item['summary']] if x)
            lines.append(f"- [[{item['path']}|{item['title']}]]" + (f' — {tail}' if tail else ''))
        lines.append('')
    untagged = [e for e in entries if not e['tags']]
    if untagged:
        lines += ['## 未打标签', ''] + [f"- [[{e['path']}|{e['title']}]]" for e in untagged] + ['']
    replace(root/'索引/标签.md', '\n'.join(lines).rstrip() + '\n')
    print(f'{len(entries)} archived notes, {len(grouped)} tags -> {root/"索引/标签.md"}')


def index(args, root):
    build_index(root)


def collect(args, root):
    raw_path = root / '.research/raw' / (args.date + '.json')
    if raw_path.exists() and not getattr(args, 'refresh', False):
        snapshot = load(raw_path)
        rows = snapshot['items']
    else:
        url = 'https://huggingface.co/api/daily_papers?date=' + args.date
        if args.input:
            rows = load(Path(args.input))
            proxy_used = None
        else:
            rows, proxy_used = fetch_rows(url)
        if not isinstance(rows, list) or any(not isinstance(x, dict) or 'paper' not in x for x in rows):
            raise ValueError('Unexpected HF response; no data written')
        snapshot = {'source': url, 'captured_at': dt.datetime.now(dt.timezone.utc).isoformat(),
            'input_file': args.input, 'proxy_used': proxy_used, 'items': rows}
    seen = reported(root, args.date)
    papers = {}
    for row in rows:
        p = row['paper']
        pid = canonical(p['id'])
        title = p.get('title') or row.get('title') or ''
        summary = p.get('summary') or row.get('summary') or ''
        text = (title + ' ' + summary).lower()
        matches = {topic: [term for term in terms if term in text] for topic, terms in TOPICS.items()}
        org = p.get('organization') or row.get('organization') or {}
        org_name = (org.get('fullname') or org.get('name') or '未知') if isinstance(org, dict) else str(org)
        score = sum(min(len(terms), 3) * 3 for terms in matches.values())
        if score and any(term in org_name.lower() for term in ORGS):
            score += 2
        papers[pid] = {'id': pid, 'title': title, 'abstract': summary, 'hf_organization': org_name,
            'paper_published_at': p.get('publishedAt'), 'hf_date': args.date,
            'url': 'https://arxiv.org/abs/' + pid, 'hf_url': 'https://huggingface.co/papers/' + pid,
            'code': p.get('githubRepo'), 'project': p.get('projectPage'),
            'score': score, 'keyword_matches': matches, 'previously_reported': pid in seen}
    candidates = list(papers.values())
    if raw_path.exists() and getattr(args, 'refresh', False):
        backup(raw_path)
        raw_path.unlink()
    if not raw_path.exists():
        save_new(raw_path, snapshot)
    out = root / '.research/candidates' / (args.date + '.json')
    if out.exists() and getattr(args, 'refresh', False):
        backup(out)
        out.unlink()
    if not out.exists():
        save_new(out, {'date': args.date, 'source': snapshot['source'], 'papers': candidates})
    print(f'{len(candidates)} papers; candidates: {out}')


def card(p):
    tags = ' '.join('#'+t for t in p.get('tags', p.get('topics', [])))
    return f"{p['summary']}\n\n{tags}\n\n[PDF](https://arxiv.org/pdf/{p['id']})\n"


def digest_body(date, papers):
    body = f"---\ndate: {date}\ntype: digest\n---\n\n# {date} 科研速读\n\n"
    body += f"共 {len(papers)} 篇 · ★ 是你可能更感兴趣的\n\n"
    for p in papers:
        star = '★ ' if p.get('highlight', True) else ''
        body += f"## {p['number']}. {star}[{p['title']}]({p.get('url') or 'https://arxiv.org/abs/' + p['id']})\n\n" + card(p)
        body += f"\n[归档](obsidian://research-archive?date={date}&id={p['id']})\n\n"
    if not papers:
        body += '本次没有经过审阅且未推送的合适论文。\n'
    return body


def render(args, root):
    """Re-render the daily Markdown from the published digest; no network, no re-summarizing."""
    data = load(root / '.research/digests' / (args.date + '.json'))
    output = root / '日报' / (args.date + '.md')
    if output.exists():
        backup(output)
    replace(output, digest_body(args.date, data['papers']))
    print(output)


def backup(path):
    stamp = dt.datetime.now().strftime('%Y%m%dT%H%M%S%f')
    directory = path.parent / '.backups'
    directory.mkdir(exist_ok=True)
    shutil.copy2(path, directory / (path.name + '.' + stamp))


def replace(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    tmp.replace(path)


def publish(args, root):
    manifest = root / '.research/digests' / (args.date + '.json')
    output = root / '日报' / (args.date + '.md')
    if (output.exists() or manifest.exists()) and not getattr(args, 'update', False):
        raise ValueError('Digest already exists; preserved to keep numbering and edits stable')
    candidates = {p['id']: p for p in load(root / '.research/candidates' / (args.date + '.json'))['papers']}
    reviews = load(Path(args.reviews))
    if isinstance(reviews, dict):
        reviews = reviews['papers']
    reviewed = {}
    seen = set()
    chosen = []
    for review in reviews:
        pid = canonical(review['id'])
        if pid in seen:
            raise ValueError('Duplicate review: ' + pid)
        if pid not in candidates:
            raise ValueError('Review not in this date’s candidates: ' + pid)
        for key in ['title_zh', 'summary']:
            if not isinstance(review.get(key), str) or not review[key].strip():
                raise ValueError('Missing review field: ' + key)
        if not isinstance(review.get('topics'), list) or any(t not in TOPICS for t in review['topics']):
            raise ValueError('Invalid review topics')
        tags = review.get('tags', review['topics'])
        if not isinstance(tags, list) or not 2 <= len(tags) <= 5 or any(not isinstance(t, str) or t not in TAGS for t in tags):
            raise ValueError('Each paper needs 2–5 tags from the fixed list in 配置/标签.md')
        fields = {k: review[k] for k in ['title_zh', 'summary', 'topics']}
        fields['tags'] = list(dict.fromkeys(tags))
        reviewed[pid] = dict(candidates[pid], **fields, highlight=review.get('highlight', True))
        seen.add(pid)
    if seen != set(candidates):
        raise ValueError('Reviews must cover ALL papers; missing: ' + ', '.join(set(candidates)-seen))
    old = load(manifest)['papers'] if manifest.exists() else []
    # Preserve published numbers, including entries no longer returned by HF.
    for p in old:
        updated = reviewed.pop(p['id'], p)
        chosen.append(dict(updated, number=p['number']))
    for pid in candidates:
        if pid in reviewed:
            chosen.append(dict(reviewed[pid], number=len(chosen)+1))
    body = digest_body(args.date, chosen)
    for path in [manifest, output]:
        if path.exists():
            backup(path)
    replace(manifest, {'date': args.date, 'style_version': STYLE_VERSION, 'papers': chosen})
    replace(output, body)
    print(output)


def archive(args, root):
    papers = load(root / '.research/digests' / (args.date + '.json'))['papers']
    by_number = {p['number']: p for p in papers}
    if any(n not in by_number for n in args.numbers):
        raise ValueError('Unknown digest number; nothing archived')
    for number in dict.fromkeys(args.numbers):
        p = by_number[number]
        output = note_path(root, p)
        if output.exists():
            print('Already archived; preserved: ' + str(output))
            continue
        head, _tags = note_fields(p, args.date)
        body = head + f"\n# [{p['title']}]({p['url']})\n\n"
        body += card(p) + f"\n来源日报：[[日报/{args.date}]]，第 {number} 篇。\n\n"
        if p.get('topics'):
            body += '相关专题：' + ' · '.join('[[专题/' + t + ']]' for t in p['topics']) + '\n\n'
        body += '## 我的选择理由\n\n' + (args.reason or '待补充。') + '\n\n## 精读笔记\n\n待精读；PDF 尚未下载。\n'
        save_new(output, body)
        print(output)
    build_index(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ['collect', 'publish', 'archive', 'render', 'index']:
        cmd = commands.add_parser(name)
        cmd.add_argument('--date', type=valid_date, required=True)
        if name == 'collect':
            cmd.add_argument('--input', help='Import an already fetched HF JSON response')
            cmd.add_argument('--refresh', action='store_true')
        elif name == 'publish':
            cmd.add_argument('--reviews', required=True)
            cmd.add_argument('--update', action='store_true')
        elif name in ('render', 'index'):
            pass
        else:
            cmd.add_argument('--numbers', type=int, nargs='+', required=True)
            cmd.add_argument('--reason', default='')
    args = parser.parse_args()
    try:
        globals()[args.command](args, args.root)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
