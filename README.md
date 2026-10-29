# Rootweaver Resolve

**An agent investigates. You inspect the evidence.**

<img align="right" width="260" src="docs/media/resolve-evidence-bench.png" alt="Conceptual anime illustration: an engineer inspects diagnostic traces before acting.">

Resolve helps SREs investigate incidents when the model has incomplete system
context. It brings debugging checks, readable evidence and competing hypotheses
together so an experienced operator can assess the conclusions and decide where
to investigate next.

In the retained lab investigation, NVIDIA Nemotron 3 Ultra selected bounded
checks and Rootweaver Observe supervised collection. The workspace makes that
method inspectable, including the model's mistakes and unresolved questions.

[**Download v0.5.0 →**](https://github.com/rduffyuk/rootweaver-resolve/releases/tag/v0.5.0) · [**Read the engineering story →**](https://rduffy.uk/writing/rootweaver-resolve/) · [**Run locally →**](#start-here--no-credentials-needed) · [**Watch Ryan’s 2:18 demo →**](https://youtu.be/WQ6nVurVR9Q) · [**Explore the architecture →**](docs/ARCHITECTURE.md)

[MIT](LICENSE) · Python 3.12+ · No runtime dependencies · Version 0.5.0 · Public retained-evidence test build

https://github.com/user-attachments/assets/f84d90ae-19a2-4c2c-aebc-0d588876c647

**[▶ Watch the narrated demonstration on YouTube](https://youtu.be/WQ6nVurVR9Q)** · [Download the video](docs/media/resolve-05-ryan-review.mp4)

*Play the full 2:18 demonstration above, with Ryan’s own narration.
Actual browser footage from a retained laboratory investigation; playback makes
no new model call or cluster request.
[Full desktop view](docs/media/desktop-overview.png) · [Mobile assessment](docs/media/mobile-assessment.png)*

## Understand it in thirty seconds

1. **Read the measured finding.** The selected endpoint is reachable in the captured connections. Four complete timings
   show first server data around **2,001 ms**, after the client FIN around **801 ms**.
2. **Compare model and evidence.** Ultra narrows the investigation, but overcounts the
   timings and calls the timeout too aggressive without seeing its configuration.
   The comparison is labelled as post-run review, not automatic error detection.
3. **Choose the next investigation.** Establish the configured timeout and intended
   service budget, then select a scoped server-side trace to locate the wait.
   That follow-up is suggested, not run; the cause and correct timeout remain open.

[Reproduce the packet timings offline](research/packet-lab/README.md) · [Inspect the original model exchanges and experiments](research/README.md)

That is the useful handover: the checks already done, the evidence that changed the
assessment, and the uncertainty an operator still needs to resolve.

## Why investigate before changing a system

An incident rarely arrives with complete architecture, dependency and business
context. A change may restore service while leaving the cause unresolved or
shifting the impact elsewhere. An operator needs to understand both the evidence
and the consequences of a restoration.

Resolve uses bounded debugging tools to surface information that can strengthen
or weaken possible explanations. Observe supplies observations about the system;
it does not give the model a complete understanding of that system. The human
reviews whether the evidence supports the hypotheses, adds missing context and
chooses the next investigation or restoration action. Resolve performs no remediation.

<details>
<summary>How architecture, code and business context could strengthen the investigation</summary>

The intended direction is an investigation assistant that can fit into an
operator's existing environment and use the context they authorise. These are
future context integrations, not demonstrated features of this release:

| Context | Investigative value |
|---|---|
| Architecture and dependency information | Identify missing dependencies and the potential impact of a change |
| Source code and configuration matched to the deployed version | Relate observed behaviour to implementation, retries, timeouts and error handling |
| Business objectives and service contracts | Establish critical operations, acceptable waiting budgets and what restoration must preserve |
| Deployment history and operational knowledge | Test explanations against recent changes and previous incident learning |

Each source would need identifiable ownership, version and freshness. Additional
context could improve an assessment; it would not prove the assessment correct
or expand the model's authority to change the system.

Today, the standalone viewer installs without private services and replays the
retained investigation. Fresh HTTP analysis uses a fixed evidence bundle. The
original Observe collector is not bundled as a plug-and-play cluster integration,
and this release does not ingest arbitrary codebases, architecture or business
documents. See [what runs where](#what-runs-where).

</details>

## Start here — no credentials needed

Clone or extract this repository first. Python 3.12 or newer; no runtime dependencies:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/resolve-demo
```

Open **http://127.0.0.1:8766/**. The measured packet finding is visible immediately. Choose **Inspect the capture**
for the complete timings, **Compare model and evidence** for the reviewer qualifications,
or **Follow the investigation** for the original check sequence. For cloning, pinned build tools and CI,
see [Build and verify](docs/BUILD.md).

<details>
<summary>What the replay includes, collection windows and original research artifacts</summary>


Open http://127.0.0.1:8766/ . The opening screen shows the completed investigation. Choose **Follow the investigation** to replay Logs → Service & endpoint → TCP capture → Pod status → Handover. Each step exposes the command, evidence available then and the next accepted model assessment. Later evidence is unavailable in earlier steps.

In thirty seconds: select **TCP capture**. Four complete timings show first server data around 2,001 ms after client payload, after client FIN around 801 ms. The selected endpoint is reachable. Neither the reason for the delay nor the correct client timeout has been established. Inspect Ultra's explanation and the visible reviewer qualifications.

The five genuine Ultra calls and four executed checks happened during the retained lab run. This exported workbench is playback: clicking it makes no provider or cluster request. Commands contain public aliases, so a human must substitute authorised targets to reproduce the method. A new capture observes a new time window. The application includes all 45 decoded frames, 74 captured log records, five model exchanges and the complete sanitised execution journal. This repository also includes the [original lab PCAP and unaliased model exchanges](research/packet-lab/README.md) for offline research inspection.

**Other cases & fresh HTTP analysis** opens the existing four-case console. Its seven historical model responses remain byte-identical. Its optional inference action below analyses a fixed HTTP evidence bundle; it does not run a new packet investigation. The earlier guided checks are authored navigation, whereas the packet investigation's four checks were selected by Ultra from a fixed catalogue.

</details>

## What runs where

| Path | What happens | What is required |
|---|---|---|
| Default evidence workbench | Replays five genuine Ultra exchanges and four executed lab checks; no new requests | Local Python installation |
| Fresh HTTP analysis | Sends fixed retained HTTP evidence to Ultra; no new telemetry | Explicit opt-in, your Nebius key and durable call budget |
| Original lab investigation | Ultra selected checks; Observe supervised collection; a human received the unresolved handover | Retained research records; the private collector is not a standalone runtime |

## Run a fresh model analysis

The separate **Other cases & fresh HTTP analysis → Ask Ultra about this evidence**
panel provides the opt-in Nebius runtime integration. It is disabled by default.
[Read the exact setup, request bounds, reservations and failure handling](docs/FRESH-ANALYSIS.md).

## Follow the investigation through the architecture

![Animated Resolve investigation architecture](docs/diagrams/investigation-loop.svg)

[Source map and all three animated diagrams](docs/ARCHITECTURE.md) · [Static version](docs/diagrams/investigation-loop.static.svg)

## Find what you need

| You want to… | Start here |
|---|---|
| Install, test or reproduce the build | [Build and CI](docs/BUILD.md) |
| Inspect original experiments, mistakes and model outputs | [Research archive](research/README.md) |
| Understand what is and is not established | [Limitations](docs/LIMITATIONS.md) |
| Review evidence transformations and attribution | [Privacy](docs/PRIVACY.md) · [Development disclosure](docs/DEVELOPMENT-DISCLOSURE.md) |
| Contribute a reproducible issue or change | [Contribution guide](CONTRIBUTING.md) |
| Review submission copy, video and artwork | [Submission review pack](docs/SUBMISSION-REVIEW.md) |

<details>
<summary>Earlier fault cases and evaluation limits</summary>

## What is actually demonstrated

- HTTP 500 despite Ready topology, with `InvalidOperation` in `calculate_checkout_total` present in the supplied logs. Identifying the named error is useful synthesis; its underlying cause and release attribution remain unproven.
- Selector mismatch: independently supported narrow selection mechanism; original incorrect Ready-only EndpointSlice assertion remains visible.
- DNS: actual NXDOMAIN and native resolver error; the historical input-window flaw and weak explanations are preserved.
- Client policy denial: source/control difference, one completed historical call, and a second request blocked before POST. The watchdog needed an in-run repair; the case remains HOLD.

Four cases and seven historical calls are a small case series. The first three categories contain six of those calls. Fresh integration checks do not increase the number of real fault categories or establish statistical reliability. No MTTR reduction, production qualification, autonomous remediation or superiority over an experienced SRE is claimed.


</details>

<details>
<summary>Evidence, privacy and complete forensic records</summary>

## Evidence and privacy

The workbench uses tool-specific readable projections by default: timestamped logs, Kubernetes resource tables and TCP conversations. Commands and complete outputs remain expandable. A contextual drawer shows collection methods, original model exchanges and exact model-facing inputs. Full exports never truncate captured lines. Post-run Codex editorial explanations are visibly separate from model answers and measured observations.

The packet case is a disclosed sanitised derivative, including its five model answers: private addresses, workload identifiers, response IDs, interface/container identities and machine paths are aliased. Model mistakes, timings, hypothesis polarity, source-row numbers and evidence references remain. Historical hashes identify the private original bytes, not the derivative. The public investigation manifest hashes all exported files. The seven older case-response strings were already suitable for public export and remain byte-identical. All private originals are unchanged.

Logs and packets were collected in different windows: the packet timings are not a correlation to those same six log requests. One stream begins mid-connection; another ends before a response. The model's five-pair claim and its unsupported timeout recommendation remain visible. The workbench is not a general claim validator or a production RCA system.

The standalone export needs no private Rootweaver services. No model weights or credentials are bundled. See [privacy](docs/PRIVACY.md), [limits](docs/LIMITATIONS.md) and the [visual architecture](docs/ARCHITECTURE.md), which separates the retained lab loop, the case console and the standalone runtime.


</details>

<details>
<summary>Verification details</summary>

## Verify and build

```sh
.venv/bin/python -m unittest discover -s tests
node --test tests/*.mjs
.venv/bin/python -m pip install build
.venv/bin/python -m build
```

For the pinned toolchain, CI, custody verification and a clean-wheel smoke check, follow [Build and verify](docs/BUILD.md). Tests use simulated provider responses and synthetic controller fixtures where explicitly labelled. They make no inference calls. See the separate retained verification receipt for genuine integration outcomes. Install the wheel into a clean environment to verify the packaged assets. The local server binds only to loopback. Hosting requires a separately reviewed gateway/access/budget plan; see [publication handoff](docs/PUBLICATION-HANDOFF.md).


</details>

## Public release and competition scope

The [v0.5.0 test build](https://github.com/rduffyuk/rootweaver-resolve/releases/tag/v0.5.0) includes a Python wheel, source archive and checksums. It runs locally with retained evidence; it is not a hosted live cluster agent. The repository and [Ryan's narrated demonstration](https://youtu.be/WQ6nVurVR9Q) are public. The [engineering article](https://rduffy.uk/writing/rootweaver-resolve/) explains the method, findings and limits. The Devpost hackathon entry remains unsubmitted pending Ryan's separate decision.

The anime artwork is conceptual editorial illustration. The workspace screenshots, original experiment artifacts and unchanged narration remain separately identified. See [the media record](docs/media/README.md).

Rootweaver predates the competition. Resolve's application, inference integration, evidence controls and visual investigation flow are competition-period work. Ryan Duffy owns the problem, design and acceptance; OpenAI Codex assisted implementation and verification. NVIDIA Nemotron produced the actual AI analyses through Nebius Token Factory. No fine-tuning was performed. MIT covers this prepared standalone slice. See LICENSE, SOURCE-ORIGINS.json, [license and attribution](docs/LICENSE-AND-ATTRIBUTION.md) and [development disclosure](docs/DEVELOPMENT-DISCLOSURE.md).
