# agent-ready-repo

A catalogue of agentbundle primitives — skills, reviewer subagents, hooks, governance scaffolding — installed à la carte into any repo. Each pack lands a coherent slice: a workflow you can run, a reviewer that pulls its weight, or the document shape that makes downstream agents work well. 

The `core` pack carries the spec-driven loop and the reviewer lenses; the rest add governance ceremony, user-docs structure, monorepo scaffolding, contract authoring, and file conversion. 

See [`docs/CHARTER.md`](docs/CHARTER.md) for the mission, scope, and four principles, and [RFC-0001](docs/rfc/0001-bundle-distribution-by-adapter-spec.md) for the catalogue model.

## Install

Three routes, depending on the agent harness you use. They install the same packs from this catalogue.

**Claude Code** — marketplace + plugins:

```
/plugin marketplace add eugenelim/agent-ready-repo
/plugin install core@agent-ready-repo
```

**Any IDE via APM:**

```bash
apm install eugenelim/agent-ready-repo/core
```

**Constrained networks** — reference CLI ([RFC-0003](docs/rfc/0003-spec-and-cli.md)):

```bash
agentbundle install --pack core git+https://github.com/eugenelim/agent-ready-repo
```

Swap `core` for any pack from the list below. Most adopters install `core` plus the add-ons that fit their repo, then run the `adapt-to-project` skill (shipped in `core`) to customize the freshly-installed primitives to local conventions.

### Where primitives land

Each install route projects pack sources through a per-IDE adapter into the shape your harness expects. `agentbundle list-targets` reports four shipped adapters (`claude_code`, `codex`, `copilot`, `kiro`); three of them shown below — Copilot omitted for brevity, see [`docs/contracts/`](docs/contracts/) for its mapping.

| Adapter | Skills | Subagents | Hooks | Governance docs |
| --- | --- | --- | --- | --- |
| **Claude Code** | `.claude/skills/<name>/SKILL.md` | `.claude/agents/<name>.md` | bodies in `tools/hooks/`; wiring merged into `.claude/settings.local.json` | top-level `AGENTS.md`, `docs/CHARTER.md`, `docs/CONVENTIONS.md` |
| **Codex** | inline managed block in root `AGENTS.md` (`<!-- agent-skills:start -->` … `<!-- agent-skills:end -->`); full bodies stay in `.apm/skills/` | dropped (Codex has no subagent concept) | bodies in `tools/hooks/`; wiring dropped | top-level as above |
| **Kiro** | `.kiro/skills/<name>/SKILL.md` | `.kiro/agents/<name>.md` (frontmatter remapped) | bodies in `tools/hooks/`; wiring degraded to a build-time info log | `.kiro/steering/*.md` (with `inclusion: always`) plus top-level governance |

The mapping is defined in [`docs/contracts/`](docs/contracts/); the contract is the authoritative source when an adapter and this table disagree.

## Packs

| Pack | Scope | What it ships |
| --- | --- | --- |
| [`core`](packs/core/) | **repo only** | Spec-driven workflow, reviewer subagents, pre-pr + session-start hooks, governance seeds. The foundation; everything else assumes it. |
| [`governance-extras`](packs/governance-extras/) | repo only | RFC and ADR ceremony — `new-rfc`, `new-adr`, `update-conventions` skills plus `docs/rfc/` and `docs/adr/` shapes. |
| [`user-guide-diataxis`](packs/user-guide-diataxis/) | repo only | Diátaxis-shaped user-docs skeleton — `docs/guides/{tutorials,how-to,reference,explanation}` plus the `new-guide` skill. |
| [`monorepo-extras`](packs/monorepo-extras/) | repo only | Monorepo scaffolding — `new-package` skill and a `packages/_example/` template. |
| [`contracts`](packs/contracts/) | user (default) or repo | Contract-authoring skills — `api-contract` for OpenAPI 3.1. Portable across projects. |
| [`converters`](packs/converters/) | user (default) or repo | File-format converters — `file-to-markdown` (PDF/DOCX/PPTX/XLSX + images), `markdown-to-html`, `msg-to-markdown`. |

**Scope** is where the pack lands. *Repo-only* packs install into the current repo's `.claude/`, `docs/`, and root files — they ship hooks and seeds that only make sense per-project. *User-scope* packs install into `~/.claude/` and follow you across every repo on the machine; the install routes default to user scope for these but `--scope repo` works too.

## After install — adapt to your project

Once a pack lands, run the `adapt-to-project` skill (shipped in `core`) to customize the seed primitives to your actual project. The install verb writes an `.adapt-install-marker.toml` at the install's scope root; the next session-start hook surfaces a nudge to run the skill. 

**Status:** shipped — see [`docs/specs/adapt-to-project/spec.md`](docs/specs/adapt-to-project/spec.md). 
The deterministic substitution half lives in `agentbundle adapt`; the skill is the LLM-judgment layer on top for non-mechanical decisions.

**Greenfield repo.** A fresh repo has nothing to merge against, so adaptation is mostly substitution into the seed `AGENTS.md`, `docs/CHARTER.md`, and `docs/CONVENTIONS.md`. Have these answers ready before you start:

- Project name and one-line description of what it does and for whom
- `install`, `test`, `lint`, `build`, and `run` commands for your stack
- A sentence or two on what's in and out of scope (for `docs/CHARTER.md`)

The skill walks each `<adapt:NAME>` marker one at a time; you approve, edit, or skip. Skipped markers come back next session.

**Brownfield repo.** Your repo already has conventions; if you installed via the `agentbundle` CLI, the install dropped `*.upstream.<ext>` companions wherever it would have collided with your existing files (an `AGENTS.md` you already wrote, a `docs/CONVENTIONS.md` that predates the pack). 

APM and Claude-plugin routes don't produce companions at install time (APM compiles straight to the working tree; Claude plugins install into a cache) — for those routes, companions appear on the *next* `agentbundle upgrade` once `agentbundle init-state` has recorded a baseline. The skill walks four classes of change with per-item approval:

1. **Substitution** — same `<adapt:NAME>` markers as greenfield, but the values usually already exist in your `README`, `package.json`, or `Makefile`; the skill proposes pulling them in.
2. **Companion merges** — for each `*.upstream.<ext>` the install left on disk, the skill proposes a merged result against your existing file. Per-file accept, edit, skip, or decline.
3. **Discovery + restructuring** — non-canonical primitives elsewhere in your tree (a `DESIGN.md` at root, a stray `docs/architecture.md`) get matched against pack-canonical paths (`docs/CHARTER.md`, `docs/architecture/overview.md`). Per-finding accept, edit, or decline.
4. **Within-layout consolidation** — overlapping shapes (your `docs/howto/` vs the diátaxis pack's `docs/guides/how-to/`) get folded together per your call.

Re-invoke any time. The skill dedupes against prior declines, surfaces only what's unresolved, and exits clean when nothing remains.

## Existing files are never silently overwritten

The catalogue's install and adapt steps will not silently overwrite a file you've edited. Concretely:

- **First-install collisions land as `*.upstream.<ext>` companions** *(CLI install route)*. If `agentbundle install` would write `AGENTS.md` and you already have one, it drops `AGENTS.upstream.md` next to yours and leaves your `AGENTS.md` alone. The `adapt-to-project` skill picks up these companions and proposes a merge per file; you accept, edit, skip, or decline.
- **Upgrade collisions land as companions, not overwrites** *(after CLI install or `agentbundle init-state`)*. The CLI records a SHA-256 of every projected file in `.agentbundle-state.toml` at install time. On the next `agentbundle upgrade --pack <name> --to <version> <catalogue>`, any file whose content diverged since install (Tier-2) gets a `*.upstream.<ext>` companion dropped next to it; your edited file is left alone and the CLI continues without prompting. The merge UI lives in the `adapt-to-project` skill, which you re-invoke after the upgrade to walk the new companions one at a time (accept, edit, skip, or decline per file). RFC-0001 specifies a richer in-CLI prompt with a `<path>.pre-update.bak` overwrite path; v0.1 ships the companion-drop only.
- **Files outside the pack's projected paths are never touched.** Your source code, your own `docs/<thing>.md` that no pack ships, your `.gitignore`, your CI config — all Tier-3, untouched on install and on upgrade.

**Scope of the guarantee.** The contract binds the `agentbundle` CLI's install path and the `adapt-to-project` skill. APM (`apm install`) and Claude Code plugins (`/plugin install`) are governed by *those tools'* native file-handling semantics; the catalogue cannot intercept them. The two routes differ in detail: APM compiles to the working tree and applies its own conflict rules, while Claude plugins install into a cache rather than the working tree (so install-time file collisions don't arise on that route at all — they re-emerge only if you copy the cached files in by hand). Adopters who want catalogue-level safety on subsequent upgrades run `agentbundle init-state` after the APM or Claude-plugin install to hash the just-installed files; from that point forward the safety contract applies. Full text: [RFC-0001 § Adopter file safety contract](docs/rfc/0001-bundle-distribution-by-adapter-spec.md#adopter-file-safety-contract).

## Upgrades

Three granularities, in order of increasing specificity:

- **Whole pack (default).** Pick the verb that matches how you installed:
  - `apm update <pack>` (APM) and `/plugin update <pack>@agent-ready-repo` (Claude Code) — native upgrade verbs of the host tool; conflict handling follows that tool's rules, not the catalogue's.
  - `agentbundle upgrade --pack <name> --to <version> <catalogue>` — the catalogue's own verb, and the only route that drops `*.upstream.<ext>` companions on Tier-2 collisions for `adapt-to-project` to merge later. (The `agentbundle install --pack` verb refuses an in-place re-install — `upgrade` is the verb for changing an installed pack's version.)
- **One primitive at a time.** Add a primitive filter to the same `upgrade` verb: `agentbundle upgrade --pack <name> --to <version> --skill <skill> <catalogue>` (or `--agent`, `--hook`, `--seed <path>`, `--command`). Only the named primitive moves; the rest of the pack stays at the previously-installed version. The CLI records the resulting mixed-version state in `.agentbundle-state.toml`; the next whole-pack upgrade flags it.
- **One file at a time.** Re-run the `adapt-to-project` skill. It walks any `*.upstream.<ext>` companions still on disk one by one, with per-file accept / edit / skip / decline.

`<catalogue>` is the same URI you installed from — e.g. `git+https://github.com/eugenelim/agent-ready-repo` or a local checkout path.

**Downgrades** aren't supported in v0.1 — `agentbundle uninstall <pack>` and reinstall at the prior version. Tier-2 and Tier-3 files survive the uninstall by design.

## The core pack

Core is the load-bearing pack. Everything else extends what it ships. If you install nothing else, install this. **Core installs into the repo only** — its hooks, governance seeds, and `AGENTS.md` template are per-project by design and the pack refuses a user-scope install.

- **Skills**
  - `work-loop` — plan → execute → gates → review, with explicit stop conditions and a capture-learnings step.
  - `new-spec` — opens a feature directory with paired spec and plan; assumptions surface up front.
  - `bug-fix` — reproduce, root-cause, write a failing test, ship the minimum diff.
  - `adapt-to-project` — walks the adopter through customizing freshly-installed primitives to local conventions.
  - `add-credentialed-skill` — scaffolds a new skill that calls an authenticated external API on the user's behalf.
- **Subagents** — sharp lenses for diff review; `work-loop` picks which to run based on what the diff actually touches.
  - `adversarial-reviewer` — spec drift, scope creep, missing edge cases. The default reviewer.
  - `security-reviewer` — OWASP Top 10 (web + LLM Apps) and STRIDE; complements SAST/SCA scanners, doesn't replace them.
  - `quality-engineer` — testability, observability, reliability, maintainability.
  - `implementer` — single-task executor used by `work-loop`'s supervisor mode.
- **Hooks**
  - `session-start` — runs at session start; surfaces context the agent needs before its first action.
  - `pre-pr` — runs before a PR is opened; the last gate before review.
- **Command**
  - `conventions-check` — runs the agent-artifact and conventions linters in one shot.
- **Governance seeds** — `AGENTS.md` (canonical agent context, symlinked from `CLAUDE.md`), `CHARTER`, `CONVENTIONS`, and the `docs/specs/` + `docs/architecture/` shapes with README seeds.

## License

Licensed under either of

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)
- MIT License ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)

at your option. Contributions are dual-licensed under the same terms unless you state otherwise.
