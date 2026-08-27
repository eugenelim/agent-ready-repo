# Plan: Thirty-day cooling and retirement

- **Spec:** [spec.md](spec.md)
- **Status:** Drafting
- **Repository anchors:** `docs/rfc/0096-portable-delivery-artifact-lifecycle.md`
  at `6e984d67b583b36798efddbb2717ce5784572a49` owns cooling policy;
  `docs/architecture/work-intake-and-artifact-routing.md` owns implemented phase
  boundaries; `packs/core/.apm/skills/close-work/scripts/close_work.py` is the
  analogous production implementation for bounded records, authority bindings,
  and confirmed effects, with `tests/roster/test_close_work_extraction_and_immediate_disposition.py`
  as its analogous test; `packs/core/.apm/skills/work-intake/scripts/surface_resolver.py`
  and `packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py` own the
  shipped resolution and confinement primitives and are unchanged here;
  `contracts/jsonschema/semantic-surface-resolution.schema.json` is the analogous
  published contract. Named deviation: no repository surface owns
  delivery-lifecycle state, so RFC §4 rung 6 applied and the owner selected
  `docs/specs/<slug>/lifecycle.json` as the adjacent record.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document may change while Drafting. After approval, Phase 1 treats substantive
> plan changes as a re-plan requiring a new review and approval.

## Approach

Land Wave 5 as five dependency-ordered review units. The first three build the
engine bottom-up — pure date arithmetic, then persistence, then identity — so
each unit is independently reviewable and leaves the repository working. The
fourth composes them into the day-30 review decision. The fifth closes doctrine,
the five current-behaviour pointers, release metadata, and every projection.

The whole engine is three operations: compute a date, persist a bounded record,
answer whether a record is due. Everything else is refusal. There is no
scheduler, no daemon, no background job, and no wake-up hook: a human invokes
`close-work` and asks. Deletion is not implemented here at all — an approved
retirement calls Wave 4's `preview_deletion`, `confirm_deletion`, and
`apply_confirmed_deletion` with no change to those seams.

Two design rules carry most of the correctness. First, the clock is always an
argument: no module in this wave imports a wall-clock call, so DST, foreign
readers, leap days, and day-boundary cases are ordinary table tests rather than
timing-dependent ones. Second, `review_on` is date arithmetic
(`completed_on + timedelta(days=30)`), not interval arithmetic, so a DST
transition inside the window cannot move it — the tests assert that property
rather than asserting a wall-clock offset.

Identity is the logical delivery ID plus the content fingerprint from
`file_safety.sha256_confined_regular_file`. Nothing in this wave reads Git.
The identity fixtures therefore build real repositories and perform a real
squash merge, merge commit, rebase, and shallow clone, and a fifth fixture
deletes `.git` outright — a mocked Git could not testify to the property being
claimed.

The new module is `cooling.py`, a sibling of `close_work.py` inside the
`close-work` skill rather than an addition to that 2,400-line module, so the
wave's seams are independently importable and testable. It reuses
`close_work.py`'s existing `file_safety()` and `surface_resolver()` sibling
loaders and its authority-binding shape; it introduces no second resolver, no
second fingerprint helper, and no third safety primitive.

`surface_resolver.py` and `file_safety.py` are byte-unchanged, so
`EXPECTED_RESOLVER_SHA256` and `EXPECTED_FILE_SAFETY_SHA256` in the Wave 4
roster test must still pass without edits. If either digest moves, that is a
defect in this wave, not a pin to re-cut.

Anchor tests identified before EXECUTE: `tests/roster/test_wave4_durable_outputs_and_release.py`
pins the core pack version literal in three places and asserts three
whitespace-normalised Wave 4 doctrine sentences; `tools/test_local_ci_shared_test_deduplication.py`
pins node-ID digests for three core lint files, none of which this wave touches;
`tools/test_workspace_status.py` pins a work-loop `SKILL.md` contract hash, and
this wave does not edit that file. New assertion strings added to doctrine
surfaces must not wrap across a line, because the roster checks are
whitespace-normalised line-independent but the pointer checks are not.

`packs/core/.apm/skills/close-work/SKILL.md` is projected into `.claude/` and
`.agents/`, so it must not cite `contracts/` or any other repository-only path;
the published schema is named in the spec and the architecture document instead.
Projections are regenerated with `env FORCE=1 make build-self` and never
hand-authored.

## Design

### The record

`docs/specs/<slug>/lifecycle.json`, one record per delivery artifact, resolved
through the Wave 1 resolver for the `runtime-coordination` role and confined to
the repository root. The published field set lives in
`contracts/jsonschema/delivery-lifecycle-record.schema.json`:

| Field | Meaning |
| --- | --- |
| `schema` | `delivery-lifecycle-record.v1` |
| `delivery_id` | Logical ID; never a commit, branch, or tag |
| `locator` | Current repository-relative locator |
| `aliases` | Prior locators retained across renames |
| `fingerprint` | `sha256:<hex>` of the artifact's content |
| `disposition` | `cool-30-days`, `retain-exception`, or `retired` |
| `completion_event` | Selected delivery-completion event kind |
| `completion_evidence_ref` | Bounded reference to that evidence |
| `completed_on` | ISO date of the selected event |
| `timezone` | IANA key recorded with the event |
| `review_on` | ISO date, `completed_on` plus thirty days |
| `authority` | Independent `source`, `write`, `delete` facts |
| `confirmation_proof` | Non-personal proof of enrolment confirmation |
| `exception` | Present only for `retain-exception`: `reason`, `owner_role`, `review_on` |

Any other key refuses the write. Requirements text, personal identity, and
rationale are refused by the same closed-key rule plus the bounded-text checks
already used by `close_work.py`.

Writes are a whole-record atomic `os.replace` of one id-keyed file. No lock is
introduced: distinct records never share a file, and a same-record concurrent
write is a whole-record last-writer-wins rather than a torn read, so no lock is
needed to prevent data loss.

### Refusal codes

`completion-event-required`, `not-delivered`, `lifecycle-state-unwritable`,
`unsafe-target`, `record-invalid`, `naive-clock`, `unknown-timezone`,
`not-due`, `review-incomplete`, `fingerprint-drift`, `locator-unresolved`,
`missing-history`, `authority-uncertain`, `exception-envelope-invalid`.

## Tasks

### Task 1 — Contract, record shape, and date arithmetic

**ACs:** AC1, AC2, AC3, AC4, AC5, AC6, AC7, AC8, AC12, AC13.
**Verification mode:** TDD.
**Depends on:** none.

**Tests:** `tests/roster/test_thirty_day_cooling_and_retirement.py` — a table
over `compute_review_on` and `is_due` covering: a plain window; a window
containing a spring-forward and one containing a fall-back in the recorded zone,
both equal to the plain window's offset; three readers in different local zones
agreeing on dueness for one instant; a window spanning 29 February; days 29, 30,
and 31 either side of local midnight in the recorded zone; a `completed_on`
forty days in the past yielding an immediately-due record; a due record carrying
no permission and an empty mutation trace; a naive `now` refusing with
`naive-clock`; an unknown IANA key refusing with `unknown-timezone`; a record
with an extra key refusing with `record-invalid`; and a record carrying
requirement text, an email-shaped string, or a `rationale` key refusing with
zero effects. Plus a static check that no Wave 5 module names a wall-clock call.

**Approach:** write `contracts/jsonschema/delivery-lifecycle-record.schema.json`
and the `CoolingRecord` dataclass, strict parse, and closed-key serialise in
`packs/core/.apm/skills/close-work/scripts/cooling.py`. `compute_review_on` is
date arithmetic; `is_due` converts the injected aware instant into the recorded
zone and compares dates.

### Task 2 — Enrolment, persistence, and fail-closed state

**ACs:** AC9, AC10, AC11, AC14, AC15, AC24.
**Verification mode:** TDD.
**Depends on:** Task 1.

**Tests:** enrolment refuses undelivered, unclosed, and non-persistent work;
refuses with `completion-event-required` when no event was selected; refuses for
each of creation, Ready, an edit, and session end; refuses with
`lifecycle-state-unwritable` for an absent, unconfined, read-only, or
symlink-escaping resolved destination; re-derives an externally supplied
fingerprint and re-checks an externally supplied timezone and authority fact
before persisting, refusing on mismatch; and writes then reloads a record in a
separate interpreter process, asserting field equality and that `workspace.toml`
is unchanged.

**Approach:** `enrol()` validates the resolved surface through the Wave 1
resolver exactly as `close_work._resolved_surface` does, binds authority with
the existing binding shape, and performs the atomic write. `load_record()`
strict-parses. Reuse `close_work.py`'s `file_safety()` and `surface_resolver()`
loaders rather than adding new ones.

### Task 3 — Identity across history shapes and deletion blockers

**ACs:** AC16, AC17, AC18, AC19.
**Verification mode:** TDD with real Git fixtures.
**Depends on:** Task 2.

**Tests:** five fixture repositories built with real `git` — squash merge, merge
commit, rebase, `--depth=1` shallow clone, and one with `.git` deleted — each
verifying the same logical artifact's identity. A rename asserts the new locator
and the retained alias. Four blocker cases assert distinct codes for missing
history, fingerprint drift, an unresolved reference, and uncertain authority. One
case asserts that source authority over an external spec with absent deletion
authority still blocks. Fixtures skip, loudly, only if `git` is unavailable.

**Approach:** `verify_identity()` re-resolves the locator or an alias and
recomputes the fingerprint via `file_safety.sha256_confined_regular_file`.
`record_rename()` returns a new record with the prior locator appended to
`aliases`. `deletion_blocked()` returns the first applicable code or `None`.

### Task 4 — Day-30 review, retirement, and exceptions

**ACs:** AC20, AC21, AC22, AC23.
**Verification mode:** TDD.
**Depends on:** Task 3.

**Tests:** review before `review_on` refuses `not-due`; each of the six rechecks
missing individually refuses `review-incomplete`; all-approve returns `Retired`;
each refusal and each `uncertain` answer returns a `retain-exception` record with
reason, owner role, and a human-supplied review date, and an exception missing
any of the three refuses `exception-envelope-invalid`. A module-level assertion
proves no Wave 5 seam calls `os.unlink`, `os.remove`, `Path.unlink`, or
`shutil.rmtree`, and an integration case shows an approved retirement calling
Wave 4's `preview_deletion` unchanged.

**Approach:** `review()` takes the record, a closed `ReviewChecks` mapping, and
the injected instant, and returns one outcome. No effect is performed.

### Task 5 — Doctrine, pointers, release, and projections

**ACs:** AC25, AC26, AC27.
**Verification mode:** Goal-based plus visual/manual QA.
**Depends on:** Task 4.

**Tests:** `EXPECTED_RESOLVER_SHA256` and `EXPECTED_FILE_SAFETY_SHA256` still
pass unedited; a check that no runtime dependency was added; the amended
`test_wave4_docs_do_not_claim_later_wave_engines`, which drops the two
Wave-5-owned sentences, keeps the Wave 6/7 boundary sentence, and adds the
Wave 5 statement; and per-pointer assertions for the five files. Manual QA:
invoke `close-work` on one shipped artifact, record the enrolment, the due
answer, and one day-30 review outcome.

**Approach:** update `packs/core/.apm/skills/close-work/SKILL.md`,
`docs/architecture/work-intake-and-artifact-routing.md`, and the five pointers;
amend `tests/roster/test_wave4_durable_outputs_and_release.py` (three version
literals and the doctrine-sentence set) rather than deleting it; bump
`packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` to `2.14.0`
and add the topmost dated `## [core][2.14.0]` changelog heading; regenerate with
`env FORCE=1 make build-self`.

## Verification

`make lint-ruff`, `make lint-mypy`, `SKIP_SAST=1 make build-check`, `make test`,
`make sast`, `make site-link-check`, `npm test --prefix web`, and — for the
emitted-changelog test — `python3 tools/build-site.py && npm run build --prefix web
&& npm run build --prefix docs-site`.

Every new guard in this wave carries a mutation proof: the property is made
false in the source, the guard is run and observed to fail, the source is
restored, and the restoration is confirmed byte-identical.

## Risks

- The lifecycle record lives inside the directory cooling may eventually retire.
  Retirement therefore removes `spec.md`, `plan.md`, and `lifecycle.json` in one
  Wave 4 confirmed file set; a partial deletion leaves an orphan record, so the
  blocker set treats an unresolved locator as blocking rather than as retirable.
- A pack version bump reddens three literals in the Wave 4 roster test. They are
  updated in Task 5, not weakened.
