"""Compact, stage-specific instructions. The JSON cards are the only runtime standard."""
import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / '配置/洞察标准/阶段卡.json'
STAGES = ('scope', 'scan', 'select', 'verify', 'synthesize', 'deliver')


def render(stage=None, path=None):
    policy = json.loads((path or PATH).read_text(encoding='utf-8'))
    lines = ['【业界洞察 · 常驻原则】'] + ['- ' + r for r in policy['common']]
    if stage is None:
        lines += ['当前阶段未指定；仅提供导航：' + ' → '.join(STAGES),
                  '确定当前环节后再加载该阶段卡，不加载全部标准。']
        return '\n'.join(lines)
    if stage not in STAGES:
        raise ValueError('Unknown insight stage: ' + str(stage))
    card = policy['stages'][stage]
    lines += [f'【当前环节：{card["title"]} / {stage}】', '目标：' + card['goal']]
    lines += ['- ' + r for r in card['rules']]
    lines += ['产出：' + card['output'], '过关：' + card['gate']]
    return '\n'.join(lines)
