# RFC-0087 OKF pilot results

Evidence status: pre-release and incomplete. RFC-0087 is accepted, but this
note does not promote OKF authoring, OKF discovery, or either pilot to a final
release state. Model E2E routing measurements, the maintainer update exercise,
and RFC Approver sign-off remain pending.

## Inputs

- Cost-engineering pilot source:
  [`packs/_okf-pilot-cost-engineering/`](../../../packs/_okf-pilot-cost-engineering/)
- Security-checklists OKF source:
  [`packs/core/okf/security-checklists/`](../../../packs/core/okf/security-checklists/)
- Cost cases:
  [`pilot-cases/cost-engineering.json`](pilot-cases/cost-engineering.json)
- Security cases:
  [`pilot-cases/security-checklists.json`](pilot-cases/security-checklists.json)
- Cost hand-authored baseline:
  [`pilot-baselines/cost-engineering-hand-authored.json`](pilot-baselines/cost-engineering-hand-authored.json)
- Security pending model baseline:
  [`pilot-baselines/security-checklists-pending-model-e2e.json`](pilot-baselines/security-checklists-pending-model-e2e.json)
- Cost provenance and licence evidence:
  [`pilot-licenses/cost-engineering.json`](pilot-licenses/cost-engineering.json)
- Adapter preservation spike:
  [`adapter-spike.md`](adapter-spike.md)

The two canonical root OKF indexes declare the repository dual content licence
`Apache-2.0 OR MIT`. The cost pilot licence record identifies only repository
source material and generic placeholders; no external source was acquired for
that pilot.

## Reproducible local evidence

The result record preserves failed or unavailable gates instead of replacing
them with inferred measurements.

| Evidence | Command | Result |
| --- | --- | --- |
| Core compiler check | `python3 packs/catalogue-curation/.apm/skills/compile-okf/scripts/compile_okf.py --root . --pack core --check` | `OKF000 check clean packs/core` |
| Cost compiler check | `python3 packs/catalogue-curation/.apm/skills/compile-okf/scripts/compile_okf.py --root . --pack _okf-pilot-cost-engineering --check` | `OKF000 check clean packs/_okf-pilot-cost-engineering` |
| Real-pilot JSON discovery and release-surface tests | `env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/agentbundle python3 -m pytest -p no:cacheprovider tests/roster/test_okf_catalogue_discovery.py -q` | `3 passed` |
| Focused discovery and version suite | `env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/agentbundle python3 -m pytest -p no:cacheprovider packages/agentbundle/tests/unit/test_okf_discovery.py packages/agentbundle/tests/integration/test_show_cmd.py packages/agentbundle/tests/unit/test_local_scope_t12_show.py packages/agentbundle/tests/unit/test_version.py -q` | Passed after the release-surface boundary repair |
| macOS write-mode determinism (AC22 partial) | Compile each managed pack twice in write mode (`python3 packs/catalogue-curation/.apm/skills/compile-okf/scripts/compile_okf.py --root . --pack <pack>`), then compare the managed tree between the two runs — `git status` stays clean, so the second compile reproduces the first byte for byte | macOS 25.5.0 arm64 / CPython 3.13.13. `_okf-pilot-cost-engineering`: both compiles succeed and leave an identical tree. `core`: write mode refuses both times with `OKF010 packs/core/.apm/skills/security-checklists ownership conflict`, because that managed directory also holds 11 hand-authored `references/*.md` this pilot deliberately retains. Check mode is clean for both packs. |
| Windows knowledge-bundle verification | `agentbundle catalogue self-host --check --windows --root .` gained an `okf compiler checks` stage invoking `tools/check-okf-managed-packs.py` | Wired in required CI. Before it, no Windows runner invoked the compiler: the Windows suite runs the adopter-facing `tools/hooks/pre-pr.py`, while the OKF gate lives in the maintainer aggregator `tools/catalogue/pre_pr_catalogue.py`. Write mode remains unavailable on Windows by design — `_apply_outputs_transactionally` refuses with `OKF010` because `os.supports_dir_fd` is empty there. |
| Adapter preservation spike | `env PYTHONPATH=packages/agentbundle python3 docs/rfc/0087-notes/verify_adapter_spike.py` | All seven adapters passed; nested OKF tree digest `sha256:4c502a8833a955799b8aaa2f52769306fedcaa79c0233dcc086c321ea8366900` |
| Fast repository build check | `SKIP_SAST=1 make build-check` | Passed in supervisor-recorded T8 evidence |
| Full AgentBundle package suite | Isolated-venv `make ci` invocation supplied by the operator on 2026-08-17 | Passed to 100%; the same run also passed the CredBroker package suite |
| Full SAST/SCA path | Isolated-venv `make ci` invocation supplied by the operator on 2026-08-17, with `SKIP_SAST` unset | Passed: Bandit, dependency-audit self-tests, all declared pip-audit inputs, Semgrep, and the Semgrep rule self-test completed successfully |
| Full repository CI | Four isolated-venv `make ci` invocations plus a final targeted artifact-gate invocation supplied by the operator on 2026-08-17 | The first exposed a product-changelog version mismatch. The second exposed two catalogue-navigation consistency defects. The third exposed checkout-only schema dependencies in the real-sdist suite. The fourth cleared all three repairs, passed full SAST/SCA, the root suite (`356 passed`, `46 subtests`), every listed core and pack suite, the site/navigation group (`157 passed`, `2 subtests`), and workspace-status tests (`220 passed`, `13 subtests`) before the real-sdist gate exposed a repository-wide release-metadata assertion in the shipping engine suite. That assertion now lives in the non-shipping roster suite, where its package and repository surfaces are all present. Targeted package and roster tests pass (`8 passed`), the operator's exact real-sdist gate passed (`1 passed`), and an accidental `tools/` directory invocation also passed all `529` collected tool tests before zsh separately rejected the split trailing command fragments. Combined operator evidence therefore covers every local `make ci` leg after the repair without treating the malformed shell command itself as a successful command. |
| Site link check | site build/link gate | Blocked by missing Astro in the local environment; not retried |

## Pilot case and baseline inventory

| Pilot | Frozen cases | Security-critical cases | Baseline evidence | Current status |
| --- | ---: | ---: | --- | --- |
| Cost engineering | 20 | 5 | Frozen hand-authored baseline, same recorded harness shape, top-1 expected-path success `1.0`, security-critical success `1.0`, fabricated paths `0` | Case and baseline prerequisite evidence present; generated-router model E2E pending |
| Security checklists | 20 | 6 | Pending model E2E baseline record with matching case counts | Case-count prerequisite present; generated-router model E2E pending |

## RFC promotion gate accounting

| Gate | Evidence accounted for | Status |
| --- | --- | --- |
| D1 canonical source | Both pilots have canonical OKF source under pack-owned roots; generated output is treated as replaceable. | Evidence present |
| D2 authoring-time projection | Both pilots compile through the `compile-okf` authoring Skill; no AgentBundle runtime CLI verb was added. | Evidence present |
| D3 projection boundary | Generated routers and reviewed Skills are ordinary `.apm/skills/` output and carry compiler manifests. | Evidence present |
| D4 authority boundary | Compiler checks and generated Skills preserve no-tools and inert knowledge boundaries. | Evidence present from compiler and focused tests; model behavior still pending |
| D5 pilot experiment | Cost pilot remains underscore-prefixed and unpublished; security-checklists remains the in-place core pilot. | Partial: experiment assets exist, model E2E and Approver decision pending |
| D6 catalogue discovery | `show --format json` exposes OKF data only as pre-release single-pack discovery and excludes cross-pack publication surfaces. | Evidence present from discovery tests |
| D7 deterministic verification | `compile-okf --check` is wired and clean for both pilots on Linux, Windows, and macOS; fast build-check, the full AgentBundle package suite, and full SAST/SCA passed. | Check-mode evidence present on all three platforms; write-mode evidence is macOS-only and cannot be produced on Windows or for `core` (see AC22) |
| D8 single-version support | Active profile remains `agentbundle-okf/v1` mapping to OKF 0.2. | Evidence present |

## Acceptance criterion accounting

| Criterion | Status |
| --- | --- |
| AC22 | Deferred as unsatisfiable as written (`okf-ac22-write-mode-unsatisfiable-as-written`). Check mode is clean for both pilots on Linux CI, Windows CI, and macOS. Write mode is byte-identical across two compiles for `_okf-pilot-cost-engineering` on macOS, refuses on Windows (`os.supports_dir_fd` empty), and refuses for `core` on every platform (unmanaged siblings in the managed directory). |
| AC23 | The adapter spike preserves nested OKF regular-file bytes across Claude Code, Kiro IDE, Kiro CLI, Copilot, Cursor, Codex, and Gemini. |
| AC24 | The compile-okf Skill and authoring prerequisite are shipped in catalogue-curation. Fast build-check and the operator-supplied isolated-venv full SAST/SCA run passed. |
| AC25 | Both pilots compile through the generic compiler path. No caller-name branch evidence is recorded in the focused compiler tests. |
| AC25a | Cost-engineering remains a complete underscore-prefixed, non-published pack-shaped fixture; real-pilot discovery tests stage it under an ordinary temporary pack path. |
| AC26 | Cost-engineering satisfies the frozen case and hand-authored baseline prerequisite. Security-checklists has matching frozen case counts and enough security-critical cases, but its model E2E baseline remains pending, so the overall AC remains pending. |
| AC27 | Pending. No local model E2E harness was available, so no generated-router success rate, security-critical attempt result, or fabricated-path measurement is claimed. |
| AC28 | Pending. No maintainer update/timing exercise was completed in this local run. |
| AC29 | Fast repository build-check, direct compiler checks, the full AgentBundle package suite, full SAST/SCA, focused post-repair package and roster suites, and the exact real-sdist gate passed. Combined operator evidence covers every local `make ci` leg after the repair. Windows now runs the compiler check in required CI; site-link evidence remains external. |

## Pending human and external gates

- Model E2E routing evaluation is pending/unavailable for generated routers.
- RFC Approver case/baseline freeze confirmation and final sign-off are
  pending/unavailable.
- No release, correction, supersession, Delivered, or Complete status is set by
  this evidence note.
