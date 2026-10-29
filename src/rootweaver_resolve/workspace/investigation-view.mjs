export function observationSummary(receipt){
  const data=receipt?.model_data;
  if(Number.isInteger(data?.captured_frames)&&Array.isArray(data.streams)){
    const streams=data.streams;
    const total=field=>streams.reduce((sum,row)=>sum+(row[field]??0),0);
    return `${data.captured_frames} captured TCP frames across ${streams.length} connections. ${streams.filter(s=>s.syn_ack_frames?.length).length} contain a SYN/ACK; ${total('client_payload_bytes')} client and ${total('server_payload_bytes')} server payload bytes observed. ${streams.reduce((n,s)=>n+(s.reset_frames?.length??0),0)} reset frames; ${streams.reduce((n,s)=>n+(s.retransmission_frames?.length??0),0)} retransmission flags. This local, bounded capture does not prove application execution or the reason for a wait. All decoded frames and the original private PCAP are retained in the evidence receipt.`;
  }
  if(data?.counts&&Array.isArray(data.groups)){
    const c=data.counts;
    const groups=data.groups.map(g=>g.count+' × '+[g.fields.event,g.fields.status,g.fields.error_type??g.fields.error,g.fields.errno===undefined?null:'errno '+g.fields.errno].filter(x=>x!==null&&x!==undefined).join(' · '));
    return `${c.captured} captured log records; ${c.included} in the observation window. ${groups.join('; ')}. ${c.before_window} before the window; ${c.after_window} after; ${c.undated_or_unparsed} undated or unparsed. Full records retained.`;
  }
  if(Array.isArray(data?.objects))return data.objects.map(o=>o.kind==='Service'?`Service ${o.name}: ${o.clusterIP==='None'?'headless':o.type}`:o.kind==='EndpointSlice'?`${o.service}: ${(o.endpoints??[]).filter(e=>e.conditions?.ready===true).length} ready endpoint(s) in this slice`:`${o.kind} ${o.name}: ${o.phase??'inspect source'}`).join('. ')+'. Full snapshot retained.';
  return receipt?.summary;
}

export function boundReview(notes,id,digest){
  return notes?.session_id===id&&notes?.session_sha256===digest&&Array.isArray(notes.steps)?notes:null;
}

export function assessmentFor(steps,selected){
  const step=steps[selected],next=steps[selected+1];
  return step?.receipt&&next?.disposition==='accepted'?next:step;
}

// Optional post-run editorial readouts. The caller first binds review notes to
// exact session bytes with boundReview(). References establish availability,
// not semantic claim support or author authentication.
export function operatorReadout(review,session,selected){
  const story=review?.operator_readout;
  const row=selected===null?story?.overview:story?.steps?.find(s=>s.index===session.steps[selected]?.index);
  if(!row||!Array.isArray(row.evidence_ids)||!row.evidence_ids.length)return null;
  const available=session.steps.slice(0,selected===null?undefined:selected+1)
    .filter(s=>s.disposition==='accepted'&&s.receipt?.status==='ok').map(s=>s.receipt.evidence_id);
  return row.evidence_ids.every(id=>available.includes(id))?row:null;
}

export function hypothesisComparison(steps,selected,initial=[]){
  const step=steps[selected];
  const prior=[...steps.slice(0,selected+1)].reverse().find(s=>s.disposition==='accepted');
  const before=step?.disposition==='accepted'?(step.proposal?.hypotheses??initial):(prior?.proposal?.hypotheses??initial);
  const assessment=step?.disposition==='accepted'?assessmentFor(steps,selected):prior;
  const after=assessment?.proposal?.hypotheses??before;
  return after.map(h=>({...h,before:before.find(p=>p.id===h.id)?.assessment??null,after:h.assessment}));
}

export function packetTiming(receipt){
  const streams=receipt?.model_data?.streams;
  if(!Array.isArray(streams))return null;
  const valid=x=>Number.isFinite(x)&&x>=0;
  const paired=streams.filter(s=>valid(s.client_fin_after_payload_ms)&&valid(s.first_server_payload_after_client_ms));
  if(!paired.length)return null;
  const first=paired[0];
  return {paired:paired.length,partial:streams.length-paired.length,
    clientFinCount:streams.filter(s=>valid(s.client_fin_after_payload_ms)).length,
    responseCount:streams.filter(s=>valid(s.first_server_payload_after_client_ms)).length,
    example:{stream:first.stream,clientFinMs:first.client_fin_after_payload_ms,serverPayloadMs:first.first_server_payload_after_client_ms}};
}
