"""Synthetic judge demo; explicit offline, retained, or opt-in live inference modes."""

import argparse
import fcntl
import json
import os
import stat

# Fixed git/test argv only; never model-supplied shell commands.
import subprocess  # nosec B404
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from time import monotonic

from rootweaver_resolve.application import Application
from rootweaver_resolve.controller_led import ControllerLedInvestigator
from rootweaver_resolve.demo_contract import ULTRA, request_for, validate_public
from rootweaver_resolve.demo_transport import post
from rootweaver_resolve.evidence_view import safe_json
from rootweaver_resolve.executions import Journal
from rootweaver_resolve.family_provider import HostedFamilyProvider
from rootweaver_resolve.nebius import ProviderError, https_request
from rootweaver_resolve.server import make_server


class DemoInvestigator(ControllerLedInvestigator):
    def _analyze(self):
        refs = tuple(e.evidence_id for e in self.view().evidence)
        previous = next(
            (x["proposal"] for x in reversed(self.decisions) if x["proposal"]), None
        )
        item = {
            "analysis_kind": "reassessment-candidate" if previous else "analysis",
            "proposal": None,
            "disposition": "rejected",
            "controller_reason": "Public analysis is not a controller-supported finding",
            "evidence_ids": refs,
            "error_code": None,
        }
        self.decisions.append(item)
        self._last_analyzed = refs
        try:
            request = request_for(self, previous)
            reply = self.client.complete(request, self.journal, refs)
            checked, diagnostic = validate_public(reply["content"], request)
            if diagnostic["error_category"] == "evidence_policy":
                raise ProviderError("unsafe_public_response")
            item.update(
                request=request,
                validation=diagnostic,
                raw_public_response={
                    "content": reply["content"],
                    "sha256": sha256(reply["content"].encode()).hexdigest(),
                },
            )
            if checked is not None:
                item.update(
                    proposal=checked,
                    disposition="accepted",
                    controller_reason="Structure/references valid only; model factual accuracy remains unverified",
                )
        except (ProviderError, ValueError):
            item["error_code"] = "demo_analysis_unavailable_or_rejected"
        # Never assign model prose to core hypotheses, claims, findings or support.

    def public_record(self):
        result = super().public_record()
        result.update(
            model_id=ULTRA if self.client else "No model invoked",
            contract_version="synthetic-demo/v1",
            analysis_qualification="NOT_PRODUCTION_QUALIFIED",
        )
        result["limitations"] = [
            "Synthetic observations only; no Kubernetes connection.",
            "Ultra is not production-qualified; model assertions can be wrong and remain unverified.",
            "Controller-owned evidence and claim-specific findings; incident cause unresolved.",
            "No remediation executor; proposed action requires human approval.",
        ]
        if self.client:
            result["limitations"].insert(
                0,
                "Inference mode: "
                + self.client.execution_mode
                + "; retained outputs and simulated clients are not new inference.",
            )
        return result


class RetainedClient:
    execution_mode = "retained"

    def __init__(self, rows):
        self.rows = rows
        self.index = 0
        self.calls = []

    def complete(self, request, journal, refs):
        if self.index >= len(self.rows):
            raise ProviderError("retained_outputs_exhausted")
        row = self.rows[self.index]
        old = json.loads(row["request"]["messages"][1]["content"])
        new = json.loads(request["messages"][1]["content"])
        if old != new:
            raise ProviderError("retained_evidence_state_mismatch")
        self.index += 1
        self.calls.append({**row["diagnostics"], "retained_output": True})
        return {"content": row["public_response"]["content"]}


class DemoBudget:
    """Owner-local persistent two-request/$0.14 limit, not an account billing control."""

    def __init__(self, path):
        self.path = Path(path)

    @contextmanager
    def locked(self):
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "r+") as f:
            if (
                os.fstat(f.fileno()).st_uid != os.getuid()
                or os.fstat(f.fileno()).st_mode & 0o077
            ):
                raise ProviderError("demo_ledger_permissions")
            fcntl.flock(f, fcntl.LOCK_EX)
            raw = f.read(65537)
            state = (
                json.loads(raw)
                if raw
                else {
                    "attempts": 0,
                    "reserved_usd": 0.0,
                    "tokens": 0,
                    "pending": False,
                    "hold": False,
                }
            )
            yield state
            f.seek(0)
            f.write(safe_json(state) + "\n")
            f.truncate()
            f.flush()
            os.fsync(f.fileno())

    def prepare(self, wire):
        pass

    def reserve(self, size, *, output_tokens):
        if not 0 < size <= 16384 or output_tokens != 16384:
            raise ProviderError("demo_bound")
        with self.locked() as s:
            cost = ((size + 4096) + output_tokens * 3) / 1000000
            if (
                s["attempts"] >= 2
                or s["pending"]
                or s["hold"]
                or s["reserved_usd"] + cost > 0.14
            ):
                raise ProviderError("demo_budget_exhausted_or_hold")
            s.update(
                attempts=s["attempts"] + 1,
                reserved_usd=s["reserved_usd"] + cost,
                pending=True,
            )

    def settle(self, usage, latency_ms):
        with self.locked() as s:
            if not s["pending"]:
                raise ProviderError("demo_unreserved_usage")
            if (
                not isinstance(usage, dict)
                or any(
                    type(usage.get(k)) is not int or usage[k] < 0
                    for k in ["prompt_tokens", "completion_tokens", "total_tokens"]
                )
                or usage["total_tokens"]
                != usage["prompt_tokens"] + usage["completion_tokens"]
                or usage["prompt_tokens"] > 20480
                or usage["completion_tokens"] > 16384
            ):
                s["hold"] = True
            else:
                s["tokens"] += usage["total_tokens"]
            s["pending"] = False

    def snapshot(self):
        with self.locked() as s:
            return {**s, "max_attempts": 2, "max_reserved_usd": 0.14}


class DemoClient(HostedFamilyProvider):
    def __init__(self, key, budget, guard, *, transport=None, catalog_transport=None):
        self.model = ULTRA
        self.input_rate = 1.0
        self.output_rate = 3.0
        self.send = transport or post
        self.catalog_transport = catalog_transport or https_request
        super().__init__(key, budget, transport=self._send, thinking=False, retries=0)
        self.launch_guard = guard
        self.execution_mode = "simulated" if transport else "live"

    def _admit_request(self):
        if self.launch_guard is None:
            raise ProviderError("demo_signed_guard_required")
        self.launch_guard.assert_ready()

    def verify(self, journal):
        self.launch_guard.assert_ready()
        status, data = self.catalog_transport("GET", "/v1/models", None, self._key)
        if status != 200 or not any(r.get("id") == ULTRA for r in data.get("data", [])):
            raise ProviderError("demo_model_unavailable")
        self.launch_guard.assert_ready()
        status, public = self.catalog_transport(
            "GET", "/api/public/models_info", None, None, host="tokenfactory.nebius.com"
        )
        matches = [
            (row, f)
            for row in public
            for f in row.get("flavors", [])
            if f.get("model_id") == ULTRA
        ]
        if status != 200 or len(matches) != 1:
            raise ProviderError("demo_price_missing")
        row, f = matches[0]
        if (
            row.get("status") != "active"
            or f.get("external_provider") is not False
            or f.get("input_price_per_million_tokens") != 1.0
            or f.get("output_price_per_million_tokens") != 3.0
            or "text" not in f.get("use_cases", [])
        ):
            raise ProviderError("demo_price_or_destination_changed")
        self.verified = True
        return {
            "authenticated": True,
            "model_id": ULTRA,
            "input_usd_per_million": 1.0,
            "output_usd_per_million": 3.0,
            "billing_verified": False,
            "pricing_source": "https://tokenfactory.nebius.com/api/public/models_info",
        }

    def build_request(self, payload):
        if (
            payload.get("model") != ULTRA
            or payload.get("max_completion_tokens") != 16384
            or payload.get("n") != 1
            or payload.get("stream") is not False
            or "chat_template_kwargs" in payload
        ):
            raise ProviderError("demo_request_denied")
        self.budget.prepare(safe_json(payload).encode())
        return payload

    def _send(self, method, path, wire, key):
        if method != "POST" or path != "/v1/chat/completions":
            return self.send(method, path, wire, key)
        tick = monotonic()
        status = None
        data = None
        try:
            status, data = self.send(method, path, wire, key)
            return status, data
        finally:
            self.budget.settle(
                data.get("usage") if status == 200 and isinstance(data, dict) else None,
                (monotonic() - tick) * 1000,
            )


class DemoGuard:
    """Portable signed-clean-checkout manifest; no native Rootweaver dependencies."""

    def __init__(self, root, digest):
        self.root = Path(root).resolve()
        self.digest = digest
        self.head = None

    def command(self, args):
        # Fixed executable/arguments from application, not user/model shell text.
        p = subprocess.run(
            args,
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )  # nosec B603
        if p.returncode:
            raise ProviderError("demo_signature_or_check_failed")
        return p.stdout.strip()

    def integrity(self):
        if self.command(["git", "status", "--porcelain", "--untracked-files=all"]):
            raise ProviderError("demo_checkout_dirty")
        self.command(["git", "verify-commit", "HEAD"])
        head = self.command(["git", "rev-parse", "HEAD"])
        f = self.root / "demo-freeze.json"
        if sha256(f.read_bytes()).hexdigest() != self.digest:
            raise ProviderError("demo_manifest_digest")
        files = json.loads(f.read_text())["protected_files"]
        required = {
            str(p.relative_to(self.root))
            for p in (self.root / "src/rootweaver_resolve").rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        }
        if not required.issubset(files):
            raise ProviderError("demo_source_guards_missing")
        for name, digest in files.items():
            path = (self.root / name).resolve()
            if (
                not path.is_relative_to(self.root)
                or not path.is_file()
                or sha256(path.read_bytes()).hexdigest() != digest
            ):
                raise ProviderError("demo_manifest_changed")
            if name.startswith("src/rootweaver_resolve/"):
                installed = Path(__file__).resolve().parent / name.removeprefix(
                    "src/rootweaver_resolve/"
                )
                if (
                    not installed.is_file()
                    or sha256(installed.read_bytes()).hexdigest() != digest
                ):
                    raise ProviderError("demo_installed_source_mismatch")
        return head

    def prepare(self):
        import sys

        head = self.integrity()
        self.command([sys.executable, "-m", "unittest", "discover", "-s", "tests"])
        if self.integrity() != head:
            raise ProviderError("demo_head_changed")
        self.head = head

    def assert_ready(self):
        if self.head is None or self.integrity() != self.head:
            raise ProviderError("demo_guard_not_ready")


def read_credential(path):
    path = Path(path)
    info = path.parent.stat(follow_symlinks=False)
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        raise ProviderError("credential_directory_permissions")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd) as f:
        info = os.fstat(f.fileno())
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_mode & 0o077
            or info.st_size > 8192
        ):
            raise ProviderError("credential_file_permissions")
        lines = [
            x.strip()
            for x in f.read(8193).splitlines()
            if x.strip() and not x.lstrip().startswith("#")
        ]
    if len(lines) != 1 or not lines[0].startswith("NEBIUS_API_KEY="):
        raise ProviderError("credential_format")
    key = lines[0].split("=", 1)[1].strip()
    if len(key) >= 2 and key[0] == key[-1] and key[0] in "\"'":
        key = key[1:-1]
    if not key or any(c.isspace() or c in "'$`\"();" for c in key):
        raise ProviderError("credential_format")
    return key


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=["offline", "retained", "live"], default="offline"
    )
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--credential-file", type=Path)
    parser.add_argument("--runtime-dir", type=Path)
    parser.add_argument("--freeze-sha256")
    args = parser.parse_args()
    if args.mode == "live":
        if not args.credential_file or not args.runtime_dir or not args.freeze_sha256:
            parser.error(
                "Live demo needs private credential file, existing private runtime directory and signed manifest digest"
            )
        guard = DemoGuard(Path.cwd(), args.freeze_sha256)
        guard.prepare()
        budget = DemoBudget(args.runtime_dir / "demo-budget.json")
        client = DemoClient(read_credential(args.credential_file), budget, guard)
        client.verify(Journal("live-demo-preflight"))
        factory = lambda s: DemoInvestigator(s, client)
    elif args.mode == "retained":
        root = Path(__file__).with_name("demo_recordings")
        rows = json.loads((root / "recorded.json").read_text())
        factory = lambda s: (
            DemoInvestigator(s, RetainedClient(rows))
            if s == "recorded"
            else ControllerLedInvestigator(s)
        )
    else:
        factory = lambda s: ControllerLedInvestigator(s)
    with make_server(
        args.port, application=Application(investigator_factory=factory)
    ) as server:
        print(
            "Resolve "
            + args.mode
            + " synthetic demo on http://127.0.0.1:"
            + str(args.port),
            flush=True,
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
