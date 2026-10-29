# Build and verify

Use Python 3.12+ and Node.js 22 for the tested development path. The application
has no third-party runtime dependencies. Node is needed only for presentation
tests; no npm install or frontend bundler is needed.

```sh
git clone https://github.com/rduffyuk/rootweaver-resolve.git
cd rootweaver-resolve
make setup
make test verify build smoke
make run
```

The repository is public; no GitHub account is needed to clone or download it. Open http://127.0.0.1:8766/ after `make run`. For a different port,
run `.venv/bin/resolve-demo --port 8793`. These commands replay retained evidence
and make no inference request. The separate opt-in route is documented in the
[README](../README.md#run-a-fresh-model-analysis).

`requirements-build.txt` pins the build frontend, backend and their dependencies.
`--no-isolation` makes the build use that installed toolchain. The Python wheel
contains the application, static UI and retained demonstration data. The source
distribution also contains documentation, research records and build scripts.
Neither contains private platform services or model weights. The release review
video is in the Git repository; it is excluded from the Python source archive to
keep the installable source small.

`scripts/smoke_wheel.py` creates a new environment, installs the wheel without
dependencies, starts its loopback server from outside the checkout, and checks
the workbench, case console and retained data. It then stops only its own server.
It does not require the private Rootweaver platform. `scripts/verify_evidence.py`
checks custody hashes, all original case-response strings, all five original
packet-case responses against their provider envelopes, and the current live-analysis freeze. The older demo freeze remains as
historical evidence; the current application freeze is authoritative for this package.

GitHub Actions runs those same tests and builds, with read-only repository
permissions and no secrets. Its artifact is a review build, not a deployment or
a published release. The local macOS result and Linux Actions result are separate
observations; neither proves physical-phone, Safari or live-cluster support.

## Manual equivalent

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
.venv/bin/python -m pip install --no-build-isolation --no-deps .
.venv/bin/python -m unittest discover -s tests
node --test tests/*.mjs
.venv/bin/python scripts/verify_evidence.py
.venv/bin/python -m build --no-isolation
.venv/bin/python scripts/smoke_wheel.py
```

Build output goes to `dist/`, which is ignored by Git. Keep API credentials and
fresh-inference reservation state outside this repository. Do not enable live
inference in CI. Updating a freeze is a separate reviewed change, not a way to
silence an integrity failure.

## Download the test build

Download `rootweaver_resolve-0.5.0-py3-none-any.whl` and `SHA256SUMS` from the [v0.5.0 release](https://github.com/rduffyuk/rootweaver-resolve/releases/tag/v0.5.0). Compare the wheel's SHA-256 with its entry in that file (`shasum -a 256` on macOS or `sha256sum` on Linux). In the download directory:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install --no-index --no-deps rootweaver_resolve-0.5.0-py3-none-any.whl
.venv/bin/resolve-demo
```

Open http://127.0.0.1:8766/. On Windows, use `py -3.12 -m venv .venv`, `.venv\Scripts\python` and `.venv\Scripts\resolve-demo`; Windows execution has not been qualified in this release. The default replay requires no API credentials and executes no cluster commands. Python 3.12+ is required. Use the full source ZIP for the research archive and offline packet calculations; TShark is only needed for those calculations.
