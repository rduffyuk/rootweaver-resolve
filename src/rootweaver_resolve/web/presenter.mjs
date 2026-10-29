// Pure presentation helpers. State, claims and support remain server-owned.
export function executionLabel(data) {
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
