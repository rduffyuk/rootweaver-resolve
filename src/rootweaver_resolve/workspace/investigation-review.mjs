import {observationSummary,boundReview,assessmentFor,operatorReadout,hypothesisComparison,packetTiming} from './investigation-view.mjs';
const $=id=>document.getElementById(id);
const el=(tag,text,attrs={})=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);return n;};
const svgEl=(tag,attrs={},text)=>{const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;return n;};
const assessmentLabel=value=>({unresolved:'Still possible',favoured:'Worth pursuing',weakened:'Less likely',rejected:'Rejected by model'}[value]??value);
let session,sessionRaw,selected=0,origin,review=null,loadRevision=0;
function show(title,value,method=false,trigger=document.activeElement){
  origin=trigger;$('method-drawer-title').textContent=title;
  const body=$('method-drawer-body');body.replaceChildren();
  if(method){body.append(el('p','This is the recorded method. Reading or copying it does not execute it. A later command observes a new time window; archived output preserves the historical result.'));
    body.append(el('h3','Human reproduction'),el('pre',value.human_equivalent??'No human equivalent was recorded.'));
    body.append(el('h3','Exact bound tool request and scope'));}
  body.append(el('pre',JSON.stringify(value,null,2)));
  $('method-drawer').showModal();$('method-close').focus();
}
function reference(id,label){
  const receipt=session.steps.map(s=>s.receipt).find(r=>r?.evidence_id===id);
  const b=el('button',label??(receipt?'Evidence: '+receipt.title:'Unresolved reference: '+id),{class:'method-ref'});
  b.onclick=e=>show('Complete evidence receipt',receipt??{unresolved_reference:id},false,e.currentTarget);return b;
}
function go(index){selected=index;render();$('check-heading').focus({preventScroll:true});}
function renderTiming(){
  const receipt=session.steps.filter(s=>s.disposition==='accepted'&&s.receipt?.status==='ok').map(s=>s.receipt).find(r=>packetTiming(r));
  const timing=packetTiming(receipt);$('timing-figure').hidden=!timing;$('timing-plot').replaceChildren();
  if(!timing)return;
  const e=timing.example,max=Math.max(e.clientFinMs,e.serverPayloadMs,1),x=t=>20+380*t/max;
  const svg=svgEl('svg',{viewBox:'0 0 420 156',role:'img','aria-label':`TCP stream ${e.stream}: client FIN ${e.clientFinMs} milliseconds after client payload; first server payload ${e.serverPayloadMs} milliseconds after client payload.`});
  svg.append(svgEl('line',{x1:20,y1:65,x2:400,y2:65,stroke:'#56727f','stroke-width':2}));
  const points=[{time:0,label:'Request sent',value:'0 ms',y:111,color:'#7cc8ef',anchor:'start'},
    {time:e.clientFinMs,label:'Client FIN',value:`${Math.round(e.clientFinMs)} ms`,y:22,color:'#f2c770',anchor:'middle'},
    {time:e.serverPayloadMs,label:'First server data',value:`${Math.round(e.serverPayloadMs)} ms`,y:111,color:'#9ae0c3',anchor:'end'}];
  for(const p of points){svg.append(svgEl('circle',{cx:x(p.time),cy:65,r:5,fill:p.color}),svgEl('text',{x:x(p.time),y:p.y,fill:p.color,'font-size':13,'text-anchor':p.anchor},p.label),svgEl('text',{x:x(p.time),y:p.y+19,fill:'#e5eff3','font-size':16,'text-anchor':p.anchor},p.value));}
  $('timing-plot').append(svg);
  $('timing-scope').textContent=`Stream ${e.stream}, measured from client payload; rounded for display. ${timing.paired} complete FIN/response pairs; ${timing.partial} other streams lack one or both timings. Transport timing does not explain the server’s wait.`;
}
function renderHypotheses(step,assessment){
  $('hypothesis-stage').textContent=(step.disposition==='denied'?'Last accepted assessment; rejected answer not applied. ':assessment!==step?'Model reassessment after this check. ':step.receipt?'Model assessment before this check; no accepted reassessment yet. ':'Final model assessment. ')+'Advisory, not proven causes.';
  $('method-hypotheses').replaceChildren();
  const rows=hypothesisComparison(session.steps,selected,session.hypotheses??[]);
  for(const h of rows){
    const label=review?.operator_readout?.hypothesis_labels?.[h.id]??h.statement;
    const card=el('article',undefined,{'data-assessment':h.after});
    const changed=h.before!==null&&h.before!==h.after;
    card.append(el('span',changed?assessmentLabel(h.before)+' → '+assessmentLabel(h.after):assessmentLabel(h.after)+(h.before===h.after?' · unchanged':''),{class:'hypothesis-status'}),el('h3',label));
    const detail=el('details');detail.append(el('summary','Model wording & evidence'),el('p',h.statement),el('p',h.explanation));
    if(h.refines?.length)detail.append(el('p','Refines: '+h.refines.join(', ')));
    for(const ref of h.evidence_ids??[])detail.append(reference(ref));card.append(detail);$('method-hypotheses').append(card);
  }
  const lineage=(session.hypothesis_lineage??[]).filter(edge=>edge.step<=assessment.index);
  if(lineage.length){const history=el('details');history.append(el('summary','Earlier hypothesis refinements · '+lineage.length));
    for(const edge of lineage){history.append(el('p',edge.parent+' → '+edge.child+' · step '+edge.step));
      const parent=[...session.steps].slice(0,edge.step-1).reverse().flatMap(s=>s.proposal?.hypotheses??[]).find(h=>h.id===edge.parent);
      if(parent)history.append(el('p',parent.statement+' · '+parent.assessment+'. '+parent.explanation));}
    $('method-hypotheses').append(history);}
}
function render(){
  const overview=operatorReadout(review,session,null),step=session.steps[selected],next=session.steps[selected+1];
  const story=operatorReadout(review,session,selected),assessment=assessmentFor(session.steps,selected);
  $('incident').textContent=session.incident.split(/(?<=[.!?])\s/)[0];$('incident-context').textContent=session.incident;
  $('finding-title').textContent=overview?.title??'Recorded checks are ready for review';
  $('finding-summary').textContent=overview?.summary??'Follow the collected results and the model’s competing explanations below. No reviewed synthesis is attached to this exact session.';
  $('finding-unknown').textContent=overview?.uncertainty??'A root cause has not been independently established.';
  $('finding-evidence').replaceChildren();
  for(const id of overview?.evidence_ids??[])$('finding-evidence').append(reference(id,overview.evidence_labels?.[id]));
  renderTiming();
  const example=session.steps.every(s=>s.attribution==='authored-method-example');
  const receipts=session.steps.filter(s=>s.receipt);
  const replay=receipts.length&&receipts.every(s=>s.receipt.method?.execution_mode==='replay');
  $('method-notice').textContent=example?'Authored method example over retained evidence; no model selected these checks.':
    (replay?'Model investigation of retained evidence. ':'Recorded live collection. ')+'Playback only · no checks run from this page · cause unproven.';
  $('recovery-note').textContent=review?.recovery_summary??'No separate recovery annotation is attached.';
  $('method-trail').replaceChildren();session.steps.forEach((s,i)=>{
    const row=operatorReadout(review,session,i),b=el('button',undefined,{'aria-current':i===selected?'step':'false'});
    b.append(el('span',String(i+1),{class:'step-number'}));const copy=el('span',row?.short_label??s.receipt?.title??'Human review',{class:'trail-copy'});
    copy.append(el('small',row?.check_label??s.receipt?.status??s.disposition));b.append(copy);b.onclick=()=>go(i);$('method-trail').append(b);
  });
  renderHypotheses(step,assessment);
  $('check-heading').textContent=story?.title??step.receipt?.title??'Human review';
  $('check-attribution').textContent=`Step ${selected+1} of ${session.steps.length} · `+(step.attribution==='authored-method-example'?'Authored example':step.disposition==='accepted'?(step.receipt?'Model-selected check':'Model handover'):'Rejected proposal');
  $('check-disposition').textContent=step.receipt?(step.receipt.status==='ok'?'Collected':step.receipt.status):step.disposition==='denied'?'Not executed':'Human review';
  $('check-did').textContent=story?.checked??step.receipt?.title??'No further check was executed.';
  $('check-result').textContent=story?.found??observationSummary(step.receipt)??(step.disposition==='denied'?'The model proposal was rejected; its requested check was not run.':'The investigation stopped for review.');
  $('check-meaning').textContent=story?.meaning??'Compare the model assessments alongside this result. They remain advisory.';
  $('check-remaining').textContent=story?.remaining??'Inspect the original model uncertainty and complete evidence limits below.';
  $('next-label').textContent=next?.receipt?'Next recorded check':next?'Next recorded step':'Human follow-up · suggested, not run';
  $('check-next').textContent=story?.next??next?.receipt?.title??(next?'Review the model’s next answer.':'Review the evidence and decide whether another scoped investigation is needed.');
  $('next-step').hidden=!next;$('next-step').onclick=()=>go(selected+1);
  $('readout-attribution').textContent=story?'SRE readout: authored after the run by '+review.reviewer+'. Original model wording is below.':'No reviewed readout is attached. Observation summaries are derived from the receipt; the original model response is below.';
  $('check-reason').textContent=step.proposal?.reason??step.error??'No accepted proposal';
  $('check-changes').replaceChildren();for(const change of assessment.changes??[])$('check-changes').append(el('p',change.id+': '+change.before+' → '+change.after));
  if(assessment!==step)$('check-changes').prepend(el('p','Model reassessment (step '+assessment.index+'): '+assessment.proposal.reason));
  if(!$('check-changes').childNodes.length)$('check-changes').append(el('p','No further accepted reassessment is recorded for this step.'));
  $('check-unknown').textContent=assessment.proposal?.uncertainty??'Inspect the failed step.';
  const caveats=review?.steps.filter(r=>r.index===step.index||r.index===assessment.index)??[];
  $('review-caveats').hidden=!caveats.length;$('review-caveat-title').textContent=caveats.length?'Review note: '+caveats[0].headline:'Review notes';
  $('review-caveat-body').replaceChildren(el('p','Post-run annotations by '+(review?.reviewer??'reviewer')+'. These do not alter the model answers or constitute human acceptance.'));
  for(const row of caveats){$('review-caveat-body').append(el('h3','Step '+row.index+' · '+row.headline));for(const note of row.notes)$('review-caveat-body').append(el('p',note));}
  $('expected-outcomes').replaceChildren();for(const outcome of step.proposal?.expected_outcomes??[])$('expected-outcomes').append(el('li',outcome));
  const method=step.receipt?.method??step.input?.available_checks?.find(c=>c.id===step.proposal?.next_check)?.method;
  $('method-open').disabled=!method;$('source-open').disabled=!receipts.length;
  $('method-open').textContent=step.receipt?'Command & scope':'Requested method · not executed';
  $('method-open').onclick=e=>show(step.receipt?'Command & scope':'Requested method · not executed',method,true,e.currentTarget);
  $('source-open').textContent=step.receipt?'See full output':'All collected output';
  $('source-open').onclick=e=>show('Complete collected evidence',step.receipt??receipts.map(s=>s.receipt),false,e.currentTarget);
  $('model-exchange').textContent=JSON.stringify({input:step.input,public_response:step.model??null,proposal:step.proposal,attribution:step.attribution},null,2);
  $('session-record').textContent=sessionRaw;
  $('review-record').textContent=review?JSON.stringify(review,null,2):'No matching annotations loaded for this exact session.';
}
function load(raw){
  const value=JSON.parse(raw);
  if(value?.schema!=='resolve-investigation/v1'||!Array.isArray(value.steps)||!value.steps.length||value.steps.length>16||typeof value.incident!=='string')throw new Error('Unsupported investigation session');
  loadRevision++;session=value;sessionRaw=raw;selected=0;review=null;render();
}
$('method-close').onclick=()=>$('method-drawer').close();$('method-drawer').addEventListener('close',()=>origin?.focus());
$('method-drawer').addEventListener('keydown',event=>{if(event.key!=='Tab')return;const first=$('method-close'),last=$('method-drawer-body');if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}});
$('session-file').onchange=async()=>{try{const file=$('session-file').files[0];if(!file||file.size>16777216)throw new Error('Choose a JSON session smaller than 16 MiB');load(await file.text());}catch(error){$('method-notice').textContent='Unable to open session: '+error.message;}};
$('export-session').onclick=()=>{if(!session)return;const url=URL.createObjectURL(new Blob([sessionRaw],{type:'application/json'}));const a=el('a','',{href:url,download:'resolve-investigation-session.json'});a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
try{
  const response=await fetch('./data/investigation-session.json');if(!response.ok)throw new Error();const raw=await response.text();
  // A file selected while the default fetch was in flight must win.
  if(loadRevision===0){load(raw);const revision=loadRevision,id=session.id;
    try{const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw))),b=>b.toString(16).padStart(2,'0')).join('');
      const note=await fetch('./data/investigation-review-notes.json');const notes=note.ok?await note.json():null;
      if(loadRevision===revision){review=boundReview(notes,id,digest);render();}
    }catch{/* Optional annotations never change the immutable session. */}
  }
}catch{if(!session){$('incident').textContent='Review an investigation session';$('method-notice').textContent='Open a saved session JSON under Full evidence & audit record. No execution takes place in this viewer.';}}
