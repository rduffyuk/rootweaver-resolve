# Fresh Ultra analysis on retained HTTP evidence

[Back to the project](../README.md) · [Build and verify](BUILD.md)

## Run a fresh model analysis

On the **Other cases & fresh HTTP analysis** page, the **Ask Ultra about this evidence** panel is the runtime integration. It sends one fixed sanitised HTTP-case input to `nvidia/Nemotron-3-Ultra-550b-a55b` through Nebius Token Factory. Inspect the exact outgoing request before pressing **Run fresh analysis**. The result, original public response, input hash, usage, timestamps and independent retained finding are inspectable and exportable.

This is fresh inference on retained observations, **not new telemetry or autonomous collection**. The revised prompt is different from the original experiment; the resulting answer is not a controlled before/after evaluation. Historical responses and gate outcomes remain unchanged.

Create a private directory with mode 700 and a mode-600 key file containing one `NEBIUS_API_KEY=...` line, using your normal secure editor or secret provisioning. Do not put the key in browser storage, a command argument, source control or a public host. Choose a durable private state directory outside the repository. Then:

```sh
.venv/bin/resolve-demo --enable-live \
  --key-file /absolute/private/nebius.env \
  --state-dir /absolute/private/resolve-review-state \
  --freeze-sha256 "$(cat LIVE-FREEZE.sha256)"
```

Opening the page still makes no inference call. An explicit button starts one. The frozen package and request, fixed HTTPS provider, current model access/pricing checks, two durable reservations, 16,384-byte request bound, 4,096-token completion allowance, 120-second transport deadline and no retries bound this route. At the expected $1/$3 per million input/output tokens, the maximum two-call reservation is $0.065536; actual request reservations are displayed. Reservations persist after errors/restarts. Missing or inconsistent usage stops further calls. These are application controls, not account-wide billing limits. Do not delete state to bypass them.

The author's local verification also uses the existing signed-commit launch guard and shared programme ledger. Those private financial records and launch credentials are not distributed. The portable package's explicit digest verifies package integrity; it is not a claim of human approval or production certification. The older synthetic qualification runner and its signed guards remain separate and unchanged.


## Recorded integration versus qualification

This route establishes a bounded runtime integration. It does not extend the historical fault sample or turn the retained packet investigation into a portable cluster executor. See [research](../research/README.md) and [limits](LIMITATIONS.md).
