# Verification ledger

Execution evidence for `spec.md`, recorded after the supervisor run reached `terminal`.

## Gates of record (final tree)

| Gate | Result |
| --- | --- |
| `pytest packs/iac-terraform/tests/skills/generate-iac -q` | 730 passed, about 14 s |
| `make lint-ruff lint-mypy` | clean (ruff 0.16.10; mypy 158 source files) |
| `make precheck` (self-host check, deep lint, bandit on the five new/changed Python files) | clean |
| `agentbundle catalogue self-host --check` | ok, no projection diff |
| `lint-spec-status.py` | spec metadata clean |

## Terraform-only journey

`test_terraform_only_journey.py` ran with Terraform 1.17.2 and the built-in `terraform_data` provider: 20 passed in about 4 s. Without the binary on `PATH` the same file reports 20 skipped with a stated reason. CI has no `terraform` binary, so CI skips these cases (see Assumptions in the spec).

## Acceptance verification

Three independent Codex verifier passes ran each of the 41 criteria against the real artifacts.

1. Pass 1: 39 pass, 2 fail. AC-0017: a `discover` `file-limit` stop echoed a discovered file name. AC-0036: one resolving evidence id masked other unresolved ids.
2. Repair T6 (tests failed before the fix, 7 cases). Pass 2: 41 pass.
3. Review found that `check-review` refused a correctly bound saved plan over 262,144 bytes (a real 150-resource plan is 678,210 bytes). Repair T7 streams saved plans and evidence under 536,870,912 bytes. Pass 3: 41 pass with 103 independent observations.

## Reviews

| Role | Round 1 | Round 2 |
| --- | --- | --- |
| adversarial-reviewer | 1 blocker (this ledger, a closeout artifact, controlled elsewhere), 1 nit (stale eval expectation, fixed in T7) | clean |
| security-reviewer | clean | clean |
| quality-engineer | 1 concern (review artifact size cap, fixed in T7) | clean |

All reviewers ran as Codex headless roles (read-only) on the committed diff. The pre-approval spec and plan review ran two rounds with an adversarial and a security reviewer; their 7 concerns were fixed before approval.

## Limits left open

- The journey proves the chain with a built-in provider and no cloud account; it does not prove behavior against a real cloud provider schema or a remote backend.
- `authoring_gate.py` checks structure, digests and that cited evidence resolves; it cannot prove a reviewer read the evidence or that a source says what its summary line claims.
- Optional core integration is exercised only through the summary's `integrations` and `sources` records; the core resolver's real output was not read.
- CI does not install Terraform, so the real-engine cases skip there.
