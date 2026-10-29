import test from 'node:test';
import assert from 'node:assert/strict';
import {sourceValue, statusText, supportedRecords, executionLabel} from '../src/rootweaver_resolve/web/presenter.mjs';

test('controller collection and simulated analysis never appear as live model investigation', () => {
  const data = {model_invoked:false,model_run:{execution_mode:'replay',acquisition_owner:'controller'}};
  assert.equal(executionLabel(data), 'Controller acquisition · Synthetic replay · No model invoked');
  data.model_run.execution_mode = 'simulated';
  assert.equal(executionLabel(data), 'Controller acquisition · Simulated model analysis · Synthetic replay observations');
});

test('insufficiency and abstention never look like an established root cause', () => {
  const data = {result:{state:'INSUFFICIENT_EVIDENCE',diagnosis:null},assessment:{verdict:'INCOMPLETE'}};
  assert.equal(statusText(data), 'Root cause not established');
  data.result.state = 'ABSTAINED';
  assert.equal(statusText(data), 'Diagnosis withheld');
  data.result.state = 'HYPOTHESIS_UPDATED'; data.assessment.verdict = 'SUPPORTED';
  assert.match(statusText(data), /pending validation/);
});
test('only emitted claims with matching supported records enter conclusion list', () => {
  const claim = {predicate:'service_exists',evidence_ids:['actual']};
  const support = {claim,assessment:{verdict:'SUPPORTED'}};
  const data = {result:{claims:[claim],support_records:[support]}};
  assert.deepEqual(supportedRecords(data), [support]);
  data.result.support_records = [{...support,assessment:{verdict:'UNSUPPORTED'}}, {claim:{...claim,evidence_ids:['unrelated']},assessment:{verdict:'SUPPORTED'}}];
  assert.deepEqual(supportedRecords(data), []);
});
test('source pointers resolve metadata and exact decoded resource fields', () => {
  const evidence = {batch:{source_id:'synthetic',resources_json:'[{"selector":{"app":"checkout"},"a/b":{"~key":false}}]'}};
  assert.equal(sourceValue(evidence, '/source_id'), 'synthetic');
  assert.deepEqual(sourceValue(evidence, 'resources_json#/0/selector'), {app:'checkout'});
  assert.equal(sourceValue(evidence, 'resources_json#/0/a~1b/~0key'), false);
  assert.throws(() => sourceValue(evidence, 'resources_json#/0/absent'));
  assert.throws(() => sourceValue(evidence, '/__proto__'));
});

test('a controller technical finding does not promote model abstention to incident causality', () => {
  const data = {result:{state:'ABSTAINED', diagnosis:null,
    technical_findings:[{nomination_origin:'controller', assessment:{verdict:'SUPPORTED'}}],
    incident_assessment:{outcome:'abstained',explains_incident:null}},assessment:{verdict:'SUPPORTED'}};
  assert.equal(statusText(data), 'Technical finding supported · incident cause unresolved');
});

test('model-supported prose stays unverified, verbatim and outside supported claims', async () => {
  const {modelAssertionText} = await import('../src/rootweaver_resolve/web/presenter.mjs');
  const raw = 'The application is correct. '.repeat(15);
  const hypothesis = {id:'application-regression',assessment:'supported',statement:raw,evidence_ids:['actual']};
  assert.equal(modelAssertionText(hypothesis), `Unverified model interpretation · application-regression · model assessment: supported. ${raw}`);
  const data = {result:{claims:[],support_records:[],technical_findings:[]},model_run:{decisions:[{proposal:{hypotheses:[hypothesis]}}]}};
  assert.deepEqual(supportedRecords(data), []);
});
