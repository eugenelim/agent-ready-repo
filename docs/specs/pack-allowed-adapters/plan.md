# Plan: pack-allowed-adapters

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this document is allowed to change as you learn. When it changes substantially (a different approach, not just a re-ordering), note why in the changelog at the bottom.

## Approach

Single-PR implementation that lands the contract bump, schema rule, resolver rewrite, four pack updates, CLI flag, install-time messages, documentation, and tests in one merge per RFC-0004's atomicity precedent. **Scope narrowed post-pre-EXECUTE-review:** the original draft included a repo-scope projection filter against `allowed-adapters`; pre-EXECUTE review verified against code that `agentbundle install --scope repo` produces dist-shaped install-route artifacts (`apm/`, `claude-plugins/`), not the four-per-IDE-directory fan-out the filter would have constrained. RFC-0011's repo-scope-projection section was amended post-merge to mark the field as user-scope-only; this spec follows. Order of operations: (1) contract + module constant — *the floor*; (2) resolver rewrite + schema validator — *the central rail*; (3) CLI flag and refuse-and-explain handler — *the imperative escape valve*; (4) pack-toml updates — *the actual adopter behaviour change*; (5) install-time message rail; (6) documentation; (7) gates. Tests-first per task. The plan's task graph is **largely sequential** — T2 depends on T1, T3 on T2, etc. — because the contract is the shared substrate everything else reads. Supervisor mode (parallel implementers) is unlikely to earn its keep here.

## Constraints

- **Constrained by:** [RFC-0011](../../rfc/0011-pack-allowed-adapters.md) — every task implements one or more of RFC-0011's commitments; deviations require the RFC to amend first.
- **Builds on:** [RFC-0004](../../rfc/0004-install-scope-per-pack.md) `[pack.install]` table; [RFC-0005](../../rfc/0005-user-scope-hook-support.md) `PackState.adapter` field; [RFC-0009](../../rfc/0009-codex-native-skills.md) live codex `direct-directory` projection at `adapter.toml:217-237`.
- **Single PR per RFC-0004 atomicity.** Partial landings risk a known-bad coherence state (schema accepts the field but resolver still uses heuristic; or four packs declare `allowed-adapters` but install ignores it).
- **Schema enum hydrated in Python**, not in `pack.schema.json` literal. (See spec § *Boundaries — Always do*.)
- **Refuse-and-explain wording fixed by RFC**; tests assert exact strings.
- **No new third-party Python dependency.** stdlib + existing `jsonschema`.

## Construction tests

Most construction tests live under **Tasks** below (per-task `Tests:`).

**Cross-cutting tests** (span more than one task):

- **End-to-end install smoke** at `packages/agentbundle/tests/integration/test_install_user_scope_allowed_adapters.py`. Installs each of the four user-scope packs (`atlassian`, `figma`, `converters`, `contracts`) against fixture `~/.claude/`, `~/.kiro/`, `~/.codex/`, and `~/.agents/skills/` trees. Cases: greenfield, single-IDE, two-of-three combinations, all-three populated, plus the `--adapter <name>` override for each. State-file shape asserted per adapter (`PackState.adapter` records the resolved value). This *is* T8; cross-referenced here for the cross-cutting view. Covers spec AC25; prerequisites span T2, T4, T5, T6, T7.
- **`pre-pr.py` end-to-end** — `python3 tools/hooks/pre-pr.py` exits 0 on the final tree. Covers spec AC28; spans every task.

**Manual verification:**

- Read the diff end-to-end against RFC-0011's *Follow-on artifacts* checklist (AC16-AC20). Spot-check the README's `Where primitives land` table renders correctly on GitHub.
- `make build-self FORCE=1 && git status --short` shows no changes after the final commit. Covers spec AC27.

## Tasks

Order matters — listed in the order they should be done. Most `Depends on:` chains are linear because the contract is the shared substrate; T6 (CLI flag, `Depends on: T2, T3`) and T7 (install-time messages, `Depends on: T2, T5`) both consume the resolver landed in T2.

### T1: Contract bump v0.5 → v0.6 plus `[adapter.codex.scope]` table (atomic edit)

**Depends on:** none

**Spec mapping:** AC1, AC2. Mode: goal-based check (contract is data; the test is a grep + version-equality assertion).

**Atomicity requirement:** the version bump AND the new `[adapter.codex.scope]` table land in a **single commit**. Splitting these two edits leaves an intermediate snapshot (`version = "0.6"` without `[adapter.codex.scope]`) that breaks every dependent test (T2's CLI-home probe expects the table; T3's schema-enum derivation expects codex in the user-scope-capable set). Verify atomicity by reviewing the commit diff before merging T1.

**Tests:**
- `packages/agentbundle/agentbundle/build/tests/test_contract_v06.py::test_contract_version_is_06` — load `_data/adapter.toml`, assert `tomllib.loads(...)["contract"]["version"] == "0.6"`.
- `packages/agentbundle/agentbundle/build/tests/test_contract_v06.py::test_codex_scope_table_shape` — assert `[adapter.codex.scope]` exists with `repo == "."`, `user == "~"`, `allowed-prefixes.user == [".agents/skills/", ".agentbundle/"]`.
- `packages/agentbundle/agentbundle/build/tests/test_contract_v06.py::test_no_other_scope_table_modified` — parse the contract via `tomllib` and assert the parsed `[adapter.claude-code.scope]` and `[adapter.kiro.scope]` *table bodies* are equal to a parsed fixture snapshot of the v0.5 tables (compare dict equality, not file bytes — the contract header comment changes in T1 itself per AC1, and unrelated whitespace/comment edits to the file must not break this assertion).

**Approach:**
- Edit `packages/agentbundle/agentbundle/_data/adapter.toml`: bump `[contract] version` from `"0.5"` to `"0.6"`; add the `[adapter.codex.scope]` table with the four lines the RFC pins; update the header comment to name RFC-0011 / this spec alongside the existing RFC pointers. **Both edits in one commit.**
- Run `make build-self FORCE=1` to propagate the bump through any projected adapter-toml copies (the lint catches drift).

**Done when:** the three contract tests pass and `make build-self FORCE=1` produces a clean working tree (`git status --short` empty for projected-toml paths).

---

### T2: Extend `scope.py` with `DEFAULT_USER_SCOPE_ADAPTER` + helpers, rewrite four-step resolver, lift `pack_state.adapter` assignment, add upgrade-side state-hint

**Depends on:** T1

**Spec mapping:** AC6, AC9, AC10, AC10a, AC10b, AC21. Mode: TDD (resolver is a pure function with enumerable cases).

**Tests:**

Add `packages/agentbundle/tests/unit/test_resolve_user_scope_target_adapter.py`. Parametrized over:

- **CLI-home probe — each adapter populated alone.** Fixture `$HOME` with only `~/.claude/`; pack declares `allowed-adapters = ["claude-code", "kiro", "codex"]`; assert resolver returns `"claude-code"`. Repeat with `~/.kiro/` only → `"kiro"`. Repeat with `~/.codex/` only → `"codex"`. Repeat with `~/.agents/skills/` only (no `~/.codex/`) → `"codex"` (OR-probe).
- **First-match-wins.** Fixture `$HOME` with both `~/.claude/` and `~/.kiro/` populated; assert `"claude-code"` (declared order wins). Reorder the pack's `allowed-adapters` to `["kiro", "claude-code", "codex"]`; assert `"kiro"`.
- **Greenfield fallback.** Fixture `$HOME` with no CLI home populated; pack declares `["claude-code", "kiro"]` and `DEFAULT_USER_SCOPE_ADAPTER == "claude-code"`; assert `"claude-code"` returned. Monkeypatch the constant to `"kiro"`; assert `"kiro"` returned. Monkeypatch to `"codex"` (not in pack's list); assert `"claude-code"` returned (fallback to `allowed-adapters[0]`).
- **`--adapter` flag — accepted path.** Pack declares `["claude-code", "kiro", "codex"]`; pass `--adapter kiro` with `~/.claude/` populated; assert `"kiro"` (override beats probe).
- **`--adapter` flag — refused, not in pack's list.** Pack declares `["claude-code", "kiro"]`; pass `--adapter codex`; assert refusal with stderr matching `install: --adapter codex not in pack's allowed-adapters set`.
- **`--adapter` flag — refused, not user-scope-capable.** Pack omits `allowed-adapters`; pass `--adapter copilot`; assert refusal with stderr matching `install: --adapter copilot not admitted as a user-scope-capable adapter under contract v0.6`.
- **`--adapter` flag — refused at repo scope.** Pass `--adapter kiro --scope repo`; assert refusal with stderr matching `install: --adapter is bound to --scope user`.
- **Legacy heuristic — `< 0.6` pack.** v0.5 pack with `.apm/agents/foo.md`; assert `"kiro"`. v0.5 pack without agents; assert `"claude-code"`.
- **Legacy heuristic — v0.6 pack omitting `allowed-adapters`.** Assert same heuristic behaviour as `< 0.6`.
- **`< 0.6` pack with stray `allowed-adapters`.** A v0.5 pack accidentally declaring `[pack.install] allowed-adapters = ["kiro"]` — assert legacy-heuristic path still fires (the `contract_version` gate pins this; `allowed_adapters is not None` alone is not enough).
- **Upgrade-side equivalence.** Pin upgrade-time adapter resolution byte-identical to install-time resolution when `adapter=None` AND `state_adapter=None` (covers AC10's upgrade-side test commitment).
- **State-hint upgrade case (AC10b).** State recorded `adapter = "claude-code"`, pack's current `allowed-adapters = ["claude-code", "kiro", "codex"]`, `~/.kiro/` now populated alongside `~/.claude/` — assert resolver returns `"claude-code"` (state hint wins, no re-probe). Then flip the recorded adapter to one not in `allowed-adapters` (e.g., the pack dropped `"kiro"` support and state recorded `"kiro"`) — assert the resolver falls through to the probe and the upgrade.py:318 refusal fires.
- **State-file unconditional assignment (AC10a).** Three sub-cases: codex install records `state.adapter == "codex"`; non-hook claude-code install records `state.adapter == "claude-code"` (would silently default before this PR); non-hook kiro install records `state.adapter == "kiro"`.

**Approach:**
- **Extend `packages/agentbundle/agentbundle/scope.py`** (which already exists at 170 LOC per RFC-0004 T17, exporting `LEGAL_SCOPES`, `ScopeRefused`, `UserScopeUnresolvable`, `resolve`, `resolve_user_root` — *do not rewrite the file*; the five existing exports are imported by `install.py`, `upgrade.py`, `uninstall.py`, `reconcile.py`, `diff.py`, `adapt.py`, and the unit-test module). Append:
  - `DEFAULT_USER_SCOPE_ADAPTER: str = "claude-code"` (the module-level greenfield-fallback constant).
  - `def shipped_adapters_from_contract() -> tuple[str, ...]:` — returns `tuple(sorted(adapter_names))` for every adapter declared in `[adapter.<name>]` blocks of `_data/adapter.toml`. Used by T6 argparse `choices=`.
  - `def user_scope_capable_adapters_from_contract() -> tuple[str, ...]:` — returns `tuple(sorted(adapter_names))` for adapters that declare `[adapter.<name>.scope].user`. Used by T3 validator + T6 handler.
  - `def contract_supports_hook_wiring(version: str | None) -> bool:` — returns `True` for `version not in {"0.1", "0.2"}` (semantic predicate; fires for v0.3+; won't trap the next contract bump). Used by T3's `_kiro_target_adapters` rail.
  A regression test imports the five pre-existing exports verbatim and walks `scope.resolve` + `scope.resolve_user_root` against fixtures to assert behaviour didn't drift.
- Rewrite `_resolve_user_scope_target_adapter` at `install.py:1249-1275` as the **six-step** lookup (publisher-drift is step 0; state-hint is step 2). The new signature is `def _resolve_user_scope_target_adapter(pack_dir: Path, *, adapter: str | None, allowed_adapters: list[str] | None, contract_version: str | None, state_adapter: str | None = None, command_name: str = "install") -> str`. The six steps in order:
  0. **Publisher-vs-installer drift refusal (AC15)** — if `allowed_adapters` is declared, intersect with `shipped_adapters_from_contract()`; if any declared adapter is missing from the bundled contract, refuse with the pinned `<command_name>: pack '<name>' declares allowed-adapter '<adapter>' which is not admitted by adapter contract v<X.Y> shipped with agentbundle <cli-version>`. **Runs first** so neither `--adapter` (step 1) nor state-hint (step 2) can leak a no-longer-shipped adapter through.
  1. **`--adapter` override** — if `adapter` is not None, validate against `allowed_adapters` (when declared) or `user_scope_capable_adapters_from_contract()` (when omitted); return it. Refuse with the pinned messages.
  2. **State-hint short-circuit (AC10b)** — if `state_adapter` is not None AND `state_adapter` is in `allowed_adapters` (when declared) OR in `user_scope_capable_adapters_from_contract()` (when omitted), return `state_adapter`. This is upgrade-side stability.
  3. **Contract-version gate + probe** — if `contract_version` is None OR `contract_supports_hook_wiring(contract_version) is False` OR `allowed_adapters is None`, fall through to step 5 (legacy heuristic). Otherwise: probe via the **explicit per-adapter probe table**:
     ```python
     PROBES = {
         "claude-code": lambda h: (h / ".claude").exists(),
         "kiro":        lambda h: (h / ".kiro").exists(),
         "codex":       lambda h: (h / ".codex").exists() or (h / ".agents" / "skills").exists(),
     }
     ```
     Walk `allowed_adapters` in declared order; first probe returning True wins. Greenfield: return `DEFAULT_USER_SCOPE_ADAPTER` if in `allowed_adapters`, else `allowed_adapters[0]`.
  5. **Legacy heuristic** — `.apm/agents/*.md` present ⇒ `"kiro"`; else `"claude-code"`.
- **Preserve the docstring's "Known limitation" block verbatim** (same-name-Kiro-agent overwrite, per Boundaries — Never do). Rewrite only the TODO block.
- **Lift `new_pack_state.adapter` assignment out of the kiro-hook-only branch (AC10a).** At `install.py:591-592` today, `new_pack_state.adapter = "kiro"` is set only when `user_target_adapter == "kiro"` AND `user_scope_hooks_enabled`. Move this to run unconditionally for `effective_scope == "user"` before the hook-merge block: `new_pack_state.adapter = user_target_adapter`. Drop the kiro-only conditional. Without this, codex / non-hook claude-code installs leave the field at the dataclass default and AC25 assertions about state shape will never hold.
- **Update all four `_resolve_user_scope_target_adapter` call sites and both `_render_for_user_scope` call sites.** Failing to thread kwargs through the bridge means install.py:440 (the primary user-scope render) silently falls through to the legacy heuristic — exactly the bug this spec is closing.
  - **`install.py:299`** (inside `run()` before scope-plan build): pass `adapter=args.adapter`, `allowed_adapters=pack_install.get("allowed-adapters") if isinstance(pack_install, dict) else None`, `contract_version=pack_toml.get("pack", {}).get("adapter-contract", {}).get("version")`, `state_adapter=None`, `command_name="install"`. `pack_toml` is already in scope at this point.
  - **`install.py:440`** (primary install-time call to `_render_for_user_scope`): widens to pass the same five kwargs through the bridge — `args.adapter`, `pack_install.get("allowed-adapters") if isinstance(pack_install, dict) else None`, the contract version, `state_adapter=None`, `command_name="install"`.
  - **`install.py:1171`** (inside `_render_for_user_scope`): consumes the kwargs from the bridge's parameters and forwards them to `_resolve_user_scope_target_adapter`.
  - **`upgrade.py:222`** (primary upgrade-time call to `_render_for_user_scope`): widens to pass `adapter=None`, the pack's `allowed-adapters` and contract version from `pack_toml` (already loaded at line 167 via `load_pack_toml`), `state_adapter=pack_state.adapter`, `command_name="upgrade"`.
  - **`upgrade.py:228`** and **`upgrade.py:311`** (the direct resolver calls — imports at 218 and 308 unchanged): same five kwargs as upgrade.py:222.
  
  **Widen `_render_for_user_scope`'s signature** to `def _render_for_user_scope(pack_dir: Path, *, adapter: str | None = None, allowed_adapters: list[str] | None = None, contract_version: str | None = None, state_adapter: str | None = None, command_name: str = "install") -> dict[str, bytes]`. Defaults preserve backward shape for legacy tests calling positional. Every production call site threads explicit values; a regression test asserts no production call site is left at all-defaults.
  
  An upgrade-side test pins that upgrade's resolver result equals install's when `adapter=None` AND `state_adapter=None`.

**Done when:** all parametrized cases in the new test module pass; the lifted `pack_state.adapter` assignment is verified by AC10a's three sub-cases; the upgrade-side state-hint case (AC10b) passes; existing tests under `packages/agentbundle/tests/unit/` that touch the resolver continue to pass; the regression test for the five pre-existing `scope.py` exports passes; `pytest packages/agentbundle/` exits 0.

---

### T3: Schema validator — `allowed-adapters` enum hydration in Python + `_kiro_target_adapters` literal-gate fix

**Depends on:** T1, T2

**Spec mapping:** AC3, AC7, AC22. Mode: TDD (validator is a pure function over a fixture pack + fixture contract).

**Tests:**

Add `packages/agentbundle/agentbundle/build/tests/test_pack_schema_allowed_adapters.py`. Cases:

- **Field omitted.** v0.6 pack with no `allowed-adapters`; validator passes (field is optional).
- **Repo-only pack admits any shipped adapter.** Pack with `allowed-scopes = ["repo"]` and `allowed-adapters = ["copilot"]`; validator passes (Copilot is shipped; the user-scope-capability check doesn't fire when `"user" ∉ allowed-scopes`).
- **User-scope pack refuses non-user-scope adapter.** Pack with `allowed-scopes = ["user"]` and `allowed-adapters = ["copilot"]`; validator refuses with pinned stderr matching `pack.toml: [pack.install] allowed-adapters contains 'copilot', which does not declare a user-scope root in the v0.6 adapter contract`.
- **Unknown adapter refused regardless.** Pack with `allowed-adapters = ["windsurf"]` (not a shipped adapter); validator refuses with pinned message.
- **Empty array refused.** Pack with `allowed-adapters = []`; validator refuses (minItems-style — empty constraint is meaningless).
- **Duplicate values refused.** Pack with `allowed-adapters = ["claude-code", "claude-code"]`; validator refuses (uniqueItems-style).
- **`_kiro_target_adapters` literal-gate widening.** This is the load-bearing v0.6 fix:
  - v0.6 pack shipping `.apm/agents/foo.md` + `.apm/hook-wiring/bar.toml` *without* `allowed-adapters`: assert `_kiro_target_adapters` returns `{"kiro"}` via on-disk inference. **This is the case the current literal `version != "0.3"` gate at `validate.py:379` silently breaks; the test pins the fix.**
  - v0.6 pack declaring `allowed-adapters = ["claude-code"]` with the same on-disk shape: assert returns `set()` (kiro not in allowed list, rail is a no-op).
  - v0.6 pack declaring `allowed-adapters = ["kiro"]`: assert returns `{"kiro"}`.
  - v0.3 pack with the same on-disk shape: assert returns `{"kiro"}` (legacy path unchanged).
  - v0.5 pack (intervening; no agents or wiring features the rail consumes): assert returns `set()` (rail is a no-op for non-v0.3 / non-v0.6 packs by construction).

**Approach:**
- Add `allowed-adapters` to `packages/agentbundle/agentbundle/_data/pack.schema.json` as `{"type": "array", "items": {"type": "string"}, "minItems": 1, "uniqueItems": true}` under `[pack.install]`. Don't try to express the adapter-name enum in JSONSchema — the Python validator owns it.
- In `packages/agentbundle/agentbundle/commands/validate.py`, add the cross-field check after schema validation passes: read the pack's `allowed-adapters` and `allowed-scopes`; intersect with the live contract's shipped-adapter set; if `"user" ∈ allowed-scopes`, additionally intersect with the user-scope-capable subset; refuse with the pinned messages on violation.
- The "user-scope-capable adapter set" helper lives in `agentbundle/scope.py` (created in T2), shared with T6's argparse derivation.
- **Widen `_kiro_target_adapters`'s literal version gate at `validate.py:379`.** Replace `if contract.get("version") != "0.3": return set()` with the equivalent of `if not contract_supports_hook_wiring(contract.get("version")): return set()`, importing the semantic predicate from `agentbundle.scope`. This fires for v0.3+ (anything not in `{"0.1", "0.2"}`), so the next contract bump (v0.7+) won't re-break the rail by literal-set mismatch. For v0.6+ packs, *before* falling into the on-disk inference, early-return based on `allowed-adapters`: `"kiro" in allowed_adapters ⇒ {"kiro"}`, `allowed_adapters declared but kiro absent ⇒ set()`, `allowed_adapters omitted ⇒ fall into on-disk inference`. v0.3 path unchanged.

**Done when:** all parametrized cases in the new test module pass; existing validate-side tests pass; `pytest packages/agentbundle/` exits 0.

---

### T4: Four shipped user-scope packs bump to v0.6 + declare `allowed-adapters`

**Depends on:** T1, T3

**Spec mapping:** AC4, AC5. Mode: goal-based check (TOML edit + projection-noop assertion).

**Tests:**
- Add `packages/agentbundle/agentbundle/build/tests/test_shipped_packs_v06_declarations.py`. For each of `atlassian`, `figma`, `converters`, `contracts`: load `pack.toml`, assert `[pack.adapter-contract] version == "0.6"` and `[pack.install].allowed-adapters == ["claude-code", "kiro", "codex"]`.
- For each of `core`, `governance-extras`, `user-guide-diataxis`, `monorepo-extras`: assert no change from current state (no `allowed-adapters` declared; `[pack.adapter-contract] version` unchanged from current value).
- `make build-self FORCE=1` is a noop on the four user-scope packs' projection (`git status` clean for `.claude/skills/<pack>/`, `.kiro/skills/<pack>/`, `.agents/skills/<pack>/` after the run, assuming pack source content didn't change).

**Approach:**
- For each of the four user-scope packs, edit `packs/<pack>/pack.toml`:
  - Bump `[pack.adapter-contract] version = "0.2"` → `"0.6"`.
  - Add `allowed-adapters = ["claude-code", "kiro", "codex"]` under `[pack.install]`.
- No other field changes.
- Run `make build-self FORCE=1`.
- Verify `git status --short` is clean modulo the `pack.toml` edits themselves.

**Done when:** the three test cases above all pass; `make build-self FORCE=1` produces a clean working tree.

---

### T5: User-scope projection dispatch gains codex arm

**Depends on:** T1, T2

**Spec mapping:** AC8, AC25. Mode: TDD (dispatch correctness).

**Tests:**
- Extend `packages/agentbundle/tests/unit/test_resolve_user_scope_target_adapter.py` (from T2) with cases that exercise the post-resolution projection. For each of the three adapters: stub the resolved adapter, call `_render_for_user_scope`, assert the right `<adapter>.project(...)` is invoked. (Or use the existing integration-test entry point.)
- Add a case where `target_adapter == "codex"`: assert `codex.project(pack_dir, contract, out)` is invoked; assert the output tree contains `.agents/skills/<skill>/SKILL.md` (using a fixture pack with a single skill).

**Approach:**
- In `packages/agentbundle/agentbundle/commands/install.py`, the existing two-arm dispatch lives inside `_render_for_user_scope` at lines 1174-1177 (the `if target_adapter == "kiro": ... else: claude_code.project(...)` block). Extend that block to a three-arm:
  ```python
  if target_adapter == "kiro":
      kiro.project(pack_dir, contract, out)
  elif target_adapter == "codex":
      codex.project(pack_dir, contract, out)
  else:
      claude_code.project(pack_dir, contract, out)
  ```
- Add `from agentbundle.build.adapters import codex` to `_render_for_user_scope`'s imports alongside the existing `claude_code, kiro` import at line 1166 (RFC-0009's `direct-directory` projection at `adapter.toml:217-237` is the live codex code path).
- For codex user-scope, the post-projection paths arrive as root-relative `.agents/skills/<skill>/...` (per RFC-0009's `direct-directory` projection at `adapter.toml:217-237`). The path-jail accepts these via the `[adapter.codex.scope].allowed-prefixes.user = [".agents/skills/", ".agentbundle/"]` table from T1. Verify `safety.write_jailed` accepts `.agents/skills/<skill>/SKILL.md` against `allowed_prefixes=[".agents/skills/", ".agentbundle/"]` rooted at `~/`; add a focused unit test under `tests/unit/test_resolve_user_scope_target_adapter.py` (or a sibling) that drives `safety.write_jailed` directly with the codex user-prefixes to pin this — don't rely on T8's integration suite as the only catch. `_rewrite_user_scope_hook_paths` is hook-only by name/docstring; it does NOT need to be extended for codex skills (skills aren't hooks). If codex hook-wiring at user scope is ever needed, that's a future RFC's surface.

**Done when:** the codex-arm dispatch test passes; the explicit `safety.write_jailed` test against the codex user-prefixes passes; the integration smoke (T8 below) confirms codex user-scope installs write to `~/.agents/skills/`.

---

### T6: `--adapter` CLI flag with every-shipped-adapter `choices=` + handler-side user-scope-capability check

**Depends on:** T2, T3

**Spec mapping:** AC11, AC12, AC13, AC23. Mode: TDD (argparse + refusal-path correctness).

**Tests:**

Add `packages/agentbundle/tests/unit/test_install_argparse_adapter_flag.py`. Cases:

- **`choices=` derivation matches the live contract — every shipped adapter.** Call the `shipped_adapters_from_contract()` helper against the bundled `adapter.toml`; assert it returns exactly `("claude-code", "codex", "copilot", "kiro")` (alphabetic sorted-tuple — T2 pins `tuple(sorted(...))` for stability across Python versions and adapter-toml edits).
- **`--adapter claude-code` / `kiro` / `codex` / `copilot` all accepted at parse time.** All four shipped adapters parse cleanly.
- **`--adapter windsurf` rejected at parse time** (argparse refuses unknown choice with stock error — fine, since `windsurf` isn't shipped).
- **Handler-side user-scope-capability check refuses `--adapter copilot`** (Copilot is shipped but lacks `[adapter.copilot.scope].user`). Pinned stderr matches `install: --adapter copilot not admitted as a user-scope-capable adapter under contract v0.6`. **This is the load-bearing case that requires the choices=any-shipped lift — argparse-level `choices=` restricted to user-scope-capable adapters would short-circuit with its stock "invalid choice" error before the pinned message can fire.**
- **`--adapter kiro --scope repo` refused at handler time** (T2 already pinned this; cross-link).
- **Help text matches RFC wording** — assert `"Override the auto-detected adapter at user scope"` appears in `--help` output for the `install` subcommand.

**Approach:**
- In `packages/agentbundle/agentbundle/cli.py:199-229`, add `sp.add_argument("--adapter", choices=shipped_adapters_from_contract(), help=...)` to the `install` subparser. The helper enumerates **every adapter declared in `[adapter.<name>]` blocks**, not just user-scope-capable ones — that admits Copilot into argparse so the handler can issue the pinned refuse-and-explain.
- The helper `shipped_adapters_from_contract()` lives in `packages/agentbundle/agentbundle/scope.py` (alongside the `user_scope_capable_adapters_from_contract()` helper created in T2). Both read the bundled `adapter.toml`.
- The `install` handler at `commands/install.py` reads `args.adapter` and, when not `None`, checks (a) `--scope user` is resolved (else refuse with `install: --adapter is bound to --scope user`), (b) the adapter is user-scope-capable per `user_scope_capable_adapters_from_contract()` (else refuse with `install: --adapter <name> not admitted as a user-scope-capable adapter under contract v0.6`), (c) the adapter is in the pack's `allowed-adapters` if declared (else refuse with `install: --adapter <name> not in pack's allowed-adapters set`). Then threads the value into the resolver's first step (covered by T2).

**Done when:** all argparse-test cases pass; `agentbundle install --help` shows the new flag with all four shipped adapters in `choices=`.

---

### T7: Install-time message rail

**Depends on:** T2, T5

**Spec mapping:** AC14, AC15. Mode: goal-based check (format-string assertions).

**Tests:**
- Add `packages/agentbundle/tests/unit/test_install_messages.py`. Cases:
  - Successful user-scope install of a v0.6 pack with one matching CLI home: stdout contains `installed: <pack> @ user via <adapter>` (no suffix).
  - Successful user-scope install where two adapters are eligible (both `~/.claude/` and `~/.kiro/` populated, pack declares both) and `--adapter` not passed: stdout contains the suffix `(other declared adapters: kiro; use --adapter to override)`.
  - **Greenfield user-scope install** (no CLI home populated, pack declares three adapters, no `--adapter`): stdout contains `installed: <pack> @ user via claude-code` with no suffix (the suffix logic intersects `allowed-adapters` with the *populated* CLI-home set minus the chosen adapter — greenfield's populated-set is empty, so the intersection is empty and no suffix renders).
  - Repo-scope install: stdout contains `installed: <pack> @ repo` (no `via`).
  - Publisher-vs-installer drift case: simulate a v0.6 pack declaring an adapter the bundled contract doesn't admit; assert refusal stderr matches `install: pack '<name>' declares allowed-adapter '<adapter>' which is not admitted by adapter contract v<X.Y> shipped with agentbundle <cli-version>`.

**Approach:**
- In `packages/agentbundle/agentbundle/commands/install.py`, locate the existing `installed: <pack> @ <scope>` print (RFC-0004's rail). Extend with the `via <adapter>` clause when `scope == "user"`. **Compute the "other declared adapters" suffix using the same per-adapter probe table from T2** (imported from `agentbundle.scope` or shared via a private helper) — so codex-via-`.agents/skills/` is counted as "populated" consistently between the resolver and the suffix logic. Intersect `allowed-adapters` with the populated CLI-home set (per the shared probe), minus the chosen adapter; render the suffix only when the intersection is non-empty.
- The install-time publisher-vs-installer drift check (AC15) is owned by T2 (lives in the resolver flow); T7 just verifies the message fires through the message-rail path. No duplicate implementation.

**Done when:** all four message-test cases pass; integration smoke (T8) confirms the messages appear in real installs.

---

### T8: End-to-end install integration tests

**Depends on:** T2, T4, T5, T6, T7

**Spec mapping:** AC25. Mode: TDD (integration; treats install as a black box and asserts state-file + filesystem outcomes).

**Tests:**

Add `packages/agentbundle/tests/integration/test_install_user_scope_allowed_adapters.py` (or extend an existing integration module). For each of the four user-scope packs:

- **Greenfield.** Fixture `$HOME` with no `~/.<ide>/`; `agentbundle install --pack <name> --scope user .`; assert install lands at `~/.claude/skills/<skill>/` (default constant); assert `~/.agentbundle/state.toml` records `adapter = "claude-code"` for the pack.
- **Single-IDE.** Fixture `$HOME` with only `~/.kiro/` populated; assert install lands at `~/.kiro/skills/<skill>/`; state records `adapter = "kiro"`.
- **Multi-IDE, no `--adapter`.** Fixture `$HOME` with both `~/.claude/` and `~/.kiro/` populated; assert install lands at `~/.claude/skills/` (declared order); state records `adapter = "claude-code"`.
- **Multi-IDE, with `--adapter`.** Same fixture, but `--adapter kiro`; assert install lands at `~/.kiro/skills/`; state records `adapter = "kiro"`.
- **Codex.** Fixture `$HOME` with `~/.codex/` populated and no other adapter home; assert install lands at `~/.agents/skills/`; state records `adapter = "codex"`.
- **All three.** Fixture `$HOME` with all three populated; assert declared-order tie-break (`allowed-adapters = ["claude-code", "kiro", "codex"]` → claude-code wins); `--adapter codex` overrides cleanly.
- **Upgrade with state-hint (AC10b).** Two-step fixture: (a) `agentbundle install --pack <name> --scope user .` with only `~/.claude/` populated → state records `adapter = "claude-code"`; (b) populate `~/.kiro/` post-install; (c) `agentbundle upgrade --pack <name> --scope user .` → assert state still records `adapter = "claude-code"` and the cross-adapter refusal at `upgrade.py:318-326` does not fire. Covers AC10b and the AC25 upgrade-case commitment.

**Approach:**
- Use the existing integration-test fixtures (`tmp_path` + monkeypatched `HOME`) and the existing `agentbundle install` invocation harness.
- Assert filesystem state (which `~/.<ide>/skills/<skill>/SKILL.md` exists) and state-file content (parse `~/.agentbundle/state.toml` and check `packs.<name>.adapter`).
- Run against each of the four shipped user-scope packs (parametrize). Don't fabricate test packs unless the shipped ones are inadequate.

**Done when:** every parametrized case passes; `pytest packages/agentbundle/tests/integration/` exits 0.

---

### T9: README + how-to guides + migration guide

(Plan task — Approach references map to spec AC16 for README, AC17 for how-to guides, AC18 for migration guide.)

**Depends on:** T1, T4

**Spec mapping:** AC16, AC17, AC18. Mode: manual QA (adopter-facing prose).

**Tests:**
- Goal-based grep: assert `README.md` contains the substrings `~/.kiro/skills/`, `~/.agents/skills/`, and `--adapter` (per the Packs-table and Install-section commitments).
- Goal-based grep: assert `docs/guides/how-to/install-user-scope-pack-into-kiro.md` exists and contains the substring `agentbundle install --pack`, `--scope user`, `~/.kiro/skills/`.
- Goal-based grep: assert `docs/guides/how-to/install-user-scope-pack-into-codex.md` exists and contains the substring `agentbundle install --pack`, `--scope user`, `~/.agents/skills/`.
- Goal-based grep: assert `docs/guides/how-to/v05-to-v06-pack-upgrade.md` exists and contains the substrings `[pack.adapter-contract]`, `0.6`, and `allowed-adapters` (three narrower greps instead of one full quoted phrase, so smart quotes / single quotes in the rendered prose don't break the assertion).
- Manual: read each new file end-to-end against the spec's AC16-AC18 commitments. Render the README locally and confirm the Packs table renders.

**Approach:**
- Edit `README.md` (per AC16):
  - Update the `Where primitives land` table's Codex row to show `.agents/skills/<name>/SKILL.md` (matching RFC-0009's live projection); add user-scope landing paths for the three user-scope-capable adapters. This table is the **single canonical location** for the landing paths.
  - Each of the four user-scope-capable pack rows in the `Packs` table links into the `Where primitives land` table (no inline path enumeration — single canonical per memory rule `feedback_writing_style`).
  - Add a one-line note in the `Install` section's `Where to run these` paragraph about user-scope adapter resolution; link to the relevant how-to.
- Write `docs/guides/how-to/install-user-scope-pack-into-kiro.md` per spec AC17 first bullet.
- Write `docs/guides/how-to/install-user-scope-pack-into-codex.md` per spec AC17 second bullet.
- Write `docs/guides/how-to/v05-to-v06-pack-upgrade.md` per spec AC18.
- Add cross-links from the README install section.

**Done when:** the four grep cases pass; manual read confirms each commitment landed.

---

### T10: Author-doc paragraph + ROADMAP entry

**Depends on:** T1, T4

**Spec mapping:** AC19, AC20. Mode: goal-based check (substring grep on the merged docs).

**Tests:**
- Goal-based grep: `packs/core/.apm/skills/add-credentialed-skill/SKILL.md` (source) and `.claude/skills/add-credentialed-skill/SKILL.md` (projected) both contain a paragraph naming `allowed-adapters` and the three-adapter guidance.
- Goal-based grep: `docs/specs/skill-secrets/spec.md` contains the same paragraph.
- Goal-based grep: `docs/backlog.md` contains the line `allowed-adapters landed` (or close match per spec AC20).

**Approach:**
- Edit `packs/core/.apm/skills/add-credentialed-skill/SKILL.md`: add one paragraph in the author-facing section per RFC-0011 *Follow-on artifacts* — "If your pack's content is portable across IDEs (skills-only, no IDE-specific agent shape), list every adapter in `allowed-adapters` that supports user scope. The two credentialed packs in this catalogue (`atlassian`, `figma`) list `claude-code`, `kiro`, and `codex` because their skills are pure text + Python and travel cleanly across all three adapters' user-scope skill directories."
- Edit `docs/specs/skill-secrets/spec.md`: add the same paragraph in the author-facing section. No change to AC3 (credential loading).
- Edit `docs/backlog.md`: add the entry under "user-scope" per spec AC20.
- Run `make build-self FORCE=1` to sync the projected `.claude/skills/add-credentialed-skill/SKILL.md` copy.

**Done when:** the three grep cases pass; `make build-self FORCE=1` produces a clean working tree.

---

### T11: Gates pass — final sweep

**Depends on:** T1, T2, T3, T4, T5, T6, T7, T8, T9, T10

**Spec mapping:** AC24, AC26, AC27, AC28, AC29. Mode: goal-based check (gates).

**Tests:**
- `pytest packages/agentbundle/` exits 0.
- `make build-self FORCE=1 && git status --short` shows no changes.
- `python3 tools/hooks/pre-pr.py` exits 0.
- (CI replication of `build-check` linux + windows, `pytest` windows, `docs` lint suite — verified post-push on the PR.)

**Approach:**
- Sweep for any test that touched `_resolve_user_scope_target_adapter`, `_kiro_target_adapters`, the four packs' `pack.toml`, the `[contract] version`, or the install argparse setup. Update each to match v0.6 expectations. (Repo-scope projection is out of scope per Boundaries — Never do; no test asserts "four directories projected at repo scope" today because `agentbundle install --scope repo` emits `dist/apm/` and `dist/claude-plugins/` install-route artifacts, not per-IDE directories. If the sweep surfaces any such test, that's a finding for a separate PR.)
- Run the full local gate suite. Resolve any drift.
- Commit; push; verify CI green.

**Done when:** all four local gates pass; CI on the open PR is green.

## Rollout

This spec ships behind no flag. The contract bump `v0.5 → v0.6` is the gate: any v0.6 pack declaring `allowed-adapters` invokes the new resolver path; any pack at `< 0.6` (or v0.6 omitting the field) continues through the legacy heuristic. **Adopter-facing behaviour change at the four shipped user-scope packs:** post-merge, a Kiro or Codex adopter installing `atlassian` at user scope lands the pack at their IDE's skills directory; a Claude Code adopter sees no change (still resolves to `~/.claude/skills/`). The repo-scope projection skip for `.github/instructions/` is a visible diff for adopters who currently install the four packs at repo scope and use Copilot's per-repo instructions — they lose the (degraded) Copilot instruction-file artifact. Documented in spec § *Drawbacks*-equivalent in the RFC.

**Reversible.** If a regression surfaces post-merge, revert the implementation PR (the contract bump comes back to v0.5; the four packs' `pack.toml` reverts; the resolver reverts to the heuristic). No data migration; no persistent state change beyond `~/.agentbundle/state.toml`'s `adapter` field (which v0.5 already wrote).

## Risks

- **Test surface across two test roots is large.** ~6 new test modules across `packages/agentbundle/tests/unit/`, `packages/agentbundle/tests/integration/`, and `packages/agentbundle/agentbundle/build/tests/`. Risk: a regression in one root masks a regression in the other. **Mitigation:** the cross-cutting tests section names the end-to-end smoke as the integration belt; T11's final sweep includes both roots.
- **The `_kiro_target_adapters` rail and `_resolve_user_scope_target_adapter` are both heuristics that the spec keeps alive for legacy packs but extends with declarative-field early-return.** Risk: drift between the two functions' v0.6-handling logic. **Mitigation:** T3 covers the `_kiro_target_adapters` early-return + literal-gate widening explicitly; T2's resolver tests cover the install-side; the helper `user_scope_capable_adapters_from_contract()` is shared.
- **The argparse `choices=` derivation at CLI-load time means a broken `adapter.toml` breaks CLI startup, not just install.** Risk: a typo in the contract file makes `agentbundle --help` fail. **Mitigation:** the helper has its own test (T6); a defensive default (empty tuple → all `--adapter` values refused with "no shipped adapters in contract") could land if the risk materialises post-merge.
- **The choices=any-shipped lift creates a small additional refusal-message surface** (the handler-side user-scope-capability check). Risk: a future contract that admits a fifth shipped adapter without a `[scope].user` table would silently surface as "refused at the handler" rather than "refused at argparse." **Mitigation:** the handler's refuse-and-explain message names the adapter and the contract version, so the failure mode is loud not silent.
- **The contract-bump's effect on adopters running pinned CLI versions.** RFC-0011's Drawbacks already names this; not a new risk introduced by the implementation.

## Changelog

- 2026-05-25 — Initial Draft.
- 2026-05-26 — Post-pre-EXECUTE-review revision. Dropped T3 (the repo-scope projection filter task) per RFC-0011 § *Repo-scope projection* erratum. Renumbered T4-T12 → T3-T11. T3 (formerly T4) explicitly pins the `_kiro_target_adapters` literal-`!= "0.3"`-gate widening as the load-bearing v0.6 fix, with a test for the case the current gate breaks. T6 (formerly T7) lifts argparse `choices=` to admit every shipped adapter and moves the user-scope-capability check to the install handler so the pinned refuse-and-explain messages are reachable. T2 explicitly pins the resolver-signature change and the upgrade.py call-site updates (closes Concern 7 from the round-1 review). T9 (README + how-to) collapses the inline four-landing-paths enumeration into a single canonical link to the `Where primitives land` table.
- 2026-05-25 (round-2) — Second pre-EXECUTE-review revision. **T2** retitled "extend `scope.py`" (file already exists per RFC-0004 T17). T2 resolver signature gains `contract_version` and `state_adapter` keyword params; the four steps now include a state-hint short-circuit (AC10b) before the contract-version gate, so upgrades don't re-probe and accidentally refuse on adopters who populated a second `~/.<ide>/` post-install. T2 Approach pins the **explicit per-adapter probe table** (not a single `Path.home()/f".{ide}"` interpolation — codex is an OR-probe). T2 also adds the **`pack_state.adapter` unconditional-assignment lift** (AC10a) — without this, codex / non-hook claude-code installs silently default the state field. T3 swaps the literal `{"0.3", "0.6"}` gate for the semantic predicate `contract_supports_hook_wiring` shared with the validator. T1's "no other scope table modified" test re-scoped to parsed-table-body comparison (not byte-identical, because T1 itself edits the header comment). T5 makes the codex jail-prefix wiring explicit — adds a focused `safety.write_jailed` unit test under T5 rather than relying on T8 as the only catch. T6's `choices=` derivation pinned to `tuple(sorted(...))` for stability. T7 adds the greenfield-suffix case (no CLI home populated → no suffix). T9 grep narrowed to three substrings to survive smart-quote / single-quote rendering drift. T11 sweep-language cleaned of the "three directories projected" residue from pre-revision T3. Closes 4 Blockers + 8 Concerns from the round-2 adversarial review.
- 2026-05-25 (round-2b) — Third pre-EXECUTE-review revision. **T2** lookup re-enumerated as five steps (state-hint at step 2; publisher-drift refused at step 3; probe at step 4; legacy at step 5). **T2** enumerates all four `_resolve_user_scope_target_adapter` call sites — install.py:299 and install.py:1171 in addition to upgrade.py:228 and :311 — and widens `_render_for_user_scope`'s signature to forward the four new kwargs (it's the bridge consumed by both install and upgrade). **T5** Approach now names `_render_for_user_scope` and the exact line (1174-1177) of the existing two-arm dispatch. **T7** suffix logic pinned to use the same per-adapter probe table from T2 so codex-via-`.agents/skills/` is treated consistently between resolver and message rail. **T8** gains an explicit upgrade-with-state-hint integration case (covers AC10b's behavioural commitment). Closes 6 Concerns from the round-2b adversarial review.
- 2026-05-25 (round-2c) — Fourth pre-EXECUTE-review revision. **T2** lookup re-enumerated as **six steps** with publisher-drift at step 0 (before `--adapter` and state-hint), so a v0.6 pack declaring a no-longer-shipped adapter cannot leak through. **T2** adds `install.py:440` as the primary install-time bridge call site (missed in round-2b — it's the line that builds `user_projection` and calls `_render_for_user_scope`). **T2** signature adds a `command_name` kwarg so AC15's refusal message uses the right verb prefix (`install:` vs `upgrade:`). **scope.py helpers renamed** to drop leading underscores (`shipped_adapters_from_contract`, `user_scope_capable_adapters_from_contract`, `contract_supports_hook_wiring`) — matching `scope.py`'s public-export convention since they're imported cross-module. Closes 3 round-2b Concerns; remaining smaller items deferred to EXECUTE.
