# RFC-0024: Copilot full-parity projection — agents, hooks, and user scope

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-04
- **Date closed:** 2026-06-04
- **Related:**
  - **Supersedes (in part)** [RFC-0012](0012-repo-scope-per-adapter-projection.md) — its "Copilot is admissible at repo scope only; no user-scope analogue exists" scope decision. An erratum on RFC-0012 links forward to this RFC.
  - [RFC-0009](0009-codex-native-skills.md) — precedent: flipped a `dropped` primitive to first-class for an adapter when the upstream tool gained native support.
  - [`docs/specs/dropped-primitives-coverage/spec.md`](../specs/dropped-primitives-coverage/spec.md) — the codex `agent`/`hook-wiring` `dropped`→first-class flip + the contract-driven warning rail this RFC re-uses; also the source of the now-stale claim *"copilot has no native agent / command / hook-wiring surface"*.
  - [RFC-0022](0022-kiro-adapter-split.md) — the most recent contract bump (v0.8→v0.9, kiro split into `kiro-ide`/`kiro-cli`); it is the actual current contract shape this RFC builds on, and its precedent (a contract bump that did **not** bump any pack) is load-bearing for Decision 7.
  - [RFC-0011](0011-pack-allowed-adapters.md) — the `allowed-adapters` mechanism this RFC edits for `research`.
  - [RFC-0005](0005-user-scope-hook-support.md) — `merge-json` / user-scope hook precedent.
  - [ADR-0002](../adr/0002-install-scope-per-pack-default-and-allowance.md) — per-pack scope default + allowance.

## The ask

**Recommendation (BLUF):** Make `copilot` a **full-parity, user-scope-capable adapter**. GitHub Copilot's app + CLI now read native, filesystem-based custom **agents** (`.github/agents/`, `~/.copilot/agents/`) and **hooks** (`.github/hooks/`, `~/.copilot/hooks/`) — surfaces that did not exist when the adapter was last specified. Flip the copilot `agent` and `hook-wiring` projections from `dropped` to first-class, give every projectable copilot primitive a user-scope home, and adapt the two subagent-bearing packs (`research`, `core`) to validate the parity end-to-end. Contract bump **v0.9 → v0.10**.

**Why now (SCQA):**
- *Situation.* RFC-0012 specified `copilot` as a repo-scope-only adapter that projects skills to `.github/instructions/` and **drops** agents, hook-wiring, and commands — correct for what Copilot exposed at the time.
- *Complication.* Copilot has since shipped (a) file-based custom **agents** (`.github/agents/<name>.agent.md`, plus a user home `~/.copilot/agents/`), (b) a documented **hooks** system (`.github/hooks/<name>.json` + `~/.copilot/hooks/<name>.json`), and (c) a stable `$HOME`-based config tree (`~/.copilot/`, `COPILOT_HOME`) shared by the **GitHub Copilot app** (built on the CLI). The contract has meanwhile moved on around Copilot — v0.7 (RFC-0012, Copilot's repo-only scope table) → v0.8 (codex first-class) → v0.9 (RFC-0022, kiro split into `kiro-ide`/`kiro-cli`) — without revisiting Copilot. Our contract's `dropped` modes and "no user-scope analogue" decision are now factually outdated: agents and hooks vanish silently on the largest agent ecosystem, and `research` can't target Copilot at all.
- *Question.* Do we model Copilot as the full-parity, user-scope-capable adapter it has become — the same `dropped`→first-class move we already made for codex — and prove it by adapting the packs that ship subagents?

**Decisions requested** (recommended option in **bold**; decide-by **2026-06-11**, default = the recommendation if no objection):

1. **Project the `agent` primitive** via a new `copilot-agent-md` mode → repo `.github/agents/<name>.agent.md` + user `~/.copilot/agents/<name>.agent.md`. *(was `dropped`)*
2. **Make `copilot` user-scope-capable** — add `[adapter.copilot.scope].user` + `allowed-prefixes.user`; the resolver stops refusing copilot at user scope. **Supersedes RFC-0012's repo-only decision.**
3. **Give `skill` a user-scope home** — add user target `~/.copilot/instructions/<name>.instructions.md`, mirroring the existing repo `.github/instructions/` projection (same `instruction-file` mode).
4. **Project the `hook-wiring` primitive** via a new `copilot-hooks-json` mode → repo `.github/hooks/<name>.json` + user `~/.copilot/hooks/<name>.json`; **move `hook-body`** from the legacy `tools/hooks/` to `.github/hooks/` + `~/.copilot/hooks/`. *(hook-wiring was `dropped`)*
5. **Keep `command` dropped** — the Copilot CLI does not yet load custom slash commands (tracked: copilot-cli#618 / #1113); the warning rail keeps the drop visible. Follow-on flips it when the CLI lands the feature.
6. **Guarantee + document the targets for the Copilot app + CLI** (the `~/.copilot/` + `.github/` layout). The cloud agent and VS Code workspace also read the repo `.github/` files — compatible, but not the guaranteed surface.
7. **Adapt the packs (in scope, validates parity):** add `copilot` to `research`'s `allowed-adapters`; `core` needs no `allowed-adapters` change (already all-shipped); `research` + `core` bump contract v0.8 → v0.10 (not an all-pack bump — rationale in § Decision 7 — pack adaptation).

**Gating condition on acceptance — CLEARED.** Because the entire value of a `dropped`→first-class flip is that the generated artifacts *load on the real tool*, this RFC gated `Accepted` on the live smoke in **§ Acceptance verification**. Run 2 (Copilot CLI + app 1.0.59, 2026-06-04) passed **T1–T8** — every projection target, the tool-alias + read-only mapping, app parity, and the full hook event map are confirmed against the real CLI + app. *Verified by:* eugenelim.

## Problem & goals

When RFC-0012 gave every adapter a `[adapter.<name>.scope]` table, Copilot got a repo-only one with the explicit comment *"no user-scope analogue exists in the Copilot ecosystem."* The `dropped-primitives-coverage` spec, flipping codex's `agent`/`hook-wiring` to first-class when codex shipped native subagents (April 2026), recorded the parallel justification for leaving Copilot alone: *"copilot has no native agent / command / hook-wiring surface."*

Both statements were true then and are false now. The cost of leaving the contract stale:

- **Subagents silently vanish on Copilot.** `core` ships 4 subagents (3 reviewers — `adversarial-reviewer`, `quality-engineer`, `security-reviewer` — plus the `implementer` executor) and `research` ships 2 retrieval subagents. On Copilot, all 6 hit the `dropped` mode — the warning rail fires, but the capability is simply unavailable on the ecosystem with the widest reach.
- **`research` can't target Copilot at all.** Its `allowed-adapters = ["claude-code", "kiro", "codex"]` refuses copilot up front — an exclusion whose stated rationale (Copilot can't represent subagents) no longer holds.
- **The "repo-scope only" limitation is self-imposed and now wrong.** Copilot's app + CLI share a stable `$HOME` config tree (`~/.copilot/{agents,instructions,hooks}/`, `COPILOT_HOME`) — a genuine user-scope home, exactly the shape we already target for claude-code (`~/.claude/`) and codex (`~/.agents/skills/`).

**Goals.**
- Project every Copilot-supported primitive (skill, agent, hook-wiring, hook-body) at **both** repo and user scope, against targets we can guarantee for the Copilot app + CLI.
- Make `copilot` a first-class user-scope-capable adapter in the resolver.
- Prove the parity by adapting the two subagent-bearing packs and exercising every projection path (including the surviving `command` drop).
- Record the governance divergence from RFC-0012 cleanly (supersession + erratum back-link).

**Non-goals.**
- **Projecting `command`/prompt files.** The CLI doesn't load them yet (copilot-cli#618/#1113); shipping to a VS-Code-only surface would contradict the app+CLI guarantee. Deferred to a follow-on, not abandoned.
- **Targeting the VS Code extension's user-profile location.** It is documented inconsistently and partly under `%APPDATA%\Code\User\…`/profile-specific paths (microsoft/vscode#305642, vscode-copilot-release#12853) — not a stable cross-platform projection target. We target the CLI/app `$HOME` layout, which VS Code increasingly shares.
- **Targeting the cloud coding agent's user scope.** It has none (repo `.github/agents/` + org `.github-private` only). Repo-scope projection already serves it; no extra work.
- **Generalising the new modes.** `copilot-agent-md` and `copilot-hooks-json` are Copilot-shaped, like codex's `codex-agent-toml`. A future sibling adapter gets sibling modes, not a generalisation.

## Proposal

### Decision 1 + 3 + 4 — the projection table

Replace the copilot `agent` and `hook-wiring` `dropped` entries and add user targets. Final copilot projection (contract v0.10):

| Primitive | Mode | Repo target | User target (`~/.copilot/…`) | Change |
| --- | --- | --- | --- | --- |
| `skill` | `instruction-file` | `.github/instructions/<n>.instructions.md` | `instructions/<n>.instructions.md` | + user target |
| `agent` | `copilot-agent-md` *(new)* | `.github/agents/<n>.agent.md` | `agents/<n>.agent.md` | **was `dropped`** |
| `hook-wiring` | `copilot-hooks-json` *(new)* | `.github/hooks/<n>.json` | `hooks/<n>.json` | **was `dropped`** |
| `hook-body` | `direct-file` | `.github/hooks/` | `hooks/` | **moved** from `tools/hooks/` |
| `command` | `dropped` | — | — | unchanged (see Decision 5) |

**`copilot-agent-md` frontmatter mapping** (our `.apm/agents/<n>.md` → Copilot `.agent.md`):
- `name`, `description`, and the markdown body → 1:1 (body becomes the agent's instructions).
- `tools` → **pass through**. Copilot accepts the Claude tool names and resolves them to its own tools (observed in app 1.0.59: `Read`→`view`, `Grep`→`grep`, `Glob`→`glob`; no unknown-tool errors), and the read-only restriction on `evidence-retriever`/`source-extractor` (no `edit`/`execute`) is preserved. **Caveat (Run 4):** `WebFetch`/`WebSearch` did **not** surface as app tools — the exact canonical alias targets and web-retrieval coverage are *not* a clean automatic pass-through and must be pinned by an explicit mapping table in the spec. See Open Q4.
- `model` → **drop on projection**. The CLI ignores the field (and errored on array syntax — copilot-cli#2133/#1195); our values (`opus`/`sonnet`) aren't Copilot model ids anyway. Each runtime falls back to its default.
- `target` → **omit** (defaults to both `vscode` + `github-copilot`).

**`copilot-hooks-json` mapping** (our `.apm/hook-wiring/<n>.toml` → Copilot `<n>.json`): each wiring file serialises to a self-contained `{"version":1,"hooks":{<event>:[{"type":"command","bash":…,"powershell":…}]}}` JSON file. Event names map to Copilot's vocabulary (`SessionStart`→`sessionStart`, `PreToolUse`→`preToolUse`, `PostToolUse`→`postToolUse`, `UserPromptSubmit`→`userPromptSubmitted`, `Stop`→`agentStop`, …). **Verified (CLI + app 1.0.59, Run 2):** every mapped event fires (see § Acceptance verification T8). The spec freezes the full map.

Why a *new* mode rather than the existing `merge-json` (which is how codex's `hook-wiring` flip was implemented — a single `.codex/hooks.json` merged in place, per `dropped-primitives-coverage`)? Because Copilot's hooks dir holds **many** independent `<name>.json` files (it reads every `*.json`), not one mergeable file — so `merge-json`'s single-target model can't express it. The serialisation shape (one source file → one output file) is the same as codex's *agent* mode (`codex-agent-toml`); the per-file-vs-merged distinction is the new part. So `copilot-hooks-json` borrows the serialise-one-file shape from `codex-agent-toml` and is deliberately *not* the `merge-json` mode codex used for its own hooks.

### Decision 2 — user-scope capability

Add to the contract:

```toml
[adapter.copilot.scope]
repo = "."
user = "~"
allowed-prefixes.repo = [".github/instructions/", ".github/agents/", ".github/hooks/"]
allowed-prefixes.user = [".copilot/agents/", ".copilot/instructions/", ".copilot/hooks/"]
```

`user_scope_capable_adapters_from_contract()` then includes `copilot`, and the resolver's user-scope-capability subcheck stops refusing it. `research` (`default-scope = "user"`) resolves to copilot at user scope naturally; no `pack.toml` schema change is required.

> The `tools/hooks/` retirement: the legacy hook-body target predates Copilot's native hooks dir. Moving to `.github/hooks/` aligns the scripts with the `<n>.json` files that reference them.

### Decision 7 — pack adaptation (validation)

The two subagent-bearing packs are the validation surface, and they split cleanly by scope:

- **`research`** (`default-scope = "user"`, `allowed-scopes = ["user", "repo"]`) — add `copilot` to `allowed-adapters` (`["claude-code", "kiro", "codex", "copilot"]`). It ships skills + agents, so it validates the **user-scope** skill (`~/.copilot/instructions/`) and agent (`~/.copilot/agents/`) targets.
- **`core`** (`allowed-scopes = ["repo"]` — repo-only by content) — no `allowed-adapters` change (already all-shipped). It ships skills + agents + hook-wiring + hook-body + one `command`, so it validates the full set of **repo-scope** targets (`.github/{instructions,agents,hooks}/`) **and** the surviving `command` drop + warning rail. Being repo-only, it cannot exercise any `~/.copilot/` target.

Honest validation gap: **user-scope hook-wiring / hook-body** (`~/.copilot/hooks/`) is exercised by *no* in-scope pack — `core` (which ships hooks) is repo-only, and `research` (user-default) ships no hooks. The implementing spec covers this with a construction test that renders a synthetic user-scope hook pack rather than relying on a shipped pack; flagged in Open questions.

**Pack-version bump.** The packs are at contract **v0.8** today (RFC-0022's v0.9 bump did *not* bump any pack — packs adopt a contract level only when they need its behavior). So this is **not** an all-pack bump: only `research` and `core` bump `[pack.adapter-contract] version` to `"0.10"` to opt into the new copilot projections, atomic with the contract change. They jump 0.8→0.10 directly (contract levels are forward-cumulative; there is no 0.9-specific pack behavior to land at). Packs that ship no agents/hooks and don't target copilot stay at v0.8 and keep the prior copilot behavior. *(This deliberately departs from `dropped-primitives-coverage`'s all-pack bump; RFC-0022 already established that a contract bump need not bump every pack.)*

### Governance

RFC-0012 is `Accepted`; this RFC reverses one factual decision in it (Copilot repo-only scope). Per the project's frozen-RFC rule, the divergence is recorded both ways: this RFC declares **Supersedes (in part)** in its header, and RFC-0012 gains an **Errata** note linking forward to RFC-0024.

## Options considered

**Axis: how the copilot adapter represents the `agent` primitive now that Copilot has a native agent surface** (exhaustive over projection target: drop / dedicated-surface / reuse-existing-surface), each grounded in prior art. This table decides only the agent-surface axis — the headline reversible choice. The coupled decisions (user-scope capability, the hook mode, keeping `command` dropped) are evaluated in Decisions 2, 4, and 5; the recommended Option B assumes those resolve as recommended.

| Option | What | Trade-off vs. goals | Prior art |
| --- | --- | --- | --- |
| **A. Do nothing** | Keep `agent`/`hook-wiring` `dropped`; copilot stays repo-only | Fails the core goal — 6 subagents stay invisible on Copilot; `research` still excluded. Cost of delay grows as Copilot adoption rises. | status quo |
| **B. First-class native projection** ⭐ | New `copilot-agent-md` + `copilot-hooks-json` modes → `.github/agents/`, `.github/hooks/` + `~/.copilot/` mirrors; copilot becomes user-scope-capable | Most work (two modes + scope table + event map). Delivers full parity; exactly the move already made for codex. | RFC-0009 + `dropped-primitives-coverage` (codex `dropped`→first-class) |
| **C. Reuse the `instruction-file` mode** | Project agents as always-on `.github/instructions/` files | Cheap, no new mode — but collapses an isolated-context **subagent** into an always-on instruction; loses the delegation that defines a subagent. Wrong altitude. | — (no precedent; degrades the primitive) |

**Do-nothing cost of delay:** every release ships a contract asserting Copilot can't hold agents/hooks while Copilot ships both; adopters installing `core`/`research` to Copilot silently lose subagents. The asymmetry with codex (which *is* first-class) is itself a defect.

Recommendation: **B** — it matches the established in-repo pattern and targets Copilot's purpose-built surfaces.

## Risks & what would make this wrong

**Pre-mortem.**
- *The CLI/app rejects our generated `.agent.md` or `<n>.json`.* Mitigation: the spec ships a construction test that round-trips one agent and one hook file and asserts the exact bytes against the documented schema; a manual `copilot` CLI smoke test is listed as an acceptance step before merge.
- *Tool-alias mapping silently widens permissions.* If a Claude tool name has no compatible Copilot alias, dropping it would grant all tools (omitting `tools` = all tools, in Copilot). Mitigation: the mapping is an explicit allow-list, and an unmapped tool name **fails the build** rather than silently widening. Note this is a *stricter* policy than the two existing frontmatter mappings — codex's `codex-agent-frontmatter` silently drops unmapped fields and kiro's mapping warn-drops unmapped tokens. The fail-closed choice is deliberate (permission-widening is a security-relevant default), and the spec must site the allow-list + the fail rule explicitly rather than inherit the existing drop-on-unmapped behavior. All current agents' tools (`Read`/`Grep`/`Glob`/`Bash`/`Edit`/`Write`/`WebFetch`/`WebSearch`) are covered.
- *`.github/agents/` or `.github/hooks/` collides with adopter-authored files.* RFC-0012 already flagged that `.github/` namespaces overlap adopter content more than `.claude/`. Mitigation: Tier-1/2/3 + `.upstream.*` companions already handle this; the new prefixes inherit it.

**Key assumptions (falsifiable).**
- *Copilot app + CLI read `.agent.md` from `.github/agents/` and `~/.copilot/agents/`, and `<n>.json` hooks from `.github/hooks/` and `~/.copilot/hooks/`.* — from current GitHub/VS Code docs (cited below). Wrong if those paths change before we ship.
- *The CLI/app share the `~/.copilot/` layout.* — the app is documented as "built on the Copilot CLI." Wrong if the app diverges its config home.
- *`command`/prompt files are inert (not error-inducing) to the CLI.* — **not relied upon**: we drop `command`, so its CLI behaviour doesn't gate this RFC. (Inference only; untested — see Open questions.)

**Drawbacks.** Two new projection modes + an event-name map to maintain; `.github/hooks`/`.github/agents` widen the adopter-collision surface; the `tools/hooks/` → `.github/hooks/` move is a behaviour change for any existing copilot hook-body consumer (none ship today). The `model` field is dropped, so Copilot uses its default model rather than the agent's declared one — acceptable given cross-surface fragility, but it is a fidelity loss.

## Evidence & prior art

**Spike / de-risk (frontmatter + targets).** Mapping `research/evidence-retriever.md` to a Copilot `.agent.md`: structure (`name`/`description`/body) is 1:1; `tools: Read, Grep, Glob, WebFetch, WebSearch` maps cleanly onto Copilot's case-insensitive aliases with the read-only restriction intact; `model` is dropped. The riskiest assumption — that the mapping is structural, not lossy — held: the only frictions are vocabulary (tools, resolved by the alias table) and `model` (resolved by dropping). A live CLI round-trip is deferred to the implementing spec's acceptance steps (the CLI isn't installed in the authoring environment, so this RFC does not claim it was run).

**Repo precedent.**
- `docs/rfc/0009-codex-native-skills.md` + `docs/specs/dropped-primitives-coverage/spec.md` — the governing precedent: `dropped`→first-class for an adapter when upstream gains support, with a new per-file serialisation mode (`codex-agent-toml`), the contract-driven warning rail, and atomic contract+pack bumps. This RFC is the same move for Copilot.
- `docs/rfc/0012-repo-scope-per-adapter-projection.md` — the copilot repo-only scope decision this RFC supersedes; also its note that `.github/` namespaces collide with adopter content more often.
- `docs/rfc/0011-pack-allowed-adapters.md` — the `allowed-adapters` field edited for `research`.

**External prior art** (each fetched and confirmed to contain the cited claim):
- Custom agent file format — `.github/agents/<name>.agent.md`, frontmatter `description` (required) + `name`/`tools`/`model`/`mcp-servers`/`target` (optional); `tools` aliases (`read`/`edit`/`search`/`web`/`execute`/…) are Claude-name-compatible and case-insensitive: [VS Code custom agents](https://code.visualstudio.com/docs/agent-customization/custom-agents), [GitHub custom-agents-configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration), [GitHub about custom agents (cloud)](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-custom-agents).
- User-scope homes (`~/.copilot/agents/`, `~/.copilot/instructions/`, `COPILOT_HOME`): [Copilot CLI config directory reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference).
- Hooks — repo `.github/hooks/<name>.json` + user `~/.copilot/hooks/<name>.json`, `{"version":1,"hooks":{…}}`, events `sessionStart`/`sessionEnd`/`userPromptSubmitted`/`preToolUse`/`postToolUse`/`errorOccurred`/`agentStop`: [Copilot CLI hooks how-to](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-hooks).
- The Copilot **app** is a desktop application "built on the GitHub Copilot CLI": [github/app](https://github.com/github/app).
- `command`/prompt files unsupported by the CLI; `model` field chat-vs-CLI divergence: [copilot-cli#618](https://github.com/github/copilot-cli/issues/618), [#1113](https://github.com/github/copilot-cli/issues/1113), [#2133](https://github.com/github/copilot-cli/issues/2133), [community #188138](https://github.com/orgs/community/discussions/188138).
- VS Code user-profile agent/instruction location is documented inconsistently (rationale for not targeting it): [microsoft/vscode#305642](https://github.com/microsoft/vscode/issues/305642), [vscode-copilot-release#12853](https://github.com/microsoft/vscode-copilot-release/issues/12853).

## Acceptance verification (pre-Accept gate)

**Hand this section to a verifier with a Copilot subscription.** Every test below maps to a decision in § The ask; **all must pass (or the affected decision is revised) before this RFC moves to `Accepted`.** The point is to prove the *generated artifact shapes load on the real tool* — the one thing the paper de-risk could not establish. Record the result in the table at the end.

### Environment

- GitHub Copilot **CLI** installed and authenticated (a plan that includes custom agents/hooks: Pro/Pro+/Business/Enterprise). Capture `copilot --version` — behaviour is preview and version-sensitive.
- GitHub Copilot **app** (tech preview) installed and signed in — for T6 only.
- A throwaway git repo for repo-scope tests: `mkdir -p probe-repo && cd probe-repo && git init`.
- An **isolated** user-scope home so you don't touch real config: `export COPILOT_HOME="$(mktemp -d)"`. The CLI uses `$COPILOT_HOME` in place of `~/.copilot` when set.

### Sample artifacts (the exact shapes the adapter will generate)

`<.github/agents/ or $COPILOT_HOME/agents/>probe-retriever.agent.md` — read-only agent, `model`/`target` omitted, Claude tool names passed through:

```markdown
---
name: probe-retriever
description: Read-only probe agent for RFC-0024 verification. Reads files and searches; must not edit or run commands.
tools: Read, Grep, Glob, WebFetch, WebSearch
---

You are a read-only probe. When asked, read or search files and report what you find.
You have no permission to edit files or run shell commands; if asked to, refuse.
```

`<.github/hooks/ or $COPILOT_HOME/hooks/>probe-session.json` — fires on session start, writes a marker:

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [
      { "type": "command",
        "bash": "echo PROBE_HOOK_FIRED > \"${TMPDIR:-/tmp}/rfc0024-probe.txt\"",
        "powershell": "Set-Content -Path \"$env:TEMP\\rfc0024-probe.txt\" -Value PROBE_HOOK_FIRED" }
    ]
  }
}
```

`$COPILOT_HOME/instructions/probe.instructions.md` — global instruction marker:

```markdown
---
applyTo: "**"
---
When you start any reply, prefix it with the token RFC0024-INSTR-OK.
```

### Tests

| ID | Decision | Setup | Action | **Pass criterion** | A failure means |
| --- | --- | --- | --- | --- | --- |
| **T1** | 1 (agent, repo) | Place `probe-retriever.agent.md` in `probe-repo/.github/agents/` | Run `copilot` in `probe-repo`; open the agent picker / `/agents` | `probe-retriever` is listed and selectable; **no parse/validation error** on the frontmatter | the `.agent.md` frontmatter shape or repo location is wrong — Decision 1 repo target invalid |
| **T2** | 2 (agent, user) | Place the same file in `$COPILOT_HOME/agents/` only (remove the repo copy) | Run `copilot` from a directory *outside* any repo | agent is discovered globally | `~/.copilot/agents/` is not a real user-scope home — **Decision 2 (the core parity claim) is invalid** |
| **T3** | 1 (tool mapping) | Select `probe-retriever` | Ask it to (a) read a file in the repo, then (b) edit/create a file and (c) run a shell command | Claude tool names accepted (no "unknown tool"); **(a) works**, **(b) and (c) are refused/unavailable** | tool-name pass-through fails (needs an explicit alias table) and/or the read-only restriction is not honoured — a security-relevant miss |
| **T4** | 4 (hook, repo) | Place `probe-session.json` in `probe-repo/.github/hooks/`; clear any old marker | Start a `copilot` session in `probe-repo` | the marker file `rfc0024-probe.txt` is created (hook fired) and JSON parsed without error | hook JSON shape, location, or the `sessionStart` event name is wrong — Decision 4 invalid |
| **T5** | 4 (hook, user) | Place `probe-session.json` in `$COPILOT_HOME/hooks/` only; clear marker | Start a session from outside any repo | marker created (fires globally) | `~/.copilot/hooks/` user home wrong — this is the user-scope-hook validation gap the RFC flagged |
| **T6** | 6 (app parity) | Keep the `$COPILOT_HOME/agents/` + `hooks/` artifacts from T2/T5 | Open the Copilot **app**; check the agent is listed and start a session | the app sees the same `~/.copilot/` agent + fires the hook | the app diverges its config home from the CLI — **narrow the guarantee to CLI-only** and re-open Decision 6 |
| **T7** | 3 (skill, user) | Place `probe.instructions.md` in `$COPILOT_HOME/instructions/` | Start a session from outside any repo; send any prompt | replies are prefixed with `RFC0024-INSTR-OK` (instruction loaded globally) | user-scope instruction home wrong — Decision 3 invalid |
| **T8** | event map | Edit `probe-session.json` to add a second entry under each event in our map (`sessionEnd`, `userPromptSubmitted`, `preToolUse`, `postToolUse`, `agentStop`) writing a per-event marker | Drive one full session (start → prompt → tool use → stop) | every event we intend to map fires; note any event Copilot does **not** recognise | the event-name map (Open Q1) needs correction before the spec freezes it |

> Not gated (do **not** block Accept): `command`/prompt projection is deliberately out of scope (CLI doesn't support custom slash commands — copilot-cli#618/#1113). If the verifier has cycles, the informational check in Open Q2 (drop a `.prompt.md` in `.github/prompts/` and confirm the CLI neither errors nor warns) would de-risk the *follow-on*, but its result does not affect this RFC.

### Result log

Run 2 (authoritative) — Copilot CLI + app **1.0.59**, 2026-06-04:

| ID | Result | CLI version | Notes / observed behaviour |
| --- | --- | --- | --- |
| T1 | ✅ pass | 1.0.59 | Repo-scope agent (`.github/agents/`) discovered; listed as available custom agent, no parse errors |
| T2 | ✅ pass | 1.0.59 | User-scope agent (`$COPILOT_HOME/agents/`) discovered from outside any repo |
| T3 | ✅ pass | 1.0.59 | Reads work; edit + shell both refused; Claude tool names accepted without error |
| T4 | ✅ pass | 1.0.59 | Repo-scope `sessionStart` hook fired; marker file created |
| T5 | ✅ pass | 1.0.59 | User-scope `sessionStart` hook fired globally from outside any repo |
| T6 | ✅ pass | 1.0.59 | **App** session sees `~/.copilot/agents/probe-retriever` and lists it; `sessionStart` hook fired (`T6_APP_HOOK_FIRED` confirmed). App shares the config home with the CLI. |
| T7 | ✅ pass | 1.0.59 | User-scope instructions loaded — `RFC0024-INSTR-OK` prefix confirmed from outside any repo |
| T8 | ✅ pass | 1.0.59 | **All** events fire: `sessionStart`, `sessionEnd`, `userPromptSubmitted`, `preToolUse`, `postToolUse`, `agentStop`. Open Q1 fully resolved. |

> Run 1 (same CLI 1.0.59) reported T6 `n/a` (app not yet installed) and T8 `partial` (only `sessionStart` firing); the T8 partial was a **test-harness bug**, not a tool limitation — Run 2 with a corrected harness fires every mapped event. Run 2 supersedes Run 1.

Run 3 (independent corroboration) — Copilot **CLI** 1.0.59, 2026-06-04, verifier joey.musselman:

| ID | Result | Notes |
| --- | --- | --- |
| T1 | ✅ pass | Repo-scope agent loaded via `--agent probe-retriever`; read-only mode active, no parse errors |
| T2 | ✅ pass | User-scope agent discovered from `/tmp` (outside any repo) |
| T3 | ✅ pass | Read worked; file creation + shell both refused; Claude tool names accepted |
| T4 | ✅ pass | Repo-scope `sessionStart` hook fired; `rfc0024-probe.txt` = `PROBE_HOOK_FIRED` |
| T5 | ✅ pass | User-scope `sessionStart` hook fired from outside any repo |
| T6 | n/a | No app in this CLI-only environment (T6 already passed in Run 2) |
| T7 | ✅ pass | `RFC0024-INSTR-OK` prefix on every reply |
| T8 | ✅ pass | All 6 events fired (`preToolUse`/`postToolUse` ×2) |

> Run 3 is a second verifier confirming the CLI-side gates (T1–T5, T7–T8); T6 was not re-tested (no app available) and stands on Run 2's pass.

Run 4 (app-only corroboration) — Copilot **app** 1.0.59, 2026-06-04, verifier joey.musselman:

| ID | Result | Notes |
| --- | --- | --- |
| T1 | ✅ pass | Repo-scope agent discovered; listed among available custom agents, no parse errors |
| T2 | ✅ pass | User-scope agent discovered from an app session in a different worktree |
| T3 | ✅ pass (with gap) | Read worked; edit + shell refused (read-only preserved). Claude names mapped (`Read`→`view`, `Grep`→`grep`, `Glob`→`glob`), no unknown-tool errors — **but `WebFetch`/`WebSearch` did not surface in the agent toolset**. See Open Q4. |
| T4 | ✅ pass | `sessionStart` hook fired; `rfc0024-probe.txt` = `PROBE_HOOK_FIRED` |
| T5 | ✅ pass | User-scope `sessionStart` hook fired; `rfc0024-probe-user.txt` = `PROBE_HOOK_FIRED_USER_SCOPE` |
| T6 | ✅ pass | App-only run — app shares `~/.copilot/` with the CLI; agents, hooks, instructions all discovered (independently re-confirms Run 2's T6) |
| T7 | ✅ pass | `RFC0024-INSTR-OK` present in the system prompt via `~/.copilot/instructions/` |
| T8 | ✅ pass | All 6 events fired |

> Run 4 deployed fixtures to `~/.copilot/{agents,hooks,instructions}/` and verified via a fresh **app** session (no CLI invocation). Hook markers wrote to `$TMPDIR` (macOS per-user temp), confirming `${TMPDIR:-/tmp}` resolves on both. **New finding (T3):** `WebFetch`/`WebSearch` declared in agent frontmatter did not map to available app tools; `Read`/`Grep`/`Glob` did. The read-only restriction held (no `edit`/`execute`), so T3 passes — but the web-tool coverage gap is now tracked in Open Q4, because `research`'s retrieval subagents depend on web tools.

**Decision rule.** T1–T7 must pass for `Accepted`; T8 informs Open Q1. **Status after Run 2: T1–T8 all pass.** Every gate is met — user-scope agents/hooks/instructions, tool-alias mapping + read-only preservation, app parity (Decision 6 guarantee holds intact), and the full hook event map are all confirmed on the real CLI + app. The pre-Accept gate is cleared.

## Open questions

1. **Exact hook event-name map.** **Resolved (Run 2, CLI + app 1.0.59):** all six mapped events fire (`sessionStart`/`sessionEnd`/`userPromptSubmitted`/`preToolUse`/`postToolUse`/`agentStop`). The spec freezes the full map; no refuse-and-warn is needed. *(Run 1 saw only `sessionStart` fire — a test-harness bug, corrected in Run 2.)*
2. **`command`/prompt graceful-no-op, for the eventual follow-on.** Whether stray `.prompt.md` files are inert to the CLI is inferred, not tested. *Default:* don't rely on it — `command` stays dropped until the CLI supports it and we can test. *Owner:* eugenelim. *Decide-by:* the follow-on RFC (gated on copilot-cli#618/#1113).
3. **`tools/hooks/` retirement vs. back-compat.** No shipped pack writes copilot hook-body today, so the move is safe now. *Default:* move outright; no alias kept. *Owner:* eugenelim. *Decide-by:* spec time.
4. **Tool-alias mapping coverage — esp. `WebFetch`/`WebSearch`.** Run 4 found Claude `Read`/`Grep`/`Glob` resolve in the app (as `view`/`grep`/`glob`) but `WebFetch`/`WebSearch` did **not** surface as tools. `research`'s `evidence-retriever`/`source-extractor` depend on web retrieval, so on Copilot they would be degraded (read/search only). *Default:* the spec ships an **explicit** Claude→Copilot tool-alias table (not automatic pass-through), maps `WebFetch`/`WebSearch` to Copilot's web/fetch tool **if one is exposed to custom agents**, and — if none is — documents the degradation in the `research` pack's Copilot projection (retrieval agents lose live web access there) rather than silently dropping it. *Owner:* eugenelim. *Decide-by:* spec time.

## Follow-on artifacts

Filled in on acceptance:
- ✅ [ADR-0013](../adr/0013-copilot-full-parity-user-scope-adapter.md) — records the Copilot full-parity / user-scope-capable decision and the `tools/hooks/`→`.github/hooks/` retirement (Accepted 2026-06-04).
- Spec — `docs/specs/copilot-full-parity/` (contract v0.10 bump; `copilot-agent-md` + `copilot-hooks-json` modes; scope table; tool-alias + event-name maps; `research`/`core` two-pack v0.8→v0.10 bump — *not* all-pack, per § Decision 7; warning-rail regression for the surviving `command` drop; synthetic user-scope hook pack for the validation gap; CLI smoke-test acceptance step).
- Erratum on `docs/rfc/0012-repo-scope-per-adapter-projection.md` linking forward to this RFC.
- Follow-on RFC stub — `command`/prompt projection, gated on copilot-cli#618/#1113.

## Errata

> Append-only corrections to this Accepted RFC. The body above is preserved as
> the historical record; these entries record where subsequent facts diverged
> from decisions or open questions frozen at acceptance. Implemented by
> [`docs/specs/copilot-skills-and-web/`](../specs/copilot-skills-and-web/spec.md)
> (contract v0.11 → v0.12, atop RFC-0026 cursor's v0.11). Vehicle: Approver-signed erratum (not a follow-on
> RFC) — both corrections are *flip-on-upstream-support* with RFC-0009
> precedent, recorded append-only and shipped atomically with the contract bump
> so the reversal is revertible. The spec-mode adversarial reviewer judged the
> skill-surface flip decision-worthy but the erratum the correct vehicle.

### E1 — Open Q4 closed: Copilot custom agents *do* get the `web` tool (CLI + app) — 2026-06-11

Open Q4 recorded that `WebFetch`/`WebSearch` "did not surface as app tools"
(Run 4, 1.0.59) and defaulted to documenting a `research`-pack web degradation.
**This is now closed: web is supported.** The official custom-agents reference
([custom-agents-configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration),
fetched 2026-06-11) documents a `web` tool with aliases **`WebSearch`,
`WebFetch`**; the *only* caveat is `web` is "Currently not applicable for cloud
agent." The Run-4 probe was confounded (empty `COPILOT_HOME` / no `allowed_urls`
/ org policy). On this repo's target surface — the Copilot **CLI + app** —
custom agents resolve `WebFetch`/`WebSearch` to `web`; `research`'s retrieval
subagents are **not** degraded there. The lone true caveat is narrow: the
Copilot **cloud agent** (served only via repo `.github/`) lacks `web`. No code
change results — the existing `copilot-agent-md` pass-through was already
correct; only the false "no web tool / research degradation" wording is removed.

*Signed-off: eugenelim (Approver), 2026-06-11.*

### E2 — Skill-surface flip: `instruction-file` → first-class Agent Skills (`SKILL.md`) — 2026-06-11

Decision 3 + the projection table gave the `skill` primitive the
`instruction-file` mode (`.github/instructions/<n>.instructions.md` repo,
`~/.copilot/instructions/` user) — correct when Copilot had no first-class skill
surface. **Copilot has since shipped Agent Skills, explicitly distinct from
custom instructions** ([add-skills how-to](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills),
fetched 2026-06-11): repo `.github/skills/<name>/SKILL.md`, user
`~/.copilot/skills/<name>/SKILL.md`, filename must be `SKILL.md` in a per-skill
subdir, required `name` (lowercase-hyphen) + `description`, optional `license`;
Copilot also accepts `.claude/skills`/`.agents/skills`. The adapter therefore
flips copilot `skill` to the existing `direct-directory` `SKILL.md` shape (the
passthrough four other adapters already use; our sources are canonical Claude
`SKILL.md`), drops the orphaned `copilot-instruction` frontmatter-default and
the `.github/instructions/` / `.copilot/instructions/` scope prefixes, and adds
`.github/skills/` / `.copilot/skills/`. This reverses Decision 3's mode (and the
Options-table rejection of `instruction-file`-for-subagents reasoning as it
applied to skills); the `agent`/`hook-wiring`/`hook-body`/`command` decisions
are unchanged.

*Signed-off: eugenelim (Approver), 2026-06-11.*
