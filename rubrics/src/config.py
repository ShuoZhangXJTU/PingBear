#!/usr/bin/env python3
"""配置读写：关注源、挂载开关。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "config.json"
DEFAULTS = {
    "sources": {"conversation": True, "archive_notes": False, "ideas": False, "cookbook_conflicts": False},
    "mounted": True,
    "observe_hours": [3],
    "conversation_paths": ["~/.codex/sessions"],
}


def load():
    data = json.loads(PATH.read_text(encoding="utf-8")) if PATH.exists() else {}
    merged = dict(DEFAULTS)
    merged.update({k: v for k, v in data.items() if k in DEFAULTS})
    merged["sources"] = {**DEFAULTS["sources"], **(data.get("sources") or {})}
    return merged


def save(data):
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return PATH


def set_mounted(value):
    data = load()
    data["mounted"] = bool(value)
    save(data)
    return data["mounted"]


def is_mounted():
    return bool(load().get("mounted"))


def enabled_sources():
    return [name for name, on in load()["sources"].items() if on]
