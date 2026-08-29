# Spec: Cooling untrusted timezone bound

- **Status:** Draft
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

**The `OSError` is only reachable where `tzdata` is importable.** `ZoneInfo`
reaches `OSError(ENAMETOOLONG)` only through `zoneinfo._common.load_tzdata`; when
the optional `tzdata` wheel is absent, `find_tzfile` swallows the `stat` error
and the lookup ends in `ZoneInfoNotFoundError`, which the shipped code already
catches. This repository declares `tzdata` nowhere, so a criterion that relies on
the platform producing `ENAMETOOLONG` proves nothing in CI. Detection therefore
rests on AC5 and AC6, which substitute `ZoneInfo` and hold in either
environment — never on AC1–AC4, which assert the contract rather than detect the
defect.

Stub coverage at PLAN — all 21 criteria are materialised, none deferred to
EXECUTE, and the split is measured, not claimed:

- **Red in both environments (8):** AC5, AC6, AC7, AC11, AC11a, AC13, AC14,
  AC16. These are the detectors: each fails whether or not `tzdata` is present.
- **Red only where `tzdata` is importable (5):** AC1, AC2, AC3, AC4, AC9, plus
  two of AC8's eleven rows. AC7 contributes 5 failing cases and AC8 contributes
  2 of its 11. Measured: 14 failures with `tzdata` present, 9 with it blocked.
- **Green by construction (4):** AC10, AC12, AC15, AC17 — non-regression
  invariants that hold today and must keep holding. Each carries a mutation
  proof in `plan.md`, because a criterion that cannot fail proves nothing.
- **Goal-based (3):** AC18, AC18a, AC19 — a named command, no test file.

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
- [ ] **AC7 — A non-string `timezone` refuses without reaching the lookup, at
  every seam.** For each of `123`, `true`, `null`, `["UTC"]`, and `{"a": 1}`:
  `validate_payload` and `parse_record_bytes` return `record-invalid`,
  `compute_review_on` and `is_due` return `unknown-timezone`, the counting spy
  records zero calls, and none raises.
- [ ] **AC8 — The enumerated timezone corpus never raises.** For each of the ten
  `timezone` values in the plan's corpus table, `validate_payload` and
  `parse_record_bytes` return a `CoolingResult` whose `code` is a member of
  `REFUSAL_CODES`.
- [ ] **AC9 — A timezone refusal carries a code and nothing else.** For each of
  AC1–AC4's four results **and each of AC6's three**, `as_dict()` equals
  `{"due": False, "permission_granted": False, "mutated": (), "code": <the
  seam's code>}` — no `record` key — and none raises. AC6's results are the
  ones produced from a real `OSError`, so they are the ones that could carry an
  errno or a host path.
- [ ] **AC10 — A resolvable timezone is unaffected.** `validate_payload` on an
  otherwise-valid payload with `timezone = "Asia/Singapore"` returns no code.

### Bounds that match the published contract

- [ ] **AC11 — The timezone bound equals the published one.**
  `cooling.MAX_TIMEZONE_LENGTH` equals `properties.timezone.maxLength` in
  `contracts/jsonschema/delivery-lifecycle-record.schema.json`.
- [ ] **AC11a — The timezone constant governs the guard.** With
  `cooling.MAX_TIMEZONE_LENGTH` patched to `8` on a freshly loaded module, a
  9-character `timezone` is refused without a lookup at each of
  `validate_payload`, `compute_review_on`, and `is_due`, and an 8-character one
  reaches the lookup once at each. Numbered `11a` because it pairs with AC11;
  renumbering the list would invalidate references the notes already carry.
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

- [ ] **AC16 — The release surfaces agree and advance past the merge base.**
  `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` name the
  same version, the topmost dated `[core]` changelog heading names it, and it is
  strictly greater than the merge base's `packs/core/pack.toml` version, which
  the test pins as a literal. Comparing against the changelog's previous heading
  instead would pass with no bump at all, because the merge base already carries
  the topmost heading's version.
- [ ] **AC17 — The projections match their source.**
  `.claude/skills/close-work/scripts/cooling.py` and
  `.agents/skills/close-work/scripts/cooling.py` are byte-identical to
  `packs/core/.apm/skills/close-work/scripts/cooling.py`.
- [ ] **AC18 — The reused primitives stay byte-unchanged.** The SHA-256 of
  `surface_resolver.py` and of `file_safety.py` equal the values pinned in
  `tests/roster/test_close_work_extraction_and_immediate_disposition.py`, which
  passes with that file unedited.
- [ ] **AC18a — The spec is indexed and registered.** `docs/specs/README.md`
  carries a row whose link resolves to this spec, and `workspace.toml` carries an
  entry for it in the room matching its Status.
- [ ] **AC19 — No dependency is added.** `pyproject.toml`,
  `packages/*/pyproject.toml`, and `tools/requirements.txt` are unchanged from
  the merge base.

## Follow-ons

Each is outside this spec's criteria. Measurements and control-flow traces live
in the notes so the next spec does not re-derive them. Every entry is owned by
`eugenelim` as the `close-work` surface owner, and none has a work-intake
artifact yet — the work-loop's DECIDE step forbids creating one by default for
work this loop did not include, so the owner registers them through
`work-intake` if and when they are picked up.

The first entry is the one this delivery most recommends for an owner decision:
it is measured, live in every environment, and one operator to repair.

- **`_exception_is_valid` admits a payload that raises `KeyError` — the largest
  residual, and the one most worth an owner decision.** `cooling.py:218` gates on
  `set(value) < {"reason", "owner_role", "review_on"}` — a *proper subset* test —
  so any envelope carrying `evidence_ref` escapes it and falls through to a bare
  subscript. Four shapes raise `KeyError` from **four** seams, not two:
  `validate_payload` and `parse_record_bytes`, and also the caller-facing
  `review()` (`cooling.py:759`, envelope supplied as the `exception` argument)
  and `review_exception(outcome="renew")` (`:815`, envelope taken from the
  attestation) — 20 of 80 seam-cases. Unlike this spec's subject the defect is
  **not** environment-contingent: it is plain dict access, so it is live in CI
  and everywhere else. The escaping traceback carries `cooling.py`'s absolute
  host path. The published contract rejects all four shapes
  (`$defs/exception` `required`). Measured and traced in
  [`notes/corpus-measurement.md`](notes/corpus-measurement.md). The repair is one
  operator — a superset test, the form `validate_payload` already uses at
  `cooling.py:240`. It is the same defect class as this spec's, on a different
  field, so including it would widen this spec's stated Objective: an owner
  scope decision, not the smallest change on this target.
- **`delivery_id` accepts a non-string the contract forbids.** `cooling.py:246`
  matches `_DELIVERY_ID_RE.fullmatch(str(payload["delivery_id"]))`, coercing
  before matching, so `{"delivery_id": 123}` validates clean and becomes
  `"123"` — which is then the on-disk filename (`:443`) and the authority
  binding's `resource` (`:517`). The contract declares
  `{"type": "string", ...}`. Not exploitable today, since `str()` of a
  non-negative integer is filename-safe and the binding compares the coerced
  value on both sides, but it is the same class on the field with the widest
  downstream reach. The sibling coercions at `:207`, `:209`, `:226`, `:230`,
  `:258-259`, and `:270` are inert: their regexes are anchored on literals no
  numeric coercion can produce.
- **A `_close_work()` failure escapes four functions uncaught.** `enrol`
  (`:645`) and `load_record` (`:658`) wrap the dependency; `verify_identity`
  resolves it outside its own `try` (`:345`), `deletion_allowed` calls
  `verify_identity` bare (`:390`), `_binding_is_issued` resolves it (`:464`)
  from `_write_record` before that function's `try` opens (`:520`, `:524`), and
  `update_record` (`:689`) wraps nothing — so the failure propagates out of
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
