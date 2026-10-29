import {assessmentFor,hypothesisComparison,packetTiming,boundReview} from './investigation-view.mjs';
export {assessmentFor,hypothesisComparison,packetTiming,boundReview};
export function availableReceipts(session, selected){
  return session.steps.slice(0,selected+1).filter(s=>s.disposition==='accepted'&&s.receipt?.status==='ok').map(s=>s.receipt);
}
export function logRows(receipt,all=false,query=''){
  const rows=receipt.source.stdout.trimEnd().split('\n').map((text,i)=>{
    try{return {row:i+1,text,value:JSON.parse(text)};}catch{return {row:i+1,text,value:null};}
  });
  const window=receipt.model_data.window;
  return rows.filter(r=>(all||(r.value?.time>=window.start&&r.value?.time<=window.end))&&r.text.toLowerCase().includes(query.toLowerCase()));
}
export function streamRows(receipt){
  return receipt.model_data.streams.map(s=>({id:s.stream,fin:s.client_fin_after_payload_ms,response:s.first_server_payload_after_client_ms,
    coverage:Number.isFinite(s.client_fin_after_payload_ms)&&Number.isFinite(s.first_server_payload_after_client_ms)?'Complete timing pair':Number.isFinite(s.client_fin_after_payload_ms)?'Response outside capture':'Starts mid-connection'}));
}
export function command(receipt){
  const quote=s=>/^[\w./:=,+-]+$/.test(s)?s:"'"+s.replaceAll("'","'\\''")+"'";
  return (receipt.source.argv??[]).map(quote).join(' ');
}
