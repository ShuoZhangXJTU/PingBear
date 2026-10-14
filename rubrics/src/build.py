#!/usr/bin/env python3
"""体系构建：把观察到的原料整理成「评价体系」（第一版）。

设计原则（按用户要求）：**不在观察阶段预先筛掉东西**——原料整包交给模型，
由"构建体系"这一步去决定什么算标准、怎么归类、哪些是噪音。

产出：rubrics/system/<日期>-v0.md（人读）+ rubrics/data/criteria.json（结构化，标记 draft）。
"""
import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg
import core
import observe

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "system"
DATA = ROOT / "data"
TAXONOMY = (ROOT / "DESIGN.md").read_text(encoding="utf-8")

OUT_SCHEMA = {
    "type": "object",
    "properties": {
        "criteria": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "judgment": {"type": "object", "properties": {
                    "text": {"type": "string"},
                    "strength": {"type": "string", "enum": ["veto", "must", "prefer", "penalty"]},
                    "mode": {"type": "string", "enum": ["mechanical", "heuristic"]},
                    "positive_examples": {"type": "array", "items": {"type": "string"}},
                    "negative_examples": {"type": "array", "items": {"type": "string"}}},
                    "required": ["text", "strength", "mode", "positive_examples", "negative_examples"],
                    "additionalProperties": False},
                "situation": {"type": "object", "properties": {
                    "object": {"type": "string"}, "decision": {"type": "string"}, "state": {"type": "string"},
                    "constraints": {"type": "array", "items": {"type": "string"}}, "trigger": {"type": "string"}},
                    "required": ["object", "decision", "state", "constraints", "trigger"],
                    "additionalProperties": False},
                "motivation": {"type": "object", "properties": {
                    "goal": {"type": "string"}, "value": {"type": "string"},
                    "cost": {"type": "string"}, "role": {"type": "string"}},
                    "required": ["goal", "value", "cost", "role"], "additionalProperties": False}},
            "required": ["judgment", "situation", "motivation"], "additionalProperties": False}},
        "taxonomy_notes": {"type": "object", "properties": {
            "missing_axes": {"type": "array", "items": {"type": "string"}},
            "axis_value_notes": {"type": "array", "items": {"type": "string"}},
            "groupings": {"type": "array", "items": {"type": "string"}}},
            "required": ["missing_axes", "axis_value_notes", "groupings"], "additionalProperties": False}},
    "required": ["criteria", "taxonomy_notes"], "additionalProperties": False}


def raw_material(days, cap=80000):
    turns = observe.conversation_turns(days)
    text = "\n\n".join(turns)
    return text[:cap], len(turns)


def build(days=3, label=None):
    material, turn_count = raw_material(days)
    date = dt.date.today().isoformat()
    label = label or f"{date}-v0"
    prompt = f"""你在为一位大厂 AI Lab 的 NLP 博士构建「个人评价体系」——记录**他在什么情境下、出于什么、给出了什么评价**。

下面是他的评价体系设计（taxonomy 与原则）：
{TAXONOMY}

下面是他最近 {days} 天的发言（**未经过滤**，混杂着任务指令、评价、纠正、原则、临时说明）。请从中构建体系：

1. **不要预先假设哪些是无用的**：如果一句话体现了"他对事情的要求/接受度/底线"，就应该成为一条标准，哪怕它伪装成一条任务指令。
2. 每条标准严格按 schema 的字段填：判断（含强度与判据形态、正反例）、情境（五轴）、动机（四元）。**不知道的字段留空字符串，不要编造**。
3. 允许合并表述相同、情境相同的条目；**情境不同就不要合并**，宁可拆成两条。
4. 正反例尽量引用他的原话片段。
5. 另外给出 taxonomy 回看：五轴/四元里有没有装不下的东西、哪些轴的值需要新增、你建议怎么给这个体系分组。
6. 只输出 JSON，不要解释文字，不要 Markdown 代码块。
"""
    schema_path = DATA / "build.schema.json"
    out_path = DATA / f"build-{label}.json"
    log_path = ROOT / "notes" / f"build-{label}.log"
    DATA.mkdir(parents=True, exist_ok=True)
    schema_path.write_text(json.dumps(OUT_SCHEMA, ensure_ascii=False, indent=2), encoding="utf-8")
    command = [str(Path.home() / ".local/bin/codex"), "exec", "--skip-git-repo-check", "--ephemeral",
        "--sandbox", "read-only", "-C", str(ROOT.parent), "-c", "features.shell_tool=false",
        "-c", 'web_search="disabled"', "--output-schema", str(schema_path), "-o", str(out_path), "-"]
    with log_path.open("a", encoding="utf-8") as handle:
        subprocess.run(command, input=prompt + "\n\n发言原文：\n" + material, text=True,
            stdout=handle, stderr=handle, timeout=3600)
    data = json.loads(out_path.read_text(encoding="utf-8"))
    criteria = data.get("criteria", [])
    items = core.load()
    stamp = dt.date.today().isoformat()
    for criterion in criteria:
        criterion.setdefault("lineage", {})
        criterion["lineage"]["created"] = stamp
        criterion["lineage"]["source"] = f"对话观察 {days} 天（{turn_count} 轮）"
        criterion["lineage"]["status"] = "draft"
        criterion["id"] = core.new_id(items)
        items.append(criterion)
    core.save(items)
    SYSTEM.mkdir(parents=True, exist_ok=True)
    path = SYSTEM / f"{label}.md"
    lines = [f"# 评价体系 {label}", "", f"构建自最近 {days} 天的对话（{turn_count} 轮，未预先过滤）。",
        f"条目 {len(criteria)} 条（状态 draft，待你确认）。", ""]
    for index, criterion in enumerate(criteria, 1):
        judgment = criterion["judgment"]
        situation = criterion["situation"]
        motivation = criterion["motivation"]
        lines += [f"## {index}. [{judgment['strength']}/{judgment['mode']}] {judgment['text']}", "",
            f"- 情境：对象={situation['object']} · 决策={situation['decision']} · 状态={situation['state']}"
            + (f" · 约束={'、'.join(situation['constraints'])}" if situation.get("constraints") else "")
            + (f" · 触发={situation['trigger']}" if situation.get("trigger") else ""),
            f"- 动机：目标={motivation['goal']} · 价值={motivation['value']}"
            + (f" · 代价={motivation['cost']}" if motivation.get("cost") else "")
            + (f" · 角色={motivation['role']}" if motivation.get("role") else "")]
        if judgment.get("positive_examples"):
            lines.append(f"- 正例：{' / '.join(judgment['positive_examples'][:2])}")
        if judgment.get("negative_examples"):
            lines.append(f"- 反例：{' / '.join(judgment['negative_examples'][:2])}")
        lines.append("")
    notes = data.get("taxonomy_notes", {})
    lines += ["## taxonomy 回看", "",
        f"- 建议分组：{' / '.join(notes.get('groupings', [])) or '（无）'}",
        f"- 缺的轴：{' / '.join(notes.get('missing_axes', [])) or '（无）'}",
        f"- 轴取值备注：{' / '.join(notes.get('axis_value_notes', [])) or '（无）'}"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"构建完成：{len(criteria)} 条标准 -> {path}")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--label")
    args = parser.parse_args()
    build(args.days, args.label)


if __name__ == "__main__":
    main()
