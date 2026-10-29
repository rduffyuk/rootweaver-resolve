import {claimLabels, operationLabels, statusText, supportedRecords, sourceValue, executionLabel, modelAssertionText} from './presenter.mjs';

const byId = id => document.getElementById(id);
const el = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
};
const badge = text => el('span', text, `badge ${text.toLowerCase()}`);
let data;
let selected;
let busy = false;

function button(text, action, className = '') {
  const node = el('button', text, className);
  node.type = 'button';
  node.addEventListener('click', action);
  return node;
}
function field(parent, label, value) {
  parent.append(el('dt', label));
  parent.append(el('dd', value, 'mono'));
}
function evidenceBlock(evidence, uses) {
  const section = el('section', undefined, 'evidence-block');
  const batch = evidence.batch;
  section.append(el('h3', operationLabels[batch.operation] ?? batch.operation));
  const metadata = el('dl');
  field(metadata, 'Source (provider declared)', batch.source_id);
  field(metadata, 'Target namespace / incident Service', `${batch.namespace} / ${data.incident.service}`);
  field(metadata, 'Observed at', batch.observed_at);
  field(metadata, 'Completeness / declared kinds', `${batch.status} / ${batch.complete_kinds.join(', ') || 'none'}`);
  section.append(metadata);
  const pointers = uses.length ? uses.map(use => use.pointer) : ['/source_id', '/observed_at', '/status', '/complete_kinds'];
  pointers.sort((a,b) => Number(!a.startsWith('resources_json#')) - Number(!b.startsWith('resources_json#')));
  for (const pointer of [...new Set(pointers)]) {
    const source = el('div', undefined, 'source-field');
    source.append(el('code', pointer));
    try { source.append(el('pre', JSON.stringify(sourceValue(evidence, pointer), null, 2))); }
    catch { source.append(el('p', 'Source field unavailable; do not treat this link as proof.', 'error')); }
    section.append(source);
  }
  const identity = el('dl');
  field(identity, 'Content identity · not producer authentication', evidence.evidence_id);
  field(identity, 'Observation limitations', batch.limitations.join('; ') || 'None declared by provider; global limits still apply.');
  section.append(identity);
  const raw = el('details'); raw.append(el('summary', 'Full normalized observation'));
  raw.append(el('pre', JSON.stringify(JSON.parse(batch.resources_json), null, 2))); section.append(raw);
  return section;
}
function inspect(selection, focus = false) {
  selected = selection;
  const root = byId('inspector'); root.replaceChildren();
  if (selection.kind === 'claim' || selection.kind === 'technical') {
    const record = selection.kind === 'technical'
      ? data.result.technical_findings.find(r => r.claim.predicate === selection.id && r.nomination_origin === selection.origin)
      : data.result.support_records.find(r => r.claim.predicate === selection.id);
    if (!record) return;
    root.append(el('h3', claimLabels[record.claim.predicate]), badge(record.assessment.verdict), el('p', record.assessment.reason), el('p', record.assessment.policy_version, 'mono'));
    for (const id of record.claim.evidence_ids) {
      const evidence = data.result.evidence.find(e => e.evidence_id === id);
      if (evidence) root.append(evidenceBlock(evidence, record.assessment.uses.filter(u => u.evidence_id === id)));
    }
  } else {
    const evidence = data.result.evidence.find(e => e.evidence_id === selection.id);
    if (evidence) root.append(evidenceBlock(evidence, []));
  }
  if (focus) {
    root.tabIndex = -1; root.focus({preventScroll: true});
    if (matchMedia('(max-width: 1100px)').matches) root.scrollIntoView({behavior: 'instant', block: 'start'});
  }
}
function render() {
  const result = data.result;
  byId('execution-mode').textContent = executionLabel(data);
  byId('model-panel').hidden = !data.model_run;
  if (data.model_run) {
    const nodes = [el('p', data.model_run.model_id, 'mono')];
    if (data.model_run.acquisition_owner === 'controller') nodes.push(el('p', 'Acquisition and supported findings: controller. Model analysis is unverified interpretation. Qualification awaits explicit semantic review.', 'muted'));
    for (const [index, decision] of data.model_run.decisions.entries()) {
      const row = el('div', undefined, 'check');
      row.append(el('strong', `${decision.analysis_kind ? 'Model analysis' : 'Model decision'} ${index + 1}${decision.analysis_kind ? ' · ' + decision.analysis_kind : ''}`), badge(decision.analysis_kind && decision.disposition === 'accepted' ? 'STRUCTURE VALID' : decision.disposition.toUpperCase()));
      if (decision.proposal) {
        for (const hypothesis of decision.proposal.hypotheses) {
          row.append(el('p', modelAssertionText(hypothesis)));
          for (const id of hypothesis.evidence_ids) row.append(button('Inspect model-cited observation', () => inspect({kind:'evidence', id}, true), 'text-button'));
        }
        if (decision.proposal.decision) row.append(el('pre', JSON.stringify(decision.proposal.decision, null, 2)));
        row.append(el('pre', JSON.stringify(decision.proposal.incident_assessment, null, 2)));
      }
      row.append(el('p', `Controller: ${decision.controller_reason}`, 'muted'));
      nodes.push(row);
    }
    for (const call of data.model_run.provider_calls) {
      nodes.push(el('pre', JSON.stringify({finish_reason:call.finish_reason, output_tokens:call.output_tokens,
        reasoning_tokens:call.reasoning_tokens, terminated_by_token_limit:call.terminated_by_token_limit,
        final_content_present:call.final_content_present, final_content_complete:call.final_content_complete,
        proposal_parse_status:call.proposal_parse_status, proposal_validation_status:call.proposal_validation_status,
        controller_validation_status:call.controller_validation_status}, null, 2)));
    }
    const budget = data.model_run.budget;
    if (budget) nodes.push(el('p', `${budget.attempts}/${budget.max_attempts} total provider attempts · $${budget.reserved_usd.toFixed(5)} reserved / $${budget.max_reserved_usd.toFixed(2)} request allowance. Billing is unverified.`, 'mono'));
    for (const execution of data.model_run.executions ?? []) {
      const row = el('details');
      row.append(el('summary', `${execution.initiator} · ${execution.actual_operation} · ${execution.execution_mode} · ${execution.status}`));
      row.append(el('pre', JSON.stringify(execution, null, 2)));
      for (const id of execution.output_evidence_refs) if (data.result.evidence.some(e => e.evidence_id === id)) row.append(button('Inspect originating observation', () => inspect({kind:'evidence', id}, true), 'text-button'));
      nodes.push(row);
    }
    byId('model-decisions').replaceChildren(...nodes);
  }
  byId('symptom').textContent = data.incident.symptom;
  byId('incident-heading').textContent = `${data.incident.service} · incident investigation`;
  byId('target').textContent = `${data.incident.namespace} / ${data.incident.service}`;
  byId('progress').textContent = `${result.evidence.length} observations · step ${data.revision}`;
  if (!byId('scenario').options.length) for (const scenario of data.scenarios) {
    const option = el('option', scenario.label); option.value = scenario.id; byId('scenario').append(option);
  }
  byId('scenario').value = data.scenario;
  byId('step').disabled = busy || data.terminal;
  byId('step').textContent = data.terminal ? 'Investigation finished' : data.assessment.verdict === 'SUPPORTED' ? 'Assess next proposal' : 'Observe next step';
  byId('reset').disabled = busy; byId('scenario').disabled = busy;
  byId('state').textContent = result.state.replaceAll('_', ' ');
  byId('verdict').textContent = statusText(data);
  byId('technical-findings').replaceChildren(...(result.technical_findings.length ? result.technical_findings.map(finding => {
    const row = el('div', undefined, 'check');
    row.append(button(claimLabels[finding.claim.predicate], () => inspect({kind:'technical', id:finding.claim.predicate, origin:finding.nomination_origin}, true), 'claim'),
      el('p', `Origin: ${finding.nomination_origin} · validation: ${finding.validation_actor} · ${finding.assessment.verdict}`),
      el('p', `${finding.scope.namespace}/${finding.scope.service} · ${finding.scope.window_start} → ${finding.scope.window_end}`, 'mono'),
      el('p', finding.limitations.join(' '), 'muted'));
    return row;
  }) : [el('p', 'No supported technical finding established.')]));
  const causal = result.incident_assessment;
  byId('incident-assessment').replaceChildren(
    el('p', `${causal.outcome.toUpperCase()} · assessed by ${result.incident_assessment_origin}. Whether the finding explains the reported incident remains unproven.`),
    el('p', `Competing explanations: ${causal.competing_hypotheses.join(', ') || 'None nominated; absence is not exclusion.'}`),
    el('p', `Missing causal evidence: ${causal.missing_evidence.join('; ') || 'No additional evidence nominated; causality is still unverified.'}`));
  byId('assessment').textContent = data.assessment.reason;
  byId('status').className = `status ${result.diagnosis ? 'supported' : result.state === 'ABSTAINED' ? 'abstained' : ''}`;
  byId('hypotheses').replaceChildren(...result.hypotheses.map(h => {
    const row = el('div', undefined, 'hypothesis');
    row.append(el('p', h.statement), badge(h.status)); return row;
  }));
  const gaps = data.gaps.map(g => {
    const row = el('div', undefined, 'gap'); row.append(el('strong', operationLabels[g.operation] ?? g.operation), el('p', g.reason, 'muted')); return row;
  });
  byId('gaps').replaceChildren(...(gaps.length ? gaps : [el('p', data.assessment.verdict === 'SUPPORTED' ? (result.diagnosis ? 'Required collections acquired and nominated technical claim validated within the declared scope.' : 'Required collections acquired. Independent scoped support is checked separately from candidate acceptance and incident causality.') : `No collection is missing. Assessment: ${data.assessment.verdict}. ${data.assessment.reason}`, 'muted')]));
  byId('timeline').replaceChildren(...result.trace.map(event => {
    const item = el('li'); item.append(el('span', String(event.sequence).padStart(2, '0'), 'sequence'), el('strong', event.state.replaceAll('_', ' ')), el('p', event.reason));
    if (event.operation) item.append(el('p', operationLabels[event.operation], 'mono'));
    for (const id of event.evidence_ids) {
      const record = result.evidence.find(e => e.evidence_id === id);
      if (record) item.append(button(`Inspect observation · ${record.batch.observed_at.slice(11, 19)} UTC`, () => inspect({kind:'evidence', id}, true), 'text-button'));
    }
    return item;
  }));
  const records = supportedRecords(data);
  byId('claim-count').textContent = records.length;
  byId('claims').replaceChildren(...(records.length ? records.map(record => {
    const node = button(claimLabels[record.claim.predicate] ?? record.claim.predicate, () => inspect({kind:'claim', id:record.claim.predicate}, true), 'claim');
    node.dataset.predicate = record.claim.predicate; node.append(badge(record.assessment.verdict)); return node;
  }) : [el('p', 'No nominated technical claim accepted. Independent controller findings, if any, are listed separately above.', 'empty')]));
  byId('checks').replaceChildren(...data.checks.map(record => {
    const row = el('div', undefined, 'check'); row.dataset.predicate = record.claim.predicate;
    row.append(el('strong', claimLabels[record.claim.predicate]), badge(record.assessment.verdict), el('p', record.assessment.reason, 'muted')); return row;
  }));
  const action = byId('action'); action.replaceChildren();
  if (result.action) {
    const proposed = result.action;
    action.append(badge('NOT EXECUTED'), el('p', proposed.description), el('p', `Target: ${proposed.target}`, 'mono'));
    const preconditions = el('ul'); for (const condition of proposed.preconditions) preconditions.append(el('li', condition));
    action.append(el('h3', 'Before any approved change'), preconditions, el('h3', 'Rollback'), el('p', proposed.rollback), el('h3', 'Verification'), el('p', proposed.verification));
  } else action.append(el('p', 'No action proposed. A human must review any future configuration change.'));
  action.append(el('p', 'This application cannot approve or execute a change.', 'muted'));
  byId('limitations').replaceChildren(...data.limitations.map(limit => el('li', limit)));
  byId('window').textContent = `Observation window: ${data.incident.window_start} → ${data.incident.window_end}. Intended labels: ${JSON.stringify(Object.fromEntries(data.incident.workload_labels))}`;
  if (selected) inspect(selected);
}
async function request(path, body) {
  if (busy) return;
  busy = true;
  if (data) render();
  byId('error').hidden = true;
  try {
    const options = body ? {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)} : {};
    const response = await fetch(path, {...options, signal:AbortSignal.timeout(8000)});
    if (!response.ok) throw new Error(response.status === 409 ? 'Another replay change superseded this screen. Reload the page to continue.' : 'Local request failed. Reload to reconcile the current investigation.');
    data = await response.json(); render();
  } catch (error) {
    byId('error').textContent = error.message; byId('error').hidden = false;
  } finally { busy = false; if (data) render(); }
}
function reset() {
  const scenario = byId('scenario').value; selected = undefined;
  byId('inspector').replaceChildren(el('p', 'Select a retained observation or supported claim. Future replay observations are not yet evidence.', 'empty'));
  return request('/api/reset', {scenario, investigation_id:data.investigation_id, revision:data.revision});
}
byId('reset').addEventListener('click', reset);
byId('scenario').addEventListener('change', reset);
byId('step').addEventListener('click', () => request('/api/step', {investigation_id:data.investigation_id, revision:data.revision}));
request('/api/state');
