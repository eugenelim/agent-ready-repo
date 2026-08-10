# Plan: Claude-plugin route — hook parity

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

> **Cross-reference convention.** This plan cites acceptance criteria by
> **name**, not number. Three review rounds of AC renumbering left every numeric
> reference here stale; names survive insertion.

## Approach

> **The filter, the docs, and the sibling spec's publish filter are
> [`../claude-plugin-route-scope/plan.md`](../claude-plugin-route-scope/plan.md).**
> Not restated here, and not duplicated in this plan's tasks or sweep — the
> round-1 split left both and they drifted within a day.

**A — the seam.** `_resolve_contract_for_route` already makes the claude-plugins
route differ from the direct route. Hooks join it: `hook-body` gains a
`plugin-target-path`, `hook-wiring` gains a `plugin-mode` resolving to
`dropped`. The resolver must **apply** `plugin-mode`, not merely require it —
today it swaps only `target-path`, and `_iter_primitives` skips a primitive only
when its `mode` is `"dropped"`.

**B — the marker.** Open question, not a decision: gating the synthetic
install-marker entry on reader-existence is undetectable without executing pack
code and tests the wrong predicate. See the spec's split note.

**C — the compiler.** `build/projections/plugin_hooks.py`, pure in / pure out,
so the fail-closed criteria are unit-testable without a build. A sibling of
`merge_json.py`, not a parameter on it: that one merges TOML into a JSON file's
managed key and is shared with codex; this compiles TOML into an in-memory block
while rewriting paths and rejecting shapes.


**E — the schema.** The derived `hooks` block becomes
`{additionalProperties: <entry-array schema>}` — shape only. Event-name
validation lives in the compiler; the spec carries the full rationale.

Verification anchors on the real-client criterion against `claude` 2.1.223.

## Constraints

- **ADR-0002** owns the scope model; **ADR-0072** the derived schema; **RFC-0008**
  the plugin-route taxonomy, with **#890** having repaired its enforcement.
- **Rail B** (`build/scope_rails.py:check_hooks`) refuses a pack declaring
  `"user"` while carrying `.apm/hooks/` or `.apm/hook-wiring/` unless it sets
  `[pack.install] user-scope-hooks = true`. Any fixture built for the hook
  criteria must declare both.
- `agentbundle` is stdlib-only. `build/validate.py` supports no `$ref`,
  `propertyNames`, numeric bounds, or length bounds.
- `contracts/*` mirrors to `agentbundle/_data/`.

## Writers of a plugin `hooks` key

| Site | Role | Disposition |
|---|---|---|
| `build/main.py` synthetic-hooks assignment | assigns the block | **must change** — merge, and gate on reader-existence |
| `build/self_host.py` source-shape gate | source `plugin.json` carrying `hooks` is drift | unchanged |
| `catalogue_tooling/verify.py` | asserts no `hooks` in a marketplace entry | unchanged |
| `build/main.py` `_APM_INSTALL_MARKER_HOOK_JSON` | `hooks` into `dist/apm/.../install-marker.json` | unchanged — APM route, different artifact |
| `adapters/claude_code.py` → `merge_json` | `.claude/settings.local.json` | unchanged code; **not reached** once `plugin-mode` resolves to `dropped` |

The two marketplace writers are the sibling spec's; ADR-0072 records
`_aggregate_marketplace` as the writer missed last time, and it was missed again
in this plan's earlier draft — which is why membership now lives in exactly one
document.

## Anchor-test sweep

Re-derived by glob at task start, not trusted from this table.

Radius 1 (the scope filter) is the sibling plan's. What follows is this
spec's own.

**Radius 2 — the hook layout.** Red under the body-relocation and
no-`.claude/` criteria: `tests/build_pipeline/test_end_to_end_build.py:67-75` (also carries
the stale "hook wiring is the exception" comment), `tests/unit/test_render_cmd.py:89-99`
(same comment), `tests/integration/test_install_session_start_wiring.py:98,124`,
`tests/integration/test_install_core_smoke.py:60-69`,
`tests/integration/test_build_derivation_claude_plugins.py`,
`tests/build_pipeline/test_plugin_manifest_schema.py`.

**Contract-version pins — six literal `assertEqual`s**, re-pinned in the contract
task: `tests/build_pipeline/test_contract.py:463`, `test_shared_prefix_contract.py:35`,
`test_adapter_gemini.py:157`, `test_adapter_cursor.py:60`,
`test_adapter_kiro_ide.py:182`, `tests/unit/test_contract_v0_3_schema.py:85`.
**Not a pin:** `test_contract_scope.py` compares a tuple and stays green; its
prose comment needs updating, as do version strings in the six files' docstrings.

**Fixtures.** `tests/build_pipeline/fixtures/packs/core/.apm/hook-wiring/baz.toml` and
`tests/fixtures/install/catalogue/packs/alpha/.apm/hook-wiring/run.toml` carry a
toy `[hooks] name = "path"` shape that is not valid Claude wiring; both rewrite.
`tests/fixtures/upgrade/catalogue_v{1,2,3}/…/pre-commit.toml` already carry the
correct nested shape and need **no** change. The five `kiro-*` fixtures and
`tests/fixtures/packs/cc-user-hooks/…/on-prompt.toml` are other adapters'
contract-supported shapes that the compiler **skips** — they must not be
rewritten, and `cc-user-hooks` is pinned by `test_cc_user_hooks_fixture.py` and
`test_user_merge_json.py`. Fixture *scope* declarations are the sibling spec's
task — and note its finding that the resolver gates on
`[pack.adapter-contract].version`, not `[pack.install]`, so declaring
`allowed-scopes` alone does not make a fixture publishable.

**Stale prose:** `commands/upgrade.py:1672`;
`tests/integration/test_tier_invariants.py:315-317`.
`tests/unit/test_manual_qa_matrix_shape.py:37-44` while the scenario becomes
impossible.

## Tasks

> **Moved.** The scope predicate and the docs/site work are
> `../claude-plugin-route-scope/plan.md` T0-T3. This plan starts at the
> contract change and assumes that spec has landed.

### T2 — Contract: route-scoped hook targets
**Depends on:** none · **Mode:** Goal-based check

**Done when:** a parse of `contracts/adapter.toml` asserts the `hook-body`
entry's `plugin-target-path == "hooks/"` and the `hook-wiring` entry's
`plugin-mode == "dropped"`; `diff` against `_data/adapter.toml` empty; `validate`
exits 0; the six version pins green.

The value assertions are the point — the projection-array item schema has no
`additionalProperties: false`, so `validate` exits 0 with either key misspelled.

**Approach:** add both keys, bump `[contract].version`, extend
`adapter.schema.json`, mirror. Update every living doc stating the version,
**re-derived by grep** rather than from a list — `overview.md`, `pack-layout.md`,
`agentbundle.md`, `DESIGN.md`, and `docs/architecture/binder-publishing/*` are
known, and the grep is what makes the set complete.

### T3 — Derived schema
**Depends on:** none · **Mode:** TDD

**Tests:** `stub: true` — extends `tests/build_pipeline/test_plugin_manifest_schema.py`.
Accepts a compiled two-event block with and without `matcher`; rejects
`type: "http"`, unknown keys in a hook object and in an entry.

**Approach:** replace the single `SessionStart` property with
`additionalProperties: <entry-array schema>`; **add `matcher`** to the entry
object (absent today, and `additionalProperties: false` would reject it). Mirror.

### T4 — Hook-wiring rules (neutral module)
**Depends on:** none · **Mode:** TDD

**Tests:** `stub: true` — `packages/agentbundle/tests/build_pipeline/test_hook_wiring_rules.py`.
Each raise: unknown event, non-`command` type, non-string command, timeout out of
range, matcher failing the grammar, basename failing the allowlist, command
carrying a shell metacharacter. Each **skip**: Kiro lowercase events, flat
user-scope shape. Every message asserts pack + file + command.

**Approach:** `build/hook_wiring_rules.py` — neutral, so `lint_packs.py` need not
import `projections/`. Exposes `KNOWN_EVENTS`, `is_claude_shaped(entry)`,
`validate_wiring_entry(...)`.

### T5 — The hook compiler
**Depends on:** T4 · **Mode:** TDD

**Tests:** `stub: true` — `packages/agentbundle/tests/build_pipeline/test_plugin_hooks.py`.
Multi-occurrence, leading `./`, `--flag=path`, `sh -c "…"` nesting (emitted bare),
single-quoted region (raises), embedded `vendor/tools/hooks/…` (raises), trailing
args, no-hook-path command; the `sh -c` execution assertion with a space-and-`$`
root asserting observed `argv`; per-fragment fail-closed both predicates;
ordering; empty block when no `hook-wiring/`.

**Approach:** `compile_plugin_hooks(pack_path, *, repo_hook_prefix,
plugin_hook_prefix, hook_source_path, wiring_source_path, pack_name) -> dict`.
All four paths are parameters read off the contract by the caller — a module
constant for any is a second copy that drifts. This departs from the
gemini/cursor/copilot private-prefix convention because those adapters hardcode
a destination this route reads from the contract. Structure and error wording
mirror `gemini.py`'s `_translate_hook_entry`; the mechanism is the anchored,
quote-aware positional splice.

### T6 — A qualifying fixture pack
**Depends on:** none · **Mode:** Goal-based check

**Done when:** `agentbundle validate` passes on a new fixture pack declaring
`allowed-scopes = ["repo", "user"]` **and** `user-scope-hooks = true`, shipping
nested PascalCase wiring and a hook body.

**Approach:** no existing fixture qualifies — the flat and Kiro shapes are
skipped by the compiler, so they compile to an empty block and cannot carry the
authored-wiring criterion. Rail B is why the consent flag is required.

### T7 — Wire into the derivation
**Depends on:** T2, T3, T5, T6 · **Mode:** TDD (T6's fixture goes green)

**Tests:** `stub: true` — extends `test_build_derivation_claude_plugins.py`.
Manifest hooks merged marker-first; reader-existence gating; no `<pack>/.claude/`;
bodies at `<pack>/hooks/`; wiring-without-manifest raises; warm and cold
(`rm -rf dist/ && make build`) rebuilds byte-identical.

**Approach:** extend `_resolve_contract_for_route` to require both new keys and
**swap `mode` ← `plugin-mode` alongside the existing `target-path` swap** —
requiring is not applying; today it swaps only `target-path`, and
`_iter_primitives` skips a primitive only when its `mode` is `"dropped"`. Replace
the `derived["hooks"]` assignment. Re-pin radius-2 anchors **here**, since this
is what breaks them.

### T8 — Pack-source gate
**Depends on:** T5 · **Mode:** TDD

**Tests:** `stub: true` — extends the lint's tests. Two violating packs both
report rather than the first aborting the sweep; a repo-only pack's wiring is
still dry-run compiled.

**Approach:** `lint_packs.py` calls `validate_wiring_entry` **and** dry-runs
`compile_plugin_hooks` against every pack shipping `.apm/hook-wiring/`,
publishable or not — otherwise `packs/core`'s wiring, the only real wiring in the
tree, is the one wiring the splice and confinement checks never run against.
Each raise converts to a finding string.

### T9 — Other-route regression
**Depends on:** T7 · **Mode:** TDD

**Tests:** `stub: true` — per projection: a non-plugins build still writes
`.claude/settings.local.json` and `tools/hooks/`; each of the six `render_pack`
consumers asserted for expected new output, `init_state.py` included; a
pre-change `state.json` carrying old relpaths behaves as specified under
`upgrade`.

### T10 — Real client, erratum, snapshot
**Depends on:** T8, T9 · **Mode:** Visual / manual QA

**Done when:** `claude plugin validate` passes on the T6 fixture pack built
through a local marketplace; `claude plugin details` reports the exact hook set;
an authored hook is observed firing; the execution model is recorded; a dropped
pack is confirmed absent; an install-then-delist run records what the client does
to an installed-but-delisted plugin. Transcripts below. **Scope boundary:** the
QA run exercises one user-capable pack and one dropped pack; the other 13 are
covered by the integration assertions, not by hand.

Then: erratum on `docs/specs/wire-session-start-hook/spec.md` and the other
frozen specs carrying the dead premise; land the hook-event documentation snapshot under the spec
dir; fix the stale-prose sites.

## Risks

- **Event-set drift.** Fail-closed by choice; the spec records the widening
  procedure. Nothing in CI detects an upstream addition and the real-client run
  is one-shot. Accepted explicitly.
- **No compensating control ships for unrestricted pushes to
  `claude-plugins-dist`.** Force-push and deletion are denied; ordinary pushes
  are not restricted, and the marketplace `ref` stays mutable. Both are Deferred
  in the spec; neither is closed here, and the exposure grows once published
  packs can carry executing hooks.
- **Marker/manifest coupling.** Gating the marker on reader-existence makes a
  pack's manifest depend on the published set's composition. Deterministic, and
  the idempotency assertion covers it, but adding a reader pack rewrites the
  others' manifests.

## Verification log

_(Real-client transcripts land here during T10.)_

## Changelog

- **2026-08-07** — initial plan; revised after rounds 1 and 2.
- **2026-08-07** — round 3. The command-rewrite mechanism was replaced a second
  time after `shlex.quote` was shown to emit single quotes (no
  `${CLAUDE_PLUGIN_ROOT}` expansion) and split-then-rejoin to destroy `&&`.
- **2026-08-07** — round 4 reframe on the owner's rule: the route publishes only
  packs whose `allowed-scopes` admits `user`, and **no pack scope changes**.
  Seven packs drop, including `core`. The runtime guard is deleted — both
  reviewers showed its trust invariant unsatisfiable, and the filter removes the
  prompt-injection path without touching `packs/core`. Docs and site joined the
  spec.
- **2026-08-07** — round 4 fold. `_aggregate_marketplace` added to the writers
  table as **must change** (missed here after quoting the ADR that names it as
  last time's miss). Rail B's `user-scope-hooks` consent flag discovered and made
  part of the qualifying shape, with a new fixture task since no existing fixture
  qualifies. Site gating moved off `scope` (which is `default-scope`).
  Command-string metacharacter validation added — this spec is what makes
  authored commands execute. Two blast radii separated, so T0's "shippable
  alone" claim is retired. Marker emission gated on reader-existence. Plan
  switched to citing criteria **by name**, since three rounds of renumbering left
  every numeric reference stale.
