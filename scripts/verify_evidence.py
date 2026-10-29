"""Verify retained bytes and field consistency offline, not semantic truth."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src/rootweaver_resolve"


def check(path, expected):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise SystemExit(f"Digest mismatch: {path.relative_to(ROOT)}")


def main():
    manifest = json.loads((ROOT / "research/manifest.json").read_text())
    for item in manifest["files"]:
        check(ROOT / item["path"], item["sha256"])
        if item["transformation"] == "none; byte-identical":
            assert item["source_sha256"] == item["sha256"], item["path"]
    investigation = PACKAGE / "workspace/data/investigation"
    exported = json.loads((investigation / "manifest.json").read_text())
    for name, digest in exported["files"].items():
        check(investigation / name, digest)
    assert len((investigation / "logs.txt").read_text().splitlines()) == 74
    responses = 0
    for case in (PACKAGE / "workspace/data").glob("*.json"):
        data = json.loads(case.read_text())
        for response, expected in zip(data["decisions"], data["model_hashes"], strict=True):
            text = response["raw_public_response"]
            assert hashlib.sha256(text.encode()).hexdigest() == expected["public_response_sha256"], case.name
            responses += 1
    assert responses == 7
    packet = ROOT / "research/packet-lab"
    for n in range(1, 6):
        envelope = json.loads((packet / f"provider-response-{n}.json").read_text())
        assert (packet / f"model-{n}-response.txt").read_text() == envelope["choices"][0]["public_content"]
    assert len((packet / "logs.txt").read_text().splitlines()) == 74
    assert len(list((ROOT / "research/synthetic").glob("*/attempt-*.json"))) == 40
    freeze = PACKAGE / "live-freeze.json"
    check(freeze, (ROOT / "LIVE-FREEZE.sha256").read_text().strip())
    for name, digest in json.loads(freeze.read_text())["files"].items():
        check(PACKAGE / name, digest)
    reference = ROOT / "reference/retained-investigation"
    for name, digest in json.loads((reference / "source-manifest.json").read_text()).items():
        check(reference / name, digest)
    print(f"PASS: {len(manifest['files'])} custody records, {len(exported['files'])} investigation files, "
          "7 historical answers, 5 original packet answers, 40 synthetic attempt records, live freeze and source references")


if __name__ == "__main__":
    main()
