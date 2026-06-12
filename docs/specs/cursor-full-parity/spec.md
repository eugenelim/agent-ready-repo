# Spec: cursor-full-parity

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0026](../../rfc/0026-cursor-full-parity-adapter.md) (the decision: add a native `cursor` full-parity adapter; the five projection decisions; the per-primitive projection table; the agent frontmatter mapping; the hook-event map; contract v0.10→v0.11 with **no** projection-mode-enum change; the two open questions deferred to this spike); [ADR-0015](../../adr/0015-cursor-full-parity-distribution-adapter.md) (the recorded decision); [ADR-0013](../../adr/0013-copilot-full-parity-user-scope-adapter.md) / [`copilot-full-parity`](../copilot-full-parity/spec.md) (the full-parity, user-scope, documented-tool-degradation template this follows); [ADR-0012](../../adr/0012-kiro-adapter-split.md) / [RFC-0022](../../rfc/0022-kiro-adapter-split.md) (the `.md`-agent + frontmatter-mapping + inline `_project_agent_as_md` shape Cursor's agent projection reuses); [RFC-0005](../../rfc/0005-user-scope-hook-support.md) (`merge-json` precedent); [ADR-0002](../../adr/0002-install-scope-per-pack-default-and-allowance.md) (per-pack scope default + allowance). Modifies [`packages/agentbundle/agentbundle/_data/adapter.toml`](../../../packages/agentbundle/agentbundle/_data/adapter.toml) (contract v0.10 → v0.11; new `[adapter.cursor]` block + `[adapter.cursor.scope]` + `[frontmatter-mapping."cursor-agent-frontmatter-v0.11"]`) — **dual-copy** into [`docs/contracts/adapter.toml`](../../contracts/adapter.toml) (byte-identical, per `test_contract_files_byte_identical`); the new adapter module [`packages/agentbundle/agentbundle/build/adapters/cursor.py`](../../../packages/agentbundle/agentbundle/build/adapters/cursor.py); its registration in [`adapters/__init__.py`](../../../packages/agentbundle/agentbundle/build/adapters/__init__.py); the two dispatch branches + imports in [`packages/agentbundle/agentbundle/commands/install.py`](../../../packages/agentbundle/agentbundle/commands/install.py); the new test module [`build/tests/test_adapter_cursor.py`](../../../packages/agentbundle/agentbundle/build/tests/test_adapter_cursor.py); the CI wiring in [`.github/workflows/build-check.yml`](../../../.github/workflows/build-check.yml); and stale version assertions in existing test roots. Amends [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md) (v0.10 → v0.11 Changelog entry) and the root [`AGENTS.md`](../../../AGENTS.md) Cursor-reader line if wording needs it.
- **Contract:** none <!-- no REST/event/RPC interface surface; the adapter contract (`adapter.toml`) is internal build-pipeline data, named in Constrained by above -->
- **Shape:** integration <!-- wiring the catalogue primitives to an external tool's (Cursor's) native `.cursor/*` surfaces; pulls dependencies & integration + interfaces & contracts + failure & resilience in the plan's LLD -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Scope: one PR, one contract bump.** The contract bump, the `[adapter.cursor]`
> block, the new frontmatter mapping, the scope table, the adapter module, the
> registration, the two install dispatch branches, the test module, the CI wiring,
> and the stale-assertion fixes all land in a **single PR** per the RFC-0004
> atomicity precedent inherited from `copilot-full-parity`. Splitting risks (a) the
> contract declaring `.cursor/…` projection with no adapter that writes there, or
> (b) `shipped_adapters_from_contract()` advertising `cursor` while the install
> resolver's dispatch raises `no … projection wired for adapter 'cursor'`.

## Objective

Make the catalogue project every primitive a Cursor adopter can consume — `skill`,
`agent`, `hook-body`, `hook-wiring`, `command` — to Cursor's native `.cursor/*` discovery
paths at **both** repo and user scope, so a Cursor adopter gets a complete, self-contained
`.cursor/` tree instead of silent degradation to "whatever Cursor reads from root
`AGENTS.md` and an incidentally co-installed `.claude/` tree." Cursor joins
claude-code / kiro / copilot / codex as a first-class adapter, reusing only existing
projection modes (no projection-mode-enum change), with documented degradation for the one
primitive Cursor cannot represent (the agent `tools:` allowlist).

**For the Cursor adopter installing `core` at repo scope:**
`agentbundle install --pack core --scope repo --adapter cursor .` today is impossible —
`cursor` is not a shipped adapter, so the install refuses up front. After this spec the
same command lands `core`'s skills at `.cursor/skills/<name>/` (straight directory copy),
its 4 reviewer/executor subagents at `.cursor/agents/<name>.md` (markdown + a Cursor-shaped
frontmatter via the `cursor-agent-frontmatter-v0.11` mapping, with the read-only reviewers
carrying `readonly: true`), its hook bodies at `.cursor/hooks/<name>.{sh,py}`, its
hook-wiring merged into `.cursor/hooks.json` (`{"version":1,"hooks":{<cursorEvent>:[…]}}`),
and its one command at `.cursor/commands/conventions-check.md` — five primitive types
projected, none dropped (Cursor honours commands, the second adapter after Claude Code to do
so).

**For the Cursor adopter installing a user-default pack at user scope:**
`agentbundle install --pack <pack> --adapter cursor` (user scope) lands the same `.cursor/*`
tree under `~/.cursor/…`, discovered globally by the Cursor app + CLI from outside any repo.
Because Cursor uses the **identical `.cursor/` prefix at both scopes** (unlike Copilot's
`.github/`→`~/.copilot/` divergence), the user-scope home is produced by the generic
user-root rooting — no Cursor-specific prefix-rewrite function is needed.

**Success for the read-only subagents on Cursor (the honest fidelity bound):** Cursor
subagents have **no per-agent tool allowlist**, so the source `tools:` list is dropped and a
`readonly: true` flag is derived for non-mutating agents (the 4 `core` reviewers and the 2
`research` retrieval subagents stay least-privilege; the `implementer` inherits all tools).
This degradation is **documented**, the same shape ADR-0013 accepted for Copilot.

**Success for the catalogue's adapter model:** `cursor` is **distribution-only** — it is
**not** added to `SELF_HOST_ADAPTERS`; this repo continues to self-host onto Claude Code +
Codex only, matching the Copilot and Kiro precedent.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines. *Always do*
applies without asking; *Ask first* requires human sign-off before proceeding;
*Never do* is a hard rule, even under time pressure.

### Always do

- **Reuse only existing projection modes.** Every Cursor primitive maps to an
  already-enumerated mode — the five standard primitives in the `[[adapter.cursor.projection]]`
  **array** (`skill`→`direct-directory`, `agent`→`direct-file`, `hook-body`→`direct-file`,
  `hook-wiring`→`merge-json`, `command`→`direct-file`) and the Kiro-only `kiro-ide-hook`→`dropped`
  declared in the **table form** `[adapter.cursor.projections.kiro-ide-hook]` (the schema's
  array `primitive` enum admits only the five standard primitives — `kiro-ide-hook` must sit in
  the table form, matching kiro-ide/kiro-cli). **No new mode**, **no `adapter.schema.json`
  change** (both copies untouched; the mode-enum and the array `primitive` enum already admit
  every mode and primitive used). The contract change is the `[adapter.cursor]` block + the
  version bump only.
- **Project the agent inline in `cursor.py`, mirroring `kiro_ide._project_agent_as_md`.**
  The agent's mode is `direct-file`, but it dispatches to a Cursor-specific
  `_project_agent_as_md` (not the shared `direct_file` copy) that applies the
  `cursor-agent-frontmatter-v0.11` mapping **and** derives `readonly`. The frontmatter
  split/parse/serialise helpers follow the existing `kiro.py` / `kiro_ide.py` shape
  (duplicate rather than reach across module privates, per the sibling-projection
  convention). This is the RFC's "minimal projection helper, not a new contract mode."
- **Derive `readonly` with the pinned predicate (Open Q2 resolved).** Emit
  `readonly: true` **iff** a `tools:` list is declared on the source agent **and** it
  contains **none** of the mutating tools `{Edit, Write, MultiEdit, NotebookEdit}`. When
  `tools:` is **absent**, **omit** `readonly` entirely (an agent with no allowlist inherits
  all tools, i.e. is *writable* — deriving `readonly: true` there would wrongly restrict a
  full-access agent). `Bash` does **not** disqualify read-only (the `core` reviewers declare
  `Read, Grep, Glob, Bash` and must stay `readonly: true`). Drop the source `tools:` field
  from the output frontmatter (Cursor has no such field). **Emit the boolean lower-cased**
  (`readonly: true`, not Python's `readonly: True`) — the kiro_ide `_serialize_frontmatter_md`
  shape this borrows has never emitted a `bool` and its `else` branch would render `True`; the
  Cursor serialiser must special-case `bool` to YAML/JSON `true`/`false`.
- **Emit Cursor agent frontmatter fields only.** The output frontmatter carries `name`
  (passthrough; derived from filename if absent), `description` (passthrough), `model`
  (identity passthrough — Cursor resolves a known id or falls back to inherit; no alias
  translation), and the derived `readonly`. Never emit `tools`, `is_background`, or any
  Claude/Kiro/Copilot-only key.
- **Aggregate hook-wiring into one `.cursor/hooks.json` with `version: 1`.** `hook-wiring`
  is `merge-json` (managed-key `hooks`), but Cursor's shape needs an event remap and a
  `version` key the shared `merge_json` projection does not produce — so dispatch to a
  Cursor-specific merge helper in `cursor.py` (mode stays `merge-json` in the contract). The
  helper reads every `.apm/hook-wiring/*.toml`, translates each source event via the event
  map, emits the handler shape `{"command": "<cmd>"}` under `hooks.<cursorEvent>`, writes
  `{"version": 1, "hooks": {…}}`, and **merges** under the managed key into any existing
  `.cursor/hooks.json` (preserving the adopter's other top-level keys and any unmanaged
  events). `on-conflict = "merge-managed-key-only"`.
- **Key the event map on the actual source event names and drop unmapped events with a
  build-time log (RFC decision 4; erratum recorded).** The shipped hook-wiring source uses
  Claude-native PascalCase event names (`SessionStart`, `UserPromptSubmit`, `PreToolUse`,
  `PostToolUse`, `Stop`) — confirmed by `packs/core/.apm/hook-wiring/session-start.toml` and
  the Copilot `_EVENT_MAP` precedent. Map: `SessionStart`→`sessionStart`,
  `UserPromptSubmit`→`beforeSubmitPrompt`, `PreToolUse`→`preToolUse`,
  `PostToolUse`→`postToolUse`, `Stop`→`stop`. A source event with **no** map entry is
  **dropped with a build-time log line** (fail-**open**-with-log, the catalogue's
  no-silent-caps rule and RFC-0026 decision 4 — deliberately unlike Copilot's fail-closed
  `copilot-hooks-json`). The map lives in the `[adapter.cursor]` contract block, read by the
  helper (not hardcoded), per RFC decision 4.
- **Wire `cursor` into both install dispatchers.** Add a `cursor` branch to
  `_render_for_user_scope` (install.py:~2356) and `_render_for_repo_scope` (~2430), each
  importing `cursor` and calling `cursor.project(pack_dir, contract, out)` — mirroring the
  `codex`/`claude-code` branches (a plain `.project()` call, **no** rewrite), since Cursor's
  prefix is identical at both scopes. Without these branches, `install --adapter cursor`
  raises `no … projection wired for adapter 'cursor'`.
- **Register `cursor` in both adapter registries.** Add `"cursor": cursor.project` to
  `ADAPTERS` and `"cursor": cursor` to `registry` in `adapters/__init__.py`. The contract
  block makes `shipped_adapters_from_contract()` advertise `cursor` automatically (no
  `cli.py` edit).
- **Declare the scope block.** `[adapter.cursor.scope]` sets `repo = "."`, `user = "~"`,
  `allowed-prefixes.repo = [".cursor/", ".agentbundle/"]`,
  `allowed-prefixes.user = [".cursor/", ".agentbundle/"]` (the `.agentbundle/` prefix carries
  the install state file at both scopes, as every scope-capable adapter lists it).
- **Run the full `agentbundle` pytest by hand, not just `make build-check`.** A contract
  version bump trips lexical version-compare bugs and stale version assertions in CI-ungated
  test roots. Bump every stale `"0.10"` contract-version assertion to `"0.11"` and fix any
  version-compare breakage the bump surfaces (see Ask-first).
- **Wire the cursor adapter test path into CI explicitly.** `build-check.yml` does not
  auto-discover package pytest; add `agentbundle/build/tests/test_adapter_cursor.py` to a CI
  step or it never gates.

### Ask first

- **Fixing the lexical version-compare at `install.py:2779`** (`contract_version >= "0.7"`).
  `"0.11" < "0.7"` lexically, but the bug is currently **latent**: Step-4b and the Step-5
  fallback both return `DEFAULT_ADAPTER`, so the wrong branch is taken with the same result.
  The inline comment already flags "two-digit minor bumps → move into a helper." If the
  full-pytest run on `"0.11"` surfaces a real failure, fix it with a tuple-comparing helper
  **and a focused regression test** (per the RFC-code-precondition rule); if green, record a
  backlog note rather than widening this PR's diff. Do not silently leave a fix untested.
- **Translating agent `model` aliases to Cursor model ids.** The spec passes `model` through
  verbatim (RFC decision: passthrough; Cursor resolves or inherits). Introducing an
  alias→cursor-id map is a follow-on that needs a probe against the then-current Cursor.
- **Projecting `.cursor/rules/*.mdc` or `.cursor/mcp.json`.** Both are RFC-0026 non-goals;
  adding either is a separate cross-adapter RFC.
- **Extending `cursor`'s inline agent/hook helpers to another adapter.** Cursor is the only
  consumer; a sibling adapter gets its own helpers, not a generalisation.

### Never do

- **No new projection mode and no `adapter.schema.json` change.** The four reused modes are
  already enumerated; the readonly derivation and event remap live in `cursor.py`, not in a
  new mode.
- **No new top-level directory.** The change fits existing trees (`packages/agentbundle/`,
  `docs/`, `.github/`).
- **No new pack manifest field and no new CLI flag.** Parity derives from existing data —
  `[adapter.cursor.*]`, `[pack.install] allowed-adapters`, `<pack>/.apm/<type>/`.
- **No new module boundary / no new top-level dependency.** `cursor.py` is a module inside
  the existing `build/adapters/` package; helpers reuse stdlib + existing siblings.
- **No `_rewrite_cursor_user_scope_paths` function.** Cursor's prefix is identical at both
  scopes; a prefix rewrite (the Copilot pattern) is wrong here.
- **No adding `cursor` to `SELF_HOST_ADAPTERS`.** Distribution-only (RFC decision 5).
- **No silent permission widening.** An agent declaring a writing tool never gets
  `readonly: true`; the derivation is conservative (read-only only on a declared,
  zero-mutating-tool list).
- **No silent event drop.** An unmapped hook event is dropped **with a build-time log line**.
- **No regression of claude-code / kiro-ide / kiro-cli / copilot / codex projection
  behaviour.** Those adapters' projection tables and outputs are byte-identical post-bump.
- **No hardcoded `if adapter == "cursor"` in any contract-driven rail** (the warning rail,
  `shipped_adapters_from_contract`, the scope-capability checks) beyond the two install
  dispatch branches that every adapter requires.

## Testing Strategy

| Behaviour from Objective | Verification mode | Why this mode |
| --- | --- | --- |
| `skill` projects to `.cursor/skills/<name>/` (straight directory copy) | **TDD** — unit test on `cursor.project` with a fixture pack; assert the skill dir + `SKILL.md` land. | Filesystem shape commitment. |
| `agent` projects to `.cursor/agents/<name>.md` with Cursor frontmatter (`tools` dropped, `readonly` derived) | **TDD** — unit test: fixture agents with mutating vs non-mutating tool sets; assert `.md` output, no `tools:` line, `readonly: true` only for the non-mutating one, no `readonly` when `tools:` absent. | Three-way commitment (path + frontmatter shape + readonly predicate); the load-bearing fidelity decision. |
| `readonly` predicate: `{Edit,Write,MultiEdit,NotebookEdit}` ⇒ not read-only; `Bash`-among-reads ⇒ read-only; absent `tools:` ⇒ omitted | **TDD** — focused unit test enumerating each arm against the real shipped agent tool sets. | Mis-derivation breaks an agent or over-privileges it; pin every arm. |
| `hook-body` projects to `.cursor/hooks/<name>.{sh,py}` | **TDD** — unit test; assert the script lands at the path. | Filesystem shape. |
| `hook-wiring` merges into one `.cursor/hooks.json` (`{"version":1,"hooks":{…}}`) with the event remap | **TDD** — unit test: a `[[hooks.SessionStart]]` wiring → `json.loads` has `version == 1` and key `hooks.sessionStart`; handler is `{"command": …}`. | Aggregation + version key + remap are the load-bearing distinctions from bare `merge-json`. |
| Hook-wiring merge preserves a pre-populated `.cursor/hooks.json` (managed-key-only) | **TDD** — unit test: seed an existing `hooks.json` with a foreign top-level key + a foreign event; project; assert the foreign key/event survive and the managed events are added. | The RFC pre-mortem's clobber risk; pin the merge is non-destructive. |
| Unmapped hook event is dropped with a build-time log (not emitted, not a crash) | **TDD** — unit test: a wiring with an unmapped event produces a `hooks.json` without it and emits a log line; no exception. | Fail-open-with-log is a deliberate divergence from Copilot's fail-closed; pin both halves. |
| `command` projects to `.cursor/commands/<name>.md` | **TDD** — unit test; assert the command `.md` lands. | Cursor is first-class for commands; pin it is not dropped. |
| `kiro-ide-hook` is dropped (not projected) | **Goal-based check** — assert the `[adapter.cursor]` block marks it `dropped` / the adapter emits nothing for it. | Contract-data assertion. |
| `cursor.project` emits repo-relpaths; user scope reuses them unchanged | **TDD** — assert the build adapter writes `.cursor/…` (no `~`), and that the contract's `allowed-prefixes.user` is `[".cursor/", ".agentbundle/"]` (proving the generic user-root, no rewrite). | Open Q1 resolution; the no-rewrite claim. |
| `install --adapter cursor` is accepted at both scopes (dispatch branches present) | **TDD** — dispatch test asserting neither `_render_for_repo_scope` nor `_render_for_user_scope` raises `no … projection wired for adapter 'cursor'`. | Without the branches the adapter is unusable; pin both. |
| `cursor` is a shipped adapter advertised by the contract | **Goal-based check** — assert `shipped_adapters_from_contract()` includes `"cursor"`. | Contract-derived; one assertion. |
| `cursor` is **not** in `SELF_HOST_ADAPTERS` | **Goal-based check** — assert `"cursor" not in SELF_HOST_ADAPTERS`. | Distribution-only invariant. |
| Contract is `version = "0.11"`; the existing adapters' tables byte-identical | **Goal-based check** — assert `[contract] version == "0.11"`; diff the existing adapter blocks against v0.10. | Bump invariant + no-regression. |
| `adapter.toml` ↔ `docs/contracts/adapter.toml` byte-identical | **Goal-based check** — `test_contract_files_byte_identical` (existing). | Dual-copy gate. |
| Full `agentbundle` pytest green on `"0.11"` (stale assertions bumped; no version-compare breakage) | **Goal-based check** — `pytest packages/agentbundle/` exits 0. | The contract-bump trap; CI-ungated roots only caught by a hand-run. |
| CI gates the cursor adapter test path | **Goal-based check** — `build-check.yml` names `test_adapter_cursor.py` in a step. | Otherwise the suite never gates. |
| `make build-self FORCE=1` is a noop after the final commit (cursor stays out of the self-host projection) | **Goal-based check** — clean `git status --short` after the run. | Build-pipeline gate; proves distribution-only. |
| `python3 tools/hooks/pre-pr.py` exits 0 | **Goal-based check** — aggregate enforcement (CI). | Covered by CI. |

## Acceptance Criteria

The spec is closed when each observable outcome is verifiable in the merged PR.

### Contract surface

- [x] **AC1.** `adapter.toml`'s `[contract] version` is `"0.11"` (was `"0.10"`); the header
  comment gains a line naming this spec / RFC-0026 alongside the existing RFC pointers. **No**
  change to `adapter.schema.json` is required or made — the projection-mode `enum` and the
  `projection`-array `primitive` `enum` already admit every mode and primitive Cursor uses
  (verify at impl time: all of `direct-directory`/`direct-file`/`merge-json`/`dropped` present
  in the mode enum; `skill`/`agent`/`hook-body`/`hook-wiring`/`command` present in the
  primitive enum).
- [x] **AC1a.** `adapter.toml` is **dual-copy**: the edits land byte-identically in
  `packages/agentbundle/agentbundle/_data/adapter.toml` **and** `docs/contracts/adapter.toml`.
  `test_contract_files_byte_identical` (`build/tests/test_contract.py`) red-fails if only one
  copy is edited.
- [x] **AC2.** A new `[[adapter.cursor.projection]]` **array** declares the five standard
  primitives, one entry each:
  - `skill` → `mode = "direct-directory"`, `target-path = ".cursor/skills/"`, `on-conflict = "prompt-then-preserve"`.
  - `agent` → `mode = "direct-file"`, `target-path = ".cursor/agents/"`,
    `frontmatter-mapping = "cursor-agent-frontmatter-v0.11"`, `on-conflict = "prompt-then-preserve"`.
  - `hook-body` → `mode = "direct-file"`, `target-path = ".cursor/hooks/"`, `on-conflict = "prompt-then-preserve"`.
  - `hook-wiring` → `mode = "merge-json"`, `target-path = ".cursor/hooks.json"`,
    `managed-key = "hooks"`, `on-conflict = "merge-managed-key-only"`, plus the
    `hook-event-map` inline table (source-PascalCase → cursor-event).
  - `command` → `mode = "direct-file"`, `target-path = ".cursor/commands/"`, `on-conflict = "prompt-then-preserve"`.

  The Kiro-only `kiro-ide-hook` is declared `mode = "dropped"` in the **table form**
  `[adapter.cursor.projections.kiro-ide-hook]` — **not** the array — because the schema's
  array `primitive` enum admits only the five standard primitives (kiro-ide/kiro-cli set the
  precedent). Declaring it in the array would red-fail `test_contract_validates_against_schema`.
- [x] **AC3.** `[adapter.cursor.scope]` declares `repo = "."`, `user = "~"`,
  `allowed-prefixes.repo = [".cursor/", ".agentbundle/"]`,
  `allowed-prefixes.user = [".cursor/", ".agentbundle/"]`. (Open Q1 resolved: the prefix is
  identical at both scopes — the claude-code/codex pattern — so the user-scope home is
  produced by generic user-rooting, **not** a Cursor-specific rewrite.)
- [x] **AC4.** A new `[frontmatter-mapping."cursor-agent-frontmatter-v0.11"]` declares the
  per-key rules consumed by the adapter: `name` → `rename = "name"`, `description` →
  `rename = "description"`, `model` → `rename = "model"` (identity passthrough, **no** `values`
  alias map). `tools` is **absent** from the mapping (dropped by the adapter, which also
  derives `readonly`). The shape follows the existing per-key sub-table convention.
- [x] **AC5.** The `claude-code`, `kiro`, `kiro-ide`, `kiro-cli`, `copilot`, and `codex`
  `[adapter.<name>]` table bodies are byte-identical to v0.10. The only edits to the file are:
  `[contract] version` (`"0.10"`→`"0.11"`), the new `[adapter.cursor]` / scope / mapping blocks,
  and the header-comment provenance line AC1 adds (the header comment is neither `[contract]`
  nor an adapter block, so it is called out here explicitly to keep AC5's diff-claim honest).

### Adapter-module surface

- [x] **AC6.** New module `build/adapters/cursor.py` exposes `project(pack_path, contract,
  output_root)` and `project_packs(pack_paths, contract, output_root)` (the kiro_ide shape).
  It iterates the `[adapter.cursor]` projection in phase order, dispatching each primitive to
  its mode handler; `dropped` and absent source dirs are skipped.
- [x] **AC7.** `skill` projects via `direct-directory` to `.cursor/skills/<name>/` (straight
  copy of the source skill directory tree, including `SKILL.md`). `command` and `hook-body`
  project via `direct-file` to `.cursor/commands/<name>.md` and `.cursor/hooks/<name>.{sh,py}`
  respectively. Observable: a fixture pack with one skill, one command, one hook body lands all
  three at the named paths.
- [x] **AC8.** `agent` projects via the inline `_project_agent_as_md` to
  `.cursor/agents/<name>.md`: the output is `---`-fenced frontmatter + the original body; the
  frontmatter carries `name`, `description`, `model` (when present, verbatim), and the derived
  `readonly`; it carries **no** `tools` field and no Claude/Kiro/Copilot-only key. Observable:
  input `---\nname: foo\ndescription: bar\ntools: Read, Grep, Glob, Bash\nmodel: opus\n---\nBody.`
  produces `.cursor/agents/foo.md` whose frontmatter has `name: foo`, `description: bar`,
  `model: opus`, `readonly: true`, **no** `tools`, and body `Body.`.
- [x] **AC9.** The readonly predicate is exactly: `readonly: true` iff a `tools:` list is
  declared **and** contains none of `{Edit, Write, MultiEdit, NotebookEdit}`; otherwise
  `readonly` is **omitted**. Observable, against the real shipped agents: the 4 `core`
  reviewers (`Read, Grep, Glob, Bash`) and the 2 `research` retrieval agents
  (`Read, Grep, Glob, WebFetch, WebSearch`) emit `readonly: true`; `implementer`
  (`Read, Edit, Write, Grep, Glob, Bash`) emits **no** `readonly`; a synthetic agent with no
  `tools:` line emits **no** `readonly`. The emitted token is the literal lower-cased
  `readonly: true` (asserted on the serialised bytes, not a YAML-parsed truthy value).
- [x] **AC10.** `hook-wiring` projects via the Cursor-specific merge helper (dispatched from
  `merge-json` mode) to a single `.cursor/hooks.json` of shape
  `{"version": 1, "hooks": {<cursorEvent>: [{"command": "<cmd>"}]}}`. Each source event is
  translated through the contract `hook-event-map`; an unmapped event is **dropped with a
  build-time log line** (no exception). The carried command's legacy `tools/hooks/` hook-body
  prefix is rewritten to `.cursor/hooks/` (where `hook-body` direct-file actually lands the
  script — the Copilot precedent; without it the projected hook references a path that does not
  exist under `.cursor/`). Observable: a `[[hooks.SessionStart]]` wiring with command
  `python tools/hooks/session-start.py` yields a `hooks.json` whose `json.loads(...)` has
  `version == 1` and `hooks.sessionStart[0].command == "python .cursor/hooks/session-start.py"`.
- [x] **AC11.** The hook-wiring merge is **non-destructive**: projecting into a pre-existing
  `.cursor/hooks.json` that carries a foreign top-level key and a foreign event preserves both
  and adds the managed events under the managed key (`merge-managed-key-only`).

### Registration / install surface

- [x] **AC12.** `adapters/__init__.py` registers `"cursor": cursor.project` in `ADAPTERS` and
  `"cursor": cursor` in `registry`, and imports the new module.
- [x] **AC13.** `shipped_adapters_from_contract()` includes `"cursor"` after the contract block
  lands, with **no** edit to `cli.py` or `scope.py`.
- [x] **AC14.** `commands/install.py` gains a `cursor` branch in **both** `_render_for_user_scope`
  and `_render_for_repo_scope` (and `cursor` is added to each function's adapter imports), each
  calling `cursor.project(pack_dir, contract, out)` with **no** prefix rewrite. Observable: a
  dispatch test confirms neither raises `no … projection wired for adapter 'cursor'` for a
  cursor-targeted pack, at either scope.
- [x] **AC15.** `cursor` is **not** in `SELF_HOST_ADAPTERS` (`build/self_host.py`); the
  self-host projection does not write any `.cursor/` tree into this repo's working tree.

### Tests / CI / gates

- [x] **AC16.** New test module `build/tests/test_adapter_cursor.py` (modelled on
  `test_adapter_kiro_ide.py` / `test_adapter_copilot.py`) covers AC6–AC11 and AC2–AC5: skill /
  command / hook-body projection, agent `.md` shape, every readonly-predicate arm, the
  hook-wiring aggregation + version key + event remap + unmapped-drop + non-destructive merge,
  and the `dropped` `kiro-ide-hook`.
- [x] **AC17.** `.github/workflows/build-check.yml` runs `build/tests/test_adapter_cursor.py` in
  an explicit step (CI does not auto-discover package pytest).
- [x] **AC18.** Every stale `"0.10"` **contract-version** assertion is updated to `"0.11"`
  (`build/tests/test_contract.py`, `build/tests/test_adapter_kiro_ide.py`,
  `tests/unit/test_contract_v0_3_schema.py`, and the shipped-adapter tuple in
  `tests/unit/test_install_argparse_adapter_flag.py` + the adapter-set / pair-count assertions in
  `test_contract.py` for the new `cursor` block; `test_multi_pack_install.py`'s `_skill_path`
  gains a cursor branch as `cursor` now parametrizes the per-adapter matrix). `test_adapter_copilot.py`
  needed no change — its `"0.10"` references are comments, not assertions. Assertions that
  intentionally pin **other** versions (e.g. `test_contract_v08.py`, `test_shipped_packs_v08_declarations.py`
  — packs that stay at `"0.8"`) are left unchanged. `pytest packages/agentbundle/` exits 0.
- [x] **AC19.** The latent lexical version-compare the `"0.11"` bump exposes (`install.py`
  Step 4b, `contract_version >= "0.7"` — lexically `"0.11" < "0.7"`) is **fixed** in this PR
  (ride-along): replaced by the numeric `scope.contract_version_at_least` helper, with a focused
  regression test (`ContractVersionAtLeastTests`) pinning `"0.11" >= "0.7"`. Recorded in the
  Changelog + `docs/backlog.md`.
- [x] **AC20.** Root `AGENTS.md`'s Cursor-reader line is accurate post-adapter (Cursor now has a
  native projection, not only incidental `AGENTS.md` reading); update the wording only if it now
  misleads.
- [x] **AC21.** `docs/specs/distribution-adapters/spec.md` Changelog gains a v0.10 → v0.11 entry
  naming the new `cursor` adapter, the five projected primitives, the `dropped` `kiro-ide-hook`,
  and the no-mode-enum-change / no-schema-change property.
- [x] **AC22.** `make build-self FORCE=1` produces a clean working tree (`git status --short`
  empty after the run), proving `cursor` stays out of the self-host projection.
- [x] **AC23.** `python3 tools/hooks/pre-pr.py` exits 0 on the merged tree.
- [x] **AC24.** CI gates (`build-check` linux + windows, package `pytest`, docs lint suite) pass
  on the implementation PR.

## Assumptions

- Technical: Contract is at `version = "0.10"` today; RFC-0026 specifies the bump to `"0.11"`
  (source: `packages/agentbundle/agentbundle/_data/adapter.toml:42`, read 2026-06-11).
- Technical: `adapter.schema.json`'s projection-mode `enum` already includes `direct-directory`,
  `direct-file`, `merge-json`, and `dropped`, and the `projection`-array `primitive` `enum`
  includes all five standard primitives — so Cursor needs **no** schema change (source:
  `packages/agentbundle/agentbundle/_data/adapter.schema.json:38–53, 34–37`, read 2026-06-11).
- Technical (Open Q1 resolved): Cursor uses the **identical `.cursor/` prefix at repo and user
  scope** — the claude-code/codex pattern (same prefix in `allowed-prefixes.repo` and
  `allowed-prefixes.user`), **not** Copilot's `.github/`→`.copilot/` divergence — so the
  user-scope home is produced by generic user-rooting and needs **no** `_rewrite_cursor_user_scope_paths`
  (source: `adapter.toml` claude-code scope `:182–189` + codex scope `:500–506`, read
  2026-06-11; RFC-0026 Open Q1).
- Technical (Open Q2 resolved): the readonly predicate `{Edit, Write, MultiEdit, NotebookEdit}`
  classifies all six shipped agents correctly — the 4 `core` reviewers and the 2 `research`
  retrieval agents → `readonly: true`, the `implementer` → omitted (source: the `tools:` lines in
  `packs/core/.apm/agents/*.md` + `packs/research/.apm/agents/*.md`, read 2026-06-11; RFC-0026
  Open Q2).
- Technical: the shipped hook-wiring source uses Claude-native PascalCase event names
  (`[[hooks.SessionStart]]`), not the RFC's `agentSpawn` spelling; the Copilot `_EVENT_MAP` keys
  on PascalCase precedent — so Cursor's event map keys on PascalCase (source:
  `packs/core/.apm/hook-wiring/session-start.toml`; `build/projections/copilot_hooks_json.py:61–68`,
  read 2026-06-11). **Erratum vs RFC-0026** recorded in the Changelog.
- Technical: cursor needs explicit branches in both `_render_for_user_scope` (install.py:~2356)
  and `_render_for_repo_scope` (~2430) — each has a per-adapter dispatch whose `else` raises
  `no … projection wired for adapter <name>`; a same-prefix adapter (codex/claude-code) just
  calls `.project()` with no rewrite (source: `install.py:2344–2437`, read 2026-06-11).
- Technical: `shipped_adapters_from_contract()` returns every `[adapter.<name>]` key, so adding
  the contract block auto-advertises `cursor` to the CLI `--adapter` choices and `list-targets`
  with no `cli.py` edit (source: `packages/agentbundle/agentbundle/scope.py`
  `shipped_adapters_from_contract`, read 2026-06-11).
- Technical: cursor needs **no** entry in `_user_scope_adapter_probes()` (install.py:~2537) — that
  per-adapter user-home probe table is consulted only at Step 4 when `--adapter` is *omitted* at
  user scope; user-scope cursor installs pass `--adapter cursor` explicitly (Step 1, probe
  skipped), matching the copilot precedent (also absent from the probe table). Implicit-probe
  user-scope discovery for cursor would be a separate, out-of-scope decision (source:
  `install.py` `_user_scope_adapter_probes` + Step 4 resolution, read 2026-06-11).
- Technical: cursor hook-wiring (`merge-json`, array-form) matches the **codex** shape, which
  `_adapter_supports_user_scope_hook_wiring` treats as repo-scope-only (array-form returns True
  only for `copilot-hooks-json`) — so cursor claims **no** user-scope hook-wiring merge, matching
  codex, and needs no change to that function (source: `install.py`
  `_adapter_supports_user_scope_hook_wiring`, read 2026-06-11).
- Technical: a contract version bump trips lexical version-compare and stale `"0.10"` assertions
  across CI-ungated test roots; `install.py:~2779` does a literal `contract_version >= "0.7"`
  whose inline comment flags two-digit-minor bumps, and every `"0.10"` contract-version literal
  across the package test tree must be triaged (count drifts — ~11 files at draft time; T5
  enumerates at impl time) — the bump requires a full hand-run of `pytest packages/agentbundle/`
  (source: `grep -rl '"0.10"'` package tree; `install.py:2776–2780`, read 2026-06-11; memory
  "Contract-bump test traps").
- Technical: `adapter.toml` is dual-copy (`_data/` + `docs/contracts/`);
  `test_contract_files_byte_identical` enforces parity (source:
  `build/tests/test_contract.py:561–572`, read 2026-06-11).
- Technical: the agent `.md` + frontmatter-mapping + inline `_project_agent_as_md` shape and the
  `_split_frontmatter`/`_apply_mapping` helpers already exist for kiro_ide and are the template
  for cursor's agent projection (source: `build/adapters/kiro_ide.py:212–276`,
  `build/adapters/kiro.py`, read 2026-06-11).
- Technical: Cursor's `.cursor/{skills,agents,commands}`, `.cursor/hooks.json`, `.cursor/hooks/`
  paths and the agent frontmatter vocabulary (`name`/`description`/`model`/`readonly`/`is_background`,
  no `tools`) and hook events (`sessionStart`/`beforeSubmitPrompt`/`preToolUse`/`postToolUse`/`stop`)
  are as RFC-0026 § Evidence verified against current Cursor docs (source: RFC-0026 § Evidence &
  prior art, citing cursor.com/docs, read 2026-06-11; a live re-probe is the manual smoke a
  follow-on may add — no shipped test depends on the live tool).
- Process: this is the implementing spec for an already-Accepted RFC (RFC-0026) and ADR (ADR-0015),
  so it lands via normal PR with no further RFC gate (source: `docs/CONVENTIONS.md` living-docs +
  RFC-0026 Status: Accepted, read 2026-06-11).
- Product: `cursor` is distribution-only (not self-hosted) per RFC-0026 decision 5 (source:
  RFC-0026 decision 5 + user direction 2026-06-11).

## Changelog

- **2026-06-11 — drafted.** Implementing spec for RFC-0026 / ADR-0015. Both RFC open questions
  settled in the spike and folded into the body:
  - **Open Q1 (user-scope `~/.cursor/commands/`)** → resolved: the user-scope path is
    `~/.cursor/commands/` — Cursor's `.cursor/` prefix is identical at repo and user scope. AC3.
  - **Erratum vs RFC-0026 (user-scope production mechanism), Approver: eugenelim.** RFC-0026
    states the user-scope home is "produced by the install handler's prefix rewrite — exactly the
    Copilot pattern" (§ Projection table, "User target (via rewrite)"). The spike found Cursor's
    prefix is **identical** at both scopes (the claude-code/codex shape, where
    `allowed-prefixes.repo == allowed-prefixes.user`), so the user-scope home is the generic
    user-rooting of the repo-relpath and there is **no** Cursor-specific rewrite function — unlike
    Copilot's `.github/`→`.copilot/` divergence, which is the only reason Copilot needs
    `_rewrite_copilot_user_scope_paths`. The **target paths are unchanged** (`~/.cursor/…` exactly
    as the RFC's projection table specifies); only the RFC's asserted *production mechanism* (a
    prefix rewrite) is corrected to "no rewrite needed." Recorded here as the governance erratum
    for this frozen-Accepted-RFC divergence, matching the hook-event-map erratum below. AC3, AC14.
  - **Open Q2 (readonly predicate)** → resolved: `readonly: true` iff a `tools:` list is declared
    and contains none of `{Edit, Write, MultiEdit, NotebookEdit}`; absent `tools:` ⇒ omitted. AC9.
  - **Erratum vs RFC-0026 (hook-event map keying).** RFC-0026's hook-event table spells the source
    vocabulary `agentSpawn` / `userPromptSubmit` / … (the Kiro `agent-event-vocabulary` names). The
    spike found the **shipped** hook-wiring source uses Claude-native PascalCase event names
    (`SessionStart`, …), and the Copilot precedent keys its map on PascalCase. This spec therefore
    keys Cursor's `hook-event-map` on PascalCase source names (mapping to the same Cursor targets the
    RFC specifies: `sessionStart` / `beforeSubmitPrompt` / `preToolUse` / `postToolUse` / `stop`). The
    RFC's target-event column stands unchanged; only the source-key spelling is corrected. Recorded
    here as the governance erratum for a frozen Accepted RFC.
  - **Ride-alongs folded in from review (2026-06-11, on request).** Two deferred review findings
    were pulled into this PR rather than left as backlog follow-ons: (1) the latent lexical
    version-compare at `install.py` Step 4b → numeric `scope.contract_version_at_least` + test
    (AC19); (2) the install-time nested-symlink read in `cursor.py`'s `_project_direct_directory`
    → copy with `ignore=_ignore_symlinks` (drops nested symlinks) + a regression test. Three
    findings stay as follow-ons (recorded in `docs/backlog.md`): the live-Cursor smoke (no tool
    access to verify), the agent model-alias map (needs a live probe — an unverified alias would
    violate no-speculative-mapping), and the block-style-YAML `tools:` parser fidelity + lifting
    the symlink guard to a shared helper for the other four adapters (both genuinely cross-adapter,
    and the parser change would diverge cursor's faithful-duplicate `_parse_frontmatter` from kiro's).
  - **Implementation clarification (hook-body-path rewrite), 2026-06-11.** Surfaced during
    EXECUTE: the shipped hook-wiring command references the body by its legacy `tools/hooks/`
    path, but cursor projects the body to `.cursor/hooks/` (`hook-body` direct-file). The
    hook-wiring merge helper therefore rewrites `tools/hooks/`→`.cursor/hooks/` in the carried
    command so the emitted `hooks.json` references the script where it lands — the same rewrite
    `copilot_hooks_json` does for `.github/hooks/`. AC10 updated to pin the rewritten command.
    Repo-scope only; no shipped pack ships a user-scope cursor hook (core is repo-only).

- **2026-06-11 — pack opt-in completed for the non-credentialed packs (follow-on PR).** The
  implementing PR (#273) shipped the adapter but added `cursor` to **no** pack's
  `allowed-adapters`, leaving it inert except where a line-less pack admits any shipped adapter
  at repo scope — the opt-in mechanism RFC-0026 § Migration path and [`plan.md`](plan.md)'s Rollout
  describe ("a new adapter is inert until a pack declares `allowed-adapters = [… "cursor"]`"),
  never exercised on the explicit allow-list packs. This follow-on opts the two
  **non-credentialed** full-parity packs in:
  `research` (the catalogue's parity validation surface — it ships the 2 retrieval subagents +
  skills the full-parity adapters are checked against; mirrors how `copilot-full-parity` added
  `copilot` to `research`) and `architect` (workspace-agnostic, pure-markdown skills). **No
  contract bump** — cursor reuses existing projection modes (no new mode), and both packs
  already declare a contract version under which cursor's skill/agent projection is valid
  (`research` v0.12, `architect` v0.10). Parity was verified by rendering `research` through the
  cursor adapter: 7 skills → `.cursor/skills/<name>/`, both retrieval subagents →
  `.cursor/agents/<name>.md` with `readonly: true` and `tools` dropped. The **5 credentialed
  packs** (atlassian, contracts, converters, figma, credential-brokers) are deferred to a
  follow-on **RFC-0013 erratum**: `credential-brokers`' 3-adapter set is frozen by RFC-0013 § 4
  (§4d ties the `adapter-root-bins/` + `~/.agentbundle/` broker projection to *exactly* the
  listed adapters), and the four consumer packs functionally depend on the broker admitting
  cursor too (a cursor-only user otherwise cannot install the broker and cannot authenticate).
  That erratum will also backfill `copilot` for catalogue-wide uniformity. See `docs/backlog.md`
  § `cursor-full-parity`.
