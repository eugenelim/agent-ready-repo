# Plan: Cooling untrusted input refusals

- **Spec:** [spec.md](spec.md)
- **Status:** Done
- **Repository anchors:** `docs/rfc/0096-portable-delivery-artifact-lifecycle.md`
  §6 owns cooling policy; `packs/core/.apm/skills/close-work/scripts/cooling.py`
  is the module under change and its own `_exceeds_depth` docstring (`:179-198`)
  is the analogous precedent — the same escape class (`RecursionError` outside
  the refusal tuple, surfacing an absolute path) was found and closed in Wave 5;
  `tests/roster/test_thirty_day_cooling_and_retirement.py` is the owning suite
  and holds the analogous bound-straddling guard at
  `test_the_depth_bound_discriminates_at_its_limit`;
  `contracts/jsonschema/delivery-lifecycle-record.schema.json` is the published
  contract, read but not written; `packs/AGENTS.md` § "Version bump rule" owns
  the release step and § self-host owns projection regeneration;
  `tools/assert-sast-chain-reachable.py:4` is the precedent for a disambiguated
  `# STUB:` marker in a file shared with another spec. Named deviation: none —
  this repairs an existing seam and introduces no new boundary.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document may change while Drafting. After approval, Phase 1 treats substantive
> plan changes as a re-plan requiring a new review and approval.

## Approach

Four tasks. T1 closes the timezone escape at all three seams and proves each
half independently. T2 closes the exception-envelope escape, which reaches four
seams including the two caller-facing review entries. T3 makes the
schema-versus-code bound divergence mechanical so it cannot recur silently. T4
lands the release, projection, and registration surfaces.

T1 and T2 are independent and repair the same class: a hand-written validator
weaker than the published contract, failing by exception rather than by refusal
code.

The whole change to production code is three new module-private functions
(`_zone`, `_is_one_of`, `_matches`), three new module constants, one comparison
operator, and the call-site edits that route through them. Nothing new
is introduced; the razor run is recorded under [Declined](#declined).

## Constraints

- `docs/specs/thirty-day-cooling-and-retirement/spec.md` is Shipped and frozen
  and is **not edited at all**. `docs/CONVENTIONS.md` § "Superseding a frozen
  document" licenses only an ADR pointer or a closed-`[backlog]`-anchor pointer
  on its Status line; this change produces neither, so no licensed form exists.
- `surface_resolver.py` and `file_safety.py` stay byte-unchanged. Their pinned
  digests in `tests/roster/test_close_work_extraction_and_immediate_disposition.py`
  (`:214`, `:216`) must pass with that file unedited.
- `contracts/jsonschema/delivery-lifecycle-record.schema.json` stays
  byte-unchanged (AC15) — see [`notes/schema-decision.md`](notes/schema-decision.md).
- No new dependency, module, store, resolver, fingerprint helper, scheduler, or
  deletion path.
- `cooling.py` must still contain no clock call (Wave 5 AC6) and no removal call
  beyond its single temp-file cleanup (Wave 5 AC36). Both are AST-asserted by
  the existing suite and must keep passing.
- `cooling.py` is a `packs/core/.apm/` runtime script: stdlib only, no
  third-party import, even one already declared for tests.
- Every `# STUB:` marker added to the shared suite is disambiguated as
  `# STUB: AC<n> (spec/cooling-untrusted-input-refusals)`; the file already
  carries 43 markers belonging to the frozen Wave 5 spec.

## Construction tests

All in `tests/roster/test_thirty_day_cooling_and_retirement.py`.

| AC | Test | Mode | Stub |
| --- | --- | --- | --- |
| AC1, AC2 | `test_an_over_long_timezone_refuses_through_both_seams` | TDD | `stub: true` |
| AC3, AC4 | `test_the_temporal_helpers_name_the_timezone_refusal` | TDD | `stub: true` |
| AC5 | `test_the_timezone_bound_precedes_the_lookup_at_every_seam` | TDD | `stub: true` |
| AC6 | `test_an_oserror_from_the_zone_lookup_escapes_no_seam` | TDD | `stub: true` |
| AC6a | `test_the_zone_catch_set_is_exactly_the_three_named_classes` | TDD | `stub: true` |
| AC7 | `test_a_non_string_timezone_refuses_without_a_lookup` | TDD | `stub: true` |
| AC8 | `test_the_timezone_corpus_never_raises` | TDD | `stub: true` |
| AC9 | `test_a_timezone_refusal_carries_a_code_and_no_mutation` | TDD | `stub: true` |
| AC10 | `test_a_resolvable_timezone_is_unaffected` | TDD | `stub: true` |
| AC11, AC13 | `test_the_code_bounds_equal_the_published_bounds` | TDD | `stub: true` |
| AC11a | `test_the_timezone_constant_governs_the_guard` | TDD | `stub: true` |
| AC12 | `test_an_empty_timezone_refuses` | TDD | `stub: true` |
| AC14 | `test_the_locator_constant_governs_the_guard` | TDD | `stub: true` |
| AC15 | `test_the_published_contract_is_unchanged` | TDD | `stub: true` |
| AC16 | `test_the_release_surfaces_agree_and_advance` | TDD | `stub: true` |
| AC17 | `test_the_cooling_projections_match_their_source` | TDD | `stub: true` |
| AC20 | `test_an_evidence_bearing_incomplete_envelope_refuses` | TDD | `stub: true` |
| AC21 | `test_the_review_seams_refuse_an_incomplete_envelope` | TDD | `stub: true` |
| AC22 | `test_a_complete_exception_envelope_is_accepted` | TDD | `stub: true` |
| AC23 | `test_a_container_where_a_scalar_belongs_refuses` | TDD | added post-GATES |
| AC24 | `test_a_container_in_the_exception_envelope_refuses` | TDD | added post-GATES |
| AC25 | `test_the_caller_supplied_enums_refuse_a_container` | TDD | added post-GATES |
| AC26 | `test_the_alias_bound_equals_the_published_one` | TDD | added post-GATES |
| AC27 | `test_a_non_string_delivery_id_refuses` | TDD | added post-GATES |
| AC28 | `test_untrusted_text_is_matched_never_coerced`, `test_untrusted_authority_and_envelope_text_is_not_coerced` | TDD | added post-GATES |
| AC29 | `test_a_malformed_candidate_refuses_instead_of_raising` | TDD | added post-GATES |
| AC18 | existing `tests/roster/test_close_work_extraction_and_immediate_disposition.py:214,216` | goal-based | passes unedited |
| AC18a | `Done when:` the `docs/specs/README.md` row link resolves and `workspace-status` lists the spec in the room matching its Status | goal-based | n/a |
| AC19 | `Done when:` `git diff --stat "$(git merge-base origin/main HEAD)" -- pyproject.toml 'packages/*/pyproject.toml' tools/requirements.txt` is empty | goal-based | n/a |

32 of 32 criteria carry a materialised stub or a named goal-based check. None
is deferred to EXECUTE. The measured red/green split is in the spec's Testing
Strategy, not asserted uniformly here.

## Design (LLD)

### Design decisions

**One resolver, three call sites.** `validate_payload` (`:279-282`),
`compute_review_on` (`:326-329`), and `is_due` (`:337-340`) each do the same two
things — bound-check nothing, then resolve — and each needs its own refusal
code. Duplicating a bound-and-type guard three times is more code than one
private helper returning `ZoneInfo | None` that lets each site name its own
code. The helper is a function in the existing module, not a new module.

**The guard runs before the lookup, not after.** `ZoneInfo` builds a filesystem
path from the key and stats it, so an over-long key produces the `OSError` this
spec exists to stop, and a non-string key produces `TypeError` from `len()` or
from `ZoneInfo` itself. A guard applied after the call would be dead code. AC5
and AC7 pin the ordering by counting calls rather than by inspecting source.

**Both halves ship, and both are proven at every seam.** The bound alone leaves
other `OSError` shapes uncaught and does not cover a multi-byte key on a
byte-limited filesystem; the `except` arm alone leaves an unbounded key reaching
a syscall on every validate and leaves the contract's published `maxLength`
unenforced. AC5 proves the bound independently of the arm and AC6 proves the arm
independently of the bound — each at all three seams, because a guard proven at
one seam does not prove the other two.

**`_zone` type-checks its input.** `validate_payload` currently coerces with
`str(payload["timezone"])`, so a non-string `timezone` is stringified before
lookup. The contract declares `"type": "string"`. Removing the coercion without
a type guard would raise `TypeError`, which is in none of the three `except`
tuples — a regression introduced by the hardening itself. AC7 pins the guard.

### Data & schema

No persisted shape changes. `MAX_TIMEZONE_LENGTH = 255`,
`MAX_LOCATOR_LENGTH = 1000`, and `MAX_ALIAS_COUNT = 16` mirror the contract's
three declared bounds; AC11 and AC13
compare them to the contract file at test time so the mirror cannot drift, and
AC14 patches the locator constant to prove the guard reads it rather than a
literal.

### Interfaces & contracts

No public function signature changes. `validate_payload`, `parse_record_bytes`,
`compute_review_on`, and `is_due` keep their return types and their refusal
codes. No code is added to or removed from `REFUSAL_CODES`.

### The AC8 corpus

Eleven `timezone` values, each driven through `validate_payload` and
`parse_record_bytes`. The "shipped behaviour" column was measured on
**darwin/APFS with `tzdata` importable**; see
[`notes/corpus-measurement.md`](notes/corpus-measurement.md) for why both the
filesystem and the presence of `tzdata` change the answer.

| # | Value | Shipped behaviour | Required |
| --- | --- | --- | --- |
| 1 | `"a" * 256` | **raises `OSError`** | `record-invalid` |
| 2 | `"é" * 300` | **raises `OSError`** | `record-invalid` |
| 3 | `"a" * 255` | `record-invalid` | unchanged |
| 4 | `""` | `record-invalid` | unchanged |
| 5 | `" "` | `record-invalid` | unchanged |
| 6 | `"."` | `record-invalid` | unchanged |
| 7 | `"/etc/passwd"` | `record-invalid` | unchanged |
| 8 | `"../../etc/passwd"` | `record-invalid` | unchanged |
| 9 | `"Not/A/Zone"` | `record-invalid` | unchanged |
| 10 | `"a\x00b"` | `record-invalid` | unchanged |
| 11 | `"é" * 200` (third in the stub's parametrize list; the table groups by kind, not by order) | `ZoneInfoNotFoundError` on APFS; **raises `OSError`** on a byte-limited filesystem | `record-invalid` |

Two of eleven are red on darwin/APFS. Row 11 is the one inside the code-point
bound: it is the only corpus value that can reach the `OSError` arm through a
real `ZoneInfo` after T1 lands, because rows 1 and 2 are short-circuited by the
bound. It is red on ext4, which is what CI runs.

### Failure, edge cases & resilience

| Input | Before | After |
| --- | --- | --- |
| `timezone` of 256 code points | `OSError(63)` escapes with absolute `filename` | `record-invalid` / `unknown-timezone` |
| `timezone` of 255 code points, not a zone | `record-invalid` | unchanged |
| multi-byte `timezone` inside the bound on a byte-limited filesystem | `OSError` escapes | caught by the arm |
| `timezone` not a string | coerced via `str()`, then `record-invalid` | `record-invalid`, no lookup |
| `timezone = "Asia/Singapore"` | accepted | unchanged |
| any other `OSError` from the lookup | escapes at all three seams | refusal code at all three |
| `locator` of 1001 characters | `record-invalid` | unchanged |

## Durable-output map

| Durable output | Task |
| --- | --- |
| `interface-contract` (read-only, byte-unchanged) | T3 |
| `decision-record` (`notes/`) | authored at PLAN |
| `release-history` | T4 |

## Tasks

### T1: Bound, type-check, and catch the timezone lookup

- **ACs:** AC1, AC2, AC3, AC4, AC5, AC6, AC6a, AC7, AC8, AC9, AC10, AC11a
  — AC11a's guard is built here, since T1 introduces `MAX_TIMEZONE_LENGTH`;
  its mutation proof M7a sits with the parity proofs in T3
- **Verification mode:** TDD
- **Depends on:** none
- **Files:** `packs/core/.apm/skills/close-work/scripts/cooling.py`,
  `tests/roster/test_thirty_day_cooling_and_retirement.py`

**Tests:** the ten rows of the Construction tests table covering AC1–AC10.
`stub: true` — all ten materialised red at PLAN.

**Approach.** Add one module constant beside the existing bounds:

```python
MAX_TIMEZONE_LENGTH = 255
```

Add one module-private helper beside the other predicates (`_is_locator`,
`_is_date`):

```python
def _zone(timezone: object) -> ZoneInfo | None:
    """Resolve a bounded IANA key, or None when it does not resolve."""
```

Its body type-checks and bounds the key first, then resolves inside
`except (ZoneInfoNotFoundError, OSError, ValueError)`. The docstring records why
`OSError` is listed: it is neither a `ValueError` nor the `KeyError` that
`ZoneInfoNotFoundError` extends, so an over-long key escaped every refusal path
carrying an absolute host path and an errno.

Replace the three call sites, each keeping its own code:

- `validate_payload` (`:279-282`) → `record-invalid`
- `compute_review_on` (`:326-329`) → `unknown-timezone`
- `is_due` (`:337-340`) → `unknown-timezone`, binding the returned zone

**Mutation proofs.** Each proof asserts its anchor text was found before
mutating, so a mutation that fails to apply cannot yield a vacuous pass.

| # | Invariant | Mutation | Expected failure |
| --- | --- | --- | --- |
| M1 | The bound precedes the lookup | `len(timezone) > MAX_TIMEZONE_LENGTH` → `> 100_000` | **AC5 and AC11a.** AC1–AC4 still pass, because the `OSError` arm the same task adds absorbs the escape — which is why the zero-call assertions are the only detectors for this mutation. |
| M2 | `OSError` is caught at every seam | drop `OSError` from the `except` tuple | AC6 and AC9 fail at all three seams with an uncaught `OSError`; AC9 is in the set because it now covers AC6's results |
| M3 | The arm is not seam-local | restore `except (ZoneInfoNotFoundError, ValueError)` at `compute_review_on` and `is_due` only, keeping `_zone` for `validate_payload` | AC6 fails at those two seams and passes at the first — the exact half-repair AC6 exists to reject |
| M4 | The type guard precedes the bound | drop `isinstance(timezone, str)` from `_zone` | AC7 fails with an uncaught `TypeError` from `len()` |
| M5 | The bound is the contract's number | `MAX_TIMEZONE_LENGTH = 255` → `= 256` | AC11 fails |

### T2: Refuse an incomplete exception envelope

- **ACs:** AC20, AC21, AC22
- **Verification mode:** TDD
- **Depends on:** none
- **Files:** `packs/core/.apm/skills/close-work/scripts/cooling.py`,
  `tests/roster/test_thirty_day_cooling_and_retirement.py`

**Tests:** the three rows covering AC20-AC22. `stub: true`.

**Approach.** `_exception_is_valid` (`cooling.py:214-232`) filters permitted keys,
then gates on

```python
if set(value) < {"reason", "owner_role", "review_on"}:
    return False
```

`<` is a proper-subset test. `evidence_ref` is a permitted key that is not in the
compared set, so any envelope carrying it is not a subset of the required three,
the gate is false, and control reaches `value["reason"]`, `value["owner_role"]`,
and `value["review_on"]` — raising `KeyError` for whichever is absent.

Replace the gate with a superset test:

```python
if not set(value) >= {"reason", "owner_role", "review_on"}:
    return False
```

That is the form the neighbouring `validate_payload` already uses at
`cooling.py:240` (`not set(payload) >= _REQUIRED`). Proved by enumeration before
writing it — of the sixteen envelope shapes, eight carry `evidence_ref` and so
fall through the old gate, and seven of those omit a required key: the superset test rejects exactly the seven dangerous shapes and
still admits both valid ones, `{reason, owner_role, review_on}` with and without
`evidence_ref`.

Nothing else changes. The reason, role, date, and evidence checks below the gate
are already correct once they cannot be reached with a missing key.

**Mutation proofs.**

| # | Invariant | Mutation | Expected failure |
| --- | --- | --- | --- |
| M13 | The gate is a superset test | restore `set(value) < {...}` | AC20 and AC21 fail with `KeyError`, the shipped defect |
| M14 | The gate still admits a valid envelope | `not set(value) >= {...}` becomes `set(value) != {...}` | AC22 fails for the envelope carrying `evidence_ref`, since exact equality rejects the permitted fourth key |
| M15 | The caller-facing seams are covered | fix `validate_payload`'s path only, leaving `review` and `review_exception` reading the unfixed helper | impossible by construction here — both call the same helper — which is why AC21 asserts them directly rather than trusting that |

### T3: Pin the schema and validator bounds together

- **ACs:** AC11, AC12, AC13, AC14, AC15
- **Verification mode:** TDD
- **Depends on:** T1 — it needs `MAX_TIMEZONE_LENGTH` from T1's helper
- **Files:** `packs/core/.apm/skills/close-work/scripts/cooling.py`,
  `tests/roster/test_thirty_day_cooling_and_retirement.py`

**Tests:** the four rows covering AC11–AC15. `stub: true`.

**Approach.** Add `MAX_LOCATOR_LENGTH = 1000` and use it in `_is_locator`
(`:162`) in place of the bare literal. The extraction is behaviour-free; AC14
makes it load-bearing by patching the constant on a freshly loaded module and
asserting the guard follows, so a dead constant fails.

The parity test reads the contract with `json.load` and compares
`properties.timezone.maxLength` to `MAX_TIMEZONE_LENGTH` and
`$defs.locator.maxLength` to `MAX_LOCATOR_LENGTH`. AC15 pins the contract's
SHA-256 to its value at the merge base, so parity cannot be satisfied by editing
the contract instead of the code. The digest literal lives in the test only.

**Mutation proofs.**

| # | Invariant | Mutation | Expected failure |
| --- | --- | --- | --- |
| M6 | The locator constant governs the guard | leave the literal `1000` in `_is_locator` while adding the constant | AC14 fails — the patched constant does not move the boundary |
| M7 | Parity is read from the contract | `MAX_LOCATOR_LENGTH = 1000` → `= 999` | AC13 fails |
| M7a | The timezone constant governs the guard | leave a bare literal `255` inside `_zone` while adding `MAX_TIMEZONE_LENGTH` | AC11a fails at all three seams — the patched constant does not move the boundary. Without AC11a, a dead constant beside a bare literal passes AC1–AC5, AC11, and M5 |
| M8 | The contract pin is live | change any byte of the schema file | AC15 fails |
| M8a | The `ValueError` arm is live | drop `ValueError` from `_zone`'s `except` tuple | AC12 fails, and five corpus rows fail with it — `""`, `"."`, `"/etc/passwd"`, `"../../etc/passwd"`, and `"a\x00b"` are all `ValueError` shapes. The Approach has no emptiness path to drop, so this is the mutation that actually reaches the empty key |
| M8b | The happy path is still asserted | make `_zone` return `None` unconditionally | AC5, AC10, AC11a, and AC14 fail. AC1–AC4, AC6, AC8, and AC9 all still pass, because refusing everything satisfies every criterion that only asserts a refusal — which is why the non-regression criteria exist |

### T4: Release, projections, and registration

- **ACs:** AC16, AC17, AC18, AC18a, AC19
- **Verification mode:** mixed — AC16 and AC17 are TDD construction tests; AC18
  and AC19 are goal-based checks
- **Depends on:** T1, T2, T3, T5 — the release ships every repair. T5 landed
  after T4's first pass; the version already covered it, so only the
  projections were regenerated and re-verified rather than re-versioned.
- **Files:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`,
  `docs/product/changelog.md`, `docs/specs/README.md`, `workspace.toml`,
  `tests/roster/test_thirty_day_cooling_and_retirement.py`
- **Generated, not edited:** `.claude/skills/close-work/scripts/cooling.py` and
  `.agents/skills/close-work/scripts/cooling.py` change as `make build-self`
  output. `packs/AGENTS.md` forbids editing an adapter projection directly, so
  they are not in the Files list; AC17 asserts the regenerated result.

**Tests:** AC16 and AC17 as construction tests; AC18 and AC19 goal-based.

**Approach.** Re-read `origin/main`'s `packs/core/pack.toml` immediately before
the bump and advance one **patch** step from it — `packs/AGENTS.md` § "Version
bump rule" gives patch for changed content, minor for new primitives, major for
removals, and this adds no primitive. The merge base already moved from `2.15.0`
twice during this spec's PLAN phase, so the number is read, never
assumed. AC16 requires the result to be strictly greater than the merge base's,
which a self-consistent but stale set cannot satisfy.

`packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` move together
— `test_core_release_metadata_and_history_agree` compares them to each other.
Its `[core][2.15.0]` regex asserts that heading still exists in history, which a
new topmost heading does not disturb, so that test needs no edit.

Add a dated `[core]` changelog heading with a `### Fixed` section and no
`### Highlights`: a validator repair is not a `/now/` highlight, and the
changelog's own rule keeps a Highlights-free entry out of `/now/`.

Update `MERGE_BASE_CORE_VERSION` in the AC16 test to the merge base's
`packs/core/pack.toml` version at the time of the rebase. It is a literal
because the test must hold in a shallow clone and in CI, where `origin/main` may
not be a local ref.

`docs/specs/README.md` and `workspace.toml` are covered by AC18a. The frozen
Wave 5 spec is not touched.

Regenerate the two projections with `make build-self` — never hand-edit them.
`build-self` refuses a dirty tree, so it runs after the source change is
committed, and its output is committed separately. The `close-work` eval harness
is unchanged and the reason is recorded: this repair alters no instruction,
prompt, or agent-visible behaviour, only a refusal code path already covered by
the roster suite.

Register the spec through `work-intake` in the room matching its final status,
and add its `docs/specs/README.md` row beside the Wave 5 row.

**Mutation proofs.** AC16 and AC17 are green by construction, so each needs a
proof it can fail at all.

| # | Invariant | Mutation | Expected failure |
| --- | --- | --- | --- |
| M9 | The two manifests move together | bump `packs/core/pack.toml` and leave `.claude-plugin/plugin.json` behind | AC16 fails on the manifest comparison |
| M10 | The changelog heading is topmost and named | bump both manifests without adding the changelog heading | AC16 fails — `headings[0]` is the predecessor |
| M11 | The version genuinely advances | leave every surface at the merge base's version — bump nothing at all | AC16 fails the strict-greater comparison against the pinned merge-base literal. Comparing against the changelog's previous heading instead would pass, because the merge base already carries the topmost heading's version |
| M12 | The projections are real copies | change one byte of `.claude/skills/close-work/scripts/cooling.py` | AC17 fails |

**Goal-based check.** `Done when:` `make lint-ruff`, `make lint-mypy`,
`SKIP_SAST=1 make build-check` (after clearing `dist/**/__pycache__`),
`make test`, `make sast`, `make site-link-check`, and `npm test --prefix web`
are green, and the emitted-changelog test is preceded by
`python3 tools/build-site.py && npm run build --prefix web && npm run build --prefix docs-site`
in that order.

### T5: Close the remaining untrusted-shape escapes

- **ACs:** AC23, AC24, AC25, AC26, AC27, AC28, AC29
- **Verification mode:** TDD
- **Depends on:** T1, T2
- **Files:** `packs/core/.apm/skills/close-work/scripts/cooling.py`,
  `tests/roster/test_thirty_day_cooling_and_retirement.py`

**Tests:** the seven rows covering AC23-AC29, all added post-GATES.

**Approach.** Post-GATES review found three further instances of one systemic
defect — trusting the shape of untrusted input — each reached by asking the same
question the first two answered.

`_is_one_of(value, options)` guards six membership tests. JSON admits lists and
dicts, both unhashable, so `value in {...}` raised `TypeError`.

`_matches(pattern, value)` replaces eight `str()` coercions. `str()` on
untrusted input fails twice over: past CPython's digit limit `str(10**5000)`
raises `ValueError`, and `str(1e999)` is `"inf"`, which `_STATUS_RE` and
`_ROLE_RE` both accept — so a coerced value could validate and then persist in a
form unequal to its source.

`_resolve_destination` type-checked the candidate container and then reached
into `.confirmations`, `.kind`, and `.status` on its elements unguarded. It also
front-ran `surface_resolver`'s own validation, which already refuses these
shapes through a caught refusal, so the local pre-check was strictly weaker than
the helper it preceded.

`MAX_ALIAS_COUNT` extracts the third published bound, the only one still a bare
literal.

**Mutation proofs.** M16 to M20, executed and recorded under
[Post-GATES mutation proofs](#post-gates-mutation-proofs). M17 is why AC27
exists: the `delivery_id` repair had no criterion until that table was built.

## Post-GATES mutation proofs

Added after review found a second escape class. Each was applied to the shipped
source, run against the full suite, and restored by editing — never by
`git checkout`, which cannot tell whose uncommitted work it would destroy. Each
asserts its anchor text was found first, so a mutation that fails to apply
cannot yield a vacuous pass.

| # | Mutation | Killed by | Result |
| --- | --- | --- | --- |
| M16 | drop the `isinstance` guard in `_is_one_of` | AC23, AC24, AC25 | killed |
| M17 | restore `delivery_id`'s `str()` coercion | AC27 | killed |
| M18 | revert the alias bound to a bare literal | AC26 | killed |
| M19 | restore the proper-subset envelope gate | AC20, AC21 | killed |
| M20 | wrap a `_zone` call site in `except Exception` | AC6a | killed |
| M21 | make `_matches` coerce again — `pattern.fullmatch(str(value))` | AC27, AC28 | killed |
| M22 | restore `_resolve_destination`'s unguarded element access, verbatim | AC29 | killed |
| M23 | make `_matches` return `True` unconditionally | AC10 (Wave 5's pattern test), AC23, AC24, AC27, AC28 | killed |

M17 is the reason AC27 exists. The repair had no criterion until this table was
built: AC23's containers fail the `delivery_id` pattern with or without the type
guard, so only a scalar that survives `str()` discriminates, and the mutation
survived until AC27 was written.

M20 is the reason AC6a walks the call sites rather than `_zone` alone. Pinning
the `except` tuple inside the helper left a caller free to wrap it in a broad
catch and do exactly what the criterion exists to prevent.

AC17 also fires on every one of these, because mutating the source makes it
differ from its projections. That is incidental — it is a canary for any source
edit, not the criterion that discriminates the mutation.

M22 first appeared to survive, and did not. The initial attempt replaced `try:`
with `if False:`, which orphaned the `except` clause: the module stopped parsing,
pytest reported a collection error rather than failures, and a harness that reads
only `FAILED` lines saw an empty kill set. A mutation that does not produce a
loadable module proves nothing about the guard. The proof above uses the
pre-repair form verbatim and asserts the mutant parses before running.

The pre-EXECUTE proofs M1, M2, M4, M6, M7a, M8a, M8b, M13, and M14 were executed
independently by the quality reviewer against the same suite and each was killed
by the criteria this plan predicts.

## Declined

The razor run, recorded once. Each was considered and cut.

| Tempted to add | Why declined |
| --- | --- |
| A path-sanitising helper for finding 1 | Finding 1 was refuted; and `resource` at `:517` is already the relativized value, so even a repair needed no helper. |
| A lease or token store for finding 2 | Finding 2 was refuted; and issue digests are deterministic over the grant payload, so a store would not stop replay by a grant holder. |
| A timezone-validation module | One module-private function in the owning module covers three call sites. A module is a new boundary for eleven lines. |
| Rewriting `_exception_is_valid` rather than changing its comparison | The four checks below the gate are already correct once an incomplete envelope cannot reach them. One operator is the whole repair; enumeration over all eight envelope shapes proved it before it was written. |
| A real JSON Schema validator to make code and contract agree by construction | Not a new dependency — `jsonschema>=4.0` is declared at `tools/requirements.txt:5` and several `tests/roster/` modules import it, including `test_semantic_surface_resolution_contract.py`, which does exactly this for another contract. The exact count lives in [`notes/schema-decision.md`](notes/schema-decision.md). Declined on its true grounds: `cooling.py` is a `packs/core/.apm/` runtime script that must stay stdlib-only, and a test-side differential validator would surface every divergence including the deferred `locator` pattern, exceeding the sustained finding's scope. |
| Reconciling the `locator` pattern divergence | Behaviour change with no decision on which side is right. Recorded as a follow-on. |
| A shared `_bounded_key` helper generalising both bounds | Two constants at two unrelated call sites. Generalising couples `locator` to `timezone` for no gain. |
| Widening `except` to bare `Exception` | Would swallow programming errors as `record-invalid`. The four named classes are the reachable set. |
| Advancing `work-intake-and-artifact-routing.md` §10's Core version | §10 is a whole-surface verification claim; this change alters nothing it describes, and the `2.15.1` release left it likewise. Bumping it would assert re-verification not performed. |
| `[backlog].open` entries for the four follow-ons | The work-loop's DECIDE step forbids a durable follow-on entry by default for work this loop did not include; the entries are reachable from the spec's `## Follow-ons`, which is a section of the shipped `new-spec` template. Route through `work-intake` if the owner asks to remember them. |

## Risks

| Risk | Mitigation |
| --- | --- |
| The version bump collides with a concurrent release on `main` | T4 re-reads `origin/main` immediately before the bump; AC16 pins the merge-base version as a literal and requires strictly-greater, which a stale self-consistent set fails. Recurred **twice** during PLAN: `2.15.0` → `2.15.1`, then `2.15.1` → `2.15.2`. Each rebase re-pins the literal. |
| A rebase regenerates a projected file and silently drops the change | Generated files are regenerated, never merged; deliverables are digest-manifested before each rebase and verified after. AC17 asserts the projections match. |
| The bound does not remove every `ENAMETOOLONG` on a byte-limited filesystem | The `OSError` arm is independent of the bound and is proven at all three seams by AC6. Recorded as a spec Assumption with its measurement. |
| A new `# STUB:` marker collides with the frozen Wave 5 spec's 43 markers | Every marker is disambiguated with the spec slug, per `tools/assert-sast-chain-reachable.py:4`. |

## Changelog

- 2026-08-28: Opened. Scope is the one sustained finding of three adjudicated;
  the two refuted ones are recorded in `notes/adjudication.md`.
- 2026-08-29: Post-GATES review found a second escape class the PLAN-time
  corpus had missed — six membership tests comparing an untrusted JSON value
  against a set of strings, where a list or dict is unhashable and `in` raises
  `TypeError`. `_is_one_of` guards all six. `delivery_id`'s `str()` coercion and
  the bare alias literal were closed in the same pass, and AC23 to AC26 cover
  the class by enumeration rather than by sampling. AC20 was corrected from four
  envelope shapes to seven.
- 2026-08-29: T2 added on an owner scope widening — the `_exception_is_valid`
  proper-subset defect moved from a recorded follow-on into the criteria, with
  mutation proofs M13 to M15, and the spec and plan were re-approved.
- 2026-08-28: Revised from pre-EXECUTE adversarial and secure-design review.
  AC5/AC6 widened from one seam to three; non-string, corpus, empty-timezone,
  locator-binding, and projection criteria added; version step corrected from
  minor to patch after `origin/main` moved to `2.15.1` mid-PLAN; `Contract:` set
  to `none`; M1's expected failure corrected — the `OSError` arm absorbs the
  bound mutation, so AC5 is its only detector; the `jsonschema` decline restated
  on true grounds. A 32-case corpus measurement found a second defect of the
  same class in `_exception_is_valid`; it was recorded as a follow-on then and
  built later, under T2.
