# Plan: adapt-to-project

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The implementation is **schema first, dep-gate second, install handoff
third, skill body fourth, fixture+matrix last** — same order as before
the RFC-0004 reconciliation, but every task that touches an on-disk
artifact now operates per-scope. The canonical `.adapt-discovery.toml`
shape lives in code (the new `AdaptDiscovery` dataclass in `config.py`
with typed `Finding` entries and a user-scope-rejects-`[markers]`
invariant) before the two consumers flip to it. The marker regex
unifies on `[a-z][a-z0-9-]*` at substitution; a sibling-spec
amendment to `distribution-adapters/spec.md` widens RFC-0004's
*marker-refusal* grep symmetrically so user-scope packs cannot bypass
the rail with lowercase-hyphen markers. The install-gate enforcement
of the existing `[pack.dependencies.required]` schema field lands as
a single function reading **both** state files. The three addon
manifests gain `[[pack.dependencies.required]]` and `[pack.install]`
(default-scope = repo, allowed-scopes = ["repo"]). The CLI's `install`
subcommand grows the per-scope marker-file append + chained
in-process `adapt.run` call. The core pack's `session-start.sh` walks
**both** marker locations. The skill body documents the dual-scope
reads and the per-scope path-jail discipline.

The riskiest part is the **schema migration's blast radius** —
three consumers (CLI, self-host, the repo's own root
`.adapt-discovery.toml`) move in lockstep, and the dual-scope rail
ripples into install, adapt, the session-start hook, and the
sibling-spec marker-refusal grep amendment.

The second risk is **testability of the LLM-driven writes at user
scope.** v1 has no user-scope-eligible packs (all four shipped packs
lock `allowed-scopes = ["repo"]` per RFC-0004), so most user-scope
matrix rows in T14 reduce to synthetic fixtures exercising the
plumbing. This is consciously deferred — RFC-0004 §
*Drawbacks* explicitly flags the absence of a real user-scope pack
as out of scope until the APM/Claude-plugins adapter parity work
lands.

The third risk is **co-locating skill + hook tests under CLI tests**
— the prior reviewer flagged this; the deferral comment headers
remain. A future spec introduces a pack-level test harness.

## Constraints

- **[RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md)**
  drives the four classes of change and the step-gated discipline.
- **[RFC-0004](../../rfc/0004-install-scope-per-pack.md)** sources
  the install-scope dimension. The follow-on flagged at RFC-0004
  *Drawbacks* § *`adapt-to-project` discovery doubles its artifact
  surface* is this spec.
- **[`docs/specs/agent-spec-cli/spec.md`](../agent-spec-cli/spec.md)**'s
  rails and dual-scope `adapt` AC at lines 609-621 are inherited.
- **[`docs/specs/self-hosting/spec.md`](../self-hosting/spec.md)**
  AC12 is amended additively via Changelog only.
- **[`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md)**
  owns the `pack.toml` schema (including `[pack.dependencies]` and
  `[pack.install]`) and the `validate`-time marker-refusal grep
  per RFC-0004 line 272 — **this plan amends one AC** to widen
  that grep to also match the canonical lowercase-hyphen syntax
  (the only structural cross-spec edit this plan ships).
- **RFC-0003**'s eleven-subcommand freeze holds.

## Construction tests

Most tests live per-task below. Cross-cutting:

- **Schema-migration regression (TDD, cross-consumer + per-scope).**
  Both consumers refuse legacy shapes with prefixed stderr; both
  accept canonical at their respective scopes; user-scope file with
  `[markers]` is refused.
- **Install→adapt chain integration (TDD).** Tests for the marker
  write at each scope, the chained in-process `adapt`, and the two
  failure modes (missing repo discovery file; malformed discovery
  file).
- **Idempotency at byte level (TDD).** Re-run produces zero diff
  at both scopes when both marker files are absent.
- **Cross-spec marker-refusal grep amendment (TDD).** The amended
  grep in `distribution-adapters/spec.md` matches both UPPER_SNAKE
  and lowercase-hyphen forms.

**Integration tests:** `tests/integration/test_brownfield_adapt.py`,
`tests/integration/test_install_adapt_chain.py`,
`tests/integration/test_pack_dependencies_gate.py`.

**Manual verification:** T14's matrix at
`docs/specs/adapt-to-project/notes/manual-qa-matrix.md`.

## Tasks

### T1: `AdaptDiscovery` typed schema in `config.py`

**Depends on:** none

**Verification mode:** TDD.

**Tests:**
- `test_canonical_schema_parses_repo_scope` — fixture with
  `discovery-schema-version`, `[markers]`, and `[[findings.*]]`
  parses into a typed `AdaptDiscovery` with `Finding` entries.
- `test_canonical_schema_parses_user_scope` — fixture with
  `discovery-schema-version` + `[[findings.*]]` only (no
  `[markers]`) parses; `AdaptDiscovery.markers` is an empty dict.
- `test_user_scope_with_markers_refused` — fixture with
  `discovery-schema-version`, `[markers]`, and `[[findings.*]]`
  loaded with `scope="user"` raises `ConfigError(
  "user-scope .adapt-discovery.toml may not contain a [markers] table; markers are repo-only per RFC-0004")`.
- `test_legacy_accepted_refused`, `test_legacy_adapt_refused`,
  `test_unknown_schema_version_refused`,
  `test_invalid_finding_kind_refused`,
  `test_finding_id_deterministic`,
  `test_finding_id_input_includes_pack_and_kind`,
  `test_findings_round_trip_preserves_fields` — unchanged from
  prior pass.

**Approach:**
- In `config.py` add `@dataclass(frozen=True) Finding` and
  `@dataclass AdaptDiscovery` per the prior pass.
- `load_adapt_discovery(path, *, scope: Literal["repo", "user"]) -> AdaptDiscovery`
  — the new `scope` kwarg drives the user-scope `[markers]` refusal.
  Default `scope="repo"` for callers that don't care (preserves
  back-compat for existing call sites).
- `finding_id_for(pack, kind, source_paths, dest_paths)` returns
  the canonical SHA-1 prefix per spec.

**Done when:** all nine tests pass; mypy/lint clean.

### T2: CLI consumer migrates; marker regex widens; stderr prefix

**Depends on:** T1

**Verification mode:** TDD.

**Tests:**
- `test_markers_table_substitutes`,
  `test_legacy_accepted_refused_with_prefix`,
  `test_unknown_schema_version_refused_with_prefix`,
  `test_lowercase_hyphen_markers_match`,
  `test_upper_snake_markers_no_longer_substituted` — unchanged
  from prior pass.

**Approach:**
- `commands/adapt.py`: `_MARKER_RE` widens to `<adapt:([a-z][a-z0-9-]*)>`;
  `_LEGACY_UPPER_RE` warns once on UPPER_SNAKE matches; replace
  `discovery.get("accepted", {})` with `AdaptDiscovery.markers`.
  Caller passes `scope="repo"` to `load_adapt_discovery` for the
  CLI's primary load (the CLI's dual-scope walk handles user-scope
  reads via a separate call with `scope="user"`).
- Migrate `tests/fixtures/adapt/.adapt-discovery.toml` and
  test_adapt_cmd.py `OWNER → owner`.

**Done when:** all five tests pass; pre-existing tests pass.

### T3: Self-host consumer migrates; regex narrows; stderr prefix

**Depends on:** T1

**Verification mode:** TDD.

**Tests:** unchanged from prior pass (single-scope; self-host is
repo-only by definition).

**Approach:** `self_host.py` replaces in-place `tomllib.loads` +
`discovery_data.get("adapt", {})` with the shared loader; narrows
`ADAPT_MARKER_RE` to `[a-z][a-z0-9-]*`; caller prefix `self-host: `.

**Done when:** four tests pass; pre-existing tests pass.

### T4: Repo's own `.adapt-discovery.toml` migrates

**Depends on:** T3

**Verification mode:** goal-based check.

**Tests:** `make build-self` exit 0 + clean `git status`;
`make build-check` exit 0; `grep -F "[markers]"` hits.

**Approach:** rewrite repo-root `.adapt-discovery.toml` from `[adapt]`
to `discovery-schema-version` + `[markers]`.

**Done when:** all three one-liners hit.

### T5: Install-gate enforcement, dual-state-file union resolution

**Depends on:** none

**Verification mode:** TDD.

**Tests:**
- `test_install_refuses_missing_required` — empty both state files;
  installing addon refuses with the spec-mandated stderr.
- `test_install_proceeds_when_required_at_repo_scope` —
  repo-scope state lists `core 0.1.0`; install proceeds.
- `test_install_proceeds_when_required_at_user_scope` —
  user-scope state lists `core 0.1.0`; install proceeds (the
  union rule honours `core at any scope`).
- `test_install_refuses_out_of_range_required` — installed core
  is `0.0.5`; addon requires `^0.1`; refused.
- `test_install_refuses_unsupported_range_grammar` — addon
  declares `version = "~0.1"`; refused with the named stderr.
- `test_install_no_required_table_proceeds` — pack with no
  `[pack.dependencies.required]` installs without gating.

**Approach:**
- New helper in `commands/install.py`:
  `validate_dependencies_required(pack_toml, *, repo_state,
  user_state) -> None`. Resolves the required entries against the
  union of both state files; raises on first failure.
- SemVer-range grammar: exactly the regex `^\^([0-9]+)\.([0-9]+)$`;
  `^X.Y` matches `>= X.Y.0 AND < (X+1).0.0`.
- Wire the check into `install` before any file write.

**Done when:** all six tests pass.

### T6: Addons migrate to conforming dependencies + explicit scope

**Depends on:** T5

**Verification mode:** TDD + goal-based.

**Tests:**
- Schema validator accepts each post-migration addon manifest
  (the validator already enforces `[pack.dependencies.required]`
  shape; RFC-0004's `[pack.install]` schema bump is owned by
  `distribution-adapters/spec.md` and applies to v0.2 packs —
  addons declare `[contract] version = "0.2"` in this PR per the
  sibling spec's amendment).
- `grep -L '^recommends ' packs/{governance-extras,user-guide-diataxis,monorepo-extras}/pack.toml`
  lists all three (line-anchored grep, no false positive on
  comments).
- `grep -c 'pack = "core"' …` hits in each.
- `grep -c 'allowed-scopes = \["repo"\]' …` hits in each (the
  explicit RFC-0004 declaration).
- `grep -c 'version = "0.2"' packs/{core,governance-extras,user-guide-diataxis,monorepo-extras}/pack.toml`
  hits in all four (the `[pack.adapter-contract]` bump
  required for `[pack.install]` to be honoured per
  `distribution-adapters/spec.md`).

**Approach:**
- For each addon's `pack.toml`:
  - Remove `recommends = ["core"]`.
  - Add `[[pack.dependencies.required]]` with `catalogue =
    "agent-ready-repo"`, `pack = "core"`, `version = "^0.1"`.
  - Add `[pack.install]` with `default-scope = "repo"` and
    `allowed-scopes = ["repo"]`.
  - Add `[pack.adapter-contract]` with `version = "0.2"` —
    `[pack.install]` is a v0.2-only field per
    `distribution-adapters/spec.md`; without the bump the new
    table is silently ignored by the schema validator.
- For `packs/core/pack.toml`:
  - Add `[pack.adapter-contract] version = "0.2"`.
  - Add `[pack.install] default-scope = "repo"` and
    `allowed-scopes = ["repo"]`. (Core ships no
    `[pack.dependencies.required]` — it is the root.)

**Done when:** schema tests pass; four grep one-liners hit.

### T7: `--values-from` shape widening; refuses ambiguous files

**Depends on:** T1

**Verification mode:** TDD.

**Tests:**
- `test_accepts_markers_table`, `test_accepts_values_table`,
  `test_accepts_flat_table_skipping_discovery_keys`,
  `test_refuses_files_with_both_markers_and_values` — unchanged
  from prior pass.
- `test_accepts_user_scope_file_yielding_empty` — passing a
  user-scope `.adapt-discovery.toml` (no `[markers]`, no
  `[values]`) returns an empty mapping; no error.

**Approach:** `load_values_from`:
- Refuse on both `[markers]` and `[values]` present.
- Try `[markers]`, then `[values]`, then flat-fallback skipping
  `discovery-schema-version`, `findings`, `marker-schema-version`.

**Done when:** five tests pass; pre-existing tests pass.

### T8: Per-scope install marker write + chained `adapt.run`

**Depends on:** T2, T5, T7

**Verification mode:** TDD.

**Tests:**
- `test_install_writes_marker_at_repo_scope_root` — repo-scope
  install writes a file at `<repo>/.adapt-install-marker.toml`
  containing a `[[packs-installed]]` entry for the installed
  pack. The location *is* the scope; no `scope` field is read
  or asserted.
- `test_install_writes_marker_at_user_scope_root` — user-scope
  install writes a file at
  `~/.agent-ready/.adapt-install-marker.toml` containing a
  `[[packs-installed]]` entry. Synthetic test pack with
  `allowed-scopes = ["user"]` and no seeds/hooks/markers (RFC-0004
  refusal rails honoured). No `scope` field is asserted.
- `test_install_marker_appends_atomically` — two sequential
  installs at the same scope produce two entries. (Atomic-rename
  protocol is preserved via `safety.write_jailed`'s
  `tmp + os.replace` primitive — the existing safety tests pin
  the protocol; this test pins the append shape.)
- `test_install_chains_adapt_in_process` — fixture pack has
  `<adapt:project-name>` markers; repo-scope
  `.adapt-discovery.toml` pre-populated with
  `project-name = "X"`; after install, projected files contain
  `X`. Patched `subprocess` confirms no subprocess call (in-process
  `adapt.run` honours *Never invoke an LLM*).
- `test_install_with_no_discovery_file_completes_zero` — empty
  repo; install exits 0; stderr has one line
  `adapt: no .adapt-discovery.toml at repo root; markers left unresolved`;
  marker file still written.
- `test_install_chained_adapt_failure_returns_nonzero_preserves_marker`
  — malformed `.adapt-discovery.toml`; install exits non-zero;
  stderr names the failure; marker file still on disk.
- `test_marker_added_to_gitignore_on_scaffold` — `agentbundle
  scaffold` lays down `.gitignore` containing
  `.adapt-install-marker.toml`.

**Approach:**
- `commands/install.py`: after successful install, compute union
  of pack-declared markers (only for repo-scope installs — markers
  are repo-only by rail) and newly-dropped companions; write the
  marker at the install's scope root via `os.replace` atomic
  rename.
- Invoke `agentbundle.commands.adapt.run` in-process (no
  subprocess) with `args.values_from =
  Path("<repo>/.adapt-discovery.toml")` regardless of install
  scope (markers are repo-only). The CLI's dual-scope walk in
  `adapt.run` handles both scopes' companions and pending reports
  via the existing agent-spec-cli AC.
- `agentbundle scaffold` template extends `.gitignore` with
  `.adapt-install-marker.toml`.

**Done when:** all seven tests pass; no `--no-adapt` flag is
added.

### T9: Session-start hook walks both scopes' install markers

**Depends on:** T8

**Verification mode:** TDD (shell fixture).

Tests live at
`packages/agentbundle/tests/hooks/test_session_start.sh` (with the
deferral comment header from the prior pass).

**Tests:**
- `test_repo_marker_only_emits_nudge` — only
  `<repo>/.adapt-install-marker.toml` present; stdout has one
  nudge line with `<K> = 1`.
- `test_user_marker_only_emits_nudge` — only
  `~/.agent-ready/.adapt-install-marker.toml` present; stdout
  has one nudge line with `<K> = 1`.
- `test_both_markers_emit_one_combined_nudge` — both present;
  stdout has one nudge line with `<K> = 2`, listing union of
  pack names lexicographically sorted.
- `test_no_markers_silent` — neither present; nudge line absent.
- `test_marker_and_patterns_both_emit` — knowledge block first,
  nudge line second.

**Approach:**
- `session-start.sh`: after the existing `patterns.jsonl` block,
  add a block that reads both `.adapt-install-marker.toml` paths
  via `python3 -c "import tomllib; ..."`; computes the union of
  pack names; emits one stdout line. Silent on absence.

**Done when:** five tests pass; `make build-check` green.

### T10: Brownfield fixture (repo + minimal user-scope plumbing)

**Depends on:** T5

**Verification mode:** goal-based check.

**Tests:**
- TOML parses for both scopes' fixture files.
- Every `pack.toml` validates.
- `pytest --collect-only` clean.

**Approach:** create
`packages/agentbundle/tests/fixtures/brownfield-adapt/` with:
- Repo-scope tree per the prior pass (pre-existing AGENTS.md,
  `AGENTS.upstream.md`, `DESIGN.md`, overlapping skills).
- Synthetic user-scope plumbing under
  `tests/fixtures/brownfield-adapt-user-home/.agent-ready/state.toml`
  and `.adapt-discovery.toml` (with `[[findings.*]]` only — no
  `[markers]`). Used by AC4's user-scope matrix rows as the
  synthetic fixture.
- `EXPECTED_TREE.md` documenting both scopes' post-adaptation
  state.

**Done when:** three one-liners hit.

### T11: Class-1 end-to-end integration test

**Depends on:** T2, T7, T10

**Verification mode:** TDD.

**Tests:**
- `test_class_one_end_to_end` — load brownfield fixture;
  hand-write `[markers]` into repo-scope `.adapt-discovery.toml`;
  invoke `agentbundle adapt --values-from
  <repo>/.adapt-discovery.toml`; assert post-state tree
  byte-identical to expected. Class 1 is repo-scope only.
- `test_idempotent_re_run` — second invocation produces zero new
  filesystem changes.

**Approach:** add `tests/fixtures/brownfield-adapt-expected/`.

**Done when:** both tests pass.

### T12: Schema-migration acceptance test (cross-consumer)

**Depends on:** T2, T3

**Verification mode:** TDD.

**Tests:** unchanged parametrised set across both consumers.

**Done when:** four tests pass.

### T13: Author skill body + grep tests + projection check

**Depends on:** T1, T2, T7, T8, T9

**Verification mode:** TDD (grep) + goal-based (projection).

**Tests** (five behaviour-pinning greps from AC1):
- `test_body_names_shell_out_command` — literal
  `agentbundle adapt --values-from <repo>/.adapt-discovery.toml`.
- `test_body_names_doctrinal_self_check` — literal
  `python3 -c "import tomllib; tomllib.loads(open('<path>').read())"`.
- `test_body_names_path_jail_rule` — literal
  `never write outside the adopter's per-scope jail`.
- `test_body_names_dirty_state_command` — `git status --porcelain`.
- `test_body_pre_flight_section_references_user_scope_state` —
  the body's *Pre-flight* section contains all three tokens
  `~/.agent-ready/`, `state.toml`, and `Tier-2` (any prose
  shape; behavioural pin on the read, not a verbatim path
  literal).
- Goal-based: projected `SKILL.md` byte-identical after
  `make build-self`; `make build-check` green.

Tests live at `packages/agentbundle/tests/skills/`.

**Approach:**
- Author full SKILL.md body at
  `packs/core/.apm/skills/adapt-to-project/SKILL.md`. Sections:
  1. *When to invoke* — after install, in the adopter's repo.
  2. *Pre-flight* — read both state files; consume both install
     markers if present; run `git status --porcelain` (repo) and
     content-hash divergence check (user-scope) per AC6; escalate
     per scope.
  3. *Class 1* — markers are repo-only; produce values into
     repo-scope `[markers]`; shell out to `agentbundle adapt
     --values-from <repo>/.adapt-discovery.toml`; doctrinal
     self-check.
  4. *Class 2* — companion merges, scope-aware (record in the
     scope of the companion).
  5. *Class 3* — discovery + restructuring; same-scope by default;
     cross-scope restructure escalates per AC23.
  6. *Class 4* — consolidation; scope-aware.
  7. *Closeout* — regenerate `.adapt-pending.md` per scope, fixed
     deterministic format.
  8. *Anti-patterns to refuse* — must contain the literal
     `never write outside the adopter's per-scope jail`.
- Run grep tests; run `make build-self`.

**Done when:** five grep tests pass; projection byte-identical.

### T14: Manual QA matrix execution (scope-aware)

**Depends on:** T13

**Verification mode:** mixed — (a) automation, (b) grep, (c)
transcript per AC4a's per-row split. See AC4a body for the
method-(a/b/c) taxonomy.

**Tests:**
- `docs/specs/adapt-to-project/notes/manual-qa-matrix.md` exists
  with the scope-aware matrix per AC4:
  - Repo-scope rows: (class 2 × {accept, edit, skip, decline}),
    (class 3 × {accept, edit, decline}), (class 4 × {accept,
    decline}). All carry method *(c)* deferred under AC4b until a
    real-adopter session; **Claude-simulated captures recorded
    inline as preparatory evidence** (authorised by AC4b's
    simulated-captures clause).
  - User-scope rows: same transitions; rows without an exercisable
    fixture (because v1 has no user-scope-eligible packs) are
    marked "v1 deferred per RFC-0004; verified by synthetic
    fixture against the user-scope plumbing in T10".
  - Cross-cutting: dirty-state-repo, dirty-state-user,
    idempotency, Tier-2-repo, Tier-2-user, cross-scope-restructure
    × {approve, decline}. *dirty-state-repo* and *Tier-2-repo*
    each carry **two AC4a pins** — method *(b)* on the skill body
    + method *(a)* on the detection primitive (the latter pinned
    by `tests/integration/test_adapt_preflight_detection.py`).

**Approach:** run sessions; capture artifacts. For rows where
real-adopter sessions aren't feasible in v1, record Claude-
simulated captures inline as preparatory evidence and keep AC4b
open against the real-adopter trigger.

**Done when:** matrix file populated with every row's verification
method declared and its artifact present (automation test, grep
test, or inline transcript — simulated transcripts count for AC4b
preparatory evidence, not for AC4a *(c)* closure).

### T15: Amend sibling specs (agent-spec-cli + self-hosting + distribution-adapters)

**Depends on:** T13

**Verification mode:** goal-based check.

**Tests:**
- `grep -F "[markers]" docs/specs/agent-spec-cli/spec.md` hits
  the amended `agentbundle adapt` AC.
- `! grep -F "accepted/declined entries" docs/specs/agent-spec-cli/spec.md`
  — removed phrase no longer appears.
- `grep -F "docs/specs/adapt-to-project/spec.md" docs/specs/agent-spec-cli/spec.md`
  hits (schema-authority pointer).
- `tail -25 docs/specs/self-hosting/spec.md | grep -F "2026-05-23: AC12 implementation migrates"`
  hits.
- AC12 body in self-hosting is byte-unchanged.
- **(new)** `grep -c '<adapt:\[a-z\]\[a-z0-9-\]\*>' docs/specs/distribution-adapters/spec.md`
  returns ≥ 2 (both line-342 prose AND the contract AC near
  line 759 are amended; the count is ≥ 2 because both
  occurrences must independently contain the widened pattern,
  whether via union regex or two separate grep declarations).
- **(new)** `docs/ROADMAP.md` contains an entry under the
  `distribution-adapters` per-spec section naming
  "Rail C grep widening to canonical syntax — paired with AC21
  of adapt-to-project" (the code-side widening deferral per
  AC21's carve-out).

**Approach:**
- `docs/specs/agent-spec-cli/spec.md` lines 473-479: in-place
  edit replacing the multi-line backticked phrase
  `and reads\n      \`.adapt-discovery.toml\` accepted/declined entries without writing to\n      it.`
  (note the leading `and `; the previous line ends `with a
  one-line diff summary,`) with
  `and reads the \`[markers]\` table in \`.adapt-discovery.toml\`\n      per docs/specs/adapt-to-project/spec.md, without writing\n      to it.`.
- `docs/specs/self-hosting/spec.md` Changelog: append
  `- 2026-05-23: AC12 implementation migrates from reading [adapt] to reading [markers] per docs/specs/adapt-to-project/spec.md; AC12 contract unchanged.`
- `docs/specs/distribution-adapters/spec.md`: amend **both
  occurrences** of the UPPER_SNAKE-only regex
  `<adapt:[A-Z_][A-Z0-9_]*>` to also match the canonical
  lowercase-hyphen form:
  - **Line 342** (descriptive prose under *Rail C → Grep
    semantics*) — update the documented regex.
  - **Line 759** (the Acceptance Criterion that pins Rail C; the
    contract-load-bearing occurrence).
  Implementation choice per amendment: regex union
  `<adapt:([A-Z_][A-Z0-9_]*|[a-z][a-z0-9-]*)>` or two separate
  grep passes. Both occurrences MUST be amended; widening line
  342 alone leaves the AC narrow and the contract bypassed.
- `docs/ROADMAP.md`: under the `distribution-adapters` per-spec
  section, add the open item
  `Rail C grep widening to canonical syntax — paired with AC21
  of adapt-to-project; code-side widening deferred when AC21
  amends only the spec text per its carve-out`.

**Done when:** all six one-liners hit; `git diff` of
self-hosting/spec.md confined to Changelog.

### T16: Update `docs/specs/README.md` and `docs/ROADMAP.md`

**Depends on:** T13

**Verification mode:** goal-based check.

**Tests:**
- `grep -F "adapt-to-project" docs/specs/README.md` hits the new
  Active-specs row.
- ROADMAP bullet replaced with `## adapt-to-project — drafted`
  section matching the format at `docs/ROADMAP.md:33`
  (`## self-hosting — Phase 1 shipped; Phase 2 pending`).
  Cross-refs to `self-hosting`, `agent-spec-cli`, **and RFC-0004**
  survive.
- `Last updated:` bumped.

**Approach:** as prior pass + add the RFC-0004 cross-ref.

**Done when:** three one-liners hit.

### T17: Cross-scope restructure non-execution + split-into-two prompt (AC23)

**Depends on:** T13

**Verification mode:** TDD (grep) + manual QA matrix row.

**Tests:**
- `test_body_names_split_into_two_prompt` — SKILL.md body
  contains the literal phrase
  `split into two same-scope operations` exactly once (the
  spec-mandated alternative offered when a cross-scope
  restructure is detected).
- `test_body_forbids_cross_scope_execution` — SKILL.md body
  contains the literal phrase
  `cross-scope restructure is never executed as a single move`.
- Manual QA matrix row in AC4a: *cross-scope-restructure ×
  decline* populated against the synthetic user-scope fixture.
  The *split-into-two* path is verified by code review against
  the SKILL.md body greps (no v1 fixture exercises both halves
  end-to-end; deferred to AC4b's enumeration with the
  user-scope-pack-arrives trigger).

**Approach:** add the cross-scope handling block under the
class-3 section of SKILL.md per the AC23 contract — detect
the scope crossing, offer the two-option prompt (decline /
split-into-two), never propose execute-as-single-restructure.

**Done when:** both greps hit; AC4a row populated.

## Rollout

Single PR. No flag-gating. The schema migration is atomic — all
three consumers + the repo's own discovery file + the three addons'
manifest fields + the cross-spec marker-refusal grep amendment flip
together.

`make build-check` catches drift between pack-side SKILL.md and the
projected copy. The CI gate is the final check.

## Risks

- **Schema rename + RFC-0004 reconciliation amplifies blast
  radius.** Mitigation: single-PR atomicity per the existing
  prefixed-stderr refusal as the migration path; no downstream
  artifacts ship yet.
- **Manual QA matrix has user-scope rows with no real fixture.**
  Mitigation: synthetic fixture under
  `tests/fixtures/brownfield-adapt-user-home/` exercises plumbing;
  acceptable per RFC-0004's explicit deferral of user-scope packs
  until APM/Claude-plugins parity work lands.
- **LLM-driven file writes at user scope could escape
  `allowed-prefixes`.** Mitigation: SKILL.md body documents
  per-scope jail rule (AC1 grep #3); CLI-side `allowed-prefixes`
  enforcement (`agent-spec-cli/spec.md` AC) is the structural
  gate; T14 matrix includes one user-scope escape attempt.
- **Cross-spec marker-refusal grep widening could regress
  distribution-adapters semantics.** Mitigation: T15 grep tests
  pin both grammars surviving; no other AC in
  distribution-adapters/spec.md is touched.
- **Install-marker race at user scope** — `~/.agent-ready/` is
  user-shared across projects, so a parallel `agentbundle install
  --scope user` in another terminal could race. Mitigation:
  `os.replace` atomic rename per AC19a; worst-case is one entry
  lost; documented in spec § Boundaries.
- **The dual-state-file Tier-2 detection (AC22) reads files the
  skill never writes.** Risk: the skill misreads user-scope state
  if the CLI hasn't run `init-state --migrate` yet. Mitigation:
  the skill detects v0.1 state files at user scope and surfaces a
  clear message naming `init-state --migrate` as the prereq; it
  does not attempt the migration itself.

## Changelog

- 2026-05-23: initial draft → 1st-pass-review fixes →
  2nd-pass-review fixes → **post-RFC-0004 rebase reconciliation**
  (per-scope schemas; dual-state-file Tier-2; cross-spec
  marker-refusal grep widening as T15 sub-task;
  cross-scope-restructure escalation as new T17; T6 adds
  `[pack.install]` declarations; T8 marker location per-scope;
  T9 walks both markers; AC count 20 → 23; task count 16 → 17).
- 2026-05-23: 4th-pass-review fixes (Blocker 1: AC21 now names
  both line-342 prose and line-759 AC occurrences in
  distribution-adapters/spec.md with `≥ 2` grep verification;
  Blocker 3: AC23 forbids cross-scope-restructure execution
  entirely, offers decline / split-into-two only; Concern 4:
  AC21 carve-out names code-side widening as deferred follow-on
  owned by distribution-adapters; Concern 8: AC22 v0.1 state-file
  sub-clause emits prereq message and continues; Concern 9: AC18
  (d) adds `[pack.adapter-contract] version = "0.2"` to all four
  packs; nits: scope field dropped from install marker schema,
  AC1 grep #5 → multi-token behavioural check, AC4 split into
  4a/4b with explicit deferral list, AC12 quote includes leading
  `and `, AC2 reconciles visible vs hashed finding-id encoding).
