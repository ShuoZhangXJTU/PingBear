"""核心行为的回归测试：不联网、不调用模型，保证重构（拆包）时不改变行为。"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import catalog
import ideas
import inbox
import knowledge
import research
import weixin_bridge


class TestTags(unittest.TestCase):
    def test_vocabulary_loaded_from_config(self):
        self.assertGreaterEqual(len(research.TAGS), 5)
        self.assertIn('Harness', research.TAGS)
        self.assertIn('其他', research.TAGS)


class TestArchivePaths(unittest.TestCase):
    def test_note_path_uses_topic_and_title(self):
        paper = {'id': '2609.12345', 'title': 'A/B Testing: Does It Work?',
                 'tags': ['Harness'], 'topics': []}
        path = research.note_path(Path('/tmp/root'), paper)
        self.assertEqual(str(path.relative_to('/tmp/root')), '论文/Harness/A B Testing Does It Work.md')

    def test_note_path_falls_back_to_other(self):
        paper = {'id': 'link-abc123', 'title': '', 'tags': []}
        path = research.note_path(Path('/tmp/root'), paper)
        self.assertTrue(str(path.relative_to('/tmp/root')).startswith('论文/其他/'))
        self.assertIn('link-abc123', path.name)

    def test_field_marker_in_archive(self):
        paper = {'id': '2609.12345', 'title': 'T', 'tags': ['RSI']}
        head, tags = research.note_fields(paper, '2026-10-01')
        self.assertEqual(tags, ['RSI'])
        self.assertIn('tags:', head)
        self.assertIn('  - RSI', head)


class TestIdeaRouting(unittest.TestCase):
    def test_harness_keywords(self):
        self.assertIn('Harness', ideas.topics_of('现在 jev as router 或者 controller 是个应用点'))

    def test_post_training_keywords(self):
        self.assertIn('后训练', ideas.topics_of('GRPO 的 reward 是不是可以改'))

    def test_unknown_goes_other(self):
        self.assertEqual(ideas.topics_of('今天天气不错'), ['其他'])


class TestWeixinCommands(unittest.TestCase):
    def test_archive_command_parses_numbers(self):
        parsed = weixin_bridge.archive_command('归档今天第 2、4 篇', __import__('datetime').date(2026, 10, 1))
        self.assertEqual(parsed, ('2026-10-01', [2, 4]))

    def test_plain_text_is_not_a_command(self):
        self.assertIsNone(weixin_bridge.archive_command('今天第 2 篇写了啥', __import__('datetime').date(2026, 10, 1)))


class TestNoteLayout(unittest.TestCase):
    def test_user_notes_stay_on_top_and_material_moves_to_tail(self):
        # 模拟早期小红书归档笔记：头部 → 截图（无标题）→ OCR（无长标题）→ 来源 → 我的备注
        body = ('# [T](u)\n\n一句话\n\n[PDF](p)\n\n'
                '![图 1](http://img)\n\n'
                'arXiv:2609.12345\n长文本' + 'x' * 300 + '\n\n'
                '来源：[[日报/2026-10-01]]\n\n## 我的备注\n\n- 我的判断\n')
        head, sections = knowledge.split_body(body)
        self.assertIn('## 我的备注', sections)
        self.assertIn('我的判断', sections['## 我的备注'])
        self.assertIn('## 截图', sections)
        self.assertIn('## 截图文字（OCR）', sections)
        self.assertNotIn('长文本', head)
        self.assertIn('# [T](u)', head)


class TestCatalogSources(unittest.TestCase):
    def test_four_sources_registered(self):
        keys = [item[0] for item in catalog.SOURCES]
        self.assertEqual(keys, ['hf', 'xhs', 'inbox', 'blog'])


if __name__ == '__main__':
    unittest.main()
