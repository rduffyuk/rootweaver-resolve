import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {pathToFileURL, fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const root=process.env.RESOLVE_WORKSPACE ?? fileURLToPath(new URL('../src/rootweaver_resolve/workspace/',import.meta.url));
const {guideFor,retainedRecord,inputRows,evidenceSources}=await import(pathToFileURL(join(root,'guide.mjs')));
const cases=Object.fromEntries(['http','selector','dns','policy'].map(name=>[name,JSON.parse(readFileSync(join(root,'data',name+'.json'),'utf8'))]));

test('every guided source resolves without inventing a model evidence identity',()=>{
  for(const data of Object.values(cases)) {
    const before=JSON.stringify(data),guide=guideFor(data);
    assert.equal(guide.steps.length,4);
    for(const step of guide.steps)for(const ref of [...step.refs,...step.inputRefs])assert.ok(retainedRecord(data,ref).source);
    assert.equal(JSON.stringify(data),before);
  }
});
test('policy source collection survives an unexecuted second request',()=>{
  const data=cases.policy,step=guideFor(data).steps[2];
  assert.equal(data.inputs.length,1);assert.equal(step.status,'Second call not sent');assert.equal(step.inputRefs.length,0);
  const records=step.refs.map(ref=>retainedRecord(data,ref));
  assert.equal(records.find(row=>row.id==='file:during-observe-logs.json').source.observations.length,408);
  assert.ok(records.some(row=>row.id==='file:during-observe-networkpolicies.json'));
  assert.ok(records.every(row=>row.projection===null));
});
test('HTTP collection count is distinct from the actual model projection',()=>{
  const data=cases.http,step=guideFor(data).steps[2];
  assert.equal(retainedRecord(data,step.refs[0]).source.observations.length,68);
  assert.equal(inputRows(data,1).find(r=>r.operation==='kubernetes_application_logs').data.length,6);
  assert.match(step.receipt.find(r=>r[0]==='Given to Ultra')[1],/6 selected log events/);
});
test('controller findings stay independent of contradictory supported model labels',()=>{
  assert.match(guideFor(cases.http).steps[1].result,/ruled out/);
  assert.match(guideFor(cases.selector).steps[1].result,/selection failure is supported/);
  assert.equal(cases.http.decisions[1].proposal.hypotheses.find(h=>h.id==='service-selection').assessment,'supported');
});
test('DNS guide retains the input-window confound',()=>{
  const guide=guideFor(cases.dns);
  assert.match(guide.steps[0].receipt.at(-1)[1],/failures were omitted/);
  assert.match(guide.steps[2].model.limit,/both logs and DNS/);
});
test('next checks are authored suggestions and never represented as executed',()=>{
  for(const data of Object.values(cases)) {
    const step=guideFor(data).steps[3];
    assert.equal(step.status,'Suggested · not run');assert.equal(step.refs.length,0);
    assert.match(step.receipt[0][1],/Authored/);assert.match(step.receipt[1][1],/has not been run/);
  }
});
test('every evidence-library button has a retained source',()=>{
  for(const data of Object.values(cases))for(const entry of evidenceSources(data)){
    assert.ok(entry.refs.length);for(const ref of entry.refs)assert.ok(retainedRecord(data,ref).source);
  }
});
test('all seven original public responses retain their declared bytes',()=>{
  let n=0;
  for(const data of Object.values(cases))for(let i=0;i<data.decisions.length;i++){
    const hash=createHash('sha256').update(data.decisions[i].raw_public_response).digest('hex');
    assert.equal(hash,data.model_hashes[i].public_response_sha256);n++;
  }
  assert.equal(n,7);
});
