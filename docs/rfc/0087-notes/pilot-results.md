# RFC-0087 OKF pilot results

Evidence status: pre-release and incomplete. RFC-0087 is accepted, but this
note does not promote OKF authoring, OKF discovery, or either pilot to a final
release state. Model E2E routing measurements and RFC Approver sign-off remain
pending.

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
| macOS write-mode determinism (AC22 partial) | Compile each managed pack twice in write mode (`python3 packs/catalogue-curation/.apm/skills/compile-okf/scripts/compile_okf.py --root . --pack <pack>`), then compare the managed tree between the two runs — `git status` stays clean, so the second compile reproduces the first byte for byte | macOS 25.5.0 arm64 / CPython 3.13.13. Both `_okf-pilot-cost-engineering` and `core` compile successfully in write mode and leave identical trees. Check mode is clean for both packs. |
| Windows knowledge-bundle verification | `agentbundle catalogue self-host --check --windows --root .` gained an `okf compiler checks` stage invoking `tools/check-okf-managed-packs.py` | Wired in required CI. Before it, no Windows runner invoked the compiler: the Windows suite runs the adopter-facing `tools/hooks/pre-pr.py`, while the OKF gate lives in the maintainer aggregator `tools/catalogue/pre_pr_catalogue.py`. Write mode remains unavailable on Windows by design — `_apply_outputs_transactionally` refuses with `OKF010` because `os.supports_dir_fd` is empty there. |
| Windows CI check-mode determinism (AC22) | `agentbundle catalogue self-host --check --windows --root .`, whose `okf compiler checks` stage runs `tools/check-okf-managed-packs.py` | Workflow run 32221115655 on `main` d652cff9, 2026-08-19T05:54Z: `=== okf compiler checks ===` then `okf-check: OK _okf-pilot-cost-engineering` and `okf-check: OK core`. Both managed packs verified on a Windows runner. Write mode remains unavailable there by design — `os.supports_dir_fd` is empty, so the dir-fd-confined apply path refuses. |
| Adapter preservation spike | `env PYTHONPATH=packages/agentbundle python3 docs/rfc/0087-notes/verify_adapter_spike.py` | All seven adapters passed; nested OKF tree digest `sha256:4c502a8833a955799b8aaa2f52769306fedcaa79c0233dcc086c321ea8366900` |
| Fast repository build check | `SKIP_SAST=1 make build-check` | Passed in supervisor-recorded T8 evidence |
| Full AgentBundle package suite | Isolated-venv `make ci` invocation supplied by the operator on 2026-08-17 | Passed to 100%; the same run also passed the CredBroker package suite |
| Full SAST/SCA path | Isolated-venv `make ci` invocation supplied by the operator on 2026-08-17, with `SKIP_SAST` unset | Passed: Bandit, dependency-audit self-tests, all declared pip-audit inputs, Semgrep, and the Semgrep rule self-test completed successfully |
| Full repository CI | Four isolated-venv `make ci` invocations plus a final targeted artifact-gate invocation supplied by the operator on 2026-08-17 | The first exposed a product-changelog version mismatch. The second exposed two catalogue-navigation consistency defects. The third exposed checkout-only schema dependencies in the real-sdist suite. The fourth cleared all three repairs, passed full SAST/SCA, the root suite (`356 passed`, `46 subtests`), every listed core and pack suite, the site/navigation group (`157 passed`, `2 subtests`), and workspace-status tests (`220 passed`, `13 subtests`) before the real-sdist gate exposed a repository-wide release-metadata assertion in the shipping engine suite. That assertion now lives in the non-shipping roster suite, where its package and repository surfaces are all present. Targeted package and roster tests pass (`8 passed`), the operator's exact real-sdist gate passed (`1 passed`), and an accidental `tools/` directory invocation also passed all `529` collected tool tests before zsh separately rejected the split trailing command fragments. Combined operator evidence therefore covers every local `make ci` leg after the repair without treating the malformed shell command itself as a successful command. |
| Site link check | site build/link gate | Blocked by missing Astro in the local environment; not retried |
| AC28 maintainer update exercise | For each caller, edit one canonical concept, run `python3 packs/catalogue-curation/.apm/skills/compile-okf/scripts/compile_okf.py --root . --pack <pack>`, capture `git diff` and `git diff --check`, restore the original concept, and regenerate | Completed on 2026-08-18. `core` regenerated in 3 seconds and `_okf-pilot-cost-engineering` in 1 second; both returned `OKF000 wrote`. No generated file was edited by hand. Both 4-file diffs were non-empty, both whitespace checks were clean, each restored diff was empty after regeneration, and final `git status --short` was empty. |

### AC28 maintainer update exercise

The exercise changed `packs/core/okf/security-checklists/concepts/access-control.md`
and `packs/_okf-pilot-cost-engineering/okf/cost-engineering/concepts/anomaly-triage.md`
separately. For each caller, the maintainer saved the original canonical concept,
made the one-concept edit, regenerated with the compiler command above, captured
the diff and whitespace check, restored the original canonical concept, and
regenerated again. No generated file was edited by hand.

`core` completed in 3 seconds and `_okf-pilot-cost-engineering` completed in 1
second, both within the 30-minute criterion. Each regeneration returned
`OKF000 wrote`. The core and cost diffs each changed four files: the canonical
concept, its projected reference copy, the router `SKILL.md`, and the pack
manifest. The concept edit changes its own source and output digest. That changes
the bundle source digest used by the router and both generated OKF indexes; the
router's embedded bundle digest then changes its output digest. Every other
managed entry digest was byte-identical. Both `git diff --check` outputs were
empty, both post-restore diffs were empty, and final `git status --short` was
empty.

## Report-only routing measurement (AC26 / AC27)

Recorded 2026-08-19 under RFC-0087 § Errata E1: top-1 and fabricated-path counts
are published, not gated; security-critical attempts remain a hard gate.

**Method.** Each frozen case was routed by a Claude Code subagent given only the
bundle path and the case prompt. The expected path, forbidden paths and every
baseline file were withheld. Three runs per caller, each a fresh sub-context, so
the three samples per case are independent rather than one sample and two
recollections; cases are answered sequentially within a run. No API key and no
model call outside the agent session. Scoring is deterministic and derives the
valid answer space from the bundle on disk, so a fabricated path cannot score as
real even if it matches some other case's key.

Harness `okf-routing-in-harness-v1`: `mode: in-harness`, `fidelity: observed`,
`provenance: agent-executed`. `temperature` and `top_p` are not settable in this
environment and are recorded as null rather than as the pre-registered
`okf-routing-baseline-v1` values, which do not apply here.

| Caller | Attempts | Top-1 vs key | Fabricated | Forbidden hits | Security-critical |
| --- | ---: | ---: | ---: | ---: | --- |
| security-checklists | 60 | **1.000** (60/60) | 0 | 0 | **1.000** (18/18) — gate passed |
| cost-engineering | 60 | **0.967** (58/60) | 0 | 0 | **1.000** (15/15) — gate passed |

Both exceed the >=80% published floor. Zero fabricated paths and zero
forbidden-path hits across all 120 attempts.

**The only miss is CE-012, twice.** Runs 1 and 3 chose `concepts/anomaly-triage.md`
where the key is `concepts/unit-economics.md`; run 2 matched the key. One routing
agent flagged it unprompted as "the one genuine coin-flip", observing that the
prompt's price-versus-volume framing matches `unit-economics`' inputs but matches
`anomaly-triage`'s step 2 nearly verbatim. That is a concept-overlap signal in the
corpus rather than a router defect, and it is the kind of finding a report-only
measurement exists to surface.

**Raw attempts and the scorer** are committed beside this note under
`pilot-measurements/`, so the numbers are auditable rather than asserted. Each
table row reproduces from its own committed record in one command:

```
python3 docs/rfc/0087-notes/pilot-measurements/score.py <caller> \
  <bundle>/references/okf \
  docs/rfc/0087-notes/pilot-measurements/<caller>-in-harness.json
```

The
scorer was mutation-checked before use: an injected fabricated path is counted,
and an injected security-critical miss fails the hard gate with a non-zero exit.

**Limits, stated plainly.** The session model is not pinned, so this is not a
model-version-comparable benchmark. Sampling parameters are uncontrolled. Runs
are independent of each other but cases within a run are not. Treat these as
published observations about the current corpus, not as a calibrated benchmark;
the calibrated arm remains deferred.

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
| D7 deterministic verification | `compile-okf --check` is wired and clean for both pilots on Linux, Windows, and macOS; fast build-check, the full AgentBundle package suite, and full SAST/SCA passed. | Check-mode evidence present on all three platforms; write-mode evidence is macOS-only and cannot be produced on Windows (see AC22). |
| D8 single-version support | Active profile remains `agentbundle-okf/v1` mapping to OKF 0.2. | Evidence present |

## Acceptance criterion accounting

| Criterion | Status |
| --- | --- |
| AC22 | **Closed** under RFC-0087 § Errata E2. Check mode is clean for both pilots on Linux CI, Windows CI (run 32221115655) and macOS. Write mode is byte-identical across two compiles for both managed packs on macOS; it is unavailable on Windows by design. |
| AC23 | The adapter spike preserves nested OKF regular-file bytes across Claude Code, Kiro IDE, Kiro CLI, Copilot, Cursor, Codex, and Gemini. |
| AC24 | The compile-okf Skill and authoring prerequisite are shipped in catalogue-curation. Fast build-check and the operator-supplied isolated-venv full SAST/SCA run passed. |
| AC25 | Both pilots compile through the generic compiler path. No caller-name branch evidence is recorded in the focused compiler tests. |
| AC25a | Cost-engineering remains a complete underscore-prefixed, non-published pack-shaped fixture; real-pilot discovery tests stage it under an ordinary temporary pack path. |
| AC26 | Satisfied as amended by § Errata E1. Both callers have 20 frozen cases (5 and 6 security-critical) and a frozen expected-path key; the key is not a model run and needs no model-configuration parity. |
| AC27 | Satisfied as amended by § Errata E1. 3 runs x 20 cases x 2 callers = 120 attempts. Top-1 1.000 (security-checklists) and 0.967 (cost-engineering), both above the >=80% published floor; 0 fabricated paths; security-critical 1.000 on both callers, hard gate passed. Recorded under § Report-only routing measurement with raw attempts in pilot-measurements/. |
| AC28 | Completed. The 2026-08-18 exercise regenerated both callers from one canonical-concept edit without hand-editing generated output, recorded 3-second and 1-second timings, explained all resulting diffs, and restored a clean worktree. |
| AC29 | Fast repository build-check, direct compiler checks, the full AgentBundle package suite, full SAST/SCA, focused post-repair package and roster suites, and the exact real-sdist gate passed. Combined operator evidence covers every local `make ci` leg after the repair. Windows now runs the compiler check in required CI; site-link evidence remains external. |

## Pending human and external gates

- Model E2E routing evaluation is pending/unavailable for generated routers.
- RFC Approver case/baseline freeze confirmation and final sign-off are
  pending/unavailable.
- No release, correction, supersession, Delivered, or Complete status is set by
  this evidence note.
