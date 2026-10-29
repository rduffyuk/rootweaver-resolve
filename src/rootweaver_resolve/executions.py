"""Secret-free typed execution metadata; evidence IDs remain owned by the original ledger."""

from dataclasses import dataclass
from datetime import datetime, timezone
from time import monotonic
from uuid import uuid4

from rootweaver_resolve.evidence_view import safe_json


@dataclass(frozen=True)
class ExecutionRecord:
    invocation_id: str
    correlation_id: str
    parent_invocation_id: str | None
    initiator: str
    execution_mode: str
    actor_identity: str
    actual_operation: str
    validated_arguments_json: str
    target: str
    scope: str
    started_at: str
    ended_at: str
    duration_ms: float
    status: str
    error_code: str | None
    input_evidence_refs: tuple[str, ...]
    output_evidence_refs: tuple[str, ...]
    proposal_disposition: str
    model_proposal_json: str | None
    redaction_status: str
    limitations: tuple[str, ...]


class Journal:
    def __init__(self, correlation_id):
        self.correlation_id = correlation_id
        self.records = []

    def begin(
        self,
        operation,
        arguments,
        *,
        initiator,
        mode,
        actor,
        target,
        scope,
        input_refs=(),
        parent=None,
    ):
        if initiator not in {"model", "human", "controller", "replay"} or mode not in {
            "replay",
            "simulated",
            "live",
        }:
            raise ValueError("invalid execution attribution")
        return {
            "invocation_id": str(uuid4()),
            "parent_invocation_id": parent,
            "initiator": initiator,
            "execution_mode": mode,
            "actor_identity": actor,
            "actual_operation": operation,
            "validated_arguments_json": safe_json(arguments),
            "target": target,
            "scope": scope,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "tick": monotonic(),
            "input_evidence_refs": tuple(input_refs),
        }

    def finish(
        self,
        started,
        *,
        status,
        error_code=None,
        output_refs=(),
        disposition="not_applicable",
        proposal=None,
    ):
        if status not in {"ok", "error", "denied"} or disposition not in {
            "accepted",
            "rejected",
            "not_applicable",
        }:
            raise ValueError("invalid execution disposition")
        fields = dict(started)
        tick = fields.pop("tick")
        record = ExecutionRecord(
            **fields,
            correlation_id=self.correlation_id,
            ended_at=datetime.now(timezone.utc).isoformat(),
            duration_ms=round((monotonic() - tick) * 1000, 3),
            status=status,
            error_code=error_code,
            output_evidence_refs=tuple(output_refs),
            proposal_disposition=disposition,
            model_proposal_json=safe_json(proposal) if proposal is not None else None,
            redaction_status="secret-fields-excluded",
            limitations=(
                "Actor identity is application-declared, not remote producer attestation.",
                "Replay observations are never live Kubernetes operations; no shell command is inferred.",
            ),
        )
        self.records.append(record)
        return record
