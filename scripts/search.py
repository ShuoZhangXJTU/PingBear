#!/usr/bin/env python3
"""按题目搜已归档论文：BM25 + 子串匹配 + 近似匹配。

你通常记得标题里的几个词、半句话，或者记错一两个字，所以权重压在标题上：
  - BM25 算相关性：标题词重复 3 次、标签 2 次、摘要 1 次；
  - 标题里出现原样子串：额外加分（按查询覆盖比例）；
  - 拼错/记错：difflib 近似匹配兜底。

  python3 scripts/search.py "token selective"
  python3 scripts/search.py "t-shrit"              # 拼错也能找到
  python3 scripts/search.py --topic 后训练 "preference"
  python3 scripts/search.py --json "gui"
"""
import argparse
import difflib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import research

ROOT = research.ROOT
NOTES = ROOT / '论文'
ASCII = re.compile(r'[a-z0-9][a-z0-9\-_.]{1,}')
CJK = re.compile(r'[\u4e00-\u9fff]+')
TITLE_BOOST = 3
TAG_BOOST = 2
SUMMARY_BOOST = 2
BODY_CHARS = 3000
K1, B = 1.5, 0.75


def tokens(text):
    text = (text or '').lower()
    found = ASCII.findall(text)
    # 标题里的连字符词（GUI-HARVEST、Token-Selective）既要整体匹配，也要拆开单独匹配。
    for token in list(found):
        if re.search(r'[-_.]', token):
            found.extend(part for part in re.split(r'[-_.]+', token) if len(part) > 1)
    for chunk in CJK.findall(text):
        found.extend(chunk[index:index + 2] for index in range(len(chunk) - 1))
        if len(chunk) == 1:
            found.append(chunk)
    return found


def normalize(text):
    """去掉空白和标点，用来做子串与近似匹配（标题里的连字符、冒号不该成为障碍）。"""
    return re.sub(r'[^0-9a-z\u4e00-\u9fff]+', '', (text or '').lower())


def partial_ratio(query, text):
    """整条标题太长时，整串比相似度会很低；这里取和查询等长的滑动窗口里最像的一段。"""
    if not query or not text:
        return 0.0
    best = difflib.SequenceMatcher(None, query, text).ratio()
    size = len(query)
    for width in (size, int(size * 1.2) + 1, int(size * 1.5) + 1):
        if width > len(text):
            continue
        step = max(width // 2, 1)
        for start in range(0, len(text) - width + 1, step):
            best = max(best, difflib.SequenceMatcher(None, query, text[start:start + width]).ratio())
    return best


def documents(topic=None):
    docs = []
    for path in sorted(NOTES.rglob('*.md')):
        if topic and path.parent.name != topic:
            continue
        fields, body = research.frontmatter(path)
        title = fields.get('title') or path.stem
        # 正文只取深读 takeaway 的前一段，低权重兜底：按题目找时标题仍然主导，
        # 但记得「困惑度」这种只出现在 takeaway 里的词也能搜到。
        digest = body.split('## 深读 takeaway', 1)[1] if '## 深读 takeaway' in body else ''
        docs.append({'path': str(path.relative_to(ROOT)), 'topic': path.parent.name,
            'title': title, 'tags': ' '.join(fields.get('tags') or []),
            'summary': fields.get('summary') or '',
            'body': re.sub(r'<!--.*?-->', ' ', digest, flags=re.S)[:BODY_CHARS],
            'id': fields.get('entry_id') or fields.get('arxiv') or ''})
    return docs


def index(docs):
    """把标题词重复 TITLE_BOOST 次、标签 TAG_BOOST 次写进词袋，等价于给字段加权。"""
    bag = []
    for doc in docs:
        bag.append(tokens(doc['title']) * TITLE_BOOST + tokens(doc['tags']) * TAG_BOOST
            + tokens(doc['summary']) * SUMMARY_BOOST + tokens(doc.get('body', '')))
    counters = [Counter(item) for item in bag]
    df = Counter()
    for counts in counters:
        df.update(counts.keys())
    total = len(bag)
    idf = {term: math.log(1 + (total - freq + 0.5) / (freq + 0.5)) for term, freq in df.items()}
    lengths = [len(item) or 1 for item in bag]
    average = sum(lengths) / total if total else 1
    return counters, idf, lengths, average


def search(query, docs=None, topic=None, limit=10):
    docs = docs if docs is not None else documents(topic)
    if not docs:
        return []
    counters, idf, lengths, average = index(docs)
    wanted = Counter(tokens(query))
    q_norm = normalize(query)
    scored = []
    for doc, counts, size in zip(docs, counters, lengths):
        score = 0.0
        for term, q_count in wanted.items():
            hits = counts.get(term, 0)
            if not hits:
                continue
            tf = hits * (K1 + 1) / (hits + K1 * (1 - B + B * size / average))
            score += idf.get(term, 0) * tf * min(q_count, 3)
        if q_norm:
            title_norm = normalize(doc['title'])
            if q_norm and q_norm in title_norm:
                score += 8 + 4 * len(q_norm) / max(len(title_norm), 1)
            else:
                ratio = partial_ratio(q_norm, title_norm)
                if ratio > 0.6:
                    score += 3 * ratio
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda item: -item[0])
    return [dict(doc, score=round(score, 2)) for score, doc in scored[:limit]]
def main():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('query', nargs='+', help='标题里的几个词、半句话都行')
    parser.add_argument('--topic', help='只在这个主题目录里找（如 后训练、Harness）')
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--out', help='把结果写成 JSON 到这个路径（给 Obsidian 插件轮询用）')
    args = parser.parse_args()
    query = ' '.join(args.query)
    hits = search(query, topic=args.topic, limit=args.limit)
    if args.out:
        import datetime as dt
        research.replace(ROOT / args.out, {'query': query,
            'at': dt.datetime.now().astimezone().isoformat(timespec='seconds'), 'hits': hits})
    if args.json:
        print(json.dumps({'query': query, 'hits': hits}, ensure_ascii=False, indent=2))
        return
    if not hits:
        print(f'没找到和「{query}」相关的归档论文。')
        return
    print(f'「{query}」命中 {len(hits)} 篇（按相关度）：')
    for n, hit in enumerate(hits, 1):
        print(f'{n:>2}. [{hit["topic"]}] {hit["score"]:>6}  {hit["title"][:78]}')
        print(f'    {hit["path"]}')


if __name__ == '__main__':
    main()
