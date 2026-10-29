"""Scoped deterministic claim support. No free-text entailment or confidence oracle."""

from rootweaver_resolve.contracts import (
    Claim,
    Evidence,
    EvidenceUse,
    Incident,
    Operation,
    Predicate,
    SupportAssessment,
    Verdict,
    timestamp,
)
from rootweaver_resolve.ledger import evidence_id
from rootweaver_resolve.namespace import IncompleteObservation, associate, collection

REQUIREMENTS = {
    Predicate.PODS_READY: (Operation.PODS,),
    Predicate.SERVICE_EXISTS: (Operation.NETWORK,),
    Predicate.NO_READY_ENDPOINTS: (Operation.NETWORK,),
    Predicate.SELECTOR_DISJOINT: (Operation.NETWORK, Operation.PODS),
    Predicate.SERVICE_SELECTION_FAILURE: (Operation.NETWORK, Operation.PODS),
}


def _labels(value):
    if (
        not isinstance(value, dict)
        or not value
        or any(
            not isinstance(k, str) or not isinstance(v, str) for k, v in value.items()
        )
    ):
        raise IncompleteObservation("explicit nonempty label/selector mapping required")
    return value


def _matches(labels, selector):
    return all(labels.get(k) == v for k, v in selector.items())


def _no_ready_endpoints(slices):
    ready = False
    for item in slices:
        if not isinstance(item.get("endpoints"), list):
            raise IncompleteObservation("endpoint array missing")
        for endpoint in item["endpoints"]:
            if not isinstance(endpoint, dict):
                raise IncompleteObservation("malformed endpoint")
            condition = endpoint.get("conditions", {}).get("ready")
            if type(condition) is not bool:
                raise IncompleteObservation("endpoint readiness unknown")
            if condition:
                if not endpoint.get("addresses"):
                    raise IncompleteObservation("ready endpoint lacks address")
                ready = True
    return not ready


def assess(
    claim: Claim, incident: Incident, records: tuple[Evidence, ...]
) -> SupportAssessment:
    by_id = {r.evidence_id: r for r in records}
    if (
        not claim.evidence_ids
        or len(set(claim.evidence_ids)) != len(claim.evidence_ids)
        or any(
            identity not in by_id or evidence_id(by_id[identity].batch) != identity
            for identity in claim.evidence_ids
        )
    ):
        return SupportAssessment(
            Verdict.INVALID_REFERENCE,
            "missing, duplicate or content-inconsistent evidence reference",
        )
    requirements = REQUIREMENTS.get(claim.predicate)
    if requirements is None:
        return SupportAssessment(
            Verdict.UNSUPPORTED,
            "no support rule for this claim in this observation vocabulary",
        )
    selected = [by_id[identity] for identity in claim.evidence_ids]
    if any(r.batch.operation not in requirements for r in selected):
        return SupportAssessment(
            Verdict.UNSUPPORTED, "claim cites an irrelevant observation operation"
        )
    grouped = {
        op: [r for r in selected if r.batch.operation == op] for op in requirements
    }
    if any(len(items) > 1 for items in grouped.values()):
        return SupportAssessment(
            Verdict.CONTRADICTORY, "multiple snapshots require explicit reconciliation"
        )
    if any(not items for items in grouped.values()):
        return SupportAssessment(
            Verdict.INCOMPLETE, "required discriminating observation missing"
        )
    try:
        times = [timestamp(r.batch.observed_at) for r in selected]
        if (
            len({r.batch.source_id for r in selected}) != 1
            or any(
                t < timestamp(incident.window_start)
                or t > timestamp(incident.window_end)
                for t in times
            )
            or (max(times) - min(times)).total_seconds() > 30
        ):
            raise IncompleteObservation("source or observation window inconsistent")
        network = grouped.get(Operation.NETWORK)
        service = slices = None
        if network:
            service, slices = associate(network[0].batch, incident)
        pods = []
        if Operation.PODS in grouped:
            pods = collection(grouped[Operation.PODS][0].batch, incident)
            for pod in pods:
                _labels(pod.get("labels"))
                if type(pod.get("ready")) is not bool or not isinstance(
                    pod.get("phase"), str
                ):
                    raise IncompleteObservation("pod readiness/phase unknown")
            intended = [
                p for p in pods if _matches(p["labels"], dict(incident.workload_labels))
            ]
            if not intended:
                raise IncompleteObservation(
                    "no intended workload observed independently of Service selector"
                )
            all_ready = all(p["phase"] == "Running" and p["ready"] for p in intended)
        else:
            intended, all_ready = [], False
        if claim.predicate == Predicate.SERVICE_EXISTS:
            supported, reason = (
                True,
                "exact target Service observed; reachability remains unknown",
            )
        elif claim.predicate == Predicate.PODS_READY:
            supported, reason = (
                all_ready,
                "intended pod phase and readiness only; HTTP correctness remains unknown",
            )
        elif claim.predicate == Predicate.NO_READY_ENDPOINTS:
            supported, reason = (
                _no_ready_endpoints(slices),
                "complete associated slice collection inspected for explicit readiness",
            )
        else:
            selector = _labels(service.get("selector"))
            if not all_ready:
                raise IncompleteObservation(
                    "intended workload readiness does not rule out missing/unready replicas"
                )
            disjoint = not any(_matches(p["labels"], selector) for p in intended)
            zero = _no_ready_endpoints(slices)
            selected_ready = any(
                p["ready"]
                and p["phase"] == "Running"
                and _matches(p["labels"], selector)
                for p in pods
            )
            if disjoint and (not zero or selected_ready):
                return SupportAssessment(
                    Verdict.CONTRADICTORY,
                    "selector exclusion conflicts with observed ready backends",
                )
            supported = (
                disjoint
                if claim.predicate == Predicate.SELECTOR_DISJOINT
                else disjoint and zero
            )
            reason = (
                "Service selector excludes independently identified Ready workload and complete slices have no Ready backends; "
                "supports this Service route only, not release causation or application correctness"
                if supported
                else "Service selector matches at least one independently intended Ready pod; Service-selection failure is not supported"
            )
        uses = []
        for record in selected:
            uses.extend(
                EvidenceUse(record.evidence_id, pointer)
                for pointer in (
                    "/source_id",
                    "/observed_at",
                    "/complete_kinds",
                    "/status",
                )
            )
            for index, row in enumerate(collection(record.batch, incident)):
                if row["kind"] == "Pod":
                    fields = ("labels", "phase", "ready")
                elif row["kind"] == "Service" and row["name"] == incident.service:
                    fields = ("name", "namespace", "selector")
                elif (
                    row["kind"] == "EndpointSlice"
                    and row.get("service_name") == incident.service
                ):
                    fields = ("service_name", "endpoints")
                else:
                    continue
                uses.extend(
                    EvidenceUse(record.evidence_id, f"resources_json#/{index}/{field}")
                    for field in fields
                )
        uses = tuple(uses)
        return SupportAssessment(
            Verdict.SUPPORTED if supported else Verdict.REFUTED, reason, uses
        )
    except (
        IncompleteObservation,
        TypeError,
        AttributeError,
        KeyError,
        ValueError,
    ) as error:
        return SupportAssessment(Verdict.INCOMPLETE, str(error))
