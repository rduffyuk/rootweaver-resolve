// Authored navigation over retained evidence. Never executes tools or changes findings.
export const operationNames = {
  namespace_service_network: 'Observe → Kubernetes Services / EndpointSlices',
  namespace_workloads: 'Observe → Kubernetes workload status',
  independent_client_http: 'Independent HTTP client checks',
  client_observations: 'Independent source and control HTTP clients',
  kubernetes_application_logs: 'Observe → Kubernetes application logs',
  application_metrics_http: 'Application HTTP metrics capture',
  dns_resolution_probe: 'Retained DNS probe and native resolver check',
  prometheus: 'Observe → Prometheus query', loki: 'Observe → Loki query', tempo: 'Observe → Tempo query',
};
export function inputRows(data, stage) {
  const inputs = stage === undefined ? data.inputs : data.inputs.filter((_, i) => i === stage);
  return inputs.flatMap(input => input.view.readable_observations);
}
export function operationRefs(data, operations) {
  return [...new Set(inputRows(data).filter(row => operations.includes(row.operation)).map(row => row.evidence_id))];
}
export function fileRefs(data, files) {
  return files.filter(file => Object.hasOwn(data.forensics, file)).map(file => 'file:' + file);
}
export function retainedRecord(data, key) {
  if (key.startsWith('file:')) {
    const file = key.slice(5);
    if (!Object.hasOwn(data.forensics, file)) throw new Error('Retained source file missing: ' + file);
    const manifest = data.source_manifest.find(row => row.file === file);
    return {id: key, source: data.forensics[file], projection: null, provenance: {
      source_file: file, reference_kind: 'retained file, not a model evidence ID', original_sha256: manifest?.original_sha256,
      note: 'Model inputs are shown separately; source presence does not mean it was supplied to Ultra.',
    }};
  }
  for (const frame of data.frames) {
    const evidence = frame.result.evidence.find(item => item.evidence_id === key);
    if (evidence) return {id: key, source: evidence, projection: inputRows(data).find(row => row.evidence_id === key),
      provenance: {observed_at: evidence.batch.observed_at, source_id: evidence.batch.source_id, original_evidence_id: key}};
  }
  const item = data.evidence[key];
  return item ? {id: key, ...item} : {id: key, source: null, projection: null,
    provenance: {limitation: 'Original citation retained; no source record was acquired for this ID.'}};
}
const cases = {
  http: {
    title: 'Checkout fails while readiness stays healthy.',
    question: 'Follow the checks from failing requests to the application error.',
    clueTitle: 'What do the application logs tell us?',
    clue: 'The six supplied error events name InvalidOperation in calculate_checkout_total.',
    clueWhy: 'A Ready Pod can still fail a request. Look for the application error behind the 500 responses.',
    tool: 'Observe → Kubernetes application logs',
    files: ['during-observe-logs.json'], operations: ['kubernetes_application_logs'], focus: ['Pod'],
    nextTitle: 'Inspect the calculation failure and relevant changes.',
    next: 'Review the exception context and inputs to calculate_checkout_total, then compare relevant changes with the failure window. A release cause is still unproven.',
    nextWhy: 'The logs locate an error. They do not establish why it started.',
    modelLimit: 'Ultra’s selector label conflicts with its explanation, and it asks again for logs it already received.',
  },
  selector: {
    title: 'Checkout connections fail after the selector changes.',
    question: 'Follow the request failure to the mismatch between Service and workload labels.',
    clueTitle: 'Which labels explain the missing backend?',
    clue: 'The Service selector and the intended Ready workload have different track labels.',
    clueWhy: 'Compare the observed selector with the intended workload before attributing the failure to the application.',
    tool: 'Observe → Kubernetes workload and network observations',
    files: ['during-network.json', 'during-workload.json'], operations: ['namespace_service_network', 'namespace_workloads'], focus: ['Service', 'Pod'],
    nextTitle: 'Review the intended selector before proposing a change.',
    next: 'Verify intended workload labels and the broader incident context before considering a human-approved selector change.',
    nextWhy: 'The narrow selector mechanism is supported. The controller does not establish the full incident cause.',
    modelLimit: 'Ultra’s earlier statement that EndpointSlices contain only Ready Pods is incorrect and remains in the original response.',
  },
  dns: {
    title: 'Checkout fails when its dependency name cannot resolve.',
    question: 'Follow the HTTP failure to the captured DNS response and application error.',
    clueTitle: 'What happened to the dependency lookup?',
    clue: 'The retained probe records NXDOMAIN and a native lookup error; the control lookup succeeds.',
    clueWhy: 'Distinguish a failed dependency name from a general DNS service outage.',
    tool: 'DNS probe / native resolver check + Observe → Kubernetes logs',
    files: ['during-http-dns.json', 'during-observe-logs.json'], operations: ['dns_resolution_probe', 'kubernetes_application_logs'], focus: ['Pod'],
    nextTitle: 'Check the dependency name and its configuration.',
    next: 'Inspect the failed name, native resolver error and successful control lookup. Do not conclude that CoreDNS was down.',
    nextWhy: 'The failed lookup is observed; a general DNS outage and full incident causality remain unproven.',
    modelLimit: 'The first input omitted captured failing HTTP checks. The second adds both logs and DNS evidence, so DNS-only improvement cannot be measured.',
  },
  policy: {
    title: 'One client is refused while the control client succeeds.',
    question: 'Follow the source-specific failure and inspect policy evidence the model never received.',
    clueTitle: 'What policy evidence was actually collected?',
    clue: 'Policy and log records are retained, but the second Ultra request was blocked before it was sent.',
    clueWhy: 'Source-specific access failure warrants inspecting policy. Collected evidence and model input are separate.',
    tool: 'Observe → Kubernetes NetworkPolicy and application logs',
    files: ['during-observe-networkpolicies.json', 'during-observe-logs.json'], operations: [], focus: ['Service', 'Pod'],
    nextTitle: 'Review policy intent and the incomplete investigation.',
    next: 'Inspect source-client scope and policy rules against the successful control. Resolve the blocked comparison and watchdog repair separately; this case remains HOLD.',
    nextWhy: 'Only the first model call completed. There is no second response or model-supported policy conclusion.',
    modelLimit: 'The first response has inconsistent basis fields and invalid pointers. The second call was not sent; the watchdog needed an in-run repair.',
  },
};
export function guideFor(data) {
  const c = cases[data.id];
  if (!c) throw new Error('Unknown retained case');
  const logCount = data.forensics['during-observe-logs.json']?.observations?.length;
  const bLogs = inputRows(data, 1).find(row => row.operation === 'kubernetes_application_logs');
  const sourceRefs = fileRefs(data, c.files), clueRefs = operationRefs(data, c.operations);
  const networkRefs = operationRefs(data, ['namespace_service_network', 'namespace_workloads']);
  const clientRefs = fileRefs(data, ['remote-client.jsonl', 'remote-source-client.jsonl', 'http-stream.jsonl']);
  const clientInputs = operationRefs(data, ['independent_client_http', 'client_observations']);
  const verdict = data.frames[1].assessment.verdict;
  const finding = verdict === 'SUPPORTED'
    ? 'The selector excludes the intended Ready workload. This specific selection failure is supported.'
    : verdict === 'REFUTED'
      ? 'The selector matches an observed Ready backend. This specific selection failure is ruled out by the check.'
      : `The selection check is ${verdict.toLowerCase()}; the available evidence does not settle it.`;
  const steps = [
    {label: 'Confirm symptom', title: 'What is failing for the client?', why: 'Begin with the request outcome, then compare it with workload health.',
      status: 'Observed', result: data.impact[1].replaceAll('HTTP500', 'HTTP 500').replaceAll('HTTP200', 'HTTP 200').replace('stays200', 'stays 200').replace('control43', 'control 43 '),
      frame: 1, focus: ['Service', 'Pod'], refs: clientRefs, inputRefs: clientInputs,
      receipt: [['Selected by', 'Experiment runner (predefined checks)'], ['Collected with', 'Independent HTTP client checks'],
        ['Given to Ultra', data.id === 'selector' ? 'These client checks were not in the two model inputs.' : data.id === 'dns' ? 'Six successful checks in the first input; captured failures were omitted.' : data.id === 'policy' ? 'Source/control counts and bounded samples in the first input.' : 'Six selected checks: three checkout 500s and three readiness 200s.']],
      sourceLabel: 'See captured requests', model: null},
    {label: 'Check selection', title: 'Does the Service select a Ready backend?', why: 'Check this specific routing mechanism before attributing the failure to it.',
      status: verdict === 'SUPPORTED' || verdict === 'REFUTED' ? 'Checked by rules' : 'Evidence limited', result: finding,
      frame: 1, focus: ['Service', 'EndpointSlice', 'Pod'], refs: networkRefs, inputRefs: networkRefs,
      receipt: [['Selected by', 'Experiment runner (predefined checks)'], ['Collected with', 'Observe → Kubernetes Services, EndpointSlices and Pods'],
        ['Checked by', 'Deterministic selector-support rules; model prose has no authority.']],
      sourceLabel: 'See Kubernetes observations', model: null},
    {label: data.id === 'selector' ? 'Compare labels' : data.id === 'dns' ? 'Inspect DNS' : data.id === 'policy' ? 'Inspect policy' : 'Inspect errors',
      title: c.clueTitle, why: c.clueWhy, status: data.id === 'policy' ? 'Second call not sent' : 'Evidence + AI', result: c.clue,
      frame: 2, focus: c.focus, refs: sourceRefs.length ? sourceRefs : clueRefs, inputRefs: clueRefs,
      receipt: [['Selected by', 'Experiment runner; Ultra did not choose this collection.'], ['Collected with', c.tool],
        ['Returned', logCount === undefined ? 'Retained Kubernetes observations; open the complete source.' : `${logCount} captured log records${data.id === 'dns' ? ' plus DNS probe evidence' : data.id === 'policy' ? ' plus policy observations' : ''}.`],
        ['Given to Ultra', data.id === 'policy' ? 'No policy/log enrichment was sent. The second request was blocked.' : bLogs ? `${bLogs.data.length} selected log events in the second input, alongside other evidence.` : 'Network and workload observations in the saved model inputs.']],
      sourceLabel: 'See collected evidence', model: {text: data.id === 'http' ? 'After receiving the logs, Ultra names InvalidOperation in calculate_checkout_total. This gives you an exception and operation to inspect.' : data.id === 'selector' ? 'With workload labels supplied, Ultra identifies the track-label mismatch.' : data.id === 'dns' ? 'The second response cites DNS and log evidence, but explains them only generically.' : 'The first response distinguishes transport failure and asks for policy evidence.', limit: c.modelLimit, stage: data.id === 'policy' ? 0 : 1}},
    {label: 'Suggested next check', title: c.nextTitle, why: c.nextWhy, status: 'Suggested · not run', result: c.next,
      frame: 2, focus: c.focus, refs: [], inputRefs: [],
      receipt: [['Suggested by', 'Authored investigation guide, based on the retained case.'], ['Execution', 'This next check has not been run by this viewer.'],
        ['Recovery in the experiment', data.recovery.summary]], sourceLabel: null, model: null},
  ];
  return {...c, steps};
}
export function evidenceSources(data) {
  const rows = [...new Map(inputRows(data).map(row => [row.evidence_id, row])).values()];
  const entries = rows.map(row => ({label: operationNames[row.operation] ?? row.operation, refs: [row.evidence_id],
    summary: `Recorded operation: ${row.operation}. Status: ${row.status ?? 'see source'}. ${row.scope ?? ''}`,
    count: Array.isArray(row.data) ? row.data.length : null}));
  for (const [label, files] of [
    ['Captured application logs', ['during-observe-logs.json']],
    ['Captured NetworkPolicy', ['during-observe-networkpolicies.json']],
    ['Independent HTTP request records', ['remote-client.jsonl', 'remote-source-client.jsonl', 'http-stream.jsonl']],
  ]) {
    const refs = fileRefs(data, files);
    if (refs.length) entries.push({label, refs, summary: 'Complete retained collection. Model input is a separate, bounded selection; source presence does not imply Ultra received it.'});
  }
  return entries;
}
