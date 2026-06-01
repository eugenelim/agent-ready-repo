# RFC-0005: Hook support across Claude Code and Kiro

- **Status:** Accepted
- **Author:** eugenelim
- **Date opened:** 2026-05-23
- **Date closed:** 2026-05-25
- **Extends:** [RFC-0004](0004-install-scope-per-pack.md) — lifts the
  conditional Rail-B refusal it parked.
- **Amends [`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md):**
  - projection forks for `hook-body` and `hook-wiring` under
    `claude-code` (user scope) and `kiro` (both scopes)
  - Rail B becomes conditional
  - Kiro `hook-wiring` lifts out of `degraded-info-log`
  - Kiro gains a `[scope]` table
  - `hook-wiring` TOML schema grows an optional `attach-to-agent` field
  - contract gains a new `kiro-ide-hook` primitive (Kiro projection;
    `dropped` on every other adapter)
  - sibling declarative lists `ide-event-vocabulary` and
    `ide-action-vocabulary` join `agent-event-vocabulary` on the Kiro
    adapter
  - contract version bumps `0.3 → 0.4`
- **Amends [`docs/specs/agent-spec-cli/spec.md`](../specs/agent-spec-cli/spec.md):**
  - `install` / `uninstall` / `upgrade` gain user-scope hook handling
  - per-entry ownership record in state
  - build-pipeline ordering invariant: agent projects before its
    wiring merges; `hook-body` projects before `kiro-ide-hook` so
    cross-primitive references can resolve

## Summary

[RFC-0004 § Adapter-level scope roots](0004-install-scope-per-pack.md#adapter-level-scope-roots-and-projection-forks)
refused hook-shaped primitives at user scope and named the missing
piece *"hook-wiring merge story"* in shorthand. The real scope is
**both** hook primitives — and the design has to cover two adapters
whose hook architectures bind to different files. This RFC designs
both forks:

- **Claude Code** binds hooks in a settings file. `hook-body` reroots
  from `tools/hooks/` to `~/.claude/hooks/` at user scope; a new
  projection mode `user-merge-json` merges `hook-wiring` into the
  hand-edited shared `~/.claude/settings.json` (no `.local`
  suffix).
- **Kiro** binds hooks inside agent JSON. A new projection mode
  `merge-into-agent-json` merges `hook-wiring` into a pack-owned
  agent file at `.kiro/agents/<attach-to-agent>.json` (the wiring
  TOML gains an `attach-to-agent` field naming a same-pack agent);
  `hook-body` rests in `tools/hooks/` at repo and `~/.kiro/hooks/`
  at user. **This closes RFC-0001 Open Q1 (Kiro
  `degraded-info-log`) at *repo* scope** — the longest-standing
  hook-related gap in the adapter contract — and simultaneously
  extends Kiro to user scope. The blocker turned out to be
  architectural (hooks-in-agent-JSON), not schema-publication.
- **Kiro IDE event hooks** are architecturally separate from CLI
  agent-bound hooks: they live in standalone `.kiro/hooks/<name>.kiro.hook`
  JSON files that Kiro fires on IDE-surface events
  (file create / save / delete, prompt submit, agent stop, manual
  trigger, etc.). The firing condition is the IDE event itself, not
  the agent identity — file-event hooks (`fileSave`, `fileCreated`,
  etc.) fire even with no agent active, while agent-runtime-event
  hooks (`preToolUse`, `agentStop`, `postTaskExecution`, etc.) fire
  on whichever agent the adopter is using. A new primitive
  `kiro-ide-hook` covers them — source
  `.apm/kiro-ide-hooks/<name>.kiro.hook`, projected `direct-file`
  to `.kiro/hooks/<pack>/<name>.kiro.hook` for the Kiro adapter,
  `dropped` on every other adapter, repo-scope only in v1 (user
  scope is gated on upstream Kiro
  [#5440](https://github.com/kirodotdev/Kiro/issues/5440)).

The contract's Rail-B refusal becomes conditional on either mode
being declared by the adapter; user-scope state grows an ownership
record so uninstall is precise. The build pipeline gains a new
invariant: agents project before their wiring merges. No pack —
user-scope or otherwise — ships in this RFC; naming the first
user-scope hook-bearing consumer is deferred, following the
precedent RFC-0004 set in its *Alternatives considered* item 8
(mechanics land ahead of a named consumer because doing them under
release pressure means corners cut).

## Motivation

Rail B refuses every hook-bearing pack at user scope today. It was
the right call when RFC-0004 landed — the merge semantics weren't
designed and a hand-edited shared file is genuinely riskier than a
pack-owned `.claude/settings.local.json`. But the deferral is now
the load-bearing blocker for the first user-scope pack carrying any
hook (a personal-review session hook, a cross-project lint nudge, a
clipboard-aware skill that wires into `UserPromptSubmit`). Today's
adopter copies the script and hand-edits `~/.claude/settings.json`,
outside upgrade, outside uninstall, outside the Tier model — exactly
the squatter problem RFC-0001 set out to solve and that RFC-0004
extended to user scope for everything *except* hooks.

The asymmetry is awkward: a user-scope pack can ship skills,
agents, and commands, but not the small executable glue that makes
those primitives reach the right runtime events. Until that gap
closes, the cross-project pack shape RFC-0004 enabled is partial.

**Kiro has been parked at `degraded-info-log` for a different but
adjacent reason.** Kiro's hook architecture binds hook entries
inside each agent's JSON at `.kiro/agents/<name>.json` under a
`hooks` key (events: `agentSpawn`, `userPromptSubmit`,
`preToolUse`, `postToolUse`, `stop`) rather than to a separate
settings file. The repo's `hook-wiring` primitive — a TOML that
merges into a settings file under a `hooks` key — had no natural
projection target in Kiro, so [`adapter.toml`](../../packages/agentbundle/agentbundle/_data/adapter.toml)
held Kiro at `degraded-info-log` with the rationale string "schema
not yet published." The rationale was wrong-in-spirit; the schema
*has* been observable in the Kiro IDE and the user-scope agent
directory is documented at
[`kiro.dev/docs/cli/custom-agents/creating/`](https://kiro.dev/docs/cli/custom-agents/creating/)
(`~/.kiro/agents/` for global, `.kiro/agents/` for workspace). The
true blocker was that the wiring primitive merged into a
settings-file shape that Kiro doesn't have. Designing a second
projection mode (`merge-into-agent-json`) is the structural fix —
and once we're designing one new mode for Kiro, doing it alongside
Claude Code's user-scope work is cheaper than two sequential
RFCs.

**Kiro IDE event hooks are the third surface left unaddressed.**
The per-agent CLI fix above does not cover IDE hooks
([`kiro.dev/docs/hooks/`](https://kiro.dev/docs/hooks/),
[`hooks/types`](https://kiro.dev/docs/hooks/types),
[`hooks/examples`](https://kiro.dev/docs/hooks/examples/)) — they
live in standalone `.kiro/hooks/<name>.kiro.hook` JSON files and
fire on IDE-surface events regardless of which agent is active.
A pack that wants to ship — say — a "Run the linter when a `.py`
file saves" automation for Kiro has no projection target today:
the pack author either documents a manual setup step (the Tier-2
squatter problem RFC-0001 set out to eliminate), or wires it as a
per-agent CLI hook via `merge-into-agent-json` (which fires only
while the attached agent is active — the wrong condition for an
"on save, every time" trigger). Neither is right; both are
documented anti-patterns in the existing § *Cross-adapter
semantic asymmetry* drawback. Adding a third surface (`kiro-ide-hook`)
alongside the two CLI surfaces this RFC already designs keeps all
the Kiro-side hook decisions in one place, and reuses the
declarative-vocabulary discipline § `agent-event-vocabulary`
introduces.

## Proposal

### `hook-body` at user scope — scope-conditional target on `direct-file`

`hook-body` already projects as `direct-file` across every adapter
([distribution-adapters/spec.md § Primitive projection
table](../specs/distribution-adapters/spec.md#primitive-projection-table),
lines 179–180). The byte-for-byte projection rule is correct at
both scopes — only the destination root differs. Introducing a
brand-new mode just to change a path would be ceremony.

The proposal is to keep `direct-file` and let the projection
*target* fork per scope, declared in `adapter.toml`:

```toml
[adapter."claude-code".projections.hook-body]
mode = "direct-file"
target.repo = "tools/hooks/<name>.{sh,py}"
target.user = ".claude/hooks/<name>.{sh,py}"
```

The schema for `target` becomes a string-or-scope-map:

- A bare string is shorthand for `target.repo = "..."` (legacy
  behaviour for v0.1 adapters and any v0.2 adapter that declares
  only `repo` scope).
- A table with `repo` and/or `user` keys declares a target per
  scope; the resolved target must exist for the scope the install
  is happening at, or the contract refuses.

This shape composes cleanly with `[adapter.<name>.scope]`'s
`allowed-prefixes.user`: the user-scope target string must resolve
under one of the declared prefixes, which is already true for
`.claude/hooks/` under `.claude/` (the existing v0.2 prefix per
[distribution-adapters/spec.md § `[scope]` table](../specs/distribution-adapters/spec.md#scope-table-on-the-adapter-contract),
lines 219–243 — `allowed-prefixes.user = [".claude/", ".agentbundle/"]`).

**Why not a new `direct-file-scope-aware` mode?** Modes are about
*how* bytes move; path-only forks belong in `target`. A new mode is
justified only when the merge algorithm itself differs — as
`user-merge-json` does (array-append-with-id vs key-replace). For
`hook-body`, only the destination root changes; forking the mode
would be shape inflation.

**Kiro adopts the same shape at user scope.** Kiro's `hook-body`
projection today is `direct-file → tools/hooks/`. With Kiro
gaining a `[scope]` table in this RFC (see § `merge-into-agent-json`
below), the natural user-scope target is `~/.kiro/hooks/<pack>/<name>.{sh,py}`
— same pack-namespaced layout as Claude Code, for the same
reason (uninstall-by-directory-removal, no name collisions across
packs). Kiro doesn't have a fixed `~/.kiro/hooks/` *read* path
the way Claude Code does — Kiro hooks resolve via the agent
JSON's `command` field, which carries an absolute or
`~`-relative path. The CLI computes that absolute path at install
time and bakes it into the projected agent JSON's `hooks` array.
Multi-machine sync risk (an absolute path baked in on machine A
won't resolve on machine B with a different `$HOME`) is the same
class as the existing multi-machine drawback below; same
mitigation (sync `~/.agentbundle/` and re-install on the second
machine).

### `hook-wiring` for Claude Code at user scope — `user-merge-json` mode

`hook-wiring` cannot reuse `merge-json` as it stands.
`merge-json` today targets a **pack-controlled** file
(`.claude/settings.local.json`) — Claude Code reads it but no
human edits it; the CLI owns the file outright. The user-scope
equivalent is `~/.claude/settings.json`, which is:

1. Hand-edited by the adopter (themes, model overrides, env vars).
2. Read and written by Claude Code itself.
3. Shared with every other pack and tool that touches user settings.

A new projection mode `user-merge-json` captures the additional
discipline this surface requires.

#### Declaration

```toml
[adapter."claude-code".projections.hook-wiring]
mode.repo = "merge-json"
target.repo = ".claude/settings.local.json"
mode.user = "user-merge-json"
target.user = ".claude/settings.json"
managed-key.user = "hooks"
```

The `mode` field becomes a string-or-scope-map under the same
schema rule as `target` above. The new `managed-key.user` field
names the top-level JSON key the merger writes under at user scope
(today: `hooks`). It exists so future user-scope merge needs
(`env`, `mcpServers`) can reuse the mode without re-deriving the
key. At repo scope `managed-key` is implied by the existing
`merge-managed-key-only` on-conflict policy; at user scope we
require it explicitly because the file has other top-level keys
that are *not* ours and must never be touched.

#### Merge semantics

`user-merge-json` writes under `<managed-key>.<event>` (e.g.
`hooks.UserPromptSubmit`) using **array-append-with-id**, not
key-replace:

1. The CLI loads the existing `~/.claude/settings.json`. If the
   file is missing, it is created with `{}`. If the file is present
   but the `hooks` key is absent, it is auto-initialised to `{}` on
   write; if `hooks.<event>` is absent for the event being wired, it
   is auto-initialised to `[]`. Only the present-with-wrong-type
   case (see § Failure modes) refuses.
2. For each hook entry the pack wires, the CLI synthesizes an
   `id` of the form `<pack-name>:<hook-source-basename>` (e.g.
   `personal-reviewers:on-prompt`). This `id` is the ownership
   tag and is recorded in user-scope state (see § State-file
   impact).
3. The merger appends each entry under `hooks.<event>` if no
   entry with the same `id` exists yet, or replaces the existing
   entry in place if one does. The position in the array is
   preserved across reinstall so adopter-set ordering survives.
4. Adopter-authored entries (entries without an `id` matching any
   installed pack's owned IDs) are never reordered, never
   rewritten, and never read by the merger except to detect
   collisions (later bullet).

Claude Code today doesn't require `id` on hook entries; the CLI
emits it as a non-functional tag (it sits alongside the entry's
`command` / `type` fields without affecting runtime). If a future
Claude Code release ever uses the key for something else, this
RFC holds an Unresolved question (below) for renaming the tag.

#### Idempotency under reinstall

Reinstalling the same pack at the same version is a no-op:
identical IDs, identical entries, in the same positions. Reinstall
at a different version replaces only the entries the CLI owns;
adopter-authored entries are not disturbed. The on-disk file diff
is empty for a same-version reinstall.

#### Uninstall — remove just our entries

`uninstall --scope user <pack>` walks the user-scope state's
ownership record for that pack, locates every `(event, id)` pair
the install recorded, removes those entries from the in-memory
`hooks.<event>` arrays, and rewrites the file. Empty
`hooks.<event>` arrays are removed (not left as `[]`) to keep the
file tidy. Adopter-authored entries are never inspected beyond
identity comparison.

If the user has hand-edited an entry the CLI owns (matching `id`
but altered `command`), uninstall removes it anyway and logs
`note: removed user-edited entry <id>; original command preserved in <state-backup-path>` —
the state file's previous snapshot serves as the recovery path.
Refusing to uninstall would strand the entry forever; silently
overwriting hand-edits would be worse.

#### Conflict — two user-scope packs claim the same hook event

Multiple packs may wire entries to the same `event` (e.g. two
packs both subscribing to `UserPromptSubmit`). This is **not** a
conflict: their entries coexist as separate items in the
`hooks.UserPromptSubmit` array, each tagged with its owner's `id`.
Claude Code runs the array in declared order.

The genuine conflict is **two packs producing the same `id`** —
i.e. two packs publishing the same name and the same
`hook-source-basename`. The CLI refuses install with stderr
`pack <P>'s hook <name> collides with already-installed pack <Q>'s hook of the same id`.
The fix is on the pack-author side (rename a hook); the CLI has no
policy for picking a winner.

**Ordering is append-only across sessions.** A later install
appends its entries after every entry already in
`hooks.<event>` — owned or adopter-authored — and never reorders.
The alphabetical rule below applies **only** as a tie-break inside
a single install session (e.g. when a single `agentbundle install`
invocation lands multiple packs at once, or one pack wires N hooks
to the same event):

- Within a session, entries are appended in **ASCII codepoint
  order on the lowercased pack name** (so `Personal-Reviewers` and
  `personal-reviewers` collate identically and pack-name
  capitalisation doesn't reorder things across machines).
- Within a single pack wiring N hooks for one event, entries
  land in `sorted(os.walk(...))` order over
  `.apm/hook-wiring/<name>.toml` filenames — applying the
  `sorted(os.walk(...))` determinism rule
  ([`distribution-adapters/spec.md:348-350`](../specs/distribution-adapters/spec.md),
  established for skill-directory enumeration) to the
  `hook-wiring` source surface. The cited lines give the
  shape of the rule; the path it walks here is `.apm/hook-wiring/`,
  not `.apm/skills/`.

Adopters who want a different order edit the array directly; the
CLI never re-sorts on subsequent installs (idempotency, above,
preserves array position by `id`).

#### Failure modes for unparseable user settings

If `~/.claude/settings.json` exists but is unparseable JSON, the
CLI refuses non-zero with stderr
`cannot parse <path>: <error>; fix or back up the file and retry`.
The file is **not** rewritten and no partial state is recorded.
This matches the refuse-and-explain shape RFC-0004 used for v0.1
state-file writes and the major-version contract refusal in
[`agent-spec-cli/spec.md`](../specs/agent-spec-cli/spec.md).

If the file is present, parseable, but `hooks` (or any
`hooks.<event>` the install would touch) is present with the wrong
shape — e.g. `hooks` is an array instead of an object, or
`hooks.UserPromptSubmit` is a string instead of an array — the CLI
refuses with
`<path>: <key-path> has unexpected shape <type>; expected <expected>`
(where `<key-path>` is `hooks` or `hooks.<event>` as relevant) and
offers no auto-repair. The same refusal covers both the top-level
and per-event cases — the merger shape-checks every key it would
write through **that exists on disk**; absent keys are
auto-initialised per § Merge semantics step 1. Hand-edited
shared state is too load-bearing to "fix up" silently.

#### User-already-set-this-key collision rule

If the adopter has hand-authored an entry under
`hooks.<event>` whose `command` field matches what the pack is
about to install (textual equality after whitespace
normalisation), the CLI refuses install with
`pack <P>'s hook <name> at event <event> appears to be already wired in <path>; remove the manual entry or pass --force-merge to take ownership`.

`--force-merge` exists for the case where an adopter manually
installed the same content earlier and is now adopting the pack
proper; it replaces the manual entry with the tagged one and the
old text is preserved in the state-file snapshot.

**Binding and interaction with `--force`.** `--force-merge` is a
separate flag from RFC-0004's `--force`
([`agent-spec-cli/spec.md:326-327`](../specs/agent-spec-cli/spec.md)
restricts `--force` to the dual-scope install conflict case and
explicitly refuses to extend it). The two flags are **orthogonal**
— `install --force --force-merge` is permitted; each addresses a
different refusal. `--force-merge` is:

- bound to `install` only (`unknown flag for <verb>` on any other);
- bound to `--scope user` (refused at repo scope: hook-wiring
  there targets a pack-owned file, so manual-collision is a
  non-case);
- a no-op when no textual collision is detected — same
  idempotent-when-no-conflict shape as `--force`, so wrapper
  scripts can pass it unconditionally.

### `hook-wiring` for Kiro at both scopes — `merge-into-agent-json` mode

Kiro's hook architecture binds hook entries inside each agent's
JSON at `.kiro/agents/<name>.json` under a `hooks` key. The
projection target is a **pack-owned** file (the same pack ships the
agent body and the wiring; both project into the same JSON), so
the discipline is closer to Claude Code's existing repo-scope
`merge-json` than to its user-scope `user-merge-json` — there's no
hand-edited adopter content to worry about inside *the pack's own
agent file*. But the merge has to land under a per-agent target,
not a per-adapter one, which neither of the existing modes
expresses.

A new projection mode `merge-into-agent-json` captures this.

#### Adapter declaration

```toml
[adapter.kiro.projections.hook-wiring]
mode = "merge-into-agent-json"
target.repo = ".kiro/agents/<attach-to-agent>.json"
target.user = ".kiro/agents/<attach-to-agent>.json"
managed-key = "hooks"
agent-event-vocabulary = [
  "agentSpawn",
  "userPromptSubmit",
  "preToolUse",
  "postToolUse",
  "stop",
]
```

- **`target.<scope>`** carries the `<attach-to-agent>` placeholder
  — resolved per wiring entry from the pack-side TOML (next
  section). Both repo and user scope use the same relative path;
  the scope-root resolves to `<repo>/` and `~/` respectively.
- **`managed-key = "hooks"`** names the JSON key the merger writes
  under inside the agent file. Same role as `managed-key.user` in
  the Claude Code user-scope design, but a plain string here
  because Kiro uses the same key at both scopes.
- **`agent-event-vocabulary`** is the **declarative** list of
  event names this adapter accepts. `validate` refuses any
  pack-side wiring TOML naming an event outside the list
  (PascalCase events from Claude Code's vocabulary fail this
  check against Kiro). The list lives in the contract, not in
  CLI source — third-party adapter declarations can introduce
  their own vocabularies without CLI changes. See the §
  Repo-scope Kiro promotion subsection for the refusal text
  shape, and Unresolved Q5 for the open question on whether the
  per-namespace *identifier* (here implicitly the adapter name
  `kiro`) should be a closed enum across the contract.

The same `[adapter.kiro.scope]` table that user-scope Kiro needs
ships here too:

```toml
[adapter.kiro.scope]
repo = "."
user = "~"
allowed-prefixes.user = [".kiro/", ".agentbundle/"]
```

User-scope Kiro is documented at
[`kiro.dev/docs/cli/custom-agents/creating/`](https://kiro.dev/docs/cli/custom-agents/creating/):
the global agents directory is `~/.kiro/agents/`. The user-scope
prefix is `.kiro/`; CLI infrastructure shares the
`.agentbundle/` prefix already established for Claude Code.

#### Pack-side schema — the `attach-to-agent` field

The wiring TOML grows an **optional** top-level field:

```toml
# packs/<P>/.apm/hook-wiring/check-clipboard.toml
attach-to-agent = "personal-reviewer"

[[hooks.userPromptSubmit]]
command = "$HOOK_BODY_PATH"
matcher = ""
```

- For **Claude Code projection**, the field is **ignored** (the
  wiring lands in the settings file regardless of which pack agent
  is "logically" attached).
- For **Kiro projection**, the field is **required**. Missing or
  pointing at an agent the same pack does not ship is a
  `validate` refusal:
  `pack <P>'s hook-wiring <name>.toml does not declare 'attach-to-agent' (or names an unknown agent); required for kiro projection`.
- For adapters that drop `hook-wiring` (Copilot, Codex), the field
  is irrelevant — the wiring isn't projected at all.

`attach-to-agent` is **single-valued**, not a list. Wiring N
hooks into the same agent uses N entries under
`[[hooks.<event>]]` in the same TOML. Wiring the same body into
multiple agents requires N wiring TOMLs (one per agent), each
referencing the same hook body via `command`. Multi-target wiring
adds complexity we don't have a consumer for; defer to a future
RFC if a pack ever needs it.

#### Merge semantics

The same array-append-with-id discipline as `user-merge-json`,
applied to the agent JSON's `hooks.<event>` arrays:

1. The CLI loads `<scope-root>/.kiro/agents/<attach-to-agent>.json`.
   The file is **guaranteed to exist** because the build-pipeline
   ordering invariant (below) projects the agent first.
2. Each hook entry gets `id = "<pack-name>:<hook-source-basename>"`,
   same as Claude Code.
3. Append-with-id under `hooks.<event>`, same idempotency / replace
   semantics.
4. Adopter-authored entries are an edge case worth naming
   explicitly: the agent JSON is **pack-owned**, so adopter
   hand-edits to the agent file are squatting on a managed
   surface. The CLI does not enforce — adopters who edit the
   projected agent JSON take the consequences (next `upgrade`
   replaces the file via the agent primitive's `direct-file`
   projection, dropping their edits). Same shape as any other
   adopter hand-edit to a CLI-owned file.

#### Build-pipeline ordering invariant

The build pipeline that produces the projected layout (per
[RFC-0002](0002-self-hosting.md)) currently projects primitives in
an unspecified order. With `merge-into-agent-json`, the pipeline
gains an invariant: **for any pack containing both `agent` and
`hook-wiring` primitives, every agent's `direct-file` projection
must complete before any wiring's `merge-into-agent-json`
projection runs against the same agent file.** The simplest
implementation: a fixed phase order — `hook-body` → `agent` →
`hook-wiring` → `command` → `skill` — applied uniformly across
adapters. `command` and `skill` land after `hook-wiring` because
neither reads the agent JSON during projection (commands project
verbatim to a separate target path; skill projection works on
skill-source files, not agent files), so their position relative
to hook-wiring is free; placing them last keeps the phases
predictable. The ordering is a no-op for Claude Code (which
doesn't read the agent file during wiring projection) but
mandatory for Kiro.

**Cross-pack ordering is not introduced.** Packs install
serially today, and the `attach-to-agent` field is restricted
to same-pack agents (see § Pack-side schema — the `validate`
rail refuses an `attach-to-agent` that names an agent the same
pack does not ship). No pack writes into another pack's agent
file, so the pipeline-ordering invariant remains intra-pack.
This is the same shape as the rest of the projection contract:
pack content is closed under its own source tree.

#### Conflict, idempotency, uninstall

Same rules as `user-merge-json`:

- **Conflict (same `id`):** refused with the same error string,
  except the path in the error message is the agent file rather
  than the settings file.
- **Idempotency:** reinstall at the same version is a no-op; the
  array position is preserved by `id`.
- **Uninstall:** the user-scope state's ownership record
  identifies every `(agent-file, event, id)` tuple the pack owns;
  uninstall removes them from each agent file's `hooks.<event>`
  arrays and rewrites the agent file. Empty `hooks.<event>`
  arrays are removed; an empty `hooks` object is left in place
  (the agent file still belongs to the pack; the agent primitive's
  uninstall handles file removal).

#### Failure modes

- The agent file is missing at merge time → the pipeline-ordering
  invariant has been violated. The CLI refuses with
  `internal: <agent-file> missing at hook-wiring merge time; agent must project before wiring` —
  this is a CLI-internal bug, not adopter-fixable. The
  `validate`-time check ensures the pack ships the named agent,
  so the only way to hit this is a pipeline-ordering regression.
- The agent file is malformed JSON → same refuse-and-explain
  shape as the Claude Code path:
  `cannot parse <path>: <error>; fix or back up the file and retry`.
  This case usually only fires under adopter hand-edit
  to a pack-owned file (a squatter on the pack-owned surface);
  the message is the same regardless.
- `hooks` or `hooks.<event>` is present-with-wrong-type → same
  `<path>: <key-path> has unexpected shape <type>; expected <expected>`
  refusal.

#### What this section does NOT add

- **No new `--force-merge` flag for Kiro.** The agent file is
  pack-owned, not adopter-shared, so there's no
  "adopter-already-set-this-key" case. `--force-merge` stays
  Claude Code only (per its existing § Binding subsection).
- **No translation layer between adapter event vocabularies.**
  The `agent-event-vocabulary` declarative list provides
  validate-time refusal of cross-vocabulary projections (e.g. a
  Claude-Code-shaped wiring TOML projected against Kiro refuses
  on event-name mismatch). This RFC does not introduce a
  translation layer that would let a Claude-Code-shaped wiring
  run on Kiro or vice versa; a pack targeting both adapters
  ships separate wiring TOMLs per adapter or restricts
  `allowed-adapters`. Translation belongs in a separate RFC if
  it ever lands.

### Kiro IDE event hooks — new `kiro-ide-hook` primitive

The two preceding sections cover *agent-bound* hooks: they fire
only while the attached agent is active. Kiro IDE event hooks are a
separate surface — standalone `.kiro/hooks/<name>.kiro.hook` JSON
files Kiro reads at workspace open and fires on IDE-surface events
(file create / save / delete, prompt submit, agent stop, tool use,
task execution, manual trigger). They are not bound to a *specific*
agent — the trigger is the IDE event. File-event triggers
(`fileSave`, `fileCreated`, `fileDeleted`, `fileEdit`,
`promptSubmit`) fire even when no agent is active;
agent-runtime-event triggers (`preToolUse`, `postToolUse`,
`agentStop`, `preTaskExecution`, `postTaskExecution`) fire during
agent operation but for whichever agent the adopter is using, not
one named in the hook.

The two declarative-list affordances `ide-event-vocabulary` and
`ide-action-vocabulary` introduced below carry the same
adapter-table discipline as `agent-event-vocabulary` (see
§ *Sibling vocabularies for IDE event hooks*, inside
§ *Validate-time rule lift*, for the full vocabulary semantics).

The natural primitive is shaped like the existing `hook-body`: one
source file per hook, projected `direct-file` into a
pack-namespaced subdirectory of the target.

#### Pack-side source

```toml
# adapter.toml
[primitive."kiro-ide-hook"]
source-path = ".apm/kiro-ide-hooks/"
```

Source files are hand-authored JSON, one file per hook, named
`<name>.kiro.hook`. The schema follows the observed `.kiro.hook`
shape Kiro reads ([hook docs](https://kiro.dev/docs/hooks/),
[examples](https://kiro.dev/docs/hooks/examples/),
[community guide](https://aicodingtools.blog/en/kiro/kiro-hooks-guide)):

```json
{
  "name": "Lint on save",
  "description": "Run ruff when a Python file is saved.",
  "version": "1",
  "when": {
    "type": "fileSave",
    "patterns": ["**/*.py"]
  },
  "then": {
    "type": "askAgent",
    "prompt": "Run ruff on the just-saved file and surface any violations."
  }
}
```

#### Kiro adapter projection

```toml
[adapter.kiro.projections.kiro-ide-hook]
mode = "direct-file"
target.repo = ".kiro/hooks/<pack>/<name>.kiro.hook"
on-conflict = "prompt-then-preserve"
ide-event-vocabulary = [
  "fileCreated",
  "fileEdit",
  "fileSave",
  "fileDeleted",
  "promptSubmit",
  "agentStop",
  "preToolUse",
  "postToolUse",
  "preTaskExecution",
  "postTaskExecution",
  "manualTrigger",
]
ide-action-vocabulary = ["askAgent", "runCommand"]
```

Pack-namespacing the target (`<pack>/<name>.kiro.hook`) matches the
convention § *hook-body at user scope* picked for the same reason —
two packs shipping `on-save.kiro.hook` would otherwise collide, and
a flat layout would force a `kiro-ide-hook-owned` state-file table
to disambiguate uninstall. With pack-namespacing, uninstall is
directory removal; no state-file shape change needed (see updated
§ *State-file impact* below).

**Recursion-into-subdirectories assumption.** This RFC assumes Kiro
recurses into `.kiro/hooks/<pack>/` and reads the `.kiro.hook` files
underneath; the upstream docs document `.kiro/hooks/` as the read
path but do not state whether recursion happens. If recursion is
not supported, the follow-on spec falls back to flat-with-prefix
`<pack>--<name>.kiro.hook`. Either layout is pack-namespaced; only
the path shape differs. Recorded as Unresolved Q6.

#### `validate` rail

The rail enforces four checks:

1. The file exists and is parseable JSON.
2. The required fields are present: `name`, `version`, `when.type`,
   `then.type`. Missing → refuse with
   `pack <P>'s kiro-ide-hook <file> is missing required field <field>`.
3. `when.type` is drawn from `ide-event-vocabulary`. Out-of-vocabulary
   events → refuse, mirroring the `agent-event-vocabulary` refusal
   shape:
   `pack <P>'s kiro-ide-hook <file> uses event '<type>'; not in adapter 'kiro' ide-event-vocabulary`.
4. `then.type` is drawn from `ide-action-vocabulary` (closed enum
   per Unresolved Q8). Refusal text mirrors event-vocabulary shape.

Semantic correctness of `when.patterns` (glob validity) and
`then.command` (shell-syntax validity) is **not** in the rail's
scope — same discipline as wiring TOML validation. Runtime issues
surface at execute time.

#### Cross-primitive reference: `then.command` pointing at a `hook-body`

`then.type = "runCommand"` carries a `command` field — a shell
invocation. When the invocation is a script the same pack already
ships as a `hook-body` primitive, the pack author needs a stable way
to reference the projected `hook-body` path from inside the
`.kiro.hook` JSON without hard-coding the projection target.

This RFC commits to the **mechanism** — placeholder expansion at
projection time — and defers the exact **syntax** to the follow-on
spec (lean: `${hook-body:<name>}`, see Unresolved Q7). A
representative shape:

```json
{
  "then": {
    "type": "runCommand",
    "command": "${hook-body:lint-on-save}"
  }
}
```

At projection time, the bundler resolves `${hook-body:lint-on-save}`
to the projected workspace-relative path of the same-pack
`hook-body` named `lint-on-save` (e.g.
`./tools/hooks/lint-on-save.py` at repo scope). Workspace-relative
defaults sidestep the absolute-path multi-machine failure mode
documented in § *Kiro projection bakes an absolute path*.

`askAgent`-shaped hooks need no cross-primitive reference (the
`prompt` field is self-contained); the placeholder syntax applies
only to `runCommand` hooks.

**Substitution rules.** Five clauses bound the placeholder
mechanism:

1. **Scan surface — `then.command` only.** No other field in the
   `.kiro.hook` JSON is scanned for placeholders. `then.prompt`
   (for `askAgent`), `when.patterns`, `name`, `description`,
   and every other field is passed through verbatim. Pack
   authors who want a `prompt` to mention a path write the path
   literally; the `prompt` text is for the agent, not the
   bundler.

2. **Verbatim substitution — no shell quoting.** The resolved
   path replaces the placeholder character-for-character. Pack
   authors who need shell-safe paths quote the placeholder
   themselves — e.g.
   `bash -lc "'${hook-body:lint}' --fix"`. Verbatim
   substitution matches how shell variable expansion works
   elsewhere and avoids the bundler making invisible quoting
   decisions that surprise pack authors.

3. **Multiple placeholders allowed; single-pass resolution.**
   A `then.command` may contain zero or more placeholders.
   Resolution is single-pass: the bundler scans the string
   once, expands each placeholder to its resolved path, and
   emits the result. Resolved text is **not** re-scanned —
   nested or recursive placeholder syntax (a `hook-body` whose
   name evaluates to another placeholder) is not supported and
   resolved text containing `${...}` patterns by coincidence
   is left alone.

4. **Placeholder grammar — pinned regex.** The
   exact form is `\$\{hook-body:[a-zA-Z0-9_-]+\}` — the closing
   brace is required, the inner name matches `[a-zA-Z0-9_-]+`:
   alphanumerics, underscore, hyphen only. No whitespace, no
   slashes, no dots — so path traversal `../`, dotfile `.foo`,
   and quoted/whitespaced names are forbidden by construction.
   The regex stands on its own; the contract does not currently
   pin a hook-body source filename character class to compare
   against, and the spec amendment may choose to do so
   independently. If a future amendment pins a narrower
   hook-body filename class, the placeholder regex narrows in
   lockstep. Malformed placeholders refuse at `validate` with
   named text:
   `pack <P>'s kiro-ide-hook <file> contains malformed placeholder '<text>'; expected ${hook-body:<name>} with name matching [a-zA-Z0-9_-]+`.

5. **Unresolvable references refuse.** `validate` refuses any
   placeholder that does not resolve to a `hook-body` file the
   same pack ships:
   `pack <P>'s kiro-ide-hook <file> references unknown hook-body '${hook-body:<name>}'; no such hook-body in pack`.

The mechanism implies a phase-order constraint: `hook-body`
projects before `kiro-ide-hook` so the reference can resolve. The
build pipeline order is updated to:
`hook-body` → `agent` → `hook-wiring` → `kiro-ide-hook` → `command` → `skill`.

**Why serial rather than DAG-parallel.** Two real dependencies
exist in the chain: (i) `hook-wiring` ← `agent` (the wiring
merger needs the agent JSON target to exist), and (ii)
`kiro-ide-hook` ← `hook-body` (placeholder expansion needs the
projected hook-body path). Every other ordering — `hook-body` →
`agent`, `hook-wiring` → `kiro-ide-hook`, `command` and `skill`
relative to anything else — is a **tiebreak**, not a dependency.
The strict serial order is the picked tiebreak, not the only
correct one; the contract pins it for *operational*
determinism — log ordering, partial-state-on-failure semantics,
and the rollback target are reproducible across hosts. The
projected *files* are byte-identical regardless of order for
non-dependent phases, so determinism here is about which phase
to debug when something breaks, not about the bytes on disk. And
for implementation simplicity (one phase at a time is easier to
reason about, log, and roll back than a DAG scheduler). If
projection time ever becomes a measured bottleneck,
parallelising independent phases is a backward-compatible later
change.

#### Scope

**Repo-scope only in v1.** User-scope projection is refused at the
contract layer until upstream Kiro
[issue #5440](https://github.com/kirodotdev/Kiro/issues/5440)
closes (`~/.kiro/hooks/` is not on Kiro's read path today; projecting
there would land an inert file). The refusal text:
`pack <P> declares kiro-ide-hook at user scope, but kiro adapter does not support user-scope IDE hooks (Kiro #5440 still open)`.

When #5440 closes, the user-scope refusal lifts via either an
in-place amendment to this RFC (if no state-file shape change is
needed — likely, given `direct-file` carries over) or a successor
RFC (if the user-scope ownership story turns out to need state-file
support). Recorded as Unresolved Q9.

#### Other adapters

`claude-code`, `codex`, and `copilot` set `mode = "dropped"` for
`kiro-ide-hook`. Same pattern as `command` (dropped for Codex /
Copilot) and `agent` (dropped for Codex / Copilot). Adapter-side
declaration is required so `validate` knows the primitive exists
at the contract layer; pack authors who don't target Kiro can leave
`.apm/kiro-ide-hooks/` empty without refusal.

#### Contract version

Adding `kiro-ide-hook` to the `primitive` TOML table and to
`pack.schema.json`'s allowed-primitives list is additive but
observable: the contract version bumps from `0.3` → `0.4` in the
same PR as the rest of this RFC's amendments. Existing v0.3-shaped
adapter declarations remain valid (the new primitive is optional;
adapters that don't declare a projection inherit `dropped`). Pack
metadata files that don't ship `.apm/kiro-ide-hooks/` need no
change.

### Validate-time rule lift

Two distinct rails change in this RFC. Rail B today is a
**user-scope refusal**; promoting Kiro out of `degraded-info-log`
at repo scope is governed by a **separate** acceptance path that
doesn't intersect Rail B at all. Treat them as two rules.

#### Rail B — user-scope lift

[`docs/specs/distribution-adapters/spec.md` § Rail B](../specs/distribution-adapters/spec.md#contract-level-user-scope-refusal-rails),
lines 318–328, refuses any pack whose source tree contains a
non-empty `.apm/hooks/` or `.apm/hook-wiring/` directory when
`"user" ∈ allowed-scopes`. This RFC lifts that refusal **only
when** the pack opts in via `[pack.install] user-scope-hooks =
true` *and* the user-scope target adapter satisfies one of two
shapes:

- **Claude Code shape:** adapter declares `target.user` for
  `hook-body` *and* `mode.user = "user-merge-json"` for
  `hook-wiring`.
- **Kiro shape:** adapter declares `target.user` for `hook-body`
  *and* declares `mode = "merge-into-agent-json"` for
  `hook-wiring` (single mode, no scope qualifier — the agent-file
  target is scope-conditional via `<scope-root>` resolution, but
  the merge algorithm is identical at both scopes) *and*
  declares an `[adapter.<name>.scope]` table making user scope
  reachable.

A pack with `user-scope-hooks = true` whose declared user-scope
target adapter satisfies neither shape is refused at
scope-resolution time with
`adapter <name> does not declare a hook-wiring mode that supports user scope; pack <P> requires it`.

The opt-in flag exists because pack-authoring a user-scope hook is
a materially different responsibility from authoring a repo-scope
one (no per-project isolation; harder for the adopter to attribute
breakage; on Claude Code, shared file with other tools). Requiring
an explicit opt-in keeps the default safe and makes the
contract-level grep at validate-time trivially deterministic: a
pack containing hooks but missing the flag stays refused at user
scope. The flag has no meaning at repo scope and is ignored if
`"user" ∉ allowed-scopes`.

#### Repo-scope Kiro promotion — separate from Rail B

The most novel Kiro change in this RFC is at **repo scope**: the
adapter table entry for Kiro `hook-wiring` flips from
`degraded-info-log` to `merge-into-agent-json` in the
[`adapter.toml`](../../packages/agentbundle/agentbundle/_data/adapter.toml)
shipped alongside the v0.3 adapter contract. Rail B does not
apply (Rail B is the user-scope refusal). The acceptance gate
is:

1. The adapter contract version is `0.3` or higher (the version
   bump records the new mode's existence so older CLIs don't
   try to use a mode they don't implement).
2. The Kiro adapter table declares `mode = "merge-into-agent-json"`
   and an `agent-event-vocabulary` for the events the namespace
   accepts (see § `agent-event-vocabulary`).
3. **When the pack ships `.apm/hook-wiring/`,** each TOML declares
   a valid `attach-to-agent` field pointing at a same-pack agent
   (`validate` refuses on missing or unresolvable references with
   `pack <P>'s hook-wiring <name>.toml does not declare 'attach-to-agent' (or names an unknown agent); required for kiro projection`).
   Packs shipping only `.apm/kiro-ide-hooks/` (no `hook-wiring`)
   are exempt — IDE event hooks have no agent binding and need no
   `attach-to-agent` field.
4. The pack's `hook-wiring` events are drawn from the adapter's
   declared `agent-event-vocabulary` (cross-vocabulary refusal —
   see same section). The pack's `kiro-ide-hook` events are drawn
   from `ide-event-vocabulary` and actions from
   `ide-action-vocabulary`; same refusal shape, different list.

No new opt-in flag at repo scope: repo-scope writes have always
been allowed by the contract; this RFC changes the projection
target, not the consent gesture. A pack already shipping wiring
that hit `degraded-info-log` on v0.2 will project successfully on
v0.3 provided the four gates above pass — same source TOML,
different runtime semantics, callout in the changelog.

#### `agent-event-vocabulary` — declarative event list

The `merge-into-agent-json` adapter entry must declare the events
it accepts as a string array:

```toml
[adapter.kiro.projections.hook-wiring]
mode = "merge-into-agent-json"
agent-event-vocabulary = [
  "agentSpawn",
  "userPromptSubmit",
  "preToolUse",
  "postToolUse",
  "stop",
]
```

`validate` checks every event key in a pack's wiring TOMLs
against this list when the wiring is being projected to that
adapter. A pack-side `[[hooks.UserPromptSubmit]]` (PascalCase)
projected against Kiro is refused with
`pack <P>'s hook-wiring <name>.toml uses event 'UserPromptSubmit'; not in adapter 'kiro' agent-event-vocabulary`.
The Claude Code projections do not declare
`agent-event-vocabulary` because `user-merge-json` does not need
the check — Claude Code's runtime ignores unknown event keys
(observed-not-contract; this RFC's `id`-as-tag drawback already
records the broader unverified-schema risk). If a future Claude
Code release validates events, we'd add the field then; for now
declaring it would over-commit.

The vocabulary string array is **declarative** — the CLI does
not carry a hardcoded list of "Kiro's events"; everything the
CLI needs is in the adapter table. This makes the contract
self-describing and lets third-party adapter declarations
introduce their own vocabularies without CLI source changes. See
Unresolved Q5 for the open question on whether the
`agent-event-namespace` *identifier* (separate from the
vocabulary list) should be a closed enum.

#### Sibling vocabularies for IDE event hooks

The same declarative-list discipline extends to the
`kiro-ide-hook` primitive introduced earlier in this RFC:
`ide-event-vocabulary` enumerates the IDE-surface event names
Kiro fires (`fileSave`, `promptSubmit`, etc.) and
`ide-action-vocabulary` enumerates the action types
(`askAgent`, `runCommand`). Both live in
`[adapter.kiro.projections.kiro-ide-hook]` rather than the
adapter root because they're projection-specific. Refusal text
mirrors `agent-event-vocabulary`'s shape:
`pack <P>'s kiro-ide-hook <file> uses event '<type>'; not in adapter 'kiro' ide-event-vocabulary`.

Pinning `ide-action-vocabulary` as a closed enum (rather than
pass-through) follows the same discipline that justifies
`agent-event-vocabulary` being closed: a future Kiro action type
means an adapter declaration change, which is correct because
adapter behaviour follows runtime capability — not the other way
around. Recorded as Unresolved Q8.

### State-file impact

User-scope state today (per [RFC-0004 § State file per
scope](0004-install-scope-per-pack.md#state-file-per-scope)) lists
the packs installed at user scope. With user-scope hooks, the CLI
needs to know **which entries in which target file belong to which
pack** so uninstall can be precise. For Claude Code that target is
`~/.claude/settings.json`; for Kiro it's the pack-owned agent JSON
at `<scope-root>/.kiro/agents/<attach-to-agent>.json`.

The state schema gains a per-install `hook-wiring-owned` table.
Each entry carries an optional `target-file` field naming the
file the entry lives in — null/omitted for Claude Code (where the
target is implied per scope), required for Kiro:

```toml
# Claude Code at user scope
[[installed]]
pack = "personal-reviewers"
version = "0.1.0"
scope = "user"

  [[installed.hook-wiring-owned]]
  event = "UserPromptSubmit"
  id = "personal-reviewers:on-prompt"
  # target-file omitted — implied as ~/.claude/settings.json by adapter

  [[installed.hook-wiring-owned]]
  event = "SessionStart"
  id = "personal-reviewers:on-session"
```

```toml
# Kiro at repo scope (also: same shape at user scope, different scope-root)
[[installed]]
pack = "clipboard-summary"
version = "0.1.0"
scope = "repo"
adapter = "kiro"

  [[installed.hook-wiring-owned]]
  event = "userPromptSubmit"
  id = "clipboard-summary:on-prompt"
  target-file = ".kiro/agents/clipboard-watcher.json"
```

The `adapter` field on the install record is new for Kiro entries
— state today doesn't track adapter per install because the CLI
runs against a single adapter at a time, but recording it makes
the state file readable across mixed installs and helps the
`reconcile` reporter group orphans by their owning adapter.
Claude Code entries can omit `adapter` (defaulted as `claude-code`
for backwards compat with v0.2-state-file reads).

**Read-time semantics pin (v0.3 readers).** A v0.3 reader hitting
a `[[installed]]` row with no `adapter` field treats it as
`adapter = "claude-code"`. This rule applies uniformly to (a)
v0.2-vintage rows preserved across the header-only migration and
(b) v0.3-vintage Claude Code rows that omit the field as a
write-time space saving. The migration step does **not** backfill
the field on existing rows — header-only-additive holds because
absent-equals-default is the read contract.

`hook-body` files don't need an ownership record: they live under
`~/.claude/hooks/<pack>/<name>.{sh,py}` — the pack-namespaced
subdirectory is **required**, not optional. Without it, two packs
shipping `on-prompt.sh` would collide at the user-scope target, and
the state-file would need to grow a `hook-body-owned` table
mirroring `hook-wiring-owned` to disambiguate ownership for
uninstall. The namespaced layout makes uninstall a directory
removal and keeps the state schema additive in one place only. Claude Code
reads `~/.claude/hooks/` recursively, so the extra path segment has
no runtime cost.

`kiro-ide-hook` files need no ownership record for the same reason
`hook-body` doesn't: they live under
`.kiro/hooks/<pack>/<name>.kiro.hook` — the pack-namespaced
subdirectory is required, and without it two packs shipping
`on-save.kiro.hook` would collide and force a `kiro-ide-hook-owned`
state-file table to disambiguate. The namespaced layout makes
uninstall a directory removal and keeps the state schema additive
in one place only (`hook-wiring-owned`).

**Adopter hand-edits to projected `.kiro.hook` files are lost on
uninstall.** `uninstall` removes `.kiro/hooks/<pack>/` verbatim.
If the adopter has hand-edited a projected `.kiro.hook` file (to
tweak a prompt or tighten a `patterns` glob), those edits go with
the directory. Same property every other `direct-file` primitive
already has — `hook-body`, `agent`, `command`, `skill` directories
all get nuked by uninstall regardless of adopter edits — and same
mitigation: the `direct-file` `on-conflict = "prompt-then-preserve"`
covers install-time conflicts, but uninstall is unconditional.
Adopters who need to preserve their tweaks copy the file outside
`.kiro/hooks/<pack>/` before uninstalling. This is accepted, not
fixed.

`runCommand`-shaped IDE hooks deserve a specific callout:
adopter-edited `command` strings often encode a *local fix* the
pack author hasn't shipped yet (a patched path, a wrapped
invocation, an added flag). Such fixes are exactly the
hand-edits an adopter cares most about preserving. The mitigation
is the same — copy the file out before uninstalling — but the
salience is higher.

The state-file schema bumps from `0.2` → `0.3`. The bump is
**additive and header-only**: `hook-wiring-owned` is an *optional*
array-of-tables under each `[[installed]]` entry, so a v0.2 file
remains a structurally valid v0.3 file once the `schema-version`
line is rewritten — entries that wire no hooks omit the table
entirely. `init-state --migrate` gains a v0.2 → v0.3 step that
patches the `schema-version` line and writes the file back; no
per-entry rewrite is required, but the migration still touches the
file (so it isn't a no-op — it's the cheapest possible additive
migration). Write against a v0.2 file is refused with the same
refuse-and-explain shape RFC-0004 established for v0.1 → v0.2
([`distribution-adapters/spec.md:428-430`](../specs/distribution-adapters/spec.md)),
which itself was additive — that migration added an explicit
`scope = "repo"` per entry.

### First consumer

Per RFC-0004 § *Alternatives considered* item 8 (line 503), the
"land mechanics *with* the first user-scope pack" position was
**rejected** — i.e. RFC-0004 set the precedent that scope mechanics
land ahead of a named consumer because doing them under release
pressure means corners cut. This RFC **follows** that precedent
for the same reason: the merge semantics are non-trivial and a
concurrent first-consumer release would force the corners RFC-0004
explicitly chose to avoid.

**Naming the first consumer is deferred to a follow-up spec.** A
plausible candidate is a personal-reviewers pack that ships a
small `SessionStart` hook surfacing pending review-task counts;
another is a clipboard-summary pack hooking `UserPromptSubmit` for
"did you mean to paste that?" prompts. Either would be a one-day
PR once this RFC and its sibling spec amendments are in. The
follow-up spec sits behind this RFC; this RFC does not commit to
either example.

### What this RFC does NOT do

- **No `recommends` across-scope changes.** Closed by RFC-0004 §
  `recommends` across scopes; nothing here reopens it.
- **No `global` (system-wide) scope.** Not reserved, not refused
  — absent, same as RFC-0004.
- **No APM / Claude-plugins install-route parity.** Out-of-CLI
  install routes for hooks at user scope are tracked separately
  under [`docs/backlog.md`](../backlog.md) § `adapt-to-project`;
  this RFC is CLI-only.
- **No F-conformance fixtures.** F-conformance is owned by
  RFC-0003's deferred task and is not gated by this RFC.
- **No knowledge-on-Kiro for the core pack.** The bundler does not
  project `docs/knowledge/patterns.jsonl` (or any other knowledge
  source) to a Kiro-readable surface. Kiro adopters who want the
  knowledge content CC adopters receive via `session-start.py` do
  not get it through this RFC. If knowledge-on-Kiro is needed for
  a specific deployment, build it separately and out-of-band; do
  not bring it into the bundler's contract.
- **No Kiro Power deployment.** The bundler does not produce Kiro
  Powers and this RFC does not cover them. Power packaging is a
  different distribution shape with its own lifecycle.
- **No `steering` primitive.** The 3× rule has not been earned —
  there is no second consumer for steering-shaped content in any
  pack today. Adding the primitive against a single hypothetical
  consumer would be contract inflation; reopen as a separate RFC
  when a second consumer materialises.

  *Asymmetry with `kiro-ide-hook`.* This RFC accepts
  `kiro-ide-hook` with zero in-repo consumers (Drawbacks above)
  while rejecting `steering` on the same zero-consumer count.
  The distinguishing argument: `kiro-ide-hook` closes a
  *projection-target gap* — pack authors have no way to ship an
  IDE-save automation to Kiro adopters today, full stop, and the
  absence of a target is itself the bug. `steering` would close
  an *adopter-experience asymmetry* — Kiro adopters don't get the
  knowledge content CC adopters receive via `session-start.py` —
  but no pack author is blocked from doing anything; they can
  build a side-channel (Power, separate distribution) without
  the bundler's help. Mechanics-before-consumer is justified for
  the gap; not justified for the asymmetry.

  **Falsifiability test for future RFC reviewers.** The test is
  binary: *Is there any first-class delivery channel by which a
  pack author can ship the affordance today?* If yes (an
  adjacent in-tool primitive, an established sibling distribution
  format like a Power), it's an asymmetry — wait for
  second-consumer pressure. If no — the delivery surface itself
  does not exist — it's a gap, and mechanics-before-consumer is
  justified.

  **What counts as a channel.** A first-class delivery channel
  means *the affordance can be delivered in the channel's
  documented surface without an authoring workaround* — the
  channel exists, the content fits the channel's native shape,
  and the pack author writes the content the way the channel
  expects.

  **What does *not* count.** *Manual hand-edit setup
  documentation*, *adopter copy-paste recipes*, and *bundler
  workarounds asking the pack author to invent or wrap a
  distribution format the channel does not natively expose*.
  These are exactly the squatter outcomes RFC-0001 set out to
  eliminate and the channel-shifting outcomes RFC-0004 closed for
  non-hook primitives — admitting them as evidence-of-channel
  would let any unmet need rationalise into "asymmetry, defer."

  **Worked examples:**
  - **`kiro-ide-hook`:** The question is whether Kiro Powers are
    a first-class IDE-event delivery channel. They are not — a
    Power's documented surface is keyword-matched activation
    against POWER.md frontmatter ([Kiro Powers docs](https://kiro.dev/docs/powers/),
    [introducing-powers blog post](https://kiro.dev/blog/introducing-powers/)),
    not IDE-event triggering. Delivering a save-triggered
    automation via a Power means *inventing* a wrapper layer the
    Power format does not natively expose. That fails the
    "without an authoring workaround" clause. **Gap stands.**
  - **`steering`:** Powers explicitly document a `steering/`
    subdirectory; pack authors write the same markdown they'd
    write for a steering primitive and drop it into the Power.
    The Power format exists, steering content fits natively, no
    wrapper invented. That passes the channel test. **Asymmetry
    holds.**

  The distinction is concrete: does the candidate channel's
  documented surface *already accept* this shape of content
  (Power's `steering/` does; Power's POWER.md does not accept
  IDE-event triggers), or would the pack author have to graft
  something on top of the channel? Workarounds-on-top fail the
  test; native-shape acceptance passes it.

  Without this test the "projection-target gap" framing is
  rhetorical; with it, reviewers have a knob to turn that
  prevents the category from decaying into "any unmet need."

## Alternatives considered

1. **Do nothing — keep refusing hooks at user scope forever.**
   Adopters who want personal hooks copy scripts into
   `~/.claude/hooks/` by hand and hand-edit
   `~/.claude/settings.json`. No upgrade, no uninstall, no
   visibility from `agentbundle`. The exact squatter problem
   RFC-0001 set out to solve and that RFC-0004 closed for every
   non-hook primitive. Rejected: the asymmetry is the cost.

2. **Define only `hook-body` reroot; leave `hook-wiring`
   permanently refused.** Adopters can ship the script but must
   wire it themselves. Cheaper one PR but leaves the surface
   half-finished — a packed hook with no wiring is dead code.
   Adopters re-derive the wiring boilerplate by hand and the
   pack-author can't even document *the* canonical wiring (every
   adopter's file is different). Rejected: half a primitive is
   worse than none.

3. **A separate `~/.claude/settings.<pack>.json` per pack
   instead of merging into the shared file.** Claude Code does
   not read `settings.<pack>.json`; only `settings.json` and
   `settings.local.json` are on the read path. We would have to
   either ship a meta-merger that produces `settings.json` (which
   recreates this RFC's merge problem one level up) or petition
   Claude Code to read sharded files (out of scope; we don't own
   that decision). Rejected: it doesn't actually avoid the merge.

4. **Generated-block markers in the user settings file (like
   Codex's `AGENTS.md` managed block) so merge is just
   block-replace.** Attractive — block-replace is the simplest
   merge semantics we know. But JSON does not have comments, so
   we can't fence a region of the file with `<!-- BEGIN
   agentbundle -->`-style markers. Two variants worth naming and
   rejecting under the same heading: (a) **Persuade Claude Code to
   read JSONC** (or YAML/TOML) so we can fence with comments —
   out of scope; the file format is owned by Claude Code, not us,
   and "we'll wait for an upstream change" is not a design. (b)
   **Introduce a structural fence** (a synthetic top-level key
   like `_agentbundle_managed`) and a runtime that copies entries
   from it into `hooks` — which Claude Code doesn't do, so the
   entries would never fire. Rejected: every form of the marker
   trick either depends on a comment-bearing format we don't have
   or on a runtime hop Claude Code isn't going to add.

5. **Per-pack settings file under our own namespace
   (`~/.agentbundle/user-hooks.json`) plus a one-time
   bootstrapper line in `~/.claude/settings.json`.** Avoids
   merge into the shared file at the cost of asking the adopter
   to add a single boilerplate line manually. Rejected: the
   one-time bootstrap line is itself an unmerged hand-edit that
   would need its own design, and a bootstrapper file that's
   *one line different* from what the CLI could write is worse
   than the CLI writing the entries directly.

6. **Have the CLI shell out to `jq` or a JSON-merge tool instead
   of building a merger.** Adds a non-stdlib dependency against
   the `agent-spec-cli` spec's stdlib-only commitment. Rejected
   on dependency grounds; the merge logic is bounded enough that
   a stdlib implementation isn't expensive.

7. **Defer Kiro to a separate follow-up RFC (treat it as a new
   primitive).** Attractive on shape grounds — "one RFC, one
   responsibility" reads cleaner than coupling two adapters'
   hook stories. But the Kiro fix turned out to be a second
   projection mode on the existing `hook-wiring` primitive, not
   a new primitive: same source TOML, same id-tag discipline,
   same idempotency rules, same `hook-wiring-owned` state shape
   with one optional field. The merge engine reuses
   `user-merge-json`'s machinery wholesale. Splitting the two
   would mean re-deriving most of those decisions in the second
   RFC against a moving target (this RFC's design would already
   have shipped) and would double the spec-amendment / state-
   schema bump count. Rejected: when two designs share their
   discipline, splitting them across RFCs trades a single
   coherent decision for two partially-coherent ones.

   *The honest counter-cost.* This isn't a free lunch. One PR
   now amends *two* specs simultaneously (distribution-adapters
   *and* agent-spec-cli) covering *two* adapters with
   overlapping-but-not-identical discipline (Claude Code
   user-scope shared-file write vs. Kiro both-scopes pack-owned
   agent-file merge). The v0.3 state-schema migration carries
   fields (`adapter`, `target-file`) that the Claude-Code-only
   design wouldn't have needed. Review burden on the amendment
   PR is higher than a Claude-Code-only PR would have been, and
   any future Kiro-side projection change (event vocabulary
   evolution, new Kiro events) touches this RFC's amendment text
   rather than a Kiro-specific successor. The rejection still
   holds — the coupled cost is one-time at amendment time, while
   the split cost would have re-paid the discipline-design cost
   twice — but the trade is real and named here so a future
   reader can re-evaluate if the assumption inverts.

8. **Extend `hook-wiring` with a new `kiro-ide-hook-json` projection
   mode that renders a TOML wiring file to a `.kiro.hook` JSON.**
   Attractive on shape consistency — one wiring primitive serves
   both Kiro CLI and IDE hooks. But the wiring TOML would have to
   encode the IDE event vocabulary (`fileCreated`, `promptSubmit`,
   etc.), the IDE action vocabulary (`askAgent` vs `runCommand`),
   glob patterns, prompt text, command strings — most of which
   never apply to CLI hooks. The TOML balloons; the renderer
   becomes a JSON templater for one adapter. Rejected — the source
   format is already JSON in Kiro's world; making pack authors
   write TOML to be rendered back to JSON loses fidelity and gains
   nothing. A dedicated `kiro-ide-hook` primitive whose source IS
   the `.kiro.hook` JSON is the least-shape design.

9. **Add a generic `event-hook` primitive instead of a Kiro-specific
   name.** The `.kiro.hook` schema is Kiro-specific (event names,
   action types, file extension); generalising the primitive name
   without generalising the source format is misleading. If a
   future adapter introduces file-event hooks with a different
   schema, that adapter gets its own primitive. Rejected on
   truth-in-naming.

10. **Allow user-scope `kiro-ide-hook` projection now, landing inert
    files until upstream Kiro #5440 closes.** Inert files invite
    confusion (the adopter installs the pack, expects the hook to
    fire, debugs an absent runtime behaviour). Refuse-and-explain
    at install is cheaper than the support load from silent
    inertness. Rejected.

11. **Add a `steering` primitive in the same RFC as `kiro-ide-hook`.**
    Considered while scoping this amendment because the
    knowledge-on-Kiro gap (CC adopters get knowledge via
    `session-start.py`; Kiro adopters get nothing) is a real
    asymmetry that a `steering` primitive could close. Rejected on
    the 3× rule: only one consumer (the rendered knowledge file)
    is in sight today; a primitive added for one consumer is
    contract inflation. Knowledge-on-Kiro is documented as out of
    scope in § *What this RFC does NOT do*; if a second non-MCP
    pack ships steering-shaped content, reopen as a separate RFC
    designed against two real consumers.

## Drawbacks

- **Hand-edited user settings file means write contention with
  Claude Code itself and other tools.** We assume single-writer
  semantics — that Claude Code is not actively rewriting
  `~/.claude/settings.json` while the CLI is writing it. There
  is no advisory lock today and no atomic-rename guarantee on
  every platform we'd want to support. A future Claude Code
  background-writer (e.g. an auto-save of UI-changed settings)
  would invalidate the assumption. The mitigation is
  read-modify-write with a final mtime check before rename;
  documented in the sibling spec amendment but not bulletproof.

- **Uninstall needs to be precise or it leaves orphans.** The
  ownership record in user-scope state is the only thing
  standing between us and "uninstall removed half the entries
  and left the other half." A corrupted or hand-edited state
  file means the CLI can't locate its own entries on uninstall.
  The pre-uninstall state-file snapshot (mentioned in §
  Failure modes) is the recovery path but adopters have to
  notice they need it. The `reconcile --scope user` subcommand
  named in follow-on artifacts is **report-only**: it surfaces
  orphan entries (in either direction) and the adopter takes
  manual action from the report. The CLI does not auto-repair —
  a write mode would re-create the merge-discipline problems
  this RFC is designed to avoid.

- **Cross-pack hook ordering becomes a new failure mode.** Two
  packs both wiring `UserPromptSubmit` produce two entries in
  the array. Claude Code runs them in declared order; the
  ordering the CLI produces depends on **install sequence** (the
  pack installed earlier runs first), not on pack identity. If
  pack *A* assumes it runs before pack *B* (because it modifies
  prompt text *B* reads), an adopter who installs *B* first and
  *A* second silently inverts the order. The fix is "hooks
  shouldn't have implicit ordering dependencies" — a pack-author
  discipline we can document but not enforce. Adopters who do
  care about order edit the array by hand; the CLI sees
  adopter-touched ordering and leaves it alone.

- **The `user-scope-hooks` opt-in is a third per-pack field on
  the scope-policy surface.** `allowed-scopes` is the permitted
  set, `default-scope` is the unflagged target, and
  `user-scope-hooks` is the explicit-opt-in for the
  hand-edited-shared-file write. Each field carries its own
  semantics — they don't *duplicate* each other — but the
  scope-policy surface is now three fields where it used to be
  two, and pack authors targeting user scope have one more
  thing to get right.

- **State-file v0.2 → v0.3 migration is the second migration
  adopters have to run in two RFCs.** v0.1 → v0.2 landed with
  RFC-0004; v0.2 → v0.3 lands here. The migration is header-only
  additive but it's still a refuse-and-explain at write, which
  costs an adopter one CLI run to notice and resolve.

- **`upgrade` against a pack that flips `user-scope-hooks` mid-
  version-stream silently wires new hooks.** A pack published as
  `user-scope-hooks = false` at v1.0 and `true` at v1.1 will, on
  `agentbundle upgrade <pack>`, write entries into the adopter's
  `~/.claude/settings.json` without an additional explicit
  consent — the original `--scope user` install was the consent
  gesture, and `upgrade` honours pack-author intent. Adopters who
  don't want shared-settings writes after a version bump must
  read the changelog or pin. Pack authors flipping this field
  should treat it as a breaking change in their semver discipline,
  but the contract cannot enforce that.

- **Multi-machine sync of `~/.claude/` decouples settings from
  state.** Adopters who sync `~/.claude/` across machines via a
  dotfiles repo, Dropbox, or iCloud carry `settings.json`
  cross-machine but not `~/.agentbundle/state.toml` unless they
  sync that path too. Uninstall on machine B against entries
  installed on machine A may fail to locate ownership records
  (no `hook-wiring-owned` row in B's state) — the entries become
  orphans the `reconcile --scope user` reporter surfaces but
  doesn't repair. Adopters do the fix by hand from the report,
  or pre-empt the case by also syncing `~/.agentbundle/`;
  documenting the latter is the mitigation. The contract has no
  enforcement.

- **The `id`-as-tag assumption is unverified against Claude Code's
  hook-entry schema.** This RFC asserts Claude Code ignores
  unknown keys on hook entries (so the synthetic `id` is a safe
  ownership marker). The assertion is true today by observation,
  not by contract — a future Claude Code release that gives the
  `id` key its own meaning would silently change the CLI's
  ownership semantics. Mitigation lives in Unresolved Q1 (rename
  to `agentbundle-id` from the start?); recording it here so the
  risk doesn't get lost.

- **Kiro's hook-entry schema is observed-but-not-publicly-documented.**
  *(Partially closed — `hooks`/events. Residual risk on optional
  hook-entry fields and on full agent-field coverage; see T7 research,
  2026-05-24.)*
  When this RFC was drafted, the
  [`kiro.dev/docs/cli/custom-agents/creating/`](https://kiro.dev/docs/cli/custom-agents/creating/)
  page documented agent files but not the `hooks` field; events and
  entry shape were known from in-IDE observation only.
  [`kiro.dev/docs/cli/custom-agents/configuration-reference/`](https://kiro.dev/docs/cli/custom-agents/configuration-reference/)
  now publishes the `hooks` field schema with the same five events
  this RFC names (`agentSpawn`, `userPromptSubmit`, `preToolUse`,
  `postToolUse`, `stop`) and confirms `command` (required) + `matcher`
  (optional) as the hook-entry fields. Three classes of residual risk
  remain:

  1. **Optional hook-entry fields** (`timeout_ms`, `max_output_size`,
     `cache_ttl_seconds`) the original drawback named are accepted by
     the Kiro runtime but remain absent from the public reference.
     The merger preserves any incoming entry fields verbatim, so
     packs declaring them round-trip cleanly today.
  2. **Agent-field coverage on the v0.3 reform.** T7's
     `_project_agent_as_json` emits `name`, `prompt`, plus whatever
     the `kiro-agent-frontmatter-v0.9` mapping table renames
     through (`description`, `tools`, `model`). Other Kiro agent
     fields documented in the reference (`allowedTools`,
     `resources`, additional inheritance keys) are silently dropped
     when a pack author declares them in markdown frontmatter — the
     mapping table doesn't know about them. Pack authors who need
     these fields can extend the mapping table; a follow-on RFC
     would widen the default coverage to all reference fields.
  3. **The `id` ownership-tag assumption** stays the same shape as
     before — Unresolved Q1.

  The same Kiro-docs research surfaced that agents are `.json` files
  (not `.md` with frontmatter as the v0.2 contract claimed) — T7
  reforms the agent projection to emit JSON; spec
  [`distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md)
  line 178 is updated.

- **Build-pipeline ordering becomes a new invariant the pipeline
  has to enforce.** Today the pipeline (per RFC-0002) projects
  primitives in unspecified order — agent, hook-body, hook-wiring,
  command, skill — and each projection is self-contained. With
  `merge-into-agent-json`, that's no longer true: the wiring
  projection reads a file the agent projection wrote. A pipeline
  bug that ran wiring first would surface as "internal: agent file
  missing" (a refuse-and-explain we wired in § Failure modes), not
  as silent corruption, but the invariant is real and worth
  flagging. Cross-pack ordering is **not** introduced — packs are
  installed serially today and no pack writes into another pack's
  agent file.

- **Kiro projection bakes an absolute path into the projected
  agent JSON.** The Kiro hook entry's `command` field carries the
  hook body's path verbatim — at user scope this is an
  expanded-absolute path like `/Users/X/.kiro/hooks/personal-reviewers/on-prompt.sh`
  computed at install time. Three failure modes follow from
  this:
  - **Repo-sync case.** Even an adopter who does not sync `~/`
    across machines is exposed: the projected `.kiro/agents/<name>.json`
    file is *inside the repo* (at repo scope) and therefore on
    the repo-sync path. Machine B cloning the repo gets a
    `command` path that resolves to machine A's `$HOME`.
  - **`$HOME` rename / move.** An adopter who renames their
    home directory between install and uninstall ends up with a
    `command` path pointing at the old home; uninstall still
    works (it reads ownership records, not the command string),
    but the hook stops firing at runtime.
  - **CI / sandboxed runs.** A CI runner with a different
    `$HOME` than the install machine sees the same baked-in
    path; the hook fails silently or noisily depending on what
    Kiro does with a missing command.
  Mitigation: the `reconcile --scope user` reporter (follow-on
  artifacts) flags `command` paths whose target doesn't exist
  at reporter-run time. The repo-scope variant of the same
  problem is **a distinct class** from the existing
  multi-machine drawback (which only fires when adopters sync
  `~/.claude/`); recording it separately so neither swallows
  the other.

- **Multi-target wiring (one hook into N agents) requires N
  duplicate wiring TOMLs.** The `attach-to-agent` field is
  single-valued; a pack that wants to wire the same hook into
  every code-review agent ships N near-identical
  `.apm/hook-wiring/<name>.toml` files, each naming a different
  agent, each pointing at the same `command`. This is a real
  pack-author footgun (forgetting to update one of the N when
  the hook body changes) and worth naming, even though the
  deferral is the right call for now (no observed consumer; a
  multi-target field would require its own design for how
  ordering and uninstall behave when one of the N agents is
  later removed from the pack).

- **Cross-adapter semantic asymmetry — same source, different
  firing model.** A `.apm/hook-wiring/<name>.toml` projected to
  Claude Code fires *globally* (any user prompt, any session
  start). Projected to Kiro, the same wiring fires only when the
  attached agent is active. A pack author writing
  `[[hooks.userPromptSubmit]]` reasonable for "intercept every
  prompt" gets that semantics on Claude Code but "intercept every
  prompt while my agent is active" on Kiro. This is documented
  per-adapter and the `agent-event-vocabulary` adapter field
  prevents accidental cross-vocabulary projection (a
  PascalCase-events TOML for Kiro is refused at `validate`), but
  the firing-model difference itself cannot be normalised away —
  it's how the two runtimes work. The "must ship an agent on
  Kiro" constraint (next drawback) is the operational corollary:
  Kiro hooks need an agent because that's the only firing
  surface available. Pack authors targeting both adapters must
  understand both halves; we can document it but not enforce
  it.

- **A pack must ship at least one agent to wire hooks on Kiro.**
  Direct corollary of the firing-model asymmetry above. A
  wiring-only pack (no `.apm/agents/`) has no `attach-to-agent`
  target on Kiro and is refused at `validate` for the kiro adapter.
  Adopters who want a global hook on Kiro (analog of Claude
  Code's settings-file hook) cannot have it via this RFC — they
  must either ship the hook on a pack-owned agent (which limits
  firing to when that agent is active) or wait for Kiro to
  publish a global-hooks mechanism we can project to. The pack
  can still target Claude Code wiring-only by setting
  `allowed-adapters = ["claude-code"]` (or its equivalent in
  pack metadata) so the Kiro `validate` rail simply doesn't fire.

  *Footnote — wiring-only packs targeting `kiro-ide-hook` instead.*
  A pack whose only Kiro-side hook need is IDE-event-triggered
  (file save, prompt submit, etc.) **does not** need to ship an
  agent: `kiro-ide-hook` files fire on IDE events independent of
  any agent. So the agent-required constraint above applies only
  to packs whose Kiro hooks belong in `hook-wiring`
  (`merge-into-agent-json`); packs whose triggers fit IDE-surface
  events can ship `.apm/kiro-ide-hooks/` alone.

- **The `.kiro.hook` schema is observed, not published.** The
  event vocabulary, action vocabulary, and required-field set are
  derived from Kiro's IDE UI behaviour and example files
  ([hook docs](https://kiro.dev/docs/hooks/),
  [types](https://kiro.dev/docs/hooks/types),
  [examples](https://kiro.dev/docs/hooks/examples/),
  [community guide](https://aicodingtools.blog/en/kiro/kiro-hooks-guide))
  rather than a published JSON schema. Kiro could change the
  shape in any release. Same risk class as the existing Kiro CLI
  agent-JSON drawback above; the mitigation is the same too —
  the vocabularies live in `adapter.toml` declaratively so
  updates require only an adapter declaration change, not CLI
  code.

- **Recursion-into-subdirectories under `.kiro/hooks/` is
  unverified upstream.** This RFC assumes Kiro recurses into
  pack-namespaced subdirectories under `.kiro/hooks/`. If it
  doesn't, the spec falls back to flat
  `.kiro/hooks/<pack>--<name>.kiro.hook` naming. Verification is
  an implementation-spec gate; recording the risk so the gate
  doesn't get forgotten.

- **Cross-primitive references (`${hook-body:<name>}`) introduce
  a new build-step affordance.** Today every projection is
  self-contained per-primitive. Placeholder expansion at
  projection time means the `kiro-ide-hook` projection must run
  *after* the `hook-body` projection — a phase-order constraint
  similar to the agent-before-wiring invariant this RFC already
  introduces. Worth flagging because the same invariant has to
  grow if other cross-primitive references appear later.

- **`runCommand`-shaped IDE hooks bake the projected `hook-body`
  path into the projected `.kiro.hook` JSON.** Same multi-machine
  caveat as § *Kiro projection bakes an absolute path into the
  projected agent JSON* — a `command` path computed on machine A
  may not resolve on machine B. Mitigation: the spec's
  placeholder-resolution rule defaults to workspace-relative
  paths at repo scope (which Kiro's CLI handles natively across
  clones), moving the failure mode from "different `$HOME`" to
  "different repo clone path," which is the lighter of the two.

- **User-scope IDE hooks are blocked on an upstream feature.**
  Until Kiro #5440 closes, Kiro adopters who want personal IDE
  hooks across every workspace must continue copying
  `.kiro.hook` files by hand. We could not fix this without
  Kiro upstream first.

- **One more primitive in the contract.** The contract grows
  from 5 primitives to 6. Pack authors targeting only Claude Code
  / Codex / Copilot ignore it; pack authors targeting Kiro have
  one more source directory to know about. Marginal cost, but
  real.

- **No second consumer for `kiro-ide-hook` yet.** The first
  consumer is hypothetical — no in-repo pack ships `.kiro.hook`
  files today. The RFC follows its own first-consumer precedent
  (§ *First consumer*): land mechanics ahead of a named consumer
  to avoid release-pressure corner-cutting. The first concrete
  consumer lands in a follow-up spec once the contract change is
  in.

- **Pack-shipped `runCommand` IDE hooks are arbitrary shell
  execution on adopter file events.** A pack containing a
  `kiro-ide-hook` with `then.type = "runCommand"` lands a shell
  command Kiro will run every time the trigger fires — file save,
  prompt submit, etc. The consent gesture is the one-time
  `install` of the pack; thereafter the hook fires silently for
  the life of the install. This is structurally identical to
  RFC-0005's existing user-scope CLI hooks (which are also
  pack-shipped shell execution at IDE/agent runtime), and the
  same mitigation applies — adopters trust the pack source they
  install — but it's worth naming explicitly because the IDE-hook
  trigger conditions (any file save in the workspace) are
  *broader* than agent-bound CLI hooks (only while the named
  agent runs). The asymmetry doesn't change the trust model but
  it does widen the blast radius if the trust is misplaced.

  **Consent gate decision: v0.4 adopts option (a) — one-time
  `install` gesture, no per-action opt-in.** The two rejected
  options were (b) require `--allow-shell-hooks` opt-in
  explicitly for `runCommand`-bearing packs and (c) refuse
  `runCommand` entirely for v1. Rejected because: a separate
  flag for `runCommand` IDE hooks but not for `hook-body` shell
  scripts wired via `merge-into-agent-json` is asymmetric (both
  are pack-shipped shell execution at runtime; the IDE trigger
  is broader but not categorically different), and refusing
  `runCommand` outright drops half the user-stated need for
  first-class IDE hook support. Reviewers who'd prefer (b) or
  (c) should raise the pushback before acceptance — the v0.4
  contract bakes (a) in; flipping later means a contract version
  bump.

- **Kiro's `.kiro/hooks/` read path is assumed to glob by file
  extension (`*.kiro.hook`).** If Kiro recurses into pack
  subdirectories *and* reads every file as a hook regardless of
  extension, then a `hook-body` script (`.sh`/`.py`) sharing the
  same `.kiro/hooks/<pack>/` subdirectory under future user-scope
  layout would surface as a parse error. The same extension-based
  filtering assumption is implicit in Kiro's own documentation
  (every documented example uses `.kiro.hook` suffix); the spec's
  recursion-verification gate (Q6) doubles as the place to
  confirm the extension filter is active. Recording the assumption
  here so it doesn't get lost.

## Unresolved questions

1. **Is `id` on hook entries safe as a non-functional tag?** This
   RFC assumes Claude Code ignores unknown keys on hook entries.
   If a future release uses `id` for something else, the CLI's
   ownership tag would silently change meaning. Reviewers should
   weigh in on whether to namespace the tag (`agentbundle-id`)
   from the start.

2. **Backup-on-write retention.** The state-file snapshot
   mentioned in § Uninstall and § User-already-set-this-key
   collision rule needs a retention rule. One previous version?
   Last N? Unbounded with a `gc` subcommand later?

3. **`upgrade` semantics across hook-wiring changes.** When a
   pack version bump adds, removes, or renames a hook entry,
   `upgrade` must reconcile the old state's owned IDs with the
   new pack's. The reconciliation algorithm is straightforward
   but the spec amendment should write it down. **This includes
   `attach-to-agent` value changes for Kiro packs** — an agent
   renamed (`personal-reviewer` → `code-reviewer`), removed, or
   added between versions means the old `target-file` in state
   names one agent JSON while the new wiring targets another.
   Upgrade reconciliation must walk *both* the old target file
   (to remove orphan entries) and the new target file (to add
   the new entry), not just the union of IDs in a single target.

4. **Should the first consumer name appear in this RFC?**
   RFC-0004's *Alternatives considered* item 8 rejected
   "wait for first consumer"; this RFC follows that precedent and
   defers naming one. Reviewers who'd prefer a named consumer
   should weigh the personal-reviewers shape sketched in §
   First consumer as the strongest candidate.

5. **`agent-event-vocabulary` identifier — closed enum or open
   string?** The adapter contract declares the **vocabulary list**
   (an array of event names) declaratively, which closes the
   "how does `validate` know Kiro's events?" gap. But the
   per-adapter *identifier* under which a vocabulary lives —
   today implicitly the adapter table name (`kiro`,
   `claude-code`) — could grow into a separately-declared
   namespace string if multiple adapters end up sharing a
   vocabulary (e.g. a hypothetical Kiro-compatible adapter
   reusing the same event names). Should the contract pin
   `agent-event-namespace = "<string>"` as a closed enum
   validated across all adapter declarations, or stay an open
   per-adapter-derived string? No consumer pressures the
   question today; flagging so a future cross-vocabulary RFC
   inherits the decision rather than re-deriving it.

6. **Read-path probe — how does Kiro enumerate `.kiro/hooks/`?**
   Two independent runtime properties gate the projection layout
   and the file-extension assumption is real:
   - **Recursion:** does Kiro recurse into subdirectories under
     `.kiro/hooks/`?
   - **Extension filter:** does Kiro glob by `*.kiro.hook` only,
     or does it parse every file regardless of extension?

   The 2×2 decides the layout:

   | Recursion | Extension filter | Projection layout |
   |---|---|---|
   | yes | yes | **`kiro-ide-hook`:** `.kiro/hooks/<pack>/<name>.kiro.hook` (this RFC's lean). **`hook-body`:** unchanged. |
   | yes | no | **`kiro-ide-hook`:** `.kiro/hooks/<pack>/<name>.kiro.hook`. **`hook-body` — cross-primitive relocation:** user-scope target moves from `.kiro/hooks/<pack>/<name>.{sh,py}` to `.kiro/hook-bodies/<pack>/<name>.{sh,py}` to avoid parse errors when Kiro reads every file under `.kiro/hooks/` regardless of extension. |
   | no | yes | **`kiro-ide-hook`:** `.kiro/hooks/<pack>--<name>.kiro.hook` (flat-with-prefix). **`hook-body`:** unchanged — stays at `tools/hooks/` and `~/.kiro/hooks/<pack>/<name>.{sh,py}`. |
   | no | no | Same layout as (no recursion × yes filter) — Kiro reads `.kiro/hooks/` top-level only, and the extension filter is moot because nothing else lands there. |

   > **Cross-primitive consequence in the yes×no quadrant only.**
   > The v0.4 contract amendment must update *both* the
   > `kiro-ide-hook` projection *and* the user-scope `hook-body`
   > projection in the same PR, or one of them ends up shipping a
   > target string the other invalidates. The other three quadrants
   > leave `hook-body` alone; this row is the lockstep case.

   **Lean:** the spec runs both probes against a real Kiro install
   before declaring contract version 0.4; the chosen layout becomes
   the canonical `target.repo` (and possibly `target.user`) string
   in `adapter.toml`. The gating-verifications bullet in § *Follow-on
   artifacts* names this as a v0.4-ship gate.

7. **Cross-primitive reference syntax for `kiro-ide-hook` →
   `hook-body`.** This RFC commits to the *mechanism* (placeholder
   expansion at projection time); the *syntax*
   (`${hook-body:<name>}`? `$HOOK_BODY_PATH(<name>)`? relative
   path with a documented base?) is deferred to the spec.
   **Lean:** `${hook-body:<name>}` — TOML-and-JSON-friendly,
   ASCII-safe, namespaced by primitive type so future
   cross-primitive cases reuse the shape.

8. **`ide-action-vocabulary` enumeration scope.** Kiro publishes
   `askAgent` and `runCommand` via the IDE UI today; the
   documentation doesn't pin a closed enum. Should the adapter
   declare a closed list (this RFC's choice) or accept any value
   pass-through? **Lean:** closed enum — same observed-vocabulary
   discipline as `agent-event-vocabulary`; a future Kiro action
   type means an adapter declaration change, which is correct.

9. **When Kiro #5440 closes, does user-scope `kiro-ide-hook`
   land via in-place amendment or successor RFC?** The lift is
   small (`target.user` addition under the same projection table)
   if no state-file shape change is needed. But the
   `agentbundle install --scope user` interaction needs a
   state-file ownership review even for a trivial lift.
   **Lean:** in-place amendment if no state-file shape change;
   successor RFC if state-file shape does change.

10. **`runCommand` consent gate — reviewer pushback surface.**
    Decision in the body: v0.4 adopts option (a), one-time
    `install` gesture, no per-action opt-in (see
    § *Pack-shipped `runCommand` IDE hooks are arbitrary shell
    execution on adopter file events* drawback for rationale).
    Q10 is kept here because the decision is reviewer-visible —
    if reviewers prefer (b) `--allow-shell-hooks` opt-in or
    (c) refuse `runCommand` entirely for v1, the v0.4 contract
    declaration changes (action vocabulary shrinks, or install
    flag is added). Pushback must land before acceptance.

11. **Are the `ide-event-vocabulary` spellings (camelCase) correct
    against real `.kiro.hook` files?** Kiro's published docs
    expose human-readable labels ("File Save", "Prompt Submit")
    but the actual `when.type` string the JSON file carries is not
    in the published reference — it's derived from community
    examples ([Kiro Hooks Guide](https://aicodingtools.blog/en/kiro/kiro-hooks-guide))
    and inference. A pack declaring `"when": {"type": "fileSave"}`
    silently never fires if Kiro internally uses `"file_save"` or
    `"FileSave"`. **Lean:** spec gates the v0.4 contract
    declaration on capturing at least one IDE-UI-authored
    `.kiro.hook` file as a fixture; the captured strings become
    the canonical vocabulary. Until that fixture lands, the
    vocabulary list is a best-guess subject to one fixture-based
    rewrite before contract version 0.4 ships.

## Follow-on artifacts

On acceptance, this RFC produces:

- **Amendment to
  [`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md):**
  - **Claude Code side:** the new `user-merge-json` mode (with
    merge semantics, idempotency, conflict, and failure-mode
    rules); the scope-conditional `target` schema for
    `direct-file` projections; the `managed-key.user` field.
  - **Kiro side:** the new `merge-into-agent-json` mode (with
    its agent-file target, `managed-key`, declarative
    `agent-event-vocabulary` array, and merge / idempotency /
    uninstall / failure-mode rules); Kiro's
    `[adapter.kiro.projection]` for `hook-wiring` flips from
    `degraded-info-log` to `merge-into-agent-json` (the
    repo-scope promotion that closes RFC-0001 Open Q1); Kiro
    gains an `[adapter.kiro.scope]` table with
    `allowed-prefixes.user = [".kiro/", ".agentbundle/"]`; Kiro
    `hook-body` projection gains scope-conditional `target.user`
    (`.kiro/hooks/<name>.{sh,py}`).
  - **`kiro-ide-hook` primitive:** add to the `[primitive]` table
    with `source-path = ".apm/kiro-ide-hooks/"`; add
    `[adapter.kiro.projections.kiro-ide-hook]` with `mode =
    "direct-file"`, target string per the gating verification
    below, `on-conflict = "prompt-then-preserve"`, and declarative
    `ide-event-vocabulary` + `ide-action-vocabulary` arrays.
    Other adapters (`claude-code`, `codex`, `copilot`) set
    `mode = "dropped"`. User-scope projection refused until
    upstream Kiro #5440 closes (refusal text per § *Scope*).

  - **Gating verifications before contract version 0.4 ships.**
    Two probes against a real Kiro install must complete before
    the v0.4 declaration lands in `adapter.toml`:
    1. *Recursion probe (Q6).* Confirm whether Kiro reads
       `.kiro/hooks/<subdir>/<name>.kiro.hook` recursively. If yes,
       the projection target is `.kiro/hooks/<pack>/<name>.kiro.hook`.
       If no, the projection target is the flat
       `.kiro/hooks/<pack>--<name>.kiro.hook`. The contract
       version does not bump until this is pinned — shipping v0.4
       with a target string that has to change on first use is a
       contract-version lie.
    2. *Vocabulary fixture (Q11).* Capture at least one
       IDE-UI-authored `.kiro.hook` file and pin the
       `ide-event-vocabulary` and `ide-action-vocabulary` strings
       against the captured artifact. The spec's fixture set
       includes this captured file as the canonical
       vocabulary-of-record.
  - **Pack-side schema:** `hook-wiring` TOML grows the optional
    `attach-to-agent` field; `validate` rail refuses
    Kiro-targeted wiring without it; extension of
    `[pack.install]` with the optional boolean
    `user-scope-hooks` field (false default; ignored if
    `"user" ∉ allowed-scopes`) and an `if`/`then` block in
    `pack.schema.json` enforcing it. `pack.schema.json`'s
    allowed-primitives list grows `kiro-ide-hook`.
  - **`kiro-ide-hook` `validate` rail:** required-field check
    (`name`, `version`, `when.type`, `then.type`), vocabulary
    membership check against `ide-event-vocabulary` and
    `ide-action-vocabulary`, placeholder-syntax check for
    cross-primitive references (the `${hook-body:<name>}` shape
    per Unresolved Q7); semantic validity of `when.patterns`
    globs and `then.command` shell syntax is out of scope.
  - **Rails:** Rail B becomes conditional on `user-scope-hooks`
    plus the adapter declaring either `mode.user =
    "user-merge-json"` or `mode = "merge-into-agent-json"`.
  - **Pipeline:** the build-pipeline gains a phase-order
    invariant — `hook-body` → `agent` → `hook-wiring` →
    `kiro-ide-hook` → others. `kiro-ide-hook` runs after
    `hook-body` so `${hook-body:<name>}` placeholder expansion
    can resolve to projected `hook-body` target paths.
  - **Contract version:** bumps `0.3 → 0.4` in the same PR
    (additive: new primitive + new projection table fields).

- **Amendment to
  [`docs/specs/agent-spec-cli/spec.md`](../specs/agent-spec-cli/spec.md):**
  `install` / `uninstall` / `upgrade` gain hook-wiring handling
  for both adapters (Claude Code user-scope; Kiro at both
  scopes); state-file schema bumps from `0.2` → `0.3` with the
  `hook-wiring-owned` table including its optional `target-file`
  field and the per-install `adapter` field; `init-state
  --migrate` gains a v0.2 → v0.3 step; new `--force-merge` flag
  on `install` (Claude Code user-scope only — binding and
  `--force` interaction per § User-already-set-this-key
  collision rule above); new `reconcile --scope user` **read-only
  reporter** subcommand that walks **both** the
  `~/.claude/settings.json` file (Claude Code) and every Kiro
  agent JSON named in user-scope state against the
  `hook-wiring-owned` ownership records and reports orphans
  (entries either file claims own but state doesn't know about,
  and vice versa) — the *visibility* affordance the
  multi-machine-sync and uninstall-orphan Drawbacks point at;
  the adopter takes manual action from the report (a write-mode
  `reconcile --apply` is explicitly **not** in this RFC's scope
  — it would re-create the merge-discipline problems this RFC
  is designed to avoid); refuse-and-explain text for unparseable
  target files and shape mismatches.

- **ADR (post-acceptance):** record two durable decisions in one
  ADR. (a) *The CLI may write to hand-edited shared
  user-settings files under an ID-tagged array-append merge
  contract, and to pack-owned agent files under a per-agent
  variant of the same contract.* Subsequent user-scope merge
  work (`env`, `mcpServers`, anything else that lands under a
  `managed-key.user`) and any future per-primitive merge work
  on other adapters will cite the ADR rather than re-derive the
  rationale. (b) *IDE-event hooks on Kiro live in their own
  primitive (`kiro-ide-hook`) rather than being shoehorned into
  `hook-wiring`'s `merge-into-agent-json` mode (wrong firing
  model), a generic `event-hook` primitive (Kiro-specific
  schema), or Kiro Powers (different distribution shape).*
  Future Kiro hook surfaces follow the same primitive-per-surface
  discipline rather than overloading existing modes.

- **Entry on [`docs/backlog.md`](../backlog.md):** open item
  under the `agent-spec-cli` or `distribution-adapters` section
  (whichever picks up the implementation pass) tracking the
  amendments above through to landed code. The Kiro
  `degraded-info-log` entry currently held under RFC-0001 Open
  Q1 is **closed** by this RFC and should be marked as such.
  A separate item tracks the first `kiro-ide-hook` consumer pack.

- **(Deferred — not in this RFC's scope.)** The first user-scope
  hook-bearing pack lands as its own spec / pack publication PR
  after the amendments above are merged. The first pack shipping
  `.apm/kiro-ide-hooks/<name>.kiro.hook` files is a separate
  follow-on, tracked under the new ROADMAP item.

---

## Errata

Corrections below are Approver-signed amendments. The RFC body above is preserved
unchanged; errata supersede where noted. (Approver: eugenelim, 2026-06-01.)

| ID | Introduced by | Date | Correction |
|----|--------------|------|------------|
| E1 | RFC-0022 | 2026-06-01 | RFC-0005 assumed a single `kiro` adapter. Superseded: `kiro` is a deprecated alias for `kiro-ide`; `kiro-cli` is the separate CLI target. |
| E2 | RFC-0022 | 2026-06-01 | `hook-wiring` (merge-into-agent-json) is CLI-only for Kiro. The IDE loader drops any agent carrying a `hooks` key. `hook-wiring` moves to `kiro-cli`; `kiro-ide` drops it in favour of the `kiro-ide-hook` primitive. |
| E3 | RFC-0022 | 2026-06-01 | RFC-0005 described the IDE event vocabulary as a "best-guess" (Unresolved Q11); `distribution-adapters/spec.md:749` marked it `<probe-pinned per Q11>`. RFC-0022 closes Q11 via static analysis of `extension.js` `IDEListenableEvent` enum (2026-06-01) — a deliberate substitution of RFC-0005's stated fixture-probe verification method. Authoritative vocabulary: `fileEdited`, `fileCreated`, `fileDeleted`, `userTriggered`, `promptSubmit`, `agentStop`, `preToolUse`, `postToolUse`, `preTaskExecution`, `postTaskExecution`, `sessionStart`. Actions: `askAgent` / `runCommand`. Shipped validate rail (`fileSave`/`fileEdit`/`manualTrigger`) superseded; updates in T2 of the `kiro-adapter-split` spec. `probes.md` Q11 outcome recorded in T10. |
