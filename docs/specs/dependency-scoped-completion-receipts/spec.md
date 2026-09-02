# Spec: Dependency-scoped completion receipts

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0096 §6, §7 and §9 (Wave 7a-ii, registered in its 2026-09-01 Errata); ADR-0103; `close-work-extraction-and-immediate-disposition` (Shipped and frozen, live dependency — its AC17 ships the producer this spec consumes); `thirty-day-cooling-and-retirement` (Shipped and frozen, live dependency — its lifecycle record publishes the three grammars this spec pins)
- **Brief:** none
- **Discovery:** none
- **Contract:** [`contracts/jsonschema/workspace-entry.schema.json`](../../../contracts/jsonschema/workspace-entry.schema.json) — the optional `receipt` object on a local need
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer whose delivery has been closed out and whose spec file has been
removed leaves behind one four-field receipt on each entry that still depends on
it, and every dependant keeps resolving. Without the receipt a dependant reports
`missing_dependency` and stops, because the entry and the file are both gone and
nothing else records that the work landed. The receipt says which delivery it
was, whether that delivery completed, which event completed it, and where the
evidence is — and nothing else. A dependant on work that was abandoned or
superseded rather than completed still refuses, so the receipt distinguishes
"my dependency shipped" from "my dependency went away".

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface contract | Applicable — the receipt is a published `workspace.toml` shape adopters write by hand | [`contracts/jsonschema/workspace-entry.schema.json`](../../../contracts/jsonschema/workspace-entry.schema.json) | repository maintainer | AC1, AC2 and AC3 pass against the shipped schema file | The `receipt` object is present with its four required properties and `additionalProperties: false` |
| Decision rationale | Applicable — three distinct concepts are spelled `outcome` in this codebase and the choice among them is not reconstructible from code | [`docs/adr/0103-completion-receipt-outcome-and-carrier.md`](../../adr/0103-completion-receipt-outcome-and-carrier.md) | repository maintainer | The ADR is `Accepted` and names all three concepts with their sources | The ADR records the vocabulary choice, the carrier choice, and the grammar-pin choice |
| Release history | Applicable — this changes shipped `packs/core` behaviour and instructions | [`docs/product/changelog.md`](../../product/changelog.md) `[core]` entry | repository maintainer | A dated `[core]` heading at the bumped version, topmost among `[core]` entries | The entry names the receipt shape and the tightened producer validation |
| Maintainer procedure | Applicable — `close-work` is the producer and its instructions state the receipt's shape | [`packs/core/.apm/skills/close-work/SKILL.md`](../../../packs/core/.apm/skills/close-work/SKILL.md) | repository maintainer | AC11 passes | The receipt paragraph names the carrier, the vocabulary, and the two pinned grammars |
| Current product truth | Not applicable | — | — | — | — |
| User documentation | Not applicable — no adopter-facing guide covers `workspace.toml` dependency receipts today, and this delivery adds no new user gesture | — | — | — | — |
| Operations | Not applicable — no runbook, deployment, or alerting surface changes | — | — | — | — |
| Reusable learning | Not applicable — the durable facts have semantic owners above; nothing generalises past this contract | — | — | — | — |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Read every pinned grammar out of `contracts/jsonschema/delivery-lifecycle-record.schema.json` at test time, never from a literal copied into a test.
- Let the surviving-membership refusal win before any receipt is read, so a dependency whose entry is still present never resolves through a receipt.
- Treat a receipt as bounded untrusted `workspace.toml` text: validate every field against its grammar before using it, and never render an unvalidated value into agent context.
- Keep the cross-repository `coordination_receipts` path reachable only from a `cross-repo` need.

### Ask first

- Widening the `outcome` vocabulary beyond `completed`, `abandoned`, and `superseded`.
- Adding a finding code, which this delivery does not do.
- Changing what `close-work` writes rather than what it accepts.

### Never do

- Create a receipt store, a shipped-spec list, a permanent initiative shell, or a third `workspace.toml` room.
- Add a new `type` value to the need discriminator, a new module, or a new dependency.
- Copy an enum or pattern literal from the lifecycle record into a second maintained home.
- Read a cooled or pruned artifact's body to decide whether a receipt is valid.

## Testing Strategy

Every criterion names a concrete input and one observable shape: a schema
accept/reject verdict, a finding code at a named JSON path, an equality
comparison against a value read from a named shipped file, or a literal string
present in whitespace-normalized text.

- **Schema shape and grammar pinning: TDD.** AC1 through AC3 are pure predicates
  over two JSON files, so they compress to a table of accepted and rejected
  documents plus one cross-file equality read. AC3 is the only criterion whose
  comparison value is not written in this spec, deliberately: it is read from
  `delivery-lifecycle-record.schema.json` at test time, so the two grammars
  cannot drift without reddening.
- **Satisfaction and refusal: TDD.** AC4 through AC9 drive the engine over
  fixture workspaces and read one finding code, which is a compressible
  invariant with a small closed input set.
- **Fixture realism is load-bearing, not incidental.** AC5's fixture must leave
  the target's `work.shipped` entry in place while AC4's must remove it. Probe 1
  in [`cooling-scope-closure/notes/probes.md`](../cooling-scope-closure/notes/probes.md)
  measured that a surviving membership raises `missing_artifact`, lands the path
  in `structurally_blocked_paths`, and refuses there before the absent-target
  refusal is reached. A fixture that leaves the entry behind therefore tests the
  wrong refusal and passes for the wrong reason.
- **Producer validation: TDD.** AC10 is a return-code assertion over
  `plan_completion_receipt`, alongside the shipped Wave 4 receipt tests.
- **Instruction text: goal-based check.** AC11 is a literal-presence check over
  `close-work`'s `SKILL.md`; a test asserting prose meaning would assert nothing.

## Acceptance Criteria

- [ ] **AC1 — The receipt rides on the citing local need.** `contracts/jsonschema/workspace-entry.schema.json` accepts a `local` need carrying an optional `receipt` object and accepts the same need without one. When `receipt` is present the schema requires exactly `delivery_id`, `outcome`, `completion_event`, and `evidence_ref`, and rejects a document adding any fifth key or omitting any of the four.
- [ ] **AC2 — `outcome` is a closed vocabulary.** The `receipt.outcome` property accepts exactly `completed`, `abandoned`, and `superseded`, and rejects every other string, including `Cooling`, `Retained`, `Retired`, and `ExternalAdvisory`.
- [ ] **AC3 — The three identifier grammars equal the lifecycle record's published grammars.** For each of `delivery_id`, `completion_event`, and `evidence_ref`, the grammar the receipt applies equals the value published at the corresponding JSON path in `contracts/jsonschema/delivery-lifecycle-record.schema.json` — `properties.delivery_id.pattern`, `properties.completion_event.enum`, and `$defs.evidenceRef.pattern` — read from that file rather than restated here.
- [ ] **AC4 — A completed receipt satisfies an absent dependency.** Given a local need whose target has no workspace membership in any initiative and whose artifact file does not exist, and whose `receipt` is valid with `outcome` `completed`, the citing entry reports no finding for that dependency and is not blocked by it.
- [ ] **AC5 — A surviving membership refuses before the receipt is read.** Given the identical valid `completed` receipt and the identical absent artifact, but with the target's `work.shipped` entry still present, the citing entry reports `unsatisfied_dependency` for that dependency.
- [ ] **AC6 — A dependency that did not land still refuses.** Given the AC4 fixture with `outcome` changed to `abandoned`, and again to `superseded`, the citing entry reports `unsatisfied_dependency` for that dependency.
- [ ] **AC7 — A malformed receipt refuses rather than resolving.** Given the AC4 fixture with the receipt mutated to omit a required field, to carry an extra key, or to violate any one of the three pinned grammars, the citing entry reports `invalid_receipt` for that dependency.
- [ ] **AC8 — A present artifact ignores the receipt.** Given a local need carrying a valid `completed` receipt whose target artifact exists, the dependency resolves by the target's own terminal status: a terminal target reports no finding and a non-terminal target reports `unsatisfied_dependency`. This is the window between closeout writing the receipt and a later wave pruning the file.
- [ ] **AC9 — The two receipts stay distinct.** A `cross-repo` need still resolves through its containing brief's single fenced `toml coordination-receipts` block, and a local need's `receipt` is never read by that path.
- [ ] **AC10 — The producer applies the same three grammars.** `plan_completion_receipt` returns `receipt-evidence-required` for a receipt whose `outcome` is outside the closed vocabulary, or whose `completion_event` or `evidence_ref` violates its pinned grammar, and returns `receipt-write-confirmation-required` for the same call with all three valid.
- [ ] **AC11 — `close-work`'s instructions state the shape.** `packs/core/.apm/skills/close-work/SKILL.md` names the receipt's carrier as the citing local need in the workspace coordination surface, lists the three `outcome` values, and states that `completion_event` and `evidence_ref` use the lifecycle record's grammars.

## Follow-ons

Separately scoped work this delivery does not perform. RFC-0096's 2026-09-01
Errata is the register for the Wave 7 slices.

| Slug | Outcome | Owner |
| --- | --- | --- |
| `rfc0096-wave7b-historical-classification` | Classify the repository's delivery history with proven outputs, dependencies, authority, and disposition, and each ambiguity an owned dated `retain-exception`. | RFC-0096 Wave 7b |
| `rfc0096-wave7c-pruning` | Prune proven-eligible artifacts under reviewed plans and explicit confirmations, removing each pruned artifact's workspace entry as well as its file. AC5 here is the reason: a surviving entry refuses before a receipt is consulted, so pruning the file alone strands every dependant. | RFC-0096 Wave 7c |
| `rfc0096-lifecycle-record-reclassified-gap` | RFC-0096 §5's phase table lists `Reclassified` as a post-closeout lifecycle record, while `delivery-lifecycle-record.schema.json` publishes `post_closeout_result` as four values without it. Decide which is authoritative. Discovered here, out of this contract's scope. | RFC-0096 Wave 7b |

## Assumptions

- Technical: the producer already ships — `plan_completion_receipt` builds the exact four-field receipt, refuses with `receipt-surface-required` and a `retain-exception` disposition when no compatible surface resolves, and requires a fresh authorization binding. (source: `packs/core/.apm/skills/close-work/scripts/close_work.py:688-735`; Wave 4 AC17 at `docs/specs/close-work-extraction-and-immediate-disposition/spec.md:457`.)
- Technical: the established compatible surface is the workspace coordination surface. (source: `packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py:254,269` pass `runtime-coordination:workspace` and the removal locator `runtime-coordination:workspace#receipt`.)
- Technical: the lifecycle record already publishes three of the four fields as required, and does not publish `outcome`. (source: `contracts/jsonschema/delivery-lifecycle-record.schema.json:10,13,19,20,37`.)
- Technical: before this delivery the producer validated all three text fields only as bounded text of at most 512 characters, and the shipped Wave 4 fixture passed `completion_event` `work-loop:gates-clean` — a value RFC-0096 §6's "selected merge/release/acceptance evidence" does not admit. (source: `close_work.py:392-399`; `test_pause_receipts_and_initiative.py:270`.)
- Technical: no consumer existed — a local dependency with no membership and no file returned `missing_dependency`. (source: `workspace_status_engine.py:2580-2581`, reached from `_dependency_is_satisfied` at 2686.)
- Technical: a surviving membership with an absent artifact refuses at `structurally_blocked_paths` before the absent-target refusal. (source: probe 1 in `docs/specs/cooling-scope-closure/notes/probes.md:18-27`.)
- Process: no gate requires an `Engine-Change-RFC:` commit trailer for `contracts/**` or `packs/core/**`; the sole path gate classifies `packages/agentbundle/**` and `packs/credential-brokers/**`. (source: `tools/lint-catalogue-curation-guard.py:77,94,101`.)
- Process: `make test` runs `pytest tests/ -q`, so a new file under `tests/roster/` is collected by directory. (source: `Makefile:530`.)
- Product: `outcome` is the closed vocabulary `completed`, `abandoned`, `superseded` rather than free text, so a dependant can distinguish a delivery that landed from one that was abandoned. (source: user confirmation 2026-09-02.)
- Product: `completion_event` and `evidence_ref` are pinned to the lifecycle record's grammars, correcting the Wave 4 fixtures that used an unadmitted event value. (source: user confirmation 2026-09-02.)
- Product: `delivery_id` is pinned by the same mechanism although the follow-on row named only the other two, because a receipt whose `delivery_id` cannot join the lifecycle record's `delivery_id` cannot be tied to the closeout that wrote it. (source: user confirmation 2026-09-02.)
- Product: the receipt rides as an optional object on the existing `local` need rather than a new `type` value, so the need discriminator is untouched. (source: user confirmation 2026-09-02.)
- Process: this spec is registered in `["ini-002".work].queue`, which withdraws that initiative's current closeout eligibility until it ships. (source: user confirmation 2026-09-02.)
