"""Portable acceptance checks: no private services, inference or credentials."""

import json
import unittest
from pathlib import Path

import rootweaver_resolve
from rootweaver_resolve.broker import Broker
from rootweaver_resolve.controller import TERMINAL, Controller
from rootweaver_resolve.replay import load_fixture


class SubmissionTests(unittest.TestCase):
    def test_synthetic_controller_support_boundaries_are_preserved(self):
        p = Path(rootweaver_resolve.__file__).parent / "fixtures"
        for name, want in [
            ("observations", "SUPPORTED"),
            ("matching", "REFUTED"),
            ("missing", "INCOMPLETE"),
            ("conflicting", "CONTRADICTORY"),
        ]:
            incident, observations = load_fixture(p / (name + ".json"))
            c = Controller(incident, Broker(incident, observations))
            for _ in range(12):
                if c.snapshot().state in TERMINAL:
                    break
                c.step()
            self.assertEqual(c.view().assessment.verdict, want)

    def test_seven_real_public_responses_and_unsent_policy_stage_are_explicit(self):
        p = Path(rootweaver_resolve.__file__).parent / "workspace"
        release = json.loads((p / "release.json").read_text())
        self.assertEqual(release["version"], "0.5.0")
        cases = [json.loads(f.read_text()) for f in (p / "data").glob("*.json")]
        self.assertEqual(sum(len(c["decisions"]) for c in cases), 7)
        policy = next(c for c in cases if c["id"] == "policy")
        self.assertEqual(len(policy["decisions"]), 1)
        self.assertIn("blocked", policy["conflict"])
        for c in cases:
            self.assertTrue(c["public"])
            self.assertTrue(c["redaction"]["model_public_text_unchanged"])
            self.assertTrue(all("raw_public_response" in d for d in c["decisions"]))

    def test_embedded_json_has_no_private_packet_payloads_or_annotations(self):
        p = Path(rootweaver_resolve.__file__).parent / "workspace/data"

        def walk(x):
            if isinstance(x, dict):
                self.assertFalse(
                    {"query_packet_hex", "response_packet_hex", "annotations"}
                    & x.keys()
                )
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
            elif isinstance(x, str) and x.lstrip().startswith(("{", "[")):
                try:
                    v = json.loads(x)
                except ValueError:
                    return
                walk(v)

        for f in p.glob("*.json"):
            d = json.loads(f.read_text())
            walk(d["forensics"])
