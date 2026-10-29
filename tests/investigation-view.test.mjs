import test from 'node:test';
import assert from 'node:assert/strict';
import {observationSummary, boundReview, assessmentFor, operatorReadout, hypothesisComparison, packetTiming} from '../src/rootweaver_resolve/workspace/investigation-view.mjs';

test('log summary includes successful and failed groups without changing evidence',()=>{
  const receipt={summary:'logs',model_data:{counts:{captured:28,included:20,before_window:8,after_window:0,undated_or_unparsed:0},groups:[{count:2,fields:{event:'checkout_response',status:200}},{count:8,fields:{event:'resolver_lookup',status:'error',error_type:'gaierror',errno:-2}}]}};
  const original=JSON.stringify(receipt),text=observationSummary(receipt);
  assert.match(text,/28 captured/);assert.match(text,/20 in the observation window/);assert.match(text,/200/);assert.match(text,/gaierror/);assert.equal(JSON.stringify(receipt),original);
});
test('review notes cannot attach to a different or edited session',()=>{
  const note={session_id:'one',session_sha256:'a'.repeat(64),steps:[]};
  assert.equal(boundReview(note,'one','a'.repeat(64)),note);
  assert.equal(boundReview(note,'two','a'.repeat(64)),null);
  assert.equal(boundReview(note,'one','b'.repeat(64)),null);
});
test('rejected next responses never become accepted reassessments',()=>{
  const step={receipt:{},disposition:'accepted'},next={disposition:'denied'};
  assert.equal(assessmentFor([step,next],0),step);
  assert.equal(assessmentFor([step,{disposition:'accepted'}],0).disposition,'accepted');
});
test('packet summary reports the transport boundary and preserves all source frames',()=>{
  const receipt={model_data:{captured_frames:9,streams:[{syn_ack_frames:['2'],client_payload_bytes:90,server_payload_bytes:0,reset_frames:[],retransmission_frames:[]}]}};
  const original=JSON.stringify(receipt),text=observationSummary(receipt);
  assert.match(text,/9 captured TCP frames/);assert.match(text,/90 client/);assert.match(text,/0 server/);
  assert.match(text,/application execution/);assert.equal(JSON.stringify(receipt),original);
});

test('operator readouts require references available at the selected step',()=>{
  const session={steps:[{index:1,disposition:'accepted',receipt:{evidence_id:'logs',status:'ok'}},{index:2,disposition:'accepted',receipt:{evidence_id:'packets',status:'ok'}}]};
  const first={index:1,title:'Timeouts',evidence_ids:['logs']};
  const review={operator_readout:{overview:{title:'Late reply',evidence_ids:['packets']},steps:[first]}};
  assert.equal(operatorReadout(review,session,0),first);
  assert.equal(operatorReadout(review,session,null).title,'Late reply');
  first.evidence_ids=['packets'];
  assert.equal(operatorReadout(review,session,0),null);
  session.steps[1].disposition='denied';
  assert.equal(operatorReadout(review,session,null),null);
  assert.equal(operatorReadout(null,session,0),null);
});

test('hypothesis comparison uses accepted reassessment and keeps hypotheses advisory',()=>{
  const hypothesis=(assessment)=>({id:'path',statement:'Packet drop',assessment});
  const steps=[{disposition:'accepted',receipt:{},proposal:{hypotheses:[hypothesis('unresolved')]}},{disposition:'accepted',proposal:{hypotheses:[hypothesis('weakened')]}}];
  const original=JSON.stringify(steps);
  assert.deepEqual(hypothesisComparison(steps,0).map(r=>[r.before,r.after]),[['unresolved','weakened']]);
  assert.equal(JSON.stringify(steps),original);
  steps[1].disposition='denied';
  assert.deepEqual(hypothesisComparison(steps,0).map(r=>[r.before,r.after]),[['unresolved','unresolved']]);
  assert.deepEqual(hypothesisComparison(steps,1).map(r=>r.after),['unresolved']);
});

test('timing diagram pairs within streams, excludes missing values, and counts boundaries',()=>{
  const receipt={model_data:{streams:[
    {stream:'1',client_fin_after_payload_ms:800,first_server_payload_after_client_ms:2000},
    {stream:'2',client_fin_after_payload_ms:810},
    {stream:'3',first_server_payload_after_client_ms:2100},
    {stream:'4',client_fin_after_payload_ms:null,first_server_payload_after_client_ms:null}
  ]}};
  const original=JSON.stringify(receipt),timing=packetTiming(receipt);
  assert.equal(timing.paired,1);assert.equal(timing.partial,3);
  assert.equal(timing.clientFinCount,2);assert.equal(timing.responseCount,2);
  assert.equal(timing.example.clientFinMs,800);assert.equal(timing.example.serverPayloadMs,2000);
  assert.equal(JSON.stringify(receipt),original);
  assert.equal(packetTiming({model_data:{streams:[]}}),null);
  assert.equal(packetTiming({model_data:{streams:[{client_fin_after_payload_ms:800}]}}),null);
});
