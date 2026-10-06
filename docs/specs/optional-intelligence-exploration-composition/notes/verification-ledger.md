# Verification ledger: optional intelligence in repository exploration

Execution observations for the spec and plan. Each entry records what was
observed, not what the contract requires.

## T1 stub validation (2026-10-05)

- `test_exploration_reader_applies_its_own_ceiling` was extracted byte-for-byte
  from the plan into disposable scratch, at the plan's path relative to a link
  to the real `packs/core/.apm/`. `py_compile` passed. pytest failed red with
  `FileNotFoundError` for `repository-exploration/scripts/read-locator.py`
  (1 failed in 0.22s), because the exploration reader does not exist yet.

## Pre-EXECUTE review round 1 (2026-10-05)

- Sustained: one security Concern (provider output widening roots or starting
  gated actions), one adversarial Concern (per-install no-provider run had no
  owning task), one adversarial Nit (absence scan covered one review agent).
  All three were repaired; the plan's Changelog lists the edits.
- The first security adjudication was rejected by the strict classifier
  (`indeterminate-present`: a stray marker with an empty indeterminate audit).
  On the owner's choice a fresh adjudication of the unchanged report replaced
  it; the rejected artifact is kept beside it in the session review folder.
- Engine sequence 2-3 is a no-op `findings-remain` / `spec-ready` pair: the
  repair script aborted on a stale match before writing, and the next command
  still fired. Sequence 4-5 carries the actual repair.

## Pre-EXECUTE review round 2 (2026-10-05)

- Sustained: two security Concerns (agent-side finality of a refused or
  unavailable locator; AC-0014 metadata and file-text sources lacked behavior
  cases), two adversarial Concerns (evaluation sessions lacked the grounding
  sibling; file-text source untested), and two adversarial Nits (unbacked
  bytecode-cache claim; colliding test module name). All were repaired; the
  plan's Changelog lists the edits.
- Stub re-validated under its new name `test_exploration_reader.py` in
  disposable scratch: `py_compile` passed and pytest failed red with
  `FileNotFoundError` for the missing exploration reader.

## Pre-EXECUTE review round 3 (2026-10-05)

- Security: clean after adjudication (both findings refuted).
- Adversarial: one sustained Concern (the skill census was in no task's scope);
  repaired by adding the census file to T1 and the census test to T4. The
  version-restatement Nit was refuted.

## Pre-EXECUTE review round 4 (2026-10-05)

- Adversarial: Nit only, deferred without edit. T2's preparation command omits
  the required `SKILL/EVAL_ID` value of `--prepare-workspace`
  (`packages/agentbundle/agentbundle/commands/pack_evals.py:1150-1156`); T2
  runs it per case as `--prepare-workspace repository-exploration/<eval id>`
  and records the exact command here.
