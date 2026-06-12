# Spec: copilot-full-parity

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0024](../../rfc/0024-copilot-subagent-projection.md) (the decision: `copilot` becomes a full-parity, user-scope-capable adapter; `agent`/`hook-wiring` flip `dropped`→first-class; contract v0.9→v0.10; **supersedes-in-part** RFC-0012's copilot repo-only scope); [ADR-0013](../../adr/0013-copilot-full-parity-user-scope-adapter.md) (the recorded decision + the `tools/hooks/`→`.github/hooks/` retirement); [RFC-0009](../../rfc/0009-codex-native-skills.md) + [`dropped-primitives-coverage`](../dropped-primitives-coverage/spec.md) (the codex `dropped`→first-class precedent this mirrors — the `codex-agent-toml` serialisation shape, the contract-driven warning rail, atomic contract+pack bumps); [RFC-0022](../../rfc/0022-kiro-adapter-split.md) (the v0.8→v0.9 contract bump this builds on, and its precedent that a contract bump need not bump every pack — load-bearing for the two-pack bump); [RFC-0011](../../rfc/0011-pack-allowed-adapters.md) (the `allowed-adapters` field edited for `research`); [RFC-0005](../../rfc/0005-user-scope-hook-support.md) (`merge-json` / user-scope-hook precedent); [ADR-0002](../../adr/0002-install-scope-per-pack-default-and-allowance.md) (per-pack scope default + allowance). Modifies [`packages/agentbundle/agentbundle/_data/adapter.toml`](../../../packages/agentbundle/agentbundle/_data/adapter.toml) (contract v0.9 → v0.10; copilot `agent` + `hook-wiring` flip `dropped`→new modes; copilot gains `[adapter.copilot.scope].user` + `allowed-prefixes.user`; copilot `skill` gains a user target; copilot `hook-body` target moves `tools/hooks/`→`.github/hooks/`; new `copilot-agent-frontmatter-v0.10` mapping) and its sibling [`adapter.schema.json`](../../../packages/agentbundle/agentbundle/_data/adapter.schema.json) (the two new modes admitted at every `dropped`-enumerating site) — **both dual-copy** into [`docs/contracts/adapter.toml`](../../contracts/adapter.toml) + [`docs/contracts/adapter.schema.json`](../../contracts/adapter.schema.json) (byte-identical, per `test_contract_files_byte_identical`); the two new projection-mode modules under `packages/agentbundle/agentbundle/build/projections/`; the dispatch + user-scope-prefix-rewrite in [`packages/agentbundle/agentbundle/commands/install.py`](../../../packages/agentbundle/agentbundle/commands/install.py); and [`packages/agentbundle/agentbundle/build/adapters/copilot.py`](../../../packages/agentbundle/agentbundle/build/adapters/copilot.py). Amends [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md) (v0.9 → v0.10 Changelog entry).
- **Contract:** none <!-- no REST/event/RPC interface surface; the adapter contract (`adapter.toml`) is internal build-pipeline data, named in Constrained by above -->
- **Shape:** integration <!-- wiring the adapter/contract to an external tool's (Copilot's) native surfaces; pulls dependencies & integration + interfaces & contracts + failure & resilience in the plan's LLD -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Superseded in part (2026-06-11) by
> [`docs/specs/copilot-skills-and-web/`](../copilot-skills-and-web/spec.md)
> (contract v0.11 → v0.12).** Two decisions recorded below are reversed there,
> against RFC-0024 § Errata: **(1)** the `skill` primitive no longer projects as
> an `instruction-file` to `.github/instructions/` (Decision 3 below) — it is now
> a first-class `direct-directory` Copilot Agent Skill at
> `.github/skills/<name>/SKILL.md` / `~/.copilot/skills/<name>/SKILL.md`; and
> **(2)** the `research` web degradation recorded below (Open Q4 / "no web tool")
> does not hold on the Copilot CLI + app — `WebFetch`/`WebSearch` resolve to
> Copilot's `web` tool there; only the cloud agent lacks it. The body below is
> preserved as the historical v0.10 record; read it through this banner.

> **Scope: one PR, one contract bump.** The contract bump, the two new projection
> modes, the new frontmatter mapping, the scope-table edit, the two-pack v0.8→v0.10
> bump, the `research` `allowed-adapters` edit, and the surviving-`command` warning-rail
> regression all land in a **single PR** per the RFC-0004 atomicity precedent inherited
> from `dropped-primitives-coverage`. Splitting risks (a) the contract claiming
> `.github/agents/` / `.github/hooks/` projection with no implementation that writes
> there, or (b) `research`/`core` declaring v0.10 while the resolver can't dispatch the
> copilot agent/hook modes.

## Objective

Make the `copilot` adapter project every primitive GitHub Copilot now supports — `skill`,
`agent`, `hook-wiring`, `hook-body` — at **both** repo and user scope, against the
Copilot app + CLI's `.github/` and `~/.copilot/` layout, so that the 4 subagents in
`core` and the 2 retrieval subagents in `research` (which today hit copilot's `dropped`
modes and silently vanish) instead land as native Copilot custom agents. Close the
self-imposed repo-only limit by giving copilot a real user-scope home, and prove the
parity by adapting the two subagent-bearing packs.

**For the Copilot adopter installing `core` at repo scope:**
`agentbundle install --pack core --scope repo --adapter copilot .` today lands only
`core`'s skills at `.github/instructions/` and drops its agents + hook-wiring (the
warning rail fires, but the capability is gone). After this spec the same command lands
`core`'s 4 agents at `.github/agents/<name>.agent.md` (markdown → `.agent.md` via the new
`copilot-agent-md` mode), `core`'s hook-wiring at `.github/hooks/<name>.json` (one
self-contained JSON per wiring file via the new `copilot-hooks-json` mode), `core`'s hook
bodies alongside them at `.github/hooks/`, and `core`'s skills at `.github/instructions/`
— four primitive types projected, only the single `command` still dropped (and the
warning rail names exactly that one drop, no longer `agent`/`hook-wiring`).

**For the Copilot adopter installing `research` at user scope:**
`research` (`default-scope = "user"`) is today refused at copilot up front
(`allowed-adapters` excludes it). After this spec, `agentbundle install --pack research
--adapter copilot` (user scope by default) lands `research`'s skills at
`~/.copilot/instructions/<name>.instructions.md` and its 2 retrieval subagents at
`~/.copilot/agents/<name>.agent.md`, discovered globally by the Copilot app + CLI from
outside any repo.

**Success for the catalogue's adapter model:** copilot joins claude-code / codex / kiro as
a first-class **user-scope-capable** adapter — `user_scope_capable_adapters_from_contract()`
includes it with no Python edit (it keys off `[adapter.copilot.scope].user`), and the
install resolver stops refusing copilot at user scope. The `command` drop stays visible
through the existing contract-driven warning rail (no copilot-specific branch).

**Success for the read-only subagents on Copilot (the honest fidelity bound):** the
read-only restriction on `research`'s `evidence-retriever` / `source-extractor` and
`core`'s reviewers is preserved (they get `view`/`grep`/`glob`, never `edit`/`execute`),
but because Copilot exposes **no web tool to custom agents** (verified, CLI 1.0.59, two
independent runs), `research`'s retrieval subagents lose live web access on Copilot —
read/search only. This degradation is **documented**, not silently dropped.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines. *Always do*
applies without asking; *Ask first* requires human sign-off before proceeding;
*Never do* is a hard rule, even under time pressure.

### Always do

- **Add the two new modes as Copilot-shaped siblings, not generalisations.**
  `copilot-agent-md` (markdown → `.agent.md`) and `copilot-hooks-json` (wiring `.toml` →
  one self-contained `<name>.json`) live each in **one** new module under
  `packages/agentbundle/agentbundle/build/projections/` — `copilot_agent_md.py` and
  `copilot_hooks_json.py` — siblings of the existing `codex_agent_toml.py` / `merge_json.py`,
  dispatched **only** from `packages/agentbundle/agentbundle/build/adapters/copilot.py`
  (which today raises `ValueError` on any mode beyond `instruction-file` / `direct-file`).
  Frontmatter split/parse duplicates the existing `_split_frontmatter` / `_parse_frontmatter`
  shape rather than reaching across module privates (the acknowledged sibling-projection
  duplication, per `dropped-primitives-coverage` § Always do).
- **Use a new per-file hook mode, NOT `merge-json`.** Copilot reads **every** `*.json` in
  its hooks dir, so each wiring file serialises to its own self-contained
  `{"version":1,"hooks":{<event>:[{"type":"command","bash":…,"powershell":…}]}}` file —
  the single-target merge model `codex` used can't express it. The one-source-file →
  one-output-file shape mirrors `codex-agent-toml`; the per-file-vs-merged distinction is
  the new part.
- **Freeze the full hook event-name map** in the contract / mode. Our event vocabulary →
  Copilot's: `SessionStart`→`sessionStart`, `SessionEnd`→`sessionEnd`,
  `UserPromptSubmit`→`userPromptSubmitted`, `PreToolUse`→`preToolUse`,
  `PostToolUse`→`postToolUse`, `Stop`→`agentStop` (and `errorOccurred` available
  upstream). All six mapped events are **verified to fire** (RFC-0024 § Acceptance,
  Runs 2–4, CLI + app 1.0.59); no refuse-and-warn is needed for them. A source event with
  no entry in the map **fails the build** (fail-closed; never silently emits an
  unrecognised event key).
- **Handle tools as pass-through gated by an explicit allow-list (fail-closed).** Copilot's
  `.agent.md` parser accepts the Claude comma-separated `tools:` format and resolves the
  names itself (verified: `Read`→`view`, `Grep`→`grep`, `Glob`→`glob`). The build emits
  the source `tools` verbatim but **validates** every token against an explicit
  allow-list of names known to be accepted by Copilot custom agents
  (`Read`, `Grep`, `Glob`, `Edit`, `Write`, `MultiEdit`, `Bash`, plus the
  known-and-explicitly-recorded `WebFetch` / `WebSearch`). A token in **none** of those
  sets **fails the build** rather than passing through to be silently ignored by Copilot
  (which would drop a needed capability invisibly). This is a deliberately *stricter*
  policy than codex's drop-on-unmapped and kiro's warn-drop — sited explicitly here, not
  inherited.
- **Drop `model`; omit `target`** on `copilot-agent-md` projection. The CLI ignores
  `model` (and errored on array syntax — copilot-cli#2133/#1195), and our values
  (`opus`/`sonnet`) aren't Copilot model ids; `target` defaults to both `vscode` +
  `github-copilot`. `name` / `description` / body pass 1:1 (body becomes the agent's
  instructions).
- **Give every projectable copilot primitive a user target.** Add
  `[adapter.copilot.scope].user = "~"`, `allowed-prefixes.user = [".copilot/agents/",
  ".copilot/instructions/", ".copilot/hooks/"]`, and set `allowed-prefixes.repo` to
  `[".github/instructions/", ".github/agents/", ".github/hooks/"]`. `skill` gains the user
  target `~/.copilot/instructions/<name>.instructions.md` (same `instruction-file` mode).
- **Move `hook-body` from `tools/hooks/` to `.github/hooks/` (repo) + `~/.copilot/hooks/`
  (user)** — outright, no back-compat alias (Open Q3 default; no shipped pack writes
  copilot hook-body today — only `core` ships hook-body, against the legacy target).
- **Bump exactly `research` and `core` `[pack.adapter-contract] version` from `"0.8"` to
  `"0.10"`** — atomic with the contract change. This is **not** an all-pack bump: packs
  that ship no agents/hooks and don't target copilot stay at `"0.8"` and keep prior copilot
  behaviour (RFC-0022 precedent — a contract bump need not bump every pack). They jump
  0.8→0.10 directly (contract levels are forward-cumulative; no 0.9-specific pack behaviour).
- **Add `copilot` to `research`'s `allowed-adapters`** —
  `["claude-code", "kiro", "codex", "copilot"]`.
- **Document the `WebFetch`/`WebSearch` degradation** for `research` on Copilot (retrieval
  subagents lose live web access — read/grep/glob only) rather than silently dropping the
  tools. Location: the `research` pack's adapter/projection notes (`packs/research/`).
- **Run the warning rail at both `--scope repo` and `--scope user`** — it stays
  contract-driven (no copilot literal). Post-bump it fires for copilot naming **only**
  `command` (the one surviving drop) against `core`, and is silent against `research`
  (which ships no `command`).

### Ask first

- **Flipping `command` from `dropped` for copilot.** The CLI does not load custom slash
  commands yet (copilot-cli#618/#1113); the drop + warning rail are load-bearing until a
  follow-on RFC lands the feature with a tested target. Do not project to `.github/prompts/`
  speculatively.
- **Mapping `WebFetch`/`WebSearch` to any Copilot tool name.** Verified absent from the
  custom-agent toolset (1.0.59, two runs); inventing an alias would be unverified. A
  future flip needs a fresh probe against the then-current CLI.
- **Extending `copilot-agent-md` or `copilot-hooks-json` to another adapter.** Copilot is
  the only consumer; a sibling adapter gets sibling modes, not a generalisation.
- **Changing the frozen event-name map.** The six mapped events are version-sensitive
  (Copilot is preview); a change needs a re-check against the then-current CLI.

### Never do

- **No new top-level directory.** The change fits existing trees
  (`packages/agentbundle/`, `packs/`, `docs/`).
- **No new pack manifest field.** Parity derives from existing data —
  `[[adapter.copilot.projection]]`, `[adapter.copilot.scope]`, `[pack.install]
  allowed-adapters`, `<pack_dir>/.apm/<type>/`.
- **No new CLI flag.** The warning rail is default-on (unchanged); no new surface.
- **No new module boundary / no new top-level dependency.** The two modes are modules
  inside the existing `build/projections/` package; no new third-party dependency.
- **No `merge-json` reuse for copilot hook-wiring** — Copilot's many-independent-files
  hooks dir can't be expressed by a single mergeable target.
- **No silent permission widening.** An emitted `.agent.md` never omits the `tools` field
  for an agent that declared one (omitting `tools` = all tools, in Copilot); read-only
  agents keep their read-only token set.
- **No regression of claude-code / kiro-ide / kiro-cli / codex projection behaviour.**
  Those adapters' projection tables are byte-identical post-bump.
- **No code path that emits the warning without consulting the contract.** A hardcoded
  `if adapter == "copilot"` anywhere in the warning trigger is a contract violation.
- **No state-schema version bump.** `STATE_SCHEMA_VERSION` is unchanged.
- **No projection of `command`/prompt files** for copilot (out of scope; deferred to the
  follow-on RFC).

## Testing Strategy

| Behaviour from Objective | Verification mode | Why this mode |
| --- | --- | --- |
| `install --pack core --scope repo --adapter copilot .` lands agents at `.github/agents/<name>.agent.md` | **TDD** — integration test against the install handler with a fixture repo. Assert on-disk projection AND `.agent.md` frontmatter shape (`name`/`description` present, `model`/`target` absent, `tools` line verbatim). | Three-way commitment (filesystem + content + only-`command`-dropped). |
| Same install lands hook-wiring at `.github/hooks/<name>.json` (one file per wiring) + hook bodies at `.github/hooks/` | **TDD** — integration test. Assert one `<name>.json` per source wiring file, each a self-contained `{"version":1,"hooks":{…}}`, and the hook-body scripts copied alongside. | Per-file shape is the load-bearing distinction from `merge-json`. |
| `install --pack research --adapter copilot` (user) lands skills at `~/.copilot/instructions/` + agents at `~/.copilot/agents/` | **TDD** — integration test at user scope with an isolated `$HOME`/`COPILOT_HOME`. Assert both user targets populated; assert copilot is no longer refused for `research`. | User-scope parity is the core RFC claim; pins the resolver no longer refuses + the targets. |
| Agent markdown → `.agent.md` conversion (`copilot-agent-md` mode) | **TDD** — focused unit test on the serialiser: frontmatter `{name, description, tools, model}` + body → `.agent.md` with `model` dropped, `target` omitted, `tools` verbatim, body 1:1. | Pure conversion logic; pin the field mapping + the model-drop. |
| Wiring `.toml` → `<name>.json` conversion (`copilot-hooks-json` mode) incl. event-name map | **TDD** — focused unit test: a wiring file with `SessionStart` → a JSON file with `sessionStart` key and `{"type":"command","bash":…,"powershell":…}` handler shape; round-trip via `json.loads`. | Pins the serialisation shape + the frozen event-name map. |
| Tool-token allow-list fails the build on an unknown token; passes known tokens (incl. `WebFetch`/`WebSearch`) verbatim | **TDD** — unit test: known set emits verbatim; a synthetic unknown token raises a build error. | Fail-closed is security-relevant; pin both arms. |
| Read-only restriction preserved (no `edit`/`execute` for read-only agents) | **TDD** — unit test asserting an agent declaring only `Read, Grep, Glob` emits exactly those tokens (no widening, no injected write/execute). | Permission-preservation is a security commitment. |
| Event-name map fails the build on an unmapped source event | **TDD** — unit test: a wiring file with an event absent from the map raises a build error. | Fail-closed; never emit an unrecognised event key. |
| Warning rail fires for `--adapter copilot` against `core` naming **only** `command` (post-flip) | **TDD** — integration test: install `core` via copilot at repo scope; assert stderr names `command` and **not** `agent`/`hook-wiring`. | The flip's whole point — those types project now; pins the warning's contract-derivation quieted for them. |
| Warning rail silent for `--adapter copilot` against `research` (no `command`) | **TDD** — integration test: install `research` via copilot; assert no `'dropped'` warning line. | Negative assertion; rail is contract-driven, not always-on. |
| User-scope hook-wiring / hook-body projection (validation gap — no shipped pack exercises it) | **TDD** — construction test rendering a **synthetic** user-scope hook pack to `~/.copilot/hooks/`. Assert both the `<name>.json` and the hook-body land at the user target. | The honest gap (`core` repo-only, `research` ships no hooks); a synthetic pack covers it without a shipped pack. |
| `copilot` is user-scope-capable | **Goal-based check** — assert `user_scope_capable_adapters_from_contract()` includes `"copilot"`. | Contract-derived; one assertion. |
| Schema admits the two new modes at every `dropped` site | **Goal-based check** — `grep -c '"dropped"'` vs the new modes present at each site (4 sites today; re-count at impl time). | Contract-data assertion; without it, schema-validated v0.10 loads reject. |
| `research`/`core` declare `version = "0.10"`; other packs unchanged at `"0.8"` | **Goal-based check** — grep the two `pack.toml`s for `"0.10"`; grep the rest stay `"0.8"`. | Two-pack-bump invariant; pins it is *not* all-pack. |
| Live Copilot CLI smoke (the generated artifacts load on the real tool) | **Manual QA** — render `core`+`research` via copilot, drop the artifacts into an isolated `COPILOT_HOME`/`probe-repo`, run the RFC-0024 T1–T8 fixtures against the then-current CLI; record version + results. | The one thing tests can't prove — that the bytes load on the real tool. |
| `make build-self FORCE=1` is a noop after the final commit | **Goal-based check** — clean `git status --short` after the run. | Build-pipeline gate. |
| `python3 tools/hooks/pre-pr.py` exits 0 | **Goal-based check** — aggregate enforcement (CI). | Covered by CI. |

## Acceptance Criteria

The spec is closed when each observable outcome is verifiable in the merged PR.

### Contract surface

- [x] **AC1.** `adapter.toml`'s `[contract] version` is `"0.10"` (was `"0.9"`); the header
  comment names this spec alongside existing RFC pointers. `adapter.schema.json` extends
  the projection-mode `enum` to admit **both** `"copilot-agent-md"` and
  `"copilot-hooks-json"` at **every** site that currently enumerates `"dropped"` (4 sites
  today — verify the count via `grep -c '"dropped"' adapter.schema.json` at impl time, since
  the schema may evolve). Without the enum extension at every site, schema-validated v0.10
  loads reject the contract on first run.
- [x] **AC1a.** Both `adapter.toml` and `adapter.schema.json` are **dual-copy**: the edits
  land byte-identically in `packages/agentbundle/agentbundle/_data/` **and** `docs/contracts/`.
  **Both copies are load-bearing** — `_data/` is the runtime/install read (`scope.py`'s
  `_load_bundled_contract`, `install.py`'s `_read_bundled`); `docs/contracts/` is the
  test/validate/lint read (`Makefile` validate, `tools/lint-agents-md.py`) — hence the
  byte-identity gates. **Two distinct tests** enforce parity: the **TOML** by
  `test_contract_files_byte_identical`
  (`packages/agentbundle/agentbundle/build/tests/test_contract.py`); the **schema** by
  `test_adapter_schema_copies_match`
  (`packages/agentbundle/tests/unit/test_contract_v0_3_schema.py` — the CI-only test root, not
  in `make build-check`). Editing only one copy of either file red-fails its gate. (The
  `dropped-primitives-coverage` plan named the dual-copy explicitly; this spec inherits it.)
- [x] **AC2.** Copilot projection-table changes in `adapter.toml`:
  - `primitive = "agent"` changes from `mode = "dropped"` to `mode = "copilot-agent-md"`,
    `target-path = ".github/agents/"`, `frontmatter-mapping = "copilot-agent-frontmatter-v0.10"`,
    `on-conflict = "prompt-then-preserve"`.
  - `primitive = "hook-wiring"` changes from `mode = "dropped"` to `mode = "copilot-hooks-json"`,
    `target-path = ".github/hooks/"`, `on-conflict = "prompt-then-preserve"`.
  - `primitive = "hook-body"` `target-path` changes from `"tools/hooks/"` to `".github/hooks/"`
    (mode stays `direct-file`, conflict stays `prompt-then-preserve`).
  - `primitive = "skill"` keeps `mode = "instruction-file"` and gains a user target so it
    projects to `~/.copilot/instructions/<name>.instructions.md` at user scope (repo target
    `.github/instructions/` unchanged).
  - `primitive = "command"` **stays** `mode = "dropped"` (copilot-cli#618/#1113).
- [x] **AC3.** `[adapter.copilot.scope]` gains `user = "~"`,
  `allowed-prefixes.user = [".copilot/agents/", ".copilot/instructions/", ".copilot/hooks/", ".agentbundle/"]`,
  and `allowed-prefixes.repo = [".github/instructions/", ".github/agents/", ".github/hooks/"]`
  (the legacy `tools/hooks/` prefix is removed, matching the hook-body move). The repo-only
  comment block is replaced with one citing RFC-0024 / ADR-0013.
  **Implementation divergence (2026-06-05):** `.agentbundle/` was added to
  `allowed-prefixes.user` (not in the spec's original list). The user-scope install writes
  its state file to `~/.agentbundle/state.toml`, which the path-jail validates against
  `allowed-prefixes.user`; without `.agentbundle/` the very first user-scope copilot install
  is refused. Every other user-scope-capable adapter (claude-code, codex) already lists it —
  the omission was a spec gap surfaced by the AC11 integration test. See Changelog.
- [x] **AC4.** New frontmatter mapping `[frontmatter-mapping."copilot-agent-frontmatter-v0.10"]`
  declares the per-key rules: `name` → `rename = "name"`, `description` →
  `rename = "description"`. `tools` is handled by the mode's allow-list pass-through (not a
  rename rule). `model` is **absent** from the mapping (dropped on projection). `target` is
  not emitted. The shape follows the existing per-key sub-table convention
  (`codex-agent-frontmatter-v0.8`, `kiro-*-agent-frontmatter-*`).
- [x] **AC5.** `claude-code`, `kiro-ide`, `kiro-cli`, and `codex` projection tables are
  byte-identical to v0.9 (no adapter but copilot changes).

### Projection-mode surface

- [x] **AC6.** New mode `copilot-agent-md` (`build/projections/copilot_agent_md.py`,
  dispatched from `build/adapters/copilot.py`) reads `.apm/agents/<name>.md`
  (YAML frontmatter + body), applies the `name`/`description` rename rules, **drops** `model`,
  **omits** `target`, passes `tools` through verbatim **after allow-list validation**, and
  emits `<name>.agent.md`. Observable: input `---\nname: foo\ndescription: bar\ntools: Read, Grep\nmodel: sonnet\n---\nBody.` produces a `.agent.md` whose frontmatter has `name: foo`,
  `description: bar`, `tools: Read, Grep`, **no** `model`, **no** `target`, and body `Body.`.
- [x] **AC7.** The tool allow-list fails the build on an unknown token and passes the known
  set verbatim. Observable: an agent declaring `tools: Read, Bogus` raises a build error
  naming `Bogus`; an agent declaring `tools: Read, Grep, Glob, WebFetch, WebSearch` emits
  that exact line (the web tools are *known-and-recorded*, not unknown). A read-only agent's
  emitted `tools` contains no `Edit`/`Write`/`Bash`.
- [x] **AC8.** New mode `copilot-hooks-json` (`build/projections/copilot_hooks_json.py`,
  dispatched from `build/adapters/copilot.py`) reads each `.apm/hook-wiring/<name>.toml` and
  emits **one** `<name>.json` per source file at the target, each a self-contained
  `{"version":1,"hooks":{<copilot-event>:[{"type":"command","bash":…,"powershell":…}]}}`.
  The event name is translated via the frozen map (`SessionStart`→`sessionStart`, etc.);
  an unmapped source event **raises a build error**. Observable: a `[[hooks.SessionStart]]`
  wiring with a `command` handler produces a JSON file whose `json.loads(...)` has key
  `version == 1` and `hooks.sessionStart[0].type == "command"`. **Shell-agnostic-source
  precondition:** the source command is carried into **both** `bash` and `powershell`
  handler keys (our shipped wiring is shell-agnostic — `python tools/...`). A wiring whose
  command is bash-only would emit a broken `powershell` handler; per-shell source commands are
  a follow-on, out of scope here (no shipped wiring needs them). **Hook-body-path rewrite
  (implementation clarification, 2026-06-05):** "carried into both shells" means
  shell-agnostic, **not** path-preserving — the carried command's legacy hook-body prefix
  `tools/hooks/` is rewritten to copilot's retargeted `.github/hooks/` so the emitted JSON
  references the script where `direct-file` actually lands it (required by AC9-repo; without
  it the adopter's `sessionStart` hook fires but can't find its script). This is **repo-scope**;
  resolving the command at *user* scope (`~/.copilot/hooks/`, arbitrary session CWD) is an
  unsolved follow-on — no shipped pack ships a user-scope copilot hook (core is repo-only), so
  it isn't exercised. See Changelog + `docs/backlog.md`.
- [x] **AC9-repo.** `copilot`'s `hook-body` projects to `.github/hooks/` (repo) via the existing
  `direct-file` mode — the scripts land alongside the `<name>.json` wiring that references them
  (the wiring command's `tools/hooks/` prefix is rewritten to `.github/hooks/` per AC8 so the
  reference is correct). No `tools/hooks/` output remains for copilot. (Verified by the T4
  adapter-level test, which emits repo-relpaths only.)
- [x] **AC9-user.** At user scope the same hook-body lands at `~/.copilot/hooks/` via AC10b's
  prefix rewrite. (Verified under AC11 / T4a, not the T4 adapter test — the `.copilot/` result
  is the install-time rewrite's, not the build adapter's.)

### Scope / resolver surface

- [x] **AC10.** `user_scope_capable_adapters_from_contract()` includes `"copilot"` after the
  scope-table edit, with **no** edit to `scope.py` (it keys off `[adapter.copilot.scope].user`
  presence). The install resolver's user-scope-capability subcheck no longer refuses copilot.
- [x] **AC10a.** `commands/install.py`'s `_render_for_user_scope` gains an explicit
  `target_adapter == "copilot"` dispatch branch (today its `else` raises
  `_AdapterResolutionRefused: "no user-scope projection wired for adapter 'copilot'"`). Without
  it, `install --pack research --adapter copilot` raises before any file is written. A test
  asserts copilot is no longer refused at the dispatch level.
- [x] **AC10b.** The build adapter emits **repo-relpaths** (`.github/{instructions,agents,hooks}/…`)
  and is scope-agnostic; user-scope install produces the divergent `~/.copilot/…` paths via a
  **post-render prefix rewrite** in `install.py` (sibling to `_rewrite_user_scope_hook_paths`),
  mapping `.github/instructions/`→`.copilot/instructions/`, `.github/agents/`→`.copilot/agents/`,
  `.github/hooks/`→`.copilot/hooks/` for **all** copilot primitives (skill, agent, hook-wiring,
  hook-body) **before** the path-jail check. (Unlike claude-code, whose skills share a prefix at
  both scopes and only hooks diverge, copilot's whole prefix changes — so the rewrite is not
  hook-gated.) The exact mechanism is the plan's design decision; the observable is AC11.
- [x] **AC11.** `install --pack research --adapter copilot` (user scope by default) is
  **accepted** (was refused via `allowed-adapters`) and projects `research`'s skills to
  `~/.copilot/instructions/` and its agents to `~/.copilot/agents/`. Path-jail compliance:
  every written path is under an `allowed-prefixes.user` entry (no path resolves under
  `~/.github/…` — the bug AC10b's rewrite prevents).

### Warning-rail surface (regression)

- [x] **AC12.** Installing `core` via `--adapter copilot --scope repo` emits the contract-driven
  warning naming **only** `command` (`ships 1 command that copilot projects as 'dropped'; …`),
  with **no** mention of `agent` or `hook-wiring` (those project natively now), and the install
  completes (rc 0). The `<compatible-list>` names the types copilot now projects for `core`
  (skill, agent, hook-wiring, hook-body). No copilot literal in the trigger.
- [x] **AC13.** Installing `research` via `--adapter copilot` emits **no** `'dropped'` warning
  line (research ships no `command`). The rail runs at both scopes.

### Pack-author surface

- [x] **AC14.** `packs/research/pack.toml` `[pack.adapter-contract] version` is `"0.10"`
  (was `"0.8"`) and `allowed-adapters = ["claude-code", "kiro", "codex", "copilot"]`.
  `packs/core/pack.toml` `[pack.adapter-contract] version` is `"0.10"` (was `"0.8"`); no
  `allowed-adapters` field added (already all-shipped). **No other pack's contract version
  changes** — the remaining packs stay at `"0.8"`.
- [x] **AC15.** `research`'s Copilot projection documents the `WebFetch`/`WebSearch`
  degradation (retrieval subagents lose live web access on Copilot — read/grep/glob only) in
  a pack-author-visible location under `packs/research/`. Wording names the cause (Copilot
  exposes no web tool to custom agents) and the residual capability.

### Documentation surface

- [x] **AC16.** `docs/specs/distribution-adapters/spec.md` Changelog gains a v0.9 → v0.10
  entry naming the copilot agent/hook-wiring flip, the two new modes, the scope-table edit,
  the skill user target, the hook-body move, and the two-pack bump. (Note: distribution-adapters
  has **no** v0.8 → v0.9 entry — RFC-0022's kiro-split bump left none — so the latest entry
  there is v0.7 → v0.8; the v0.9 → v0.10 entry is authored against that discontinuity, not
  back-filling the missing v0.9 one.)
- [x] **AC17.** `docs/backlog.md` gains/updates a `copilot-full-parity` section recording the
  spec → shipped milestone and the open follow-ons (the `command`/prompt-projection RFC gated
  on copilot-cli#618/#1113; any `WebFetch`/`WebSearch` re-map when Copilot exposes a custom-agent
  web tool). The stale backlog entry asserting copilot's `agent` is `dropped` — the RFC-0016
  open-question-1 item at `docs/backlog.md:238–244` — is the line this spec resolves; retire or
  update it specifically (do not correct a different line and miss it).
- [x] **AC18.** RFC-0012's Errata note links forward to RFC-0024 (already present at
  `docs/rfc/0012-…md` — verify it stands; do not duplicate). No new erratum authored here.

### Tests

- [x] **AC19.** Unit tests for `copilot-agent-md` at
  `packages/agentbundle/tests/unit/test_copilot_agent_md.py` (new module): trivial round-trip;
  `model` dropped; `target` omitted; `tools` verbatim for the known set; unknown-token build
  failure; read-only agent emits no write/execute tokens; `WebFetch`/`WebSearch` pass as
  known-recorded; empty body preserved.
- [x] **AC20.** Unit tests for `copilot-hooks-json` at
  `packages/agentbundle/tests/unit/test_copilot_hooks_json.py` (new module): one-file-per-wiring;
  the frozen event-name map for all six events; `bash`+`powershell` handler shape; unmapped-event
  build failure; `json.loads` round-trip.
- [x] **AC21.** Integration tests at
  `packages/agentbundle/tests/integration/test_install_copilot_full_parity.py` (new module):
  install `core` via copilot at repo scope → `.github/{instructions,agents,hooks}/` populated,
  only `command` dropped per the warning; install `research` via copilot at user scope (isolated
  `$HOME`) → `~/.copilot/{instructions,agents}/` populated and not refused; warning silent for
  `research`; the synthetic user-scope hook pack lands `~/.copilot/hooks/` (the validation gap).
- [x] **AC22.** Existing tests touching the v0.9 contract version, the copilot projection entries,
  the copilot repo-only scope, or `adapter.toml` shape are updated to v0.10 expectations.
  `pytest packages/agentbundle/` exits 0.

### Gates

- [x] **AC23.** Live Copilot CLI smoke (the RFC-0024 T1–T8 fixtures) run against the then-current
  CLI before merge; CLI version + per-test results recorded in **this spec's changelog** (durable,
  version-controlled — not only the PR description, which rots). **Done:** run on **CLI 1.0.60**
  (2026-06-05), 5 pass / 1 fail / 2 n/a — results in the Changelog. The single failure (T4,
  repo-scope hook *execution*) is a CLI-version-sensitive limitation (repo-scope hooks fired on
  1.0.59 per RFC-0024 Runs 2–4; not on 1.0.60), not a projection defect — our artifacts are
  byte-correct, agents project at both scopes, and user-scope hooks fire. Tracked in
  `docs/backlog.md`; no projection AC falsified.
- [x] **AC24.** `make build-self FORCE=1` produces a clean working tree (`git status --short`
  empty after the run).
- [x] **AC25.** `python3 tools/hooks/pre-pr.py` exits 0 on the merged tree.
- [x] **AC26.** CI gates (`build-check` linux + windows, `pytest` windows, docs lint suite) pass
  on the implementation PR.

## Assumptions

- Technical: Contract is at `version = "0.9"` today; RFC-0024/ADR-0013 specify the bump to
  `"0.10"` (source: `packages/agentbundle/agentbundle/_data/adapter.toml:30`, read 2026-06-05).
- Technical: Copilot today projects `agent = dropped`, `hook-wiring = dropped`,
  `hook-body = direct-file → tools/hooks/`, `skill = instruction-file → .github/instructions/`,
  and has a repo-only `[adapter.copilot.scope]` (no `user`) (source: `adapter.toml:386–421`,
  read 2026-06-05).
- Technical: `adapter.schema.json` enumerates `"dropped"` at 4 sites; each must also admit the
  two new modes or schema-validated v0.10 loads reject (source: `grep -c '"dropped"'
  adapter.schema.json` = 4, 2026-06-05).
- Technical: `research` is at contract `v0.8` with `allowed-adapters = ["claude-code", "kiro",
  "codex"]`; `core` is at `v0.8`, repo-only, no `allowed-adapters`; both bump to `"0.10"` — and
  this is *not* an all-pack bump (only these two ship the agents/hooks that need it) (source:
  `packs/research/pack.toml`, `packs/core/pack.toml`, read 2026-06-05).
- Technical: `core` is the only pack shipping `hook-body` and ships `agents`; `research` ships
  `agents` only; no other pack ships either — so the validation surface is exactly core+research
  and the `tools/hooks/`→`.github/hooks/` move has zero existing copilot hook-body consumers
  (source: `ls packs/*/.apm/`, 2026-06-05).
- Technical: Precedent modules `codex_agent_toml.py` + `merge_json.py` exist under
  `build/projections/`; `build/adapters/copilot.py` raises `ValueError` on any mode beyond
  `instruction-file`/`direct-file`; hook-wiring source is one `.toml` per file
  (`packs/core/.apm/hook-wiring/session-start.toml`, Claude-Code nested-event shape) (source:
  files read 2026-06-05).
- Technical: `user_scope_capable_adapters_from_contract()` keys purely off
  `[adapter.<name>.scope].user` presence — adding the `user` key makes the resolver include
  copilot with no `scope.py` edit (source: `scope.py:250`, read 2026-06-05). **But** the
  install user-scope render path needs *two* edits the contract alone can't supply: (a)
  `_render_for_user_scope` (`install.py:~2128`) has a per-adapter dispatch whose `else` raises
  for copilot — it needs a `copilot` branch; (b) the build adapter is scope-agnostic and emits
  repo-relpaths, so the divergent `.github/`→`.copilot/` user prefix is produced by a post-render
  rewrite (the seam claude-code uses via `_rewrite_user_scope_hook_paths` at `install.py:700`,
  there gated on `user-scope-hooks`) before the path-jail. Surfaced by adversarial review
  2026-06-05 (source: `install.py:2126–2147, 700`; `adapter.toml:134–147` claude-code
  scope-conditional table; read 2026-06-05).
- Technical: `adapter.toml` and `adapter.schema.json` are dual-copy
  (`packages/agentbundle/agentbundle/_data/` + `docs/contracts/`); `test_contract_files_byte_identical`
  enforces parity, so every contract edit lands in both (source:
  `packages/agentbundle/agentbundle/build/tests/test_contract.py:565`; `ls docs/contracts/`,
  2026-06-05).
- Technical: Copilot CLI/app **1.0.59** exposes **no** web tool to custom agents;
  `WebFetch`/`WebSearch` are silently ignored at load (no warning, no widening); confirmed
  Claude→Copilot mappings are `Read`→`view`, `Grep`→`grep`, `Glob`→`glob`; the `.agent.md`
  parser accepts the Claude comma-separated `tools:` format (source: two independent verifier
  runs 2026-06-05, settling RFC-0024 Open Q4; [VS Code custom agents
  docs](https://code.visualstudio.com/docs/agent-customization/custom-agents) confirm Claude-format
  acceptance).
- Technical: The hook event-name map (`sessionStart`/`sessionEnd`/`userPromptSubmitted`/
  `preToolUse`/`postToolUse`/`agentStop`) is fully verified to fire (source: RFC-0024
  § Acceptance Runs 2–4, CLI + app 1.0.59).
- Process: RFC-0012's Errata already links forward to RFC-0024 — that follow-on artifact is
  done; this spec verifies, not re-authors it (source: `docs/rfc/0012-…md:9–11`, read 2026-06-05).
- Process: Specs are living docs landing via normal PR; this is the implementing spec for an
  already-Accepted RFC, so no further RFC gate (source: `docs/CONVENTIONS.md:119, 262`).
- Product: Open Q4 resolves to **document-degradation** (option B) — omit `WebFetch`/`WebSearch`
  from any mapping and document the `research` Copilot degradation rather than inventing an
  unverified alias (source: two-run live verification + user confirmation 2026-06-05).
- Product: `command` stays dropped until copilot-cli#618/#1113 land; a follow-on RFC flips it
  (source: RFC-0024 Decision 5 / Open Q2).

## Changelog

- **2026-06-05 — implemented (PR for this spec).** All 26 ACs land in one PR. Two
  divergences from the spec-as-written, both surfaced by the integration tests and corrected
  in-PR (the spec is the validation gate; drift is a bug):
  - **AC3 `.agentbundle/` prefix.** `allowed-prefixes.user` gained `.agentbundle/` (state-file
    home) on top of the three `.copilot/` prefixes. Without it the first user-scope copilot
    install is path-jailed on `~/.agentbundle/state.toml`. AC3 updated.
  - **AC8 / AC9-repo — hook-body-path rewrite.** The carried hook-wiring command's legacy
    `tools/hooks/` prefix is rewritten to copilot's retargeted `.github/hooks/`, so the emitted
    `<name>.json` references the script where `direct-file` lands it. Surfaced while preparing
    the AC23 smoke: without it `core`'s `sessionStart` hook on Copilot fires but can't find its
    script (the unit tests asserted byte shape, not command↔body-location consistency; RFC-0024's
    T4 used a self-contained `echo` probe). Repo-scope only; user-scope hook-command resolution
    is a documented follow-on (`docs/backlog.md`) — no shipped pack ships a user-scope copilot hook.
  - **AC9-user / AC10b mechanism — file-based user-scope hooks.** The plan's T4a scoped the
    user-scope wiring as "dispatch branch + prefix rewrite". Landing copilot hooks at
    `~/.copilot/hooks/` (AC9-user, AC21's synthetic pack) additionally required teaching two
    pre-existing user-scope-hook rails about copilot's **file-based** hook model (distinct
    from claude-code's settings-merge and kiro's agent-json-merge): `(_adapter_supports_user_
    scope_hook_wiring)` now returns `True` for copilot's `copilot-hooks-json` array-form mode,
    and `(_merge_user_scope_hook_wiring)` returns no rows for copilot (its hooks are tracked as
    ordinary projection writes, not merge-owned rows). A hook-shipping copilot user-scope pack
    still declares `[pack.install] user-scope-hooks = true` (the adapter-agnostic Rail-B consent
    gesture). No change to claude-code / kiro behaviour. Recorded in `plan.md` Changelog too.
- **AC23 — live Copilot CLI smoke (recorded 2026-06-05).** RFC-0024 T1–T8 fixtures run against
  the **generated** `core`+`research` copilot artifacts. **Copilot CLI 1.0.60** (T6 n/a — app
  not tested), verifier JoeyMussAITech (run via Copilot). **5 pass · 1 fail (T4) · 2 n/a:**
  - **T1 ✅** repo-scope agents (`.github/agents/`) — all 4 `core` reviewers load, no frontmatter
    parse errors, selectable via `/agent`.
  - **T2 ✅** user-scope agents (`$COPILOT_HOME/agents/`) — `evidence-retriever`,
    `source-extractor` discovered globally from outside any repo.
  - **T3 ✅** tool mapping + read-only — read works; edit + shell refused ("read-only tool
    surface"); Claude tool names accepted. `WebFetch`/`WebSearch` absent from the agent tool
    surface (the documented degradation — declared in frontmatter, not surfaced by the CLI).
  - **T4 ❌** repo-scope hook (`.github/hooks/session-start.json`) — **the artifact is correct**
    (JSON parses, `version:1` + `sessionStart` key, valid `bash`/`powershell`, command path
    resolves) but **CLI 1.0.60 does not execute repo-scope `.github/hooks/`**: debug logs show
    only the user-scope hook fires, no repo-scope entry, no marker written. This is a **CLI-side
    behaviour**, not an artifact defect — and it is **version-sensitive**: RFC-0024 § Acceptance
    Runs 2–4 verified repo-scope hooks **firing on 1.0.59**. So repo-scope hook *execution*
    changed between 1.0.59 and 1.0.60 — re-verification against the copilot-cli changelog
    (1.0.8 / 1.0.41 / 1.0.51, re-checked on **1.0.61**) points to the documented folder-trust /
    prompt-mode opt-in gate on repo `.github/hooks/`, not a scope-wide regression (open
    conditional bug copilot-cli#1503 also skips repo hooks on `--resume`). The CLI loads
    `.github/agents/` (T1) but not `.github/hooks/` on 1.0.60 without that gate cleared. Tracked
    as a follow-on in `docs/backlog.md`; our projection is byte-correct and forward-compatible.
    No AC revised (AC9-repo is a *projection* contract — files land correctly — not a
    CLI-execution claim).
  - **T5 ✅** user-scope hook (`$COPILOT_HOME/hooks/`) fires globally — marker written, confirmed
    in debug log. (Confirms the file-based hook model + the user-scope path work end-to-end.)
  - **T6 n/a** — requires the Copilot app (tech preview).
  - **T7 ✅** user-scope instructions — all 7 `research` instruction files present in context,
    model lists them by name.
  - **T8 n/a** — `core` ships only a `SessionStart` wiring; the full 6-event map stands on
    RFC-0024 Runs 2–4 + the `copilot_hooks_json` unit test.

  **Verdict:** the spec's primary objective — subagents project to Copilot at both scopes with
  the read-only restriction preserved — is **verified on 1.0.60**. The one failure (T4) is a
  CLI-version-sensitive limitation on repo-scope hook *execution*, outside our artifacts'
  control; user-scope hooks (T5) work. See `docs/backlog.md` § copilot-full-parity.
