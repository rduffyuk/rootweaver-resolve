"""Decode the retained PCAP locally. No network access or new capture."""
import hashlib
import json
import shutil
import subprocess
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

CAPTURE = Path(__file__).resolve().parents[1] / "research/packet-lab/capture.pcapng"
EXPECTED = "68ce2051eb01e41f5243e2dcb3d392ff61bc04d475f6a7121c4b48853633dfda"


def main():
    if hashlib.sha256(CAPTURE.read_bytes()).hexdigest() != EXPECTED:
        raise SystemExit("This script is scoped to the retained lab capture; its digest differs.")
    executable = shutil.which("tshark")
    if not executable:
        raise SystemExit("Install Wireshark/TShark to inspect the original PCAP offline.")
    fields = ["frame.number", "frame.time_epoch", "tcp.stream", "ip.src", "tcp.len", "tcp.flags.syn", "tcp.flags.fin"]
    command = [executable, "-n", "-r", str(CAPTURE), "-Y", "tcp", "-T", "fields"]
    for field in fields:
        command.extend(["-e", field])
    result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
    streams = defaultdict(list)
    for line in result.stdout.splitlines():
        number, epoch, stream, address, length, syn, fin = line.split("\t")
        streams[int(stream)].append({"frame": int(number), "at": Decimal(epoch), "src": address,
                                     "length": int(length), "syn": syn.lower() in {"1", "true"},
                                     "fin": fin.lower() in {"1", "true"}})
    rows = []
    for stream, frames in sorted(streams.items()):
        client = [f for f in frames if f["src"] == "10.42.0.178"]
        request = next((f for f in client if f["length"] > 0), None)
        response = next((f for f in frames if f["src"] == "10.42.0.180" and f["length"] > 0), None)
        fin = next((f for f in client if f["fin"]), None)
        syn = next((f for f in client if f["syn"]), None)
        row = {"stream": stream, "frames": len(frames), "complete_pair": bool(syn and request and response and fin)}
        if request:
            row["request_frame"] = request["frame"]
            if fin:
                row["client_fin_ms"] = round(float((fin["at"] - request["at"]) * 1000), 3)
            if response:
                row["first_server_data_ms"] = round(float((response["at"] - request["at"]) * 1000), 3)
        row["limitation"] = None if row["complete_pair"] else (
            "Capture begins after request/handshake" if not request else "No server data before capture ends")
        rows.append(row)
    report = {"frames": sum(len(v) for v in streams.values()), "streams": rows,
              "complete_pairs": sum(r["complete_pair"] for r in rows),
              "interpretation": "Timing and reachability only; no cause of server delay or correct timeout established."}
    assert report["frames"] == 45 and report["complete_pairs"] == 4, report
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
