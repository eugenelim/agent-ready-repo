# Plan: Cooling untrusted timezone bound

- **Spec:** [spec.md](spec.md)
- **Status:** Drafting
- **Repository anchors:** `docs/rfc/0096-portable-delivery-artifact-lifecycle.md`
  §6 owns cooling policy; `packs/core/.apm/skills/close-work/scripts/cooling.py`
  is the module under change and its own `_exceeds_depth` docstring (`:179-198`)
  is the analogous precedent — the same escape class (`RecursionError` outside
  the refusal tuple, surfacing an absolute path) was found and closed in Wave 5;
  `tests/roster/test_thirty_day_cooling_and_retirement.py` is the owning suite
  and holds the analogous bound-straddling guard at
  `test_the_depth_bound_discriminates_at_its_limit`;
  `contracts/jsonschema/delivery-lifecycle-record.schema.json` is the published
  contract, read but not written. Named deviation: none — this repairs an
  existing seam and introduces no new boundary.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document may change while Drafting. After approval, Phase 1 treats substantive
> plan changes as a re-plan requiring a new review and approval.

## Approach

Three dependency-ordered tasks. T1 closes the escape in `cooling.py` and proves
both halves of it. T2 makes the schema-versus-code bound divergence mechanical
so it cannot recur silently. T3 lands the release and registration surfaces.

The whole change to production code is one new module-private function, two new
module constants, and four call-site edits. Nothing new is introduced: the razor
run is recorded under [Declined](#declined).

## Constraints

- `docs/specs/thirty-day-cooling-and-retirement/spec.md` is Shipped and frozen.
  It receives a Status-line pointer at most; its ACs are not edited.
- `surface_resolver.py` and `file_safety.py` stay byte-unchanged. Their pinned
  digests in `tests/roster/test_close_work_extraction_and_immediate_disposition.py`
  (`:214`, `:216`) must pass with that file unedited.
- `contracts/jsonschema/delivery-lifecycle-record.schema.json` stays
  byte-unchanged (AC12) — see [`notes/schema-decision.md`](notes/schema-decision.md).
- No new dependency, module, store, resolver, fingerprint helper, scheduler, or
  deletion path.
- `cooling.py` must still contain no clock call (Wave 5 AC6) and no removal call
  beyond its single temp-file cleanup (Wave 5 AC36). Both are AST-asserted by
  the existing suite and must keep passing.

## Construction tests

All in `tests/roster/test_thirty_day_cooling_and_retirement.py`.

| AC | Test | Mode |
| --- | --- | --- |
| AC1, AC2, AC11 | `test_an_over_long_timezone_refuses_through_both_seams` | TDD |
| AC3, AC4 | `test_the_temporal_helpers_name_the_timezone_refusal` | TDD |
| AC5 | `test_the_timezone_bound_is_checked_before_the_lookup` | TDD |
| AC6 | `test_an_oserror_from_the_zone_lookup_cannot_escape` | TDD |
| AC7 | `test_a_timezone_refusal_carries_only_a_published_code` | TDD |
| AC8, AC9 | `test_the_code_bounds_equal_the_published_bounds` | TDD |
| AC10 | `test_the_locator_bound_discriminates_at_its_limit` | TDD |
| AC12 | `test_the_published_contract_is_unchanged` | TDD |
| AC13 | `test_the_release_surfaces_agree_on_one_core_version` | TDD |
| AC14 | existing `tests/roster/test_close_work_extraction_and_immediate_disposition.py:214,216` | goal-based — passes unedited |
| AC15 | `Done when:` `git diff --stat origin/main -- pyproject.toml 'packages/*/pyproject.toml' tools/requirements.txt` is empty | goal-based |

## Design (LLD)

### Design decisions

**One resolver, three call sites.** `validate_payload` (`:279-282`),
`compute_review_on` (`:326-329`), and `is_due` (`:337-340`) each do the same two
things — bound-check nothing, then resolve — and each needs its own refusal
code. Duplicating a length guard three times is more code than one private
helper that returns `ZoneInfo | None` and lets each site name its own code. The
helper is a function in the existing module, not a new module: the razor's
"one obvious line" rung, not a new boundary.

**The bound runs before the lookup, not after.** `ZoneInfo` builds a filesystem
path from the key and stats it, so an over-long key produces the `OSError` this
spec exists to stop. A bound applied after the call would be dead code. AC5
pins the ordering by counting calls rather than by inspecting source.

**Both halves ship.** The bound alone leaves other `OSError` shapes uncaught;
the `except` arm alone leaves an unbounded key reaching a syscall on every
validate and leaves the contract's published `maxLength` unenforced. AC5 proves
the bound independently of the arm and AC6 proves the arm independently of the
bound, so neither can make the other vacuous.

**`_zone` type-checks its input.** `validate_payload` previously coerced with
`str(payload["timezone"])`, so a non-string `timezone` was stringified before
lookup. The contract declares `"type": "string"`. `_zone` returns `None` for a
non-string, which is the same observable (`record-invalid`) by a correct route.

### Data & schema

No persisted shape changes. `MAX_TIMEZONE_LENGTH = 255` and
`MAX_LOCATOR_LENGTH = 1000` mirror the contract's declared bounds; AC8 and AC9
compare them to the contract file at test time so the mirror cannot drift.

### Interfaces & contracts

No public function signature changes. `validate_payload`, `parse_record_bytes`,
`compute_review_on`, and `is_due` keep their return types and their refusal
codes. No code is added to or removed from `REFUSAL_CODES`.

### Failure, edge cases & resilience

| Input | Before | After |
| --- | --- | --- |
| `timezone` of 256 chars | `OSError(63)` escapes with absolute `filename` | `record-invalid` / `unknown-timezone` |
| `timezone` of 255 chars, not a zone | `record-invalid` | unchanged |
| `timezone` not a string | coerced, then `record-invalid` | `record-invalid` |
| `timezone = "Asia/Singapore"` | accepted | unchanged |
| any other `OSError` from the lookup | escapes | refusal code |
| `locator` of 1001 chars | `record-invalid` | unchanged |

## Durable-output map

| Durable output | Task |
| --- | --- |
| `interface-contract` (read-only, byte-unchanged) | T2 |
| `decision-record` (`notes/`) | authored at PLAN |
| `current-architecture` §10 | T3 |
| `release-history` | T3 |

## Tasks

### T1: Bound and catch the timezone lookup

**Files:** `packs/core/.apm/skills/close-work/scripts/cooling.py`,
`tests/roster/test_thirty_day_cooling_and_retirement.py`.

**Tests:** AC1, AC2, AC3, AC4, AC5, AC6, AC7, AC11 per the table above.

**Approach.** Add after the existing module constants:

```python
MAX_TIMEZONE_LENGTH = 255
```

Add one module-private helper near the other predicates (`_is_locator`,
`_is_date`):

```python
def _zone(timezone: object) -> ZoneInfo | None:
    """Resolve a bounded IANA key, or None when it does not resolve."""
```

Its body bounds the key first, then resolves inside
`except (ZoneInfoNotFoundError, OSError, ValueError)`. The docstring records
why `OSError` is listed: it is neither a `ValueError` nor the `KeyError` that
`ZoneInfoNotFoundError` extends, so an over-long key escaped every refusal path
carrying an absolute host path and an errno.

Replace the three call sites, each keeping its own code:

- `validate_payload` → `record-invalid`
- `compute_review_on` → `unknown-timezone`
- `is_due` → `unknown-timezone`, binding the returned zone

**Mutation proofs.**

| # | Invariant | Mutation | Expected failure |
| --- | --- | --- | --- |
| M1 | The bound rejects an over-long key | `len(timezone) > MAX_TIMEZONE_LENGTH` → `len(timezone) > 100_000` | AC5's zero-call assertion fails; AC1–AC4 fail with `OSError` |
| M2 | `OSError` is caught | drop `OSError` from the `except` tuple | AC6 fails with an uncaught `OSError` |
| M3 | The bound precedes the lookup | move the `len` check below the `try` | AC5's zero-call assertion fails |
| M4 | The bound is the contract's number | `MAX_TIMEZONE_LENGTH = 255` → `= 256` | AC8 fails |

Each mutation targets the form a real implementation would use, not a literal
the matcher already sees. Before mutating, each proof asserts the anchor text
was found, so a mutation that fails to apply cannot yield a vacuous pass.

### T2: Pin the schema and validator bounds together

**Files:** `packs/core/.apm/skills/close-work/scripts/cooling.py`,
`tests/roster/test_thirty_day_cooling_and_retirement.py`.

**Tests:** AC8, AC9, AC10, AC12.

**Approach.** Add `MAX_LOCATOR_LENGTH = 1000` and use it in `_is_locator`
(`:162`) in place of the bare literal. This is a constant extraction with no
behaviour change; its purpose is to make the bound nameable by the parity test.

The parity test reads the contract file with `json.load` and compares
`properties.timezone.maxLength` to `MAX_TIMEZONE_LENGTH` and
`$defs.locator.maxLength` to `MAX_LOCATOR_LENGTH`. AC12 pins the contract's
SHA-256 to `8bb85ebde713c3b9f6bdd4aeca8b50dfb8291608c731607a426517e7f474a6f3`
and its `x-spec` to `["docs/specs/thirty-day-cooling-and-retirement/"]`, so the
parity test cannot be satisfied by editing the contract instead of the code.

**Mutation proofs.**

| # | Invariant | Mutation | Expected failure |
| --- | --- | --- | --- |
| M5 | The locator bound is load-bearing | `len(value) > MAX_LOCATOR_LENGTH` → `> MAX_LOCATOR_LENGTH + 1` | AC10's 1001-char case returns no code and fails |
| M6 | Parity is read from the contract, not restated | `MAX_LOCATOR_LENGTH = 1000` → `= 999` | AC9 fails |
| M7 | The contract pin is live | change any byte of the schema file | AC12 fails |

**Scope note.** The `locator` *pattern* divergence is not reconciled here; it is
recorded as a spec follow-on because changing it changes behaviour.

### T3: Release surfaces, spec index, and registration

**Files:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`,
`docs/product/changelog.md`,
`docs/architecture/work-intake-and-artifact-routing.md` §10,
`tests/roster/test_wave4_durable_outputs_and_release.py` (`:110-111` pins the
version), `docs/specs/README.md`, `workspace.toml`,
`docs/specs/thirty-day-cooling-and-retirement/spec.md` (Status-line pointer only).

**Tests:** AC13, AC15.

**Approach.** Advance the Core pack version one minor step from whatever
`origin/main` carries at the time of the bump — re-read it immediately before
editing rather than assuming, because a concurrent change took `2.14.0` during
Wave 5 and every consistency check still passed by agreeing with itself. Update
all four surfaces plus the pinned assertion in the Wave 4 release test.

Add a dated `[core]` changelog heading above `[Unreleased]`'s successor, topmost
among dated `[core]` headings. Update §10's Core version.

Register the spec through `work-intake`, in the room matching its final status.
Add its `docs/specs/README.md` row. Add the frozen Wave 5 spec's Status-line
pointer to this spec — nothing else in that file changes.

**Goal-based check.** `Done when:` `make lint-ruff`, `make lint-mypy`,
`SKIP_SAST=1 make build-check`, `make test`, `make sast`, `make site-link-check`,
and `npm test --prefix web` are green, and
`python3 tools/build-site.py && npm run build --prefix web && npm run build --prefix docs-site`
runs in that order before the emitted-changelog test.

## Declined

The razor run, recorded once. Each was considered and cut.

| Tempted to add | Why declined |
| --- | --- |
| A path-sanitising helper for finding 1 | Finding 1 was refuted; and `resource` at `:517` is already the relativized value, so even a repair needed no helper. |
| A lease or token store for finding 2 | Finding 2 was refuted; and issue digests are deterministic over the grant payload, so a store would not stop replay by a grant holder. |
| A timezone-validation module | One module-private function in the owning module covers three call sites. A module is a new boundary for nine lines. |
| A real JSON Schema validator, to make code and contract agree by construction | A new dependency, which AC15 forbids. Numeric parity by test is the bounded answer. |
| Reconciling the `locator` pattern divergence | Behaviour change with no decision on which side is right. Recorded as a spec follow-on. |
| A shared `_bounded_key` helper generalising both bounds | Two constants used at two unrelated call sites. Generalising them couples `locator` to `timezone` for no gain. |
| Widening `except` to bare `Exception` | Would swallow programming errors as `record-invalid`. The three named classes are the reachable set. |

## Risks

| Risk | Mitigation |
| --- | --- |
| `NAME_MAX` differs on a target platform, so the bound does not remove every `ENAMETOOLONG` | The `OSError` arm is independent of the bound and is proven by AC6. |
| The version bump collides with a concurrent release on `main` | T3 re-reads `origin/main` immediately before the bump; AC13 requires all four surfaces to agree, and the rebase-then-verify step re-runs it. |
| A rebase regenerates a projected file and silently drops the change | Generated files are regenerated, never merged; deliverables are digest-manifested before each rebase and verified after. |

## Changelog

- 2026-08-28: Opened. Scope is the one sustained finding of three adjudicated;
  the two refuted ones are recorded in `notes/adjudication.md` and listed as
  spec follow-ons, not built.
