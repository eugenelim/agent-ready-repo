# Spec: Install-Defaults Preferred Adapter Hint

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0036 (install-source trusted-by-construction precedence chain; the org adapter hint lives in the same packaged wheel as the layer-4 source default, the same trust layer), RFC-0046 (convenient install defaults; this extends `install-defaults.toml` without touching the source chain)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: light (no risk trigger fired)

## Objective

Org forks of agentbundle that standardize on one IDE can ship a
`preferred_adapter` hint in `_data/install-defaults.toml` under the
`[organization]` table, letting developers run bare `agentbundle install core`
without typing `--adapter <name>` on every install. The hint slots as step 2.75
in `_resolve_target_adapter`'s six-step chain — after user-config (step 2.5) and
before auto-probe (steps 3+4) — so explicit `--adapter`, state-hint, and
user-config always win. A blank or absent value falls through silently (the
private-fork pattern); an invalid value (present but not in the shipped adapter
contract) fails closed with a clear error before any write. The value is never
persisted in state.

## Boundaries

### Always do

- Validate `preferred_adapter` against `shipped_adapters_from_contract()` in
  `read_packaged_preferred_adapter()`; raise `CatalogueError` for a non-blank
  invalid value, naming the value and the admissible set.
- Validate the hint against the pack's `allowed_adapters` at resolution time;
  raise `_AdapterResolutionRefused` if the hint is not in the pack's declared set.
- Return `None` for an absent or blank `preferred_adapter` (silent fall-through;
  no error).
- Consult the hint only when `state_adapter is None` — same gate as user-config
  step 2.5, so upgrade correctness is preserved.

### Ask first

- Any change that reads `preferred_adapter` from a file outside the packaged
  wheel (e.g., a repo-committed file), which would cross the trust boundary.

### Never do

- Write the org hint to state; it is resolution-time only, not provenance.
- Apply the hint when `--adapter` is specified or when the user-config adapter
  is set (steps 1 and 2.5 always win).
- Add a repo-scoped or in-repo `preferred_adapter` source (ADR-0036 D3 reasoning
  applies: a cloned repo directing which adapter paths get written has the same
  trust problem as a repo-scoped source — the org-packaged wheel is the right
  boundary).
- Introduce a new dependency.

## Testing Strategy

- **TDD** for `_preferred_adapter_from_install_defaults` and
  `read_packaged_preferred_adapter` (pure parse/validate functions with
  compressible invariants; red stubs materialized in plan.md T1).
- **TDD** for the new step 2.75 in `_resolve_target_adapter` (pure with
  injected `preferred_adapter`; red stubs materialized in plan.md T2).
- **Goal-based check** for the integration: `pytest packages/agentbundle/`
  still exits 0 after all changes.

## Acceptance Criteria

- [x] `_preferred_adapter_from_install_defaults(text)` returns the string value
  when `[organization].preferred_adapter` is present and non-blank; returns
  `None` for a missing `[organization]` table, a missing key, a blank value, or
  malformed TOML.
- [x] `read_packaged_preferred_adapter()` reads the packaged
  `_data/install-defaults.toml`, validates the result against
  `shipped_adapters_from_contract()`, raises `CatalogueError` naming the invalid
  value and the admissible set when the value is non-blank but not in the shipped
  adapter contract, and returns `None` for an absent or blank value.
- [x] `_resolve_target_adapter` accepts a `preferred_adapter: str | None = None`
  parameter. When non-`None` and `state_adapter is None`: validates against the
  pack's `allowed_adapters` if declared (raises `_AdapterResolutionRefused` naming
  the pack's supported adapters if the hint is not in the set); validates against
  `admissible_at_scope`; returns the hint value if admissible.
- [x] Explicit `--adapter <name>` (step 1) wins over the org hint.
- [x] User-config adapter (step 2.5) wins over the org hint.
- [x] State-hint (step 2) wins over the org hint; the hint is skipped when
  `state_adapter is not None`.
- [x] An invalid `preferred_adapter` in `install-defaults.toml` causes `install`
  to exit non-zero with a clear error message before any write.
- [x] A blank or absent `preferred_adapter` leaves all existing behavior
  unchanged; the existing test suite passes.
- [x] `_render_for_repo_scope` and `_render_for_user_scope` accept and thread
  `preferred_adapter` to their `_resolve_target_adapter` calls.
- [x] `install.run()` reads `read_packaged_preferred_adapter()` once, exits 1 on
  `CatalogueError`, and passes the result to all `_resolve_target_adapter` call
  sites and render helpers.
- [x] `docs/guides/_shared/reference/agentbundle.md` adapter cascade is updated
  to include the org preferred-adapter hint as step 4 (after user-config, before
  on-disk probe), and a new "Org adapter default" sub-section explains what it is
  and how an org fork sets it.
- [x] `packages/agentbundle/README.md` (PyPI) "Build your own catalogue" section
  mentions `[organization].preferred_adapter` so org forks know to add it to
  `_data/install-defaults.toml`.

## Assumptions

- Technical: Python 3.11 stdlib-only; no new dependencies
  (source: `packages/agentbundle/pyproject.toml`).
- Technical: lazy import of `shipped_adapters_from_contract` from
  `agentbundle.scope` inside `read_packaged_preferred_adapter()` avoids a
  circular-import issue — the same pattern `user_config.py:_parse_adapter` uses
  (source: `packages/agentbundle/agentbundle/user_config.py:155`).
- Technical: `[organization].preferred_adapter` is structurally compatible with
  the future `[organization.artifactory]` subtable (RFC-0072 / spec
  `organization-artifactory-bootstrap`) — TOML allows a top-level `[organization]`
  key and a `[organization.artifactory]` subtable to coexist in the same file
  (source: TOML spec; structural review of RFC-0072 §M4b).
- Process: light mode is appropriate — no risk trigger fires
  (source: `work-loop` skill risk-trigger list).
- Product: org forks control the packaged wheel content and can edit
  `_data/install-defaults.toml` without a code change
  (source: user confirmation 2026-07-23).
