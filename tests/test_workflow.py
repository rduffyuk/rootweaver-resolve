"""Standalone tests: no private services, credentials or network inference."""
import json
import tempfile
import unittest
from pathlib import Path
from rootweaver_resolve.application import Application
from rootweaver_resolve.controller_led import ControllerLedInvestigator
from rootweaver_resolve.demo import DemoBudget,DemoInvestigator,RetainedClient
from rootweaver_resolve.contracts import Claim,Predicate
from rootweaver_resolve.nebius import ProviderError
from rootweaver_resolve.support import assess

class WorkflowTests(unittest.TestCase):
    def test_four_synthetic_cases_keep_correct_controller_boundary(self):
        for name,want in [('recorded','SUPPORTED'),('matching','REFUTED'),('conflicting','CONTRADICTORY'),('missing','INCOMPLETE')]:
            r=ControllerLedInvestigator(name);result=r.run()
            self.assertEqual(r.view().assessment.verdict,want)
            self.assertEqual(bool(result.technical_findings),name=='recorded')
            self.assertIsNone(result.incident_assessment.explains_incident)
            self.assertTrue(result.action is None or (result.action.human_approval_required and not result.action.executed))
    def test_no_future_evidence_is_acquired_initially(self):
        r=ControllerLedInvestigator('recorded');self.assertEqual(len(r.view().evidence),0);r.step();self.assertEqual(len(r.view().evidence),1)
    def test_readiness_does_not_establish_application_correctness(self):
        r=ControllerLedInvestigator('recorded');r.run()
        a=assess(Claim(Predicate("application_correct"),tuple(e.evidence_id for e in r.view().evidence)),r.incident,r.view().evidence)
        self.assertNotEqual(a.verdict,'SUPPORTED')
    def test_retained_actual_outputs_are_not_live_and_do_not_establish_findings(self):
        import rootweaver_resolve.demo as d
        rows=json.loads((Path(d.__file__).with_name('demo_recordings')/'recorded.json').read_text());app=Application(investigator_factory=lambda s:DemoInvestigator(s,RetainedClient(rows)));state=app.snapshot()
        for _ in range(8):
            if state['terminal']:break
            state=app.step(state['investigation_id'],state['revision'])
        self.assertFalse(state['model_invoked']);self.assertEqual(state['model_run']['execution_mode'],'retained');self.assertEqual(len(state['model_run']['decisions']),2)
        self.assertTrue(all(f['nomination_origin']=='controller' for f in state['result']['technical_findings']))
        self.assertIn('fully explains',state['model_run']['decisions'][1]['raw_public_response']['content'])
        self.assertIsNone(state['result']['incident_assessment']['explains_incident'])
    def test_budget_survives_new_object_and_does_not_count_reasoning_twice(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'budget.json'
            for _ in range(2):
                b=DemoBudget(p);b.reserve(10000,output_tokens=16384);b.settle({'prompt_tokens':10,'completion_tokens':20,'total_tokens':30,'completion_tokens_details':{'reasoning_tokens':15}},1)
            self.assertEqual(DemoBudget(p).snapshot()['tokens'],60)
            with self.assertRaises(ProviderError):DemoBudget(p).reserve(10000,output_tokens=16384)
