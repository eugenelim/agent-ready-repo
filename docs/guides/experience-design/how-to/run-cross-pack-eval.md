# How to run the cross-pack experience eval

The cross-pack experience eval (`check-xd-chain.py`) is a deterministic checker that validates five structural invariants of the XD skill chain — without running an LLM. It runs in seconds and requires no API key.

This guide covers: running the checker, reading its output, and promoting a check to a fail-closed gate.

## What the checker validates

The XD skill chain runs in this order: **design-token-taxonomy → design-system-foundations → information-architecture → copy-direction → design-review**. The checker enforces five structural invariants:

1. **Chain completeness** — all five chain skills exist at their expected paths under `packs/experience-design/.apm/skills/`.
2. **No phantom handoffs** — every skill name backtick-quoted in a `Do NOT use` guard resolves to an existing skill in the pack. Cross-pack references (e.g., `ux-writing` in the `product-engineering` pack) are correctly exempted.
3. **Boundary guards present** — each chain skill's `description:` frontmatter references its required neighbors per the adjacency map. For example, `information-architecture` must reference `` `copy-direction` `` to make clear where copy work belongs.
4. **Contract copies present** — the Digital Experience Contract exists as a copy in each of the four packs (product-strategy, product-engineering, experience-design, core).
5. **Description within cap** — each chain skill's description is ≤1024 characters (the agentbundle description-length cap; over-cap descriptions are silently truncated on some adapters).

## Running the checker

From the repo root:

```
python3 tools/check-xd-chain.py --root .
```

This runs in **report-only mode**: all checks run, findings are printed, and the tool exits 0 regardless of findings. Use report-only mode to observe the current state without blocking a workflow.

Example output when all checks pass:

```
[check-xd-chain] Check 1: chain completeness
  ✓ chain skill exists: design-token-taxonomy
  ✓ chain skill exists: design-system-foundations
  ...

[check-xd-chain] All checks passed.
```

## Interpreting report-only output

Each check prints one line per item:

- `✓` — the item passed.
- `✖` — the item failed. The message names what failed and where.

A finding in report-only mode is a warning — it documents a structural issue but does not stop the workflow. Use the finding to plan a fix, then verify the fix by re-running the checker.

**Finding format:**

```
  ::warning ::[check-name] message describing what failed
```

The check name tells you which invariant was violated:
- `chain-completeness` — a chain skill is missing from the pack.
- `phantom-handoff` — a guard references a skill that does not exist.
- `boundary-guards` — a chain skill's description is missing a required neighbor reference.
- `contract-copies` — a DEC contract copy is missing from a pack.
- `description-length` — a skill description exceeds 1024 characters.

## Running as a gate

To run the checker as a fail-closed gate (exit 1 on any failure):

```
python3 tools/check-xd-chain.py --gate --root .
```

Use `--gate` when you want the checker to block a workflow — for example, as a pre-push hook or in CI. The `--gate` flag is the hook point for wiring this checker into a CI workflow once calibration is complete.

When run with `--gate`, findings use the `::error ::` prefix (compatible with GitHub Actions annotation syntax):

```
  ::error ::[boundary-guards] 'information-architecture' description is missing required guard reference(s): ['copy-direction']
```

## Promoting a fixture to a gate

The cross-pack eval fixtures (`packs/experience-design/.apm/evals/cross-pack-fixtures.json`) describe golden-path scenarios, boundary violations, and weak regression patterns. These are currently documentation-form only — they describe what to look for, not a runnable test.

To promote a deterministic structural check to a gate:

1. Verify the check passes consistently on the live repo in report-only mode.
2. Run `python3 tools/check-xd-chain.py --gate --root .` and confirm exit 0.
3. Wire the `--gate` invocation into your pre-push hook or CI workflow.

To promote an LLM-based fixture scenario to a runnable eval:

1. Author an `evals.json` rubric for the scenario (following the pattern in `packs/experience-design/.apm/skills/design-review/evals/evals.json`).
2. Run the eval via `python3 tools/run-pack-evals.py` in report-only mode to observe actual model behavior.
3. After calibration (confirming the rubric discriminates coherent from weak responses), file a follow-on PR to promote to a gate or add to CI.

## Adding a new check

To add a structural invariant to the checker:

1. Write a `check_<name>(root)` function in `tools/check-xd-chain.py` that returns a list of `(check_name, message)` findings.
2. Call it in `main()` after the existing checks, with a `print` header.
3. Add a corresponding test in `tools/test-check-xd-chain.py` that injects a failure and verifies `--gate` exits 1.
4. Update the spec's acceptance criteria to include the new check.

## Related

- Deterministic checker: `tools/check-xd-chain.py`
- Self-test: `tools/test-check-xd-chain.py`
- Cross-pack fixtures: `packs/experience-design/.apm/evals/cross-pack-fixtures.json`
- Digital Experience Contract drift check: `tools/check-contract-drift.py`
- Per-skill activation evals: `packs/experience-design/.apm/skills/<skill>/evals/`
