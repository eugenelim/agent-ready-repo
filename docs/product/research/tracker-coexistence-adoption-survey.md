# Moving product authority out of the tracker — applied survey

> Discipline: applied (practitioner-pattern survey)

- **Run date:** 2026-09-23
- **Commissioned by:** [CAP-0004 Delivery-system coexistence](../intents/CAP-0004-external-tracker-projection.md), to de-risk its riskiest assumption at capability altitude.
- **Assumption under test:** a team running a traditional SDLC can reach this operating model through a **staged** change journey in which each stage pays for itself, without a big-bang change to where scope is negotiated and how progress is reported.
- **Kill condition:** predeclared before the external retrievals returned, and reproduced verbatim under [§ Verdict](#verdict).
- **Four retrievals**, dispatched independently on 2026-09-23: docs-as-code adoption; role and governance impact; sync and projection prior art; agentic delivery metrics. Vendor incentive is flagged inline. Two retrievals hit 403s on specific sources; those are marked as unverified rather than dropped silently.

---

## Bottom line

**The staged path is evidenced, so the bet survives — but it survives on an analogy, and the analogy is weaker than it first looks.**

Three things are now established well enough to design against. Staged adoption is the only pattern anyone has documented; nobody ran a big-bang. One-way projection is the shape that survives contact with production, and bidirectional sync has a named, enumerated set of failure mechanisms. And the dominant way this class of change dies is **pilot-then-abandon**, not technical defeat.

Two things cut the other way, and both are load-bearing.

**No organisation has publicly documented the specific move this capability makes.** Two independent retrievals looked for a named-company account of moving *product scope and decomposition* out of a tracker into the repository and neither found one. What exists is adoption evidence for **decisions** in the repo — ADRs and RFCs. That is a different artifact with a different audience and a much weaker claim on the PMO. Reasoning from ADR adoption to product-scope adoption is an inference this survey makes explicit rather than hides.

**Governance may be a hard floor, not a staging problem.** In SOX-bound and medical-device settings the ticket *is* the control artifact. The claim that a git-based artifact satisfies those obligations is vendor-asserted and, in everything retrieved, never regulator-confirmed — and an academic proposal exists to add traceability tooling to GitHub precisely *because* plain git history does not suffice. Staging does not help here. This is a scope constraint the capability should absorb, not a risk it can sequence around.

---

## Findings

### F1. Nobody has published the migration this capability performs [uncertain — absence of evidence]

Two retrievals searched independently for a named organisation that moved authoritative product scope out of a tracker and into version-controlled repository artifacts. Neither found one. The docs-as-code retrieval reports the tracker→repo migration story "is not documented in named-company form"; the role/governance retrieval reports "almost nothing found is a rigorous study of an organisation that deliberately stopped treating Jira as authoritative for scope and meaning."

This is an **absence, not a refutation**. It means the capability has no direct precedent to copy and no published failure to learn from — and that every finding below transfers by analogy from a neighbouring practice.

Downgrade reason: absence across a practitioner corpus that was not designed to look for this question. Two independent retrievals agreeing on an absence raises confidence that it is a real gap rather than a search failure, but not to the level of a finding.

### F2. Staged adoption is the only documented pattern; heavy-first, light-later [moderate]

No retrieved case ran big-bang. The recurring shape is: start with one heavyweight, broadly-reviewed format for the highest-stakes decisions, then introduce a lighter, narrower format for team-local ones. **Stedi** started with heavyweight RFCs and added lighter Decision Records. **Peloton** oscillated between centralised and decentralised review before landing on ADRs alongside longer design docs. **Klarna** started RFCs for company-wide changes and pushed smaller decisions down to ADRs. **Rust** has run `rust-lang/rfcs` for a decade and explicitly triages which changes need an RFC versus a plain pull request, to stop governance overhead swallowing routine work.

Olaf Zimmermann's adoption model formalises this as five maturity levels and **explicitly warns against forcing every organisation to level 5** (mandatory reviews, a central tracker-integrated repository); stopping at levels 2–3 is a rational endpoint.

Sources: [Companies Using RFCs or Design Docs — Pragmatic Engineer](https://blog.pragmaticengineer.com/rfcs-and-design-docs/) (secondary, June 2022 / updated Feb 2024, compiles ~80 companies), [rust-lang/rfcs](https://github.com/rust-lang/rfcs) (primary, live), [An Adoption Model for Architectural Decision Making — ozimmer.ch](https://ozimmer.ch/practices/2023/04/21/ADAdoptionModel.html) (secondary, 2023/2024), [The Power of "Yes, if" — Squarespace Engineering](https://engineering.squarespace.com/blog/2019/the-power-of-yes-if) (primary, 2019).

Downgrade reason: the named cases come largely from one secondary compilation, and all concern **decisions**, not product scope. Treat the sequencing shape as inferred from a handful of anecdotes, not a general law.

### F3. The dominant failure is pilot-then-abandon, and it is quantified [moderate]

Buchgeher et al. mined **921 GitHub repositories** that had adopted architecture decision records and found roughly **half contain only 1–5 records in total** — adoption of the practice, then abandonment, rather than sustained use.

This is the single most useful number in the survey, because it names the failure shape the capability must design against. It is *not* evidence of reversion to a tracker; it measures abandonment of one artifact type. No retrieved source documents an organisation publicly reverting docs-as-code back to a tracker.

Source: [Using Architecture Decision Records in Open Source Projects — An MSR Study on GitHub, IEEE Access](https://www.researchgate.net/publication/371709784_Using_Architecture_Decision_Records_in_Open_Source_Projects_-_An_MSR_Study_on_GitHub) (primary, empirical, 2023).

Downgrade reason: open-source repositories are not enterprise delivery teams, and an ADR count is a proxy for practice health rather than a measure of it.

A related practitioner claim — that ADR decay is "architectural not cultural" — was retrieved from [JavaCodeGeeks](https://www.javacodegeeks.com/2026/05/the-reason-most-architecture-decision-records-get-written-and-never-read-is-architectural-not-cultural.html) (May 2026) but cites only unlinked "composite practitioner data". **Flagged as low-credibility and not carried as evidence.**

### F4. "Spec drift" is a live, named, unsolved problem — and it is exactly ours [moderate]

GitHub's own `spec-kit` community is currently arguing about the precise failure this capability must prevent. In Discussion #4001 ("Spec Drift") and #1804 ("How do you keep your spec files canonical?"), practitioners report an in-repo `spec.md` and a Jira epic describing the same work diverging silently while both humans and agents edit each.

Two positions are live and unreconciled: an **immutable, one-spec-per-branch** camp and a **living spec with reconciliation tooling** camp. There is explicitly no consensus on cross-repository canonical authority. The maintainer's counter-position is worth carrying: treating spec change as an anomaly is the wrong frame — the real problem is *unauthorised or unlabelled* redirection, not divergence as such.

Sources: [spec-kit Discussion #4001](https://github.com/github/spec-kit/discussions/4001), [spec-kit Discussion #1804](https://github.com/github/spec-kit/discussions/1804) (both tertiary/anecdotal — live discussion threads, not studies — but directly on point and dated August 2026).

**Why it matters here:** CAP-0004's guardrail protects one direction only — the tracker must not silently rewrite canonical intent. Spec drift is the *other* direction: the repository artifact goes stale while the tracker item accumulates the real scope. The guardrail as written does not address it.

### F5. One-way projection is the shape that survives; bidirectional sync fails in named ways [moderate]

The clearest enumeration of bidirectional failure mechanisms: **race conditions on overwrite** (arrival order decides the final value, not business intent), **echo loops** (a write to B is reported as a change and sent back), **cross-field constraint breakage** (per-field merge preserves both edits and breaks a business rule spanning them), **mapping drift mid-flight**, and **duplicate side effects** (a repeated update retriggers notifications). The proposed remedy is a shared correctness contract — cross-system identity, explicit field ownership, idempotency keys — rather than two one-way pipelines pretending to be bidirectional.

Three independent corroborations of the one-way preference. **Canonical's `sync-issues-github-jira`** states outright that "the syncing is only one way: GitHub to Jira"; it was archived in February 2025 and **replaced with another one-way sync bot**, not upgraded to bidirectional. **git-bug** embeds issues in git as the source of truth and models tracker sync as explicit directional `bridge pull` / `bridge push` commands rather than an automatic loop. **Exalate** ships *no* default conflict-resolution model at all, requiring per-field Groovy scripts — an implicit admission that no default policy generalises.

Sources: [The Engineering Challenges of Bi-Directional Sync — Stacksync](https://www.stacksync.com/blog/the-engineering-challenges-of-bi-directional-sync-why-two-one-way-pipelines-fail) (secondary, vendor-authored; the mechanism list is more credible than the product framing), [canonical/sync-issues-github-jira](https://github.com/canonical/sync-issues-github-jira) (primary, archived Feb 2025), [git-bug](https://github.com/git-bug/git-bug) (primary), [Exalate two-way synchronization](https://exalate.com/blog/two-way-synchronization/) (tertiary, vendor).

**Evidence against, and it is real:** Unito and Exalate are commercially viable products years into operation, so bidirectional sync clearly works well enough for paying customers over narrow, well-scoped field sets. The honest claim is that *naive* bidirectional sync fails by named mechanisms and that some teams deliberately choose one-way — not that bidirectional universally fails. Two data points are not a survey.

**Consequence for this repository:** ADR-0019 D5's one-way rule is corroborated by the external record. It should not be softened.

### F6. Hierarchy impedance is real, and GitHub's limits are hard numbers [moderate, two claims flagged unverified]

**GitHub sub-issues** (generally available 2025) carry documented limits: **maximum depth 8 levels, maximum 100 sub-issues per level, single parent only**. Maintainers explicitly rejected multi-parent requests, redirecting them to a separate dependency feature. In [community discussion #148714](https://github.com/orgs/community/discussions/148714), teams migrating from Jira report missing board-view parent-child visualisation; "group by parent issue" was acknowledged by maintainers to produce duplicate parent rows or drop parentless issues, and cross-organisation sub-issue linking is still under evaluation.

Sources: [Introducing sub-issues — GitHub Engineering](https://github.blog/engineering/architecture-optimization/introducing-sub-issues-enhancing-issue-management-on-github/), [GitHub changelog 2025-04-09](https://github.blog/changelog/2025-04-09-evolving-github-issues-and-projects/) (both primary), community discussion #148714 (primary, live).

**Jira's hierarchy is now confirmed against Atlassian's own documentation, and the explainer sources had it slightly wrong.** [Configure the work type hierarchy](https://support.atlassian.com/jira-cloud-administration/docs/configure-the-issue-type-hierarchy/) (primary, Atlassian) states Jira provides "three levels of work type hierarchy: a level for larger pieces of work (level 1, by default called **Epic**), a level for standard work items (level 0, called **Story**), and a level for smaller pieces of work (level -1, called **Subtask**)." Three levels on Atlassian's own counting, not the two the explainer sources reported.

Three further facts matter for a projection and none appeared in the explainer material. **Both** adding work types at the Epic level **and** creating additional custom levels require **Jira Cloud Premium or Enterprise**. A new level "will be created at the top of the work type hierarchy", so the hierarchy extends upward rather than downward. And no maximum number of levels is stated.

**Atlassian's current vocabulary is "work type", not "issue type"**, throughout that page. A profile table naming an "Issue" row is using terminology Atlassian has moved off.

One claim from the same area remains unconfirmed:

- On Jira ↔ Jira Align sync, a Jira **Epic** becomes a Jira Align **Feature**. If accurate, this is the sharpest possible illustration of the impedance problem: the same word names a different tier depending on which system you are looking at. Rests on a search snippet, not a verified read.

**Consequence for this repository:** the impedance thesis in `decompose-intent`'s `references/tracker-projection.md` is externally corroborated in shape. Its specific profile table is not, and the GitHub Issues + Projects and Jira Software rows it lacks are exactly where the unverified claims sit.

### F7. The blocker is organisational, not explanatory — and this repository already measured that [high]

This finding is carried from the repository's own [platform-adoption-evaluation survey](platform-adoption-evaluation-survey.md) rather than re-retrieved, and it is the strongest evidence in scope.

The CNCF 2025 annual survey ranks **cultural change with the development team at 47%** — top-ranked, ahead of security (36%), lack of training (36%) and technical complexity (34%) — with the survey's own framing that "for the first time, the primary challenge to cloud native adoption is not technical — it's organizational." Backstage, the nearest structural analogue, reached 96% adoption inside Spotify but external adopters **plateau around 10%**, attributed to being treated as a catalogue rather than a self-service workflow system; separately, **64% of engineers have been observed bypassing internal developer platforms** they were meant to use. DORA 2024 finds user-centric platforms outperform **mandated** ones, which closes off the obvious top-down remedy.

See that survey for full citations and its per-source incentive flags.

### F8. Role impact is essentially unevidenced [uncertain — absence]

No retrieved source documents a business analyst's, product owner's or PMO's job actually changing as a consequence of a tracker being demoted. Thoughtworks' November 2025 analysis of spec-driven development describes specs as markdown living in the repository rather than the tracker, and **does not address role reassignment at all** — it says only that "a human in the loop" reviews specs, unspecified who.

What exists is adjacent symptom literature: warnings against product owners becoming "Jira jockeys"; scrum masters reporting felt redundancy as teams self-organise; and a structural mismatch in which 34% of PMOs define their purpose as "process and governance" while executives focus on margin and trade-offs. None of it is causally linked to a tracker-demotion decision.

Sources: [Spec-driven development — Thoughtworks](https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices) (secondary, Nov 2025), [The Product Owner is Not Your Jira Jockey](https://www.rebelscrum.site/post/the-product-owner-is-not-your-jira-jockey) (secondary, opinion), [18th State of Agile Report summary — pmwares](https://pmwares.com/the-18th-state-of-agile-report-key-insights/) (tertiary; not verified against Digital.ai's original).

A widely-repeated "70% of PMOs cannot prove their worth" statistic was blocked at fetch (403) and is **not carried** — it should not be cited.

### F9. Governance is a floor, and "git satisfies it" is vendor-asserted, never regulator-confirmed [moderate — the negative half is the load-bearing part]

**SOX.** Compliance practitioner sources state that SOX-bound teams require every database change to map to an approved ticket, and that auditors test "the field, not the policy PDF" — a live, validated, non-editable-after-the-fact link between change and ticket. In that setting the ticket *is* the control artifact. Both retrieved sources are SEO/compliance-content sites naming no auditor or firm; treat the direction as plausible and the specifics as weak.

**Medical device (IEC 62304 / FDA).** Vendor and content-mill sources claim submissions can cite a git tag or commit ID per released version so a regulator can inspect the code at that commit. Against that: an academic paper proposes adding traceability tooling *to* GitHub specifically because plain git history is insufficient for regulatory documentation out of the box, and a compliance-tooling market (Ketryx, Jama Connect, Visure) exists precisely to bridge the gap. **No documented precedent was found of a regulator or auditor publicly accepting bare git history in place of a structured traceability matrix.**

**DO-178C.** Nothing found outside vendor marketing. Evidence absent.

Sources: [Introducing Traceability in GitHub for Medical Software Development — arXiv:2110.13034](https://arxiv.org/abs/2110.13034) (primary, 2021, abstract only), [Git Version Control for FDA and IEC 62304 Compliance — IntuitionLabs](https://intuitionlabs.ai/articles/git-workflows-fda-compliance) (tertiary, marketing, Aug 2025), [Building an audit trail from Jira and Git — SecurityScientist](https://www.securityscientist.net/blog/12-questions-and-answers-about-building-an-audit-trail-from-jira-and-git-complete-guide-for-2026/) (tertiary).

**Consequence for this capability:** in a regulated adopter the tracker may have to remain the audited system of record. That is not a stage to sequence through; it is a boundary. CAP-0004 currently has no position on it.

### F10. Probabilistic forecasting has one named case, and its politics are missing [low]

**John Lewis & Partners**, via Equal Experts: traditional estimation was "prohibitively expensive," threatening to consume around **10% of the team's annual capacity**. Monte Carlo simulation over historical throughput replaced it, and two deadline-dependent initiatives were reported delivered on time using forecasts generated "without a single estimation session."

The conspicuous gap is the one the question asked about. The case study reports **no stakeholder resistance, no political friction and no account of how leadership reacted to giving up fixed-date commitments.** It reads as a success narrative with the politics edited out, self-reported by the consultancy that did the work.

**Basecamp's Shape Up** is the counter-example that names the limit: no standups, no sprint planning, no story points, replaced by pitches at a betting table. Secondary commentary observes the trade-off directly — with no backlog you cannot point to a roadmap, and organisations with enterprise sales or board reporting requirements cannot operate that way. (Attributed to the commentator, not to Basecamp.)

No case was found of an external fixed-price or fixed-date **contract** renegotiated toward probabilistic ranges, nor of client or procurement resistance to that shift. Squarely unevidenced.

Sources: [Stop wondering and start using probabilistic forecasting — Equal Experts](https://www.equalexperts.com/blog/data/stop-wondering-and-start-using-probabilistic-forecasting-a-case-study-at-john-lewis-partners/) (secondary, vendor case study — success framing discounted), [Shape Up — Basecamp](https://basecamp.com/shapeup/0.1-foreword) (primary).

Downgrade reasons: single case, vendor-reported, and missing exactly the dimension under test.

### F11. "Issues-as-code" as a category has not stuck [uncertain — inference from converging weak signals]

Small git-native trackers have existed for over a decade — git-bug, git-issue, gitissius, BugsEverywhere, Fossil's built-in tickets. Practitioners describe the category as niche; BugsEverywhere is noted as never having gained popularity, and git-bug's own maintainer acknowledges limited real-world use.

Four structural reasons are offered, and all four bear on this capability: trackers serve non-engineer stakeholders who will not adopt git-native workflows; large organisations prefer centralised tools by default; no schema or workflow convergence emerged across implementations; and relational querying is harder against git-native storage than against a database. That last tension is visible live — the **Beads** project is mid-migration from git-JSONL persistence to a Dolt SQL backend specifically to get richer querying, and has hit new consistency problems across working-directory checkouts. An open, unresolved issue, not a concluded case study.

One clear counter-case: **Backstage TechDocs** made the authoritative-in-repo, rendered-elsewhere pattern stick at real scale. But that is documentation, not work state, so it is only a partial analogue.

Sources: [Issues in the Repo — nesbitt.io](https://nesbitt.io/2026/08/20/issues-in-the-repo.html) (primary practitioner survey, Aug 2026), [HN thread on git-bug](https://news.ycombinator.com/item?id=43971620) (tertiary), [beads#3135 — Clarify git vs dolt as source of truth](https://github.com/gastownhall/beads/issues/3135) (primary, open), [TechDocs Overview — Backstage](https://backstage.io/docs/features/techdocs/techdocs-overview) (primary).

**Note the distinction that rescues the capability from this finding:** the failed category tried to make the repository the *working surface* for everyone, including non-engineers. CAP-0004 does the opposite — it keeps the repository authoritative for meaning and gives non-engineers the tracker they already use. F11 is evidence against the thing this capability explicitly refuses to do.

### F12. Under agentic execution, output rises and outcome does not follow [moderate]

This is the best-evidenced finding in the survey and it lands squarely on the capability's completion-versus-outcome guardrail.

**DORA 2025** (~5,000 professionals, 100+ hours of qualitative data, September 2025) reports 90% AI adoption and a **reversal on throughput** — AI adoption's relationship with throughput flipped positive in 2025, having been negative in 2024 — while **AI adoption continues to correlate with lower delivery stability**. Its framing is that AI amplifies existing organisational strengths and weaknesses rather than fixing dysfunction.

**Faros AI** telemetry across roughly 10,000–22,000 developers and 1,000+ teams found high-AI-adoption teams completed **21% more tasks** and merged **98% more pull requests**, while **PR review time rose 91%, PR size 154%, and bug count 9% — and org-level DORA metrics showed no measurable improvement.** Separately: a 180% commit increase yielded only 50% more projects and 30% more releases, and a four-marketplace analysis found **no increase in total usage at all** despite the code-activity rise.

**Greptile**, analysing several million pull requests across 65,000 organisations, reports fully AI-generated merged PRs rising from **0.86% in February 2025 to 27.6% in April 2026**, with AI-generated PRs about **20% larger** than human PRs by the same author.

**METR's randomised study** (early 2025) found developers using AI tools took **19% longer** on real tasks while believing they were **20% faster** — a 39-point perception gap.

Mik Kersten's *Output to Outcome* (2025, drawing on 8,000+ value streams) names the thesis directly: as agents amplify output, the bottleneck shifts to the enterprise's ability to connect output to outcomes.

Sources: [Announcing the 2025 DORA report](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report) (primary), [dora.dev 2025](https://dora.dev/dora-report-2025/) (primary), [Faros AI — key takeaways](https://www.faros.ai/blog/key-takeaways-from-the-dora-report-2025) (secondary, vendor — sells DORA tooling; the underlying counts read as real telemetry, the framing is self-interested), [Rise of the Overnight Agents — Greptile](https://www.greptile.com/blog/rise-of-the-overnight-agents) (secondary, vendor, own corpus), [Why AI Agent Metrics Lie — Augment Code](https://www.augmentcode.com/guides/why-ai-agent-metrics-lie) (secondary, vendor), [Output to Outcome — IT Revolution](https://itrevolution.com/product/output-to-outcome/) (publisher page, book not read).

**Consequence:** CAP-0004's guardrail that delivery completion and outcome progress are reported as two numbers is not a stylistic preference. It is the documented failure mode of agentic delivery, measured by three independent telemetry sources.

### F13. Flow metrics survive; throughput forecasting under agentic work is unevidenced [moderate finding, with a named gap]

Yuval Yeret argues flow metrics become **more** necessary under agentic development, not less, because "AI makes starting work feel almost free" and local 10x coding speedups routinely turn into meagre org-level throughput improvements once review, architecture and validation bottlenecks — still human — are hit. That is consistent with Faros's numbers above and with Reinertsen's flow principles unchanged.

**The gap is specific and was searched for directly.** No dated source between 2023 and 2026 tests Monte Carlo or throughput-based forecasting against agent-driven throughput data and reports whether forecast accuracy held. Targeted searches against the named forecasting practitioners returned nothing on-topic. One podcast episode surfaced in search as covering it; on direct read of the episode page, AI was not mentioned anywhere — **that claim is explicitly not corroborated and is not carried here.**

This matters because Monte Carlo forecasting assumes a roughly stable item-size distribution, and Greptile and Faros both measure item size *changing character* (+20% and +154% respectively). That forecasting validity therefore degrades is a plausible **inference and is labelled as one** — no retrieved source tests it.

On presenting a forecast without it being read as a commitment, the practitioner pattern is risk-appetite-anchored pairs — "50% by June, 85% by August" — letting leadership choose how much schedule risk to carry. The named political objection is that a committee which asked for a date can reasonably read a probability distribution as evasion. Both claims come from secondary sources not verified by direct fetch; **lower confidence.**

Sources: [How to Leverage Flow Metrics To Accelerate Your Agentic Development Lifecycle — Yuval Yeret](https://yuvalyeret.com/blog/flow-metrics-still-matter-agentic-ai-development/) (secondary, practitioner, July 2026). The percent-complete critique (the 90/90 rule; "a measure of convenience, not completion") is durable management theory dating to 2003 and earlier — **flagged stale as an AI-era claim**, structurally still applicable.

### F14. OpenAI Symphony is direct prior art, and it points the other way on authority [moderate — primary source, early-stage project]

Published during this capability's shaping and directly adjacent to it. Symphony "turns project work into isolated, autonomous implementation runs, allowing teams to manage work instead of supervising coding agents." It **monitors a Linear board for work and spawns agents to handle the tasks**, landing pull requests on GitHub, with engineers reviewing CI status, PR feedback, complexity analysis and walkthrough videos rather than supervising the agent. It is a **specification-based framework implementable in any language**, with an experimental reference implementation in Elixir, Apache-2.0 licensed, and explicitly "a low-key engineering preview for testing in trusted environments." At retrieval it showed roughly 27.4k stars against 47 commits — a very recent, high-visibility launch rather than a mature system.

Three consequences, and they pull in different directions.

**It corroborates the managed-unit floor.** "Manage work instead of supervising coding agents" is the same problem CAP-0004 names, and Symphony's answer places the floor at the tracker work item, with the agent run below the line. That is independent support for the floor being real and roughly placeable.

**It establishes the opposite authority direction.** In Symphony the tracker is the queue agents pull from — Linear is where work originates. That is tracker-as-source, the convention this capability refuses. A high-visibility OpenAI project normalising it is an adoption headwind: it makes repo-canonical authority the position that must be argued rather than assumed. Note the README does not state whether Linear remains authoritative throughout, so this is read from the described flow, not from a stated authority model.

**Its runtime shape is what the guardrail forbids.** Something must *watch* the board and *spawn* agents. CAP-0004 forbids introducing a daemon, control plane, database or scheduler. Symphony is evidence that the adjacent design space reaches for exactly that, and the capability's refusal is therefore a real constraint with a real cost, not a free choice.

Being spec-based and Apache-2.0, it is a plausible interop target rather than something to rebuild.

Sources: [openai/symphony](https://github.com/openai/symphony) and its README (primary). Downgrade reasons: engineering preview, not production; no documented component topology, queue or database; the authority model is inferred from the described flow.

### F15. Enterprise work items occupy four to six states, measured [moderate]

Added 2026-09-23 from a second research round commissioned to re-test
[FEAT-0010](../intents/FEAT-0011-intent-backed-working-view.md)'s granularity
assumption outside this repository's corpus. Both sources are peer-reviewed and
neither is vendor-published — a distinction that matters here, because
everything else in this survey's delivery-metrics material is vendor telemetry.

A **2023 process-mining study at Thermo Fisher Scientific** mined 14,739
nonduplicate Jira issues across 24 teams and 74 repositories. Observed feature
paths commonly span **four states** — Inbox, To Do, In Progress, Done — or five
where testing occurred, and about **10% of one team's features moved backwards**
from Done to In Test.

A **2018 IEEE case study** reconstructed complete Jira status histories: 795
completed issues produced 6,011 status events, or **7.56 recorded state visits
per issue**, with the dominant path traversing **six distinct statuses** and
**176 distinct path variants** observed across 15 status and activity types.

What is absent is a representative cross-enterprise *distribution* — no
benchmark exists to borrow for how many states an item typically occupies.
Single-enterprise and team-level measurements are what exist.

Sources: [Coremans et al., October 2023](https://jacobkrueger.github.io/assets/papers/Coremans2023ProcessMiningTFS.pdf)
(primary, peer-reviewed, industry co-authored with Thermo Fisher Scientific),
[Marques et al., July 2018](https://web.tecnico.ulisboa.pt/diogo.ferreira/papers/marques18assessing.pdf)
(primary, IEEE). Downgrade reasons: two studies, not a survey; the 2018 paper
is eight years old; the 7.56 figure counts revisits rather than unique states.

**Consequence:** this refutes, on measurement, the proposition that enterprise
items pass through too few states to occupy a board column. It is the single
finding that separates the enterprise population from this repository's own
corpus, where the median shipped spec exposes two states.

### F16. Enterprise epics persist for months; hierarchy churn is unmeasured [moderate finding, named gap]

A **2025 University of Hamburg dissertation** analysing resolved issues from
public Jira repositories reports recorded **epic changes at a median 81 days
after creation**, epic workflow-field changes at **118 days**, and resolution
changes at **164 days** — with epics and new features carrying roughly five
more field changes than other requirement types (requirements overall: median
eight field changes, IQR 5–12). Epics are demonstrably touched for months.

That is a lifespan *proxy*, not a lifespan: it measures change timing, and the
corpus is public open-source Jira rather than enterprise delivery data.

**The churn question is answerable and has not been asked.** A related 2022
paper characterises the *static* structure of **607,208 Jira links** — 97.7% of
composition-link graphs are hierarchical trees — without measuring how those
trees change through replanning. The dataset behind it holds **2.7 million
issues and 32 million historical changes**, so split, merge, re-parent and
renumber rates are technically measurable today.

Sources: [Montgomery, May 2025](https://ediss.sub.uni-hamburg.de/bitstream/ediss/11664/1/2025-05-14%20Lloyd%20PhD%20Thesis%20-%20PDF%20Version.pdf)
(primary, doctoral), [Montgomery, Lüders & Maalej, May 2022](https://arxiv.org/abs/2201.08368)
(primary, dataset paper), [Lüders, Bouraffa & Maalej, May 2022](https://arxiv.org/abs/2204.12893)
(primary). None vendor-published.

### F17. Independent retrieval paths disagreed, and the disagreement was the finding [high]

Three retrievals ran on the second round: two Claude subagents and one Codex
worker on a different model with a different search path. The two Claude
retrievals independently concluded that state occupancy had **no quantitative
evidence at all** and that only prescriptive "configure 7–8 statuses" advice
existed. The Codex worker found F15's two peer-reviewed process-mining studies
measuring it directly.

Two agreeing retrievals produced a confident absence finding that was wrong.
The absence was a property of the search path, not of the literature.

**It happened again on the third round, which makes it a pattern rather than an
incident.** Probing sample-size requirements for flow metrics, a Claude
retrieval reported that "no sourced guidance was found" on bootstrapping,
reference-class forecasting or borrowing across teams, and called it "a genuine
gap in the retrieved literature, not something I'm inferring exists." The Codex
worker returned four peer-reviewed sources on exactly that question, including
Minku's Dycom result — cross-company borrowing maintaining or improving
performance with 10× fewer local training projects in 15 of 18 cases. The same
round also produced feature-per-PI counts that the Claude retrieval had
reported as unavailable.

Twice now, an absence asserted with explicit confidence by agreeing Claude
retrievals has been refuted by a single differently-routed worker. This is
recorded as a method finding because this survey leans on absence findings
elsewhere — F1 and F8 are both absences reached by agreeing retrievals. **Those
two should be read as provisional until a differently-routed worker has looked
for them**, which has not been done.

### F18. Outcome review needs no platform — and lapses anyway [moderate]

Added 2026-09-24 from a third research round, commissioned to de-risk
[FEAT-0012](../intents/FEAT-0013-timeline-and-strategic-progress-review.md).

**No method prescribes a product.** MSP 5th edition, PRINCE2 7, PMI's
benefits-realisation framework and Scrum.org's Evidence-Based Management all
describe the same shape — an owner-led review against pre-agreed baselines and
measures, with named owners and review dates — and none requires a data
platform. EBM deliberately defines no mandatory measures; PMI's plan chooses
"whatever tools and resources are necessary." Australia's national audit office
found one agency's measurement deliberately reusing existing tools and surveys.
**No source establishes that buying a benefits platform improves review
completion.** The guidance is an evidence and governance obligation, not a
technology architecture.

**It lapses regardless.** Ten Norwegian public IT projects studied roughly a
year after completion — when their plans expected nearly all benefits to exist
— had realised an average of **45%**, while owners still expected eventual
realisation of **92%**. **None quantified benefit uncertainty; only two of ten
had a complete written measurement plan.** A systematic review of **47
empirical software and IT studies** found benefit overstatement reported by
26–48% of respondents in four studies and 54–70% in two others. A separate
Norwegian survey (n ≤ 71) found **40% reporting deliberate overstatement** to
secure approval.

Sources: [Holgeid et al., 2023](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/sfw2.12079)
and [Holgeid et al., 3 February 2021](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/sfw2.12007)
(both primary, peer-reviewed); [Lin & Pervan, 2003](https://espace.curtin.edu.au/bitstream/handle/20.500.11937/24510/20679_downloaded_stream_135.pdf?sequence=2)
(primary); [Scrum.org EBM Guide, 7 May 2024](https://www.scrum.org/resources/evidence-based-management-guide),
[PMI BRM framework, November 2016](https://www.pmi.org/-/media/pmi/documents/public/pdf/learning/thought-leadership/benefits-realization-management-framework.pdf)
(both primary, publisher sells certification — interest flagged).

Downgrade reasons: overstatement figures are self-reported from small
convenience samples with low response rates; the ten-project realisation study
is one country and one sector.

**Not carried:** a frequently-cited 56%-value-shortfall figure across 5,400+
projects is consultancy research whose data and methods are not public. UK
national-audit figures (8% / 64%) circulated in a first retrieval could not be
verified — every primary document returned 403 — and a second, differently
routed search reported **no quantitative evidence** for the exact proportion
that declares benefits and never checks them.

### F19. The review lapses hardest exactly where it is most needed [moderate]

The single most design-relevant finding of the three rounds. In an Australian
study of 69 organisations, **26.2% admitted their process overstated benefits
to obtain approval** — and among those, **only 50% routinely reviewed benefits
afterwards, against 84.6% of the rest**.

The projects whose claims most need checking are the least likely to be
checked. That is a selection effect, not a discipline problem, and it means a
*voluntary* outcome review is completed by the honest and skipped by the
inflated — so measuring review completion rates in aggregate will understate
the problem, because the missing reviews are non-randomly the important ones.

Source: [Lin & Pervan, 2003](https://espace.curtin.edu.au/bitstream/handle/20.500.11937/24510/20679_downloaded_stream_135.pdf?sequence=2)
(primary). Downgrade reasons: single study, 2003 and therefore old, n=69,
self-reported admission of overstatement — which if anything understates the
rate.

---

## Verdict

**Kill condition as predeclared, 2026-09-23, before the external retrievals returned:**

> KILLED if BOTH hold across the retrieved prior art: (i) NO staged adoption path is evidenced — every documented success of moving authoritative product meaning out of the incumbent tracker required the reporting/governance layer to change at the same time; AND (ii) the dominant documented failure mode for this class of migration is organisational authority/mandate, NOT tooling friction — meaning a better projection surface would not have saved the failed cases.
>
> SURVIVES if EITHER a staged path with per-stage value is evidenced, OR the documented failures are attributable to causes this capability's design can address.

**Condition (i): FALSE.** A staged path is evidenced (F2) — heavy-first then light-later, across four named organisations and one formal adoption model that explicitly sanctions stopping partway.

**Condition (ii): TRUE.** Organisational friction outranks technical friction (F7, 47% top-ranked), and the quantified failure is pilot-then-abandon (F3).

The kill required both. **The bet SURVIVES.**

**It survives desk-grounded only, which is not validation.** Per `de-risk-intent`, a surviving bet whose only evidence is desk research still carries a `to-validate` hook. Three qualifications travel with this verdict and none is cosmetic:

1. **The staged evidence is an analogy.** It is drawn from ADR and RFC adoption — decisions in the repository — not from product scope and decomposition. No instance of the actual migration is published (F1).
2. **Survival does not extend to regulated adopters.** Where the ticket is the audited control artifact (F9), staging is not the issue and no amount of it helps.
3. **The verdict says the journey can be staged. It does not say anyone completed it.** Half of ADR adopters stopped at a pilot.

---

## What this changes in the capability

Five consequences, each traceable to a finding.

- **Keep the one-way rule and do not soften it.** F5 corroborates ADR-0019 D5 from outside the repository.
- **The guardrail is half-written.** It forbids the tracker rewriting canonical intent; F4 names the opposite drift — the repository artifact going stale while the tracker accrues the real scope — and nothing currently addresses it.
- **Design against pilot-abandonment, not against rejection.** F3 is the measured failure. This aligns with the repository's own [graph-powered SDLC survey](graph-powered-sdlc-survey.md) finding that an edge survives when producing it is a byproduct of work someone had to do anyway, and dies when it is a separate act of documentation. Projection must be a byproduct.
- **Regulated adopters need a stated position.** F9 is a boundary, not a risk.
- **The first stage must not require the reporting layer to move.** That is what "each stage pays for itself" means operationally, and F2 is the only evidence that such a staging exists.
- **The completion-versus-outcome guardrail is now the best-evidenced thing in the capability.** F12 measures it three independent ways: +98% pull requests with no org-level DORA movement, a 180% commit rise yielding 30% more releases, and a marketplace analysis where usage did not move at all.
- **Repo-canonical authority must now be argued, not assumed.** F14 shows a high-visibility OpenAI project normalising the opposite direction. The capability's position needs a stated rationale an adopter can read.
- **The no-runtime guardrail has a named cost.** F14 shows the adjacent design space reaching for a watcher that spawns agents. Refusing it is defensible and is not free.

---

## Known unknowns

- **Known-unknown:** whether a team that moved product scope (not decisions) into the repository sustained it. Would be closed by: a named case study, or this repository's own adopters once one exists. F1 shows none is published today.
- **Known-unknown:** what a BA, product owner or PMO actually does differently afterwards. Would be closed by: interviews with those roles at an adopting organisation — F8 shows the literature has not asked.
- **Known-unknown:** whether a regulator or auditor will accept repository-based traceability in place of ticket-based control. Would be closed by: a documented audit outcome. F9 found only vendor assertion.
- ~~**Known-unknown:** Jira Software's exact native hierarchy depth.~~ **Closed against Atlassian's own documentation** — three levels, Epic/Story/Subtask at 1/0/−1, with both extra work types at Epic level and additional custom levels gated behind Premium or Enterprise, and new levels added at the top. See F6.
- **Known-unknown:** the Jira → Jira Align tier rename. Would be closed by: a read of Atlassian's own documentation on that sync; it still rests on a search snippet.
- **Unknowable from published sources:** the reversion rate for docs-as-code. Organisations do not publish the practices they quietly dropped, so F3's abandonment proxy is the closest measurable thing and the true rate cannot be recovered.
- **Unknowable as posed:** whether *this* capability's staging works, before an adopter runs it. The outcome has not happened.
- **Known-unknown:** whether throughput-based forecasting stays valid when agentic work changes item-size distribution. Would be closed by: a forecast-accuracy study against agent-driven throughput. F13 shows the named forecasting practitioners have not published one.
- **Known-unknown:** whether Symphony treats the tracker as authoritative throughout, or only as an entry queue. Would be closed by: reading its specification rather than its README. F14's authority reading is inferred from the described flow.
- **Known-unknown:** whether AI-generated work items pollute a tracker in practice. Would be closed by: telemetry on item provenance. Two vendor sources that would have had the data did not discuss it, which may be selection rather than absence.

---

## Evidence-class notes

Four retrievals ran independently. F2, F3 and F5 are the load-bearing findings and each rests on at least one primary source. F1 and F8 are absence findings, which two retrievals reached separately — that agreement raises confidence the gap is real, and an absence still cannot carry a positive claim. F7 is imported from an existing repository survey rather than re-retrieved.

Vendor incentive is flagged on Stacksync, Unito, Exalate, Equal Experts, IntuitionLabs and the compliance-content sites. Two claims in F6 and the PMO statistic in F8 were blocked at fetch and are recorded as unverified rather than cited as fact. One source (JavaCodeGeeks, F3) was retrieved and **rejected** for unlinked sourcing.
