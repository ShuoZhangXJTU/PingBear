"""Stage loading, hourglass handoffs, evidence retention and scope regression checks."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2] / 'scripts'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'src'))
import industry
import industry_workflow as flow
import insight_policy
import knowledge
import rubrics_bridge


def report():
    return {'answer':'有条件的结论','differences':['体验与技术链'],'competitors':[],
            'scenarios':[],'business_models':[],'commercial_bets':[],
            'gaps':[],'opportunities':[],'watchlist':[]}


def outputs():
    return {'scope':{'decision':'比较方案','user_task':'测试任务','boundaries':'测试范围','unknowns':[]},
            'scan':{'players':['A','B'],'web_queries':['query'],'scenarios':['场景']},
            'select':{'selected':[{'id':'web-1','reason':'关键差异'}], 'deferred':[{'id':'web-2','reason':'同类重复'}], 'questions':['真实效果？']},
            'verify':{'claims':[{'claim':'测试主张','evidence_ids':['web-1'],'conditions':'测试条件','observations':'测试材料','limitations':'仅fixture','status':'supported'}],'gaps':[]},
            'synthesize':{'relationships':['测试关系'],'experience_technology_tradeoffs':[], 'alternative_explanations':[], 'implications':[], 'unresolved':[]},
            'deliver':report()}


class InsightStandardsTests(unittest.TestCase):
    def test_loads_only_current_card_with_small_budget(self):
        for stage in insight_policy.STAGES:
            s=insight_policy.render(stage)
            self.assertLess(len(s),650)
            self.assertEqual(s.count('【当前环节：'),1)
        self.assertNotIn('差评',insight_policy.render('scope'))
        self.assertNotIn('商业成功',insight_policy.render('scan'))
        self.assertNotIn('【当前环节：',insight_policy.render())
        with self.assertRaises(ValueError):insight_policy.render('guess')

    def test_scanning_preserves_all_candidates_before_reading_pages(self):
        rows=[{'url':'https://example.org/'+str(i),'title':str(i),'snippet':'text','query':'q'} for i in range(4)]
        with patch.object(industry,'web_search',return_value=rows),patch.object(industry,'page_text',side_effect=AssertionError('too early')):
            evidence=industry.gather_web(['q'],pages=1)
        self.assertEqual(len(evidence),4)
        self.assertTrue(all(not e['text'] for e in evidence))

    def test_six_stage_order_and_filtered_handoffs(self):
        fake_outputs=outputs();calls=[]
        def fake(prompt,payload,schema,out,log,**kwargs):
            stage=kwargs['rubric_stage'];calls.append((stage,payload))
            return json.loads(json.dumps(fake_outputs[stage]))
        evidence=[{'id':'web-'+str(i),'kind':'web','title':'candidate','url':'https://example.org/'+str(i),'summary':'summary','text':''} for i in range(1,4)]
        with tempfile.TemporaryDirectory() as d,patch.object(flow,'ROOT',Path(d)),patch.object(knowledge,'codex_json',side_effect=fake):
            planned=flow.plan('topic')
            fetch=unittest.mock.Mock(return_value='SELECTED PAGE')
            data=flow.insight('topic',planned,evidence,[],deep_limit=1,fetcher=fetch)
            pool=json.loads((Path(planned['_run_dir'])/'evidence-pool.json').read_text())
            self.assertEqual(len(pool),3)
            self.assertEqual(fetch.call_count,1)
            self.assertEqual(calls[3][1]['evidence'][0]['text'],'SELECTED PAGE')
            self.assertEqual({e['id'] for e in calls[5][1]['evidence']},{'web-1'})
            self.assertEqual(len(data['_workflow']['selection']['deferred']),2)
        self.assertEqual([s for s,p in calls],list(insight_policy.STAGES))

    def test_handoff_rejects_unknown_and_duplicate_selection(self):
        evidence=[{'id':'a'}]
        for selected in [[{'id':'invented','reason':'x'}],[{'id':'a','reason':'x'},{'id':'a','reason':'y'}]]:
            with self.assertRaises(ValueError):flow.check_selection({'selected':selected,'deferred':[]},evidence,2)
        with self.assertRaises(ValueError):flow.check_selection({'selected':[{'id':'a','reason':'x'}],'deferred':[]},evidence,0)

    def test_resolved_claim_requires_real_reference_and_observation(self):
        c=outputs()['verify']
        with self.assertRaises(ValueError):flow.check_verification(c,[{'id':'other'}])
        c['claims'][0]['evidence_ids']=[]
        with self.assertRaises(ValueError):flow.check_verification(c,[])
        c['claims'][0]['status']='unresolved'
        flow.check_verification(c,[])

    def test_explanation_precedes_competitor_table(self):
        with tempfile.TemporaryDirectory() as d,patch.object(industry,'OUT',Path(d)),patch.object(industry,'build_index'):
            p=industry.render('topic',{'web_queries':[]},[],[],report(),'test')
            s=p.read_text()
            self.assertLess(s.index('核心体验变化'),s.index('竞品清单'))

    def test_shared_model_entry_receives_explicit_stage(self):
        from types import SimpleNamespace
        seen=[]
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'industry/scan.json'
            def fake(*args,**kwargs):out.write_text('{"ok":true}');return SimpleNamespace(returncode=0)
            def context(task,stage=None):seen.append((task,stage));return 'ONLY_THIS_STAGE'
            with patch.object(rubrics_bridge,'context',side_effect=context),patch.object(knowledge.subprocess,'run',side_effect=fake):
                knowledge.codex_json('TASK',{}, {}, out,Path(d)/'test.log',rubric_stage='scan')
        self.assertEqual(seen,[('industry_insight','scan')])

    def test_actual_bridge_does_not_repeat_raw_genomes(self):
        value=rubrics_bridge.context('industry_insight',stage='verify')
        self.assertLess(len(value),650)
        self.assertIn('深核',value)
        self.assertNotIn('episode_id',value)
        self.assertNotIn('当时动机',value)


if __name__=='__main__':unittest.main()
