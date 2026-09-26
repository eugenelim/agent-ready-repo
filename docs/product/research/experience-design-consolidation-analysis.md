# Router impact analysis — folding design-adjacent skills

- **Status:** analysis only. This document changes no skill registration.
- **Decider:** repository maintainer.
- **Route:** **errata on the RFCs that created the skills** — RFC-0066 D4 for
  the genre skills, RFC-0062 for the copy cluster — not a new or superseding
  RFC (owner decision, 2026-09-24). The change still obliges a major version
  bump, because removals are major; the erratum records the governance change,
  not the release mechanics.
- **Delivered by:** [`xd-genre-router`](../../specs/xd-genre-router/spec.md) and
  [`xd-copy-router`](../../specs/xd-copy-router/spec.md), coordinated by
  [`experience-design-skill-consolidation`](../briefs/experience-design-skill-consolidation.md).
- **Date:** 2026-09-24.
- **Measured against:** `packs/experience-design/` at `2.0.9`, twenty skills.

**Why erratum rather than a new RFC.** The repository already discharges a
superseded decision this way. RFC-0066's own 2026-07-27 erratum records that a
rename D7 said would need "a separate product-engineering RFC" instead shipped
through an implementation spec citing D7 plus ADR-0038 as governing authority,
and the erratum discharges the requirement. RFC-0011 carries two post-merge
errata that reverse a decision outright. An erratum is the established
instrument for "this Accepted decision no longer holds". The owner's ground is
that the routing mechanism these folds use is already shipped and only its
targets move.

An independent review disputes that this suffices, holding that retiring
registrations originates a new decision rather than recording where an
authorised one landed, and that a fresh RFC is the instrument for that. The
owner decided errata on 2026-09-24 and the decision stands; the objection is
recorded here so this note and the specs that cite it agree.

## Why this exists

The `creative-direction` delivery this note sits under was scoped to one skill.
While investigating it, four measurements and one field observation came up that
bear on a larger question: whether the pack should present one router with modes
instead of twenty separately registered skills. They are recorded here because
they were paid for and would otherwise be lost, not because this delivery acts
on them.

## How each figure was produced

Every number below was taken against `packs/experience-design` at `2.0.9` on
2026-09-24 by the method named beside it. A figure whose method is not stated is
not evidence. One caveat: the Jaccard rows depend on a stopword list held only in
the throwaway script that produced them, so those two figures are indicative
rather than independently reproducible.

| Figure | Method |
| --- | --- |
| Resident description bytes | Sum of the byte length of each skill's `description:` frontmatter value, quotes stripped, across every `SKILL.md` in the pack. Counting the raw YAML line instead gives ~15,008; the difference is quote and key handling. |
| Always-loaded body bytes | File bytes minus the frontmatter block minus the managed `agentbundle:output-rendering` block, inclusive of both delimiter comments. |
| Copies and distinct versions | `find` by filename, then MD5 per file; distinct-hash count. |
| Differing lines between two files | `diff <a> <b> \| grep -c '^[<>]'`, which counts changed lines on **both** sides rather than a one-directional edit distance. |
| Line identity between two skills | Python `difflib.SequenceMatcher` over line lists, matching blocks summed and divided by the longer file's line count. |
| Activation-prose overlap | Jaccard index over lowercased content words (`[a-z][a-z-]{2,}`) from each skill's `description:`, after removing a 40-term stopword list of framing words common to every description ("use", "when", "produces", "belongs", and similar). |

The activation-prose figures were computed for three named clusters only. The
twenty skills were never compared pairwise, so no figure here supports a
pack-wide ranking claim.

## Prior-art study

A structural study of how comparable design guidance is packaged was run on
2026-09-24. Method: read one mature, permissively licensed design-skill
distribution end to end — its skill source, reference tree, plugin manifests and
adapter projections — and record how it divides always-loaded material from
on-demand material, and what it does to avoid converging on category defaults.

Findings that bear on this repository:

- The same ground is covered by **one registered skill with one description**.
  Roughly two dozen operations are rows in a table inside an 89-line `SKILL.md`,
  each pointing at a reference file, with about 5,100 lines of method behind
  them. The one projected command delegates back to the skill.
- Routing is three rules: no argument shows a menu and never auto-runs; a named
  operation loads exactly its reference; anything else is treated as general
  work.
- Convergence is resisted by naming the category default *and* its predictable
  opposite and excluding both, by deriving referents from the audience's world
  rather than the software category, and by keeping a standing "category
  standard, played straight" option the agent may never recommend.

**Status of this section.** The study's source is not named here, so nothing in
it can be re-checked by a later reader. Every statement above is therefore an
**unverifiable assumption**, not a measured finding, and none of it is carried
in the brief's provenance or used to size anything. It is kept because it
records where the shape came from.

**Licence handling.** The licences examined attach their attribution obligation
to reused text, not to reused ideas. Only mechanisms were taken, rewritten in
this repository's own voice, so no attribution notice is incurred. That reading
is part of the same unverifiable assumption — it is not legal advice and no
criterion rests on it.

## What was measured

### Resident cost

Every installed skill's `description` sits in the host's skill index for the
whole session, whether or not any design work happens.

| Pack | Skills | Description bytes resident | Approx. tokens |
| ---: | ---: | ---: | ---: |
| `experience-design` | 20 | 14,966 | 3,742 |
| `product-engineering` | 15 | 9,344 | 2,336 |
| `desk-research` | 12 | 8,927 | 2,232 |
| `core` | 18 | 8,036 | 2,009 |

`experience-design` is the largest resident description surface in the
catalogue. For comparison, the entire `creative-direction` `SKILL.md` — loaded
only after activation — is 13,085 bytes. The always-resident cost of the pack's
index exceeds the on-demand cost of its largest skill.

For comparison, see § *Prior-art study* above: the same ground is covered
elsewhere by a single registered skill with one description.

### Duplication and drift

| Shared file | Copies | Distinct versions |
| --- | ---: | ---: |
| `references/containment.md` | 5 | **1** |
| `references/agentbundle-layout.md` | 12 | **9** |
| managed output-rendering block | 20 | — (51,060 bytes total) |

The asymmetry is the finding. `containment.md` has not drifted across five
copies because `test_experience_design_write_declaration_and_containment.py`
asserts byte equality. `agentbundle-layout.md` — the same adopter-facing
resolution contract — has no such test and now exists in nine different
versions across twelve copies.

Duplication did not cause the drift. The absence of a test did. That is worth
separating, because a router would remove the duplication but a byte-equality
test would remove the drift, and the second is far cheaper.

### Genre-skill similarity

The six genre-direct skills are 35–50% line-identical to one another. Much of
that is the 30-line managed block each one carries, so the figure overstates
substantive overlap; the genre-specific reasoning in each is real.

### Activation-prose overlap

Jaccard similarity over content words in each skill's `description`:

| Cluster | Mean | Highest pair |
| --- | ---: | --- |
| copy cluster (`content-design`, `copy-direction`, `tone-of-voice`) | 0.31 | `content-design` / `copy-direction` — **0.35** |
| direction cluster (`creative-direction`, `design-system`, `design-principles`, `design-review`) | 0.20 | `creative-direction` / `design-system` — **0.27** |
| genre skills (six) | 0.16 | `documentation-design` / `informational-design` — 0.23 |

This cuts against the intuition. The descriptions are *not* especially similar,
because each was written with explicit boundary prose ("use X for Y, not Z").
By this measure the genre skills are the **least** confusable of the three
clusters scored.

So prose similarity is the wrong criterion for the genre skills. Their case
rests on coupling and drift instead. It is the right criterion for the copy
cluster, the most confusable of the three — and the pack's own
`DESIGN.md` § 4 carries a section titled "Content-design vs. tone-of-voice vs.
copy-direction vs. ux-writing", which exists because the boundary is not
self-evident. A section whose job is to tell four skills apart is evidence about
those four skills.

### The coupling is already stale

`frontend-engineering`'s genre-routing table names four of the pack's six genre
skills:

| Genre skill | Routed from the frontend pre-flight |
| --- | --- |
| `analytical-design` | yes |
| `conversion-design` | yes |
| `documentation-design` | yes |
| `informational-design` | yes |
| `marketplace-design` | **no** |
| `workspace-design` | **no** |

A listing, search, or transactional surface, and a productivity workspace
surface, get no genre routing from the frontend pre-flight. No test covers
routing-table completeness, so the gap is silent and nothing dates it.

This is the strongest argument in the note. Name-by-name coupling across packs
went stale without anyone noticing. A router would let `frontend-engineering`
name one skill and pass a genre, and a new genre would be reachable on the day
it ships.

### Field evidence: what real sessions produced

The repository's own design artifacts, produced by real sessions, are under
`docs/design/`. One engagement (`team-orientation`) produced 45 files across
eight folders and roughly 29 distinct `type:` values.

Two things in that corpus matter.

**Genre is already a routing parameter on both sides.** Artifacts carry
`surface-genre: marketing` or `surface-genre: documentation` in frontmatter,
consistently, across screen briefs, content briefs and direction amendments —
and `information-architecture/SKILL.md` step 1 already routes on that field
through a seven-row table.

An earlier draft of this note claimed the data model and the skill model
disagreed about whether genre was a parameter. That was wrong: the routing table
already ships. What is still modelled as six registrations is only the method
each row points at. The correction strengthens the case rather than weakening
it — a fold completes a migration the pack began, instead of proposing a new
mechanism, and that is also why an erratum is the proportionate instrument.

**Composition is hand-rolled, differently each time.** With no relationship
model in the pack, individual artifacts invented their own linking vocabulary in
frontmatter: `amends`, `builds-on`, `governed_by`, `verifies`, `direction`,
`invalidated-by`, `voice_chart`, `brand_register`, `state_matrix`. One screen
brief records its own split in prose — "IA half here, interaction half enriched
in `screens/team-orientation/operating-model-canvas.md`" — with a `gap:` marker
beside it.

That is the reported experience, visible in the files: a marketing and technical
website needing `copy-direction`, `content-design`, `information-architecture`
and `interaction-design` together, with nothing to link them. The difficulty is
not only picking the skill. It is that four skills produce four artifacts with
no contract describing how they compose, so each session improvises one.

**A router alone would not fix this.** Consolidating registrations makes the
skills easier to find; it does not give their outputs a relationship model. The
composition contract is a separate, and probably larger, piece of work. Treating
the router as the fix for the linking problem would ship the cheaper half and
declare the problem solved.

## The recorded decision this has to answer

`packs/experience-design/DESIGN.md` § 10 records: *"Why six genre-direct skills
instead of one general IA skill with genre flags"*, rejecting the alternative
because a flag-parameterised skill *"would bury the genre logic; separate skills
make it first-class."*

That rejection targets flags, not progressive disclosure. Under the router shape,
each genre's structural logic stays a first-class, separately reviewable document
in `references/`, loaded only when that genre is selected. What disappears is the
registration, not the document.

The rationale entry should be amended to say so rather than quietly contradicted.
Whether the conclusion changes is the maintainer's call; the premise it rejected
is not the premise a router proposes.

## A first fold, scoped

The criterion used below: fold where the skills share one output contract and one
decision, or where external coupling is already breaking. Keep separate where the
output is a distinct artifact with distinct downstream consumers.

| Skills | Verdict | Reason |
| --- | --- | --- |
| The six genre skills | **Fold first** | Coupling to `frontend-engineering` is already stale and untested; genre is already a frontmatter field; all six replace exactly one step (the IA step) and none has its own output contract — they write the same IA artifact. Folding them makes the cross-pack contract one name plus a genre. |
| `content-design`, `copy-direction`, `tone-of-voice` | **Fold second** | Highest activation overlap of the three clusters measured — mean 0.31, highest pair 0.35 — and the pack already ships a section to disambiguate them. Distinct outputs, so the fold is a router over three modes, not a merge of three artifacts. |
| `creative-direction`, `design-system` | **Keep separate** | Sequential, not overlapping. Two distinct artifacts (`direction/<slug>.md` with `type: creative-direction`; `tokens/<slug>.md` with `type: token-taxonomy`) that `frontend-engineering` reads through two separate slots of its handoff contract, and that a human approves at two different gates. Overlap of 0.27 is sequence adjacency, not ambiguity. Folding would merge the approval points, which is where the direction/values separation lives. |
| `design-review` | **Keep separate** | It is the critique half and pairs with the forked `experience-reviewer` agent. Folding a reviewer into the authoring router invites the authoring session to mark its own homework, which § 6 of `DESIGN.md` exists to prevent. |
| `journey-mapping`, `service-blueprint`, `process-mapping`, `user-flow` | **Out of scope** | Upstream discovery, not creative design. The user scoped this round to the design-adjacent skills. |
| `experience-status` | **Keep separate** | Read-only orientation over the artifact tree; it is how a session finds what the others wrote. |

On `design-system` specifically, asked directly: yes, it earns its registration —
but on the strength of its output contract and its approval gate, not on the
strength of its description. If the fold ever reaches it, the thing to preserve
is the two-gate structure, not the two skills.

## What would settle it

The one objection that could kill the router is activation accuracy: twenty
descriptions are twenty chances for the host to match a user's phrasing, and one
router description must carry all of it.

That is measurable before committing, with an instrument the pack already ships.
`evals/eval_queries.json` in each of the twenty skills holds labelled trigger
queries, and the Tier-A harness grades a query as passing when its trigger rate
exceeds 0.5:

```bash
python -m agentbundle pack evals run --pack experience-design
```

The experiment: write a candidate router description, pool the positive queries
from the skills proposed for folding, and measure the router's trigger rate
against that pool. Compare to the current per-skill baseline from the same
harness. A router that holds its trigger rate answers the objection with data; a
router that drops it has failed cheaply, before any restructure.

Run the baseline first. It costs one harness run and is worth having regardless
of what the maintainer decides.

## Cost if it proceeds

- **Governance, by erratum.** RFC-0066 D4 and RFC-0062 each take an
  approver-signed erratum recording that the registrations they created are
  retired. RFC-0071 carries the skill inventory in its operative text and takes
  one too. **An erratum names no spec and no brief**: those are delivery-time
  artifacts that get archived and pruned, so an RFC pointing at one decays into
  a dangling reference, and the RFC is the durable record. It states the
  decision change, the date, and the approver, and stands alone for a reader who
  has only the RFC. **RFC-0055 D2 governs the shape**: once an
  Errata section holds more than one entry, or any entry supersedes another, it
  converts to the two-layer `### Current state` / `### History` form — both
  conditions fire here, so a plain appended bullet is not sufficient.
- **Major version bump.** Removing skill registrations is a removal under
  `packs/AGENTS.md` § Version bump rule. Two sequential folds mean two majors:
  the genre fold takes `3.0.0` and the copy fold `4.0.0`.
- **Cross-pack change.** `frontend-engineering`'s genre-routing table, its named
  skip text, and `guides/frontend-engineering/` all name the folded skills.
- **Surfaces to update in the same change:** `pack.toml` `[pack.evals]`,
  `DESIGN.md` §§ 5 and 10, `JOURNEY.md`, `README.md`, the guide tree, the
  marketplace projection, `web/src/content/`, and the roster suites that walk the
  skill set.
- **Not covered by the fold:** the composition contract. See the field-evidence
  section; that is the larger piece and should not be folded into this decision.

## Recommended next step

Run the Tier-A baseline, then take the six genre skills first, under an erratum
on RFC-0066 D4. That is the fold with an already-broken external contract to
fix, the clearest criterion, and the smallest blast radius. The copy cluster is
a better second round once the first has a measured activation result behind it.

An earlier draft of this section recommended opening an RFC. That was superseded
on 2026-09-24 by the owner decision recorded in the Route header above, and the
recommendation is corrected here rather than left to contradict it.
