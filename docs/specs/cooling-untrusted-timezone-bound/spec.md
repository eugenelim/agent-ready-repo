# Spec: Cooling untrusted timezone bound

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0096 §6; `thirty-day-cooling-and-retirement` (Shipped, frozen — this spec repairs its AC5 without editing its body; Status-line pointer only)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — [`contracts/jsonschema/delivery-lifecycle-record.schema.json`](../../../contracts/jsonschema/delivery-lifecycle-record.schema.json) is read and pinned byte-unchanged, never defined or touched; see [`notes/schema-decision.md`](notes/schema-decision.md)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer hands the cooling engine a lifecycle record whose `timezone` field
came from outside the process. Every unresolvable zone — malformed, non-string,
absent from the platform database, or longer than the published contract permits
— comes back as a named refusal code from every seam that resolves one. Nothing
raises, and no host filesystem path or `errno` reaches the caller. The two
numeric bounds this spec names can no longer drift from the published contract
unnoticed.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| `interface-contract` | Applicable, read-only: the contract already declares the bound this spec makes the validator honour. No field, bound, or shape changes, so the `Contract:` header stays `none`. | [`contracts/jsonschema/delivery-lifecycle-record.schema.json`](../../../contracts/jsonschema/delivery-lifecycle-record.schema.json) | `thirty-day-cooling-and-retirement` retains sole `x-spec` ownership | AC11, AC13, AC15 | The file's bytes are unchanged and `x-spec` still names only Wave 5. |
| `decision-record` | Applicable: the schema-versus-code decision, the three adjudicated Wave 5 findings, and the measured corpus are the durable reasoning this delivery produces; all spec-local, so no new ADR. | [`notes/schema-decision.md`](notes/schema-decision.md), [`notes/adjudication.md`](notes/adjudication.md), [`notes/corpus-measurement.md`](notes/corpus-measurement.md) | This spec | The three notes exist and the Changelog cites them | Each note resolves and states its evidence. |
| `release-history` | Applicable: a shipped `packs/core` runtime script changes, so the pack version advances one patch step. | [`docs/product/changelog.md`](../../product/changelog.md) | Release surface | AC16 | A dated `[core]` heading names the version `packs/core/pack.toml` carries. |
| `current-architecture` | Not applicable: `docs/architecture/work-intake-and-artifact-routing.md` §10 pins a verified Core version, but this change alters nothing §10 describes — intake precedence, routing, and phase boundaries are untouched. Advancing its number would assert a whole-surface re-verification this delivery does not perform, and the `2.15.1` release set the same precedent by leaving it. | — | — | — | — |
| `user-documentation` | Not applicable: no published refusal code, guide table, or maintainer task changes. `record-invalid` and `unknown-timezone` keep their existing meanings and are already documented. | — | — | — | — |

## Boundaries

### Always do

- Refuse untrusted temporal input with a published code rather than an exception.
- Keep every seam that resolves a zone behind the same guard.
- Keep the code's numeric bounds equal to the published contract's.
- Bound and type-check input before handing it to a platform lookup that
  touches the filesystem.
- Regenerate the self-hosted projections of any `.apm/` file this change edits.

### Ask first

- Changing any published field, bound, pattern, or `x-spec` entry in the contract.
- Changing which refusal code an existing input shape produces.
- Widening this spec's objective beyond the `timezone` field.

### Never do

- Edit `docs/specs/thirty-day-cooling-and-retirement/spec.md` beyond a
  Status-line pointer; it is Shipped and frozen.
- Modify `surface_resolver.py` or `file_safety.py`.
- Add a timezone-validation module, a new store, resolver, fingerprint helper,
  dependency, scheduler, or deletion path.
- Widen a refusal into a fallback: no zone resolves to UTC or the system zone.
- Hand-edit a projected file; regenerate it.

## Testing Strategy

Unit tests in `tests/roster/test_thirty_day_cooling_and_retirement.py`, the
suite that already owns this module. Every criterion drives the shipped public
functions — `validate_payload`, `parse_record_bytes`, `compute_review_on`,
`is_due` — with a literal payload, never a mock seam.

That file already carries 43 `# STUB: AC<n>` markers belonging to the frozen
Wave 5 spec, so every marker this spec adds is disambiguated as
`# STUB: AC<n> (spec/cooling-untrusted-timezone-bound)`, the form already used
at `tools/assert-sast-chain-reachable.py:4`.

Two criteria replace the platform lookup rather than varying the input: AC5
counts calls to prove the bound fires *before* the lookup, and AC6 forces the
`OSError` arm directly so the bound cannot make it vacuous. Both substitute
`ZoneInfo` in the freshly-loaded module's namespace, and both assert all three
seams — a guard proven at one seam does not prove the other two.

Stub coverage at PLAN: 19 of 19 criteria carry a materialised red stub
(`stub: true` on every task). None is deferred to EXECUTE.

## Acceptance Criteria

### The timezone bound

- [ ] **AC1 — A `timezone` one character past the published bound refuses.** An
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
- [ ] **AC5 — The bound precedes the lookup at all three seams.** With
  `ZoneInfo` replaced by a counting spy, a 256-character `timezone` calls it
  zero times through each of `validate_payload`, `compute_review_on`, and
  `is_due`; a 255-character one calls it once through each.
- [ ] **AC6 — An `OSError` from the lookup escapes no seam.** With `ZoneInfo`
  replaced by one raising `OSError(63, "File name too long")` for `"UTC"`, and
  `timezone = "UTC"`: `validate_payload` returns `record-invalid`, and
  `compute_review_on` and `is_due` each return `unknown-timezone`.
- [ ] **AC7 — A non-string `timezone` refuses without reaching the lookup.** For
  each of `123`, `true`, `null`, `["UTC"]`, and `{"a": 1}`, `validate_payload`
  and `parse_record_bytes` return `record-invalid`, the counting spy records
  zero calls, and neither raises.
- [ ] **AC8 — The enumerated timezone corpus never raises.** For each of the ten
  `timezone` values in the plan's corpus table, `validate_payload` and
  `parse_record_bytes` return a `CoolingResult` whose `code` is a member of
  `REFUSAL_CODES`.
- [ ] **AC9 — A timezone refusal carries a code and no mutation.** For each of
  AC1–AC4's four results, `as_dict()` keys equal
  `{"due", "permission_granted", "mutated", "code"}` and `mutated` equals `()`.
- [ ] **AC10 — A resolvable timezone is unaffected.** `validate_payload` on an
  otherwise-valid payload with `timezone = "Asia/Singapore"` returns no code.

### Bounds that match the published contract

- [ ] **AC11 — The timezone bound equals the published one.**
  `cooling.MAX_TIMEZONE_LENGTH` equals `properties.timezone.maxLength` in
  `contracts/jsonschema/delivery-lifecycle-record.schema.json`.
- [ ] **AC12 — The published lower bound needs no mirrored constant.**
  `validate_payload` on a payload with `timezone = ""` returns `record-invalid`,
  so the contract's `minLength: 1` is left to the lookup by design.
- [ ] **AC13 — The locator bound equals the published one.**
  `cooling.MAX_LOCATOR_LENGTH` equals `$defs.locator.maxLength` in that same
  contract.
- [ ] **AC14 — The locator constant governs the guard.** With
  `cooling.MAX_LOCATOR_LENGTH` patched to `8` on a freshly loaded module, a
  9-character `locator` returns `record-invalid` and an 8-character one returns
  no code.
- [ ] **AC15 — The published contract is unchanged.** The schema file's SHA-256
  equals its value at this branch's merge base.

### Surfaces

- [ ] **AC16 — The release surfaces agree and advance.** `packs/core/pack.toml`
  and `packs/core/.claude-plugin/plugin.json` name the same version, a dated
  `[core]` changelog heading names it, and it is strictly greater than the merge
  base's `packs/core/pack.toml` version.
- [ ] **AC17 — The projections match their source.**
  `.claude/skills/close-work/scripts/cooling.py` and
  `.agents/skills/close-work/scripts/cooling.py` are byte-identical to
  `packs/core/.apm/skills/close-work/scripts/cooling.py`.
- [ ] **AC18 — The reused primitives stay byte-unchanged.** The SHA-256 of
  `surface_resolver.py` and of `file_safety.py` equal the values pinned in
  `tests/roster/test_close_work_extraction_and_immediate_disposition.py`, which
  passes with that file unedited.
- [ ] **AC19 — No dependency is added.** `pyproject.toml`,
  `packages/*/pyproject.toml`, and `tools/requirements.txt` are unchanged from
  the merge base.

## Follow-ons

Each is separately owned and outside this spec's criteria. Measurements and
control-flow traces live in the notes so the next spec does not re-derive them.

- **`_exception_is_valid` admits a payload that raises `KeyError`.**
  `cooling.py:218` gates on `set(value) < {"reason", "owner_role", "review_on"}`
  — a *proper subset* test — so any envelope carrying `evidence_ref` escapes it
  and falls through to a bare subscript. Four shapes raise `KeyError` from both
  `validate_payload` and `parse_record_bytes`; the published contract rejects
  all four. Measured and traced in
  [`notes/corpus-measurement.md`](notes/corpus-measurement.md). The repair is one
  operator — a superset test, the form `validate_payload` already uses at
  `cooling.py:240`. It is the same defect class as this spec's, on a different
  field, and including it would widen this spec's stated Objective: an owner
  scope decision, not the smallest change on this target.
- **Wave 5 finding 1 — refuted, not repaired.** The success payload's absolute
  `mutated` path. Evidence in [`notes/adjudication.md`](notes/adjudication.md).
  Residual observation: `CoolingResult.as_dict`'s "diagnostic-free" docstring
  claims more than the success path delivers.
- **Wave 5 finding 2 — refuted, not repaired.** The unpopped write grant in
  `_binding_is_issued`. Evidence in [`notes/adjudication.md`](notes/adjudication.md).
  Single-use write grants remain a defensible hardening with Wave 4 precedent as
  a blast-radius reduction for a leaked binding object. The unrecorded residual
  is different and larger: `_ISSUED_COORDINATION_AUTHORITIES` is never evicted on
  the write path, and `_binding_is_issued` linearly scans it on every write, so
  N resolved grants make each subsequent write O(N) and the dict grows unbounded
  for the process lifetime. Bounded retention — eviction and a cap — is what the
  per-write scan makes load-bearing.
- **Locator pattern divergence.** `_is_locator` (`cooling.py:161-166`) admits the
  C0 control range and `U+007F`, which the contract's `$defs/locator` pattern
  excludes; `_is_locator` rejects a `.` segment, which the pattern admits. AC13
  and AC14 pin only the numeric bound. The write path is unaffected — it binds
  on `delivery_id`, which is regex-bounded — so the reach is limited to the
  deletion path via `close_work._bounded_text`'s control-character refusal, and
  `verify_identity` usually refuses first with `locator-unresolved`.
  Reconciling the pattern changes behaviour and belongs to a spec that can decide
  which side is right.

## Assumptions

- `ZoneInfo` raises `OSError(ENAMETOOLONG)` — not `ZoneInfoNotFoundError` — when
  the key's final path component exceeds the filesystem's `NAME_MAX`.
  (measured 2026-08-28, CPython 3.13.13, darwin/APFS: `ZoneInfo("a" * 256)`
  raises `OSError(63, 'File name too long')` carrying an absolute `filename`;
  `ZoneInfo("Not/A/Zone")` raises `ZoneInfoNotFoundError` and `ZoneInfo("")`
  raises `ValueError`)
- `MAX_TIMEZONE_LENGTH` is a **code-point** bound, because JSON Schema
  `maxLength` and Python `len()` both count code points, while `NAME_MAX` counts
  bytes on some filesystems. It therefore does not eliminate `ENAMETOOLONG` for
  a multi-byte key inside the published bound. The `OSError` arm — not the bound
  — is the control for that residue, which is why AC6 asserts the arm at all
  three seams independently of AC5. (measured: `"é" * 200` is 200 code points
  and 400 bytes and resolves to `ZoneInfoNotFoundError` on APFS; `"é" * 300`
  raises `OSError`)
- `zoneinfo` is stdlib on the `>=3.11` floor both packages declare, so no
  manifest changes. (checked: AC19)
- Wave 5's spec is frozen, so its AC5 defect is repaired by this spec's criteria
  rather than by amending it. Wave 5's tests are not frozen and are extended
  here. (`docs/CONVENTIONS.md` § "A spec directory freezes as a unit")

## Changelog

- 2026-08-28: Opened. Three Wave 5 post-code review Concerns were adjudicated
  before any repair; one sustained and two refuted, all recorded in
  [`notes/adjudication.md`](notes/adjudication.md). Pre-EXECUTE adversarial and
  secure-design review returned 28 findings; the sustained ones widened AC5 and
  AC6 from one seam to three, added the non-string criterion, the corpus
  criterion, and the projection criterion, corrected the version step from minor
  to patch, and set `Contract:` to `none`. A 32-case corpus measured against the
  shipped module ([`notes/corpus-measurement.md`](notes/corpus-measurement.md))
  found a second defect of the same class in `_exception_is_valid`; it is
  recorded as a follow-on rather than built, because fixing it here would widen
  this spec's Objective.
