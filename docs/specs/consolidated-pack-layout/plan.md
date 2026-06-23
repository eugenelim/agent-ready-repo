# Plan: consolidated-pack-layout

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change has one foundation and four leaves. The foundation is the
**manifest extension** (T1): `pack.toml` gains an optional scope-keyed
`[pack.layout]` table, `pack.schema.json` accepts it, and the manifest version
bumps — nothing else can land until the schema validates a pack that declares a
default. On top of it, four mutually-independent leaves: the **installer append
step** (T2, the only new code that *writes* the file), and the three
**consumer migrations** — `research` (T3, a clean rename of an existing
prompt-only read), `architect` (T4, a new read plus the loose-file→per-effort-folder
shift), and `product-engineering` (T5, a new read, file-per-slug). Each leaf
adds its pack's `references/agentbundle-layout.md` schema doc, its `[pack.layout]`
default, the security rails in its skill body, and its version bump. A final
housekeeping task (T6) adds the `.gitignore` entry, confirms self-host stays
clean, and runs the observable smoke.

The riskiest part is the **manifest contract bump** (T1) — a version bump trips
lexical version-compare bugs and stale assertions in CI-ungated test roots, so the
full `agentbundle` package pytest runs by hand. The second risk is that the
security control is **prose, not code** (the reader is prompt-only): T3–T5 must
carry the realpath / reject-`..` / surface / untrusted-origin rails verbatim
enough that `rg` and the smoke can verify them, generalising the rail
`research-project-start` already takes.

**Per-pack defaults (settled at PLAN, pre-EXECUTE review):** all three consumers
default to **user** scope but their output is per-repo, so none has a sensible
*absolute* user default. Each therefore declares only `[pack.layout.repo]` and
**omits `[pack.layout.user]`** (user-scope append is a no-op; the commented
placeholder lives in the schema doc as adopter guidance). Repo defaults:
`research` → `.context/research` (gitignored scratch — honours research's
"never the committed tree" posture); `architect` → `docs/design` (its first
scan-target today); `product-engineering` → `docs/product`.

**Sequencing constraint:** T3, T4, and T5 each append to the single
`docs/product/changelog.md`, so they are **not** file-disjoint and must merge
**sequentially** — no parallel implementer wave (the only shared file; each
otherwise touches its own pack dir + its own guides). T6's self-host / AC12
`find` gates also require T3–T5's `make build` projections to have landed first.

The spec/plan first landed in a **governance-docs PR** (#359); T1–T6 below were
then **implemented** in the follow-on PR (this one), which also carries the
pre-EXECUTE-review refinements recorded in the changelog. All six tasks are done;
every AC is checked.

## Constraints

- **RFC-0040 / ADR-0030** — the file contract, two-location resolution,
  anchor-by-location, prompt-only read, install-time append (never create / never
  overwrite), scope-keyed `[pack.layout]`, clean rename / no alias.
- **ADR-0029 / Charter Principle 3** — reading is a prompt-only habit; no runtime
  reader/engine/index/daemon. Only the install-time append is code.
- **ADR-0021** — `pack.toml` is the metadata source of truth; `[pack.layout]`
  lands there, not in a parallel config.
- **RFC-0035** — namespacing + shipped-placeholder delivery is the precedent for
  the `references/agentbundle-layout.md` doc; it is **not** a prompt-only-read
  precedent (that's ADR-0029).
- **Repo memory — contract-bump test traps:** every manifest/contract version bump
  must run the full package pytest by hand (`"0.10" < "0.8"` lexical bugs; stale
  assertions in CI-ungated roots).
- **Self-host projection** — skill sources live under `packs/<pack>/.apm/…`; edit
  there, then `make build`. Never edit `.claude/skills/…` directly.

## Construction tests

Most tests live per-task below. Cross-cutting:

- **Integration:** the AC16 observable smoke — one consumer end-to-end against a
  hand-written repo-root `agentbundle-layout.toml` (resolve + surface + topic
  folder + Ask-first on a hostile `parent`), plus `agentbundle install <pack>`
  against an existing layout file (append / never-overwrite / never-create).
- **Manual verification:** the smoke is recorded in the implementing PR
  description; a passing grep does not substitute for exercising the skills.

## Design (LLD)

### Design decisions

- **One file, `[<pack>]` tables, `parent`-as-base.** Chosen over per-pack files
  and flat prefixed keys; the table is the per-pack scope + per-table override
  unit a prompt-only reader handles cleanly. Traces to: AC1, AC2 · no `contracts/`.
- **Anchor by file location, not ambient cwd.** Repo-file `parent` is
  repo-relative (portable across clones); user-file `parent` is absolute (a
  user-scope skill runs from arbitrary cwds). Traces to: AC3, AC4.
- **Reading prompt-only, writing install-time only.** The security control is
  therefore prose acceptance criteria in skill bodies, not a code jail. Traces to:
  AC12, AC13–AC15.
- **Append-if-exists / never-create / never-overwrite,** sourced from scope-keyed
  `[pack.layout]`. The installer never imposes a config file; once the file exists
  every later install keeps it current. Traces to: AC9, AC10.
- **Clean rename, no alias** — `research-layout.toml` is undistributed. Traces to:
  AC5, AC17.

### Data & schema

- **`agentbundle-layout.toml`** (adopter-owned, never shipped): `[research]`,
  `[architect]`, `[product-engineering]` tables, each a single `parent` string.
  Repo-root form repo-relative; user form absolute / `~`-anchored.
- **`pack.toml` `[pack.layout]`** (shipped manifest metadata): optional table with
  optional `.repo` / `.user` sub-tables; each declares the section inline or points
  at a within-pack `agentbundle-layout.toml` template. Added to
  `pack.schema.json` as an optional property; validated by `validate_pack_metadata`.
  Traces to: AC10 · `pack.schema.json`.
- **`references/agentbundle-layout.md`** (shipped, per pack): documents `parent`,
  default base, per-unit folder shape, posture. Traces to: AC8.

### Interfaces & contracts

- **The file contract** is a prompt-only convention carried in the three consumer
  SKILL.md bodies and their schema docs — no `contracts/<type>/` file.
- **The manifest contract** (`pack.schema.json`) is the one versioned surface that
  moves; its version field bumps per the contract-bump discipline. Traces to: AC10.
- **Installer surface:** `_append_layout_section(plan.root, plan.scope, pack
  metadata, …)`, peer to `_append_install_marker`, called from the Step-11
  per-scope loop. Traces to: AC9, AC11.

### Failure, edge cases & resilience

- **`..`-escaping or symlinked `parent`:** reject `..`, realpath-resolve, surface —
  never follow out of the intended root silently (AC13, AC14).
- **Repo-root-sourced out-of-tree `parent`:** untrusted-origin → Ask-first confirm
  before writing (AC15).
- **Layout file absent at install:** the append is a no-op (never create) (AC9).
- **`[<pack>]` already present at install:** left untouched (never overwrite) (AC9).
- **Hostile `[pack.layout]` default** containing `"`, `]`, newline, `../`:
  round-trips intact + well-formed through `_emit_basic_string` + `tomllib`
  (AC11).
- **Empty matrix of consumers** (a pack with no adopter section): falls back to the
  pack's own default — graceful degradation (AC1, AC6, AC7).

### Quality attributes (NFRs)

- **Security:** AC13–AC15 (confinement, realpath, untrusted-origin) + AC11
  (injection-safe emit, path-jailed write). The prompt-only boundary makes
  AC13–AC15 goal-based / manual-QA, not unit tests.
- **Operability:** the append is idempotent (re-running install never duplicates or
  clobbers a section).

### Dependencies & integration

- No new dependency. Reuses `_append_install_marker` pattern,
  `config._emit_basic_string`, `safety.write_jailed`, and the existing
  prompt-only-read shape from `research-project-start`. `pack.schema.json` +
  `validate_pack_metadata` are the only versioned surfaces touched.

> **Rollout & deployment** — see [`## Rollout`](#rollout).

## Tasks

### T1: `[pack.layout]` manifest extension validates

**Depends on:** none

**Touches:** `packages/agentbundle/agentbundle/_data/pack.schema.json`,
`packages/agentbundle/agentbundle/_data/adapter.toml`,
`docs/contracts/adapter.toml`, `docs/contracts/pack.schema.json`,
`packages/agentbundle/agentbundle/build/main.py`,
`packages/agentbundle/tests/**`,
`packages/agentbundle/agentbundle/build/tests/**` (4 of the 5 `== "0.15"`
contract-version assertions live in this second, CI-ungated test root)

**Tests:**
- Goal-based: `validate_pack_metadata` accepts a `pack.toml` carrying
  `[pack.layout]` with `.repo` / `.user` sub-tables (inline section and
  template-pointer forms both validate); rejects a malformed `[pack.layout]`
  (e.g. wrong type for `parent`). Verifies AC10.
- Goal-based: the manifest schema / contract version field is bumped and asserted;
  **the full `agentbundle` package pytest is run by hand** (both test roots —
  `packages/agentbundle/tests/` and `…/agentbundle/build/tests/`) to catch lexical
  version-compare and stale-assertion traps. Verifies AC10.

**Approach (version field settled):** the governing field is the `adapter.toml`
`[contract] version` → `SPEC_VERSION` (the umbrella manifest/projection contract;
direct precedent — the enriched-pack-manifest extension, contract v0.14, bumped this
same field). Bump it **`"0.15"` → `"0.16"`** in *both* byte-identical copies
(`_data/adapter.toml` and `docs/contracts/adapter.toml`, drift-gated by
`BundledCopiesMatchTests`) with a dated ledger comment citing this spec.
- Add `[pack.layout]` to `pack.schema.json` (both copies) as an optional `object`
  property under `pack.properties` with optional `.repo` / `.user` sub-tables, each
  allowing a `parent` string and/or a template-path string. The change is purely
  additive (`pack` has no `additionalProperties: false`).
- Leave the **stale install-gate enum** (`["0.2","0.3","0.6"]`) and each shipped
  pack's `[pack.adapter-contract] version` **untouched** — the runtime gate is
  major-only, so a 0.x pack declaring `[pack.layout]` still validates; re-arming the
  enum would be an out-of-scope behaviour change.
- Update the 5 exact-string `== "0.15"` assertions: `tests/unit/test_contract_v0_3_schema.py`
  (+ its ledger comment), `build/tests/test_contract.py`, `build/tests/test_adapter_gemini.py`,
  `build/tests/test_adapter_kiro_ide.py`, `build/tests/test_adapter_cursor.py`. (The
  `>=`-tuple assertions in `test_contract_v07/v08/scope.py` are numeric and safe.)
- Run the full `agentbundle` package pytest by hand in **both** test roots.

**Done when:** `validate_pack_metadata` accepts/rejects per the tests, the version
bump is asserted, and the full package pytest is green in both roots.

### T2: Installer `_append_layout_section` (append-if-exists / never-create / never-overwrite)

**Depends on:** T1

**Touches:** `packages/agentbundle/agentbundle/commands/install.py`,
`packages/agentbundle/tests/**`

**Tests (TDD):**
- Round-trip a `[pack.layout]` default containing `"`, `]`, newline, and `../`
  through `config._emit_basic_string` + `tomllib`; assert the parsed `parent` is
  intact and the emitted TOML is well-formed. Verifies AC11.
- Never-overwrite: given a layout file with an existing `[<pack>]` section, the
  append leaves it byte-identical. Verifies AC9.
- Never-create: given **no** layout file at the scope location, the append writes
  nothing. Verifies AC9.
- Scope-keyed selection: a repo-scope append uses the `[pack.layout.repo]`
  (repo-relative) default; a user-scope append uses the `[pack.layout.user]`
  (absolute / placeholder) default. Verifies AC10.
- Jailed write — **modelled on `_append_install_marker`, not re-derived**: repo
  scope `root=<repo>`, top-level `relpath`, `allowed_prefixes=None`; user scope
  `root=<home>`, `relpath=".agentbundle/agentbundle-layout.toml"`,
  `allowed_prefixes` = the adapter's `allowed-prefixes.user` list. A
  **user-scope-write-succeeds** test exercises this against a real prefix list
  (not merely the `TypeError`-when-omitted rail). Verifies AC11.
- Re-emit type-validation: feed a tampered existing section (`parent = 42`,
  `parent = ["x"]`) and assert it is dropped/coerced before re-emit, not crashed
  on — mirroring `_append_install_marker`'s parsed-field hardening. Verifies AC11.
- Symlink fails-closed: when the layout *file path itself* is a symlink escaping
  `root`, the append's `write_jailed` → `assert_under` realpath-resolve raises
  `PathJailError` (never follows the link). Verifies AC11/AC14.

**Approach:**
- Add `_append_layout_section`, modelled on `_append_install_marker`'s upsert:
  read the existing file (if any) via `tomllib`, **type-validate the parsed
  `[<pack>]`/`parent` values**, check for `[<pack>]`, append the scope-keyed
  default only if the file exists and the section is missing, emit via
  `config._emit_basic_string`, write via `safety.write_jailed` with the
  marker-mirrored per-scope jail contract (repo: top-level relpath, no prefixes;
  user: `root=<home>` + `.agentbundle/` relpath + `allowed-prefixes.user`, via
  `safety.user_state_path`).
- Call it from the Step-11 per-scope loop alongside `_append_install_marker`.

**Done when:** all five construction tests pass and the Step-11 loop invokes the
step per scope.

### T3: `research` migrates to `[research]` (clean rename, no alias)

**Depends on:** T1

**Touches:** `packs/research/.apm/skills/research-project-start/**`,
`packs/research/pack.toml`, `packs/research/.claude-plugin/plugin.json`,
`docs/guides/research/**`, `docs/product/changelog.md`

**Tests:**
- Goal-based: `rg` against `research-project-start/SKILL.md` names
  `agentbundle-layout.toml`, the `[research]` table, the two-location
  repo-overrides-user read, anchor-by-location, the scratch default, and the
  resolve-then-surface order; **no `research-layout.toml` reference survives** in
  the body or the research guides. Verifies AC5, AC1–AC4, AC17.
- Goal-based: the security rails (realpath / reject-`..` / surface /
  untrusted-origin Ask-first) are present in the body. Verifies AC13–AC15.
- Goal-based: `references/agentbundle-layout.md` exists and names `[research]`,
  the scratch default, and the `<YYYY-MM-DD>-<topic-slug>/` folder shape; `research`
  is 0.5.0 in `pack.toml` + `plugin.json`. Verifies AC8, AC18.

**Approach:**
- Rewrite the "Where the project lives" section to read `[research]` from
  `agentbundle-layout.toml`; add the `[pack.layout.repo]` / `[pack.layout.user]`
  default to `research/pack.toml`; add the `references/` schema doc; update the
  reference / how-to / tutorial guides; add the changelog entry; bump 0.4.0→0.5.0;
  `make build`.

**Done when:** the greps pass, no `research-layout.toml` survives, and `make build`
leaves the tree clean.

### T4: `architect` becomes a consumer with a per-effort folder

**Depends on:** T1

**Touches:** `packs/architect/.apm/skills/architect-design/**`,
`packs/architect/pack.toml`, `packs/architect/.claude-plugin/plugin.json`,
`docs/guides/architect/**`, `docs/product/changelog.md`

**Tests:**
- Goal-based: `rg` against `architect-design/SKILL.md` names the `[architect]`
  read, the per-effort `<parent>/<topic-slug>/` folder, and the existing
  scan-then-elicit (`docs/design/`→`design/`→`architecture/`→`docs/`) as the
  **default** when no section resolves; the security rails are present. Verifies
  AC6, AC1–AC4, AC13–AC15.
- Goal-based: `references/agentbundle-layout.md` exists and documents `[architect]`,
  the scan default, the per-effort folder, and the file→folder shift; `architect`
  version bumped in `pack.toml` + `plugin.json`. Verifies AC8, AC18.

**Approach:**
- Replace the every-run scan-and-offer with: read `[architect]` → anchor → resolve
  + surface → create `<parent>/<topic-slug>/`; the scan-then-elicit becomes the
  no-section default. Add the `[pack.layout]` default, the schema doc, the guide
  updates, the changelog entry, the version bump; `make build`.

**Done when:** the greps pass, the file→folder shift is documented, and `make build`
leaves the tree clean.

### T5: `product-engineering` becomes a consumer (file-per-slug)

**Depends on:** T1

**Touches:** `packs/product-engineering/.apm/skills/frame-intent/**`,
`packs/product-engineering/.apm/skills/align-value-stream/**`,
`packs/product-engineering/pack.toml`,
`packs/product-engineering/.claude-plugin/plugin.json`,
`docs/guides/product-engineering/**`, `docs/product/changelog.md`

**Tests:**
- Goal-based: `rg` against `frame-intent` + `align-value-stream` SKILL.md names the
  `[product-engineering]` read, the `<parent>/intents/<slug>.md` /
  `<parent>/rollups/<slug>.md` file-per-slug shape (default `parent = docs/product`),
  and the security rails; `rg` confirms `decompose-intent` still pins
  `docs/product/briefs/`. Verifies AC7, AC1–AC4, AC13–AC15.
- Goal-based: `references/agentbundle-layout.md` exists and documents
  `[product-engineering]`, the `docs/product` default, and the file-per-slug shape;
  `product-engineering` version bumped. Verifies AC8, AC18.

**Approach:**
- Make `frame-intent` and `align-value-stream` resolve `[product-engineering]` →
  anchor → resolve + surface → write file-per-slug under `intents/` / `rollups/`;
  leave `decompose-intent`'s briefs pinned. Add the `[pack.layout]` default, the
  schema doc, the guide updates, the changelog entry, the version bump; `make build`.

**Done when:** the greps pass, briefs stay pinned, and `make build` leaves the tree
clean.

### T6: Self-host housekeeping + observable smoke

**Depends on:** T2, T3, T4, T5

**Touches:** `.gitignore`

**Tests:**
- Goal-based: `rg -F 'agentbundle-layout.toml' .gitignore` hits in the
  install-time-scratch section; the self-host drift gate (`make build-check` /
  `build/self_host.py`) is clean after a consumer skill is exercised in the
  catalogue. Verifies AC17.
- Goal-based (cross-cutting): across all three consumer skill directories,
  `find packs/{research,architect,product-engineering}/.apm/skills \( -name '*.py'
  -o -name '*.sh' \)` (grouped so `-print` binds both branches) returns nothing
  that reads or resolves `agentbundle-layout.toml` (the only file-touching code is
  the installer append), and `rg` confirms each body frames resolution as
  prompt-driven. Verifies AC12.
- Manual QA: one consumer end-to-end against a hand-written repo-root
  `agentbundle-layout.toml` — topic folder lands under the resolved `parent`, the
  absolute path is surfaced, a hostile/out-of-tree `parent` triggers Ask-first;
  `agentbundle install <pack>` against an existing layout file appends `[<pack>]`,
  never overwrites, never creates when absent. Recorded in the PR description.
  Verifies AC16.

**Approach:**
- Add `agentbundle-layout.toml` to `.gitignore` beside `.adapt-install-marker.toml`;
  run the smoke and record it.

**Done when:** the `.gitignore` entry is present, self-host is clean, and the PR
description records the smoke observations.

## Rollout

- **Delivery:** the implementing PR is additive and reversible — three skill-body
  edits, one installer step, one optional manifest table. The one **behaviour
  change** is `architect`'s loose-file → per-effort-folder output; it is additive
  (a folder around what was a file), `architect` is user-scope, and the schema doc
  + changelog document it.
- **Irreversible:** none. No data migration, no published event. The
  `research-layout.toml` → `[research]` rename is a clean rename of an undistributed
  file (no adopter holds the old name).
- **Deployment sequencing:** T1 (manifest schema) must land before any pack
  declares `[pack.layout]` (T3–T5) and before the installer reads it (T2) — `make
  build` / `validate` would otherwise reject the new table. Within the implementing
  PR, T1 → {T2, T3, T4, T5} → T6.
- **External-system integration:** none.

## Risks

- **Contract-bump traps (T1).** A manifest version bump trips lexical
  version-compare bugs and stale assertions in CI-ungated test roots. Mitigation:
  settle the governing version field first, run the full package pytest by hand in
  both test roots.
- **Prose-not-code security (T3–T5).** The confinement / realpath / untrusted-origin
  controls are skill-body prose, weaker than a code jail and dependent on the
  reviewer pass. Mitigation: carry the rails verbatim enough for `rg` + the smoke to
  verify; security-reviewer pass at spec and diff stage.
- **`architect` behaviour-change surprise.** Current users get a folder where they
  had a file. Mitigation: documented in the schema doc + changelog; additive, not
  destructive.
- **Self-host drift (T6).** A contributor exercising a consumer skill writes a
  repo-root `agentbundle-layout.toml`. Mitigation: the `.gitignore` entry; the gate
  honours gitignore.

## Changelog

- 2026-06-22: initial plan (governance-docs PR; T1–T6 are the implementing PR).
- 2026-06-22: implementing-PR pre-EXECUTE review refinements (no behaviour change
  vs RFC-0040 — all within its optional-sub-table latitude): settled the version
  field as `adapter.toml` `[contract] version` 0.15→0.16 (T1); recorded that all
  three consumers omit `[pack.layout.user]` (no sensible absolute default) so the
  commented placeholder is schema-doc guidance only, never installer-emitted
  (resolves the net-new-emit-shape concern); fixed per-pack repo defaults
  (`.context/research` / `docs/design` / `docs/product`); added the symlink-target
  fails-closed test (T2) and the second test root to T1 Touches; clarified AC11/AC15
  (append type-validates but never path-confines `parent`); scoped AC17's
  rename-sweep to live consumer surfaces, exempting the frozen `research-project-mode`
  spec/plan + its `docs/specs/README.md` row.
