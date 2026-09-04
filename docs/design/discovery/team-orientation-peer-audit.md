# Peer audit — how others teach an operating model

> Discipline: applied (practitioner-pattern survey)

Comparative audit for the cohort-orientation redesign. Three questions: how peers
render two orthogonal lifecycles on one page; what governs a hand-crafted
explanatory graphic as an above-the-fold centrepiece; and what actually enables a
champion to transfer understanding to a budget holder.

Confidence tags are `[high]` / `[moderate]` / `[low]` / `[uncertain]`, with the
applied overlay: no peer-review penalty for practitioner sources, and
`survivorship bias` and `stale prior art` added as downgrade factors. Under the
practitioner-independence rule, sources from one vendor, one employer cohort, or
one re-blogged original count as **one** source. Claims no single source states
are tagged `[synthesis]` or `[inference]`.

Retrieval ran 2026-09-04 across three parallel sub-questions.

---

## Part 1 — Two lifecycles on one page

### F1. Subordination is the established pattern; peer presentation is not `[moderate]`

Nesting one lifecycle inside a stage of the other, rather than showing both at
equal weight, is what the corroborated prior art does.

Nielsen Norman Group is explicit that designers should avoid requiring users to
hold multiple conflicting mental models, and that the remedies are to align to
the reader's single existing model or to teach **one** accurate model — not two
([NN/g, Mental Models](https://www.nngroup.com/articles/mental-models/)). The
industry's named version of the pattern is the **inner loop / outer loop** split,
where the developer's edit-run cycle executes many times inside one iteration of
the deploy-observe cycle, and the two interface at a single handoff rather than
sitting side by side ([Red Hat Developer, Sep 2024](https://developers.redhat.com/articles/2024/09/05/platform-engineers-role-devsecops-inner-and-outer-loops)).
The C4 model formalises the same move for system diagrams: four zoom levels where
each is a subordinated drill-down, on the stated principle that different levels
tell different stories to different audiences ([c4model.com](https://c4model.com/introduction)).

Three independent sources. **Downgraded from `[high]`** because no controlled
study measures whether subordination changes comprehension or conversion on a
landing page; all three sources establish the pattern, none measures the outcome.

### F2. Two disclosure levels is the ceiling `[moderate]`

NN/g's progressive-disclosure guidance states that designs beyond two disclosure
levels typically have low usability, because users get lost moving between
levels, and distinguishes *staged* disclosure for linear sequences from
*progressive* disclosure for hierarchical access — different mechanisms, not
interchangeable ([NN/g, Jul 2022](https://www.nngroup.com/articles/progressive-disclosure/)).

**Downgraded** for single-source: NN/g is the canonical authority here, but no
independent replication was located. Treated as a hard design bound anyway,
because the cost of being wrong is high and the cost of complying is nil.

**Direct consequence for this engagement:** the canvas gets exactly two levels —
the adoption spine, and the work detail inside one station. There is no third
level. Anything that would need one goes to the documentation surface.

### F3. Peer presentation forces two chunk-sets; nesting collapses them into one `[inference]`

Working memory holds roughly 7±2 *chunks*, and chunking related information into
meaningful units reduces the number that must be held at once. Applied here: two
peer process models require two independent chunk-sets simultaneously, while
subordination yields one chunk-set with internal structure.

Explicitly marked `[inference]`. The retrieval found no source applying Miller's
Law or cognitive-load theory to the dual-lifecycle landing-page case; general UX
applications cover navigation items and form fields. This is the mechanism behind
F1, and it is our reasoning, not a cited finding.

### F4. Counter-evidence: the best-documented resolution is to eliminate the duality `[moderate]`

Stripe's answer to the dual-audience problem was to collapse it — choose
developers as the single primary audience and structure everything around them,
trusting that developers influence the purchase ([Foundation Inc analysis](https://foundationinc.co/lab/stripe-content-marketing),
independent, not vendor self-reporting). HashiCorp's Tao page resolves a
developer/operator split by abstracting to a higher common level so neither
appears as a separate narrative ([hashicorp.com](https://www.hashicorp.com/en/tao-of-hashicorp),
vendor). dbt's Analytics Development Lifecycle subordinates one lifecycle under
the established SDLC framing to borrow its legitimacy ([dbt Labs, Sep 2024](https://roundup.getdbt.com/p/announcing-the-analytics-development),
vendor).

This is recorded as counter-evidence to our own decision, because it is the most
robustly documented approach found and we are not taking it. Our justification is
that the two lifecycles here are genuinely orthogonal — one acts on a piece of
work, the other on a team — so collapsing them would misrepresent the product.
**That justification is our assertion, not a finding.** If it is wrong, Stripe's
route is better evidenced than ours.

The dbt precedent is the closest usable analogue: subordinate, and borrow
legitimacy from a framing the reader already has.

### F5. The vocabulary we have been using is not a named anti-pattern `[high]`

Three independent retrievals failed to find "two pages stapled together",
"diagram soup", or "competing diagrams of equal weight" as named anti-patterns in
the NN/g, Baymard, or academic IA literature. "Diagram soup" appears in one
GitHub skill file with an unsourced heuristic. The general landing-page
literature warns about multiple CTAs and unfocused content without naming a
dual-lifecycle variant.

The nearest documented case is NN/g's account of the University of Michigan
Library's two simultaneous search bars: readers expect search to be universal, so
two of them confuse even when distinctly labelled — and the recommendation is not
to introduce the duality at all ([NN/g, Mental Models](https://www.nngroup.com/articles/mental-models/)).

**Consequence:** "two pages stapled together" is the owner's phrase and ours. It
is a good description of a real risk. It must not be cited as an established
anti-pattern in any artifact that leaves this engagement.

### F6. Polyhierarchy conflicts with breadcrumbs `[moderate]`

A page that belongs under multiple parents fights breadcrumb navigation, which
can show only one canonical path; NN/g recommends faceted search instead for
deeply overlapping hierarchies ([NN/g, Polyhierarchies](https://www.nngroup.com/articles/polyhierarchy/)).

Relevant to the proposed job-grouped documentation sidebar: several guide areas
serve more than one job, so a job grouping is a polyhierarchy waiting to happen.
Either accept one canonical placement per area, or reach for faceting.

---

## Part 2 — The explanatory graphic

### F7. GitHub's Markdown sanitiser removes almost all SVG presentation `[high]`

Stripped: `<script>`, inline `style=`, `class=` and `id=` on SVG elements,
`<foreignObject>`, CSS `@import`, event attributes — and, critically, a `<style>`
block **inside** the SVG is not reliably preserved. Surviving: basic shapes,
`<text>`, `<path>`, `<rect>`, `<circle>`, `<g>` with `transform`, `<defs>`,
`<marker>`, `<linearGradient>`, and per-element `fill` and `stroke` attributes.
For `<img src="*.svg">` in Markdown, no animation of any kind plays — SMIL, CSS,
and JS all fail ([GitHub community discussion](https://github.com/orgs/community/discussions/151372),
corroborated by the responsive-SVG and accessibility sources below).

**This is the binding constraint on the canvas.** All presentation must live in
element-level attributes. No stylesheet, no classes.

**Verification owed.** This claim governs a deliverable, so it should be proved
by rendering a probe SVG in a real README rather than accepted from documentation.
Recorded as a build-handoff verification step, not treated as settled.

### F8. SVG cannot be a link-preview image; the text payload matters more than the picture `[high]`

No major platform accepts SVG as an `og:image` — Slack, Teams, Discord,
WhatsApp, Telegram, and Twitter/X all require raster. The safe format is
1200×630 under 1 MB, with WhatsApp soft-capping near 300 KB
([env.dev, 2026](https://env.dev/guides/opengraph-image-sizes)).

More useful: **Slack fetches only 32 kB of the page** — the most restrictive of
the major platforms — so `og:title` and `og:description` are the mandatory
payload, and without them the recipient sees a bare URL. `twitter:label` and
`twitter:data` surface up to two extra contextual fields in Slack, which is the
only mechanism for signalling what a link is and what it costs to read before
anyone clicks ([whitep4nth3r](https://whitep4nth3r.com/blog/level-up-your-link-previews-in-slack/)).

**This reorders our own priority.** We had treated the unfurl as needing a raster
export of the canvas. The evidence says the *text* is what does the work in a
chat channel, and the image is secondary. The champion-transfer surface is
therefore three meta tags plus a raster, not a picture.

### F9. The accessible pattern for a meaning-bearing diagram `[high]`

`role="img"` with `aria-labelledby` referencing **both** a `<title>` and a
`<desc>`; `role="img"` suppresses inconsistent traversal into SVG internals. For
a complex diagram `<desc>` alone is impractical, and the current recommendation
is a disclosure widget — an expandable inline transcript navigable by screen
reader, associated with `aria-describedby`. The `longdesc` attribute was
deprecated in HTML 5.1 and must not be used ([Deque, 2024](https://www.deque.com/blog/creating-accessible-svgs/);
[A11Y Collective, Jul 2025](https://www.a11y-collective.com/blog/svg-accessibility/);
[CSS-Tricks](https://css-tricks.com/accessible-svgs/) — flagged `stale prior art`
at 10 years old, corroborated by the two current sources).

Applicable success criteria: **1.1.1** — a complex diagram carrying information
absent from adjacent text needs a real text alternative, and a short `<title>`
does not satisfy it; **1.4.1** — colour-carried meaning needs shape, label, or
pattern too; **1.4.3** — text inside the SVG meets the same contrast ratios as
page text; **2.2.2** — animation over five seconds must be pauseable, which our
static decision makes moot.

Hand-crafted SVG with explicit ARIA outperforms generated SVG; no diagram tool
has fully solved assistive-technology support for its output. That is independent
corroboration for the engagement's rejection of a Mermaid conversion.

### F10. `viewBox` scaling alone is a named near-universal failure `[moderate]`

Shipping a wide SVG with `preserveAspectRatio` only produces illegible text on a
phone — described as an observed near-universal failure mode on technical SaaS
landing pages, not a hypothesis. SVG-internal media queries have patchy browser
support, and would be stripped by GitHub in any case. The robust strategy is
**replace-at-breakpoint**: below a defined width, hide the diagram and render a
semantic list or prose instead ([12 Days of Web, 2023](https://12daysofweb.dev/2023/responsive-svgs/);
LogRocket; practitioner consensus).

**Downgraded** for weak independence — these sources sit close together in the
same practitioner cohort.

**The useful convergence:** replace-at-breakpoint requires the diagram's
information to exist in parallel textual form, which is exactly what WCAG 1.1.1
requires. One artifact satisfies both. Build it once.

Staged reveal — showing part of the diagram at a time on scroll — is frequently
proposed and rarely works in a hero, because it prevents the reader forming a
model of the whole before engaging with parts.

### F11. Metaphor is the load-bearing layer; polish before metaphor is the failure `[moderate]`

Maggie Appleton's framework runs metaphor → drawing → composition → colour, with
the source-to-target metaphor mapping doing the work and everything above it
elaboration; failed diagrams invert this, adding colour and finish before the
metaphor exists ([maggieappleton.com](https://maggieappleton.com/drawinginvisibles1)).
Distill's analysis of interactive articles converges on multiple representations
serving different thinking modes, and on overview-first-then-details-on-demand as
information hierarchy ([Distill, 2020](https://distill.pub/2020/communicating-with-interactive-articles/)
— flagged: the publication paused in 2021, authoritative on fundamentals,
potentially stale on tooling). Julia Evans's zine practice holds every panel to
exactly one question, with "explain everything in one panel" as the anti-pattern.

**Consequence:** name the canvas's metaphor before drawing anything. We do not
have one yet. That is the first task of the canvas design, not a later refinement.

### F12. Architecture-diagram idiom fails on a persuasion surface `[moderate]`

The C4 FAQ is explicit that its audience is engineers and engineering managers
needing a common language for a system that exists ([c4model.com/faq](https://c4model.com/faq)).
Appleton names the cost directly: unfamiliar symbols and interface patterns
confuse, and boxes-and-arrows routing produces visually chaotic layouts —
"spaghetti wires" as automatic failure. The reader spends effort parsing notation
instead of absorbing meaning.

Independent corroboration for the engagement's rejection of `architect-diagram`
as the wrong genre.

### F13. Named failure modes to design against `[synthesis]`

Chartjunk — decoration carrying no information, which for a hero diagram means
gradient fills, drop shadows, and category-indexing icons that encode no
relationship. Spaghetti wires. Abstraction-level mismatch — mixing business value
and implementation detail in one frame. Metaphor inversion. Every-concept-in-one-panel.
Wide-diagram mobile failure. No static fallback — works where authored, strips to
nothing in a sanitised pipeline, so the page looks broken exactly where many
developers first meet it. Semantic void — the diagram is the sole carrier of
information and has no `<title>`, no `<desc>`, and no `aria-hidden`, so a screen
reader emits silence or path coordinates.

Note one live dispute: Tufte's data-ink ratio is contested in current practitioner
writing on the grounds that maximising data-ink can strip redundant cues that
accessibility needs ([Frank Elavsky, Apr 2025](https://www.frank.computer/blog/2025/04/data-to-ink.html)).
The reconciliation we adopt: apply data-ink reasoning to information density —
cut chartjunk — but not to encoding redundancy, where WCAG 1.4.1 requires the
redundant cue.

---

## Part 3 — Champion transfer

### F14. Cohort adoption runs on peer usage, and champions add contextualisation rather than demonstration `[high]`

The strongest evidence in this audit, and the only part of it that is independent
academic work.

An independent study of individual and team drivers of developer AI-tool use
found usage patterns clustering *within* teams, indicating collective
sensemaking; individuals in identical team contexts showed very different
patterns, and those with sharing structures showed positive momentum that
isolated learners did not. Champions' contribution was step-by-step
contextualisation into team-specific workflows — sharing failures as well as
successes — not demonstration. Peer influence operated through informal
micro-interactions accumulating over time. The study also names a **Productivity
Pressure Paradox**: organisations expected immediate gains without protecting
learning time, and developers reverted to familiar methods under deadline
([arXiv 2507.21280, Jul 2025](https://arxiv.org/html/2507.21280)).

A Microsoft study of Claude Code and Copilot CLI adoption across thousands of
engineers found the strongest predictor of trying a tool was peer usage in the
skip-level peer group — **+216% higher odds** where more than a quarter of that
group had adopted — with manager usage raising subordinate odds by 82%
([arXiv 2607.01418, 2026](https://arxiv.org/html/2607.01418v1)).

An independent practitioner survey of ten technology companies captured the
champion's credibility gap verbatim: *"My engineering org is getting hooked on
AI, but execs want metrics on value-add. I don't want to push vanity metrics just
to justify spend, but outside of vanity metrics, I have nothing of value to
show."* ([Pragmatic Engineer, 2024](https://newsletter.pragmaticengineer.com/p/measuring-ai-dev-tools))

Three independent sources, two peer-reviewed preprints. **This grounds the
engagement's cohort premise in evidence rather than assumption**, and it
corroborates our observed pasted-link behaviour: peer micro-interaction is the
mechanism, and a link in a channel is a peer micro-interaction.

It also sharpens the budget-holder persona. The champion's problem is not that
they lack enthusiasm; it is that they have nothing credible to show.

### F15. Adoption predictors are not retention predictors `[moderate]`

The same Microsoft study found the factors predicting initial adoption differed
from those predicting persistence: engineers with prior IDE Copilot experience
tried CLI tools at higher rates but retained them at lower rates, because
established tool loyalty created switching barriers rather than openness.

**Downgraded:** single source, internal to one employer, and its Claude Code
series was truncated when licences were discontinued company-wide mid-2026, so
sustained-adoption data is incomplete.

**Consequence for the measurement plan:** one metric cannot serve both. The
adoption target and the retention target need separate instruments, and the
existing journey's TTFV and 30-day-retention pair is the right shape.

### F16. Counter-evidence: generic collateral fails, and each stakeholder needs different proof `[low]`

Practitioner sales-enablement writing converges on a per-stakeholder bundle: a
one-pager in the buyer's language, a business-case template the champion fills in
so it reads as internally authored, role-specific proof points (cost avoidance
for finance, workflow impact for the VP, risk framing for IT), and an
objection-response script. "Generic collateral" is named as the failure. One
source specifies the one-pager structure concretely: Problem / Impact / Proposed
solution / Expected outcome / Implementation summary / Required stakeholders /
Next step.

**Downgraded to `[low]`:** every source is a vendor or a sales consultant with
client-acquisition incentives, and `survivorship bias` applies — only successful
adoptions get written up. No independent audit of which artifact type actually
converts champion enthusiasm into funded adoption was located.

**This is a genuine tension with our design decision** and is recorded as such.
Our personas artifact argues one canvas serves all four readers through four
entry points. This body of practice says one artifact for four stakeholders
fails. The reconciliation we propose — the canvas is the shared *model*, while the
per-audience answers are entry points into it, not separate collateral — is
plausible and untested. It should be a question at the aesthetic-direction gate,
not a settled point.

### F17. The anti-pattern we are fixing is not named anywhere `[high]`

"A landing page optimised for self-serve signup when the real conversion event is
a funded team rollout" is implied across the product-led-growth literature — the
user-is-not-the-buyer pathology is well described — but no located source names it
as a discrete anti-pattern.

The nearest named thing is **"narrative vacuum"**: the assumption that a clean
product experience replaces a narrative, when *"a dashboard does not communicate
architectural philosophy or strategic fit"* ([GTM Delta](https://gtmdelta.com/why-plg-fails-without-technical-storytelling-and-what-to-fix-first/)
— vendor-adjacent consultant, `[low]` on its own).

### F18. The explain-it-back check has no software precedent `[moderate]`

Teach-back — asking someone to restate what they have understood — is an
established comprehension-verification method, and the retrieval found its
literature **entirely within healthcare**. No academic or practitioner source
applying it to software rollout comprehension was located.

**Consequence:** the engagement's Gap D is not only a gap in our packs; it is a
gap in the practitioner literature. Our five-question check should therefore be
labelled as adapted from healthcare teach-back rather than presented as a
standard practice, and its design should carry the caution that teach-back
protocols in healthcare are administered by a trained practitioner, which a
self-serve web check is not.

### F19. Rollout shape: small cohorts, advocates first, no early all-hands `[low]`

GitHub's own guidance runs a small interested cohort → pilot-group advocates
willing to lead training → a team onboarding sprint pairing developers on real
codebases → sprint-retrospective feedback loops. One vendor-adjacent source
recommends cohorts of three to five developers, one per week. Named anti-patterns:
the **early demo trap** — all-hands visibility before champions are established,
after which engagement wanes because business priorities win — and **incomplete
transition** — social proof without documentation, leaving teams able only to
mimic the champion's configuration.

**Downgraded to `[low]`:** vendor documentation and vendor-adjacent consultants
throughout; no independent measurement.

Note the alignment with the existing adoption journey's own rollout-playbook gap,
which describes the same failure from the inside.

### F20. The champion is a single point of failure and the mitigations are weak `[low]`

Practitioner sources name "the internal champion leaves and the system has no
documented owner" as a primary rollout failure, and recommend multithreading —
engaging several people so one departure does not reset to zero. The
documentation-based mitigations are procedural, and one source concedes they are
insufficient.

**Downgraded:** practitioner-only, undated, and no post-mortem of a cohort
adoption that failed this way was found — a `survivorship bias` gap rather than
absence of the phenomenon.

**Consequence:** it is an argument for the documentation surface carrying the
transferable map, so the champion's competence is not the only copy. That is
documentation journey Stage 5's pain, independently arrived at.

---

## Known unknowns

- **Known-unknown:** does subordinating one lifecycle inside another measurably
  improve comprehension on a landing page? Would be closed by a comprehension
  test on two variants — the explain-it-back check applied as an A/B, which is
  within this project's reach.
- **Known-unknown:** which champion-enablement artifact actually converts
  enthusiasm into funded adoption? Would be closed by independent research; every
  located source has an incentive.
- **Known-unknown:** does our own canvas survive GitHub's sanitiser? Would be
  closed by rendering a probe SVG in a real README. Owed at build handoff.
- **Known-unknown:** how many simultaneous process models can a reader sustain on
  one page? Would be closed by primary research; NN/g's two-level disclosure
  ceiling is the nearest proxy and is about disclosure depth, not model count.
- **Unknowable:** whether the pasted-link behaviour we measured is champion
  transfer or something else. Why not: the traffic API reports a referrer and a
  count, never an intent. Only the champion interview can distinguish them, and
  even then for one person.
- **Unknowable:** whether cohort adoption here would have persisted absent
  intervention. Why not: the counterfactual cannot be run, and the one large
  study that came closest had its series truncated by an unrelated licensing
  decision.
- **Unknowable, contested:** whether Stripe's collapse-the-duality approach or
  our subordination approach is right for this product. Why not: it turns on
  whether the two lifecycles are genuinely orthogonal, which is a judgement about
  our own product that no external evidence settles. Recorded as a tension, not
  resolved.

## What changed in our design because of this audit

1. **The canvas gets exactly two levels.** F2. No third.
2. **Name the metaphor before drawing.** F11. It is the first task, not a later
   refinement, and we do not have one yet.
3. **The chat-transfer surface is three meta tags plus a raster, not a picture.**
   F8 reorders our own priority — Slack reads 32 kB and shows text.
4. **Replace-at-breakpoint and the screen-reader alternative are one artifact.**
   F9 and F10 converge.
5. **All canvas presentation moves into element-level attributes.** F7.
6. **The cohort premise is now evidence-backed, not assumed.** F14, with two
   independent preprints.
7. **Adoption and retention get separate metrics.** F15.
8. **"Two pages stapled together" stops being cited as a named anti-pattern.**
   F5. It is our phrase for a real risk.
9. **The one-canvas-for-four-audiences decision is now an open question at the
   next gate,** not a settled one. F16.
10. **The explain-it-back check gets labelled as adapted from healthcare
    teach-back,** with the practitioner-administered caveat. F18.
