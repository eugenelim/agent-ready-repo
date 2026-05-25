# Spec: user-scope-hooks

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0005](../../rfc/0005-user-scope-hook-support.md)
  — sole driving RFC. Touches [RFC-0001](../../rfc/0001-bundle-distribution-by-adapter-spec.md)
  (closes Open Q1 for Kiro `hook-wiring`) and
  [RFC-0004](../../rfc/0004-install-scope-per-pack.md) (lifts the
  conditional Rail-B refusal it parked).

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Make hook-bearing packs installable across two adapter shapes that
RFC-0004 left refused:

1. **Claude Code at user scope** — a pack carrying hook bodies and
   wiring TOMLs installs at user scope (`agentbundle install --scope
   user`), with bodies projecting to `~/.claude/hooks/<pack>/<name>.{sh,py}`
   and wiring entries merging into the hand-edited shared
   `~/.claude/settings.json` under the `hooks` key. The merge is
   precise: a reinstall is byte-for-byte idempotent; an uninstall
   removes only entries the pack owns; an adopter hand-editing a
   collision-eligible entry gets a refuse-and-explain (or accepts
   ownership via `--force-merge`).
2. **Kiro at both repo and user scope** — the existing Kiro
   `hook-wiring` projection lifts out of `degraded-info-log` to
   a new mode `merge-into-agent-json` that merges hook entries into
   a pack-owned agent JSON at `<scope-root>/.kiro/agents/<attach-to-agent>.json`.
   Pack-side wiring TOMLs gain an optional `attach-to-agent` field
   (required for Kiro projection, ignored elsewhere); `validate`
   refuses Kiro-targeted wiring whose `attach-to-agent` names an
   agent the same pack doesn't ship, or whose event keys fall
   outside the adapter's declared `agent-event-vocabulary`.

A pack author opts into user-scope hook handling by declaring
`[pack.install] user-scope-hooks = true` (Claude Code shared-file
write and Kiro pack-owned-file write both gated by the same flag —
the consent gesture is "yes, my hooks land on the adopter's
machine outside per-project isolation"). Repo-scope Kiro promotion
needs no opt-in: repo-scope writes have always been allowed.

The CLI's user-facing surface gains:

- `install --scope user` accepting hook-bearing packs (was refused).
- `install` against Kiro projecting `hook-wiring` (was logged as
  deferred).
- `uninstall` / `upgrade` walking a new `hook-wiring-owned` state
  table to remove the right entries from the right files.
- A new `--force-merge` flag on `install` (Claude Code user scope
  only) for adopting hand-authored entries.
- A new `reconcile --scope user` read-only subcommand reporting
  orphans across both adapters' target files.

Success looks like a fixture pack containing hooks for either or
both adapters that installs, upgrades, and uninstalls with exit
code 0 across both scopes, and `reconcile --scope user` reporting
zero orphans after any well-formed sequence of those operations.

## Boundaries

The three-tier guard that keeps an implementing agent inside the
lines. *Always do* applies without asking; *Ask first* requires
human sign-off before proceeding; *Never do* is a hard rule, even
under time pressure.

### Always do

- **Run the gates** (`make build-check`) before declaring any task
  done, even if the task is "edit a markdown file." Self-hosted
  files mean unintended drift between `packs/<P>/seeds/` and
  `<repo>/` shows up here.
- **Use fixture packs under `tests/fixtures/` for every test.**
  Tests never touch the developer's real `~/.claude/settings.json`,
  `~/.kiro/agents/`, or `~/.agentbundle/`; tests set `$HOME` to a
  `tmp_path`-scoped directory and clean up.
- **Cite RFC-0005 by section name in any spec amendment.** The two
  follow-on spec amendments (`distribution-adapters/spec.md`,
  `agent-spec-cli/spec.md`) should reference RFC-0005 sections (e.g.
  *§ `merge-into-agent-json`*) so the durable rationale stays
  discoverable.
- **Update this spec when implementation diverges.** The contract
  is here; drift is a bug.

### Ask first

- **Renaming the `id` ownership tag** (e.g. `id` →
  `agentbundle-id`). Unresolved Q1 of RFC-0005 holds this open;
  the implementation will pin one or the other in the first
  user-scope-hook PR and the spec amendment should reflect that
  decision.
- **Changing the build-pipeline phase order** from `hook-body` →
  `agent` → `hook-wiring` → `command` → `skill`. The phase order
  is a new invariant; reordering needs review against every
  adapter's projection rules.
- **Touching the v0.2 → v0.3 state-file migration semantics.** The
  migration is declared header-only-additive; making it
  per-entry-rewriting changes adopter blast radius.

### Never do

- **No new top-level dependency.** Stdlib-only Python implementation
  per the existing `agent-spec-cli/spec.md` constraint; the JSON
  merger is built with `json` + `pathlib`. No `jq`, no `pydantic`,
  no `tomlkit`.
- **No new top-level directory.** All new code lives under
  `packages/agentbundle/`; all new tests under
  `packages/agentbundle/tests/`.
- **No write mode for `reconcile`.** `reconcile --scope user` is
  report-only; an adopter takes manual action from the report.
  A `--apply` flag is explicitly out of scope (RFC-0005 § Follow-on
  artifacts).
- **No projection changes for Copilot or Codex.** Their
  `hook-wiring` projection stays `dropped`; `hook-body` is
  unchanged. Touching them is a separate RFC.
- **No live writes to the developer's home directory from tests or
  CI.** Every test that exercises user-scope projection runs with
  `$HOME` pointed at `tmp_path`.
- **No translation between adapter event vocabularies.** A wiring
  TOML targeting Claude Code does not get its event names
  translated for Kiro projection (or vice versa). `agent-event-vocabulary`
  refuses cross-vocabulary projection at `validate` time.
- **No silent overwrites of unparseable JSON.** Whether the file is
  `~/.claude/settings.json` (Claude Code) or a pack-owned agent
  JSON (Kiro), unparseable input refuses with the refuse-and-explain
  shape RFC-0005 mandates.

## Testing Strategy

Three verification modes mapped per Objective behavior:

- **TDD** for everything with a compressible invariant — merge
  semantics, id-tag synthesis, idempotency, uninstall precision,
  shape-check refusals, validate-time rails, state-schema migration
  reads/writes. Construction tests live in
  `packages/agentbundle/tests/unit/` and
  `packages/agentbundle/tests/integration/`. Contract-shaped
  examples in the RFC (e.g. "merge-and-replace under the same
  `id`") map to construction tests one-to-one.
- **Goal-based check** for the build-pipeline phase-order
  invariant — a one-liner asserting the pipeline emits agent
  files before wiring merges run, verified by an integration test
  that inspects intermediate state. Also for the adapter-contract
  schema additions (`agent-event-vocabulary`, scope-conditional
  `target`) — JSON-schema validation passes/fails as a single
  shell check.
- **Visual / manual QA** is **not** used for this spec — no UI, no
  end-to-end UX flow. Every behavior in the Objective is
  expressible as a contract or a build-pipeline assertion.

**Fixture packs** are the load-bearing test shape:

- `tests/fixtures/packs/cc-user-hooks/` — Claude Code user-scope
  pack with `hook-body` + `hook-wiring`, `user-scope-hooks = true`,
  `allowed-scopes = ["user"]`.
- `tests/fixtures/packs/kiro-repo-hooks/` — Kiro repo-scope pack
  with `agent` + `hook-body` + `hook-wiring` (the wiring's
  `attach-to-agent` names the pack's agent).
- `tests/fixtures/packs/kiro-user-hooks/` — Kiro user-scope variant.
- `tests/fixtures/packs/malformed-*/` — negative fixtures: missing
  `attach-to-agent`, wrong-vocabulary events (PascalCase against
  Kiro), `attach-to-agent` naming an agent the pack does not ship.

Cross-adapter projection coverage falls out for free: the existing
build pipeline projects every pack against every reference adapter,
so the same Kiro fixtures (which ship wiring with `attach-to-agent`
and camelCase events) also project under Claude Code (where the
`attach-to-agent` field is ignored and events pass through
unfiltered). No dedicated cross-adapter fixture needed.

Every Acceptance Criterion maps to at least one fixture-pack
exercise.

## Acceptance Criteria

Schema and contract:

- [x] **AC1.** `adapter.toml` declares `[adapter.kiro.scope]` with
      `repo = "."`, `user = "~"`,
      `allowed-prefixes.user = [".kiro/", ".agentbundle/"]`.
      Schema validation passes.
- [x] **AC2.** `adapter.toml` declares
      `[adapter.kiro.projections.hook-wiring]` with
      `mode = "merge-into-agent-json"`, `managed-key = "hooks"`, and
      `agent-event-vocabulary` containing the five Kiro events
      verbatim. The legacy `[[adapter.kiro.projection]]`
      `degraded-info-log` entry is removed.
- [x] **AC3.** `adapter.toml` declares
      `[adapter."claude-code".projections.hook-wiring]` with
      `mode.repo = "merge-json"`, `mode.user = "user-merge-json"`,
      scope-conditional `target`, `managed-key.user = "hooks"`.
- [x] **AC4.** `adapter.toml` declares
      `[adapter."claude-code".projections.hook-body]` and
      `[adapter.kiro.projections.hook-body]` with
      scope-conditional `target` values per RFC-0005.
- [x] **AC5.** `pack.schema.json` accepts `[pack.install]
      user-scope-hooks = true` and refuses any non-boolean value;
      defaults to `false` when absent.
- [x] **AC6.** The `hook-wiring` TOML schema accepts an optional
      top-level `attach-to-agent` string field. `validate` against a
      Kiro-targeted pack refuses wiring without `attach-to-agent` or
      naming a non-same-pack agent with the exact refusal text
      RFC-0005 § Repo-scope Kiro promotion specifies.
- [x] **AC7.** Adapter contract version bumps to `0.3`.

Merge behavior (Claude Code user scope):

- [x] **AC8.** Installing a Claude Code user-scope pack into an
      empty `~/.claude/settings.json` writes the file with
      `hooks.<event>` arrays containing the pack's entries, each
      tagged with `id = "<pack>:<hook-basename>"`. No other top-level
      keys are touched.
- [x] **AC9.** Reinstalling the same pack at the same version is a
      byte-for-byte no-op on the settings file.
- [x] **AC10.** Installing a *second* pack with overlapping events
      appends its entries after the first pack's; the first pack's
      entries are not reordered. Both packs' IDs coexist.
- [x] **AC11.** Uninstalling one of two packs sharing an event
      removes that pack's entries only; the other pack's entries
      remain in their original positions; empty `hooks.<event>`
      arrays are removed (not left as `[]`).
- [x] **AC12.** A pre-existing adopter entry whose `command` field
      matches the pack's hook (after whitespace normalisation)
      causes `install` to refuse with the RFC-0005-specified text.
      `install --force-merge` adopts the entry; the original is
      preserved in a state-file snapshot.
- [x] **AC13.** Unparseable `~/.claude/settings.json` causes
      `install` to refuse non-zero without rewriting the file or
      recording state.
- [x] **AC14.** A `hooks` key present-with-wrong-type (e.g. array)
      causes `install` to refuse with the
      `<key-path> has unexpected shape` text. Same refusal for any
      `hooks.<event>` of wrong type.

Merge behavior (Kiro):

- [x] **AC15.** Installing a Kiro repo-scope pack with one agent and
      one wiring TOML writes the agent JSON to
      `.kiro/agents/<agent>.json` and merges the wiring's hook
      entries into that file's `hooks.<event>` array under the same
      array-append-with-id discipline as Claude Code.
- [x] **AC16.** The build pipeline projects the agent file before
      wiring projection runs (phase order
      `hook-body` → `agent` → `hook-wiring` → `command` → `skill`).
      A test asserting the file's existence at the wiring step's
      entry point passes.
- [x] **AC17.** A wiring TOML naming events outside Kiro's
      `agent-event-vocabulary` (e.g. PascalCase `UserPromptSubmit`)
      refuses at `validate` with the
      "not in adapter ... agent-event-vocabulary" text.
- [x] **AC17b.** The event-vocabulary check fires **only** when
      the resolved target adapter declares `agent-event-vocabulary`.
      Claude Code's projection does not declare the field
      (RFC-0005 § Declaration), so a wiring TOML with arbitrary
      event names projected against Claude Code passes `validate`.
      The vocabulary refusal is per-adapter, not per-RFC.
- [x] **AC18.** Kiro user-scope install writes to
      `~/.kiro/agents/<agent>.json` with hook entries whose
      `command` field resolves to the projected hook body on a
      fresh shell — i.e. running `sh -c "$command"` from any
      working directory locates and executes the body. Whether
      the field carries an absolute path or a `~`-relative path
      is an implementation choice; the observable is
      dispatchability.
- [x] **AC19.** Uninstalling a Kiro pack removes its
      `hook-wiring-owned` entries from the agent JSON and removes
      the agent file itself via the `direct-file` projection's
      uninstall.
- [x] **AC19b.** Upgrading a Kiro pack whose `attach-to-agent`
      value changes between versions (agent renamed, removed, or
      added) walks the OLD `target-file` to remove orphan entries
      AND the NEW `target-file` to add the new entries; state
      file's `target-file` is updated to the new value; after the
      upgrade, `reconcile --scope user` reports no orphans. Same
      shape covers agent added (no old-file walk) and agent
      removed (no new-file walk plus the agent primitive
      uninstall removes the old agent file).

State schema and migration:

- [x] **AC20.** State-file `schema-version` bumps from `0.2` →
      `0.3`. `[[installed]]` rows grow optional `adapter` and
      `hook-wiring-owned` fields. The `hook-wiring-owned` table
      rows carry `event`, `id`, and optional `target-file`.
- [x] **AC21.** `init-state --migrate` against a v0.2 file rewrites
      the `schema-version` line only. Existing rows are not
      backfilled. A v0.3 reader sees absent `adapter` as
      `claude-code`. For absent `target-file`: when the implied
      `adapter` is `claude-code`, default to `~/.claude/settings.json`
      (settings-file binding); `target-file` is **required** for
      Kiro rows (no implicit default — Kiro rows always carry the
      pack-owned `.kiro/agents/<agent>.json` path explicitly).
- [x] **AC22.** Write against a v0.2 state file refuses with the
      "run `agentbundle init-state --migrate` first" text.

CLI surface:

- [x] **AC23.** `install --scope user` against a pack with
      `user-scope-hooks = true` and a working user-scope target
      adapter (Claude Code with `mode.user = "user-merge-json"` or
      Kiro with `mode = "merge-into-agent-json"`) succeeds. Rail B
      no longer refuses such packs.
- [x] **AC24.** `install --scope user` against a pack lacking the
      `user-scope-hooks` flag refuses at `validate` with Rail B's
      existing refusal text.
- [x] **AC25.** `install --scope user` against an adapter that
      doesn't declare a working user-scope `hook-wiring` mode
      refuses with the RFC-0005-specified text.

> **Independent refusal — `kiro-ide-hook` at user scope.** Rail B
> as defined above gates *hook-shaped primitives* (`.apm/hooks/`,
> `.apm/hook-wiring/`) at user scope. RFC-0005's v0.4 amendment
> adds a separate `kiro-ide-hook` primitive that carries its **own**
> contract-layer user-scope refusal — independent of Rail B. A pack
> shipping only `.apm/kiro-ide-hooks/` (no Rail B trigger) still
> refuses at user scope because the primitive is repo-only in v1.
> Detail in
> [`docs/specs/distribution-adapters/spec.md` § v0.4 IDE event
> hooks (RFC-0005)](../distribution-adapters/spec.md#v04-ide-event-hooks-rfc-0005)
> and [`docs/specs/agent-spec-cli/spec.md` § v0.4 kiro-ide-hook
> primitive (RFC-0005)](../agent-spec-cli/spec.md#v04-kiro-ide-hook-primitive-rfc-0005).
- [x] **AC26.** `reconcile --scope user` reads both the Claude
      Code settings file (if exists) and every Kiro agent JSON
      named in user-scope `hook-wiring-owned` state. It reports two
      orphan classes: (a) entries the target file claims own but
      state doesn't know about, (b) state ownership records
      pointing at entries that no longer exist in the target file.
      Output is grouped by adapter and is read-only.

Verification:

- [x] **AC27.** `make build-check` exits clean with the amendments
      applied (no drift between `packs/<P>/seeds/` and `<repo>/`).
- [x] **AC28.** Every fixture pack named in § Testing Strategy is
      shipped under `tests/fixtures/packs/` and exercised by at
      least one test.
- [x] **AC29.** No test or CI step writes to `~/.claude/`,
      `~/.kiro/`, or `~/.agentbundle/` outside a `tmp_path`-scoped
      `$HOME`.
