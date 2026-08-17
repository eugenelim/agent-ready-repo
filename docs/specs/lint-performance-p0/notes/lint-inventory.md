# Lint surface inventory — task zero for `lint-performance-p0`

**Status:** complete · **Captured:** 2026-08-17 · **Host:** darwin 25.5.0, Python 3.13.13

This is the audit that scopes the P0 work. Every lint-like production entry
point and every lint self-test in the repository is classified here, with a
recorded P0 disposition. The disposition column is the scope contract: the
implementation may change a lint **only** if its row says `CHANGE`.

Findings are measured, not inferred. Method is recorded in
[§ Measurement method](#measurement-method) so the after-numbers are
comparable.

---

## Headline result

Of **38** production lint entry points, **7** pack/skill-owned lint scripts,
and **27** lint self-tests audited, exactly **three files** exhibit a P0
pattern:

| File | P0 patterns present |
| --- | --- |
| `tools/lint-pack-test-boundary.py` | per-path Git subprocess · Git subprocess inside traversal · repeated same-root traversal · repeated runner/catalogue parsing · catalogue-wide checks independently rebuilding one inventory |
| `tools/test-lint-pack-test-boundary.py` | falsification rerunning the complete worktree lint for every planted case · real-checkout Makefile mutation · real-checkout file plants |
| `tools/lint-agents-md.py` | one Git subprocess per candidate path |

Everything else is measured clean and carries a justified **no P0 change**
disposition. The single dominant cost is `lint-pack-test-boundary`: **337
`git check-ignore` subprocesses and 32.4 s per invocation**, launched **12
times** by its own falsification suite — a ~6.5-minute floor that alone
explains the 71%-then-stall.

**No second Git-ignore helper is required.** Portable `agentbundle`
catalogue lint/verify and every shipped pack lint were measured at **zero**
`git check-ignore` calls, so a package-local portable resolver would have no
caller. See [§ Distribution boundaries](#distribution-boundaries).

---

## Measurement method

Reproducible; all numbers below come from these three probes.

1. **Git process count** — a counting shim earlier on `PATH` that appends its
   argv to `$GITSHIM_LOG` and `exec`s the real `git`. Counts every Git
   subprocess a lint launches, by subcommand.
2. **Traversal / parse counts** — the lint module loaded via
   `importlib.util`, its internal helpers (`_walk`, `_is_ignored`, `_packs`,
   `_destinations`, `_runner_lines`, `_glob_tree_is_confined`,
   `_projected_packs`) wrapped with counters, then `main()` invoked in-process.
   Distinct-vs-total base paths recorded to separate real work from repeated
   work.
3. **Wall clock** — `/usr/bin/time -p` on the bare CLI with no shim, warm
   filesystem cache.

Structural counts (1) and (2) are the normative evidence. Wall clock (3) is
supporting evidence only and is deliberately **not** asserted in CI.

---

## Scope classes

Per the three execution models this spec adopts:

- **pack/skill-local** — complete correctness boundary is one owning pack or
  one owning skill; needs no peer catalogue state.
- **catalogue-wide** — enforces a relationship *across* packs, projections,
  profiles, rosters, runners, or shared contracts; one pack can conflict with
  another.
- **repo-global** — non-catalogue repository surface (CI parity, docs
  structure, site/workflow parity, release policy, security-gate form, root
  config).
- **hybrid** — a file carrying checks in more than one class.

Classification is **per check**, not per file. `lint-pack-test-boundary.py`
is the case that matters: three of its six checks read one pack at a time,
but its runner, projection, coverage and confinement contracts all depend on
the complete catalogue, so the **file is catalogue-wide** and its checks are
individually annotated in
[§ lint-pack-test-boundary, per check](#lint-pack-test-boundary-per-check).

---

## 1. Catalogue-wide lints

| Entrypoint/check | Owner | Scope class | Gate wiring | Traversal roots | Ignore semantics | Git process shape | Repeated work | Self-test model | P0 disposition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `tools/lint-pack-test-boundary.py` (6 checks) | repo tooling | catalogue-wide (hybrid per check) | `.github/workflows/docs.yml:161`; `tools/test-all.py:120`. Not in `pre_pr_catalogue.py`, not a direct Make target | `packs/*/.apm`, `packs/*/tests`, `packs/*/tests/skills/*`, `.claude/skills/*`, `.agents/skills/*`, 6 runner files | **skips** gitignored paths — build residue (`__pycache__` etc.) is not authored content, so not a boundary violation | **337 `check-ignore`, one per candidate path**, launched from inside `_walk()` | `_walk` 141 calls / 109 distinct bases; `_glob_tree_is_confined` 45 / 16 distinct; `_runner_lines` ×2; `_destinations` ×2; `_packs` ×5 | real-worktree mutation | **CHANGE** — every P0 pattern |
| `agentbundle catalogue lint` / `--deep` | portable agentbundle | catalogue-wide | `build-check` chain; `pre_pr_catalogue.py` step 1 | per-pack `glob`/`rglob` under `packs/*`, `profiles/*.toml`, seeds via `os.walk(followlinks=False)` | does not consult Git ignore | **0 Git subprocesses** | none observed; bounded per-pack globs | pytest, fixture catalogues | **no change** — 5.89 s, zero Git calls; bounded per-pack globs only. Churning it is explicitly out of scope |
| `agentbundle catalogue verify` | portable agentbundle | catalogue-wide | `build-check` chain; `pre_pr_catalogue.py` step 1 | `dist/`, `packs/*/.apm/skills/*`, `agents/`, `commands/` | uses `git ls-files` for tracked-file set | **1 `ls-files`, already batched** for the whole tree | none observed | pytest, fixture catalogues | **no change** — 13.47 s, one batched Git call. Already the target shape |
| `agentbundle` skill-spec lint (`skill_spec_lint.py`) | portable agentbundle | catalogue-wide | invoked by catalogue lint; `pre_pr_catalogue.py:114` | `packs/*/.apm/skills`, `packs/*/pack.toml` | no Git ignore use | 0 | bounded `glob("*/…")` per root | pytest unit | **no change** — bounded globs, no Git |
| `agentbundle` `build/lint_packs.py` | portable agentbundle | catalogue-wide | build pipeline | per-subtree `rglob("*")` | no Git ignore use | 0 | per-subtree walk, single pass | pytest unit | **no change** — one bounded pass per subtree |
| `tools/lint-pack-descriptions.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py` | `packs/*/pack.toml` | no Git ignore use | 0 | none | `tools/test-lint-pack-descriptions.py`, temp fixture | **no change** — 0.22 s, no Git |
| `tools/lint-plugin-roster.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py` | `packs/*`, roster files | no Git ignore use | 0 | none | temp fixture | **no change** — 0.18 s, no Git |
| `tools/lint-plugin-membership.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py` | `packs/*`, plugin manifests | no Git ignore use | 0 | none | temp fixture | **no change** — 0.29 s, no Git |
| `tools/lint-plugin-route-docs.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py` | plugin route docs | no Git ignore use | 0 | none | temp fixture | **no change** — 0.27 s, no Git |
| `tools/lint-pack-journeys.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py:132` | `packs/*` journey files | no Git ignore use | 1 (`rev-parse`, root discovery, loop depth 0) | none | temp fixture | **no change** — 0.52 s; one root-discovery call |
| `tools/lint-journey-contract.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py:134` | journey contracts across packs | no Git ignore use | 1 (`rev-parse`) | none | temp fixture | **no change** — 0.43 s |
| `tools/lint-knowledge-surface-parity.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py:123` | knowledge surfaces across packs | no Git ignore use | 1 (`rev-parse`) | none | temp fixture | **no change** — 0.28 s |
| `tools/lint-catalogue-curation-guard.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py` | `catalogue.toml`, `packs/*` | no Git ignore use | 1 (`rev-parse`) | none | temp fixture | **no change** — 2.68 s; single pass |
| `tools/lint-experience-agnostic.py` | repo tooling | catalogue-wide | `pre_pr_catalogue.py` | `packs/*` skill text | no Git ignore use | 1 (`rev-parse`) | none | temp fixture | **no change** — 0.44 s |
| `tools/lint-conformance-portability.py` | repo tooling | catalogue-wide | `build-check` | `tests/conformance` | no Git ignore use | 0 | none | none | **no change** — 0.18 s, one bounded `rglob` |
| `tools/lint_zone_violations.py` | repo tooling | catalogue-wide | `build-check` | pack zone trees | no Git ignore use | 0 | none | none | **no change** — 0.37 s; three bounded `rglob`s over distinct roots |
| `tools/catalogue/check_contract_parity.py` | catalogue tooling | catalogue-wide | `pre_pr_catalogue.py` | `contracts/` | no Git ignore use | 0 | none | pytest | **no change** — no Git, single pass |
| `tools/catalogue/sync_contract_inventory.py` | catalogue tooling | catalogue-wide | `pre_pr_catalogue.py` | `contracts/` | no Git ignore use | 0 | none | pytest | **no change** |
| `tools/catalogue/sync_authoring_scaffold.py` | catalogue tooling | catalogue-wide | `pre_pr_catalogue.py` | scaffold trees | no Git ignore use | 0 | none | pytest | **no change** |
| `tools/check-artifact-contents.py` | repo tooling | catalogue-wide | `build-check` | `dist/` archives | no Git ignore use | 0 observed | none | none | **no change** — 0.19 s; needs a built `dist/` (exit 2 bare) |
| `tools/check-contract-drift.py` / `tools/repo/check_contract_drift.py` | repo tooling | catalogue-wide | `build-check` | `contracts/` | no Git ignore use | 0 | none | `tools/test-check-contract-drift.py`, temp fixture | **no change** — 2.10 s, no Git |
| `tools/check-atlassian-phase3-readiness.py` | repo tooling | catalogue-wide (one pack's readiness) | invoked by no workflow (recorded in `_NO_RUNNER`) | `packs/atlassian/**` | no Git ignore use | 3, loop depth 0 | none | 4 CLI launches, bounded to one pack | **no change** — bounded to a single pack; no ignore-query loop |

### `lint-pack-test-boundary`, per check

Recorded per check because the file is hybrid and the spec's scope-class
treatment differs by class. The **file** stays catalogue-wide: a partial run
must never print the six-check terminal wording.

| Check | Class of the check itself | Why the file is still catalogue-wide |
| --- | --- | --- |
| `apm-carries-no-tests` | pack-local per pack | must enumerate **all** packs; a vacuous empty iteration is an explicit failure |
| `projection-carries-no-tests` | catalogue-wide | asserts each pack in the self-host recipe's include list is actually projected — needs the recipe **and** the projected trees |
| `tests-live-in-the-pack-tree` | pack-local per pack | must enumerate all packs; vacuity is a failure |
| `runners-keep-suites-isolated` | catalogue-wide | one pytest invocation spanning two packs' suites is a cross-pack conflict |
| `every-suite-dir-has-a-runner` | catalogue-wide | global coverage relation between all destinations and all runner files |
| `pack-tests-stay-in-pack` | pack-local per pack, global exemption set | needs every pack's test tree; `_NO_RUNNER` staleness is a global relation |

---

## 2. Repo-global, non-catalogue lints

| Entrypoint/check | Owner | Scope class | Gate wiring | Traversal roots | Ignore semantics | Git process shape | Repeated work | Self-test model | P0 disposition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `tools/lint-agents-md.py` | repo tooling | repo-global | `.github/workflows/docs.yml:86`; `pre_pr_catalogue.py:113` | root `AGENTS.md`, `packs/core/seeds/AGENTS.md`, projected docs; **3 fixed gitignore probe paths** | **asserts probes ARE ignored** — inverted vs. the boundary lint; a non-ignored probe calls `note()`, which is **fatal** (`fail = 1` → exit 1) | **3 `check-ignore`, one per probe path** (line 313, inside a `for probe in (...)` loop) | none beyond the 3 probes | 3 fixture-based self-tests (see § 4) | **CHANGE** — one Git subprocess per candidate path. 3 → 1 batched. Git-missing contract **differs today**: no `FileNotFoundError` guard, so absent Git raises. Unified to fail-open by authorised decision (2026-08-17); because its probe assertion is inverted, "nothing ignored" yields a clean `exit 1` with 3 drift notes rather than a silent pass |
| `tools/lint-ci-parity.py` | repo tooling | repo-global | `build-check`; Make | `Makefile`, `.github/workflows/*.yml`, gate chain | no Git ignore use | 0 | none | `tools/test-lint-ci-parity.py` — **fixture roots via `--root` + one real-root e2e launch** | **no change** — 0.13 s. Already the exact target architecture; used as the repo precedent for the boundary-lint refactor |
| `tools/lint-build.py` | repo tooling | repo-global | `pre_pr_catalogue.py:120` | build outputs | no Git ignore use | 3; `git merge-base` in a **bounded 2-element base-ref fallback loop** that returns on first success | none | none | **no change** — not an ignore query; bounded fallback, not per-candidate |
| `tools/lint-nosec-form.py` | repo tooling | repo-global (security-gate form) | `build-check` | `tools/`, `packs/`, `packages/` Python sources | no Git ignore use | 1 (`rev-parse`) | none | `tools/test-lint-nosec-form.py`, temp fixture | **no change** — 5.33 s, the slowest non-P0 lint, but one bounded pass and zero ignore queries. Recorded as P1 watch item only |
| `tools/lint-sso-config.py` | repo tooling | repo-global | `pre_pr_catalogue.py:121` | SSO config | no Git ignore use | 0 | none | temp fixture | **no change** — 0.25 s |
| `tools/lint-site-scope-parity.py` | repo tooling | repo-global (site parity) | `pre_pr_catalogue.py` | `site.toml`, `docs-site/` | no Git ignore use | 0 | none | temp fixture | **no change** — 0.35 s |
| `tools/lint-web-journey-parity.py` | repo tooling | repo-global (site parity) | `pre_pr_catalogue.py:129` | `web/`, journeys | no Git ignore use | 1 (`rev-parse`) | none | temp fixture | **no change** — 0.40 s |
| `tools/lint-claude-plugin-publish-control.py` | repo tooling | repo-global (release policy) | `build-check` | plugin publish config | no Git ignore use | 0 | none | temp fixture | **no change** — 0.18 s |
| `tools/lint-guide-titles.py` | repo tooling | repo-global (docs structure) | `.github/workflows/docs.yml` | `docs/guides/`, `guides/` | no Git ignore use | 0 | none | none | **no change** — 1.46 s, one bounded `rglob` |
| `tools/lint-guides-no-repo-only-refs.py` | repo tooling | repo-global (docs structure) | `.github/workflows/docs.yml` | `guides/` | no Git ignore use | 0 | none | none | **no change** — 1.46 s |
| `tools/validate_guides.py` | repo tooling | repo-global (docs structure) | `.github/workflows/docs.yml` | `docs/guides/`, `guides/` | no Git ignore use | 0 | none | none | **no change** — 0.87 s, one bounded `rglob` |
| `tools/check-guide-index.py` | repo tooling | repo-global (docs structure) | `.github/workflows/docs.yml` | guide index + tree | no Git ignore use | 0 | none | none | **no change** — 0.43 s |
| `tools/check-docs-contrast.py` | repo tooling | repo-global (docs a11y) | `.github/workflows/docs.yml` | docs theme tokens | no Git ignore use | 0 | none | none | **no change** — 0.55 s |
| `tools/check-rendered-site-links.py` | repo tooling | repo-global (site parity) | `.github/workflows/docs.yml` | rendered site output | no Git ignore use | 0 | single `os.walk` of rendered output | none | **no change** — 0.24 s; needs rendered site (exit 2 bare) |
| `tools/check-site-plugin-offers.py` | repo tooling | repo-global (site parity) | `.github/workflows/docs.yml` | site plugin offers | no Git ignore use | 0 | none | `tools/test-check-site-plugin-offers.py`, temp fixture | **no change** — 0.41 s |
| `tools/lint-ruff.py` | repo tooling | repo-global (style) | `make lint-ruff`; `make ci` | delegates to `ruff` | ruff's own ignore handling | 1 (`ruff`, not Git) | none | none | **no change** — thin delegator |
| `tools/lint-mypy.py` | repo tooling | repo-global (types) | `make lint-mypy`; `make ci` | delegates to `mypy` | mypy's own handling | 1 (`mypy`, not Git) | none | none | **no change** — thin delegator |
| `tools/repo/check_release_impact.py` | repo tooling | repo-global (release policy) | release gate | changed-file list | no Git ignore use | `git diff --name-only` in a **bounded 2-form fallback loop**, returns on first success | none | none | **no change** — not an ignore query; not per-candidate |
| `tools/repo/build_gate_chain.py` | repo tooling | repo-global (gate orchestration) | `build-check` | gate chain declaration | n/a | 0 | none | covered by ci-parity | **no change** — orchestration only |

---

## 3. Pack/skill-local lints (shipped)

All are shipped pack content and must **not** depend on repo-only helpers.

| Entrypoint/check | Owner | Scope class | Gate wiring | Traversal roots | Ignore semantics | Git process shape | Repeated work | Self-test model | P0 disposition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` | core pack (work-loop skill) | pack/skill-local (one spec dir) | work-loop finish checklist | one `docs/specs/<slug>/` | no Git ignore use | 4, all loop depth 0 (`rev-parse` ×2, bounded base-ref resolve, `git show`) | none | `packs/core/tests/skills/work-loop/test_lint_spec_status*.py`, temp fixture | **no change** — already bounded to one spec dir; no ignore query |
| `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py` | core pack (work-loop skill) | pack/skill-local | work-loop | one spec dir + bounded roots | no Git ignore use | 1 (`rev-parse`, loop depth 0) | single `os.walk(followlinks=False)` per root | `test_lint_traceability.py`, temp fixture | **no change** — one bounded walk; `followlinks=False` already correct |
| `packs/core/.apm/skills/work-loop/scripts/lint-knowledge.py` | core pack | pack/skill-local | work-loop | knowledge journal partitions | no Git ignore use | 1 (`rev-parse`) | none | pytest | **no change** |
| `packs/core/.apm/skills/work-loop/scripts/check-spec-status.py` | core pack | pack/skill-local | work-loop | one spec file | n/a | 0 | none | pytest | **no change** — no subprocess at all |
| `packs/core/.apm/skills/work-loop/scripts/check-base-freshness.py` | core pack | pack/skill-local | work-loop preflight | git refs | n/a | `git config --get` in a bounded key loop | none | `test_check_base_freshness.py`, temp git repos | **no change** — not an ignore query; base-freshness optimization is an explicit non-goal |
| `packs/core/.apm/skills/receive-brief/scripts/lint-brief-coverage.py` | core pack (receive-brief skill) | pack/skill-local (one brief) | receive-brief | one brief file | no Git ignore use | 1 (`rev-parse`) | none | `test_lint_brief_coverage.py`, temp fixture | **no change** |
| `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py` | core pack | repo-global (workspace index) | session start; work-loop ORIENT | `workspace.toml`, `docs/specs/*/spec.md` | no Git ignore use | 0 | bounded by subcommand (`status` = Type 2+3 only; `reconcile` adds Type 1) | `tools/test_workspace_status_cli.py`, temp fixture | **no change** — already has bounded/full scan modes by design |

---

## 4. Lint self-tests (falsification suites)

Measured by full-production-CLI launch count and by whether plants mutate the
real checkout.

| Self-test | Subject | Full-lint CLI launches | Real-tree mutation | P0 disposition |
| --- | --- | --- | --- | --- |
| `tools/test-lint-pack-test-boundary.py` | `lint-pack-test-boundary.py` | **12** (lines 421, 436, 450, 459, 478, 498, 519, 551, 573, 613, 634, 661) | **yes** — plants into `packs/figma/.apm/**`, `packs/figma/tests/**`, `packs/contracts/tests`, and **rewrites the real root `Makefile` twice** (lines 568, 606) | **CHANGE** — 12 × 32.4 s ≈ 6.5 min floor. Reduce to fixture-based plants + a minimal real-tree e2e layer |
| `tools/test-lint-ci-parity.py` | `lint-ci-parity.py` | 3 (1 real-root, 2 fixture-root via `--root`) | no — fake roots in temp dirs | **no change** — already the target architecture. Note it anchors aggregator extraction: line 292 asserts `run_call_targets(AGGREGATOR) == {"tools/lint-agents-md.py"}`, so the agents-md `_run` line in `pre_pr_catalogue.py` must stay byte-stable |
| `tools/test_lint_agents_md_legacy_block.py` | `lint-agents-md.py` check 10d | 1 | no — temp fixture (heavy `tmp_path` use) | **no change** — fixture-based already; asserts a warning shape unrelated to the probe loop |
| `tools/test_lint_agents_md_diataxis_block.py` | `lint-agents-md.py` check 8 | 1 | no — temp fixture | **no change** — fixture-based already |
| `tools/test_lint_agents_md_risk_block.py` | `lint-agents-md.py` check 10g | 1 | no — temp fixture | **no change** — fixture-based already; asserts risk-trigger block byte-equality, not the probe loop |
| `tools/test-check-atlassian-phase3-readiness.py` | readiness checker | 4 | no | **no change** — bounded to one pack; no worktree scan |
| `tools/test-lint-sso-config.py` | `lint-sso-config.py` | 2 | no — temp fixture | **no change** |
| `tools/test-lint-experience-agnostic.py` | `lint-experience-agnostic.py` | 1 | no — temp fixture | **no change** |
| `tools/test-lint-journey-contract.py` | `lint-journey-contract.py` | 1 | no — temp fixture | **no change** |
| `tools/test-lint-knowledge-surface-parity.py` | parity lint | 1 | no — temp fixture | **no change** |
| `tools/test-lint-pack-journeys.py` | `lint-pack-journeys.py` | 1 | no — temp fixture | **no change** |
| `tools/test-lint-web-journey-parity.py` | parity lint | 1 | no — temp fixture | **no change** |
| `tools/test-check-contract-drift.py` | drift check | 1 | no — temp fixture | **no change** |
| `tools/test-run-pack-evals.py` | pack-evals runner | 1 | no | **no change** — contains **one** `git check-ignore` on a **single** path (line 686) asserting a real `.gitignore` fact. One candidate, one process; it is a self-test, not a production lint, so it is outside the source-enforcement scope. Documented, not migrated |
| `tools/test-lint-nosec-form.py` | `lint-nosec-form.py` | 0 (in-process) | no — temp fixture | **no change** |
| `tools/test-lint-catalogue-curation-guard.py` | curation guard | 0 | no — temp fixture | **no change** |
| `tools/test-lint-claude-plugin-publish-control.py` | publish control | 0 | no — temp fixture | **no change** |
| `tools/test-lint-pack-descriptions.py` | pack descriptions | 0 | no — temp fixture | **no change** |
| `tools/test-lint-plugin-membership.py` | plugin membership | 0 | no — temp fixture | **no change** |
| `tools/test-lint-plugin-roster.py` | plugin roster | 0 | no — temp fixture | **no change** |
| `tools/test-lint-plugin-route-docs.py` | route docs | 0 | no — temp fixture | **no change** |
| `tools/test-lint-site-scope-parity.py` | site scope parity | 0 | no — temp fixture | **no change** |
| `tools/test-check-site-plugin-offers.py` | site plugin offers | 0 | no — temp fixture | **no change** |
| `packs/core/tests/skills/work-loop/test_lint_spec_status*.py` | spec-status lint | 0 | no — temp fixture | **no change** |
| `packs/core/tests/skills/work-loop/test_lint_traceability.py` | traceability lint | 0 | no — temp fixture | **no change** |
| `packs/core/tests/skills/receive-brief/test_lint_brief_coverage.py` | brief coverage | 0 | no — temp fixture | **no change** |
| `packages/agentbundle/tests/**` (catalogue lint/verify/skill-spec) | portable lints | pytest in-process | no — fixture catalogues | **no change** |

---

## 5. Gate wiring and aggregators

Terminal behaviour of all of these is preserved unchanged by this spec.

| Aggregator / target | Invokes | Note |
| --- | --- | --- |
| `.github/workflows/docs.yml:161` | `python3 tools/lint-pack-test-boundary.py` | the production CI gate for the boundary lint |
| `.github/workflows/docs.yml:166` | `python3 tools/test-lint-pack-test-boundary.py` | the falsification gate — comment records that `test-all.py` is run by no workflow, so **this step is the gate** |
| `.github/workflows/docs.yml:86` | `python tools/lint-agents-md.py` | agents-md CI gate |
| `tools/catalogue/pre_pr_catalogue.py` | ~30 lints as separate processes, verification-first, fail-fast | process-per-guard shape retained; in-process conversion is explicitly P1 |
| `tools/test-all.py:120,122` | boundary lint + its self-test | umbrella runner; invoked by no workflow |
| `make pre-pr` (`Makefile:62`) | `pre_pr_catalogue.py` | unchanged |
| `make build-check` (`Makefile:123`) | portable verify + repo policy gates + SAST | unchanged |
| `make ci` (`Makefile:381`) | `build-check pre-pr lint-ruff lint-mypy test` | unchanged |

---

## Distribution boundaries

The spec permits one shared Git-ignore resolver **per legitimate distribution
boundary**. Measured, only **one** boundary has a caller:

| Boundary | Callers needing batched ignore resolution | Decision |
| --- | --- | --- |
| repo-only `tools/` | `lint-pack-test-boundary.py`, `lint-agents-md.py` | **one helper**, repo-only |
| portable `agentbundle` | **none** — catalogue lint 0 Git calls, verify 1 batched `ls-files` | **no helper.** Adding one would have no caller; forbidden by *add an option only when a second caller actually needs to differ* |
| shipped pack/skill content | **none** — all 7 pack lints measured at 0 `check-ignore` | **no helper.** Shipped code must stay independent of repo-only `tools/`; nothing needs it |

Consequence: exactly **one** helper module. The source-level enforcement test
therefore has exactly one approved home to whitelist.

---

## Baseline evidence (before)

`tools/lint-pack-test-boundary.py`, one full six-check invocation:

| Metric | Before |
| --- | --- |
| `git check-ignore` subprocesses | **337** |
| all other Git subprocesses | 0 |
| `_walk()` calls / distinct bases | **141 / 109** (32 redundant) |
| `_glob_tree_is_confined()` calls / distinct bases | **45 / 16** (29 redundant) |
| `_runner_lines()` invocations (re-reads + re-parses 6 runner files) | **2** |
| `_destinations()` invocations (re-walks 32 skill dirs) | **2** |
| `_packs()` invocations | **5** |
| `_projected_packs()` invocations | 1 |
| inventory constructions | **none — no inventory exists** |
| wall clock, one invocation | **32.35 s** |

`tools/test-lint-pack-test-boundary.py`:

| Metric | Before |
| --- | --- |
| full production-lint CLI launches | **12** |
| implied `check-ignore` subprocesses across the suite | **~4 044** (12 × 337) |
| real-worktree scans | **12** |
| real `Makefile` rewrites | **2** |
| real pack-tree plants | 7 distinct plant sites |
| suite floor from lint launches alone | **≈ 6.5 min** — over the 5-minute inner-loop budget |

`tools/lint-agents-md.py`:

| Metric | Before |
| --- | --- |
| `git check-ignore` subprocesses | **3** (one per probe) |
| wall clock | 0.82 s |

Every other production lint: **0.13 s – 5.33 s**, and **0** `check-ignore`
subprocesses. Full sweep in the P0 spec's evidence section.

---

## Existing backlog item this audit closes

`workspace.toml [backlog].open` already carries
`selftest-mutates-tracked-makefile`:

> Stop `tools/test-lint-pack-test-boundary.py` from mutating the real
> `Makefile` in place; a concurrent `git add -A` commits its injected
> violation and the failure surfaces only in CI.

The recorded history is concrete — *"That happened on PR #961"* — and the
recorded fix (*"build the fixture in a tmpdir copy, or drive the linter with a
`--makefile` argument, so no tracked file is ever mid-mutation"*) is the same
change this spec makes via the fixture-root option. The Wave 2 falsification
refactor closes this item; it moves to `[backlog].closed` at finish time rather
than being deferred again.

Its trailing note — *"Same pattern is worth auditing across `tools/test-*`"* —
is discharged by § 4 of this inventory: all 26 other lint self-tests were
audited and none mutates a tracked file.

## Recorded P1 residuals

Out of scope here; captured so they are not silently lost.

1. **Cross-process duplicate scans in `pre_pr_catalogue.py`.** ~30 lints run
   as separate processes; several independently enumerate `packs/*`. Sharing
   one inventory across processes needs a persistent cache or an in-process
   aggregator — both explicit non-goals.
2. **`lint-nosec-form.py` at 5.33 s** is the slowest non-P0 lint. One bounded
   pass over three source roots, no ignore queries; a P0 change is not
   warranted.
3. **`agentbundle catalogue verify` at 13.47 s** is the slowest single gate.
   Its one Git call is already batched; cost is filesystem traversal of
   `dist/`.
