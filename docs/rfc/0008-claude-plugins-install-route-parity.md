# RFC-0008: Claude-plugins install-route parity — per-pack SessionStart writer for the install→adapt chain

- **Status:** Accepted
- **Author:** eugenelim
- **Date opened:** 2026-05-24
- **Date closed:** 2026-05-25
- **Related:** [RFC-0001](0001-bundle-distribution-by-adapter-spec.md)
  (Claude-plugins as a canonical install route);
  [RFC-0003](0003-spec-and-cli.md) (CLI install→adapt chain;
  derived per-tool manifests); [RFC-0004](0004-install-scope-per-pack.md)
  (raised this gap as an Unresolved question; scope dimension this RFC
  consumes); [RFC-0005](0005-user-scope-hook-support.md) (contract
  currently at v0.3; this RFC bumps to v0.4);
  [RFC-0007](0007-user-scope-converter-pack.md) (first user-scope pack
  ships, making the user-scope leg of this gap concrete).
  Touches [`docs/specs/adapt-to-project/spec.md`](../specs/adapt-to-project/spec.md)
  and [`docs/contracts/adapter.toml`](../contracts/adapter.toml).

## Summary

Today only `agentbundle install` writes `.adapt-install-marker.toml` and
chains to `/adapt-to-project`. Adopters who install via
`claude plugin install` get the bundle but not the adaptation. Close the
gap by deriving — for every pack that ships via the Claude-plugins
route — a `SessionStart` hook in the pack's `.claude-plugin/plugin.json`
that uses Anthropic's recommended `${CLAUDE_PLUGIN_DATA}` diff pattern
to detect first install or update, then writes a `[[packs-installed]]`
entry to the scope-correct marker file. The core pack's existing session-start nudge
([`packs/core/.apm/hooks/session-start.py:182-193`](../../packs/core/.apm/hooks/session-start.py))
reads the marker unchanged. Contract bumps `0.3 → 0.4` with a single
`install-routes` array on `[adapter."claude-code"]` and per-route
conformance cases. APM parity ships in a separate RFC; the marker
contract is route-agnostic by design and does not preclude APM's
native pre/post-install hooks.

## Motivation

[`docs/specs/adapt-to-project/spec.md:100-118`](../specs/adapt-to-project/spec.md)
defines the install→adapt chain as: `agentbundle install` writes
`.adapt-install-marker.toml` at the scope's root, chains in-process to
`agentbundle adapt`, and the core pack's session-start hook surfaces
*"you have pending adaptations from pack(s) X; run `/adapt-to-project`."*
The chain is the load-bearing path from *bundle on disk* to *bundle
adapted to this repo*.

Today the chain only fires through `agentbundle install`. Adopters
who install via `claude plugin install <marketplace>/core` land files
under `~/.claude/plugins/cache/<marketplace>/core/<version>/`, step 1
of the chain never runs, no marker is written, the session-start hook
sees nothing to nudge — and the bundle ships without adapting. The
adopter has the skills, agents, and hooks installed, but `AGENTS.md`
still says `<project-name>`, the docs tree still has stock seeds, and
the class-2/3/4 discoveries the LLM skill is supposed to surface
never happen.

[RFC-0001 § Distribution outputs](0001-bundle-distribution-by-adapter-spec.md#distribution-outputs)
settled that Claude-plugins is a **canonical install route**, not a
fallback — RFC-0003 reaffirms the same framing for the CLI's
complementary role. The gap is therefore a contract failure for one of
the three routes the bundle is meant to ship through, not a
"use-the-other-route" workaround opportunity.

[RFC-0004 § Unresolved questions](0004-install-scope-per-pack.md#unresolved-questions)
flagged this explicitly: *"APM defaults to user; Claude-plugins
caches at `~/.claude/plugins/cache/`. Both adapters land *after* this
RFC. Will their conventions force a schema revision? Tentative answer:
contract bumps to `0.3` then if needed, with conformance-suite cases
added per scope."* The contract has since bumped to v0.3 via RFC-0005
for hook-body/hook-wiring forks; this RFC resolves the
Claude-plugins half of RFC-0004's question and bumps to v0.4.

[RFC-0007](0007-user-scope-converter-pack.md) (Accepted 2026-05-24)
shipped `converters`, the first user-scope pack. The user-scope leg
of the gap is no longer hypothetical: a user running
`claude plugin install converters --scope user` today receives the
converter skills but no install→adapt chain — and `converters` has
no `<adapt:NAME>` markers, so the class-1 substitutions are a no-op,
but classes 2-4 (discovery, restructuring, consolidation) still
silently don't run.

**Scope.** Claude-plugins only. APM is a sibling gap with a different
hook surface (APM has native pre/post-install lifecycle hooks per the
APM package-anatomy reference) and a different scope semantic (APM
defaults user-wide). APM parity gets its own RFC; trying to design
both at once forces a lowest-common-denominator design that fits
neither route well. See [Alternatives § Alt 5](#alt-5--bundle-this-rfc-with-apm-parity).

## Proposal

### Who writes the marker

A `SessionStart` hook, shipped in each pack's derived
`.claude-plugin/plugin.json`, runs a canonical stdlib-Python writer
that detects first install or update and writes the install marker at
the scope's canonical path.

**Detection.** The writer fires when **either** condition holds: the
hash at `${CLAUDE_PLUGIN_DATA}/pack-manifest-hash` is missing or
differs from `sha256(${CLAUDE_PLUGIN_ROOT}/pack.toml)`, **or** the
hash matches but the scope-correct marker file does not contain a
`[[packs-installed]]` entry for this pack. The second condition
covers the reinstall-after-`--keep-data`-uninstall edge case: when
the adopter uninstalls a pack with `--keep-data`
([Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)
documents that `${CLAUDE_PLUGIN_DATA}` is deleted by default on
last-scope uninstall but survives with `--keep-data`), the hash file
persists; on reinstall the hash matches but the marker entry is
absent (the previous `/adapt-to-project` consumed it long ago), and
the dual check forces a re-fire.

This is the canonical first-run idiom Anthropic documents — the same
shape as their `npm install`-into-`${CLAUDE_PLUGIN_DATA}` example,
with the writer's effect substituted for the install step.

**Write.** When detection fires, the writer:

1. **Detects the install scope.** Reads `enabledPlugins` from
   `${CLAUDE_PROJECT_DIR}/.claude/settings.local.json` (local),
   `${CLAUDE_PROJECT_DIR}/.claude/settings.json` (project), and
   `${HOME}/.claude/settings.json` (user), in that precedence order.
   Missing file, malformed JSON, absent `enabledPlugins` key, or
   `enabledPlugins` present but not a JSON array of plugin
   identifiers are all treated as "not opted in at that scope" and
   fall through to the next check. If `${CLAUDE_PROJECT_DIR}` is
   unset (no project open), the project / local checks are skipped.
   **No-match fallthrough:** if every check misses, the writer
   exits 0 without writing the marker **and without updating
   `${CLAUDE_PLUGIN_DATA}`**, so the next session retries; no
   partial state lands on disk.
2. **Enforces `allowed-scopes`.** Reads the pack's
   `[pack.install] allowed-scopes` from
   `${CLAUDE_PLUGIN_ROOT}/pack.toml`. If the detected scope is not in
   `allowed-scopes`, the writer **refuses and warns**: emits one line
   to stderr (`install-marker: pack <name> declares
   allowed-scopes=<...>, detected install scope <detected>; skipping
   marker write`) and exits 0. No marker is written;
   `${CLAUDE_PLUGIN_DATA}` is not updated, so the next session
   re-checks and re-warns until the adopter reinstalls correctly.
3. **Appends or merges** a `[[packs-installed]]` entry to the
   scope-correct marker file under an `os.replace`-based atomic
   rename (read-modify-write into a tempfile in the same directory,
   then atomic rename) — the same primitive `agentbundle install`
   uses per the spec. Two writers racing on the same marker file
   (the common case when multiple Claude-plugin packs ship the same
   `SessionStart` hook and fire in one session) both land an entry;
   the second writer reads the first's appended state before
   rewriting. Example entry:
   ```toml
   [[packs-installed]]
   name = "core"
   version = "0.1.0"
   install-route = "claude-plugins"
   installed-at = 2026-05-24T10:00:00Z
   # unresolved-markers and new-companions omitted — see "Marker entry fields" below
   ```
4. **Copies the manifest hash** to
   `${CLAUDE_PLUGIN_DATA}/pack-manifest-hash` — **only after** step 3
   succeeds. A partial-write failure (disk full; permission denied at
   `~/.agentbundle/`) leaves no false "already adapted" signal — the
   next session retries the marker write.

The marker shape matches what `agentbundle install` already writes
(per [`docs/specs/adapt-to-project/spec.md:100-118`](../specs/adapt-to-project/spec.md)).
The `install-route` field is a **new optional** column on the existing
schema — `agentbundle install` adds `install-route = "cli"`. The core
pack's existing session-start nudge reads the marker file unchanged;
the nudge wording does not mention the route.

**Marker entry fields.** The schema in
[`docs/specs/adapt-to-project/spec.md`](../specs/adapt-to-project/spec.md)
declares two arrays on each `[[packs-installed]]` entry beyond
`name` / `version` / `installed-at`: `unresolved-markers` (the
`<adapt:NAME>` markers the install left un-substituted) and
`new-companions` (the just-dropped `<filename>.upstream.<ext>`
paths). The CLI route populates both at install time because it can
inspect the projection it just wrote. The Claude-plugins writer
cannot — it runs at `SessionStart` from the plugin cache, with no
visibility into the adopter's destination tree. Under v0.4 both
fields become **optional**. A marker entry written by the
Claude-plugins route omits both; on read, `/adapt-to-project` treats
their absence as "scan the projected primitive tree for
`<adapt:NAME>` markers and `.upstream.<ext>` companions directly" —
the same scan the skill already runs when no marker exists at all.
The two fields remain a populated hint for the CLI route (where
they're cheap) but are not load-bearing for the read side.

**Consumption.** Unchanged. `/adapt-to-project` consumes (deletes on
read) the marker, runs class-1/2/3/4 adaptation, the writer's hash
file ensures it doesn't re-fire on the next session, and the adopter
is in steady state.

### Scope mapping

Claude-plugins installs to one of three settings-file scopes; the
writer maps each to one of the two install-marker scopes defined by
[`docs/specs/adapt-to-project/spec.md:71-73`](../specs/adapt-to-project/spec.md):

| Claude-plugins scope     | Detected by reading                                          | Marker file                                     |
| ------------------------ | ------------------------------------------------------------ | ----------------------------------------------- |
| `--scope user` (default) | plugin listed in `${HOME}/.claude/settings.json` `enabledPlugins` only | `~/.agentbundle/.adapt-install-marker.toml`     |
| `--scope project`        | plugin listed in `${CLAUDE_PROJECT_DIR}/.claude/settings.json` `enabledPlugins` | `<repo>/.adapt-install-marker.toml`             |
| `--scope local`          | plugin listed in `${CLAUDE_PROJECT_DIR}/.claude/settings.local.json` `enabledPlugins` | `<repo>/.adapt-install-marker.toml` (marker file is gitignored at the repo root per AC19c of the adapt-to-project spec) |

Precedence is **local → project → user** (most specific opt-in
wins): an adopter who enabled a plugin at user scope and explicitly
re-enabled it at project scope gets the project-scope marker, not a
duplicate user-scope one. Missing files, malformed JSON, or absent
`enabledPlugins` are all treated as "not opted in at that scope" and
fall through (per the `Write` step 1 above).

`pack.toml`'s `[pack.install] allowed-scopes` is enforced at the
writer layer as defence in depth. Claude-plugins itself does not know
about our scope constraint, so an adopter could install a repo-only
pack (`allowed-scopes = ["repo"]`) at Claude-plugins user scope. The
writer refuses-and-warns in that case (per step 2 above).

### Pack-level declarations

**No new `[pack.install.claude-plugins]` table on `pack.toml`.**
The Claude-plugins-side wiring is fully derived by `agentbundle build`
from fields `pack.toml` already declares. The derivation produces three
artifacts under each pack's projected `.claude-plugin/`:

1. **`plugin.json`** — extended from today's hand-authored
   name/version/description with a synthesised `hooks` block:
   ```json
   {
     "name": "core",
     "version": "0.1.0",
     "description": "...",
     "hooks": {
       "SessionStart": [
         { "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/.claude-plugin/scripts/install-marker.py\"" }
       ]
     }
   }
   ```
2. **`.claude-plugin/scripts/install-marker.py`** — a stdlib-Python
   writer copied verbatim from a single source-of-truth template at
   `packages/agentbundle/templates/install-marker.py`. One canonical
   writer; per-pack divergence is impossible by construction.
3. **`pack.toml`** — projected into the plugin root so the writer has
   something to hash and to read `allowed-scopes` from. The
   `pack.schema.json` shape RFC-0004 pinned is unchanged; the
   projection is a copy, not a transform.

Existing hand-authored `plugin.json` files in `packs/<name>/.claude-plugin/`
are migrated to a build-derived shape in the follow-on F-claude-plugin-derivation
work (see [Follow-on artifacts](#follow-on-artifacts)).

### Contract impact

Adapter contract bumps from v0.3 to v0.4. The shape change is one
new array under the existing `[adapter."claude-code"]` block, plus
per-route cases in the conformance suite. No projection-table forks;
no per-route projection differences.

```toml
[contract]
version = "0.4"

[adapter."claude-code"]
# Install routes for which this adapter has a conforming install→adapt
# chain. Each declared route MUST satisfy the install-marker contract
# (per docs/specs/adapt-to-project/spec.md) after a successful install.
# A flat array key on the adapter table — not array-of-tables — because
# the route name is the only field; per-route conformance lives in the
# suite, not the contract.
install-routes = ["cli", "claude-plugins"]

[[adapter."claude-code".projection]]
# ...existing entries unchanged...
```

**Conformance cases added.** One pair per declared route:

- *Marker presence.* After installing pack P via route R into scope
  S, the marker file at the scope-canonical path contains a
  `[[packs-installed]]` entry with `name = P` and (for v0.4)
  `install-route = R`. For `route = "claude-plugins"` the case is
  asserted on **session 2 or later** until
  [anthropics/claude-code#10997](https://github.com/anthropics/claude-code/issues/10997)
  ships a fix (see
  [Drawbacks § first session may not fire](#claude-plugin-install-first-session-may-not-fire-the-sessionstart-hook));
  the fixture explicitly opens a follow-up session before asserting.
- *Scope refusal.* When the requested scope is not in pack P's
  `allowed-scopes`, the route's installer (or the writer hook, for
  Claude-plugins) emits the refusal-and-warn rail and leaves no
  partial state.

Install-route is **not** a fourth axis on the projection contract.
Per-primitive projection rules remain shared across routes; only the
post-install-marker contract is route-keyed. This contains the
"conformance-surface doubling" cost
[RFC-0004 §Drawbacks](0004-install-scope-per-pack.md#drawbacks) warned
about — the route axis exists only where it materially differs, not
across the whole contract.

### Migration path

1. **`agentbundle build`** learns to project `pack.toml` and
   `install-marker.py` into each pack's `.claude-plugin/`, and to
   synthesise the `SessionStart` hook entry in derived `plugin.json`.
2. **Existing CLI install path unchanged.** `agentbundle install`
   keeps writing the marker as today; it adds `install-route = "cli"`
   to its `[[packs-installed]]` entries.
3. **Existing markers from the CLI route remain valid.**
   `install-route` is an additive field — v0.3 readers (which
   predate the field) ignore it as an unknown TOML key; v0.4 writers
   MUST emit it; v0.4 readers MAY treat its absence as
   `install-route = "cli"` for backward-compat with markers written
   before the contract bump. `unresolved-markers` and
   `new-companions` likewise become optional under v0.4 per the
   *Marker entry fields* note above.
4. **First Claude-plugins install of any pack** triggers the writer
   on `SessionStart`, drops the marker, and the next time the core
   pack's nudge runs (same session for the second+ session — see
   [Drawbacks § anthropics/claude-code#10997](#claude-plugin-install-first-session-may-not-fire-the-sessionstart-hook))
   the adopter sees the `/adapt-to-project` nudge.
5. **Stale entries on uninstall.** Until the uninstall companion
   lands (see [Unresolved questions § Q2](#unresolved-questions)),
   `[[packs-installed]]` entries for packs the adopter has since
   uninstalled remain in the marker file and surface as stale
   nudges. `/adapt-to-project` on read detects "pack not installed
   at any scope" (no matching cache directory under
   `~/.claude/plugins/cache/` and no projection on disk) and
   silently drops the entry. Spec amendment to land this read-side
   behaviour ships in the same PR as the contract bump.
6. **No data migration of historical markers.** Markers are
   pending-adaptation signals, deleted on read by the LLM skill;
   any marker on disk after the v0.4 ship is freshly written.

## Alternatives considered

### Alt 1 — Do nothing

Leave the gap open. Claude-plugins adopters silently get no
adaptation; the marketplace listing for `core` implies parity with
the CLI route that doesn't exist. Adopters with stock `AGENTS.md`,
unmerged `<adapt:NAME>` markers, and no class-2/3/4 discoveries are
the failure mode RFC-0001 explicitly set out to prevent at the
brownfield surface.

**Why not chosen:** the gap is the substance of RFC-0004's Unresolved
question. Indefinite deferral is not a position; it accumulates as a
permanent footgun on the route RFC-0001 picked as canonical for
adopters who prefer ecosystem-native installers over our own CLI.

### Alt 2 — Option (b): `plugin.json` post-install lifecycle hook

Have each pack declare a `PostInstall` hook in `plugin.json` that
shells out to a writer script. Pro: explicit, matches the CLI's
install→adapt chain shape directly, doesn't depend on
session-start firing.

**Why not chosen:** Claude Code does not currently expose plugin
install lifecycle hooks.
[anthropics/claude-code#11240](https://github.com/anthropics/claude-code/issues/11240)
requested `PreInstall` / `PostInstall` / `PreUninstall` /
`PostUninstall` — the issue is **closed as duplicate** of an open
feature request, so the surface is on Anthropic's backlog but not
shipping. Building against a non-existent hook is building on a date
we don't own.

Migration is mechanical when Anthropic ships the hooks: the writer
moves from `SessionStart` to `PostInstall`, the `${CLAUDE_PLUGIN_DATA}`
diff scaffolding disappears, the conformance suite's
Claude-plugins case stays unchanged. Reopen this RFC for that
amendment if and when the hooks land.

### Alt 3 — Central detector (in `core`, or as a standalone shim plugin)

Two variants of the same shape: one detector, plural packs to
notice.

- **Alt 3a — in `core`'s session-start hook.** Diff
  `~/.claude/plugins/cache/` against a tracked manifest;
  synthesise install markers for unfamiliar packs.
- **Alt 3b — standalone "shim" plugin (`agentbundle-shim`).**
  Adopters install it once; its `SessionStart` hook scans the
  cache and writes markers for any pack it recognises.

Both share the central-detector pro: one place to maintain
detection logic, no per-pack writer.

**Why not chosen:** both variants couple a single detector to
enumerating *other* packs' adapter-specific cache directories and
`allowed-scopes` declarations — pack-boundary violations the rest
of the contract carefully avoids. Alt 3b adds a separate install
prerequisite ("install the shim before installing anything else")
that the route is supposed to avoid. The per-pack writer keeps
each pack's install-route concerns inside the pack; `core` reads
the marker and emits the nudge, unchanged from today.

Alt 3a was the framing in the original brief; the per-pack
refinement is the load-bearing change.

### Alt 4 — New axis on the contract: `(primitive × adapter × scope × install-route)`

Make install-route a fourth axis alongside primitive, adapter, and
scope, with per-route projection forks where they would differ.

**Why not chosen:** RFC-0004 §Drawbacks already flagged that every
new install route "doubles the conformance surface." Most
install-route differences don't affect projection — Claude-plugins
and the CLI both project skills to `.claude/skills/`, agents to
`.claude/agents/`, and so on. The route differences manifest in the
install-marker contract and in install-time mechanics, not in
projection. A single `install-routes` array plus per-route
conformance cases is sufficient without a new axis; this RFC takes
the minimal change.

### Alt 5 — Bundle this RFC with APM parity

Solve both gaps in one RFC.

**Why not chosen:** APM has native pre/post-install lifecycle hooks
per the [APM package-anatomy reference](https://microsoft.github.io/apm/concepts/package-anatomy/),
so the natural APM design is option (b) — exactly the design
Claude-plugins doesn't yet allow. A combined RFC would either flatten
both routes to option (a) (worse for APM than necessary) or carry two
conditional designs that make the conformance suite harder to reason
about. The marker contract is route-agnostic by design; each route's
RFC argues its hook surface on its own merits.

## Drawbacks

### Claude-plugin install: first session may not fire the `SessionStart` hook

[anthropics/claude-code#10997](https://github.com/anthropics/claude-code/issues/10997)
documents that `SessionStart` hooks do not execute on the *first*
session after a plugin is loaded from a GitHub marketplace: the
marketplace fetch is asynchronous, and hooks register only after the
cache lands. On subsequent sessions, `SessionStart` fires
reliably.

Practical effect: the install→adapt nudge appears one session late on
the very first install of a Claude-plugins-routed pack. Once the
cache is warm, subsequent installs (additional packs, upgrades) fire
on the same session.

Why this is acceptable: graceful degradation, not contract failure.
The marker still gets written on session 2; `/adapt-to-project`
still works as documented; the only cost is one delayed nudge on
brand-new-install. The bug is upstream and likely to land. See
[Unresolved questions § Q1](#unresolved-questions) for the
mitigation-policy decision.

### Marketplace-review friction risk

Anthropic curates the official Claude-plugins marketplace; community
plugins go through review per
[`anthropics/claude-plugins-official`](https://github.com/anthropics/claude-plugins-official).
The canonical Anthropic `SessionStart` example writes inside
`${CLAUDE_PLUGIN_DATA}` (installing `node_modules` into the plugin's
persistent data directory). The writer this RFC proposes writes
**outside** that territory — to `<repo>/.adapt-install-marker.toml`
or `~/.agentbundle/.adapt-install-marker.toml` — because the marker
file's location is fixed by
[`docs/specs/adapt-to-project/spec.md:71-73`](../specs/adapt-to-project/spec.md).

Mitigation: pre-disclose the behaviour in the plugin description
submitted for marketplace review. The marker is a small TOML file
(50-100 bytes per pack entry), not an executable, auto-consumed by
the LLM skill.

### Adopter-trust and partial-write recovery

Every Claude-plugins install of any pack in the catalogue now ships
executable Python that writes outside `${CLAUDE_PLUGIN_DATA}` on
first session start. An adopter who scans plugin contents before
installing will see this. Three failure modes are real:

- **(a) Marker written, adaptation later fails.** The adopter sees a
  `<repo>/.adapt-install-marker.toml` they didn't expect, with no
  record of what created it. *Mitigation:* every pack's README
  documents the marker's purpose, exact write location, and
  "consumed-on-first-`/adapt-to-project`-run" lifetime, so the
  on-disk artifact is explained.
- **(b) Mid-write failure (disk full, permission denied at
  `~/.agentbundle/`).** *Mitigation:* the writer uses `os.replace`-
  based atomic rename for the marker (Proposal § Write step 3); a
  failed write leaves the previous marker state intact, never a
  partial TOML file.
- **(c) Hash file written, marker write failed.** Would leave the
  next session seeing `pack-manifest-hash` match and skipping the
  retry. *Mitigation:* the hash file is written **only after** the
  marker write succeeds (Proposal § Write step 4) — a marker-side
  failure leaves the hash file untouched and the next session
  retries.

### Conformance surface grows per route

Per the prediction in
[RFC-0004 §Drawbacks](0004-install-scope-per-pack.md#drawbacks).
This RFC's contract amendment adds four conformance cases (one
*marker presence* + one *scope refusal* per route × two routes: CLI
and Claude-plugins). Each new install route added in future adds
two more.

Mitigation: only the install-marker contract is route-keyed.
Per-primitive projection cases stay shared across routes. The
route-cases share their assertion vocabulary (marker shape,
scope-refusal rail) — they're parameterised, not duplicated.

### Each pack ships an executable script in `.claude-plugin/`

The `install-marker.py` writer is bundled into every pack that
ships via the Claude-plugins route. One writer per shipped pack ⇒
one copy on disk per pack in adopter caches. The script is small
(around 80 lines of stdlib Python), but it is genuine code surface
in directories that previously held only manifest JSON.

Mitigation: the script is build-derived from a single
source-of-truth template at
`packages/agentbundle/templates/install-marker.py`. Per-pack
divergence is impossible by construction; any security fix patches
in one place and re-projects to every pack.

### Coupling between the install-marker contract and `pack.toml` shape

The writer reads `${CLAUDE_PLUGIN_ROOT}/pack.toml` to find
`[pack.install] allowed-scopes`. This means `pack.toml` must be
projected into the Claude-plugins bundle as a stable artifact —
today the file is source-only under `packs/<name>/pack.toml`, and
the build pipeline derives per-tool manifests rather than projecting
the source manifest.

Mitigation: `pack.toml` is already the single source of truth per
RFC-0004's `pack.schema.json`; projecting it is a mechanical
copy-not-transform step. The build pipeline already projects
seeds verbatim — `pack.toml` is added to that set.

### Writer ships executable Python; some adopters disable hooks

[Claude Code hooks reference](https://code.claude.com/docs/en/hooks)
documents that adopters can disable all hooks as part of a safe
setup. An adopter who disables `SessionStart` hooks for safety
will not get the install marker written.

Mitigation: surface in each pack's README (alongside the
marker-write disclosure). For adopters who want the bundle without
hooks, the `agentbundle adapt` CLI variant remains available as a
manual fallback — they run it once after install.

## Prior art

### In repo

- [RFC-0001 § Distribution outputs](0001-bundle-distribution-by-adapter-spec.md#distribution-outputs)
  — Claude-plugins is a canonical install route; per-tool manifests
  are derived from `pack.toml`.
- [RFC-0003 § Proposal](0003-spec-and-cli.md#proposal) —
  `agentbundle adapt` is the scriptable counterpart to the LLM
  skill; the CLI never invokes LLM. Sets the rail that this RFC's
  writer respects (the writer drops a marker; it does not invoke
  the skill).
- [RFC-0004 § Unresolved questions](0004-install-scope-per-pack.md#unresolved-questions)
  — raised this gap explicitly; tentatively expected the contract
  to bump per scope as adapters land. This RFC bumps per route
  instead, for the reasons in
  [Alt 4](#alt-4--new-axis-on-the-contract-primitive--adapter--scope--install-route).
- [RFC-0005](0005-user-scope-hook-support.md) — current contract
  v0.3; this RFC bumps to v0.4.
- [RFC-0007](0007-user-scope-converter-pack.md) — first user-scope
  pack ships, making the user-scope leg of this RFC's gap concrete.
- [`docs/specs/adapt-to-project/spec.md:71-73, 100-118`](../specs/adapt-to-project/spec.md)
  — marker contract and install→adapt chain definition. Unchanged
  by this RFC; this RFC adds a second writer (the `SessionStart`
  hook) that produces the same marker shape as `agentbundle install`.
- [`packs/core/.apm/hooks/session-start.py:182-193`](../../packs/core/.apm/hooks/session-start.py)
  — nudge reader. Unchanged by this RFC.

### External

- [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)
  — official plugin extension surface; documents the recommended
  `${CLAUDE_PLUGIN_DATA}` diff pattern for first-run detection;
  documents that `${CLAUDE_PLUGIN_DATA}` survives plugin updates
  and `${CLAUDE_PLUGIN_ROOT}` does not.
- [anthropics/claude-code#11240](https://github.com/anthropics/claude-code/issues/11240)
  — plugin lifecycle hook feature request, closed as duplicate.
  Confirms option (b) is not currently available.
- [anthropics/claude-code#10997](https://github.com/anthropics/claude-code/issues/10997)
  — first-session `SessionStart` bug for GitHub-marketplace plugins.
  Source of the graceful-degradation drawback.
- [APM package anatomy](https://microsoft.github.io/apm/concepts/package-anatomy/)
  — APM's `hooks/` directory with native pre/post-install lifecycle
  hooks. Reference point for why APM parity is a separate RFC.
- [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official)
  — Anthropic-managed marketplace; reference for the
  marketplace-review-friction drawback.

## Unresolved questions

1. **`#10997` mitigation policy.** Do we ship a fallback writer, or
   accept the one-session-late nudge on first install and wait for
   the upstream bug fix? Two real concerns are bundled here:
   - **Passive case** (the nudge appears one session late). Accept
     the degradation; document in pack READMEs.
   - **Active case** (the adopter follows a README that says "the
     install→adapt nudge will appear" and proactively runs
     `/adapt-to-project` in session 1 before the writer fires). The
     skill exits with "no pending adaptations," the adopter assumes
     adaptation is unnecessary, closes the session, and the
     subsequent nudge fires into an empty room. This is more
     dangerous than the passive case because the adopter has
     already moved on.
   **Author lean:** for the passive case, accept and document. For
   the active case, amend the `adapt-to-project` SKILL.md to detect
   "Claude-plugins pack on disk under `~/.claude/plugins/cache/` or
   `${CLAUDE_PROJECT_DIR}/.claude/plugins/cache/` with no
   corresponding marker entry" and treat as a fresh install — the
   skill runs class-1/2/3/4 inline without needing the
   marker. This collapses the upstream-bug exposure to the passive
   case alone. The skill amendment is in scope as a follow-on
   artifact below.

2. **Plugin uninstall handling.** When an adopter runs
   `claude plugin uninstall core`, no signal reaches our
   install→adapt chain — Claude-plugins deregisters the
   `SessionStart` hook before it can detect anything, and the
   marker file at the scope root is outside Claude-plugins'
   cleanup scope. Tier-1 cache files vanish via Claude-plugins'
   own cleanup; Tier-3 (adopter-edited) files stay. Does the
   install-marker contract need an uninstall companion (e.g., a
   `[[packs-removed]]` array surfaced as a nudge to clean up
   Tier-3 leftovers)?
   **Author lean:** out of scope for this RFC; revisit alongside
   the APM RFC. APM's post-uninstall hook gives a natural place to
   write the companion entry, and designing the uninstall side
   without that surface available now risks a Claude-plugins-only
   shape we'd later replace.

3. **Marker entry deduplication on upgrade.** When `/plugin update`
   bumps a pack version, the `SessionStart` writer detects the
   manifest hash changed and re-writes the marker. Should the new
   entry **replace** the existing one for the same pack, or
   **stack** as a separate `[[packs-installed]]` entry tagged
   `reason = "upgrade"`?
   **Author lean:** replace. The marker is a pending-adaptation
   signal, not an audit log; `/adapt-to-project` consumes-on-read,
   so stacking would surface as duplicate nudges. The CLI route's
   `agentbundle install` already overwrites on re-install.

4. **APM parity (Future Work).** APM has native pre/post-install
   hooks, so the parity design there is option (b)-shaped, not
   option (a)-shaped. Constraint this RFC must not violate: the
   choices made here (single `install-routes` array; route-keyed
   conformance; route-agnostic marker contract) must not preclude
   APM's hook-based writer landing as `install-route = "apm"` in
   the same `supported` array with no further contract changes.
   **Author lean:** confirm the constraint holds when the APM RFC
   is drafted; the marker contract is already route-agnostic by
   design, and the `install-route` field on `[[packs-installed]]`
   was added with this in mind.

5. **First Claude-plugins consumer / close trigger.** Likely
   `core` distributed via the existing Claude-plugins marketplace.
   Close this RFC when end-to-end parity is demonstrated on a
   real install: `claude plugin install core@<marketplace>`, next
   session writes `<repo>/.adapt-install-marker.toml`, core's
   nudge surfaces *"1 pack pending adaptation"*, and
   `/adapt-to-project` runs class-1/2/3/4 normally. A second
   demonstration with `converters` at user scope closes the
   user-scope leg.
   **Author lean:** verification artifacts pinned to two
   integration tests under the F-claude-plugin-install-marker
   work —
   `packages/agentbundle/tests/integration/test_claude_plugins_install_route.py::test_first_install_end_to_end_core_project_scope`
   and `::test_first_install_end_to_end_converters_user_scope` —
   plus a manual-QA matrix row under
   `docs/specs/distribution-adapters/notes/manual-qa-matrix.md`
   recording the live marketplace install demonstration.

## Follow-on artifacts

On acceptance:

- **ADR:** *Install-route is a property of the install route, not
  a fourth axis on the projection contract.* Records the rejection
  of [Alt 4](#alt-4--new-axis-on-the-contract-primitive--adapter--scope--install-route)
  in favour of the minimal `install-routes` array.
- **Contract amendment:**
  [`docs/contracts/adapter.toml`](../contracts/adapter.toml) bumps
  to v0.4; adds an `install-routes = ["cli", "claude-plugins"]` array
  key under `[adapter."claude-code"]`. Conformance suite
  (`docs/contracts/adapter.schema.json` and the fixture set under
  RFC-0003 F-conformance) gains route-keyed *marker presence* and
  *scope refusal* cases.
- **Spec amendment:**
  [`docs/specs/adapt-to-project/spec.md`](../specs/adapt-to-project/spec.md)
  § *Install→adapt handoff* gains a second writer (the per-pack
  `SessionStart` hook) producing the same marker shape as
  `agentbundle install`. The marker schema gains an optional
  `install-route` field on each `[[packs-installed]]` entry and
  marks `unresolved-markers` / `new-companions` optional under v0.4.
  Read-side fallback (scan the projected primitive tree) is the
  documented behaviour when either field is absent. A new
  *Boundaries* entry covers the build-derived per-pack
  `install-marker.py` artifact (under `.claude-plugin/scripts/`) —
  not a new top-level dependency, not adopter-modifiable, build
  output only. **Acceptance Criteria amendments:** stale-entry
  drop-on-read (see Migration path step 5) **plus** a new clause
  covering the proactive cache-scan branch introduced by the
  *adapt-to-project* skill amendment below, including its
  idempotence with the marker-consume path (the skill must not
  double-adapt when both signals are present in one session).
- **Skill amendment — `adapt-to-project` proactive-invocation
  branch.** Per [Unresolved questions § Q1](#unresolved-questions),
  the SKILL.md gains a branch that scans
  `~/.claude/plugins/cache/` and
  `${CLAUDE_PROJECT_DIR}/.claude/plugins/cache/` for known pack
  roots with no marker entry; when found, runs class-1/2/3/4
  inline. Closes the *#10997 active case* hole for adopters who
  invoke `/adapt-to-project` in session 1 before the writer fires.
- **Spec amendment:**
  [`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md)
  (RFC-0001's F-spec home) gains the route-keyed conformance cases.
- **Build-pipeline work — F-claude-plugin-derivation.**
  `agentbundle build` learns to (1) project `pack.toml` into the
  derived `.claude-plugin/`, (2) ship `install-marker.py` from a
  canonical template under
  `packages/agentbundle/templates/install-marker.py`, and (3)
  synthesise the `SessionStart` hook entry in derived
  `plugin.json`. The existing hand-authored per-pack `plugin.json`
  files migrate to a derived shape.
- **Plugin-level work — F-claude-plugin-install-marker.**
  `install-marker.py` template authored once; integration tests
  added under
  `packages/agentbundle/tests/integration/test_claude_plugins_install_route.py`
  covering: first-install marker write at each scope,
  no-write-on-warm-cache, scope refusal, plugin update marker
  replace.
- **Documentation.** Per-pack README updates disclose the
  install-marker write behaviour (marketplace-review-friction
  mitigation; hooks-disabled fallback path).
- **First consumer.** `core` via the existing Claude-plugins
  marketplace; close trigger = end-to-end demonstration of marker
  write + nudge fire + `/adapt-to-project` run per
  [Unresolved questions § Q5](#unresolved-questions).
