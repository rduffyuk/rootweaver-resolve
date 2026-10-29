import {availableReceipts, streamRows} from './workbench-data.mjs';

// This is a post-run operator summary, not another model assessment. It only
// derives timings from observations available at the selected replay step.
export function investigationSummary(session, selected) {
  const receipts = availableReceipts(session, selected);
  const packet = receipts.find(r => r.check_id === 'packets');
  const streams = packet ? streamRows(packet) : [];
  const complete = streams.filter(s => s.coverage === 'Complete timing pair');
  const sample = complete[0];
  return {
    packet, streams, complete, sample,
    checks: receipts.length,
    laterThanFin: complete.length > 0 && complete.every(s => s.response > s.fin),
    final: selected === session.steps.length - 1,
  };
}

const el = (tag, text, attrs = {}) => {
  const n = document.createElement(tag);
  if (text !== undefined) n.textContent = text;
  for (const [key, value] of Object.entries(attrs)) n.setAttribute(key, value);
  return n;
};

export function timingGraphic(sample) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 720 116');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', `Stream ${sample.id}: client payload at zero; client FIN at ${sample.fin.toFixed(3)} milliseconds; first server data at ${sample.response.toFixed(3)} milliseconds. Time spacing is proportional.`);
  const add = (tag, attrs, text) => {
    const n = document.createElementNS(svg.namespaceURI, tag);
    for (const [key, value] of Object.entries(attrs)) n.setAttribute(key, value);
    if (text !== undefined) n.textContent = text;
    svg.append(n);
  };
  const x = time => 36 + 648 * time / Math.max(sample.fin, sample.response);
  add('path', {d: 'M36 55 H684', class: 'time-baseline'});
  add('path', {d: 'M36 55 H684', class: 'time-reveal', pathLength: 1});
  const events = [
    {time: 0, label: 'Client payload', cls: 'payload', anchor: 'start'},
    {time: sample.fin, label: 'Client FIN', cls: 'fin', anchor: 'middle'},
    {time: sample.response, label: 'First server data', cls: 'response', anchor: 'end'},
  ];
  for (const event of events) {
    add('circle', {cx: x(event.time), cy: 55, r: 6, class: event.cls});
    add('text', {x: x(event.time), y: 26, 'text-anchor': event.anchor, class: 'event-label'}, event.label);
    add('text', {x: x(event.time), y: 90, 'text-anchor': event.anchor, class: event.cls}, event.time === 0 ? '0 ms' : `≈${Math.round(event.time).toLocaleString('en-GB')} ms`);
  }
  return svg;
}

export function renderOverview(container, session, selected, onPackets, onReview) {
  const summary = investigationSummary(session, selected);
  container.replaceChildren();
  if (!summary.sample) {
    container.hidden = true;
    return;
  }
  container.hidden = false;
  const timing = el('div', undefined, {class: 'timing-overview'});
  const heading = el('div', undefined, {class: 'timing-heading'});
  heading.append(el('h2', 'The wait, measured'), el('span', `Stream ${summary.sample.id} · ${summary.complete.length} complete timing pairs`, {class: 'timing-coverage'}));
  timing.append(heading, timingGraphic(summary.sample), el('p', `${summary.streams.length - summary.complete.length} other streams have incomplete timing coverage. FIN is a transport event, not a measurement of the configured timeout.`, {class: 'timing-limit'}));
  const actions = el('div', undefined, {class: 'overview-actions'});
  const packets = el('button', 'Inspect the capture', {type: 'button', class: 'primary', id: 'inspect-capture'});
  packets.onclick = onPackets;
  actions.append(packets);
  if (summary.final) {
    const review = el('button', 'Compare model and evidence', {type: 'button', id: 'compare-model'});
    review.onclick = onReview;
    actions.append(review);
  }
  timing.append(actions);
  const readout = el('dl', undefined, {class: 'outcome-readout', 'aria-label': 'Operator handover'});
  const rows = [
    ['Established', 'The selected endpoint is reachable in the captured connections.'],
    ['Less likely', 'A wrong Service target or connection failure for these flows.'],
    ['Still open', 'What causes the delay, and what waiting budget is appropriate.'],
    ['Next investigation', 'Check the configured timeout and intended service budget; select a scoped server-side trace to locate the wait.'],
  ];
  for (const [label, text] of rows) {
    const row = el('div'); row.append(el('dt', label), el('dd', text)); readout.append(row);
  }
  container.append(timing, readout, el('p', 'Post-run operator summary. The follow-up is suggested, not run. Logs and packets cover different windows; individual requests are not correlated.', {class: 'overview-attribution'}));
}
