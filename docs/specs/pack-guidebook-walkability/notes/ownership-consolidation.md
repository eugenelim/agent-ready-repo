# Ownership consolidation

The guidebook step contract claims obligations that nine other artifacts already
claim in whole or in part. Every one of them is **Draft** — none is Shipped —
so consolidating is a live decision rather than an amendment to frozen history.
Recorded here because AC-0012 is checked against this ledger, and because a
reader of any of these documents is owed the reason their scope changed.

Verified 2026-09-11 by reading each document's Status and Outcome.

## Nothing is superseded — the overlap is three pages

**Corrected 2026-09-11 by owner decision, after enumerating the targets.** An
earlier version of this ledger handed each sibling "every guide outside the five
packs". Measuring what they actually own showed that over-reaches badly.

Targets the three siblings own **inside** the five packs:

| Spec | inside the five packs | `packs/**` source | `guides/` |
| --- | --: | --: | --: |
| `guide-invocation-outcome-coverage` (S3) | 20 | **16** | 4 |
| `tutorial-worked-examples` (S4) | 5 | 0 | 5 |
| `how-to-sample-output-coverage` (S5) | 25 | 0 | 25 |

**31 of those 34 guide targets carry no `order:` frontmatter, so they are not
guidebook steps at all.** The siblings uplift existing pages; this slice authors
new ones. Superseding would have stranded 31 targets with nobody uplifting
them, on top of S3's 16 `packs/**` targets this slice's boundary forbids it from
touching. `experience-design` — the pack this slice proves the contract on —
appears in **no** sibling ledger.

So: **the siblings keep every target they own, inside and outside the five
packs.** This slice owns only the guidebook steps it authors.

### The three pages that genuinely collide

All in `guides/core/`, which already carries an ordered fragment at orders 9 to
12 tagged `journey: core`:

| Page | Also owned by |
| --- | --- |
| `guides/core/how-to/start-or-remember-work.md` | S3, S5 |
| `guides/core/how-to/close-and-disposition-work.md` | S3, S5 |
| `guides/core/reference/work-intake-routing-and-lifecycle.md` | S3 |

Owner decision, 2026-09-11: **T6 absorbs core's four existing ordered pages into
its seven-step guidebook** rather than leaving an orphan fragment beside a new
sequence — two competing ordered sets on one sidebar is the reader confusion
this slice exists to remove. Those three pages therefore become guidebook steps,
and the carve-out is recorded on both sides for **those three only**. AC-0012
compares target paths for exactly this reason, and its universe is the three
siblings' accepted-base ledgers.

## Partly delivered here

**`docs/product/intents/skill-sequence-wayfinding.md`** (Draft, capability).
**Extended on owner direction, 2026-09-11**, from sequence wayfinding alone to
sequence wayfinding **plus deliverable orientation** — what the step produces,
where it lands, and what a good one contains. Its title, outcome, falsifier,
opportunity, decomposition, risks and open questions all carry the second half
now, each with its own measured baseline and its own kill signal.

Four of this contract's eleven obligations are that capability's outcome stated
as authored prose:

| Contract row | The capability's derived form |
| --- | --- |
| 1 — where you are | position in the declared sequence |
| 9 — the artifact and its path | the deliverable's location, projectable from the 63 of 74 skills that name a path |
| 10 — what to expect inside it | the deliverable's form, which 38 of 74 skills declare nothing about |
| 11 — what to run next | the successor edge |

This slice is the capability's **first delivery**, by hand, for five packs. The
capability keeps the remaining packs and the derived mechanism. The division is
deliberate: this slice establishes what the obligations are worth on real
content, and the capability decides whether they can be generated rather than
written. It records the reciprocal boundary in its own Boundary section, and
names the specific dependency — if this slice finds an obligation satisfiable
mechanically but useless to a reader, the capability should not derive it.

Nothing is superseded. The intent keeps its outcome and gained a second half.

## Ownership moved

**`docs/product/intents/experience-design-delivery-packet.md`** (Draft).
Its outcome is that a designer "can account for **every** deliverable they would
expect", each "owned by a skill, satisfied by an artifact the repository already
carries, or named in the pack's own documentation as out of scope". It owns
authoring that pack's guides, including the deliverables the pack owns but does
not teach, and records that as part of its outcome rather than a follow-on.

**This is a direct collision.** `experience-design` is the pack this slice
proves the contract on — 20 published skills, 2 guides, neither showing a prompt
or an output, 10 skills named nowhere in the pack's journey. Two slices
authoring the same pack's guides is the collision that costs review rounds.

**Decision, owner, 2026-09-11:** `experience-design` guidebook authoring moves
to this slice. The packet keeps its distinct half — the deliverable-accounting
question of whether every expected deliverable is owned, satisfied or explicitly
out of scope, which is a completeness audit of the pack rather than a reader's
walk through it. The packet records the move in its own body.

The two are separable: this slice makes the pack's declared thread walkable; the
packet decides whether that thread is the right set of deliverables at all. A
guidebook over an incomplete thread is still a usable guidebook over what the
pack actually has.

## Boundary recorded, nothing moved

| Artifact | Why it is adjacent and not absorbed |
| --- | --- |
| `docs/product/intents/digital-product-guides-update.md` (Draft) | Wants "a coherent end-to-end digital-product guide", which sounds identical. It is not: its chain carries `frontend-engineering` rather than `desk-research`, and it is RFC-0071 M6, gated behind an unstarted M5. Different membership, and unstartable. |
| `docs/product/intents/nontechnical-pack-first-value-rollout.md` (Draft) | Owns per-pack first-value adoption slices. This slice is **barred** from any first-value claim by its own Boundaries, because the probe is unrun. The two cannot collide while that prohibition holds. |
| `docs/product/briefs/stage-input-readiness.md` (Draft) | Closest to row 2. Its question is machine-checked and asked *between stages* — can the consumer do the work from what it was handed. Row 2 is a sentence a reader reads. Delivering row 2 does not deliver its outcome, and its outcome would not satisfy row 2. |
| `docs/product/briefs/work-loop-next-action.md` (Draft) | Derives one authoritative next action from persisted work-loop state, and is explicitly reporting-only. Row 11 — what to run next — is static prose in a guide. Runtime state versus authored text. |

## Slug consolidation

This spec replaces an earlier draft of the same work registered under
`four-discipline-walk-execution`. That draft never reached `main` —
`git log origin/main -- docs/specs/four-discipline-walk-execution/` is empty —
so nothing downstream could depend on it and it was re-cut rather than amended.
Its slug is removed from `workspace.toml` and replaced by this one; its engine
and cohort state were reset rather than left orphaned. The records it produced
survive in this directory: the grounding pass, the premise correction, the
acceptance-set construction record, and the review record for the rounds that
ran against the narrower scope.
