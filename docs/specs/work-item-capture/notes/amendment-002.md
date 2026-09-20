# Amendment 002 — the write-path refusal binds in the store, not the validator

**Authorised by:** eugenelim, 2026-09-20 (same authority as amendment 001;
this corrects that amendment's target)
**Against:** approved_plan_hash 194d0a7aa40a

## What amendment 001 got wrong

Amendment 001 widened T1 so the non-writable-version refusal could bind at
the write path. T1 implemented it by making `validate_capture_request`
delegate to `select_validator(..., require_writable=True)`.

`knowledge_store.py` calls that one function from **three** sites: two on the
write path (`_check_pre_admission`, and the event builder) and **one on the
read path** — `_validate_event`, which validates every stored event during a
replay. Making it require-writable therefore refused every already-stored
legacy record at read, with a `strict_parse` code.

Verified against the committed corpus, not inferred: a real stored v1 payload
taken from `docs/knowledge/**/*.jsonl` was refused by
`validate_capture_request` and admitted by `select_validator`. The suite
stayed green throughout because no test reads real legacy content through
that path — the blind spot, not an absence of the defect.

That is a regression against committed repository content, and it is worse
than the gap it closed. It has been reverted: `validate_capture_request` is
version-agnostic again and reading a stored legacy record works.

## Why T1 cannot hold this criterion at all

One function serves both the read and the write call sites, and the file that
distinguishes them — `knowledge_store.py` — is outside T1's `Touches:`. So
T1 can satisfy the write-refusal criterion or the read-admission criteria,
never both. This is a decomposition defect in the plan, surfaced by
execution rather than by review.

## The amendment

**The write-path refusal moves to T4**, which already owns
`knowledge_store.py` and schedules the corpus replay — so it is the one task
that can wire `_check_pre_admission` to the writable-only selector and
`_validate_event` to the version-agnostic one, and prove both with the replay
in the same task.

`packs/core/tests/skills/project-knowledge/test_contracts.py` is added to
T4's `Touches:`, because the test asserting write-path refusal must live
beside the code that performs it and T4 could not otherwise write it. T4 is
alone in its wave, so no same-wave collision is introduced.

T1 keeps the selector-level guarantee it built and proved:
`select_validator(..., require_writable=True)` refuses a non-writable
version. That is the mechanism T4 wires; T1 is no longer asked to bind it.

## Standing instruction this produced

Refusing at write is not refusing at read. Any future change to a shared
validator must state which call sites it binds, and a criterion that names a
path must be owned by a task that can reach that path.
