# Methodology and interpretation

## Synthetic comparison

The funded comparison contains batches 01, 02 and 03 with 6, 4 and 8 inference
POSTs respectively. Stage 1 supplied Service/EndpointSlice observations. Stage 2
added workload observations and the candidate's previous accepted public answer.
The controller acquired the fixtures; the model did not choose those checks.
The records retain requests, exact model identity, public answers when retained,
validation dispositions, usage and latency. Private reasoning was not retained.

Instructions changed between frozen batches to clarify the public vocabulary
and output contract. Consequently, validity improvements are observations across
different conditions, not a controlled estimate of a model improvement. Earlier
family-v2 records used a smaller completion allowance and are a separate reference.
Usage estimates are historical list-price calculations, not invoices or current
pricing. Completion-token counts already include any exposed reasoning subset.

Ultra was provisionally selected because its later answer connected the observed
canary/stable label mismatch with new workload evidence. It also overreached from
readiness to application health. Nano, Super and Super VL had their own citation,
stale-question, unsupported-history or causality problems. Structural acceptance
means schema/domain/reference checks passed; it does not validate the truth of
every sentence. The qualification/recovery/final-negative checkpoints preserve
the subsequent failures and unresolved human review. They do not pass Phase 3.

## Real disposable faults

| Case | Evidence and result | Material limitation |
|---|---|---|
| Selector — VW-2317 | Actual Service/Pod selection mismatch; two Ultra calls on retained evidence | Unsupported claim that EndpointSlices contain only Ready endpoints; model polarity/prose tension. Narrow controller support is separate from model wording and full incident causality. |
| HTTP500 — VW-2318 | 55 baseline 200s, 58 fault 500s, 50 recovery 200s; all 163 readiness responses 200. Logs added `InvalidOperation` / `calculate_checkout_total` specificity. | Both answers label selection “supported” while prose rejects a selection fault. Stage B asks for already supplied logs without specifying the missing detail. Release cause unproven. |
| DNS — VW-2319 | Real NXDOMAIN and resolver failure; two Ultra calls | Stage A inconsistency and an input-window limitation; Stage B does not supply strong mechanism specificity. Model semantic result remains FAIL. |
| Policy — VW-2320 | One completed Ultra response and a source/control contrast | Second request blocked before POST by the request-size guard. Recovery watchdog needed an in-run repair; case remains HOLD. |

These are small, adapted case demonstrations, not a randomized held-out test set.
Logs, metrics and trace summaries differ in completeness and specificity. Empty
query results do not prove absence of application events. Kubernetes readiness
and endpoint selection do not prove application correctness. Later baseline or
recovery observations shown in playback are not automatically evidence the model
had at its earlier call. The app's `inputs` fields expose the actual staged input.

Independent experiment controls restored faults. Recovery is not credited to the
model, which had no remediation authority. Captured log limits and missing
finalization receipts remain disclosed in each case's coverage/forensics fields.

## Model-selected packet investigation — VW-2321

The lab run exposed a fixed catalogue of four checks: client logs, Service and
EndpointSlice inspection, a bounded packet capture and workload status. Ultra
selected that order, received each result and revised its public hypotheses over
five calls. The host bound scope and arguments, checked references and retained
the journal. It did not treat cited prose as a deterministically proven cause.

The 74 logs and 45 TCP frames were acquired in different windows. Only six recent
log rows entered the model window; the whole capture remains available for human
inspection. Four complete request/response timings show first server data around
2,001 ms after client payload, with client FIN around 801 ms. One stream starts
mid-connection; another ends before a response. Ultra claimed five complete pairs;
the post-run review corrects that to four while retaining the original answer.

The capture supports reachability and delayed response on the observed path.
It does not establish CPU pressure, locks, garbage collection, a downstream cause,
or that the client timeout should be increased. The packet requests are not
correlated to those same six log requests. The model's final handover also follows
catalogue exhaustion; it is not proof of general autonomous stopping judgment.

## Reproduction levels

1. **Byte verification:** manifests and original response-string checks work
   offline in this repository.
2. **Presentation replay:** the standalone viewer replays retained observations
   without credentials or services.
3. **Independent packet inspection:** TShark/Wireshark can decode the supplied
   original PCAP and recalculate the timings without a live capture.
4. **Fresh fixed-evidence inference:** explicitly opt-in HTTP route with the
   owner's provider access, separate reservation state and a different prompt.
   A new answer is not a matched repeat of the historical A/B experiment.
5. **Fresh fault/capture experiment:** not included as a one-command runner.
   It requires a separately authorized disposable environment, collectors and
   independent recovery controls. Copying commands cannot recreate the old window.

The research justifies a reviewable investigation prototype and some useful
evidence synthesis. It does not justify an accuracy percentage, MTTR improvement,
production RCA qualification, autonomous repair or superiority over an SRE.
