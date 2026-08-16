# Plan: npm-sca-gate

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

### The integration-point decision (spec Objective)

Four options were on the table for where npm SCA runs:

| | Option | Local↔CI parity | Notes |
|---|---|---|---|
| (a) | New job in `ci-security.yml` | **No** | `ci-security.yml` is out of `lint-ci-parity.py`'s `WORKFLOW_SCOPE` — a step added there has no local counterpart and nothing detects that |
| (b) | New standalone workflow | No | Fails `lint-ci-parity` until classified in `WORKFLOW_SCOPE`; classifying it out-of-scope reproduces (a)'s defect by hand |
| (c) | `.github/dependabot.yml` only | n/a | Not a gate — proposes bumps, never blocks a merge. Does not discharge the deferral |
| (d) | **New leg on `make sast`** | **Yes, by construction** | Already chained into `build-check` → `build-check.yml`, the one workflow `lint-ci-parity` holds in scope |

**Chosen: (d).** ADR-0017 named the gate "SAST/SCA" and built it with `pip-audit`
as the SCA leg. npm is a second ecosystem on the same control, not a new control.
Putting it anywhere else would leave the repo with two SCA gates whose coverage a
reader has to reconcile by hand.

The decision has one non-obvious dependency: **`SAST_CONFIG` must gain both
lockfiles.** `build-check.yml` computes SAST relevance from
`make -s print-sast-dirs` / `print-sast-config` against the PR's changed files,
and sets `SKIP_SAST=1` when nothing matches. Neither `docs-site/` nor `web/` is
under `SAST_DIRS` (`tools packs packages tests`), so without the `SAST_CONFIG`
addition a lockfile-only PR — precisely the diff shape a dependency bump has —
would skip the gate that exists to check it. This is the same class of defect
`spec/local-gate-ci-parity` was written to close, so repeating it here would be
unforgivable.

### The wrapper decision (spec § Boundaries, AC3)

`npm audit` has no per-advisory ignore. Its only lever is `--audit-level`, which
is repo-wide and coarse: the escape hatch for one unfixable transitive advisory
is to stop gating an entire severity band.

That is not a hypothetical problem for this repo. The `pip-audit` leg in
`make sast` runs today with four live `--ignore-vuln` suppressions (Semgrep's
hard-pinned `mcp` and `click` transitive CVEs), each carrying a written
diagnosis and an unblock condition. The observed steady state of this control,
in this repo, includes suppressions. A gate shipped without an escape hatch
would wedge every merge the first time a no-fix-available advisory lands — and
the hatch would then be designed under exactly the pressure that produces a bad
one.

So: a thin stdlib wrapper that parses `npm audit --json` and applies an
ID-keyed allowlist. It ships **empty**; the mechanism exists so the first
suppression is a reviewed diff rather than a `--audit-level` downgrade.

Rejected: two bare `npm audit` lines in the `sast:` recipe (~2 lines vs ~150
including the self-test). Cheaper today, and it forfeits the allowlist, the
three-way exit code, lockfile discovery, and any way to prove the gate is not a
no-op.

### Discovery over a hardcoded list

The tool walks for `package-lock.json` rather than naming `docs-site` and `web`.
A hardcoded pair silently under-covers the moment a third npm project lands —
the same failure mode as `WORKFLOW_SCOPE` being a hand-maintained list, which
`lint-ci-parity` solves by failing on any unclassified file. Discovery is
cheaper here than classification: there is nothing to decide per lockfile.

`node_modules/` is excluded. Nested lockfiles inside an installed tree are
dependency artifacts, not projects, and auditing them would both duplicate
findings and depend on whether someone happened to run `npm ci`.

### Remediation (AC5)

`npm audit fix --package-lock-only` in each project. Verified on scratch copies
before planning: it resolves all findings in both, and leaves both
`package.json` files byte-identical — every fix is a transitive patch bump.

| Project | Change |
|---|---|
| `docs-site/` | `js-yaml` 4.3.0 → 4.3.1, `nanoid` 3.3.16 → 3.3.18 |
| `web/` | the same two, plus `postcss` 8.5.19 → 8.5.26 |

The install-script invariant is re-checked after the bump: the
`"hasInstallScript": true` set is unchanged in both lockfiles
(`esbuild@0.28.1`, `fsevents@2.3.3`, and in `web/` a pre-existing
`playwright/node_modules/fsevents@2.3.2`). That third entry already sits outside
`web/package.json`'s `allowScripts` keys and is **pre-existing, not introduced
here** — it is the reason `npm-allowscripts-enforcement` is deferred rather than
built: turning that invariant into a gate today would land CI red on arrival.

## Tasks

### T1 — `tools/audit-npm.py` + self-test (AC1, AC3, AC4)

**Tests:** `tools/test-audit-npm.py`, TDD, written first as a red stub. Eight
cases against synthetic `npm audit --json` fixtures (no network, no npm):
clean passes; `high` fails; `critical` fails; `moderate` passes; allowlisted
`high` passes and prints; allowlist entry missing `reason`/`unblocked_when` is
a tool error; **a payload carrying an `error` key is a tool error, not a pass**;
**a payload with no `auditReportVersion` is a tool error, not a pass**. Plus a
discovery case: a lockfile under `node_modules/` is not discovered.

The last two are the fail-closed cases from AC1a and are the reason this task is
TDD rather than goal-based — they are exactly the paths a live run against a
healthy registry never exercises, so nothing but a fixture can prove them.

**Approach:** pure functions for the two decidable parts — `discover_lockfiles`
(path → list) and `evaluate(report, allowlist)` (parsed JSON → verdict) — with
`subprocess` confined to one thin `run_audit` shim the tests do not touch.
Mirrors `tools/audit-requirements.py`'s shape. Three-way exit: 0 clean,
1 findings, 2 tool error.

### T2 — chain into `make sast` + `SAST_CONFIG` (AC2)

**Tests:** goal-based. `Done when:` `make -s print-sast-config` names both
lockfiles, and `make sast` reaches the npm leg (observed in a real run).

**Approach:** self-test line then audit line, placed with the other SCA legs and
before the Semgrep scan, so the fast deterministic check fails before the slow
network scan. `command -v npm` guard alongside the existing `bandit` /
`pip-audit` / `semgrep` guards.

### T3 — register in `tools/test-all.py` (AC4)

**Tests:** goal-based. `Done when:` `python3 tools/test-all.py` runs the new
entry and exits 0.

**Approach:** one `TESTS` tuple, alphabetical position. Without this the
self-test only runs inside `make sast`; the umbrella suite is where a
contributor changing the linter looks.

### T4 — remediate both lockfiles (AC5)

**Tests:** goal-based + manual QA. `Done when:` `npm audit --audit-level=moderate`
reports 0 in each; `git diff --stat` shows no `package.json`; the
`hasInstallScript` set is unchanged in both.

**Approach:** `npm audit fix --package-lock-only` per project. Verify the new
gate then passes against the real tree — T4 is what turns T1's gate from
"parses fixtures" into "exits 0 on this repo".

### T5 — docs + ADR + backlog (AC6, AC7, AC8)

**Tests:** goal-based. `Done when:` `tools/lint-agents-md.py` passes (≤150-line
subdirectory cap); `lint-spec-status.py` resolves both deferral anchors against
`[backlog].open`.

**Approach:** rewrite `docs-site/AGENTS.md`'s Known-gap paragraph; add the
matching paragraph to `web/AGENTS.md`; write ADR-0083 and add its back-reference
to ADR-0017's `Related:` line; in `workspace.toml`, remove
`docs-site-npm-sca-gap` and add the two new deferral slugs with
cold-start-sufficient comments.

### T6 — gates + PR (AC9)

**Tests:** manual QA. `Done when:` `make ci` observed green locally; CI observed
green on the PR with the SAST leg running (not skipped).

## Constraints

- Pure-stdlib Python; no new dependency (root `AGENTS.md`; ADR-0017's
  zero-runtime-dependency posture).
- `tools/audit-npm.py` must not mutate anything — no `npm audit fix`, no
  `npm install`, no lockfile write.
- Subdirectory `AGENTS.md` ≤ 150 lines, CI-enforced.
- `docs.yml` `paths:` already covers `docs-site/**/AGENTS.md` and
  `web/**/AGENTS.md`, so no workflow path change is needed for T5.

## Risks

| Risk | Mitigation |
|---|---|
| Advisory database moves under us — a clean gate reddens with no diff | Accepted, and identical to the `pip-audit` and Semgrep-registry legs ADR-0017 already accepts. The allowlist is the response |
| `npm` absent on a contributor machine | Explicit `command -v npm` guard with the install hint, matching the three existing guards. Never a silent skip |
| Network required at gate time | Accepted; `make sast` is already network-bound (Semgrep registry, PyPI). `SKIP_SAST=1` remains the documented offline path |
| The `SAST_CONFIG` addition is forgotten | AC2 asserts it directly via `make -s print-sast-config`. Note the trap: this PR **cannot** test the predicate end-to-end, because its diff also touches `tools/` (already in `SAST_DIRS`), so `skip_sast=false` either way. Recorded as a stated residual on AC9 rather than claimed as covered |
| The gate reads a registry error as "clean" | AC1a: exit 0 is reachable only from a parseable report carrying `auditReportVersion`. `npm audit` returns non-zero for both "found advisories" and "could not run", so the verdict is taken from the payload, never the exit code. Two of the six self-test cases pin this |

## Changelog

- **Initial draft** — integration point (d) chosen over a new workflow or
  `ci-security.yml` job on local↔CI parity grounds; wrapper chosen over bare
  `npm audit` lines on allowlist grounds, evidenced by the four live
  `--ignore-vuln` suppressions the sibling `pip-audit` leg already carries.
