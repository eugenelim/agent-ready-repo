# Authoring product documentation for any repository

> Discipline: applied (practitioner-pattern survey)

Commissioned 2026-10-10 to ground the generalization of `author-product-docs`
beyond agent packs (intent FEAT-0010). The question: what do practitioners agree
a documentation set needs across a reader's whole journey, for any software
surface — library, CLI, HTTP API, app, service, or plugin — and how do teams keep
it true to what ships? Every finding is cited and rated with the applied-mode
overlay; sources from one organization count as one.

---

## Findings

### F1. Readers enter at any page, so the journey is a set of stages, not a sequence `[moderate]`

The stages practitioners name are: discover and evaluate, install, first
success, daily tasks, look-up, understand, troubleshoot, upgrade, and
contribute. DevRel journey maps disagree on stage names and count, and several
reject a linear funnel. Every page must therefore stand alone and link to its
context ("every page is page one").

- DevRel journey maps: [DevRel journey guide](https://developerrelations.com/guides/mapping-the-developer-journey)
- Every page is page one: [Baker via Adobe, 2013](https://blog.adobe.com/en/publish/2013/10/10/7-principles-for-designing-help-topics-in-the-age-of-the-web), [I'd Rather Be Writing](https://idratherbewriting.com/2011/05/16/every-page-is-page-one/)
- Discoverable and addressable pages: [Write the Docs principles](https://www.writethedocs.org/guide/writing/docs-principles/)

Downgrade: stale prior art (Baker, 2013). The principle is widely repeated but
untested empirically.

### F2. Each stage asks one reader question that one artifact answers `[moderate]` [synthesis]

| Stage | Reader question | Artifact |
| --- | --- | --- |
| Discover and evaluate | Is this for me? | README or landing page with use cases and limits |
| Install | Can I get it running? | Installation section or guide |
| First success | Can I make it work quickly? | Quickstart or tutorial |
| Daily tasks | How do I do X? | How-to guides |
| Look-up | What exactly does X accept or return? | Reference (API, CLI, configuration) |
| Understand | Why does it work this way? | Explanation |
| Troubleshoot | It broke. What now? | Error text that links to docs, troubleshooting page |
| Upgrade | What changed, and what breaks for me? | Changelog, release notes, migration guide |
| Contribute | How do I change or extend this? | CONTRIBUTING, extension docs |

The mapping of Diátaxis kinds to stages is inference: Diátaxis maps kinds to
reader need, not to journey stage ([Diátaxis](https://diataxis.fr/start-here/)).
This repository's `journey-mapping` documentation genre covers Discovering →
Orienting → First value → Recurring reference → Mastery, and has no upgrade or
contribute stage.

### F3. A README answers what, why, how to start, and where to get help `[high]`

Required: name, a one-line description, install, usage with an example,
support, contributing, and license. Longer material moves to a docs site rather
than being deleted. Practitioners disagree on length: makeareadme accepts long
READMEs, while GitHub limits a README to what is needed to start and contribute.

- [GitHub Docs: About READMEs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes) and [opensource.guide](https://opensource.guide/starting-a-project/) (one organization)
- [makeareadme.com](https://www.makeareadme.com/)
- [standard-readme spec](https://github.com/RichardLitt/standard-readme/blob/main/spec.md)

### F4. First success needs one reliable path with a visible result at each step `[moderate]`

A quickstart shows a result early, offers no choices, and must work every time.
Prerequisites are stated up front and code samples work as pasted. Practitioners
do not agree whether a quickstart is a tutorial or a how-to; the tutorial rules
fit it best.

- [Diátaxis tutorials](https://diataxis.fr/tutorials/)
- [The Good Docs Project templates](https://www.thegooddocsproject.dev/template)
- [Open edX content types](https://docs.openedx.org/en/open-release-sumac.master/documentors/concepts/content_types.html)

Time-to-first-success is the usual measure, but no benchmark data was found.

### F5. Reference is generated from code where possible, and its examples are tested `[moderate]`

Library reference comes from docstrings or doc comments. Doc tests then fail the
build when an example stops matching: Python `doctest`, Sphinx doctest, and
rustdoc. HTTP API reference comes from an OpenAPI or similar contract and states
auth, errors, rate limits, and pagination. CLI help leads with examples, and
`--help` works on every subcommand.

- [Python doctest](https://docs.python.org/3/library/doctest.html), [Sphinx doctest](https://www.sphinx-doc.org/en/master/usage/extensions/doctest.html), [rustdoc tests](https://doc.rust-lang.org/rustdoc/write-documentation/documentation-tests.html)
- [Command Line Interface Guidelines](https://clig.dev/) `[low]` alone
- [Gravitee API docs guide](https://www.gravitee.io/docs-guide.html), [Moesif Stripe teardown](https://www.moesif.com/blog/best-practices/api-product-management/the-stripe-developer-experience-and-docs-teardown/) `[low]`, vendors

### F6. The repository itself reveals the user-facing surface `[uncertain]` [inference]

Package manifests and public exports reveal a library. Argument parsers and
`bin` entries reveal a CLI. Route definitions and OpenAPI or proto files reveal
an API. Config schemas, deploy files, and health endpoints reveal a service.
Extension manifests reveal a plugin's commands and settings
([VS Code extension manifest](https://code.visualstudio.com/api/references/extension-manifest)).
No source tests this mapping; it is the riskiest assumption in FEAT-0010.

### F7. Troubleshooting pairs a symptom with a cause and a fix `[moderate]`

Error text names the cause, echoes the bad value, says how to fix it, and links
to docs. Minimalism treats error recognition and recovery as part of every task.

- [Google technical writing: error messages](https://developers.google.com/tech-writing/error-messages/set-tone)
- [Carroll's minimalism summary](https://www.psy.gla.ac.uk/~steve/MinMan2.html), 1990s
- [The Good Docs Project troubleshooting template](https://www.thegooddocsproject.dev/template)

### F8. Upgrade docs separate the change record from the migration steps `[moderate]`

A changelog is for humans, newest first, with ISO dates and the groups Added,
Changed, Deprecated, Removed, Fixed, and Security. A migration guide covers
breaking changes only, one per version pair, as a checklist the reader can
search their code against. Deprecations name the replacement and the removal
window.

- [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
- [Astro upgrade guides](https://contribute.docs.astro.build/upgrade-guides/about/), [Elasticsearch breaking changes](https://www.elastic.co/guide/en/elasticsearch/reference/8.4/breaking-changes.html), [Ultravox deprecation table](https://docs.ultravox.ai/changelog/deprecation)

Practitioners disagree on whether release notes and the changelog are one file
or two.

### F9. A standalone FAQ page is an anti-pattern `[high]`

FAQs duplicate content that then drifts, organize by format instead of task, and
are often invented rather than asked. Fold the answers into task pages; at most,
keep a short list of real questions that link to them.

- [Unity docs style guide](https://docs-style-guide.unity.com/content-types/faqs), [I'd Rather Be Writing](https://idratherbewriting.com/2017/06/23/why-tech-writers-hate-faqs/), [Kirklees website standards](https://www.kirklees.gov.uk/beta/website-standards/why-we-dont-publish-faqs.aspx)

### F10. Navigation groups by reader goal, and its shape scales with page count `[moderate]`

Group by how readers look for things, not by code or org structure. Headings
must describe their section, because readers scan headings first. This
repository's `information-architecture` documentation route adds a page-count
rule (flat under 30 pages, hub-and-spoke to 200, search-first beyond) and a
landing page with a single "start here" path.

- [NN/g layer-cake scanning](https://www.nngroup.com/articles/layer-cake-pattern-scanning/)
- [Diátaxis](https://diataxis.fr/)
- [Write the Docs principles](https://www.writethedocs.org/guide/writing/docs-principles/)

### F11. Docs stay true when they change in the same pull request as the code `[moderate]`

Docs-as-code keeps docs in version control, reviewed like code, and blocks
merging features without docs. Link checkers and prose linters (such as lychee
and Vale) run in CI. Doc tests cover runnable examples only. Prose claims,
defaults, and screenshots still need a human check.

- [Write the Docs: docs as code](https://www.writethedocs.org/guide/docs-as-code/)
- [Kubernetes: contributing new content](https://kubernetes.io/docs/contribute/new-content/)
- [Vale](https://docs.vale.sh/), [lychee](https://github.com/lycheeverse/lychee)

Screenshots go stale every release. Teams that keep many screenshots generate
them from end-to-end tests ([TYPO3](https://talk.typo3.org/t/typo3-screenshots-tool-base-module/4427),
[CloudCannon](https://community.cloudcannon.com/t/100-automated-screenshot-coverage-in-our-documentation/493)).

### F12. For machine readers, plain Markdown pays off and llms.txt is unproven `[moderate]`

Serving pages as Markdown cuts their size by more than 99% in one measured case
(180,573 tokens as HTML versus 478 as Markdown). Some coding agents already ask
for Markdown. llms.txt is cheap to publish, but log studies report that most
files get no requests, and no source shows that it improves answers.

- [Checkly agent content negotiation](https://www.checklyhq.com/blog/state-of-ai-agent-content-negotation/)
- [Vercel AI-readable docs guide](https://vercel.com/kb/guide/make-your-documentation-readable-by-ai-agents) (vendor)
- [llmstxt.org](https://llmstxt.org/), [Common Crawl llms.txt analysis](https://commoncrawl.org/blog/a-content-analysis-of-llms-txt-files-from-the-july-2026-crawl-archive), [ppc.land on the Ahrefs log study](https://ppc.land/llms-txt-adoption-rises-8-8x-but-97-of-files-get-zero-ai-requests/)

### F13. Page views mislead, and search failures show what is missing `[moderate]`

Bounce rate and time on page need too much guessing. Zero-result searches and
task tests (time a reader on a task with old and new docs) say more.

- [Write the Docs newsletter, May 2018](https://www.writethedocs.org/blog/newsletter-may-2018/)
- [GitBook docs analytics](https://gitbook.com/docs/guides/docs-analytics/documentation-analytics) (vendor)
- [Document360 search analytics](https://docs.document360.com/docs/analytics-search) (vendor)

---

## What this means for `author-product-docs` [synthesis]

- Discover the surface from repository evidence before choosing artifacts (F5, F6).
- Map an existing docs set to the journey stages and report gaps by stage (F1, F2).
- Give each stage artifact a page contract, including the ones Diátaxis does not
  cover: README, quickstart, installation, troubleshooting, changelog, migration
  guide, contributing, and landing page (F3, F4, F7, F8).
- Fold FAQ content into task pages (F9).
- Hand navigation structure to `information-architecture`, the journey picture
  to `journey-mapping`, rendered-site critique to `design-review`, and UI strings
  to `ux-writing`, when those skills are installed (F2, F10).
- Verify by surface: run doc tests, `--help`, or the contract the reference
  claims to describe; label prose claims that no check covered (F5, F11).
- Do not create llms.txt by default (F12).

## Known unknowns

- **Known-unknown:** whether repository signals identify a surface reliably
  across real repositories. Would be closed by: running the skill on a sample of
  library, CLI, API, and app repositories and scoring the inferred surface.
- **Known-unknown:** contracts for docs landing pages from a primary source.
  Would be closed by: reading the per-template contracts of The Good Docs
  Project and docs-platform guidance.
- **Known-unknown:** whether release notes and changelog should be one artifact.
  Would be closed by: a survey of maintainers' reader feedback; sources conflict.
- **Unknowable:** the effect of any docs metric on business outcomes. Why not:
  practitioners report no controlled comparison, and Write the Docs speakers say
  the link is hard to isolate.
