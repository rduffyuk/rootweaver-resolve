# Rootweaver Resolve standalone repository

This repository contains the portable 0.5.0 investigation viewer, an opt-in
fixed-evidence HTTP inference route, and a selected research archive. It is not
the private Rootweaver platform or a general cluster executor.

- Preserve original evidence, response text, captured timestamps, failed outcomes
  and the distinction between a model hypothesis and controller support.
- Do not rewrite historical evidence or its hashes to make an evaluation pass.
- Use `make setup test verify build smoke` for the portable validation path.
  Tests and CI must not make provider calls or connect to a cluster.
- Keep API keys, kubeconfigs, run-state directories and personal recordings out
  of Git. Lab IP addresses and workload names are intentionally present in the
  research archive; do not blanket-redact them.
- Update research custody records for intentional additions. A digest verifies
  retained bytes, not semantic truth, completeness of acquisition or human approval.
- The source modules under `reference/` document the retained investigation;
  they are not installed as a working Observe/cluster backend.
- Publication, hosting, model calls and Devpost submission require the owner's
  authorization. A private review push does not authorize public release.
