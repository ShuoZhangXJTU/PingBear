"""Versioned artifact DAG. Invalidations preserve outputs; dependency snapshots determine freshness."""
import argparse
from contextlib import contextmanager
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import uuid


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.graph-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            json.dump(value, out, ensure_ascii=False, indent=2); out.write('\n'); out.flush(); os.fsync(out.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)


class StaleInput(ValueError):
    pass


class Graph:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.path = self.directory / 'graph.json'

    def load(self):
        if not self.path.exists():
            return {'version': '1', 'meta': {}, 'nodes': {}, 'events': []}
        value = json.loads(self.path.read_text())
        if value.get('version') != '1': raise ValueError('Unsupported graph version')
        return value

    @contextmanager
    def locked(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        with (self.directory / 'graph.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state = self.load()
            yield state

    def set_meta(self, **values):
        with self.locked() as state:
            state['meta'].update(values); self.persist(state)

    def persist(self, state):
        atomic(self.path, state)
        # Only real project runs update the Obsidian view; temporary test runs do not.
        root = Path(__file__).resolve().parents[1]
        if self.directory.resolve().parent == root / '.research/industry/runs':
            try:
                from industry_status import refresh
                refresh(root)
            except Exception as error:
                import sys
                print('运行总览刷新失败：' + type(error).__name__, file=sys.stderr)

    @staticmethod
    def record(state, node):
        item = state['nodes'].get(node, {})
        return item.get('revisions', {}).get(item.get('head'))

    def status_in(self, state, node, visiting=None):
        visiting = set() if visiting is None else visiting
        if node in visiting: raise ValueError('Dependency cycle')
        visiting = visiting | {node}
        item = state['nodes'].get(node)
        revision = self.record(state, node)
        if not revision: return 'missing'
        if item.get('invalidated'): return 'stale'
        for dep, version in revision['deps'].items():
            if state['nodes'].get(dep, {}).get('head') != version or self.status_in(state, dep, visiting) != 'fresh':
                return 'stale'
        return 'fresh'

    def artifact(self, revision):
        data = json.loads((self.directory / revision['path']).read_text())
        if digest(data) != revision['digest']: raise ValueError('Artifact checksum mismatch')
        return data

    def read(self, node, require_fresh=True):
        with self.locked() as state:
            if require_fresh and self.status_in(state, node) != 'fresh': raise StaleInput(node)
            revision = self.record(state, node)
            if not revision: raise StaleInput(node)
            return self.artifact(revision)

    def snapshot(self, deps):
        with self.locked() as state:
            versions, data = {}, {}
            for node in deps:
                if self.status_in(state, node) != 'fresh': raise StaleInput(node)
                versions[node] = state['nodes'][node]['head']
                data[node] = self.artifact(self.record(state, node))
            return versions, data

    @staticmethod
    def check_cycle(state, node, deps):
        def visit(current, seen):
            if current == node: raise ValueError('Dependency cycle')
            if current in seen: return
            revision = Graph.record(state, current)
            for dep in (revision or {}).get('deps', {}): visit(dep, seen | {current})
        for dep in deps: visit(dep, set())

    def _put(self, state, node, data, deps, recipe, reason, force=False):
        if not isinstance(node, str) or not node: raise ValueError('Node id required')
        self.check_cycle(state, node, deps)
        for dep, version in deps.items():
            if state['nodes'].get(dep, {}).get('head') != version or self.status_in(state, dep) != 'fresh':
                raise StaleInput('Input changed during computation: ' + dep)
        old = self.record(state, node)
        sha = digest(data)
        if not force and old and not state['nodes'][node].get('invalidated') and old['deps'] == deps and old['recipe'] == recipe and old['digest'] == sha:
            return state['nodes'][node]['head']
        ident = 'rev-' + uuid.uuid4().hex
        path = Path('artifacts') / (ident + '.json')
        atomic(self.directory / path, data)
        item = state['nodes'].setdefault(node, {'head': None, 'order': [], 'revisions': {}, 'invalidated': False})
        item['revisions'][ident] = {'id': ident, 'path': str(path), 'digest': sha, 'deps': dict(deps), 'recipe': recipe, 'created_at': now(), 'reason': reason, 'previous': item.get('head')}
        item['order'].append(ident); item['head'] = ident; item['invalidated'] = False
        state['events'].append({'at': now(), 'action': 'commit', 'node': node, 'revision': ident, 'reason': reason})
        return ident

    def put_inputs(self, values, reason='input update'):
        """Update related external inputs atomically so projections cannot disagree."""
        with self.locked() as state:
            heads = {n: self._put(state, n, v, {}, 'external-input', reason) for n, v in values.items()}
            self.persist(state)
            return heads

    def commit(self, node, data, versions, recipe, reason='rebuild', force=False):
        with self.locked() as state:
            ident = self._put(state, node, data, versions, recipe, reason, force)
            self.persist(state)
            return ident

    def build(self, node, deps, recipe, compute, validate=None, force=False, alias=None):
        versions, inputs = self.snapshot(deps)
        attempt = {'id': uuid.uuid4().hex, 'started_at': now(), 'pid': os.getpid(), 'dependencies': versions}
        with self.locked() as state:
            attempt['code_version'] = state['meta'].get('code_version', {})
        with self.locked() as state:
            old = self.record(state, node)
            if not force and old and self.status_in(state, node) == 'fresh' and old['deps'] == versions and old['recipe'] == recipe:
                data = self.artifact(old)
                attempt.update(status='cached', finished_at=now(), duration_seconds=0)
                state.setdefault('attempts', {})[node] = attempt
                state['events'].append({'at': now(), 'action': 'attempt_cached', 'node': node, 'attempt': attempt['id']})
                self.persist(state)
                return data
            attempt['status'] = 'running'
            state.setdefault('attempts', {})[node] = attempt
            state['events'].append({'at': now(), 'action': 'attempt_started', 'node': node, 'attempt': attempt['id'],
                                    'code_commit': attempt['code_version'].get('git_commit'),
                                    'code_sha256': attempt['code_version'].get('source_sha256')})
            self.persist(state)
        started = time.monotonic()
        try:
            data = compute(inputs)
            if validate: validate(data)
            revision = self.commit(node, data, versions, recipe, force=force)
        except Exception as error:
            with self.locked() as state:
                state['events'].append({'at': now(), 'action': 'failed_attempt', 'node': node, 'attempt': attempt['id'], 'error_type': type(error).__name__})
                attempt.update(status='failed', finished_at=now(), duration_seconds=round(time.monotonic()-started, 3), error_type=type(error).__name__)
                state.setdefault('attempts', {})[node] = attempt
                self.persist(state)
            raise
        with self.locked() as state:
            attempt.update(status='completed', finished_at=now(), duration_seconds=round(time.monotonic()-started, 3), revision=revision)
            state.setdefault('attempts', {})[node] = attempt
            state['events'].append({'at': now(), 'action': 'attempt_completed', 'node': node, 'attempt': attempt['id'],
                                    'duration_seconds': attempt['duration_seconds'], 'revision': revision})
            self.persist(state)
        if alias:
            with self.locked() as state:
                if self.status_in(state, node) == 'fresh': atomic(self.directory / alias, self.artifact(self.record(state, node)))
        return data

    def descendants(self, state, node):
        found = set()
        changed = True
        while changed:
            changed = False
            for name in state['nodes']:
                if name == node or name in found: continue
                if set((self.record(state, name) or {}).get('deps', {})) & ({node} | found):
                    found.add(name); changed = True
        return sorted(found)

    def invalidate(self, node, reason):
        with self.locked() as state:
            if not self.record(state, node): raise ValueError('Unknown node')
            state['nodes'][node]['invalidated'] = True
            impacted = self.descendants(state, node)
            state['events'].append({'at': now(), 'action': 'invalidate', 'node': node, 'reason': reason, 'affected': impacted})
            self.persist(state)
            return impacted

    def restore(self, node, revision, reason):
        with self.locked() as state:
            item = state['nodes'].get(node, {})
            if revision not in item.get('revisions', {}): raise ValueError('Unknown revision')
            self.artifact(item['revisions'][revision])
            self.check_cycle(state, node, item['revisions'][revision]['deps'])
            item['head'] = revision; item['invalidated'] = False
            state['events'].append({'at': now(), 'action': 'restore', 'node': node, 'revision': revision, 'reason': reason})
            self.persist(state)
            return self.status_in(state, node)

    def undo(self, node, reason):
        with self.locked() as state:
            item = state['nodes'].get(node)
            if not item or not item.get('head'): raise ValueError('Unknown node')
            index = item['order'].index(item['head'])
            current = item['revisions'][item['head']]
            item['head'] = current['previous'] if 'previous' in current else (item['order'][index-1] if index else None)
            item['invalidated'] = False
            state['events'].append({'at': now(), 'action': 'undo', 'node': node, 'revision': item['head'], 'reason': reason})
            self.persist(state)
            return item['head']

    def replace(self, node, data, reason):
        state = self.load(); old = self.record(state, node)
        if not old: raise ValueError('Unknown node')
        versions, _ = self.snapshot(old['deps'])
        return self.commit(node, data, versions, old['recipe'], reason=reason, force=True)

    def summary(self):
        with self.locked() as state:
            names = set(state['nodes']) | set(state.get('attempts', {}))
            return {name: {'status': self.status_in(state, name), 'revision': item.get('head'),
                           'dependencies': (self.record(state, name) or {}).get('deps', state.get('attempts', {}).get(name, {}).get('dependencies', {})),
                           'execution': state.get('attempts', {}).get(name, {}),
                           'revisions': len(item.get('order', []))}
                    for name in sorted(names) for item in [state['nodes'].get(name, {})]}


    def mermaid(self):
        summary = self.summary()
        names = {name: 'n' + str(i) for i,name in enumerate(sorted(summary))}
        lines = ['flowchart LR']
        for name in sorted(summary):
            label = (name + ' / ' + summary[name]['status']).replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            lines.append(f'  {names[name]}["{label}"]')
        for name,row in summary.items():
            for dep in row['dependencies']:
                if dep in names: lines.append(f'  {names[dep]} --> {names[name]}')
        return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['status', 'graph', 'history', 'invalidate', 'undo', 'restore', 'replace'])
    parser.add_argument('run', type=Path)
    parser.add_argument('--node'); parser.add_argument('--revision'); parser.add_argument('--file', type=Path)
    parser.add_argument('--reason', default='explicit local operation')
    args = parser.parse_args(); graph = Graph(args.run)
    if args.action == 'graph':
        print(graph.mermaid(), end=''); raise SystemExit(0)
    if args.action == 'status': result = graph.summary()
    elif args.action == 'history': result = graph.load()['nodes'].get(args.node, {})
    elif args.action == 'invalidate': result = graph.invalidate(args.node, args.reason)
    elif args.action == 'undo': result = graph.undo(args.node, args.reason)
    elif args.action == 'restore': result = graph.restore(args.node, args.revision, args.reason)
    else:
        if not args.file: parser.error('--file required')
        import industry_workflow
        result = industry_workflow.replace_node(graph, args.node, json.loads(args.file.read_text()), args.reason)
    print(json.dumps(result, ensure_ascii=False, indent=2))
