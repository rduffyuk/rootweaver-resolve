"""Read-only, target-scoped broker with finite acquisition and payload budgets."""

from typing import Protocol

from rootweaver_resolve.contracts import (
    Incident,
    ObservationBatch,
    Operation,
    ToolRequest,
)
from rootweaver_resolve.ledger import Ledger


class ObservationProvider(Protocol):
    def observe(self, request: ToolRequest) -> ObservationBatch: ...


class Broker:
    def __init__(
        self, incident: Incident, provider: ObservationProvider, *, max_calls: int = 3
    ):
        if type(max_calls) is not int or not 1 <= max_calls <= 8:
            raise ValueError("call budget must be 1..8")
        self.incident = incident
        self._provider = provider
        self.ledger = Ledger()
        self.max_calls = max_calls
        self._attempts = {operation: 0 for operation in Operation}

    @property
    def attempts(self):
        return tuple(self._attempts.items())

    @property
    def exhausted(self):
        return sum(self._attempts.values()) >= self.max_calls

    def request(self, request: ToolRequest):
        if (
            not isinstance(request.operation, Operation)
            or request.namespace != self.incident.namespace
        ):
            raise ValueError("observation operation or target denied")
        if self.exhausted or self._attempts[request.operation] >= 2:
            raise ValueError("observation budget exhausted")
        self._attempts[request.operation] += 1
        try:
            batch = self._provider.observe(request)
            if (
                not isinstance(batch, ObservationBatch)
                or batch.operation != request.operation
                or batch.namespace != request.namespace
            ):
                raise ValueError("provider returned a different operation or target")
        except Exception:
            # Never serialize exception text: future provider failures may contain secrets.
            batch = ObservationBatch(
                request.operation,
                request.namespace,
                "unavailable:provider",
                self.incident.window_end,
                "error",
                (),
                "[]",
                ("provider_failed",),
            )
        return self.ledger.append(batch)
