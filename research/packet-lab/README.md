# Inspect the original packet investigation

`capture.pcapng` is the original 6,116-byte capture, SHA256
`68ce2051eb01e41f5243e2dcb3d392ff61bc04d475f6a7121c4b48853633dfda`.
It contains 45 frames between the disposable client `10.42.0.178` and dependency
`10.42.0.180`, TCP port 8081. Their lab names and HTTP test payloads are preserved.
The source capture filter and platform metadata are also intact.

With Wireshark/TShark installed, from the repository root:

```sh
tshark -r research/packet-lab/capture.pcapng -q -z conv,tcp
tshark -r research/packet-lab/capture.pcapng -Y tcp -T fields \
  -E header=y -E separator=, \
  -e frame.number -e frame.time_epoch -e tcp.stream \
  -e ip.src -e tcp.srcport -e ip.dst -e tcp.dstport \
  -e tcp.flags -e tcp.len -e tcp.seq -e tcp.ack
python scripts/inspect_packet_timing.py
```

These are offline reads. No root privileges, cluster access, capture process or
inference call is needed. `inspect_packet_timing.py` requires the local `tshark`
executable and derives the four complete pairs from packet fields. It reports
the incomplete streams separately. The retained application decoder is also
available in [the source reference](../../reference/retained-investigation/deep_capture.py).

`methods.json` contains the human command equivalents and acquisition times for
all four executed checks. Running a `kubectl` command later would produce a new
observation and requires an authorized target; it would not reproduce old bytes.
`model-N-request.json` contains each complete original retained request, while
`model-N-response.txt` is the exact original public answer string. The copied
`provider-response-N.json` envelopes omit private reasoning by the original
capture policy. Their `public_content` fields can be compared byte-for-byte with
the text exports. `logs.txt` retains all 74 captured log lines.

Do not merge these unaliased records into the demo's aliased citation namespace
without its mapping. The app keeps its existing derivative unchanged. Original
and exported digests are distinguished in [the custody manifest](../manifest.json).
