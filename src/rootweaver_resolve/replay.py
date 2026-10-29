"""Observation-only replay storage. No cause, expected answer or tool-sequence fields."""

import json
from pathlib import Path

from rootweaver_resolve.contracts import Incident, ObservationBatch, Operation


class ReplayProvider:
    def __init__(self, batches):
        self._batches = tuple(batches)
        self._offsets = {op: 0 for op in Operation}

    def observe(self, request):
        matching = tuple(
            b
            for b in self._batches
            if b.operation == request.operation and b.namespace == request.namespace
        )
        offset = self._offsets[request.operation]
        self._offsets[request.operation] += 1
        if offset >= len(matching):
            raise ValueError("no further replay observation for requested scope")
        return matching[offset]


def load_fixture(path):
    data = Path(path).read_bytes()
    if len(data) > 262144:
        raise ValueError("fixture byte bound exceeded")
    fixture = json.loads(data)
    if not isinstance(fixture, dict) or set(fixture) != {"incident", "observations"}:
        raise ValueError("fixture must contain only incident and observations")
    incident = Incident(**fixture["incident"])
    batches = []
    if (
        not isinstance(fixture["observations"], list)
        or len(fixture["observations"]) > 8
    ):
        raise ValueError("bounded observation list required")
    for row in fixture["observations"]:
        if set(row) - {
            "operation",
            "namespace",
            "source_id",
            "observed_at",
            "status",
            "complete_kinds",
            "resources",
            "limitations",
        }:
            raise ValueError("unknown replay observation field")
        fields = dict(row)
        fields["resources_json"] = json.dumps(fields.pop("resources"), allow_nan=False)
        batches.append(ObservationBatch(**fields))
    return incident, ReplayProvider(batches)
