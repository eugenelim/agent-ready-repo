# Spec: the four disciplines read as one sequence

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** [`docs/product/briefs/sdlc-guide-uplift-and-learning-paths.md`](../../product/briefs/sdlc-guide-uplift-and-learning-paths.md)
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
published surfaces alone, that **product strategy → desk research → experience
design → product engineering** is one ordered sequence, and can walk it.

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

The order is the owner's decision, not a derivation. It conflicts with the
shipped P2 step order, which gathers evidence before shaping; outcome 2 carries
the obligation to state that difference rather than publish the two as agreeing.

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
- **Publish the new path and P2 as if their orders agreed.**
- **Introduce a new top-level directory or dependency.** Both surfaces exist.

## Testing Strategy

- **Grouping, order, ordered markup and accessible step position (AC-0001 to
  AC-0004):** goal-based check over the built page on the `web/` vitest suite,
  `npm run test --prefix web`. The observation is the rendered HTML, because the
  criteria are about what a reader receives, not what the source says.
- **Membership (AC-0005, AC-0006):** construction tests on the same suite.
  AC-0005 compares the multiset of collection slugs against the multiset of
  rendered card slugs — identity and multiplicity, not totals, because a count
  comparison passes when one journey is omitted and another duplicated.
- **Index and guide prose (AC-0007 to AC-0011):** goal-based checks over the two
  files. Presence and placement are mechanically checkable; whether the sequence
  is *followable* is a comprehension property and is AC-0012's.
- **Guide validity (AC-0013 to AC-0015):** the three existing guide gates, each
  named separately because they inspect different contracts, fail differently,
  and are fixed differently.
- **The prohibitions (AC-0016 to AC-0019):** two whole-diff reads and one
  path-scoped `git diff`.
- **Link integrity (AC-0020):** `make site-link-check`.

**Known verification risk.** `make bootstrap-sites` currently exits 0 locally
without producing `build/docs/`, and four `web/` vitest cases already fail
locally as a result. Every built-HTML criterion (AC-0001 to AC-0006) observes
through that build. The plan's T1 diagnoses it before those criteria are
trusted locally. CI is green, so this is a local-evidence risk, not a product
defect.

No TDD-mode outcome for the guide half: it changes prose, and a unit test over
prose would assert its own fixture.

## Acceptance Criteria

- [ ] **AC-0001.** The journeys index renders the four disciplines in a group
      distinct from all other journeys, under a heading naming it as a sequence.
- [ ] **AC-0002.** Within that group the four appear in the order
      product-strategy, desk-research, experience-design, product-engineering.
- [ ] **AC-0003.** The group is an ordered list element, so the order is carried
      by the markup and not only by visual arrangement.
- [ ] **AC-0004.** Each of the four cards exposes its step position to assistive
      technology, so the position is not conveyed by a decorative number alone.
- [ ] **AC-0005.** The multiset of journey slugs rendered on the page equals the
      multiset of slugs in the `journeys` collection.
- [ ] **AC-0006.** A journey present in the collection but named in no group
      still renders, in the catch-all group.
- [ ] **AC-0007.** On the index, each of the first three disciplines names what
      it hands the next, and the fourth names what the reader ends with.
- [ ] **AC-0008.** `guides/README.md` carries an ordered path covering the four
      disciplines in the same order as AC-0002.
- [ ] **AC-0009.** That path states a prerequisite, a `**First value:**` moment
      and an "ends at", matching the shape P1–P6 already use.
- [ ] **AC-0010.** The path states, where a reader can see it, that its order
      differs from P2's, which gathers evidence before shaping.
- [ ] **AC-0011.** In the path, each of the first three disciplines names what it
      hands the next, and the fourth names what the reader ends with.
- [ ] **AC-0012.** A cold reader who has seen only these two surfaces can name
      the four disciplines in order and state what one hands the next.
- [ ] **AC-0013.** `guides/README.md` frontmatter remains valid.
- [ ] **AC-0014.** `guides/README.md`'s `title` matches its leading H1.
- [ ] **AC-0015.** The guide index remains complete.
- [ ] **AC-0016.** Neither edited surface contains image syntax.
- [ ] **AC-0017.** No text in the change claims that a reader has reached first
      value, completed a method, or installed successfully. The structural
      `**First value:**` path label required by AC-0009 is not such a claim.
- [ ] **AC-0018.** No file under `web/src/content/journeys/` is modified.
- [ ] **AC-0019.** No text in the change describes the Claude-plugins route and
      the Agent Plugins route as carrying the same packs.
- [ ] **AC-0020.** Every internal link emitted by the change resolves.

## Acceptance-set construction record

Run 2026-09-11, after the owner routed this outcome into the brief. Obligations
were enumerated from the Objective's three outcomes, the non-waivable `Never do`
rails, and the applicable Durable Outputs; each was admitted only once a single
observing surface could be named.

- **Candidate obligations:** 30
- **Admitted as criteria:** 20
- **Routed:** 10

| Candidate obligation | Disposition | Criterion / owner | Red input | Observer |
| --- | --- | --- | --- | --- |
| The four render as a distinct group | admitted | AC-0001 | four still in one flat grid, or no group heading | built page |
| The group carries the decided order | admitted | AC-0002 | any adjacent pair transposed | built page |
| Order is in the markup, not only visual | admitted | AC-0003 | `<ul>`, or CSS-only ordering | built page markup |
| Step position reaches assistive tech | admitted | AC-0004 | number present but `aria-hidden` with no text equivalent | accessible name of each card heading |
| No journey dropped or duplicated | admitted | AC-0005 | one slug omitted, or one rendered twice | slug multiset comparison |
| An ungrouped journey still renders | admitted | AC-0006 | catch-all replaced by a hardcoded list | the rendered page under a fixture journey |
| The index names each handoff | admitted | AC-0007 | any of the first three not naming what it passes on, or the fourth not naming its end state | the index page copy |
| The guides carry the same sequence | admitted | AC-0008 | path absent, or ordered differently from AC-0002 | `guides/README.md` |
| The path matches the P-path shape | admitted | AC-0009 | any of prerequisite, first value, ends-at missing | `guides/README.md` |
| The P2 conflict is disclosed | admitted | AC-0010 | difference unstated where both paths are reachable | `guides/README.md` |
| The path names each handoff | admitted | AC-0011 | any of the first three not naming what it passes on, or the fourth not naming its end state | `guides/README.md` |
| A cold reader can restate the sequence | admitted | AC-0012 | order or any handoff unstatable | the reader |
| Guide frontmatter stays valid | admitted | AC-0013 | invalid or missing frontmatter | `validate_guides.py` |
| `title` matches the H1 | admitted | AC-0014 | the two diverge | `lint-guide-titles.py` |
| Guide index stays complete | admitted | AC-0015 | page missing from the index | `check-guide-index.py` |
| No image on either surface | admitted | AC-0016 | any image syntax in the two edited files | image-syntax scan over the change |
| No adopter-outcome claim | admitted | AC-0017 | any first-value, completed-method or install-success assertion | whole-diff read |
| Generated journey content untouched | admitted | AC-0018 | any modification under that path | `git diff -- web/src/content/journeys/` |
| The two routes are not equated | admitted | AC-0019 | text implying both carry all four | whole-diff read |
| Emitted links resolve | admitted | AC-0020 | any unresolved emitted link | `make site-link-check` |
| A diagram of the sequence | **routed** | `docs-site-build-contract-hardening/notes/guide-image-projection.md` | — | not this slice's; AC-0016 avoids the defect |
| Handoff copy inside journey content | **routed** | `packs/*/JOURNEY.md` + the pack release pipeline | — | a four-pack released change, fenced by AC-0018 |
| Sub-agent degradation on the chat surface | **routed** | `claude-plugin-route-scope/notes/subagent-present-but-unrunnable.md` | — | AC-0019 discloses; it does not repair |
| A pack delivering first value | **routed** | `claude-apps-first-value-entry` | — | needs the unrun probe; AC-0017 fences it |
| Affordance uplift in the four packs' guides | **routed** | sibling slices S3–S5 of this brief | — | this slice adds a path over existing guides |
| The `digital-product` profile | **routed** | `digital-product-maker-profile` | — | CLI-only artifact; cannot serve a no-terminal reader |
| The integrative cross-pack tutorial | **routed** | `digital-product-guides-update` (RFC-0071 M6) | — | blocked behind unstarted M5 |
| No new top-level directory or dependency | **routed** | the repository decision process (root `AGENTS.md`: "Propose a new top-level directory through the repository decision process"); a dependency needs its owning manifest or an ADR | — | pre-existing repository control; this slice adds neither |
| The 19-vs-20 collection count | **routed** | `plan.md` § D1, as a discovery predicate | — | only the build can settle it |
| Step-number styling and the dropped `list-style` rule | **routed** | `plan.md` § D2, as a discovery predicate | — | an implementation choice, not a contract obligation |

**Set-level result.** *Necessity:* each criterion states its whole failure
predicate above — input, expected outcome, observing surface — and no sibling
enforces the same predicate. AC-0005 and AC-0006 can both red on a missing
journey, which the contract permits: two controls may share an input while
asserting different outcomes. AC-0005 asserts exhaustiveness over the current
collection; AC-0006 asserts that the catch-all mechanism exists, and its red
input is the hardcoded-list mutation, not an omission. *Uniqueness:* every
criterion names exactly one observing surface. AC-0003 and AC-0004 are adjacent
but distinct — markup order is not an accessible name, and a page can pass
either while failing the other. AC-0007 and AC-0011 state the same obligation on
two surfaces and are therefore two criteria with one observer each, not one
criterion with two. *Consistency:* AC-0009 requires a `**First value:**` label
while AC-0017 forbids first-value claims; the Boundary rail states the
distinction explicitly, so the two coexist. AC-0007 and AC-0011 require handoff
copy while AC-0018 forbids touching journey content; they coexist because the
copy is hand-authored on the index page and in the path. *Joint feasibility:*
AC-0016 forbids images and AC-0001 needs a legible group, which a heading and an
ordered list satisfy without one. *Coverage both ways:* Objective outcome 1
reaches AC-0001 to AC-0006; outcome 2 reaches AC-0008 to AC-0010; outcome 3
reaches AC-0007, AC-0011 and AC-0012; the six `Never do` rails reach AC-0018,
AC-0016, AC-0017, AC-0019, AC-0010 and the routed repository-decision row
respectively; the three applicable Durable Outputs reach AC-0008, AC-0013 to
AC-0015, and the ledger row. Every criterion traces back to one of those.

## Accepted residuals

- **AC-0012's observer is a person.** No mechanical oracle exists for whether a
  reader can restate a sequence, and inventing one would compare the page to
  itself. Accepted as proportionate: the criterion can still fail, the two
  surfaces are named, and it adds no new class of verification burden beyond the
  cold read the repository already runs.
- **AC-0010 discloses a conflict rather than resolving it.** The right fix is one
  reconciled order across P2 and the new path. That changes a shipped path, and
  although P2 is now under the same brief, reconciling it would reopen delivered
  work rather than add a slice. Bounding it out and disclosing it is the honest
  move for this scope; recorded here so a later round does not re-raise it.

Neither is a defect found late; both are judgements recorded when made.

## Assumptions and undischarged risks

- The four journeys already say enough about their inputs and outputs that
  AC-0007 and AC-0011's handoff copy can be written from existing material. If
  false, those are the criteria that fail, and the response is to narrow them to
  the guides surface rather than to edit generated journey content.
- `guides/README.md` can carry a seventh path without a schema change, because
  P1–P6 are prose under headings and add no frontmatter key.
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

**One Sol round ran against an earlier, differently-scoped draft** of this spec,
when it was a standalone intent rather than slice S6. It returned three blocking
and nine major findings. The rescope answers the blocking ownership finding at
its root; the remaining sustained findings are applied in this text.

**Rescoping restarts the rounds.** This text is therefore **unreviewed**, and
the count above is prior-round history, not a clean verdict on what is written
here.
