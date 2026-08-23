# Plan: Core install handoff and hook documentation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document may change while Drafting or Executing. Substantive changes are
> recorded in the changelog.

## Approach

Make one small behavioral extension to the existing first-value contract, then
reconcile living documentation and tests with the audited runtime contracts.
The installer remains the guaranteed onboarding rail; hooks remain optional
convenience. No `adapt-to-project` implementation, hook projector, hook body,
event map, or runtime configuration changes in this plan.

## Constraints

- Use canonical pack and contract sources; regenerate derived metadata only
  through owning builders.
- Preserve local-scope omissions and core's fresh user-scope refusal.
- Do not write Git metadata in this enterprise workspace.
- Do not mutate or inspect runtime trust/configuration stores.
- Keep frozen historical spec bodies, RFCs, and work-loop fixture corpora
  unchanged. After ADR-0095 is accepted, only the two affected shipped specs'
  status lines receive partial-supersession pointers.

## Construction tests

- Unit-test Level A optional `next-action` emission and validation.
- Install real core at repo and local scope and assert the exact handoff plus
  existing scope-specific omissions.
- Run existing adapter projection suites without changing their expected
  outputs.
- Run README disclosure, guide, catalogue, build, and generated-drift checks.
- Exercise the built CLI's successful core repo and local install paths and
  capture the observed stdout.

## Design

### Decisions

- Reuse optional `pack.first-value.next-action`; do not add a core-only
  installer branch or new manifest field.
- Validate optional `next-action` for both levels while retaining Level B's
  requirement.
- Put the exact instruction in `packs/core/pack.toml` so installer code remains
  pack-agnostic.
- Correct the minimum living documentation set and link to the adapter contract
  or the audit instead of copying a support matrix into generated targets.
- Record the newly discovered adapter-fidelity gaps but leave their behavior
  unchanged pending a separate human decision.
- Require human acceptance of ADR-0095 before implementing the shared Level A
  contract amendment.

### Control flow

1. A successful install completes existing projection, seed, state, marker, and
   chained-adapt behavior for the selected scope.
2. The installer emits `Verify:` from first-value metadata.
3. When `next-action` is present at either level, the installer emits `Next:`.
4. Hook activation may provide an additional nudge, but its absence never
   removes the deterministic step 3 handoff.

### Compatibility

- Existing repo installs gain one additive stdout line on a future successful
  install that emits first-value handoff; state and files are otherwise
  unchanged.
- Existing local installs receive no retroactive marker or seed. A future
  successful local install with the updated core metadata emits the new line.
- Existing user state is not migrated. Fresh core user-scope requests continue
  to fail before installation.
- Packs without Level A `next-action` and all existing Level B packs keep their
  output contract.

## Tasks

### T1: Emit and validate optional Level A next action

**Depends on:** none

**Touches:** `packages/agentbundle/agentbundle/commands/install.py`,
`packages/agentbundle/agentbundle/catalogue_tooling/lint.py`,
`packages/agentbundle/tests/unit/test_install_first_value_handoff.py`,
`packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py`,
`packages/agentbundle/tests/integration/test_local_scope_install.py`,
`tests/roster/test_core_install_handoff.py`,
`packs/core/pack.toml`, status lines only in
`docs/specs/agentbundle-first-value-handoff/spec.md` and
`docs/specs/portfolio-pack-first-value-contract/spec.md`

**Verification mode:** TDD

`stub: true`

```python
# Red additions, placed in the existing first-value and lint test modules.
def test_level_a_optional_next_action_is_emitted() -> None:
    data = {**_LEVEL_A_DATA, "next-action": "run readiness"}
    out = _capture_handoff(data)
    assert "Verify:" in out
    assert "Next:     run readiness" in out


def test_level_a_next_action_over_limit_is_cat_l030(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(_lp_module, "lint_pack", lambda pack_dir: [])
    monkeypatch.setattr(_lint_module, "_load_pack_schema", lambda: None)
    _setup_markers(tmp_path)
    extra = _FV_SECTION + f'next-action = "{"x" * 121}"\n'
    _add_pack_fv(tmp_path, "pack-a", pack_toml_extra=extra)
    result = lint_catalogue(tmp_path)
    assert any(
        item.code == "CAT-L030" and "next-action" in item.message
        for item in result.diagnostics
    )
```

**Approach:** Move optional `Next:` emission outside the Level B-only branch;
validate a present field before the Level B required-field check; add the
120-character core instruction. After ADR-0095 is accepted, add exact
status-only partial-supersession pointers to the two frozen specs without
changing their bodies.

**Done when:** focused first-value/lint tests and real repo/local core install
tests pass with the exact output, while absent-field and Level B regressions
remain green.

### T2: Reconcile living docs, disclosures, and release metadata

**Depends on:** T1

**Touches:** `packs/core/README.md`,
`packs/core/.apm/hook-wiring/session-start.toml` (comments only),
`guides/core/how-to/adapt-to-project.md`,
`guides/_shared/explanation/install-routes.md`,
`docs/architecture/agentbundle.md`,
`packages/agentbundle/agentbundle/commands/install.py` (stale comment only),
`packs/core/tests/pack/test_apm_readme_disclosure.py`,
`tests/roster/test_core_onboarding_documentation.py`,
`docs/product/changelog.md`, generated core metadata and distribution output

**Verification mode:** goal-based

**Approach:** Replace obsolete Codex/APM support claims, invalid `adapt --scope`
syntax, universal-marker claims, and Claude-only authoring comments. Keep the
adopter flow task-first and concise. Bump core's patch version and regenerate
through repository builders; do not hand-edit projections.

**Done when:** targeted searches find no stale living claims, disclosure and
guide checks pass, all adapter projection tests pass unchanged, the built CLI
repo/local happy paths show the exact handoff, and catalogue/build drift checks
are clean.

## Gates

Run the narrow tests first, then the repository gates proportional to the
affected surfaces:

```bash
python3 -m pytest packages/agentbundle/tests/unit/test_install_first_value_handoff.py packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py packages/agentbundle/tests/integration/test_local_scope_install.py packs/core/tests/pack/test_apm_readme_disclosure.py tests/roster/test_core_onboarding_documentation.py tests/roster/test_core_install_handoff.py -q
python3 -m pytest packages/agentbundle/tests/build_pipeline/test_adapter_claude_code.py packages/agentbundle/tests/build_pipeline/test_adapter_codex.py packages/agentbundle/tests/build_pipeline/test_adapter_copilot.py packages/agentbundle/tests/build_pipeline/test_adapter_cursor.py packages/agentbundle/tests/build_pipeline/test_adapter_gemini.py packages/agentbundle/tests/build_pipeline/test_adapter_kiro_ide.py packages/agentbundle/tests/build_pipeline/test_adapter_kiro_cli.py -q
python3 tools/validate_guides.py
python3 tools/check-guide-index.py
python3 tools/lint-guide-titles.py
make lint-ruff
make build-self
SKIP_SAST=1 make build-check
```

## Risks

- A generic first-value change could alter Level B output order; focused tests
  pin all branches.
- Documentation could imply projection equals execution; wording keeps the
  runtime gates separate.
- The audit could be mistaken for repaired adapter behavior; its disposition
  names every deferred compatibility gap.
- Regeneration could touch unrelated projections; inspect and preserve existing
  worktree changes, and accept only source-derived output required by the core
  patch version/comment change.

## Changelog

- 2026-08-21: initial option-3 plan included installer handoff, Codex path
  hardening, and an `adapt-to-project` doctor.
- 2026-08-22: user narrowed scope to stale documentation and deterministic
  installer handoff; all `adapt-to-project` implementation and doctor work was
  removed.
- 2026-08-22: current first-party hook contracts were audited. Kiro projection,
  cross-runtime output protocol, and root-stable command repairs were recorded
  as separate decisions rather than bundled into this change.
- 2026-08-22: adversarial review found the Level A extension contradicted two
  frozen specs. ADR-0095 was proposed to own the amendment; implementation is
  gated on its human acceptance and status-only forward pointers.
- 2026-08-22: the authoring-time design review made the recovery referent
  explicit (`the skill`) while keeping the handoff within the 120-character
  contract.
- 2026-08-23: three gate repairs, none of them behavior changes. (1) The T2 doc
  rewrite had deleted two literals that `tools/lint-plugin-route-docs.py` pins
  as contiguous substrings; both claims are still true, so they were restored
  in the rewritten prose rather than the lint being relaxed. (2) T2 had grown
  the core pack test two `guides/` reads, which `pack-tests-stay-in-pack`
  rejects; that repository-level coverage moved to the new
  `tests/roster/test_core_onboarding_documentation.py`, with the pack-local
  README half left in place and no assertion dropped. (3) The ADR was
  renumbered 0093 to 0095 after both 0093 and 0094 were taken on `main` by
  other work the same day.
- 2026-08-23: AC1's two real-core-install cases moved from the shipped
  `agentbundle` integration module to `tests/roster/test_core_install_handoff.py`.
  The export-boundary gate builds an sdist and runs the shipped suite inside it,
  where no `packs/` tree exists, so a shipped test that installs the repository
  catalogue fails there. Core versions were also renumbered to 2.10.7 / 0.39.2
  after `main` took 2.10.6 / 0.39.1 with no merge conflict.
