# Plan: workspace-status repo backlog rendering

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Close the contract at its first divergent boundary. The engine parses
`[backlog].open` once into a dedicated ordered display model while retaining
the existing typed-only shaping extraction. The shared CLI serializer adds
`repo_backlog.open`, so both `status` and `reconcile` expose the same data.
The skill renderer consumes that field instead of rediscovering entry
membership from raw TOML; raw text remains relevant only for legacy comment
summaries. Contract tests go red before production changes, then pack eval,
release metadata, projection, gates, and real invocation close the loop.

## Constraints

- Preserve CLI `schema_version: 1` and every existing key.
- Keep `extract_top_level_backlog` and `shaping.top_level_backlog` typed-only.
- Preserve the existing dependency resolver, classifiers, reconciliation, and
  repair-plan paths byte-for-byte unless a failing regression test proves a
  necessary coupling.
- Edit runtime skill sources only under `packs/core/.apm/**`; the required
  repository tests, fixtures, core metadata, changelog, spec artifacts, and
  generated projections remain in scope. Regenerate projections with
  `make build-self` after all pack edits.
- Core pack behavior changes require a patch bump in `pack.toml` and
  `.claude-plugin/plugin.json`, plus a changelog entry.
- No dependency or workspace data migration.

## Construction tests

- Integration: run the production CLI in `status` and `reconcile` modes against
  the same mixed fixture and compare `repo_backlog.open` exactly.
- Manual verification: invoke the projected backend against the mixed fixture
  and this worktree, then record representative JSON and rendered rows.

## Design (LLD)

### Design decisions

- Add a separate `RepoBacklogEntry` display model rather than broadening
  `ShapingEntry`; this prevents display-only build items from entering the
  shaping guard. Traces to AC1–AC6.
- Serialize the collection as `repo_backlog.open`, mirroring the source
  lifecycle table while making repository scope explicit. Traces to AC1.
- Use `room` for the build/shape renderer label and retain declared shaping
  subtype separately as `entry_type`. Traces to AC2 and AC7.
- Preserve legacy and target `needs` values in their contracted JSON forms but
  do not compute `blocking_needs`; the repository backlog is visible and
  non-dispatchable. Traces to AC2, AC3, and AC6.

### Interfaces & contracts

The additive schema-version-1 surface is:

```json
{
  "repo_backlog": {
    "open": [
      {
        "slug": "example-build",
        "room": "build",
        "needs": [],
        "source": "spec/example",
        "summary": "Implement the example"
      },
      {
        "slug": "example-shape",
        "room": "shape",
        "entry_type": "research",
        "needs": ["backlog:example-build"],
        "source": "review/example",
        "summary": "Research the example"
      }
    ]
  }
}
```

For legacy records, `slug`, `room`, and normalized-list `needs` are always
present. `entry_type`, `source`, and `summary` are emitted only when their
source inline table declares the corresponding `type`, `source`, or `summary`
field. `source` accepts the existing string form and structured TOML table
form, represented as the equivalent JSON string or object.

A target five-field record retains its existing contract and adds only the
display discriminator:

```json
{
  "path": "docs/product/intents/example.md",
  "kind": "intent",
  "source": {"mode": "repo-origin"},
  "summary": "Frame the example",
  "needs": [],
  "room": "shape"
}
```

Target records omit `slug` and `entry_type`; the renderer displays `path`.
Kinds `intent`, `research`, `design`, and `brief` map to the display-only shape
room; `spec` and `defect` map to build. Bare-string repository backlog entries
remain unsupported.

### State & control flow

1. `parse_workspace` returns the TOML mapping.
2. `extract_repo_backlog` walks `[backlog].open` once in source order and
   constructs display entries.
3. `analyze` and `analyze_bounded` attach the list to
   `WorkspaceStatusResult` without passing it into classification.
4. `_build_json` serializes the list under `repo_backlog.open`.
5. The skill renders the section when that array is nonempty.

### Failure, edge cases & resilience

- Missing or empty backlog collections yield an empty array.
- Inline objects without optional metadata remain visible with only the three
  required output keys.
- Target five-field objects remain lossless and use `path` as their display
  identifier.
- Missing optional metadata is omitted rather than fabricated.
- The existing TOML parse-error behavior remains unchanged.

## Tasks

### T1: Production CLI contract tests fail on the missing repository backlog projection

**Depends on:** none

**Touches:** `packs/core/tests/skills/workspace-status/fixtures/repo-backlog/**`, `tools/test_workspace_status_cli.py`

**Verification mode:** TDD

**Tests:**
- `stub: true`
- Add a small static fixture with an untyped build entry followed by a typed
  shaping entry, including explicit `needs`, `source`, and `summary` values.
- Assert `status` and `reconcile` expose identical, ordered
  `repo_backlog.open` data and keep `shaping.top_level_backlog` typed-only
  (AC1–AC5, AC9).
- Add absent/empty-backlog cases that require `repo_backlog.open == []` (AC4,
  AC9).
- Add a focused target five-field entry case that preserves `path`, `kind`,
  structured `source`, `summary`, and structured `needs`, adds the kind-derived
  room, and emits neither `slug` nor `entry_type`. Cover one upstream kind and
  one implementation kind to pin the kind→room mapping (AC3, AC9).
- Snapshot `work`, `shaping.ready/blocked/signals`, and reconciliation outputs
  around the fixture to prove the display field does not affect classifications
  (AC6).
- Materialize these red contract stubs before production code:

  ```python
  def test_status_exposes_ordered_repo_backlog() -> None:
      raise NotImplementedError  # STUB: AC1, AC2, AC3, AC5, AC6, AC9


  def test_reconcile_exposes_ordered_repo_backlog() -> None:
      raise NotImplementedError  # STUB: AC1, AC2, AC3, AC5, AC6, AC9


  def test_status_repo_backlog_empty() -> None:
      raise NotImplementedError  # STUB: AC4, AC9


  def test_reconcile_repo_backlog_absent() -> None:
      raise NotImplementedError  # STUB: AC4, AC9


  def test_status_preserves_target_repo_backlog_entries() -> None:
      raise NotImplementedError  # STUB: AC1, AC3, AC9
  ```

**Approach:**
- Add the fixture and contract assertions without changing production code.
- Run only the new tests and confirm failure because `repo_backlog` is absent.

**Done when:** the new tests compile and fail for the missing
`repo_backlog` contract, not fixture setup or import errors.

### T2: Both analysis modes expose the ordered display-only repository backlog

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`, `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`, `tools/test_workspace_status.py`

**Verification mode:** TDD

**Tests:**
- `stub: true`
- Turn T1 green in both modes (AC1–AC6, AC9).
- Add focused engine coverage for source order, inline objects without optional
  metadata, typed room/subtype mapping, optional field preservation, and empty
  input where the CLI contract test does not isolate failures cleanly.
- Run the existing shaping-guard and dependency/classification cases unchanged
  (AC5–AC6).
- Materialize this focused red engine stub:

  ```python
  def test_extract_repo_backlog_preserves_declared_display_data() -> None:
      raise NotImplementedError  # STUB: AC1, AC2, AC3, AC4
  ```

**Approach:**
- Add the display-only dataclass and extractor.
- Attach its result to both `WorkspaceStatusResult` construction paths.
- Add an optional-field serializer and the top-level `repo_backlog.open`
  object in `_build_json`.

**Done when:** the red tests pass and existing engine/CLI tests remain green.

### T3: The shipped renderer, eval, release metadata, and projections use the new contract

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/workspace-status/SKILL.md`, `packs/core/.apm/skills/workspace-status/evals/**`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`, generated self-host projections

**Verification mode:** goal-based check + visual / manual QA

**Tests:**
- Eval fixture and assertions require a nonempty `Backlog — 2 open items`
  section with one `[build]` and one `[shape]` row in source order (AC7–AC10).
- An empty-backlog eval excludes the `Backlog —` section, and a structural
  contract test pins the count expression to `len(repo_backlog.open)` so a
  literal fixture count cannot satisfy the renderer contract (AC7–AC10).
- A target-entry eval or recorded manual fixture asserts that the rendered row
  uses the kind-derived room and `path` identifier rather than a missing
  `slug` (AC3, AC7, AC9).
- Structural assertions require `SKILL.md` to name `repo_backlog.open` as the
  authoritative collection and retain comment fallback only for missing
  summaries (AC7–AC8).
- Pack metadata versions match, changelog describes the fix, and self-host
  verification reports no projection drift (AC11).
- Invoke the real backend and record representative corrected output (AC7,
  AC9).

**Approach:**
- Rewrite only the backlog rendering paragraph and update the behavior eval.
- Bump core from 2.5.3 to 2.5.4 and add its changelog entry.
- Run `make build-self` after all `.apm` edits, then canonical gates.

**Done when:** eval/static checks, projection verification, canonical gates,
and the recorded real invocation all satisfy AC7–AC11.

### T4: Verification and independent review close the published-contract change

**Depends on:** T3

**Touches:** `docs/specs/workspace-status-repo-backlog-rendering/**`

**Verification mode:** goal-based check

**Tests:**
- Record targeted test and canonical lint, typecheck, test, projection, and
  manual-invocation results (AC12).
- Record adversarial-reviewer and quality-engineer reports at Clean, with an
  explicit security-review non-trigger unless the actual diff crosses a
  security boundary (AC12).

**Approach:**
- Run gates in repository order, fix failures, and rerun from the first affected
  gate.
- Iterate adversarial review to Clean, then run the full-mode quality floor.
- Reassess the security trigger against the final diff and record the result.

**Done when:** all required gates and reviewers are clean, every finding has an
apply/defer disposition, and the security-review decision is recorded.

## Rollout

This is an additive patch release. Existing JSON keys remain intact, including
the typed-only shaping guard field. Rollback restores the prior scripts and
renderer instructions; no persistent data or migration is involved.

## Risks

- Reusing `ShapingEntry` would silently broaden guard inputs; the separate
  display model prevents that coupling.
- Treating copied `needs` as evaluated readiness would make display affect
  dispatch; contract tests pin classification outputs unchanged.
- Fixed-shape serializers could invent absent metadata as null; optional
  fields are emitted only when declared.
- Renderer tests can pass while the backend omits build entries if fixtures
  contain only typed shaping data; the mixed contract fixture closes that gap.

## Changelog

- 2026-08-10: initial plan; contract confirmed as `repo_backlog.open` with
  display-only room discrimination.
- 2026-08-10: applied spec-plan review findings by making the entry contract
  normative, removing bare-string widening, adding red stubs and dynamic/empty
  renderer coverage, clarifying scope, and separating review closeout.
- 2026-08-10: applied re-review findings by defining the target five-field
  projection and display identifier, and making every TDD stub unconditional
  with an explicit `stub: true` marker.
- 2026-08-10: applied target-format review findings by defining the
  kind-to-display-room mapping and adding target-path renderer verification.
