# Brief: make three gates fail on their declared failure condition

- **Slug:** `gates-that-read-clean-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Draft
- **Source / provenance:** Mode `repo-origin`; locator [`docs/product/intents/gates-that-read-clean-while-gating-nothing.md`](../intents/gates-that-read-clean-while-gating-nothing.md), cut into slices on 2026-11-05 after reproducing the first two gaps.
- **Parent intent:** intent:gates-that-read-clean-while-gating-nothing

## Outcome

The SAST relevance step sees every changed path, output drift check CAT-V-014 runs in the required job, and the Semgrep self-test fails on a ratcheted target it can prove unparseable. A target with no usable positive control is named in an `UNPROTECTED_TARGETS` list in the self-test, so the gap is visible and not silent.

## Success metrics

- A changed file whose name holds non-ASCII characters still sets `skip_sast=false`.
- `make build-check` runs a verify pass after the build, so CAT-V-014 can report drift.
- Each ratcheted Semgrep target either has a positive-control assertion that fails on a seeded whole-file parse error or appears in the self-test's `UNPROTECTED_TARGETS` list with a reason.

## Scope / Non-goals

**In scope:** the three slices below.

**Non-goals:** the hidden-command-inside-a-dispositioned-step gap (the recorded position, option c in the intent, is to accept it); pinned-ref workflow requirements; any edit under `packages/agentbundle/**`.

## Proposed slices

Every slice is checked by an agent with no live service, credential, or human reviewer.

| # | Slice | Agent-only verification | Depends on | Gating |
| --- | --- | --- | --- | --- |
| G1 | Read changed paths with `git diff --name-only -z` and NUL-safe matching in the `gate-sast` relevance step; sweep `docs.yml` for the same quoting assumption. | A fixture repo with a `tools/weird<e9>.py` change: old command prints a quoted path that fails the anchor, new command matches; a posture mutation restoring the line-oriented form fails `tools/test-build-check-workflow.py` | none | Security-reviewer pass; own PR because it changes a security gate |
| G2 | Add a second `catalogue verify` step after `catalogue-build` in `tools/repo/build_gate_chain.py`; `catalogue verify` takes no output argument and reads the configured `build-output` (`dist` in `catalogue.toml`), so the step first fails the whole chain, not just itself, when the chain's `--output-dir` resolves to a different directory, then deletes `__pycache__` directories under the build output, then verifies; this checks the build the previous step just made. | `tools/test_build_gate_chain.py` ordered literal updated and passing; a build from a clean checkout passes the second verify with no CAT-V-014 finding; a seeded drifted file under the build output fails it | none | Own PR |
| G3 | A scanned-path membership assertion per ratcheted Semgrep target in `tools/test-semgrep-argv-boundary.py`: each target must appear in the scan's reported scanned paths and a positive-control finding for a known-bad construction in that file type must fire. | The self-test passes on the real tree; a seeded target that the parser cannot read (so its positive control never fires) fails it | none | none |

### Manual or live residue, split off as non-blocking follow-ups

- None. All three slices run offline.

## Constraints / Appetite

Three small sessions; G1 and G2 are independent of G3.

## Assumptions / Risks

- Riskiest assumption for G2: a clean build yields no CAT-V-014 noise. Measured 2026-11-05: with a build output present, `agentbundle catalogue verify` runs CAT-V-014 and can fail; it flagged `__pycache__` `.pyc` files in the build output. G2's verification therefore uses a clean-checkout build, and interpreter cache files are deleted by the chain step before the second verify, not excluded in the engine under the protected `packages/agentbundle/**` tree, which would need an `Engine-Change-RFC:` trailer.
- Riskiest assumption for G3: a whole-file or whole-construct parse failure gives empty `errors`, empty `skipped`, empty stderr and exit 0 even under `--strict` (the `scan_all` docstring in `tools/test-semgrep-argv-boundary.py` records this), so no error signal exists to read. The positive-control finding is the only signal that proves the file parsed; if a file type has no usable control construct, G3 records that target as unprotected rather than asserting.
- G1 repeats a measured result: on 2026-11-05 a `tools/weird<e9>.py` change printed as `"tools/weird \303\251.py"` and failed `grep -qE "^(tools|packs)/"`, while `-z` printed the real path.
- Any G1 repair must make the predicate see more paths, never fewer.

## Ready gaps (Draft only)

- None open.

## Spec map

| Spec | Status |
| --- | --- |
|  |  |

## Provenance

- Parent intent: [`gates-that-read-clean-while-gating-nothing.md`](../intents/gates-that-read-clean-while-gating-nothing.md).
