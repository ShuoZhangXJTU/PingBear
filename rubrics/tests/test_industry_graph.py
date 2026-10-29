"""Meaningful mutation/recovery tests: independent branches, stale writes and incremental runs."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2] / 'scripts'))
from industry_graph import Graph, StaleInput
import industry_workflow as flow
import industry
import knowledge
from test_insight_standards import outputs


class ArtifactGraphTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.g=Graph(Path(self.tmp.name))

    def branch_graph(self):
        self.g.put_inputs({'a':{'v':1},'b':{'v':1}})
        self.g.build('va',['a'],'r',lambda d:{'v':d['a']['v']})
        self.g.build('vb',['b'],'r',lambda d:{'v':d['b']['v']})
        self.g.build('joint',['va','vb'],'r',lambda d:d)

    def test_invalidation_preserves_outputs_and_independent_branch(self):
        self.branch_graph();old=self.g.load()['nodes']['va']['head']
        affected=self.g.invalidate('a','recheck')
        self.assertEqual(set(affected),{'va','joint'})
        self.assertEqual(self.g.summary()['vb']['status'],'fresh')
        self.assertEqual(self.g.load()['nodes']['va']['head'],old)
        self.assertEqual(self.g.read('va',require_fresh=False),{'v':1})
        with self.assertRaises(StaleInput):self.g.read('joint')

    def test_restoring_exact_upstream_version_revalidates_old_descendants(self):
        self.branch_graph();old=self.g.load()['nodes']['a']['head']
        self.g.put_inputs({'a':{'v':2}})
        self.assertEqual(self.g.summary()['joint']['status'],'stale')
        self.g.restore('a',old,'return to accepted source')
        self.assertTrue(all(v['status']=='fresh' for v in self.g.summary().values()))
        self.assertEqual(self.g.read('a'),{'v':1})

    def test_undo_keeps_both_versions(self):
        self.g.put_inputs({'a':1});first=self.g.load()['nodes']['a']['head']
        self.g.put_inputs({'a':2});self.g.undo('a','undo')
        self.assertEqual(self.g.load()['nodes']['a']['head'],first)
        self.assertEqual(self.g.summary()['a']['revisions'],2)
        self.assertEqual(self.g.read('a'),1)

    def test_undo_after_restore_follows_actual_branch_parent(self):
        self.g.put_inputs({'a':1});first=self.g.load()['nodes']['a']['head']
        self.g.put_inputs({'a':2})
        self.g.restore('a',first,'branch from v1')
        self.g.put_inputs({'a':3});self.g.undo('a','undo branch')
        self.assertEqual(self.g.read('a'),1)

    def test_failed_rebuild_does_not_replace_accepted_result(self):
        self.g.put_inputs({'a':1});self.g.build('v',['a'],'r',lambda d:10)
        old=self.g.load()['nodes']['v']['head']
        def fail(d):raise RuntimeError('model failed')
        with self.assertRaises(RuntimeError):self.g.build('v',['a'],'r',fail,force=True)
        self.assertEqual(self.g.load()['nodes']['v']['head'],old)
        self.assertEqual(self.g.read('v'),10)

    def test_changed_input_during_computation_rejects_commit(self):
        self.g.put_inputs({'a':1})
        def race(d):self.g.put_inputs({'a':2});return d['a']
        with self.assertRaises(StaleInput):self.g.build('v',['a'],'r',race)
        self.assertNotIn('v',self.g.load()['nodes'])

    def test_cycle_rejected_without_changing_heads(self):
        self.g.put_inputs({'a':1});self.g.build('b',['a'],'r',lambda d:2)
        before=self.g.load()['nodes']['a']['head'];versions,_=self.g.snapshot(['b'])
        with self.assertRaises(ValueError):self.g.commit('a',3,versions,'r')
        self.assertEqual(self.g.load()['nodes']['a']['head'],before)

    def test_cached_node_does_not_recompute(self):
        self.g.put_inputs({'a':1});self.g.build('b',['a'],'r',lambda d:2)
        with patch('builtins.print'):
            result=self.g.build('b',['a'],'r',lambda d:self.fail('cache missed'))
        self.assertEqual(result,2)

    def test_checksum_detects_modified_artifact(self):
        self.g.put_inputs({'a':1});record=self.g.record(self.g.load(),'a')
        (self.g.directory/record['path']).write_text('2')
        with self.assertRaises(ValueError):self.g.read('a')

    def test_progress_records_running_failure_and_old_artifact_validity_independently(self):
        self.g.put_inputs({'a':1})
        def compute(d):
            self.assertEqual(self.g.load()['attempts']['v']['status'],'running')
            self.assertEqual(self.g.summary()['v']['execution']['status'],'running')
            self.assertEqual(self.g.summary()['v']['status'],'missing')
            return 10
        self.g.build('v',['a'],'r',compute)
        self.assertEqual(self.g.load()['attempts']['v']['status'],'completed')
        def fail(d):raise RuntimeError('test')
        with self.assertRaises(RuntimeError):self.g.build('v',['a'],'r',fail,force=True)
        self.assertEqual(self.g.load()['attempts']['v']['status'],'failed')
        self.assertEqual(self.g.summary()['v']['status'],'fresh')
        self.g.build('v',['a'],'r',lambda d:self.fail('should reuse'))
        self.assertEqual(self.g.load()['attempts']['v']['status'],'cached')

    def test_dashboard_reports_no_run_without_inventing_progress(self):
        from industry_status import render
        self.assertIn('尚无真实六环节运行记录',render(Path(self.tmp.name)))

    def test_dashboard_shows_interruption_and_stale_dependency(self):
        from industry_status import render
        root=Path(self.tmp.name);self.g=Graph(root/'.research/industry/runs/test')
        self.g.put_inputs({'a':1})
        self.g.build('verify',['a'],'r',lambda d:10)
        self.g.put_inputs({'a':2})
        page=render(root)
        self.assertIn('待复核',page)
        self.assertIn('当前有效产出：0/6',page)


class WorkflowGraphTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.calls=[];self.fixture=outputs()
        self.root_patch=patch.object(flow,'ROOT',self.root);self.root_patch.start();self.addCleanup(self.root_patch.stop)
        def fake(prompt,payload,schema,out,log,**kw):
            self.calls.append(kw['rubric_stage']);return copy.deepcopy(self.fixture[kw['rubric_stage']])
        self.model_patch=patch.object(knowledge,'codex_json',side_effect=fake);self.model_patch.start();self.addCleanup(self.model_patch.stop)
        self.planned=flow.plan('topic')
        self.evidence=[{'id':'web-'+str(i),'kind':'web','url':'https://example.org/'+str(i),'title':'candidate','summary':'summary','text':'body'} for i in range(1,4)]
        self.data=flow.insight('topic',self.planned,self.evidence,[],deep_limit=1)
        self.g=Graph(self.planned['_run_dir']);self.calls.clear()

    def test_resume_unchanged_run_makes_no_model_calls(self):
        flow.resume(self.g.directory)
        self.assertEqual(self.calls,[])

    def test_manual_verification_correction_rebuilds_only_synthesis_and_delivery(self):
        corrected=self.g.read('verify');corrected['gaps']=['new gap']
        flow.replace_node(self.g,'verify',corrected,'correct interpretation')
        self.assertEqual(self.g.summary()['scan']['status'],'fresh')
        self.assertEqual(self.g.summary()['synthesize']['status'],'stale')
        flow.resume(self.g.directory)
        self.assertEqual(self.calls,['synthesize','deliver'])
        self.assertEqual(self.g.read('verify')['gaps'],['new gap'])

    def test_unselected_body_change_does_not_invalidate_report(self):
        source=self.g.read('source:web-3');source['text']='corrected unselected body'
        flow.replace_node(self.g,'source:web-3',source,'source correction')
        self.assertEqual(self.g.summary()['deliver']['status'],'fresh')
        flow.resume(self.g.directory)
        self.assertEqual(self.calls,[])

    def test_selected_body_change_rebuilds_only_dependent_stages(self):
        source=self.g.read('source:web-1');source['text']='corrected selected body'
        flow.replace_node(self.g,'source:web-1',source,'source correction')
        self.assertEqual(self.g.summary()['select']['status'],'fresh')
        self.assertEqual(self.g.summary()['deliver']['status'],'stale')
        flow.resume(self.g.directory)
        self.assertEqual(self.calls,['verify','synthesize','deliver'])

    def test_outdated_report_cannot_be_published(self):
        self.g.invalidate('verify','evidence recheck')
        with self.assertRaises(StaleInput):
            industry.render('topic',self.planned,self.evidence,[],self.data,'test')

    def test_scope_change_requires_reacquisition_when_search_changes(self):
        scope=self.g.read('scope');scope['decision']='new decision'
        flow.replace_node(self.g,'scope',scope,'goal change')
        with self.assertRaises(StaleInput):flow.resume(self.g.directory)
        self.assertEqual(self.calls,['scan'])

    def test_bad_manual_reference_does_not_commit(self):
        old=self.g.load()['nodes']['verify']['head'];data=self.g.read('verify')
        data['claims'][0]['evidence_ids']=['invented']
        with self.assertRaises(ValueError):flow.replace_node(self.g,'verify',data,'bad correction')
        self.assertEqual(self.g.load()['nodes']['verify']['head'],old)


if __name__=='__main__':unittest.main()
