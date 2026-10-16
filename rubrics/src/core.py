#!/usr/bin/env python3
"""Transactional storage, explicit lifecycle, and conservative applicability."""
import copy
import hashlib
import fcntl
import json
import os
from contextlib import contextmanager
from pathlib import Path
import tempfile
import genome

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / 'data/criteria.json'


def load():
    return json.loads(STORE.read_text(encoding='utf-8')) if STORE.exists() else []


def save(items):
    STORE.parent.mkdir(parents=True, exist_ok=True)
    if STORE.exists():
        old = STORE.read_bytes()
        history = STORE.parent / 'history'
        history.mkdir(exist_ok=True)
        snapshot = history / (hashlib.sha256(old).hexdigest() + '.json')
        if not snapshot.exists():
            snapshot.write_bytes(old)
    fd, name = tempfile.mkstemp(dir=STORE.parent, prefix='.criteria-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(items, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, STORE)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def transaction():
    STORE.parent.mkdir(parents=True, exist_ok=True)
    with STORE.with_suffix('.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def new_id(items):
    year = genome.now()[:4]
    nums = [int(i['id'].split('-')[-1]) for i in items if i['id'].startswith(f'r-{year}-')]
    return f'r-{year}-{max(nums or [0]) + 1:04d}'


def add(item):
    with transaction():
        items = load()
        item = copy.deepcopy(item)
        item['id'] = item.get('id') or new_id(items)
        if any(i['id'] == item['id'] for i in items):
            raise ValueError('duplicate criterion id')
        if item.get('schema_version') != '0.3':
            item = genome.migrate(item)
        genome.validate(item)
        items.append(item)
        save(items)
        return item


def match(snapshot, items=None, at=None):
    import episodes
    episode_map = {e['id']: e for e in episodes.load()}
    result = []
    for item in (load() if items is None else items):
        if genome.applicable(item, snapshot, at) != 'applicable':
            continue
        try:
            genome.validate(item, episode_map)
        except ValueError:
            continue
        result.append(item)
    return result


def scoped_update(current_id, new_item, reason):
    """Propose an immutable successor; old rule stays active until explicit review."""
    with transaction():
        items = load()
        if not any(i['id'] == current_id for i in items):
            raise ValueError('missing predecessor')
        item = copy.deepcopy(new_item)
        item['id'] = new_id(items)
        item = genome.migrate(item)
        item['lifecycle'].update(status='draft', confirmed_at=None, created_at=genome.now(),
                                 supersedes=[current_id], review_note=reason)
        genome.validate(item)
        items.append(item)
        save(items)
        return item


def confirm(ident, note):
    import episodes
    with transaction():
        items = load()
        item = next(i for i in items if i['id'] == ident)
        if item['lifecycle']['status'] != 'draft' or not note.strip():
            raise ValueError('only draft may be confirmed; review note required')
        item['lifecycle']['review_note'] = note
        genome.validate(item, {e['id']: e for e in episodes.load()}, confirmation=True)
        item['lifecycle'].update(status='confirmed', confirmed_at=genome.now())
        save(items)
        return item


def retire(ident, note):
    with transaction():
        items = load()
        item = next(i for i in items if i['id'] == ident)
        if not note.strip():
            raise ValueError('retirement reason required')
        item['lifecycle']['status'] = 'retired'
        item['lifecycle']['review_note'] += '\n退休：' + note
        save(items)


def review_policy(ident, policy, note):
    """Explicit local review action; never called by the model extraction path."""
    import episodes
    with transaction():
        items = load()
        item = next(i for i in items if i['id'] == ident)
        if item['lifecycle']['status'] == 'retired' or not note.strip():
            raise ValueError('cannot review retired item; review note required')
        policy = copy.deepcopy(policy)
        policy.update(reviewed=True, review_note=note)
        item['applicability'] = policy
        if item['lifecycle']['status'] == 'confirmed':
            item['lifecycle']['confirmed_at'] = genome.now()  # policy revision changes the effective confirmation time
        genome.validate(item, {e['id']: e for e in episodes.load()})
        if not policy['required']:
            raise ValueError('at least one necessary condition required')
        if item['kind'] == 'project_spec' and not any(p['field'] == 'project' and p['op'] == 'eq' for p in policy['required']):
            raise ValueError('project_spec requires explicit project boundary')
        save(items)
        return item
