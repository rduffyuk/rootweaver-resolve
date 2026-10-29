"""Immutable public contracts. Predicates, not free text, define supported claims."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Operation(StrEnum):
    PODS = "namespace_workloads"
    NETWORK = "namespace_service_network"


class Predicate(StrEnum):
    PODS_READY = "intended_pods_ready"
    SERVICE_EXISTS = "service_exists"
    NO_READY_ENDPOINTS = "service_has_no_ready_endpoints"
    SELECTOR_DISJOINT = "selector_excludes_intended_ready_pods"
    SERVICE_SELECTION_FAILURE = "service_selection_failure"
    HTTP_HEALTHY = "http_responses_healthy"
    SERVICE_REACHABLE = "service_reachable"
    NETWORKPOLICY_CAUSE = "networkpolicy_caused_failure"
    APP_CORRECT = "application_correct"
    APP_REGRESSION = "release_caused_application_regression"


class Verdict(StrEnum):
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    INCOMPLETE = "INCOMPLETE"
    CONTRADICTORY = "CONTRADICTORY"
    UNSUPPORTED = "UNSUPPORTED"
    INVALID_REFERENCE = "INVALID_REFERENCE"


class State(StrEnum):
    INVESTIGATING = "INVESTIGATING"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    EVIDENCE_UNAVAILABLE = "EVIDENCE_UNAVAILABLE"
    HYPOTHESIS_UPDATED = "HYPOTHESIS_UPDATED"
    DIAGNOSIS_SUPPORTED = "DIAGNOSIS_SUPPORTED"
    ABSTAINED = "ABSTAINED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    COMPLETE = "COMPLETE"


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("observation timestamps must include a timezone")
    return parsed


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True)
class Incident:
    incident_id: str
    namespace: str
    service: str
    workload_labels: tuple[tuple[str, str], ...]
    window_start: str
    window_end: str
    symptom: str

    def __post_init__(self):
        if not all(
            isinstance(x, str) and x
            for x in (self.incident_id, self.namespace, self.service, self.symptom)
        ):
            raise ValueError("incident identity, target and symptom are required")
        labels = tuple(tuple(pair) for pair in self.workload_labels)
        if (
            not labels
            or any(
                len(p) != 2 or not all(isinstance(x, str) and x for x in p)
                for p in labels
            )
            or len(dict(labels)) != len(labels)
        ):
            raise ValueError("independent intended workload labels required")
        object.__setattr__(self, "workload_labels", labels)
        if timestamp(self.window_start) > timestamp(self.window_end):
            raise ValueError("invalid incident observation window")


@dataclass(frozen=True)
class ObservationBatch:
    operation: Operation
    namespace: str
    source_id: str
    observed_at: str
    status: str
    complete_kinds: tuple[str, ...]
    resources_json: str
    limitations: tuple[str, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "operation", Operation(self.operation))
        object.__setattr__(self, "complete_kinds", tuple(self.complete_kinds))
        object.__setattr__(self, "limitations", tuple(self.limitations))
        if any(
            not isinstance(value, str) or not value
            for value in (
                *self.complete_kinds,
                *self.limitations,
                self.namespace,
                self.source_id,
                self.observed_at,
            )
        ):
            raise ValueError("immutable nonempty string metadata required")
        timestamp(self.observed_at)
        if (
            not self.namespace
            or not self.source_id
            or self.status not in {"complete", "partial", "unavailable", "error"}
        ):
            raise ValueError("invalid observation provenance/status")
        if len(self.resources_json.encode()) > 65536:
            raise ValueError("observation exceeds byte bound")
        value = json.loads(self.resources_json)
        if not isinstance(value, list) or len(value) > 256:
            raise ValueError("bounded resource array required")
        object.__setattr__(self, "resources_json", canonical(value))


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    batch: ObservationBatch


@dataclass(frozen=True)
class Claim:
    predicate: Predicate
    evidence_ids: tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, "predicate", Predicate(self.predicate))
        refs = tuple(self.evidence_ids)
        if len(refs) > 16 or any(
            not isinstance(value, str) or not value for value in refs
        ):
            raise ValueError("bounded string evidence IDs required")
        object.__setattr__(self, "evidence_ids", refs)


@dataclass(frozen=True)
class EvidenceUse:
    evidence_id: str
    pointer: str


@dataclass(frozen=True)
class SupportAssessment:
    verdict: Verdict
    reason: str
    uses: tuple[EvidenceUse, ...] = ()
    policy_version: str = "selection-support/v1"


@dataclass(frozen=True)
class ClaimSupport:
    claim: Claim
    assessment: SupportAssessment


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    statement: str
    status: str = "PLAUSIBLE"


@dataclass(frozen=True)
class EvidenceGap:
    operation: Operation
    reason: str


@dataclass(frozen=True)
class ToolRequest:
    operation: Operation
    namespace: str


@dataclass(frozen=True)
class Proposal:
    operation: Operation | None = None
    claim: Claim | None = None
    abstain_reason: str | None = None
    incident_assessment: IncidentCausalAssessment | None = None

    def __post_init__(self):
        if (
            sum(
                x is not None for x in (self.operation, self.claim, self.abstain_reason)
            )
            != 1
        ):
            raise ValueError("one proposal kind required")
        if self.operation is not None:
            object.__setattr__(self, "operation", Operation(self.operation))
        if self.claim is not None and not isinstance(self.claim, Claim):
            raise ValueError("typed claim required")
        if self.abstain_reason is not None and not isinstance(self.abstain_reason, str):
            raise ValueError("public abstention reason must be a string")
        if self.incident_assessment is not None and not isinstance(
            self.incident_assessment, IncidentCausalAssessment
        ):
            raise ValueError("typed incident assessment required")


@dataclass(frozen=True)
class IncidentCausalAssessment:
    """No current evidence rule licenses supported incident-level causality."""

    outcome: str = "uncertain"
    explains_incident: None = None
    competing_hypotheses: tuple[str, ...] = ("application-regression",)
    missing_evidence: tuple[str, ...] = (
        "Request-level failure, route and application evidence remain unverified.",
    )

    def __post_init__(self):
        if (
            self.outcome not in {"uncertain", "abstained"}
            or self.explains_incident is not None
        ):
            raise ValueError("incident_causality_not_licensed")
        for name in ("competing_hypotheses", "missing_evidence"):
            values = tuple(getattr(self, name))
            if len(values) > 4 or any(
                not isinstance(s, str) or not 1 <= len(s) <= 180 for s in values
            ):
                raise ValueError("incident_assessment_invalid")
            object.__setattr__(self, name, values)
        if any(
            h not in {"service-selection", "application-regression"}
            for h in self.competing_hypotheses
        ):
            raise ValueError("incident_assessment_invalid")


@dataclass(frozen=True)
class FindingScope:
    namespace: str
    service: str
    window_start: str
    window_end: str


@dataclass(frozen=True)
class TechnicalFinding:
    claim: Claim
    assessment: SupportAssessment
    scope: FindingScope
    nomination_origin: str
    validation_actor: str = "controller"
    limitations: tuple[str, ...] = (
        "Scoped Service-selection mechanism only; reported incident causality is unresolved.",
        "Workload intent, source identity and collection completeness are supplied declarations.",
        "Readiness is not HTTP correctness; snapshots are not atomic; release causation is unverified.",
    )


@dataclass(frozen=True)
class FindingAuditRecord:
    sequence: int
    event: str
    actor: str
    claim: Claim | None = None
    assessment: SupportAssessment | None = None


@dataclass(frozen=True)
class Action:
    target: str
    description: str
    preconditions: tuple[str, ...]
    rollback: str
    verification: str
    human_approval_required: bool = True
    executed: bool = False


@dataclass(frozen=True)
class AuditRecord:
    sequence: int
    previous_state: State | None
    state: State
    reason: str
    evidence_ids: tuple[str, ...] = ()
    operation: Operation | None = None


@dataclass(frozen=True)
class View:
    incident: Incident
    evidence: tuple[Evidence, ...]
    gaps: tuple[EvidenceGap, ...]
    attempts: tuple[tuple[Operation, int], ...]
    assessment: SupportAssessment


@dataclass(frozen=True)
class Result:
    state: State
    diagnosis: Claim | None
    claims: tuple[Claim, ...]
    hypotheses: tuple[Hypothesis, ...]
    evidence: tuple[Evidence, ...]
    trace: tuple[AuditRecord, ...]
    action: Action | None
    support_records: tuple[ClaimSupport, ...] = ()
    technical_findings: tuple[TechnicalFinding, ...] = ()
    incident_assessment: IncidentCausalAssessment = IncidentCausalAssessment()
    incident_assessment_origin: str = "controller"
    finding_audit: tuple[FindingAuditRecord, ...] = ()
