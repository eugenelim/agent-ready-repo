# Verification ledger — ci-gate-main-failure-reporting

Execution observations from the delivery. The spec's criteria are the contract;
this records what was run and what it returned.

## T4a — AC-0013, AC-0014, AC-0015 (dispatched runs, 2026-09-21)

Each branch breaks exactly one step and changes nothing else; every delivered
condition stays as shipped. Branch `verify/t4a-<slug>`, never merged.

| Broken step | Run | Dependents skipped | AC-0013 | AC-0014 |
| --- | --- | ---: | --- | --- |
| `Set up Python` | 35665358727 | 71 / 71 | PASS | PASS |
| `Install tools dependencies` | 35665362621 | 4 / 4 | PASS | PASS |
| `Install agentbundle (editable) + pytest` | 35665366815 | 1 / 1 | PASS | PASS |
| `Install ripgrep` | 35665370966 | 2 / 2 | PASS | PASS |
| `Install ruff + mypy` | 35665374955 | 2 / 2 | PASS | PASS |
| `Install credbroker (editable, with crypto extra)` | 35665378924 | 3 / 3 | PASS | PASS |
| `pip install httpx …` | 35665383252 | 0 / 0 | PASS | PASS |
| `pip install the Markdown→Office render libraries` | 35665387205 | 4 / 4 | PASS | PASS |
| `pip install the Tier-0 PDF library` | 35665392097 | 1 / 1 | PASS | PASS |
| `pip install the Tier-0 .msg reader` | 35665396973 | 1 / 1 | PASS | PASS |
| `Install bandit unconditionally` | 35665402147 | 2 / 2 | PASS | PASS |

AC-0015, run 35665407632: one check broken (`pytest version constants`), all
provisioning green. No other check skipped; the broken check is the only failure.

In every run the only `failure` is the step that was broken. That is AC-0014
across the recorded matrix, and AC-0013's skip sets match the declared
dependents exactly.

## Two defects these runs surfaced, both fixed before the passing round

The first round (runs 356637xxxxx) failed AC-0014 on 8 of 11. Neither defect was
visible to any local gate.

1. **`check-adr-index` failed inside `make build-check`.** ADR-0122 (authored as 0121, renumbered when that ordinal was taken) landed
   without regenerating `docs/adr/README.md`. The anchor reddened wherever it
   ran; the three branches where it skipped hid the defect entirely.
2. **`ruff lint` did not declare its install.** On the `ruff + mypy` break it
   FAILED rather than skipping. The original matrix lost that edge: `ruff lint`
   reddened in all ten measurement runs because of a `SIM223` confound in the
   scratch relaxation, and subtracting it uniformly was right for nine rows and
   wrong for this one. Uniformity of a confound establishes that it was present,
   not that it was the only cause.

## Environment note

Two branches — `verify/t4a-python` and `verify/t4a-bandit` — fail
`tools/test-build-check-workflow.py` locally, because breaking those steps trips
the pins protecting them (`setup-python-with`, `gate-main-bandit`). In CI the
anchor depends on both, so it skips and the posture test never runs inside
`gate-main`; those two rows rest on that reasoning rather than on a clean local
posture run.
