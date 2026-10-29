#!/usr/bin/env python3
"""Read local execution evidence and publish a managed Obsidian control page; no model calls."""
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
START, END = '<!-- research:control:start -->', '<!-- research:control:end -->'
STAGES = [('scope', '定题'), ('scan', '广搜'), ('select', '筛选'), ('verify', '深核'),
          ('synthesize', '综合'), ('deliver', '决策')]
FILES = ['scripts/industry.py', 'scripts/industry_workflow.py', 'scripts/industry_graph.py',
         'scripts/industry_status.py', 'scripts/knowledge.py', 'scripts/rubrics_bridge.py',
         'rubrics/src/bridge.py', 'rubrics/src/insight_policy.py', '配置/洞察标准/阶段卡.json']


def git(root, *args):
    try:
        return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return ''


def code_version(root=ROOT):
    files = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in FILES if (root / name).exists()}
    return {'git_commit': git(root, 'rev-parse', 'HEAD') or 'unknown',
            'source_sha256': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
            'files': files, 'modified': bool(git(root, 'status', '--porcelain', '--', *FILES))}


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')[:160]


def attempt_state(attempt):
    status = attempt.get('status')
    if status == 'running':
        try:
            os.kill(attempt['pid'], 0)
        except ProcessLookupError:
            return '执行进程已退出（结束状态未记录）'
        except (KeyError, OSError):
            return '运行记录未结束（需核实进程）'
    return {'running': '运行中', 'completed': '执行完成', 'cached': '复用', 'failed': '失败'}.get(status, '未记录执行')


def render(root=ROOT):
    from industry_graph import Graph
    version = code_version(root)
    counts = Counter()
    data = root / 'rubrics/data/criteria.json'
    if data.exists():
        counts.update((row.get('lifecycle') or {}).get('status', 'unknown') for row in json.loads(data.read_text()))
    lines = [f'刷新：{dt.datetime.now(ZoneInfo("Asia/Shanghai")):%Y-%m-%d %H:%M:%S}（北京时间）', '',
        '[[配置/洞察标准|标准导航]] · [[研究路线/当前路线|当前路线]] · [[研究路线/审视记录|路线审视]] · [[研究路线/飞轮|上次夜间运行快照]]', '',
        '## 已接入与实际使用', '',
        '| 入口 | 实际接线 | 如何核实 |', '| --- | --- | --- |',
        '| CLI 交互 | 全局 AGENTS.md 要求先调用只读 bridge；属于指令约定 | 在新交互任务执行下方桥接命令；旧会话需重新加载指令 |',
        '| 业界洞察 | industry → 六环节 workflow → 每步 bridge 短卡 → Codex 生成 | 本页逐环节执行记录；运行目录 attempts 保留调用输入和日志 |',
        '| Obsidian | 同一库中的 Markdown 入口与结果；iCloud 同步生成区 | 今日简报顶部「运行总览」；云盘同步不等于手机已下载 |',
        '| 路线审视 | 本聊天已配置 heartbeat，读取路线、关注与原始证据 | 审视记录仅在有行动性发现时追加；本页不据此推断调度成功 |', '',
        'CLI 的 AGENTS 接入不是强制 shell hook；脚本接入是在模型调用前实际拼接阶段标准。Obsidian 展示文件和提供入口，没有另一个内置模型。', '',
        f'当前本地 rubric：已确认 {counts["confirmed"]} 条，草稿 {counts["draft"]} 条；确认不代表在所有任务中生效。', '',
        '## 版本', '',
        f'- 当前 Git：`{version["git_commit"][:12]}`；相关实现和阶段卡' + ('有未提交修改。' if version['modified'] else '无未提交修改。'),
        f'- 当前实现指纹：`{version["source_sha256"][:16]}`。每次模型阶段保留当时 Git 与文件哈希，提交后不改写过去记录。',
        '- Git 管理代码、schema 和标准；本地运行目录保留材料、产物版本、依赖、执行状态。私人数据不纳入公开代码仓库。', '',
        '## 洞察任务进度', '',
        '执行状态与产物有效性独立：重做失败时旧产物可以仍然有效；已完成也可能因上游修改而待复核。阶段完成数不是报告可信度或耗时百分比。', '']
    paths = sorted((root / '.research/industry/runs').glob('*/graph.json'), key=lambda p:p.stat().st_mtime, reverse=True)
    if not paths:
        lines += ['**尚无真实六环节运行记录。** 代码与测试已接入，旧版报告不能冒充新流程验收。',
                  '下一份真实洞察从定题开始时，这里才会出现运行、复用、失败和版本记录。', '']
    for path in paths[:10]:
        graph = Graph(path.parent)
        try:
            state = graph.load()
            lines += [f'### {cell(state["meta"].get("topic", path.parent.name))}', '', f'运行编号：`{path.parent.name}`', '',
                      '| 环节 | 最近执行 | 产物有效性 | 耗时 | 当前产物版本 |', '| --- | --- | --- | --- | --- |']
            completed = 0
            for name, label in STAGES:
                validity = graph.status_in(state, name)
                completed += validity == 'fresh'
                attempt = state.get('attempts', {}).get(name, {})
                revision = state['nodes'].get(name, {}).get('head') or '—'
                duration = str(attempt['duration_seconds']) + ' 秒' if 'duration_seconds' in attempt else '—'
                execution = attempt_state(attempt)
                if attempt.get('status') == 'running':
                    duration = '开始于 ' + dt.datetime.fromisoformat(attempt['started_at']).astimezone(ZoneInfo('Asia/Shanghai')).strftime('%m-%d %H:%M:%S')
                if attempt.get('error_type'): execution += '：' + attempt['error_type'] + '（查运行日志）'
                lines.append(f'| {label} | {cell(execution)} | ' + {'fresh':'有效', 'stale':'待复核', 'missing':'未产出'}[validity] + f' | {duration} | `{revision[:20]}` |')
            blockers=[]
            for name,label in STAGES:
                if graph.status_in(state,name) == 'stale':
                    deps=(graph.record(state,name) or {}).get('deps',{})
                    changed=[dep for dep,rev in deps.items() if state['nodes'].get(dep,{}).get('head') != rev or graph.status_in(state,dep) != 'fresh']
                    blockers.append(label+'：'+('依赖变化 '+', '.join(changed) if changed else '已明确标记重做'))
            if blockers:lines += ['', '待复核原因：'+'；'.join(blockers)+'。']
            lines += ['', f'当前有效产出：{completed}/6 个模型环节。材料采集与正文读取另有依赖节点，详见运行图。',
                      f'本地记录：`.research/industry/runs/{path.parent.name}/graph.json`；日志在同级 `attempts/`。', '']
        except (ValueError, OSError, KeyError) as error:
            lines += [f'- `{path.parent.name}` 状态读取失败：{type(error).__name__}，未将其视为完成。', '']
    lines += ['## 检查与操作', '', '在 Research 目录执行；这些检查不调用模型：', '', '```sh',
        'python3 -B scripts/industry_status.py',
        'python3 -B rubrics/src/bridge.py --snapshot \'{"channel":"cli","project":"research","task":"industry_insight","stage":"verify"}\'',
        'git log -5 --oneline -- scripts/industry* 配置/洞察标准*', '```', '',
        '局部修改、撤销和续跑命令见 [[配置/洞察标准/依赖图与局部重做]]。运行图每次状态变更刷新本地本页；activity 与 publish_review 也会刷新，后者负责同步到 iCloud。', '',
        '## 开源方案选择', '',
        '- 当前执行状态直接保存在运行图，无新增常驻服务；这部分是本项目实现，尚未接入外部编排器。',
        '- 若需要跨进程调度、自动重试和 Web 控制台，首选验证 [Prefect](https://www.prefect.io/docs/v3/concepts/states)。当前官方版要求 Python 3.11+，本机 Research 默认 Python 为 3.9，需独立环境。',
        '- [Dagster](https://dagster.io/docs/guides/build/assets) 更侧重持久资产与依赖；[DVC](https://doc.dvc.org/user-guide/pipelines) 适合数据与管线复现。现阶段先验证一份真实报告，再决定是否引入服务。', '',
        '此页仅报告程序执行与文件证据；科研问题是否验证、路线是否有效，需要实验与人工判断。']
    return '\n'.join(lines)


def refresh(root=ROOT):
    sys.path.insert(0, str(root / 'rubrics/src'))
    from activity import replace_block
    page = root / '研究路线/运行总览.md'
    replace_block(page, render(root), '# 运行总览', start=START, end=END)
    return page


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    print(refresh(args.root))
