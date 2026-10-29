"""Content-addressed append-only evidence, independent of diagnosis and truth."""

from dataclasses import asdict
from hashlib import sha256

from rootweaver_resolve.contracts import Evidence, ObservationBatch, canonical


def evidence_id(batch: ObservationBatch) -> str:
    return sha256(canonical(asdict(batch)).encode()).hexdigest()


class Ledger:
    def __init__(self):
        self._records: dict[str, Evidence] = {}

    @property
    def records(self) -> tuple[Evidence, ...]:
        return tuple(self._records.values())

    def append(self, batch: ObservationBatch) -> Evidence:
        identity = evidence_id(batch)
        if identity in self._records:
            return self._records[identity]
        if len(self._records) >= 16:
            raise ValueError("evidence record limit reached")
        record = Evidence(identity, batch)
        self._records[identity] = record
        return record
