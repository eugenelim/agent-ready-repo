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
- `packages/agentbundle/agentbundle/build/tests/test_contract_v06.py::test_no_other_scope_table_modified` — assert claude-code and kiro scope tables byte-identical to a fixture snapshot of the v0.5 state.

**Approach:**
- Edit `packages/agentbundle/agentbundle/_data/adapter.toml`: bump `[contract] version` from `"0.5"` to `"0.6"`; add the `[adapter.codex.scope]` table with the four lines the RFC pins; update the header comment to name RFC-0011 / this spec alongside the existing RFC pointers. **Both edits in one commit.**
- Run `make build-self FORCE=1` to propagate the bump through any projected adapter-toml copies (the lint catches drift).

**Done when:** the three contract tests pass and `make build-self FORCE=1` produces a clean working tree (`git status --short` empty for projected-toml paths).

---

### T2: Module-level `DEFAULT_USER_SCOPE_ADAPTER` constant + four-step resolver rewrite

**Depends on:** T1

**Spec mapping:** AC6, AC9, AC10, AC21. Mode: TDD (resolver is a pure function with enumerable cases).

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
- **Upgrade-side equivalence.** Pin upgrade-time adapter resolution byte-identical to install-time resolution when `adapter=None` (covers AC10's upgrade-side test commitment).

**Approach:**
- Create `packages/agentbundle/agentbundle/scope.py` with the module-level constant `DEFAULT_USER_SCOPE_ADAPTER: str = "claude-code"` plus the shared helpers `_user_scope_capable_adapters_from_contract()` (used by T3's validator and T6's handler-side user-scope-capability check) and `_shipped_adapters_from_contract()` (used by T6's argparse `choices=`). Both helpers read the bundled `adapter.toml`; the former returns adapters declaring `[adapter.<name>.scope].user`, the latter returns every adapter declared in `[adapter.<name>]` blocks.
- Rewrite `_resolve_user_scope_target_adapter` at `install.py:1249-1275` as the four-step lookup. The new signature is `def _resolve_user_scope_target_adapter(pack_dir: Path, *, adapter: str | None, allowed_adapters: list[str] | None) -> str`. Read the `--adapter` value (passed by the install handler from `args.adapter`), read the pack's `[pack.install] allowed-adapters` (already loaded as `pack_install` by the handler), probe `~/.claude/`, `~/.kiro/`, `~/.codex/` OR `~/.agents/skills/` (use `Path.home() / ".<ide>"` plus `Path.exists()`); fall through to greenfield-constant + `allowed-adapters[0]`; finally fall through to legacy heuristic when `allowed_adapters is None`.
- Update the docstring TODO block to reference RFC-0011's resolution and the four-step lookup.
- Update the **two call sites** in `upgrade.py` (the actual invocations at lines 228 and 311; lines 218 and 308 are the matching `from ... import _resolve_user_scope_target_adapter` lines and don't change). Upgrade has no `--adapter` flag, so each invocation passes `adapter=None`. Upgrade loads the pack's `pack.toml` at upgrade time (existing code path); thread `allowed_adapters = pack_install.get("allowed-adapters")` into the call. An upgrade-side test pins that upgrade's resolver result is byte-identical to install's when `adapter=None`.

**Done when:** all parametrized cases in the new test module pass; existing tests under `packages/agentbundle/tests/unit/` that touch the resolver continue to pass; the upgrade-side equivalence test passes; `pytest packages/agentbundle/` exits 0.

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
- **Widen `_kiro_target_adapters`'s literal version gate at `validate.py:379`.** Replace `if contract.get("version") != "0.3": return set()` with the equivalent of `if contract.get("version") not in {"0.3", "0.6"}: return set()`. For v0.6 packs, *before* falling into the on-disk inference, early-return based on `allowed-adapters`: `"kiro" in allowed_adapters ⇒ {"kiro"}`, `allowed_adapters declared but kiro absent ⇒ set()`, `allowed_adapters omitted ⇒ fall into on-disk inference`. v0.3 path unchanged.

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
- In `packages/agentbundle/agentbundle/commands/install.py:1170-1178`, extend the two-arm dispatch to a three-arm:
  ```python
  if target_adapter == "kiro":
      kiro.project(pack_dir, contract, out)
  elif target_adapter == "codex":
      codex.project(pack_dir, contract, out)
  else:
      claude_code.project(pack_dir, contract, out)
  ```
- Confirm `agentbundle.build.adapters.codex` is already importable at the top of the file (RFC-0009's code added it as a peer to `claude_code` and `kiro`).
- For codex user-scope, the post-projection path-rewrite needs to map projected `.agents/skills/<skill>/...` paths to `~/.agents/skills/<skill>/...` per the `[adapter.codex.scope]` table. If `_rewrite_user_scope_hook_paths` (or its peer for non-hook content) doesn't already handle the codex-skills shape, extend it.

**Done when:** the codex-arm dispatch test passes; the integration smoke (T8 below) confirms codex user-scope installs write to `~/.agents/skills/`.

---

### T6: `--adapter` CLI flag with every-shipped-adapter `choices=` + handler-side user-scope-capability check

**Depends on:** T2, T3

**Spec mapping:** AC11, AC12, AC13, AC23. Mode: TDD (argparse + refusal-path correctness).

**Tests:**

Add `packages/agentbundle/tests/unit/test_install_argparse_adapter_flag.py`. Cases:

- **`choices=` derivation matches the live contract — every shipped adapter.** Call the `_shipped_adapters_from_contract()` helper against the bundled `adapter.toml`; assert it returns `("claude-code", "codex", "copilot", "kiro")` (or whatever sorted-tuple order the helper chooses; stability matters).
- **`--adapter claude-code` / `kiro` / `codex` / `copilot` all accepted at parse time.** All four shipped adapters parse cleanly.
- **`--adapter windsurf` rejected at parse time** (argparse refuses unknown choice with stock error — fine, since `windsurf` isn't shipped).
- **Handler-side user-scope-capability check refuses `--adapter copilot`** (Copilot is shipped but lacks `[adapter.copilot.scope].user`). Pinned stderr matches `install: --adapter copilot not admitted as a user-scope-capable adapter under contract v0.6`. **This is the load-bearing case that requires the choices=any-shipped lift — argparse-level `choices=` restricted to user-scope-capable adapters would short-circuit with its stock "invalid choice" error before the pinned message can fire.**
- **`--adapter kiro --scope repo` refused at handler time** (T2 already pinned this; cross-link).
- **Help text matches RFC wording** — assert `"Override the auto-detected adapter at user scope"` appears in `--help` output for the `install` subcommand.

**Approach:**
- In `packages/agentbundle/agentbundle/cli.py:199-229`, add `sp.add_argument("--adapter", choices=_shipped_adapters_from_contract(), help=...)` to the `install` subparser. The helper enumerates **every adapter declared in `[adapter.<name>]` blocks**, not just user-scope-capable ones — that admits Copilot into argparse so the handler can issue the pinned refuse-and-explain.
- The helper `_shipped_adapters_from_contract()` lives in `packages/agentbundle/agentbundle/scope.py` (alongside the `_user_scope_capable_adapters_from_contract()` helper created in T2). Both read the bundled `adapter.toml`.
- The `install` handler at `commands/install.py` reads `args.adapter` and, when not `None`, checks (a) `--scope user` is resolved (else refuse with `install: --adapter is bound to --scope user`), (b) the adapter is user-scope-capable per `_user_scope_capable_adapters_from_contract()` (else refuse with `install: --adapter <name> not admitted as a user-scope-capable adapter under contract v0.6`), (c) the adapter is in the pack's `allowed-adapters` if declared (else refuse with `install: --adapter <name> not in pack's allowed-adapters set`). Then threads the value into the resolver's first step (covered by T2).

**Done when:** all argparse-test cases pass; `agentbundle install --help` shows the new flag with all four shipped adapters in `choices=`.

---

### T7: Install-time message rail

**Depends on:** T2, T5

**Spec mapping:** AC14, AC15. Mode: goal-based check (format-string assertions).

**Tests:**
- Add `packages/agentbundle/tests/unit/test_install_messages.py`. Cases:
  - Successful user-scope install of a v0.6 pack with one matching CLI home: stdout contains `installed: <pack> @ user via <adapter>` (no suffix).
  - Successful user-scope install where two adapters are eligible (both `~/.claude/` and `~/.kiro/` populated, pack declares both) and `--adapter` not passed: stdout contains the suffix `(other declared adapters: kiro; use --adapter to override)`.
  - Repo-scope install: stdout contains `installed: <pack> @ repo` (no `via`).
  - Publisher-vs-installer drift case: simulate a v0.6 pack declaring an adapter the bundled contract doesn't admit; assert refusal stderr matches `install: pack '<name>' declares allowed-adapter '<adapter>' which is not admitted by adapter contract v<X.Y> shipped with agentbundle <cli-version>`.

**Approach:**
- In `packages/agentbundle/agentbundle/commands/install.py`, locate the existing `installed: <pack> @ <scope>` print (RFC-0004's rail). Extend with the `via <adapter>` clause when `scope == "user"`. Compute the "other declared adapters" suffix by intersecting `allowed-adapters` with the populated CLI-home set, minus the chosen adapter.
- Add the install-time contract-drift check: when resolving `allowed-adapters`, intersect with the bundled contract's shipped-adapter set; refuse with the pinned stderr on mismatch.

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
- **All three.** Fixture `$HOME` with all three populated; assert default first-match wins; `--adapter codex` overrides cleanly.

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
- Goal-based grep: assert `docs/guides/how-to/v05-to-v06-pack-upgrade.md` exists and contains the substring `[pack.adapter-contract] version = "0.6"` and `allowed-adapters`.
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
- Goal-based grep: `docs/ROADMAP.md` contains the line `allowed-adapters landed` (or close match per spec AC20).

**Approach:**
- Edit `packs/core/.apm/skills/add-credentialed-skill/SKILL.md`: add one paragraph in the author-facing section per RFC-0011 *Follow-on artifacts* — "If your pack's content is portable across IDEs (skills-only, no IDE-specific agent shape), list every adapter in `allowed-adapters` that supports user scope. The two credentialed packs in this catalogue (`atlassian`, `figma`) list `claude-code`, `kiro`, and `codex` because their skills are pure text + Python and travel cleanly across all three adapters' user-scope skill directories."
- Edit `docs/specs/skill-secrets/spec.md`: add the same paragraph in the author-facing section. No change to AC3 (credential loading).
- Edit `docs/ROADMAP.md`: add the entry under "user-scope" per spec AC20.
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
- Sweep for any test that touched `_resolve_user_scope_target_adapter`, `_kiro_target_adapters`, the four packs' `pack.toml`, the `[contract] version`, or the install argparse setup. Update each to match v0.6 expectations. Tests that previously asserted "all four directories projected at repo scope" for a user-scope pack now need to assert "three directories projected" once the pack declares `allowed-adapters` excluding copilot.
- Run the full local gate suite. Resolve any drift.
- Commit; push; verify CI green.

**Done when:** all four local gates pass; CI on the open PR is green.

## Rollout

This spec ships behind no flag. The contract bump `v0.5 → v0.6` is the gate: any v0.6 pack declaring `allowed-adapters` invokes the new resolver path; any pack at `< 0.6` (or v0.6 omitting the field) continues through the legacy heuristic. **Adopter-facing behaviour change at the four shipped user-scope packs:** post-merge, a Kiro or Codex adopter installing `atlassian` at user scope lands the pack at their IDE's skills directory; a Claude Code adopter sees no change (still resolves to `~/.claude/skills/`). The repo-scope projection skip for `.github/instructions/` is a visible diff for adopters who currently install the four packs at repo scope and use Copilot's per-repo instructions — they lose the (degraded) Copilot instruction-file artifact. Documented in spec § *Drawbacks*-equivalent in the RFC.

**Reversible.** If a regression surfaces post-merge, revert the implementation PR (the contract bump comes back to v0.5; the four packs' `pack.toml` reverts; the resolver reverts to the heuristic). No data migration; no persistent state change beyond `~/.agentbundle/state.toml`'s `adapter` field (which v0.5 already wrote).

## Risks

- **Test surface across two test roots is large.** ~6 new test modules across `packages/agentbundle/tests/unit/`, `packages/agentbundle/tests/integration/`, and `packages/agentbundle/agentbundle/build/tests/`. Risk: a regression in one root masks a regression in the other. **Mitigation:** the cross-cutting tests section names the end-to-end smoke as the integration belt; T11's final sweep includes both roots.
- **The `_kiro_target_adapters` rail and `_resolve_user_scope_target_adapter` are both heuristics that the spec keeps alive for legacy packs but extends with declarative-field early-return.** Risk: drift between the two functions' v0.6-handling logic. **Mitigation:** T3 covers the `_kiro_target_adapters` early-return + literal-gate widening explicitly; T2's resolver tests cover the install-side; the helper `_user_scope_capable_adapters_from_contract()` is shared.
- **The argparse `choices=` derivation at CLI-load time means a broken `adapter.toml` breaks CLI startup, not just install.** Risk: a typo in the contract file makes `agentbundle --help` fail. **Mitigation:** the helper has its own test (T6); a defensive default (empty tuple → all `--adapter` values refused with "no shipped adapters in contract") could land if the risk materialises post-merge.
- **The choices=any-shipped lift creates a small additional refusal-message surface** (the handler-side user-scope-capability check). Risk: a future contract that admits a fifth shipped adapter without a `[scope].user` table would silently surface as "refused at the handler" rather than "refused at argparse." **Mitigation:** the handler's refuse-and-explain message names the adapter and the contract version, so the failure mode is loud not silent.
- **The contract-bump's effect on adopters running pinned CLI versions.** RFC-0011's Drawbacks already names this; not a new risk introduced by the implementation.

## Changelog

- 2026-05-25 — Initial Draft.
- 2026-05-26 — Post-pre-EXECUTE-review revision. Dropped T3 (the repo-scope projection filter task) per RFC-0011 § *Repo-scope projection* erratum. Renumbered T4-T12 → T3-T11. T3 (formerly T4) explicitly pins the `_kiro_target_adapters` literal-`!= "0.3"`-gate widening as the load-bearing v0.6 fix, with a test for the case the current gate breaks. T6 (formerly T7) lifts argparse `choices=` to admit every shipped adapter and moves the user-scope-capability check to the install handler so the pinned refuse-and-explain messages are reachable. T2 explicitly pins the resolver-signature change and the upgrade.py call-site updates (closes Concern 7 from the round-1 review). T9 (README + how-to) collapses the inline four-landing-paths enumeration into a single canonical link to the `Where primitives land` table.
