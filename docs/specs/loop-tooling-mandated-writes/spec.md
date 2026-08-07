# Spec: loop-tooling-mandated-writes

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0061, `docs/specs/loop-approved-spec-state/spec.md`

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Two defects, one concern: **the work-loop's tooling does not account for the
writes the work-loop itself mandates.**

### 1 — The approval pins are broken by the loop's own lifecycle writes

`loop-cohort approve-plan` pins `approved_spec_hash = sha256(raw bytes of
spec.md)` and `approved_plan_hash = sha256(canonical(plan.md))`, where
`canonical` normalizes only line endings and trailing whitespace
(`loop-cohort.py:177-186`). `plan check-current` and `schedule check-current`
recompute and compare.

The same skill then mandates writes to those exact files:

| Mandated write | Where |
|---|---|
| spec `Status:` → `Implementing`, before any code | `SKILL.md:220`, `:174` |
| spec `Status:` → `Shipped`; every AC to `[x]` | `SKILL.md:434` |
| plan `Status:` → `Done` (full mode) | `SKILL.md:434` |

So the pin is guaranteed to break one mandated step after it is taken. Both
sides reproduce in a sandbox spec dir:

```
$ loop-cohort plan check-current $S --require-schedule      # right after G-plan
loop-cohort: plan check-current OK for demo                  → exit 0
$ # apply SKILL.md:220 — bump spec Status: Approved → Implementing
$ loop-cohort plan check-current $S --require-schedule
stop — plan check-current: spec.md has changed since approve-plan  → exit 1
$ # apply SKILL.md:434 — bump plan Status: Approved → Done
$ loop-cohort schedule check-current $S
stop — schedule check-current: plan.md has changed since schedule  → exit 1
```

The plan-side half is the more dangerous one: `schedule check-current` is a
**mandatory pre-guard on every `CODE-*` transition** (`loop-engine.py:764`), so
a plan-side lifecycle write can wedge the state machine mid-EXECUTE.

The contradiction is **encoded as intended behavior in three tests**:
`test-loop-cohort.py:503`, `:1712`, and `:457` each mutate spec.md *precisely by
bumping `Status` to `Implementing`* and assert the refusal. The suite certifies
the bug.

What the pin is *for* is unchanged: it detects the scope a human approved
changing under an approved plan. What it must stop doing is treating the loop's
own bookkeeping fields as scope.

### 2 — Knowledge capture has no writer, so its encoding drifts

`SKILL.md:454` mandates promoting learnings to `docs/knowledge/patterns.jsonl`
and documents the schema — but names no way to write a line. The obvious
`json.dumps(entry)` defaults `ensure_ascii=True`, so `—` lands as `—`;
`ensure_ascii=False` gives the literal character. Both lint clean today.

The file accumulated both forms and was rewritten by hand to uniform raw UTF-8
(recorded at `docs/specs/local-gate-ci-parity/plan.md:436`). That fixed the
instance, not the cause: nothing states the convention and nothing enforces it,
so the next append re-drifts by picking the other default.

Two properties discovered during secure-design review shape the fix. First,
`json.dumps` with the default emits **surrogate pairs** for non-BMP characters
(`😀` → `😀`), which are valid JSON but invalid as TOML/YAML scalars —
so the drift is not merely cosmetic. Second, `str.splitlines()` — which both
`lint-knowledge.py:78` and `tools/hooks/session-start.py` use to read the file —
splits on `U+0085`, `U+2028`, and `U+2029`, and `ensure_ascii=False` emits all
three raw. A naive "always write raw" rule would let one entry become two
unparseable lines.

## Acceptance Criteria

**Defect 1 — lifecycle-tolerant contract hashing**

- [x] AC1. `loop-cohort.py` canonicalizes both contract artifacts identically
      before hashing, normalizing exactly four things: CRLF/CR → LF; per-line
      trailing whitespace; the **status token only**, on the preamble status
      line only; and the **bracket contents only** of an acceptance-criterion
      or task checkbox (`[x]` → `[ ]`). Leading whitespace and the bullet run
      are preserved byte-for-byte, so re-indenting a criterion — which changes
      what the list contains — still moves the digest.
- [x] AC2. Status and checkbox recognition reuse the shared canonical parsers
      from `lint-spec-status.py` — `parse_status`, `extract_status_token`,
      `_AC_DONE_RE` (only ticked boxes are normalized), and the three that *locate* the preamble
      line (`_STATUS_RE`, `_SECTION_HEADING_RE`, `_HTML_COMMENT_RE`) — via the
      `importlib` pattern `check-spec-status.py` already uses. The line is
      located by the same comment-stripped, heading-terminated scan
      `parse_status` performs. No fourth ad-hoc status parser.
- [x] AC3. All four verbs that compute a contract hash use the canonical form:
      `approve-plan` (idempotency compare and baseline write), `plan
      check-current`, `schedule` (`_schedule_run_impl`, which writes
      `plan_hash`), and `schedule check-current`.
- [x] AC4. Bumping spec `Status:` through `Approved → Implementing → Shipped`,
      and plan `Status:` through `Approved → Done`, leaves `plan check-current
      --require-schedule` and `schedule check-current` at exit 0.
- [x] AC5. Ticking an acceptance-criterion or plan-task checkbox leaves both
      checks at exit 0.
- [x] AC6. A substantive edit still fails both checks and still makes
      `approve-plan` refuse with `spec_changed=True` / `plan_changed=True`:
      changed AC text, added or removed AC, changed task text, changed
      `Depends on:`, **and free text appended after the status token on the
      status line** (`- **Status:** Implementing — scope now also covers X`).
- [x] AC7. A `**Status:**` occurrence in the document *body* — after the first
      `##` heading, as in a table row or fenced example — is hashed verbatim,
      not normalized. Only the preamble field is bookkeeping.
- [x] AC8. Appending `(deferred: <slug>)` to an AC still fails `plan
      check-current`. Deferring an AC is a scope change, not bookkeeping. So is
      a `Shipped (2026-01-01)`-style annotation after the token: 
      `extract_status_token` truncates at `" ("`, so the annotation is not part
      of the token and stays hashed.
- [x] AC9. Every verb that reads a pinned artifact asserts its status token is
      legal after approval — spec.md in {`Approved`, `Implementing`, `Shipped`},
      plan.md in {`Approved`, `Executing`, `Done`} — and stops otherwise. This
      replaces the regression detection the raw-byte hash provided
      incidentally. All three sites, via one shared helper: `plan
      check-current`, `schedule check-current`, and `approve-plan`'s
      already-approved branch, which is reached *before* the crash-window guard
      and would otherwise report a clean no-op against a spec that no longer
      claims to be approved.

      **An absent or unparseable token is skipped, not stopped.** That is what
      makes it safe on `schedule check-current`, a pre-guard on every `CODE-*`
      transition: plan fixtures legitimately carry no status line
      (`test-loop-engine.py:93-97`), so they are unaffected, and the three
      statuses a plan legitimately holds after `plan-locked` are all in the
      allowed set. A draft of this criterion excluded `schedule check-current`
      to avoid giving it a new way to go red; secure-design review pointed out
      that a compensating control covering one of three sites is not one, and
      the skip rule already carries the safety.
- [x] AC10. Every hash-mismatch message names **both** possible causes
      unconditionally — approved scope changed, *or* this baseline predates
      canonical hashing — and points at the reset pair. This covers all four
      mismatch sites: `plan check-current`'s spec and plan compares, its
      `plan_hash != approved_plan_hash` compare (`loop-cohort.py:635`),
      `schedule check-current`, and `approve-plan`'s idempotency-compare
      message (`:558-563`) — which is the one a wedged run hits when it tries
      to re-approve, so it is the least exemptable of the four. `schema_version` stays at `1`.

      No legacy-hash comparison is retained. A first draft compared the
      pre-canonical hash to detect a stale pin, but it cannot fire for the
      population it was for: a run past `plan-locked` has already had `Status:
      Implementing` written, so the *legacy* hash of the current bytes
      mismatches too and the branch stays silent exactly when it is needed.
      An unconditional both-causes message is strictly more accurate and
      deletes the mechanism.
- [x] AC11. The three tests that encode the bug are rewritten to exercise a
      substantive change: `test_plan_check_current_changed_spec` (`:503`),
      `test_approve_plan_refuses_changed_spec` (`:1712`), and
      `test_approve_plan_overwrites_hashes` (`:457`), whose post-change
      contract is exit 0 no-op on a status bump and exit 1 on a substantive
      edit. `test_approve_plan_state_preserved_on_refusal` (`:1829`) is also
      rewritten — its scenario A bumps `Status` and would stay green while no
      longer testing the refusal its name claims. New cases cover AC4–AC10,
      including a re-indented criterion (AC1) and an `approve-plan` replay
      after a lifecycle bump, which exercises the idempotency-compare site.
      `test-loop-engine.py`'s duplicated `sha256_file` /
      `sha256_canonical_plan` helpers (`:101-105`, used by 28 fixtures) are
      replaced by an `importlib` load of the canonicalizer so the two cannot
      drift.
- [x] AC12. Three documents state what the pin covers and what it deliberately
      does not: `references/state-schema.md`, `references/pre-execute-review.md`
      (whose `:31-33` "any edit to `plan.md` after `approve-plan` causes a
      refusal" AC4 falsifies, and which names the wrong verb), and the
      **shipped adopter guide**
      `guides/core/how-to/plan-and-execute-non-trivial-work.md:122`, which
      tells adopters "the only safe post-approval edits are trailing-whitespace
      and line-ending normalization — `canonical_plan()` normalizes only those
      two". That sentence is falsified by AC4/AC5 and names a function AC1
      renames; it is the only guide referencing `canonical_plan`.

**Defect 2 — a canonical knowledge writer**

- [x] AC13. `scripts/append-knowledge.py` ships beside `lint-knowledge.py`,
      takes the entry fields as arguments, allocates the next free `K-NNNN`,
      and writes exactly one line with `ensure_ascii=False` and
      `allow_nan=False`.
- [x] AC14. The writer confines `--file`: the target is resolved
      (`expanduser()` then `resolve()`) and refused unless it
      `is_relative_to(<repo root>/docs/knowledge)`. The containment check runs
      **after** resolution, so a symlinked target is validated at its real
      location. It reuses the shape of the repo's blessed helper,
      `tools/hooks/session-start.py:_safe_override_path` — not
      `loop-cohort.py:_resolve_spec_dir`, whose lexical `".." in parts` test is
      CWE-22-shaped, not CWE-73-shaped.
- [x] AC15. Repo-root resolution runs `git rev-parse` with `GIT_DIR`,
      `GIT_WORK_TREE`, `GIT_COMMON_DIR`, and `GIT_CEILING_DIRECTORIES` stripped
      from the child environment, and a non-git cwd is a refusal rather than a
      `cwd` fallback — otherwise the confinement root of AC14 is itself
      environment-steerable.
- [x] AC16. Field values are validated **before** the file is opened: refused
      if they contain a C0 control character (including `ESC`, which would be
      replayed as an ANSI sequence by `session-start.py`), `U+0085`, `U+2028`,
      or `U+2029`, or a lone surrogate; and `title` is capped at 120
      codepoints and `body` at 2000, a refusal naming the field and its limit.
      Knowledge entries are injected verbatim into every future agent session,
      so the writer is a durable-instruction channel and validates like one.
- [x] AC17. The candidate is **linted before it is installed**: the new
      content is written to a temp file in the same directory, that temp path
      is linted, and only on success is it `os.replace`d over the target
      (matching `loop-cohort.py:write_state_atomic`). A failed lint, or any
      exception, leaves the target untouched — never restored, because it was
      never replaced. There is no rollback window in which a bad entry is live
      on disk, and no partial line. `lint-knowledge.py` accepts an arbitrary
      path argument, so linting the candidate costs nothing extra.
- [x] AC18. The post-write lint runs `lint-knowledge.py` as a **subprocess**,
      so its `os.chdir` stays in the child, passing the resolved absolute path
      as the sole argument. No `--` separator: `lint-knowledge.py` has no
      argparse and would take `--` as the target path, failing every append.
      An absolute path already cannot collide with `-h`, so AC14's resolution
      is the mitigation.
- [x] AC19. If the knowledge base already fails lint *before* the append, the
      writer exits with a distinct "knowledge base already fails lint; fix it
      first" message rather than appending and blaming the caller's entry. A
      **non-existent** target is not a pre-existing failure — it is treated as
      an empty file and created, so a fresh knowledge base is reachable.
- [x] AC20. `lint-knowledge.py` fails an entry that escapes a character as
      `\uXXXX` when that codepoint is `>= 0x20` and is not one of `U+0085`,
      `U+2028`, `U+2029`, naming the character and the fix. Escapes JSON
      requires (below `U+0020`) stay legal, as does a literal backslash-u
      sequence in body text, as do the three line-separator codepoints — for
      which the escaped form is the *only* representation that survives
      `splitlines()`.
- [x] AC21. `SKILL.md`, `docs/knowledge/README.md`, and
      `packs/core/seeds/docs/knowledge/README.md` name the script as the way to
      append, state the raw-UTF-8 convention, and state the trust posture from
      AC16. The two READMEs' `## Verify before committing` sections stay
      byte-identical.
- [x] AC22. A self-test covers the writer: id allocation over a gap;
      confinement refusal for both an out-of-root path and a symlink that
      escapes after resolution; the git-env-stripping of AC15 (a decoy
      `GIT_DIR` does not move the root); the out-of-process lint of AC18; the
      pre-existing-lint-failure path and the absent-target path; a forced
      post-lint failure leaving the target byte-identical; the AC16 caps at
      their boundary (at-cap accepted, cap+1 refused); and a round-trip
      proving a non-ASCII body lands raw.
- [x] AC23. The self-test actually gates. `tools/test-all.py` lists it, **and**
      a step running it is added to the `lint-knowledge` job in
      `.github/workflows/docs.yml` — `tools/test-all.py` is hand-run
      (`tools/repo/build_gate_chain.py:205-212` says so), so listing it there
      alone would be a gate that does not gate.

**Both**

- [x] AC24. These pass: `test-loop-cohort.py`, `test-loop-cohort.sh`,
      `test-loop-engine.py`, `test_loop_cohort_schedule.py`,
      `test-lint-knowledge.py`, `test-append-knowledge.py`, `tools/test-all.py`,
      and `make build-check`. `.claude/` and `.agents/` projections are
      regenerated and committed.
- [x] AC25. Core pack version bumped in `pack.toml`, `plugin.json`, and
      `.claude-plugin/marketplace.json`; `docs/product/changelog.md` gains a
      `## [core][<version>]` entry recording both fixes and the migration note
      whose canonical statement is Assumption 1. (This repo keeps a per-pack
      changelog at that path; there is no root `CHANGELOG.md`.)

## Boundaries

### Always do

- Read every status token through `parse_status` / `extract_status_token` from
  `lint-spec-status.py`, per `docs/specs/loop-approved-spec-state/spec.md:34`.
- Confine any caller-supplied filesystem target with canonicalize-then-
  verify-prefix, after resolution, against a named root.
- Keep both scripts pure-stdlib, per the repo's new-tool-scripts rule.

### Ask first

- Changing the knowledge schema — the six required keys, three kinds, the
  README field table, and the linter's `REQUIRED_KEYS` / `OPTIONAL_KEYS` /
  `ALLOWED_KINDS` sets. This change does not.
- Widening the canonical form beyond the two field families named in AC1.

### Never do

- Add a verb, flag, or path that re-pins an approved baseline on demand. A
  re-pin is an authorization bypass wearing a convenience hat.
- Add a new `state.json` field, or write `state.json` by hand.
- Change `loop-engine.py`'s transition table, guard wiring, or state set.
- Let `append-knowledge.py` edit or delete an existing entry. The file is
  append-only by design.

## Assumptions

1. **Every in-flight run must be reset, not only already-wedged ones.** A run
   parked at `SPEC-PLAN-APPROVED` still carries `Status: Approved` (the
   `Implementing` write happens *after* `plan-locked`, `SKILL.md:174`) and is
   healthy today; this change newly invalidates its pin. AC10's legacy-pin
   *diagnosis* is what makes that failure honest, without a schema cutover.

   A `schema_version: 2` bump was the first design and was withdrawn: four
   enforcement sites hardcode `!= 1` beyond the hash verbs
   (`loop-cohort.py:194,423,452,778`, plus a stale `help=` string at `:1221`),
   three suites assert `== 1` (`test-loop-cohort.sh:105,131`,
   `test_loop_cohort_schedule.py:202`, `test-loop-engine.py:114,142`). Note honestly what
   is *not* the discriminator: this run's own pin breaks either way — the hash
   change invalidates it exactly as a version bump would. The difference is
   blast radius. A version bump also stops `identity`, `status`, and `check`,
   which are how a resuming session diagnoses anything at all; the hash change
   stops only the two check verbs and is recovered by the documented reset.
   The plan's Sequencing section carries the recovery step for this run.

   Recovery is the documented reset pair, which preserves `spec.md` and
   `plan.md`. Note the wrinkle the CHANGELOG must state: a run past
   `plan-locked` has `spec.md` at `Implementing`, and `approve-plan`'s
   crash-window guard (`loop-cohort.py:570-582`) requires both files to read
   `Approved` — so re-approval means restoring `Status: Approved` in both
   files first. `state.json` is gitignored run-local state (verified:
   `.gitignore:14-15`), so the blast radius is one developer's working copy.
2. **Un-ticking a checkbox is not a scope change**, so the canonical form
   deliberately cannot detect it. Residual risk: flipping `[x]` → `[ ]` after
   approval could conceal an unmet criterion. Compensating control:
   `lint-spec-status.py` runs at the finish checklist (`SKILL.md:434`) and
   requires every AC to be `[x]` or `(deferred: <slug>)`, so a concealed
   criterion fails there.
3. **Concurrent invocation of `append-knowledge.py` is handled, not deferred.**
   This assumption originally scoped it out as disproportionate for a
   "single-agent-session authoring tool". That was wrong on two counts, both
   shown by the post-EXECUTE security pass: this repo runs parallel implementers
   in a shared worktree, so concurrency is expected rather than exotic; and the
   failure is not a benign id collision but a repudiation — six concurrent
   appends landed two entries while telling all six callers their learning was
   recorded. AC17 now serializes the read-allocate-write window.
4. **The `--file` flow is reviewer-owned, not scanner-owned.**
   `tools/semgrep/env-path-taint.yml:41-45` sources only `os.environ.*`, so an
   argv → path write sink produces no finding; a green SAST gate says nothing
   about AC14. Recorded so a later reader does not mistake scanner silence for
   coverage.

## Testing strategy

TDD for the hashing change — a pure function over text with a compressible
invariant (lifecycle writes in, identical digest out; substantive writes in,
different digest out), and two existing tests must go red first. TDD for the
linter rule and for the writer's allocation, confinement, validation, and
restoration paths. Red stubs are materialized at PLAN per
`docs/CONVENTIONS.md:397-406`, each carrying `# STUB: AC<n>` and `stub: true`
in its task's `Tests:` subsection.

Goal-based checks for the reference-doc and guidance edits.

Visual / manual QA for the writer as a shipped artifact: invoke
`append-knowledge.py` for real and read the bytes it produced, per the finish
checklist's real-invocation requirement.
