# Research evidence

Resolve asks whether bounded debugging tools can help a model develop useful,
inspectable explanations while a human keeps operational authority. This archive
includes useful answers, contradictions, rejected outputs and unsuccessful
qualification. It is a selected research export, not a claim that every private
development attempt is included.

## Start with the evidence, not a score

| Experiment | Included records | What it establishes and what it does not |
|---|---|---|
| [Early family v2](synthetic/family-v2-live-results/) | Five attempt records and review package; synthetic evidence, 2,048-token allowance | Retains failed/domain-invalid and token-limited outputs. Different conditions from later batches. |
| [Funded family comparison](synthetic/programme-batch-03-live-results/) | All 18 attempts across batches 01–03, all three review packages and request templates | Nano, Super, Ultra and Super VL received staged synthetic evidence. Eight final-batch outputs passed structural validation; that did not qualify their claims. |
| [Focused qualification](synthetic/ultra-qualification-01-live-results/) | Ten attempt records and checkpoint, plus three review-recovery and four final-negative records | Positive/matching/conflicting/missing evidence and separate review calls. Review models are not human adjudicators. Phase 3 remains unqualified. |
| [Real fault cases](real-faults/) | Seven original public response strings and complete exported staged inputs; full case records in the app data | Selector, HTTP500 and DNS comprise the original three categories/six Ultra calls. Policy adds one completed call; its second request was blocked before POST. |
| [Packet investigation](packet-lab/) | Five original requests, five original public response strings, five provider envelopes, usage records, 74 logs, methods and original 45-frame PCAP | Ultra selected four available checks then handed over. Four complete timings show late server data. The reason for that delay is unresolved. |

The synthetic folders contain **40 attempt records**: 5 early-family, 18 funded
comparison and 17 qualification/review records. Some are reviewer calls or
failures. They are not 40 real incident investigations, and must not be added to
the real-fault sample as evidence of statistical qualification. The five packet
calls are a separate later investigation. Two fresh HTTP integration smoke calls
recorded in the existing candidate's verification history are not new fault
categories and are not exported here as another controlled comparison.

## Files and lineage

- [Methodology and findings](METHODOLOGY.md) explains the changing protocols,
  what information was available at each stage, and the limits of comparison.
- [Packet reproduction](packet-lab/README.md) lets a human decode the original
  PCAP offline. It does not start another capture or contact a cluster.
- [Custody manifest](manifest.json) lists every added source record, original
  digest, extraction pointer where applicable and exported digest.
- [Complete case data](../src/rootweaver_resolve/workspace/data/) contains the
  original case responses, evidence, execution journals and recovery records.
- [Displayed investigation](../src/rootweaver_resolve/workspace/data/investigation/)
  is the existing aliased derivative; its separate manifest binds all files.
- [Investigation source reference](../reference/retained-investigation/)
  shows the check-selection loop and capture contract used by the lab.

Run `python scripts/verify_evidence.py` from the repository root. This verifies
retained bytes and consistency, not semantic correctness or independent review.

## What was preserved, and what was excluded

Disposable lab names, private lab IP addresses, commands, request IDs, timestamps
and model mistakes in the added research records are preserved. The original
PCAP also retains its CPU/OS/dumpcap version, capture filter and interface name.
The packet requests and responses are the original retained fields, without
the demo's aliases. The requests are JSON-reserialized; their historical wire
hashes therefore identify the original serialization, not these pretty-printed
files. The public response **strings** and copied provider envelopes are unchanged.

The already prepared demo keeps its disclosed aliases. Its seven earlier
response strings remain byte-identical; the five displayed packet answers are
aliased derivatives. Both forms are labelled, and their hashes are distinct.

No credential files, authorization headers, kubeconfigs, private reasoning,
personal voice-memo originals, account preflights, signing keys, host inventories,
private financial ledgers or platform Git history are included. The unaliased
full session's raw Kubernetes JSON includes surrounding-node metadata and remains
in private custody; its complete exported derivative is available in the app.
This archive does not silently label that derivative as the original.

Earlier capture qualification attempts, injector/watchdog deployment adapters and
all intermediate UI/video iterations remain in the private archive. They are not
needed to decode this PCAP, inspect these model exchanges or run the standalone
viewer. Six rejected public texts from family batches 01/02 were never retained
by the historical runner: their requests, failure diagnostics and hashes remain,
but the missing answers cannot be reconstructed. No fresh calls were made to
fill that gap. Historical outcomes are unchanged.
