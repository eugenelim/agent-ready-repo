# Plan: Reclassified lifecycle result

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/CONVENTIONS.md` § *Superseding a frozen document*
  (`:140-160`, `:456`) governs the AC22 correction; the shipped
  `("retain-exception", "ExternalAdvisory")` outcome at
  `packs/core/.apm/skills/close-work/scripts/cooling.py:63,875` is the analogous
  implementation and `tests/roster/test_thirty_day_cooling_and_retirement.py` its
  construction path. Named uncertainty: the ADR ordinal is not reserved, so 0105
  may be taken before this merges.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`.

## Approach

Widen one enum in the two places that hold it independently, then add a
dedicated producer that validates the durable owner's acceptance and persists
through the existing guarded writer. The record's structural contract — its
`disposition` enum, its `exception` conditional, its required keys — does not
move.

The producer is a new module-level entry point rather than another
`review_exception` outcome, for two reasons found by review. First,
`review_exception` gates every outcome on `is_due`, which compares the
*top-level* `review_on`; `_proposed_record` never updates that field, so for any
retained record the comparison is against the original day-30 date and can never
refuse. Reusing that seam would give reclassification a date gate that cannot
fail. Second, the outcomes that inherit the prior exception ignore `attestation`
entirely, so reclassification through that branch would carry a block the caller
never supplied. The new entry point takes the validation `renew` uses and
consults no date. That validation checks shape and vocabulary, not authority —
the same bar retention already meets — which the spec records rather than
raises.

Contract first, then the transition, then the readers: each later layer needs
the value to exist. Governance lands with the transition that creates the need
for it.

The risk is not the code; it is the pinning. Six mechanisms pin content this
change touches, and they behave differently. Four fail loudly: the six-file byte
digest, the exact set-equality on the engine's cooling pairs, the three-way Core
version pin, and the removal-surface guard that counts the literal `unlink` in
the validator's module. Two do not fail at all — a ticked criterion in a frozen
spec whose oracle is an uneditable table, and a hash over the status-projection
suite's test-name set that fires only if a test is added there. The silent pair
is why T3 exists and why new cases go in a new suite.

Digests are computed last. Any earlier computation is stale by the time the
task ends.

## Constraints

- RFC-0096 § 2 (`:83`): reclassification ends delivery authority without
  deletion and is not a disposition. No disposition is added.
- RFC-0096 2026-09-03 Errata (`:432`): Wave 7c owns this follow-on.
- `docs/CONVENTIONS.md:456` and `:153`: a frozen spec accepts only a
  `Status`-token parenthetical, and it must name an ADR.
- `docs/CONVENTIONS.md:119-121`: a shipped spec directory freezes as a unit,
  `spec.md` and `plan.md` together.
- The 2026-09-03 decision in
  [`docs/product/design/rfc0096-wave7c-lifecycle-record-decisions.md`](../../product/design/rfc0096-wave7c-lifecycle-record-decisions.md):
  Option A, transition-only reachability, and cooled reader semantics. The
  `x-spec` deviation and the ADR carrying the AC22 correction were settled by
  separate task-owner confirmations on 2026-09-03, after that document was
  written; it does not record them.

## Construction tests

**Integration tests:** none beyond per-task tests. The projected status payload
is exercised in T4 at the projection surface, which is where the observable
outcome lives.

**Manual verification:** none. Every artefact is a JSON record or status payload.

**Suite placement.** Every new case lands in
`tests/roster/test_reclassified_lifecycle_result.py`. Adding a case to
`tests/roster/test_status_projection_and_context_exclusion.py` would change its
`def test_*` name set, which `tests/roster/test_cooling_scope_closure.py:443-454`
SHA-256 pins. That file is edited only at its `COOLING_PAIRS` literal, which
adds no test name.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility — the record contract | T1 | Exact five-value assertion on the schema, plus a probe comparing the validator's accepted set to it | Contract and validator admit the same set |
| Decision rationale — the Option A record | T3 | The design document's recorded decision | The rejected alternative survives as a readable record |
| Decision rationale (dependent contract) — the AC22 correction | T3 | The ADR and both `Status` annotations | The superseded criterion names the ADR that corrects it |
| Maintainer procedure — cooled-set prose | T5 | Each of the five result tokens present in the paragraph | No result is unaccounted for |
| Release history — Core version and changelog | T6 | Both manifests agreeing, and the topmost Core heading naming that version | The three-way version pin is green |
| Interface compatibility (dependents) — pinned digests | T6 | Both digest sites recomputed after the final content edit | Every pinned digest equals its file's bytes |

## Design (LLD)

### Data & schema

The record's structural contract does not move: `disposition` keeps two members,
the `allOf` conditional binding `exception` to `retain-exception` is untouched,
and the required-key set is untouched. That is what keeps
`tests/roster/test_thirty_day_cooling_and_retirement.py:175` (exact required-key
equality) and `:179-188` (every object closed with a non-empty `required`) green
without modification — they are the standing evidence that only the enum moved.

`Reclassified` is terminal and reachable from one state. The producer replaces
the predecessor's `exception` with the acceptance block supplied at the
transition; it does not inherit it. No `exception.reason` member is added,
because the durable owner selects from the published enum.

Traces to: AC1, AC3, AC4, AC5, AC6, AC7 · `contracts/jsonschema/delivery-lifecycle-record.schema.json`

### Interfaces & contracts

Two surfaces hold the admitted result set independently — the published contract
and the validator's own literal at
`packs/core/.apm/skills/close-work/scripts/cooling.py:331`. Equality between
them is necessary but not sufficient: two derived sets agree while both are
stale. So the contract is asserted exactly against a literal five-tuple, and the
validator is then compared to the contract. The comparison probe includes a
value outside the published set, so it fails if the validator accepts anything.

The reader surfaces consume the value through the cooling-pair predicate and the
due predicate. Neither gains a `Reclassified` branch: the pair joins the admitted
cooling set and the result joins the due predicate's exclusion set, so the new
result is handled by existing mechanisms rather than a parallel one.

Traces to: AC2, AC9, AC10, AC11, AC12, AC13 · `contracts/jsonschema/delivery-lifecycle-record.schema.json`

## Tasks

### T1: The contract and the validator admit the same five results

**Depends on:** none

**Touches:** `contracts/jsonschema/delivery-lifecycle-record.schema.json`,
`packs/core/.apm/skills/close-work/scripts/cooling.py`,
`tests/roster/test_reclassified_lifecycle_result.py`

**Tests:**
- The contract is asserted exactly, not by agreement with the validator. Both
  are derived, so equality alone passes while both remain four-valued.
- AC2 is proved exhaustively, not by sampling: a probe cannot show the validator
  accepts *no* other value. The membership set the validator tests
  `post_closeout_result` against is captured at its `_is_one_of` call and
  compared to the schema enum, so an extra member on either side fails.
- `stub: true` — red today, compiles against shipped paths:

  ```python
  import importlib.util
  import json
  from pathlib import Path

  ROOT = Path(__file__).resolve().parents[2]
  COOLING_PATH = ROOT / "packs/core/.apm/skills/close-work/scripts/cooling.py"
  SCHEMA_PATH = ROOT / "contracts/jsonschema/delivery-lifecycle-record.schema.json"
  RESULTS = ["Cooling", "Retained", "Retired", "Reclassified", "ExternalAdvisory"]


  def _load():
      spec = importlib.util.spec_from_file_location("wave7c_cooling", COOLING_PATH)
      assert spec is not None and spec.loader is not None
      module = importlib.util.module_from_spec(spec)
      spec.loader.exec_module(module)
      return module


  def test_the_contract_admits_exactly_five_results() -> None:  # AC1
      schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
      assert schema["properties"]["post_closeout_result"]["enum"] == RESULTS
  ```

- `tests/roster/test_thirty_day_cooling_and_retirement.py:175` and `:179-188`
  stay green unmodified; they are the evidence the structural contract held.

**Approach:**
- Add the member to the schema enum, in the contract's existing order.
- Add the member to the validator's literal set.

**Done when:** the exact-five assertion and the validator probe both pass, and
the two structural-contract cases pass without edit.

### T2: A retained record reclassifies on a validated acceptance

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/close-work/scripts/cooling.py`,
`tests/roster/test_thirty_day_cooling_and_retirement.py`,
`tests/roster/test_reclassified_lifecycle_result.py`

**Tests:**
- Extend `_TRANSITION_TABLE` at
  `tests/roster/test_thirty_day_cooling_and_retirement.py:301` with the accepted
  pair, and add `("retain-exception", "Reclassified")` to **both** literal domain
  tuples building `_TRANSITION_COMPLEMENT` at `:309-325`. That domain is
  hardcoded, not derived from the schema, so without the second edit the new
  state never enters the refusal sweep and AC6 and AC7 are asserted by nothing.
  With it, the existing sweep proves both exhaustively over the widened domain.
- A case asserting the persisted record's `exception` equals the block supplied,
  not the predecessor's.
- Negative cases for AC5: acceptance absent, not an object, and failing the
  exception envelope's own rules. Each must leave the persisted bytes unchanged,
  so each asserts the file's digest before and after.
- A case proving reclassification is not date-gated: the same acceptance
  succeeds with a clock before the record's `review_on`. Without it, AC3's
  "whatever the current date" is asserted by nothing.
- **A mutation proof that the producer delegates to `update_record`.** Only
  `update_record` consults the transition table (`cooling.py:751`);
  `_write_record` does not (`:554`). So asserting table membership and asserting
  the producer persists are independent facts, and even a removed-edge refusal
  proves too little — a producer could repeat the membership check itself and
  still write directly. The proof therefore spies on `update_record` during the
  mutation: with the edge removed from `_TRANSITIONS`, the producer must invoke
  `update_record` exactly once with the expected prior and proposed records,
  return `record-invalid`, and leave the persisted bytes byte-identical. The
  invariant is that reclassification reaches disk only through transition
  enforcement; the mutation is deleting the edge; the expected failure is a
  single delegated call that refuses, not a write.
- A case for AC8: create a regular file at the record's locator, reclassify, and
  assert a regular file is still there. Nothing else proves the transition did
  not move or remove the artifact.
- **Preservation check, not a new assertion:**
  `tests/roster/test_thirty_day_cooling_and_retirement.py:1113-1120` forbids
  `remove`, `rmdir`, `removedirs`, and `rmtree` in `cooling.py` and asserts the
  literal `unlink` occurs exactly once. That is a raw substring count over the
  whole file, so even a comment mentioning unlink reddens it. The edits here add
  neither a removal call nor the word.
- `stub: true` — red today, uses T1's `_load`:

  ```python
  def test_the_transition_table_admits_reclassification() -> None:  # AC6
      cooling = _load()
      assert (
          ("retain-exception", "Retained"),
          ("retain-exception", "Reclassified"),
      ) in cooling._TRANSITIONS
  ```

**Approach:**
- Add the transition pair to `_TRANSITIONS`.
- Add a module-level producer that accepts a prior record and a supplied
  acceptance, validates it with the same envelope check `review_exception` uses
  for `renew` at `cooling.py:892`, builds the target through `_proposed_record`,
  and persists through `update_record`. It consults no date.
- Add no removal call, and do not write the literal `unlink` anywhere in the
  module.

**Done when:** the widened accepted and refusal sweeps pass, a reclassified
record carries the supplied acceptance, each negative case leaves the persisted
bytes byte-identical, the not-date-gated case passes, and under the
removed-edge mutation the producer delegates once to `update_record` and
refuses.

### T3: The frozen transition criterion points at its correction

**Depends on:** T2

**Touches:** `docs/adr/0105-*.md`,
`docs/specs/thirty-day-cooling-and-retirement/spec.md`,
`docs/specs/thirty-day-cooling-and-retirement/plan.md`

**Blocker to clear first:** the ADR ordinal is not reserved. Re-derive the next
free ordinal immediately before writing, and use the same value in the file name
and both pointers.

**Tests:**
- Goal-based:
  `python3 packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py --root .`
  reports no new finding, and the annotated `Status` tokens still satisfy the
  vocabulary rule, which truncates at the first ` (`.
- No test asserts AC22's pair count, which is why this task exists: the criterion
  goes false with nothing reddening.

**Approach:**
- Author the ADR recording that the transition table admits reclassification
  from retention, and why the record contract carries it.
- Annotate both `Status` lines in the frozen directory with a parenthetical
  naming the ADR and the superseded part. Change no body line.

**Done when:** both frozen documents carry a pointer naming the ADR and the part
superseded, and `git diff` shows only their `Status` lines changed.

### T4: A reclassified artifact leaves orientation and is never due

**Depends on:** T1, T2 — the reader must not cool a state the transition table
cannot reach, or an intermediate tree passes its own tests while no producer
exists.

**Touches:**
`packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`,
`packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`,
`tests/roster/test_status_projection_and_context_exclusion.py`,
`tests/roster/test_reclassified_lifecycle_result.py`

**Tests:**
- Update the `COOLING_PAIRS` literal at
  `tests/roster/test_status_projection_and_context_exclusion.py:20`. The
  set-equality guard at `:168` fails until it moves; its docstring states the
  reason. The `:172` parametrization then covers the new pair automatically.
- A projection-level case: place the reclassified artifact in live coordination
  and assert it is absent from the dispatchable set and its body unread. The
  inherited parametrization proves cooled-locator membership only, which is a
  weaker claim than AC9 and AC10.
- Cases for the due projection on and after the review date, and for absence
  from the retention-exceptions list.
- A version-skew case for AC13: resolve status with a cooling module that
  rejects the new result, and assert the run reports `invalid_lifecycle_record`
  naming that record and reports cooling context as visible. The engine resolves
  the module at `workspace_status_engine.py:2130`, so an older installed copy is
  reachable in production; `workspace_status.py:798` is what makes the failure
  loud rather than a silent omission.
- **Preservation checks, not new assertions:**
  `tests/roster/test_cooling_scope_closure.py:443-454` hashes this suite's
  test-name set, so no test is added to it; and
  `tests/roster/test_cooling_scope_closure.py` counts the single-argument
  reconciliation call sites in `workspace_status.py`, so the due-predicate edit
  adds and removes no call.
- `stub: true` — red today:

  ```python
  import sys

  ENGINE_PATH = (
      ROOT / "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py"
  )


  def _load_engine():
      spec = importlib.util.spec_from_file_location(
          "workspace_status_engine", ENGINE_PATH
      )
      assert spec is not None and spec.loader is not None
      module = importlib.util.module_from_spec(spec)
      # The module carries postponed dataclass annotations that resolve against
      # its own name, so it must be in sys.modules before exec_module runs.
      sys.modules[spec.name] = module
      try:
          spec.loader.exec_module(module)
      finally:
          sys.modules.pop(spec.name, None)
      return module


  def test_the_engine_cools_a_reclassified_record() -> None:  # AC9
      assert ("retain-exception", "Reclassified") in _load_engine()._COOLING_PAIRS
  ```

**Approach:**
- Add the pair to the engine's admitted cooling set.
- Add the result to the due predicate's exclusion set alongside the retired one.
- Leave the obligations predicate unchanged; absence is the required outcome.

**Done when:** the set-equality guard passes, the projection-level cases show the
artifact absent from dispatch and its body unread, and a reclassified record projects `due: false` with
no exceptions entry.

### T5: The cooled-set prose accounts for every result

**Depends on:** T4

**Touches:** `packs/core/.apm/skills/workspace-status/SKILL.md`

**Tests:**
- Goal-based. The paragraph at `:266-268` partitions four results today; a grep
  for each of the five result tokens within it returns a hit.

**Approach:**
- Extend the exclusion clause to name the new result.

**Done when:** every one of the five results appears on a named side of the
exclusion boundary in that paragraph.

### T6: The release surface matches the changed content

**Depends on:** T1, T2, T3, T4, T5

**Touches:** `tests/roster/test_cooling_scope_closure.py`,
`docs/specs/cooling-scope-closure/spec.md`, `packs/core/pack.toml`,
`packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`,
`packs/core/.apm/skills/close-work/evals/evals.json`, and the regenerated
`.agents/`, `.claude/`, and `packages/agentbundle/agentbundle/_data/` copies

**Tests:**
- Goal-based. `FORCE=1 make build-self` leaves regenerated copies byte-identical
  to their pack sources, and `make build-check` passes.
- The version is pinned three ways, not two:
  `tests/roster/test_security_checklists_okf_projection.py:112-122` asserts both
  manifests agree *and* that the topmost `## [core][…]` heading in
  `docs/product/changelog.md` names that version. A bump without the heading
  reddens it.
- Goal-based for the eval case: the close-work eval set contains an entry whose
  expected behaviour names the retained-to-`Reclassified` transition and the
  preserved exception. `packs/AGENTS.md:60` requires the harness to move with
  a non-cosmetic pack change, and nothing else asserts it did.
- The AC23 digest case is the oracle for the digests and reddens if either site
  is stale. Four rows move, not two: the contract and the validator from T1 and
  T2, and the frozen spec and plan from T3.

**Approach:**
- Add the eval case to the close-work harness as the next free id.
- Add the dated Core changelog entry as the topmost `## [core][…]` heading.
- Bump the patch version in both manifests, derived from the merge base rather
  than a literal carried from another change.
- Regenerate projections, then recompute all four digests and write both sites.

**Done when:** the digest case, the three-way version pin — manifests agreeing,
the version advanced, and the topmost heading naming it — and the projection
parity gate are all green.

## Rollout

A pure-logic and contract change with no infrastructure, no external system, and
no deployment sequencing. It ships in one PR behind no flag. Every code and
document edit is reversible; the published enum member is not, since an adopter
may have written it into a record before it could be reconsidered — which is why
the value is terminal and reachable from one state only.

Origin is unreachable in this workspace, so the Core version is derived locally
from the merge base after rebasing onto the concurrent Wave 7b delivery, which
merges first by agreement.

## Risks

- **The ADR ordinal is not reserved.** A concurrent delivery holds 0104 unmerged
  and may take 0105 first. Re-derive at rebase and update the file name and both
  pointers together; a pointer naming a stolen ordinal is worse than none.
- **Three shared files with a concurrent delivery.** The engine, the
  `workspace-status` skill document, and the status-projection roster test are
  edited by Wave 7b at different lines. That delivery lands first, so the
  mitigation is to re-read all three after rebase and confirm both sides
  survived, rather than trusting a clean textual merge.
- **Parent-scope attribution changes meaning mid-flight.** On the current base,
  a cooled child is attributed only when its entry declares `source.parent`; a
  parentless one is deliberately unattributed, the recorded
  `cooling-brief-child-scope` residual
  (`packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py:2883`).
  The concurrent Wave 7b delivery closes that residual with a fail-closed floor,
  after which a parentless reclassified entry *will* refuse brief dependencies.
  Re-read this consequence after rebasing onto that delivery; the Objective
  describes the base as it stands.
- **Two pins fail silently.** The frozen AC22 criterion and the test-name hash
  both stay green while being violated. T3 and the suite-placement rule are the
  only things standing between this change and either one.
- **Digest staleness.** Any content edit after T6 invalidates all four digests
  until the case runs. Recompute; never carry a value forward.

## Changelog

- 2026-09-03: initial plan.
- 2026-09-03: after shaping review — split the contract assertion from the
  validator comparison, because two derived sets agree while both are stale;
  added the changelog to the release surface after finding the version pinned
  three ways; recorded the test-name hash and reconciliation-call count as
  preservation checks; added the projection-level case for orientation absence.
- 2026-09-04: after shaping re-review — registered the engine stub in
  `sys.modules` so it fails at its assertion rather than at import; mapped the
  artifact-preservation criterion to a real test; split two conjoined criteria;
  recorded the removal-surface guard as a sixth pin.
- 2026-09-04: after shaping round 3 — made the validator comparison exhaustive
  by capturing its membership set rather than probing one value; corrected the
  pin inventory to six; re-attributed the AC22 decision to its own confirmation.
- 2026-09-04: after adversarial spec review — replaced the `review_exception`
  outcome with a dedicated producer, because that seam's date gate cannot fail
  and its inheriting branch ignores the attestation; made the acceptance
  supplied and validated rather than inherited; added the version-skew case; and
  made T4 depend on T2.
- 2026-09-04: after adversarial round 2 — corrected the design section that
  still described an inherited exception; qualified the parent-scope consequence
  to entries declaring `source.parent`; and weakened the acceptance and
  reversibility claims to what the machinery delivers, after finding `Retired`
  and `ExternalAdvisory` already share both limits.
- 2026-09-04: after adversarial round 3 — added a mutation proof binding the
  producer to the transition table, because asserting table membership and
  producer success separately would pass for a producer that bypassed
  enforcement entirely.
- 2026-09-04: after adversarial round 4 — the mutation now spies on
  `update_record`, because a refusal alone was also satisfiable by a producer
  that duplicated the membership check and wrote directly.
