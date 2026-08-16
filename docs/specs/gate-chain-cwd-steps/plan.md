# Plan: gate-chain-cwd-steps

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `tools/repo/build_gate_chain.py` — the step kind and one wired step.
- `tools/test_build_gate_chain.py` — relaxed assertion + new coverage.
- `tools/lint-ci-parity.py` — extractor and two dispositions.
- `workspace.toml`.

**What demonstrates done**
- `lint-ci-parity` 31 locally covered; its 99-case self-test; the chain's own
  17 tests; `make ci`.

**What I am NOT changing**
- The catalogue-curation step (AC7 records why).
- CI's import probe (AC8).
- Any gate's actual assertions.

## Declined patterns

- **Tempted:** express the cwd as `cd <dir> && pytest ...` in a shell step, which
  is what the CI step effectively does. **Declined:** that is precisely the
  Windows-hostile form the chain exists to avoid, and it would have made the
  relaxed assertion meaningless.
- **Tempted:** delete `test_script_steps_are_windows_clean`'s length check
  outright. **Declined:** it was standing in for something real. Replaced with
  the direct claim — no shell tokens, no metacharacters — rather than removed.
- **Tempted:** move the catalogue-curation step too, since the entry lists it.
  **Declined:** measured it. Its blocker is a count-floor shell body, not the
  step vocabulary; moving it needs a different step kind and its own reasoning.
  Recorded rather than half-done.
- **Tempted:** copy CI's `python -c "import credbroker, cryptography, argon2"`
  probe into the local step for fidelity. **Declined:** it would fail
  `make build-check` for any contributor without an optional extra, over a suite
  that already self-skips those cases. CI asserting its own provisioning is a
  different job from a local gate.

## Anchor-test sweep

- `tools/test_build_gate_chain.py` pins the step sequence AND every spawned
  script path — both extended.
- Five `fake_run` fakes in that file needed a `cwd=None` parameter; without it
  the new step raises `TypeError` in four unrelated tests. A mock that does not
  accept the real call signature is a test that passes for the wrong reason.
- `tools/test-lint-ci-parity.py` — 99 cases, all still pass.

## Course corrections during the build

Two, both worth keeping because each was a wrong premise rather than a slip.

1. **The entry named the wrong caller.** I wired the credential-setup suite
   first, on the entry's word plus a local check that `credbroker` imports —
   which it does *here*, because it is pip-installed. It is not installed on the
   build-check runner, and the suite does not degrade gracefully: `setup.py`
   hard-exits 3 at import, and later spawns itself as a subprocess where a
   `PYTHONPATH` source path still does not satisfy it. CI rejected it twice.
   The catalogue-curation suites are the real callers: pure stdlib, no install,
   and they run clean from their directories.
2. **The remaining exemption's stated blocker was also wrong** — and I had
   already written it into a successor entry before checking. It is not "needs a
   count floor, therefore CI-only": the floor is ~15 lines in the step kind. It
   is credential-setup that is blocked, on provisioning.

The general shape: an "unblocks when" line in a backlog entry is a *hypothesis*
about why something is blocked, and it ages worse than the description of the
problem. Re-derive it before building on it.

## Verification log

- **AC1/AC2** `lint-ci-parity` -> ok, 31 locally covered (was 30), 25 CI-only.
- **AC3** extractor joins cwd + target; without it the linter reported the gate
  unreachable from `make ci` — caught on the first run.
- **AC4/AC5** `tools/test_build_gate_chain.py` 17 passed.
- **AC6** from the repo root the catalogue-curation suites collect nothing; from
  their directories, 30 and 7 pass — the counts the floors assert.
- **AC7** floor exercised both ways: floor=7 on the 7-test suite returns 0;
  floor=999 returns 1 and prints the directory with both counts.
- **AC9** `tools/test-lint-ci-parity.py` 102 cases; mutation-verified — removing
  the quote strip fails 5, including the phantom `"$dir"/test_a.py`.
- **Mock hygiene, twice.** Seven `fake_run` fakes needed the real call signature
  (`cwd=`, then `capture_output`/`text` for the floor probe) and a `stdout` the
  probe could count. A mock that does not accept the real call is a test that
  passes for the wrong reason.
- **REVIEW** `adversarial-reviewer` = named skip (session instruction prohibits
  subagent dispatch). Self-reviewed against the spec-less checklist.
