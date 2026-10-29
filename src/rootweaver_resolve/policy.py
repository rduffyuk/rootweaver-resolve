"""Provider-independent policy: requirements and current gaps, never fixture truth."""

from rootweaver_resolve.contracts import Claim, Predicate, Proposal, Verdict, View
from rootweaver_resolve.support import REQUIREMENTS


def candidate(view: View, predicate=Predicate.SERVICE_SELECTION_FAILURE) -> Claim:
    operations = REQUIREMENTS.get(predicate, ())
    return Claim(
        predicate,
        tuple(
            e.evidence_id
            for e in view.evidence
            if e.batch.operation in operations and e.batch.status == "complete"
        ),
    )


class OfflinePolicy:
    def choose(self, view: View) -> Proposal:
        if view.assessment.verdict == Verdict.SUPPORTED:
            return Proposal(claim=candidate(view))
        if view.assessment.verdict == Verdict.CONTRADICTORY:
            return Proposal(
                abstain_reason="conflicting topology requires new reconciled evidence"
            )
        if any(e.batch.status in {"unavailable", "error"} for e in view.evidence):
            return Proposal(
                abstain_reason="required evidence unavailable; diagnosis withheld"
            )
        attempts = dict(view.attempts)
        for gap in view.gaps:
            if attempts[gap.operation] < 2:
                return Proposal(operation=gap.operation)
        return Proposal(
            abstain_reason="available observations do not justify a registered causal diagnosis"
        )
