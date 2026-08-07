# Plan: Claude-plugin hook parity

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

**A — the seam.** `_resolve_contract_for_route` (`build/main.py`) already makes
the claude-plugins route differ from the direct route without widening every
adapter's signature. Hooks join it: `hook-body` gains a `plugin-target-path`,
`hook-wiring` gains a `plugin-mode` resolving to `dropped`. Both new keys extend
the existing fail-loud check, for the reason that check exists — a missing or
typo'd key must not silently restore the broken layout. Critically the resolver
must **apply** `plugin-mode`, not merely require it: today it swaps only
`target-path`, and `_iter_primitives` skips a primitive only when the entry's
`mode` is `"dropped"`.

**B — the compiler.** `build/projections/plugin_hooks.py`, pure in / pure out,
so the fail-closed ACs are unit-testable without a build. A sibling of
`merge_json.py`, not a parameter on it: that one merges TOML into a JSON file's
managed key and is shared with codex; this compiles TOML into an in-memory block
while rewriting paths and rejecting shapes.

**C — the merge.** `build/main.py` currently *assigns* `derived["hooks"]`. It
becomes marker-entry-first, then the compiled block appended.

**D — the scope guard.** #890 repaired the `enabledPlugins` walk, so the rail
`templates/install-marker.py` applies to the marker now actually resolves. The
guard reuses that resolution but **not** its precedence: per spec AC8 the permit
comes from adopter-controlled state only, and workspace files may narrow but
never grant. The guard ships as its own projected file with its own mirror and
drift gates (AC19) rather than as an edit to the install-marker template, which
three gates pin byte-for-byte and which is projected standalone into the plugin
cache where it cannot import from `agentbundle`.

The APM route needs nothing: #890 records that `_apm_detect_scope` resolves
scope by projected-path containment and never reads `enabledPlugins`, so its
copy of the rail has been enforcing all along.

**E — the schema.** The derived `hooks` block becomes
`{additionalProperties: <entry-array schema>}` — shape only. Event-name
validation lives in the compiler; spec AC7 carries the full rationale and this
plan does not restate it.

Verification anchors on spec AC13 against the real `claude` binary (2.1.223).

## Constraints

- **ADR-0072** governs the derived schema. **RFC-0008** owns the plugin-route
  scope taxonomy; **#890** repaired its enforcement.
- `agentbundle` is stdlib-only. `build/validate.py` supports no `$ref`,
  `propertyNames`, numeric bounds, or length bounds — which is why spec AC7 and
  AC9 are compiler checks.
- `contracts/*` mirrors to `agentbundle/_data/`. `templates/install-marker.py`
  and any sibling projected script are pinned by three `build/self_host.py`
  drift gates.

## Writers of a plugin `hooks` key — complete set

| Site | Role | Disposition |
|---|---|---|
| `build/main.py` synthetic-hooks assignment | assigns the block | **must change** — becomes merge |
| `build/main.py` dist marketplace aggregation | strips `hooks` from entries | unchanged |
| `build/self_host.py` `_aggregate_marketplace` | `entry.pop("hooks")` — **second** marketplace writer | unchanged; reads source manifests |
| `build/self_host.py` source-shape gate | source `plugin.json` carrying `hooks` is drift | unchanged |
| `catalogue_tooling/verify.py` | asserts no `hooks` in a marketplace entry | unchanged |
| `build/main.py` `_APM_INSTALL_MARKER_HOOK_JSON` | writes `hooks` into `dist/apm/.../install-marker.json` | unchanged — APM route, different artifact |
| `adapters/claude_code.py` → `merge_json` | writes `.claude/settings.local.json` | unchanged code; **not reached** once `plugin-mode` resolves to `dropped` |

ADR-0072 records `_aggregate_marketplace` as the writer missed last time, which
is why both its sites are listed rather than assumed.

## Anchor-test sweep

Both test roots swept (`packages/agentbundle/tests/` and
`packages/agentbundle/agentbundle/build/tests/`).

**Artifact-layout pins — red under AC3 / AC4 / AC11:**

| Test | Pins | Disposition |
|---|---|---|
| `build/tests/test_end_to_end_build.py:67-75` | `tools/hooks/baz.{sh,py}` exist; `.claude/settings.local.json` exists; stale "hook wiring is the exception" comment | re-pin to `hooks/`; invert the `.claude/` assertion; delete the comment |
| `tests/unit/test_render_cmd.py:89-99` | `any("tools/hooks/" in k)`; `claude-plugins/core/.claude/settings.local.json`; same stale comment | re-pin both; delete the comment |
| `tests/integration/test_install_session_start_wiring.py:98,124` | file at `claude-plugins/test-core/.claude/settings.local.json`; `command == "python tools/hooks/session-start.py"` | re-pin to manifest + rewritten command |
| `tests/integration/test_install_core_smoke.py:60-69` | same, against real `packs/core` | re-pin |
| `tests/integration/test_build_derivation_claude_plugins.py` | `EXPECTED_COMMAND` + the `hooks` block | extend, not replace |
| `build/tests/test_plugin_manifest_schema.py` | derived-schema accept/reject set | extend |

**Contract-version pins — red under AC16's bump. Six, and they re-pin in the
contract task, not later** (otherwise the tree is red between tasks):
`build/tests/test_contract.py:463`, `test_shared_prefix_contract.py:35`,
`test_adapter_gemini.py:157`, `test_adapter_cursor.py:60`,
`test_adapter_kiro_ide.py:182`, `tests/unit/test_contract_v0_3_schema.py:85`.
**Not a pin:** `build/tests/test_contract_scope.py` asserts `version >= (0, 8)`
as a tuple and stays green; only its prose comment at `:99` needs updating.

**Fixture wiring the fail-closed compiler will now reject.** Every
`.apm/hook-wiring/*.toml` under a fixture tree that reaches the claude-plugins
recipe — roughly twenty test modules call `--emit-install-routes` / `render_pack`:

| Fixture | Problem under AC6/AC7 | Disposition |
|---|---|---|
| `build/tests/fixtures/packs/core/.apm/hook-wiring/baz.toml` | `[hooks] baz = "…"` — unknown event, value is a string not an entry array | rewrite to the real nested shape, on a non-`SessionStart` event |
| `tests/fixtures/install/catalogue/packs/alpha/.apm/hook-wiring/run.toml` | same shape | rewrite |
| `tests/fixtures/packs/cc-user-hooks/.apm/hook-wiring/on-prompt.toml` | entry has a top-level `command`, no nested `hooks` array, no `type` | rewrite |
| `tests/fixtures/upgrade/catalogue_v{1,2,3}/packs/core/.apm/hook-wiring/pre-commit.toml` | same shape; reached via `test_tier_invariants.py:311` | rewrite all three |

Enumerate the full set with a glob at task start rather than trusting this
table — it was built by grep and the suite grows.

**Must stay green:** `build/tests/test_adapter_claude_code.py:126` and
`test_self_host_check.py:332-362` assert the *direct* route's payload; both
build their own pack, so fixture rewrites do not reach them.

**Stale prose:** `commands/upgrade.py:1672`;
`tests/integration/test_tier_invariants.py:315-317`.

## Tasks

### T0 — Fixtures + red integration test
**Depends on:** none · **Mode:** TDD

**Tests:** `test_build_derivation_claude_plugins.py::test_authored_wiring_reaches_manifest`
— red here.

**Approach:** glob every fixture `.apm/hook-wiring/*.toml`, rewrite each to the
real nested shape per the table above, wiring to a **non-`SessionStart`** event
so AC1 and AC2 stay distinguishable. Leave unit tests that build their own pack
alone.

### T1 — Contract + version re-pins
**Depends on:** none · **Mode:** Goal-based check

**Done when:** a parse of `contracts/adapter.toml` asserts the `hook-body`
entry's `plugin-target-path == "hooks/"` **and** the `hook-wiring` entry's
`plugin-mode == "dropped"`; `diff` against `_data/adapter.toml` is empty;
`validate` exits 0; and the six contract-version pins are green again.

The value assertions are the point — the projection-array item schema has no
`additionalProperties: false`, so `validate` exits 0 with either key misspelled
or omitted.

**Approach:** add both keys, bump `[contract].version`, record it in the
version-history block, extend `adapter.schema.json` (`plugin-mode` under the
`mode` enum), mirror both files. Update `overview.md`, `pack-layout.md`,
`agentbundle.md`, `DESIGN.md` (×2), and `test_contract_scope.py:99`'s comment.

### T2 — Derived schema
**Depends on:** none · **Mode:** TDD

**Tests:** accepts a compiled two-event block with and without `matcher`;
rejects `type: "http"`, an unknown key in a hook object, an unknown key in an
entry.

**Approach:** replace the single `SessionStart` property with
`additionalProperties: <entry-array schema>`; **add `matcher`** to the entry
object (absent today, and `additionalProperties: false` would reject it);
retain `additionalProperties: false` inside entry and hook objects. Mirror.

### T3 — Hook-wiring rules (neutral module)
**Depends on:** none · **Mode:** TDD

**Approach:** `build/hook_wiring_rules.py` — neutral validation shared by the
compiler and the pack lint so the two gates cannot disagree. Exposes
`KNOWN_EVENTS` (frozenset) and
`validate_wiring_entry(entry, *, pack_name, wiring_file) -> None`. Neutral
module rather than importing `projections/` from `lint_packs.py`, which today
imports only `agentbundle.pack_inventory` / `agentbundle.safety`.

**Tests:** each raise — unknown event, non-`command` type, non-string command,
timeout out of range, entry/hook count caps, matcher shape. Every message
asserts pack + file + command.

### T4 — The scope guard
**Depends on:** none · **Mode:** TDD

**Tests:** the trust invariant, driven through real settings files —
a hostile repo-committed `.claude/settings.json` granting the pack must **not**
cause a hook to run; unset `CLAUDE_PROJECT_DIR`, unset `HOME`, malformed JSON,
and empty `allowed-scopes` each resolve `undetermined` → refuse; a legitimate
`project`-scope install of a repo-only pack runs. Object-form `enabledPlugins`
throughout — the array form is what hid #890's bug.

**Approach:** a standalone projected script (AC19), self-contained, stdlib-only,
no `agentbundle` import. Reuses #890's repaired reading of `enabledPlugins` but
resolves the permit per AC8's trust invariant, returning three values. Register
its projected path and `_data/` mirror in all three `build/self_host.py` drift
gates. **Do not edit `templates/install-marker.py`** — its behaviour is correct
after #890 and three gates pin its bytes.

### T5 — Guard emission in the compiler
**Depends on:** T3, T4 · **Mode:** TDD

**Approach:** `build/projections/plugin_hooks.py` exposing
`compile_plugin_hooks(pack_path, *, repo_hook_prefix, plugin_hook_prefix,
hook_source_path, wiring_source_path, guard_path, pack_name) -> dict`. **All
five paths are parameters read off the contract by the caller** — `tools/hooks/`
and `hooks/` are `target-path`/`plugin-target-path`, and `.apm/hooks/` /
`.apm/hook-wiring/` are `[primitive.*] source-path`. A module-level constant for
any of them would be a second copy that drifts the day the contract changes.
This departs from the gemini/cursor/copilot sibling convention of a private
prefix constant, because those adapters hardcode a destination this route reads
from the contract.

Structure and error wording mirror `gemini.py`'s `_translate_hook_entry` so the
four read alike. The **mechanism** diverges per AC4: positional regex splice
with a double-quoted replacement.

The compiler emits the guard invocation as part of each compiled command, so
AC4's expected string for `packs/core` is the guarded form — stated in AC4, and
the same string AC13 asserts against the real client.

**Tests:** the AC4 case list (multi-occurrence, leading `./`, `--flag=path`,
`sh -c "…"` nesting, trailing args, a command with no hook path); the `sh -c`
execution assertion with a space-and-`$` root; AC5 both predicates; ordering;
empty block when no `hook-wiring/`.

### T6 — Wire into the derivation
**Depends on:** T0, T1, T2, T5 · **Mode:** TDD (T0 goes green)

**Approach:** extend `_resolve_contract_for_route` to require both new keys and
**swap `mode` ← `plugin-mode` alongside the existing `target-path` swap** —
requiring is not applying. Route `_project_direct_file`'s `target_prefix`
through `_resolve_target` (AC21). Replace the `derived["hooks"]` assignment with
marker-first-then-compiled. Re-pin the artifact-layout anchors.

### T7 — Pack-source gate
**Depends on:** T3 · **Mode:** TDD

**Approach:** `build/lint_packs.py` calls `hook_wiring_rules.validate_wiring_entry`.
The compiler's validators are the single source; the lint restates nothing.

### T8 — Publish-time validation
**Depends on:** T6 · **Mode:** TDD

**Approach:** `tools/catalogue/publish_claude_plugins.py` re-validates each
`plugin.json` against the derived schema and `KNOWN_EVENTS` before pushing
(AC20).

### T9 — Other-route regression
**Depends on:** T6 · **Mode:** TDD

**Approach:** assert per projection that a non-plugins build still writes
`.claude/settings.local.json` and `tools/hooks/`; assert each of the five
`render_pack` consumers for its expected new output.

### T10 — Real client, docs, erratum, changelog
**Depends on:** T7, T8, T9 · **Mode:** Visual / manual QA

**Done when:** `claude plugin validate` passes; `claude plugin details` reports
the exact hook set; an authored hook is observed firing at `--scope project` and
observed refusing at `--scope user`; the execution model for AC12 is recorded;
transcripts pasted below.

Then: erratum on `docs/specs/wire-session-start-hook/spec.md` (frozen — body not
edited); `packs/core/README.md` + plugin `description` per AC17, including the
default-scope refusal; `[Unreleased]` entries in
`packages/agentbundle/CHANGELOG.md` and `docs/product/changelog.md`; fix the two
stale-prose sites.

## Risks

- **Event-set drift.** Fail-closed by choice; spec AC7 records the widening
  procedure. Residual: nothing in CI detects an upstream addition, and AC13 is a
  one-shot manual run. Accepted explicitly — a recurring real-client check is
  the honest fix and is ADR-0072's recorded follow-on.
- **Branch integrity is only partly satisfied.** Force-push and deletion are now
  denied on `claude-plugins-dist`, but ordinary pushes are unrestricted and
  `enforce_admins: false`, so ADR-0072's named threat — anyone with repo write,
  or any workflow holding `contents: write` — is untouched. AC20 is the
  compensating control this spec adds; signature requirements or a rebuild-and-
  compare check remain open.
- **`python` vs `python3`.** `packs/core` authors bare `python`, absent on stock
  macOS. Pre-existing on every route; out of scope (spec § Ask first).

## Verification log

_(AC13 transcripts land here during T10.)_

## Changelog

- **2026-08-07** — initial plan.
- **2026-08-07** — revised after round 1 (adversarial + security).
- **2026-08-07** — revised after round 2. Substantive: (1) AC4's mechanism
  replaced a second time — `shlex.quote` emits single quotes, inside which `sh`
  never expands `${CLAUDE_PLUGIN_ROOT}`, and split-then-rejoin destroys `&&`;
  the positional-splice replacement was verified by execution before being
  written down. (2) AC8 rebuilt on a trust invariant after review showed the
  inherited `local → project → user` precedence lets a hostile repo *grant*
  execution. (3) The guard became its own governed artifact (AC19) rather than
  an edit to the three-gate-pinned install-marker template. (4) T3 split out as
  a neutral rules module. (5) Fixture sweep added — six more wiring files the
  fail-closed compiler rejects. (6) Contract-version pins corrected to six and
  moved into T1. (7) New AC20 (publish-time validation) and AC21 (`_resolve_target`
  confinement). Unblocked by **#890**, which repaired the `enabledPlugins` walk
  this spec's scope rail depends on.
