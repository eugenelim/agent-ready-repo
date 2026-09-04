# Spec: Reclassified lifecycle result

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0096
- **Brief:** none
- **Discovery:** none
- **Contract:** [`contracts/jsonschema/delivery-lifecycle-record.schema.json`](../../../contracts/jsonschema/delivery-lifecycle-record.schema.json)
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer closing out a multi-role artifact hands it to a durable owner, and
that outcome persists. The lifecycle record carries `Reclassified` as a
post-closeout result, so the routing decision RFC-0096 section 2 describes —
delivery authority ends without deletion — survives the session that made it and
is readable by anyone who later asks what became of the artifact.

A reclassified artifact keeps its file at its recorded locator and leaves
delivery. It is absent from ordinary orientation, never due for a retention
review, and not counted among the obligations someone still owes delivery work
against.

Reclassification follows retention. A record reaches it from a retained state
when a well-formed acceptance block naming the durable owner is supplied at the
transition, which the record then carries. That block is validated for shape and
vocabulary, not proven: it is the same standard every `Retained` record already
meets, and `evidence_ref` remains optional as it is there. The record therefore
states who accepted the artifact; it does not attest that they did.
Reclassification is not gated on a date, because a durable owner accepting an
artifact is not a day-30 event.

It is the end of the record's life: nothing transitions out of it, and no
deletion route admits a lifecycle record. Reclassification is therefore
irreversible in the same way `Retired` and `ExternalAdvisory` already are — no
edge leaves either, and the confirmed-deletion seam admits only
delivery-contract surfaces. A mistaken reclassification is corrected by an
ordinary reviewed change to the record file, not by a transition or a deletion
workflow.

Reclassification reuses the existing cooled-artifact mechanism rather than a
parallel one, so it inherits that mechanism's whole semantics: a direct
dependency on the artifact resolves from its lifecycle record instead of its
body, a cross-repository dependency on it is refused, findings derived from its
body stop being produced, and it stops counting toward an initiative's queue
emptiness. If — and only if — its workspace entry declares `source.parent`, the
named brief's child scope becomes unevaluable and that brief's dependencies fail
closed; a reclassified entry declaring no parent is not attributed, which is the
recorded `cooling-brief-child-scope` residual rather than a new gap. Those are
accepted consequences of the cooling mechanism, not behaviour this delivery
defines.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable and changed: the published record contract gains an enum member | [`contracts/jsonschema/delivery-lifecycle-record.schema.json`](../../../contracts/jsonschema/delivery-lifecycle-record.schema.json) | maintainer | AC1, AC2 | The contract and the validator admit the same result set |
| Decision rationale | Applicable: widening the contract was chosen against a recommendation to declare the value projection-only | [`docs/product/design/rfc0096-wave7c-lifecycle-record-decisions.md`](../../product/design/rfc0096-wave7c-lifecycle-record-decisions.md) | Approver | The recorded decision and its rejected alternative | The rejected alternative survives as a readable record |
| Decision rationale (dependent contract) | Applicable: a ticked criterion in a frozen spec names a transition table this delivery extends | [`docs/adr/`](../../adr/) and [`docs/specs/thirty-day-cooling-and-retirement/`](../thirty-day-cooling-and-retirement/) | Approver | AC20 | The superseded criterion names the ADR that corrects it |
| Maintainer procedure | Applicable and changed: the skill's cooled-set prose partitions every post-closeout result and would otherwise omit the new one | [`packs/core/.apm/skills/workspace-status/SKILL.md`](../../../packs/core/.apm/skills/workspace-status/SKILL.md) | maintainer | AC14 | The prose names which side of the exclusion boundary every result falls on |
| Release history | Applicable: a non-cosmetic Core pack change, whose version is pinned to a dated changelog heading | [`docs/product/changelog.md`](../../product/changelog.md) | maintainer | AC16, AC17, AC18 | The topmost Core heading names the shipped version |
| Interface compatibility (dependents) | Applicable: a byte pin covers four files this delivery edits | [`docs/specs/cooling-scope-closure/spec.md`](../cooling-scope-closure/spec.md) and [`tests/roster/test_cooling_scope_closure.py`](../../../tests/roster/test_cooling_scope_closure.py) | maintainer | AC15 | Both digest sites name current bytes |
| Current product truth | Not applicable: no living product promise changes, because the value is reachable only by a maintainer already performing an exception review | — | — | — | — |
| Operations | Not applicable: no runtime service, deployment, or operational surface changes | — | — | — | — |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Change the pack source under `packs/core/.apm/` and regenerate the
  `.agents/`, `.claude/`, and `packages/agentbundle/agentbundle/_data/` copies
  from it.
- Recompute every byte digest after the final content edit, and write both
  digest sites in the same commit.
- Put new test cases in this delivery's own suite, because the status-projection
  suite's test-name set is hash-pinned.

### Ask first

- Adding a value to `exception.reason`, or changing the `allOf` conditional that
  binds `exception` to `disposition`.
- Accepting a reclassification whose durable-owner acceptance was inherited from
  the prior record rather than supplied and validated.
- Making `Reclassified` reachable from any state other than a retained record,
  including at enrolment.
- Editing `workspace.toml` line 378, the shared register for three follow-ons
  held by a concurrent delivery.

### Never do

- Add a disposition. RFC-0096 states reclassification is not a seventh
  disposition, and the record admits exactly `cool-30-days` and
  `retain-exception`.
- Add this spec to the contract's `x-spec` list, which a ticked criterion in a
  frozen spec asserts exactly.
- Edit a frozen spec's body. Annotating its `Status` token with a supersession
  pointer is the one licensed edit and is not a body change.
- Edit any file under `docs/specs/dependency-scoped-completion-receipts/`.
- Add a module, package, top-level directory, or third-party dependency.
- Delete or relocate a lifecycle record or an artifact.

## Testing Strategy

**TDD** covers the record contract, the acceptance envelope, the transition
graph, and artifact preservation — AC1 through AC8.
Each is a compressible invariant over a small closed set, stated as an exact
comparison against a shipped artifact rather than a value authored in a test.

**TDD** also covers the reader outcomes, AC9 through AC13, exercised at the
projected status payload rather than at any single function's return, because
the payload is what a maintainer observes.

**Goal-based checks** cover AC14 through AC21. Each is a one-line comparison —
a token present in a paragraph, a digest equal to a file's bytes, two manifests
agreeing, a heading naming a version, an eval case present, a pointer present —
whose failure is unambiguous and which carries no invariant a test could
compress further.

Manual QA is not used. Every artefact this change produces is a JSON record or a
JSON status payload, both of which a test reads more reliably than a person.

## Acceptance Criteria

- [x] **AC1 — The contract admits five results.** `post_closeout_result` in
  `contracts/jsonschema/delivery-lifecycle-record.schema.json` accepts exactly
  `Cooling`, `Retained`, `Retired`, `Reclassified`, and `ExternalAdvisory`.
- [x] **AC2 — The validator admits the contract's set.** The set of
  `post_closeout_result` values the record validator accepts equals the set the
  contract publishes.
- [x] **AC3 — A retained record reclassifies on a supplied acceptance, not on a
  date.** Given a persisted record with disposition `retain-exception` and result
  `Retained`, when a well-formed acceptance block is supplied, the persisted
  record carries disposition `retain-exception` and result `Reclassified`,
  whatever the current date.
- [x] **AC4 — The record carries the supplied acceptance.** The reclassified
  record's `exception` block equals the block supplied at the transition.
- [x] **AC5 — Reclassification refuses a malformed acceptance.** A
  reclassification whose supplied block is absent, is not an object, carries a
  key outside the exception envelope, or fails that envelope's vocabulary rules
  leaves the persisted record byte-unchanged and reports an invalid envelope.
- [x] **AC6 — Retention is the only route in.** The transition graph admits
  exactly one edge whose destination is disposition `retain-exception` with
  result `Reclassified`, and that edge's source is disposition
  `retain-exception` with result `Retained`.
- [x] **AC7 — Reclassification is terminal.** The transition graph admits no
  edge whose source is disposition `retain-exception` with result
  `Reclassified`.
- [x] **AC8 — Reclassification does not move the artifact.** After a record
  reclassifies, a regular file remains at the locator that record names.
- [x] **AC9 — A reclassified artifact leaves ordinary orientation.** An artifact
  named by a lifecycle record with disposition `retain-exception` and result
  `Reclassified` is absent from the scanned, dispatchable set.
- [x] **AC10 — A reclassified artifact's body is not read.** Resolving status
  over that artifact opens no handle on the file its record names.
- [x] **AC11 — A reclassified record is never due.** The projection reports
  `due: false` for it on every date, because it excludes the result before
  comparing any date.
- [x] **AC12 — A reclassified record is not a live obligation.** It is absent
  from the projected retention-exceptions list.
- [x] **AC13 — A reader that cannot recognise the result fails loudly.** When
  the resolving cooling module rejects `Reclassified`, the run reports
  `invalid_lifecycle_record` naming that record and reports cooling context as
  visible, rather than omitting the record silently.
- [x] **AC14 — The cooled-set prose accounts for every result.** The
  `workspace-status` skill document states, for each of the five results,
  whether an artifact named by that record is excluded from orientation.
- [x] **AC15 — Every pinned digest names current bytes.** For each file in the
  `cooling-scope-closure` AC23 pinned set, the digest recorded in that spec's
  table and the digest recorded in the roster test constant both equal the
  file's SHA-256.
- [x] **AC16 — The Core manifests agree.** `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json` carry the same version.
- [x] **AC17 — The Core version advances.** That version is greater than the
  version on the merge base.
- [x] **AC18 — The topmost Core changelog heading names the shipped version.**
  The first `## [core][…]` heading in `docs/product/changelog.md` names the
  version both Core manifests carry.
- [x] **AC19 — The generated copies match the pack source.** Each regenerated
  `close-work` and `workspace-status` file under `.agents/`, `.claude/`, and
  `packages/agentbundle/agentbundle/_data/` is byte-identical to its
  `packs/core/.apm/` source.
- [x] **AC20 — The superseded transition criterion names its correction.**
  `docs/specs/thirty-day-cooling-and-retirement/spec.md` and its sibling
  `plan.md` each carry a `Status` annotation naming the ADR that records the
  extended transition table and the part it supersedes.
- [x] **AC21 — The eval harness covers the reclassification outcome.** The
  `close-work` eval set contains a case whose expected behaviour is a retained
  record transitioning to result `Reclassified` on a validated durable-owner
  acceptance.

## Follow-ons

- RFC-0096 Wave 7c pruning (`rfc0096-wave7c-pruning`): the entry-removal
  precondition, reassigned by the decision recorded in
  [`docs/product/design/rfc0096-wave7c-lifecycle-record-decisions.md`](../../product/design/rfc0096-wave7c-lifecycle-record-decisions.md).
  A pruning session must prove that an artifact's file and its workspace entry
  are removed together; a self-reported record field cannot supply that.

## Assumptions

- Technical: the published record contract is
  `contracts/jsonschema/delivery-lifecycle-record.schema.json` at
  `contract_version: delivery-lifecycle-record.v1`, and its
  `post_closeout_result` enum carries four values (source:
  `contracts/jsonschema/delivery-lifecycle-record.schema.json:7,18`)
- Technical: `retain-exception` already pairs with a result that is not itself a
  disposition, so no disposition is needed (source:
  `packs/core/.apm/skills/close-work/scripts/cooling.py:63,875`)
- Technical: an exception-review outcome that is neither a renewal nor a return
  to cooling carries the prior record's exception block forward (source:
  `packs/core/.apm/skills/close-work/scripts/cooling.py:896`)
- Technical: the record validator holds its own literal copy of the accepted
  result set, independent of the contract (source:
  `packs/core/.apm/skills/close-work/scripts/cooling.py:331`)
- Technical: the contract and the validator are SHA-256 byte-pinned by AC23 of
  `cooling-scope-closure`, which is `Status: Implementing` and so not frozen
  (source: `tests/roster/test_cooling_scope_closure.py:842`;
  `docs/specs/cooling-scope-closure/spec.md:3` for the status and `:281-291`
  for the digest table)
- Technical: an artifact is excluded from orientation only when its record's
  `(disposition, post_closeout_result)` pair is an admitted cooling pair (source:
  `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py:2102`)
- Technical: the Core pack version is pinned three ways — both manifests and the
  topmost dated Core changelog heading must name it (source:
  `tests/roster/test_security_checklists_okf_projection.py:112-122`)
- Technical: the status-projection suite's test-name set is SHA-256 pinned, so
  new cases belong in this delivery's own suite (source:
  `tests/roster/test_cooling_scope_closure.py:443-454`)
- Technical: JSON Schema has no contract-authoring skill installed, so the
  contract is edited directly without standard-specific rule enforcement
  (source: `.claude/skills/new-spec/references/contract-types.md:16`)
- Technical: no corpus of real lifecycle records is reachable to validate AC2's
  refusal against recorded inputs, because `docs/lifecycle/` holds no records;
  the refusal is validated against constructed payloads only (source:
  `docs/lifecycle/` contains only `README.md`)
- Process: a non-cosmetic `.apm/**` change bumps both Core manifests and updates
  the pack's eval harness (source: `packs/AGENTS.md:45,60`)
- Process: the spec-to-contract backward reference is warn-only, so omitting
  this spec from `x-spec` fails no gate (source:
  `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py:1246`)
- Process: extending the transition table falsifies ticked AC22 of the frozen
  spec `thirty-day-cooling-and-retirement`, whose oracle is a table in that
  spec's frozen `plan.md`, and no gate detects it because the refusal sweep runs
  over a hardcoded domain (source:
  `docs/specs/thirty-day-cooling-and-retirement/plan.md:117-124`;
  `tests/roster/test_thirty_day_cooling_and_retirement.py:309-325`; user
  confirmation 2026-09-03)
- Product: `Reclassified` is reachable only as a transition from a retained
  record, so no `exception.reason` value is added (source: user confirmation
  2026-09-03)
- Product: a reclassified artifact is excluded from orientation, never due, and
  not a live obligation (source: user confirmation 2026-09-03)
- Product: this spec is not named in the contract's `x-spec`, because that list
  is asserted exactly by ticked AC15a of the frozen spec
  `cooling-untrusted-input-refusals` (source:
  `tests/roster/test_thirty_day_cooling_and_retirement.py:1617`;
  `docs/specs/cooling-untrusted-input-refusals/spec.md:311`; user confirmation
  2026-09-03)
- Technical: the acceptance block is validated for shape and vocabulary only.
  `evidence_ref` is optional and `owner_role` is a pattern-matched string bound
  to no approver, which is the same standard every `Retained` record meets
  (source: `packs/core/.apm/skills/close-work/scripts/cooling.py:279-296`)
- Technical: no deletion route admits a lifecycle record, because the
  confirmed-deletion seam accepts only a `delivery-contract` surface role while
  records resolve to a runtime-coordination destination; `Retired` and
  `ExternalAdvisory` are already terminal and already share this property
  (source: `packs/core/.apm/skills/close-work/scripts/close_work.py:1596`;
  `packs/core/.apm/skills/close-work/scripts/cooling.py:647`)
- Product: the record states rather than proves the durable owner's acceptance,
  and reclassification is irreversible, both accepted rather than repaired
  (source: user confirmation 2026-09-04)
