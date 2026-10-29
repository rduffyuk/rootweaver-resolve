"""Portable runtime boundary tests; all provider responses are explicitly simulated."""

import functools
import json
import tempfile
import threading
import time
import unittest
from hashlib import sha256
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

import rootweaver_resolve
from rootweaver_resolve.fresh_analysis import (
    FreshAnalysis,
    encoded,
    public_response,
    request_for,
    verify_freeze,
)
from rootweaver_resolve.nebius import ProviderError
from rootweaver_resolve.retained_workspace import Handler

PACKAGE = Path(rootweaver_resolve.__file__).parent


class FreshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "package/workspace"
        (self.workspace / "data").mkdir(parents=True)
        raw = (PACKAGE / "workspace/data/http.json").read_bytes()
        (self.workspace / "data/http.json").write_bytes(raw)
        freeze = encoded(
            {"files": {"workspace/data/http.json": sha256(raw).hexdigest()}}
        )
        (self.workspace.parent / "live-freeze.json").write_bytes(freeze)
        self.digest = sha256(freeze).hexdigest()
        self.key = self.root / "test-key"
        self.key.write_text("NEBIUS_API_KEY=test-only-not-a-real-key\n")
        self.key.chmod(0o600)
        self.posts = []

    def response(self, request):
        ids = [
            r["evidence_id"]
            for r in json.loads(request["messages"][1]["content"])["observations"]
        ]
        return {
            "id": "simulated",
            "model": request["model"],
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": json.dumps(
                            {
                                "summary": "Simulated analysis",
                                "hypotheses": [
                                    {
                                        "title": "Application failure",
                                        "assessment": "observed",
                                        "explanation": "Simulated fixture response",
                                        "evidence_ids": ids[:1],
                                    }
                                ],
                                "uncertainty": "Cause unknown",
                                "next_check": "Review exception context",
                            }
                        )
                    },
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 100,
                "total_tokens": 200,
            },
        }

    def engine(self, **options):
        def transport(wire, key):
            self.posts.append(wire)
            return self.response(json.loads(wire))

        engine = FreshAnalysis(
            self.workspace,
            self.root / "state",
            key_file=self.key,
            freeze=self.digest,
            transport=options.pop("transport", transport),
            preflight=lambda key: None,
            **options,
        )
        self.addCleanup(engine.lock_file.close)
        return engine

    def completed(self, engine, run_id):
        deadline = time.monotonic() + 5
        while engine.status()["running"] and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertFalse(engine.status()["running"])
        return engine.result(run_id)

    def test_request_is_fixed_sanitised_evidence_without_prior_answer(self):
        request = request_for(self.workspace)
        payload = json.loads(request["messages"][1]["content"])
        self.assertNotIn("previous_public_analysis", payload)
        logs = next(
            r
            for r in payload["observations"]
            if r["operation"] == "kubernetes_application_logs"
        )
        self.assertEqual(len(logs["data"]), 6)
        self.assertLessEqual(len(encoded(request)), 16384)

    def test_tampered_or_added_package_file_denies_before_provider(self):
        engine = self.engine()
        (self.workspace / "extra.mjs").write_text("// unexpected")
        with self.assertRaisesRegex(ProviderError, "freeze_inventory_changed"):
            engine.submit(engine.digest)
        self.assertEqual(self.posts, [])
        self.assertEqual(engine.status()["attempts"], 0)

    def test_default_replay_cannot_make_calls(self):
        engine = FreshAnalysis(self.workspace)
        with self.assertRaisesRegex(ProviderError, "live_mode_disabled"):
            engine.submit(engine.digest)

    def test_exact_public_response_retained_and_finding_separate(self):
        engine = self.engine()
        result = self.completed(engine, engine.submit(engine.digest))
        self.assertEqual(result["status"], "complete")
        self.assertEqual(
            result["raw_public_response"],
            self.response(engine.request)["choices"][0]["message"]["content"],
        )
        self.assertIn("Retained deterministic", result["independent_finding"])
        self.assertIn("NOT verified", result["validation"])
        self.assertEqual(result["request_sha256"], sha256(self.posts[0]).hexdigest())

    def test_duplicate_and_restart_do_not_reset_reservations(self):
        engine = self.engine()
        for _ in range(2):
            self.completed(engine, engine.submit(engine.digest))
        with self.assertRaisesRegex(ProviderError, "call_limit"):
            engine.submit(engine.digest)
        engine.lock_file.close()
        resumed = self.engine()
        self.assertEqual(resumed.status()["attempts"], 2)
        with self.assertRaises(ProviderError):
            resumed.submit(resumed.digest)
        self.assertEqual(len(self.posts), 2)

    def test_failed_transport_is_retained_without_retry_or_refund(self):
        def fail(wire, key):
            self.posts.append(wire)
            raise ProviderError("transport_failed")

        engine = self.engine(transport=fail)
        result = self.completed(engine, engine.submit(engine.digest))
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"], "transport_failed")
        self.assertEqual(len(self.posts), 1)
        self.assertEqual(engine.status()["attempts"], 1)

    def test_arbitrary_exception_text_never_leaves_trusted_boundary(self):
        def fail(wire, key):
            raise RuntimeError(key)

        engine = self.engine(transport=fail)
        result = self.completed(engine, engine.submit(engine.digest))
        self.assertEqual(result["error"], "analysis_failed")
        self.assertNotIn("test-only-not-a-real-key", json.dumps(result))

    def test_unknown_usage_holds_further_calls_and_preserves_public_text(self):
        def no_usage(wire, key):
            response = self.response(json.loads(wire))
            response.pop("usage")
            return response

        engine = self.engine(transport=no_usage)
        result = self.completed(engine, engine.submit(engine.digest))
        self.assertEqual(result["error"], "usage_missing_or_inconsistent")
        self.assertIn("Simulated analysis", result["raw_public_response"])
        self.assertTrue(engine.status()["hold"])
        with self.assertRaisesRegex(ProviderError, "accounting_hold"):
            engine.submit(engine.digest)

    def test_concurrent_click_cannot_admit_a_second_inflight_call(self):
        release = threading.Event()

        def slow(wire, key):
            release.wait(2)
            return self.response(json.loads(wire))

        engine = self.engine(transport=slow)
        run_id = engine.submit(engine.digest)
        with self.assertRaisesRegex(ProviderError, "busy"):
            engine.submit(engine.digest)
        release.set()
        self.completed(engine, run_id)
        self.assertEqual(engine.status()["attempts"], 1)

    def test_unknown_citations_are_visible_not_promoted(self):
        request = request_for(self.workspace)
        response = self.response(request)
        parsed = json.loads(response["choices"][0]["message"]["content"])
        parsed["hypotheses"][0]["evidence_ids"] = ["invented"]
        response["choices"][0]["message"]["content"] = json.dumps(parsed)
        result = public_response(response, request)
        self.assertEqual(result["unknown_citations"], ["invented"])
        response["choices"][0]["message"]["content"] = "not JSON; retain exactly"
        result = public_response(response, request)
        self.assertIsNone(result["interpretation"])
        self.assertEqual(result["raw_public_response"], "not JSON; retain exactly")

    def test_process_interruption_is_not_reported_as_success_or_retried(self):
        engine = self.engine()
        engine.rows = [
            {
                "id": "fresh-interrupted",
                "request_sha256": engine.digest,
                "reserved_usd": 0.03,
            }
        ]
        engine._persist("fresh-interrupted.json", {"status": "running"})
        self.assertEqual(engine.result("fresh-interrupted")["status"], "interrupted")
        self.assertEqual(self.posts, [])

    def test_installed_package_freeze_matches(self):
        digest = sha256((PACKAGE / "live-freeze.json").read_bytes()).hexdigest()
        verify_freeze(PACKAGE, digest)

    def test_http_rejects_cross_origin_arbitrary_prompt_and_wrong_digest(self):
        engine = self.engine()
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0), functools.partial(Handler, directory=str(self.workspace))
        )
        server.analysis = engine
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        port = server.server_port

        def request(origin, body, token=None):
            connection = HTTPConnection("127.0.0.1", port)
            connection.request(
                "POST",
                "/api/analysis",
                encoded(body),
                {
                    "Origin": origin,
                    "Content-Type": "application/json",
                    "X-Resolve-Token": token or engine.token,
                },
            )
            response = connection.getresponse()
            status, result = response.status, json.loads(response.read())
            connection.close()
            return status, result

        body = {"case": "http", "request_sha256": engine.digest}
        self.assertEqual(request("https://untrusted.example", body)[0], 403)
        self.assertEqual(
            request(f"http://127.0.0.1:{port}", {**body, "prompt": "run a shell"})[0],
            400,
        )
        self.assertEqual(
            request(f"http://127.0.0.1:{port}", {**body, "request_sha256": "bad"})[0],
            409,
        )
        self.assertEqual(self.posts, [])
        status, result = request(f"http://127.0.0.1:{port}", body)
        self.assertEqual(status, 202)
        self.assertEqual(self.completed(engine, result["id"])["status"], "complete")


if __name__ == "__main__":
    unittest.main()
