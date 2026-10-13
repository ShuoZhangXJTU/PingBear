#!/usr/bin/env python3
"""rubrics 核心：条目存储、情境匹配、沿革。无外部依赖，独立可拆。"""
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "data/criteria.json"


def load():
    return json.loads(STORE.read_text(encoding="utf-8")) if STORE.exists() else []


def save(items):
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def new_id(items):
    year = dt.date.today().year
    nums = [int(item["id"].split("-")[-1]) for item in items if item["id"].startswith(f"r-{year}-")]
    return f"r-{year}-{max(nums or [0]) + 1:04d}"


def add(item):
    items = load()
    item["id"] = item.get("id") or new_id(items)
    if not item.get("lineage"):
        item["lineage"] = {}
    item["lineage"]["created"] = dt.date.today().isoformat()
    if not any(existing["id"] == item["id"] for existing in items):
        items.append(item)
    save(items)
    return item


def match(snapshot, items=None):
    """情境匹配：五根轴分别计分，返回按匹配度排序的条目。
    snapshot 形如 {"object":…, "decision":…, "state":…, "constraints":[…], "trigger":…}
    """
    items = items or load()
    scored = []
    for item in items:
        sit = item.get("situation", {})
        score = 0
        for axis in ("object", "decision", "state"):
            if snapshot.get(axis) and snapshot[axis] == sit.get(axis):
                score += 3
        for constraint in snapshot.get("constraints") or []:
            if constraint in (sit.get("constraints") or []):
                score += 1
        if snapshot.get("trigger") and sit.get("trigger") and snapshot["trigger"] in sit["trigger"]:
            score += 2
        if score:
            scored.append((score, item))
    scored.sort(key=lambda pair: -pair[0])
    return [item for _score, item in scored]


def scoped_update(current_id, new_item, reason):
    """演进：不覆盖旧条目。新条目写 lineage.supersedes，旧条目补 superseded_by。"""
    items = load()
    added = add(new_item)
    added.setdefault("lineage", {})["supersedes"] = [current_id]
    for item in items:
        if item["id"] == current_id:
            item.setdefault("lineage", {})
            item["lineage"].setdefault("superseded_by", []).append(added["id"])
            item["lineage"].setdefault("notes", []).append(
                {"at": dt.date.today().isoformat(), "reason": reason})
    save(items)
    return added
