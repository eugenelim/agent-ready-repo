# Supervisor launch routing for plan-authored commands

- **Slug:** `supervisor-launch-routing-for-plan-authored-commands`
- **Status:** Draft
- **Kind:** outcome
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:work-loop-delivery-efficiency

## Outcome

- **Steerable input:** Route every supervisor launch — `red-proof`, `scratch`,
  and `git` — through the Slice 1 safe-process primitive under a recorded
  grant. None is routed today.
  `execution-supervisor-attempt-security` removed its AC-0019 on 2026-10-23 and
  handed the work here; that spec still requires the `git` child's environment
  to be bounded, which its hardened helper does without the primitive.
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
  --batch` in `_supervisor_attempt.py`, and four in `_supervisor_commit.py` —
  have no route, because the launch record fixes `stdin_mode` to closed and
  stdin bytes are themselves redacted from the output.
- Includes the three live obstacles any design must clear: three copies of
  `_process_safety.validate_process_spec_dict` refuse an unknown spec key; the
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

## Source

- Mode: repo-origin
- Locator: docs/specs/execution-supervisor-attempt-security/spec.md
- Authority: repo-origin
