# YouTube publication receipt

Visibility: **Public**, authorised by Ryan and verified in YouTube Studio on
29 October 2026. YouTube’s unauthenticated oEmbed endpoint also returns HTTP 200
for this video.
[Watch on YouTube](https://youtu.be/WQ6nVurVR9Q) ·
[Edit in YouTube Studio](https://studio.youtube.com/video/WQ6nVurVR9Q/edit)

Uploaded with the cover thumbnail, chapters and English (United Kingdom) SRT subtitles.
YouTube copyright check at upload: no issues found. Publication changed visibility
and removed the obsolete private-review paragraph from the description. The
approved video, narration, thumbnail and captions are unchanged. Repository
publication, test-build hosting and final Devpost submission remain separate.

File: [Ryan-narrated demonstration](media/resolve-05-ryan-review.mp4), 137.52 seconds.
The revised footage opens with the measured finding and model/evidence comparison. The original levelled voice track and caption timings are unchanged. Captions: [SRT](media/captions.srt).
Thumbnail candidate: [Resolve cover](media/resolve-cover.png).

Previous private cut: https://youtu.be/u5MD-dPgKpo (retained for comparison; superseded by this finding-first cut).

## Title

Rootweaver Resolve — inspect the AI investigation | Nebius × NVIDIA Hackathon

## Description

An agent investigates. You inspect the evidence.

Rootweaver Resolve gives NVIDIA Nemotron 3 Ultra a bounded catalogue of debugging
checks and shows an SRE the method, readable output and changing assessment.
This demonstration follows a real retained laboratory investigation through
client logs, Service/EndpointSlice inspection, a scoped TCP capture and pod status.

The packet evidence narrows the investigation: the selected endpoint is reachable,
but four complete timings show first server data around 2,001 ms after client
payload, after the client FIN around 801 ms. The underlying latency cause and
correct timeout remain unresolved. The original model's overcount and unsupported
timeout recommendation stay visible alongside explicit reviewer qualifications.

This video replays genuine prior execution. Playback does not run new inference
or cluster commands. The separate optional HTTP analysis route makes a fresh
Nebius Token Factory call on fixed retained evidence; it is disabled in this video.
Public evidence uses disclosed aliases. The standalone viewer has no cluster
connection and performs no remediation.

00:00 Measured packet finding and inspectable investigation
00:16 What the evidence establishes
00:30 Logs and Service evidence
00:45 Scoped packet capture and collection method
01:01 TCP timings and the remaining uncertainty
01:27 Where the model overreached
01:38 Handover and a separate fresh-analysis route
02:03 What the operator can inspect next

Built with Python, JavaScript, SVG, Kubernetes evidence, dumpcap/TShark and
NVIDIA Nemotron 3 Ultra via Nebius Token Factory. Ryan Duffy owns the problem,
design and acceptance; OpenAI Codex assisted implementation and verification.
Narration is Ryan's own recording, not a cloned or synthetic voice.
