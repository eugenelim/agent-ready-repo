# Brief: Experience-design skill consolidation

- **Slug:** `experience-design-skill-consolidation`
- **Received:** 2026-09-24
- **Owner:** Repository maintainers (`ini-003`)
- **Status:** Ready
- **Source / provenance:** Direct maintainer request, 2026-09-24, after an investigation into `creative-direction` measured the pack and found the larger lever outside that skill. The measurements and their methods are recorded in [`experience-design-consolidation-analysis.md`](../research/experience-design-consolidation-analysis.md), which is this brief's durable evidence. That note also records a prior-art study whose source is unnamed; it informed the shape of the standalone `creative-direction` slice, is unverifiable by a later reader, and is **not** part of this brief's evidence.
- **Parent intent:** none — raised directly, not projected from an intent.

## Outcome

Someone doing design work in this pack picks from twelve entry points instead of
twenty, and every surface genre the taxonomy defines is reachable from the
frontend pre-flight — including the two that no caller can reach today. No
design method is removed; what disappears is the registration, not the document.

## Success metrics

- Registered skills fall from 20 to 12.
- All seven `surface-genre` values are reachable from `frontend-engineering`'s
  pre-flight; two are unreachable today.
- Each fold's Tier-A activation pass rate is no worse after than before, on both
  the positive and the negative query sets. A fold failing this does not ship.
- No genre's structural logic and no copy-layer rule is deleted; each survives in
  a first-class reference.
- Five same-named duplicate references in the copy layer become one copy each,
  plus the two-name jobs-to-be-done pair, with a test holding the one that stays
  shared. A sixth shared name, `agentbundle-layout.md`, is reduced by the
  deletions rather than reconciled.

## Scope / Non-goals

**In scope:**

- S1 — fold six genre skills and `information-architecture` into one
  genre-aware skill; repair `frontend-engineering`'s genre routing.
- S2 — fold `content-design`, `copy-direction` and `tone-of-voice` into one
  copy-layer skill with three modes, reconciling the drifted shared references
  that block it.
- Three errata: RFC-0066 D4, RFC-0062, and RFC-0071, each carrying the skill
  inventory or a decision the folds reverse.
- `DESIGN.md`, file-wide, per each spec's acceptance criteria. Section-scoped
  edits miss § 1's sequence diagram and dependency list and § 7's artifact
  table, none of which name a skill by slug.
- Version bumps in three packs, attributed per slice and levelled per the rule.
  `experience-design` takes a **major** from each fold, because each removes
  registrations. `frontend-engineering` takes a **patch** (`0.3.2 → 0.3.3`) from
  **S1 only**, which edits its routing table, sentinel and README.
  `product-engineering` takes a **patch** (`0.13.17 → 0.13.18`) from **S2 only**,
  which retargets `ux-writing`. Neither cross-pack change removes a primitive, so
  neither is a major. S2 touches no `frontend-engineering` file.

**Non-goals:**

- The `creative-direction` uplift. It shares no outcome with this brief and
  ships as a standalone spec, `docs/specs/creative-direction-modes/spec.md`,
  ahead of both folds. Two couplings remain, neither an outcome: it edits five
  of the same files, and it hands `DESIGN.md` § 10 to S1 by carrying a criterion
  forbidding itself to touch that section, making S1 § 10's only editor.
- A composition contract for design artifacts. See [Rabbit
  holes](#rabbit-holes); it is the larger problem and no fold addresses it.
- Folding `design-system`, `design-review`, `design-principles` or
  `interaction-design`. Each was assessed and kept — the analysis records why.
- The discovery and flow skills (`journey-mapping`, `service-blueprint`,
  `process-mapping`, `user-flow`).
- Renaming the pack, changing the `surface-genre` taxonomy, or changing any
  output artifact's path or `type:`.
- Pack-wide reference deduplication beyond what the copy fold needs. See
  [What this takes from the sibling brief](#what-this-takes-from-the-sibling-brief)
  for the exact boundary — it is narrower than "leave S8a alone" and the
  difference matters.

## Constraints / Appetite

**Two slices, roughly three weeks each, sequenced.** The window starts when that
slice's spec reaches `Approved` — both specs' abort criteria cite that instant,
because a duration with no origin is a judgement gate wearing a number.

A fold that cannot land inside its window is abandoned rather than extended.
Each fold aborts on either trigger — a failed activation gate, or the window
elapsing — and each leaves its own residue.

- **S1's residue:** the six directories stay, and the non-fold half ships alone —
  the `frontend-engineering` routing repair, the `design-system-foundations`
  slug correction, and that pack's patch bump, without the erratum or the
  `experience-design` major.
- **S2's residue:** nothing ships. It has no separable repair to land alone, and
  saying so is what prevents a partial fold.

**An S1 abort also blocks S2.** S2 depends on S1 relocating
`editorial-quality-gates.md` under `information-architecture` and citing it
there. An aborted S1 leaves that file with `conversion-design` and the
relocation undone, so S2 waits until the relocation ships as its own change.

Sequencing is load-bearing rather than preference. Both folds and the
`creative-direction` spec edit five of the same files — `DESIGN.md`,
`pack.toml`, `.claude-plugin/plugin.json`, the changelog, and
`.apm/agents/experience-reviewer.md` — and each carries a version bump, so they
cannot run in parallel.

Hard constraints carried by both slices:

- **Errata, not superseding RFCs** (owner decision, 2026-09-24). The ground is
  that the routing mechanism these folds use is already shipped and only its
  targets move. An independent reviewer disputes that this suffices — see
  [Assumptions / Risks](#assumptions--risks); the objection is recorded, not
  resolved.
- **An erratum names no spec and no brief** (owner decision, 2026-09-24). Those
  are delivery-time artifacts that get archived and pruned, so an RFC pointing at
  one decays into a dangling reference. This corrects the convention: RFC-0066's
  existing 2026-07-27 entry does cite a spec path, and new entries do not follow
  it in that respect.
- **RFC-0055 D2 governs errata shape.** Once a section holds more than one entry,
  or any entry supersedes another, it converts to the two-layer
  `### Current state` / `### History` form. Both conditions fire on all three
  RFCs, so a plain appended bullet is not sufficient.
- **No aliases or deprecation shims** for removed skill names (ADR-0038), so
  each sweep must be complete within its own PR.
- **Frozen records are not rewritten.** The test is lifecycle class, not
  directory: a shipped spec, an Accepted RFC and a closed ADR are amended only by
  erratum, while a live record — including `docs/product/journeys/designer-designs-surface.md`,
  which RFC-0066's follow-on designates the single source of truth for the design
  chain — is updated.
- **No values in pack content** (RFC-0033 / ADR-0024, enforced by
  `tools/lint-experience-agnostic.py`).
- **Each fold is gated on its own activation measurement**, run before any
  directory is deleted.

## Current-state evidence

Measured against `experience-design` at `2.0.9` on 2026-09-24. Every method is
stated in the analysis's `How each figure was produced` table; figures without a
stated method are not carried here.

| Measure | Value | Bears on |
| --- | ---: | --- |
| Registered skills | 20 | S1, S2 |
| Resident description bytes, every session | 14,966 (~3,742 tokens) | S1, S2 |
| Genre skills reachable from `frontend-engineering` | 4 of 6 | S1 |
| Copy-layer references shared under one name and drifted | 6 of 6 | S2 |
| Of those, reconciled by S2 | 5 | S2 |
| Of those, reduced but not reconciled | 1 — `agentbundle-layout.md` | S2 |
| Copy-layer references shared under two names | 1 pair | S2 |
| `copy-arbitration.md` divergence | 37 changed lines, both sides, between files of 33 and 42 lines | S2 |
| Activation-prose overlap, copy cluster | mean 0.31, highest pair 0.35 — highest of three clusters scored | S2 |
| Activation-prose overlap, genre skills | mean 0.16 — lowest of three clusters scored | S1 |

The pack's always-resident description index (~3,742 tokens) costs more per
session than `creative-direction`'s body (~3,256 tokens), the largest measured,
which loads only on activation. That
is what makes the registration count, rather than any skill's size, the lever.

One measured result cut against the initial hypothesis and is kept because it
changed the plan: the genre skills are the **least** confusable of the clusters
scored, not the most. Their descriptions carry explicit "use X, not Y"
boundaries. So S1 rests on coupling and drift, and S2 on prose confusability.

## Confirmed delivery slices

**S1 — genre fold.** `DESIGN.md` § 5 already states the six genre skills "are a
replacement for `information-architecture` only", and
`information-architecture/SKILL.md` already routes on `surface-genre:` through a
seven-row table. So seven registrations occupy one step, and the routing
mechanism is already shipped — only what each row points at is still modelled as
six registrations. Meanwhile `frontend-engineering` routes to four of the six,
leaving listings/search and workspace surfaces with no genre routing, uncaught
because no test covers routing-table completeness.

**S2 — copy fold.** The three copy skills are the most confusable of the clusters
scored, and `DESIGN.md` § 4 ships a section whose only job is telling them apart.
The decisive evidence is drift: five same-named references, none identical, plus
a sixth pair under two names. S2 gives the shared method one copy and keeps three
distinct output artifacts.

## What this takes from the sibling brief

[`digital-experience-doctrine-completion`](digital-experience-doctrine-completion.md)
owns pack-wide reference deduplication as its S8a candidate, decomposed there as
eight families. This brief does **not** defer all of it, and saying so plainly
matters because nothing re-reads prose that records an obligation.

S2 executes two of those families:

- `editorial-quality-gates` — 3 copies / 3 hashes today, **2/1** after. One copy
  lives under `conversion-design`, which S1 deletes, so S1 relocates it to
  `information-architecture` and cites it there, and S2 reconciles the pair
  behind a byte-equality suite. The file survives only because S1 moves it;
  neither slice may assume the other did.
- `interrogation-sequence` — 3 copies / 3 hashes today, **2 copies** after. S2
  reconciles the two copy-layer instances into one; the `creative-direction`
  variant is left alone, so the family shrinks rather than closing.
- the jobs-to-be-done pair — `copy-direction/audience-jtbd.md` and
  `tone-of-voice/copy-jtbd.md` merge into one file named `copy-jtbd.md`.
  Deliberately **not** `audience-jtbd.md`: `creative-direction` holds a third
  file of that basename, pinned by the standalone spec, so reusing the name
  would open a new family instead of closing one.

S2 also reduces a fourth family without reconciling it: deleting two skill
directories removes two `agentbundle-layout.md` copies, taking that family from
12 copies to 10, with its hash count measured at delivery. Three further
families — `copy-arbitration`, `copy-grounding`, `plain-language-floor` — exist
only in the two folded skills and drop to one copy each, leaving the duplicate
set entirely. Eight families become five. The remaining families stay outside this brief — though not with the
sibling either. `digital-experience-doctrine-completion` routes S8a **out** of
itself to an intake candidate named `experience-design-reference-reconciliation`,
which has no admitted intent yet, so those families are currently unowned.

S2 carries an acceptance criterion to amend that brief's own re-check and
Adjacent-work rows with post-fold counts, because `docs/product/AGENTS.md` is
explicit that an obligation on a sibling is discharged by changing the sibling's
cell — nothing re-reads the prose that recorded it.

## Assumptions / Risks

- **Risk — one description activates worse than several.** The single objection
  that can defeat either fold. Mitigated by measurement: each spec runs the
  Tier-A baseline before deleting anything, reports the lowest of three runs, and
  refuses to ship on a worse pooled figure on either the positive or the negative
  set. Over-triggering, not under-triggering, is the expected failure mode of one
  broad description. Tier-A needs the `claude` CLI on PATH, so CI cannot re-check
  the figure and the abort path is the only backstop.
- **Risk — a genre's method is thinned in transit.** Both folds forbid reducing
  method to a summary and make preservation a manual-QA criterion with a named
  reviewer.
- **Risk — an incomplete sweep ships a dangling name.** No aliases are
  permitted, so a missed reference is a broken link rather than a soft failure.
- **Risk — adopters already have the removed skills installed.** Whether
  `agentbundle` prunes a directory the pack no longer declares is unverified;
  S1 records the observed behaviour and the changelog states the manual step if
  it does not. An unpruned stale skill keeps activating against a method the pack
  no longer ships.
- **Risk — two of `ini-003`'s own queued intents cite files these folds rewrite.**
  Of the initiative's seven backlog intents, two touch fold-affected surfaces.
  [`xd-ia-archetypes-objects`](../intents/xd-ia-archetypes-objects.md) (M3c)
  carries an `Observed state` table dated 2026-09-20 with two live line-range
  citations — `information-architecture/SKILL.md:69-77`, the genre table S1
  rewrites, and `frontend-engineering/…/SKILL.md:357-374`, below the table S1
  edits. Both ranges are accurate today, which is precisely why they will move.
  [`xd-state-reviewer-doctrine`](../intents/xd-state-reviewer-doctrine.md) (M3d)
  names the `experience-reviewer` restructure but cites no line numbers, so it
  carries no mechanical staleness.

  The table being dated means it is an honest snapshot rather than a false
  currency claim, so this is supersession, not rot. The real cost is different:
  S1 fills `information-architecture/references/` with six genre files, which
  moves M3c's starting position, while its table still reads "not started" and
  "no file of that name anywhere". Whoever picks up M3c against a stale baseline
  could rebuild a reference structure S1 already shipped. S1 therefore carries an
  acceptance criterion to re-measure and re-date that table, and S2 carries the
  reviewer check.
- **Risk — a stale slug reaches further than its table.**
  `design-system-foundations` names no skill; the real directory is
  `design-system`. S1 corrects it in the routing table, the
  `frontend-engineering` README route list, and the test that cross-checks the
  two. It deliberately does **not** correct the same slug in the four
  byte-identical copies of `digital-experience-contract.md`, which span
  `experience-design`, `product-strategy`, `product-engineering` and
  `frontend-engineering`: unpinning that hash means editing and bumping four
  packs, which is a separate change with its own owner.

- **Risk — reconciling drifted references by hash.** The sibling brief cautions
  that equal names do not prove equal contracts and unequal hashes do not prove
  useful differences. S2 reconciles one file at a time, each with a recorded
  reason and a manual-QA check.
- **Assumption — recorded dissent on the erratum route.** An independent reviewer
  held that retiring registrations originates a new decision rather than
  recording where an authorised one landed, and that a fresh RFC is the
  instrument for that. The owner decided errata on 2026-09-24. Each spec carries
  the objection in its own `Assumptions`; it is recorded, not resolved.
- **Assumption** — `content-design` is the surviving copy-layer name, forced
  rather than preferred: a roster suite hard-codes that directory and three files
  inside it.
- **Assumption — unverifiable.** The prior-art study's reading is that
  attribution attaches to reused text, not reused ideas, and only mechanisms
  were taken. Its source is unnamed, so no later reader can re-check it. No
  criterion in either fold rests on it; it binds only the standalone slice.

## Readiness record

**Transitioned to Ready on 2026-09-24 by owner instruction.** The canonical
readiness fields all pass: Outcome, In scope, Non-goals, Constraints / Appetite,
named Assumptions / Risks, and durable source provenance are each present and
non-empty.

**The shaping-review gate did not pass, and was overridden rather than met.**
`author-delivery-brief` requires a revision-bound `Clean` from an independent
review before Ready. The last independent round returned findings (4 critical, 9
major); those findings were worked in, and a material edit invalidates the review
evidence that preceded it. No review has run against the current text, so no
`Clean` binds to it. This is recorded here rather than left implicit, because a
Ready status that looks earned and was not is the failure mode the gate exists to
prevent.

**Two conditions remain open at the transition.** Neither blocks the work; both
bound what the status means.

- No artifact in this programme is committed, so no revision can bind a later
  review to what it read.
- No fold has a pre-fold activation baseline. Both specs gate on one, and
  neither fold is shippable until its numbers exist.

## Rabbit holes

- **Treating a fold as the fix for composition.** Consolidating registrations
  makes skills findable; it does not give their outputs a relationship model. The
  design corpus under `docs/design/` shows what that costs: artifacts invented
  their own linking vocabulary — `amends`, `builds-on`, `governed_by`, `verifies`,
  `invalidated-by`, `voice_chart`, `brand_register`, `state_matrix` — and one
  screen brief records its own split in prose with a `gap:` marker. Shipping the
  folds and declaring the linking problem solved would close the cheaper half.
- **Merging the copy layer's three artifacts.** S2 keeps three outputs. Merging
  them changes `frontend-engineering`'s handoff read and the reviewer's
  marketing-clarity lens, and belongs to a different spec.
- **Folding `design-system` on prose overlap.** Tempting at 0.27; wrong on
  contract — two artifacts, two handoff slots, two approval gates. Folding merges
  the approval points, which is where the direction-versus-values separation
  lives.
- **Reference deduplication as a side quest.** The boundary is stated above and
  is narrower than it looks; the number of files is what holds it.
- **Rewriting frozen records to remove folded skill names.** They record what was
  true when written; errata carry the change.

## Spec map

The Status column is derived by the `author-delivery-brief` coverage lint from
each linked spec; do not hand-edit it.

| Spec | Slice | Version effect | Status |
| --- | --- | --- | --- |
| `xd-genre-router` | S1 — genre fold | major, `→ 3.0.0` | Draft |
| `xd-copy-router` | S2 — copy fold | major, `→ 4.0.0` | Draft |

Both also oblige bumps in `frontend-engineering` and, for S2,
`product-engineering`. Why the order cannot change is in
[Constraints / Appetite](#constraints--appetite).

## Governance references

- [RFC-0066](../../rfc/0066-experience-pack-surface-genre-and-skill-uplift.md) —
  D4 created the six genre skills; D2's seven-type taxonomy and D5(d)'s
  `transactional-journey` route are untouched. S1 amends D4 by erratum.
- [RFC-0062](../../rfc/0062-content-design-and-copy-direction-skills.md) —
  created two copy skills; its 2026-08-02 erratum re-scoped `tone-of-voice` to
  brand level and reserved `copy/brand-register.md`. S2 amends it and preserves
  that reservation.
- [RFC-0071](../../rfc/0071-digital-experience-doctrine.md) — carries the skill
  inventory in operative text, an ordering dependency naming `copy-direction`,
  and a boundary statement S2 reverses. Takes its own erratum. Also the governing
  authority of the sibling brief, so amending it here is a cross-brief act.
- RFC-0055 D2 — the two-layer errata structure all three must adopt.
- [RFC-0050](../../rfc/0050-the-experience-pack.md) — the founding skill chain.
- [RFC-0033](../../rfc/0033-design-craft-pack.md) and ADR-0024 — framework
  agnosticism.
- ADR-0038 — alias-free rename precedent; why no deprecation shims ship.

## Design artifacts

- [`experience-design-consolidation-analysis.md`](../research/experience-design-consolidation-analysis.md)
  — the measurements, their methods, the fold criterion, the skills assessed and
  kept, and the activation experiment. Its prior-art section is labelled
  unverifiable and carries nothing this brief relies on.
- [`digital-experience-doctrine-completion`](digital-experience-doctrine-completion.md)
  — owns the remaining reference-deduplication families.
- The design corpus under `docs/design/`, read as field evidence for the
  composition problem.
