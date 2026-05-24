# RFC-0005: Hook support — user-scope wiring for Claude Code; agent-bound wiring for Kiro

- **Status:** Draft
- **Author:** eugenelim
- **Date opened:** 2026-05-23
- **Date closed:**
- **Extends:** [RFC-0004](0004-install-scope-per-pack.md) — lifts the
  conditional Rail-B refusal it parked.
- **Amends:**
  [`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md)
  — projection forks for `hook-body` and `hook-wiring` under
  `claude-code` (user scope) and `kiro` (both scopes); Rail B
  becomes conditional; Kiro `hook-wiring` lifts out of
  `degraded-info-log`; Kiro gains a `[scope]` table; the hook-wiring
  TOML schema grows an optional `attach-to-agent` field.
- **Amends:**
  [`docs/specs/agent-spec-cli/spec.md`](../specs/agent-spec-cli/spec.md)
  — `install` / `uninstall` / `upgrade` gain user-scope hook handling
  and a per-entry ownership record in state; build-pipeline ordering
  invariant added (agent projects before its wiring merges).

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
lines 219–243 — `allowed-prefixes.user = [".claude/", ".agent-ready/"]`).

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
mitigation (sync `~/.agent-ready/` and re-install on the second
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
allowed-prefixes.user = [".kiro/", ".agent-ready/"]
```

User-scope Kiro is documented at
[`kiro.dev/docs/cli/custom-agents/creating/`](https://kiro.dev/docs/cli/custom-agents/creating/):
the global agents directory is `~/.kiro/agents/`. The user-scope
prefix is `.kiro/`; CLI infrastructure shares the
`.agent-ready/` prefix already established for Claude Code.

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
3. The pack's `.apm/hook-wiring/<name>.toml` declares a valid
   `attach-to-agent` field pointing at a same-pack agent
   (`validate` refuses on missing or unresolvable references with
   `pack <P>'s hook-wiring <name>.toml does not declare 'attach-to-agent' (or names an unknown agent); required for kiro projection`).
4. The pack's hook events are drawn from the adapter's declared
   `agent-event-vocabulary` (cross-vocabulary refusal — see same
   section).

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
  under [`docs/ROADMAP.md`](../ROADMAP.md) § `adapt-to-project`;
  this RFC is CLI-only.
- **No F-conformance fixtures.** F-conformance is owned by
  RFC-0003's deferred task and is not gated by this RFC.

## Alternatives considered

1. **Do nothing — keep refusing hooks at user scope forever.**
   Adopters who want personal hooks copy scripts into
   `~/.claude/hooks/` by hand and hand-edit
   `~/.claude/settings.json`. No upgrade, no uninstall, no
   visibility from `agent-ready`. The exact squatter problem
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
   agent-ready -->`-style markers. Two variants worth naming and
   rejecting under the same heading: (a) **Persuade Claude Code to
   read JSONC** (or YAML/TOML) so we can fence with comments —
   out of scope; the file format is owned by Claude Code, not us,
   and "we'll wait for an upstream change" is not a design. (b)
   **Introduce a structural fence** (a synthetic top-level key
   like `_agent_ready_managed`) and a runtime that copies entries
   from it into `hooks` — which Claude Code doesn't do, so the
   entries would never fire. Rejected: every form of the marker
   trick either depends on a comment-bearing format we don't have
   or on a runtime hop Claude Code isn't going to add.

5. **Per-pack settings file under our own namespace
   (`~/.agent-ready/user-hooks.json`) plus a one-time
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
  cross-machine but not `~/.agent-ready/state.toml` unless they
  sync that path too. Uninstall on machine B against entries
  installed on machine A may fail to locate ownership records
  (no `hook-wiring-owned` row in B's state) — the entries become
  orphans the `reconcile --scope user` reporter surfaces but
  doesn't repair. Adopters do the fix by hand from the report,
  or pre-empt the case by also syncing `~/.agent-ready/`;
  documenting the latter is the mitigation. The contract has no
  enforcement.

- **The `id`-as-tag assumption is unverified against Claude Code's
  hook-entry schema.** This RFC asserts Claude Code ignores
  unknown keys on hook entries (so the synthetic `id` is a safe
  ownership marker). The assertion is true today by observation,
  not by contract — a future Claude Code release that gives the
  `id` key its own meaning would silently change the CLI's
  ownership semantics. Mitigation lives in Unresolved Q1 (rename
  to `agent-ready-id` from the start?); recording it here so the
  risk doesn't get lost.

- **Kiro's hook-entry schema is observed-but-not-publicly-documented.**
  The Kiro user-scope agent directory is documented at
  [`kiro.dev/docs/cli/custom-agents/creating/`](https://kiro.dev/docs/cli/custom-agents/creating/),
  but that page does *not* document a `hooks` field — the events
  (`agentSpawn`, `userPromptSubmit`, `preToolUse`, `postToolUse`,
  `stop`) and entry shape (`command`, `matcher`, `timeout_ms`,
  `max_output_size`, `cache_ttl_seconds`) are known from in-IDE
  observation. The Kiro runtime accepts the field today but the
  schema is not under contract. If Kiro renames the key, restructures
  the entries, or starts validating against a documented schema
  that rejects the synthetic `id` tag, the projection regresses
  silently. Same risk class as the Claude Code `id`-as-tag
  drawback, just for a different field. Mitigation: pin the
  Kiro mode to a single-source-of-truth in the spec amendment and
  re-verify against Kiro's published docs at each contract version
  bump.

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

## Unresolved questions

1. **Is `id` on hook entries safe as a non-functional tag?** This
   RFC assumes Claude Code ignores unknown keys on hook entries.
   If a future release uses `id` for something else, the CLI's
   ownership tag would silently change meaning. Reviewers should
   weigh in on whether to namespace the tag (`agent-ready-id`)
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
    `allowed-prefixes.user = [".kiro/", ".agent-ready/"]`; Kiro
    `hook-body` projection gains scope-conditional `target.user`
    (`.kiro/hooks/<name>.{sh,py}`).
  - **Pack-side schema:** `hook-wiring` TOML grows the optional
    `attach-to-agent` field; `validate` rail refuses
    Kiro-targeted wiring without it; extension of
    `[pack.install]` with the optional boolean
    `user-scope-hooks` field (false default; ignored if
    `"user" ∉ allowed-scopes`) and an `if`/`then` block in
    `pack.schema.json` enforcing it.
  - **Rails:** Rail B becomes conditional on `user-scope-hooks`
    plus the adapter declaring either `mode.user =
    "user-merge-json"` or `mode = "merge-into-agent-json"`.
  - **Pipeline:** the build-pipeline gains a phase-order
    invariant — `hook-body` → `agent` → `hook-wiring` → others.
  - **Contract version:** bumps in the same PR.

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

- **ADR (post-acceptance):** record the durable decision that
  *the CLI may write to hand-edited shared user-settings files
  under an ID-tagged array-append merge contract, and to
  pack-owned agent files under a per-agent variant of the same
  contract*. Subsequent user-scope merge work (`env`,
  `mcpServers`, anything else that lands under a
  `managed-key.user`) and any future per-primitive merge work
  on other adapters will cite the ADR rather than re-derive the
  rationale.

- **Entry on [`docs/ROADMAP.md`](../ROADMAP.md):** open item
  under the `agent-spec-cli` or `distribution-adapters` section
  (whichever picks up the implementation pass) tracking the
  amendments above through to landed code. The Kiro
  `degraded-info-log` entry currently held under RFC-0001 Open
  Q1 is **closed** by this RFC and should be marked as such.

- **(Deferred — not in this RFC's scope.)** The first user-scope
  hook-bearing pack lands as its own spec / pack publication PR
  after the amendments above are merged.
