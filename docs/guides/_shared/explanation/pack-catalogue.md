# The pack catalogue

This repo isn't a starter template — it's a catalogue. Eight packs you install à la carte — four land inside a repo you own (per-project infrastructure: agent conventions, governance scaffolding, monorepo primitives), four land at user scope (portable workflows that follow you across every repo on the machine). The distinction matters because it changes what you're agreeing to when you adopt: you take the slices that fit, your edits are first-class, and the catalogue keeps a file-safety contract that says "your edits are never silently overwritten."

## What a pack is

A pack is a coherent slice of agent infrastructure — usually one of:

- A **workflow you can run** (`work-loop`, `new-spec`, `bug-fix`).
- A **reviewer that pulls its weight** (`adversarial-reviewer`, `security-reviewer`, `quality-engineer`).
- The **document shape** that makes downstream agents work well (the Diátaxis quadrants, RFC/ADR templates, the `docs/CHARTER.md` scaffold).
- A **credentialed primitive** plus the workflows that compose against it (`jira` + `flow-metrics` + `jira-defect-flow`).

A pack ships skills, agents, hooks, commands, and seed documents. It does **not** import code from other packs — composition happens by convention, not import. Two packs landing in the same scope share nothing but the directory they project into (a repo working tree for repo-scope packs; a user-scope root like `~/.claude/` for user-scope packs).

## Why `core` is the load-bearing pack

`core` carries the discipline. The plan → execute → verify → review loop, the reviewer agents that read diffs adversarially in a fresh session, the session-start hook that nudges you into `adapt-to-project` on first session — none of that lives in the other packs.

Concretely, every repo-scope pack assumes `core` is also installed in two ways (user-scope packs don't depend on `core` — see the composition rule below):

1. **The session-start hook** in `core` is the single read-side of the install→adapt chain. Every install route drops the same `.adapt-install-marker.toml`; `core`'s hook surfaces it. Without `core`, the marker lands and nothing reads it.
2. **The reviewer agents and the work-loop skill** in `core` are what the other packs' skills compose against when they say "run the work-loop." If you install `governance-extras` without `core`, the `new-rfc` skill still works but the loop discipline it points at isn't there.

The fix is mechanical: install `core` first, then add whichever packs fit. The README's pack table is the menu. For a deeper look at *what* `core` ships and *why* the loop+reviewer+spec combination is more productive than vibe-coding or competing spec-driven workflows, see [The core pack as a system](../../core/explanation/core-pack.md).

## Two scopes: repo and user

The catalogue's eight packs split by where they land on disk.

**Repo-scope (four packs):** `core`, `governance-extras`, `user-guide-diataxis`, `monorepo-extras`. These install into the root of a repo you own and only make sense per-project — they ship hooks, governance seeds (`AGENTS.md`, `docs/CHARTER.md`, `docs/CONVENTIONS.md`), the `docs/specs/` skeleton, and other content that's specific to the repo they land in. Their `[pack.install]` table declares `allowed-scopes = ["repo"]`; the bundler refuses any attempt to install them at user scope.

**User-scope (four packs):** `contracts`, `converters`, `atlassian`, `figma`. These land under the user-scope root of whichever adapter you're using — `~/.claude/` for Claude Code, `~/.kiro/` for Kiro, `~/.agents/skills/` for Codex — and follow you across every repo on the machine. They declare `default-scope = "user"` with `allowed-scopes = ["user", "repo"]` and (since RFC-0011 / contract v0.6) `allowed-adapters = ["claude-code", "kiro", "codex"]`. Pass `--scope repo` if you want a copy local to one project (pinning a specific `jira` version per repo, for instance); pass `--adapter <name>` to override the auto-detected IDE when more than one CLI home is populated on your machine. See the [`Where primitives land`](../../../../README.md#where-primitives-land) table in the README for per-adapter target paths, and the [Kiro](../how-to/install-user-scope-pack-into-kiro.md) and [Codex](../how-to/install-user-scope-pack-into-codex.md) how-to guides for the adopter walkthroughs.

The two scopes never share files. A user-scope pack installed with `--scope repo` projects into that repo's working tree the way a repo-scope pack would; otherwise it stays in your user directory.

## Profiles: a curated set in one command

Some pack combinations are blessed — a solution architect's toolkit is `architect` + `research` + `contracts`; a repo's full governance setup is `core` + `governance-extras` + `user-guide-diataxis` + `monorepo-extras`. (Each name is a pack from [the README's catalogue table](../../../../README.md#the-catalogue), the authoritative menu.) A **profile** promotes that curated knowledge from prose into one executable unit: `agentbundle install --profile <name> <catalogue>` installs the whole set in one command, and `agentbundle list-profiles <catalogue>` shows what's on offer.

A profile is a thin pointer list, not a pack — a hand-authored `profiles/<name>.toml` at the catalogue root that names packs in dependency-first order. It adds no primitives, no new dependency edges, and no state entity: the packs install exactly as they would one at a time, just sequenced and gated as a batch. Two properties make it safe rather than a mega-bundle:

- **Single-scope.** A profile is repo-only or user-only — it never mixes scopes, so there's no half-applied cross-scope install to reason about. The scope is declared in the manifest; you don't pass `--scope`.
- **All-or-nothing pre-flight.** Every pack's preconditions run before the first write, on one pinned adapter, so the batch is no less safe than installing each pack by hand.

Profiles cover *installing* a set; there is no `upgrade --profile` or `uninstall --profile` — you act on the individual packs afterward. See [how to install a profile](../how-to/install-a-profile.md) for the walkthrough.

## The composition rule

Packs compose by convention, not by import — no pack ever imports code from another pack. The rule is one-directional: repo-scope packs depend on `core`; user-scope packs don't.

The one **runtime** dependency that catches adopters off-guard: every credentialed primitive in `atlassian` and `figma` imports `from agentbundle.credentials import load_credentials`, so installing those packs via Claude plugins or APM still requires the `agentbundle` Python module to be importable in the agent's shell-out subprocess. See [the `install-agentbundle-from-clone` guide](../how-to/install-agentbundle-from-clone.md) for the pip step that closes the loop, and the [README's install section](../../../../README.md#install) for the same caveat in the front-door framing.

## Why a catalogue, not a template

The obvious alternative would be: ship the bundle as a template, ask adopters to fork or clone, then merge updates by hand. We rejected that because the catalogue model gives three things a template can't:

1. **Granular adoption.** Take `core` + `atlassian`; skip the rest. A template forces you to inherit the whole thing.
2. **Upgrade-safe edits.** The file-safety contract distinguishes Tier-1 (catalogue-owned) from Tier-2 (you edited it) and writes `*.upstream.<ext>` companions on collision. A template fork loses that — every upgrade is a manual merge against a moving base.
3. **Multiple install routes.** The same pack content reaches you via `agentbundle install`, `apm install`, `/plugin install`, or the four-line clone-and-pip dance — pick the one your environment allows. A template has one shape.

The tradeoff is that a catalogue needs the machinery to support those three properties. That machinery is the `agentbundle` CLI plus the adapter contract at `docs/contracts/adapter.toml`, both versioned independently of the packs they project.

## Where to read next

- [Install routes](install-routes.md) — the four ways to install, and how they share work via the install→adapt chain.
- [The file-safety contract](file-safety-contract.md) — the Tier-1/2/3 model that protects your edits.
- [Credentialed skills](../../credential-brokers/explanation/credentialed-skills.md) — how packs like `atlassian` and `figma` get a token without ever putting it on argv.
- [RFC-0001](../../../rfc/0001-bundle-distribution-by-adapter-spec.md) — the authoritative source for the catalogue model.
