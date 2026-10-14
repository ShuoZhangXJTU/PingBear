#!/usr/bin/env python3
"""挂载开关 + 供其它模块调用的注入接口。

  python3 mount.py status           查看状态
  python3 mount.py on|off           挂载 / 取消挂载（只影响执行，不影响监听总结）
  python3 mount.py render '<json>'  按情境渲染 prompt 片段（未挂载时输出空）
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as cfg
import core


def render(snapshot):
    if not cfg.is_mounted():
        return ""
    lines = []
    # 反射层：永不检索、每次加载
    reflex_path = Path(__file__).resolve().parents[1] / "reflex.json"
    if reflex_path.exists():
        reflex = json.loads(reflex_path.read_text(encoding="utf-8"))
        lines.append("【底线约束（常驻，不参与检索）】")
        lines += [f"- {item['text']}" for item in reflex.get("items", [])]
        lines.append("")
    # 索引层：按情境匹配
    items = core.match(snapshot)
    if not items:
        lines.append("【我的评价体系】当前线索没有匹配到检索层条目，"
            "不确定时应当直接问，不要用近似条目套用。")
        return "\n".join(lines)
    lines.append("【我的评价体系（按当前情境匹配）】")
    for item in items:
        judgment = item.get("judgment", {})
        lines.append(f"- ({judgment.get('strength', 'prefer')}) {judgment.get('text', '')}")
        motivation = item.get("motivation", {})
        if motivation.get("value") or motivation.get("cost"):
            why = "；".join(x for x in [motivation.get("value"), motivation.get("cost")] if x)
            lines.append(f"  出于：{why}")
    lines.append("（由 rubrics 模块提供；只列与当前情境匹配的条目，未匹配的不推断）")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["status", "on", "off", "render"], nargs="?", default="status")
    parser.add_argument("snapshot", nargs="?")
    args = parser.parse_args()
    if args.action in ("on", "off"):
        print("已挂载 ✅" if cfg.set_mounted(args.action == "on") else "已取消挂载")
    elif args.action == "render":
        print(render(json.loads(args.snapshot or "{}")))
    else:
        data = cfg.load()
        print(f"挂载：{'已挂载（rubrics 会影响后续执行）' if data['mounted'] else '未挂载（只监听、不影响执行）'}")
        print("关注源：" + "、".join(cfg.enabled_sources()))
        print(f"监听时间：每天 {data['observe_hours']} 点（错峰）")
        print(f"条目数：{len(core.load())}")


if __name__ == "__main__":
    main()
