# Spec: the four disciplines read as one sequence

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none — this is the whole of its intent, not a slice
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Provenance

This spec delivers
[`four-discipline-sequence-surfaces`](../../product/intents/four-discipline-sequence-surfaces.md)
in full. That intent records why none of the adjacent intents owns this outcome,
and its unresolved question 1 carries the owner's order decision of 2026-09-10.

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
   `product-strategy` and `experience-design` appear in no path at all.
3. **Each step names what it hands the next**, so a reader can stop after any
   one of them and still know what they hold.

The order is the owner's decision, not a derivation. It conflicts with the
shipped P2 step order, which gathers evidence before shaping; outcome 2 carries
the obligation to state that difference rather than publish the two as agreeing.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — adopters read both surfaces | `guides/README.md` § the new path; `web/src/pages/journeys/index.astro` | `author-product-docs` conventions | Guide validators pass; page builds and renders | Both surfaces carry the sequence in the decided order |
| Current product truth | Applicable — the intent tracks this outcome | `docs/product/intents/four-discipline-sequence-surfaces.md` | This spec's owner | Intent's UQ1 records the order decision | Intent resolves through this spec's back-link |
| Reusable learning | Applicable — the membership-derivation rule is the reason a prior hardcoded list dropped five journeys | `docs/specs/four-discipline-sequence/notes/verification-ledger.md` | This spec's owner | Recorded run of the membership check with counts | Ledger records the collection count and the rendered count, and they match |
| Release history | **Not applicable** — `web/` and `guides/` are not published packs; no `pack.toml` or `plugin.json` version changes. Had the handoff copy required editing `packs/*/JOURNEY.md`, this row would apply to four packs; Boundary forbids that route | none | — | — | — |
| Decision rationale | **Not applicable** — the order decision is recorded in the intent's UQ1 by its owner; no architectural choice is made or reversed | none | — | — | — |
| Interface compatibility | **Not applicable** — no published URL, slug, or frontmatter key changes; the path is additive prose and the index page's grouping is internal to one component | none | — | — | — |

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
- Changing the decided order, which is the owner's and is recorded in the
  intent.

### Never do

- **Edit any file under `web/src/content/journeys/`.** They carry
  `generated: true` and are projected from `packs/*/JOURNEY.md` by
  `tools/build-site.py --journeys-only`. Editing one by hand either loses the
  edit at the next projection or turns this into a four-pack released change.
- **Add an image to either surface.** A guide cannot carry an image that renders
  on both GitHub and the docs site; the projector rewrites Markdown image paths
  into page URLs and copies no assets. The sequence reads as a sequence in text.
- **Claim first value or install success.** The dated Claude-apps
  install-to-first-value probe has not been run. Nothing here may assert that a
  reader who walks the sequence reaches a working artifact.
- **Describe the two plugin routes as equivalent.** `product-engineering` (3),
  `desk-research` (2) and `experience-design` (1) ship agents; Agent Plugins
  1.0.0 defines no agent component type, so three of the four are refused there.
- **Publish the new path and P2 as if their orders agreed.**
- **Introduce a new top-level directory or dependency.** Both surfaces exist.

## Testing Strategy

- **Grouping, order, ordered markup and accessible step position (AC1–AC4):**
  goal-based check over the built page on the `web/` vitest suite,
  `npm run test --prefix web`. The observation is the rendered HTML, because the
  criteria are about what a reader receives, not what the source says.
- **Membership derivation and exhaustiveness (AC5, AC6):** construction test on
  the same suite, comparing the `journeys` collection against the rendered
  cards. AC6's disconfirming input is a journey added to the collection and
  named in no group.
- **Guide path content (AC7–AC10):** goal-based check over `guides/README.md`
  itself. Prose placement and presence are mechanically checkable; whether the
  path is *followable* is a comprehension property and is AC11's.
- **Guide validity (AC12–AC14):** the three existing guide gates, each named
  separately because they inspect different contracts, fail differently, and are
  fixed differently.
- **The prohibitions (AC15–AC18):** whole-diff reads and one path-scoped
  `git diff`. AC17's observer is a diff over `web/src/content/journeys/`, which
  is a different failure from AC15's image check over the two edited files.
- **Link integrity (AC19):** `make site-link-check`.

**Known verification risk.** `make bootstrap-sites` currently exits 0 locally
without producing `build/docs/`, and four `web/` vitest cases already fail
locally as a result. Every built-HTML criterion above (AC1–AC6) observes through
that build. The plan must reproduce and resolve the bootstrap failure before
those criteria can be trusted locally; CI is green, so this is a local-evidence
risk, not a product defect.

No TDD-mode outcome for the guide half: it changes prose, and a unit test over
prose would assert its own fixture.

## Acceptance Criteria

- [ ] **AC-0001.** The journeys index renders the four disciplines in a group
      distinct from all other journeys, with a heading naming it as a sequence.
- [ ] **AC-0002.** Within that group the four appear in the order
      product-strategy, desk-research, experience-design, product-engineering.
- [ ] **AC-0003.** The group is an ordered list element, so the order is carried
      by the markup and not only by visual arrangement.
- [ ] **AC-0004.** Each of the four cards exposes its step position to assistive
      technology, so the position is not conveyed by a decorative number alone.
- [ ] **AC-0005.** Every journey in the `journeys` collection renders exactly
      once across all groups on the page.
- [ ] **AC-0006.** A journey present in the collection but named in no group
      still renders, in the catch-all group.
- [ ] **AC-0007.** `guides/README.md` carries an ordered path covering the four
      disciplines in the same order as AC-0002.
- [ ] **AC-0008.** That path states a prerequisite, a first-value moment and an
      "ends at", matching the shape P1–P6 already use.
- [ ] **AC-0009.** The path states, where a reader can see it, that its order
      differs from P2's, which gathers evidence before shaping.
- [ ] **AC-0010.** Each of the four steps, on both surfaces, names what it hands
      the next step.
- [ ] **AC-0011.** A cold reader who has seen only these two surfaces can name
      the four disciplines in order and state what one hands the next.
- [ ] **AC-0012.** `guides/README.md` frontmatter remains valid.
- [ ] **AC-0013.** `guides/README.md`'s `title` matches its leading H1.
- [ ] **AC-0014.** The guide index remains complete.
- [ ] **AC-0015.** Neither edited surface contains image syntax.
- [ ] **AC-0016.** No claim of first value, completed method, or successful
      install appears anywhere in the change.
- [ ] **AC-0017.** No file under `web/src/content/journeys/` is modified.
- [ ] **AC-0018.** No text in the change describes the Claude-plugins route and
      the Agent Plugins route as carrying the same packs.
- [ ] **AC-0019.** Every internal link emitted by the change resolves.

## Acceptance-set construction record

Run 2026-09-10, after the owner settled the sequence order. Obligations were
enumerated from the Objective's three outcomes, the non-waivable `Never do`
rails, and the applicable Durable Outputs; each was admitted only once an
observer could be named.

- **Candidate obligations:** 27
- **Admitted as criteria:** 19
- **Routed or merged:** 8

| Candidate obligation | Disposition | Criterion / owner | Red input | Observer |
| --- | --- | --- | --- | --- |
| The four render as a distinct group | admitted | AC-0001 | four still in one flat grid, or no group heading | built page |
| The group carries the decided order | admitted | AC-0002 | any adjacent pair transposed | built page |
| Order is in the markup, not only visual | admitted | AC-0003 | `<ul>`, or CSS-only ordering | built page |
| Step position reaches assistive tech | admitted | AC-0004 | number present but `aria-hidden` with no text equivalent | accessible name of each heading |
| No journey is dropped | admitted | AC-0005 | a collection journey rendering zero times, or twice | collection vs rendered cards |
| An ungrouped journey still renders | admitted | AC-0006 | new journey named in no group and absent from the page | fixture journey added to the collection |
| The guides carry the same sequence | admitted | AC-0007 | path absent, or ordered differently from AC-0002 | `guides/README.md` |
| The path matches the P-path shape | admitted | AC-0008 | any of prerequisite, first value, ends-at missing | `guides/README.md` |
| The P2 conflict is disclosed | admitted | AC-0009 | difference unstated where both paths are reachable | reader of the path |
| Each step names its handoff | admitted | AC-0010 | any step not naming what it passes on | both surfaces |
| A cold reader can restate the sequence | admitted | AC-0011 | order or any handoff unstatable | the reader |
| Guide frontmatter stays valid | admitted | AC-0012 | invalid or missing frontmatter | `validate_guides.py` |
| `title` matches the H1 | admitted | AC-0013 | the two diverge | `lint-guide-titles.py` |
| Guide index stays complete | admitted | AC-0014 | page missing from the index | `check-guide-index.py` |
| No image on either surface | admitted | AC-0015 | any image syntax in the two files | the two files |
| No first-value or install claim | admitted | AC-0016 | any such assertion | whole-diff read |
| Generated journey content untouched | admitted | AC-0017 | any modification under that path | `git diff -- web/src/content/journeys/` |
| The two routes are not equated | admitted | AC-0018 | text implying both carry all four | whole-diff read |
| Emitted links resolve | admitted | AC-0019 | any unresolved emitted link | `make site-link-check` |
| A diagram of the sequence | **routed** | `docs-site-build-contract-hardening/notes/guide-image-projection.md` | — | not this spec's; AC-0015 avoids the defect |
| Handoff copy inside journey content | **routed** | `packs/*/JOURNEY.md` + the pack release pipeline | — | not this spec's; a four-pack released change, fenced by AC-0017 |
| Sub-agent degradation on the chat surface | **routed** | `claude-plugin-route-scope/notes/subagent-present-but-unrunnable.md` | — | not this spec's; AC-0018 discloses, does not repair |
| A pack delivering first value | **routed** | `claude-apps-first-value-entry` | — | needs the unrun probe; AC-0016 fences it |
| Affordance uplift in the four packs' guides | **routed** | `sdlc-guide-uplift-and-learning-paths` S3–S5 | — | not this spec's; this adds a path over existing guides |
| The `digital-product` profile | **routed** | `digital-product-maker-profile` | — | CLI-only artifact; cannot serve a no-terminal reader |
| The integrative cross-pack tutorial | **routed** | `digital-product-guides-update` (RFC-0071 M6) | — | blocked behind unstarted M5 |
| Step-number styling and the 19-vs-20 count | **routed** | `plan.md`, as a discovery predicate | — | only the build can settle the count; styling is an implementation choice |

**Set-level result.** *Necessity:* every criterion names a red input above and
no two share one. AC-0012, AC-0013 and AC-0014 stay separate because the three
gates inspect different contracts and are fixed differently; AC-0015 and
AC-0017 both read a diff but assert different outcomes on different paths.
*Uniqueness:* one observer each. AC-0003 and AC-0004 are adjacent but distinct —
markup order is not an accessible name, and a page can pass either while failing
the other. *Consistency:* AC-0010 requires handoff copy while AC-0017 forbids
touching journey content; they coexist because the handoff is stated in the
hand-authored index copy and the guides path. *Joint feasibility:* AC-0015
forbids images and AC-0001 needs a legible group, which a heading and ordered
list satisfy without one. *Coverage both ways:* Objective outcome 1 reaches
AC-0001 to AC-0006; outcome 2 reaches AC-0007 to AC-0009; outcome 3 reaches
AC-0010 and AC-0011; each `Never do` rail reaches AC-0015 to AC-0018 or a routed
owner; the applicable Durable Outputs reach AC-0007, AC-0012 to AC-0014 and the
ledger row. Every criterion traces back to one of those.

## Accepted residuals

- **AC-0011's observer is a person.** No mechanical oracle exists for whether a
  reader can restate a sequence, and inventing one would compare the page to
  itself. Accepted as proportionate: the criterion can still fail, the two
  surfaces are named, and it adds no new class of verification burden beyond the
  cold read the repository already runs.
- **AC-0009 discloses a conflict rather than resolving it.** The right fix is
  one reconciled order across P2 and the new path, which changes a shipped path
  and belongs to `sdlc-guide-uplift`. Bounding it out and disclosing it is the
  honest move for this scope; recorded here so a later round does not re-raise
  it as an oversight.

Neither is a defect found late; both are judgements recorded when made.

## Assumptions

- The four journeys already say enough about their inputs and outputs that
  AC-0010's handoff copy can be written from existing material. If false,
  AC-0010 is the criterion that fails, and the response is to narrow it to the
  guides surface rather than to edit generated journey content.
- `guides/README.md` can carry a seventh path without a schema change, because
  P1–P6 are prose under headings and add no frontmatter key.

## Review status

**Not yet reviewed.** No round has run against this text.
