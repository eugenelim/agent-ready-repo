# Spec: Contract backward-traceability registry

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0008, RFC-0017
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

## Outcome

A maintainer whose spec names a contract that cannot carry an `x-spec`
extension has a place to record the back-reference, and the repository's own
lint tells them when that record is missing or points at the wrong spec.
Invariant (v) becomes a control that can fail on the registry channel, where it
previously could not.

## What Changes

- A backward-pointer map covering contract formats that carry no `x-spec`
  extension — `contracts/REGISTRY.md`, a table with one row per
  (contract, spec) pair.
- Invariant (v)'s registry check reads one row at a time instead of the whole
  file — `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`, and
  its `.claude/` and `.agents/` projections.
- A repository-level assertion that the real registry is present and current —
  a new module under `tests/roster/`, with its named CI step and parity entry.
- A row for the new file in the contracts inventory — `contracts/README.md`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable — the registry is a new published map with a row grammar the lint parses | `contracts/REGISTRY.md` | work-loop implementer | The file, plus a clean invariant (v) run over the repository | Every non-`x-spec` contract token named by a spec has a row |
| Current architecture | Applicable — `docs/architecture/work-intake-and-artifact-routing.md` is the one architecture page naming traceability | `docs/architecture/work-intake-and-artifact-routing.md` | work-loop implementer | The page states the registry channel, or a recorded finding that it does not describe this contract | Page agrees with the shipped behaviour, or is recorded as out of scope with the evidence |
| Maintainer procedure | Applicable — a maintainer adding a `.toml` or `.md` contract must know a row is owed | `contracts/README.md` | work-loop implementer | The Files-table row for `REGISTRY.md` | A reader of the contracts inventory learns the registry exists and what it pins |
| Decision rationale | Not applicable — ADR-0008 and RFC-0017 already decide the forward/backward pair; this delivers them | none | — | — | — |
| Release history | Not applicable — no touched file is release-impacting (`tools/repo/check_release_impact.py`), and no core version is bumped | none | — | — | — |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Regenerate the `.claude/` and `.agents/` projections in the same change as any
  edit to `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`.
- Derive the registry's rows from the lint's own `contract_header_refs` parser,
  never from a hand-written regex over the spec corpus.
- Keep invariant (v) warn-only; report the real pass/fail set rather than
  changing its severity.

### Ask first

- Raising invariant (v) from warn-only to a hard failure.
- Adding a row to the registry for a contract no spec's `Contract:` header names.
- Changing the registry's row grammar after the roster test pins it.

### Never do

- Edit the body of ADR-0008 or RFC-0017.
- Remove or weaken any existing `x-spec` field, or change the `x-spec` branch at
  `lint-spec-status.py:1247`.
- Add a new top-level directory, a new module boundary, or a new dependency.
- Place a repository-level assertion under `packs/core/tests/`, which may not
  read above its own pack.

## Testing Strategy

- **Row-scoped acceptance (AC-0002):** TDD. The defect is a compressible invariant —
  a pairing predicate over one row — so the red comes first, from a fixture whose
  token and spec directory appear in the file but never on the same row.
- **Registry completeness and repository cleanliness (AC-0001, AC-0003):** goal-based
  check, exercised by an integration test. Both are properties of the real
  repository read through the real lint, so the check runs the lint over the
  repository root and reads its findings.
- **Absent-registry detection (AC-0004) and stale-row detection (AC-0005):**
  TDD. Each is a distinct failure the roster module must produce on demand, and
  they are driven at different seams: AC-0005 mutates a copy of the registry
  text in memory, while AC-0004 passes the loader a path that does not exist,
  because a missing path is the one state text cannot express.
- **Inventory row (AC-0006):** goal-based check, because the outcome is a
  present-or-absent fact about a file the change writes, with no logic to
  compress into a test.
- **Projection parity (AC-0007):** goal-based check — `make build-self` in `--check`
  mode exits zero.

## Acceptance Criteria

- [ ] **AC-0001.** `contracts/REGISTRY.md` contains a row pairing the contract token with the
      spec directory for every (token, spec) pair where a `docs/specs/*/spec.md`
      `Contract:` header names a token not ending in `.yaml`, `.yml`, or `.json`.
      The pair set is derived by the lint's `contract_header_refs` parser and
      `_XSPEC_FORMATS`, which is what makes the coverage exhaustive; at the
      revision this spec is approved, that set has 10 pairs across 6 specs.
- [ ] **AC-0002.** Invariant (v) treats a registry back-reference as present
      only when a single row names the contract token exactly and names the
      naming spec's directory as a whole path, not as a prefix of a longer one.
      A registry whose every row fails that test for a token produces an
      invariant (v) finding for it, including when the token appears on a row
      naming a different spec directory, when a row's spec directory has the
      naming spec's directory as a proper prefix, and when a row's contract
      token has the named token as a proper prefix.
- [ ] **AC-0003.** `lint-spec-status.py --root . --all --verbose` over this
      repository reports zero invariant (v) backward findings for contract
      tokens that do not end in `.yaml`, `.yml`, or `.json`. At the revision
      this spec is approved, 10 such findings exist across 6 specs. Findings for
      `x-spec`-format tokens are outside this criterion and are recorded under
      Follow-ons.
- [ ] **AC-0004.** A `tests/roster/` module fails, rather than skipping or
      passing, when the registry path it is given does not exist.
- [ ] **AC-0005.** A `tests/roster/` module fails when a registry row names a spec directory
      that no longer names that contract token.
- [ ] **AC-0006.** The `contracts/README.md` Files table has a `REGISTRY.md` row recording
      `no` in the CLI data column.
- [ ] **AC-0007.** `python -m agentbundle catalogue self-host --root . --check` exits zero, so
      the `.claude/` and `.agents/` copies of `lint-spec-status.py` match the
      `packs/core/.apm/` source.

## Follow-ons

- eugenelim: no artifact yet — 35 (contract, spec) pairs across 22 specs fail
  invariant (v) through the inline `x-spec` channel, because the `x-spec` lists
  on the `.json` contracts are short or absent. `contracts/pack.schema.json`
  carries no `x-spec` key and is named by 7 specs. Out of scope here: several of
  those files are release-impacting, so filling them pulls in an `agentbundle`
  release. Measured 2026-09-22 over 36 specs; 45 backward findings in total, of
  which this spec closes 10.
- eugenelim: no artifact yet — the `x-spec` branch at `lint-spec-status.py:1247`
  carries the same whole-file substring laxity the registry branch had. Out of
  scope because tightening it needs its own measurement, which the gaps above
  would confound.
- eugenelim: no artifact yet — invariant (v)'s severity. It stays warn-only in
  this change; the real pass/fail set is reported at completion so the raise can
  be decided on evidence.

## Assumptions

- Process: whether `docs/architecture/work-intake-and-artifact-routing.md`
  actually states the spec↔contract traceability contract, or only mentions
  traceability in another sense — decides whether the architecture durable output
  is an edit or a recorded no-op (settled by: reading the page during EXECUTE).
