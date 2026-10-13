#!/usr/bin/env python3
"""监听总结（每天半夜错峰跑）：从关注源里抽候选评价标准 → 提案，不自动入库。

当前默认只关注「我们的对话」：读本地 Codex 会话记录里的用户发言，挑出评价性表述，
整理成候选条目写进 rubrics/proposals/<日期>.md，等你确认后才进 seed/。

注意：监听总结与「挂载」开关无关，永远照跑；挂载只决定 rubrics 是否影响后续执行。
"""
import argparse
import datetime as dt
import json
import re
from pathlib import Path

import config as cfg

ROOT = Path(__file__).resolve().parents[1]
PROPOSALS = ROOT / "proposals"
# 评价性表述的信号词：纠正、要求、原则、取舍
SIGNALS = ["不对", "不行", "不要", "应该", "必须", "要求", "重要", "关键", "请你", "以后", "注意",
    "我觉得", "我希望", "我需要", "偏好", "胜过", "优于", "别把", "不能", "更值钱", "伪概念", "本质"]


def conversation_turns(days=1):
    """读最近几天的用户发言（本地 jsonl，仅本机读取）。"""
    since = dt.datetime.now() - dt.timedelta(days=days)
    turns = []
    for base in cfg.load()["conversation_paths"]:
        root = Path(base).expanduser()
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.jsonl")):
            if dt.datetime.fromtimestamp(path.stat().st_mtime) < since:
                continue
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    item = json.loads(line)
                except ValueError:
                    continue
                if item.get("type") != "response_item":
                    continue
                payload = item.get("payload") or {}
                if payload.get("type") != "message" or payload.get("role") != "user":
                    continue
                text = "".join(part.get("text", "") for part in payload.get("content", []))
                if "<environment_context>" in text or text.startswith("<"):
                    continue
                turns.append(text.strip())
    return turns


def extract(turns):
    """粗筛：含评价信号的句子，作为候选标准的原料（真正的归类由后续人工/AI 完成）。"""
    picked = []
    for turn in turns:
        for sentence in re.split(r"[。\n]", turn):
            sentence = sentence.strip()
            if 8 <= len(sentence) <= 300 and any(sig in sentence for sig in SIGNALS):
                picked.append(sentence)
    return list(dict.fromkeys(picked))


def write_proposals(snippets, date):
    PROPOSALS.mkdir(parents=True, exist_ok=True)
    path = PROPOSALS / f"{date}.md"
    lines = [f"# {date} 候选评价标准（待确认）", "",
        f"来源：{ '、'.join(cfg.enabled_sources()) }（挂载状态：{'已挂载' if cfg.is_mounted() else '未挂载'}）", "",
        "下面是今天从对话里抽出的评价性表述。确认后（或直接改）我再把它们整理成条目进 `seed/`；"
        "不确认的会留在提案里，不会进体系。", ""]
    for index, snippet in enumerate(snippets, 1):
        lines += [f"## C{index}. {snippet[:60]}", "", f"> {snippet}", ""]
    if not snippets:
        lines.append("（今天没抽到新的评价性表述）")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=1)
    args = parser.parse_args()
    date = dt.date.today().isoformat()
    turns = conversation_turns(args.days)
    snippets = extract(turns)
    path = write_proposals(snippets, date)
    print(f"读对话 {len(turns)} 轮 → 候选 {len(snippets)} 条 → {path}")


if __name__ == "__main__":
    main()
