# Surface references

Per-surface evidence on what good product docs do, for choosing page shape after surface discovery. Load one file only when [`../surface-discovery.md`](../surface-discovery.md) names that surface. A repository with two surfaces loads two files.

| Surface | Load | Surface discovery section |
| --- | --- | --- |
| Library or SDK | [`library-sdk.md`](library-sdk.md) | Library or SDK |
| CLI | [`cli.md`](cli.md) | CLI |
| HTTP or RPC API | [`http-api.md`](http-api.md) | HTTP or RPC API |
| Desktop or mobile app | [`desktop-or-mobile-app.md`](desktop-or-mobile-app.md) | App |
| Service | [`service.md`](service.md) | Service |
| Agent-context pack | [`agent-pack.md`](agent-pack.md) | Agent-context pack |

Plugin or extension and framework surfaces have no file here. Use their section in surface discovery and the nearest surface above.

## How to read these files

Evidence is narrow: mostly popular open-source projects and large vendors, a few older studies, and pages read through a summarising fetch. Treat each file as follows:

- **Default** is a rule supported on more than one source.
- **Option** applies only under its stated condition. Name the condition when you use it.
- **Do not resolve** means sources conflict and reader state decides. Pick by that state and say which you picked.
- Everything else is judgement and says so.

When you rely on a page described here, re-open it. Do not trust a summary of it.

## Defaults shared by two or more surfaces

1. A runnable or checkable first task whose result the reader can verify: a command, a call, a request, a typed ask, or a click path for apps.
2. Real, short example output, input and output in separate blocks, placeholders explained (CLI, library, API).
3. At least one example for every reference entry (CLI, API, library).
4. Hand-written task or tutorial material beside any reference; never generated reference as the only docs (library, API).
5. Symptom-worded troubleshooting headings (library, agent pack).
6. Say plainly what is unsupported or unfinished; do not leave it silent (service).

## Evidence quality

Count sources by cohort, not by page. Claude Code docs, the Agent Skills specification, and Anthropic's best-practices page are one cohort. Stripe and Twilio are one cohort. The Google style guide and the Write the Docs newsletter argue from maintenance cost and count as one view. The case for annotated screenshots is a 2000 study of 48 novices on printed manuals; the case for sparse ones is cost, translation, and privacy.

Not tested anywhere in the sources: whether example asks narrow how readers phrase requests, whether in-app help beats web help, how long a first task takes, how a skill catalogue should be ordered, and any government-manual guidance (every fetch failed).
