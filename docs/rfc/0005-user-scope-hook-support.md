# RFC-0005: User-scope hook support — body reroot + wiring merge mode

- **Status:** Draft
- **Author:** eugenelim
- **Date opened:** 2026-05-23
- **Date closed:**
- **Extends:** [RFC-0004](0004-install-scope-per-pack.md) — lifts the
  conditional Rail-B refusal it parked.
- **Amends:**
  [`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md)
  — projection forks for `hook-body` and `hook-wiring` under
  `claude-code` at user scope; Rail B becomes conditional.
- **Amends:**
  [`docs/specs/agent-spec-cli/spec.md`](../specs/agent-spec-cli/spec.md)
  — `install` / `uninstall` / `upgrade` gain user-scope hook handling
  and a per-entry ownership record in state.

## Summary

[RFC-0004 § Adapter-level scope roots](0004-install-scope-per-pack.md#adapter-level-scope-roots-and-projection-forks)
refused hook-shaped primitives at user scope and named the missing
piece *"hook-wiring merge story"* in shorthand. The real scope is
**both** hook primitives. This RFC designs them: a scope-conditional
target for `hook-body` (reroot from `tools/hooks/` to
`~/.claude/hooks/` per Claude Code's user-scope read paths) and a new
projection mode `user-merge-json` for `hook-wiring` that merges into
the hand-edited shared `~/.claude/settings.json` (no `.local`
suffix). The contract's Rail-B refusal becomes conditional on the
new mode being declared by the adapter; user-scope state grows an
ownership record so uninstall is precise. No pack — user-scope or
otherwise — ships in this RFC; naming the first user-scope
hook-bearing consumer is deferred, following the precedent RFC-0004
set in its *Alternatives considered* item 8 (mechanics land ahead of
a named consumer because doing them under release pressure means
corners cut).

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

### `hook-wiring` at user scope — `user-merge-json` mode

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
  ([`distribution-adapters/spec.md:348-349`](../specs/distribution-adapters/spec.md),
  established for skill-directory enumeration) to the
  `hook-wiring` source surface. The cited line gives the
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
and per-event cases — the merger does a shape check on every key
it would write through, not just the root. Hand-edited shared
state is too load-bearing to "fix up" silently.

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

### Validate-time rule lift

[`docs/specs/distribution-adapters/spec.md` § Rail B](../specs/distribution-adapters/spec.md#contract-level-user-scope-refusal-rails),
lines 318–328, refuses any pack whose source tree contains a
non-empty `.apm/hooks/` or `.apm/hook-wiring/` directory when
`"user" ∈ allowed-scopes`. This RFC lifts that refusal **only
when**:

1. The adapter declares both `target.user` (for `hook-body`) and
   `mode.user = "user-merge-json"` (for `hook-wiring`), **and**
2. The pack opts in by declaring `[pack.install] user-scope-hooks
   = true` — an explicit, single-purpose flag that says *yes, I
   understand my hook-wiring will land in the adopter's shared
   settings file*.

The flag exists because pack-authoring a user-scope hook is a
materially different responsibility from authoring a repo-scope
one (shared file, no per-project isolation, harder for the adopter
to attribute breakage). Requiring an explicit opt-in keeps the
default safe and makes the contract-level grep at validate-time
trivially deterministic: a pack containing hooks but missing the
flag stays refused. The flag has no meaning at repo scope and is
ignored if `"user" ∉ allowed-scopes`.

`validate` continues to fail closed: if the pack declares the
flag but the adapter doesn't declare `mode.user`, the install
refuses at scope-resolution time with
`adapter <name> does not declare user-scope hook-wiring; pack <P> requires it`.

### State-file impact

User-scope state today (per [RFC-0004 § State file per
scope](0004-install-scope-per-pack.md#state-file-per-scope)) lists
the packs installed at user scope. With user-scope hooks, the CLI
needs to know **which entries in `~/.claude/settings.json` belong
to which pack** so uninstall can be precise.

The state schema gains a per-install `hook-wiring-owned` table:

```toml
[[installed]]
pack = "personal-reviewers"
version = "0.1.0"
scope = "user"

  [[installed.hook-wiring-owned]]
  event = "UserPromptSubmit"
  id = "personal-reviewers:on-prompt"

  [[installed.hook-wiring-owned]]
  event = "SessionStart"
  id = "personal-reviewers:on-session"
```

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
   but the spec amendment should write it down.

4. **Should the first consumer name appear in this RFC?**
   RFC-0004's *Alternatives considered* item 8 rejected
   "wait for first consumer"; this RFC follows that precedent and
   defers naming one. Reviewers who'd prefer a named consumer
   should weigh the personal-reviewers shape sketched in §
   First consumer as the strongest candidate.

## Follow-on artifacts

On acceptance, this RFC produces:

- **Amendment to
  [`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md):**
  the new `user-merge-json` mode (with merge semantics,
  idempotency, conflict, and failure-mode rules); the
  scope-conditional `target` schema for `direct-file`
  projections; the `managed-key.user` field; extension of
  `[pack.install]` with the optional boolean `user-scope-hooks`
  field (false default; ignored if `"user" ∉ allowed-scopes`)
  and an `if`/`then` block in `pack.schema.json` enforcing it;
  Rail B becomes conditional on `user-scope-hooks` plus the
  adapter's `mode.user` / `target.user` declarations; contract
  version bump.

- **Amendment to
  [`docs/specs/agent-spec-cli/spec.md`](../specs/agent-spec-cli/spec.md):**
  `install` / `uninstall` / `upgrade` gain user-scope
  hook-wiring handling; state-file schema bumps from `0.2` →
  `0.3` with the `hook-wiring-owned` table; `init-state
  --migrate` gains a v0.2 → v0.3 step; new `--force-merge` flag
  on `install` (binding and `--force` interaction per §
  User-already-set-this-key collision rule above); new
  `reconcile --scope user` **read-only reporter** subcommand
  that walks `~/.claude/settings.json` against the user-scope
  state file and reports orphans (entries the file claims own
  but state doesn't know about, and vice versa) — the
  *visibility* affordance the multi-machine-sync and
  uninstall-orphan Drawbacks point at; the adopter takes manual
  action from the report (a write-mode `reconcile --apply` is
  explicitly **not** in this RFC's scope — it would re-create
  the merge-discipline problems this RFC is designed to avoid);
  refuse-and-explain text for unparseable user settings and
  shape mismatches.

- **ADR (post-acceptance):** record the durable decision that
  *the CLI may write to hand-edited shared user-settings files
  under an ID-tagged array-append merge contract*. Subsequent
  user-scope merge work (`env`, `mcpServers`, anything else that
  lands under a `managed-key.user`) will cite the ADR rather
  than re-derive the rationale.

- **Entry on [`docs/ROADMAP.md`](../ROADMAP.md):** open item
  under the `agent-spec-cli` or `distribution-adapters` section
  (whichever picks up the implementation pass) tracking the
  amendments above through to landed code.

- **(Deferred — not in this RFC's scope.)** The first user-scope
  hook-bearing pack lands as its own spec / pack publication PR
  after the amendments above are merged.
