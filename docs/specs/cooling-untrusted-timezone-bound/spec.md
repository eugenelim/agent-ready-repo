# Spec: Cooling untrusted timezone bound

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0096 §6; `thirty-day-cooling-and-retirement` (Shipped, frozen — this spec repairs its AC5 without editing it)
- **Brief:** none
- **Discovery:** none
- **Contract:** [`contracts/jsonschema/delivery-lifecycle-record.schema.json`](../../../contracts/jsonschema/delivery-lifecycle-record.schema.json) — read, not changed; see [`notes/schema-decision.md`](notes/schema-decision.md)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer hands the cooling engine a lifecycle record whose `timezone` field
came from outside the process. Every unresolvable zone — malformed, absent from
the platform database, or longer than the published contract permits — comes
back as a named refusal code. Nothing raises, and no host filesystem path or
`errno` reaches the caller. The published contract already states the bound the
engine enforces, and the two can no longer drift apart unnoticed.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| `interface-contract` | Applicable, read-only: the contract already declares the bound this spec makes the validator honour. No field, bound, or shape changes. | [`contracts/jsonschema/delivery-lifecycle-record.schema.json`](../../../contracts/jsonschema/delivery-lifecycle-record.schema.json) | Wave 5's spec retains sole `x-spec` ownership | AC8, AC9, AC12 | The file's bytes are unchanged and `x-spec` still names only Wave 5. |
| `decision-record` | Applicable: the schema-versus-code decision and the two refuted findings are the durable reasoning this delivery produces; both are spec-local, so no new ADR. | [`notes/schema-decision.md`](notes/schema-decision.md), [`notes/adjudication.md`](notes/adjudication.md) | This spec | The two notes exist and the Changelog cites them | Both notes resolve and state their evidence. |
| `current-architecture` | Applicable: §10 "Last verified surface" names `cooling source and tests` and pins a Core version this delivery advances. | [`docs/architecture/work-intake-and-artifact-routing.md`](../../architecture/work-intake-and-artifact-routing.md) §10 | Architecture page owner | AC13 | §10's Core version equals `packs/core/pack.toml`. |
| `release-history` | Applicable: a shipped `packs/core` runtime script changes, so the pack version advances. | [`docs/product/changelog.md`](../../product/changelog.md) | Release surface | AC13 | The topmost dated `[core]` heading equals `packs/core/pack.toml`. |
| `user-documentation` | Not applicable: no published refusal code, guide table, or maintainer task changes. `record-invalid` and `unknown-timezone` keep their existing meanings and are already documented. | — | — | — | — |

## Boundaries

### Always do

- Refuse untrusted temporal input with a published code rather than an exception.
- Keep the code's bounds numerically equal to the published contract's.
- Bound input before handing it to a platform lookup that touches the filesystem.

### Ask first

- Changing any published field, bound, pattern, or `x-spec` entry in the contract.
- Changing which refusal code an existing input shape produces.

### Never do

- Edit `docs/specs/thirty-day-cooling-and-retirement/spec.md` beyond a Status-line
  pointer; it is Shipped and frozen.
- Modify `surface_resolver.py` or `file_safety.py`.
- Add a timezone-validation module, a new store, resolver, fingerprint helper,
  dependency, scheduler, or deletion path.
- Widen a refusal into a fallback: no zone resolves to UTC or the system zone.

## Testing Strategy

Unit tests in `tests/roster/test_thirty_day_cooling_and_retirement.py`, the
suite that already owns this module. Every criterion drives the shipped public
functions — `validate_payload`, `parse_record_bytes`, `compute_review_on`,
`is_due` — with a literal payload, never a mock seam.

Two criteria need the platform lookup replaced rather than the input varied:
AC5 counts calls to prove the bound fires *before* the lookup, and AC6 forces
the `OSError` arm directly so that the length bound cannot make it vacuous.
Both substitute `ZoneInfo` in the module namespace and restore it.

Every new guard carries a mutation proof recorded in `plan.md`: the invariant,
the mutation a real implementation would make, and the expected failure.

## Acceptance Criteria

- [ ] **AC1 — A timezone one byte past the published bound refuses.** An
  otherwise-valid payload whose `timezone` is 256 `a` characters returns
  `code = "record-invalid"` from `validate_payload`, and raises nothing.
- [ ] **AC2 — The bytes seam refuses the same payload.** `parse_record_bytes` on
  that payload's canonical JSON encoding returns `code = "record-invalid"`, and
  raises nothing.
- [ ] **AC3 — `compute_review_on` names the timezone refusal.**
  `compute_review_on(date(2026, 8, 1), "a" * 256)` returns a `CoolingResult`
  whose `code` is `unknown-timezone`.
- [ ] **AC4 — `is_due` names the timezone refusal.** A record carrying
  `timezone = "a" * 256`, given an aware instant, returns
  `code = "unknown-timezone"`.
- [ ] **AC5 — The bound is checked before the platform lookup.** With `ZoneInfo`
  replaced by a counting spy, `validate_payload` on a 256-character `timezone`
  calls it zero times; on a 255-character one it calls it once.
- [ ] **AC6 — An `OSError` from the lookup cannot escape.** With `ZoneInfo`
  replaced by one that raises `OSError(63, "File name too long")` for `"UTC"`,
  `validate_payload` returns `record-invalid` instead of raising.
- [ ] **AC7 — The refusal carries only a published code.** For each of AC1–AC4's
  four results, `as_dict()` keys equal
  `{"due", "permission_granted", "mutated", "code"}` and `code` is a member of
  `REFUSAL_CODES`.
- [ ] **AC8 — The timezone bound equals the published one.**
  `cooling.MAX_TIMEZONE_LENGTH` equals `properties.timezone.maxLength` in
  `contracts/jsonschema/delivery-lifecycle-record.schema.json`.
- [ ] **AC9 — The locator bound equals the published one.**
  `cooling.MAX_LOCATOR_LENGTH` equals `$defs.locator.maxLength` in that same
  contract.
- [ ] **AC10 — The locator bound is load-bearing.** A payload whose `locator` is
  1000 path-safe characters returns no code; one of 1001 returns
  `record-invalid`.
- [ ] **AC11 — A resolvable timezone is unaffected.** An otherwise-valid payload
  with `timezone = "Asia/Singapore"` returns no code from `validate_payload`.
- [ ] **AC12 — The published contract is unchanged.** The schema file's SHA-256
  equals its value at `97a0b6ad`, and its `x-spec` equals
  `["docs/specs/thirty-day-cooling-and-retirement/"]`.
- [ ] **AC13 — The release surfaces agree on one version.**
  `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, the topmost
  dated `[core]` changelog heading, and
  `docs/architecture/work-intake-and-artifact-routing.md` §10 all name the same
  Core version.
- [ ] **AC14 — The reused primitives stay byte-unchanged.** The SHA-256 of
  `surface_resolver.py` and of `file_safety.py` equal the values pinned in
  `tests/roster/test_close_work_extraction_and_immediate_disposition.py`.
- [ ] **AC15 — No dependency is added.** `pyproject.toml`,
  `packages/*/pyproject.toml`, and `tools/requirements.txt` gain no entry.

## Follow-ons

Each is separately owned and outside this spec's criteria.

- **Wave 5 finding 1 — refuted, not repaired.** The success payload's absolute
  `mutated` path. Evidence and reasoning in [`notes/adjudication.md`](notes/adjudication.md).
  Residual observation: `CoolingResult.as_dict`'s "diagnostic-free" docstring
  claims more than the success path delivers.
- **Wave 5 finding 2 — refuted, not repaired.** The unpopped write grant in
  `_binding_is_issued`. Evidence and reasoning in
  [`notes/adjudication.md`](notes/adjudication.md). Single-use write grants
  remain a defensible hardening with Wave 4 precedent; they need their own spec
  and acceptance criterion, because no shipped authority requires them.
- **Locator pattern divergence.** The contract's `$defs/locator` pattern rejects
  the C0 control range and `U+007F`, which `_is_locator` admits; `_is_locator`
  rejects a `.` segment, which the pattern admits. AC9 and AC10 pin only the
  numeric bound. Reconciling the pattern changes behaviour and belongs to a
  spec that can state which side is right.

## Assumptions

- `ZoneInfo` raises `OSError(ENAMETOOLONG)` rather than `ZoneInfoNotFoundError`
  for a key whose final path component exceeds the platform `NAME_MAX`.
  (checked 2026-08-28 on CPython 3.13.13: `ZoneInfo("a" * 256)` raises
  `OSError(63, 'File name too long')` carrying an absolute `filename`)
- 255 is the platform `NAME_MAX` on the supported targets, so a key inside the
  published bound cannot produce `ENAMETOOLONG` from the final component.
  The `OSError` arm covers the residue regardless. (checked: AC6 forces the arm
  independently of the bound)
- `zoneinfo` is stdlib on the `>=3.11` floor both packages declare, so no
  manifest changes. (checked: AC15)
- Wave 5's spec is frozen, so its AC5 defect is repaired by this spec's criteria
  rather than by amending it. Wave 5's tests are not frozen and are extended
  here. (`docs/CONVENTIONS.md` § "A spec directory freezes as a unit")

## Changelog

- 2026-08-28: Opened. Three Wave 5 post-code review Concerns were adjudicated
  before any repair; one sustained and two refuted. This spec carries the
  sustained one. See [`notes/adjudication.md`](notes/adjudication.md) for all
  three verdicts and [`notes/schema-decision.md`](notes/schema-decision.md) for
  why the bound is code-side only.
