#!/usr/bin/env python3
"""Replay applicability against a frozen memory snapshot and independent labels.
Cases: [{id, cutoff, snapshot, expected_ids, category}]. No model calls.
"""
import argparse
import json
from pathlib import Path
import genome


def evaluate(items, cases, episode_map):
    results = []
    if len({i['id'] for i in items}) != len(items):
        raise ValueError('duplicate rubric ids')
    if len({c['id'] for c in cases}) != len(cases):
        raise ValueError('duplicate case ids')
    for item in items:
        genome.validate(item, episode_map)
    for case in cases:
        cutoff = genome.parse_time(case['cutoff'])
        for item in items:
            if genome.parse_time(item['lifecycle']['created_at']) >= cutoff:
                raise ValueError('memory created after evaluation cutoff')
            if item['lifecycle']['confirmed_at'] and genome.parse_time(item['lifecycle']['confirmed_at']) >= cutoff:
                raise ValueError('confirmation after evaluation cutoff')
            for evidence in item['evidence']:
                ep = episode_map[evidence['episode_id']]
                if not ep.get('ts') or genome.parse_time(ep['ts']) >= cutoff:
                    raise ValueError('missing timestamp or future evidence leakage')
        predicted = {i['id'] for i in items if genome.applicable(i, case['snapshot'], case['cutoff']) == 'applicable'}
        expected = set(case['expected_ids'])
        if expected - {i['id'] for i in items}:
            raise ValueError('expected rubric absent from frozen memory')
        results.append({'id': case['id'], 'category': case.get('category', 'unspecified'),
                        'predicted': sorted(predicted), 'expected': sorted(expected),
                        'tp': len(predicted & expected), 'fp': len(predicted - expected),
                        'fn': len(expected - predicted), 'exact': predicted == expected})
    def metrics(rows):
        tp, fp, fn = (sum(r[k] for r in rows) for k in ('tp', 'fp', 'fn'))
        return {'cases': len(rows), 'precision': tp / (tp + fp) if tp + fp else None,
                'recall': tp / (tp + fn) if tp + fn else None, 'false_applications': fp,
                'exact_accuracy': sum(r['exact'] for r in rows) / len(rows) if rows else None}
    return {'scope': 'applicability replay only; not evidence of user preference improvement',
            'metrics': metrics(results),
            'by_category': {c: metrics([r for r in results if r['category'] == c]) for c in sorted({r['category'] for r in results})},
            'cases': results}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--memory', required=True)
    parser.add_argument('--cases', required=True)
    parser.add_argument('--episodes', required=True, help='frozen JSON array of episodes')
    args = parser.parse_args()
    print(json.dumps(evaluate(json.loads(Path(args.memory).read_text()), json.loads(Path(args.cases).read_text()),
                             {e['id']: e for e in json.loads(Path(args.episodes).read_text())}), ensure_ascii=False, indent=2))
