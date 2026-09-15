# Plan: Selection-scoped membership absence

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` (`_extract_canonical_memberships`, `_legacy_canonical_alias`, and `run_canonical_reconciliation`); `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py` (additive subcommand routing and JSON emission); analogous construction path `tests/roster/test_workspace_status_projection.py`; governing constraints `packs/AGENTS.md`, ADR-0114, and RFC-0096 2026-09-13 Errata. Named uncertainty: the exact additive CLI subcommand and flag spelling is not established by a prior contract and must be settled during plan approval without changing the spec's selection or result semantics.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/selection-scoped-membership-absence/notes/verification-ledger.md`.
> A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material: an implementer corrects them in place as the
> work teaches, without an amendment and without a review round. `Grounding`
> stays recorded because a per-task resolution that nobody wrote is not
> grounding; what it stops being is a claim a reviewer holds the plan to.

## Approach

Add one selection-scoped query to the existing `workspace-status` engine, then
expose it through the existing CLI as an additive read-only command. The engine
reuses the canonical membership extractor and legacy alias resolver, indexes
all resolvable and selected-target parse-blocked occurrences by canonical spec
artifact path, and projects one deterministic result per supplied spec
directory. Build the contract first in a new `tests/roster/` module, wire the
CLI second, then update the pack documentation, eval harness, release coupling,
and generated self-host projection. No task mutates `workspace.toml` or composes
the later prune protocol.

## Constraints

- [ADR-0114](../../adr/0114-prune-success-requires-a-two-sided-post-mutation-invariant.md) requires canonical membership identity resolution across duplicate and legacy-alias cases, while assigning mutation closure, participating mutators, baselines, and ABA handling to the later prune slice.
- [RFC-0096](../../rfc/0096-portable-delivery-artifact-lifecycle.md) 2026-09-13 Errata requires a mechanical re-check of entry-less status before any carved-out spec is deleted and keeps reference-free verification as a separate condition.
- `packs/AGENTS.md` makes `.apm/` the source, requires self-host projection after edits, forbids internal governance citations in shipped pack content, requires an eval-harness update, and requires matching patch version bumps for non-cosmetic pack changes.
- `packs/core/AGENTS.md` reserves `tomlkit == 0.15.1` for `repair-apply`; this read-only capability remains standard-library-only.
- `Makefile` lines 636–650 establish why this slice's tests live in `tests/roster/`: `test-unleased` injects the two `tools/test_workspace_status*.py` modules, but `test-after-build-check-unleased` leaves that macro slot empty, while `pytest tests/` is collected on both routes.
- Any `.apm/` script output is UTF-8 configured before its first print.
- Pack tests load the engine under a unique module name containing both pack and skill, such as `core_workspace_status_selection_membership`; they do not add a skill `scripts/` directory to `sys.path` or import the engine by a bare name.
- No shipped file under `packs/` cites this spec, ADR-0114, RFC-0096, an acceptance-criterion number, or a repository-only path; comments state portable rules directly.

## Construction tests

Most construction tests live under **Tasks** below (per-task `Tests:`
subsections).

**Integration tests:** The focused roster suite invokes the new projected CLI against a fixture with canonical, duplicate, legacy, absent, malformed, and unrelated memberships, then compares existing command output against frozen compatibility fixtures.

**Manual verification:** Run the read-only command against a disposable fixture, inspect one present and one absent result, and compare a before/after repository status and byte snapshot. Do not run a prune or edit this repository's `workspace.toml`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User and maintainer promise in `packs/core/.apm/skills/workspace-status/SKILL.md` | T3, T4 | Focused CLI tests, projected end-to-end invocation, and eval behavior case | `close-work` verifies the installed invocation, fields, and read-only scope against the source documentation. |
| Core release history in `docs/product/changelog.md` | T4 | Matching core/plugin version assertions and changelog construction test | `close-work` verifies the core-led release entry and `Highlights` disposition name the shipped capability and version. |

## Design (LLD)

### Data & schema

The comparison identity is the canonical repository-relative artifact path
`docs/specs/<slug>/spec.md`; nested spec selectors are invalid. A result contains the supplied spec directory, its
canonical artifact path, a membership-presence boolean, and an ordered list of
matching occurrences. Each occurrence carries repository-relative identity
provenance: initiative when present, collection, zero-based entry position,
and form. The JSON remains an internal skill interface, so no new file under
`contracts/` is introduced. Traces to: AC-0006–AC-0012, AC-0014–AC-0020, AC-0029, AC-0030.

### Interfaces & contracts

The engine owns a typed, side-effect-free selection function over parsed
workspace data and validated spec-directory selectors. The CLI adds one
explicit subcommand with a repeatable selector argument; plan approval settles
the spelling before tests pin it. Valid analysis exits successfully for
present, absent, and mixed results because the surface reports facts and does
not gate a prune. Existing subcommands and their compatibility alias do not
call the new route. Traces to: AC-0001–AC-0005, AC-0015–AC-0025, AC-0029.

### Failure, edge cases & resilience

Empty or unsafe selections are invalid. A selected artifact need not exist,
because Slice 2 must be able to ask about membership after artifact removal.
Malformed workspace structure fails closed. A target-like parse failure whose
safe canonical path equals a selected identity is retained as a blocked
occurrence rather than converted into absence; an unrelated parse failure does
not widen the selected domain. Duplicate matching entries are preserved rather
than deduplicated so later consumers cannot mistake partial removal for
absence. Traces to: AC-0001–AC-0004, AC-0010–AC-0012, AC-0017, AC-0021–AC-0025, AC-0029, AC-0030.

### Quality attributes (NFRs)

The query is offline, deterministic, repository-confined, UTF-8, and
read-only. Output carries no absolute root, traceback, or instruction-like raw
payload. A complete before/after byte snapshot is the no-write oracle. Traces
to: AC-0002, AC-0019–AC-0027, AC-0029.

## Tasks

### T1: The roster contract fails on every unsupported selection or identity result

**Depends on:** none

**Touches:** `tests/roster/test_selection_scoped_membership_absence.py`

**Tests:**
- Add named TDD cases for AC-0001–AC-0004, AC-0006–AC-0012, AC-0014–AC-0023, AC-0029, and AC-0030 using the fixtures named by those criteria, including a non-empty mixed-presence selection, canonical/canonical, canonical/legacy, and legacy/legacy duplicates, the positive sentinels required by negative and relational criteria, the rejected nested selector, and the live slug-shaped shaping form represented in a fixture.
- For AC-0001, invoke the selected-membership route with no selectors and prove its structured `empty_selection` response differs from the `unknown_subcommand` response. For AC-0002, send the valid absent-artifact selector from AC-0003 through that same route and prove it is accepted alongside the invalid-selector matrix.
- Load the engine with `importlib.util.spec_from_file_location` under the unique name `core_workspace_status_selection_membership`; do not alter `sys.path`.

**Approach:**
- Build a small fixture writer for canonical target objects, accepted legacy spec aliases, the legacy shaping shape, invalid target-like objects, rejected nested selectors, and absent artifacts.
- Start with one compilable red assertion against the implementation-discovered engine seam, then fill the edge-case matrix without importing CLI internals into engine tests.

**Done when:** The focused roster module collects and fails only because the selected-membership engine and CLI surfaces do not yet exist.

### T2: The engine returns complete selected membership facts without reading or writing artifacts

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`, `tests/roster/test_selection_scoped_membership_absence.py`

**Tests:**
- Make the T1 engine cases for AC-0001, AC-0002, AC-0003, AC-0004, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0014, AC-0016, AC-0017, AC-0018, AC-0021, AC-0022, AC-0023, AC-0029, and AC-0030 pass. Keep AC-0026's engine-level proof narrow: call the pure selection seam and compare the fixture tree's byte snapshot before and after.
- Add a source-level assertion that the implementation reuses canonical extraction and alias resolution rather than creating a parallel TOML parser.

**Approach:**
- Validate and canonicalize the explicit non-empty selection through existing confinement primitives without requiring the selected artifact to exist.
- Reuse `_extract_canonical_memberships` and `_legacy_canonical_alias`; index canonical, accepted legacy, and safe selected-target parse-blocked occurrences by canonical artifact identity while retaining duplicates and provenance.
- Return one ordered typed result per supplied selector and leave aggregate prune judgment to the future consumer.

**Done when:** The focused engine cases and their byte-snapshot assertions are green.

### T3: The projected CLI exposes the read-only selection without changing existing commands

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`, `packs/core/.apm/skills/workspace-status/SKILL.md`, `tests/roster/test_selection_scoped_membership_absence.py`

**Tests:**
- Add CLI subprocess cases for AC-0001, AC-0002, AC-0005, AC-0015, AC-0019, AC-0020, AC-0024, AC-0025, AC-0026, and AC-0027, plus an end-to-end projected invocation using the mixed-presence fixture.
- Pin the two capability controls at CLI level: the recognized selected-membership route's structured `empty_selection` response must differ from the `unknown_subcommand` response, and the valid absent-artifact selector from AC-0003 must be accepted through the same invocation path used by the invalid-selector cases.
- For AC-0026, snapshot the entire fixture tree around five CLI runs: valid-present, valid-absent, mixed, invalid-selector, and invalid-workspace. Every before/after snapshot must be byte-identical.
- Compare frozen `status`, `reconcile`, and `explain` output before and after routing the additive command; assert valid presence does not change the valid-input exit code.

**Approach:**
- Settle the subcommand and repeatable selector flag spelling at plan approval, then add it to the existing dispatch and serializer without changing compatibility-alias routing.
- Document the explicit non-empty selection, per-spec result, supported identity forms, safe errors, and read-only/no-gating boundary in portable language.
- Keep UTF-8 stream configuration ahead of every print and avoid internal repository citations in pack content.

**Done when:** The focused CLI suite and projected mixed-presence invocation are green while frozen existing-command outputs remain identical.

### T4: The core pack projection, evals, version pair, and release record agree

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/workspace-status/evals/eval_queries.json`, `packs/core/.apm/skills/workspace-status/evals/evals.json`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`, generated self-host projections

**Tests:**
- Extend `test_eval_harness_covers_selected_membership_check` for AC-0028 and add construction assertions for identical `2.25.19` core/plugin versions plus a core-led changelog entry with its `Highlights` disposition.
- Run self-host in write mode, then verify the generated workspace-status projections match the `.apm/` sources byte for byte.

**Approach:**
- Add one triggering query and one behavior case covering a non-empty mixed-presence selection.
- Bump both core version files from `2.25.18` to the free patch `2.25.19`.
- Lead the matching `docs/product/changelog.md` entry with the core pack and include outcome-led highlights because consumers gain a new capability.
- Treat all generated projection changes as build output; never hand-edit them.

**Done when:** Eval, version-pair, changelog, and projection checks all pass with no source/projection drift.

### T5: Focused and repository gates prove the slice without running a prune

**Depends on:** T1-T4

**Tests:**
- Required local gate: `python3 .agents/skills/new-spec/scripts/lint-contract-item-alignment.py docs/specs/selection-scoped-membership-absence` exits 0 with every active criterion named by one Testing Strategy bullet and at least one task, and every retired identifier excluded from active references.
- Required local gate: `python3 .agents/skills/work-loop/scripts/lint-spec-status.py --root .` exits 0 with no hard spec-status or reference violation.
- Required local gate: `python3 -m pytest tests/roster/test_selection_scoped_membership_absence.py -q` exits 0 with every focused roster case passing, including the pack eval-contract assertions.
- Required local gate: `make build-self` exits 0 and regenerates the self-hosted artifacts from the `.apm/` sources; `make bootstrap-sites` then exits 0 with the source and generated workspace-status projections byte-identical.
- Required local gate: `make build-check` exits 0 with every local build, catalogue, lint, and policy leg invoked successfully, and `make test` exits 0 with the repository test suite green.
- Optional remote evidence: `build-check.yml`, `test-corpus.yml`, `test-roster.yml`, and `pages.yml` may be dispatched when available. An unavailable, undispatched, or unauthenticated workflow is recorded as optional evidence and does not block completion.
- Exercise the documented projected command against the mixed-presence fixture and record exit code, JSON fields, and before/after byte equality in the verification ledger.

**Approach:**
- Run the narrowest checks first, then self-host/build verification, then the full repository gates owned by the outer work-loop.
- Inspect the final diff for only the accepted source, generated projection, tests, evals, version pair, changelog, and verification evidence; reject any prune, closure, reference scan, or `workspace.toml` change.

**Done when:** Every required local gate above is green and the outer work-loop has recorded the end-to-end read-only evidence; optional remote workflow state does not affect completion.

## Rollout

This is an additive core-pack capability with no flag, infrastructure,
external-system dependency, data migration, or deployment sequencing. It ships
with the next core pack patch and is removed by reverting the source, test,
eval, version, changelog, and generated projection changes. It performs no
irreversible operation.

## Risks

- Reusing only canonical entries could silently report absence while a legacy alias survives; the duplicate and legacy fixtures make that failure red.
- Treating a parse-blocked selected-target entry as unrelated could produce a false absence; the selected parse-blocked fixture requires a conservative occurrence.
- Requiring the artifact to exist would make the capability unusable after Slice 2 removes it; the absent-artifact fixture separates membership identity from artifact state.
- Sharing the global Type 1 scan would widen default behavior and skip Shipped or Archived specs; compatibility fixtures pin both the selection boundary and unchanged defaults.
- Putting tests under `tools/` would miss the post-build CI route; the plan pins the suite under `tests/roster/`.

## Changelog

- 2026-09-13: Initial Drafting plan for Wave 7c Slice 1, separating selection-scoped membership identity and absence reporting from Slice 2 mutation and closure.
