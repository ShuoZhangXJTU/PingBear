import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import core
import genome
import build
import evaluate
import episodes

EP = {'id': 'ep-test', 'ts': '2026-01-01T00:00:00Z', 'role': 'user', 'text': '给外行写日报时，用大白话。'}


def rule():
    r = genome.draft('r-2026-0001')
    r['kind'] = 'project_spec'
    r['genome']['judgment']['statement'] = {'value': EP['text'], 'basis': 'explicit', 'evidence_ids': ['e1']}
    r['evidence'] = [{'id': 'e1', 'episode_id': EP['id'], 'quote': EP['text']}]
    r['lifecycle'].update(status='confirmed', created_at='2026-01-02T00:00:00Z', confirmed_at='2026-01-03T00:00:00Z', review_note='test human review')
    r['applicability'].update(reviewed=True, review_note='test boundary review', required=[
        {'field': 'project', 'op': 'eq', 'value': 'brief'},
        {'field': 'audience', 'op': 'eq', 'value': 'nonexpert'},
        {'field': 'trigger.event', 'op': 'eq', 'value': 'write_brief'}])
    return r


SNAP = {'project': 'brief', 'audience': 'nonexpert', 'trigger': {'event': 'write_brief'}}


class GenomeTests(unittest.TestCase):
    def test_exact_evidence(self):
        genome.validate(rule(), {EP['id']: EP})
        r = rule(); r['evidence'][0]['quote'] = '模型编造的原话'
        with self.assertRaises(ValueError): genome.validate(r, {EP['id']: EP})

    def test_unknown_not_filled(self):
        r = rule(); r['genome']['motivation']['goals'] = [{'value': '发论文', 'basis': 'unknown', 'evidence_ids': []}]
        with self.assertRaises(ValueError): genome.validate(r)

    def test_unattributed_inference(self):
        r = rule(); r['genome']['trigger']['event'] = {'value': '失败', 'basis': 'inferred', 'evidence_ids': []}
        with self.assertRaises(ValueError): genome.validate(r)

    def test_boundary_pairs(self):
        r = rule()
        self.assertEqual(genome.applicable(r, SNAP), 'applicable')
        for field in ['project', 'audience']:
            s = dict(SNAP, **{field: 'other'})
            self.assertEqual(genome.applicable(r, s), 'not_applicable')
        self.assertEqual(genome.applicable(r, {k: v for k, v in SNAP.items() if k != 'trigger'}), 'unknown')
        self.assertEqual(genome.applicable(r, dict(SNAP, trigger={'event': 'write_paper'})), 'not_applicable')

    def test_exclusion_unknown_is_not_false(self):
        r = rule(); r['applicability']['excluded'] = [{'field': 'urgent', 'op': 'eq', 'value': 'yes'}]
        self.assertEqual(genome.applicable(r, SNAP), 'unknown')
        self.assertEqual(genome.applicable(r, dict(SNAP, urgent='yes')), 'not_applicable')
        self.assertEqual(genome.applicable(r, dict(SNAP, urgent='no')), 'applicable')

    def test_expiry_and_draft(self):
        r = rule(); r['applicability']['valid_until'] = '2026-02-01T00:00:00Z'
        self.assertEqual(genome.applicable(r, SNAP, '2026-02-01T00:00:00Z'), 'expired')
        r['lifecycle']['status'] = 'draft'
        self.assertEqual(genome.applicable(r, SNAP), 'ineligible')

    def test_project_and_task_gating(self):
        r = rule(); r['applicability']['required'] = r['applicability']['required'][1:]
        self.assertEqual(genome.applicable(r, SNAP), 'unreviewed')
        r['kind'] = 'task'
        self.assertEqual(genome.applicable(r, SNAP), 'unreviewed')

    def test_legacy_is_not_promoted(self):
        old = {'id': 'r-2026-0001', 'judgment': {'text': 'MIT'}, 'situation': {'trigger': '开源'}}
        m = genome.migrate(old)
        self.assertEqual(m['legacy'], old)
        self.assertEqual(m['genome']['trigger']['event']['basis'], 'unknown')
        self.assertEqual(genome.migrate(m), m)
        genome.validate(m)

    def test_scoped_successor_persists(self):
        with tempfile.TemporaryDirectory() as d, patch.object(core, 'STORE', Path(d) / 'criteria.json'):
            core.save([rule()])
            added = core.scoped_update(rule()['id'], rule(), 'narrow scope')
            saved = core.load()
            self.assertEqual(len(saved), 2)
            self.assertEqual(saved[1]['id'], added['id'])
            self.assertEqual(saved[1]['lifecycle']['supersedes'], [rule()['id']])
            self.assertEqual(saved[0]['lifecycle']['status'], 'confirmed')
            self.assertEqual(saved[1]['lifecycle']['status'], 'draft')
            self.assertTrue(list((Path(d) / 'history').glob('*.json')))

    def test_empty_items_does_not_load_store(self):
        with patch.object(core, 'load', side_effect=AssertionError('must not load')), patch.object(episodes, 'load', return_value=[]):
            self.assertEqual(core.match({}, []), [])

    def test_batches_preserve_oversized_records(self):
        records = [{'text': 'x' * 200}, {'text': 'second'}, {'text': 'third'}]
        self.assertEqual([r for b in build.batches(records, 30) for r in b], records)

    def test_temporal_leakage(self):
        case = {'id': 'case', 'cutoff': '2026-01-05T00:00:00Z', 'snapshot': SNAP, 'expected_ids': [rule()['id']]}
        result = evaluate.evaluate([rule()], [case], {EP['id']: EP})
        self.assertEqual(result['metrics']['exact_accuracy'], 1)
        later = dict(EP, ts='2026-02-01T00:00:00Z')
        with self.assertRaises(ValueError): evaluate.evaluate([rule()], [case], {EP['id']: later})

    def test_schema_rejects_undeclared_field(self):
        r = rule(); r['confidence'] = .9
        with self.assertRaises(ValueError): genome.validate(r)

    def test_confirmation_requires_original_evidence(self):
        with tempfile.TemporaryDirectory() as d, patch.object(core, 'STORE', Path(d) / 'criteria.json'):
            r = rule(); r['lifecycle'].update(status='draft', confirmed_at=None)
            core.save([r])
            with patch.object(episodes, 'load', return_value=[]):
                with self.assertRaises(ValueError): core.confirm(r['id'], 'reviewed')
            self.assertEqual(core.load()[0]['lifecycle']['status'], 'draft')
            with patch.object(episodes, 'load', return_value=[EP]):
                core.confirm(r['id'], 'reviewed')
            self.assertEqual(core.load()[0]['lifecycle']['status'], 'confirmed')

    def test_review_policy_requires_project_scope(self):
        with tempfile.TemporaryDirectory() as d, patch.object(core, 'STORE', Path(d) / 'criteria.json'), patch.object(episodes, 'load', return_value=[EP]):
            core.save([rule()])
            policy = copy.deepcopy(rule()['applicability'])
            policy['required'] = policy['required'][1:]
            with self.assertRaises(ValueError): core.review_policy(rule()['id'], policy, 'reviewed')
            self.assertEqual(core.load()[0]['applicability'], rule()['applicability'])

    def test_import_is_draft_and_idempotent(self):
        with tempfile.TemporaryDirectory() as d, patch.object(core, 'STORE', Path(d) / 'criteria.json'), patch.object(episodes, 'load', return_value=[EP]):
            path = Path(d) / 'result.json'
            path.write_text(json.dumps({'criteria': [rule()]}))
            build.import_result(path)
            build.import_result(path)
            self.assertEqual(len(core.load()), 1)
            self.assertEqual(core.load()[0]['lifecycle']['status'], 'draft')
            self.assertFalse(core.load()[0]['applicability']['reviewed'])

    def test_import_invalid_batch_never_partially_saves(self):
        with tempfile.TemporaryDirectory() as d, patch.object(core, 'STORE', Path(d) / 'criteria.json'), patch.object(episodes, 'load', return_value=[EP]):
            path = Path(d) / 'result.json'
            invalid = rule(); invalid['evidence'][0]['quote'] = 'invented'
            path.write_text(json.dumps({'criteria': [rule(), invalid]}))
            with self.assertRaises(ValueError): build.import_result(path)
            self.assertEqual(core.load(), [])

    def test_runtime_rechecks_evidence(self):
        with patch.object(episodes, 'load', return_value=[EP]):
            self.assertEqual(len(core.match(SNAP, [rule()])), 1)
        with patch.object(episodes, 'load', return_value=[]):
            self.assertEqual(core.match(SNAP, [rule()]), [])


if __name__ == '__main__': unittest.main()
