"""Deterministic state owner. Policies propose; support rules license conclusions."""

from rootweaver_resolve.contracts import (
    Action,
    AuditRecord,
    ClaimSupport,
    EvidenceGap,
    FindingAuditRecord,
    FindingScope,
    Hypothesis,
    Incident,
    IncidentCausalAssessment,
    Predicate,
    Proposal,
    Result,
    State,
    SupportAssessment,
    TechnicalFinding,
    ToolRequest,
    Verdict,
    View,
)
from rootweaver_resolve.policy import OfflinePolicy, candidate
from rootweaver_resolve.support import REQUIREMENTS, assess

TERMINAL = {State.ABSTAINED, State.AWAITING_APPROVAL, State.COMPLETE}
ALLOWED = {
    State.INVESTIGATING: {
        State.INSUFFICIENT_EVIDENCE,
        State.HYPOTHESIS_UPDATED,
        State.EVIDENCE_UNAVAILABLE,
        State.ABSTAINED,
    },
    State.INSUFFICIENT_EVIDENCE: {
        State.INVESTIGATING,
        State.DIAGNOSIS_SUPPORTED,
        State.INSUFFICIENT_EVIDENCE,
        State.ABSTAINED,
    },
    State.HYPOTHESIS_UPDATED: {
        State.INSUFFICIENT_EVIDENCE,
        State.DIAGNOSIS_SUPPORTED,
        State.ABSTAINED,
    },
    State.EVIDENCE_UNAVAILABLE: {State.INSUFFICIENT_EVIDENCE, State.ABSTAINED},
    State.DIAGNOSIS_SUPPORTED: {State.AWAITING_APPROVAL, State.COMPLETE},
}


class Controller:
    def __init__(
        self,
        incident: Incident,
        broker,
        *,
        policy=None,
        max_steps: int = 8,
        policy_origin="controller",
    ):
        if broker.incident != incident:
            raise ValueError("broker target differs from investigation")
        if type(max_steps) is not int or not 1 <= max_steps <= 32:
            raise ValueError("step budget must be 1..32")
        self.incident = incident
        self._broker = broker
        self._policy = policy or OfflinePolicy()
        if policy_origin not in {"controller", "model", "simulated-model"}:
            raise ValueError("invalid policy origin")
        self._policy_origin = policy_origin
        self._incident_assessment = IncidentCausalAssessment()
        self._incident_origin = "controller"
        self._finding_audit = []
        self._independent_keys = set()
        self._max_steps = max_steps
        self._steps = 0
        self._trace = [
            AuditRecord(
                1,
                None,
                State.INVESTIGATING,
                "incident opened; release correlation is not causation",
            )
        ]
        self._diagnosis = None
        self._claims = ()
        self._action = None
        self._state = State.INVESTIGATING
        self._hypotheses = (
            Hypothesis(
                "service-selection",
                "Service configuration or backend selection could explain the failed route",
            ),
            Hypothesis(
                "application-regression",
                "A release-related application regression remains possible",
            ),
        )
        self._transition(
            State.INSUFFICIENT_EVIDENCE,
            "two plausible explanations; discriminate using target Service topology and intended workload",
        )

    def _transition(self, state, reason, ids=(), operation=None):
        if state not in ALLOWED.get(self._state, set()):
            raise ValueError("invalid investigation state transition")
        self._trace.append(
            AuditRecord(
                len(self._trace) + 1, self._state, state, reason, ids, operation
            )
        )
        self._state = state

    def view(self):
        records = self._broker.ledger.records
        provisional = View(
            self.incident,
            records,
            (),
            self._broker.attempts,
            SupportAssessment(Verdict.INCOMPLETE, "required observations missing"),
        )
        claim = candidate(provisional)
        assessment = (
            assess(claim, self.incident, records)
            if claim.evidence_ids
            else provisional.assessment
        )
        complete_ops = {
            e.batch.operation for e in records if e.batch.status == "complete"
        }
        gaps = tuple(
            EvidenceGap(
                op,
                "complete target topology and workload evidence required to distinguish hypotheses",
            )
            for op in REQUIREMENTS[Predicate.SERVICE_SELECTION_FAILURE]
            if op not in complete_ops
        )
        return View(self.incident, records, gaps, self._broker.attempts, assessment)

    def snapshot(self):
        findings = ()
        view = self.view()
        independent = candidate(view)
        if view.assessment.verdict == Verdict.SUPPORTED:
            key = independent.evidence_ids
            if key not in self._independent_keys:
                self._independent_keys.add(key)
                self._finding_event(
                    "independent_finding_established",
                    "controller",
                    independent,
                    view.assessment,
                )
            claim = self._diagnosis or independent
            findings = (
                TechnicalFinding(
                    claim,
                    assess(claim, self.incident, view.evidence),
                    FindingScope(
                        self.incident.namespace,
                        self.incident.service,
                        self.incident.window_start,
                        self.incident.window_end,
                    ),
                    self._policy_origin if self._diagnosis else "controller",
                ),
            )
        return Result(
            self._state,
            self._diagnosis,
            self._claims,
            self._hypotheses,
            self._broker.ledger.records,
            tuple(self._trace),
            self._action,
            tuple(
                ClaimSupport(
                    claim, assess(claim, self.incident, self._broker.ledger.records)
                )
                for claim in self._claims
            ),
            findings,
            self._incident_assessment,
            self._incident_origin,
            tuple(self._finding_audit),
        )

    def _finding_event(self, event, actor, claim=None, assessment=None):
        self._finding_audit.append(
            FindingAuditRecord(
                len(self._finding_audit) + 1, event, actor, claim, assessment
            )
        )

    def step(self):
        if self._state in TERMINAL:
            return self.snapshot()
        if self._steps >= self._max_steps:
            self._transition(
                State.ABSTAINED, "decision budget exhausted; no supported diagnosis"
            )
            return self.snapshot()
        self._steps += 1
        view = self.view()
        try:
            proposal = self._policy.choose(view)
            if not isinstance(proposal, Proposal):
                raise ValueError("policy proposal schema invalid")
        except Exception:
            self._transition(State.ABSTAINED, "policy_failed; diagnosis withheld")
            return self.snapshot()
        if proposal.incident_assessment is not None:
            self._incident_assessment = proposal.incident_assessment
            self._incident_origin = self._policy_origin
            if proposal.incident_assessment.outcome == "abstained":
                self._finding_event("incident_causality_abstained", self._policy_origin)
        if proposal.abstain_reason is not None:
            # Policy text is not evidence or private reasoning; default policy uses fixed public reasons.
            self._transition(State.ABSTAINED, proposal.abstain_reason[:500])
        elif proposal.claim is not None:
            self._finding_event(
                "candidate_nominated", self._policy_origin, proposal.claim
            )
            assessment = assess(proposal.claim, self.incident, view.evidence)
            if (
                proposal.claim.predicate != Predicate.SERVICE_SELECTION_FAILURE
                or assessment.verdict != Verdict.SUPPORTED
            ):
                self._finding_event(
                    "candidate_rejected", "controller", proposal.claim, assessment
                )
                self._transition(
                    State.INSUFFICIENT_EVIDENCE,
                    "rejected proposed diagnosis: " + assessment.verdict,
                    proposal.claim.evidence_ids,
                )
            else:
                self._finding_event(
                    "candidate_validated", "controller", proposal.claim, assessment
                )
                self._diagnosis = proposal.claim
                self._claims = tuple(
                    claim
                    for predicate in REQUIREMENTS
                    if (claim := candidate(view, predicate)).evidence_ids
                    and assess(claim, self.incident, view.evidence).verdict
                    == Verdict.SUPPORTED
                )
                self._transition(
                    State.DIAGNOSIS_SUPPORTED,
                    assessment.reason,
                    proposal.claim.evidence_ids,
                )
                self._action = Action(
                    f"{self.incident.namespace}/{self.incident.service}",
                    "Review and correct Service selection against the intended workload contract",
                    (
                        "human configuration review",
                        "preserve existing selector",
                        "confirm intended workload and traffic route",
                    ),
                    "restore reviewed pre-change selector if verification fails",
                    "verify selected Ready endpoints and actual checkout requests after an approved change",
                )
                self._transition(
                    State.AWAITING_APPROVAL,
                    "reversible configuration proposal only; no remediation executor",
                )
        else:
            if self._broker.exhausted:
                self._transition(
                    State.ABSTAINED, "observation budget exhausted; diagnosis withheld"
                )
                return self.snapshot()
            self._transition(
                State.INVESTIGATING,
                "acquire discriminating namespace observation",
                operation=proposal.operation,
            )
            try:
                record = self._broker.request(
                    ToolRequest(proposal.operation, self.incident.namespace)
                )
            except ValueError:
                self._transition(
                    State.ABSTAINED, "observation denied or budget exhausted"
                )
                return self.snapshot()
            after = self.view().assessment
            if record.batch.status in {"unavailable", "error"}:
                self._transition(
                    State.EVIDENCE_UNAVAILABLE,
                    "requested observation unavailable",
                    (record.evidence_id,),
                    proposal.operation,
                )
            else:
                before_status = self._hypotheses[0].status
                status = {
                    Verdict.SUPPORTED: "SUPPORTED",
                    Verdict.REFUTED: "WEAK",
                    Verdict.CONTRADICTORY: "UNRESOLVED",
                }.get(after.verdict, "PLAUSIBLE")
                self._hypotheses = (
                    Hypothesis(
                        "service-selection", self._hypotheses[0].statement, status
                    ),
                    Hypothesis(
                        "application-regression",
                        self._hypotheses[1].statement,
                        "UNRESOLVED" if status == "SUPPORTED" else "PLAUSIBLE",
                    ),
                )
                if status != before_status:
                    self._transition(
                        State.HYPOTHESIS_UPDATED,
                        after.reason,
                        (record.evidence_id,),
                        proposal.operation,
                    )
            if self._state != State.HYPOTHESIS_UPDATED:
                self._transition(
                    State.INSUFFICIENT_EVIDENCE,
                    "support reassessed: " + after.verdict + "; " + after.reason,
                    (record.evidence_id,),
                    proposal.operation,
                )
        return self.snapshot()

    def run(self):
        while self._state not in TERMINAL:
            self.step()
        return self.snapshot()
