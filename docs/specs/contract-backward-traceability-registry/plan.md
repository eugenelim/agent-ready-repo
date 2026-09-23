# Plan: Contract backward-traceability registry

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - `docs/adr/0008-contract-authoring-seam.md` — D3 (repo-level contract tree)
    and the Consequences clause naming the forward/backward pair.
  - `docs/rfc/0017-pluggable-api-contract-standards.md:155` — the registry
    fallback, and the stated reason the lint exists: it "keeps `REGISTRY.md`
    from silently rotting".
  - `tests/AGENTS.md` — a repository-level assertion belongs in `tests/roster/`
    and obliges a named CI step plus a parity entry.
  - Analogous implementation: `packs/core/tests/skills/work-loop/`
    `test_lint_spec_status.py::test_v_extensionless_registry_and_dangling` —
    the shipped fixture that already drives the registry branch, and the
    construction pattern (`write_contract` / `write_spec_with_contract` /
    `run_lint`) the new pack-level cases reuse.
  - Analogous implementation: `tests/roster/test_index_records.py` — a roster
    module that derives an expected set from the live tree and compares.

## Approach

The registry branch of invariant (v) already runs; it just cannot tell a
correct back-reference from a coincidental one, because it tests the whole
file rather than a row. Row-scoping it turns the same branch into a control
that can fail, and the registry file then becomes an artifact a gate reads
rather than a document that rots unobserved.

## Constraints

- Invariant (v) stays warn-only. Nothing in this change may make
  `lint-spec-status.py` exit non-zero on a finding it did not already fail on.
- The `x-spec` branch (`lint-spec-status.py:1247`) is untouched.
- `packs/core/.apm/` and its `.claude/` and `.agents/` projections ship
  together; `catalogue self-host --check` is the gate that sees a mismatch.
- A pack test may not read above its own pack, so the repository-level
  assertion cannot live beside the pack-level ones.

## Construction tests

| Criterion | Where the check lives | What drives it |
| --- | --- | --- |
| AC-0001, AC-0003 | `tests/roster/test_contract_backward_registry.py` | The live repository tree, read through the lint's own parser |
| AC-0002 | `packs/core/tests/skills/work-loop/test_lint_spec_status.py` | A fixture tree whose token and spec directory never share a row |
| AC-0005 | `tests/roster/test_contract_backward_registry.py` | A mutated copy of the real registry text, in-memory |
| AC-0004 | `tests/roster/test_contract_backward_registry.py` | The loader, given a path under `tmp_path` that does not exist |
| AC-0006 | `tests/roster/test_contract_backward_registry.py` | The `contracts/README.md` Files table |
| AC-0007 | `make build-self` in `--check` mode | The gate chain |

## Durable-output map

| Durable output | Task | Evidence at closeout |
| --- | --- | --- |
| `contracts/REGISTRY.md` | T2 | Zero invariant (v) findings over the repository |
| `contracts/README.md` Files row | T2 | AC-0006 assertion green |
| `docs/architecture/work-intake-and-artifact-routing.md` | T2 | Edited, or a recorded finding that the page does not state this contract |

## Design (LLD)

### Design decisions

Owned by: T1, T2, T3

- **Row scope with exact halves, not a parsed table.** The check tests each
  line, but neither half by bare containment: the contract token must appear in
  that row's `_CONTRACT_TOKEN_RE` matches exactly, and the spec directory must
  appear with a trailing `/`. Bare containment reproduces the same false pass
  one level down — `docs/specs/foo` sits inside `docs/specs/foo-bar/`, and this
  repository has 12 such spec-directory prefix pairs — so row scope alone would
  move the defect rather than close it. A Markdown-table parser would instead
  pin the registry to one layout and break the shipped bullet-style fixture.
  Verified by spike across four cases: a spec-directory prefix collision warns,
  a contract-token prefix collision warns, a correct table row passes, and
  `test_v_extensionless_registry_and_dangling` stays green.
- **The pair set is derived, never transcribed.** Both the registry's content
  and the roster test's expectation come from `contract_header_refs` plus
  `_XSPEC_FORMATS`, loaded from the lint module itself. Six hand-written
  regexes produced six different answers for this set before the parser settled
  it, so a transcribed list is a known defect source here.
- **AC-0005 falls out of one equality assertion; AC-0004 does not.** The roster
  test compares the registry's pair set to the derived pair set, so a stale row
  yields a mismatched pair with no separate rule. An absent file is a different
  seam: the comparison never runs, and a loader that returns early on a missing
  path satisfies every text-level case while leaving AC-0004 undischarged.
  AC-0004 is therefore driven at the loader, with a path that does not exist,
  asserting a failure rather than a skip.

### Data & schema

Owned by: T2

The registry is a Markdown table under a `## Pairs` heading, one row per pair:

| Contract | Spec |
| --- | --- |
| `contracts/adapter.toml` | `docs/specs/claude-plugin-hook-parity/` |

The grammar the check depends on is narrow, and exactly two things in it are
load-bearing: the contract token appears on the row verbatim, and the spec
directory appears on that same row with its trailing `/`. Backticks, the table
pipes, and the column order are readability, not contract.

### Interfaces & contracts

Owned by: T1

`lint-spec-status.py` gains no new function and no new flag. The change is the
expression assigned to `backward` on the registry branch.

### Failure, edge cases & resilience

Owned by: T2, T3

- A registry naming a contract no spec references is not a finding — invariant
  (v) walks spec headers, not registry rows. The roster test's equality
  comparison is what catches it.
- A spec directory that is a prefix of another (`docs/specs/foo` inside
  `docs/specs/foo-bar/`) would let a substring test pass the wrong pair, and 12
  such pairs exist in this repository. Both readers are hardened, because
  hardening one leaves the other wrong: the lint requires the trailing `/`, and
  the roster test compares parsed pairs. `feature_dir` as the lint computes it
  carries no trailing delimiter, which is what made bare containment unsafe.

## Tasks

### T1: A registry back-reference counts only when one row carries both halves

**Depends on:** none

**Touches:** packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py, packs/core/tests/skills/work-loop/test_lint_spec_status.py, .claude/skills/work-loop/scripts/lint-spec-status.py, .agents/skills/work-loop/scripts/lint-spec-status.py

**Tests:** (AC-0002, AC-0007)
- A fixture tree where the registry pairs `contracts/b.toml` with
  `docs/specs/gamma/` and mentions `docs/specs/beta/` only on another line
  produces an invariant (v) finding for `docs/specs/beta/spec.md`. This is the
  red: the shipped whole-file check reports clean here.
- A registry whose only row names `docs/specs/foo-bar/` produces a finding for
  the spec at `docs/specs/foo/` naming that same contract. Without this case a
  bare per-row containment test passes and AC-0002's prefix clause cannot fail.
- A registry whose only row names `contracts/a.toml.bak` produces a finding for
  a spec naming `contracts/a.toml`. This is the token half of the same class,
  and it fails for a different reason, so one case does not cover both.
- A correct row satisfies the check, pinning that the two cases above are not
  satisfied by a check that rejects everything.
- `test_v_extensionless_registry_and_dangling` and
  `test_contract_registry_symlink_outside_root_does_not_supply_backref` stay
  green, pinning that the change neither loosens confinement nor breaks the
  one-line bullet layout.
- Exit code is unchanged: the new finding is warn-only, so the run exits zero.
- `python -m agentbundle catalogue self-host --root . --check` exits zero, so
  the edited pack source and its two projections agree. (AC-0007)
- Every case above is proved red before it is proved green, by running it
  against `git show HEAD:packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`.
  A case that is green against both revisions is not testing this change.

**Approach:**
- Regenerate projections in this task rather than a later one. A pack source
  whose `.claude/` and `.agents/` copies lag fails `catalogue verify` while
  lint, pytest, and catalogue-lint all pass against the stale copy, so the
  mismatch surfaces far from its cause.

**Done when:** every bullet under this task's `Tests:` is green.

### T2: Every stranded contract has a registry row, and the repository lint is clean

**Depends on:** T1

**Touches:** contracts/REGISTRY.md, contracts/README.md, docs/architecture/work-intake-and-artifact-routing.md

**Tests:** (AC-0001, AC-0003, AC-0006)
- `lint-spec-status.py --root . --all --verbose` over the repository reports
  zero invariant (v) backward findings whose contract token does not end in
  `.yaml`, `.yml`, or `.json` — down from 10 at the approved revision. Run
  unfiltered and read the exit code and the finding lines, not a `grep` of them.
  The `x-spec`-channel findings are expected to remain and are counted, so a
  change in their number is visible rather than absorbed.
- The registry's pair set equals the set derived from `contract_header_refs`
  over `docs/specs/*/spec.md`. Set equality, not containment: a superset would
  satisfy AC-0001 while carrying a row for a contract no spec names.
- In `contracts/README.md`, the Files table has a `REGISTRY.md` row whose
  `CLI data` cell reads `no`. The oracle is the parsed table cell, not the
  file's text, so a mention of `REGISTRY.md` in the prose above the table does
  not satisfy it. (AC-0006)

**Approach:**
- Read `docs/architecture/work-intake-and-artifact-routing.md` whole before
  deciding whether it needs an edit; the Assumptions entry in `spec.md` records
  that this is unsettled, and either outcome is recorded rather than assumed.

**Done when:** every bullet under this task's `Tests:` is green.

### T3: The roster module fails on an absent or stale registry

**Depends on:** T2

**Touches:** tests/roster/test_contract_backward_registry.py

**Tests:** (AC-0004, AC-0005)
- Given a registry path that does not exist, the module fails rather than
  skipping or passing. (AC-0004) This drives the loader, not the comparison:
  the comparison never runs on a missing path, so no text-level case reaches
  this branch.
- Given the real registry text with one row's spec directory rewritten to a
  spec that does not name that contract, the comparison fails. (AC-0005)
- Given the real registry text with every row removed, the comparison fails.
  This is a distinct case from the absent path and does not substitute for it.
- Given the real tree unmodified, the comparison passes.
- The failure cases drive the same loader and comparison the live assertion
  uses, so a mutation that would let the live case pass silently fails them
  too.

**Approach:**
- Mutate registry *text* in memory, never the repository file. A test that
  rewrites `contracts/REGISTRY.md` and restores it leaves the tree dirty when
  it fails, and `build-self` refuses a dirty tree.
- The absent-path case is the one that cannot be expressed as text, so it
  passes the loader a path under `tmp_path` instead. It does not reproduce the
  repository tree: only the loader is driven, because only the loader has the
  missing-path branch.

**Done when:** every bullet under this task's `Tests:` is green.

### T4: The roster module is named by CI and recorded in the parity table

**Depends on:** T3

**Touches:** .github/workflows/build-check.yml, tools/lint-ci-parity.py

**Tests:** (no new criterion — this discharges the `tests/AGENTS.md` obligation)
- `python tools/lint-ci-parity.py` exits zero with the new `STEP_DISPOSITION`
  entry present.
- The new `build-check.yml` step sits above the bulk `pytest tests/ -q` step, so
  a failure is attributed to the named module rather than reported twice.

**Done when:** every bullet under this task's `Tests:` is green.

## Rollout

- **Delivery:** big bang, one PR. Reversible by reverting it; nothing persists
  state and no consumer reads the registry but the lint.
- **Infrastructure:** none.
- **Deployment sequencing:** none beyond the task order.

## Risks

- The roster suite takes about 15 minutes and must not be run locally; T3 and
  T4 are verified on CI, and the module's pure comparison functions are
  exercised directly in-session so the logic is not first seen on CI.
- `catalogue self-host --check` refuses a dirty tree, so T1's projection step
  needs its source edit committed first.

## Changelog

- 2026-09-22 — Drafted.
- 2026-09-23 — Spec approved (scope) by eugenelim.
- 2026-09-23 — Plan approved (build strategy) by eugenelim.
