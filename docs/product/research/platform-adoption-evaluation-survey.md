# How organisations evaluate adopting a technical platform

> Discipline: applied (practitioner-pattern survey)

Commissioned 2026-09-10 to de-risk
[`cohort-orientation-surfaces`](../intents/cohort-orientation-surfaces.md)
without waiting on a champion interview. The intent's premise is that a
champion's blocker is explanatory. This survey tests that against prior art on
platform adoption, because the estate is multi-party and one interview cannot
sample it.

Three independent retrievals. Every finding is cited, confidence-tagged, and
carries its downgrade reason. Vendor incentive is flagged inline.

---

## Bottom line

**The intent is aimed at half its estate, and not the half that can say no.**

Adoption of a developer-facing platform is decided by two groups with
different needs. **Influencers** — engineers, tech leads, platform teams —
advocate but cannot approve, and for them documentation demonstrably matters.
**Gatekeepers** — architecture review boards, security, procurement, budget
holders — hold the veto, and they demand evidence types a shared explanatory
artifact cannot carry: a three-year TCO, an exit path, an SBOM, DORA deltas.

So the two claims under test resolve differently:

- **"The blocker is explanatory"** — unsupported as a primary cause. The
  top-ranked blocker in the largest practitioner survey is organisational.
- **"One artifact can serve several stakeholders"** — supported for the shared
  *mental model*, unsupported for *gatekeeper evidence*. The canvas is
  necessary and not sufficient, and the insufficiency is concentrated exactly
  where the veto sits.

---

## Findings

### F1. The estate is two-tier, and the tiers want different things [high]

Influencers, who advocate but cannot approve: individual engineers, tech leads
and engineering managers, platform/infrastructure teams, staff and principal
architects.

Gatekeepers, who hold formal veto: the Architecture Review Board or enterprise
architects, security/CISO, procurement and legal, and budget holders. LeanIX
documents a seven-step ARB process requiring a project description, business
case, technical specification, risk assessment and compliance alignment before
approval, with a board typically composed of CIO/CTO, CISO, CFO or procurement
officer, and a legal/compliance officer.

Evidence demanded, by role — the detail that matters most here:

| Role | Demands |
| --- | --- |
| Individual engineer | Solves real pain, low-friction onboarding, documentation quality |
| Tech lead | Team productivity delta, integration with existing stack, support model |
| Platform team | Adoption metrics, before/after DORA deltas, user satisfaction |
| Staff/principal architect | Reference architecture, failure-mode analysis, **exit path**, topology alignment |
| ARB | Full technical specification, risk assessment, compliance alignment, exit strategy |
| Security / CISO | SOC 2 Type II, SSO, audit logs, data residency, SBOM, CVE posture, data-flow diagram |
| VP Eng / CTO | DORA metrics, deployment velocity, headcount impact, TCO |
| Budget holder / CFO | Three-year TCO, licensing predictability, risk-adjusted ROI |
| Procurement / Legal | Contract terms, OSS licence compatibility, indemnification, SLAs, DPAs |

Sources: [daily.dev enterprise dev-tool selling guide](https://business.daily.dev/resources/sell-developer-tools-enterprise-from-individual-user-to-procurement/)
(primary), [LeanIX ARB](https://www.leanix.net/en/wiki/ea/architecture-review-board)
(primary; LeanIX sells EA tooling — incentive flagged),
[InfoQ on Kubernetes adoption](https://www.infoq.com/articles/kubernetes-successful-adoption-foundation/)
(primary).

### F2. Bottom-up initiation with top-down ratification is the dominant pattern [high]

Five documented stages: discovery by an individual, validation on real work,
expansion across peers, champion formation, then formalisation through
architecture, security and procurement review.

Named cases: **Kubernetes at Zalando** — 2016 Hack Week, 60 infrastructure
engineers, then teams onboarded one at a time with mandatory training and a
production gate. **Kubernetes at Bloomberg** — 2015 trial to 2017 production,
with leadership requiring CI and monitoring maturity first. **Terraform** —
HashiCorp's Adopt → Collaborate → Scale → Govern, 12–18 months to maturity
(vendor source, incentive flagged). **Backstage at Spotify** — platform team
solving its own problem, 96% R&D adoption before open-sourcing. **Go at
Google** — engineer frustration with 45-minute compiles (2012 paper; flagged
stale at 14 years as a model for current organisational dynamics).

Sources: [srcco.de Zalando](https://srcco.de/posts/how-zalando-manages-140-kubernetes-clusters.html),
[InfoWorld Kubernetes success stories](https://www.infoworld.com/article/2264741/kubernetes-meets-the-real-world-3-success-stories.html),
[HashiCorp phases](https://developer.hashicorp.com/terraform/intro/phases),
[Backstage background](https://backstage.io/docs/overview/adopting/) (all primary).

### F3. The bottom-up route is narrowing, and that changes who must be convinced [high]

TechCrunch reported that enterprises allowing engineer-selected tools in
production fell to **11%, down from 38% six months earlier** — a 65-point drop
in sandbox permissions. The average enterprise deal cycle for developer tools
runs **6.5 months with seven or more decision-makers**.

This is the single most consequential finding for any strategy that assumes a
champion carries the decision. The champion still initiates; they no longer
close.

Source: [TechCrunch, May 2023](https://techcrunch.com/2023/05/30/have-enterprise-buyers-finally-soured-on-bottoms-up-tech-sales/)
(primary, quantified, independent publication). Downgrade note: 2023 data in a
moving market; direction is corroborated by the ARB and procurement literature
but the exact figure may have moved.

### F4. Organisational friction outranks explanation as an adoption blocker [high]

The CNCF 2025 annual survey ranks blockers: **cultural change with the
development team 47%** — top-ranked — with security 36%, lack of training 36%,
and technical complexity 34%. The survey's own framing: "for the first time,
the primary challenge to cloud native adoption is not technical — it's
organizational."

Platform-engineering practitioner literature agrees: "Platform engineering
rarely stalls due to technology; it stalls because of change management or
because organisational misalignment prevents platforms from getting started."
On Terraform modules, documented failure "stems from internal organisational
issues, not from the modules' maturity or coverage."

Sources: [CNCF 2025 survey](https://www.cncf.io/announcements/2026/01/20/kubernetes-established-as-the-de-facto-operating-system-for-ai-as-production-use-hits-82-in-2025-cncf-annual-cloud-native-survey/)
(primary), [platformengineering.com](https://platformengineering.com/features/why-platform-adoption-fails-and-how-successful-teams-fix-it/)
(secondary, expert testimony without quantitative data).

### F5. "I cannot re-explain it" is not a documented blocker [moderate]

No source retrieved names it. The adjacent documented failure is different in
kind: champions lack the **vocabulary to translate technical value into
business outcomes**. A champion may understand a system completely and still
fail to map it to a CFO's concerns.

The distinction changes the intervention. Better explanation of the model
addresses comprehension; the documented gap is translation to business value,
which is a different artifact — a TCO model, a risk register — not a clearer
diagram.

Downgrade reason: this is an absence-of-evidence finding across a
practitioner corpus, not a study that looked for the failure and failed to find
it. Sources: [M Accelerator](https://maccelerator.la/en/blog/growth-strategy/why-your-champion-cant-sell-internally/),
[Ten Lives Media](https://tenlivesmedia.com/champion-enablement-b2b-sales/)
(both secondary; both consultancies selling champion enablement — incentive
flagged).

### F6. Documentation does move adoption — at the evaluation stage [moderate]

**91.18% of practitioners rely on open-source documentation when making
adoption decisions**, examining compatibility, ease of use, use-case examples
and community adoption among nine categories.

This does not contradict F4. Documentation moves *evaluation*; organisational
friction kills *adoption*. They are different stages with different actors, and
conflating them is how a documentation strategy gets aimed at an organisational
problem.

Source: [arXiv:2403.03819](https://arxiv.org/abs/2403.03819) (primary,
peer-reviewed). Downgrade reason: scope narrowed to Sphinx/ReadTheDocs, so
generalisation to other documentation types is inference.

### F7. Architecture-diagram effectiveness is unmeasured [uncertain]

**No empirical research was found** on whether architecture diagrams shorten
evaluation or move non-architect audiences. Everything located is practitioner
advocacy. C4's audience tiering — context diagram for executives, container and
component for architects — is stated as design rationale, never as a measured
outcome, and the most detailed source is a vendor ebook from a company selling
C4 tooling.

This is an absence, not a refutation. The canvas may work; nothing published
shows that it does.

Sources: [Lucidchart C4](https://lucid.co/blog/c4-model) (tertiary,
vendor-produced, no research citations). Downgrade: no primary research exists
to rate.

### F8. Evaluations are long, and most die without a decision [moderate]

A primary buyer survey (n=502, April 2026) found evaluation spans **four
months**, 92% experienced research fatigue, 72% delayed purchases, and **65%
abandoned their search entirely** without selecting anything. Abandonment
causes: unmet requirements 24%, budget changes 20%, **stakeholder misalignment
16%**, comparison difficulty 12%. 54% reported post-purchase regret.

Note what is absent from that list: an inability to explain the product to
colleagues. The nearest is stakeholder misalignment at 16%, ranked fourth, and
it is not the same failure.

Source: [softwarefinder.com buyer-fatigue study](https://softwarefinder.com/resources/software-decision-fatigue)
(primary). Downgrade reason: sector mix is HR, LMS and EHR rather than
developer tools, so transfer is inference.

### F9. The closest analogue to this catalogue plateaus at 10% [moderate]

Backstage reached 96% adoption inside Spotify, where the platform team built it
to solve their own documented pain. External adopters typically **plateau
around 10%**, attributed to treating it as a catalogue rather than a
self-service workflow system. Separately, 64% of engineers have been observed
bypassing internal developer platforms they were meant to use, attributed to
setup complexity and autonomy concerns rather than documentation gaps.

The relevance is direct: this repository publishes a catalogue, and the
documented failure mode of the nearest comparable is being *treated as* a
catalogue.

Sources: [DX newsletter](https://newsletter.getdx.com/p/backstage-and-the-developer-portal-market)
(primary; DX sells developer-experience tooling — incentive flagged),
CNCF survey. Downgrade: the 10% figure is widely cited but traces to one
analyst newsletter.

### F10. Mandated platforms underperform user-centric ones [moderate]

DORA 2024 finds user-centric platforms outperform mandated platforms. This is
the strongest counterweight to a purely top-down reading of F3: the route is
narrowing, but forcing adoption from above is not the answer either.

Source: DORA 2024 via [Frontiers multivocal review](https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2026.1814498/full)
(secondary citation of a large annual practitioner survey).

---

## Claims under test — verdicts

**Claim A — the blocker is explanatory.** *Unsupported as a primary cause.*
Organisational and cultural factors rank first (F4); the specific failure the
intent names is undocumented (F5); and it is absent from the measured
abandonment causes (F8). Explanation remains a real secondary factor at the
evaluation stage (F6).

**Claim B — one artifact can serve several stakeholders.** *Split, and the
split is the finding.* One coherent mental model with role-appropriate entry
points is defensible for the influencer tier. It is **not** sufficient for
gatekeepers, who demand structurally different evidence — a TCO model, an exit
path, an SBOM, DORA deltas (F1). Those are not entry points into a diagram;
they are separate artifacts. Note the counter-pressure: most sources advocating
role-specific collateral are sales-enablement vendors who profit from
collateral proliferation, so the *degree* of differentiation is contested even
though its necessity is not.

---

## Discarded — widely repeated, unsourced

Three figures appear across practitioner writing with no traceable primary
source. None should enter a repository artifact:

- "Developers evaluate a README in 30 seconds" — a propagated heuristic; no
  eye-tracking or session study supports a threshold.
- "First API call within 10 minutes converts 3–4×" — unattributed everywhere it
  appears.
- "73% of deals die from champion failure" — appears in consultancy content
  with no primary citation.

---

## Known unknowns

- **Known-unknown:** what *this* estate blocks on. Prior art establishes what
  comparable organisations did, never what a specific adopter will do. Would be
  closed by: interviews across the gatekeeper tier, not the champion alone.
- **Known-unknown:** whether a context-level diagram measurably helps a
  non-architect evaluate. Would be closed by: a controlled comparison, which
  F7 shows nobody has published.
- **Known-unknown:** base rates for bottom-up versus top-down success by tool
  class. The DORA and Puppet data cover DevOps practice broadly, not specific
  tool adoption.
- **Unknowable from published sources:** documented cases of a security or
  legal team formally vetoing a platform. Post-mortems record stalls, not
  vetoes — organisations do not publish their refusals, so the absence is
  structural rather than evidential.

---

## Evidence-class notes

Three retrievals ran independently and agreed on F1–F4, which is the
triangulation that carries the bottom line. Vendor incentive is flagged on
every source that has one — HashiCorp, Backstage, Roadie, DX, Pulumi, LeanIX,
IcePanel and the sales-enablement corpus all sell into the problem they
describe. The Go case is flagged stale at 14 years. Two sources returned 403
and are cited only through search summaries, marked as such above.
