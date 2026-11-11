# Supervisor launch routing for plan-authored commands

- **Slug:** `supervisor-launch-routing-for-plan-authored-commands`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Kind:** outcome
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:work-loop-delivery-efficiency

## Outcome

- **Steerable input:** Every supervisor-launched plan-authored command runs with a bounded environment and an interpreter the launched code cannot change, and the launch record shows which code the child loaded.
- **Lagging outcome:** A stub command runs under a recorded grant, a bounded
  environment and a pinned program, and the supervisor can say afterwards which
  code the child loaded.
- **Guardrail:** Whatever selects the child's import surface must not be
  reachable by the code the supervisor launches. Three designs failed that test
  and each is written up below, so a fourth is judged against it first.

## Opportunity

The primitive refuses a link as the program and pins the file it runs. Every
virtual environment's `python` is a link, so a launch that resolves the link
drops the environment: the child cannot import its packages, `python -m pytest`
exits 1, and that is exactly the exit a red stub declares. The supervisor then
records a red proof for a stub that never ran. This was measured, not reasoned.

Three repairs were tried and each was holed on the same point — whatever decides
the child's import surface is writable by the launched code:

- Run the link and pin its target. Fails on Linux, where the primitive execs the
  resolved descriptor through `/proc/self/fd`.
- Pass the environment's `site-packages` on `PYTHONPATH`. The repository's own
  environment sits inside the execution root, where launched code may write and
  no manifest reaches.
- Keep the program name and bound where it may point. The bound checks location,
  not writability, and the temp and home trees it admits are writable by the
  same launched code; a `pyvenv.cfg` `home` key or a symlinked `site-packages`
  also points back inside the repository.

## Boundary

- Includes the launch route for all three kinds, the Launch-grants rows they
  adopt, whatever identifies the import surface in the launch record, and the
  `safe-process.v1` field the route needs.
- Includes `git`, which is blocked by two measured obstacles rather than the
  import-surface one. The primitive puts every environment value it passes into
  its redaction set and rewrites each occurrence out of the returned output;
  `HOME` prefixes a normal repository path and the hardened helper parses git's
  stdout everywhere, so git's own paths would come back rewritten before the
  supervisor read them. And the helper's stdin-bearing calls — `cat-file
  --batch` in `_supervisor_attempt.py`, and six in `_supervisor_commit.py` —
  have no route, because the launch record fixes `stdin_mode` to closed and
  stdin bytes are themselves redacted from the output.
- Includes the three live obstacles any design must clear: `_process_safety.validate_process_spec_dict` — the pack source and its two self-host mirrors — refuses an unknown spec key; the
  schema sets `additionalProperties: false`; and
  `tests/roster/test_security_primitives_schema_parity.py` builds its fixture
  without the new field, so it stays green whether the field exists or not.
- Excludes the red proof's own evidence rule, which is
  [`red-proof-discriminates-a-stub-that-ran`](red-proof-discriminates-a-stub-that-ran.md).
- Excludes the scratch tree at `sys.path[0]`, which is worker-influenced by
  design and is covered by the conftest fixtures of VI-5030 and VI-5031.

## Owner

- eugenelim, Platform Core maintainer.

## Unresolved questions

- Is the import surface bounded by making it unwritable, or by pinning its
  contents in the launch record and re-checking them before exec?
- May a plan-authored stub line choose the interpreter at all, or does the
  supervisor record a sanctioned one at admission?
- Does CPython under the Linux `/proc/self/fd` exec honour a supplied program
  name for prefix detection? Unmeasured; it decides whether a name-based design
  is viable at all.

## Riskiest assumption

**Riskiest assumption:** pinning the sanctioned interpreter's digest at admission and re-checking it before exec bounds the child's import surface, where three earlier designs failed because launched code could write what selected it. Tested agent-only: a fixture that changes the interpreter file between admission and launch must refuse, and the schema-parity test must fail when the new field is removed.

## Non-goals

- The red proof's evidence rule, which `red-proof-discriminates-a-stub-that-ran` owns.
- The scratch tree at `sys.path[0]`, covered by the conftest fixtures of VI-5030 and VI-5031.
- Routing `git` through the primitive: the hardened helper already bounds its environment.

## Readiness

**Route:** new-spec, after `red-proof-discriminates-a-stub-that-ran`, and narrowed.

**Current truth.** The supervisor's red proof and git calls still use bare `subprocess`; neither `_supervisor_tdd.py` nor `_supervisor_git.py` imports `_process_safety`. Untrusted runs are refused before any launch, so the route matters for the trusted path, where the aim is a bounded environment and a recorded interpreter.

**Answers.** A plan-authored stub line may not choose the interpreter: the supervisor records one sanctioned interpreter at admission and pins that file's digest in the launch record, then re-checks it before exec. This replaces the unwritable-surface design and removes the need to measure CPython under Linux `/proc/self/fd`. `git` routing leaves this intent: the hardened helper already bounds the environment, and the redaction and stdin obstacles buy nothing for a trusted run.

**First slice:** `red-proof` and `scratch` launches through the primitive under a recorded grant with the pinned interpreter, plus the `safe-process.v1` field and a schema-parity test fixture that includes it.

**Agent-only proof:** a fixture where the interpreter file changes between admission and launch refuses, and the parity test fails when the field is removed.

## Source

- Mode: repo-origin
- Locator: docs/specs/execution-supervisor-attempt-security/spec.md
- Authority: repo-origin
