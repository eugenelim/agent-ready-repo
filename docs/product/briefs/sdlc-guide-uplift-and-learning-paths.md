# Brief: a new team can walk the whole SDLC from the guides

- **Slug:** `sdlc-guide-uplift-and-learning-paths`
- **Received:** 2026-09-03
- **Owner:** eugenelim
- **Status:** Executing

## Outcome

A team adopting this catalogue can go from install to a shipped, governed change
by following the guides alone. Every skill they must invoke shows what to type,
what to supply, what comes back, and what they hold at the end. The landing page
must expose one obvious end-to-end walkthrough, and each step must carry the
reader to the next. A newcomer should get a route rather than a menu of files.

The route this repository's own owner uses must become walkable end to end: shape on
`desk-research` + `product-engineering` + `architect`, hand over with
`intake-intent`, build with `new-spec` + `work-loop`, and collaborate
through RFCs and ADRs sourced from those shaping artifacts.

## Success metrics

- A newcomer can start from the website landing page or documentation home and
  enter one named install-to-ship walkthrough without first choosing a pack.
- The walkthrough keeps a visible next step from installation through shaping,
  architecture, Core intake, build, governance, release, and reporting. Each
  step states its prerequisite, a literal request, its result, and the next link.
- Both `architect` and `desk-research` link to the shaping-to-build handover, so
  neither shaping route dead-ends.
- In-scope how-tos show the request a reader supplies, a representative sample
  of what the agent returns, and the result the reader should expect. Tutorials
  demonstrate the input and matching output rather than only describing them.
- Affordance slices derive their current file set from
  `python3 tools/audit-guide-affordances.py` and pair presence movement with
  exemplar-quality evidence.

### Dated affordance baseline and accepted movement

The 2026-09-09 audit is a planning baseline, not a frozen denominator: chat
input was present in 92 of 207 guides (44%), demonstrated input in 10 (5%),
sample output in 67 (32%), and stated outcome in 65 (31%). Published skill
descriptions carried a quoted example in 85 of 135 cases (63%) and `Triggers
on` phrasing in 78 (58%).

The accepted-base ledgers turn those corpus-wide rates into stable slice
commitments:

- S3 closes 11 chat-input gaps and three outcome gaps, and adds quoted example
  utterances to 42 published skill descriptions; missing `Triggers on`
  phrasing within that same accepted set closes with it.
- S4 closes 15 demonstrated-input gaps and seven sample-output gaps, leaving
  every tutorial in the dated baseline with both parts of a worked example.
- S5 closes 40 sample-output gaps in how-tos that already show a literal
  request.

If the corpus denominator stayed unchanged while all three slices shipped,
those deltas would move overall chat-input coverage to 50%, demonstrated input
to 12%, sample output to 55%, stated outcomes to 33%, and quoted skill examples
to 94%, while `Triggers on` phrasing would reach 87%. Delivery is judged
against the accepted paths, not those decaying percentages.

## Scope / Non-goals

**In scope.** This brief covers landing-page and documentation-home access to
the ordered paths; a continuous install-to-ship walkthrough; the
`desk-research` link to the handover; the unfinished U3 and U9 affordance pass;
tutorials missing complete worked input-and-output examples; the sample-output
gap for invocable-skill how-tos; and any path metadata or navigation needed to
keep the route visible after generation. The delivered and open tables below
are the current status: S3-S5 and S7 remain open. S6 shipped 2026-09-11 and was **reopened the same day** to govern the website work its design pass produced; it is Implementing with one criterion awaiting an independent read.

**Owner decision, 2026-09-11 — the four-discipline sequence joins this brief as
S6.** Presenting `desk-research → product-strategy → experience-design →
product-engineering` as one ordered sequence, on the journeys index and in
`guides/README.md`, is delivered here rather than under a separate intent.

Ownership was tested against the alternatives before this decision. This brief's
own outcome is guides "grouped into ordered paths that name their
prerequisites", which is exactly the guides half. `cohort-orientation-surfaces`
places journey pages explicitly out of its Boundary, and
`digital-product-guides-update` is RFC-0071 M6 — a chain carrying
frontend-engineering rather than `desk-research`, gated behind unstarted M5.
`digital-product-maker-profile` names the same four disciplines but its unit is
a `profiles/*.toml` that by its own record "is read only by the `agentbundle`
CLI and never reaches the plugin route".

**This widens the brief's site surface, deliberately and only by degree.** S1
already delivered `web/` entry points — it named the walkthrough on the guide
hub and entered it from the marketing landing page. S6 adds one further `web/`
page, the journeys index. `guides/README.md`'s navigation model remains owned by
`cohort-orientation-surfaces`: S6 adds a path within the existing hub structure
and does not restructure it, the same coordination stance
`claude-apps-route-docs` records for its own link into that file.

**Route constraint, measured.** `product-engineering` ships 3 agents,
`desk-research` 2, `experience-design` 1, `product-strategy` 0. Claude plugins
carry agents, so all four install there. Agent Plugins 1.0.0 defines no agent
component type, so three of the four are refused and the sequence cannot be
walked on that route. S6 is a Claude-plugins-route outcome and may not describe
the two routes as equivalent.

**Owner decisions, 2026-09-03.** The routed questions this brief held outside
delivery have been settled, and their consequences are in scope:

- **The catalogue supports multiple tracker modes.** The Atlassian
  write-back-to-Jira journey **survives**. It is not a contradiction to remove
  but a second supported mode to name and bound, alongside repo-first
  projection. Both modes must be documented, with the choice made explicit.
- **Light intents are the primary shaping path**; the robust path stays
  supported and must be **surfaced in the guides**, not deleted. This settles
  U12; S1 carries that choice into the walkthrough.
- **The earlier uplift was not registered.** Those changes landed outside this
  brief's governed delivery lifecycle. The remaining outcome is now registered
  under `["ini-002".brief_queue].draft` while this amended revision is reviewed;
  this does not retroactively turn the earlier changes into governed slices.

**Out of scope.**

- Building a tracker exporter. The audit confirms a documented projection
  mapping with no live API integration, and `tracker-projection.md` records
  that deferral deliberately. This brief documents the mapping and both modes;
  it does not ship the export.
- Any change to skill behaviour. This is a documentation and schema outcome.
- Reworking original candidates already verified as shipped below.
- The experience-design deliverable inventory, the cross-pack digital-product
  tutorial and intent indexes, and role-specific first-value rollout. Their
  owning intents remain separate shaping work below.

## Appetite

A few weeks, not a quarter. Make the end-to-end route discoverable first, then
close the remaining affordance gaps in independently testable slices. Reuse the
path and invocation content already present; net-new workflow behavior remains
out of scope.

## Assumptions / Risks

- **Risk.** The ordered paths exist in `guides/README.md`, but
  `web/src/pages/index.astro`, `docs-site/src/content/docs/index.mdx`, and
  `docs-site/src/content/docs/getting-started/index.mdx` do not link to that
  guide landing page. Content presence therefore overstates discoverability.
- **Assumption.** Existing SKILL.md trigger phrases are correct invocations, so
  lifting them projects fact rather than inventing phrasing.
- **Assumption.** A path grouping is orthogonal to `kind:` and needs no file
  moves, so generated navigation and published URLs survive. **Open:** whether
  it needs a new frontmatter key at all. `contracts/guide.schema.json` sets
  `additionalProperties: false` and already carries optional `journey` and
  `order` keys. The remaining path work must test those before adding another
  key.
- **Risk.** The affordance measurement is regex-based. It proves presence, not
  quality, so delivery can satisfy a count with a weak example. The source
  audit's exemplar, `architect/how-to/diagram-a-system.md`, is the quality
  comparison point for future affordance slices.
- **Risk.** A catalogue-wide affordance pass can duplicate role-specific guide
  work. Candidate slices must exclude surfaces owned by the related intents
  below unless that owner explicitly hands the surface to this brief.

## Shipped portions and delivered slices

Checked against the repository and the audit instrument on 2026-09-09. These
changes landed outside this brief's lifecycle, so `Shipped` below means the
named repository outcome is present. It does not create a spec, populate the
Spec map, or make this brief `Shipped`.

| Shipped portion | Repository evidence |
| --- | --- |
| S6 — the four disciplines are discoverable as one ordered sequence — **reopened 2026-09-11**, see below | [`four-discipline-sequence`](../../specs/four-discipline-sequence/spec.md) is Shipped: the journeys index groups the four in a collection-derived ordered list and `guides/README.md` carries the path as P2b, an alternative to P2 rather than a trailing seventh. Its Objective was narrowed on delivery to drop "and can walk it", which no criterion tested — the walk is S7 |
| Shaping-to-build handover foundation | `hand-an-intent-to-build.md` exists; `architect` links to it; both governance guides name upstream shaping artifacts |
| Optional journey chat input | `youType` is optional in the validator and schema, has tests and authoring guidance, and is present in the published `JOURNEY.md` contracts |
| Completed shaping-guide affordances | The product-engineering how-tos have chat inputs and outcomes; the audit records the product-strategy and phrase-harvest improvements already present |
| Repo-first tracker projection | The projection guide carries the one-way rule, Jira Software and GitHub mappings, manual-export limit, and links to the intake mode |
| Architecture artifact registration | Both architect how-tos that create durable architecture artifacts show the canonical `kind = "design"` workspace entry and `needs` reference |
| Learning-path foundation | The whole-lifecycle install guide, light-versus-robust choice, and ordered paths exist in `guides/README.md` |
| Verified defect corrections | The stale names, claims, and workspace shapes are corrected; the audit records the related broken-link sweep |
| Existing tutorial demonstrations | The detector finds demonstrated inputs in the tutorials already uplifted |
| Linear and GitHub baseline | Both packs state their mode, show a literal request, describe the intake result, and link to the shared tracker guidance |
| Design and frontend invocation phrasing | Experience-design and frontend-engineering skills carry a quoted example and `Triggers on` phrasing |
| Two-mode tracker guidance | The chooser and projection guides name both modes, cross-link them, and warn against mixing authority within one body of work |
| S1 — walkthrough discoverability | [`install-to-ship-walkthrough`](../../specs/install-to-ship-walkthrough/spec.md) is Shipped: the public entry points now lead into the named route and its ordered next steps |
| S2 — desk-research handover | [`desk-research-build-handover`](../../specs/desk-research-build-handover/spec.md) is Shipped: the pack now reaches the shaping-to-build handover and its accepted broken-link repairs are present |

## Related shaping work

These are coordination references, not delivery slices, hard dependencies, or
Spec-map entries.

| Artifact | What it owns | Boundary with this brief |
| --- | --- | --- |
| [`experience-design-delivery-packet`](../intents/experience-design-delivery-packet.md) | Researching the experience-design deliverable inventory and, if its assumptions survive, bringing that pack's guides to the full affordance standard | This brief does not pre-empt that research or claim experience-design guide uplift in its catalogue-wide passes |
| [`digital-product-guides-update`](../intents/digital-product-guides-update.md) | A cross-pack digital-product tutorial and per-pack intent indexes after the cross-pack experience evaluation | S1 connects the existing catalogue walkthrough; it does not create or satisfy the future digital-product tutorial |
| [`nontechnical-pack-first-value-rollout`](../intents/nontechnical-pack-first-value-rollout.md) | Role-appropriate first-value adoption slices, including safety, recovery, and evaluation evidence | This brief can improve affordances in existing guides but does not create pack-specific first-value surfaces |

## Spec map

S1 and S2 have shipped. S3 passed its shaping gate and an owner-authorized
fourth adversarial round after repairing the third-round construction-gate
finding. S4 passed a clean-room review after its earlier indeterminate review
unit was closed and its gate and scope findings were repaired. S5 passed its
shaping gate and three adversarial rounds. S6 was added by owner decision on
2026-09-11, took four Sol review rounds plus a mechanical set-level sweep, and
shipped the same day; no round returned a clean verdict, and the owner shipped
on the recorded review economics rather than on convergence. S3-S5 are
registered below as Draft specs pending human approval. S7 has no spec yet.

| Spec | Status |
| --- | --- |
| `install-to-ship-walkthrough` | Shipped |
| `desk-research-build-handover` | Shipped |
| `guide-invocation-outcome-coverage` | Draft |
| `tutorial-worked-examples` | Draft |
| `how-to-sample-output-coverage` | Draft |
| `four-discipline-sequence` | `<auto>` |

## Open delivery slices

Review-clean S3-S5 appear in the Spec map as non-dispatchable Drafts. S6 has
shipped and is recorded with the delivered work above. S7 is a candidate slice
with no spec yet.
Shipped S1 and S2 are recorded with the delivered work above rather than mixed
into this table.

| # | Candidate slice | Open portion | Independently shippable boundary |
| --- | --- | --- | --- |
| S3 | Raise invocation and outcome coverage — **confirmed 2026-09-09, review-clean and registered as Draft [`guide-invocation-outcome-coverage`](../../specs/guide-invocation-outcome-coverage/spec.md)** | Guides still lack literal chat inputs and stated outcomes, and user-invocable skill descriptions still lack quoted examples or `Triggers on` phrasing | Every current in-scope target identified by the audit gains its missing source-grounded invocation or outcome affordance; the accepted-base ledger proves positive movement without freezing corpus totals |
| S4 | Complete the remaining tutorial examples — **confirmed 2026-09-09, review-clean and registered as Draft [`tutorial-worked-examples`](../../specs/tutorial-worked-examples/spec.md)** | Most tutorials describe a workflow without showing the supplied input and matching output used in the worked run | Every current in-scope tutorial target demonstrates its workflow input and keeps it paired with a representative output and the result shown; related-intent surfaces remain excluded |
| S7 | Make the four-discipline sequence walkable, not just findable — **opened 2026-09-11** | S6 shipped discoverability only: no step shows a literal request, the path was reachable from nothing until its 2026-09-11 placement fix, no surface routes a Claude Desktop reader to an install, no worked example shows one artifact actually entering the next skill, and **the journey cards' own content contradicts the sequence** — `product-engineering`'s tagline reads "Raw idea → build-ready decision brief" while the group says it receives a designed bet, so the last discipline appears to restart the sequence and stop before implementation | A new team can execute the sequence end to end from the guides: every step states a literal request, its result, and its next link; the path is entered from the journeys index as well as from P2; one worked example carries a real artifact across all three handoffs; every pack in the walk is operable for a reader who has not used the catalogue before; and **card IA is settled for the sequence** — what one card must carry, and each of the four taglines agreeing with its position. Card content is generated from `packs/*/JOURNEY.md`, so this half is a released pack change that S6 could not make (its AC-0018 forbids touching generated journey content); it lands here because it shares a source with the walk's handoff semantics |
| S5 | Close the how-to sample-output gap — **confirmed 2026-09-09, review-clean and registered as Draft [`how-to-sample-output-coverage`](../../specs/how-to-sample-output-coverage/spec.md)** | Sample-output coverage did not move in the earlier uplift, and many invocable-skill how-tos still describe a result without showing a representative agent response | Every current in-scope how-to target shows a source-grounded representative response; reference and explanation pages and related-intent surfaces remain excluded |

## Rabbit holes

- **Rewriting the audit instrument into a shipped lint.** The instrument
  measures presence by regex and was built to size the problem. Promoting it to
  a gate is its own decision and remains outside this brief.
- **Re-litigating Diataxis.** The `kind:` axis works and drives generated
  navigation. The path axis is additive.
- **Expanding the tracker mapping into a sync design.** The one-way rule in
  `tracker-projection.md` is load-bearing; documenting it is not an invitation
  to design round-tripping.
- **Fixing every guide to the full affordance score.** Explanation and
  reference pages do not need a chat input or a demonstrated input. The target
  is every guide that documents an invocable skill, not every file.

## Source

- Mode: repo-origin
- Locator: docs/product/intents/sdlc-guide-uplift-and-learning-paths.md
- Revision: sha256-bytes-v1:d0ff456f4541b9d2b06819ac7b886ffdfe670f08772f1a4791c3b8eece213cf3

## Supporting artifacts

- [Feature intent](../intents/sdlc-guide-uplift-and-learning-paths.md) — the
  outcome, opportunity, and what the decision requires.
- [New-team SDLC adoption — journey map and guide uplift audit](../findings/new-team-sdlc-guide-uplift-audit.md)
  — the evidence: the journey map, the guide-affordance measurement, the uplift
  table keyed to source content, the proposed path structure, and the verified
  defects with per-file evidence.
