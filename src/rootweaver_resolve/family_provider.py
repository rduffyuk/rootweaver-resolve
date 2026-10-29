"""Frozen-comparison-only projection, copied from the existing bounded provider.

The consumed qualification hashes the original provider. Keep that source intact;
this isolated subclass preserves its transport, diagnostics and secret boundaries.
Only frozen family adapters supply their approved exact model/rate profiles.
"""

import json
from hashlib import sha256
from time import monotonic

from rootweaver_resolve.evidence_view import PolicyDenied, safe_json
from rootweaver_resolve.nebius import (
    HOST,
    MAX_OUTPUT,
    NebiusClient,
    ProviderError,
    https_request,
)


class HostedFamilyProvider(NebiusClient):
    launch_guard = None

    def _admit_request(self):

        if self.launch_guard is not None:
            self.launch_guard.assert_ready()
        elif self._transport is https_request:
            raise ProviderError("live_provider_requires_committed_preflight")

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
            self._admit_request()
            status, data = self._transport("GET", "/v1/models", None, self._key)
            if status != 200:
                raise ProviderError(f"http_{status}")
            if not any(row.get("id") == self.model for row in data.get("data", [])):
                raise ProviderError("required_model_unavailable")
            if self._transport is https_request:
                self._admit_request()
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
                    if flavor.get("model_id") == self.model
                ]
                if (
                    status != 200
                    or len(matches) != 1
                    or matches[0].get("input_price_per_million_tokens")
                    != self.input_rate
                    or matches[0].get("output_price_per_million_tokens")
                    != self.output_rate
                    or matches[0].get("external_provider") is not False
                ):
                    raise ProviderError("pricing_or_destination_changed")
            self.verified = True
            self.access = {
                "authenticated_model_list": True,
                "model_id": self.model,
                "input_usd_per_million": self.input_rate,
                "output_usd_per_million": self.output_rate,
                "pricing_source": "https://tokenfactory.nebius.com/api/public/models_info",
                "billing_verified": False,
            }
            journal.finish(started, status="ok", output_refs=("model:" + self.model,))
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

    def build_request(self, payload):
        thinking = self.thinking is True or (
            self.thinking == "assess" and payload.get("investigation_phase") == "assess"
        )
        output_tokens = self.assessment_output if thinking else MAX_OUTPUT
        return {
            **{k: v for k, v in payload.items() if k != "investigation_phase"},
            "model": self.model,
            "max_tokens": output_tokens,
            "temperature": 0,
            "stream": False,
            "response_format": payload.get("response_format", {"type": "json_object"}),
            "chat_template_kwargs": {"enable_thinking": thinking},
        }

    def complete(self, payload, journal, evidence_refs):
        if not self.verified:
            raise ProviderError("model_not_verified")
        request = self.build_request(payload)
        output_tokens = request.get("max_completion_tokens", request.get("max_tokens"))
        thinking = request.get("chat_template_kwargs", {}).get("enable_thinking")
        try:
            encoded = safe_json(request).encode()
        except PolicyDenied:
            raise ProviderError("outgoing_policy_denied") from None
        if len(encoded) > 16384:
            raise ProviderError("request_size_exceeded")
        for attempt in range(self.retries + 1):
            self._admit_request()
            self.budget.reserve(len(encoded), output_tokens=output_tokens)
            start = journal.begin(
                "POST https://api.tokenfactory.nebius.com/v1/chat/completions",
                request,
                initiator="controller",
                mode=self.execution_mode,
                actor="resolve-application",
                target=self.model,
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
                        usage["prompt_tokens"] * self.input_rate
                        + usage["completion_tokens"] * self.output_rate
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
                call["response_model_matches"] = response.get("model") == self.model
                if response.get("model") != self.model:
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
                call["final_response_sha256"] = (
                    sha256(content.encode()).hexdigest()
                    if isinstance(content, str)
                    else None
                )
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
                    "model": self.model,
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
