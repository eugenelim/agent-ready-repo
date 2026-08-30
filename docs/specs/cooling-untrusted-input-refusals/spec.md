# Spec: Cooling untrusted input refusals

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0096 §6; `thirty-day-cooling-and-retirement` (Shipped and frozen — this spec repairs its AC5 without editing that file at all)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer hands the cooling engine a lifecycle record that came from outside
the process. Where the hand-written validator is weaker than the published
contract, it now refuses with a named code instead of raising.

Two fields are repaired. An unresolvable `timezone` — malformed, non-string,
absent from the platform database, or longer than the contract permits — returns
a named refusal from every seam that resolves one. An `exception` envelope
missing a required key returns a named refusal from every seam that reads one,
including the two caller-facing review seams.

Nothing raises, so no host filesystem path or `errno` reaches the caller. The two
numeric bounds this spec names can no longer drift from the published contract
unnoticed.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| `interface-contract` | Applicable, read-only: the contract already declares the bound this spec makes the validator honour. No field, bound, or shape changes, so the `Contract:` header stays `none`. | [`contracts/jsonschema/delivery-lifecycle-record.schema.json`](../../../contracts/jsonschema/delivery-lifecycle-record.schema.json) | `thirty-day-cooling-and-retirement` retains sole `x-spec` ownership | AC11, AC13, AC15 | The file's bytes are unchanged and `x-spec` still names only Wave 5. |
| `decision-record` | Applicable: the schema-versus-code decision, the three adjudicated Wave 5 findings, and the measured corpus are the durable reasoning this delivery produces; all spec-local, so no new ADR. | [`notes/schema-decision.md`](notes/schema-decision.md), [`notes/adjudication.md`](notes/adjudication.md), [`notes/corpus-measurement.md`](notes/corpus-measurement.md) | This spec | The three notes exist and the Changelog cites them | Each note resolves and states its evidence. |
| `release-history` | Applicable: a shipped `packs/core` runtime script changes, so the pack version advances one patch step. | [`docs/product/changelog.md`](../../product/changelog.md) | Release surface | AC16 | A dated `[core]` heading names the version `packs/core/pack.toml` carries. |
| `current-architecture` | Not applicable: `docs/architecture/work-intake-and-artifact-routing.md` §10 pins a verified Core version, but this change alters nothing §10 describes — intake precedence, routing, and phase boundaries are untouched. Advancing its number would assert a whole-surface re-verification this delivery does not perform, and the `2.15.1` release set the same precedent by leaving it. | — | — | — | — |
| `user-documentation` | Not applicable: no published refusal code, guide table, or maintainer task changes. `record-invalid`, `unknown-timezone`, and `exception-envelope-invalid` keep their existing meanings and are already documented. | — | — | — | — |

## Boundaries

### Always do

- Refuse untrusted input with a published code rather than an exception,
  wherever the hand-written validator is weaker than the published contract.
- Keep every seam that resolves a zone behind the same guard, and every seam
  that reads an exception envelope behind the same predicate.
- Keep the code's numeric bounds equal to the published contract's.
- Bound and type-check input before handing it to a platform lookup that
  touches the filesystem.
- Regenerate the self-hosted projections of any `.apm/` file this change edits.

### Ask first

- Changing any published field, bound, pattern, or `x-spec` entry in the contract.
- Changing which refusal code an existing input shape produces.

### Never do

- Edit `docs/specs/thirty-day-cooling-and-retirement/spec.md` at all. It is
  Shipped and frozen, and `docs/CONVENTIONS.md` § "Superseding a frozen document"
  licenses only two Status-line shapes — a pointer to a superseding ADR, and a
  pointer recording that a `[backlog].open` anchor the body names was closed.
  This change produces no ADR and that spec names no anchor, so neither shape
  fits and the file is left untouched.
- Modify `surface_resolver.py` or `file_safety.py`.
- Add a timezone-validation module, a new store, resolver, fingerprint helper,
  dependency, scheduler, or deletion path.
- Widen a refusal into a fallback: no zone resolves to UTC or the system zone.
- Hand-edit a projected file; regenerate it.

## Testing Strategy

Unit tests in `tests/roster/test_thirty_day_cooling_and_retirement.py`, the
suite that already owns this module. Every criterion drives the shipped public
functions — `validate_payload`, `parse_record_bytes`, `compute_review_on`,
`is_due`, and for AC21 the two caller-facing seams `review` and
`review_exception` — with a literal payload, never a mock seam.

That file already carries 43 `# STUB: AC<n>` markers belonging to the frozen
Wave 5 spec, so every marker this spec adds is disambiguated as
`# STUB: AC<n> (spec/cooling-untrusted-input-refusals)`, the form already used
at `tools/assert-sast-chain-reachable.py:4`.

Two criteria replace the platform lookup rather than varying the input: AC5
counts calls to prove the bound fires *before* the lookup, and AC6 forces the
`OSError` arm directly so the bound cannot make it vacuous. Both substitute
`ZoneInfo` in the freshly-loaded module's namespace, and both assert all three
seams — a guard proven at one seam does not prove the other two.

**The `OSError` is only reachable where `tzdata` is importable.** `ZoneInfo`
reaches `OSError(ENAMETOOLONG)` only through `zoneinfo._common.load_tzdata`; when
the optional `tzdata` wheel is absent, `find_tzfile` swallows the `stat` error
and the lookup ends in `ZoneInfoNotFoundError`, which the shipped code already
catches. This repository declares `tzdata` nowhere, so a criterion that relies on
the platform producing `ENAMETOOLONG` proves nothing in CI. Detection therefore
rests on AC5 and AC6, which substitute `ZoneInfo` and hold in either
environment — never on AC1–AC4, which assert the contract rather than detect the
defect.

AC20 to AC22 cover the `exception` envelope. Unlike the timezone defect they are
red in every environment, because the escape is plain dict access rather than a
platform lookup.

Coverage — all 30 criteria are materialised and none is deferred.

Twenty-five were written at PLAN, before any implementation existed. Twenty of
those were red then; the other five are non-regression or consistency
invariants that held already and each carries a mutation proof in `plan.md`,
because a criterion that cannot fail proves nothing.

Four more — AC23 to AC26 — were added after post-GATES review found a second
escape class the PLAN-time corpus had missed: a membership test against an
untrusted value. JSON admits lists and dicts, both unhashable, so
`value in {...}` raised `TypeError`. Each of the four was red against the code
as it then stood.

Measured now: **214 cases pass, none fail, identically with `tzdata` importable
and with it blocked.** Running both matters, because the `OSError` this repairs
only arises when the optional `tzdata` wheel is importable, and this repository
declares it nowhere. A single-environment green run would prove nothing about
that half of the fix; detection rests on AC5, AC6, and AC6a, which substitute
`ZoneInfo` and hold either way.

## Acceptance Criteria

### The timezone bound

- [x] **AC1 — A `timezone` one character past the published bound refuses.** An
  otherwise-valid payload whose `timezone` is 256 `a` characters returns
  `code = "record-invalid"` from `validate_payload`, and raises nothing.
- [x] **AC2 — The bytes seam refuses the same payload.** `parse_record_bytes` on
  that payload's canonical JSON encoding returns `code = "record-invalid"`, and
  raises nothing.
- [x] **AC3 — `compute_review_on` names the timezone refusal.**
  `compute_review_on(date(2026, 8, 1), "a" * 256)` returns a `CoolingResult`
  whose `code` is `unknown-timezone`.
- [x] **AC4 — `is_due` names the timezone refusal.** A record carrying
  `timezone = "a" * 256`, given an aware instant, returns
  `code = "unknown-timezone"`.
- [x] **AC5 — The bound precedes the lookup at all three seams.** With
  `ZoneInfo` replaced by a counting spy, a 256-character `timezone` calls it
  zero times through each of `validate_payload`, `compute_review_on`, and
  `is_due`; a 255-character one calls it once through each.
- [x] **AC6 — An `OSError` from the lookup escapes no seam.** With `ZoneInfo`
  replaced by one raising `OSError(63, "File name too long")` for `"UTC"`, and
  `timezone = "UTC"`: `validate_payload` returns `record-invalid`, and
  `compute_review_on` and `is_due` each return `unknown-timezone`.
- [x] **AC6a — The catch set is exactly the three named classes.** The `except`
  handler guarding the zone lookup names `ZoneInfoNotFoundError`, `OSError`, and
  `ValueError` and nothing else, asserted over `cooling.py`'s AST. A bare
  `except Exception` would satisfy every other criterion while turning a future
  `TypeError` or `AttributeError` inside the lookup into `record-invalid`.
- [x] **AC7 — A non-string `timezone` refuses without reaching the lookup.** For
  each of `123`, `true`, `null`, `["UTC"]`, and `{"a": 1}`: `validate_payload`,
  `parse_record_bytes`, and `compute_review_on` refuse — `record-invalid` from
  the first two, `unknown-timezone` from the third — with the counting spy
  recording zero calls, and none raises. `is_due` is excluded by construction:
  `CoolingRecord.from_payload` coerces `timezone` with `str()` at
  `cooling.py:106`, so a record's `timezone` is always a string and that seam
  cannot observe the original type.
- [x] **AC8 — The enumerated timezone corpus never raises.** For each of the
  eleven `timezone` values in the plan's corpus table, `validate_payload` and
  `parse_record_bytes` return a `CoolingResult` whose `code` is a member of
  `REFUSAL_CODES`.
- [x] **AC9 — A timezone refusal carries a code and nothing else.** For each of
  AC1–AC4's four results **and each of AC6's three**, `as_dict()` equals
  `{"due": False, "permission_granted": False, "mutated": (), "code": <the
  seam's code>}` — no `record` key — and none raises. AC6's results are the
  ones produced from a real `OSError`, so they are the ones that could carry an
  errno or a host path.
- [x] **AC10 — A resolvable timezone is unaffected.** `validate_payload` on an
  otherwise-valid payload with `timezone = "Asia/Singapore"` returns no code.

### The exception envelope

- [x] **AC20 — An incomplete envelope refuses instead of raising.** Of the
  sixteen envelope shapes, eight carry the permitted `evidence_ref` and so fell
  through the old proper-subset gate; seven of those omit a required key. For
  each of those seven, a `retain-exception` payload returns `record-invalid`
  from `validate_payload` and from `parse_record_bytes`, and raises nothing.
- [x] **AC21 — The caller-facing review seams refuse it too.** Given the
  `{reason, owner_role, evidence_ref}` envelope and a due record, `review` with
  six `refuse` answers returns `exception-envelope-invalid`, and
  `review_exception` with `outcome = "renew"` and that envelope in the
  attestation returns `exception-envelope-invalid`. Neither raises.
- [x] **AC22 — A complete envelope is still accepted.** A `retain-exception`
  payload whose `exception` carries `reason`, `owner_role`, and `review_on`
  returns no code from `validate_payload`, both with and without an
  `evidence_ref`.

### Untrusted values where a scalar belongs

- [x] **AC23 — A container where a scalar belongs refuses.** For each required
  field other than `aliases`, and for each of `["x"]` and `{"a": 1}`,
  `validate_payload` and `parse_record_bytes` return a code in `REFUSAL_CODES`,
  and neither raises. `aliases` is excluded because the contract publishes
  `"type": "array"` for it; its own shape is asserted separately.
- [x] **AC24 — A container in the exception envelope refuses.** For each of
  `reason`, `owner_role`, `review_on`, and `evidence_ref`, and for each of the
  same two containers, both seams return a code in `REFUSAL_CODES`.
- [x] **AC25 — The caller-supplied enums refuse a container.** `enrol` with
  `completion_event = ["merge"]` returns `completion-event-required`, and
  `review` with a check answer of `["refuse"]` returns `review-incomplete`.
  Neither raises.
- [x] **AC27 — A non-string `delivery_id` refuses.** For each of `123`, `0`,
  `1.5`, and `true`, `validate_payload` and `parse_record_bytes` return
  `record-invalid`. AC23's containers cannot cover this: `str(["x"])` fails the
  pattern with or without the type guard, so only a scalar that survives `str()`
  discriminates.
- [x] **AC26 — The alias bound equals the published one.**
  `cooling.MAX_ALIAS_COUNT` equals `properties.aliases.maxItems`, and with the
  constant patched to `2` a three-element `aliases` returns `record-invalid`
  while a two-element one returns no code.

### Bounds that match the published contract

- [x] **AC11 — The timezone bound equals the published one.**
  `cooling.MAX_TIMEZONE_LENGTH` equals `properties.timezone.maxLength` in
  `contracts/jsonschema/delivery-lifecycle-record.schema.json`.
- [x] **AC11a — The timezone constant governs the guard.** With
  `cooling.MAX_TIMEZONE_LENGTH` patched to `8` on a freshly loaded module, a
  9-character `timezone` is refused without a lookup at each of
  `validate_payload`, `compute_review_on`, and `is_due`, and an 8-character one
  reaches the lookup once at each. Numbered `11a` because it pairs with AC11;
  renumbering the list would invalidate references the notes already carry.
- [x] **AC12 — The published lower bound needs no mirrored constant.**
  `validate_payload` on a payload with `timezone = ""` returns `record-invalid`,
  so the contract's `minLength: 1` is left to the lookup by design.
- [x] **AC13 — The locator bound equals the published one.**
  `cooling.MAX_LOCATOR_LENGTH` equals `$defs.locator.maxLength` in that same
  contract.
- [x] **AC14 — The locator constant governs the guard.** With
  `cooling.MAX_LOCATOR_LENGTH` patched to `8` on a freshly loaded module, a
  9-character `locator` returns `record-invalid` and an 8-character one returns
  no code.
- [x] **AC15 — The published contract is unchanged.** The schema file's SHA-256
  equals its value at this branch's merge base.

### Surfaces

- [x] **AC16 — The release surfaces agree and advance past the merge base.**
  `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` name the
  same version, the topmost dated `[core]` changelog heading names it, and it is
  strictly greater than the merge base's `packs/core/pack.toml` version, which
  the test pins as a literal. Comparing against the changelog's previous heading
  instead would pass with no bump at all, because the merge base already carries
  the topmost heading's version.
- [x] **AC17 — The projections match their source.**
  `.claude/skills/close-work/scripts/cooling.py` and
  `.agents/skills/close-work/scripts/cooling.py` are byte-identical to
  `packs/core/.apm/skills/close-work/scripts/cooling.py`.
- [x] **AC18 — The reused primitives stay byte-unchanged.** The SHA-256 of
  `surface_resolver.py` and of `file_safety.py` equal the values pinned in
  `tests/roster/test_close_work_extraction_and_immediate_disposition.py`, which
  passes with that file unedited.
- [x] **AC18a — The spec is indexed and registered.** `docs/specs/README.md`
  carries a row whose link resolves to this spec, and `workspace.toml` carries an
  entry for it in the room matching its Status.
- [x] **AC19 — No dependency is added.** `pyproject.toml`,
  `packages/*/pyproject.toml`, and `tools/requirements.txt` are unchanged from
  the merge base.

## Follow-ons

Each is outside this spec's criteria. Measurements and control-flow traces live
in the notes so the next spec does not re-derive them. Every entry is owned by
`eugenelim` as the `close-work` surface owner, and none has a work-intake
artifact yet — the work-loop's DECIDE step forbids creating one by default for
work this loop did not include, so the owner registers them through
`work-intake` if and when they are picked up.

The `_exception_is_valid` defect that used to head this list is no longer here:
the owner widened the scope on 2026-08-29 and it is built, under AC20 to AC22.

- **`delivery_id` accepts a non-string the contract forbids.** `cooling.py:246`
  matches `_DELIVERY_ID_RE.fullmatch(str(payload["delivery_id"]))`, coercing
  before matching, so `{"delivery_id": 123}` validates clean and becomes
  `"123"` — which is then the on-disk filename (`:477`) and the authority
  binding's `resource` (`:551`). The contract declares
  `{"type": "string", ...}`. Not exploitable today, since `str()` of a
  non-negative integer is filename-safe and the binding compares the coerced
  value on both sides, but it is the same class on the field with the widest
  downstream reach. The sibling coercions at `:207`, `:209`, `:226`, `:230`,
  `:258-259`, and `:270` are inert: their regexes are anchored on literals no
  numeric coercion can produce.
- **A `_close_work()` failure escapes four functions uncaught.** `enrol`
  (`:679`) and `load_record` (`:692`) wrap the dependency; `verify_identity`
  resolves it outside its own `try` (`:378`), `deletion_allowed` calls
  `verify_identity` bare (`:424`), `_binding_is_issued` resolves it (`:496`)
  from `_write_record` before that function's `try` opens (`:554`), and
  `update_record` (`:723`) wraps nothing — so the failure propagates out of
  `review()` and `review_exception()`. The outcome is fail-closed, but the
  observable is a traceback carrying the absolute paths of both `cooling.py` and
  `close_work.py` from the permission-granting seam.
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
- **Locator pattern divergence.** `_is_locator` (`cooling.py:167-172`) admits the
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
  the key's final path component exceeds the filesystem's `NAME_MAX`, **and the
  optional `tzdata` wheel is importable**. Without `tzdata`, `find_tzfile`
  swallows the `stat` error and the lookup ends in `ZoneInfoNotFoundError`.
  (measured 2026-08-28, CPython 3.13.13, darwin/APFS: `ZoneInfo("a" * 256)`
  raises `OSError(63, 'File name too long')` carrying an absolute `filename`
  with `tzdata` present, and `ZoneInfoNotFoundError` with it blocked;
  `ZoneInfo("Not/A/Zone")` raises `ZoneInfoNotFoundError` and `ZoneInfo("")`
  raises `ValueError` in both)
- The defect is still worth repairing despite that contingency, because this is
  a published pack that adopters run in their own environments. `tzdata` is a
  common transitive dependency — `arrow` requires it unconditionally, and
  `pandas`, `Faker`, `pydantic[timezone]`, and `babel` require it on Windows —
  and on Windows `zoneinfo` has no system `TZPATH`, so `tzdata` is effectively
  mandatory for any zone to resolve at all. (checked: `importlib.metadata`
  requirement scan in this tree; `.github/workflows/build-check-windows.yml`)
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

- 2026-08-29: Scope widened by the owner. The `_exception_is_valid`
  proper-subset defect moves from a recorded follow-on into this spec's criteria
  as AC20 to AC22, and the spec is renamed from
  `cooling-untrusted-timezone-bound` to match what it now covers. Both repairs
  are the same class — a hand-written validator weaker than the published
  contract, failing by exception rather than by refusal code — so the Objective
  now names the class rather than one field.
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
