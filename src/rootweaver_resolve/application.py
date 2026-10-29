"""One bounded local replay workspace; presentation never licenses a diagnosis."""

from dataclasses import asdict
from pathlib import Path
from threading import Lock
from uuid import uuid4

from rootweaver_resolve.broker import Broker
from rootweaver_resolve.contracts import Claim, ClaimSupport, Predicate
from rootweaver_resolve.controller import TERMINAL, Controller
from rootweaver_resolve.policy import candidate
from rootweaver_resolve.replay import load_fixture
from rootweaver_resolve.support import REQUIREMENTS, assess

SCENARIOS = {
    "recorded": ("Recorded observations", "observations.json"),
    "matching": ("Matching selector / Ready endpoint", "matching.json"),
    "missing": ("Workload observation unavailable", "missing.json"),
    "conflicting": ("Conflicting backend observations", "conflicting.json"),
}
FIXTURES = Path(__file__).with_name("fixtures")
if not FIXTURES.is_dir():
    FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
LIMITATIONS = (
    "Synthetic deterministic replay. No model or live Kubernetes request is invoked.",
    "Completeness and source identity are provider declarations; content hashes do not authenticate a producer.",
    "Observation times must be inside the incident window and within 30 seconds; this is not an atomic snapshot.",
    "Intended workload labels and the affected traffic route are supplied incident context, not independently authenticated intent.",
    "Namespace/name associations are not owner-UID authentication. Pod readiness does not establish HTTP or application correctness.",
    "A supported finding applies to this Service selection mechanism and observation window, not universal causality or release causation.",
)


class Conflict(ValueError):
    """A different tab/reset/step superseded the submitted workspace revision."""


class Application:
    def __init__(self, *, investigator_factory=None, controller_led=False):
        if controller_led:
            if investigator_factory is not None:
                raise ValueError("choose one investigation factory")
            from rootweaver_resolve.controller_led import ControllerLedInvestigator

            investigator_factory = ControllerLedInvestigator
        self._lock = Lock()
        self._investigator_factory = investigator_factory
        self._reset("recorded")

    def _reset(self, scenario):
        if self._investigator_factory is None:
            incident, provider = load_fixture(FIXTURES / SCENARIOS[scenario][1])
            self._controller = Controller(incident, Broker(incident, provider))
        else:
            self._controller = self._investigator_factory(scenario)
        self._scenario = scenario
        self._id = str(uuid4())
        self._revision = 0

    def _check(self, identity, revision):
        if (
            identity != self._id
            or type(revision) is not int
            or revision != self._revision
        ):
            raise Conflict("workspace changed; reload current state before continuing")

    def _snapshot(self):
        controller = self._controller
        view = controller.view()
        result = controller.snapshot()
        model_run = controller.public_record() if self._investigator_factory else None
        checks = []
        for predicate in Predicate:
            claim = (
                candidate(view, predicate)
                if predicate in REQUIREMENTS
                else Claim(predicate, tuple(e.evidence_id for e in view.evidence))
            )
            assessment = assess(claim, view.incident, view.evidence)
            checks.append(asdict(ClaimSupport(claim, assessment)))
        return {
            "investigation_id": self._id,
            "revision": self._revision,
            "scenario": self._scenario,
            "scenarios": [{"id": k, "label": v[0]} for k, v in SCENARIOS.items()],
            "execution_mode": (
                model_run["execution_mode"] + "-model-with-replay-observations"
                if model_run
                else "synthetic-deterministic-replay"
            ),
            "model_invoked": bool(
                model_run
                and model_run["execution_mode"] == "live"
                and model_run["provider_calls"]
            ),
            "model_run": model_run,
            "incident": asdict(view.incident),
            "result": asdict(result),
            "gaps": [asdict(gap) for gap in view.gaps],
            "assessment": asdict(view.assessment),
            "checks": checks,
            "terminal": result.state in TERMINAL,
            "limitations": (
                model_run.get("limitations", LIMITATIONS) if model_run else LIMITATIONS
            ),
        }

    def snapshot(self):
        with self._lock:
            return self._snapshot()

    def reset(self, scenario, identity, revision):
        with self._lock:
            self._check(identity, revision)
            if not isinstance(scenario, str) or scenario not in SCENARIOS:
                raise ValueError("unknown replay")
            self._reset(scenario)
            return self._snapshot()

    def step(self, identity, revision):
        with self._lock:
            self._check(identity, revision)
            if self._controller.snapshot().state not in TERMINAL:
                self._controller.step()
                self._revision += 1
            return self._snapshot()
