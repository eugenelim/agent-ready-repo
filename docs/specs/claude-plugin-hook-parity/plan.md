# Plan: Claude-plugin hook parity

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Five moving parts, sequenced so no gate is red between tasks.

**A — the seam.** `_resolve_contract_for_route` (`build/main.py:510`) already
makes the claude-plugins route differ from the direct route without widening
every adapter's signature. Hooks join it: `hook-body` gains a
`plugin-target-path`, and `hook-wiring` gains a `plugin-mode` that resolves to
`dropped` so the adapter stops writing `.claude/settings.local.json` into the
plugin. Both new keys extend the existing fail-loud check, for the reason that
check already exists — a missing or typo'd key must not silently restore the
broken layout.

**B — the compiler.** A new pure module,
`build/projections/plugin_hooks.py`, reads `.apm/hook-wiring/*.toml` and
returns the manifest `hooks` block. Pure in / pure out, which is what makes the
fail-closed ACs unit-testable without a build. It is a *sibling* of
`merge_json.py`, not a parameter on it: `merge_json` merges TOML into a JSON
file's managed key and is shared with codex; this compiles TOML into an
in-memory block while rewriting paths and rejecting types. Different return
type, different job.

**C — the merge.** `build/main.py:585` currently *assigns* `derived["hooks"]`.
It becomes: install-marker entry first, then the compiled authored block
appended (creating the `SessionStart` list when absent). Marker-first per AC12.

**D — the scope rail.** RFC-0008's `allowed-scopes` enforcement already exists
at `templates/install-marker.py:797,849` but gates only marker writing.
Compiled hooks become sibling entries that Claude runs independently, so they
need the same gate. Rather than duplicate the resolution logic, the rail is
lifted into a small guard the compiled command invokes; the marker writer and
the guard read the same precedence (local → project → user).

**E — the schema.** The derived schema's `hooks` block grows from
one-event-one-shape to `{additionalProperties: <entry-array schema>}` — one
subschema, shape only. Event-name validation moves to the compiler.
`build/validate.py` supports neither `$ref` nor `propertyNames`, so a closed
enum in the schema would mean 31 longhand copies kept byte-identical across two
mirrored files; a compiler-side frozenset is one source of truth and produces a
locating error instead of `$.hooks: additional property 'X' not allowed`.

Verification anchors on AC13 against the real `claude` binary (2.1.223).

## Constraints

- **ADR-0072** governs the derived schema: it mirrors a contract we do not own;
  a local departure must be restrictive.
- **RFC-0008** (Accepted) owns the plugin-route scope taxonomy and the
  `allowed-scopes` rail. This spec extends that rail; it does not invent one.
- `agentbundle` is stdlib-only. `build/validate.py` supports no `$ref`,
  `$defs`, `oneOf`/`anyOf`/`allOf`, `propertyNames`, numeric bounds, or length
  bounds — which is why AC7 and AC9 are compiler checks, not schema checks.
- `contracts/*` has a byte-identical mirror under `agentbundle/_data/`.

## Current-state enumeration (done at PLAN)

Built the fixture packs and the real `packs/core` into scratch dirs:

| Artifact | Today | After |
|---|---|---|
| `<pack>/.claude/settings.local.json` | written, inert | not written (AC11) |
| `<pack>/tools/hooks/<name>.{sh,py}` | written, unreferenced | moves to `<pack>/hooks/` (AC3) |
| `<pack>/.claude-plugin/plugin.json` `hooks` | install-marker only | marker + authored (AC1) |
| core's hooks at plugin user scope | never run (inert) | refused by the scope rail (AC8) |

Writers and readers of a plugin `hooks` key — the complete set:

| Site | Role | Disposition |
|---|---|---|
| `build/main.py:585` | assigns the synthetic block | **must change** — becomes merge |
| `build/main.py:748` | strips `hooks` from dist marketplace entries | unchanged |
| `build/self_host.py:623` | `entry.pop("hooks")` — **second** marketplace writer | unchanged; reads source manifests, which the source schema still forbids `hooks` on |
| `build/self_host.py:1509` | build-check gate: source `plugin.json` carrying `hooks` is drift | unchanged; source manifests stay hooks-free |
| `catalogue_tooling/verify.py:662` | asserts no `hooks` in a marketplace entry | unchanged |
| `adapters/claude_code.py:160` → `merge_json` | writes `.claude/settings.local.json` | unchanged code; **not reached** on the plugin route once `hook-wiring` resolves to `dropped` |

ADR-0072 records `self_host.py:_aggregate_marketplace` as the writer missed last
time, which is why both its sites are listed explicitly rather than assumed.

## Anchor-test sweep (done at PLAN)

Tests pinning exact content of files this change touches. Both agentbundle test
roots swept (`packages/agentbundle/tests/` and
`packages/agentbundle/agentbundle/build/tests/`).

**Artifact-layout pins — go red under AC3 / AC4 / AC11:**

| Test | What it pins | Disposition |
|---|---|---|
| `build/tests/test_end_to_end_build.py:71-75` | `core_plugin/tools/hooks/baz.{sh,py}` exist **and** `.claude/settings.local.json` exists | re-pin to `hooks/`; invert the `.claude/` assertion |
| `tests/unit/test_render_cmd.py:89-99` | `any("tools/hooks/" in k)` and `"claude-plugins/core/.claude/settings.local.json" in k`, under the comment "hook wiring is the exception — it stays under `.claude/`" | re-pin both; delete the stale comment |
| `tests/integration/test_install_session_start_wiring.py:98,124` | the file exists at `claude-plugins/test-core/.claude/settings.local.json`; `command == "python tools/hooks/session-start.py"` | re-pin to the manifest + rewritten command |
| `tests/integration/test_install_core_smoke.py:60-69` | same, against real `packs/core` | re-pin |
| `tests/integration/test_build_derivation_claude_plugins.py` | `EXPECTED_COMMAND` + the `hooks` block | extend, not replace |
| `build/tests/test_plugin_manifest_schema.py` | derived-schema accept/reject set | extend for AC7 |

**Contract-version pins — go red under AC16's bump.** Seven files assert the
literal `"0.17"`: `build/tests/test_contract.py:463`,
`test_shared_prefix_contract.py:35`, `test_contract_scope.py`,
`test_adapter_gemini.py:157`, `test_adapter_cursor.py:60`,
`test_adapter_kiro_ide.py:182`, `tests/unit/test_contract_v0_3_schema.py:85`.
All re-pin to the new version.

**Must stay green (AC14):** `build/tests/test_adapter_claude_code.py:126` and
`test_self_host_check.py:332-362` assert the *direct* route's
`settings.local.json` payload. Both build their own pack, so T0's fixture change
does not reach them.

**Stale prose to fix in the same PR:** `commands/upgrade.py:1672` (docstring
cites `claude-plugins/core/tools/hooks/pre-commit.sh`);
`tests/integration/test_tier_invariants.py:315-317` (comment documents
`tools/hooks/`; the assertion uses a `/hooks/` substring so it stays green and
the comment would rot unnoticed).

## Tasks

### T0 — Realistic fixture + red integration test

**Depends on:** none · **Verification mode:** TDD

**Tests:** `test_build_derivation_claude_plugins.py::test_authored_wiring_reaches_manifest`
— builds the fixture packs, asserts the derived `core` manifest's `hooks`
carries the fixture's authored event *and* the install-marker entry. Red here.

**Approach:** replace the fixture pack's toy `.apm/hook-wiring/baz.toml`
(`baz = "tools/hooks/baz.sh"` — not a valid Claude hook block at all) with the
real nested shape, wiring `baz.sh` to a **non-`SessionStart`** event so AC1 and
AC2 are distinguishable. Leave every unit test that constructs its own pack
alone.

### T1 — Contract: route-scoped hook targets

**Depends on:** none · **Verification mode:** Goal-based check

**Tests:** no stub (goal-based). **Done when:** a Python one-liner parses
`contracts/adapter.toml` and asserts the `hook-body` entry's
`plugin-target-path == "hooks/"` **and** the `hook-wiring` entry's
`plugin-mode == "dropped"`, `diff` against `_data/adapter.toml` is empty, and
`python3 -m agentbundle.build validate` exits 0.

The value assertions are the point: `contracts/adapter.schema.json`'s
projection-array item has no `additionalProperties: false`, so `validate` exits
0 with either key misspelled, omitted, or wrong. A parse-and-diff check alone
would pass while the change it gates is absent.

**Approach:** add both keys; bump `[contract].version`; record it in the
version-history comment block. Add `plugin-target-path` (string) and
`plugin-mode` (same enum as `mode`) to `adapter.schema.json`. Mirror both files
into `_data/`. Update the three living architecture docs that state the version
(`overview.md:101`, `pack-layout.md:129`, `agentbundle.md:147`).

### T2 — Derived schema: shape-only hooks block

**Depends on:** none · **Verification mode:** TDD

**Tests:** `build/tests/test_plugin_manifest_schema.py` — accepts a compiled
two-event block with and without `matcher`; rejects a `type: "http"` hook, an
unknown key inside a hook object, and an unknown key inside an event entry.

**Approach:** replace the single `SessionStart` property with
`additionalProperties: <entry-array schema>`, `additionalProperties: false`
retained inside the entry and hook objects. Mirror to `_data/`.

### T3 — The hook compiler

**Depends on:** none · **Verification mode:** TDD

**Tests:** new `build/tests/test_plugin_hooks.py` —
- authored block compiles verbatim except the rewritten token;
- `tools/hooks/x.py` → `"${CLAUDE_PLUGIN_ROOT}/hooks/x.py"`, quoted;
- a root containing a space stays one `shlex.split` token;
- multiple occurrences in one command (`a && b`) all rewrite, and the result
  round-trips through `shlex.split` with each path as exactly one token;
- a leading `./tools/hooks/x.py` rewrites correctly;
- a token with trailing arguments keeps them;
- sorted wiring-filename order; install-marker first;
- AC5(a) command names a shipped body, no `${CLAUDE_PLUGIN_ROOT}` → raises;
- AC5(b) rewritten token names a body the pack doesn't ship → raises;
- AC6 `type: "http"` → raises; AC7 unknown event → raises;
- AC9 `timeout: 3600` and an over-long `matcher` → raise;
- absent `hook-wiring/` returns an empty block, not `None`.
Every raise asserts pack + file + command in the message.

**Approach:** `build/projections/plugin_hooks.py` exposing
`compile_plugin_hooks(pack_path, *, repo_hook_prefix, plugin_hook_prefix,
pack_name) -> dict`. **Both prefixes are parameters read off the contract entry
by the caller** — no module-level constant. `"tools/hooks/"` and `"hooks/"` are
contract-owned (`adapter.toml` `target-path` and T1's `plugin-target-path`); a
third copy here would drift silently the day T1's value changes. This
deliberately departs from the gemini/cursor/copilot sibling convention of a
private `_LEGACY_HOOK_BODY_PREFIX`, because those adapters hardcode a
destination this route reads from the contract.

Structure and error wording mirror `gemini.py:400-420`
(`_translate_hook_entry`) so the four read alike — preserve `matcher`, raise on
a non-`command` handler. The **mechanism** diverges: `shlex.split` /
rewrite-token / `shlex.quote`, not `str.replace`, per AC4.

Raise `ValueError`; the dispatcher's existing
`RuntimeError(f"pack {pack.name!r}: {exc}")` wrapper (`build/main.py:506`)
prefixes the pack name.

### T4 — The scope rail

**Depends on:** none · **Verification mode:** TDD

**Tests:** exercise the real resolution path at both scopes — a repo-only pack
enabled at plugin `user` scope no-ops with the stderr warning; the same pack
enabled at `project` scope runs. Drive `enabledPlugins` in the three settings
files rather than mocking the resolver, so the test fails if the precedence
regresses.

**Approach:** lift the scope resolution + `allowed-scopes` comparison out of
`templates/install-marker.py:797,849` into a shared helper both the marker
writer and the compiled-hook guard call, preserving the marker writer's
observable behaviour byte-for-byte (its own tests are the regression witness).
The compiled command invokes the guard; on refusal it exits 0 without running
the body, matching the marker's refuse-and-warn-exit-0 contract.

### T5 — Wire the compiler into the derivation

**Depends on:** T0, T1, T2, T3, T4 · **Verification mode:** TDD (T0 goes green)

**Tests:** T0's test plus: no `<pack>/.claude/` in the output; bodies at
`<pack>/hooks/`; a pack with no `hook-wiring/` yields a marker-only manifest;
a pack with `hook-wiring/` and no `plugin.json` raises (AC10); warm and cold
rebuild byte-identical.

**Approach:** extend `_resolve_contract_for_route` to require
`plugin-target-path` on `hook-body` and `plugin-mode` on `hook-wiring`, raising
on either missing. Replace the `derived["hooks"] = {...}` assignment with
marker-first-then-compiled. Re-pin the anchor tests above.

### T6 — Pack-source gate

**Depends on:** T3 · **Verification mode:** TDD

**Tests:** `lint-packs` rejects a pack whose wiring has an unknown event,
a non-`command` type, a non-string `command`, or an out-of-bounds `timeout`.

**Approach:** add the rule to `build/lint_packs.py`, reusing T3's validation
helpers so the two gates cannot disagree.

### T7 — Other-route regression

**Depends on:** T5 · **Verification mode:** TDD

**Tests:** a non-plugins build over the same fixture packs still writes
`.claude/settings.local.json` with the authored payload and `tools/hooks/`
bodies; APM output unchanged. Assert per projection.

**Approach:** assertions only; extend existing direct-route tests rather than
duplicating.

### T8 — Real client, docs, erratum, changelog

**Depends on:** T7 · **Verification mode:** Visual / manual QA

**Tests:** no stub (manual QA). **Done when:** `claude plugin validate` passes
on the built `core` plugin; `claude plugin details` reports the exact expected
hook set; one authored hook is observed firing; all transcripts pasted into the
Verification log below.

**Approach:** build `packs/core` through the claude-plugins recipe into a
scratch dir; run the client in a throwaway `CLAUDE_CONFIG_DIR`. Then:
- erratum on `docs/specs/wire-session-start-hook/spec.md` (frozen — erratum
  only, body not edited);
- `packs/core/README.md` + plugin `description` enumerate the registered hooks
  (AC17);
- `[Unreleased]` entries in **`packages/agentbundle/CHANGELOG.md`** and
  **`docs/product/changelog.md`**, naming the behavioural change;
- fix the two stale-prose sites (`commands/upgrade.py:1672`,
  `test_tier_invariants.py:315-317`).

## Risks

- **Event-set drift.** Claude Code adds events without notice; a pack
  authoring a newer one fails the build. That is the chosen fail-closed mode,
  and AC7 records the widening procedure so the cheapest green is not "add the
  key". The residual is real: nothing in CI detects an upstream addition, and
  AC13 is a one-shot manual run in this PR. Accepted explicitly rather than
  mitigated — a recurring real-client check is the honest fix and is out of
  scope here (ADR-0072 already records it as a known follow-on).
- **`python` vs `python3`.** `packs/core` authors bare `python`, absent on a
  stock macOS. Pre-existing on every route; relocating the path is in scope,
  restyling the interpreter token is not (spec § Ask first).
- **Scope-rail regression surface.** T4 moves logic out of a shipped,
  security-relevant writer. Its existing tests are the witness; if they cannot
  be kept green byte-for-byte, stop and surface rather than adjusting them.

## Verification log

_(AC13 transcripts land here during T8.)_

## Changelog

- **2026-08-07** — initial plan.
- **2026-08-07** — revised after round 1 review (adversarial + security).
  Substantive changes, not re-ordering: (1) command rewriting moves from prefix
  substitution to `shlex` token rewriting — the precedent mechanism cannot emit
  a balanced quote and silently neuters `&&`; (2) new T4 extends RFC-0008's
  `allowed-scopes` rail to compiled hooks, which the marker-only enforcement
  left uncovered; (3) event validation moves from the schema to the compiler
  after confirming `build/validate.py` supports neither `$ref` nor
  `propertyNames`; (4) install-marker ordering flipped to first; (5) anchor
  sweep and writers table completed (three artifact tests, seven version pins,
  two `self_host.py` sites); (6) new T6 adds the pack-source gate.
