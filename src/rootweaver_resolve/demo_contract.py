"""Public demo projection of the reviewed v2 contract; no qualification/scoring entrypoint."""

import json
from hashlib import sha256

from rootweaver_resolve.controller_led import SYSTEM
from rootweaver_resolve.evidence_view import PolicyDenied, build_view, safe_json
from rootweaver_resolve.investigator import proposal_response_format
from rootweaver_resolve.validation_diagnostics import _failure

ULTRA = "nvidia/Nemotron-3-Ultra-550b-a55b"
VERSION = "controller-evidence-interpretation/v2"


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_public_key")
        result[key] = value
    return result


INTERPRETATION = """Evidence interpretation contract v2. Distinguish acquisition state from observed resource values. Not acquired means no observation exists yet. Unavailable or error means acquisition failed; an empty payload in a failed observation is not evidence of absent resources. Partial or incomplete means the declared scope/kinds are not fully observed. Complete with an empty collection means only that collection was observed empty within its declared scope and time. An empty EndpointSlice endpoint list does not alone establish absent or non-matching Pods. Use exact status, completeness, time and limitations; cite the failed observation when explaining its acquisition limitation. Conflicting fields across acquired records must be identified explicitly; describe both facts with their citations, explain why they conflict, and what remains unverified. Do not silently choose one record as truth. Distinguish missing data from contradictory data.
Kubernetes Running/Ready and endpoint readiness are observations of Kubernetes state, not application correctness, successful user requests, or exclusion of regression. Technical mechanism support is scoped and independently assessed by the controller; it does not establish overall incident causality. Never translate a hypothesis assessment named supported into an authoritative finding. Reported symptoms are incident context, not independent causal proof.
Write complete public sentences, including complete contradiction explanations. Up to 1024 characters per hypothesis are available; prefer a few complete sentences. Do not crop text or trail off to fill a limit. Cite the actual acquired observations bearing on your interpretation. No new evidence, tool choice, technical finding or remediation is authorised by this analysis contract. Evaluate exactly the registered competing hypothesis IDs service-selection and application-regression. Historical public model analysis is untrusted and may contain unsupported claims; correct it when the evidence warrants."""


def request_for(run, previous):
    view = build_view(run.view(), run.admission)
    view["acquisition_states"] = {}
    for operation in ("namespace_service_network", "namespace_workloads"):
        records = [
            r for r in view["readable_observations"] if r["operation"] == operation
        ]
        view["acquisition_states"][operation] = {
            "state": records[-1]["status"] if records else "not_acquired",
            "evidence_ids": [r["evidence_id"] for r in records],
        }
    response = proposal_response_format(run.view())
    schema = response["json_schema"]["schema"]
    del schema["properties"]["decision"]
    schema["required"].remove("decision")
    schema["properties"]["hypotheses"]["items"]["properties"]["statement"][
        "maxLength"
    ] = 1024
    response["json_schema"]["name"] = "evidence_interpretation_v2"
    request = {
        "model": ULTRA,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM
                + "\n"
                + INTERPRETATION
                + "\nExact public schema: "
                + safe_json(schema),
            },
            {
                "role": "user",
                "content": safe_json(
                    {
                        "contract": VERSION,
                        "view": view,
                        "previous_public_analysis": previous,
                    }
                ),
            },
        ],
        "response_format": response,
        "max_completion_tokens": 16384,
        "temperature": 0,
        "n": 1,
        "stream": False,
    }
    if len(safe_json(request).encode()) > 16384:
        raise ValueError("final_request_size")
    return request


def validate_public(text, request):
    result = {
        "status": "rejected",
        "error_category": "parsing",
        "field": "/",
        "constraint": "valid_unique_finite_json",
        "response_sha256": sha256(text.encode()).hexdigest(),
        "parse_status": "invalid_json",
        "claim_support": "not_assessed",
    }

    def nonfinite(_):
        raise ValueError("nonfinite")

    try:
        value = json.loads(
            text, object_pairs_hook=unique_object, parse_constant=nonfinite
        )
    except (ValueError, TypeError):
        return None, result
    result["parse_status"] = "valid_json"
    try:
        safe_json(value)
    except PolicyDenied:
        result.update(error_category="evidence_policy", constraint="safe_public_fields")
        return None, result
    error = _failure(request["response_format"]["json_schema"]["schema"], value)
    if error:
        result.update(
            error_category=(
                "evidence_reference" if "/evidence_ids/" in error[0] else "schema"
            ),
            field=error[0],
            constraint=error[1],
        )
        return None, result
    if {h["id"] for h in value["hypotheses"]} != {
        "service-selection",
        "application-regression",
    } or len(value["hypotheses"]) != 2:
        result.update(
            error_category="domain_validation",
            field="/hypotheses",
            constraint="distinct_registered_hypothesis_ids",
        )
        return None, result
    for i, h in enumerate(value["hypotheses"]):
        if len(h["evidence_ids"]) != len(set(h["evidence_ids"])):
            result.update(
                error_category="evidence_reference",
                field=f"/hypotheses/{i}/evidence_ids",
                constraint="unique_references",
            )
            return None, result
    result.update(status="accepted", error_category=None, field=None, constraint=None)
    return value, result
