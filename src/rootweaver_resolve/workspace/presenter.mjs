// Pure presentation helpers. State, claims and support remain server-owned.
export function executionLabel(data) {
  if(data.execution_mode==='retained-live-kubernetes-evidence') return 'Genuine Kubernetes capture · offline replay · '+(data.model_invoked?'completed Ultra inference, retained output':'no model analysis for this capture stage');
  const run = data.model_run;
  if (run?.execution_mode === 'retained') return 'Retained Nemotron output replay · No new inference · Synthetic observations';
  if (run?.acquisition_owner === 'controller') {
    if (run.execution_mode === 'replay') return 'Controller acquisition · Synthetic replay · No model invoked';
    return `Controller acquisition · ${run.execution_mode === 'simulated' ? 'Simulated model analysis' : data.model_invoked ? 'Live Nebius analysis' : 'No model invoked'} · Synthetic replay observations`;
  }
  return run ? `${run.execution_mode === 'simulated' ? 'Simulated model proposals' : data.model_invoked ? 'Live Nebius requests' : 'Nemotron ready'} · Synthetic replay observations` : 'Synthetic replay · No model invoked';
}
export const claimLabels = {
  intended_pods_ready: "Intended pods report Running and Ready",
  service_exists: "The target Service exists",
  service_has_no_ready_endpoints: "Associated slices contain no Ready endpoints",
  selector_excludes_intended_ready_pods: "Service selector excludes the intended Ready pods",
  service_selection_failure: "Service selection failure in the observed route",
  http_responses_healthy: "HTTP responses are healthy",
  service_reachable: "The Service is reachable",
  networkpolicy_caused_failure: "NetworkPolicy caused the failure",
  application_correct: "The application is correct",
  release_caused_application_regression: "The release caused an application regression",
};
export const operationLabels = {
  namespace_service_network: "Namespace Service / EndpointSlice topology",
  namespace_workloads: "Independent intended workload readiness and labels",
};
export function statusText(data) {
  if (data.result.technical_findings?.some(f => f.assessment.verdict === 'SUPPORTED'))
    return 'Technical finding supported · incident cause unresolved';
  if (data.result.diagnosis) return "Service selection finding supported";
  if (data.result.state === "ABSTAINED") return "Diagnosis withheld";
  if (data.assessment.verdict === "SUPPORTED") return "Evidence acquired · conclusion pending validation";
  return "Root cause not established";
}
export function supportedRecords(data) {
  // Never promote provisional checks to emitted conclusions.
  return data.result.support_records.filter(record =>
    record.assessment.verdict === "SUPPORTED" && data.result.claims.some(claim =>
      claim.predicate === record.claim.predicate &&
      JSON.stringify(claim.evidence_ids) === JSON.stringify(record.claim.evidence_ids)));
}
export function sourceValue(evidence, pointer) {
  let value = evidence.batch;
  if (pointer.startsWith("resources_json#")) {
    value = JSON.parse(evidence.batch.resources_json);
    pointer = pointer.slice("resources_json#".length);
  }
  if (!pointer.startsWith("/")) throw new Error("Invalid source pointer");
  for (const segment of pointer.slice(1).split("/")) {
    const key = segment.replaceAll("~1", "/").replaceAll("~0", "~");
    if (value === null || typeof value !== "object" || !Object.hasOwn(value, key))
      throw new Error("Missing source field");
    value = value[key];
  }
  return value;
}

export function modelAssertionText(hypothesis) {
  return `Unverified model interpretation · ${hypothesis.id} · model assessment: ${hypothesis.assessment}. ${hypothesis.statement}`;
}

// All projections below read the authorised state only. They do not acquire or alter evidence.
export function causalStatus() { return 'CAUSE NOT ESTABLISHED'; }
export function observationTimes(data, evidence) {
  const acquired = data.model_run?.executions?.find(r => (r.output_evidence_refs ?? []).includes(evidence.evidence_id) && r.actual_operation === 'ReplayProvider.observe');
  return {observed:evidence.batch.observed_at, acquired:acquired?.started_at ?? null};
}
export function recordIndex(data) {
  const rows=[];
  const add=(kind,raw,path,source,timestamp,refs=[])=>rows.push({key:path,kind,raw,path,source:source ?? 'Not retained',timestamp:timestamp ?? null,severity:raw.severity ?? raw.level ?? null,evidenceIds:refs});
  (data.result.evidence ?? []).forEach((e,i)=>add('observation',e,`/result/evidence/${i}`,e.batch.source_id,e.batch.observed_at,[e.evidence_id]));
  (data.model_run?.executions ?? []).forEach((e,i)=>add('invocation',e,`/model_run/executions/${i}`,e.actor_identity,e.started_at,[...(e.input_evidence_refs ?? []),...(e.output_evidence_refs ?? [])]));
  (data.result.trace ?? []).forEach((e,i)=>add('transition',e,`/result/trace/${i}`,'controller',null,e.evidence_ids ?? []));
  (data.checks ?? []).forEach((e,i)=>add('claim-check',e,`/checks/${i}`,'deterministic claim checker',null,e.claim.evidence_ids));
  (data.result.support_records ?? []).forEach((e,i)=>add('claim-support',e,`/result/support_records/${i}`,'deterministic claim checker',null,e.claim.evidence_ids));
  (data.result.technical_findings ?? []).forEach((e,i)=>add('technical-finding',e,`/result/technical_findings/${i}`,e.validation_actor,null,e.claim.evidence_ids));
  (data.model_run?.decisions ?? []).forEach((e,i)=>add('model-analysis',e,`/model_run/decisions/${i}`,'unverified model analysis',null,e.evidence_ids ?? []));
  (data.model_run?.provider_calls ?? []).forEach((e,i)=>add('provider-diagnostic',e,`/model_run/provider_calls/${i}`,'inference provider metadata',null));
  (data.result.hypotheses ?? []).forEach((e,i)=>add('controller-hypothesis',e,`/result/hypotheses/${i}`,'controller hypothesis',null));
  return rows;
}
export function fullRecord(record) { return typeof record.raw === 'string' ? record.raw : JSON.stringify(record.raw,null,2); }
export function exportSnapshot(data, originalResponse) { return originalResponse ?? JSON.stringify(data,null,2); }
export function textWindow(text, start=0, size=32768) {
  if (!Number.isInteger(start) || start<0 || !Number.isInteger(size) || size<1) throw new Error('Invalid display window');
  let next=Math.min(text.length,start+size);
  // Keep surrogate pairs together across appended DOM text nodes.
  if (next<text.length && next>start && /[\uD800-\uDBFF]/.test(text[next-1]) && /[\uDC00-\uDFFF]/.test(text[next])) next++;
  return {text:text.slice(start,next),next,total:text.length,complete:next>=text.length,preview:next<text.length};
}
export function recordPage(rows, page=0, size=25) {
  if (!Number.isInteger(page) || page<0 || !Number.isInteger(size) || size<1) throw new Error('Invalid record page');
  const pages=Math.max(1,Math.ceil(rows.length/size)),current=Math.min(page,pages-1),start=current*size;
  return {items:rows.slice(start,start+size),page:current,pages,total:rows.length,start,end:Math.min(start+size,rows.length)};
}
export function filterRecords(rows, {text='',source='',kind='',severity='',from='',to=''}={}) {
  return rows.filter(r=>(!kind || r.kind===kind) && (!source || r.source.toLowerCase().includes(source.toLowerCase())) && (!severity || String(r.severity ?? '').toLowerCase()===severity.toLowerCase()) && (!text || fullRecord(r).toLowerCase().includes(text.toLowerCase())) && (!from || (r.timestamp && Date.parse(r.timestamp)>=Date.parse(from))) && (!to || (r.timestamp && Date.parse(r.timestamp)<=Date.parse(to))));
}
export function logSources(data) {
  // The current state API has no application-log or Kubernetes-event collection contract.
  return [{id:'application',label:'Application logs',status:'NOT COLLECTED',count:null,kind:null},
    {id:'events',label:'Kubernetes events',status:'NOT COLLECTED',count:null,kind:null},
    {id:'invocation',label:'Controller invocations',status:data.model_run?.executions?.length?'COLLECTED':'NOT COLLECTED',count:data.model_run?.executions?.length ?? 0,kind:'invocation'},
    {id:'transition',label:'Controller transitions',status:data.result.trace?.length?'COLLECTED':'NOT COLLECTED',count:data.result.trace?.length ?? 0,kind:'transition'},
    {id:'commands',label:'Command stdout / stderr',status:'NOT COLLECTED',count:null,kind:null}];
}
export function operationalFacts(data) {
  const names={service_exists:'Target Service existence',intended_pods_ready:'Intended workload readiness',service_has_no_ready_endpoints:'Absence of Ready endpoints',selector_excludes_intended_ready_pods:'Selector exclusion of intended Ready pods'};
  return (data.checks ?? []).filter(c=>Object.hasOwn(names,c.claim.predicate)).map(c=>({text:names[c.claim.predicate],verdict:c.assessment.verdict,reason:c.assessment.reason,record:c,evidenceIds:c.claim.evidence_ids}));
}
export function acquisitionSummary(data) {
  const evidence=data.result.evidence ?? [];
  if (!evidence.length) return 'No observations acquired';
  const statuses=evidence.map(e=>e.batch.status);
  if (statuses.every(s=>s==='complete')) return data.gaps?.length?'Acquired observations complete; further collection gaps remain':'All acquired observations completed';
  return statuses.map((s,i)=>`Observation ${i+1}: ${s}`).join('; ');
}
export function operationalTimeline(data) {
  return (data.result.trace ?? []).filter(e=>(e.operation && e.evidence_ids?.length) || ['AWAITING_APPROVAL','ABSTAINED'].includes(e.state));
}

/** @typedef {{evidenceId:string, pointer:string}} VisualSourceRef */
/** @typedef {{id:string,kind:string,title:string,status:string,detail:string,refs:VisualSourceRef[],recordPath:string|null}} IncidentVisualNode */
/**
 * Deterministic projection of the authorised incident snapshot. Per-observation identities
 * deliberately keep conflicting versions separate. No support or causality is computed here.
 * @returns {{version:string,revision:number,nodes:IncidentVisualNode[],edges:object[],notices:string[]}}
 */
export function incidentVisualModel(data) {
  const nodes=[],edges=[],notices=[],resources=[];let outsideTopology=0;
  const add=(id,kind,title,status,detail,refs=[],recordPath=null)=>{
    const node={id,kind,title,status,detail,refs,recordPath};nodes.push(node);return node;
  };
  for(const [i,e] of (data.result.evidence??[]).entries()){
    const ref=pointer=>({evidenceId:e.evidence_id,pointer});
    const observation=add(`observation:${i}`,'Observation',operationLabels[e.batch.operation]??e.batch.operation,e.batch.status.toUpperCase(),`Observed ${e.batch.observed_at}; ${e.batch.source_id}`, [ref('/status')],`/result/evidence/${i}`);
    let payload;try{payload=JSON.parse(e.batch.resources_json);if(!Array.isArray(payload))throw new Error();}catch{
      observation.status='UNREADABLE';notices.push(`Observation ${e.evidence_id}: structured payload unreadable; full retained record remains available.`);continue;
    }
    observation.detail+=`; ${payload.length} retained resource entries`;
    payload.forEach((r,j)=>{
      if(!r||typeof r!=='object'||!['Service','Pod','EndpointSlice','Deployment','Endpoints'].includes(r.kind)){outsideTopology++;return;}
      const pointer=`resources_json#/${j}`,namespace=r.namespace??e.batch.namespace;
      const n=add(`resource:${i}:${j}`,r.kind,typeof r.name==='string'?r.name:'Name not retained',e.batch.status==='complete'?'OBSERVED':e.batch.status.toUpperCase(),`Namespace: ${namespace??'not retained'} · source status: ${e.batch.status}`, [ref(pointer)],null);
      const facts=[];for(const field of ['selector','labels','phase','ready','replicas','readyReplicas'])if(Object.hasOwn(r,field))facts.push(`${field}: ${JSON.stringify(r[field])}`);
      if(Array.isArray(r.endpoints))facts.push(`${r.endpoints.length} recorded endpoint entries`);
      n.summary=facts.join(' · ');
      resources.push({node:n,raw:r,namespace,evidence:e});
      if(r.kind==='EndpointSlice'){
        if(Array.isArray(r.endpoints))r.endpoints.forEach((endpoint,k)=>{
          if(!endpoint||typeof endpoint!=='object')return;
          const target=typeof endpoint.target==='string'?endpoint.target:typeof endpoint.targetRef?.name==='string'?endpoint.targetRef.name:null;
          const item=add(`endpoint:${i}:${j}:${k}`,'Endpoint',target??`Endpoint entry ${k+1}`,'OBSERVED',`Readiness as recorded: ${String(endpoint.conditions?.ready??'not retained')}; not application correctness`,[ref(`${pointer}/endpoints/${k}`)]);
          resources.push({node:item,raw:{...endpoint,kind:'Endpoint',target},namespace,evidence:e});
          edges.push({id:`contains:${item.id}`,from:n.id,to:item.id,relation:'contains entry',refs:[ref(`${pointer}/endpoints/${k}`)]});
        });
      }
    });
  }
  const connect=(a,b,relation)=>edges.push({id:`${relation}:${a.node.id}:${b.node.id}`,from:a.node.id,to:b.node.id,relation,refs:[...a.node.refs,...b.node.refs]});
  for(const a of resources)for(const b of resources){
    if(typeof a.namespace!=='string'||a.namespace!==b.namespace)continue;
    if(a.raw.kind==='Service'&&b.raw.kind==='EndpointSlice'&&typeof a.raw.name==='string'&&b.raw.service_name===a.raw.name)connect(a,b,'service_name association');
    // A named endpoint target is a reference, never proof of health or reachability.
    if(a.raw.kind==='Endpoint'&&b.raw.kind==='Pod'&&typeof a.raw.target==='string'&&a.raw.target===b.raw.name&&(!a.raw.targetRef?.kind||a.raw.targetRef.kind==='Pod')&&(!a.raw.targetRef?.namespace||a.raw.targetRef.namespace===b.namespace))connect(a,b,'target reference');
    if(a.raw.kind==='Deployment'&&b.raw.kind==='Pod'&&typeof a.raw.name==='string'&&Array.isArray(b.raw.owner_references)&&b.raw.owner_references.some(o=>o.kind==='Deployment'&&o.name===a.raw.name))connect(a,b,'owner reference');
  }
  // A selector comparison is a presentation of recorded fields, not a support predicate.
  for(const a of resources)for(const b of resources){
    if(a.raw.kind!=='Service'||b.raw.kind!=='Pod'||typeof a.namespace!=='string'||a.namespace!==b.namespace)continue;
    const selector=a.raw.selector,labels=b.raw.labels;
    if(!selector||typeof selector!=='object'||Array.isArray(selector)||!Object.keys(selector).length||!labels||typeof labels!=='object'||Array.isArray(labels))continue;
    if(a.evidence.batch.status!=='complete'||b.evidence.batch.status!=='complete'||!Object.values(selector).every(v=>typeof v==='string')||!Object.values(labels).every(v=>typeof v==='string'))continue;
    const matches=Object.entries(selector).every(([key,value])=>Object.hasOwn(labels,key)&&labels[key]===value);
    const intended=Object.fromEntries(data.incident.workload_labels??[]);
    const inClaimScope=a.raw.name===data.incident.service&&a.namespace===data.incident.namespace&&Object.entries(intended).every(([k,v])=>labels[k]===v);
    const conflict=inClaimScope&&(data.checks??[]).some(c=>c.assessment.verdict==='CONTRADICTORY'&&c.claim.predicate==='selector_excludes_intended_ready_pods'&&c.claim.evidence_ids.includes(a.evidence.evidence_id)&&c.claim.evidence_ids.includes(b.evidence.evidence_id));
    edges.push({id:`selector:${a.node.id}:${b.node.id}`,from:a.node.id,to:b.node.id,kind:'selector',status:conflict?'CONTRADICTORY':matches?'MATCH':'MISMATCH',relation:conflict?'Selector discrepancy · controller reports conflict':matches?'Selector matches observed labels':'Selector does not match observed labels',detail:'Field comparison only; does not establish actual traffic, application correctness or incident cause.',refs:[{...a.node.refs[0],pointer:a.node.refs[0].pointer+'/selector'},{...b.node.refs[0],pointer:b.node.refs[0].pointer+'/labels'}]});
  }
  const claimRefs=record=>(record.claim?.evidence_ids??[]).map(evidenceId=>({evidenceId,pointer:''}));
  (data.result.technical_findings??[]).forEach((f,i)=>add(`finding:${i}`,'Finding',claimLabels[f.claim.predicate]??f.claim.predicate,f.assessment.verdict,`Controller-validated technical finding · nominated by ${f.nomination_origin} · ${f.assessment.reason}`,claimRefs(f),`/result/technical_findings/${i}`));
  const technical=new Set(['service_exists','intended_pods_ready','service_has_no_ready_endpoints','selector_excludes_intended_ready_pods','service_selection_failure']);
  (data.checks??[]).forEach((c,i)=>{if(technical.has(c.claim.predicate))add(`check:${i}`,'Check',claimLabels[c.claim.predicate]??c.claim.predicate,c.assessment.verdict,`Controller check, not an emitted finding · ${c.assessment.reason}`,claimRefs(c),`/checks/${i}`);});
  (data.model_run?.decisions??[]).forEach((d,i)=>add(`model:${i}`,'Model',`Public model analysis ${i+1}`,'UNVERIFIED',`Unverified interpretation · disposition: ${d.disposition??'not retained'} · public text remains in original record`,[],`/model_run/decisions/${i}`));
  (data.gaps??[]).forEach((g,i)=>add(`gap:${i}`,'Missing',operationLabels[g.operation]??g.operation,'MISSING',g.reason,[],`/gaps/${i}`));
  (data.result.trace??[]).forEach((t,i)=>add(`transition:${i}`,'Transition',`#${t.sequence} · ${t.state}`,'RECORDED',t.reason,(t.evidence_ids??[]).map(evidenceId=>({evidenceId,pointer:''})),`/result/trace/${i}`));
  for(const kind of ['Service','Pod','EndpointSlice','Deployment'])if(!resources.some(r=>r.raw.kind===kind))notices.push(`${kind}: not observed in acquired data; no resource or absence claim is inferred.`);
  if(outsideTopology)notices.push(`${outsideTopology} retained resource entries are outside the typed topology vocabulary; inspect complete observations.`);
  notices.push('Schematic associations from recorded fields, not measured traffic. Pod/endpoint readiness is not application correctness. Incident cause remains unproven.');
  return {version:'resolve-evidence-visuals/v2',revision:data.revision,nodes,edges,notices};
}
export function visualView(model,view){
  const kinds={summary:['Finding','Check','Model','Missing'],topology:['Service','Pod','EndpointSlice','Endpoint','Endpoints','Deployment','Missing','Finding'],timeline:['Transition'],evidence:['Observation','Missing']};
  if(!Object.hasOwn(kinds,view))throw new Error('Unknown evidence view');
  const nodes=model.nodes.filter(n=>kinds[view].includes(n.kind)),ids=new Set(nodes.map(n=>n.id));
  const edges=view==='topology'?model.edges.filter(e=>ids.has(e.from)&&ids.has(e.to)):view==='timeline'?nodes.slice(1).map((n,i)=>({id:`sequence:${i}`,from:nodes[i].id,to:n.id,relation:'controller order, not elapsed time',refs:[...nodes[i].refs,...n.refs]})):[];
  if(view==='topology')nodes.sort((a,b)=>(({Service:0,Deployment:1,EndpointSlice:2,Endpoints:2,Endpoint:3,Pod:4}[a.kind]??9)-({Service:0,Deployment:1,EndpointSlice:2,Endpoints:2,Endpoint:3,Pod:4}[b.kind]??9)));
  return {nodes,edges};
}
export function visualTone(status){
  if(status==='SUPPORTED')return 'supported';
  if(status==='UNVERIFIED')return 'unverified';
  if(status==='CONTRADICTORY')return 'contradictory';
  if(status==='REFUTED')return 'refuted';
  if(['MISSING','INCOMPLETE','UNAVAILABLE','UNREADABLE','UNSUPPORTED','PARTIAL'].includes(status))return 'missing';
  return 'observed';
}
/** Word-aware lossless line wrapping; long tokens still split without ellipsis. */
export function wrapVisualText(text,count){
  const chars=Array.from(text),lines=[];let at=0;
  while(at<chars.length){let end=Math.min(chars.length,at+count);if(end<chars.length){const boundary=chars.slice(at,end).lastIndexOf(' ');if(boundary>0)end=at+boundary+1;}lines.push(chars.slice(at,end).join(''));at=end;}
  return lines;
}
/** Fixed row-major lanes, no force simulation, clocks or random layout. Labels wrap losslessly. */
export function visualLayout(nodes,width=1000){
  const available=Math.max(300,Math.floor(Number.isFinite(width)?width:1000));
  const columns=available<650?1:available<1050?2:3,gap=20,cardWidth=Math.floor((available-gap*(columns+1))/columns);
  let y=20;const laid=[];
  for(let i=0;i<nodes.length;i+=columns){
    const group=nodes.slice(i,i+columns).map((n,col)=>{
      const count=Math.max(12,Math.floor((cardWidth-32)/8)),lines=wrapVisualText(n.title,count);
      const detailLines=wrapVisualText(n.summary??'',Math.max(12,Math.floor((cardWidth-32)/7)));
      const height=Math.max(116,76+lines.length*19+detailLines.length*17);
      return {...n,detailLines,x:gap+col*(cardWidth+gap),y,width:cardWidth,height,lines};
    });laid.push(...group);y+=Math.max(...group.map(n=>n.height))+gap;
  }
  return {width:available,height:Math.max(160,y),nodes:laid};
}
/** Serialize only this renderer's inert SVG vocabulary with XML-safe attribute escaping. */
export function serializeVisualSvg(root){
  const tags=new Set(['svg','title','desc','metadata','rect','g','path','text']);
  const escape=text=>String(text).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
  function encode(node){
    if(node.nodeType===3)return escape(node.textContent);
    if(node.nodeType!==1)return '';
    const tag=node.localName;
    if(node.namespaceURI!=='http://www.w3.org/2000/svg'||!tags.has(tag))throw new Error('Unexpected active or foreign SVG content');
    const attributes=Array.from(node.attributes).sort((a,b)=>a.name.localeCompare(b.name)).map(a=>{
      if(/^on/i.test(a.name)||/href$/i.test(a.name))throw new Error('Active SVG attributes are forbidden');
      return ` ${a.name}="${escape(a.value)}"`;
    }).join('');
    return `<${tag}${attributes}>${Array.from(node.childNodes).map(encode).join('')}</${tag}>`;
  }
  return '<?xml version="1.0" encoding="UTF-8"?>\n'+encode(root);
}

/** Never trigger a model-backed or retained-provider step from playback. */
export function syntheticPlaybackAllowed(data){
  return data.model_invoked===false && (!data.model_run || data.model_run.execution_mode==='replay') && (data.execution_mode==='synthetic-deterministic-replay'||data.model_run?.observation_mode==='synthetic-replay') && !(data.model_run?.provider_calls?.length);
}
/** Source-role columns on desktop; connected vertical graph on narrow screens. */
export function topologyLayout(nodes,width=1000){
  if(width<760)return visualLayout(nodes,Math.min(width,620));
  const roles=[['Service','Deployment'],['EndpointSlice','Endpoints','Endpoint','Missing','Finding'],['Pod']];
  const available=Math.max(760,Math.floor(width)),gap=56,cardWidth=Math.floor((available-48-gap*2)/3),laid=[];
  for(let col=0;col<roles.length;col++){
    const items=visualLayout(nodes.filter(n=>roles[col].includes(n.kind)),Math.min(cardWidth+40,620));
    for(const n of items.nodes)laid.push({...n,x:24+col*(cardWidth+gap),width:cardWidth});
  }
  return {width:available,height:Math.max(300,...laid.map(n=>n.y+n.height+24)),nodes:laid};
}
