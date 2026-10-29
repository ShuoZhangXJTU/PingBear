import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import datetime as dt
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import activity
import publish_review
import bridge
import config
import core


class IntegrationTests(unittest.TestCase):
    def test_duplicate_idea_is_one_signal(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root / '灵感').mkdir()
            for name in ['RSI', '评测']:
                (root / '灵感' / (name + '.md')).write_text('- 2026-10-14 09:59　RSI 需要可验证反馈\n')
            events = activity.collect(root)
            self.assertEqual(len(events), 1)

    def test_archive_source_date_is_not_action_date(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root / '论文').mkdir()
            (root / '论文/p.md').write_text('---\nentry_id: p\ntitle: Memory paper\nselected_from: 2026-10-14\nopened: 2026-10-15\n---\n')
            events = activity.collect(root)
            self.assertIsNone(next(e for e in events if e['kind'] == 'archived')['date'])
            self.assertEqual(next(e for e in events if e['kind'] == 'opened')['date'], '2026-10-15')

    def test_answers_do_not_count_as_user_interest(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root / '问答').mkdir()
            (root / '问答/p.md').write_text('## Q1（2026-10-10 10:00）\n\n这是做什么的？\n\n### 答\n\nRSI memory 后训练\n')
            events = activity.collect(root)
            self.assertEqual(events[0]['text'], '这是做什么的？')
            self.assertEqual(events[0]['topics'], ['未分类'])

    def test_feed_does_not_count_as_attention(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root / '日报').mkdir()
            (root / '日报/2026-10-15.md').write_text('RSI memory paper\n' * 100)
            self.assertEqual(activity.collect(root), [])

    def test_recent_window_excludes_future_and_unknown(self):
        events = [{'date': d} for d in [None, '2026-10-01', '2026-10-02', '2026-10-15', '2026-10-16']]
        self.assertEqual([e['date'] for e in activity.recent_events(events, dt.date(2026, 10, 15))], ['2026-10-02', '2026-10-15'])

    def test_generated_block_preserves_manual_feedback(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'note.md'
            p.write_text('我的手写\n')
            activity.replace_block(p, 'first')
            with p.open('a') as f: f.write('\n我的反馈\n')
            activity.replace_block(p, 'second')
            self.assertIn('我的手写', p.read_text())
            self.assertIn('我的反馈', p.read_text())
            self.assertNotIn('first', p.read_text())

    def test_cloud_manual_change_is_preserved(self):
        self.assertEqual(publish_review.merge_manual('base', 'base', 'phone edit'), 'phone edit')
        self.assertEqual(publish_review.merge_manual('base', 'local edit', 'base'), 'local edit')
        self.assertEqual(publish_review.merge_manual('base', 'base\nlocal', 'base\nphone'), 'base\nlocal\nphone')
        with self.assertRaises(ValueError): publish_review.merge_manual('base', 'local edit', 'phone edit')

    def test_custom_sync_markers_and_home_navigation_preserve_manual_text(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'page.md';p.write_text('# Title\n\n用户手写\n')
            activity.replace_block(p,'first',start='<!-- x -->',end='<!-- /x -->',top=True)
            activity.replace_block(p,'second',start='<!-- x -->',end='<!-- /x -->',top=True)
            text=p.read_text()
            self.assertIn('用户手写',text)
            self.assertEqual(text.count('<!-- x -->'),1)
            self.assertLess(text.index('second'),text.index('用户手写'))
            self.assertNotIn(activity.START,text)

    def test_publisher_keeps_flywheel_marker_namespace(self):
        with tempfile.TemporaryDirectory() as d:
            root,cloud=Path(d)/'local',Path(d)/'cloud'
            (root/'研究路线').mkdir(parents=True);cloud.mkdir()
            start,end='<!-- flywheel:start -->','<!-- flywheel:end -->'
            (root/'研究路线/飞轮.md').write_text('# 飞轮\n'+start+'\n真实状态\n'+end)
            (cloud/'研究路线').mkdir()
            (cloud/'研究路线/飞轮.md').write_text('# 飞轮\n'+activity.START+'\n旧状态\n'+activity.END+'\n手机备注')
            publish_review.publish(root,cloud)
            value=(cloud/'研究路线/飞轮.md').read_text()
            self.assertIn(start,value);self.assertNotIn(activity.START,value)
            self.assertIn('手机备注',value)

    def test_mount_off_returns_no_context(self):
        with patch.object(config, 'is_mounted', return_value=False):
            self.assertEqual(bridge.context({'project': 'research'}), '')

    def test_snapshot_fingerprint_stable_on_rescan(self):
        with tempfile.TemporaryDirectory() as d, patch.object(core, 'load', return_value=[]):
            root = Path(d)
            a = activity.run(root, dt.date(2026, 10, 15))
            b = activity.run(root, dt.date(2026, 10, 15))
            self.assertEqual(a['fingerprint'], b['fingerprint'])

    def test_generated_instructions_are_not_personal_evidence(self):
        import genome
        from test_genome import rule, EP
        injected = dict(EP, origin='injected_context')
        with self.assertRaises(ValueError): genome.validate(rule(), {EP['id']: injected})

    def test_research_model_prompt_receives_bridge_context(self):
        from types import SimpleNamespace
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
        import knowledge
        import rubrics_bridge
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'deepen' / 'test.json'
            log = Path(d) / 'test.log'
            captured = []
            def fake_run(command, **kwargs):
                captured.append(kwargs['input'])
                out.write_text('{"ok":true}')
                return SimpleNamespace(returncode=0)
            with patch.object(rubrics_bridge, 'context', return_value='CONFIRMED_RUBRIC'), patch.object(knowledge.subprocess, 'run', side_effect=fake_run):
                result = knowledge.codex_json('TASK:', {'source':'data'}, {}, out, log)
            self.assertTrue(result['ok'])
            self.assertTrue(captured[0].startswith('CONFIRMED_RUBRIC'))
            self.assertIn('TASK:', captured[0])


if __name__ == '__main__': unittest.main()
