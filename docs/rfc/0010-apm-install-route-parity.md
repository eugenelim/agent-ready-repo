# RFC-0010: APM install-route parity — per-pack `SessionStart` writer projected through APM's HookIntegrator

- **Status:** Accepted
- **Author:** eugenelim
- **Date opened:** 2026-05-25
- **Date closed:** 2026-05-25
- **Related:** [RFC-0001](0001-bundle-distribution-by-adapter-spec.md)
  (APM as a canonical install route; intentional `.apm/` source-layout
  convergence); [RFC-0003](0003-spec-and-cli.md) (CLI install→adapt
  chain; rail this RFC's writer respects);
  [RFC-0004](0004-install-scope-per-pack.md) (raised this gap as an
  Unresolved question; scope dimension this RFC consumes; corrects
  an inherited default-scope assumption);
  [RFC-0007](0007-user-scope-converter-pack.md) (Accepted; first
  user-scope pack — makes the user-scope leg of this gap concrete);
  [RFC-0008](0008-claude-plugins-install-route-parity.md) (immediate
  precedent — Claude-plugins parity via the same writer pattern;
  contract currently at v0.4; this RFC bumps to v0.5). Touches
  [`docs/specs/adapt-to-project/spec.md`](../specs/adapt-to-project/spec.md),
  [`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md),
  and [`docs/contracts/adapter.toml`](../contracts/adapter.toml).

## Summary

`apm install` lands a pack's primitives under the target tool's
directories (`.claude/`, `.github/`, `.cursor/`, …) but never writes
`.adapt-install-marker.toml`; the existing core-pack nudge sees
nothing and the bundle ships unadapted. Close the gap by deriving —
for every pack that ships via the APM route — a hook file at
`.apm/hooks/install-marker.json` declaring a `SessionStart` entry
that invokes the same canonical writer RFC-0008 authored for the
Claude-plugins route. APM's `HookIntegrator`
([`src/apm_cli/integration/hook_integrator.py`](https://github.com/microsoft/apm/blob/main/src/apm_cli/integration/hook_integrator.py))
projects the hook per target tool with no further per-pack work.
Adapter contract bumps `0.4 → 0.5` by appending `"apm"` to the
existing `install-routes` array on `[adapter."claude-code"]`; per-route
conformance cases mirror RFC-0008's pair. No new `pack.toml` table;
no new contract axis; no new writer template.

## Motivation

[`docs/specs/adapt-to-project/spec.md:100-118`](../specs/adapt-to-project/spec.md)
defines the install→adapt chain as: `agentbundle install` writes
`.adapt-install-marker.toml` at the scope's root, chains in-process
to `agentbundle adapt`, and the core pack's session-start hook
([`packs/core/.apm/hooks/session-start.py:182-193`](../../packs/core/.apm/hooks/session-start.py))
surfaces *"you have pending adaptations from pack(s) X; run
`/adapt-to-project`."*

RFC-0008 closed this gap for the Claude-plugins route. The APM route
is the remaining canonical install route without parity. Today an
adopter who declares an `agent-ready-repo` pack in their `apm.yml`
and runs `apm install` gets the bundle's primitives projected to the
target tool's directories — the `HookIntegrator` even rewrites runtime
tool-use hooks (`PreToolUse`, `PostToolUse`, `Stop`, `SessionStart`)
per target — but no marker file is written, no nudge fires, and the
adopter receives an unadapted bundle. `AGENTS.md` still says
`<project-name>`, the docs tree still has stock seeds, and the
class-2/3/4 discoveries `/adapt-to-project` is meant to surface
never happen. The failure mode is identical to RFC-0008's; the
installer is different.

**Two assumptions inherited from earlier RFCs must be corrected here.**

[RFC-0004 § Unresolved questions:582-586](0004-install-scope-per-pack.md#unresolved-questions)
framed APM as *"defaults to user; Claude-plugins caches at
`~/.claude/plugins/cache/`."* Against
[APM's `apm install` reference](https://microsoft.github.io/apm/reference/cli/install/)
the default is **project**, not user — `apm install` deploys to the
current directory's tool targets; `-g, --global` switches to user
(`~/.apm/`). RFC-0007 §Distribution-route parity carried the same
default-user inheritance forward without correcting it. This RFC
corrects the inheritance: the scope mapping below is grounded in
APM's live docs, not RFC-0004's tentative framing.

The original briefing for this RFC also assumed APM had *"native
pre/post-install lifecycle hooks"* and that the natural design was
RFC-0008's [Alt 2](0008-claude-plugins-install-route-parity.md#alt-2--option-b-pluginjson-post-install-lifecycle-hook)
(option-b). Against APM's actual source — the `HookIntegrator` at
[`src/apm_cli/integration/hook_integrator.py:1-44, 153-174`](https://github.com/microsoft/apm/blob/main/src/apm_cli/integration/hook_integrator.py),
surfaced via [DeepWiki § 6.4](https://deepwiki.com/microsoft/apm/6.4-hook-integration)
— APM *"does not support arbitrary code execution during installation."*
The `hooks/` and `.apm/hooks/` directories hold **runtime tool-use
hooks** (passed through to the target tool to fire at agent runtime),
not install-time lifecycle hooks. The
[package-anatomy page](https://microsoft.github.io/apm/concepts/package-anatomy/)
calls these *"lifecycle hooks fired on pre/post install, compile, or
run events"*, but the
[hooks-and-commands authoring page](https://microsoft.github.io/apm/producer/author-primitives/hooks-and-commands/)
and the source both confirm the only events that exist are tool-use
events. APM's `scripts:` block is the closest install-shaped surface
(named shell commands invoked manually via experimental `apm run`)
— it doesn't auto-fire on install.

So APM and Claude-plugins share the same constraint by different
mechanisms: neither installer exposes a hook that runs at install
time. The same writer pattern is the natural answer for both.

## Proposal

### Who writes the marker

A `SessionStart` hook declared in each pack's
`.apm/hooks/install-marker.json` invokes the same canonical
stdlib-Python writer RFC-0008 authored. APM's `HookIntegrator`
copies the hook to the target tool's hook directory and rewrites
script paths during `apm install` integration; the writer itself
fires on the next session of the target tool, detects first install
or update, and writes the marker.

**Single source of truth.** The writer script is the same
`packages/agentbundle/templates/install-marker.py` template
RFC-0008 named. The script's existing first-run detection
(`${CLAUDE_PLUGIN_DATA}/pack-manifest-hash` diff or marker-entry
absence) keeps working at Claude Code targets unchanged; for
non-Claude-Code targets the equivalent `${PLUGIN_ROOT}`-rooted token
APM rewrites to is documented per the
[hooks-and-commands page](https://microsoft.github.io/apm/producer/author-primitives/hooks-and-commands/)
(`${PLUGIN_ROOT}`, `${CURSOR_PLUGIN_ROOT}`, …). The template's
small portability shim — *"data directory = `${CLAUDE_PLUGIN_DATA}`
if set else `${PLUGIN_ROOT}/.data` else
`${CURSOR_PLUGIN_ROOT}/.data`"* — is the one change to the shared
template this RFC requires; landed once, both routes consume it.

**Route detection.** The writer needs to record `install-route` on
the marker entry (the field RFC-0008 added). The build pipeline
hard-codes the route at projection time: when `agentbundle build`
emits `dist/apm/<pack>/.apm/hooks/install-marker.json`, the hook's
`command` line passes `--install-route apm` as an argument; the
RFC-0008-emitted `plugin.json` hook passes `--install-route
claude-plugins`. The writer treats the flag as authoritative — no
runtime route-sniffing.

**Scope detection.** Per [Scope mapping](#scope-mapping) below. The
writer reads the projected hook's own path at runtime
(`os.path.dirname(__file__)`-style) and matches the projected-tool
scope root against APM's two install locations.

### Scope mapping

APM installs to one of two locations per
[`apm install`](https://microsoft.github.io/apm/reference/cli/install/):

| APM scope                     | CLI invocation             | Marker file                                 |
| ----------------------------- | -------------------------- | ------------------------------------------- |
| Project (default)             | `apm install <source>/<pack>`         | `<repo>/.adapt-install-marker.toml`         |
| User (`--global`)             | `apm install -g <source>/<pack>`      | `~/.agent-ready/.adapt-install-marker.toml` |

The writer detects which by inspecting whether the projected hook
sits under the current working tree (project) or under `$HOME`
(user). Falls through to "no marker write; exit 0" if neither
matches, on the same no-partial-state rail RFC-0008 §Proposal step 1
established.

`pack.toml`'s `[pack.install] allowed-scopes` is enforced at the
writer layer as defence in depth, identical to RFC-0008 §Proposal
step 2. The refusal-and-warn rail emits the same one-line stderr
message and exits 0 without writing the marker or the hash file.

### Pack-level declarations

**No new `[pack.install.apm]` table on `pack.toml`.** The APM-side
wiring is fully derived by `agentbundle build` from fields
`pack.toml` already declares, mirroring RFC-0008's no-new-table
approach. The derivation produces one new artifact per pack under
the projected `dist/apm/<pack>/`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${PLUGIN_ROOT}/.apm/hooks/install-marker.py\" --install-route apm",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

`install-marker.py` is copied verbatim from the same source-of-truth
template at `packages/agentbundle/templates/install-marker.py` that
RFC-0008's claude-plugins route projects from. One canonical writer;
per-pack divergence is impossible by construction; per-route
divergence is bounded to the one-line `--install-route` flag the
build sets at projection time.

The `.apm/` overlap (APM's source layout and ours both use the same
path) is intentional convergence — RFC-0001 §3 chose `.apm/` because
APM is one of the canonical install routes. The convergence makes
the projection a near-no-op: `agentbundle build` writes
`dist/apm/<pack>/.apm/hooks/install-marker.json` and
`dist/apm/<pack>/.apm/hooks/install-marker.py`, and APM's
HookIntegrator picks them up unchanged.

### Multi-tool semantics

APM compiles to seven targets per its
[README](https://github.com/microsoft/apm/blob/main/README.md):
Copilot, Claude, Cursor, OpenCode, Codex, Gemini, Windsurf. APM's
`HookIntegrator` currently projects `SessionStart` hooks to four of
the seven — Claude Code, Copilot, Cursor, Gemini — per
[DeepWiki § 6.4](https://deepwiki.com/microsoft/apm/6.4-hook-integration).
The remaining three:

- **Codex** is AGENTS.md-driven and has no documented hook surface.
  APM passes it manifest text, not hooks.
- **OpenCode** *"silently skips"* hooks per APM's own docs.
- **Windsurf**'s hook story is undocumented in the sources surveyed
  for this RFC.

Coverage is therefore **four of seven**: an `apm install` of a pack
into a Claude-Code, Copilot, Cursor, or Gemini target fires the
writer on next session; an install into Codex, OpenCode, or
Windsurf silently lacks the chain. For the unsupported three the
adopter runs `agentbundle adapt --scope <project|user>` once after
install as the manual fallback — the same gesture that already
serves adopters who disable hooks for safety (RFC-0008 §Drawbacks
*Writer ships executable Python; some adopters disable hooks*).
Documented per-target in `docs/specs/distribution-adapters/spec.md`
on acceptance.

**Kiro is not currently an APM target.** Our adapter contract
declares Kiro as a first-class adapter
([`docs/contracts/adapter.toml:124-181`](../contracts/adapter.toml)),
but APM does not compile to Kiro today — [microsoft/apm#702](https://github.com/microsoft/apm/issues/702)
is an open feature request from April 2026 to add Kiro to the
target set. When APM lands Kiro support, our writer projects
automatically through APM's HookIntegrator with no change to this
RFC's design — Kiro has a documented `SessionStart`-equivalent
agent-hook surface
([`kiro.dev/docs/hooks/`](https://kiro.dev/docs/hooks/), already
consumed by RFC-0005's hook-wiring work). Until then, Kiro adopters
reach `agent-ready-repo` packs via the CLI route (RFC-0003), not
the APM route. Captured in
[Unresolved questions § Q7](#unresolved-questions) as a
watch-this-space item, not a blocker.

The single-authored-hook → multi-target-projection fan-out is APM's
job, not ours. RFC-0008's Alt 3a (central detector in `core`) was
rejected because it required `core` to enumerate other packs'
adapter-specific cache directories — a pack-boundary violation.
That objection does not apply here because each pack ships its own
hook; the fan-out happens inside APM's HookIntegrator, on APM's
own cache layout (`apm_modules/`), and never crosses pack
boundaries on our side.

### Contract impact

Adapter contract bumps from v0.4 to v0.5. The shape change is one
element appended to the existing `install-routes` array under
`[adapter."claude-code"]`, plus per-route conformance cases mirroring
RFC-0008's pair. No projection-table forks; no per-route projection
differences; no new axis.

```toml
[contract]
version = "0.5"

[adapter."claude-code"]
install-routes = ["cli", "claude-plugins", "apm"]
```

**Conformance cases added.** One pair per declared route, mirroring
RFC-0008's shape:

- *Marker presence.* After installing pack P via APM into scope S
  (project or user), the marker file at the scope-canonical path
  contains a `[[packs-installed]]` entry with `name = P` and
  `install-route = "apm"`. Asserted on **session 2 or later** of
  the target tool, on the same RFC-0008-pinned cache-warmup rail
  (the first session may not fire the writer because the integrated
  hook landed mid-session).
- *Scope refusal.* When `apm install [-g]` requests a scope not in
  pack P's `allowed-scopes`, the writer emits the refusal-and-warn
  rail and leaves no partial state.

The `install-routes` array stays on `[adapter."claude-code"]` for
this RFC's purposes — APM is a route the bundle ships *through*, and
the bundle's target adapter is still Claude Code (and its peers).
Whether `install-routes` should also be declared on the Kiro /
Copilot / Codex adapters once they consume the APM route is
captured in [Unresolved questions § Q3](#unresolved-questions).

### Migration path

1. **`agentbundle build`** learns to project
   `.apm/hooks/install-marker.json` and `.apm/hooks/install-marker.py`
   into each pack's `dist/apm/<pack>/.apm/hooks/` from the canonical
   template, with `--install-route apm` baked into the projected
   hook `command`.
2. **Existing CLI and Claude-plugins install paths unchanged.**
   `agentbundle install` keeps writing `install-route = "cli"`;
   RFC-0008's plugin.json writer keeps writing
   `install-route = "claude-plugins"`. The shared template gains
   the small portability shim covering `${PLUGIN_ROOT}` /
   `${CURSOR_PLUGIN_ROOT}` data-directory fallback.
3. **Existing markers remain valid.** `install-route` is already
   an optional additive field per RFC-0008's v0.4 amendment;
   adding `"apm"` as a permitted value is a write-side change only
   — readers that don't know the value treat it as any other
   string.
4. **First APM install of any pack** triggers the writer on next
   session of the target tool (subject to the per-tool first-session
   caveat — see [Drawbacks § first session may not fire](#first-session-may-not-fire-the-writer));
   the marker drops; the core pack's nudge surfaces it.
5. **Stale entries on uninstall** follow the same read-side
   drop-on-mismatch rail RFC-0008 §Migration step 5 already
   pinned — `/adapt-to-project` detects "pack not installed at any
   scope" by walking both `apm_modules/` and Claude-plugins
   `~/.claude/plugins/cache/` cache layouts and silently drops the
   entry. APM's stable `apm_modules/` layout makes this enumeration
   trivial on our side (APM-owned, consistent across packs); the
   pack-boundary objection from RFC-0008 Alt 3a does not apply at
   read time.
6. **No data migration of historical markers.** Same as RFC-0008.

## Alternatives considered

### Alt 1 — Do nothing

Leave the APM leg of the gap open. Adopters who declare
`agent-ready-repo` packs in `apm.yml` continue to receive
unadapted bundles. RFC-0001 picked APM as a canonical route; the
silent-no-adaptation outcome is the failure mode RFC-0001 set out
to prevent. **Why not chosen:** RFC-0007 already shipped the
user-scope leg of the converter pack via APM-as-distribution; the
gap is exercised by a Accepted RFC's first consumer. Indefinite
deferral is a permanent footgun, not a position.

### Alt 2 — Option (b): APM lifecycle hook in `apm.yml`

Declare a `post-install` hook in `apm.yml` and have APM execute it
during `apm install`'s integration phase. This was the briefing's
load-bearing premise and the natural shape if it were available.

**Why not chosen:** APM does not support arbitrary code execution
during installation. Per
[DeepWiki § 6.4](https://deepwiki.com/microsoft/apm/6.4-hook-integration)
on `src/apm_cli/integration/hook_integrator.py:1-44, 153-174`:
*"APM does not support arbitrary code execution during installation.
The HookIntegrator runs during apm install to perform a specific,
contained task: copying hook definitions from packages and rewriting
script paths for target tools."* APM's `scripts:` block is the
closest install-shaped surface but it's invoked manually via
experimental `apm run`, not at install. The
[package-anatomy page](https://microsoft.github.io/apm/concepts/package-anatomy/)
calls the `.apm/hooks/` directory *"lifecycle hooks fired on pre/post
install, compile, or run events"*, but the
[authoring page](https://microsoft.github.io/apm/producer/author-primitives/hooks-and-commands/)
and the source agree: the only events that exist are tool-use
(`PreToolUse`, `PostToolUse`, `Stop`, `SessionStart`). The
package-anatomy phrasing reads as aspirational documentation, not a
schema we can build against.

If APM publishes install-time lifecycle hooks in a future release,
migration is mechanical: the writer moves from `SessionStart` to
`postInstall`, the per-tool fan-out collapses to one execution per
install, and the conformance suite's APM case stays unchanged.
Reopen this RFC for that amendment if and when those hooks land.

### Alt 3 — Single APM-native `scripts:` entry the adopter runs manually

Declare a `scripts:` entry in the projected `apm.yml` and document
`apm run adapt` as the post-install adopter gesture.

**Why not chosen:** the `scripts:` mechanism is experimental per the
docs and adds an explicit gesture (`apm run adapt`) that the
install→adapt chain is supposed to make unnecessary. The
`agentbundle adapt` manual fallback already exists for adopters who
prefer an explicit gesture (and for the three APM targets without
hook surfaces — Codex, OpenCode, Windsurf — where it's the only
option). Promoting it to the primary path for the four
hook-capable targets discards the silent-adaptation property
RFC-0001 picked as the headline UX.

### Alt 4 — Per-target `.apm/hooks/install-marker-<tool>.json` (one writer per supported target)

Author four separate hook JSON files — one per Claude Code,
Copilot, Cursor, Gemini — instead of relying on APM's HookIntegrator
to project a single authored hook.

**Why not chosen:** APM's HookIntegrator already handles per-target
projection from a single authored hook keyed by event. Shipping four
files duplicates work the installer is designed to do, and the
per-target rewrites (`${PLUGIN_ROOT}` → `${CLAUDE_PLUGIN_ROOT}` /
`${CURSOR_PLUGIN_ROOT}`) are exactly what `HookIntegrator` already
does. Single authored file, four projections, one writer template.

### Alt 5 — Add a fourth axis to the contract: `(primitive × adapter × scope × install-route)`

Same alternative RFC-0008 considered and rejected. APM-route
projection produces the same file layout as the CLI route's APM
recipe already produces today (`dist/apm/<pack>/`); the route
differences manifest in the install-marker contract and in
install-time mechanics, not in projection.

**Why not chosen:** RFC-0008 §Alt 4 reasoning carries over verbatim.
A single `install-routes` array plus per-route conformance cases is
sufficient.

### Alt 6 — Bundle the RFC-0008 status-bump cleanup into this RFC

The briefing flags that RFC-0008 reads `Status: Draft` despite
PR #105 having shipped. Bundling its status update with this RFC
would close two paperwork items at once.

**Why not chosen:** the status bump is housekeeping, not a
governance change. RFC-0008's `Accepted` flip belongs in a separate
docs-only PR (or as part of whoever lands the RFC-0008 acceptance
ceremony). Bundling muddies what reviewers are looking at.

## Drawbacks

### First session may not fire the writer

APM's HookIntegrator copies hooks into the target tool's hook
directory during `apm install`; the target tool registers them on
its next session-start scan. For Claude Code specifically,
[anthropics/claude-code#10997](https://github.com/anthropics/claude-code/issues/10997)
documents that `SessionStart` hooks may not fire on the very first
session after a fresh plugin/hook load. RFC-0008 already named this
caveat. Practical effect: the install→adapt nudge appears one
session late on the very first APM install of a Claude-Code-targeted
pack. Once the hook is registered, subsequent installs fire on the
same session.

The other three HookIntegrator-covered tools (Copilot, Cursor,
Gemini) have their own first-session semantics not surveyed in
depth for this RFC; the [Drawbacks § APM-target hook-firing
matrix](#apm-target-hook-firing-matrix-uncharacterised) below
captures this as a follow-on-research item.

Why this is acceptable: graceful degradation, not contract failure
— same rationale RFC-0008 already accepted. The active-case
mitigation RFC-0008 added to the `adapt-to-project` skill (proactive
cache scan when the adopter invokes `/adapt-to-project` in session 1
before the writer fires) extends naturally to walk APM's
`apm_modules/` cache too. Captured in
[Follow-on artifacts](#follow-on-artifacts).

### APM-target hook-firing matrix uncharacterised

This RFC commits to four target tools (Claude Code, Copilot,
Cursor, Gemini) firing the writer, but only Claude Code's
SessionStart semantics are characterised in depth (via RFC-0008's
prior research). Copilot, Cursor, and Gemini are claimed under
`HookIntegrator` coverage per APM's docs but their first-session
behaviour, hook-disable surface, and equivalents of
`${CLAUDE_PLUGIN_DATA}` were not surveyed for this RFC. Three of
seven targets (Codex, OpenCode, Windsurf) lack hook surfaces
entirely and silently lack the chain.

Mitigation: the implementation spec lands a small per-target
characterisation matrix as a `Tests:` row, documenting first-session
behaviour and the writer's data-directory token per tool, before
the conformance suite asserts on more than the Claude-Code case.
The three no-hook targets are documented explicitly with the
`agentbundle adapt` manual-fallback gesture; not a regression
against today (today they get no adaptation either), but an
honest disclosure.

### `.apm/` overlap with APM's source layout

The writer ships at `.apm/hooks/install-marker.py` inside the
projected APM package. APM's own source layout also names `.apm/`.
The overlap is intentional convergence (RFC-0001 §3 chose `.apm/`
because APM is a canonical route), not coupling — but a future
APM release that re-purposes the `.apm/hooks/` slot for something
other than tool-use hooks would conflict with us silently.

Mitigation: the shared layout is documented in RFC-0001 and named
in this RFC's Proposal. The risk is monitored, not designed away;
if APM's `.apm/hooks/` semantics drift, we treat the conflict as
this RFC's reopen-trigger.

### Coverage gap: three APM targets silently lack the chain

Codex, OpenCode, Windsurf adopters who `apm install` a pack get the
primitives projected but never receive a marker write. The manual
`agentbundle adapt` fallback exists, but the silent-no-adaptation
property RFC-0001 set out to prevent applies to those three routes.

Mitigation: the implementation spec documents this per-target;
README updates for affected packs surface the manual-fallback
gesture; the conformance suite's APM case explicitly enumerates
the four covered targets and the three uncovered ones. Closing
the three is contingent on APM upstream adding hook surfaces for
them — out of our hands.

### Adopter-trust and partial-write recovery — inherited

Same three failure modes RFC-0008 §Drawbacks already named
(marker-without-adaptation, mid-write failure, hash-without-marker).
The shared writer template handles all three identically. New
exposure here: the writer now ships inside `.apm/hooks/`, which
some adopters scan for review before running `apm install`.
README disclosure (same hook adopters already disclose for the
Claude-plugins route) covers it.

### Conformance surface grows per route

Per RFC-0008's prediction inherited from RFC-0004 §Drawbacks. This
RFC's contract amendment adds two more conformance cases (one
*marker presence* + one *scope refusal* for the APM route). Every
new install route added in future adds two more.

Mitigation: same RFC-0008 reasoning — only the install-marker
contract is route-keyed; per-primitive projection cases stay
shared; the route-cases are parameterised, not duplicated.

### APM upstream may publish its own adapter contract

[RFC-0001 §4](0001-bundle-distribution-by-adapter-spec.md) named
this risk explicitly: APM may upstream a per-tool adapter contract
someday and conflict with ours. The HookIntegrator currently lives
inside APM's source (`src/apm_cli/integration/`) with no
documented third-party extension surface. Our writer is a normal
APM-shaped hook (a JSON file under `.apm/hooks/` keyed by
`SessionStart`); it does not require APM to publish anything new,
and it does not foreclose a future contribution path if APM ever
opens an adapter-contract extension surface.

Mitigation: capture as [Unresolved questions § Q5](#unresolved-questions);
no design change required today.

## Prior art

### In repo

- [RFC-0001 § Distribution outputs](0001-bundle-distribution-by-adapter-spec.md#distribution-outputs)
  — APM is a canonical install route; `.apm/` layout convergence
  with APM is intentional.
- [RFC-0003 § Proposal](0003-spec-and-cli.md#proposal) — CLI
  install→adapt chain; *Never invoke an LLM* rail respected by
  this RFC's writer.
- [RFC-0004 § Unresolved questions](0004-install-scope-per-pack.md#unresolved-questions)
  — raised this gap explicitly; this RFC corrects the inherited
  "APM defaults user" assumption.
- [RFC-0007 § Distribution-route parity](0007-user-scope-converter-pack.md)
  — first user-scope pack ships; explicitly defers APM parity to
  this RFC.
- [RFC-0008 § Proposal](0008-claude-plugins-install-route-parity.md#proposal)
  — same writer pattern; same canonical template; same contract
  shape (route-keyed conformance, not route-keyed projection).
- [`docs/specs/adapt-to-project/spec.md:71-73, 100-118`](../specs/adapt-to-project/spec.md)
  — marker contract and install→adapt chain. Unchanged by this
  RFC; the APM route writes the same marker shape.
- [`docs/specs/distribution-adapters/spec.md:103, 159, 180`](../specs/distribution-adapters/spec.md)
  — `per-pack-apm-package` recipe already produces `dist/apm/<pack>/`;
  `install-route = "apm"` already enumerated in the recipe rule.
- [`packages/agentbundle/templates/install-marker.py`](../../packages/agentbundle/templates/install-marker.py)
  — canonical writer template introduced by RFC-0008; this RFC
  adds the small data-directory portability shim and the
  `--install-route` flag.

### External

- [Microsoft APM — package anatomy](https://microsoft.github.io/apm/concepts/package-anatomy/)
  — declares `.apm/hooks/` exists; phrasing about pre/post-install
  events is aspirational against the source.
- [Microsoft APM — hooks-and-commands authoring](https://microsoft.github.io/apm/producer/author-primitives/hooks-and-commands/)
  — JSON-keyed-by-event shape (`PreToolUse`, `PostToolUse`,
  `SessionStart`, …); `${PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_ROOT}` /
  `${CURSOR_PLUGIN_ROOT}` token resolution; per-target portability
  story.
- [Microsoft APM — `apm install` reference](https://microsoft.github.io/apm/reference/cli/install/)
  — default scope is project; `-g, --global` switches to user.
  Lockfile `apm.lock.yaml` written every install.
- [Microsoft APM — README (compile targets)](https://github.com/microsoft/apm/blob/main/README.md)
  — seven compile targets (Copilot, Claude, Cursor, OpenCode,
  Codex, Gemini, Windsurf); hook portability across the four
  HookIntegrator-covered tools.
- [DeepWiki — APM Quick-start (install flow)](https://deepwiki.com/microsoft/apm/2.2-quick-start)
  — 4-step install (resolve → download → integrate → lock); no
  package-declared post-install execution at any step.
- [DeepWiki — APM § 6.4 Hook Integration](https://deepwiki.com/microsoft/apm/6.4-hook-integration)
  — `src/apm_cli/integration/hook_integrator.py:1-44, 153-174`;
  *"APM does not support arbitrary code execution during
  installation."* Source for the central design pivot.
- [anthropics/claude-code#10997](https://github.com/anthropics/claude-code/issues/10997)
  — first-session SessionStart bug; same caveat applies to the
  Claude-Code APM target.

## Unresolved questions

1. **APM-target first-session matrix.** Only Claude Code's
   SessionStart first-session semantics are characterised (via
   RFC-0008's prior work and #10997). Copilot, Cursor, Gemini may
   have analogous quirks unsurveyed in this RFC.
   **Author lean:** the implementation spec adds a small
   characterisation task — install the writer on each target,
   record when the writer first fires (session 1, session 2,
   session N), and document the per-target equivalent of
   `${CLAUDE_PLUGIN_DATA}`. Not gating this RFC; gating the
   conformance suite's claims about coverage.

2. **Coverage of the three no-hook APM targets.** Codex, OpenCode,
   Windsurf adopters silently lack the chain. The `agentbundle adapt`
   manual fallback exists. Should the per-pack README ship a
   target-aware install snippet that pops the manual gesture only
   when the adopter installs into one of the three?
   **Author lean:** defer to the per-pack README work in
   `F-apm-install-marker` (Follow-on artifacts). A static
   per-target snippet is overkill until we have an adopter who
   complains about silence on a no-hook target; the conformance
   suite's enumeration of covered-vs-uncovered targets is the
   first-line disclosure.

3. **`install-routes` array on adapters other than Claude Code.**
   Today the array lives on `[adapter."claude-code"]` only. APM
   compiles to seven targets; Kiro doesn't ship via APM today but
   could. Should the contract gain an `install-routes` declaration
   on each adapter, with per-adapter route enumerations?
   **Author lean:** no — keep the array on the adapter that
   declares conformance for the route. APM as a *route* ships
   primitives projected for many adapters; the conformance assertion
   ("the install→adapt chain works after `apm install` for adapter
   X") is naturally per-adapter. Promoting to a top-level
   `[install-route]` table is the next natural shape if more
   routes land; out of scope for this RFC.

4. **Stacking vs. replace on `apm install` upgrade.** When an
   adopter runs `apm install` against an updated `apm.lock.yaml`,
   the HookIntegrator re-projects the writer hook. The writer
   detects the manifest hash changed and re-writes the marker
   entry. RFC-0008 §Q3 chose *replace*, not *stack*.
   **Author lean:** inherit replace. The marker is a
   pending-adaptation signal, not an audit log.

5. **APM upstream contribution path.** Our writer is a normal
   APM-shaped hook; APM does not need to publish anything for it
   to work. If APM ever publishes an adapter-contract extension
   surface (per RFC-0001 §4's recognised risk), our contract
   becomes a candidate to contribute.
   **Author lean:** out of scope for this RFC; document the
   non-blocker disposition in Drawbacks. Revisit when APM signals
   an extension surface is coming.

6. **First APM consumer / close trigger.** Likely `core`
   distributed via an APM source the adopter declares in
   `apm.yml`. Close this RFC when end-to-end parity is demonstrated
   on a real install: `apm install agent-ready-repo/core`, next
   session of a HookIntegrator-covered target writes
   `<repo>/.adapt-install-marker.toml`, the nudge surfaces, and
   `/adapt-to-project` runs class-1/2/3/4 normally. A second
   demonstration with `converters` at `--global` scope closes the
   user-scope leg.
   **Author lean:** verification pinned to two integration tests
   under `F-apm-install-marker` —
   `packages/agentbundle/tests/integration/test_apm_install_route.py::test_first_install_end_to_end_core_project_scope`
   and `::test_first_install_end_to_end_converters_user_scope` —
   plus a manual-QA matrix row recording the live `apm install`
   demonstration.

7. **APM adds Kiro support ([microsoft/apm#702](https://github.com/microsoft/apm/issues/702)).**
   When APM lands Kiro as a compile target, the design pivots
   naturally: Kiro has a documented agent-hook surface RFC-0005
   already projects to (`.kiro/agents/<attach-to-agent>.json`
   under the `hooks` key, `merge-into-agent-json` mode), so APM's
   HookIntegrator can in principle route the writer there too.
   **Author lean:** confirm the constraint holds when APM ships
   Kiro support — the writer pattern is hook-surface-agnostic, and
   the `install-route = "apm"` marker entry doesn't change shape
   per target tool. Until then, Kiro adopters use the CLI route.
   Treat as a watch-this-space item; reopen this RFC only if APM's
   Kiro projection turns out to disallow `SessionStart`-equivalent
   hooks.

8. **APM `apm-policy.yml` interaction.** Adopter organisations
   may enforce APM policy that disallows hooks writing outside
   `${PLUGIN_ROOT}` (the writer writes to `<repo>/` or
   `~/.agent-ready/` by design). Does parity require an APM
   policy whitelist gesture documented per pack?
   **Author lean:** out of scope for this RFC; reference RFC-0008
   §Drawbacks *Marketplace-review friction risk* for the analogous
   pattern. Per-pack READMEs disclose the marker-write location;
   policy authors who enforce stricter rules can carve out the
   adapt-marker path explicitly.

## Follow-on artifacts

On acceptance:

- **ADR:** *APM install-route parity uses the same writer pattern
  as Claude-plugins, projected per target by APM's HookIntegrator.*
  Records the rejection of [Alt 2](#alt-2--option-b-apm-lifecycle-hook-in-apmyml)
  (option-b not available) and confirms RFC-0008's pattern as
  ecosystem-route-agnostic.
- **Contract amendment:**
  [`docs/contracts/adapter.toml`](../contracts/adapter.toml) bumps to
  v0.5; appends `"apm"` to `install-routes` under
  `[adapter."claude-code"]`. Conformance suite gains route-keyed
  *marker presence* and *scope refusal* cases for the APM route.
- **Spec amendment:**
  [`docs/specs/adapt-to-project/spec.md`](../specs/adapt-to-project/spec.md)
  documents the third writer (the per-pack `.apm/hooks/install-marker.json`
  projected through APM) producing the same marker shape. The
  proactive cache-scan branch (RFC-0008 follow-on) extends to walk
  `apm_modules/` alongside `~/.claude/plugins/cache/`. Acceptance
  Criteria amendment: APM-route stale-entry drop-on-mismatch.
- **Spec amendment:**
  [`docs/specs/distribution-adapters/spec.md`](../specs/distribution-adapters/spec.md)
  documents the per-pack `.apm/hooks/install-marker.json` artifact
  derivation in the `per-pack-apm-package` recipe, the four-of-seven
  APM-target coverage matrix, and the route-keyed conformance cases.
- **Skill amendment — `adapt-to-project` proactive-invocation
  branch extension.** The RFC-0008-introduced cache-scan branch
  gains a fourth walk: `apm_modules/` at both project and user
  scope (`./apm_modules/` and `~/.apm/`). Closes the first-session
  active-case hole for the APM route.
- **Build-pipeline work — F-apm-derivation.** `agentbundle build`
  projects `.apm/hooks/install-marker.json` and
  `.apm/hooks/install-marker.py` into `dist/apm/<pack>/.apm/hooks/`
  from the shared template. The template gains the small
  data-directory portability shim
  (`${CLAUDE_PLUGIN_DATA}` → `${PLUGIN_ROOT}/.data` fallback) and
  the `--install-route` flag.
- **Plugin-level work — F-apm-install-marker.** Integration tests
  under `packages/agentbundle/tests/integration/test_apm_install_route.py`
  cover: first-install marker write at project scope, first-install
  marker write at `--global` scope, scope refusal, lockfile-replay
  marker replace on upgrade, per-target characterisation (Claude
  Code, Copilot, Cursor, Gemini).
- **Documentation.** Per-pack README updates disclose the
  install-marker write behaviour at the APM route (mirror the
  RFC-0008 disclosure pattern; surface the `agentbundle adapt`
  manual gesture for the three no-hook APM targets).
- **First consumer.** `core` distributed via an APM source the
  adopter declares in `apm.yml`; close trigger = end-to-end
  demonstration of marker write + nudge fire + `/adapt-to-project`
  run on a HookIntegrator-covered target, plus a `converters`
  demonstration at `--global` scope.
