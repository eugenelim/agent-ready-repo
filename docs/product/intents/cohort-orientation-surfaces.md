# Cohort orientation across the marketing and documentation surfaces

- **Status:** Draft

## Outcome

An adoption champion can understand the whole AI-supervised operating model
from the published surfaces and re-explain it accurately **to an engineer and a
platform team** — without improvising.

**Narrowed 2026-09-10, on the de-risk.** The outcome previously named a budget
holder as a third audience. It no longer does. Prior art puts budget holders,
architecture review boards, security and procurement in a **gatekeeper** tier
that demands a three-year TCO, an exit path, an SBOM, a data-flow diagram and
DORA deltas — evidence types no explanatory artifact carries. Claiming to serve
them by explaining the model better was an overclaim, and the surfaces here
cannot discharge it. What the evidence supports is the **influencer** tier — engineers, tech leads
and platform teams — where documentation is relied on during evaluation at
moderate confidence (see the survey's F6 and its stated scope limit).

Concretely, the surfaces stop asking a reader to assemble the relationships
themselves. The marketing home leads with one artifact that carries the whole
model; the documentation surface leads with the ordered paths it already
publishes and groups its navigation by the reader's job; and the **marketing**
surface describes the human decision points in the words a person would use
rather than in internal gate identifiers.

**Scoped to marketing on the gate-identifier clause, deliberately.** The
documentation surface publishes 94 gate-code occurrences across 14 files in
`guides/`, one of which defines them as reader-facing vocabulary. Those are out
of this boundary, so a both-surfaces claim would be unachievable — see Boundary.

**Falsifier.** The outcome is achieved when a reader **in the influencer tier**
who has seen only these surfaces can explain the model back. A gatekeeper who
can also explain it back has not been served by that alone, and a gatekeeper
who cannot is outside this outcome rather than a failure of it. It is *not* achieved by shipping any
particular composition — the nesting of the work lifecycle inside one adoption
station is an inherited design decision with its own recorded kill condition,
not part of this outcome.

## Addition 2026-09-10 — the canvas ships light and dark, via `<picture>`

**Decided by the owner, 2026-09-10.** The canvas carries a dark variant.

**Mechanism, measured not assumed.** An `<img>`-embedded SVG gets no host
cascade, so it cannot follow a reader's colour scheme on its own. `<picture>`
with `prefers-color-scheme` sources is the answer, and it survives GitHub's
sanitiser intact — probed 2026-09-10 via `gh api --method POST /markdown` in
`gfm` mode, which returned the `<picture>` element with both `<source>` tags,
both `media` queries and both `srcset` values preserved. The same element works
unchanged on the Astro and Starlight surfaces, which apply no sanitiser. One
construct therefore serves every surface the canvas appears on.

**Both variants come from the token source.** This intent already records why:
"Generate the canvas SVG from the token source — decay control. A hand-authored
snapshot diverges from the palette silently and nothing fails." Hand-forking a
dark copy of an existing light SVG reintroduces exactly that decay, doubled —
two snapshots drifting from one palette. The generator emits both, or neither
is trustworthy.

**Known constraint.** Inline SVG is removed outright by GitHub's sanitiser, so
the README surface has no fallback below `<picture>`; there is no degraded
inline path to fall back to. The site surfaces are unaffected.

## De-risk 2026-09-10

### Reversibility triage — mixed, and that is itself the first finding

This intent bundles two door types, which is why it reads as one bet and is not.

| Component | Door | Why |
| --- | --- | --- |
| Marketing home structure and copy, guides index navigation | **two-way** | Copy and layout; revert is a commit. No consumer depends on them. |
| The canvas as a portable artifact | **two-way** | A generated asset. Regenerate or withdraw. |
| Removal of eleven rendered gate identifiers | **one-way-ish** | Public vocabulary. Readers and external links may already use those identifiers; removing them is a visible contract change. |
| Amendment to the **Shipped** `guides-sidebar-generation` spec | **one-way** | A Shipped contract whose data model pins `[[guide_groups]]` to `dir` + `label`. Adding a `job` field changes a published structure, and 209 guide pages route through it. |

**Structural de-risk available with no experiment.** The two-way components can
ship and be judged without touching either one-way component. Sequencing the
reversible surfaces first turns one large bet into a cheap probe followed by a
committed change — and the cheap probe produces the very evidence the committed
change needs. This costs nothing and does not wait on anything.

### Riskiest assumption — **revised 2026-09-10 against prior art**

The first pass named this as "explanatory versus commercial blocker" and routed
it to a champion interview. That instrument was wrong: the estate is
multi-party, and one champion can report their own experience of a blocker but
not an architect's veto or a budget holder's silence. Prior art can answer most
of it without the interview, and
[the platform-adoption survey](../research/platform-adoption-evaluation-survey.md)
now does.

**Restated target:** that a *shared mental model* is what this estate is
missing — when the documented gap for the people who can say no is
*role-specific evidence* no single explanatory artifact carries.

**What the evidence establishes.** The estate is two-tier. Influencers
(engineers, tech leads, platform teams) advocate and cannot approve;
gatekeepers (architecture review board, security, procurement, budget holders)
hold the veto and demand a three-year TCO, an exit path, an SBOM, a data-flow
diagram and DORA deltas. Enterprises allowing engineer-selected tools in
production fell to 11% from 38% in six months, with dev-tool deal cycles
running 6.5 months across seven or more decision-makers. The champion still
initiates; they no longer close.

### Kill condition — **superseded**

The original bar — "kill if explanation is not raised unprompted by a majority"
— was mis-specified twice over. A majority across mixed roles is a meaningless
aggregate when roles have different blockers, and the bar has now been answered
from prior art rather than from this estate.

**Result against the original line: the explanatory framing does not survive.**
The top-ranked adoption blocker is organisational at 47%; "I cannot re-explain
it" is documented nowhere; and it is absent from the measured abandonment
causes, where the nearest — stakeholder misalignment at 16% — ranks fourth.

### Verdict — **partially killed, and reframed**

Not a clean kill. The evidence cuts the intent in two along a line it did not
draw.

**What survives.** A moderate-confidence peer-reviewed study found that 91.18%
of practitioners using Sphinx/ReadTheDocs relied on documentation when making
adoption decisions. Applying that to these surfaces is an inference, not a
transfer. It supports *testing* an influencer-tier comprehension bet; it does
not establish that this redesign improves evaluation. A shared mental model with
role-appropriate entry points is defensible for them. DORA 2024's finding that
user-centric platforms outperform mandated ones also supports the packet's
self-serve instinct.

**What does not.** The former budget-holder outcome treated influencer
comprehension and gatekeeper approval as the same need. Gatekeepers require
separate evidence — TCO, exit path, security artifacts — that no canvas
carries. Platform teams **remain** in the influencer-tier comprehension
outcome, but their before/after DORA deltas are a separate adoption-evidence
need outside this intent, and this outcome does not claim to satisfy it.

**And the centrepiece is unmeasured.** No empirical research exists on whether
architecture diagrams shorten evaluation or move non-architect audiences. C4's
audience tiering is design rationale, not measured outcome, and its most
detailed source sells C4 tooling. That is an absence rather than a refutation —
the canvas may work, and nothing published shows that it does.

**The nearest analogue's failure mode is ours.** Backstage reached 96% inside
Spotify and plateaus near 10% externally, attributed to being treated as a
catalogue rather than a self-service workflow. This repository publishes a
catalogue.

### What this changes

1. **Narrow the outcome to the influencer tier.** Claim comprehension and
   first-value for engineers, tech leads and platform teams — where the
   evidence supports it — and stop claiming the budget holder.
2. **Name the gatekeeper artifacts as out of scope, explicitly.** TCO, exit
   path, SBOM and data-flow are real requirements with no owner here. Silence
   reads as coverage.
3. **Hold the canvas as a bet, not a conclusion.** It is unmeasured, and it is
   the largest single investment in the packet.
4. **The two-way-first sequencing already recorded above is now better
   supported**, because the influencer tier is exactly what the reversible
   surfaces serve.

### Validation hook — revised

```
validation_hook:
  assumption: after using only the reversible surfaces, an influencer-tier
    reader can explain the operating model accurately
  kill_condition: on the release candidate or in the next-cohort M2 check, any
    M2 item is partial or absent for an intended influencer role
  activity: administer M2 to influencer-tier readers on the release candidate,
    with the next cohort, and after any material change to the model or
    vocabulary
```

**Required model relationships — the answer key.** The bar is only testable if
the required set is enumerated, so it is: (1) the eight work steps in order;
(2) the three human decisions and what each decides; (3) the five adoption
stations in order, with the work lifecycle nested inside station two; (4) the
repository as source of truth with a one-way outbound tracker projection; and
(5) no autonomous approval, merge, or production ship. An item is `correct`
only when every concept listed for it is present; otherwise it is `partial` or
`absent`.

**Why the bar is absolute, not a delta.** The earlier hook said "comprehension
does not improve", which is unfalsifiable now: the pre-redesign baseline died
with the champion interview, so improvement is unknowable. An absolute bar —
can a reader express each required relationship — is testable without a
baseline.

**The champion interview is retired, 2026-09-10 — owner decision.** It was the
de-risk instrument and it is no longer defensible as one. Enterprise adoption
dynamics are well characterised: the estate's structure, its sequence, the
evidence each role demands, and the ranking of organisational over explanatory
blockers are all `[high]`-confidence findings triangulated across three
independent retrievals. Running a single interview to re-derive settled
knowledge is theatre, and the survey's own F8 makes the cost concrete —
evaluations already run four months with 65% abandonment, so a gating activity
adds latency to a process whose documented failure mode is latency.

**What dies with it, stated plainly.** The M2 explain-it-back metric loses its
pre-redesign baseline permanently. A later score will describe comprehension
but cannot demonstrate improvement. That is accepted: the baseline was worth
having, not worth gating on, and the heuristic baseline already recorded in the
design packet plus the five-second-scan hook can be run against the current
surfaces by anyone at any time.

Desk-grounding is not validation, and this intent still carries an untested
claim: that the reversible surfaces improve comprehension for the influencer
tier. That is now tested by shipping them, not by interviewing ahead of them.

## Boundary

**In:** the marketing home page's structure and copy; two new marketing pages
(the operating-model canvas as a portable artifact, and an internal-case route);
the documentation guides index and its navigation model; and the removal of the
**eleven rendered gate identifiers in two marketing components** —
`HumanGates.astro` (six) and `ThreeLoops.astro` (five). Also in: the canvas's
`README.md` rendering and the probe that verifies it, because that rendering is
what defines the canvas's contract.

**Explicitly out — the first-value doors.** The terminal and Claude-apps
first-value doors, the public navigation into the no-terminal route, and that
route's copy are owned by
[`claude-apps-first-value-entry`](claude-apps-first-value-entry.md). An earlier
2026-09-10 addition placed them here on the grounds that this intent owns the
marketing home's structure; that was ownership by *surface* where the
repository resolves by *outcome*, and this intent's surviving outcome is
comprehension, not reaching first value. Removed rather than duplicated.

**Explicitly out — the Shipped-spec premise correction and the palette gap.**
Correcting `guides-sidebar-generation`'s stale directory-fallback premise, and
remediating the broader pre-existing marketing-palette gap, are not required to
satisfy this outcome. Capture either separately only if the owner requests it.

**Explicitly out — the gatekeeper evidence set.** Named here because silence
reads as coverage. A three-year TCO, a risk-adjusted ROI, an exit or migration
path, a failure-mode analysis, an SBOM and CVE posture, SOC 2 / SSO / audit-log
claims, a data-flow diagram, licence-compatibility and indemnification terms,
and before/after DORA deltas are all real requirements of the roles that hold
the veto. **None of them is in scope here, and none has an owner.** They are
not entry points into the canvas; they are separate artifacts with separate
evidence standards. An adopting organisation whose architecture review board or
security function blocks on these will not be unblocked by anything this intent
ships.

**Also in, each on its own recorded basis** — not on one universal claim:

| Item | Why it is in |
| --- | --- |
| Amend the Shipped `guides-sidebar-generation` spec with the `job` field | **The outcome is unreachable without it:** its data model pins `[[guide_groups]]` to `dir` + `label`, so job grouping cannot be expressed. The stale directory-fallback premise in that same spec is a real defect but is **not** required by this outcome, and riding it along would make this intent's completion depend on unrelated contract correction — see the exclusion above. |
| Generate the canvas SVG from the token source | **Decay control.** A hand-authored snapshot diverges from the palette silently and nothing fails. |
| Raster export for link previews | **Link-preview validity** — no platform accepts SVG. Note the packet corrected its own emphasis here: the text payload does more work than the image, so this is required but not the centre of the transfer surface. |
| Contrast check for the marketing palette | **An owner-approved accessibility control** closing a pre-existing gap, not a consequence of this outcome. The canvas is simply the first element to walk into it. |

**Out:**

- **Restructuring `README.md`.** Its highest-traffic status is why this is
  tempting; the canvas's rendering there is separately In, above.
- **The 94 gate-code occurrences across 14 files in `guides/`**, including one
  explanation page that defines them as reader-facing vocabulary. A content
  programme, not a redesign. This is why the outcome's gate-identifier clause is
  scoped to marketing.
- The pack catalogue, journey pages, and `/now/`.
- The nine generated content files carrying 12 gate-code occurrences, fixable
  only at their `packs/*/JOURNEY.md` sources. **One of them,
  `web/src/content/packs/iac-terraform.md`, is also in the adjacent intent's
  scope** — see unresolved question 2.
- Writing tutorials for the ten guide areas that have none.
- **Moving the job taxonomy into `site.toml`.** Not merely "separable": the
  taxonomy has two homes today — a marketing-only TypeScript module and a
  Markdown table — and their pack membership has **already drifted in three of
  seven rows**. The In-scope re-grouping consumes those same seven names, so
  which home governs membership must be answered even though the consolidation
  is out.
- **`agent-skill-engineering` is named in the job taxonomy with no guide
  directory**, which interacts with the spec rule requiring an entry per
  directory. The taxonomy's owner decides.

**Not a boundary change but worth stating:** no file under `web/`, `docs-site/`,
`guides/`, `site.toml`, or `packs/` was changed by the design session.
Everything upstream of this intent is specification.

## Owner

eugenelim.

**Decisions this owner cannot make alone**, each named in the source with a
different holder: the scope of ADR-0020 (its owner), whether the guide source
model gains a `hub` kind (the guide source model's owner), and which of the job
taxonomy's two homes governs pack membership (the taxonomy's owner).

## Unresolved questions

1. **Which solution artifact this becomes.** The scope spans two surfaces, a
   Shipped-spec amendment, and three new pipeline capabilities. That is larger
   than one spec and may warrant a delivery brief coordinating several, or an RFC
   for the spec amendment with specs beneath it. This intent deliberately does
   not choose.
2. **Who owns the marketing navigation model and the zero-gate-code count across
   two intents?** `docs/product/intents/catalogue-wave7-marketing-evaluator.md`
   adds a marketing `/evaluate/` page and updates catalogue and pack pages under
   RFC-0076 D10, and **RFC-0076 is Accepted** — so on a collision its page-level
   scope outranks a design packet on a collision. (That packet's third gate has
   since been granted, 2026-09-10, which removes the gate asymmetry but not
   RFC-0076's page-level precedence.) Different
   reader, different outcome, but two shared surfaces remain after this intent
   cedes the catalogue and pack pages: **the marketing navigation model**, and
   **`web/src/content/packs/`** — where `iac-terraform.md` carries a gate
   identifier this intent declares Out while wave7 edits that file. So wave7
   could either break or discharge the zero-count check.

   **Trigger:** whichever intent reaches implementation first. **Needed:** one
   owner for the marketing navigation model, and one owner for the gate-code
   count across both. Recording the adjacency is sufficient for admission;
   neither intent has to move first.
3. **Who writes the marketing headline.** The design packet specifies its
   contract in full — at most ten words, the team's situation before any
   mechanism — and no installed skill produces positioned marketing copy. Three
   candidates exist as input, not as a decision.
4. **Closed 2026-09-10 — gatekeeper adequacy is outside this intent.** This
   previously carried the "one canvas, four audiences" bet as an accepted risk,
   with the role-stratified comprehension check as its falsifier. The Outcome no
   longer claims a gatekeeper audience, so the bet is not this intent's to
   carry: the canvas may be viewed by a budget holder, but nothing here
   promises or tests that it serves their decision. The comprehension check
   covers champions, engineers, tech leads and platform teams only.
   **Consequence for the measurement plan:** its M4 role-stratified audience and
   its "Use one canvas for four audiences" kill condition still score budget
   holders and respond to failure by adding role-specific collateral — which
   Boundary now excludes. Both need the same influencer-only narrowing before
   that plan is run.
5. **Which of the five owed verifications gates delivery, and who runs each?**
   Three need execution rather than writing — diffing generated slugs, querying
   the live index, and measuring a read time — and one cannot be closed inside
   this repository at all. **Resolved 2026-09-10 for V1:** the sanitiser
   question was probed against GitHub's own renderer — the `<img>` binding
   works, inline is removed outright. The remaining verifications and their
   ownership are still unresolved.
6. **Closed 2026-09-10 — the primary success metric has no baseline and will
   not get one.** The champion interview that would have established it was
   retired as theatre. Every stage emotion and pain in the source journeys
   remains assumption-based, and that is now a permanent property of this
   packet rather than an outstanding action. Do not re-open it as a gate.

7. **Who defines "pack" in plain words, and where?** It is unfamiliar
   product-specific vocabulary sitting in navigation on both surfaces, and the
   plain-language floor bars it until defined. Nobody owns the sentence.
8. **Does ADR-0020's per-pack Diátaxis hierarchy engage the job grouping?** It
   governs structure *within* an area, and grouping areas above themselves
   appears not to touch it — but that reading needs the ADR's owner, and if it
   does engage, the sidebar work needs a different shape.
9. **Does the guide source model gain a `hub` kind?** All 21 area index pages
   function as navigation hubs; 18 declare `explanation` and 3 declare
   `reference`, for no structural reason. Either they retype or the type set
   grows. The guide source model's owner decides.

## Projection

**Tracker:** none. No tracker projection was requested and none is implied — the
repository holds the truth for this work.

**Artifact:** deferred to unresolved question 1. This intent does not choose
between an RFC, a delivery brief, or a set of specs, and the field should not be
read as "no downstream artifact".

## Source

- Mode: repo-origin
- Locator: docs/design/discovery/team-orientation-build-handoff.md
- Revision: sha256-bytes-v1:fb74c0f2034dd6a0422b958b56f89a8abec66b48ec15becdf46509b92c70eadc
- Revision note: repinned after the source was corrected. The original pin went
  stale within the session when the gate-code scope was narrowed to marketing.
- Authority: the design packet under `docs/design/`, produced through the
  experience-design thread with **all three owner gates passed** —
  `approve-journey` (2026-09-04, re-gated 2026-09-10 for the Stage 2
  surface-plural install), `approve-aesthetic-direction` (2026-09-04), and
  `review-experience-designs` (**granted 2026-09-10**: six blockers and
  fourteen of sixteen majors fixed; Major 1/V1 closed by a live GitHub render
  probe; Minor 5 retired with the champion interview). Delivery depended on
  that third gate and is now unblocked; nothing is implemented.
  Rationale and every decision's basis are in
  `docs/design/discovery/team-orientation-decision-log.md`; the six screens and
  their transitions are in `docs/design/screens/team-orientation-flow.md`.
