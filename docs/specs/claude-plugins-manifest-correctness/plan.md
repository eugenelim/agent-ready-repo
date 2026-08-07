# Plan: Claude-plugins manifest correctness

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Three parts, sequenced so no gate is left red across tasks.

**Part A — the validation gap (why both defects shipped).** No gate validates a
marketplace plugin entry. `build/main.py:545-546` pops `source` and `category`
before `validate_derived_plugin_manifest_dict`, so the derived schema has never
seen a `source`; `verify.py:594` validates only per-pack `plugin.json` under
`dist/claude-plugins`. Proof: live entries carry `category`, which the derived
schema forbids. T0 closes this **against the current schema**, so the gate starts
running before its contract changes.

**Part B — the source shape.** Two writers, not one: the dist aggregation in
`build/main.py`, and `self_host._aggregate_marketplace` (`self_host.py:602`/`:632`)
which writes the root `.claude-plugin/marketplace.json` adopters add. Schema and
generator move together in T2 so `catalogue verify` never goes red between tasks.
Removing `repo` breaks dist envelope derivation (`build/main.py:705-717`).

**Part C — the component layout.** Plugins load `skills/`, `agents/`, `commands/`
at the plugin root; the projection emits `.claude/`. The seam decision is T3; the
implementation is T4. They are separate tasks because two tasks owning one change
produces either a double implementation or neither.

Verification anchors on AC11 against the real client, not the unit gates.

## Constraints

- **ADR-0072** governs: the derived manifest schema mirrors Claude Code's
  published schema; when they disagree, upstream wins. AC8's at-least-one
  `ref`/`sha` requirement is a deliberate tightening *beyond* upstream, expressed
  with `if`/`then`/`else` (never `oneOf` — unsupported by the real validator) and
  recorded there as a named exception. Moves to Accepted in this PR.
- Edit generators and `packs/`, never projected output.

## Source readers — enumeration (AC6)

Completed at PLAN, not deferred. A bare `grep '"source"'` is hostile: `source` is
an unrelated catalogue concept in `config.py:564`, `user_config.py:179`,
`commands/upgrade.py:659`, `commands/list_installed.py:262`. The genuine readers
of a *plugin* `source` object are three, all under `build/`:

| Reader | Role | Disposition |
|---|---|---|
| `build/main.py:705-717` | derives dist envelope `name`/`owner` from `src["repo"]` | **must change** — AC5 |
| `build/main.py:545-546` | pops `source`/`category` off `plugin.json` | shape-agnostic; unchanged |
| `build/self_host.py:602`/`:632` | second writer; root `marketplace.json` | **must change** — AC4 |

T5 verifies this table still holds after the change; it does not produce it.

## Layout consumers — enumeration (AC13)

The counterpart table. These assert the old
`claude-plugins/<pack>/.claude/...` shape and go stale with T4:

| Consumer | What it asserts | Disposition |
|---|---|---|
| `docs/specs/claude-plugins-publish-and-discover/spec.md:46` | **shipped** spec, AC3 `[x]`: branch dir "contains ... `.claude/skills/`" | **supersede, do not edit** — `Status: Shipped` → Frozen (`CONVENTIONS.md:103`); erratum only |
| `tests/integration/test_install_adapt_chain.py:87,98,110` | `claude-plugins/demo/.claude/skills/demo/SKILL.md` relpaths | update to plugin-root |
| `tests/integration/test_install_core_smoke.py:15` | `claude-plugins/core/.claude/settings.local.json` | unchanged — hook wiring stays (AC2) |
| `commands/upgrade.py:1667` | docstring example naming the old path | update |
| `docs/adr/0004-...md:13`, `docs/specs/repo-scope-per-adapter-projection/spec.md:14` | historical narrative in shipped governance docs | **leave** — historical record, not operative |

## Stub materialisation (PLAN artifact)

`packages/agentbundle/tests/integration/test_marketplace_entry_validation.py`
carries the red stubs for T0, T1, and T2, each marked `# STUB: AC<n>` per
`docs/CONVENTIONS.md § Stub → EXECUTE handoff`. Run at PLAN: **11 failed, 4
passed, 0 skipped** — the file compiles, so no AC in its scope is
under-specified.

Two properties are load-bearing and were corrected during PLAN:

- **They use `agentbundle.build.validate`, not `jsonschema`.** `jsonschema` is
  absent from `pyproject.toml` `dependencies = []` and from CI Gate A's install
  list, so an `importorskip` turned four assertions into silent skips on CI while
  passing locally (it is installed on the author's machine). It is also the wrong
  validator: `build/validate.py` is what `build/main.py:31` and `verify.py:600`
  gate on.
- **They build into `tmp_path`, not the working tree.** `dist/` is gitignored
  (`.gitignore:73`) and CI runs no `make build`, so reading it skipped the dist
  half of AC9 and all of AC5. Zero skips now.

The stub also caught an API error at PLAN, which is the mechanism working:
`_run_aggregate` returns a *summary* (`{'entries': 1, 'recipe': ...}`) and writes
the payload to disk; the first draft asserted against the return value.

One stub result is load-bearing beyond its own task:
`test_http_repository_link_is_rejected_not_upgraded` reports `DID NOT RAISE`,
empirically confirming that `_GITHUB_URL_RE` accepts `http://` today and would
silently emit it as `https://`. T2 fixes this.

**Known stub weakness (all 4 passes), to close in T2.** Three are
`test_source_requires_ref_or_sha` and the two `test_source_url_is_constrained`
params. The fourth is `test_dist_envelope_survives_repo_key_removal`, which
passes *because `repo` still exists*: `_run_aggregate` overwrites the fixture's
`source` from `pack.toml` (`build/main.py:694-697`), so `:712` still finds
`repo` and derives the envelope. It currently tests the opposite of its name and
will read as durable green through EXECUTE — T2 must re-assert it after `repo`
is gone, and assert *values* (`name == "agent-ready-repo"`,
`owner == {"name": "eugenelim"}`) not mere key presence, since a mis-parsed
clone URL would pass a presence check. The other three pass because a
`git-subdir` payload also fails the legacy subschema (which requires
`repo`/`branch`/`directory` under `additionalProperties: false`), so
`pytest.raises` is satisfied by the wrong error. They become meaningful only once
T2 lands the new subschema; T2 must re-assert them against the corrected schema
rather than trusting a green.

## Construction tests

Cross-cutting: for one representative pack, the claude-plugins route and the
non-plugins routes emit **different** component paths from the same source pack,
and a decoy `<root>/skills/decoy/` planted before a non-plugins build survives it.
Guards AC2, AC3, and the orphan-sweep hazard together.

## Tasks

### T0 — Close the validation gap

**Depends on:** none · **Verification mode:** TDD · `stub: true`

**Tests:** `packages/agentbundle/tests/integration/test_marketplace_entry_validation.py`
— `# STUB: AC9`. Cases: (a) a malformed `source` in the **dist**
`marketplace.json` fails `catalogue verify`; (b) the same for the **root**
`.claude-plugin/marketplace.json`; (c) every entry in each built marketplace
validates, asserting `>= 1` entries were checked rather than a fixed count.

**Approach:** Introduce a **marketplace-entry schema** — the derived schema plus
`source` *required* and `category` permitted. One schema cannot serve both
artifacts: `plugin.json` must not carry `source`, an entry must require it.
Extend `verify.py` `_step_plugin_manifests` (currently `dist_dir = tmpdir /
"dist" / "claude-plugins"`, `:594`) to validate both marketplace paths. Land
against the **current** source shape so the gate is proven live before T2 changes
what it asserts. Also add the `x-spec` back-link / `contracts/REGISTRY.md` entry
for every contract this spec touches — `lint-spec-status.py --root .` emits a live
warn-only invariant-(v) warning for `spec.md:7` today.

**No ride-alongs.** An earlier draft claimed the four `category` comments at
`build/tests/test_plugin_manifest_schema.py:169,185,202,210` go stale here. They
do not: T0 introduces a *separate* entry schema, leaving the derived schema's
`additionalProperties: false` rejection of `category` intact, so all four remain
accurate. Editing them would be unauthorised sprawl on a false rationale.

**Fifth schema copy.** The entry schema needs a `_data/` twin —
`verify.py:599-605` resolves through `_read_bundled`, which reads
`agentbundle/_data/` first (`build/main.py:70-85`), and `pyproject.toml:41` ships
`_data/*` into the wheel. Add its byte-equality gate beside
`tests/unit/test_contract_v0_3_schema.py:601-617`.

### T1 — Re-pin every assertion holding the old shape (red)

**Depends on:** T0 · **Verification mode:** TDD · `stub: true`

**Tests:** Assertion-only; all must fail against the current generator.

**Approach:** Re-pin by invariant, not line number — no assertion may require
`source.source == "github"`, `source.repo`, `source.branch`, or
`source.directory`. Known sites: `tests/integration/test_marketplace_manifest_regression.py`
(`TestDeriveProjectableSubsetSource`, and the assertions around :236, :250-257),
`agentbundle/build/tests/test_projectable_subset.py:69-73`,
`agentbundle/build/tests/test_plugin_manifest_schema.py:181-182`. Grep the
invariant rather than trusting this list.

### T2 — Correct the four schemas and both writers together

**Depends on:** T1 · **Verification mode:** TDD · `stub: true`

**Tests:** T1's tests go green. Plus: an `http://` repository link is **rejected**,
not upgraded; a payload with neither `ref` nor `sha` is rejected; a non-github.com
`url` is rejected; the dist envelope keeps `name`/`owner`/`description`; the
`config.build.claude_plugin_branch` override still reaches `source.ref`; each
writer's output asserted separately, with the self-host writer invoked into
`tmp_path` rather than reading the committed artifact. The `_data/` byte-equality
gates (`tests/unit/test_contract_v0_3_schema.py:601-617`) stay green.

**Approach:** Schema and generator land in one task so `catalogue verify` is never
red between tasks. Rewrite the `source` subschema in both `contracts/` files and
re-sync both `_data/` twins: `required: ["source","url","path"]` plus
at-least-one `ref`/`sha` via `if`/`then`/`else`; `enum: ["git-subdir"]`; `url`
pattern `^https://github\.com/[^/]+/[^/]+\.git$`; `path` pattern
`^[a-z0-9][a-z0-9-]*$`. Express ref-or-sha with **`if`/`then`/`else`, never
`oneOf`** — `build/validate.py:23-28` lists `oneOf`/`anyOf`/`allOf` as
"Unsupported by design" and both real gates use that validator
(`build/main.py:31`, `verify.py:600`), so a `oneOf` would be silently ignored by
the gate while a `jsonschema`-based test went green. Then
`derive_projectable_subset` (`build/main.py:199`): tighten `_GITHUB_URL_RE`
(`:49-51`) to `^https://` **and add an explicit `http://github.com/...` branch
that raises `ValueError`** — tightening alone converts a silent upgrade into a
silent omission, because a non-matching link yields no `source` key at all
(pinned by `test_marketplace_manifest_regression.py:150`); read `_DIST_BRANCH` for
`ref` (do not inline — `catalogue_tooling/build.py:103-113` overrides it);
re-point envelope derivation (`:705-717`) at the parsed `url`. Apply to
`self_host._aggregate_marketplace`. Update the docstring at `:209-211`.

### T3 — Decide the per-route layout seam

**Depends on:** none · **Verification mode:** goal-based check · `no stub (mode)`

**Done when:** the chosen option and its concrete signature or contract diff hunk
are recorded in this plan's changelog. **Decision only — T4 implements.**

**Corrected finding (a prior draft got this wrong).** The claude-code adapter
reads the **legacy `projection` array** (`build/adapters/claude_code.py:120`),
whose item schema (`contracts/adapter.schema.json`) requires only `primitive` and
`mode` and does **not** set `additionalProperties: false`. The
`projections.<primitive>.target` object that *does* pin `repo`/`user` under
`additionalProperties: false` is consumed only by kiro/kiro-ide/cursor/gemini;
`contracts/adapter.toml:170-177` states the legacy array "remain authoritative"
and the new tables are "declarative metadata". **So there is no Ask-first contract
boundary here**, and a route-scoped key on the `projection[]` entry needs no
schema amendment.

Options:
- **(a) Route argument threaded through dispatch.** `build/main.py:475` resolves
  `project = ADAPTERS[recipe.adapter]` and calls it at `:504` as
  `project(pack.path, contract, per_pack_output)`. The route is a property of the
  *recipe* (`per-pack-claude-plugin`), not the adapter, so a defaulted kwarg on
  `claude_code.project_packs` alone is unreachable — the dispatch in
  `_run_per_pack_single` must derive the route from `recipe.name` and pass it
  through. Requires deciding whether every adapter's `project` signature widens
  or claude-code is special-cased.
- **(b) Route-scoped key on the `projection[]` entry.** No schema amendment
  needed (see above). Declarative; keeps dispatch untouched.
- **(c) Route-scoped `target-path` on the recipe TOML.**

**Recommendation: (b).** It is the smallest change that keeps the layout
declarative where the adapter already reads it, and avoids widening a signature
shared by every adapter.

**Also decide:** whether the orphan-sweep target is route-aware.
`_skill_direct_directory_target` (`claude_code.py:65`) and
`_sweep_skill_orphans` (`:101-115`) read the same contract target as the
projection. If the route reaches the projection but not the sweep, the sweep
silently targets a nonexistent `.claude/skills/` on the plugins route.

### T4 — Project components to the plugin root

**Depends on:** T3 · **Verification mode:** TDD · `stub: true`

**Tests:** The cross-cutting pair (AC2 + AC3). The decoy expectation is
**per-route and opposite**, not "both routes": on a non-plugins build a decoy at
`<root>/skills/decoy/` **survives** (that route's sweep target is
`.claude/skills/`); on the plugins route `<root>/skills/` *is* the sweep target,
so a decoy there is an orphan that must be reaped — and it cannot even be planted,
since `per_pack_output` is `rmtree`'d before every build (`build/main.py:501-504`).
Also pin the plugins-route sweep target explicitly, so T3's second decision is
covered by a test rather than only by prose.

**Approach:** Implement T3's decision. Components reach the plugin root through
`_project_direct_directory` (`skill`) and `_project_direct_file` (`agent`,
`command`) — `contracts/adapter.toml` declares agent and command as `direct-file`
— under the `_assert_under(per_pack_output, output_dir)` already applied at
`build/main.py:498`. No post-projection relocation. Confirm `${CLAUDE_PLUGIN_ROOT}`
still resolves (`.claude-plugin/scripts/install-marker.py` does not move). Add the
reserved-name build failure (AC10), deriving the reserved set from the
`skill`/`agent`/`command` `target-path` entries in `contracts/adapter.toml:188-215`
— **not** `PRIMITIVE_DIRS` (`build/main.py:93`), which is the five *source* dir
names and would over-reserve `hooks/` and `hook-wiring/`.

### T4b — Reconcile layout consumers (AC13)

**Depends on:** T4 · **Verification mode:** goal-based check · `no stub (mode)`

**Done when:** the unfiltered sweep
`grep -rn 'claude-plugins/[a-z-]*/\.claude/skills' packages/ docs/specs/`
returns only the frozen-spec body and the **leave**-marked historical rows in
the Layout consumers table. Concretely: the three assertions in
`test_install_adapt_chain.py::test_install_marker_records_new_companions`
(`:87,98,110`) updated; `commands/upgrade.py:1667`'s docstring example updated;
and a dated one-line erratum added under the header of
`docs/specs/claude-plugins-publish-and-discover/spec.md` pointing at this spec's
AC2. **The frozen spec's AC3 body is not edited** — `CONVENTIONS.md:103` freezes
shipped bodies, and its `(Verified via gh api…)` note records an observation
that was true when made.

### T5 — Verify readers, sweep anchors, regenerate

**Depends on:** T2, T4 · **Verification mode:** goal-based check · `no stub (mode)`

**Done when:** ADR-0072 is flipped `Proposed` → `Accepted`; the Source readers
table above still holds; `make build-self`
clean; `git status` shows only intended regenerated files; `SKIP_SAST=1 make
build-check` passes; and the two CI gates pass locally — `make build` and
`PYTHONPATH=packages/agentbundle python -m agentbundle catalogue verify --root .`.

**Approach:** Per the AGENTS.md anchor-test rule, grep for tests that hash, count,
or snapshot projected paths *before* regenerating — the layout move will move many
files and content-pinning failures are consequences, not defects. Run the
agentbundle suite from `packages/`; `make build-check` reads site-packages locally.

### T6 — Docs, changelog, migration note

**Depends on:** T2, T7 · **Verification mode:** goal-based check · `no stub (mode)`

**Done when:** `docs/architecture/pack-manifest.md`'s derived-key table gains a
`source` row and its `author` row is corrected (it says `"Name <email>"`, a
string; the generator emits an object); adopter docs show the `git-subdir` shape
and plugin-root layout; the existing-adopter `marketplace update` + reinstall step
is documented; a `docs/product/changelog.md` entry lands; and
`.github/workflows/publish-claude-plugins.yml:20`'s recorded client version is
refreshed to the version T7 verified against. **Depends on T7 for that version.**

### T7 — End-to-end install against the real CLI

**Depends on:** T5 · **Verification mode:** visual / manual QA · `no stub (mode)`

**Done when:** observed `claude plugin details` output is pasted into the
changelog below showing Skills ≥ 13 and Agents ≥ 4 for `core`, with the client
version and the actual field list recorded.

**Approach:** Build a marketplace from locally regenerated output — **not** the
published branch, which carries the old layout until this merges. Add it with
`CLAUDE_CONFIG_DIR` pointed at a throwaway directory; never touch the operator's
`~/.claude`. Spot-check `converters` (ships `scripts/` trees). Note whether a tag
shares the branch name, since `ref` is ambiguous in git.

## Rollout

Ordering matters, because merging to `main` auto-publishes executable content to
adopters.

1. **Branch protection on `claude-plugins-dist` lands first** — block force-push
   and deletion, restrict pushes to the publish workflow. Verified absent today
   (protection API returns 404 for that branch; `main` blocks force-pushes). This
   is a repository-settings action outside this diff and **owned by the repo
   owner**; registered as `workspace.toml [backlog].open` slug
   `dist-branch-protection` so it survives this PR.
2. Merge this PR. `publish-claude-plugins.yml` rebuilds and republishes
   `claude-plugins-dist` automatically; no manual step.
3. Existing adopters run `claude plugin marketplace update` then reinstall (T6
   documents this).

Rollback: revert the PR; the next push to `main` republishes the prior shape.

## Risks

- **`claude-plugins-dist` has no branch protection.** Before this change the
  branch delivered empty plugins, so exposure was theoretical; after it, it
  delivers skills, agents, and a `SessionStart` hook that execute on every
  adopter's machine. Anyone with repo write, or any workflow holding
  `contents: write`, can push there unreviewed. Sequenced first in Rollout.
- **CI cannot run the real client**, so the hermetic gate can only prove the
  generator agrees with a schema we also wrote. T0 makes the gate real; ADR-0072
  names the residual.
- **Anchor tests.** The layout move touches many projected paths; T5 front-loads
  the sweep.

## Changelog

- **Initial draft.** Both defects reproduced with the real client (Claude Code
  2.1.223) in throwaway `CLAUDE_CONFIG_DIR`s: `github` + `branch`/`directory`
  installed the repo root of `main`, reporting Skills 0 / Agents 0 / Hooks 0;
  `git-subdir` alone reached Skills 0 / Agents 0 / Hooks 1; plugin-root components
  reached Skills 13 / Agents 4 / Hooks 1.
- **Revision 1** (adversarial + security round 1). Generator is
  `derive_projectable_subset`, not the fabricated `_derive_manifest_subset`.
  **Root-cause correction:** the schema was never the gate — `source` is popped at
  `build/main.py:545-546`, so marketplace entries are validated by nothing. Second
  writer found (`self_host.py:602`). Four schema files, not one. `ref`/`sha`
  `oneOf` and `url`/`path` patterns added. Branch protection surfaced.
- **Revision 2** (adversarial round 2). **Ask-first claim withdrawn:** the prior
  draft said `adapter.schema.json` blocks a route seam; that node is the
  forward-looking `projections.*` table the claude-code adapter never reads, and
  `adapter.toml:170-177` says so. The authoritative `projection` array permits a
  route key with no schema change — T3 now recommends that. Also: AC9 extended to
  the root marketplace, not just dist; a separate marketplace-entry schema, since
  one schema cannot both forbid and require `source`; `_GITHUB_URL_RE` tightened
  to `^https://` (it accepts `http://` today and would have silently upgraded it);
  `_project_direct_file` named for agent/command; `_assert_under` claim corrected
  to the per-pack guard at `:498`; AC11's unsatisfiable Commands field replaced
  with `Skills ≥ 13`; T6/T7 dependency inverted; schema and generator merged into
  T2 to remove a three-task red window; `## Rollout` added.
- **Revision 3** (adversarial round 3). **`oneOf` withdrawn:** `build/validate.py:23-28`
  lists `oneOf`/`anyOf`/`allOf` as "Unsupported by design" and both real gates use
  that validator, so AC8's `oneOf` would have been silently ignored by the gate
  while a `jsonschema` test went green — the same looks-like-a-gate failure this
  spec exists to fix. Now the `if`/`then`/`else` trio, which also fixes a second
  bug: `oneOf` would have rejected a legal `ref`+`sha` payload, falsifying
  ADR-0072's "exactly one departure". Stubs rewritten off `jsonschema` (absent
  from CI) and off the gitignored `dist/` tree; zero skips. AC3 rescoped per
  *projection* after finding `install.py --emit-install-routes` emits the
  claude-plugins route; the non-existent "unprojection map" replaced with
  `_installed_skill_names`. AC1 gained an explicit raising branch — tightening
  `_GITHUB_URL_RE` alone converts a silent upgrade into a silent omission. Fifth
  schema copy scheduled (`_data/` twin of the entry schema). AC13 added: a
  **shipped** spec's checked AC (`claude-plugins-publish-and-discover/spec.md:46`)
  asserts the published branch contains `.claude/skills/` and goes false here;
  layout-consumer table added. A false ride-along dropped — the `category`
  comments stay accurate under a separate entry schema. Citation anchors
  normalised repo-wide.

## Execution record

- **T3 decided, and refined during T4.** The plan recommended option (b), a
  route-scoped key on the `projection[]` entry. Implementation kept the key
  (`plugin-target-path`) but resolved it in the **dispatcher**
  (`_resolve_contract_for_route`) rather than in the adapter: the adapter still
  reads `target-path`, so no signature widens, and — the reason this is better
  than what was planned — the orphan sweep reads the same contract and becomes
  route-correct *by construction*. Concern 18's hazard (sweep targeting a
  nonexistent `.claude/skills/` on the plugins route) cannot arise.

  Verified per route:
  `per-pack-overlay → .claude/skills|agents|commands`;
  `per-pack-claude-plugin → skills|agents|commands`.

- **T0 shipped the defect it was fixing, and the negative probe caught it.**
  The first wiring passed `catalogue verify: ok`, but a probe with three
  malformed entries returned **0 diagnostics**: the early return
  `if not dist_dir.exists(): return []` sat above the root-marketplace check,
  making it unreachable whenever `dist/` is absent — which is how CI runs. After
  the fix the same probe returns 6 diagnostics. A gate is not a gate until you
  have watched it reject something.

- **T7 — AC11 observed output** (Claude Code 2.1.223, throwaway
  `CLAUDE_CONFIG_DIR`, marketplace built from locally regenerated output because
  the published branch still carries the old layout):

  ```
  Core (core) 2.2.0
    Skills (13)  adapt-to-project, author-brief, bug-fix, capture-work,
                 contract-acquisition, conventions-check, init-project, new-spec,
                 operational-safety, receive-brief, security-checklists,
                 work-loop, workspace-status
    Agents (4)   security-reviewer, adversarial-reviewer, quality-engineer, implementer
    Hooks (1)    SessionStart
  ```

  The client reports the `conventions-check` command under Skills, so 13 = 12
  skills + 1 command and there is no separate Commands field — as Assumption 2
  predicted. `converters` spot-checked for `scripts/` integrity after the move:
  `skills/mermaid-renderer/scripts/render_mermaid.py` present, Skills (8).

- **Anchor tests.** The layout move broke four, exactly as T5 predicted:
  `test_pipeline` (2), `test_self_host_check` (1), `test_end_to_end_build` (1),
  plus `test_install_adapt_chain` in wave 1. All re-pointed; the end-to-end test
  additionally gained negative assertions so a half-applied move now fails.

- **Tooling tension found.** `loop-cohort plan check-current` exits 1 with
  "spec.md has changed since approve-plan" — caused by the work-loop's own
  mandated `Status: Implementing` bump, which necessarily happens *after*
  `approve-plan` pins the spec hash. `check --phase implement` stays green, so
  EXECUTE is unblocked, but the two mechanisms contradict each other by
  construction. Worth a fix in the loop tooling.

### Post-GATES review round (adversarial + security)

Both reviewers found real defects. The most serious were self-inflicted and of
one kind, now captured as `docs/knowledge/patterns.jsonl` **K-0017**:

- **ACs were marked `[x]` before the work existed.** AC10's reserved-name guard
  was never implemented, and AC3's decoy test and AC9's negative gate tests did
  not exist. AC10 is now un-checked and deferred
  (`plugin-root-name-collision-guard`); the missing tests were written. The
  AC-checking pass ran ahead of the implementation — a bookkeeping habit that
  produced a spec claiming more than the diff delivered.

- **The new gate failed open.** Both schemas loaded in one `try` with a bare
  `return []`, so one unresolvable file silently disabled the whole step —
  including the `plugin.json` validation that already worked. Verified against
  an installed wheel, which has `plugin-manifest.derived.schema.json` but not
  the new `marketplace-entry.schema.json`. Now emits a diagnostic and fails
  closed, pinned by `test_gate_fails_closed_when_a_schema_is_unresolvable`.

- **`source` as a required property broke adopters.**
  `[pack.links].repository` is optional and the shipped scaffold `_example`
  pack omits it, so requiring `source` turned every scaffold-derived adopter's
  `catalogue verify` red. It is now constrained-when-present, with an
  actionable diagnostic naming `[pack.links].repository` when absent.

- **`target-path` reached a filesystem join unconfined.** An absolute value
  discards the base on join and a `..` value walks out of it — and the orphan
  sweep resolves the same value, so an escaped target becomes the root of a
  `rmtree`. `_resolve_target` now canonicalises and prefix-checks (CWE-73
  depth, not just CWE-22).

- **`_resolve_contract_for_route` failed open**, silently restoring the
  `.claude/` layout on a typo'd or stale contract key. It now raises.

- **The site-packages trap bit again.** `make build-self` resolves
  `agentbundle` from site-packages, not this workspace, and silently
  regenerated all 21 marketplace entries with the *old* generator. Only
  `PYTHONPATH=packages/agentbundle` produces a correct artifact locally. Any
  local gate on this pipeline must pin `PYTHONPATH` or it verifies someone
  else's code.

**Still open, deliberately:** branch protection on `claude-plugins-dist`
(`dist-branch-protection`) remains the merge precondition; AC10 is deferred;
the reviewers' remaining Concerns (contract-schema declaration of
`plugin-target-path`, `adapter.toml` version-history line, a meta-check
forbidding unsupported JSON-Schema keywords, `\Z` vs `$` in patterns) are
recorded here and not yet actioned.
