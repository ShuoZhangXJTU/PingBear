#!/usr/bin/env python3
"""第一层：无损 episode 库。

把对话原文逐字存进 rubrics/episodes/<年-月>.jsonl，只追加、不修改、不去重内容本身
（同一条内容重复出现也只存一次）。**不做任何压缩或摘要**——摘要属于后面的索引层。

每条 episode 记：时间、角色、原文、所属会话，以及能拿到的「当时环境」（cwd 等产物引用）。
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "episodes"
SKIP = ("<environment_context>", "<skills_instructions>", "<collaboration_mode>")


def episode_id(session, ts, role, text):
    digest = hashlib.sha1(f"{session}|{ts}|{role}|{text}".encode("utf-8")).hexdigest()
    return "ep-" + digest[:12]


def iter_messages():
    """从本地 Codex 会话记录里逐条产出消息（含角色与时间）。"""
    for base in cfg.load()["conversation_paths"]:
        root = Path(base).expanduser()
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.jsonl")):
            session = path.stem
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    item = json.loads(line)
                except ValueError:
                    continue
                payload = item.get("payload") or {}
                if item.get("type") == "turn_context" and payload.get("cwd"):
                    yield {"kind": "context", "session": session, "ts": item.get("timestamp"),
                        "cwd": payload.get("cwd"), "text": ""}
                    continue
                if item.get("type") != "response_item" or payload.get("type") != "message":
                    continue
                role = payload.get("role")
                # 只收「我们的对话」：开发者/系统指令不属于用户表达，不入库
                if role not in ("user", "assistant"):
                    continue
                text = "".join(part.get("text", "") for part in payload.get("content", [])).strip()
                if not text or any(marker in text for marker in SKIP):
                    continue
                yield {"kind": "message", "session": session, "ts": item.get("timestamp"),
                    "role": role, "text": text, "cwd": payload.get("cwd") or ""}


def ingest():
    STORE.mkdir(parents=True, exist_ok=True)
    existing = {}
    for path in STORE.glob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                existing[json.loads(line)["id"]] = True
            except Exception:
                continue
    added, current_cwd, handled_sessions = 0, "", set()
    handles = {}
    for item in iter_messages():
        if item["kind"] == "context":
            current_cwd = item.get("cwd") or current_cwd
            continue
        session = item["session"]
        if session not in handled_sessions:
            current_cwd = ""
            handled_sessions.add(session)
        ident = episode_id(session, item.get("ts"), item.get("role"), item["text"])
        if ident in existing:
            continue
        month = (item.get("ts") or "")[:7] or "unknown"
        path = STORE / f"{month}.jsonl"
        record = {"id": ident, "ts": item.get("ts"), "role": item.get("role"),
            "session": session, "cwd": item.get("cwd") or current_cwd, "text": item["text"],
            "artifact_refs": []}
        handle = handles.get(path) or path.open("a", encoding="utf-8")
        handles[path] = handle
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        existing[ident] = True
        added += 1
    for handle in handles.values():
        handle.close()
    total = len(existing)
    print(f"episode 库：新增 {added} 条，累计 {total} 条 -> {STORE}")
    return added


def load(month=None):
    items = []
    for path in sorted(STORE.glob(f"{month or '*'}.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                items.append(json.loads(line))
            except ValueError:
                continue
    return items


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["ingest", "count"], nargs="?", default="ingest")
    args = parser.parse_args()
    if args.action == "count":
        items = load()
        print(f"{len(items)} 条 episode；"
            f"用户 {sum(1 for i in items if i['role'] == 'user')} / "
            f"助手 {sum(1 for i in items if i['role'] == 'assistant')}")
    else:
        ingest()


if __name__ == "__main__":
    main()
