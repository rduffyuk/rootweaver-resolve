# Contributing to Resolve

Resolve is a small, inspectable SRE investigation workbench. Start with
[the build guide](docs/BUILD.md), then run `make setup test verify build smoke`.
The default app and all tests run without a cluster or provider credentials.

For a bug report, include the revision, Python/browser version, selected case,
steps to reproduce, expected behaviour and observed result. Distinguish a UI
problem from a disputed model statement: historical mistakes are intentionally
retained. Share only evidence you have permission to disclose. Never include
keys, kubeconfigs, private incident data or fresh-inference state.

Keep changes focused. Application code lives in `src/rootweaver_resolve/`,
portable tests in `tests/`, build and custody tools in `scripts/`, and research
records in `research/`. `reference/` documents the original lab implementation;
it is not an installed cluster backend. See [architecture](docs/ARCHITECTURE.md)
for the source map.

Do not rewrite original model outputs, timestamps, failed outcomes or evidence
digests to make a test pass. A corrected interpretation belongs alongside the
original with its own attribution. Preserve complete exports and keep observed
facts separate from hypotheses and post-run editorial explanations.

Describe the user-visible change, relevant validation and remaining limitations
in a pull request. Do not enable inference in tests or CI. Changes to collection,
execution permissions, provider spending or public hosting need separate review.

The project is maintained by Ryan Duffy. During private owner review, use the
repository's issue or pull-request workflow if you have access. Code is MIT
licensed; see [LICENSE](LICENSE) and [attribution](docs/LICENSE-AND-ATTRIBUTION.md).
