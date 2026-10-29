# Submission review pack — Resolve 0.5.0

Prepared on 29 October 2026 for the Nebius x NVIDIA Global AI Hackathon.
**Private owner review. No final submission or public release is authorised.**

The official deadline is **30 October 2026, 17:00 UTC / London time**.
[Official event](https://nebiusglobalaihackathon.devpost.com/) ·
[Requirements](https://nebiusglobalaihackathon.devpost.com/rules)

[Devpost draft](https://devpost.com/software/rootweaver-resolve) is saved with the
project story, technologies, repository link, cover and three actual screenshots.
Eleven technical/free-text answers plus track and Tavily selection were saved and
read back. Proposed ratings still say owner review. Personal declarations and
publication-dependent URL fields remain incomplete.
Devpost reports `draft`, `published_at: null`, and no submitted date.
[YouTube review](https://youtu.be/u5MD-dPgKpo) is **Private** with thumbnail and captions.

## Open these first

1. [Ryan's 2:18 demonstration](media/resolve-05-ryan-review.mp4)
2. [Devpost story](../devpost-submission.md)
3. [All official form answers](DEVPOST-FIELDS.md)
4. [YouTube title, description and chapters](YOUTUBE-UPLOAD.md)
5. [Build and verify](BUILD.md), [original research](../research/README.md) and
   [animated architecture](ARCHITECTURE.md)

## Cover candidate

![Resolve cover candidate — conceptual branding](media/resolve-cover.png)

## Proposed Devpost gallery

| Order | File | Caption |
|---|---|---|
| Cover | [Resolve cover](media/resolve-cover.png) | An agent investigates. You inspect the evidence. Conceptual branding. |
| 1 | [Desktop workbench](media/desktop-overview.png) | The recorded check, readable output and model assessment in one workbench. Genuine retained execution; playback does not make new calls. |
| 2 | [Collection method](media/method-desktop.png) | Inspect the scoped command, tool method and captured output. Original records remain available in full. |
| 3 | [Mobile assessment](media/mobile-assessment.png) | Review hypotheses and qualifications in a mobile viewport. Physical-phone validation remains separate. |
| 4, optional | [Evidence artwork](media/resolve-evidence-art.png) | Follow the checks. Challenge the conclusion. Conceptual illustration, not a product screenshot. |

## Publication decisions still needed

- Approve the video, captions and thumbnail after viewing the private upload.
- Approve public repository visibility and an anonymously accessible test-build
  URL. A local preview and a private GitHub Actions artifact do not satisfy this.
- Decide whether the downloadable test build with the documented opt-in runtime
  meets the desired judge experience, or whether a hosted replay is also wanted.
  Fresh inference needs the operator's own key; the retained packet collector is
  not portable. Do not claim a hosted live agent or automatic new collection.
- Confirm submitter identity/residence, existing-project disclosure, eligibility
  declarations and subjective feedback ratings in the field packet.
- Authorise the final Devpost submission separately.

## Review criteria

The strongest thirty-second path is **TCP capture → four measured timings →
model qualification → unresolved next check**. The video currently reaches the
detailed timings around 61 seconds. An optional future opening edit could move
that visual payoff earlier; the current recording already fits the time limit
and preserves Ryan's delivery.

Keep the story focused on inspectable debugging and a useful human handover.
Do not claim reliable autonomous RCA, improved MTTR, calibrated confidence,
production qualification or superiority from this small case series.
