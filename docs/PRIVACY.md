# Public evidence custody

Version 0.5.0 is an owner-review candidate, not a published release. Public observations are derived from real retained disposable-workload captures. Namespace, Pod/EndpointSlice identifiers, hostnames, UUIDs, private addresses and filesystem paths are aliased or removed. Annotations and raw DNS packet hex are excluded because they may carry private infrastructure details. No credentials, host-local kubeconfigs, private signing records, platform Git history, host inventories or injector scripts are included.

The seven earlier case model public-response strings remain byte-identical, including mistakes; their SHA256 hashes are listed in each case. The full original private captures remain untouched outside this export. Source IDs identify original observations and are preserved for citation continuity. Those IDs must not be used as hashes of the sanitised copies. Public files have their own manifest hashes.

No captured line is shortened to fit the UI. Forensic panels start collapsed and export the full retained public copy. Redaction changes sensitive content explicitly; it does not imply complete acquisition. HTTP recovery logs were capped; later events/journal finalization were incomplete. NetworkPolicy recovery logs are partial500. Missing telemetry remains missing.

The app renders untrusted logs and model content with textContent, not HTML. It fetches only local static files, has a restrictive same-origin content policy and has no execution/remediation API. The Python server binds only toloopback; same-user local processes are not a strong isolation boundary. Public hosting requires separate owner approval and hosting review.

## Fresh-analysis boundary in 0.4.0

Only the frozen sanitised HTTP model input is sent to Nebius after explicit opt-in. It excludes raw private source collections and the previous model answer. The exact request is inspectable. New public response text and safe metadata are stored in a private run directory, separate from served static assets; the owner can export them. Private reasoning and credentials are excluded. Failed calls expose categorical errors, not provider error bodies or arbitrary exception strings. Review any new response before including it in public materials.

## Packet investigation workbench in 0.5.0

The separate five-call packet investigation includes private identifiers in its model answers. Its public copy therefore aliases those identifiers consistently across observations, requests, responses and execution records. It does not claim those five answers are byte-identical originals. It preserves all model assertions and mistakes, every captured log record, every decoded frame and all five exchanges. The application bundle excludes raw PCAP and decoded application payload. The separate repository research archive now includes the original disposable-lab PCAP and original model request/response fields; see the archive disclosure below. The application manifest still identifies original input and derivative file digests separately. Public copies of commands are templates containing aliases, not directly executable targets.

The post-run review notes are digest-bound to the exported session. Digest matching prevents accidental attachment to another session; it does not certify semantic truth or independent human review. The viewer fails closed if the notes and session do not match.

## Repository research archive

The repository is private for owner review. Its additional `research/` archive intentionally preserves disposable lab names, IP addresses, commands, HTTP test payloads and original public model answers. The PCAP retains capture-interface and CPU/OS/tool-version metadata. A disposable lab does not require blanket identifier replacement. Specific credential and surrounding-infrastructure exposures were checked before copying records. The original raw Kubernetes session records containing shared-node metadata remain in private custody; the existing application derivative is unchanged. See [research custody and exclusions](../research/README.md). This is a selected evidence archive, not a complete export of private platform operations.
