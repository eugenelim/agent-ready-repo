# Gates report their declared failure conditions

- **Slug:** `gates-that-read-clean-while-gating-nothing`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim

## Outcome

Each affected gate rejects its declared failure condition instead of reporting a clean result that proves nothing.

## Opportunity

The Semgrep self-test can report zero findings after an unreported whole-file parse failure, CAT-V-014 cannot report output drift without `dist/`, the CI-parity roster cannot see a hidden command inside an already-dispositioned step, and `gate-sast` can report success on a pull request it never scanned because its relevance predicate cannot read a path git quoted.

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

### gate-sast-relevance-predicate-misses-a-c-quoted-path

- **Authority:** [ADR-0113 § Context](../../adr/0113-sast-guarantee-moves-from-the-local-gate-to-gate-sast.md), which records this as a residual and deliberately does not fix it.
- `.github/workflows/build-check.yml`'s `Detect whether SAST-relevant files changed` step matches `git diff --name-only` output against an anchored `^(<SAST_DIRS>)/` regex. Git C-quotes any path holding non-ASCII or special characters, so a changed `tools/` file arrives as `"tools/we ird\303\251.py"`. The leading double quote defeats the anchor, the step sets `skip_sast=true`, and `Run make sast` — the predicate's only consumer — never runs. The job still reports success and the aggregator's `Require every gate` step accepts it.
- Measured by construction on 2026-09-13: a modified `tools/we ird<e9>.py` produced `"tools/we ird\303\251.py"`, which failed `grep -qE "^(tools|packs)/"`.
- Pre-existing, not a regression. Introduced 2026-08-17 in `823cd1742f` (the `ci-gate-parallelization` work behind ADR-0086). Found during review of PR #1285, whose only change to that workflow is a header comment.
- The recorded repair is `git diff --name-only -z` with NUL-safe matching, which also removes the newline-in-path ambiguity the current line-oriented `grep` shares. `core.quotePath=false` is the narrower alternative. Any repair must make the predicate see **more** paths, never fewer.
- Sweep for the same C-quoting assumption in other path-matching gates before closing; the predicate was written once and may have been copied.
- This is the third way this one gate can be green without scanning. ADR-0086 already accepts the other two — the head-ref self-certifying `SAST_CONFIG` predicate, and "a green aggregator does not prove a scan executed" — and they stay accepted; closing those is `ci-gate-parallelization-required-workflow-pinned-ref`.
- **Changing a security gate needs its own review.** That is why it was not repaired inside PR #1285.
- Unblocks when: picked up — no dependency.

## Assumptions

- None.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
