# Install routes

Four ways to install a pack from this catalogue:

| Route | Command | When it fits |
| --- | --- | --- |
| **Claude plugins** | `/plugin marketplace add <owner>/<catalogue>` then `/plugin install <pack>@<catalogue>` | You're on Claude Code and want one-line install with auto-update. |
| **APM** | `apm install <owner>/<catalogue>/<pack>` | You're in any other IDE harness with the [APM](https://github.com/agent-package-manager) CLI. |
| **Reference CLI** | `agentbundle install --pack <name> git+https://github.com/<owner>/<catalogue>` | You want a pinned, scriptable install with state tracking from day one. |
| **Local clone** | `git clone … && pip install -e packages/agentbundle/ && agentbundle install --pack <name> . --output <target>` | Network-constrained environment, or you want both the catalogue and the runtime library editable. |

The same pack content lands every way; the differences are in mechanics (state tracking, where the marker drops, how upgrades work). This page explains *why* there are four and how to pick.

> **Caveat — route 3 still requires route 4's pip install today.** [RFC-0003](../../../rfc/0003-spec-and-cli.md) § F-cli-dist's release artifact (zipapp / wheel / Homebrew) hasn't shipped yet, so until it does, getting `agentbundle` onto `$PATH` means running route 4's `pip install -e packages/agentbundle/` step against a local clone. Route 3's distinction from route 4 — fetching the catalogue from a remote `git+https://` URL instead of a local clone — still applies once `agentbundle` is importable.

## The install→adapt chain

Every install route does the same thing in two phases:

1. **Project pack content** into the target — skills, agents, hooks, seed documents, projected `.claude/` artifacts.
2. **Drop `.adapt-install-marker.toml`** at the install root.

The marker is what closes the loop with [the `adapt-to-project` skill](../../core/how-to/adapt-to-project.md). On the next agent session, `core`'s `session-start.py` hook reads the marker and nudges the agent into the adapt walk — substituting `<adapt:NAME>` placeholders, walking `*.upstream.<ext>` companions, asking about local conventions.

The mechanism is identical across routes:

| Route | Marker writer |
| --- | --- |
| Reference CLI | The `install` verb writes it in-process and chains to `agentbundle adapt`. |
| Claude plugins | A `SessionStart` hook derived into each pack's `.claude-plugin/plugin.json` runs the canonical writer on first session after install. |
| APM | `.apm/hooks/install-marker.{json,py}`, projected via APM's `HookIntegrator`, runs the same canonical writer. |
| Local clone | Same as Reference CLI — the clone route uses the same `install` verb. |

The writer template at [`packages/agentbundle/templates/install-marker.py`](../../../../packages/agentbundle/templates/install-marker.py) is the single source of truth; every route projects a copy of it. That's the unifying invariant: *one writer, one marker, one read-side*.

## Pick by where you live

**You're on Claude Code, you have a GitHub remote, and you don't mind auto-update.** Use the Claude-plugins route. One line of setup, one line per pack, and `/plugin update` keeps you current.

**You're in another IDE (Cursor, Copilot, Gemini, Codex, Windsurf, OpenCode).** Use APM. The same `<owner>/<catalogue>/<pack>` target works; APM's `HookIntegrator` projects the hooks for whichever IDE you're in. RFC-0010 closes the install→adapt chain on the four hook-capable APM targets — Claude Code (asserted in CI), Cursor, Gemini, Copilot (deferred to manual QA per AC17). The other three targets — Codex, OpenCode, Windsurf — have no hook surface in APM, so the per-pack README documents `agentbundle adapt` as the explicit manual gesture instead.

**You want pinned versions and full state tracking.** Use the reference CLI. `agentbundle install` hashes every projected file into `.agentbundle-state.toml` at install time, so upgrade-time safety is exact from day one. The other routes need a one-shot `agentbundle init-state` after install to reach the same baseline.

**You're network-constrained or want the runtime library editable.** Clone and `pip install -e packages/agentbundle/`. This is the only route where `packages/agentbundle/` and `packs/` come together in your filesystem — useful when you're also developing primitives, or when your network can fetch a git clone but not a pip package.

## The state-tracking nuance

The reference CLI is the only route that hashes projected files at install time. The other three routes lose that baseline unless you opt in:

```bash
agentbundle init-state
```

After `init-state`, all four routes behave identically on upgrade — collisions land as `*.upstream.<ext>` companions, the file-safety contract kicks in, no silent overwrites. See [the file-safety contract](file-safety-contract.md) for the Tier model and per-route mechanics.

## Codex skills (shipped)

[RFC-0009](../../../rfc/0009-codex-native-skills.md) made Codex skills a first-class projection — `direct-directory` writes to `.agents/skills/<name>/SKILL.md` instead of the old managed-block inline shape. [RFC-0011](../../../rfc/0011-pack-allowed-adapters.md) then made Codex user-scope-capable, so the same skills also project to `~/.agents/skills/` when an adopter passes `--scope user` against a pack declaring `codex` in its `allowed-adapters`. The four catalogue user-scope packs (`atlassian`, `figma`, `converters`, `contracts`) all do; see the [Codex user-scope how-to](../how-to/install-user-scope-pack-into-codex.md). A future RFC would add a `codex-plugins` install route (sibling to `claude-plugins`) so Codex's own plugin manager can install these packs without going through the CLI/APM routes — that work isn't opened yet.

## The `--adapter` override

Adopters with multiple IDE homes populated (`~/.claude/` plus `~/.kiro/`, say) can override the resolver's first-match-wins pick by passing `--adapter <name>` to `agentbundle install`. The flag is admitted at **both scopes** (RFC-0012) — at user scope it must name a user-scope-capable adapter from the pack's `allowed-adapters`; at repo scope every shipped adapter is admissible (Copilot included). The pinned refuse-and-explain messages name the field and the contract version, so failed installs are loud, not silent. See [RFC-0011](../../../rfc/0011-pack-allowed-adapters.md) for the six-step (0–5) resolver this flag participates in, plus [RFC-0012](../../../rfc/0012-repo-scope-per-adapter-projection.md) for the scope-branched resolution at steps 0, 1, 4, and 5.

## `--emit-install-routes` — catalogue-publishing opt-in

Pre-RFC-0012, `agentbundle install --pack X --scope repo .` produced dist-tree artifacts (`<repo>/claude-plugins/<pack>/`, `<repo>/apm/<pack>/`) regardless of adapter choice. RFC-0012 flips the default at repo scope to per-IDE projection (the same shape user scope has used since RFC-0004); the dist-tree producer becomes an explicit opt-in via `--emit-install-routes`:

```
agentbundle install --pack core --scope repo --emit-install-routes .
```

Catalogue maintainers scripting the dist-tree shape for publishing pipelines add this one flag to their existing invocations. The flag is bound to `--scope repo` and mutually exclusive with `--adapter` at that scope (the dist-tree producer doesn't pick a single adapter). It carries a `DeprecationWarning` from day one and is targeted for removal in the next minor — see [RFC-0012 § *Alternatives* #6](../../../rfc/0012-repo-scope-per-adapter-projection.md).

## Where to read next

- [The file-safety contract](file-safety-contract.md) — the Tier-1/2/3 guarantee that protects your edits.
- [How to adapt a freshly-installed pack](../../core/how-to/adapt-to-project.md) — what the post-install agent session actually does.
- [How to upgrade an installed pack](../how-to/upgrade-packs.md) — and how the file-safety contract applies on upgrade.
- [Installing `agentbundle` from a clone](../how-to/install-agentbundle-from-clone.md) — the route 4 walkthrough.
