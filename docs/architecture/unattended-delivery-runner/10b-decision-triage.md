# Architecture Change — Owner decision triage

**Decision sought:** Confirm a triage that sorts 26 owner decisions into four classes, and records that all 26 are decided on 2026-11-07.

The seven decisions that unblock P0 are decided, and 8 need a recorded ADR or RFC before a named phase. Three points carry the triage:

- Class 1 holds 5 decisions that had to be settled before the `ferryman` build starts, and all five are decided.
- Class 4 holds 8 owner-only security or authority judgments, each gated on a record, and all eight are decided.
- The other 50 numbers are folded into a parent, take a default, or are superseded (D2), so the owner reviewed 26 and decided all 26.

**Author(s):** Repository owner (draft)
**Status:** Draft
**Last updated:** 2026-11-07
**Reviewers:** Repository owner

**Baseline — current architecture:** [Owner decisions](10c-review-decisions.md), [folded decisions and defaults](10d-folded-decisions-and-defaults.md), and [records](10-decisions-and-records.md) own the decisions. [Rollout](13-rollout-spikes-and-risks.md) owns the phases. This page changes no recommendation.

## 1. Scope and Baseline

This page classifies and orders decisions, and it decides none of them.

| Delta item | In scope | Why it is here |
| --- | --- | --- |
| Class, gate, record, and consequence for D1 to D76 | yes | One owner cannot review 76 numbers in one sitting |
| The decide-first list and the session grouping | yes | The owner needs an order |
| The decisions and recommendations | no | [Page 10c](10c-review-decisions.md) |

| Unchanged context | Link |
| --- | --- |
| Phases S0 to S3, E0 to E3, P0, PL, P1, P4 to P7, spare P8, and the gates | [page 13](13-rollout-spikes-and-risks.md) |

## 2. Structural Change

The four classes are defined once here. Folded, default, and superseded numbers carry no class.

| Class | Meaning | Count | Open |
| --- | --- | --- | --- |
| 1 | Must be decided before the `ferryman` build starts | 5 | 0 |
| 2 | Must be decided before a named later phase gate | 11 | 0 |
| 3 | Has a safe provisional default and can be decided at its phase gate | 2 | 0 |
| 4 | Owner-only security or authority judgment that needs a recorded ADR or RFC before the gated phase | 8 | 0 |

Each owner decision is in exactly one class. A security or authority judgment that needs a record is class 4, even when its phase is P0. D30 and D56 are decided, and D7's route (D35) is decided with its ADR Proposed.

## 3. Runtime Change

The table gives each number's class or marker, gate, record, and what stays frozen if it stays open.

| Decision | Class | Status | Gating phase | Record | If left open, what stays frozen |
| --- | --- | --- | --- | --- | --- |
| D1 | 1 | decided | P0 | 1 | the whole `packages/ferryman/` build |
| D2 | superseded | n/a | none | none | nothing, since D30 chose `ferryman` |
| D3 | 2 | decided | E2 | 3 | the two intake doors, ticket intake before E2, and the discovery supervisor's scope |
| D4 | 2 | decided | E1 | 4 | the spec supervisor: ships inside `new-spec`, driven by `work-loop` |
| D5 | 2 | decided | E2 | 21 (RFC) | the discovery-supervisor engine |
| D6 | 4 | decided | P5 | 7 | standing mirror writes and per-brief grants |
| D7 | 4 | decided | P5, P7 | 8, 18 | tracker, host, and withdrawn approvals (route decided, ADR Proposed) |
| D8 | 2 | decided | P4 | 9 | the GitHub shim |
| D9 | 2 | decided | E2 | 3 | the supervised discovery tiers: committed tier A and local tier B |
| D10 | 3 | decided | P1 | 5 | nothing, since the default is `ask` |
| D11 | default | n/a | none | none | nothing, since the default applies |
| D12 | default | n/a | none | none | nothing, since the default applies |
| D13 | default | n/a | none | none | nothing, since the default applies |
| D14 | 4 | decided | P0 | 11 | the scribe and guard home and the approval-field contract |
| D15 | 4 | decided | P0 | 11, 18 | the v1 approval path and the P0 gate wording |
| D16 | folded | n/a | into D3 | see D3 | the facet follows its parent |
| D17 | 1 | decided | P0 | 12 | the push and delete argv allowlist |
| D18 | folded | n/a | into D14 | see D14 | the facet follows its parent |
| D19 | default | n/a | none | none | nothing, since the default applies |
| D20 | folded | n/a | into D15 | see D15 | the facet follows its parent |
| D21 | folded | n/a | into D15 | see D15 | the facet follows its parent |
| D22 | folded | n/a | into D7 | see D7 | the facet follows its parent |
| D23 | 4 | decided | P0 | 12 | the trusted configuration pin |
| D24 | 2 | decided | P7 | 14 | checkpoints, restore, claims, and ticket intake across clones |
| D25 | 4 | decided | P7 | 15 | relayed tracker signals |
| D26 | folded | n/a | into D24 | see D24 | the facet follows its parent |
| D27 | 4 | decided | P7 | 13 | pool nodes: trust, egress, effects, merge, and integrity |
| D28 | folded | n/a | into D25 | see D25 | the facet follows its parent |
| D29 | folded | n/a | into D23 | see D23 | the facet follows its parent |
| D30 | 1 | decided | P0 | none | the package name, now decided |
| D31 | 2 | decided | P1 | 17 | brief-scoped ordering and slice worktrees |
| D32 | folded | n/a | into D31 | see D31 | the facet follows its parent |
| D33 | folded | n/a | into D67 | see D67 | the facet follows its parent |
| D34 | folded | n/a | into D31 | see D31 | the facet follows its parent |
| D35 | folded | n/a | into D7 | see D7 | the facet follows its parent |
| D36 | 3 | decided | P7 and later | 16 | concurrent attempts, which stay a documented stop |
| D37 | 2 | decided | E1 | 4 | the review round cap and the consent gate at the cap |
| D38 | default | n/a | none | none | nothing, since the default applies |
| D39 | default | n/a | none | none | nothing, since the default applies |
| D40 | default | n/a | none | none | nothing, since the default applies |
| D41 | default | n/a | none | none | nothing, since the default applies |
| D42 | folded | n/a | into D7 | see D7 | the facet follows its parent |
| D43 | folded | n/a | into D27 | see D27 | the facet follows its parent |
| D44 | folded | n/a | into D27 | see D27 | the facet follows its parent |
| D45 | 4 | decided | P7 | 14 | pool checkpoints, clocks, and push scope |
| D46 | folded | n/a | into D27 | see D27 | the facet follows its parent |
| D47 | folded | n/a | into D24 | see D24 | the facet follows its parent |
| D48 | folded | n/a | into D45 | see D45 | the facet follows its parent |
| D49 | default | n/a | none | none | nothing, since the default applies |
| D50 | 2 | decided | P0 release | 19 | the first publish and the compatibility checks |
| D51 | folded | n/a | into D50 | see D50 | the facet follows its parent |
| D52 | default | n/a | none | none | nothing, since the default applies |
| D53 | folded | n/a | into D50 | see D50 | the facet follows its parent |
| D54 | default | n/a | none | none | nothing, since the default applies |
| D55 | folded | n/a | into D27 | see D27 | the facet follows its parent |
| D56 | 2 | decided | P1 | 17 | brief-scoped ordering, with `schema_version` present on `next` in the merged runner (decided) |
| D57 | folded | n/a | into D45 | see D45 | the facet follows its parent |
| D58 | folded | n/a | into D59 | see D59 | the facet follows its parent |
| D59 | 1 | decided | P0 | none | the v1 checkout refusals and the branch rule |
| D60 | default | n/a | none | none | nothing, since the default applies |
| D61 | default | n/a | none | none | nothing, since the default applies |
| D62 | default | n/a | none | none | nothing, since the default applies |
| D63 | folded | n/a | into D4 | see D4 | the facet follows its parent |
| D64 | default | n/a | none | none | nothing, since the default applies |
| D65 | folded | n/a | into D15 | see D15 | the facet follows its parent |
| D66 | default | n/a | none | none | nothing, since the default applies |
| D67 | 1 | decided | P0 | none | which contracts P0 freezes |
| D68 | folded | n/a | into D27 | see D27 | the facet follows its parent |
| D69 | folded | n/a | into D27 | see D27 | the facet follows its parent |
| D70 | default | n/a | none | none | nothing, since the default applies |
| D71 | folded | n/a | into D27 | see D27 | the facet follows its parent |
| D72 | folded | n/a | into D24 | see D24 | the facet follows its parent |
| D73 | folded | n/a | into D27 | see D27 | the facet follows its parent |
| D74 | folded | n/a | into D15 | see D15 | the facet follows its parent |
| D75 | 2 | decided | PL | 22 | the session route: `ferryman session`, `route` in run-state, and `light_candidates` |
| D76 | default | n/a | none | none | nothing, since the default applies |

**Decide first.** The seven decisions that unblocked P0 are all decided (2026-11-07): D1, D67, D14, D15, D23, D59, and D17. D59 carries the revised D58 branch sub-rule.

**Gates.** Each phase waits for the decisions and records below, and page 13 splits them into "enter when" and "leave when".

| Phase | Decisions that must be decided | Records Accepted |
| --- | --- | --- |
| E0 | none | 3, 4 |
| E1 | D4 and D37 | 4 (the spec-supervisor record) |
| E2 | D3, D5, and D9 | 3, 21 (RFC) |
| E3 | none | none |
| P0 | D1, D14, D15, D17, D23, D59, D67. For the release also D50 and the compatibility rule (D53) | 11, 12. For the release also 19 |
| PL | D75, and `light-mode.md` recording, on the maintainer's confirmation, that a local human `ferryman session` launch is an explicit trusted invocation | 22 |
| P1 | D31 and D56 | 17 |
| P4 | D8 | 9 |
| P5 | D6 and D7 | 7, 8, 18 |
| P6 | D32, a facet of D31 | 6 |
| P7 | D24, D25, D27, D45, and the D34 pool facet. D27's D55 facet names its execution boundary | 13, 14, 15, 18 |

**Records and gates.** Only a record that an implemented element needs Accepted gates a phase, and the others are written, not gating. E0 also ships the `approval-fields.v1` lists that the siblings' `report` reads, and record 11 governs them at P0.

| Record | Blocks |
| --- | --- |
| 11, 12 | P0 |
| 22 | PL |
| 19 | the P0 release |
| 17 | P1 |
| 3 | E0 |
| 4 | E0 and E1 |
| 21 | E2 |
| 9 | P4 |
| 7, 8, 18 | P5 |
| 6 | P6 |
| 13, 14, 15, 18 | P7 |
| 1, 2, 5, 10, 16, 20 | written, not gating |

## 4. Contract and Invariant Change

This page adds no contract.

| Semantic name | Change type | Baseline reference | Compatibility during transition | Enforcement | Verification |
| --- | --- | --- | --- | --- | --- |
| none | n/a | n/a | n/a | n/a | n/a |

**Decision sessions.** All 26 decisions are decided (2026-11-07).

| Session | Decisions | Count |
| --- | --- | --- |
| Decided on 2026-11-07 | D1, D3, D4, D5, D6, D7, D8, D9, D10, D14, D15, D17, D23, D24, D25, D27, D30, D31, D36, D37, D45, D50, D56, D59, D67, D75 | 26 |

## 5. Data/State Migration

No state moves.

| Data element | Old shape | New shape | Migration mechanism | Rollback |
| --- | --- | --- | --- | --- |
| none | n/a | n/a | none | none |

## 6. Deployment/Operational Change

Nothing deploys from this page.

| Deployment unit | Change type | Baseline reference |
| --- | --- | --- |
| none | n/a | n/a |

## 7. Quality Regression and Verification

The triage stays correct only if every number has a class, a fold, or a default.

| Attribute at risk | Baseline target | Stimulus that could regress it | Verification |
| --- | --- | --- | --- |
| Triage completeness | 76 numbers, each classified, folded, or defaulted | a new decision without a row | count check against pages 10c and 10d |

## 8. Build Mapping

None. The triage is a reading aid.

## Evidence

This page cites no source of its own. The classes follow the phase gates on [page 13](13-rollout-spikes-and-risks.md) and the records on [page 10](10-decisions-and-records.md).
