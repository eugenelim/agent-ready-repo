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

**D — scope, resolved by not fighting it.** The route is user-scope
distribution: a plugin's code lives in the adopter's global cache, and
`project`/`local` record an enablement pointer in a repo file rather than placing
anything in the repo. So the fix is a *filter*, not a guard — publish only packs
whose `allowed-scopes` admits `user`, derived from the declaration. No pack
scopes change; no runtime guard is built; `templates/install-marker.py` is not
touched (three drift gates pin its bytes, and #890 already made its own rail
correct).

That filter also disposes of the prompt-injection path earlier rounds chased:
`packs/core` is the only pack shipping hooks and it is repo-only, so it leaves
the route entirely. No delimiting of `session-start.py`'s knowledge output is
needed on this route, and core's hook body is not touched.

`catalogue-curation`'s operator-only exclusion is retained alongside the derived
predicate rather than folded into it — different rationale, and folding would
re-publish it if its scopes were ever widened.

**D2 — the docs follow the filter.** Two Astro pages build a
`claude plugin install` command for every pack with `scope` present and unread
(`web/src/pages/packs/[pack].astro:24`, `web/src/pages/catalogue/index.astro:54`),
and five prose docs advertise the route without a scope caveat — including
`README.md:32-35`, which names `core` specifically. The route table in
`guides/_shared/explanation/install-routes.md` is where the rule gets stated
once; the rest reference it.

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

### T0 — Scope predicate + the seven exclusions
**Depends on:** none · **Mode:** TDD

**Tests:** the predicate over a matrix of `allowed-scopes` values; an integration
assertion that the seven named packs reach neither `dist/claude-plugins/` nor
either `marketplace.json`, and that a user-capable pack still does.

**Approach:** one predicate, read from `[pack.install] allowed-scopes`, applied
at the recipe (AC3) and at publish (AC1). `publish_claude_plugins.py`'s
`EXCLUDE` keeps `catalogue-curation` for its operator-only reason and gains the
derived filter beside it. This task alone is shippable and is the deliverable.

### T1 — Docs and site
**Depends on:** T0 · **Mode:** Goal-based check + site build

**Done when:** a grep for `plugin install` / `plugin marketplace add` across
`README.md`, `docs-site/`, `guides/`, and `web/` returns no instance offering the
route for a repo-only pack; and the built site shows no plugin-install command on
a repo-only pack's page while still showing one for a user-capable pack.

**Approach:** re-derive the file list by grep rather than trusting the spec's.
Gate both Astro pages on the `scope` field each already carries. State the rule
once in `install-routes.md`'s route table and reference it from the others.
Changelog entries per AC6.

### T2 — Contract: route-scoped hook targets
**Depends on:** none · **Mode:** Goal-based check

**Done when:** a parse of `contracts/adapter.toml` asserts the `hook-body`
entry's `plugin-target-path == "hooks/"` **and** the `hook-wiring` entry's
`plugin-mode == "dropped"`; `diff` against `_data/adapter.toml` is empty;
`validate` exits 0; the six contract-version pins are green again.

The value assertions are the point — the projection-array item schema has no
`additionalProperties: false`, so `validate` exits 0 with either key misspelled
or omitted.

**Approach:** add both keys, bump `[contract].version`, record it in the
version-history block, extend `adapter.schema.json`, mirror both files. Update
`overview.md`, `pack-layout.md`, `agentbundle.md`, `DESIGN.md` (×2), and the
version prose in the six pinning tests plus `test_contract_scope.py:99`'s
comment.

### T3 — Derived schema
**Depends on:** none · **Mode:** TDD

**Tests:** accepts a compiled two-event block with and without `matcher`; rejects
`type: "http"`, an unknown key in a hook object, an unknown key in an entry.

**Approach:** replace the single `SessionStart` property with
`additionalProperties: <entry-array schema>`; **add `matcher`** to the entry
object (absent today, and `additionalProperties: false` would reject it). Mirror.

### T4 — Hook-wiring rules (neutral module)
**Depends on:** none · **Mode:** TDD

**Approach:** `build/hook_wiring_rules.py` — neutral validation shared by the
compiler and the pack lint so the two cannot disagree. Exposes `KNOWN_EVENTS`,
`is_claude_shaped(entry)` (the per-adapter skip of AC14), and
`validate_wiring_entry(entry, *, pack_name, wiring_file) -> None`. Neutral module
rather than importing `projections/` from `lint_packs.py`, which today imports
only `agentbundle.pack_inventory` / `agentbundle.safety`.

**Tests:** each raise — unknown event, non-`command` type, non-string command,
timeout out of range, matcher failing the AC15 grammar, basename failing AC12 —
and each *skip*: Kiro lowercase events, flat user-scope shape. Every message
asserts pack + file + command.

### T5 — The hook compiler
**Depends on:** T4 · **Mode:** TDD

**Approach:** `build/projections/plugin_hooks.py` exposing
`compile_plugin_hooks(pack_path, *, repo_hook_prefix, plugin_hook_prefix,
hook_source_path, wiring_source_path, pack_name) -> dict`. **All four paths are
parameters read off the contract by the caller** — a module constant for any is a
second copy that drifts the day the contract changes. This departs from the
gemini/cursor/copilot convention of a private prefix constant, because those
adapters hardcode a destination this route reads from the contract.

Structure and error wording mirror `gemini.py`'s `_translate_hook_entry`. The
**mechanism** diverges per AC10: anchored, quote-aware positional splice.

**Tests:** the AC10 case list — multi-occurrence, leading `./`, `--flag=path`,
`sh -c "…"` nesting (emitted bare), an embedded `vendor/tools/hooks/…` that must
raise, trailing args, a command with no hook path; the `sh -c` execution
assertion with a space-and-`$` root; AC11 both predicates per fragment; ordering;
empty block when no `hook-wiring/`.

### T6 — Wire into the derivation
**Depends on:** T2, T3, T5 · **Mode:** TDD

**Approach:** extend `_resolve_contract_for_route` to require both new keys and
**swap `mode` ← `plugin-mode` alongside the existing `target-path` swap** —
requiring is not applying; today it swaps only `target-path`, and
`_iter_primitives` skips a primitive only when its `mode` is `"dropped"`. Replace
the `derived["hooks"]` assignment with marker-first-then-compiled. Re-pin the
artifact-layout anchors **in this task**, since this is what breaks them.

### T7 — Pack-source gate
**Depends on:** T4 · **Mode:** TDD

**Approach:** `build/lint_packs.py` calls `hook_wiring_rules.validate_wiring_entry`,
wrapping each call and converting the exception to a finding string so one bad
pack does not abort the sweep. Test that two violating packs both report.

### T8 — Other-route regression
**Depends on:** T6 · **Mode:** TDD

**Approach:** assert per projection that a non-plugins build still writes
`.claude/settings.local.json` and `tools/hooks/`; assert each of the six
`render_pack` consumers for its expected new output, `init_state.py` included.

### T9 — Real client, erratum, snapshot
**Depends on:** T1, T7, T8 · **Mode:** Visual / manual QA

**Done when:** `claude plugin validate` passes on a built user-capable pack;
`claude plugin details` reports the exact hook set; an authored hook is observed
firing; the execution model is recorded; a dropped pack is confirmed absent from
the marketplace; transcripts pasted below.

Then: erratum on `docs/specs/wire-session-start-hook/spec.md` (frozen — body not
edited); land the hook-event documentation snapshot under the spec dir; fix the
two stale-prose sites (`commands/upgrade.py:1672`,
`test_tier_invariants.py:315-317`).

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
- **2026-08-07** — round 3. The scope guard is **removed**, not repaired. Both
  reviewers independently showed AC8's trust invariant was unsatisfiable, and
  the empirical check settled it: no `$HOME`-side artifact records per-project
  plugin enablement, so a legitimate `--scope project` install and a hostile
  repo-committed `.claude/settings.json` are byte-identical inputs. The route is
  user-scope distribution by design; `packs/core` widens `allowed-scopes`, and
  the safety property moves to AC22 (untrusted-content delimiting), which is
  stronger — it holds on the direct route too, where the same exposure exists
  today unguarded. Also: AC20's and AC21's premises were wrong and are corrected
  (`catalogue verify` already validates manifests pre-publish; `claude_code.py`
  already confinement-checks before `_project_direct_file`); AC17 drops the
  plugin `description` per #888 and gains the three-file pack version bump; the
  fixture table is regenerated by glob rather than by grep.
- **2026-08-07** — round 3 → 4. Reframed on the owner's rule: **the route
  publishes only packs whose `allowed-scopes` admits `user`, and no pack scope
  changes.** Seven packs drop, including `core`. That replaces the whole
  guard/widen line of thinking — both reviewers had shown the runtime guard was
  unsatisfiable, and excluding repo-only packs removes the prompt-injection path
  without touching `packs/core` at all. Docs and site join the spec: two Astro
  pages build a plugin-install command for every pack with `scope` present and
  unread, and five prose docs advertise the route without the precondition,
  `README.md` naming `core` by name. Stated plainly that the hook-compile half
  ships no activation today, since core is the only pack with hooks and it is one
  of the seven.
