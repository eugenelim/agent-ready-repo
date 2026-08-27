---
title: "Install routes"
summary: "Compare the catalogue's four installation routes and choose the one that fits your agent tool, scope, and upgrade needs."
pack: _shared
kind: explanation
---

# Install routes

Four ways to install a pack from this catalogue:

| Route | Command | When it fits |
| --- | --- | --- |
| **Claude plugins** | `/plugin marketplace add <owner>/<catalogue>` then `/plugin install <pack>@<catalogue>` | You're on Claude Code and want one-line install with auto-update. **Carries only packs whose `allowed-scopes` admits `user`** — see the note below. |
| **APM** | `apm install <owner>/<catalogue>/<pack>` | You're in any other IDE harness with the [APM](https://github.com/agent-package-manager) CLI. |
| **Reference CLI** | `agentbundle install --pack <name> git+https://github.com/<owner>/<catalogue>` | You want a pinned, scriptable install with state tracking from day one. |
| **Local clone** | `git clone … && python -m pip install -e packages/agentbundle/ && agentbundle install --pack <name> . --output <target>` | Network-constrained environment, or you want both the catalogue and the runtime library editable. |

:::note
**The plugin route is user-scope only.** A Claude plugin's code lives in your
global cache and `claude plugin install` defaults to `--scope user`, so the
marketplace carries only packs that permit a user-scope install. A pack
declaring `allowed-scopes = ["repo"]` — `core`, `governance-extras`,
`iac-terraform`, `monorepo-extras`, `release-engineering`,
`user-guide-diataxis` — installs with `agentbundle install` instead. That is
the route they are scoped for, not a gap.
:::

:::caution
**Already added the marketplace before 2026-08?** Run
`/plugin marketplace update <catalogue>` and reinstall your packs. Entries
published before then used a plugin source Claude Code could not resolve to a
subdirectory, so installs succeeded but delivered nothing — check with
`/plugin details <pack>@<catalogue>`; a healthy pack reports a non-zero skill
count. A cached catalogue keeps serving the old entries until you update it.
:::

The routes share canonical pack sources, but scope and route admission decide
which files and follow-up state land. Local scope deliberately omits seeds,
adaptation markers, layout sections, and chained CLI adaptation. This page
explains why there are four routes and how to pick.

## Portable Agent Plugins catalogue output

Catalogue maintainers can also produce Agent Plugins 1.0.0 packages with the
normal build:

```bash
make build
```

Eligible skills-only packs land at `dist/agent-plugins/<pack>/`, with a root
`plugin.json` and canonical content under `skills/`. A pack carrying any other
canonical primitive is excluded, and the build diagnostic names the pack and
the complete sorted primitive set. The manifest validates offline against the
immutable schema bundled at
`agentbundle/_data/vendor/agent-plugins/1.0.0/plugin.schema.json`; the paired MCP
schema is bundled for the next phase.

This release provides package projection whose support posture is verified by
the repository documentation and build gates. It does not provide MCP behavior,
seed or adaptation projection, publication automation, client installation, or
runtime verification. Those remain separate routes or follow-on work.

:::caution
**Caveat — route 3 still requires route 4's pip install today.** The release artifact (zipapp / wheel / Homebrew) hasn't shipped yet, so until it does, getting `agentbundle` onto `$PATH` means running route 4's `python -m pip install -e packages/agentbundle/` step against a local clone. Route 3's distinction from route 4 — fetching the catalogue from a remote `git+https://` URL instead of a local clone — still applies once `agentbundle` is importable.
:::

## The install-to-adapt handoff

Projection and adaptation are separate steps, and the gap between them is why
this page names one reliable handoff rather than four. Installing a pack writes
files. Whether a projected lifecycle hook then *runs* is the runtime's decision,
and it turns on the active runtime, its managed policy, repository and hook
trust, command resolution, the output protocol, and the adaptation marker. Any
one of those can be missing or mismatched. So the handoff cannot be the hook —
it is the install's own printed output.

Routes 3 and 4 print it. Installing core with `agentbundle install`, at
repository or local scope, ends with this line:

```text
Next:     Ask your agent to run adapt-to-project for a read-only readiness check; start a new session if the skill is unavailable.
```

If the newly installed skill is not loaded yet, start a fresh agent session
first — that fallback is the tail of the printed line, which a narrow terminal
will have scrolled out of view. Routes 1 and 2 print nothing at all, which is
exactly why their next step is to invoke `adapt-to-project` directly.

A lifecycle hook may repeat that nudge. It is never the only path, and you never
need to determine whether it fired. So the division is clean: the installer
guarantees the projected files, the state and omissions specific to the scope you
chose, and this stdout. It does not guarantee hook execution or context
injection, because those are the runtime's to decide, not the installer's.

| Route and scope | Seeds | Marker and CLI adaptation | What you do next |
| --- | --- | --- | --- |
| Reference CLI, repository scope | Yes, when declared by the pack | `install` writes `.adapt-install-marker.toml` and chains `agentbundle adapt` | Follow the printed `Next:` line |
| Reference CLI, local scope | No | No marker, layout section, or chained `adapt` | Follow the printed `Next:` line; start a new agent session first if the skill is not yet available |
| Claude plugin | Only content admitted to the user-scope plugin route | **Not for `core`**, which is repo-scoped and so is never published to this route. For published packs, a `SessionStart` hook derived into each **published** pack's `.claude-plugin/plugin.json` can run the marker writer | Invoke `adapt-to-project` directly |
| APM | Package content selected for the active target | HookIntegrator can project the package hook; whether it executes is the runtime's decision | Invoke `adapt-to-project` directly |
| Local clone | Uses the selected Reference CLI scope | Same behavior as the corresponding Reference CLI row | Follow the printed `Next:` line |

Where a route writes a marker, the template at
[`packages/agentbundle/templates/install-marker.py`](../../../packages/agentbundle/templates/install-marker.py)
owns its format. The marker lets the session-start hook find unresolved work; its
presence says nothing about whether that hook ran.

## Pick by where you live

**You're on Claude Code, you have a GitHub remote, and you don't mind auto-update.** Use the Claude-plugins route. One line of setup, one line per pack, and `/plugin update` keeps you current.

**You're in another IDE.** Use APM when it supports your target. Its
HookIntegrator currently deploys hook bundles to Claude Code, Copilot, Cursor,
Gemini, Codex, Antigravity, Windsurf, and Kiro. OpenCode remains unsupported.
Deploying a hook bundle is projection, not execution — see
[the handoff above](#the-install-to-adapt-handoff) for what that turns on. This
route prints no `Next:` line, so invoke `adapt-to-project` directly.

**You want pinned versions and full state tracking.** Use the reference CLI. `agentbundle install` hashes every projected file into `.agentbundle-state.toml` at install time, so upgrade-time safety is exact from day one. The other routes need a one-shot `agentbundle init-state` after install to reach the same baseline.

**You're network-constrained or want the runtime library editable.** Clone and `python -m pip install -e packages/agentbundle/`. This is the only route where `packages/agentbundle/` and `packs/` come together in your filesystem — useful when you're also developing primitives, or when your network can fetch a git clone but not a pip package.

## The state-tracking nuance

The reference CLI is the only route that hashes projected files at install time. The other three routes lose that baseline unless you opt in:

```bash
agentbundle init-state
```

After `init-state`, all four routes behave identically on upgrade — collisions land as `*.upstream.<ext>` companions, the file-safety contract kicks in, no silent overwrites. See [the file-safety contract](file-safety-contract.md) for the Tier model and per-route mechanics.

## Codex skills (shipped)

Codex skills are a first-class projection: `direct-directory` writes to `.agents/skills/<name>/SKILL.md` instead of the old managed-block inline shape. The same skills also project to `~/.agents/skills/` when an adopter passes `--scope user` against a pack declaring `codex` in its `allowed-adapters`. The four catalogue user-scope packs (`atlassian`, `figma`, `converters`, `contracts`) all do; see the [Codex user-scope how-to](../how-to/install-user-scope-pack-into-codex.md). A future RFC would add a `codex-plugins` install route (sibling to `claude-plugins`) so Codex's own plugin manager can install these packs without going through the CLI/APM routes — that work isn't opened yet.

## The `--adapter` override

Adopters with multiple IDE homes populated (`~/.claude/` plus `~/.kiro/`, say) can override the resolver's first-match-wins pick by passing `--adapter <name>` to `agentbundle install`. The flag is admitted at **both scopes**: at user scope it must name a user-scope-capable adapter from the pack's `allowed-adapters`; at repo scope every shipped adapter is admissible (Copilot included). The pinned refuse-and-explain messages name the field and the contract version, so failed installs are loud, not silent.

## `--emit-install-routes` — catalogue-publishing opt-in

At repo scope, `agentbundle install --pack X --scope repo .` defaults to per-IDE projection. The dist-tree producer (`<repo>/claude-plugins/<pack>/`, `<repo>/apm/<pack>/`) is an explicit opt-in via `--emit-install-routes`:

```
agentbundle install --pack architect --scope repo --emit-install-routes .
```

Catalogue maintainers scripting the dist-tree shape for publishing pipelines add this one flag to their existing invocations. The `claude-plugins/<pack>/` half is emitted only for packs the plugin route carries — a repo-only pack like `core` yields `apm/<pack>/` alone. The flag is bound to `--scope repo` and mutually exclusive with `--adapter` at that scope (the dist-tree producer doesn't pick a single adapter). It carries a `DeprecationWarning` and is targeted for removal in the next minor.

## Where to read next

- [The file-safety contract](file-safety-contract.md) — the Tier-1/2/3 guarantee that protects your edits.
- [How to adapt a freshly-installed pack](../../core/how-to/adapt-to-project.md) — what the post-install agent session actually does.
- [How to upgrade an installed pack](../how-to/upgrade-packs.md) — and how the file-safety contract applies on upgrade.
- [Installing `agentbundle` from a clone](../how-to/install-agentbundle-from-clone.md) — the route 4 walkthrough.
