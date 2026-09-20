# T4 completion evidence

**Task:** every site pinning the kind vocabulary admits the new kind together,
plus the write/read split amendment 002 moved here.
**Completed:** 2026-09-20.

## What shipped

- The store's partition allowlist and kind enumerator widened, completing the
  five capture-kind sites. T2 had done the schema copies and the request
  validator.
- A **source-parsed** five-site sweep, not a grep: a grep cannot decide this,
  because a site holding the old set and one holding the new set both match
  it. The sweep drops a site whose pattern stops matching and asserts a floor
  on the count, so a site that silently stops being swept is a failure rather
  than a pass.
- A negative control over the four sets that must **not** widen — the two
  synthesis kinds, the legacy row kind, and the knowledge lint's allowlist —
  quantified over the same membership so the sweep and the control cannot
  disagree.
- The write/read split: `_check_pre_admission` bound to the writable-only
  selector, `_validate_event` left version-agnostic.
- The corpus replay over the real store, partitioned on capture-payload
  presence, asserting every file's bytes unchanged. No record count appears.

## Verification, checked by the controller

- **Both directions of the split, against the committed corpus**: a real
  stored legacy record taken from `docs/knowledge/**/*.jsonl` is **admitted**
  at read, and a legacy submission is **refused** at write. This is the pair
  that amendment 002 records as previously broken in the read direction.
- Argv derivation: all 46 rows through the shipped validator, **0
  mismatches** — T4 edited the same module, so this confirms T3's boundary is
  undisturbed.
- `_expect_repo_path` still admits `.ssh/id_rsa`, so the committed store
  stays readable.
- The store admits the new kind; the knowledge lint's allowlist does **not**.
- Full `packs/core/tests/skills/project-knowledge/` suite: **288 passed, 0
  failed**, against a 283 baseline. Roster suite: 6 passed. Contract parity
  exits 0.

## What the implementer did that is worth keeping

It **mutation-tested its own tests** rather than asserting they work: it
reproduced amendment 002's exact regression and confirmed the replay test
failed on a real legacy record; reverted the write-path binding and confirmed
that test failed; reverted a capture-kind site and confirmed the sweep
failed. Three load-bearing checks proven able to fail, then restored. That is
the discipline this spec spent its review rounds trying to encode, applied
unprompted.
