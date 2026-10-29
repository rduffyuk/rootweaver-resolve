import {sourceValue} from './presenter.mjs';
import {guideFor, retainedRecord, evidenceSources, operationNames} from './guide.mjs';
const $=id=>document.getElementById(id),ns='http://www.w3.org/2000/svg';
const release=await(await fetch('./release.json')).json();let data,guide,stepIndex=0,at=1,timer,origin,selected,tab='summary',loadSequence=0;
const titles=['Baseline','Fault','Enriched','Recovery'];
function element(tag,attrs={},text){const e=document.createElement(tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text!==undefined)e.textContent=text;return e;}
function svg(tag,attrs={},text){const e=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text!==undefined)e.textContent=text;return e;}
function record(id){return retainedRecord(data,id);}
function pause(){clearInterval(timer);timer=null;$('play').disabled=false;}
function play(){pause();if(matchMedia('(prefers-reduced-motion: reduce)').matches){$('announce').textContent='Reduced motion: use Step to advance.';return;}if(at===3)at=0;render();$('play').disabled=true;timer=setInterval(()=>{at++;render();if(at===3)pause();},2400);}
function download(value,name){const blob=new Blob([JSON.stringify(value,null,2)+'\n'],{type:'application/json'}),url=URL.createObjectURL(blob),a=element('a',{href:url,download:name});a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function openEvidence(title,ids,summary,trigger=document.activeElement,extra={}) {
  pause(); origin=trigger;
  selected={title,summary,records:ids.map(record),...extra}; tab=extra.initialTab??'summary';
  $('evidence-title').textContent=title;
  $('evidence-description').textContent=data.public?'Sanitised retained source · no new collection':'Private retained source · no new collection';
  $('copy-id').disabled=!selected.records.length;
  $('export-evidence').disabled=!selected.records.length&&!selected.modelStatement&&!selected.modelInput;
  renderDrawer(); if(!$('evidence').open)$('evidence').showModal();
  $('close-evidence').focus(); $('announce').textContent='Evidence opened: '+title;
}
function renderDrawer() {
  document.querySelectorAll('[data-tab]').forEach(b=>{
    const active=b.dataset.tab===tab; b.id='drawer-tab-'+b.dataset.tab;
    b.setAttribute('aria-controls','drawer-content');b.setAttribute('role','tab');
    b.setAttribute('aria-selected',String(active));b.tabIndex=active?0:-1;
  });
  const pane=$('drawer-content');pane.setAttribute('aria-labelledby','drawer-tab-'+tab);pane.replaceChildren();
  if(tab==='summary') {
    pane.append(element('p',{},selected.summary));
    if(selected.modelStatement) {
      pane.append(element('h3',{},'Exact retained model response · unverified'));
      pane.append(element('pre',{},selected.modelStatement));
    }
    const sample=selected.records.flatMap(r=>Array.isArray(r.projection?.data)?r.projection.data:[]);
    const logs=sample.filter(r=>r.error_type);
    if(logs.length) {
      pane.append(element('h3',{},'Events in this saved model input'));
      const table=element('table'),head=element('tr');
      for(const h of ['Time','Operation / error','HTTP'])head.append(element('th',{},h));
      table.append(head);
      for(const row of logs){const tr=element('tr');tr.append(element('td',{},row.time??row.observed_at??'See source'),element('td',{},(row.operation??'')+' · '+row.error_type),element('td',{},String(row.status??'—')));table.append(tr);}
      pane.append(table);
    }
    for(const r of selected.records) {
      const item=element('div',{class:'source-summary'});
      item.append(element('h3',{},r.provenance?.source_file??'Retained evidence'),element('p',{class:'source-ref'},r.id));
      if(r.source?.observations)item.append(element('p',{},r.source.observations.length+' captured observations. Full source includes every retained record.'));
      if(r.provenance?.observed_at)item.append(element('p',{},'Observed '+r.provenance.observed_at));
      if(r.source===null)item.append(element('p',{class:'warning'},'This citation has no acquired source record.'));
      pane.append(item);
    }
    pane.append(element('p',{class:'section-note'},data.public?'Public observations are sanitised copies. Original evidence IDs refer to private originals; public file hashes are separate. Capture limits remain in the source.':'Original retained records; capture limits remain in the source.'));
  } else if(tab==='projection') {
    if(selected.modelInput) {
      const inputs=Array.isArray(selected.modelInput)?selected.modelInput:[selected.modelInput];
      pane.append(element('h3',{},'Evidence in the saved request'));
      pane.append(element('p',{},'The collection pipeline selected these inputs. Opening this view does not ask Ultra to run a tool.'));
      for(const input of inputs) {
        const rows=input.view.readable_observations;
        const table=element('table'),head=element('tr');
        for(const h of ['Source / tool','What was supplied'])head.append(element('th',{},h));table.append(head);
        for(const row of rows) {
          const tr=element('tr');let count=Array.isArray(row.data)?row.data.length+' records':row.scope??'Retained structured observation';
          tr.append(element('td',{},operationNames[row.operation]??row.operation),element('td',{},count));table.append(tr);
        }
        pane.append(table);
        const logs=rows.filter(r=>r.operation==='kubernetes_application_logs').flatMap(r=>r.data??[]);
        if(logs.length) {
          pane.append(element('h3',{},logs.length+' supplied log events'));
          const table=element('table'),head=element('tr');
          for(const h of ['Time','Operation / error','HTTP'])head.append(element('th',{},h));table.append(head);
          for(const row of logs){const tr=element('tr');tr.append(element('td',{},row.time??'See original input'),element('td',{},(row.operation??'')+' · '+(row.error_type??row.error??'See original input')),element('td',{},String(row.status??'—')));table.append(tr);}
          pane.append(table);
        }
        if(input.previous_public_analysis)pane.append(element('p',{},'The previous model response was also included in this request.'));
      }
      const full=element('details');full.append(element('summary',{},'Complete original model input · no truncation'),element('pre',{},JSON.stringify(selected.modelInput,null,2)));pane.append(full);
    }
    else if(selected.records.some(r=>r.projection)) {
      pane.append(element('p',{},'Recorded evidence projections. These are not the full captured collection.'));
      pane.append(element('pre',{},JSON.stringify(selected.records.map(r=>({reference:r.id,model_projection:r.projection??null})),null,2)));
    } else pane.append(element('p',{},data.id==='policy'?'No second model request was sent. This source collection is retained for inspection, not presented as model input.':'This is a full source collection. Use “What Ultra received” in the guide to inspect the separately retained model input.'));
  } else {
    if(!selected.records.length) pane.append(element('p',{},'No source record is attached to this explanation. Use the guide’s evidence buttons or the full case export.'));
    else pane.append(element('pre',{},JSON.stringify(selected.records.map(r=>tab==='source'?{reference:r.id,source:r.source,selected_fields:r.fields}:{reference:r.id,...r.provenance}),null,2)));
  }
  pane.scrollTop=0;
}
function citation(title,ids,summary,extra={}) {
  const b=element('button',{class:'citation'},title);
  b.onclick=e=>openEvidence(title,ids,summary,e.currentTarget,extra);return b;
}
function showModel(stage,trigger) {
  const decision=data.decisions[stage];
  if(!decision)return;
  openEvidence('Ultra response '+(stage+1),decision.evidence_ids??[],
    'Actual earlier '+decision.model+' response through Nebius Token Factory. Reading this response does not run the model.',trigger,
    {modelStatement:decision.raw_public_response,modelInput:data.inputs[stage]});
}
function showInput(trigger) {
  const current=guide.steps[stepIndex];
  const stage=stepIndex===2&&data.decisions.length>1?1:0;
  openEvidence('What Ultra received · call '+(stage+1),current.inputRefs,
    data.id==='policy'&&stepIndex===2?'Only call 1 completed. Policy/log enrichment was not sent; below is the actual first input.':'Complete saved user input, including the bounded evidence and any earlier model response. Other source records were not automatically supplied.',
    trigger,{initialTab:'projection',modelInput:data.inputs[stage]});
}
function selectStep(index,focus=true) {
  pause();stepIndex=index;at=guide.steps[index].frame;render();
  if(focus){$('step-title').focus({preventScroll:true});$('investigation').scrollIntoView({block:'start',behavior:'instant'});}
  $('announce').textContent='Step '+(index+1)+': '+guide.steps[index].title;
}
function renderGuide() {
  const current=guide.steps[stepIndex];$('guide-steps').replaceChildren();
  guide.steps.forEach((s,i)=>{
    const b=element('button',{'aria-current':i===stepIndex?'step':'false','data-guide-step':i});
    b.append(element('span',{class:'step-number'},String(i+1)),element('span',{},s.label));
    if(i===3)b.append(element('small',{class:'not-executed'},'Not executed'));
    b.onclick=()=>selectStep(i);$('guide-steps').append(b);
  });
  $('step-position').textContent='Step '+(stepIndex+1)+' of '+guide.steps.length;
  $('step-status').textContent=current.status;$('step-status').dataset.kind=stepIndex===3?'suggested':stepIndex===2?'model':'observed';
  $('step-title').textContent=current.title;$('step-why').textContent=current.why;
  $('result-label').textContent=stepIndex===3?'Suggested next investigation':stepIndex===1?'Deterministic check':'Observed in the retained evidence';
  $('step-result').textContent=current.result;
  $('step-receipt').replaceChildren();
  for(const [label,value]of current.receipt)$('step-receipt').append(element('dt',{},label),element('dd',{},value));
  const actions=$('step-actions');actions.replaceChildren();
  if(current.refs.length)actions.append(citation(current.sourceLabel,current.refs,current.result));
  if(data.inputs.length&&(current.inputRefs.length||stepIndex===2)) {
    const b=element('button',{class:'citation'},'What Ultra received');b.onclick=e=>showInput(e.currentTarget);actions.append(b);
  }
  if(current.model) {
    const b=element('button',{class:'citation'},data.id==='policy'?'Read first Ultra response':'Read Ultra’s response');b.onclick=e=>showModel(current.model.stage,e.currentTarget);actions.append(b);
  }
  if(current.model&&data.id==='http'){const live=element('button',{class:'citation'},'Try fresh Ultra analysis');live.onclick=()=>{$('fresh-analysis').scrollIntoView({block:'start',behavior:'instant'});$('fresh-input').focus({preventScroll:true});};actions.append(live);}
  $('ai-summary').hidden=!current.model;
  if(current.model){$('ai-text').textContent=current.model.text;$('ai-limit').textContent=current.model.limit;}
  $('previous').disabled=stepIndex===0;$('next').disabled=stepIndex===guide.steps.length-1;
  $('guide-progress').textContent=(stepIndex+1)+' / '+guide.steps.length;
  $('next').textContent=stepIndex===2?'See next investigation':'Next check';
  $('graph-context').textContent='Step '+(stepIndex+1)+': '+current.label+'. Graph shows the '+titles[at].toLowerCase()+' capture.';
}

function renderGraph(){const f=data.frames[at],all=f.result.evidence.flatMap(e=>{try{return JSON.parse(e.batch.resources_json).map((r,i)=>({r,e,p:'resources_json#/'+i}));}catch{return [];}}),svc=all.find(x=>x.r.kind==='Service'&&x.r.name===f.incident.service),slice=all.find(x=>x.r.kind==='EndpointSlice'&&x.r.service_name===f.incident.service),pod=all.find(x=>x.r.kind==='Pod'&&Object.entries(Object.fromEntries(f.incident.workload_labels)).every(([k,v])=>x.r.labels?.[k]===v));
const ready=(slice?.r.endpoints??[]).filter(e=>e.conditions?.ready===true).length;
const nodes=[{kind:'Service',label:'Service '+(svc?.r.name??'not observed'),description:svc?'Selector '+JSON.stringify(svc.r.selector):'No Service observation',source:svc},{kind:'EndpointSlice',label:slice?'EndpointSlice':'Backend observation',description:slice?ready+' Ready backend(s)':'No slice in acquired record; inspect coverage',source:slice??svc},{kind:'Pod',label:pod?'Pod · '+pod.r.phase:'Pod not observed',description:pod?'Ready='+pod.r.ready+' · '+JSON.stringify(Object.fromEntries(Object.entries(pod.r.labels).filter(([k])=>k==='app'||k==='track'))):'Missing workload evidence',source:pod}];
const appError=data.id==='http'&&(at===1||at===2)&&!!data.forensics['during-observe-logs.json'];
const width=Math.max(280,$('topology').clientWidth),mobile=width<540,w=mobile?width-28:(width-72)/3,h=mobile?104:130,gap=mobile?28:22,height=mobile?3*(h+gap)+12:202,root=svg('svg',{viewBox:`0 0 ${width} ${height}`,role:'group','aria-label':'Evidence-derived Service, EndpointSlice and Pod topology'});root.append(svg('title',{},'Observed topology, independently scoped selector check. Associations are not traced traffic.'));
const pos=nodes.map((n,i)=>({...n,x:mobile?14:14+i*(w+gap),y:mobile?12+i*(h+gap):30}));
for(let i=0;i<2;i++){const a=pos[i],b=pos[i+1],d=mobile?`M${a.x+w/2} ${a.y+h}V${b.y}`:`M${a.x+w} ${a.y+h/2}H${b.x}`,path=svg('g',{'role':'button',tabindex:'0','aria-label':'Inspect backend association'});path.append(svg('path',{d,stroke:ready?'#7cc8ef':'#f2c770','stroke-width':3,'stroke-dasharray':ready?'none':'7 4',fill:'none'}),svg('path',{d,stroke:'transparent','stroke-width':20,fill:'none'}));const ids=[a.source?.e.evidence_id,b.source?.e.evidence_id].filter(Boolean);path.onclick=()=>openEvidence('Backend association',ids,'Source fields describe configured association and readiness. They do not prove the path of an individual request.',path);path.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();path.dispatchEvent(new Event('click'));}};root.append(path);}
const icons={Service:'M3 9h18M7 9V4h10v5M5 9v10h14V9M9 13h6M9 16h6',EndpointSlice:'M3 4h18v16H3ZM7 8h2M7 12h2M7 16h2M13 8h4M13 12h4M13 16h4',Pod:'M12 2 3 7v10l9 5 9-5V7ZM3 7l9 5 9-5M12 12v10'};
for(const n of pos){const g=svg('g',{class:'resource'+(guide.steps[stepIndex].focus.includes(n.kind)?' related':''),role:'button',tabindex:'0','data-kind':n.kind,'aria-label':'Inspect '+n.kind});g.append(svg('rect',{x:n.x,y:n.y,width:w,height:h,rx:7,fill:'#10212b',stroke:n.source?'#6a9bb4':'#f2c770','stroke-width':1.5}),svg('path',{d:icons[n.kind],transform:`translate(${n.x+12} ${n.y+13})`,fill:'none',stroke:'#b7d6e4','stroke-width':1.6}),svg('text',{x:n.x+45,y:n.y+29,fill:'#e5eff3','font-size':mobile?13:12},n.label));const desc=n.description,parts=desc.match(new RegExp('.{1,'+Math.max(18,Math.floor((w-22)/6.2))+'}','g'))??[];parts.forEach((line,j)=>g.append(svg('text',{x:n.x+12,y:n.y+52+j*13,fill:'#b0c3ce','font-size':11},line)));if(appError&&n.kind==='Pod'){const badge=svg('g',{role:'button',tabindex:'0','data-application-error':'true','aria-label':'Application HTTP 500 errors; inspect all 68 captured log records'});badge.append(svg('rect',{x:n.x+7,y:n.y+h-29,width:w-14,height:24,rx:4,fill:'#422831',stroke:'#ffadb8'}),svg('text',{x:n.x+14,y:n.y+h-12,fill:'#ffced5','font-size':11},'HTTP 500 · app error ↗'));badge.onclick=e=>{e.stopPropagation();openEvidence('Application errors · Ready is separate',['file:during-observe-logs.json'],'Observe captured 68 log records. Six selected error events were supplied to Ultra. Kubernetes Ready does not establish request success.',badge);};badge.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();badge.dispatchEvent(new Event('click',{bubbles:true}));}};g.append(badge);}
g.onclick=()=>{const s=n.source;openEvidence(n.kind+' source fields',s?[s.e.evidence_id]:[],n.description,g);if(s){selected.records[0].fields=sourceValue(s.e,s.p);}};g.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();g.dispatchEvent(new Event('click'));}};root.append(g);}
$('topology').replaceChildren(root);$('graph-note').textContent=f.assessment.verdict==='SUPPORTED'?'Selector excludes the intended Ready workload. This scoped mechanism is supported; overall incident causality remains separate.':'Ready topology does not establish application correctness. Select a resource or association to inspect its exact evidence.';}
function renderComparison(){const pane=$('hypotheses');pane.replaceChildren();const a=data.decisions[0],b=data.decisions[1],ids=[...new Set(data.decisions.flatMap(d=>d.proposal?.hypotheses.map(h=>h.id)??[]))];for(const id of ids){const ah=a?.proposal?.hypotheses.find(h=>h.id===id),bh=b?.proposal?.hypotheses.find(h=>h.id===id),row=element('article',{class:'hypothesis'});row.append(element('h3',{},id.replaceAll('_',' ')));const states=element('div',{class:'states'});for(const [label,h]of[['A · initial',ah],['B · enriched',bh]]){const box=element('div');box.append(element('span',{},label),element('b',{class:'unverified'},h?'Model label: '+h.assessment:'Not executed'));states.append(box);}row.append(states);const summary=data.comparison[id]??'Original model labels above; no controller authority.';row.append(element('p',{},summary));for(const [label,h]of[['A',ah],['B',bh]])if(h){row.append(citation('Inspect '+label+' citations',h.evidence_ids,'Original '+label+' statement; citation existence is not proof that it supports the claim.',{modelStatement:h.statement}));}pane.append(row);}
$('conflict').textContent=data.conflict;
}
function render() {
  const f=data.frames[at];
  $('case-title').textContent=guide.title;$('case-question').textContent=guide.question;
  $('impact').textContent=guide.steps[0].result;$('uncertainty').textContent=data.uncertainty;
  $('time').textContent='Captured '+f.result.evidence[0].batch.observed_at+((at===0||at===3)?' · this stage was not sent to Ultra':'');
  $('mode').textContent=data.public?'Recorded investigation · sanitised':'Recorded investigation · private';
  $('version').textContent=release.version+' candidate';
  $('stages').replaceChildren();titles.forEach((t,i)=>{const b=element('button',{'aria-pressed':String(at===i)},t);b.onclick=()=>{pause();at=i;render();};$('stages').append(b);});
  renderGuide();renderGraph();renderComparison();renderFreshState();
  const coverage=$('coverage');coverage.replaceChildren();
  for(const entry of evidenceSources(data))coverage.append(citation(entry.label,entry.refs,entry.summary));
  $('recovery').textContent=data.recovery.summary;
  $('copy-status').textContent=data.public?'Sanitised public observations; complete retained text and exact original model responses. Private source originals remain unchanged. Capture limits and original IDs are preserved.':'Complete private retained records, original model responses and capture limits.';
  $('model-record').textContent=JSON.stringify({decisions:data.decisions,provider_calls:data.calls,inputs:data.inputs},null,2);
  $('raw-record').textContent=JSON.stringify(data.forensics,null,2);
  $('controller-record').textContent=JSON.stringify({frames:data.frames,executions:data.executions},null,2);
  $('recovery-record').textContent=JSON.stringify(data.recovery,null,2);
  $('provenance-record').textContent=JSON.stringify({records:data.source_manifest,model_text_hashes:data.model_hashes,redaction:data.redaction},null,2);
}
async function load() {
  pause();const sequence=++loadSequence,value=$('case').value;
  try {
    const response=await fetch('./data/'+value+'.json');if(!response.ok)throw new Error('Case could not be loaded');
    const nextData=await response.json();if(sequence!==loadSequence)return;
    data=nextData;guide=guideFor(data);stepIndex=0;at=1;
    document.querySelectorAll('details').forEach(d=>d.open=false);render();history.replaceState(null,'','#'+value);
    $('start').disabled=false;
  } catch(error) {
    $('case-title').textContent='This recorded case could not be loaded.';$('case-question').textContent='Choose another case or reload the viewer. No collection or AI call has run.';$('start').disabled=true;
    $('announce').textContent=error.message;
  }
}
$('case').onchange=load;
$('start').onclick=()=>selectStep(0);$('previous').onclick=()=>selectStep(Math.max(0,stepIndex-1));$('next').onclick=()=>selectStep(Math.min(guide.steps.length-1,stepIndex+1));
$('explore').onclick=()=>{$('evidence-title-main').focus({preventScroll:true});$('evidence-library').scrollIntoView({block:'start',behavior:'instant'});};
$('replay').onclick=()=>{at=0;play();};$('play').onclick=play;$('pause').onclick=pause;$('step').onclick=()=>{pause();at=(at+1)%4;render();};
$('model-evidence').onclick=e=>openEvidence('Exact Ultra public responses',data.decisions.flatMap(d=>d.evidence_ids??[]),'Original responses from earlier genuine Nebius calls. The guide is authored explanation; these are the original model words.',e.currentTarget,{modelStatement:data.decisions.map(d=>d.raw_public_response).join('\n\n'),modelInput:data.inputs});
$('about').onclick=e=>openEvidence('How this recorded investigation works',[],
  'The experiment collectors and Observe gathered evidence. A prepared pipeline selected bounded inputs for Nemotron Ultra. Deterministic rules separately checked Service selection. This guide explains those saved results; its next checks are authored suggestions. It does not demonstrate autonomous tool selection. '+data.conflict+' '+data.recovery.summary,e.currentTarget);
$('export-case').onclick=()=>download(data,'resolve-'+data.id+'-complete-case.json');
$('export-evidence').onclick=()=>download(selected,'resolve-evidence.json');
$('copy-id').onclick=async()=>{try{await navigator.clipboard.writeText(selected.records.map(r=>r.id).join('\n'));$('drawer-announce').textContent='Source reference copied';}catch{$('drawer-announce').textContent='Copy unavailable. Full references remain in Provenance and the export.';}};
$('close-evidence').onclick=()=>$('evidence').close();
$('evidence').addEventListener('close',()=>{if(origin?.isConnected)origin.focus({preventScroll:true});else $('step-title').focus({preventScroll:true});$('announce').textContent='Evidence closed';});
$('evidence').addEventListener('keydown',e=>{
  if(e.key!=='Tab')return;
  const focusable=[...$('evidence').querySelectorAll('button,[tabindex],summary')].filter(b=>b.tabIndex>=0&&!b.disabled),first=focusable[0],last=focusable.at(-1);
  if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
  else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
});
const tabs=[...document.querySelectorAll('[data-tab]')];
tabs.forEach((b,i)=>{b.onclick=()=>{tab=b.dataset.tab;renderDrawer();};b.onkeydown=e=>{if(!['ArrowRight','ArrowLeft'].includes(e.key))return;e.preventDefault();const next=tabs[(i+(e.key==='ArrowRight'?1:3))%4];tab=next.dataset.tab;renderDrawer();next.focus();};});
document.querySelector('.drawer-tabs').setAttribute('role','tablist');$('drawer-content').setAttribute('role','tabpanel');
addEventListener('resize',()=>{if(data)renderGraph();});
let freshState=null,freshRun=null,freshBusy=false;
function renderFreshState(){
  $('fresh-analysis').hidden=data?.id!=='http';
  if(!freshState)return;
  $('fresh-history-label').hidden=!freshState.runs.length;
  $('fresh-history').replaceChildren(...freshState.runs.map((id,i)=>element('option',{value:id},'Saved run '+(i+1))));
  if(freshRun)$('fresh-history').value=freshRun.id;
  $('fresh-history').disabled=freshState.running||freshBusy;
  const available=freshState.enabled&&!freshState.hold&&freshState.attempts<freshState.max_calls&&!freshState.running&&!freshBusy;
  $('fresh-run').disabled=!available||data?.id!=='http';
  $('fresh-run').textContent=freshState.running||freshBusy?'Analysis running…':'Run fresh analysis';
  if(!freshRun)$('fresh-status').textContent=data?.id!=='http'?'Fresh analysis is scoped to the HTTP 500 case. Select that case to continue.':freshState.enabled?`${freshState.attempts} / ${freshState.max_calls} durable call reservations used. Maximum next reservation $${freshState.maximum_next_reservation_usd.toFixed(5)} at checked list rates; no automatic retry.`:'Fresh analysis is disabled in this replay launch. The README has the explicit local opt-in command; no credentials are needed for recorded investigations.';
}
async function refreshFresh(){
  try{const r=await fetch('/api/analysis');if(!r.ok)throw new Error();freshState=await r.json();renderFreshState();
    if(freshState.runs.length){freshRun=await(await fetch('/api/analysis/runs/'+freshState.runs.at(-1))).json();renderFreshResult();if(freshRun.status==='running')pollFresh(freshRun.id);}
  }catch{$('fresh-status').textContent='Fresh analysis is unavailable in this launch. Recorded evidence remains usable.';}
}
function renderFreshResult(){
  if(!freshRun)return;
  const pane=$('fresh-result');pane.replaceChildren();
  $('fresh-status').textContent=`${freshRun.status.toUpperCase()} · ${freshRun.started_at} · ${freshRun.id}. ${freshRun.status==='running'?'Waiting for Nebius; no cluster action is running.':'This new run is separate from the seven original responses.'}`;
  if(freshRun.error)pane.append(element('p',{class:'warning'},freshRun.error+' · No automatic retry. Recorded evidence and the complete failed-run receipt remain available.'));
  pane.append(element('p',{class:'independent-finding'},freshRun.independent_finding));
  pane.append(element('p',{class:'section-note'},'Evidence limit: cumulative 200/500 counters do not establish intermittent failure within this fault window. Ready resources do not rule out every infrastructure contribution. These limits apply to the interpretation below.'));
  if(freshRun.interpretation){
    pane.append(element('h3',{},'Ultra’s new interpretation · advisory'),element('p',{},freshRun.interpretation.summary));
    const grid=element('div',{class:'fresh-hypotheses'});
    for(const h of freshRun.interpretation.hypotheses){const box=element('article');box.append(element('h3',{},h.title),element('p',{class:'unverified'},'Model assessment: '+h.assessment));
      const detail=element('details');detail.append(element('summary',{},'Explanation and '+h.evidence_ids.length+' citations'),element('p',{},h.explanation));
      for(const id of h.evidence_ids){const row=data.inputs.flatMap(x=>x.view.readable_observations).find(x=>x.evidence_id===id);detail.append(citation(operationNames[row?.operation]??'Inspect citation',[id],'Fresh model citation. Membership is checked; semantic support is not automatically verified.'));}box.append(detail);
      grid.append(box);}
    pane.append(grid,element('p',{class:'warning'},'Still uncertain: '+freshRun.interpretation.uncertainty),element('p',{},'Model suggests: '+freshRun.interpretation.next_check+' · NOT EXECUTED'));
  }
  if(freshRun.raw_public_response){const full=element('details');full.append(element('summary',{},'Exact new public model response · complete'),element('pre',{},freshRun.raw_public_response));pane.append(full);}
  if(freshRun.unknown_citations?.length)pane.append(element('p',{class:'warning'},'Unknown citations: '+freshRun.unknown_citations.join(', ')));
  if(freshRun.validation)pane.append(element('p',{class:'section-note'},freshRun.validation));
  if(freshRun.status!=='running'){const forensic=element('details');forensic.append(element('summary',{},'Complete run receipt · input, output, usage and timestamps'),element('pre',{},JSON.stringify(freshRun,null,2)));pane.append(forensic);}
  $('fresh-export').hidden=false;renderFreshState();
}
async function pollFresh(id){
  try{const response=await fetch('/api/analysis/runs/'+id);if(!response.ok)throw new Error();freshRun=await response.json();renderFreshResult();
    if(freshRun.status==='running'){setTimeout(()=>pollFresh(id),1200);}else{freshState=await(await fetch('/api/analysis')).json();freshBusy=false;renderFreshState();}
  }catch{freshBusy=false;$('fresh-status').textContent='Connection interrupted. The request may still be running; reload to inspect its durable receipt. Do not assume it was cancelled.';}
}
$('fresh-input').onclick=async()=>{try{const r=await(await fetch('/api/analysis/input')).json();openEvidence('Exact outgoing fresh-analysis request',[],'Fixed sanitised HTTP evidence; no earlier model response is included. Request SHA256: '+r.sha256,document.activeElement,{modelStatement:JSON.stringify(r.request,null,2)});}catch{$('fresh-status').textContent='Request inspection unavailable. No call was sent.';}};
$('fresh-history').onchange=async()=>{freshRun=await(await fetch('/api/analysis/runs/'+$('fresh-history').value)).json();renderFreshResult();};
$('fresh-export').onclick=()=>download(freshRun,'resolve-'+freshRun.id+'.json');
$('fresh-run').onclick=async()=>{
  if(!freshState||freshBusy||data.id!=='http')return;freshBusy=true;renderFreshState();
  try{const r=await fetch('/api/analysis',{method:'POST',headers:{'Content-Type':'application/json','X-Resolve-Token':freshState.token},body:JSON.stringify({case:'http',request_sha256:freshState.request_sha256})}),result=await r.json();
    if(!r.ok)throw new Error(result.error);freshRun=null;await pollFresh(result.id);
  }catch(error){freshBusy=false;renderFreshState();$('fresh-status').textContent='Analysis could not start: '+error.message+'. Inspect the run list after reloading if the connection failed; no automatic retry.';}
};

const caseIds=['http','selector','dns','policy'];
addEventListener('hashchange',()=>{const name=location.hash.slice(1);if(caseIds.includes(name)&&name!==data?.id){$('case').value=name;load();}});
if(caseIds.includes(location.hash.slice(1)))$('case').value=location.hash.slice(1);
await load();
await refreshFresh();
