# Plan: Completion receipts and cooling scope

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/work-intake-and-artifact-routing.md`
  and `docs/CONVENTIONS.md`. Two analogous production implementations: the
  coordination-receipt reader — `_COORDINATION_RECEIPT_FIELDS`,
  `_validated_receipt_match`, `_cross_repo_receipt_satisfied` in
  `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`
  — which fixes the field-set-constant idiom, the in-construction duplicate
  check, and the precedent that a receipt gets no file under
  `contracts/jsonschema/`; and Wave 6's cooling projection —
  `_resolve_cooled_state` plus the `cooling` and `closeout` blocks in
  `workspace_status.py` — which fixes the block-projection idiom and the
  emission gate. Their tests are
  `tests/roster/test_status_projection_and_context_exclusion.py` and
  `tools/test_workspace_status_cli.py`. Named uncertainty: every anchor inside
  `_dependency_is_satisfied` is resolved by symbol, not by line — that function
  moved twice during Wave 6.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially (a different approach, not just
> a re-ordering), note why in the changelog at the bottom. Once it is `Done`
> and the spec is `Shipped`, the directory freezes as a unit.

## Approach

The delivery has a producer half and a consumer half, and the producer half is
new work that round-1 review uncovered: nothing in the repository names the
receipt key today, so `close-work`'s instructions gain the exact spelling before
the reader is written. T2 lands the writer's half first for that reason — a
reader whose producer emits a different key is a control that cannot fire.

The engine then gains one reader and one decision point. The reader parses the
top-level `completion_receipts` array into a mapping keyed by `delivery_id`,
built with the in-construction duplicate check the sibling reader already uses,
extended to drop both occurrences rather than keeping the first.

The decision point is keyed on a **finding code in one arm**, not on a phase.
`notes/probes.md` probes 5 and 8 fix the coordinates: an absent dependency
target is refused by `_dependency_metadata_safety_finding` with
`missing_dependency` before any terminal-status test, and
`_dependency_is_satisfied` carries two further refusals after that helper. The
gate therefore goes on the **general arm only**, leaving the `defect` arm's own
`missing_dependency` return and both post-helper refusals untouched. Probe 8
carries the return order; this plan does not restate it.

The cooling work is separate and smaller. `all_specs_shipped` and `queue_empty`
are two expressions in `workspace_status.py` today, which is why Wave 6's repair
could filter one and not the other. They collapse into one cooled-exclusion pass
that both read. `closeout` describes one initiative, so the agreement criterion
is scoped to that initiative and compares the cooled delta rather than asserting
the two values are equal — they are derived over different lists by design and
were never meant to be equal.

The repair and migration decision produces no behaviour change. Its deliverable
is five control-run identities that pin the current outcome, so a later blanket
filter has to edit those lines and justify it.

The riskiest part is the decision point's arm and placement. A receipt consulted
in the `defect` arm, or above the safety return, silently converts refusals into
satisfactions — including the two Wave 6 fail-closed controls. T5's tests lead
with the refusals.

## Constraints

- **RFC-0096 §7** fixes the receipt's four fields and its citation-scoped
  retention licence; **§9** scopes Wave 7; **§10** rejects `workspace.toml` as a
  lifecycle database.
- **`close-work-extraction-and-immediate-disposition` AC17** (frozen) makes the
  receipt minimal, dependency-scoped, and carried on an already established
  surface without inventing the Wave 5 lifecycle schema. It is conditional and
  fixes no key, which is why T2 exists.
- **`thirty-day-cooling-and-retirement`** (frozen) owns `cooling.is_due`,
  `cooling.load_record`, the record schema, and the `docs/lifecycle/`
  single-writer rule; its AC24 test forbids new cooling keys in
  `workspace.toml`.
- **`status-projection-and-context-exclusion`** (frozen) owns the cooled-set
  resolution, the `cooling` and `closeout` blocks, the emission gate, and the
  read-free metadata rule for a cooled membership.
- **RFC-0099 §7**, as recorded in RFC-0096's Errata, makes a post-sealing
  criterion change a material amendment requiring reapproval and resealing.
- **`docs/CONVENTIONS.md`** freezes a shipped spec directory as a unit.

## Construction tests

**Two verification shapes, and the difference matters.** AC1-AC34 and AC58
specify new behaviour and get compiled red stubs. AC35-AC41, AC47, AC49, AC53,
AC55, and AC56 are **preservation** criteria: they assert something already true
stays true, so they are green before the change by design and a red stub is
impossible. Each is verified by a named mutation instead, in the table below.
Recording a preservation criterion as "red" would be the defect Wave 6 shipped
six times.

**Integration tests:** one CLI-level run per emitting subcommand (`status`,
`reconcile`, `repair-plan`, `explain`) over a single fixture carrying a valid
cited receipt, a refused receipt, an uncited receipt, a cooled queue entry, and
an uncooled sibling — added to `tools/test_workspace_status_cli.py`. The
engine-level suites cannot catch a block emitted by the shared builder and
dropped by a subcommand's own builder, which is the defect class Wave 6's AC35
exists for.

**Manual verification:** T12.

### Mutation table

Every guard this delivery adds has one mutation verified to redden its named
case. The mutation is applied by editing the source, its named test is confirmed
red, and the file's digest is re-asserted after restore.

| Mutation | Reddens |
| --- | --- |
| drop the key-set equality check in the receipt validator | AC5 |
| accept a control character in a receipt field | AC6 |
| keep the first duplicate instead of dropping both | AC7 |
| return early on the first refused receipt | AC8 |
| treat a non-list `completion_receipts` as an empty list | AC10 |
| drop the citation scan | AC15, AC16 |
| skip confinement on `delivery_id` | AC18 |
| drop the `outcome == "completed"` test | AC20 |
| move the receipt consultation above the safety return | AC23 |
| extend the receipt gate to the `defect` arm | AC25 |
| extend the receipt gate below `brief_scope_unknown` | AC24 |
| emit the receipts block from the shared builder ungated | AC41 |
| filter cooled entries from `all_specs_shipped` only | AC28 |
| drop the `cooling_context_visible` guard | AC31 |
| pass a repository root to either rootless call site | AC40 |
| add a cooled filter to `repair-plan` | AC35 |
| add a cooled filter to the migration apply path | AC38 |

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `user-documentation` / close-work SKILL.md | T2 | AC12 and AC13 string assertions | Writer spelling matches reader |
| `runtime-coordination` / `workspace.toml` | T3, T4 | AC58 byte-identity across every fixture | No receipt writer in `workspace-status` outside `repair-apply` |
| `current-architecture` / work-intake routing | T9 | AC47 pinned trio plus AC48 | Three strings, absent string, two new statements |
| `user-documentation` / workspace-toml-schema | T9 | The finding-code gate, AC43, AC45 | Two rows, shape, posture |
| `user-documentation` / workspace-status SKILL.md | T9 | The finding-code gate, AC44, AC45, AC46 | Two rows, section, posture, closeout paragraph |
| `capability-evidence` / Wave 6 Status line | T10 | AC53 digest and AC54 pointer form | Body unchanged, pointer resolves |
| `decision-record` / RFC-0096 Errata | T10 | AC49-AC52 | Three corrections recorded, §9 digest unchanged |
| `interface-contract` / lifecycle record | T10 | AC55, AC56 digests | Digests match |
| `release-history` / changelog | T11 | AC57 | Three surfaces agree |
| `project-knowledge` | T12 | Gate receipt or not-applicable finding | One of the two |

## Design (LLD)

### Design decisions

- **The receipt lives in `workspace.toml`.** Wave 4 AC17 forbids folding it into
  the Wave 5 record, and a separate file under `docs/lifecycle/` would be the
  receipt store `close-work`'s instructions forbid. Rejected alternative: a
  fenced block in the citing artifact — dependency-scoped by construction, but
  unreadable exactly when the artifact is cooled or pruned, which is the case
  the receipt exists for. Traces to: AC1, AC14.
- **`delivery_id` is the join key and needs no companion field.** Probe 6 shows
  a colon-bearing value confines to a real path, so the writer's instructions
  must say which form to use rather than the reader guessing. Rejected
  alternative: a `cited_by` array, which would make the receipt five fields and
  duplicate `needs`. Traces to: AC13, AC17, AC18.
- **The reader mirrors the writer's bound instead of tightening it.** Probe 7
  measured this against the shipped writer's corpus: 10 accepted, 1 rejected,
  and the one rejection is the writer's own deliberate malformed case. Traces
  to: AC6.
- **Only a completion satisfies.** The ordinary path satisfies on a successful
  terminal status alone, so honouring `abandoned` or `superseded` would unblock
  work the same engine refuses when the artifact is present. Traces to: AC19,
  AC20.
- **Two codes, not one.** A malformed receipt and an expired retention licence
  have different remedies — correct the block versus remove it through
  `close-work` — and a shipped consumer routes on the code. Traces to: AC5,
  AC15.

### Data & schema

A top-level TOML array of tables. No file under `contracts/jsonschema/`: the
sibling coordination receipt is validated by a field-set constant alone, and
`workspace-entry.schema.json` pins one *entry*, which AC9 establishes a receipt
is not. The validated in-memory form is a mapping keyed by `delivery_id`, built
with an explicit in-construction duplicate check that drops **both**
occurrences — the sibling idiom refuses only the later one, and AC7 requires
neither to survive. Traces to: AC1-AC11 · contracts: none.

### Behavior & rules

One precondition, one action. Precondition: in the general arm,
`_dependency_metadata_safety_finding` returned `missing_dependency`. Action: if
a validated, cited receipt whose `outcome` is `completed` resolves to the same
confined path as the dependency, the dependency is satisfied and the finding is
dropped. Probe 8 in `notes/probes.md` carries the surrounding refusal order and
is the single home for it. Traces to: AC19-AC27.

### Failure, edge cases & resilience

- A `completion_receipts` value that is not a list of tables yields one
  collection-level refusal and leaves every other emitted value unchanged.
- A validated but uncited receipt degrades to visibility, never to authority.
- `_is_bounded_text` does not reject control characters, so the new validator
  adds that check itself rather than reusing the helper unchanged.

Traces to: AC10, AC11, AC15, AC16.

## Tasks

### T1: The corpus measurement is recorded and the criteria are final

**Depends on:** none

**Verification mode:** goal-based check. `no stub (mode)` — the deliverable is a
recorded measurement.

**Tests:**
- None. `notes/probes.md` probe 7 is the artifact.

**Approach:**
- Already performed before approval, so no criterion is provisional at the
  sealing gate. Probe 7 records 10 accepted and 1 rejected against every literal
  the shipped writer's tests pass for a receipt field.
- If a later-discovered shipped-writer value is refused, that is a material
  amendment under RFC-0099 §7 — park delivery, invalidate the baseline, return
  to spec-plan drafting, reapprove and reseal. It is not an in-flight criterion
  edit.

**Done when:** probe 7's per-field counts are in `notes/probes.md` and no
shipped writer value is refused.

### T2: The writer's instructions name the key, the fields, and the join rule

**Depends on:** none

**Verification mode:** TDD.

**Tests:**
- Two whitespace-normalized string assertions over
  `packs/core/.apm/skills/close-work/SKILL.md`, in the new roster suite. The
  normalization idiom is the one at
  `tests/roster/test_workspace_status_projection.py:191`, because the target
  sentences wrap in source.

```python
# STUB: AC12 — the writer's instructions name the exact key and fields.
def test_ac12_writer_names_key_and_fields():
    text = _normalized("packs/core/.apm/skills/close-work/SKILL.md")
    assert "[[completion_receipts]]" in text
    for field in ("delivery_id", "outcome", "completion_event", "evidence_ref"):
        assert field in text


# STUB: AC13 — the writer's instructions bind delivery_id to the join key.
def test_ac13_writer_binds_delivery_id_to_the_join_key():
    text = _normalized("packs/core/.apm/skills/close-work/SKILL.md")
    assert "delivery_id is the repository-relative path" in text
```

`stub: true`. Compiled clean; both red against the current tree — the key
appears nowhere in that file.

**Approach:**
- Extend the existing receipt paragraph at `close-work/SKILL.md`; do not add a
  section.
- State the key, the four field names, and that a repository-local delivery's
  `delivery_id` is the delivered artifact's repository-relative path.

**Done when:** AC12 and AC13 pass and `packs/core/tests/skills/close-work/`
still passes.

### T3: A well-formed receipt is projected and a malformed one is refused

**Depends on:** T2

**Verification mode:** TDD.

**Tests:**
- New suite `tests/roster/test_completion_receipts_and_cooling_scope.py`, built
  on the fixture-tree and injected-instant helpers in
  `tests/roster/test_status_projection_and_context_exclusion.py`; reuse them
  rather than authoring a second fixture builder.
- The refusal cases share one parametrized fixture whose only varying part is
  the receipt table, so a validator that refuses everything fails AC8 in the
  same run.
- The finding-code documentation gate at
  `tests/roster/test_workspace_status_projection.py` goes red as soon as a code
  is declared; it stays red until T9.

```python
# STUB: AC1 — a well-formed cited receipt is projected in status.
def test_ac1_wellformed_receipt_is_projected(tmp_path):
    data = _status(tmp_path)
    assert data["receipts"]["retained"] == [{
        "delivery_id": "docs/specs/gone/spec.md",
        "outcome": "completed",
        "completion_event": "work-loop:gates-clean",
        "evidence_ref": "evidence:current",
    }]


# STUB: AC3 — the receipts object's key set is exactly {retained}.
def test_ac3_receipts_key_set_is_closed(tmp_path):
    assert set(_status(tmp_path)["receipts"]) == {"retained"}


# STUB: AC5 — a receipt whose key set differs is refused.
def test_ac5_wrong_key_set_is_refused(tmp_path):
    codes = [f["code"] for f in _status(tmp_path)["canonical"]["findings"]]
    assert "invalid_completion_receipt" in codes
```

`stub: true`. Compiled clean; all three red against the current tree with
`KeyError: 'receipts'` and an absent finding code.

**Approach:**
- Add the field-set constant and the per-element validator beside the
  coordination-receipt reader so the two idioms stay adjacent.
- Declare both finding codes in `_FINDING_NEXT_ACTIONS`.
- Emit the block from the shared JSON builder, not from each subcommand.

**Done when:** AC1-AC11 and AC58 pass; `tools/test_workspace_status.py` and
`tools/test_workspace_status_cli.py` show no new failure other than the
documentation gate T9 closes.

### T4: A retained receipt is in scope only while a live entry cites it

**Depends on:** T3

**Verification mode:** TDD.

**Tests:**
- The citation scan's input is the parsed membership set, so the test asserts
  over an entry whose `needs` names the delivery — not over raw TOML text, which
  would pass while the scan read the wrong collection.
- AC16's fixture carries the citing entry in `work.shipped`, so an
  implementation that treats every membership as live reddens.

```python
# STUB: AC15 — an uncited receipt is reported, not retained.
def test_ac15_uncited_receipt_is_reported(tmp_path):
    data = _status(tmp_path)
    codes = [f["code"] for f in data["canonical"]["findings"]]
    assert "uncited_completion_receipt" in codes
    assert data["receipts"]["retained"] == []
```

`stub: true`. Compiled clean; red against the current tree.

**Approach:**
- Derive the live-cited set from the memberships already parsed for
  reconciliation; add no second walk. The live predicate is the closed set the
  spec's Definitions section names.
- Confine each `delivery_id` before comparison, reusing the engine's existing
  confinement helper.

**Done when:** AC14-AC18 pass, and AC17's fixture uses the literal
`delivery:wave4`.

### T5: A completion receipt satisfies an absent artifact and answers nothing else

**Depends on:** T4

**Verification mode:** TDD.

**Tests:**
- The five refusal cases first, then satisfaction. AC22 pins a spec present with
  `Status: Implementing`; AC23 pins the three safety codes; AC24 pins the
  cooled-children brief; AC25 pins the defect arm; AC20 pins the two
  non-completion outcomes.
- AC21 asserts on `diagnostics.spec_files_read`, already emitted by the shared
  builder — not on a sentinel, because the satisfying run has no body to plant
  one in.
- AC26 runs the cooled fixture twice, with and without a receipt, asserting
  identity; this is the criterion that catches a receipt inserted above Wave 6's
  cooled short-circuit.

```python
# STUB: AC19 — a completion receipt satisfies an absent-artifact dependency.
def test_ac19_completion_receipt_satisfies_absent_artifact(tmp_path):
    ready = [e["path"] for e in _status(tmp_path)["canonical"]["ready"]]
    assert "docs/specs/dependant/spec.md" in ready


# STUB: AC20 — a non-completion receipt satisfies nothing.
def test_ac20_non_completion_receipt_satisfies_nothing(tmp_path):
    blocked = [e["path"] for e in _status(tmp_path)["canonical"]["blocked"]]
    assert "docs/specs/dependant/spec.md" in blocked


# STUB: AC21 — satisfaction reads no artifact.
def test_ac21_satisfaction_reads_no_artifact(tmp_path):
    assert _status(tmp_path)["diagnostics"]["spec_files_read"] == 1


# STUB: AC24 — a receipt does not answer an unknown brief child scope.
def test_ac24_receipt_does_not_answer_unknown_brief_scope(tmp_path):
    codes = {f["path"]: f["code"]
             for f in _status(tmp_path)["canonical"]["findings"]}
    assert codes.get("docs/product/briefs/parent.md") == "missing_dependency"
```

`stub: true`. Compiled clean; all four red against the current tree.

**Approach:**
- Site the consultation where `_dependency_is_satisfied` acts on
  `_dependency_metadata_safety_finding`'s result **in the general arm**, gated on
  that result's code being `missing_dependency` and on the receipt's `outcome`
  being `completed`. Resolve both anchors by symbol.
- Leave the `defect` arm's own call to that helper untouched.
- Correct the cooled cross-repo branch's comment, which currently says receipt
  projection is "deferred to Wave 7 by
  `wave6-dependency-scoped-completion-receipts`", to record the decision AC27
  states and point at `cooling-cross-repo-receipt-refusal`.

**Done when:** AC19-AC27 pass and every pre-existing dependency test in
`packs/core/tests/skills/workspace-status/test_workspace_status_engine_autonomous.py`
still passes.

### T6: Only `status` and `reconcile` carry the receipts block

**Depends on:** T3

**Verification mode:** TDD. **Preservation** — AC41 is green before the change
and its killing mutation is emitting the block ungated.

**Tests:**
- One predicate over both `repair-plan` and `explain`. Only the `repair-plan`
  member can break, because `explain` uses `_build_explain_json`, which this
  delivery does not touch.

**Approach:**
- Extend `_build_json`'s `mode in {"status", "reconcile"}` guard — the
  block-emission gate. Do **not** extend `_cooling_selection`, which admits
  `explain` as well and would break AC41.

**Done when:** AC2 and AC41 pass, Wave 6's AC35 test still passes, and the
ungated-emission mutation reddens AC41.

### T7: Shipped-ness and queue-emptiness are one derivation

**Depends on:** none

**Verification mode:** TDD.

**Tests:**
- AC28 is one assertion over both emitted values for the projected initiative,
  comparing the cooled and uncooled runs. Two separate assertions would both
  pass against the defect Wave 6 reverted.
- AC31's fixture makes the cooled reading incomplete by the mechanism Wave 6
  ships for it — an unreadable lifecycle record — not by patching the flag.
- AC34 carries the uncooled sibling, so an implementation that excludes every
  entry fails.
- **This task retires a shipped assertion.**
  `tests/roster/test_status_projection_and_context_exclusion.py::test_a_fully_cooled_initiative_still_reports_unshipped_specs`
  asserts `all_specs_shipped is False` and `"unshipped-specs" in
  closeout_blockers` for exactly AC29's fixture, as Wave 6's recorded known
  starting state. It is replaced in place by an assertion that the same fixture
  now reports `all_specs_shipped is True` and no `unshipped-specs` blocker, with
  a comment naming this spec.

```python
# STUB: AC28 — the two closeout consumers agree about the cooled set.
def test_ac28_closeout_consumers_agree_about_cooled_set(tmp_path):
    data = _status(tmp_path)
    assert data["closeout"]["all_specs_shipped"] is data["initiatives"][0]["queue_empty"]


# STUB: AC31 — an incomplete cooled reading withholds the affirmative.
def test_ac31_incomplete_cooled_reading_withholds_affirmative(tmp_path):
    closeout = _status(tmp_path)["closeout"]
    assert closeout["cooling_context_visible"] is True
    assert closeout["next_action"] != "invoke-close-work"
    assert "cooling-context-incomplete" in closeout["closeout_blockers"]
```

`stub: true`. Compiled clean; both red against the current tree.

**Approach:**
- Replace the two expressions in `workspace_status.py` with one shared
  cooled-exclusion derivation and read both emitted values from it. `closeout`
  covers the projected initiative only, so scope the comparison there.
- Add the `cooling_context_visible` guard to the affirmative next action and the
  named blocker.

**Done when:** AC28-AC34 pass, the retired roster assertion is replaced rather
than deleted, and `packs/core/tests/skills/close-work/` still passes including
Wave 5's AC24 workspace-key test.

### T8: The repair and migration paths are pinned as unaffected by cooling

**Depends on:** none

**Verification mode:** TDD. **Preservation** — AC35-AC40 are green before the
change; each carries a mutation in the table above.

**Tests:**
- Each of AC35-AC39 is a control-run identity: the same fixture with and without
  `docs/lifecycle/`, asserting equal output. An assertion on the presence or
  absence of a filter would pass against an implementation that added one and
  ignored it.
- AC40 parses `workspace_status.py` and counts the rootless call sites, so the
  count is read from the file rather than restated. Both sites are inside
  `_migration_rollback_workspace_bytes`, which AC35-AC39 do not otherwise reach.
- The migration criteria need a confirmation file. The fixture generates its own
  opaque identifiers inside the test; no confirmation file is authored by hand.

**Approach:**
- Add tests only. No production change belongs to this task; if one is needed,
  the decision the spec records is wrong and the spec changes first under
  RFC-0099 §7.

**Done when:** AC35-AC41 pass with no diff outside test files, and each mutation
named in the table above reddens its case.

### T9: The three documented surfaces carry the codes, the shape, and the posture

**Depends on:** T3, T7

**Verification mode:** TDD for the gate; goal-based for the prose.
`no stub (mode)` for AC42-AC48 — each is a string assertion over a file this
task authors.

**Tests:**
- The finding-code gate at `tests/roster/test_workspace_status_projection.py`
  turns green here; it is red from T3.
- AC43-AC48 use the whitespace-normalized comparison idiom, because every target
  sentence wraps in its source.

**Approach:**
- Add the two rows to `packs/core/.apm/skills/workspace-status/SKILL.md` and
  `guides/core/reference/workspace-toml-schema.md`.
- Add the `receipts` output section, the collection's shape, and the trust
  posture to both.
- Rewrite the skill's closeout-check paragraph against the shared derivation,
  removing the sentence that calls raw queue emptiness authoritative.
- Add the receipt-scope sentence and the 7a/7b/7c split to
  `docs/architecture/work-intake-and-artifact-routing.md` without touching the
  three pinned statements or introducing the negated string.

**Done when:** AC42-AC48 pass and
`tests/roster/test_wave4_durable_outputs_and_release.py` still passes.

### T10: The governance surfaces record the corrections without a frozen-body edit

**Depends on:** T9

**Verification mode:** goal-based check. `no stub (mode)` — AC49, AC53, AC55 and
AC56 are digest assertions over files this task must not change; AC50-AC52 and
AC54 are string assertions over content this task authors.

**Tests:**
- AC49, AC53, AC55, AC56 are literal pinned digests computed in the new roster
  suite, so each holds after the branch is gone. AC53 excludes every line
  beginning `- **Status:**` before hashing, because that line does change.

**Approach:**
- Append one dated, signed erratum to RFC-0096 § Errata carrying the slice
  split, the corrected receipt precondition, and the corrected
  `cooling-brief-child-scope` basis. Do not touch §9.
- Amend only the `**Status:**` line of Wave 6's `spec.md`, in the convention's
  non-supersession pointer form, naming all three closed slugs.

**Done when:** AC49-AC56 pass and
`python 'packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py' --root .`
exits 0.

### T11: The release surface agrees across all three files

**Depends on:** T2-T10

**Verification mode:** goal-based check. `no stub (mode)`.

**Tests:**
- AC57 reads all three values, asserts they are equal, and asserts the parsed
  tuple exceeds `(2, 18, 2)`.

**Approach:**
- Re-derive the number from `git show origin/main:packs/core/pack.toml`
  immediately before committing. This is a process step, not an assertion: a
  test that reads `origin/main` at assertion time depends on fetch state and
  re-baselines exactly as a merge-base comparison does.
- Bump `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`, add
  the topmost dated `[core]` changelog heading, and regenerate the four engine
  projections through the gate chain rather than by hand.

**Done when:** AC57 passes, `SKIP_SAST=1 make build-check` exits 0 on a clean
`build/` and `dist/`, and the four engine copies are byte-identical.

### T12: A maintainer invoking the CLI sees the projected receipt

**Depends on:** T11

**Verification mode:** visual / manual QA. `no stub (mode)`.

**Approach:**
- In a scratch fixture outside the repository tree, write a `workspace.toml`
  carrying one valid cited receipt whose target file is absent, one uncited
  receipt, and one malformed receipt.
- Invoke the real CLI's `status` and `reconcile` and record stdout, the exit
  code, and the emitted `receipts` and `canonical.findings` values in
  `notes/manual-qa.md`.
- Invoke `repair-plan` on the same fixture and record that no `receipts` key is
  emitted.

**Done when:** `notes/manual-qa.md` records the observed output of all three
invocations, including exit codes.

## Rollout

Pure-logic and documentation change with one additive persistent
representation. Single merge, no flag: a `workspace.toml` carrying no
`completion_receipts` key behaves exactly as it does today, and one carrying the
key is already valid to every shipped consumer (probe 1), so there is no
mixed-version window. Rollback is a revert; nothing is irreversible, because
this delivery adds no writer to `workspace-status` and deletes nothing.

## Risks

- **The gate in the wrong arm or above the safety return** converts refusals into
  satisfactions, including Wave 6's two fail-closed controls. T5 leads with five
  refusal cases.
- **A preservation criterion recorded as a red stub** would be a green guard
  proving nothing. The Construction tests section splits the two shapes and the
  mutation table carries the preservation half.
- **The engine has four copies** — the pack source, two projected skill trees,
  and the packaged `_data/` tree. A hand-edited copy passes local tests and
  fails the packaged-runtime pair check, so T11 regenerates through the gate
  chain.
- **`pytest` and `build-check` cannot run concurrently**: `pytest` writes
  `.apm/__pycache__` that `build-check` rejects. T11 cleans `build/` and `dist/`
  and runs the two in sequence.
- **A receipt is honoured on repository write access alone.** The spec records
  the posture and AC45 puts it on both documented surfaces; the residual is that
  a pull request adding a receipt block can unblock queued work whose artifact
  is absent, and only spec-level review catches it.

## Changelog

- 2026-09-01: initial plan.
- 2026-09-01: reworked from round-1 spec review (52 sustained findings across
  two adjudicated reports). Five changes of substance, not re-ordering.
  **(1)** Added T2: nothing in the repository names the receipt key, so the
  producer's spelling is new work this delivery owns; the reader was previously
  specified against a writer that does not exist. **(2)** Re-keyed the decision
  point from a phase to a finding code in the general arm only — probe 8 found
  two further refusals after the safety helper, and the previous placement would
  have let a receipt answer Wave 6's fail-closed brief control. **(3)** Added
  the `outcome == "completed"` test; `outcome` was inert, so an `abandoned`
  receipt would have unblocked work the engine refuses when the artifact is
  present. **(4)** Split construction tests into red-stub and preservation
  shapes after three of thirteen stubs passed on the unchanged tree; recording
  those as red would have been a green guard. **(5)** Replaced merge-base
  comparisons with literal digests, and named the shipped roster assertion T7
  retires.
