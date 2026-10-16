"""Evidence-grounded rubric genome. Standard library only; no model calls."""
import copy
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / 'schema.json').read_text())


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def check_schema(value, schema=SCHEMA, path='$'):
    """Validate the deliberately small JSON Schema subset used by this project."""
    if 'const' in schema and value != schema['const']:
        raise ValueError(f'{path}: invalid constant')
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError(f'{path}: invalid enum')
    types = schema.get('type', [])
    types = [types] if isinstance(types, str) else types
    valid = {'object': isinstance(value, dict), 'array': isinstance(value, list),
             'string': isinstance(value, str), 'null': value is None,
             'boolean': isinstance(value, bool)}
    if types and not any(valid.get(t, False) for t in types):
        raise ValueError(f'{path}: expected {types}')
    if isinstance(value, dict) and 'properties' in schema:
        props = schema['properties']
        if set(schema.get('required', [])) - set(value):
            raise ValueError(f'{path}: missing fields')
        if schema.get('additionalProperties') is False and set(value) - set(props):
            raise ValueError(f'{path}: unknown fields')
        for key, val in value.items():
            if key in props:
                check_schema(val, props[key], f'{path}.{key}')
    if isinstance(value, list) and 'items' in schema:
        for n, val in enumerate(value):
            check_schema(val, schema['items'], f'{path}[{n}]')


def empty(schema):
    if 'properties' in schema:
        return {k: empty(v) for k, v in schema['properties'].items()}
    if schema.get('type') == 'array':
        return []
    if 'enum' in schema:
        return 'unknown' if 'unknown' in schema['enum'] else schema['enum'][0]
    if isinstance(schema.get('type'), list) and 'null' in schema['type']:
        return None
    return ''


def draft(ident):
    return {'schema_version': '0.3', 'id': ident, 'kind': 'unclassified',
            'genome': empty(SCHEMA['properties']['genome']), 'evidence': [],
            'applicability': {'reviewed': False, 'required': [], 'excluded': [],
                              'valid_from': None, 'valid_until': None, 'review_note': ''},
            'lifecycle': {'status': 'draft', 'created_at': now(), 'confirmed_at': None,
                          'supersedes': [], 'review_note': ''}, 'legacy': None}


def atoms(tree):
    if isinstance(tree, dict):
        if set(tree) == {'value', 'basis', 'evidence_ids'}:
            yield tree
        else:
            for value in tree.values():
                yield from atoms(value)
    elif isinstance(tree, list):
        for value in tree:
            yield from atoms(value)


def parse_time(value):
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    return parsed.replace(tzinfo=dt.timezone.utc) if parsed.tzinfo is None else parsed


def validate(item, episodes=None, confirmation=False):
    check_schema(item)
    evidence = {e['id']: e for e in item['evidence']}
    if len(evidence) != len(item['evidence']):
        raise ValueError('duplicate evidence id')
    for e in evidence.values():
        if not e['id'] or not e['episode_id'] or not e['quote'].strip():
            raise ValueError('empty evidence reference')
        if episodes is not None:
            ep = episodes.get(e['episode_id'])
            if ep is not None and (ep.get('origin') == 'injected_context' or ep['text'].startswith('# AGENTS.md instructions')):
                raise ValueError('injected instructions cannot ground personal judgments')
            # 引用必须是原文，但模型抄写时常丢空格/换行：忽略空白后再比对，
            # 这样既挡住编造，又不会因为排版差异丢掉整条草稿。
            def squeeze(text):
                return ''.join(text.split())
            if ep is None or squeeze(e['quote']) not in squeeze(ep['text']):
                raise ValueError('evidence quote is absent from episode')
    for a in atoms(item['genome']):
        if a['basis'] == 'unknown':
            if a['value'] is not None or a['evidence_ids']:
                raise ValueError('unknown must be null without evidence')
        elif not a['value'] or not a['evidence_ids'] or set(a['evidence_ids']) - set(evidence):
            raise ValueError('known or inferred fact requires value and evidence')
    policy = item['applicability']
    for p in policy['required'] + policy['excluded']:
        if not p['field'] or not p['value']:
            raise ValueError('empty applicability predicate')
    for t in [policy['valid_from'], policy['valid_until'], item['lifecycle']['created_at'], item['lifecycle']['confirmed_at']]:
        if t:
            parse_time(t)
    if policy['valid_from'] and policy['valid_until'] and parse_time(policy['valid_from']) >= parse_time(policy['valid_until']):
        raise ValueError('invalid validity interval')
    if confirmation or item['lifecycle']['status'] == 'confirmed':
        if episodes is None or not evidence:
            raise ValueError('confirmation requires checked original episodes')
        if not item['genome']['judgment']['statement']['value']:
            raise ValueError('missing judgment')
        if item['kind'] == 'unclassified':
            raise ValueError('classify before confirming')
        if not item['lifecycle']['review_note']:
            raise ValueError('confirmation requires review note')
        if item['lifecycle']['status'] == 'confirmed' and not item['lifecycle']['confirmed_at']:
            raise ValueError('missing confirmation time')
    return item


def migrate(old):
    """Preserve legacy claims without pretending their provenance is known."""
    if old.get('schema_version') == '0.3':
        return copy.deepcopy(old)
    item = draft(old['id'])
    item['legacy'] = copy.deepcopy(old)
    item['lifecycle']['review_note'] = '旧条目完整保留；缺少逐条原始证据，基因组留空待重建。'
    return item


def field(snapshot, path):
    value = snapshot
    for part in path.split('.'):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def predicate(snapshot, condition):
    value = field(snapshot, condition['field'])
    if value is None:
        return None
    if condition['op'] == 'eq':
        return value == condition['value']
    if not isinstance(value, list):
        return None  # contains is list membership, never fuzzy substring inference
    return condition['value'] in value


def applicable(item, snapshot, at=None):
    if item.get('schema_version') != '0.3' or item['lifecycle']['status'] != 'confirmed':
        return 'ineligible'
    policy = item['applicability']
    if not policy['reviewed'] or not policy['required'] or item['kind'] in ('task', 'unclassified'):
        return 'unreviewed'
    if not policy['review_note']:
        return 'unreviewed'
    if item['kind'] == 'project_spec' and not any(p['field'] == 'project' and p['op'] == 'eq' for p in policy['required']):
        return 'unreviewed'
    at = parse_time(at or now())
    if not item['lifecycle']['confirmed_at'] or parse_time(item['lifecycle']['confirmed_at']) > at:
        return 'ineligible'
    if policy['valid_from'] and at < parse_time(policy['valid_from']):
        return 'ineligible'
    if policy['valid_until'] and at >= parse_time(policy['valid_until']):
        return 'expired'
    required = [predicate(snapshot, p) for p in policy['required']]
    excluded = [predicate(snapshot, p) for p in policy['excluded']]
    if False in required or True in excluded:
        return 'not_applicable'
    if None in required or None in excluded:
        return 'unknown'
    return 'applicable'
