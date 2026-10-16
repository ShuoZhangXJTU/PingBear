#!/usr/bin/env python3
"""Local migration, validation and explicit review commands."""
import argparse
import json
import core
import episodes
import genome


def migrate():
    with core.transaction():
        items = core.load()
        count = sum(i.get('schema_version') != '0.3' for i in items)
        migrated = [genome.migrate(i) for i in items]
        for item in migrated:
            genome.validate(item)
        core.save(migrated)
    print(f'迁移 {count} 条；原条目保留在 legacy，未自动确认或激活。')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['migrate', 'audit', 'confirm', 'retire', 'review-policy'])
    parser.add_argument('--id')
    parser.add_argument('--note')
    parser.add_argument('--policy-file')
    args = parser.parse_args()
    if args.action == 'migrate':
        migrate()
    elif args.action == 'audit':
        em = {e['id']: e for e in episodes.load()}
        items = core.load()
        for i in items:
            genome.validate(i, em)
        print(json.dumps({'items': len(items), 'confirmed': sum(i['lifecycle']['status'] == 'confirmed' for i in items),
                          'with_evidence': sum(bool(i['evidence']) for i in items)}, ensure_ascii=False))
    else:
        if not args.id or not args.note:
            parser.error('--id and --note required')
        if args.action == 'review-policy':
            if not args.policy_file:
                parser.error('--policy-file required')
            from pathlib import Path
            core.review_policy(args.id, json.loads(Path(args.policy_file).read_text()), args.note)
        else:
            (core.confirm if args.action == 'confirm' else core.retire)(args.id, args.note)
