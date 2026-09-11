# Ownership consolidation

The guidebook step contract claims obligations that nine other artifacts already
claim in whole or in part. Every one of them is **Draft** — none is Shipped —
so consolidating is a live decision rather than an amendment to frozen history.
Recorded here because AC-0012 is checked against this ledger, and because a
reader of any of these documents is owed the reason their scope changed.

Verified 2026-09-11 by reading each document's Status and Outcome.

## Superseded inside the five packs

These three own the guidebook's rows 3, 4 and 10 across the whole guide corpus
against their own accepted-base ledgers. They keep the corpus; this slice takes
the five packs a team SOP needs, because a step that satisfies three rows out of
eleven is not walkable and no reader benefits from four slices each delivering a
fraction of a step.

**The carve-out is by target path, not by pack name.** An earlier draft of this
ledger handed each sibling "every guide outside the five packs", which would
have stranded work neither slice could then do. S3's plan names **16
`SKILL.md` targets inside these five packs** — 7 under `packs/core/.apm/skills/`,
7 under `packs/desk-research/.apm/skills/`, 2 under
`packs/product-engineering/.apm/skills/`. This slice forbids every `packs/**`
edit, so a pack-level carve-out would have removed those 16 from S3 while giving
them to nobody. AC-0012 checks the carve-out at path granularity for exactly
this reason.

| Spec | What it owns | After this slice |
| --- | --- | --- |
| `guide-invocation-outcome-coverage` (S3) | literal chat input and stated outcome | Keeps every guide outside the five packs **and retains all 16 of its `packs/**/.apm/skills/**` targets**, including those inside the five, which this slice cannot edit |
| `tutorial-worked-examples` (S4) | demonstrated input paired with output | Keeps every guide target outside the five packs; retains any non-guide target inside them |
| `how-to-sample-output-coverage` (S5) | representative agent response | Same carve-out as S4 |

None of the three reaches the deliverable obligations as this contract states
them — the artifact's **path** and its **expected outline**. S3's "stated
outcome" is an end state in prose, not a location or a shape. An earlier draft
of this ledger asserted the siblings owned those rows; they do not. The
deliverable half collides with no sibling and is new obligation, not
re-parcelled scope.

**Future state, not current.** Only `skill-sequence-wayfinding.md` names this
spec today. The reciprocal records in the other eight artifacts are T8's work,
and AC-0012 is false until they exist — this ledger states what must be true,
not what is. Each of the three will record the carve-out in its own body, so the
boundary is readable from either side. Their accepted-base ledgers are unchanged: this slice
adds no entries to them and removes none.

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
