"""Pure bounded namespace-result adapter; never uses named-Service filtering."""

import json

from rootweaver_resolve.contracts import Incident, ObservationBatch, Operation


class IncompleteObservation(ValueError):
    """The collection cannot establish target absence or consistent topology."""


def collection(batch: ObservationBatch, incident: Incident) -> list[dict]:
    required = (
        {"Pod"} if batch.operation == Operation.PODS else {"Service", "EndpointSlice"}
    )
    if (
        batch.namespace != incident.namespace
        or batch.status != "complete"
        or batch.limitations
        or not required <= set(batch.complete_kinds)
    ):
        raise IncompleteObservation(
            "required namespace collection is unavailable or incomplete"
        )
    rows = json.loads(batch.resources_json)
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("kind") not in required:
            raise IncompleteObservation("resource kind does not belong to operation")
        if row.get("namespace") != incident.namespace or not row.get("name"):
            raise IncompleteObservation(
                "foreign namespace or missing resource identity"
            )
        identity = (row["kind"], row["name"])
        if identity in seen:
            raise IncompleteObservation("duplicate resource identity")
        seen.add(identity)
    return rows


def associate(
    batch: ObservationBatch, incident: Incident
) -> tuple[dict, tuple[dict, ...]]:
    if batch.operation != Operation.NETWORK:
        raise IncompleteObservation("network operation required")
    rows = collection(batch, incident)
    services = [
        r for r in rows if r["kind"] == "Service" and r["name"] == incident.service
    ]
    if len(services) != 1:
        raise IncompleteObservation("exact target Service not observed")
    slices = []
    for row in rows:
        if row["kind"] != "EndpointSlice":
            continue
        if not isinstance(row.get("service_name"), str) or not row["service_name"]:
            raise IncompleteObservation("EndpointSlice association unknown")
        if row["service_name"] == incident.service:
            slices.append(row)
    return services[0], tuple(slices)
