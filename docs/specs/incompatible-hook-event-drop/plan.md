# Plan: incompatible-hook-event-drop

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done (2026-05-26)

> **Plan contract:** this is the implementation strategy. Unlike the spec, this document is allowed to change as you learn. When it changes substantially (a different approach, not just a re-ordering), note why in the changelog at the bottom.

## Approach

Single-PR implementation. The change has three thin layers, none of which require new contract fields or new modules:

1. **Refactor:** lift the safe-load walk inside `check_kiro_wiring` into a sibling helper so the security/correctness rails (symlink + TOML parse) are callable independently of the compatibility rail (`check_kiro_attach_to_agent`) that this spec swallows. The lift is mechanical; existing tests stay green.
2. **Validate-side swallow:** `commands/validate.py`'s two refusal sites (rails 4c / 4d) stop returning 1 on the compatibility refusal categories. Instead, the per-file drop list flows to **stdout** as `info:` text. Symlink and parse-fail refusals continue to exit 1.
3. **Install-side enumeration + formatter extension:** add `_enumerate_event_dropped_wirings` alongside the shipped `_enumerate_dropped_primitives`; extend `_format_dropped_warning` to compose the three-clause grammar; wire the enumeration into `_maybe_emit_dropped_warning`. The single-clause (primitive-type-only) case stays byte-identical.

Tests-first per the work-loop discipline. Most tasks are TDD-shaped; one is goal-based (cross-caller survey at merge). Task graph: T1 (refactor) is `Depends on: none`; T2 (validate swallow) depends on T1; T3 / T4 (enumerator + formatter) are independent siblings both `Depends on: none`; T5 (wire-up) depends on T3 + T4; T6 (integration tests) depends on T2 + T5; T8 (gates + status flip) depends on everything.

The riskiest part is **AC8** — the existing primitive-type-only tests at `packages/agentbundle/tests/unit/test_install_dropped_primitives_warning.py` must stay green byte-for-byte. The formatter extension is additive; degrade-when-event-list-empty is the load-bearing invariant.

## Constraints

- **Constrained by:** `docs/specs/dropped-primitives-coverage/` (shipped 2026-05-26) — this spec reuses its warning-rail helpers and extends its grammar. The parent spec is **frozen** per `docs/CONVENTIONS.md:80`; the extension lives in this sibling spec.
- **Constrained by:** RFC-0005 — the `merge-into-agent-json` mode + `agent-event-vocabulary` semantics. The two refusal sites this spec swallows were introduced by RFC-0005's T2 and T6.
- **Single PR per the parent spec's atomicity precedent.** Partial landings risk validate exiting 0 but install still refusing, or vice versa — opposite signals from the same condition.
- **No new third-party Python dependency.** stdlib (`tomllib` for reads, hand-rolled walking) plus existing helpers.
- **No new contract field, schema entry, or pack manifest field.** The fix is entirely in install handler call sites + validate.py call sites + one extracted helper in `scope_rails.py`.

## Construction tests

Most construction tests live under **Tasks** below (per-task `Tests:` subsections).

**Cross-cutting tests** (span more than one task):

- **End-to-end install integration suite extension** at `packages/agentbundle/tests/integration/test_install_dropped_primitives_warning.py` (existing module — extended, not replaced). New cases: `agentbundle install --pack core --scope repo --adapter kiro <root>` exits 0 + emits the three-clause warning + projects skills/agents but not the session-start wiring; positive control `--adapter claude-code` projects the SessionStart wiring. This is T6; cross-referenced here for the cross-cutting view. Covers spec AC10; prerequisites span T1-T5.
- **`pre-pr.py` end-to-end** — `python3 tools/hooks/pre-pr.py` exits 0 on the final tree. Covers spec AC17; spans every task.
- **`make build-self FORCE=1` clean** after the final commit. Covers spec AC16; spans T1-T8 (no pack-content changes in this spec, so the projection invariant is "no diff" rather than "diff matches expectations").

## Tasks

Order matters — listed in the order they should be done. The graph has two independent task pairs (T1 alone; T3 + T4 as siblings); the rest is sequential because validate-side and install-side both depend on the refactored helpers + extended formatter.

### T1: Extract safe-load helper from `check_kiro_wiring` (refactor)

**Depends on:** none

**Spec mapping:** AC3, AC3b, AC4 (the security/correctness rails must continue to refuse — extracting them into their own callable makes that invariant local rather than relying on the validate.py call-site to short-circuit by string-matching). Mode: TDD (existing tests are the safety net; the lift is a pure refactor — public surface unchanged).

**Tests:**

The existing tests for `check_kiro_wiring` in `packages/agentbundle/agentbundle/build/tests/test_scope_rails.py` (search for `check_kiro_wiring` test cases) stay green before and after. Plus:

- New module `packages/agentbundle/agentbundle/build/tests/test_load_pack_hook_wiring_safely.py`:
  - `test_returns_loaded_tomls_when_clean` — fixture pack with valid hook-wiring + agents; helper returns `(wiring_tomls, agent_basenames)` with the expected dict + set.
  - `test_returns_refusal_string_on_hook_wiring_symlink` — fixture with a symlink under `.apm/hook-wiring/`; helper returns a string matching `pack <name>'s hook-wiring entry is a symlink`.
  - `test_returns_refusal_string_on_toml_parse_failure` — fixture with a malformed `.toml`; helper returns a string matching `failed to parse`.
  - `test_returns_refusal_string_on_agent_symlink` — fixture with a symlink under `.apm/agents/`; helper returns a string matching `pack <name>'s agent entry is a symlink`.
  - `test_empty_hook_wiring_dir_returns_empty_tuple` — fixture with `.apm/` present but no `hook-wiring/` subdir; helper returns `({}, <agent_basenames>)` or equivalent "nothing to load" shape.

**Approach:**

- Extract `scope_rails.py:414-468` (the walk inside `check_kiro_wiring`) into a sibling function `_load_pack_hook_wiring_safely(pack_path: Path, pack_name: str) -> tuple[dict, set] | str`. Return type is the loaded tuple on success; a refusal string on any of the three security/correctness violations (hook-wiring symlink, agent symlink, TOML parse fail). Function is module-public-by-convention (prefixed with `_` but importable from validate.py).
- Refactor `check_kiro_wiring` to call the new helper:
  ```python
  loaded = _load_pack_hook_wiring_safely(pack_path, pack_name)
  if isinstance(loaded, str):
      return loaded  # security or correctness refusal
  wiring_tomls, agent_basenames = loaded
  return check_kiro_attach_to_agent(pack_name, wiring_tomls, agent_basenames, target_adapters)
  ```
- Public signatures of `check_kiro_wiring`, `check_kiro_attach_to_agent`, `check_kiro_event_vocabulary` are byte-identical post-refactor.
- Re-run the full `pytest packages/agentbundle/agentbundle/build/tests/test_scope_rails.py`; all tests stay green.

**Done when:** the new 5 tests pass; existing `test_scope_rails.py` tests stay green; `grep -n "def _load_pack_hook_wiring_safely" packages/agentbundle/agentbundle/build/scope_rails.py` returns exactly one match; `check_kiro_wiring`'s body is <= 5 lines after the lift (the walk is gone; only the call to the new helper + the dispatch to `check_kiro_attach_to_agent` remain).

---

### T2: Switch `validate.py` rails 4c/4d to non-refusal for hook-wiring compatibility

**Depends on:** T1, T3, T4 (uses the shared `_drop_warning.py` module created in T3+T4)

**Spec mapping:** AC1, AC2, AC3, AC3b, AC4, AC4b, AC5, AC6b. Mode: TDD.

**Tests:**

New module `packages/agentbundle/tests/unit/test_validate_hook_wiring_per_file_compatibility.py`:

- `test_validate_packs_core_exits_zero` — invoke `commands/validate.validate(pack_path=packs_dir / "core")`; assert return code 0; assert no `validate:` refusal substring on stderr; assert stdout contains the `info: pack core: the following hook-wiring file(s) will not project to kiro (event not in adapter vocabulary): hook-wiring/session-start.toml.` line. Load-bearing AC1 + AC2 pin.
- `test_validate_swallows_missing_attach_to_agent` — fixture pack with a hook-wiring that omits `attach-to-agent` (`data.get("attach-to-agent")` returns `None`) AND has its event IN the vocabulary (so only the attach-to-agent rail fires); validate exits 0; stdout contains an `info:` line with reason `kiro requires 'attach-to-agent'`. **The sibling round-3 test `test_validate_refuses_on_empty_attach_to_agent_string` covers the explicit-empty-string case (refuses, exit 1).**
- `test_validate_still_refuses_on_hook_wiring_symlink` — fixture with a symlink under `.apm/hook-wiring/`; validate exits 1; stderr contains `pack <name>'s hook-wiring entry is a symlink`. Pins AC3.
- `test_validate_still_refuses_on_toml_parse_failure` — fixture with a malformed `.toml`; validate exits 1; stderr contains `failed to parse`. Pins AC4.
- `test_validate_still_refuses_on_unknown_agent_reference` — fixture with `attach-to-agent = "ghost-agent"` and NO `agents/ghost-agent.md`; validate exits 1; stderr contains `or names an unknown agent`. **This is the load-bearing AC4b case** — the swallow distinguishes missing-attach-to-agent (compat, swallowed) from unknown-agent (correctness, kept).
- `test_validate_refuses_on_empty_attach_to_agent_string` — fixture with `attach-to-agent = ""` (explicit empty string, distinct from omitted field); validate exits 1 with the same refusal text. Pins the round-3 spec/plan reconciliation: empty string is treated as "unknown agent" (matches today's `scope_rails.py:332` behavior — `"" not in agent_basenames` is True). The contrast test `test_validate_swallows_missing_attach_to_agent` uses an omitted field (`data.get("attach-to-agent")` returns `None`); the swallow fires there but not on `""`.
- `test_validate_still_refuses_on_allowed_adapters_violation` — fixture with a schema-cross-field violation on `[pack.install] allowed-adapters` (reuse one of PR #140's existing test fixtures, or construct a minimal one); validate exits 1. Pins AC5's scoping that the swallow doesn't bleed beyond hook-wiring compatibility.
- `test_validate_info_text_uses_pinned_wording_one_file_one_reason` — assert validate stdout for the `core + kiro` case matches the AC2 byte-for-byte: `info: pack core: the following hook-wiring file(s) will not project to kiro (event not in adapter vocabulary): hook-wiring/session-start.toml.`
- `test_validate_info_text_uses_pinned_wording_one_file_two_reasons` — fixture pack with one wiring tripping BOTH the vocabulary AND attach-to-agent rails; validate stdout matches AC2's two-reason form (`(event not in adapter vocabulary + kiro requires 'attach-to-agent')`).
- `test_validate_info_text_uses_pinned_wording_two_files` — fixture pack with two distinct wirings each tripping the vocabulary rail; validate stdout matches AC2's two-file form (serial-comma-plus-`and`, lexicographically sorted).

**Approach:**

- At `validate.py:196-199` (rail 4c) and `:209-217` (rail 4d), replace the unconditional `return 1` with the following dispatch sequence (single block; both rails fold into one):

  ```python
  # 1. Safe-load: security + correctness refusals (AC3, AC3b, AC4).
  loaded = _load_pack_hook_wiring_safely(pack_path, pack_name)
  if isinstance(loaded, str):
      print(f"validate: {loaded}", file=sys.stderr)
      return 1
  wiring_tomls, agent_basenames = loaded

  # 2. Unknown-agent refusal (AC4b) — discriminated from input data, NOT
  #    from inspecting check_kiro_attach_to_agent's refusal text, which
  #    is bytewise identical for missing-vs-unknown subcases per
  #    scope_rails.py:332-337 (load-bearing per round-2 review).
  #
  #    Condition matches spec AC4b exactly: `attach is not None and
  #    isinstance(attach, str) and attach not in agent_basenames`.
  #    Empty string is preserved as "unknown agent" (kept refusal,
  #    exit 1) to match today's helper behavior at scope_rails.py:332
  #    — `"" not in agent_basenames` is True, so today's helper
  #    refuses on `attach = ""`; this spec preserves that.
  if "kiro" in target_adapters:
      for stem, body in sorted(wiring_tomls.items()):
          attach = body.get("attach-to-agent") if isinstance(body, dict) else None
          if (
              attach is not None
              and isinstance(attach, str)
              and attach not in agent_basenames
          ):
              # Use the existing helper's pinned refusal text — single source
              # of truth for the wording (RFC-0005:474). The helper composes
              # the message even though we're only firing the unknown-agent
              # branch; the substring is invariant.
              refusal = (
                  f"pack {pack_name}'s hook-wiring {stem}.toml "
                  f"does not declare 'attach-to-agent' (or names an unknown "
                  f"agent); required for kiro projection"
              )
              print(f"validate: {refusal}", file=sys.stderr)
              return 1

  # 3. Compatibility drops (missing-attach OR out-of-vocab event) — flow to
  #    the shared enumerator + info-line emit. Single source of truth with
  #    the install side (AC6b).
  info_drops = _drop_warning.enumerate_event_dropped_wirings(
      pack_path, "kiro", contract,
  )
  if info_drops:
      info = _drop_warning.format_drop_message(
          mode="validate_info",
          pack_name=pack_name,
          adapter="kiro",
          dropped_counts={},
          compatible_types=[],
          event_drops=info_drops,
      )
      print(info)  # stdout per AC2 + adopter direction
  return 0
  ```

- The unknown-agent inline check above duplicates what `check_kiro_attach_to_agent` already does internally — that's deliberate. The helper composes one refusal string for both subcases and cannot tell its caller which branch fired; rather than extending its signature (out-of-scope helper surgery), the call site re-checks `attach not in agent_basenames` against the same input data. The refusal text matches `check_kiro_attach_to_agent`'s output byte-for-byte (RFC-0005-pinned at `docs/rfc/0005-user-scope-hook-support.md:474`). A future RFC-0005 wording change would need to update both call sites — the duplication is documented in the inline comment so a maintainer notices.
- `check_kiro_attach_to_agent` is NOT called from validate.py anymore in the new flow. It's still callable (and called from `check_kiro_wiring`'s composer for any strict-refusal use case); only the validate.py call site is reorganised.
- `target_adapters` for the rail comes from `_kiro_target_adapters(pack_data, pack_path)` (the existing helper at validate.py:194). `contract` is read via the existing helper accessor (per `_drop_warning.py`'s contract-loading approach — implementer reuses the path).

**Done when:** all 6 tests pass; `agentbundle validate packs/core; echo $?` prints the `info:` line on stdout and `0` on the next line; the symlink-and-parse-fail fixtures still exit 1 with the expected stderr text.

---

### T3: Add `enumerate_event_dropped_wirings` helper to new shared module

**Depends on:** none

**Spec mapping:** AC6, AC6b, AC6c. Mode: TDD (pure enumeration logic).

**Tests:**

Extend `packages/agentbundle/tests/unit/test_install_dropped_primitives_warning.py` (existing module). New cases:

- `test_enumerate_event_drops_core_against_kiro` — `_enumerate_event_dropped_wirings(packs_dir / "core", "kiro", contract)` returns `[("hook-wiring/session-start.toml", "event not in adapter vocabulary")]`. Pins the load-bearing case.
- `test_enumerate_event_drops_emits_two_entries_when_both_reasons_fire` — fixture pack with a hook-wiring TOML that uses an out-of-vocab event AND lacks `attach-to-agent`, against kiro: returns **exactly two entries** `[(file, "event not in adapter vocabulary"), (file, "kiro requires 'attach-to-agent'")]` — one drop entry per `(file, reason_category)` per spec AC6's pinned shape. **Never concatenated** at the enumerator output; the formatter dedups at file level for `<file-list>` rendering.
- `test_enumerate_event_drops_silent_for_claude_code` — claude-code's hook-wiring projection declares no `agent-event-vocabulary` (verify against `_data/adapter.toml` to avoid hardcoding); helper returns `[]`.
- `test_enumerate_event_drops_silent_when_type_dropped` — for copilot (where hook-wiring is dropped at the type level), the helper returns `[]`. Pins the "gated on non-dropped type" semantic in AC6 step 1.
- `test_enumerate_event_drops_handles_wiring_with_no_events_table` — fixture wiring TOML that has no `[[hooks.<EventName>]]` table (well-formed but empty hooks section): helper returns `[]` for that file. Pins defensive handling for the empty-but-valid case.
- `test_enumerate_event_drops_emits_entry_on_parse_failure` — fixture wiring TOML that's malformed (unparseable): helper emits `(relpath, "hook-wiring TOML failed to parse")`. **Pins AC6c's asymmetry resolution** — install enumerates the parse-fail as a drop entry, surfacing it in the warning; validate refuses with exit 1 per AC4 (separate code path).
- `test_enumerate_event_drops_attach_to_agent_only_when_adapter_is_kiro` — fixture pack with a wiring missing `attach-to-agent`, against an adapter that's NOT kiro but DOES declare `agent-event-vocabulary` (hypothetical — no such adapter today). The test constructs the contract fixture **inline as a Python dict literal** in the test body (no on-disk fixture file needed); the enumerator's `contract` argument is a plain dict so an inline literal suffices. Helper returns no attach-to-agent reason. Pins the kiro-only scoping in AC6 step 2 second bullet.
- `test_enumerate_event_drops_sorted_by_filename` — fixture pack with multiple wirings each tripping the rail; returned list is sorted by `<wiring_relpath>`. Pins determinism.

**Approach:**

- **Create a new shared module** at `packages/agentbundle/agentbundle/commands/_drop_warning.py` (the underscore prefix marks it module-private-by-convention while still permitting cross-module imports from `install.py` and `validate.py`). This module owns the enumerator AND the formatter (T4). Imported by both `install.py` (replacing the local `_enumerate_event_dropped_wirings` proposal) and `validate.py` (replacing the proposed in-validate.py helper).
- Add the enumerator as a module-public function (no leading underscore on the function itself):
  ```python
  def enumerate_event_dropped_wirings(
      pack_dir: Path,
      adapter: str,
      contract: dict,
  ) -> list[tuple[str, str]]:
      """Return per-file hook-wiring drops as (relpath, reason_category) pairs.

      AC6 / AC6b / AC6c of spec incompatible-hook-event-drop.
      """
      # Step 1: gate on non-dropped type.
      if _is_primitive_type_dropped(contract, adapter, "hook-wiring"):
          return []
      # Step 2: walk hook-wiring TOMLs.
      drops: list[tuple[str, str]] = []
      hook_wiring_dir = pack_dir / ".apm" / "hook-wiring"
      if not hook_wiring_dir.exists():
          return []
      vocab = _adapter_agent_event_vocabulary(contract, adapter)
      for toml_path in sorted(hook_wiring_dir.glob("*.toml")):
          relpath = f"hook-wiring/{toml_path.name}"
          try:
              data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
          except (tomllib.TOMLDecodeError, OSError):
              # AC6c: install-time emits a parse-fail drop entry;
              # validate-time refuses earlier (separate code path).
              drops.append((relpath, "hook-wiring TOML failed to parse"))
              continue
          # 2a: vocab check.
          if vocab is not None:
              events = data.get("hooks", {})
              if isinstance(events, dict):
                  for event_name in sorted(events.keys()):
                      if event_name not in vocab:
                          drops.append((relpath, "event not in adapter vocabulary"))
                          break  # one entry per file per reason category (AC6 dedup)
          # 2b: attach-to-agent check (kiro-only, presence-only — AC4b
          # carve-out: NON-EMPTY unknown-agent references stay as
          # validate-time refusals; empty string and missing field both
          # flow here as install-side drops. The validate side refuses
          # on `attach = ""` per the test pin, but install-side
          # enumerator treats omitted-or-empty as "effectively missing"
          # for warning purposes — adopters running install-without-validate
          # see the file named in the warning rather than a silent
          # downstream projection error.
          if adapter == "kiro":
              attach = data.get("attach-to-agent")
              if not isinstance(attach, str) or not attach:
                  drops.append((relpath, "kiro requires 'attach-to-agent'"))
      return drops
  ```
- Companion helper `_adapter_agent_event_vocabulary(contract, adapter)` returning the list (or `None` if undeclared) — read from the contract's `[adapter.<name>.projections.hook-wiring].agent-event-vocabulary` field. **Existing helper survey (2026-05-26):** searched `install.py` for `agent_event_vocabulary`, `vocab`, `event_vocabulary` — no existing helper that does exactly this exists; the closest is `_kiro_event_vocabulary` in `validate.py:304` (kiro-hardcoded). Add a fresh adapter-parametric helper in `_drop_warning.py`; do not import from `validate.py` (validate.py imports from `_drop_warning.py`, not vice versa, to keep the dependency direction one-way).
- Companion predicate `_is_primitive_type_dropped(contract, adapter, primitive)` — **existing helper survey (2026-05-26):** `_enumerate_dropped_primitives` at `install.py:1061` walks `[[adapter.<name>.projection]]` entries internally; no exposed predicate exists. Either extract from `_enumerate_dropped_primitives`'s body (preferred — single source of truth for the "is this type dropped?" question) or add fresh. Pick during implementation; the choice is the implementer's.

**Done when:** all 7 new tests pass; the existing 12 tests for `_enumerate_dropped_primitives` stay green; `pytest packages/agentbundle/tests/unit/test_install_dropped_primitives_warning.py` exits 0; `packages/agentbundle/agentbundle/commands/_drop_warning.py` exists with the public `enumerate_event_dropped_wirings` function.

---

### T4: Move `_format_dropped_warning` into shared module + extend with three-clause grammar + validate-mode

**Depends on:** none (T3 creates the module file; this task adds the formatter to the same module — T3 and T4 can land in either order or be merged into one commit at the implementer's discretion)

**Spec mapping:** AC7, AC8, AC6b (the validate-mode formatter is the same helper with a `mode` parameter). Mode: TDD (pure formatter logic).

**Tests:**

Extend `packages/agentbundle/tests/unit/test_install_dropped_primitives_warning.py`. New cases:

- `test_format_warning_pre_amendment_wording_pinned` — **load-bearing AC8 pin.** Assert the formatter output for the exact input shape `pack_name="core", adapter="codex", dropped_counts={"command": 1}, compatible_types=["skill","agent","hook-body","hook-wiring"], event_drops=[], mode="install_warning"` equals the inline-quoted byte string:
  > `warning: pack core ships 1 command that codex projects as 'dropped'; these primitives will not be installed. The compatible primitives (skill, agent, hook-body, hook-wiring) will proceed.`
  Quote the string in the test source verbatim (do NOT compute it via the existing formatter — that would be tautological). This guards against accidental edits of the existing tests in the module that would let the formatter drift without detection.
- `test_format_warning_event_only` — call with `dropped_counts={}` and `event_drops=[(file, reason)]`; assert output is `warning: the following hook-wiring file(s) will be skipped (event not in adapter vocabulary): hook-wiring/session-start.toml. The compatible primitives (skill, agent, hook-body, hook-wiring) will proceed.` No `Additionally,` prefix; the event clause is the lead clause.
- `test_format_warning_primitive_and_event` — both non-empty; assert exact three-clause output with `Additionally, ` (capital `A`, comma-space) prefix on the event clause.
- `test_format_warning_reason_summary_dedupe` — `event_drops` containing two entries with the same file but different reason categories; `<reason-summary>` = `event not in adapter vocabulary + kiro requires 'attach-to-agent'` (vocabulary first; joined with ` + ` space-plus-space). Pins AC7's order rule.
- `test_format_warning_file_list_dedupe_and_sort` — `event_drops` with multiple entries for the same file (different reasons): `<file-list>` shows the file ONCE; multiple distinct files appear lexicographically sorted with serial-comma-plus-`and`.
- `test_format_validate_info_one_file_one_reason` — `mode="validate_info"`, single file + reason; assert output matches AC2's pinned wording exactly: `info: pack core: the following hook-wiring file(s) will not project to kiro (event not in adapter vocabulary): hook-wiring/session-start.toml.`
- `test_format_validate_info_one_file_two_reasons` — `mode="validate_info"`, single file with both reasons; assert AC2's two-reason form.
- `test_format_validate_info_two_files` — `mode="validate_info"`, two files; assert AC2's two-file form (sorted, serial-comma-plus-`and`).
- `test_format_validate_info_adapter_name_substituted` — `mode="validate_info"`, single file + single reason, `adapter="copilot"` (or any non-kiro string); assert the output substitutes `copilot` into the line and the rest of the wording is invariant byte-for-byte (a hardcoded `kiro` in the formatter source would fail this test). Pins AC2's fourth case.
- `test_format_validate_info_refuses_when_dropped_counts_nonempty` — call the formatter in `validate_info` mode with `dropped_counts={"command": 1}` AND any non-empty `event_drops`; assert `ValueError` is raised. Pins the formatter's defensive-by-construction contract: validate-mode cannot compose a primitive-type clause (the rail is event-only). Closes round-2 Concern 5.

**Approach:**

- **Move** `_format_dropped_warning` from `commands/install.py` into `commands/_drop_warning.py` (the module created in T3). Re-export from install.py as a name-alias for backward compat with any existing test that imports it: `from agentbundle.commands._drop_warning import format_drop_message as _format_dropped_warning`. The function name in the new module is `format_drop_message` (module-public, no leading underscore); the alias keeps PR #156's tests working.
- Extend the signature:
  ```python
  def format_drop_message(
      *,
      pack_name: str,
      adapter: str,
      dropped_counts: dict[str, int],
      compatible_types: list[str],
      event_drops: list[tuple[str, str]] | None = None,
      mode: Literal["install_warning", "validate_info"] = "install_warning",
  ) -> str:
  ```
- `mode="install_warning"` behaviour (the PR #156 case, extended):
  - When `event_drops` is `None` or empty, output is byte-identical to PR #156's single-clause `warning:` line.
  - When `event_drops` is non-empty, compose the three-clause grammar:
    - `<reason-summary>`: deduplicate reason categories, then re-order using a pinned tuple `("event not in adapter vocabulary", "kiro requires 'attach-to-agent'", "hook-wiring TOML failed to parse")` — categories appear in this order; any future category (defensive) appears after in stable-sorted order.
    - `<file-list>`: deduplicate file paths, lexicographically sort, join with serial-comma-plus-`and` using the existing `_join_serial_comma` helper (which moves into `_drop_warning.py` alongside the formatter).
    - Build the event clause: `the following hook-wiring file(s) will be skipped ({reason_summary}): {file_list}.`
    - When `dropped_counts` is also non-empty: prefix with `Additionally, `.
  - Compose: `warning: <primitive_clause?> <event_clause?> <closing_clause>`. Drop missing clauses; join with single spaces.
- `mode="validate_info"` behaviour (new):
  - Ignore `dropped_counts` and `compatible_types` (validate doesn't enumerate primitive-type drops; the rail is event-only).
  - Require `event_drops` non-empty (caller guards).
  - Output: `info: pack {pack_name}: the following hook-wiring file(s) will not project to {adapter} ({reason_summary}): {file_list}.` — single-line, NO closing clause, NO `Additionally,` prefix (never composes with a primitive-type clause in this mode).
  - `<reason-summary>` and `<file-list>` use the same dedup + order rules as install_warning mode.
- Raise `ValueError` if both `dropped_counts` and `event_drops` are empty in `install_warning` mode; raise `ValueError` if `event_drops` is empty in `validate_info` mode; **raise `ValueError` if `dropped_counts` is non-empty in `validate_info` mode** (validate-side rail is event-only — composing a primitive-type clause from validate would be a caller-side bug per round-2 Concern 5). Caller-side guards catch these before entry; the raises are defensive.

**Done when:** all 6 new tests pass; the existing 12 tests in the module stay green byte-for-byte; `pytest packages/agentbundle/tests/unit/test_install_dropped_primitives_warning.py` exits 0.

---

### T5: Wire enumerator + formatter into `_maybe_emit_dropped_warning`

**Depends on:** T3, T4

**Spec mapping:** AC9. Mode: TDD.

**Tests:**

Extend `packages/agentbundle/tests/unit/test_install_dropped_primitives_warning.py`:

- `test_maybe_emit_calls_event_enumerator` — monkey-patch or spy on `_enumerate_event_dropped_wirings`; assert called once with the pack_dir + adapter + contract from the install scope.
- `test_maybe_emit_short_circuit_covers_event_only_case` — first call against a pack that has ONLY event drops (no primitive-type drops); warning fires once. Second call same (root, pack, adapter, scope); silent. Pins the short-circuit key is unchanged.
- `test_maybe_emit_silent_when_both_empty` — pack with no primitive-type drops AND no event drops; no warning fires; the seen-set is updated (consistent with PR #156's no-op caching).
- `test_maybe_emit_full_three_clause_for_kiro_core` — fixture install of `core` via kiro; assert stderr contains the exact AC10 expected three-clause warning text. Integration-shape but lives in the unit module for inputs-stable assertion.

**Approach:**

- Extend `_maybe_emit_dropped_warning`'s body to call `_enumerate_event_dropped_wirings(pack_dir, adapter, contract)` after `_enumerate_dropped_primitives`. Pass both results to `_format_dropped_warning`.
- Update the guard: warning fires when `dropped_counts` OR `event_drops` is non-empty. Currently the guard is `if not dropped: return` — change to `if not dropped and not event_drops: ...` (still records the no-op into `_DROPPED_WARNING_SEEN`).
- Short-circuit key unchanged. `(root, pack_name, adapter, scope)` covers both drop kinds since they derive from the same inputs.
- The `_enumerate_event_dropped_wirings` call needs the contract — read it via the existing accessor in install.py (find by `grep _contract_data\|_adapter_contract\|_load_contract` in install.py; reuse). Don't reload from disk.

**Done when:** all 4 new tests pass; `_maybe_emit_dropped_warning` exhibits the new behavior; existing primitive-type-only tests stay green.

---

### T6: End-to-end install integration tests for the kiro+core case

**Depends on:** T2, T5

**Spec mapping:** AC10. Mode: TDD (integration; install handler as black box).

**Tests:**

Extend `packages/agentbundle/tests/integration/test_install_dropped_primitives_warning.py` (existing module from PR #156):

- `test_install_core_via_kiro_emits_three_clause_warning_and_projects_other_primitives` — `agentbundle install --pack core --scope repo --adapter kiro <tmp>`; assert rc 0; assert stderr contains the exact three-clause warning naming `hook-wiring/session-start.toml`; assert each agent in `core/.apm/agents/` produces a kiro agent JSON file at `<tmp>/.kiro/agents/<basename>.json` (the path is derivable from `[adapter.kiro.projections.hook-wiring].target.repo = ".kiro/agents/<attach-to-agent>.json"` in `_data/adapter.toml`); assert `<tmp>/.kiro/skills/<skill>/SKILL.md` exists for each skill; assert NO kiro agent JSON file contains a top-level `hooks.SessionStart` key (read each JSON, assert `"SessionStart" not in json.loads(text).get("hooks", {})`). **Note on path resolver:** the install handler computes the projection target via `agentbundle.build.target_resolver.resolve_target` (callable at `packages/agentbundle/agentbundle/build/target_resolver.py`). Test imports + calls this resolver directly rather than hardcoding; if `resolve_target` doesn't exist by that exact name during T6 implementation, the implementer either uses the actual symbol name (grep `target_resolver.py` for the public function) or extracts a minimal helper as part of T6 scope.
- `test_install_core_via_claude_code_writes_sessionstart_positive_control` — `agentbundle install --pack core --scope repo --adapter claude-code <tmp>`; resolve the projection target for the claude-code hook-wiring projection (`[adapter."claude-code".projections.hook-wiring]` → typically `<tmp>/claude-plugins/core/.claude/settings.local.json` per RFC-0012's repo-scope dist-tree path — same path resolver as the kiro test); assert the file exists; assert `json.loads(file.read_text()).get("hooks", {}).get("SessionStart")` is non-empty. Pins that the per-file drop is per-adapter, not blanket.

(Dropped from this task: the dual-scope test that was previously listed here. Spec AC10 names only `--scope repo`; the dual-scope dedup semantics are already covered by T5's `test_maybe_emit_short_circuit_covers_event_only_case`. If a dual-scope test surfaces as load-bearing during EXECUTE, surface as a plan amendment rather than smuggling it in here.)

**Approach:**

- Reuse the existing integration-test fixture pattern (`tmp_path` + monkeypatched `HOME` + `<repo>` argument) from PR #156's `test_install_dropped_primitives_warning.py`.
- Assert on stderr content via the `capsys` fixture; pin the exact wording via the formatter helper to keep the assertion future-proof against minor rephrasings.

**Done when:** all 3 new integration tests pass; `pytest packages/agentbundle/tests/integration/` exits 0.

---

### T8: Spec README + ROADMAP + gates + status flip

**Depends on:** T1, T2, T3, T4, T5, T6

**Spec mapping:** AC12, AC13, AC14, AC15, AC16, AC17. Mode: goal-based check.

**Tests:**

- `pytest packages/agentbundle/` exits 0 (AC15).
- `make build-self FORCE=1 && git status --short` shows no output (AC16).
- `python3 tools/hooks/pre-pr.py` exits 0 (AC17).
- `grep -n "incompatible-hook-event-drop" docs/specs/README.md` returns a non-empty match (AC12).
- `grep -n "incompatible-hook-event-drop" docs/backlog.md` returns a non-empty match (AC13).
- `grep -rn -E "does not declare 'attach-to-agent'|not in adapter.*agent-event-vocabulary" tools/ .github/ docs/guides/ docs/architecture/ docs/product/` returns empty (AC14). The whitelisted-directories command sidesteps the spec/RFC self-match documented in spec § Boundaries.

**Approach:**

- Add a row to `docs/specs/README.md`'s active-spec table for `incompatible-hook-event-drop` (status Shipped, brief one-line summary, cross-link to spec).
- Add a section to `docs/backlog.md` recording the spec → shipped milestone (mirror the layout of the existing `dropped-primitives-coverage` section).
- Run the cross-caller survey one more time at merge-prep; record the result.
- **Flip status fields** as the final edit before commit:
  - `docs/specs/incompatible-hook-event-drop/spec.md` line `- **Status:** Draft` → `- **Status:** Shipped (YYYY-MM-DD)`.
  - `docs/specs/incompatible-hook-event-drop/plan.md` line `- **Status:** Drafting` → `- **Status:** Done`.
- Commit; push; verify CI green.

**Done when:** all gates green; status fields flipped; README + ROADMAP updated; cross-caller survey clean; CI on the open PR is green.

## Rollout

This spec ships behind no flag. The validate-side change makes a previously-failing invocation succeed; the install-side change adds a new clause to an existing warning. Both are pure relaxations — no adopter who currently has a working install loses anything; previously-blocked Kiro-on-`core` adopters gain a working install.

**Adopter-facing behaviour change:** post-merge, an adopter running `agentbundle validate packs/core` sees exit 0 + an `info:` line on stdout (previously: exit 1 + a `validate:` line on stderr). An adopter running `agentbundle install --pack core --adapter kiro <root>` sees the three-clause warning + a working partial install (previously: refused at validate-time upstream, install never reached).

**Reversible.** If a regression surfaces post-merge, revert the PR. No data migration; no persistent state change. The refactor in T1 is the only piece that touches widely-used code (`scope_rails.py`); its public surface is byte-identical so a revert is a clean delete.

## Risks

- **AC8's "byte-identical when event-drops empty" invariant is the load-bearing piece.** The formatter extension is additive but the grammar must compose correctly. **Mitigation:** every existing test stays in the module and must pass byte-identically (verified during T4); a failure of any existing test signals the additive shape isn't actually additive.
- **The validate.py swallow accidentally broadens beyond hook-wiring compatibility.** The risk: a future call-site refactor uses the same code path for a different rail and the swallow leaks. **Mitigation:** AC5's scoping test (`test_validate_still_refuses_on_other_rail_failures`) pins that rails 4a / 4b / 4e continue to refuse; the T1 helper's name (`_load_pack_hook_wiring_safely`) makes the scoping explicit. A future broadening would have to either rename the helper or wire it into another rail — both visible in diff.
- **The `<reason-summary>` order is a free-floating contract surface.** Adopters reading the warning text may build expectations on the order. **Mitigation:** the pinned tuple at T4's formatter ("event-vocabulary first, then attach-to-agent") is tested explicitly; future categories must be appended (defensive sort), not interleaved.
- **`enumerate_event_dropped_wirings`'s "unknown agent" case is not enumerated AND the validate swallow MUST also exclude it.** The validate-time `check_kiro_attach_to_agent` refuses on both "missing attach-to-agent" AND "names an unknown agent". The spec splits these: AC1's swallow covers missing-only; AC4b keeps unknown-agent (and explicit empty string `""`) as an exit-1 refusal. **Discrimination is from input data, NOT from refusal-string inspection** (round-2 fix): validate.py's call site re-implements the two-branch check inline against the loaded `(wiring_tomls, agent_basenames)` from T1's safe-load helper, then constructs the refusal text inline byte-for-byte matching `scope_rails.py:333-337`'s composition. The helper at `scope_rails.py:302-338` returns a single composed refusal string that can't tell its caller which branch fired, so validate.py doesn't call it for the swallow path. **Risk:** a future RFC-0005 wording change must update both the helper composition AND the validate.py inline construction. Mitigation: the plan T2 inline comment names the duplication; AC4b's `test_validate_still_refuses_on_unknown_agent_reference` (and the round-3 sibling `test_validate_refuses_on_empty_attach_to_agent_string`) catch text drift. The install-time enumerator deliberately doesn't enumerate unknown-agent references (the install handler's downstream projection rail catches missing target files with a clearer error than "drop"), but DOES enumerate omitted-or-empty attach as a compat drop entry — see T3 step 2b for the empty-string carve-out.
- **Install-time tolerates a malformed hook-wiring TOML; validate refuses it.** AC6c documents the asymmetry. **Mitigation:** install enumerates the parse-fail as a drop entry so the file is visibly named in the warning (not silently absent). The risk that an adopter only runs install (never validate) and ignores the warning is real but small — the warning grammar is loud and the parse-fail reason category is distinct.
- **Perf nod: `enumerate_event_dropped_wirings` walks every hook-wiring TOML at every install.** For packs with no hook-wirings this is a no-op (the directory-exists check at T3's step 2 short-circuits). For packs with many wirings (none in the catalogue today), the cost is O(N · M) where N is wirings × M is events-per-wiring — small constants. No mitigation needed at this scale; revisit if a future pack ships hundreds of wirings.

## Changelog

- 2026-05-26 — Initial Drafting. Spec follows from the post-PR-#156 adopter direction ("we already have dropped primitives support, extend it to drop and inform the user that session-start doesn't carry over"). Designed as a new spec rather than an amendment because PR #156's `dropped-primitives-coverage` spec is **frozen** (Shipped status; bodies immutable per `docs/CONVENTIONS.md:80`). Five user-confirmed product decisions baked into the spec: (A) extend the single formatter to a three-clause grammar (vs sibling formatter); validate-time text is `info:` to stdout (vs silent or stderr); `<reason-summary>` order is vocabulary-then-attach-to-agent; drop entries are `(file, reason-category)` tuples never concatenated; spec lifecycle is single-PR Draft → Implementing → Shipped.
- 2026-05-26 — **Round-1 adversarial review.** 5 Blockers / 7 Concerns / 6 Nits. All Blockers addressed: (1) AC2 wording extended to enumerate four pinned cases; (2) AC6b adds the shared `_drop_warning.py` module so validate and install consume the same enumerator and formatter — fixes the under-specified "single source of truth" claim; (3) AC8 byte-pin replaced with explicit-quoted-string assertion in a new test; (4) AC14 grep command uses a whitelist (`docs/guides/`, `docs/architecture/`, `docs/product/`) sidestepping the spec/RFC self-match; (5) AC3b added for agent-symlink rail; AC4b added for unknown-agent rail. Material Concerns addressed: AC6c documents the install-vs-validate parse-fail asymmetry; AC4b carves out unknown-agent references as a kept-refusal; the validate-side formatter is the same shared helper with a `mode` parameter (single source of truth restored); T6's dual-scope test dropped (out of AC scope; T5 covers dedup semantics). Risks section gained two new bullets (unknown-agent + install-vs-validate parse-fail asymmetry + perf nod).
- 2026-05-26 — **Declined patterns** (made explicit per Concern 12):
  - **Tempted: text-match the swallow scope by parsing the refusal string in validate.py.** Declined for symlink + parse-fail rails (covered by the T1 safe-load helper extraction — discrimination by helper, not by string-match). **Accepted for the unknown-agent vs missing-attach-to-agent split** because the underlying helper composes both into one refusal string and restructuring its return shape is out-of-scope helper-signature surgery. AC4b's regression test catches drift.
  - **Tempted: add a `--strict-hook-events` flag for adopters who want refusal instead of warning.** Declined — Never-do covers it; the warning-not-refusal stance is the shipped policy from `dropped-primitives-coverage` and this spec extends, not reverses, that policy.
  - **Tempted: generalise `enumerate_event_dropped_wirings` to all primitive types.** Declined — Boundaries `Ask first` covers it; other primitives (skill, agent, command, hook-body, kiro-ide-hook) have their own compatibility paths that aren't shaped like `agent-event-vocabulary`. The three-times rule applies; a second consumer surfacing during EXECUTE earns a follow-on spec.
  - **Tempted: emit the validate-time info to stderr for visibility-by-default.** Declined — user direction picked stdout; stdout matches Unix convention for informational messages and avoids polluting CI logs that filter stderr-as-errors.
  - **Tempted: dual-scope test in T6.** Declined — spec AC10 names only `--scope repo`; T5's short-circuit test covers the dedup semantic the dual-scope case would otherwise need.
