# Spec: pack-allowed-adapters

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0011](../../rfc/0011-pack-allowed-adapters.md) (canonical proposal — read first); [RFC-0004](../../rfc/0004-install-scope-per-pack.md) (`[pack.install]` table this spec extends; scope dimension; anti-silent-default rule); [RFC-0005](../../rfc/0005-user-scope-hook-support.md) (precedent for adapter-targeted contract bumps; `PackState.adapter` field this spec consumes); [RFC-0009](../../rfc/0009-codex-native-skills.md) (Accepted 2026-05-25; codex `direct-directory` projection at `.agents/skills/` is the live contract entry this spec's `[adapter.codex.scope]` table extends). Modifies [`packages/agentbundle/agentbundle/_data/adapter.toml`](../../../packages/agentbundle/agentbundle/_data/adapter.toml) (contract v0.5 → v0.6; new `[adapter.codex.scope]` table). Amends [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md) (contract version bump recorded; conformance cases for codex user-scope + repo-scope projection filter) and [`docs/specs/agent-spec-cli/spec.md`](../agent-spec-cli/spec.md) (`install` CLI surface gains `--adapter` flag; `_resolve_user_scope_target_adapter` four-step lookup documented as the resolver contract).

> **Spec contract:** this document defines what "done" means. The implementing PR must match this spec, or update it. Verification must be derivable from it.

> **Scope: one PR, one contract bump.** RFC-0011's *Follow-on artifacts* list bundles deliverables that cannot ship independently without leaving the catalogue in an incoherent state — the contract bump, the schema rule, the resolver rewrite, the four shipped user-scope packs' adopter declarations, the README/how-to/migration documentation, and the author-doc paragraph. Per RFC-0004's atomicity precedent ([RFC-0004 § Drawbacks](../../rfc/0004-install-scope-per-pack.md#drawbacks), the spec-amendment-atomicity rationale), all of it lands in a single PR. Splitting risks a partial v0.5 → v0.6 transition where the CLI accepts the new field but the four shipped packs haven't declared it (silent fall-through to the legacy heuristic), or the schema accepts the field but the resolver still routes to claude-code by construction (a known-bad outcome with no adopter recourse).

## Objective

Close the user-scope adapter-resolution gap that RFC-0011 names. Today an adopter installing a user-scope-capable pack via `agentbundle install --pack <name> --scope user .` lands the pack at one of `~/.claude/skills/`, `~/.kiro/skills/`, or `~/.agents/skills/` (the codex skills root) based on an agents-presence heuristic at `_resolve_user_scope_target_adapter` (install.py:1249-1275) — which silently routes every shipped user-scope pack to Claude Code because none of them ships `.apm/agents/`. **After this spec ships**, a Kiro adopter running that command lands the pack in `~/.kiro/skills/`; a Codex adopter lands in `~/.agents/skills/`; a multi-IDE adopter (anyone whose `~/.claude/` is populated from past Claude Code use, plus a second IDE) can pass `--adapter kiro` (or `--adapter codex`) on the CLI to override the auto-detected routing. The pack author's `[pack.install] allowed-adapters` declaration in `pack.toml` is the constraint: the resolver picks the first matching CLI home in declared order; the `--adapter` value must be in the declared set; an explicit module-level constant `DEFAULT_USER_SCOPE_ADAPTER` (default `"claude-code"`, modifiable downstream) provides the greenfield fallback when no CLI home matches.

`allowed-adapters` is **user-scope only** per RFC-0011 § *Repo-scope projection* (amended post-merge). Repo-scope `agentbundle install` is unchanged by this spec — it continues to emit `dist/apm/<pack>/` and `dist/claude-plugins/<pack>/` install-route artifacts regardless of `allowed-adapters` content. Per-pack constraints on the install-route fan-out at repo scope are a separate decision RFC-0011 does not gate.

Success for the adopter: the IDE they actually use receives the pack at user scope. Success for the catalogue author: the `pack.toml` field they declare is the single source of truth for which IDE shapes their user-scope content targets. Success for the contract: a v0.6 pack's adapter constraints are machine-checkable at validate time (schema) and at install time (resolver re-check), with refuse-and-explain messages naming the field by full path.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines. *Always do* applies without asking; *Ask first* requires human sign-off before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- **Every new code path lands with at least one regression test** under `packages/agentbundle/tests/unit/` (CLI / resolver / install surface) or `packages/agentbundle/agentbundle/build/tests/` (contract / schema / projection). There are two test trees per the repo's `reference_agentbundle_two_test_roots` convention; pick the right one and don't leave the test for "later in the spec."
- **Use the exact refuse-and-explain wording the RFC pins** for every refusal path (`pack.toml: [pack.install] allowed-adapters is …`, `install: --adapter <name> not in pack's allowed-adapters set`, `install: --adapter is bound to --scope user`, `install: pack '<name>' declares allowed-adapter '<adapter>' which is not admitted by adapter contract v<X.Y> shipped with agentbundle <cli-version>`). Tests assert against the exact strings.
- **Pin the schema's adapter-enum hydration in Python validator code** (not in `pack.schema.json` literal `enum`). The JSON file declares `"items": {"type": "string"}`; the validator reads `adapter.toml` at validate time and intersects with the live `[adapter.<name>.scope].user` set when the pack declares `"user" ∈ allowed-scopes`. A test under `build/tests/` pins the derivation against a fixture contract.
- **Hydrate the argparse `choices=` on `--adapter` from the live contract at CLI-load time** via a helper shared with the validator. Same symmetry as above. A test in `tests/unit/` pins the helper's output against the shipped contract and fails on drift.
- **Run `make build-self FORCE=1` after every change to `packs/<pack>/.apm/` or `packs/<pack>/seeds/`** so projected `.claude/skills/...` etc. stay in sync. Closing a build-self drift is in-scope for this PR (per memory rule `feedback_build_self_undoes_projection_only_edits`).
- **Use `eugenelim <eugenelim@users.noreply.github.com>` commit identity**, no Claude trailer; run `gh auth status` before push.

### Ask first

- **Any change to another adapter's `[adapter.<name>.scope]` table** (e.g. adding `[adapter.copilot.scope]` to admit Copilot at user scope). RFC-0011's *What this RFC does NOT do* lists Copilot user-scope as explicitly out of scope; touching it is a separate RFC's surface.
- **Any rename of the `allowed-adapters` field** (or the `DEFAULT_USER_SCOPE_ADAPTER` constant). The RFC settled the naming after multiple review rounds; renaming after Approval would be a contract bump for no behaviour change.
- **Any deletion of the legacy `_resolve_user_scope_target_adapter` heuristic branch.** RFC-0011 retains the heuristic for `< 0.6` packs and v0.6 packs omitting `allowed-adapters`. Deletion is a future RFC's call.
- **Any change to `PackState` schema** (the dataclass at `config.py:108-135`). The `adapter` field already exists since RFC-0005; this spec just changes the value source. Any field addition or rename earns a state-file `schema-version` bump, which is RFC-0004's territory.
- **Splitting this spec into multiple PRs.** The user explicitly chose one big PR (per RFC-0004 atomicity); splitting requires re-deciding that.

### Never do

- **No new top-level directory.** RFC-0011's surface fits inside existing trees (`packages/agentbundle/`, `packs/`, `docs/`, `.claude/`).
- **No new pack format.** `pack.toml` gains one field; no new sibling manifest, no new schema file beyond `pack.schema.json`'s existing surface.
- **No new install route.** Codex plugins is explicitly deferred to a sibling RFC ([RFC-0011 § What this RFC does NOT do](../../rfc/0011-pack-allowed-adapters.md)); this spec touches only the CLI install route (`agentbundle install`). No `dist/codex-plugins/` emission, no marketplace.json aggregation, no `SessionStart` writer.
- **No new third-party Python dependency.** The repo's policy is conservative; the resolver and schema check use stdlib (`tomllib`, `pathlib`, `argparse`) plus the existing `jsonschema` already on the dependency list.
- **No silent default for unknown adapter values.** The schema and the resolver both refuse-and-explain when `allowed-adapters` names an adapter the contract doesn't admit. No "treat unknown as claude-code" fallback.
- **No regression of the four user-scope packs' existing behaviour** for adopters who already installed them at the v0.2 contract level. The legacy heuristic stays alive; `agentbundle install --pack <name> --scope user .` against a v0.2-version-pinned pack still routes via the heuristic. Only v0.6+ packs see the new resolver.
- **No removal of the codex `direct-directory` projection** at `adapter.toml:217-237`. That's RFC-0009's code, ratified governance, and this spec depends on it.
- **No `--adapter` at repo scope.** The flag is bound to `--scope user` only; passing it at repo scope is a hard refuse, not a soft warning.
- **No fix to the same-name-Kiro-agent overwrite limitation in the legacy heuristic branch.** RFC-0011 § *Resolution at install time* step 4 explicitly retains it; a fix is a future RFC's surface. Don't drift into it during the resolver rewrite.
- **No repo-scope projection filter.** Per RFC-0011 § *Repo-scope projection* (post-merge erratum), `allowed-adapters` has no repo-scope semantics. The implementing PR does not touch `render.py`'s recipe pipeline or any repo-scope projection dispatch.

## Testing Strategy

| Behaviour from Objective | Verification mode | Why this mode |
| --- | --- | --- |
| Kiro adopter lands pack at `~/.kiro/skills/` | **TDD** — unit test against `_resolve_user_scope_target_adapter` with a fixture `~/.kiro/` populated and a fixture pack declaring `allowed-adapters = ["claude-code", "kiro"]`. | Pure-function resolver with a compressible invariant (probe order → first match wins). |
| Codex adopter lands pack at `~/.agents/skills/` | **TDD** — same shape with `~/.codex/` populated (CLI home probe) and the projection target asserted at `~/.agents/skills/`. | The asymmetry (probe `~/.codex/`, write `~/.agents/skills/`) earns its own assertion. |
| Multi-IDE adopter overrides with `--adapter <name>` | **TDD** — unit test against the argparse path; pass `--adapter kiro` with `~/.claude/` populated and assert resolution to `kiro`. The flag has two refusal paths (bound-to-user-scope, not-in-allowed-adapters) that earn separate cases. | Refusal-path correctness; exact-string assertion. |
| Greenfield adopter (no CLI home present) lands at `DEFAULT_USER_SCOPE_ADAPTER` | **TDD** — fixture `$HOME` with no `~/.<ide>/` populated; assert `claude-code` resolution; flip the constant in-test to `"kiro"` and assert resolution flips. | The constant's downstream-modifiability is the load-bearing feature. |
| Schema refuses `allowed-adapters = ["copilot"]` for user-scope packs | **TDD** — fixture pack with `allowed-scopes = ["user"]` and the offending field; assert `agentbundle validate` exits non-zero with the pinned stderr message. | Refusal-path correctness; exact-string assertion. |
| Adopter-side `agentbundle install --pack <name> --scope user --adapter copilot .` refuses | **TDD** — argparse `choices=` admits any shipped adapter (claude-code/kiro/codex/copilot); the handler then checks user-scope-capability and pack-set membership, refusing with the pinned `install: --adapter <name> not in pack's allowed-adapters set` (when copilot is not in the pack's list) or `install: --adapter copilot not admitted as a user-scope-capable adapter under contract v0.6` (when the pack omits `allowed-adapters`). | Both fallthroughs documented; tests pin both. The choices=any-shipped lift (vs. choices=user-scope-only) keeps the pinned messages reachable through the CLI surface. |
| Install-time print line `installed: <pack> @ <scope> via <adapter>` is visible | **Goal-based check** — run `agentbundle install` in a fixture and grep stdout for the line. | Format-string check; no need for a behavioural test. |
| `make build-self FORCE=1` is a noop after the final commit | **Goal-based check** — `make build-self FORCE=1 && git status --short` shows no changes. | Build-pipeline gate; covered by CI but verified locally too. |
| `pre-pr.py` passes on the merged tree | **Goal-based check** — `python3 tools/hooks/pre-pr.py` exits 0. | Aggregate enforcement gate; covered by CI. |
| Documentation surface (README + two how-to guides + migration guide + author-doc paragraph) is internally consistent and grep-able by adopter | **Manual QA** — read the diff end-to-end against the RFC's *Follow-on artifacts* list and verify every commitment landed. | Adopter-facing prose; no automated equivalent. |

## Acceptance Criteria

The spec is closed when each of the following observable outcomes is verifiable in the merged PR.

### Contract surface

- **AC1.** `packages/agentbundle/agentbundle/_data/adapter.toml`'s `[contract] version` is `"0.6"` (previously `"0.5"`). The header comment names this spec / RFC-0011 alongside the existing RFC pointers.
- **AC2.** `packages/agentbundle/agentbundle/_data/adapter.toml` contains an `[adapter.codex.scope]` table with `repo = "."`, `user = "~"`, and `allowed-prefixes.user = [".agents/skills/", ".agentbundle/"]`. No other adapter's scope table is modified.
- **AC3.** `packages/agentbundle/agentbundle/_data/pack.schema.json` admits `[pack.install].allowed-adapters` as an optional array of strings; the schema does not hardcode the adapter set. The validator-side enum check is implemented in Python (see AC7).

### Pack-author surface

- **AC4.** `packs/atlassian/pack.toml`, `packs/figma/pack.toml`, `packs/converters/pack.toml`, `packs/contracts/pack.toml` each declare `[pack.adapter-contract] version = "0.6"` and `[pack.install] allowed-adapters = ["claude-code", "kiro", "codex"]`. No other field on these packs is touched.
- **AC5.** The four shipped repo-only packs (`core`, `governance-extras`, `user-guide-diataxis`, `monorepo-extras`) are unchanged. (They neither bump contract version nor declare `allowed-adapters` — they project everywhere by default, status quo.)

### Resolver surface

- **AC6.** `_resolve_user_scope_target_adapter` in `packages/agentbundle/agentbundle/commands/install.py` is rewritten as a four-step lookup per [RFC-0011 § Resolution at install time](../../rfc/0011-pack-allowed-adapters.md):
  1. `--adapter` CLI flag (highest priority); refused if not in pack's `allowed-adapters` (or, for legacy/omitted packs, not in the live contract's user-scope-capable set).
  2. Contract-version gate: v0.6+ packs with `allowed-adapters` declared consult the field; legacy packs fall through to step 4.
  3. Adapter-root probe: walk `allowed-adapters` in declared order; check CLI-home presence (`~/.claude/`, `~/.kiro/`, `~/.codex/` OR `~/.agents/skills/` for codex). First match wins. Greenfield fallback: `DEFAULT_USER_SCOPE_ADAPTER` if in the pack's set, else `allowed-adapters[0]`.
  4. Legacy heuristic (`.apm/agents/*.md` present ⇒ `kiro`; else `claude-code`).
  The function keeps its name. The docstring TODO block is rewritten to reference RFC-0011's resolution.
- **AC7.** `_kiro_target_adapters` in `packages/agentbundle/agentbundle/commands/validate.py:351-389` is updated in two places:
  1. **Replace the literal `version != "0.3"` gate at line 379** with a `version not in {"0.3", "0.6"}` check (or equivalent — the rail fires for both v0.3 AND v0.6+ contract packs). This closes a silent breakage where v0.6 hook-bearing packs would have skipped the kiro-targeting check entirely because of the literal-string gate.
  2. **Early-return from `allowed-adapters`** when the pack is v0.6+ and the field is declared: `"kiro" in allowed_adapters ⇒ return {"kiro"}`; otherwise on-disk inference (agents + wiring presence) is the fallback. No behavioural change for `< 0.6` packs.
  A test pins a v0.6 pack shipping `.apm/agents/` + `.apm/hook-wiring/` *without* `allowed-adapters` and asserts the rail fires (legacy heuristic path) — that's the case the current literal gate breaks.
- **AC8.** The user-scope projection dispatch at `install.py:1170-1178` gains a third arm for `codex.project(...)` (same `direct-directory` tree-copy logic as the live repo-scope codex projection, rooted at `~/.agents/skills/`). The two existing arms (claude-code, kiro) are unchanged.
- **AC9.** A new module `packages/agentbundle/agentbundle/scope.py` exports the module-level constant `DEFAULT_USER_SCOPE_ADAPTER: str = "claude-code"`. The constant is the single source of truth for the greenfield-fallback default. A test in `tests/unit/` asserts its current value and walks the resolver against a fixture flipping the constant to `"kiro"` and `"codex"`.
- **AC10.** `_resolve_user_scope_target_adapter`'s signature gains two keyword parameters — `adapter: str | None` (the resolved `--adapter` value, or None) and `allowed_adapters: list[str] | None` (the pack's declared list, or None). The **two invocations** in `upgrade.py` (lines 228 and 311; the imports at lines 218 and 308 don't change) are updated to pass `adapter=None` plus the pack's `allowed-adapters` (loaded inline from the pack's `pack.toml` at the call site if not already in scope). An upgrade-side test asserts upgrade-time adapter resolution is byte-identical to install-time resolution when `adapter=None`.

### CLI surface

- **AC11.** `packages/agentbundle/agentbundle/cli.py` `install` argparse setup at lines 199-229 gains an optional `--adapter` argument. Its `choices=` are hydrated at CLI-load time from the live `adapter.toml` — **every shipped adapter** (`claude-code`, `kiro`, `codex`, `copilot`), not just user-scope-capable ones. The user-scope-capable check moves to the install handler (see AC13). The help text matches the RFC's pinned wording.
- **AC12.** `--adapter` is bound to `--scope user`. Passing `--adapter <name> --scope repo` (or omitting `--scope` with the pack's `default-scope = "repo"`) is refused with the pinned `install: --adapter is bound to --scope user` message and a non-zero exit.
- **AC13.** `--adapter` against a pack that omits `allowed-adapters` is admitted iff the value names a user-scope-capable adapter in the live contract. `--adapter copilot` is refused regardless because Copilot has no user-scope root. The refuse-and-explain message at the handler matches the pinned `install: --adapter copilot not admitted as a user-scope-capable adapter under contract v0.6`. **The handler-level check (not argparse-level) is load-bearing for AC13's reachability** — argparse would otherwise short-circuit with its stock "invalid choice" error before the pinned message can fire.

### Install-time message rail

- **AC14.** On successful user-scope install, stdout includes the line `installed: <pack> @ user via <adapter>` (extending RFC-0004's `installed: <pack> @ <scope>` rail with the `via <adapter>` clause for user scope only). When `allowed-adapters` has more than one matching CLI home and `--adapter` was not passed, the line gains a one-line suffix `  (other declared adapters: <comma-separated>; use --adapter to override)` so adopters see the alternatives.
- **AC15.** On install-time failure from the publisher-vs-installer adapter-set drift (a v0.6 pack declaring an adapter the bundled contract no longer admits), the error message matches `install: pack '<name>' declares allowed-adapter '<adapter>' which is not admitted by adapter contract v<X.Y> shipped with agentbundle <cli-version>`.

### Documentation surface

- **AC16.** `README.md`'s `Where primitives land` table is updated: the Codex row shows `.agents/skills/<name>/SKILL.md` (matching RFC-0009's live projection); the table notes user-scope landing paths for the three user-scope-capable adapters. Each user-scope-capable pack's row in the `Packs` table links into the `Where primitives land` table rather than re-listing the three landing paths inline (single canonical location per memory rule `feedback_writing_style`). The `Install` section's `Where to run these` paragraph picks up a one-line note about user-scope adapter resolution and links to the relevant how-to.
- **AC17.** Two new how-to guides land:
  - `docs/guides/how-to/install-user-scope-pack-into-kiro.md` covers the Kiro adopter path: prerequisites (`~/.kiro/` exists), the `agentbundle install --pack <name> --scope user .` invocation, the `installed: ... via kiro` confirmation line, upgrade and uninstall verbs.
  - `docs/guides/how-to/install-user-scope-pack-into-codex.md` covers the Codex adopter path: prerequisites, the same invocation (or with `--adapter codex` if multiple CLI homes are present), the `~/.agents/skills/` discovery model, the interaction with `~/.codex/plugins/` (separate surface, not addressed here), upgrade and uninstall verbs.
  Both cross-linked from the README install section.
- **AC18.** A new migration guide lands at `docs/guides/how-to/v05-to-v06-pack-upgrade.md`. It covers the `[pack.adapter-contract] version` bump, the `allowed-adapters` field shape and the three currently-admitted user-scope-capable values, the schema's refuse-and-explain messages, the user-scope-only semantics (per RFC-0011's post-merge erratum), and the legacy path for older packs.
- **AC19.** The `add-credentialed-skill` skill body (`packs/core/.apm/skills/add-credentialed-skill/SKILL.md` and the projected `.claude/skills/...` copy) gains one paragraph naming `allowed-adapters` and the per-pack-author guidance. `docs/specs/skill-secrets/spec.md` gains the same paragraph in its author-facing section. No change to credential loading (skill-secrets AC3 untouched).
- **AC20.** `docs/ROADMAP.md` gains an entry under "user-scope": *"`allowed-adapters` landed — Kiro and Codex user-scope installs now exercise the integrated path; next: codex-plugins install-route parity (sibling RFC, not yet opened; will be modeled on RFC-0008)."*

### Tests

- **AC21.** Unit tests for the four-step resolver under `packages/agentbundle/tests/unit/test_resolve_user_scope_target_adapter.py`. Coverage:
  - **CLI-home probes — each adapter populated alone.** `~/.claude/` only → `claude-code`; `~/.kiro/` only → `kiro`; `~/.codex/` only → `codex`; `~/.agents/skills/` only (no `~/.codex/`) → `codex` (OR-probe — the RFC's codex sub-cases land here).
  - **First-match-wins.** Multiple roots populated; declared-order ties broken by `allowed-adapters` ordering.
  - **`--adapter` flag accepted** against a pack declaring the adapter.
  - **`--adapter` refused — not in pack's `allowed-adapters`.** Pinned stderr `install: --adapter <name> not in pack's allowed-adapters set`.
  - **`--adapter` refused — not user-scope-capable.** v0.6 pack omits `allowed-adapters`; `--adapter copilot`; pinned stderr `install: --adapter copilot not admitted as a user-scope-capable adapter under contract v0.6`.
  - **`--adapter` refused at `--scope repo`.** Pinned stderr `install: --adapter is bound to --scope user`.
  - **Greenfield $HOME** (no `~/.<ide>/` populated) resolves to `DEFAULT_USER_SCOPE_ADAPTER` when in the pack's `allowed-adapters`; falls back to `allowed-adapters[0]` when the constant's value is not in the pack's set. Monkeypatch the constant in-test to assert the fallback path.
  - **Legacy heuristic for `< 0.6` packs** unchanged.
  - **V0.6 pack omitting `allowed-adapters`** falls through to the legacy heuristic.
- **AC22.** Unit tests for the schema validator under `packages/agentbundle/agentbundle/build/tests/test_pack_schema_allowed_adapters.py`. Coverage:
  - Optional field accepted when omitted.
  - Admits any shipped adapter when pack is repo-only (`"user" ∉ allowed-scopes`).
  - Refuses `"copilot"` when pack is user-scope-eligible; refuses unknown adapter values regardless.
  - Schema's adapter-enum derivation against a fixture contract.
  - **`_kiro_target_adapters` literal-gate fix:** v0.6 pack shipping `.apm/agents/` + `.apm/hook-wiring/` *without* `allowed-adapters` fires the rail (returns `{"kiro"}` via on-disk inference); v0.6 pack declaring `allowed-adapters = ["claude-code"]` returns `set()`; v0.3 pack with the same on-disk shape returns `{"kiro"}` (legacy path unchanged).
- **AC23.** Unit tests for the argparse `choices=` derivation under `packages/agentbundle/tests/unit/test_install_argparse_adapter_flag.py`. Coverage: `choices` matches the live contract's **every-shipped-adapter** set (`claude-code`, `kiro`, `codex`, `copilot`); help text matches the RFC's pinned wording; a separate handler-time test asserts the user-scope-capability check refuses `--adapter copilot` with the pinned message.
- **AC24.** Existing flow-metrics probe test at `packages/agentbundle/tests/unit/test_flow_metrics_upstream_probe.py` (landed alongside RFC-0011) is unchanged by this spec and continues to pass.
- **AC25.** End-to-end install smoke under `packages/agentbundle/tests/integration/test_install_user_scope_allowed_adapters.py`: install each of the four user-scope packs against fixture `~/.claude/`, `~/.kiro/`, `~/.codex/`, and `~/.agents/skills/` trees (greenfield, single-IDE, two-of-three combinations, all-three combinations, plus the `--adapter <name>` override). State-file shape asserted per adapter (`PackState.adapter` records the resolved value).
- **AC26.** Existing tests that touch `_resolve_user_scope_target_adapter`, `_kiro_target_adapters`, the four pack's `pack.toml`, the `[contract] version`, or the install argparse setup are updated to match v0.6 expectations. `pytest packages/agentbundle/` exits 0.

### Gates

- **AC27.** `make build-self FORCE=1` produces a clean working tree (`git status --short` empty after the run; verify against the Makefile's actual flag spelling).
- **AC28.** `python3 tools/hooks/pre-pr.py` exits 0 on the merged tree.
- **AC29.** CI gates (`build-check` linux + windows, `pytest` windows, `docs` lint suite) all pass on the implementation PR.

## Changelog

- 2026-05-25 — Initial Draft.
- 2026-05-26 — Post-pre-EXECUTE-review revision. Dropped AC11/AC12 (the repo-scope projection filter, which targeted a four-per-IDE-directory fan-out that `agentbundle install --scope repo` does not actually perform — see RFC-0011 § *Repo-scope projection* erratum). Renumbered remaining ACs. AC7 explicitly pins the `_kiro_target_adapters` literal-`!= "0.3"`-gate widening. AC10 acknowledges the resolver signature change and the upgrade.py call-site updates. AC11 lifts argparse `choices=` to admit every shipped adapter (with the user-scope-capability check moving to the handler) so the pinned refuse-and-explain messages are reachable. Documentation surface ACs renumbered to drop the four-landing-paths-inline duplication into a single canonical link to the README's `Where primitives land` table.
