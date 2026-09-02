# Spec: Dependency-scoped completion receipts

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0096 §6, §7 and §9 (Wave 7a-ii, registered in its 2026-09-01 Errata); [ADR-0103](../../adr/0103-the-completion-receipt-carries-a-delivery-outcome-not-a-disposition.md); `close-work-extraction-and-immediate-disposition` (Shipped and frozen, live dependency — its AC17 ships the producer this spec constrains); `status-projection-and-context-exclusion` (Shipped and frozen, live dependency — its ticked AC57 rests on `invalid_receipt` having one emitter, which this spec preserves); `thirty-day-cooling-and-retirement` (Shipped and frozen — its lifecycle record publishes the three grammars this spec pins; a contract citation, not a declared `needs` edge); `workspace-routing-invariants` (Shipped — its *Ask first* boundary governs adding a finding code, and its § Canonical findings table is the public refusal contract)
- **Brief:** none
- **Discovery:** none
- **Contract:** [`contracts/jsonschema/workspace-entry.schema.json`](../../../contracts/jsonschema/workspace-entry.schema.json) — the optional `receipt` object on a local need
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer whose delivery has been closed out and whose spec file has been
removed leaves behind one four-field receipt on each workspace entry that still
depends on it, and every dependant keeps resolving. Without the receipt a
dependant reports `missing_dependency` and stops, because the entry and the file
are both gone and nothing else records that the work landed. The receipt says
which delivery it was, whether that delivery completed, which event completed
it, and where the evidence is — and nothing else. A dependant on work that was
abandoned or superseded rather than completed still refuses, so the receipt
distinguishes "my dependency shipped" from "my dependency went away".

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface contract | Applicable — the receipt is a published `workspace.toml` shape adopters write by hand | [`contracts/jsonschema/workspace-entry.schema.json`](../../../contracts/jsonschema/workspace-entry.schema.json) | repository maintainer | AC1, AC2, AC3 pass against the shipped schema | The `receipt` object carries its four required properties and `additionalProperties: false` |
| User documentation | Applicable — this is the adopter-facing reference for the `needs` shape, and a gate asserts it documents every finding code | [`guides/core/reference/workspace-toml-schema.md`](../../../guides/core/reference/workspace-toml-schema.md) and [`guides/core/how-to/close-and-disposition-work.md`](../../../guides/core/how-to/close-and-disposition-work.md) | repository maintainer | AC12 and AC13 pass | The reference documents the receipt and the new code and admits receipt-covered removal; the how-to states the closed vocabulary rather than the superseded "short outcome statement" |
| Maintainer procedure | Applicable — `close-work` produces the receipt and `workspace-status` consumes it; both state its contract | [`packs/core/.apm/skills/close-work/SKILL.md`](../../../packs/core/.apm/skills/close-work/SKILL.md) and [`packs/core/.apm/skills/workspace-status/SKILL.md`](../../../packs/core/.apm/skills/workspace-status/SKILL.md) | repository maintainer | AC12 and AC14 pass | `close-work` states the carrier, the vocabulary and the pinned grammars; `workspace-status` documents the new finding code with a reason and an action |
| Decision rationale | Applicable — three distinct concepts are spelled `outcome` here and the choice among them is not reconstructible from code | [`docs/adr/0103-the-completion-receipt-carries-a-delivery-outcome-not-a-disposition.md`](../../adr/0103-the-completion-receipt-carries-a-delivery-outcome-not-a-disposition.md) | repository maintainer | The ADR is `Accepted` and indexed in `docs/adr/README.md` | The ADR records the vocabulary, carrier, grammar-pin and finding-code choices |
| Release history | Applicable — this changes shipped `packs/core` behaviour and instructions | [`docs/product/changelog.md`](../../product/changelog.md) `[core]` entry | repository maintainer | A dated `[core]` heading at the bumped version, topmost among `[core]` entries | The entry names the receipt shape and the tightened producer validation |
| Current product truth | Not applicable — the receipt states no promise or boundary a product-truth surface owns; the published behaviour is the interface contract and the adopter reference above | — | — | — | — |
| Current architecture | Not applicable — no module, layer or ownership boundary moves; the change adds one branch inside an existing resolver | — | — | — | — |
| Operations | Not applicable — no runbook, deployment or alerting surface changes | — | — | — | — |
| Reusable learning | Not applicable — every durable fact has a semantic owner above and none generalises past this contract | — | — | — | — |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Read every pinned grammar out of `contracts/jsonschema/delivery-lifecycle-record.schema.json` at test time, never from a literal copied into a test.
- Let the surviving-membership refusal win before any receipt is read, so a dependency whose entry is still present never resolves through a receipt.
- Validate a receipt where a refusal scopes to the one dependency, so a bad receipt never removes the citing entry from the projection.
- Constrain the receipt's key set and value types before it reaches a serialized or hashed structure, and defer only its grammar and vocabulary to satisfaction time. Every need is `json.dumps`-serialized on every run, and `tomllib` yields `datetime.date` for an unquoted date, which would fail the whole projection rather than one dependency.
- Treat a receipt as bounded untrusted `workspace.toml` text: validate every field before use, and never render an unvalidated value into agent context.
- Carry the `Engine-Change-RFC: 0096` commit trailer, because `make build-self` reprojects both edited runtimes into `packages/agentbundle/agentbundle/_data/`.

### Ask first

- Adding a finding code. This delivery adds exactly one, `invalid_completion_receipt`, which `workspace-routing-invariants` § *Ask first* requires be reviewed rather than assumed.
- Widening the `outcome` vocabulary beyond `completed`, `abandoned`, and `superseded`.
- Changing what `close-work` writes or removes, rather than what it accepts.
- Editing any file inside a frozen spec directory.

### Never do

- Create a receipt store, a shipped-spec list, a permanent initiative shell, or a third `workspace.toml` room.
- Add a new `type` value to the need discriminator, a new module, or a new dependency.
- Broaden `invalid_receipt` beyond `_cross_repo_receipt_satisfied`, whose single-emitter property is a shipped test oracle.
- Read a cooled or pruned artifact's body to decide whether a receipt is valid.

## Testing Strategy

Every criterion names a concrete input and one observable shape: a schema
accept/reject verdict, a finding code at a named JSON path, an equality
comparison against a value read from a named shipped file, a producer return
code, or a literal string present in whitespace-normalized text.

- **Schema shape and grammar pinning: TDD.** AC1–AC3 are pure predicates over
  two JSON files, so they compress to a table of accepted and rejected documents
  plus cross-file equality reads. AC3's comparison values are deliberately not
  written here: they are read from the shipped lifecycle record at test time, so
  restating them would create a third maintained copy that could pass green
  while the two schemas disagreed.
- **Satisfaction and refusal: TDD.** AC4–AC9 drive the engine over fixture
  workspaces and read one finding code, a compressible invariant over a small
  closed input set.
- **Not every criterion can start red.** AC5 and AC8 are precedence pins that
  hold against the unmodified repository; their discrimination exists only once
  the new branch is present, so each is written after its branch and proved by
  the mutation that removes the ordering. AC4, AC6, AC7 and AC9 start red.
- **Fixture realism is load-bearing, not incidental.** AC5's fixture leaves the
  target's `work.shipped` entry in place while AC4's removes it. Probe A in
  [`notes/probes.md`](notes/probes.md) re-measured at this branch's base that a
  surviving membership raises `missing_artifact`, lands the path in
  `structurally_blocked_paths`, and refuses there before the absent-target
  refusal is reached. A fixture that leaves the entry behind tests the wrong
  refusal and passes for the wrong reason.
- **Producer validation: TDD.** AC10 is a return-code assertion beside the
  shipped Wave 4 receipt tests.
- **Documentation: goal-based check.** AC11 and AC12 are literal-presence and
  gate-passing checks; a test asserting prose meaning would assert nothing.

## Acceptance Criteria

- [ ] **AC1 — The receipt rides on the citing local need.** `contracts/jsonschema/workspace-entry.schema.json` accepts a `local` need carrying an optional `receipt` object and accepts the same need without one. When `receipt` is present the schema requires exactly `delivery_id`, `outcome`, `completion_event`, and `evidence_ref`, and rejects a document adding any fifth key or omitting any of the four.
- [ ] **AC2 — `outcome` is a closed vocabulary.** The `receipt.outcome` property accepts exactly `completed`, `abandoned`, and `superseded`, and rejects every other string, including `Cooling`, `Retained`, `Retired`, `ExternalAdvisory`, and the empty string.
- [ ] **AC3 — The three identifier grammars equal the lifecycle record's published grammars, in all three homes that apply them.** For each of `delivery_id`, `completion_event`, and `evidence_ref`, the grammar applied by the published schema, by the engine's receipt validator, and by `close-work`'s receipt planner equals the value at the corresponding JSON path in `contracts/jsonschema/delivery-lifecycle-record.schema.json` — `properties.delivery_id.pattern`, `properties.completion_event.enum`, and `$defs.evidenceRef.pattern` — read from that file rather than restated here.
- [ ] **AC4 — A completed receipt satisfies an absent dependency.** Given a local need whose target has no workspace membership in any initiative and whose artifact file does not exist, and whose `receipt` is valid with `outcome` `completed`, the citing entry is present in `canonical.ready` and reports no finding for that dependency.
- [ ] **AC5 — A surviving membership refuses before the receipt is read.** Given the identical valid `completed` receipt and the identical absent artifact, but with the target's `work.shipped` entry still present, the citing entry reports `unsatisfied_dependency` for that dependency.
- [ ] **AC6 — A dependency that did not land still refuses.** Given the AC4 fixture with `outcome` changed to `abandoned`, and again to `superseded`, the citing entry reports `unsatisfied_dependency` for that dependency.
- [ ] **AC7 — A malformed receipt refuses without removing its entry.** Given the AC4 fixture with the receipt mutated to omit a required field, to carry an extra key, to hold a non-string value, to violate any one of the three pinned grammars, or to carry an `outcome` outside the closed vocabulary, the citing entry reports `invalid_completion_receipt` for that dependency and the citing entry remains present in `canonical.blocked`.
- [ ] **AC8 — A receipt never breaks the run.** For every mutation enumerated in AC7, `status` and `reconcile` both exit 0 and report every other entry in the workspace unchanged against a receiptless control.
- [ ] **AC9 — A present artifact resolves by its own status.** Given a local need carrying a `receipt` whose target artifact exists, a terminal target reports no finding for that dependency and a non-terminal target reports `unsatisfied_dependency`.
- [ ] **AC10 — A present artifact never consults the receipt.** Given the AC9 fixture with a receipt that violates a pinned grammar, the citing entry reports no `invalid_completion_receipt` finding, because closeout writes the receipt before a later wave prunes the file and both existing at once is the ordinary transitional state.
- [ ] **AC11 — A malformed completion receipt never reports the cross-repository code.** Given the AC7 fixtures, the citing entry's finding codes contain `invalid_completion_receipt` and do not contain `invalid_receipt`; and the shipped cross-repository fixture continues to report `invalid_receipt`.
- [ ] **AC12 — The new code is documented in both required homes.** `packs/core/.apm/skills/workspace-status/SKILL.md` and `guides/core/reference/workspace-toml-schema.md` each carry an `invalid_completion_receipt` row with a reason and an action.
- [ ] **AC13 — The producer refuses what the consumer would refuse.** For an authorized closeout call, `close-work` refuses to plan a completion receipt with `receipt-evidence-required` when any of its four fields violates its rule — `outcome` outside the closed vocabulary, or `delivery_id`, `completion_event` or `evidence_ref` outside its pinned grammar — and reaches `receipt-write-confirmation-required` only when all four are valid.
- [ ] **AC14 — The adopter surfaces describe the current contract.** `guides/core/reference/workspace-toml-schema.md` shows a `local` need carrying a `receipt` with its four fields and states that a shipped entry may be removed while a live `needs` edge references it when every such edge carries a valid completion receipt; `guides/core/how-to/close-and-disposition-work.md` states the closed vocabulary in place of "a short outcome statement"; and `packs/core/.apm/skills/close-work/SKILL.md` names the receipt's carrier as the citing local need, lists the three `outcome` values, and states that the other three fields use the lifecycle record's grammars.

## Follow-ons

Separately scoped work this delivery does not perform. The two Wave 7 slices
below are registered by RFC-0096's Approver-signed 2026-09-01 Errata, which holds
their canonical wording; `cooling-scope-closure` § Follow-ons reproduces them and
is not the owner. The two slugs this delivery discovered are registered by the
canonical `[backlog].open` entry whose artifact is
[`notes/follow-ons.md`](notes/follow-ons.md).

| Slug | Register | Owner |
| --- | --- | --- |
| `rfc0096-wave7b-historical-classification` | RFC-0096 Errata | RFC-0096 Wave 7b |
| `rfc0096-wave7c-pruning` | RFC-0096 Errata | RFC-0096 Wave 7c |
| `lifecycle-record-entry-removal-fact` | [`notes/follow-ons.md`](notes/follow-ons.md) | RFC-0096 Wave 7b |
| `engine-cross-repo-deferral-slug-stale` | [`notes/follow-ons.md`](notes/follow-ons.md) | RFC-0096 Wave 7b |
| `lifecycle-record-reclassified-gap` | [`notes/follow-ons.md`](notes/follow-ons.md) | RFC-0096 Wave 7b |

## Assumptions

- Technical: the producer already ships — `plan_completion_receipt` builds the exact four-field receipt, refuses with `receipt-surface-required` and a `retain-exception` disposition when no compatible surface resolves, and requires a fresh authorization binding. (source: `packs/core/.apm/skills/close-work/scripts/close_work.py:688-735`; Wave 4 AC17 at `docs/specs/close-work-extraction-and-immediate-disposition/spec.md:457`.)
- Technical: the established compatible surface is the workspace coordination surface. (source: `packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py:221,269` pass `runtime-coordination:workspace`, and `:254` uses the removal locator `runtime-coordination:workspace#receipt`.)
- Technical: the lifecycle record already publishes three of the four fields as required, and does not publish `outcome`. (source: `contracts/jsonschema/delivery-lifecycle-record.schema.json:10,13,19,20,37`.)
- Technical: before this delivery the producer validated all four fields only as bounded text of at most 512 characters, and the one shipped call that constructs a receipt successfully (`:222`) passes three values that fail the pinned grammars — `delivery_id` `delivery:wave4`, `completion_event` `work-loop:gates-clean`, and `evidence_ref` `evidence:current`. (source: `close_work.py:392-399`; `test_pause_receipts_and_initiative.py:219-236`.)
- Technical: no consumer existed — a local dependency with no membership and no file returned `missing_dependency`. (source: `workspace_status_engine.py:2580-2581`, reached from `_dependency_is_satisfied` at 2686.)
- Technical: a surviving membership with an absent artifact refuses at `structurally_blocked_paths` before the absent-target refusal. (source: probe A in `notes/probes.md`, re-measuring `cooling-scope-closure` probe 1 at this branch's base.)
- Technical: a finding raised while parsing a need discards the whole citing entry and does not mark its path as blocking dependants, so receipt validation belongs at satisfaction time rather than in the parser. (source: `workspace_status_engine.py:869` returns `None` for the entry; `:2418-2420` sets `blocks_dependencies` only for `invalid_entry` and `invalid_artifact_path`.)
- Technical: `invalid_receipt` has exactly one emitter today, and a ticked criterion in a frozen spec plus a shipped test use that property as an oracle, so this delivery adds a distinct code rather than broadening it. (source: `docs/specs/status-projection-and-context-exclusion/spec.md:491-492`; `tests/roster/test_status_projection_and_context_exclusion.py:1007-1009`.)
- Process: the commit needs an `Engine-Change-RFC: 0096` trailer. Both edited runtimes are reprojected into `packages/agentbundle/agentbundle/_data/`, which matches the guard's `ENGINE_PREFIX` with carve-outs only for `build/recipes/` and `/tests/`. (source: `packages/agentbundle/agentbundle/build/self_host.py:88-115`; `tools/lint-catalogue-curation-guard.py:82-83,110-125`.)
- Process: a gate asserts every code in the engine's finding table is documented with a reason and an action in both `workspace-status/SKILL.md` and `guides/core/reference/workspace-toml-schema.md`, so a new code obliges both. The check is a superset comparison, so adding a code is admissible. (source: `tests/roster/test_workspace_status_projection.py:488-495`.)
- Process: `make test` runs `pytest tests/ -q`, so a new file under `tests/roster/` is collected by directory. (source: `Makefile:530`.)
- Product: `outcome` is the closed vocabulary `completed`, `abandoned`, `superseded` rather than free text, so a dependant can distinguish a delivery that landed from one that was abandoned. (source: user confirmation 2026-09-02; recorded in ADR-0103.)
- Product: `completion_event` and `evidence_ref` are pinned to the lifecycle record's grammars, correcting the Wave 4 fixture that used unadmitted values. `delivery_id` is pinned by the same mechanism although the follow-on row named only the other two, because a receipt whose `delivery_id` cannot be joined to the lifecycle record cannot be traced to the closeout that wrote it. (source: user confirmation 2026-09-02.)
- Product: the receipt rides as an optional object on the existing `local` need rather than a new `type` value, so the need discriminator is untouched. (source: user confirmation 2026-09-02.)
- Product: the receipt is a self-assertion. Once the artifact is pruned there is nothing left to verify it against, and its trust rests on `workspace.toml` being a reviewed, committed file — the same trust the entry it replaces already carried. (source: user confirmation 2026-09-02; recorded in ADR-0103.)
- Process: this spec is registered in `["ini-002".work].queue` before approval, which withdraws that initiative's closeout eligibility until it ships. (source: user confirmation 2026-09-02.)
