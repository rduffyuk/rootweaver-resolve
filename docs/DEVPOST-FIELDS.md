# Devpost field packet — 0.5.0 owner-review draft

Prepared from the official event requirements retrieved on 29 October 2026. The project story, technologies, repository link, cover and screenshot gallery are saved in the [online draft](https://devpost.com/software/rootweaver-resolve). Eleven technical/free-text answers plus the track and Tavily selection are also saved and read back. Personal declarations and publication-dependent URL fields remain incomplete. No final submission has been made. Proposed subjective ratings and personal declarations require owner review; they are not already attested.

[Official event rules](https://nebiusglobalaihackathon.devpost.com/rules). The demo/test-build URL is required by the narrative rules for this track even though the API field metadata marks it optional. A public YouTube video of no more than three minutes is also required; its approved URL remains pending.

## 28261 — Submitter Type

Required · dropdown

Suggested: Individual. Owner must confirm whether submitting personally or as an organisation/team.

## 28262 — Organization Name (if applicable)

Required · text

Suggested: N/A if submitting as an individual. Owner declaration.

## 28265 — Submitter Country of Residence

Required · dropdown

Suggested: United Kingdom. Owner must confirm current residence.

## 28266 — If you or any team members reside in Canada, please indicate the province below.

Required · text

Suggested: N/A if no team member resides in Canada. Owner declaration.

## 28267 — Which track are you submitting your project into?

Required · dropdown

Best apps and agents.

## 28268 — Is your project new or existing prior to August 26, 2026?

Required · dropdown

Suggested: Existing, with the explicit disclosure below. Rootweaver predates 26 August; Resolve is a new competition-period application slice. Owner must confirm how the event's definition applies.

## 28269 — If your project is existing, explain how you significantly updated your project with Nebius tools.

Optional in form metadata · textarea

Rootweaver's private SRE and observation platform existed before this competition. During the submission period we built Resolve's standalone evidence/controller contracts, bounded NVIDIA Nemotron inference through Nebius Token Factory, deterministic selector-support checks, genuine fault case demonstrations, source/citation inspector, visual investigation workspace, an agent-selected four-check packet investigation and the opt-in fresh-analysis route. The older platform and independent watchdog are not claimed as newly built or as autonomous remediation. The export does not require the private platform.

## 28270 — Provide a URL to your public code repository for judging and testing on either GitHub, GitLab or Bitbucket.

Required · text

PUBLICATION PENDING — insert the approved public standalone repository URL after verifying anonymous access, root LICENSE and setup instructions. Do not use a private platform repository.

## 28271 — Provide a URL to a working demo, hosted application, or test build of your Project.

Optional in form metadata · text

PUBLICATION PENDING — insert the approved working application or downloadable test-build URL and exact revision. Local loopback previews are not public URLs. The prepared source ZIP/wheel supports a downloadable test build.

## 28272 — Which model(s) did you use, and why did you choose that size/variant?

Required · textarea

The demonstrated application uses nvidia/Nemotron-3-Ultra-550b-a55b through Nebius Token Factory for advisory investigation of bounded Kubernetes, log and TCP evidence. In the main retained run, it selected four debugging checks and revised competing hypotheses across five calls. Earlier exploratory family trials included Nano, Super and Super-VL, with different prompts and small samples; those trials do not establish a general ranking. Ultra provided useful scoped technical interpretations, but its errors require the independent deterministic finding and visible uncertainty.

## 28273 — How would you rate Nemotron's output quality for your use case? (1 = Poor, 10 = Excellent)

Required · textarea

Draft rating for owner review: 6/10 for this constrained SRE use case. Ultra connects supplied logs to a concrete InvalidOperation/calculate_checkout_total clue and can interpret selector/label mismatches. It also made an unsupported Ready-only EndpointSlice claim, contradicted hypothesis polarity, requested logs already provided and gave weak DNS specificity. The main packet run additionally shows useful narrowing from connection failure to response timing, but overcounts complete timing pairs and calls a timeout too aggressive without seeing its configuration. Four earlier fault cases with seven calls and this separate five-call adapted run are not broad qualification. New integration calls use a changed prompt and must not be counted as an accuracy benchmark.

## 28274 — Did you fine-tune, prompt-engineer, or use Nemotron out of the box? What was your approach?

Required · textarea

Prompt engineering, bounded structured evidence and explicit output contracts; no fine-tuning. The investigation prompt requests competing hypotheses, one next check from the approved catalogue, a public rationale and uncertainty. The separate fresh-HTTP runtime prompt distinguishes a failure hypothesis from healthy selection and asks for advisory hypotheses, uncertainty and an unexecuted next check. We inspect the exact model input and preserve the original public response. Deterministic rules independently assess only a narrow Service-selection mechanism.

## 28275 — How did Nemotron's performance compare to other models you've used for similar tasks?

Required · textarea

We cannot make a controlled cross-vendor superiority claim. Earlier small Nemotron-family trials suggested Ultra was useful for scoped interpretation, while all candidates showed limitations. Prompts, contexts and conditions differed across historical experiments. We have not demonstrated superiority over an experienced SRE or other observability products.

## 28276 — Which Nebius platform capabilities were most valuable to your project and how?

Required · textarea

Token Factory's hosted inference API and model catalogue let us use Ultra without deploying its weights or operating a dedicated local inference GPU. The application checks model availability and expected pricing, uses a fixed endpoint and retains safe request/response metadata. This submission does not claim Nebius AI Cloud GPU deployment, Serverless scaling or fine-tuning that we did not use.

## 28277 — How likely are you to recommend running Nemotron on Nebius to other developers? (1 = Unlikely, 10 = Highly Likely)

Required · textarea

Draft rating for owner review: 8/10 for hosted experimentation. API access made a large NVIDIA model practical to integrate and inspect, but production use still requires application-level budgets, input limits, failure handling and evidence validation. This is a subjective proposed rating, not a measured service score.

## 28278 — How would you rate your experience running Nemotron inference on Nebius compared to previous cloud or local development environments? (1 = Poor, 10 = Excellent)

Required · textarea

Draft rating for owner review: 8/10. Hosted access reduced model-serving setup for this application. We retained catalogue, limit, output and usage diagnostics rather than assuming successful JSON equals reliable reasoning. No controlled cloud/local performance comparison or verified invoice reconciliation was performed.

## 28279 — What additional features or improvements would have made the Nemotron on Nebius experience more effective for your project?

Required · textarea

Clearer per-model capability and limit discovery; consistent machine-readable usage/reasoning accounting; explicit guidance on structured-output behaviour and truncation; and easily inspected request diagnostics. Our NetworkPolicy second call was blocked by our own request-size guard before POST, so it is not attributed to a Nebius outage.

## 28280 — What do you most hope to see from the Nemotron team next?

Required · textarea

More reliable hypothesis polarity and evidence-window reasoning; stronger grounding to exact cited fields; better specificity when explaining DNS/log evidence; and recognition that an observation already supplied should not be requested again. Preserve uncertainty about overall cause when only a narrow mechanism is established.

## 28282 — Did you use Tavily in your project?

Required · dropdown

No. There is no functional runtime Tavily call in Resolve.

## 28281 — Builders & Brews - IRL Events City

Optional in form metadata · dropdown

Leave blank unless the owner actually attended an eligible event. Do not infer attendance from residence.

## 28283 — Age

Required · checkbox

OWNER MUST CONFIRM. Do not pre-check or attest on the owner's behalf.

## 28284 — Employee

Required · checkbox

OWNER MUST CONFIRM. Do not pre-check or attest on the owner's behalf.

## 29059 — Which AI tools have you leveraged while working on this project?

Required · textarea

OpenAI Codex assisted source inspection, implementation, tests, debugging, documentation and packaging. NVIDIA Nemotron supplied the application's actual AI analyses through Nebius Token Factory. Ryan recorded the narration for the current review cut. Codex assisted the script, screen capture, audio levelling, subtitle preparation and editing; local Whisper supplied draft transcription. No cloned or synthetic voice is used in that cut. OpenAI image generation supplied conceptual cover artwork; the product gallery uses actual browser screenshots. Ryan Duffy owns the problem, design choices, evaluation acceptance and publication decisions.

## 29060 — Describe the level of learning you/your team derived from the project

Required · dropdown

Suggested: Significant. Owner must confirm this subjective response.

## 29061 — Did you gain AI value that you can use in your career?

Required · dropdown

Suggested: Yes. Owner must confirm. Practical learning included evidence provenance, separating deterministic support from model interpretation, bounded inference and incident UX.




Repository preparation update: https://github.com/rduffyuk/rootweaver-resolve is the private owner-review repository. It includes the build workflow, MIT license, research records and narrated review video. Public visibility, judge-facing demo access and final submission remain pending owner approval. The YouTube review upload is private.
