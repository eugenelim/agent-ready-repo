# Gates report their declared failure conditions

- **Status:** Draft
- **Level:** feature

## Outcome

Each affected gate rejects its declared failure condition instead of reporting a clean result that proves nothing.

## Opportunity

The Semgrep self-test can report zero findings after an unreported whole-file parse failure, CAT-V-014 cannot report output drift without `dist/`, and the CI-parity roster cannot see a hidden command inside an already-dispositioned step.

## What this absorbs

### sast-semgrep-unparseable-target-reads-clean

- **Authority:** [spec/semgrep-selftest-batching Assumptions](../../specs/semgrep-selftest-batching/spec.md)
- A whole-file parse failure still reads as scanned with zero findings under `--strict`, although the partial-failure half now gates through `run-semgrep-gate.py`.
- `tools/test-semgrep-argv-boundary.py`'s `scan_all` docstring measures the behavior: `--strict` escalates a partial parse failure to exit 3, but a whole-file or whole-construct failure yields empty `errors`, empty `skipped`, empty stderr, and exit 0 even under `--strict`.
- Add a parse-success assertion for every ratcheted target.
- Unblocks when: a parse-success assertion per ratcheted target exists.

### output-drift-silent-without-dist

- **Authority:** [spec/marketplace-generator-single-source Assumptions](../../specs/marketplace-generator-single-source/spec.md)
- CAT-V-014 cannot fire in CI because `_step_output_drift` in `packages/agentbundle/agentbundle/catalogue_tooling/verify.py:1324` returns `[]` when `dist/` is absent: `if not output_dir.is_dir(): return []`.
- `test_absent_output_directory_passes` deliberately pins the absent-output case.
- **BLOCKER:** The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC. This applies at commit time.

### ci-parity-hidden-gate-in-dispositioned-step

- **Authority:** [spec/local-gate-ci-parity AC and residual](../../specs/local-gate-ci-parity/spec.md)
- `tools/lint-ci-parity.py`'s per-step disposition roster misses a gate added inside a step that already carries a disposition. A second command on a later line changes nothing the roster sees, and extraction catches it only when the new command names a literal path it can parse.
- This was measured: appending `D=tools; N=x; python3 "$D/$N".py` to an already-dispositioned step leaves the gate green. `tools/test-lint-ci-parity.py:783` records that a hidden gate inside such a step is not caught and that only reading the command would catch it.
- No per-step scheme closes the gap. The recorded options are: (a) disposition per command, using a content hash of each step's `run:` body so any body edit invalidates its disposition and forces re-reading; this is about 20 lines but makes every whitespace change demand a re-sign; (b) execute or fully parse each command, which is correct but far too expensive; or (c) accept the residual, which is today's position and is stated in § What it does not prove and asserted by `roster-residual-hidden-gate-in-known-step`.
- If this bites, the recorded recommendation is option (a), whose noise is tolerable because `run:` bodies change rarely.
- Unblocks when: picked up — no dependency.

## Assumptions

- None.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
