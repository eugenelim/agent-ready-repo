# Spec: the four disciplines are discoverable as one ordered sequence

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** docs/product/briefs/sdlc-guide-uplift-and-learning-paths.md
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Provenance

Slice **S6** of
[`sdlc-guide-uplift-and-learning-paths`](../../product/briefs/sdlc-guide-uplift-and-learning-paths.md),
added by owner decision on 2026-09-11. It is a slice, not the whole brief: S3–S5
remain open alongside it.

**Routed here rather than to a new intent.** An earlier pass in this session
authored a standalone intent for this outcome. A Sol review round found that the
brief above already owns the guides half outright — its outcome sentence is
guides "grouped into ordered paths that name their prerequisites" — and the
owner routed the whole outcome here. The brief's § "Scope / Non-goals" records
the decision and why the three adjacent intents do not own it.

**One coordination point, not split ownership.** The path lands in
`guides/README.md`, whose navigation model belongs to
[`cohort-orientation-surfaces`](../../product/intents/cohort-orientation-surfaces.md).
Adding a path within the existing hub structure does not restructure that model;
if the hub's navigation is reworked, this path travels with it. This is the same
stance [`claude-apps-route-docs`](../claude-apps-route-docs/spec.md) records for
its own link into the same file.

## Objective

A first-time Claude Desktop user who has installed nothing can see, from the
published surfaces alone, that **desk research → product strategy → experience
design → product engineering** is one ordered sequence, and can find the entry
point for each of the four.

**Narrowed 2026-09-11, after the build.** This previously ended "and can walk
it". No criterion in this set ever tested walkability, and the delivered
surfaces do not provide it: no step shows a literal request, the guides path is
reachable from nothing, and no surface routes a Claude Desktop reader to an
install. Claiming the walk while testing only grouping, order and links was a
claim reaching past its check, so the claim is narrowed rather than the check
invented after the fact. **The walk is slice S7**, recorded in the brief.

Three outcomes:

1. **The journeys index presents the four as an ordered group.** Today it
   renders one flat grid in which they sit at positions 2, 9, 10 and 19 of 20,
   with no signal that they relate.
2. **The guides publish an ordered path for the four**, in the shape P1–P6
   already use — a prerequisite, a first-value moment, an "ends at". Today
   `product-strategy` and `experience-design` appear in no path at all; both
   exist only as rows in two unordered chooser tables.
3. **Each step names what it hands on**, so a reader can stop after any one of
   them and know what they hold.

The order is the owner's decision, taken 2026-09-11 against the packs' own
dependency contracts: `desk-research/DESIGN.md` declares "Upstream (none)" and
names `product-strategy` its downstream, and `product-strategy/DESIGN.md` calls
its own position upstream of `product-engineering` and `experience-design` "the
architectural invariant". The order agrees with the shipped P2 step order, which
also gathers evidence before shaping, so the two routes a reader can reach do
not contradict each other.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — adopters read both surfaces | `guides/README.md` § the new path; `web/src/pages/journeys/index.astro` | `author-product-docs` conventions | Guide validators pass; page builds and renders | Both surfaces carry the sequence in the decided order |
| Current product truth | Applicable — the brief tracks slice delivery | `docs/product/briefs/sdlc-guide-uplift-and-learning-paths.md` § "Spec map" | `lint-brief-coverage` roll-up | Coverage roll-up resolves this spec through its `Brief:` back-link | Roll-up names this spec; no status hand-written into the brief |
| Reusable learning | Applicable — the membership-derivation rule is why a prior hardcoded list dropped five journeys | `docs/specs/four-discipline-sequence/notes/verification-ledger.md` | This spec's owner | Recorded run of the membership check with slug multisets | Ledger records the collection multiset and the rendered multiset, and they match |
| Release history | **Not applicable** — `web/` and `guides/` are not published packs; no `pack.toml` or `plugin.json` version changes. Had the handoff copy required editing `packs/*/JOURNEY.md`, this row would apply to four packs; Boundary forbids that route | none | — | — | — |
| Decision rationale | **Not applicable** — the order decision and the routing decision are both recorded in the brief by its owner; no architectural choice is made or reversed | none | — | — | — |
| Interface compatibility | **Not applicable** — no published URL, slug, or frontmatter key changes; the path is additive prose and the grouping is internal to one component | none | — | — | — |

## Boundaries

### Always do

- Derive group membership from the `journeys` collection, so any journey not
  named in a group still renders. A hardcoded list previously dropped five
  journeys, including `product-strategy`.
- Keep `guides/README.md`'s `title` identical to its leading body H1.
- Build marketing before docs: the `web/` build cleans repository `build/`.

### Ask first

- Adding a frontmatter key to `contracts/guide.schema.json`. It sets
  `additionalProperties: false`, and the existing optional `journey` and `order`
  keys must be tested first.
- Changing the decided order, which is the owner's and is recorded in the brief.
- Restructuring `guides/README.md`'s navigation model, which is
  `cohort-orientation-surfaces`'s.

### Never do

- **Edit any file under `web/src/content/journeys/`.** They carry
  `generated: true` and are projected from `packs/*/JOURNEY.md` by
  `tools/build-site.py --journeys-only`. Editing one by hand either loses the
  edit at the next projection or turns this into a four-pack released change.
- **Add an image to either surface.** A guide cannot carry an image that renders
  on both GitHub and the docs site; the projector rewrites Markdown image paths
  into page URLs and copies no assets. The sequence reads as a sequence in text.
- **Claim that a reader has reached first value, completed a method, or
  installed successfully.** The dated Claude-apps install-to-first-value probe
  has not been run. This rail is about *adopter outcome claims*; it does not
  touch the guides' structural `**First value:**` label, which names what a path
  step produces and is required by AC-0009.
- **Describe the two plugin routes as equivalent.** `product-engineering` (3),
  `desk-research` (2) and `experience-design` (1) ship agents; Agent Plugins
  1.0.0 defines no agent component type, so three of the four are refused there.
- **Introduce a new top-level directory or dependency.** Both surfaces exist.

## Testing Strategy

- **Grouping, order, ordered markup and step-number announcement (AC-0001 to
  AC-0004):** goal-based check over the built page on the `web/` vitest suite,
  `npm run test --prefix web`. The observation is the rendered HTML, because the
  criteria are about what a reader receives, not what the source says.
- **Membership (AC-0005, AC-0006):** construction tests on the same suite.
  AC-0005 compares the multiset of collection slugs against the multiset of
  rendered card slugs — identity and multiplicity, not totals, because a count
  comparison passes when one journey is omitted and another duplicated.
- **Index and guide prose (AC-0007 to AC-0010):** goal-based checks over the two
  files. Presence and placement are mechanically checkable; whether the sequence
  is *followable* is a comprehension property and is AC-0011's.
- **Guide validity (AC-0012 to AC-0014):** the three existing guide gates, each
  named separately because they inspect different contracts, fail differently,
  and are fixed differently.
- **The prohibitions (AC-0015 to AC-0018):** four observations, not three — an
  image-syntax scan over the edited files (AC-0015), two whole-diff reads
  (AC-0016, AC-0018), and one path-scoped `git diff` (AC-0017).
- **Guide-surface self-consistency (AC-0022):** goal-based check over
  `guides/README.md`. Two chooser rows currently order these four as strategy
  before research — "Decide what to build" and the "Product manager or
  strategist" role row — so this criterion is red against the file as it stands
  today and can only go green by reconciling them.
- **Required links (AC-0020, AC-0021):** goal-based checks — AC-0020 on the
  built page over the `web/` vitest suite, AC-0021 over `guides/README.md`.
- **Group signatures and the onward route (AC-0023, AC-0024):** construction
  tests on the `web/` vitest suite over the built page. AC-0023 asserts the
  modifier class **and** an at-rest style rule for it: matching any rule is not
  enough, because a `:hover`-only rule leaves the card identical at rest, which
  is exactly when the groups must be distinguishable.
- **Adjacency and the selection axis (AC-0025, AC-0026):** goal-based checks over
  `guides/README.md`. AC-0026's observer is a reader, for the reason recorded
  under Accepted residuals.
- **Link integrity (AC-0019):** `make site-link-check`. It verifies resolution,
  not existence; AC-0020 and AC-0021 own existence, which is why AC-0019 is not
  load-bearing on its own.

**Verification surface, checked 2026-09-11.** Every built-HTML criterion
(AC-0001 to AC-0006, AC-0020) observes through the built site. The build command
is `make site-build`, which writes `build/` then `build/docs/`; build order is
load-bearing because the `web/` build cleans repository `build/`.

An earlier note here recorded a "known risk" that `make bootstrap-sites` exits 0
without emitting `build/docs/`, with four `web/` vitest cases failing as a
result. **That was a false premise and is withdrawn.** `bootstrap-sites`
installs npm dependencies only — its own help text says so — and was never the
build. Run against a real `make site-build`, the suite is fully green: 18 files,
148 tests, 39s. There is no bootstrap defect and no local-evidence gap.

No TDD-mode outcome for the guide half: it changes prose, and a unit test over
prose would assert its own fixture.

## Acceptance Criteria

- [x] **AC-0001.** The journeys index renders the four disciplines in a group
      distinct from all other journeys, under a heading naming it as a sequence.
- [x] **AC-0002.** Within that group the four appear in the order
      desk-research, product-strategy, experience-design, product-engineering.
- [x] **AC-0003.** The group is an ordered list element, so the order is carried
      by the markup and not only by visual arrangement.
- [x] **AC-0004.** The visible step number is hidden from assistive technology,
      so a reader hears the position once from the ordered list rather than
      twice.
- [x] **AC-0005.** The multiset of journey slugs rendered on the page equals the
      multiset of slugs in the `journeys` collection.
- [x] **AC-0006.** A journey present in the collection but named in no group
      still renders, in the catch-all group.
- [x] **AC-0007.** On the index, each of the first three disciplines names what
      it hands the next, and the fourth names what the reader ends with.
- [x] **AC-0008.** `guides/README.md` carries an ordered path covering the four
      disciplines in the order desk-research, product-strategy,
      experience-design, product-engineering.
- [x] **AC-0009.** That path states a prerequisite, a `**First value:**` moment
      and an "ends at", matching the shape P1–P6 already use.
- [x] **AC-0010.** In the path, each of the first three disciplines names what it
      hands the next, and the fourth names what the reader ends with.
- [x] **AC-0011.** A cold reader who has seen only these two surfaces can name
      the four disciplines in order and state what one hands the next.
- [x] **AC-0012.** `guides/README.md` frontmatter remains valid.
- [x] **AC-0013.** `guides/README.md`'s `title` matches its leading H1.
- [x] **AC-0014.** The guide index remains complete.
- [x] **AC-0015.** Neither edited surface contains image syntax.
- [x] **AC-0016.** No text in the change claims that a reader has reached first
      value, completed a method, or installed successfully. The structural
      `**First value:**` path label required by AC-0009 is not such a claim.
- [x] **AC-0017.** No file under `web/src/content/journeys/` is modified.
- [x] **AC-0018.** No text in the change describes the Claude-plugins route and
      the Agent Plugins route as carrying the same packs.
- [x] **AC-0019.** Every internal link emitted by the change resolves.
- [x] **AC-0020.** On the index, each of the four discipline cards links to that
      discipline's journey page.
- [x] **AC-0021.** In the path, each of the four steps links to that discipline's
      guide directory.
- [x] **AC-0022.** No other row on `guides/README.md` states an order for these
      four disciplines that conflicts with AC-0008's.
- [x] **AC-0023.** Each of the three groups applies its own card modifier, and
      the built page emits a style rule for each, so the relationship between
      groups survives with the headings suppressed.
- [x] **AC-0024.** The sequence group links onward to the guides path that walks
      the same four disciplines.
- [x] **AC-0025.** In `guides/README.md` the alternative path is adjacent to the
      step it is an alternative to, with no other stage between them.
- [ ] **AC-0026.** The alternative path and the step it replaces do not both
      claim the same selection condition.

## Acceptance-set construction record

Run 2026-09-11, after the owner routed this outcome into the brief. Obligations
were enumerated from the Objective's three outcomes, the five non-waivable `Never do`
rails, and the applicable Durable Outputs; each was admitted only once a single
observing surface could be named.

- **Candidate obligations:** 41
- **Admitted as criteria:** 26
- **Routed:** 14
- **Cut:** 1

| Candidate obligation | Disposition | Criterion / owner | Red input | Observer |
| --- | --- | --- | --- | --- |
| The four render as a distinct group | admitted | AC-0001 | four still in one flat grid, or no group heading | built page |
| The group carries the decided order | admitted | AC-0002 | any adjacent pair transposed | built page |
| Order is in the markup, not only visual | admitted | AC-0003 | `<ul>`, or CSS-only ordering | built page markup |
| The step number is not announced twice | admitted | AC-0004 | the visible number rendered without `aria-hidden`, so the list position and the numeral are both announced | accessible name of each card |
| No journey dropped or duplicated | admitted | AC-0005 | one slug omitted, or one rendered twice | slug multiset comparison |
| An ungrouped journey still renders | admitted | AC-0006 | catch-all replaced by a hardcoded list | the rendered page under a fixture journey |
| The index names each handoff | admitted | AC-0007 | on the index, any of the first three not naming what it passes on, or the fourth not naming its end state | the index page copy |
| The guides carry the same sequence | admitted | AC-0008 | path absent, or the four in any other order | `guides/README.md` |
| The path matches the P-path shape | admitted | AC-0009 | any of prerequisite, first value, ends-at missing | `guides/README.md` |
| The P2 conflict is disclosed | **cut** | — | — | the P2 conflict no longer exists: with desk-research first, this path and P2 agree that evidence precedes shaping. A criterion disclosing a difference that is not there could not fail |
| The groups survive without their headings | admitted | AC-0023 | two groups sharing one modifier, or a modifier applied with no emitted rule | built page markup and its inlined style |
| The sequence routes the reader onward | admitted | AC-0024 | the sequence group emitting no link to the guides path | built page |
| The alternative sits beside the step it replaces | admitted | AC-0025 | another stage heading between them | `guides/README.md` |
| The two routes state different selection conditions | admitted | AC-0026 | both passages naming the same trigger | a reviewer reading the two passages |
| The guide surface does not contradict its own order | admitted | AC-0022 | a chooser row ordering these four differently from the path | `guides/README.md` |
| The path names each handoff | admitted | AC-0010 | in the guides path, any of the first three not naming what it passes on, or the fourth not naming its end state | `guides/README.md` |
| A cold reader can restate the sequence | admitted | AC-0011 | order or any handoff unstatable | the reader |
| Guide frontmatter stays valid | admitted | AC-0012 | invalid or missing frontmatter | `validate_guides.py` |
| `title` matches the H1 | admitted | AC-0013 | the two diverge | `lint-guide-titles.py` |
| Guide index stays complete | admitted | AC-0014 | page missing from the index | `check-guide-index.py` |
| No image on either surface | admitted | AC-0015 | any image syntax in the two edited files | image-syntax scan over the change |
| No adopter-outcome claim | admitted | AC-0016 | any first-value, completed-method or install-success assertion | whole-diff read |
| Generated journey content untouched | admitted | AC-0017 | any modification under that path | `git diff -- web/src/content/journeys/` |
| The two routes are not equated | admitted | AC-0018 | text implying both carry all four | whole-diff read |
| The index links each discipline to its journey | admitted | AC-0020 | any of the four cards rendering without a link to its journey page | built page |
| The path links each step to its guide | admitted | AC-0021 | any of the four steps stated without a link to its guide directory | `guides/README.md` |
| Emitted links resolve | admitted | AC-0019 | any unresolved emitted link | `make site-link-check` |
| The brief's coverage roll-up resolves this spec | **routed** | `lint-brief-coverage`, via the `Brief:` back-link | — | a pre-existing repository control; this slice supplies the back-link it reads |
| A diagram of the sequence | **routed** | `docs-site-build-contract-hardening/notes/guide-image-projection.md` | — | not this slice's; AC-0015 avoids the defect |
| Handoff copy inside journey content | **routed** | `packs/*/JOURNEY.md` + the pack release pipeline | — | a four-pack released change, fenced by AC-0017 |
| Sub-agent degradation on the chat surface | **routed** | `claude-plugin-route-scope/notes/subagent-present-but-unrunnable.md` | — | AC-0018 discloses; it does not repair |
| A pack delivering first value | **routed** | `claude-apps-first-value-entry` | — | needs the unrun probe; AC-0016 fences it |
| Affordance uplift in the four packs' guides | **routed** | sibling slices S3–S5 of this brief | — | this slice adds a path over existing guides |
| The `digital-product` profile | **routed** | `digital-product-maker-profile` | — | CLI-only artifact; cannot serve a no-terminal reader |
| The integrative cross-pack tutorial | **routed** | `digital-product-guides-update` (RFC-0071 M6) | — | blocked behind unstarted M5 |
| No new top-level directory or dependency | **routed** | the repository decision process (root `AGENTS.md`: "Propose a new top-level directory through the repository decision process"); a dependency needs its owning manifest or an ADR | — | pre-existing repository control; this slice adds neither |
| The catch-all group names a relationship, not leftovers | **routed** | `docs/design/content/journeys-index.md` | — | a copy decision recorded in the brief; no criterion could fail on it without asserting its own wording |
| Card content agrees with its position in the sequence | **routed** | S7, and the owning packs | — | `product-engineering`'s tagline contradicts its position, but taglines are generated from `packs/*/JOURNEY.md` and AC-0018 forbids touching them |
| The surface has a content brief to anchor on | **routed** | `docs/design/content/journeys-index.md`, authored 2026-09-11 | — | a design artifact, not a shippable criterion; its absence is why this slice had nothing to anchor on |
| The 19-vs-20 collection count | **routed** | `plan.md` § D1, as a discovery predicate | — | only the build can settle it |
| Step-number styling and the dropped `list-style` rule | **routed** | `plan.md` § D2, as a discovery predicate | — | an implementation choice, not a contract obligation |

**Set-level result.** *Necessity:* each criterion states its whole failure
predicate above — input, expected outcome, observing surface — and no sibling
enforces the same predicate. AC-0005 and AC-0006 can both red on a missing
journey, which the contract permits: two controls may share an input while
asserting different outcomes. AC-0007 and AC-0010 are the other such pair —
the same obligation on two surfaces — so their red inputs are stated
surface-first to keep them distinguishable at a glance. AC-0005 asserts exhaustiveness over the current
collection; AC-0006 asserts that the catch-all mechanism exists, and its red
input is the hardcoded-list mutation, not an omission. *Uniqueness:* every
criterion names exactly one observing surface. AC-0003 and AC-0004 are adjacent
but distinct — markup order is not an accessible name, and a page can pass
either while failing the other. AC-0007 and AC-0010 state the same obligation on
two surfaces and are therefore two criteria with one observer each, not one
criterion with two. *Consistency:* AC-0009 requires a `**First value:**` label
while AC-0016 forbids first-value claims; the Boundary rail states the
distinction explicitly, so the two coexist. AC-0007 and AC-0010 require handoff
copy while AC-0017 forbids touching journey content; they coexist because the
copy is hand-authored on the index page and in the path. *Joint feasibility:*
AC-0015 forbids images and AC-0001 needs a legible group, which a heading and an
ordered list satisfy without one. AC-0019 is deliberately paired rather than
standing alone: on its own it passes on the empty set, because a path emitting
no links has no unresolved link. AC-0020 and AC-0021 supply the links whose
existence it then verifies, so the pair cannot both be satisfied vacuously.
*Coverage both ways:* Objective outcome 1 reaches AC-0001 to AC-0006 and AC-0020;
outcome 2 reaches AC-0008, AC-0009, AC-0021, AC-0022 and AC-0025; outcome 3
reaches AC-0007, AC-0010, AC-0011 and AC-0024. AC-0023 and AC-0026 reach the
User-facing promise Durable Output: a page whose groups collapse without their
headings, or a pair of routes that claim the same trigger, has not carried the
sequence to a reader. AC-0019 reaches the User-facing promise Durable Output: a
surface whose emitted links do not resolve has not carried the sequence to a
reader, whatever else holds.
The five `Never do` rails reach AC-0017, AC-0015, AC-0016, AC-0018 and the
routed repository-decision row respectively. The three applicable Durable
Outputs reach AC-0008 and AC-0021, AC-0012 to AC-0014, and the ledger row, with
the brief roll-up carried by the routed `lint-brief-coverage` row. Every
criterion traces back to one of those.

## Accepted residuals

- **AC-0011's observer is a person.** No mechanical oracle exists for whether a
  reader can restate a sequence, and inventing one would compare the page to
  itself. Accepted as proportionate: the criterion can still fail, the two
  surfaces are named, and it adds no new class of verification burden beyond the
  cold read the repository already runs.
- **The brief's five sibling Spec-map statuses stay hand-written.**
  `docs/CONVENTIONS.md:515` and `lint-brief-coverage.py`'s own contract agree
  that the Status column "is auto-derived and must not be hand-maintained".
  **This slice's own row is repaired**, not accepted: it carries the unset
  marker `<auto>`, which that linter explicitly reports rather than fails.
  Deleting the row instead would have been wrong — the same linter reports a
  back-linking spec absent from the Spec map as *untracked*. The five older rows
  for S1–S5 keep hand-written values. They are not drift today, because each
  still matches its spec, and they become drift the moment one status moves.
  Bounded out with its owner named: correcting them is the brief's remediation,
  not this slice's. **Owner: the brief.**

Neither is a defect found late; both are judgements recorded when made.

## Assumptions and undischarged risks

- The four journeys already say enough about their inputs and outputs that
  AC-0007 and AC-0010's handoff copy can be written from existing material. If
  false, those are the criteria that fail, and the response is to narrow them to
  the guides surface rather than to edit generated journey content.
- `guides/README.md` can carry a seventh path without a schema change, because
  P1–P6 are prose under headings and add no frontmatter key.
- **Closed 2026-09-11 — the order now matches the packs' contracts.** Round 3
  found that the previously decided order (`product-strategy` first) inverted
  the one adjacent pair the packs state explicitly:
  `packs/desk-research/DESIGN.md` declares **"Upstream (none)"** — "it is the
  evidence layer" — and names `product-strategy` as its **downstream**, because
  `synthesize-stakeholder-research` "consumes `desk-research` survey artifacts
  as a primary evidence source"; `packs/product-strategy/DESIGN.md` adds that
  that skill "runs **at the start** when prior desk-research outputs exist".
  The owner reordered to `desk-research → product-strategy → experience-design
  → product-engineering`, which satisfies both that pair and the separate
  invariant that strategy precedes `product-engineering` and
  `experience-design`. **The experience-design/product-engineering pair is
  constrained too — an earlier draft of this entry wrongly called it
  unconstrained.** `packs/experience-design/DESIGN.md` § "Downstream:
  product-engineering" states that "the per-screen state matrix produced by
  `user-flow` is the hand-off artifact `voice-and-microcopy`
  (product-engineering pack) consumes", and `packs/product-engineering/DESIGN.md`
  describes the same interface from its own side. That handoff runs
  experience-design → product-engineering, which is the order adopted here. The
  same PE file also records experience-design skills running "inside the
  convergence loop as optional lens participants" during discovery; that is a
  nesting, not a competing order, and the linear sequence does not claim to
  represent it.

  **This also closed a criterion.** The former AC-0010 required disclosing that
  this path's order differs from the guides' P2. With desk-research first the
  two agree that evidence precedes shaping, so the difference it disclosed no
  longer exists and the criterion could not fail. It is recorded as **cut** in
  the construction record, and the `Never do` rail that forbade publishing the
  two as agreeing is withdrawn with it.

- **Not discharged — whether the two lifecycles are orthogonal.**
  `docs/design/discovery/team-orientation-decision-log.md:52` flags that
  orthogonality as "our assertion", not a finding. This slice adds a second
  ordering to surfaces that already carry the five-station adoption spine. No
  criterion observes that risk, and shipping does not settle it.
- **Not discharged — whether the adoption blocker is explanatory or
  commercial.** The same decision log leaves this open, and
  `cohort-orientation-surfaces` was partially killed on it: the top-ranked
  adoption blocker measured 47% organisational, and "I cannot re-explain it" is
  documented nowhere. If the blocker is commercial here too, a better-sequenced
  index is a real but small improvement. This slice is sized as a route-map
  change, not defended as an adoption fix.

## Review status

**Three Sol rounds have run.** Round 1 read an earlier, differently-scoped draft
authored as a standalone intent, and returned 3 blocking and 9 major; its
blocking ownership finding is what routed this outcome into the brief as S6.
Rescoping restarted the rounds. Round 2 read the rescoped text: 1 blocking,
4 major. A mechanical set-level sweep then ran as a script and closed four
drifts. Round 3 read the swept text: 2 blocking, 3 major, 1 minor.

**No round has returned a clean verdict, and round 3 ended `WORKER_BLOCKED`.**
Blocking counts across rounds ran 3, 1, 2 — not converging — and **four of round
3's six findings originated in a prior round's repair**. That is the pattern a
repair-first habit produces, and it is the reason the open item below is being
put to the owner rather than repaired again.

**Four Sol rounds have run.** Blocking counts: 3, 1, 2, 5. Round 4 read the
reordered text and returned 5 blocking, 1 major, 1 minor, ending
`WORKER_BLOCKED`. Every round-4 finding is applied.

**The trend is the thing to read, not the totals.** Six of round 4's seven
findings originated in a prior round's repair, and five of those were
stale-companion defects created by round 3's own renumbering — a task row still
carrying a cut criterion's instruction, a sequencing note contradicted by a test
added later, a residual count left at three. They were mechanical and cheap,
which is a different character from round 1's design findings, but they are the
signature of repair-first work and the reason this document records its own
review economics rather than only its conclusions.

**Round 4 also caught one real reversal.** Cutting the P2-disclosure criterion
was correct about that criterion and wrong about the obligation beneath it: two
chooser rows on the same guide surface still order these four disciplines
strategy-first. AC-0022 replaces disclosure with self-consistency, which is a
stronger check on the same obligation rather than a restatement of the cut one.

**A fifth round has not run against this text.** The owner approved the spec and
plan on 2026-09-11 and directed the build to proceed, accepting the review
economics recorded above: further rounds were auditing prior repairs rather than
the artifact.

## Delivery

**What this slice is, stated plainly:** discoverability, not procedure. It makes
the four legible as an ordered sequence on both surfaces. It does **not** make
the sequence walkable — see the Objective's narrowing above and slice S7.

Built 2026-09-11. All 22 criteria are ticked against observed evidence, not
against intent; every observation is recorded in
[`notes/verification-ledger.md`](notes/verification-ledger.md), including the
three mutation proofs, the resolved D1 count and D3 seam, the cold read, and the
gate results.

**AC-0026 is deliberately unticked, and the spec stays `Implementing`.** Its
observer is "a reviewer reading the two passages", and the author cannot be that
reviewer. The overlap it guards was found by the design review and repaired by
me; the repair is unreviewed. One independent read discharges it. Ticking it on
my own reading would be the exact failure this session has hit repeatedly —
verification that ratifies intent.

**Reopened 2026-09-11 after the design pass.** The craft sequence that should
have preceded this slice ran after it, and produced obligations no criterion
covered: the three groups collapsed without their headings, the page routed the
reader nowhere, the guides path's placement and its selection axis were both
undecided contracts. Shipping code governed by no criterion is the defect this
reopening closes. Four criteria were admitted, three obligations routed, and the
implementation verified against them rather than re-asserted.

**Shipped 2026-09-11 by owner decision**, with the narrowed Objective above. The
brief's Spec-map cell stays `<auto>`: the coverage roll-up derives that value
and it must not be hand-written.
