# Spec: Next-item suggestions removed

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-27 by eugenelim, spec and plan, after spec-stage shaping and adversarial reviews over five rounds ending clean; review records under `.context/reviews/slice6-spec-r1/` to `slice6-spec-r5/`.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0106 (D3, which authorises removing the first-in-list `next_queue` and `next_shape` suggestions, and which says selecting among several ready specs always lists them and asks)
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Depends on:** none
- **Amends:** [workspace-status-next-actions](../workspace-status-next-actions/spec.md) — its Choice 1 criterion, replaced by AC-0002; its Choice 2 and Choice 3 criteria, removed by AC-0001; its Objective's ceiling of "up to four choices" and "up to four content choices", removed because AC-0002 gives each active spec its own choice; and its Testing Strategy fixture cases A-installed, A-absent, B and D, as far as each expects a queue-item or shaping-item choice. Every other criterion and rule of that spec carries over unchanged.
- **Contract:** none — skill prose; no interface contract.
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites.

## Outcome

`workspace-status`'s closing Next-actions list never picks one item because it comes first in a registry list. Success is that the list offers each active spec as its own choice and offers no "next queue item" or "first shaping item" choice, while Ready to start still lists every ready item with its command.

## What Changes

- § Next-actions in `packs/core/.apm/skills/workspace-status/SKILL.md`: the `next_queue` and `next_shape` definitions and their two choices go, and the active-spec choice becomes one choice per active spec. The projected `.claude/` and `.agents/` copies follow.
- A pack test that pins § Next-actions — `packs/core/tests/skills/workspace-status/`.
- The retirement record's Equivalence row and Disposition text for this removal, the inventory rows it changes, and their checks in the retirement roster suite — `docs/specs/workspace-retirement/`, `tests/roster/`.
- FEAT-0034's answer to where list order is read, which names the readers the inventory marks.
- The `workspace-status-next-actions` spec's `Amended in part by:` header, pointing here.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth: what the orient run offers | Applicable: shipped skill behavior changes | `packs/core/.apm/skills/workspace-status/SKILL.md` § Next-actions | Platform Core maintainer | AC-0001 to AC-0003 pass | The section matches this spec |
| Decision rationale: the removal and its authority | Applicable: RFC-0105 D3 needs accepted authority for each deliberate removal | `docs/specs/workspace-retirement/retirement-record.md` § Equivalence | Platform Core maintainer | AC-0004 passes | The row is present and the retirement check passes |
| Current product truth: the consumer inventory | Applicable: this spec and the amended spec name `workspace-status` | `docs/specs/workspace-retirement/inventory.toml` | Platform Core maintainer | AC-0005 to AC-0007 pass | The rows match this spec |
| Interface compatibility: the amended spec | Applicable: a Shipped spec's criteria change | `docs/specs/workspace-status-next-actions/spec.md` header | Platform Core maintainer | An `Amended in part by:` line names this spec and everything this spec's `Amends:` line names | The line is present |
| Current product truth: where list order is read | Applicable: FEAT-0034 counts and names the inventory's `reads_order` readers | `docs/product/intents/FEAT-0034-workspace-registry-retirement.md` § Unresolved questions | Platform Core maintainer | Plan T2's Done-when conditions hold | The count and the named readers match the inventory's `reads_order` rows |
| Release history | Applicable: shipped `core` behavior changes | a `docs/product/changelog.d/` fragment, with `core`'s `pack.toml` and `.claude-plugin/plugin.json` at one new patch version | Platform Core maintainer | The changelog gate passes | The fragment names the removal |
| Delivery membership | Applicable: the brief's coverage map | The brief's Spec map and this spec's `workspace.toml` entry | `author-delivery-brief` | `lint-brief-coverage.py` lists this spec under the brief | The coverage lint passes |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- For the `workspace-status` skill, edit only its `.apm/` source, never the `.claude/` or `.agents/` projections; regenerate them with `make build-self` and bump `core`'s version.
- Keep Ready to start, the dependency graph, the parallel-session offer, and the final `work-intake` choice as they are.

### Ask first

- Changing any `workspace-status` section other than § Next-actions.
- Adding a new kind of choice to § Next-actions.

### Never do

- Replace a removed choice with a rule that picks one item, including by the `Priority:` header field. RFC-0106 D3 forbids a rule that chooses among ready specs, and the field never decides order.
- Change `work-loop`'s argless start, the `navigate-intents` readiness bridge, the engine, or the guides. Those belong to the brief's slices 8 and 9.
- Add a script under `.apm/`, a dependency, or a top-level directory.

## Testing Strategy

- **The Next-actions text (AC-0001, AC-0002, AC-0003):** goal-based check. The skill is prose with no executable path, so a pack test reads § Next-actions from the source `SKILL.md` and pins what it must and must not say.
- **The retirement record and inventory (AC-0004, AC-0005, AC-0006, AC-0007):** goal-based check, because both are data files in this repository whose rows a roster test can read and compare exactly. The checks live in `tests/roster/test_workspace_retirement_inventory.py`, which already runs every retirement rule on each pull request, as the `workspace-retirement` spec requires.

## Acceptance Criteria

**Next-actions section.** The text of `packs/core/.apm/skills/workspace-status/SKILL.md` from the line `### Next-actions` up to the next line that starts with `## `.

- [ ] **AC-0001.** No line of `SKILL.md` contains `next_queue` or `next_shape`, and the Next-actions section contains neither `Next queue item` nor `First shaping item`.
- [ ] **AC-0002.** The Next-actions section defines the active-spec choice as one numbered choice for each entry in `canonical.active`, and contains no `first entry in`.
- [ ] **AC-0003.** The Next-actions section still contains its `5b`, `5c`, and `5d` steps and its final `work-intake` choice.
- [ ] **AC-0004.** The retirement record's § Equivalence holds a row whose Case text is `the first-in-list next_queue and next_shape suggestions`, with Slice `6`, Result `accepted removal`, and an Authority link to RFC-0106 D3.
- [ ] **AC-0005.** In `inventory.toml`, the governing row of `docs/specs/next-item-suggestions-removal/spec.md` is a `contract` row with owner `6`.
- [ ] **AC-0006.** In `inventory.toml`, the governing row of `docs/specs/workspace-status-next-actions/spec.md` carries no `reads_order = true`.
- [ ] **AC-0007.** No `consumer` in `inventory.toml` contains `next_queue` or `next_shape`.

## Assumptions

none

## Follow-ons

- The brief's slice 8 replaces `work-loop`'s argless first-ready start with list-and-ask, and the `navigate-intents` owner re-points the readiness bridge in that release.
- The brief's slice 9 shrinks `workspace-status` to the repair, which removes the rest of its list-order reading.
