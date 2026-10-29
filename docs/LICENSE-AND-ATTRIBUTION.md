# License and attribution

The standalone Resolve code and accompanying authored documentation use the
[MIT license](../LICENSE), copyright 2026 Ryan Duffy. MIT is explicitly listed
among the accepted licenses in the
[Nebius x NVIDIA hackathon rules](https://nebiusglobalaihackathon.devpost.com/rules).
The root LICENSE and project metadata make the license detectable by GitHub.
This private preparation does not make the repository publicly accessible for
judging; that visibility change remains an owner decision.

The research records are supplied as evidence of the author's experiments.
Model-generated text is identified as such and remains unverified interpretation.
No claim is made to own NVIDIA models, Nebius services, Kubernetes, Wireshark,
their trademarks, or other third-party rights. The software license does not
relicense those products. No model weights or third-party executables are bundled.
The review video contains Ryan's own narration; it is not a voice clone.

| Component | Role in this work | Distribution here |
|---|---|---|
| NVIDIA Nemotron models | Genuine model analyses through Nebius Token Factory | Identified request/response records; no weights |
| Nebius Token Factory | Hosted inference API | Integration code and retained safe response records; no credentials |
| Rootweaver Observe | Bounded collection in the retained lab investigation | Source reference and execution evidence; private deployment not included |
| Kubernetes / kubectl | Disposable workload and resource/log inspection | Lab outputs and human command equivalents; binaries not included |
| Wireshark dumpcap / TShark | Supervised TCP acquisition and offline decoding | Original lab PCAP, decoded evidence and reproduction instructions; binaries not included |
| Python / Hatchling / Node.js | Runtime, packaging and tests | Dependency declarations; runtimes not included |
| OpenAI Codex | Assisted implementation, evidence review and documentation | Disclosed in development history and signed contribution records |

Kubeshark and eBPF are not claimed as the tools used for the retained packet
case. That run used Observe-supervised dumpcap and TShark decoding. Broader
Observe capabilities are not evidence that they were exercised here.
