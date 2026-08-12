# Plan: Claude-plugin route — hook parity

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->

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

**B — the marker.** Keep the synthetic install-marker entry unconditional and
first. No marker-reader declaration and no published-set composition input.

**C — the compiler.** `build/projections/plugin_hooks.py`, pure in / pure out,
so the fail-closed criteria are unit-testable without a build. A sibling of
`merge_json.py`, not a parameter on it: that one merges TOML into a JSON file's
managed key and is shared with codex; this compiles TOML into an in-memory block
while replacing one validated body path and rejecting every other command
shape. It parses exactly two tokens; it is not a general shell rewriter.

**D — the publication ingress gate.** `build/hook_wiring_rules.py` owns
Claude-shape detection and plugin-publication validation. `commands/validate.py`
applies it to route-qualified source; full-route render consumers reach it
through the plugin compiler; `build/lint_packs.py` calls the same functions
directly for every wiring pack. Direct adapter dispatch does not call it, so
valid direct-route bytes do not change.

**E — the schema.** The derived `hooks` block becomes
`{additionalProperties: <entry-array schema>}` — shape only. Event-name
validation lives in the compiler; the spec carries the full rationale.

**F — disclosure.** `_aggregate_marketplace` appends a deterministic authored
hook inventory to the marketplace description: entry count plus each event,
matcher, effective timeout, interpreter, and plugin-relative body path. The
synthetic marker alone does not change existing descriptions. The writer does
not copy the executable `hooks` key: Claude Code 2.1.226 accepts that shape and
appends it to `plugin.json`, which would register every hook twice. T10 fails
closed unless the real client exposes the full inventory before installation.

**G — publication integrity.** A branch ruleset restricts updates to
`claude-plugins-dist`; its sole bypass is a dedicated, repository-scoped
publisher GitHub App, not the generic Actions app. The publish job uses a
read-only `GITHUB_TOKEN`, non-persisted checkout credentials, and an
environment-protected short-lived app token delivered only to the final publish
step. A canary branch proves ordinary denial and app acceptance before the
ruleset targets the live branch. This closes ADR-0072's precondition without
requiring PRs on a machine-generated branch.

Verification anchors on the real-client criterion against `claude` 2.1.226.

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

## Assumption trio

- **Files expected to change:** the adapter contract and derived plugin schema
  plus their `_data/` mirrors; hook compilation/validation and plugin derivation
  under `packages/agentbundle/agentbundle/`; focused package, tooling, and
  workflow and publisher authentication boundary, workflow-fixture tests;
  living contract-version docs; the frozen-artifact errata discovered by the
  premise sweep; this spec and plan. Repository settings add one dedicated app,
  one protected environment, and one exact-branch ruleset. No pack source is
  expected to change.
- **Evidence for done:** construction tests for the exact invocation and event
  boundaries; direct `validate`/install rejection; fixture build and all six
  `render_pack` consumers; strict Claude Code 2.1.226 validation plus runtime
  hook inventory/fire evidence; warm/cold byte identity; local gates, the three
  named CI-only reproductions, workflow enumeration, and mutation proofs for
  every new gate; AC35's live ruleset/environment snapshot and canary identity
  proof validated against an independent desired-state artifact.
- **Not changing:** any pack's default or allowed scopes; any valid direct,
  self-host, or APM projection bytes; pack-authored hook bodies/interpreters;
  Python dependencies; the dist branch name or marketplace source topology.

**Declined patterns:**

- Add `[pack.install] marker-reader` — one hypothetical caller and a
  marketplace-composition dependency do not justify a new contract flag.
- Build a fourth quote-aware shell rewriter — the exact two-token grammar removes
  the unsupported command forms instead.
- Copy hooks into marketplace entries for disclosure — the client treats that
  as a second executable registration source.
- Change pack scopes to obtain a live fixture — fixture coverage satisfies the
  compiler contract without publishing a repo-only pack.
- Allow the generic GitHub Actions app through the dist ruleset — every
  `GITHUB_TOKEN` represents that app, so the bypass would not identify the
  publisher workflow.
- Put the app credential in a repository secret — any workflow on `main` could
  request it; the protected environment supplies the required approval and
  audit boundary.

## Resolve-vs-surface record

| Question | Disposition | Evidence / recovery |
| --- | --- | --- |
| Do any of the 14 published packs ship hooks now? | Resolved: no; gap, not incident | Literal roster plus filesystem sweep and `lint-plugin-roster.py` |
| What hook shapes does the current client accept? | Resolved at strong structural / medium behavioral confidence | 2.1.226 strict validator matrix plus loader probe; inputs are `spike-*.json` |
| Can marketplace `hooks` be disclosure-only? | Resolved: no | Strictly accepted, but client loader contract appends entry components to `plugin.json`; duplicate registration risk |
| Can ordinary dist pushes be blocked without granting every workflow a bypass? | Resolved: yes, with owner-authorized settings | Exact-branch ruleset; dedicated publisher GitHub App is sole bypass; app credential is released only by a protected environment |
| Can the direct install probe run here? | Surface at final real-artifact gate if still needed | `--dry-run` reached render then failed because no usable temporary directory; use a writable user run |
| Can AC18 observe a successful side effect here? | Surface at final real-artifact gate if still needed | Plugin registered and hooks launched in parallel; command failed on read-only plugin-data creation and the client was not logged in |

## Writers of a plugin `hooks` key

| Site | Role | Disposition |
|---|---|---|
| `build/main.py` synthetic-hooks assignment | assigns the block | **must change** — merge marker-first; marker stays unconditional |
| `build/self_host.py` source-shape gate | source `plugin.json` carrying `hooks` is drift | unchanged |
| `catalogue_tooling/verify.py` | asserts no `hooks` in a marketplace entry | unchanged |
| `build/main.py` `_aggregate_marketplace` | writes marketplace description | **must change** — append complete authored-hook disclosure, never executable hooks |
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

### T1 — Publisher-only control: repository construction
**Depends on:** none · **Mode:** TDD

**Tests:** `stub: true` — extend `tools/test-publish-claude-plugins.py` with a
workflow/construction section that fails unless the workflow has read-only
`GITHUB_TOKEN`, `persist-credentials: false`, the exact protected environment,
a full-commit pin on every external `uses:` action, and the app token scoped
only to the final publisher step. Keep build and publish in one job; if a future
edit introduces an artifact handoff, the test requires producer/consumer digest
verification. Enumerate every workflow and fail if any other
one references the environment/app values, invokes the dist publisher, names
`claude-plugins-dist` as a push target, or otherwise combines write permission
with that branch. Unrelated workflow write permissions are out of scope.
Unit-test the publisher's authentication
environment builder: the token never occurs in printed argv, remote URLs, or
exception text, and absence of the token in CI fails before a remote mutation.

**Approach:** add a small declarative, non-secret control description at
`.github/claude-plugin-publish-control.json`; change the publish workflow and
`tools/catalogue/publish_claude_plugins.py` to AC35's short-lived app-token
boundary. The script passes Git's authorization header through a subprocess
environment mapping that `_run` never prints. The workflow's ordinary token is
read-only and checkout persists no credential. Add the pure-stdlib
`tools/lint-claude-plugin-publish-control.py`, which compares the desired-state
file with the independent sanitized evidence file T13 produces. Fixture
mutations of the bypass actor, target, environment policy, and canary results
each make it red.

T1 and the compiler can be implemented before live settings exist because no
published pack ships hooks. The lint's fixture tests land here; its
`--require-live-evidence` gate and real evidence become green in T13 before the
initiative is marked Shipped or a qualifying hook-bearing pack publishes. T7 depends only on this repository
construction. T13, not T1, is the owner-run Shipped gate.

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
range, matcher failing the grammar, basename failing the allowlist, each
instruction-injection/permission-control event, authored entry count at the
per-event and per-pack limits plus one, resolution/stat errors, and each
exact-command-grammar violation. Each
**skip**: Kiro lowercase events, flat user-scope shape. Command-validation
messages assert pack + file + command; unknown and known-but-unpublishable event
messages assert pack + file + event.

**Approach:** `build/hook_wiring_rules.py` — neutral, so `lint_packs.py` need not
import `projections/`. Exposes `KNOWN_EVENTS`, `is_claude_shaped(entry)`,
`PUBLISHABLE_EVENTS`, and `validate_wiring_entry(...)`.

### T5 — The hook compiler
**Depends on:** T4 · **Mode:** TDD

**Tests:** `stub: true` — `packages/agentbundle/tests/build_pipeline/test_plugin_hooks.py`.
Each allowed interpreter/suffix pair, leading `./`, interpreter flags, trailing
args, environment assignments, operators, substitutions, embedded
`vendor/tools/hooks/…`, zero/multiple hook paths, symlink escape, missing body;
the `sh -c` execution assertion with a space-and-`$` root asserting observed
`argv`; ordering; empty block when no `hook-wiring/`.

**Approach:** `compile_plugin_hooks(pack_path, *, repo_hook_prefix,
plugin_hook_prefix, hook_source_path, wiring_source_path, pack_name) -> dict`.
All four paths are parameters read off the contract by the caller — a module
constant for any is a second copy that drifts. This departs from the
gemini/cursor/copilot private-prefix convention because those adapters hardcode
a destination this route reads from the contract. Structure and error wording
mirror `gemini.py`'s `_translate_hook_entry`; the mechanism is exact token
validation followed by deterministic rendering.

### T6 — A qualifying fixture pack
**Depends on:** none · **Mode:** Goal-based check

**Done when:** `agentbundle validate` passes on a new fixture pack declaring the
current `[pack.adapter-contract].version`,
`allowed-scopes = ["repo", "user"]`, and **`user-scope-hooks = true`**, shipping
nested PascalCase wiring and a hook body. The production route predicate
classifies it as user-capable. A twin without the consent flag is refused by
Rail B.

**Approach:** no existing fixture qualifies — the flat and Kiro shapes are
skipped by the compiler, so they compile to an empty block and cannot carry the
authored-wiring criterion. Rail B is why the consent flag is required.

### T7 — Wire into the derivation
**Depends on:** T1, T2, T3, T5, T6 · **Mode:** TDD (T6's fixture goes green)

**Tests:** `stub: true` — extends `test_build_derivation_claude_plugins.py`.
Manifest hooks merged marker-first and unconditionally; no `<pack>/.claude/`;
bodies at `<pack>/hooks/`; route-eligible wiring-without-manifest raises; a pack with authored
wiring has a marketplace description listing the complete deterministic
authored inventory while the entry omits executable `hooks`; warm and cold
rebuilds are byte-identical.

**Approach:** extend `_resolve_contract_for_route` to require both new keys and
**swap `mode` ← `plugin-mode` alongside the existing `target-path` swap** —
requiring is not applying; today it swaps only `target-path`, and
`_iter_primitives` skips a primitive only when its `mode` is `"dropped"`. Replace
the `derived["hooks"]` assignment and extend `_aggregate_marketplace` with the
description-only disclosure. Re-pin radius-2 anchors **here**, since this is
what breaks them.

### T8 — Pack-source gate
**Depends on:** T5 · **Mode:** TDD

**Tests:** `stub: true` — extends the lint's tests. Two violating packs both
report rather than the first aborting the sweep; a repo-only pack's wiring is
still dry-run compiled. Package tests prove `agentbundle validate` and a
parameterized command-level case covering all six AC20 `render_pack` consumers
reject a hazardous Claude-shaped command for a route-qualified pack at the
shared pre-projection boundary, before `merge_json` or any output write.

**Approach:** pack validation calls `validate_wiring_entry` only when the pack
qualifies for the Claude-plugin route; full-route render consumers reach the
same rule through `compile_plugin_hooks`; direct adapter dispatch deliberately
does not. `lint_packs.py` calls the same function **and** dry-runs
`compile_plugin_hooks` against every pack shipping `.apm/hook-wiring/`,
publishable or not — otherwise `packs/core`'s wiring, the only real wiring in the
tree, is the one wiring the splice and confinement checks never run against.
Each raise converts to a finding string.

### T9 — Other-route regression
**Depends on:** T7 · **Mode:** TDD

**Tests:** `stub: true` — per projection: a non-plugins build still writes
`.claude/settings.local.json` and `tools/hooks/`; byte-baseline assertions cover
`build/self_host.py` via `project_packs`, `commands/pack_evals.py`, and the APM
recipe independently; each of the six `render_pack` consumers is asserted for
expected new output, `init_state.py` included; a pre-change `state.json` carrying
old relpaths behaves as specified under `upgrade`.

### T10 — Real client, erratum, snapshot
**Depends on:** T1, T8, T9 · **Mode:** Visual / manual QA

**Done when:** Claude Code 2.1.226 `claude plugin validate --strict` passes on
the T6 fixture pack built through a local marketplace; `claude plugin details`
reports the exact hook set;
the install surface displays AC34's complete inventory before the explicit
install gesture; an authored hook is observed firing; the execution model is recorded; a dropped
pack is confirmed absent. A writable throwaway marketplace fixture puts one
harmless hook in both its marketplace entry and `plugin.json`; the real client
must report or fire two registrations, proving append rather than metadata
semantics. Transcripts below. **Scope boundary:** the
QA run exercises one user-capable pack and one dropped pack; the other 13 are
covered by the integration assertions, not by hand.

Then: verify the existing Approver-signed erratum on
`docs/specs/wire-session-start-hook/spec.md`; add an Approver-signed erratum to
`docs/specs/claude-plugins-manifest-correctness/spec.md` because its deferred
AC10's "over-reserve hooks/" premise becomes false; land the hook-event
snapshot at
`packages/agentbundle/tests/build_pipeline/fixtures/claude-code-2.1.226-hook-events.json`
so the engine suite carries its own test data in staged source distributions.
T13 owns the later errata that can truthfully say the external branch control
is live.

### T11 — Package release coupling
**Depends on:** T7, T8, T9 · **Mode:** Goal-based check

**Done when:** the non-cosmetic engine/output change bumps the agentbundle
version in both `packages/agentbundle/agentbundle/version.py` and
`packages/agentbundle/pyproject.toml`, updates the package changelog, and the two
version declarations agree. The implementation commit carries the required
`Engine-Change-RFC:` trailer. This PR stops at the versioned release artifact;
tagging and PyPI publication are release-operator closeout and must be recorded
before the feature is marked downstream-shipped.

### T12 — CI parity and mutation evidence
**Depends on:** T10, T11 · **Mode:** Goal-based check

**Done when:** every `.github/workflows/*.yml` trigger is enumerated against the
diff; `make test` (including `tools/test_build_gate_chain.py`), the exact Gate B
heredoc command extracted from `catalogue-tooling-ci-gates.yml`, and
`make lint-mypy` are run separately from `make build-check`. For every new gate
(publisher identity/workflow boundary, schema shape, shared ingress, compiler
confinement/event/count boundary, route projection, and frozen-premise check),
record one deliberate mutation,
the command that turns red, and restoration followed by green. A mutation whose
expected and actual sides derive from the same source does not count.

### T13 — Owner rollout and live publication-control evidence
**Depends on:** T12, T14 · **Mode:** Operational verification

> **Rolled out 2026-08-12.** Steps 1–4 are complete and evidenced in
> `publish-control-evidence.json`. The dedicated publisher App is installed on
> this repository only, with `contents: write` as its sole write permission; the
> `claude-plugin-publish` environment is `main`-only with one required reviewer,
> self-review prevented, and admin bypass off; an active ruleset targets
> `refs/heads/claude-plugins-dist` restricting updates, deletions, and force
> pushes, with the App as its only always-bypass actor. No App, installation,
> ruleset, or account identifier is recorded here or in the evidence — those are
> internal settings, and the lint refuses an evidence file carrying one.
> Canary probes both landed as required — an ordinary owner push was rejected
> (`GH013 … push declined due to repository rule violations`) and the same commit
> pushed with an App installation token was accepted (`Bypassed rule violations
> …`); the canary ref was then deleted with the App identity and the ruleset
> retargeted to the live branch, which was never used as a negative probe.
>
> **Step 5 is NOT done.** The frozen-artifact errata — `claude-plugins-manifest-correctness`,
> `claude-plugin-route-scope`, and ADR-0072's dated branch-integrity statements —
> have not been written, and the named frozen-artifact sweep has not been run.
> The spec must not move to `Shipped`, and no hook-bearing user-capable pack may
> publish, until that is closed.

> **Re-sequenced 2026-08-12 (see T14).** The workflow's App-token step merged in
> #916 ahead of this task, so the publisher could not authenticate and every
> push to `main` failed at the minting step for eight consecutive commits. T14
> restored the interim publisher, made the ordering mechanically enforced, and
> built the tooling steps 4–5 below assume. What remains here is only the part
> that needs a human at github.com: steps 1–4's settings and canary. Run
> `python3 tools/capture-publish-control-evidence.py` for step 4's snapshot and
> follow [`docs/guides/how-to/publisher-app-rollout.md`](../../guides/how-to/publisher-app-rollout.md).

**Done when:** the owner completes AC35's external settings and canary sequence;
`docs/specs/claude-plugin-hook-parity/publish-control-evidence.json` contains the
sanitized independently observed state; and
`tools/lint-claude-plugin-publish-control.py --require-live-evidence` exits 0
against that file plus `.github/claude-plugin-publish-control.json`.

Owner settings, sequenced before the live target is enabled:

1. Create and install a dedicated publisher GitHub App on this repository only,
   with Contents read/write and no other write permission.
2. Create `claude-plugin-publish`, restricted to `main`, with the repository
   owner as required reviewer; store the app ID as an environment variable and
   its private key as an environment secret.
3. Create the exact ruleset against
   `refs/heads/claude-plugins-dist-control-canary` first. Its only always-bypass
   actor is the publisher app; it restricts updates/deletion and blocks force
   pushes.
4. Record an ordinary-identity canary push rejection, then an
   environment-approved publisher-app canary push success. Clean up the canary
   with the app identity, retarget the ruleset to
   `refs/heads/claude-plugins-dist`, and capture sanitized ruleset/environment
   API state into the evidence artifact.
5. Run the live-evidence lint, commit the evidence and frozen-artifact errata,
   including `claude-plugins-manifest-correctness`, `claude-plugin-route-scope`,
   and ADR-0072's dated branch-integrity statements. The frozen-artifact grep is
   the named sweep; if it finds another Shipped/Accepted premise, amend T13
   before execution. Only then permit the Shipped transition or publication of
   a qualifying hook-bearing pack.

The live branch is never the target of the negative probe. If the GitHub plan or
repository ownership model cannot express the app-only bypass or required
environment reviewer, Surface; do not weaken the bypass list.

### T14 — Re-sequence the publisher identity and enforce the ordering
**Depends on:** none · **Mode:** TDD + goal-based check

Satisfies AC36. #916 enabled the live target before T13 provisioned it, which
the plan's own "sequenced before the live target is enabled" forbade. AC35
clause 5's construction tests still passed, because they assert the *end-state*
workflow shape and never ask whether the credentials it names exist. The fix is
to make provisioning state and workflow shape one invariant, checked both ways.

**Tests:** extend `tools/test-publish-claude-plugins.py` — derive the mode from
the presence of `publish-control-evidence.json`, then assert the matching shape.
Two red-first mutations: the current `main` state (App shape, no evidence) must
fail, and a synthetic provisioned-but-interim state must fail. AC35's SHA-pin,
control-lint, and cross-workflow assertions stay unconditional. Add
`tools/test-lint-claude-plugin-publish-control.py` cases for the same invariant
at the lint layer, including a fixture where deleting the check turns the suite
red.

**Done when:** `python3 tools/test-publish-claude-plugins.py` and
`python3 tools/test-lint-claude-plugin-publish-control.py` exit 0; `make
build-check` is green; and a real push to `main` completes the publish job and
updates `claude-plugins-dist`.

1. Restore the interim publisher in `.github/workflows/publish-claude-plugins.yml`:
   `contents: write`, no `environment:`, no token-minting step, checkout at its
   default credential behaviour, `github-actions[bot]` identity. Keep the
   full-SHA action pins and the publication-control lint step — both are
   improvements from #916 that are independent of the identity.
2. Teach `tools/lint-claude-plugin-publish-control.py` the mode invariant, so
   the gate that already runs inside the publish job is the one that refuses a
   mismatch. Export the mode helper for reuse rather than restating the regexes.
3. Add `tools/capture-publish-control-evidence.py` — pure-stdlib, reads live
   ruleset/environment/app state via `gh api`, emits the sanitized evidence
   shape `compare_evidence` expects. This is T13 step 4's "capture sanitized
   API state" made runnable instead of hand-written.
4. Write [`docs/guides/how-to/publisher-app-rollout.md`](../../guides/how-to/publisher-app-rollout.md)
   — the maintainer runbook for T13 steps 1–4, with the exact `gh` commands for
   every part that is scriptable and an explicit marker on the browser-only App
   creation.

Reverting the identity is not a retreat from ADR-0079: the ADR's end state is
unchanged and AC36 clause 4 now makes the interim state self-terminating — once
evidence lands, the interim shape fails its own test.

## Risks

- **Event-set drift.** The accepted event/type surface already exceeds the old
  derived schema. `KNOWN_EVENTS` is pinned to 2.1.226; nothing in CI detects an
  upstream addition, so widening requires another real-client matrix.
  Fail-closed behavior is intentional.
- **The publisher app becomes a high-value credential.** It is repository-scoped
  and short-lived, but compromise during the approved publish job can update the
  executable branch. Environment approval, least privilege, non-persisted
  checkout credentials, exact-step token scope, and GitHub's automatic token
  revocation bound the exposure. Rotation and installation review remain owner
  operations.
- **The marketplace `ref` remains mutable.** AC35 controls the only identity
  allowed to advance it; it does not give adopters an immutable SHA or content
  digest. Per-pack content hashes remain a separate follow-on.
## Verification log

### Publication-control contract acquisition — 2026-08-10

Official GitHub documentation establishes the control primitives:

- branch rulesets can restrict updates so only bypass actors may push, and
  GitHub Apps are eligible bypass actors
  ([available rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets),
  [creating rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository));
- `GITHUB_TOKEN` is an installation token for the GitHub Actions app
  ([token contract](https://docs.github.com/en/actions/concepts/security/github_token));
- a protected environment can require approval before its job starts or its
  secrets are exposed
  ([deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments));
- the official `actions/create-github-app-token` action creates a scoped,
  short-lived installation token and revokes it after the job
  ([action contract](https://github.com/actions/create-github-app-token/blob/main/README.md)).

Inference from those contracts: bypassing the generic Actions app would bypass
by actor, not by workflow, so it cannot distinguish the publisher from another
workflow with `contents: write`. AC35 therefore requires a dedicated app plus an
environment-held credential. Live availability and exact settings still require
T13's owner-run canary; documentation evidence is not a substitute.

### Spike — 2026-08-10

**Contract slice:** Claude Code `2.1.226 (Claude Code)`. Oracle tier is strong
for manifest structure (`plugin validate --strict`) and medium for behavior
(runtime loader plus one constrained launch; official versioned docs were not
available through the session's retrieval surface). The later T10 run must
still complete installation, `plugin details`, and a successful side effect in
a writable, authenticated environment.

Canonical strict-validation command:

```bash
claude plugin validate --strict \
  docs/specs/claude-plugin-hook-parity/<fixture>
```

| Fixture / probe | Exit | Observed contract |
| --- | ---: | --- |
| `spike-baseline.plugin.json` | 0 | Inline `SessionStart` command hook accepted |
| `spike-empty-hooks.plugin.json` | 0 | Empty inline hook object accepted |
| `spike-all-events.plugin.json` | 0 | All 31 named events accepted together |
| `spike-decision-events.plugin.json` | 0 | `Setup`, `PreToolUse`, `PermissionRequest`, `PermissionDenied` accepted |
| `spike-unknown-event.plugin.json` | 1 | Unknown event rejected as `hooks: Invalid input` |
| `spike-command-strings.plugin.json` | 0 | `python3 -c`, `;`, pipe, substitution, backticks, newline all accepted |
| `spike-unsafe-matcher.plugin.json` | 0 | Nested-quantifier matcher accepted |
| `spike-timeout-61.plugin.json` | 0 | Timeout 61 accepted |
| `spike-timeout-zero.plugin.json` | 1 | Timeout 0 rejected |
| `spike-{prompt,agent,http}-hook.plugin.json` | 0 each | Non-command hook types accepted by the client |
| `spike-path-reference.plugin.json` + `spike-hooks.json` | 0 | Manifest path reference to a hook file accepted |
| Temporary marketplace-entry inline hook | 0 | Marketplace `hooks` object accepted under strict validation |

The installed runtime's loader contract adds marketplace-entry component fields
to components from `plugin.json`; inline hooks in both locations are therefore a
second registration source, not metadata-only disclosure. Runtime output also
showed `PreToolUse` and `PermissionRequest` can return permission decisions,
`PermissionDenied` can request retry, and `Setup` contributes additional
context.

Runtime-load command:

```bash
claude \
  --plugin-dir packages/agentbundle/tests/fixtures/blank_catalogue/packs/_example \
  --no-session-persistence \
  --include-hook-events \
  --output-format stream-json \
  --verbose \
  --tools '' \
  --max-budget-usd 0.01 \
  -p 'Reply with OK.'
```

Observed: the temporary inline plugin appeared as `example-pack@inline`; four
`SessionStart` hooks emitted `hook_started` before any emitted `hook_response`,
establishing parallel execution. The spike hook then failed before its command
ran because the client could not create its plugin-data directory in the
read-only user root. The model call reported `Not logged in`; cost was zero.
Both temporary package and marketplace edits were restored byte-for-byte.

Direct-route residual probe: a temporary Claude-shaped wiring command containing
`;` passed `agentbundle validate --strict` with exit 0. The subsequent real
`install --dry-run` reached render and exited 1 because this workspace exposes no
usable temporary directory. This proves the validation gap; T8 must add a
writable-environment install artifact that fails on the command before render.

### Manual work-loop implementation checkpoint — 2026-08-10

The user approved the spec and plan and authorized manual state tracking because
the work-loop state writers cannot write in this workspace. T1–T9 and T11 are
implemented in the working tree; T10, T12, and T13 remain open until the
writable-environment, real-client, CI-parity, mutation, and owner-control
evidence exists.

Read-only evidence completed here:

- `ruff check --no-cache .` exits 0; `git diff --check` exits 0 (with only the
  enterprise runtime's harmless `xcrun` cache warnings).
- Source and derived contract/schema checks, the six contract pins, the
  72-cell pack-scope mirror test, the 14-pack roster lint, and direct
  `agentbundle validate`/`lint packs` probes exit 0.
- An in-memory derived plugin manifest containing the marker plus the two real
  `packs/core` authored hooks validates; the marker remains first.
- The publication-control desired state validates with no current qualifying
  hook-bearing published pack. Independent in-memory evidence with one App ID
  compares green; changing only the protected-environment App ID turns the
  comparison red.
- The diff triggers `build-check`, `build-check-windows`,
  `catalogue-tooling-ci-gates`, `ci-security`, `codeql`, `docs`, and
  `release-agentbundle` on a pull request; the publisher runs after a push to
  `main`. `pages`, the two scheduled canaries, `publish-catalogue`, and
  `release-credbroker` are not path-triggered by this diff.

Environment-limited evidence is recorded as blocked, not green:

- `tools/test-publish-claude-plugins.py` stops at its first
  `tempfile.TemporaryDirectory()` before any assertion because none of the
  system or workspace temporary roots is writable.
- `tools/test_build_gate_chain.py` reaches 12 of 13 gates; the remaining gate
  errors only while creating a temporary fixture. Pytest, build/site outputs,
  `make test`, `make build-check`, and catalogue archive/build commands have the
  same write boundary.
- `mypy --no-incremental` terminates with a mypy 2.1.0 internal error rather
  than a project diagnostic. T12 still requires `make lint-mypy` in the
  supported environment.
- GitHub settings, the canary, authenticated API evidence, commits, and the
  required `Engine-Change-RFC:` trailer cannot be produced here. They remain
  T13 and release-closeout work, not inferred success.

Manual review loop:

- The implementation adversarial pass found a direct `agentbundle.build`
  recipe bypass, missing command-handler coverage for the six `render_pack`
  consumers, and a Windows shell-test portability issue. Validation now runs
  inside `run_recipe`; the six actual handlers share one hazardous-wiring
  parameterization with pre-write assertions; the execution oracle is
  POSIX-gated. Re-review: `Clean — ready to commit.`
- The implementation security pass found that the publisher construction gate
  enumerated `.yml` but not GitHub's equally executable `.yaml` suffix. The
  scan now covers both and an in-memory `backdoor.yaml` mutation turns it red.
  Re-review: `Clean — ready to commit.`
- The quality pass found an unguarded symlink fixture on Windows and no
  independent desired-policy mutations. The missing/symlink cases are split
  with `OSError` skip semantics, and target, bypass actor, app permission,
  environment reviewer, and canary desired-state mutations all turn
  `validate_desired` red. Re-review: `Clean — ready to commit.`
- The newest local annotated release tag is `agentbundle-v0.31.1`, dated
  2026-08-10, so `0.32.0` is the monotonic checkout successor. The public PyPI
  retrieval cache still showed 0.6.0 and a single bounded `pip index` probe
  stalled, so release closeout must confirm 0.31.1 is actually present on PyPI
  before 0.32.0 is tagged; cached search output is not publication evidence.

### First writable full-gate run and correction — 2026-08-10

The owner's writable run drove the real package artifact and found that T8's
first ingress placement was too broad. The compiler's publication policy was
being applied to repo-only direct-route fixtures and to a user-scope
Copilot-only fixture that had no plugin manifest. That rejected established
`PreToolUse`, compatibility `command = "x"`, and Copilot `tools/on-start.py`
shapes before their owning adapters could handle them. A second ordering bug
made the Claude-plugin recipe raise for a repo-only wiring pack without a
manifest before applying the route-scope filter. Most package failures were
cascades from those two early exits.

The first correction made the shared runtime ingress conditional on the
canonical `pack_is_publishable` predicate. The next writable run showed that
identity alone was still too broad: historical direct-route fixtures were
user-capable and carried manifests even though the operation under test was
direct adapter dispatch. The final boundary therefore applies publication
policy only in `agentbundle validate`, repository lint, and actual plugin-recipe
compilation. Direct install/self-host/adapter paths retain their established
contract. The missing-manifest refusal still applies when a pack otherwise
qualifies by scope.

The three upgrade catalogues intentionally request the legacy full dist-tree,
so they do compile the plugin recipe. Their static `PreToolUse`/`command =
"true"` wiring was never a live-hook fixture and could not satisfy that route's
new contract. Without changing scope metadata, those fixtures now use
`PostToolUse` and name their existing `pre-commit.sh` body. Their tested concern
remains SHA tracking, matcher change, and atomic body/wiring movement. Separate
regression artifacts exercise direct-route command preservation, Copilot
user-scope hooks, and the route-qualified hazardous fixture.

The same run found two independent small defects: the publisher construction
test matched the app-token action input `permission-contents: write` as if it
were a workflow `contents: write` permission, and mypy required an annotation
on the adapter's empty validation fallback mapping. The construction test now
matches an exact YAML `contents` key; the fallback disappeared when redundant
direct-adapter validation was removed. The owner's second run reports every
publisher construction case green. Its remaining package failures all shared
the legacy upgrade-wiring fixture described above; no independent failure class
remained. After the final boundary edits, `python3 tools/lint-mypy.py` reports
no issues across 113 source files, `ruff check --no-cache` passes on every
touched Python file, the three upgraded fixture catalogues compile through the
real plugin compiler, and `git diff --check` is clean. The next writable package
rerun remains the T12 evidence gate.

The owner's targeted integration rerun then passed the entire pre-existing
integration corpus and left only six new ingress-test failures. In all six, the
compiler correctly refused the hazardous command, but `_run_per_pack` converted
the expected pack-input `ValueError` into an uncaught `RuntimeError`. The
dispatcher now preserves `ValueError` (while adding pack context), so command
handlers render their normal one-line nonzero refusal; unexpected engine errors
remain `RuntimeError`. Render output-root creation also moves after recipe
acceptance, preserving the pre-write assertion without changing successful or
empty-recipe output guarantees.

The focused `test_hook_wiring_ingress.py` rerun is green in the writable owner
environment after that error-contract correction.

The subsequent `make ci` run reaches the final SAST/SCA leg after the package,
tooling, lint, build, parity, and Bandit gates pass. `pip-audit` then fails to
start because the active `.venv` Python has no `pip_audit` module. This is
recorded as a missing local verification dependency, not a vulnerability
finding and not a green SCA result; the audit must be rerun after installing the
declared gate tool into that environment.

The owner reran `make sast` with a working `pip-audit` on `PATH`. Bandit, the
audit-input self-test, every requirements/build-system audit, the documented
Semgrep-tooling transitive allowlist, the Semgrep scan, and all five custom-rule
mutation fixtures pass. The repeated CacheControl deserialization warnings
cause stale entries to be ignored and do not suppress an audit result. SAST/SCA
is green.

Gate B also passes from the built `agentbundle` 0.32.0 wheel installed into an
isolated environment. Using only that installed artifact, an external
user-capable catalogue completed build, lint, source-tree verification,
packaging, and archive-plus-checksum verification. The source verification
reported only the expected optional-lint-extra and sample repository-link
warnings. The temporary local runner used to collect this evidence was removed
after the pass; it is not part of the shipped implementation.

The final adversarial pass found that AC26's Rail B consent was enforced by
`agentbundle validate` but not repeated at the actual plugin build or publisher
membership boundaries. The shared on-disk publication predicate now applies
Rail B, the plugin recipe refuses an unconsented user-capable hook pack before
creating output, and the publisher independently rechecks the same rail from
the source tree. Regression cases pin both refusal boundaries and confirm that
direct adapter dispatch retains its established byte-preserving behavior.

The owner then reran the complete `packages/agentbundle/tests/` suite, the
publisher construction suite, and mypy after the consent correction. All pass;
the publisher suite now reports 28 green construction cases, including the
missing-consent refusal and explicit-consent lift, and mypy reports no issues
across 113 source files. The final adversarial, security, and quality reviews
each returned `Clean — ready to commit.` The 0.32.0 PyPI long description was
also brought forward to the shipped local-scope and Claude-plugin behavior and
its release-facing links were checked against existing repository artifacts.
The owner built fresh wheel and source distributions after that documentation
edit and `twine check` accepted both artifacts, so the release will carry a
renderable long description rather than relying on the earlier pre-edit wheel.

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
- **2026-08-10** — spike against Claude Code 2.1.226. Kept marker emission
  unconditional; replaced shell rewriting with an exact two-token grammar;
  restricted the three permission-control events and the `Setup`
  context-injection event;
  moved validation into the shipped ingestion path; added description-only
  marketplace disclosure because inline marketplace hooks are executable and
  would double-register.
- **2026-08-10** — owner authorized closing the dist-branch integrity
  precondition. Added AC35/T1: dedicated repository-scoped publisher GitHub App,
  app-only branch-ruleset bypass, protected environment approval, read-only
  ordinary workflow token, and canary denial/acceptance proof. A generic
  Actions-app bypass was declined because it identifies the platform app, not
  the one publisher workflow.
- **2026-08-10** — writable gate iterations moved T8's guard to the actual
  plugin-publication boundary rather than adapter dispatch or pack identity.
  Repository lint still compiler-checks all wiring packs; direct routes retain
  their established contracts. The full-dist upgrade fixtures now carry valid
  publishable wiring without scope changes. Also fixed the publisher permission
  test's substring false positive.
