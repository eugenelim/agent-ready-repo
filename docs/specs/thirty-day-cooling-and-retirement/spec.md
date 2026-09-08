# Spec: Thirty-day cooling and retirement

- **Status:** Shipped (superseded in part by ADR-0105 — AC22's transition table now includes the retained-to-Reclassified edge; everything else stands)
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0096 §6 and §9; `close-work-extraction-and-immediate-disposition` (Shipped, live dependency); `semantic-surface-resolver` (Shipped)
- **Brief:** none
- **Discovery:** none
- **Contract:** [`contracts/jsonschema/delivery-lifecycle-record.schema.json`](../../../contracts/jsonschema/delivery-lifecycle-record.schema.json)
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer enrols one delivered, closed delivery artifact into a thirty-day
cooling period; thirty days later a human invokes `close-work` and reviews it.
The engine is three operations — compute a date, persist a bounded record,
answer whether a record is due — and every other path is a refusal with a named
code. Being due authorizes nothing: day 30 never auto-deletes, and an approved
deletion runs through Wave 4's unchanged seams.

The acceptance criteria below are the contract. Each names an input and the
exact observable it must produce.

## Durable Outputs

| Semantic role | Applicability and resolved destination | Owner and closeout evidence |
| --- | --- | --- |
| `decision-record` | Applicable: [`docs/rfc/0096-portable-delivery-artifact-lifecycle.md`](../../rfc/0096-portable-delivery-artifact-lifecycle.md) at `6e984d67b583b36798efddbb2717ce5784572a49` | The accepted RFC owns cooling policy and rationale; Wave 5 adds no ADR. Closeout verifies the pin. |
| `interface-contract` | Applicable, new exact target: [`contracts/jsonschema/delivery-lifecycle-record.schema.json`](../../../contracts/jsonschema/delivery-lifecycle-record.schema.json) | Owns the persistent record's field set, its bounds at every level, and the excluded fields. Closeout verifies the shipped writer and reader validate against it and that it carries `x-spec`. |
| `runtime-coordination` | Applicable, new exact target: `docs/lifecycle/` with its `README.md` | Owns the destination this repository resolves for cooling records. Closeout verifies the directory is the confirmed candidate and that no other writer touches it. |
| `current-architecture` | Applicable: [`docs/architecture/work-intake-and-artifact-routing.md`](../../architecture/work-intake-and-artifact-routing.md) | Owns where cooling state lives, who may write it, and the Wave 6/7 boundary. Closeout requires a whole-surface read against shipped behaviour, including its "Last verified surface" section. |
| `user-documentation` (how-to) | Applicable: [`guides/core/how-to/close-and-disposition-work.md`](../../../guides/core/how-to/close-and-disposition-work.md) | Owns the maintainer's enrol, check-due, and day-30 review task. Closeout verifies the `cool-30-days` row no longer claims classification only. |
| `user-documentation` (reference) | Applicable: [`guides/core/reference/work-intake-routing-and-lifecycle.md`](../../../guides/core/reference/work-intake-routing-and-lifecycle.md) | Owns the public disposition-result table and the remaining Wave 6/7 boundary. Closeout verifies the table header and the `cool-30-days` row. |
| `user-documentation` (workspace reference) | Applicable: [`guides/core/reference/workspace-toml-schema.md`](../../../guides/core/reference/workspace-toml-schema.md) | Owns the statement that `workspace.toml` points at cooling state and never owns it. Closeout verifies no cooling schema entered the file. |
| `user-documentation` (navigation) | Applicable: [`packs/core/README.md`](../../../packs/core/README.md) | Owns terse discovery of the cooling capability. Closeout verifies navigation without copied implementation detail. |
| `user-documentation` (workflow instructions) | Applicable: [`packs/core/.apm/skills/close-work/SKILL.md`](../../../packs/core/.apm/skills/close-work/SKILL.md) | Owns what the agent is actually instructed to do at runtime. Closeout verifies the disposition row, the deterministic-seam sentence, and the timer prohibition all describe shipped behaviour. |
| `release-history` | Applicable: [`docs/product/changelog.md`](../../product/changelog.md) | Owns the shipped Core capability after the pack version settles. Closeout verifies the topmost dated `[core]` heading equals `packs/core/pack.toml`. |
| `project-knowledge` | Conditional and intentionally unresolved until implementation produces reusable learning: route through the existing `project-knowledge --capture` gate | No placeholder is created. Closeout requires either an explicit `not applicable—no reusable learning` finding or an accepted gate receipt. |

### Capability and delivery evidence

This delivery is a live dependency for RFC-0096 Waves 6 and 7, and Wave 4's
spec and plan are a live dependency of it. None of the three is disposed of
here.

## Boundaries

These are the rails the acceptance criteria do not already pin. A rail that
merely restates a criterion has been removed.

### Always do

- Treat every persisted record, external claim, and model-proposed locator,
  date, timezone, authority fact, or confirmation as bounded untrusted data and
  revalidate it at the deterministic seam that acts on it.
- Keep source, write, and deletion authority independent, and refuse when any is
  unknown or contradictory.
- Draw every persisted vocabulary token from a published set: RFC §5 disposition
  intents and `close_work.POST_CLOSEOUT_RESULTS`.

### Ask first

- Ask before changing the record's field set, the excluded-field rule, the
  resolved record destination, or the selected delivery-completion event.
- Ask before accepting a retained exception's reason, owner role, and review
  date, or renewing one.
- Ask before adding a second lifecycle adapter, a dependency, a configuration
  file, a registry, or a top-level directory.

### Never do

- Never auto-delete on day 30, on elapsed time, on a status change, on session
  end, or after a passing review.
- Never let a prior review substitute for fresh confirmation.
- Never add a scheduler, daemon, cron entry, background job, or wake-up hook.
- Never derive identity, dueness, or eligibility from commit topology, branch
  shape, reflog, or history depth.
- Never create the lifecycle destination implicitly; absence is an offer to
  select or create, which a human accepts.
- Never add a second semantic-surface resolver, a second fingerprint helper, or
  a weaker path check.
- Never implement workspace-status projection, ordinary-context exclusion,
  historical migration, or pruning.

## Testing Strategy

Every acceptance criterion below names a concrete input and the exact observable
it must produce — a refusal code from the published set, a field value, a byte
comparison, or a resolved symbol set over a named path. That is the falsifiability
rule for this spec: an AC that cannot name its input and its observation is not
finished, and no criterion here asserts a property of the code's character.

- **Dates, dueness, record shape, enrolment, the write seam, identity, and
  review: TDD.** The clock and the current instant are injected arguments and
  every outcome is a code or a value, so each criterion is a table of
  (input → observable) rows over pure or filesystem-bounded functions.
- **Identity across history shapes: TDD with real Git fixtures.** Five temporary
  repositories perform a real squash merge, merge commit, rebase, `--depth=1`
  shallow clone, and a `.git` deletion. The record is written *before* each
  operation and verified *after* it, so an implementation deriving identity from
  commit topology cannot self-verify. Git is never mocked.
- **Absence criteria: AST over a named path with an enumerated symbol set.**
  AC6 and AC36 each name one file and one closed set of call targets, resolved
  through the module's import bindings. Both carry a mutation proof using a
  receiver-variable form, not the literal form the matcher already sees.
- **Surfaces: goal-based string pairs.** AC39 enumerates each file with the
  string it must gain and the string it must lose, so it fails on a missed file
  and on a stale claim.

**Stub coverage.** TDD-mode criteria are stubbed in `plan.md`'s per-task
`Tests:` subsections. Compiled red stubs: AC1–AC36. `no stub (mode)`:
AC37–AC40 (Task 5, goal-based and manual QA). Uncovered: none.

## Acceptance Criteria

### Dates and dueness

- [x] **AC1 — The offset is always thirty calendar days.** For every row of
  Task 1's date table, `compute_review_on(completed_on, timezone)` returns a
  date exactly 30 calendar days later. The table contains a window holding a
  spring-forward transition, one holding a fall-back transition, one spanning
  29 February, and one holding none of these.
- [x] **AC2 — Dueness flips at local midnight in the recorded zone.** For a
  record with `review_on = 2026-08-31` and `timezone = Asia/Singapore`,
  `is_due` returns `due=False` at 23:59 on 2026-08-30 local, and `due=True` at
  00:00 on 2026-08-31 and at 00:00 on 2026-09-01 — and returns the same three
  answers when each instant is expressed in `UTC`, `America/New_York`, and
  `Australia/Sydney`.
- [x] **AC3 — Late closeout keeps the event date.** Enrolling with
  `completed_on` forty days before the injected instant produces a record whose
  persisted `completed_on` is that supplied date, not the enrolment day, and for
  which `is_due` returns `due=True`.
- [x] **AC4 — A due record carries no permission.** `is_due` on a due record
  returns `permission_granted=False` and `mutated=()`.
- [x] **AC5 — Invalid temporal input returns a named code.** A naive `datetime`
  returns `naive-clock`; a `timezone` string that `ZoneInfo` cannot resolve —
  whether malformed or absent from the platform database — returns
  `unknown-timezone`. Neither falls back to UTC or the system zone.
- [x] **AC6 — `cooling.py` calls no clock.** With import aliases resolved, the
  AST of `packs/core/.apm/skills/close-work/scripts/cooling.py` contains no call
  to `datetime.now`, `datetime.utcnow`, `datetime.today`, `date.today`,
  `time.time`, `time.monotonic`, `time.perf_counter`, or `os.times`, through any
  receiver.

### The record

- [x] **AC7 — The schema declares the RFC §6 field set as required.** The
  contract's top-level `required` equals exactly `schema`, `delivery_id`,
  `locator`, `aliases`, `fingerprint`, `disposition`, `post_closeout_result`,
  `completion_event`, `completion_evidence_ref`, `completed_on`, `timezone`,
  `review_on`, `authority`, `confirmation_proof`; and every object node in the
  schema sets `additionalProperties: false` and a non-empty `required`.
- [x] **AC8 — An undeclared key refuses at every level.** A payload carrying an
  extra key at the top level, inside `authority.write`, and inside a complete
  `exception` object each return `record-invalid`; an unmodified valid payload
  returns no code.
- [x] **AC9 — A missing required key refuses.** Deleting any single member of
  AC7's required set returns `record-invalid`.
- [x] **AC10 — Every value is pattern-constrained.** `delivery_id` matches
  `^[a-z0-9][a-z0-9-]{0,127}$`; `fingerprint` and `confirmation_proof` match
  `^sha256:[0-9a-f]{64}$`; `owner_role` matches `^[a-z][a-z0-9-]{1,63}$`; each
  `*_evidence_ref` matches one of `commit:<40 hex>`, `pr:<digits>`,
  `run:<digits>`. The inputs `a/b`, `..`, `author:jane-doe`, `owner:j.doe`, and
  `approved by a.person@example.com` each return `record-invalid`.
- [x] **AC11 — The filename is the delivery ID.** The record for `delivery_id`
  `X` is `docs/lifecycle/X.json` with no transformation, and loading a file
  whose stem differs from its own `delivery_id` returns `record-invalid`.
- [x] **AC12 — Serialization is canonical.** `canonical_bytes` of a payload
  whose keys are supplied in shuffled order equals `canonical_bytes` of the same
  payload sorted, ends with a single `\n`, and re-serializing a loaded record
  reproduces the input bytes. A payload containing `NaN` or `Infinity` returns
  `record-invalid`.
- [x] **AC13 — Oversized and over-nested input refuses without raising.** A
  schema-valid record padded past 64 KiB returns `record-invalid`. Over-nested
  JSON also returns `record-invalid` rather than raising, and the depth bound
  admits `MAX_RECORD_DEPTH` while refusing one level beyond it — asserted
  directly, because every field of a valid record is constrained and none can
  nest that far.

### Enrolment and the write seam

- [x] **AC14 — Each enrolment precondition has its own code.** Not delivered
  returns `not-delivered`; not closed returns `not-closed`; no persistent record
  returns `no-persistent-record`; an unset completion event and each of
  `creation`, `ready`, `edit`, `session-end` return `completion-event-required`.
- [x] **AC15 — An unconfirmed destination refuses.** Enrolment with no candidate,
  or with a candidate whose `destination-selection` confirmation is not
  `confirmed`, returns `destination-unconfirmed` and creates no file.
- [x] **AC16 — An absent destination refuses; an absent record does not.**
  Enrolment against a destination directory that does not exist returns
  `lifecycle-state-unwritable` and creates no directory; against an existing
  destination with a record file not yet present it returns `enrolled` and the
  file exists afterwards. A record file that is already present returns
  `record-invalid` and leaves it byte-unchanged, so enrolment cannot overwrite a
  disposition someone already recorded.
- [x] **AC17 — A declared attribute cannot make an unwritable destination
  writable.** Enrolment against a destination the process cannot write to
  returns `lifecycle-state-unwritable` and creates no file, and supplying a
  candidate whose `writability` is `writable` returns the same code.
- [x] **AC18 — A swapped parent refuses with no bytes anywhere.** When the
  destination's parent is replaced by a symlink to a directory outside the
  repository root, enrolment returns `unsafe-target`, and neither the link
  target nor the repository contains a new file.
- [x] **AC19 — The write is authorized for this exact record.** The binding must
  be the object the shipped `_mutation_binding` returned for an issued authority
  fact, with `resource` equal to this record's own lifecycle file path
  (`docs/lifecycle/<delivery_id>.json`), not the delivered artifact's locator. An absent binding, a
  well-formed binding that was never issued, one naming a different action, and
  one naming a different resource each return `authority-uncertain` and create no
  file.
- [x] **AC20 — Refusals carry a code and nothing else.** Every refusal returned
  by the write seam is a member of the published code set, and its payload
  contains no absolute path, no `errno`, and no exception text.
- [x] **AC21 — A stale `review_on` refuses.** Loading a record whose stored
  `review_on` differs from `completed_on` plus thirty days in its recorded zone
  returns `record-invalid`.
- [x] **AC22 — State changes only along the transition table, over persisted
  state.** `update_record` accepts exactly the `(disposition,
  post_closeout_result)` pairs enumerated in the plan's transition table and
  returns `record-invalid` for every other pair, including every pair whose
  source is `Retired`. The pair is read from the record on disk, so a stale or
  fabricated `prior` cannot drive a transition the table forbids.
- [x] **AC23 — An update survives the process.** A record enrolled and then
  changed by `update_record` in one process yields identical `canonical_bytes`
  when loaded in another process.
- [x] **AC24 — `workspace.toml` holds no cooling state.** Parsed as TOML, it
  contains no key named `cooling`, `review_on`, `completed_on`, or
  `lifecycle_record` at any depth.

### Identity and deletion permission

- [x] **AC25 — Identity survives five history shapes.** For each of a squash
  merge, a merge commit, a rebase, a `--depth=1` shallow clone, and a `.git`
  deletion, a record written before the operation returns `identity-verified`
  when checked after it.
- [x] **AC26 — A rename keeps the old locator.** After `record_rename`, the
  record's `locator` is the new path and the previous locator is a member of
  `aliases`.
- [x] **AC27 — Permission is granted, never inferred.** The seam returns
  `deletion-permitted` only when completion evidence, identity, references, and
  deletion authority are each affirmatively proven; drift returns
  `fingerprint-drift`, an unresolvable locator returns `locator-unresolved`, an
  unresolvable completion-evidence reference returns `missing-history`, and any
  `authority.delete.status` outside the recognized set returns
  `authority-uncertain`.
- [x] **AC28 — `missing-history` is about evidence, not Git.** A record whose
  completion-evidence reference cannot be resolved returns `missing-history`,
  and a record in a tree with no `.git` directory but a resolvable reference
  does not.
- [x] **AC29 — Persisted authority is a hint, never a grant.** A record whose
  stored `authority.delete.status` is `delegated` but for which no live grant
  resolves at review time returns `authority-uncertain`.
- [x] **AC30 — Source authority is not deletion authority.** A record whose
  `authority.source.status` is `external-owned` and whose
  `authority.delete.status` is `none` returns `authority-uncertain`.

### Day-30 review

- [x] **AC31 — All six answers are required.** Omitting any one of `completion`,
  `outputs`, `active_use`, `obligations`, `identity`, or `authority` returns
  `review-incomplete`.
- [x] **AC32 — The attestation must carry a human's own answers.** A valid
  attestation restates all six answers exactly, names an approver role different
  from the proposing role, and carries a human evidence reference. An
  attestation missing any of the three, one whose restated answers differ from
  the supplied checks, and one whose approver role equals the proposer each
  return `review-incomplete`.
- [x] **AC33 — Approval retires and persists.** Six approving answers produce a
  record whose `post_closeout_result` is `Retired`, written through
  `update_record` and readable afterwards.
- [x] **AC34 — Refusal or uncertainty produces a complete exception.** Any
  `refuse` or `uncertain` answer produces `disposition = retain-exception` with
  `reason`, `owner_role`, and `review_on` all present; omitting any of the three
  returns `exception-envelope-invalid`.
- [x] **AC35 — Exception review has exactly four outcomes.**
  `confirm-deletion`, `renew`, `choose-cooling`, and `advisory` are each
  accepted and each map to a pair in the transition table; any other outcome
  returns `exception-envelope-invalid`.
- [x] **AC36 — `cooling.py` removes nothing but its own temp file.** With import
  aliases resolved and receiver variables included, its AST contains no call to
  `os.unlink`, `os.remove`, `os.rmdir`, `os.removedirs`, `Path.unlink`,
  `Path.rmdir`, or `shutil.rmtree`, except the single temp-file cleanup the plan
  names by line.

### Surfaces

- [x] **AC37 — The reused primitives are byte-unchanged.** The SHA-256 of
  `surface_resolver.py` and of `file_safety.py` equal the values pinned in
  `tests/roster/test_close_work_extraction_and_immediate_disposition.py`.
- [x] **AC38 — No dependency is added.** `pyproject.toml`,
  `packages/*/pyproject.toml`, and `tools/requirements.txt` gain no entry.
- [x] **AC39 — Each instructional surface gains and loses a named string.** For
  each of the seven file/string pairs enumerated in Task 5, the file contains
  its replacement string and does not contain its superseded string. The seventh
  is the shipped skill's cooling-seam sentence, which named the wrong module.
- [x] **AC40 — The Wave 6/7 boundary is still proven.** The amended Wave 4
  roster test asserts the Wave 6/7 boundary sentence, and deleting that sentence
  from the doctrine corpus makes the test fail.

## Assumptions

Each is checked, or labelled as an unchecked predicate. Rejected alternatives
live in [`notes/resolve-vs-surface.md`](notes/resolve-vs-surface.md), not here.

- The record destination is `docs/lifecycle/<delivery_id>.json`. The first
  choice, `docs/specs/<slug>/lifecycle.json`, was withdrawn: `docs/CONVENTIONS.md`
  § "A spec directory freezes as a unit" freezes a shipped spec directory, and
  only shipped work cools. (checked 2026-08-27; owner decision)
- `runtime-coordination` is an existing resolver role, so `surface_resolver.py`
  is unchanged and its pinned digest holds. (checked: `SURFACE_ROLES`)
- The resolver performs no discovery, so the caller supplies the candidate and
  its confirmation. (checked: `surface_resolver.resolve_surface` takes
  `candidates`; module docstring states it never scans)
- `file_safety.py` exposes no writer, so the write seam reuses Wave 4's
  validated-parent walk rather than adding a second confinement implementation.
  (checked: the module's four public helpers are all read-side)
- Wave 4's `preview_deletion` / `confirm_deletion` / `apply_confirmed_deletion`
  already implement confirmed deletion, so Wave 5 adds none. (checked:
  `close_work.py`)
- `datetime`, `date`, `timedelta`, and `zoneinfo` are stdlib on the `>=3.11`
  floor both packages declare, and no date library is declared by any manifest.
  Some are importable transitively, which is not a licence to import them.
  (checked: `pyproject.toml`, `packages/*/pyproject.toml`,
  `tools/requirements.txt`)
- Wave 5 depends on Wave 4 only and runs alone. (RFC-0096 §9)

## Changelog

- 2026-08-28: Shipped. Post-GATES adversarial, security, and quality
  review; eight sustained blockers repaired. The write seam became a
  compare-and-swap against persisted state after three reviewers independently
  showed `Retired` was not terminal; the writer now validates what it serialises;
  the depth guard became iterative after a 2 KB file exhausted the stack inside
  it; and the AC13 and AC19 guards were rebuilt after mutation showed both could
  be deleted with the suite green. AC16 and AC22 gained the persisted-state
  clauses the repair established.

- 2026-08-27: Opened.
- 2026-08-27: Pre-EXECUTE adversarial and secure-design review; 27 sustained
  findings applied. Destination re-decided to `docs/lifecycle/<delivery-id>.json`
  after the frozen-spec-directory conflict surfaced. Added criteria for the
  candidate destination, write-seam confinement, write authorization, on-load
  revalidation and forward-only disposition, structural exclusion, canonical
  serialization, input bounds, human attestation, and exception review. Cut the
  leap-day criterion to a plan table case; merged the two write-surface criteria.
