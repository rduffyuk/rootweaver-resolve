"""Fixed-origin Token Factory transport with bounded spend and public-only response projection."""

import fcntl
import http.client
import json
import os
import ssl
from hashlib import sha256
from pathlib import Path
from time import monotonic

from rootweaver_resolve.evidence_view import PolicyDenied, safe_json

MODEL = "nvidia/Nemotron-3_5-Lightning"
HOST = "api.tokenfactory.nebius.com"
INPUT_RATE = 0.06
OUTPUT_RATE = 0.24
MAX_OUTPUT = 1024
# Read historical reservations approved by VW-2313. General spending stays capped at $0.05.
LEDGER_HISTORY_LIMIT = 0.05087274


class ProviderError(RuntimeError):
    pass


class Budget:
    """Reservation is never refunded for failed/unknown charges. Not an account billing limit."""

    def __init__(self, *, path=None, max_calls=24, max_usd=0.05):
        if (
            type(max_calls) is not int
            or not 1 <= max_calls <= 64
            or not 0 < max_usd <= 0.05
        ):
            raise ValueError("budget exceeds approved qualification cap")
        self.path = Path(path) if path else None
        self.max_calls = max_calls
        self.max_usd = max_usd
        self.state = {"attempts": 0, "reserved_usd": 0.0}

    def _reserve(self, state, size, output_tokens):
        cost = ((size + 4096) * INPUT_RATE + output_tokens * OUTPUT_RATE) / 1_000_000
        if (
            state["attempts"] >= self.max_calls
            or state["reserved_usd"] + cost > self.max_usd
        ):
            raise ProviderError("inference_budget_exhausted")
        state = {
            "attempts": state["attempts"] + 1,
            "reserved_usd": round(state["reserved_usd"] + cost, 10),
        }
        self.state = state
        return state

    def reserve(self, size, *, output_tokens=MAX_OUTPUT):
        if (
            type(size) is not int
            or not 0 < size <= 16384
            or output_tokens not in (1024, 2048, 4096)
        ):
            raise ProviderError("request_size_exceeded")
        if self.path is None:
            return self._reserve(self.state, size, output_tokens)
        descriptor = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "r+") as handle:
            if (
                os.fstat(handle.fileno()).st_uid != os.getuid()
                or os.fstat(handle.fileno()).st_mode & 0o077
            ):
                raise ProviderError("budget_file_permissions")
            fcntl.flock(handle, fcntl.LOCK_EX)
            raw = handle.read(4097)
            try:
                state = json.loads(raw) if raw else {"attempts": 0, "reserved_usd": 0.0}
                if (
                    set(state) != {"attempts", "reserved_usd"}
                    or type(state["attempts"]) is not int
                    or not 0 <= state["attempts"] <= 64
                    or not 0 <= state["reserved_usd"] <= LEDGER_HISTORY_LIMIT
                ):
                    raise ValueError("invalid budget")
                state = self._reserve(state, size, output_tokens)
            except (ValueError, TypeError, KeyError):
                raise ProviderError("budget_file_invalid") from None
            handle.seek(0)
            handle.write(json.dumps(state, allow_nan=False))
            handle.truncate()
            handle.flush()
            os.fsync(handle.fileno())
            return state

    def snapshot(self):
        if self.path and self.path.exists():
            descriptor = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(descriptor) as handle:
                if (
                    os.fstat(handle.fileno()).st_uid != os.getuid()
                    or os.fstat(handle.fileno()).st_mode & 0o077
                ):
                    raise ProviderError("budget_file_permissions")
                fcntl.flock(handle, fcntl.LOCK_SH)
                try:
                    state = json.loads(handle.read(4097))
                    if (
                        set(state) != {"attempts", "reserved_usd"}
                        or type(state["attempts"]) is not int
                        or not 0 <= state["attempts"] <= 64
                        or not 0 <= state["reserved_usd"] <= LEDGER_HISTORY_LIMIT
                    ):
                        raise ValueError("invalid budget")
                    self.state = state
                except (ValueError, TypeError, KeyError):
                    raise ProviderError("budget_file_invalid") from None
        return {
            **self.state,
            "max_attempts": self.max_calls,
            "max_reserved_usd": self.max_usd,
            "programme_credit_budget_usd": 60,
            "billing": "list-rate estimate; account-wide billing and remaining credit unverified",
        }


def https_request(method, path, body, key, *, host=HOST):
    if host not in {HOST, "tokenfactory.nebius.com"} or path not in {
        "/v1/models",
        "/v1/chat/completions",
        "/api/public/models_info",
    }:
        raise ProviderError("endpoint_denied")
    if host != HOST and key:
        raise ProviderError("credential_destination_denied")
    connection = http.client.HTTPSConnection(
        host, timeout=30, context=ssl.create_default_context()
    )
    deadline = monotonic() + 30
    try:
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = "Bearer " + key
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        chunks = []
        size = 0
        while True:
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise TimeoutError
            if connection.sock:
                connection.sock.settimeout(remaining)
            chunk = response.read1(8192)
            if not chunk:
                break
            size += len(chunk)
            if size > 1_048_576:
                raise ProviderError("response_size_exceeded")
            chunks.append(chunk)
        # Never propagate HTTP error bodies or arbitrary exception strings.
        if response.status != 200:
            return response.status, {}
        text = b"".join(chunks).decode("utf-8")
        if key and key in text:
            raise ProviderError("credential_echo_blocked")
        return response.status, json.loads(text)
    except ProviderError:
        raise
    except ssl.SSLCertVerificationError:
        raise ProviderError("tls_verification_failed") from None
    except (TimeoutError, OSError, ValueError, http.client.HTTPException):
        raise ProviderError("transport_failed") from None
    finally:
        connection.close()


class NebiusClient:
    def __init__(
        self,
        key,
        budget,
        *,
        transport=None,
        thinking=False,
        assessment_output=2048,
        retries=1,
    ):
        if type(retries) is not int or retries not in (0, 1):
            raise ValueError("retry_limit_invalid")
        self.retries = retries
        if type(assessment_output) is not int or assessment_output not in (2048, 4096):
            raise ValueError("assessment_output_invalid")
        self.assessment_output = assessment_output
        if type(thinking) is not bool and thinking != "assess":
            raise ValueError("thinking_mode_invalid")
        self.thinking = thinking
        if (
            not isinstance(key, str)
            or not key
            or any(c.isspace() for c in key)
            or key.startswith(("'", '"'))
            or key.endswith(("'", '"'))
        ):
            raise ProviderError("credential_unavailable")
        self._key = key
        self.budget = budget
        self._transport = transport or https_request
        self.execution_mode = "simulated" if transport is not None else "live"
        self.verified = False
        self.calls = []
        self.access = None

    def verify(self, journal):
        started = journal.begin(
            "GET https://api.tokenfactory.nebius.com/v1/models",
            {},
            initiator="controller",
            mode=self.execution_mode,
            actor="resolve-application",
            target=HOST,
            scope="authenticated-model-discovery",
        )
        try:
            status, data = self._transport("GET", "/v1/models", None, self._key)
            if status != 200:
                raise ProviderError(f"http_{status}")
            if not any(row.get("id") == MODEL for row in data.get("data", [])):
                raise ProviderError("required_model_unavailable")
            if self._transport is https_request:
                status, catalog = https_request(
                    "GET",
                    "/api/public/models_info",
                    None,
                    None,
                    host="tokenfactory.nebius.com",
                )
                matches = [
                    flavor
                    for row in catalog
                    for flavor in row.get("flavors", [])
                    if flavor.get("model_id") == MODEL
                ]
                if (
                    status != 200
                    or len(matches) != 1
                    or matches[0].get("input_price_per_million_tokens") != INPUT_RATE
                    or matches[0].get("output_price_per_million_tokens") != OUTPUT_RATE
                    or matches[0].get("external_provider") is not False
                ):
                    raise ProviderError("pricing_or_destination_changed")
            self.verified = True
            self.access = {
                "authenticated_model_list": True,
                "model_id": MODEL,
                "input_usd_per_million": INPUT_RATE,
                "output_usd_per_million": OUTPUT_RATE,
                "pricing_source": "https://tokenfactory.nebius.com/api/public/models_info",
                "billing_verified": False,
            }
            journal.finish(started, status="ok", output_refs=("model:" + MODEL,))
            return self.access
        except (ProviderError, TypeError, KeyError, AttributeError) as error:
            code = (
                str(error)
                if isinstance(error, ProviderError)
                else "model_discovery_failed"
            )
            if code not in {
                "http_400",
                "http_401",
                "http_403",
                "http_404",
                "http_429",
                "http_500",
                "http_502",
                "http_503",
                "transport_failed",
                "tls_verification_failed",
                "required_model_unavailable",
                "pricing_or_destination_changed",
                "credential_echo_blocked",
            }:
                code = "model_discovery_failed"
            journal.finish(started, status="error", error_code=code)
            raise ProviderError(code) from None

    def complete(self, payload, journal, evidence_refs):
        if not self.verified:
            raise ProviderError("model_not_verified")
        thinking = self.thinking is True or (
            self.thinking == "assess" and payload.get("investigation_phase") == "assess"
        )
        output_tokens = self.assessment_output if thinking else MAX_OUTPUT
        request = {
            **{k: v for k, v in payload.items() if k != "investigation_phase"},
            "model": MODEL,
            "max_tokens": output_tokens,
            "temperature": 0,
            "stream": False,
            "response_format": payload.get("response_format", {"type": "json_object"}),
            "chat_template_kwargs": {"enable_thinking": thinking},
        }
        try:
            encoded = safe_json(request).encode()
        except PolicyDenied:
            raise ProviderError("outgoing_policy_denied") from None
        if len(encoded) > 16384:
            raise ProviderError("request_size_exceeded")
        for attempt in range(self.retries + 1):
            self.budget.reserve(len(encoded), output_tokens=output_tokens)
            start = journal.begin(
                "POST https://api.tokenfactory.nebius.com/v1/chat/completions",
                request,
                initiator="controller",
                mode=self.execution_mode,
                actor="resolve-application",
                target=MODEL,
                scope="hosted-synthetic-inference",
                input_refs=evidence_refs,
            )
            tick = monotonic()
            call = {
                "attempt": self.budget.snapshot()["attempts"],
                "status": "error",
                "error_code": None,
                "request_sha256": sha256(encoded).hexdigest(),
                "request_bytes": len(encoded),
                "usage": None,
                "estimated_usd": None,
                "latency_ms": None,
                "thinking_enabled": thinking,
                "thinking_requested": thinking,
                "thinking_control_support": "unverified",
                "output_token_limit": output_tokens,
                "finish_reason": None,
                "completion_tokens": None,
                "output_tokens": None,
                "reasoning_tokens": None,
                "final_content_present": False,
                "final_content_bytes": None,
                "final_content_complete": False,
                "refusal_present": False,
                "response_model_matches": None,
                "proposal_parse_status": "not_attempted",
                "proposal_validation_status": "not_attempted",
                "controller_validation_status": "not_applied",
            }
            call["terminated_by_token_limit"] = None
            try:
                status, response = self._transport(
                    "POST", "/v1/chat/completions", encoded, self._key
                )
                if status != 200:
                    raise ProviderError(f"http_{status}")
                if self._key in json.dumps(response):
                    raise ProviderError("credential_echo_blocked")
                usage = response.get("usage")
                if isinstance(usage, dict) and all(
                    type(usage.get(k)) is int and usage[k] >= 0
                    for k in ("prompt_tokens", "completion_tokens", "total_tokens")
                ):
                    call["usage"] = {
                        k: usage[k]
                        for k in ("prompt_tokens", "completion_tokens", "total_tokens")
                    }
                    call["estimated_usd"] = (
                        usage["prompt_tokens"] * INPUT_RATE
                        + usage["completion_tokens"] * OUTPUT_RATE
                    ) / 1_000_000
                if isinstance(usage, dict):
                    completion = usage.get("completion_tokens")
                    # Output aliases the exposed completion count, never another charge.
                    if type(completion) is int and completion >= 0:
                        call["completion_tokens"] = call["output_tokens"] = completion
                    details = usage.get("completion_tokens_details")
                    reasoning = (
                        details.get("reasoning_tokens")
                        if isinstance(details, dict)
                        else None
                    )
                    if (
                        type(reasoning) is int
                        and reasoning >= 0
                        and (
                            call["completion_tokens"] is None
                            or reasoning <= call["completion_tokens"]
                        )
                    ):
                        call["reasoning_tokens"] = reasoning
                call["response_model_matches"] = response.get("model") == MODEL
                if response.get("model") != MODEL:
                    raise ProviderError("response_model_mismatch")
                choice = response["choices"][0]
                finish = choice.get("finish_reason")
                call["finish_reason"] = (
                    finish
                    if isinstance(finish, str)
                    and finish
                    in {
                        "stop",
                        "length",
                        "content_filter",
                        "tool_calls",
                        "function_call",
                    }
                    else "other"
                )
                call["terminated_by_token_limit"] = (
                    (finish == "length") if call["finish_reason"] != "other" else None
                )
                message = choice.get("message")
                if not isinstance(message, dict):
                    raise ProviderError("public_response_invalid")
                content = message.get("content")
                call["final_content_present"] = isinstance(content, str) and bool(
                    content
                )
                call["final_content_bytes"] = (
                    len(content.encode()) if isinstance(content, str) else None
                )
                call["refusal_present"] = bool(message.get("refusal"))
                if finish != "stop":
                    raise ProviderError("output_not_complete")
                if call["refusal_present"]:
                    raise ProviderError("provider_refused")
                if not isinstance(content, str) or len(content.encode()) > 8192:
                    raise ProviderError("public_response_invalid")
                try:
                    call["final_content_complete"] = isinstance(
                        json.loads(content), dict
                    )
                except ValueError:
                    pass
                # Never retain reasoning_content, HTTP headers or the full transport response.
                call.update(
                    status="ok",
                    response_model=response["model"],
                    response_id=str(response.get("id", "UNKNOWN"))[:200],
                )
                reply = {
                    "content": content,
                    "model": MODEL,
                    "usage": call["usage"],
                    "response_id": call["response_id"],
                }
                journal.finish(
                    start,
                    status="ok",
                    output_refs=(
                        "public-response-sha256:"
                        + sha256(content.encode()).hexdigest(),
                    ),
                )
                return reply
            except (
                ProviderError,
                TypeError,
                ValueError,
                KeyError,
                IndexError,
                AttributeError,
            ) as error:
                code = (
                    str(error)
                    if isinstance(error, ProviderError)
                    else "response_schema_invalid"
                )
                if code not in {
                    "http_401",
                    "http_403",
                    "http_400",
                    "http_429",
                    "http_500",
                    "http_502",
                    "http_503",
                    "http_504",
                    "transport_failed",
                    "response_model_mismatch",
                    "output_not_complete",
                    "public_response_invalid",
                    "provider_refused",
                    "credential_echo_blocked",
                    "response_size_exceeded",
                }:
                    code = "provider_failed"
                call["error_code"] = code
                journal.finish(start, status="error", error_code=code)
                if attempt == self.retries or code not in {
                    "http_429",
                    "http_500",
                    "http_502",
                    "http_503",
                    "http_504",
                    "transport_failed",
                }:
                    raise ProviderError(code) from None
            finally:
                call["latency_ms"] = round((monotonic() - tick) * 1000, 3)
                self.calls.append(call)
        raise ProviderError("provider_failed")

    def record_proposal_status(self, *, parse=None, validation=None, controller=None):
        """Append only fixed status labels; never model content or exception strings."""
        allowed = {
            "proposal_parse_status": {"valid_json", "invalid_json"},
            "proposal_validation_status": {"accepted", "rejected"},
            "controller_validation_status": {"accepted", "rejected"},
        }
        if not self.calls:
            return
        for field, value in (
            ("proposal_parse_status", parse),
            ("proposal_validation_status", validation),
            ("controller_validation_status", controller),
        ):
            if value is not None:
                if value not in allowed[field]:
                    raise ValueError("invalid diagnostic status")
                self.calls[-1][field] = value
