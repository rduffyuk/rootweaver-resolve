# Rootweaver Resolve — inspect the investigation

Version 0.5.0 owner-review draft. The story and gallery are saved in the [Devpost draft](https://devpost.com/software/rootweaver-resolve). Public release and final submission remain on hold. The hackathon entry is still draft; the project page was inadvertently published by a general-editor gallery save and hidden from the portfolio. The owner accepted continuing to edit this project page; the hackathon entry remains unsubmitted. See docs/SUBMISSION-REVIEW.md.

**An agent investigates. You inspect the evidence.**

Resolve makes an AI investigation reviewable: which debugging checks it chose, what came back, what changed its assessment and what still needs a human.

## Inspiration

I am an SRE. Agents can read logs convincingly, but their suggested fixes can conflict or be disruptive. I wanted to give a model real debugging tools, let it gather evidence against competing explanations, and expose enough of its method for a human to judge what to investigate next.

## What it does

Resolve gives NVIDIA Nemotron 3 Ultra a fixed catalogue of scoped checks. In the demonstrated laboratory run, Ultra selected client logs, Service/EndpointSlice inspection, a bounded TCP capture and pod status, then handed the unresolved investigation to a human. Observe supervised collection; the controller constrained the targets and budgets. The model could not execute arbitrary commands or remediate.

The workbench opens with the concrete finding and a proportional packet timing diagram. Established observations, weakened explanations, remaining uncertainty and the next suggested investigation are visible together. Readable log rows, resource snapshots and TCP conversations remain beside the evolving hypotheses. Every check exposes its recorded command, output, model input and accepted assessment. A human can follow the method and access complete captured records without having to read JSON first.

## The demonstration

A dependency times out while readiness stays green. Service evidence weakens an endpoint-selection explanation. Packet evidence shows successful exchanges and four complete timings: first server data around 2,001 ms after client payload, after client FIN around 801 ms. The investigation narrows toward response delay and client waiting budget, but it does not establish the underlying latency cause or the correct timeout.

The model overstated five complete timings and called the timeout too aggressive. A side-by-side model/evidence comparison preserves those statements and shows the reviewer qualifications. These were added after the run, not detected automatically by the agent. The practical consequence is explicit: these observations do not yet justify changing the timeout. Check its configuration and intended service budget, then select a scoped server-side trace to locate the wait; that follow-up has not run. The video and default viewer replay genuine prior execution; they do not imply that playback runs new commands or inference. The viewer uses an explicitly aliased derivative. The repository also includes the original lab PCAP, retained model requests and public answers, and commands to reproduce the four timings offline. The earlier log window and later packet window are not correlated request by request.

## How we built it

Python, plain JavaScript and SVG; NVIDIA Nemotron 3 Ultra through Nebius Token Factory; Kubernetes reads and Observe-supervised dumpcap with offline TShark decoding. The bounded investigation selected from four approved checks, with deadlines, a fixed target and no remediation. An independent experiment runner handled recovery. The public test build has no cluster connection.

The existing four-case console remains available. It includes a narrow deterministic Service-selection check and an opt-in runtime action that sends fixed sanitised HTTP evidence for fresh Ultra analysis. That action is separate from the packet investigation and is disabled by default. It requires the operator's own Nebius key and retains call budgets and audit outputs.

## Challenges and learning

Readable output and honest attribution mattered as much as tool access. A readiness result does not establish application health. A packet capture does not identify a server-side lock or GC pause. Valid JSON and citations do not establish a correct explanation. We preserve evidence windows, model mistakes, complete outputs and the distinction between observations, model assessments and post-run editorial explanations.

## Scope and limits

The main run contains five genuine calls and four checks in one adapted disposable fixture. Four earlier fault case records contain seven separate historical calls. These are small demonstrations with differing prompts and windows, not a combined accuracy benchmark, held-out evaluation, calibrated confidence estimate or proof of reduced MTTR. No production qualification, autonomous remediation or superiority over experienced SREs is claimed.

## Existing work and AI assistance

Rootweaver predates this competition. Resolve's application, bounded model integration, evidence contracts, fault demonstrations and investigation workspace were developed during the competition. The older platform and independent watchdog are disclosed dependencies. Ryan Duffy owns the problem, architecture and acceptance; OpenAI Codex assisted implementation, verification and packaging. OpenAI image generation supplied conceptual cover artwork, separate from actual product screenshots. NVIDIA Nemotron produced the actual diagnostic outputs. No fine-tuning was performed.

## Links awaiting owner approval

- Public repository: publication pending; standalone source includes MIT licence and setup instructions.
- Working demo or downloadable test build: publication pending; local source ZIP and wheel prepared for review.
- Public YouTube video, under three minutes: Ryan-narrated review cut uploaded privately; public visibility remains pending.

All official form answers are in docs/DEVPOST-FIELDS.md. Subjective ratings and personal declarations remain owner decisions.


Repository preparation update: https://github.com/rduffyuk/rootweaver-resolve is the private owner-review repository. It includes the build workflow, MIT license, research records and narrated review video. Public visibility, judge-facing demo access and final submission remain pending owner approval. The YouTube review upload is private.
