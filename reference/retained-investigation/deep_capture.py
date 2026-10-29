"""Fixed packet-capture contract for the owner-approved disposable experiment.

This is not a general privileged tool API. The model receives only a check ID.
"""

import ipaddress
import re
import uuid

RESOURCE_PROPERTIES = [
    "--property=CPUQuota=20%",
    "--property=MemoryMax=64M",
    "--property=TasksMax=16",
    "--property=UMask=0077",
    "--property=TimeoutStopSec=2s",
]
FIELDS = {
    "frame": "frame.number",
    "stream": "tcp.stream",
    "time": "frame.time_epoch",
    "src": "ip.src",
    "dst": "ip.dst",
    "sport": "tcp.srcport",
    "dport": "tcp.dstport",
    "syn": "tcp.flags.syn",
    "ack": "tcp.flags.ack",
    "length": "tcp.len",
    "reset": "tcp.flags.reset",
    "retrans": "tcp.analysis.retransmission",
    "fin": "tcp.flags.fin",
}


def capture_request(scope, run_id, incident_id):
    uuid.UUID(scope["pod_uid"])
    if not re.fullmatch(r"[a-f0-9]{64}", scope["container_id"]):
        raise ValueError("container_identity_required")
    if (
        not re.fullmatch(r"veth[A-Za-z0-9]{1,11}", scope["interface"])
        or scope["ifindex"] < 1
    ):
        raise ValueError("pinned_workload_veth_required")
    addresses = [ipaddress.IPv4Address(scope[k]) for k in ["client_ip", "peer_ip"]]
    if addresses[0] == addresses[1] or any(
        a.is_unspecified or a.is_multicast for a in addresses
    ):
        raise ValueError("distinct_unicast_workload_ips_required")
    if scope["port"] != 8081:
        raise ValueError("approved_dependency_port_required")
    capture_filter = (
        f"tcp and host {addresses[0]} and host {addresses[1]} and port 8081"
    )
    return dict(
        operation="run",
        run_id=run_id,
        incident_id=incident_id,
        program="dumpcap",
        argv=[
            "-i",
            scope["interface"],
            "-p",
            "-s",
            "0",
            "-B",
            "1",
            "-c",
            "128",
            "-a",
            "duration:10",
            "-a",
            "filesize:512",
            "-f",
            capture_filter,
            "-w",
            "{run_dir}/capture.pcapng",
        ],
        duration_seconds=10,
        mode="DEEP",
        max_output_bytes=16384,
        max_artifact_bytes=1048576,
        min_free_bytes=10737418240,
        privileged=True,
    )


def validate_capture_request(request, scope):
    if request != capture_request(scope, request["run_id"], request["incident_id"]):
        raise ValueError("capture_request_differs_from_fixed_approval")


def verify_scope(expected, observed):
    if expected != observed:
        raise ValueError("capture_target_identity_changed")


def require_stopped(statuses):
    if any(row.get("status") not in {"stopped", "expired"} for row in statuses):
        raise ValueError("capture_admission_hold_unverified_cleanup")


def project_packets(rows, scope):
    """Describe all captured TCP frames; never infer execution from TCP ACKs."""
    if not rows or len(rows) > 128:
        raise ValueError("empty_or_over_budget_capture")
    streams = {}

    def flag(value):
        return str(value).lower() in {"1", "true"}

    for row in rows:
        outgoing = row["src"] == scope["client_ip"]
        if {row["src"], row["dst"]} != {scope["client_ip"], scope["peer_ip"]} or row[
            "dport" if outgoing else "sport"
        ] != str(scope["port"]):
            raise ValueError("packet_outside_approved_scope")
        item = streams.setdefault(
            row["stream"],
            dict(
                stream=row["stream"],
                first_at=row["time"],
                last_at=row["time"],
                syn_frames=[],
                syn_ack_frames=[],
                client_payload_frames=[],
                server_payload_frames=[],
                reset_frames=[],
                retransmission_frames=[],
                client_payload_bytes=0,
                server_payload_bytes=0,
                client_fin_frames=[],
            ),
        )
        item["last_at"] = row["time"]
        if flag(row["syn"]):
            item["syn_ack_frames" if flag(row["ack"]) else "syn_frames"].append(
                row["frame"]
            )
        if int(row["length"]) > 0:
            side = "client" if outgoing else "server"
            item[side + "_payload_frames"].append(row["frame"])
            item[side + "_payload_bytes"] += int(row["length"])
        if flag(row["reset"]):
            item["reset_frames"].append(row["frame"])
        if row["retrans"]:
            item["retransmission_frames"].append(row["frame"])
        if outgoing and flag(row["fin"]):
            item["client_fin_frames"].append(row["frame"])
    if len(streams) > 12:
        raise ValueError("stream_projection_budget_exceeded")
    times = {r["frame"]: float(r["time"]) for r in rows}
    for item in streams.values():
        client = item["client_payload_frames"]
        server = item["server_payload_frames"]
        if client and server:
            item["first_server_payload_after_client_ms"] = round(
                (times[server[0]] - times[client[0]]) * 1000, 3
            )
        if client and item["client_fin_frames"]:
            item["client_fin_after_payload_ms"] = round(
                (times[item["client_fin_frames"][0]] - times[client[0]]) * 1000, 3
            )
    return dict(
        captured_frames=len(rows),
        streams=list(streams.values()),
        limitations="One client-side interface, at most 10 seconds / 128 packets / 512 KiB capture stop; a 1 MiB hard file ceiling. TCP acknowledgement is transport evidence, not proof that the application executed a request. No server process, scheduler, database or lock evidence. Missing packets, encryption, capture boundaries and TCP reassembly can limit inference. Raw PCAP and all decoded frames remain private and available; no payload is sent to the model.",
    )
