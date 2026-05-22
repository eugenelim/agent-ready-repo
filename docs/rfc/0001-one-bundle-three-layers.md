# RFC-0001: One bundle, three layers — portable agent-template distribution

- **Status:** Accepted
- **Author:** eugenelim
- **Date opened:** 2026-05-21
- **Date closed:** 2026-05-21
- **Related:** drift-reconciliation commit `a2bc58d` (motivating bug); the
  Agent Skills specification at `agentskills.io/specification`.

## Contents

- [Summary](#summary)
- [Motivation](#motivation)
- [Proposal](#proposal)
  - [Repo layout](#repo-layout)
  - [The three layers](#the-three-layers)
  - [Per-IDE projection](#per-ide-projection)
  - [Skills go directory-scoped](#skills-go-directory-scoped)
  - [Install routes](#install-routes)
  - [The install mechanic](#the-install-mechanic)
  - [`/adopt-repo` — the Claude Code overlay](#adopt-repo--the-claude-code-overlay)
  - [Placeholder format](#placeholder-format)
  - [Python-everywhere, no shell scripts in the install path](#python-everywhere-no-shell-scripts-in-the-install-path)
  - [Manifest format](#manifest-format)
  - [Catalog shape: core and extensions](#catalog-shape-core-and-extensions)
  - [Downstream-defined bundles](#downstream-defined-bundles)
  - [Upgrade scalability](#upgrade-scalability)
  - [From design to spec — the trajectory](#from-design-to-spec--the-trajectory)
  - [Success criteria](#success-criteria)
- [Alternatives considered](#alternatives-considered)
- [Drawbacks](#drawbacks)
- [Unresolved questions](#unresolved-questions)
- [Follow-on artifacts](#follow-on-artifacts)

## Summary

Restructure this template's distribution into **one bundle with three
internal layers** — universal context (Layer 0), spec-conformant skills
(Layer 1), and Claude-and-Kiro extensions (Layer 2) — installed via one
of three coordinated routes (**Copier** for Python-equipped adopters,
`bootstrap.py` for stdlib-only environments, **`/adopt-repo`** for
adopters running Claude Code) sharing a single TOML manifest and
placeholder format. The bundle's source-of-truth lives in canonical
directories; per-IDE projections are computed at install time for the
four named targets (Claude Code, Kiro, GitHub Copilot, OpenAI Codex).
Upgrades scale through semver tags on the template and a documented
scheduled-action pattern that opens PRs in adopter repos without
maintainer coordination. The recent spec-section drift bug is the
proximal trigger; the deeper aim is to close the *template-owned
section-name* coupling class structurally and align the bundle with the
open Agent Skills spec.

## Motivation

Four observations from the last month:

**1. The drift bug we just fixed is one instance of a structural class.**
Commit `a82adf0` restructured `docs/_templates/spec.md` from `Behavior /
Constraints / Non-goals / Contract tests` to `Objective / Boundaries /
Testing Strategy / Acceptance Criteria`. The fix commit `a2bc58d` touched
9 files; roughly half were skill bodies referencing the renamed section
names (closed structurally by this RFC's skill-directory-scoping) and
roughly half were Layer 0 files — `docs/CONVENTIONS.md`, `docs/APPROACH.md`,
`docs/specs/README.md`, `tools/install-skill.py` — where one Layer 0 doc
references another by section name. This RFC closes the **skill-body →
Layer 0 section-name drift** subclass. **Layer 0 → Layer 0 drift** (one
governance doc renames a heading that another references) remains an
unaddressed class; the linter checks for it but the restructure doesn't
remove its possibility. Sibling-skill-availability drift (a dispatched
subagent isn't installed; the skill silently no-ops) is mitigated by the
graceful-degrade discipline but not eliminated — invisible drift is still
drift.

**2. The Agent Skills spec rules out the structure we have.** Skills are
directory-scoped: `references/`, `scripts/`, `assets/` live inside the
skill; file references stay one level deep from `SKILL.md`. Our skill
bodies reach into `docs/_templates/`, `docs/CONVENTIONS.md#anchor`,
`tools/`, and four sibling agents via `../../../` relative paths. The
existing `lint-skill-deps.sh` partially mitigates this for adopter-owned
files (`AGENTS.md`, `CONVENTIONS.md`) but does not cover template-owned
files, which is the leak the drift bug exploited.

**3. There is no clean install story under realistic corporate
constraints.** The concrete environment driving this RFC: API-gateway
auth in front of internal GitLab blocks raw HTTP API calls against the
git host; `git clone` and `git pull` work through authenticated git
access; `pip install` works only through Artifactory using a developer's
personal access token (one-time per-developer setup). This rules out
install paths that rely on raw-file fetches or `npx`/curl one-liners.
Adopters today fork the whole repo and edit by hand; there is no
upstream-update channel beyond manual three-way merges.

**4. Multi-IDE adopters are a real and growing audience.** Claude Code,
Kiro, GitHub Copilot (app), and OpenAI Codex are the named targets. Two
of them — Claude Code and Kiro — support the full Agent Skills spec
including directory-scoped skills and custom subagents; the other two
read AGENTS.md and a per-tool instruction file but have no skills
system. Today the template ships under `.claude/` with no awareness of
any of this; adopters using non-Claude tools get governance docs and not
much else. (Kiro path conventions and Layer 2 feature parity are subject
to verification — see Unresolved Question 3.)

## Proposal

One bundle, three internal layers, three coordinated install routes, a
single TOML manifest, per-IDE projection at install time, and a
documented upgrade-scalability pattern.

### Repo layout

The bundle ships as a **single repo with three top-level directories** —
`agents/`, `template/`, `tools/`. Each is independently shippable but
versioned together; a contributor opening the repo sees all three layers
at once. Sibling repos were considered and declined: they would fragment
discovery, and the bundle is small enough (kilobytes) that consumers
cloning the whole thing isn't a real cost.

### The three layers

The bundle's source-of-truth lives in those three top-level directories.
Layering is *internal*: it shapes what the per-IDE projection step
emits, but adopters don't see three install commands.

| Layer | Contents | Portability |
|---|---|---|
| **0 — Universal context** | Declared as `[layout.X]` atoms in the manifest. Three today: `layout.agents-md` (root `AGENTS.md` skeleton), `layout.docs` (governance docs — `CHARTER.md`, `CONVENTIONS.md`, `adr/`, `rfc/`, `architecture/`, `product/`, `guides/`, `knowledge/`, `_templates/`), `layout.package-example` (`packages/_example/` shape). | Every agent tool that reads `AGENTS.md` — Claude Code, Kiro, GitHub Copilot, Codex (and any other AGENTS.md-aware tool) |
| **1 — Spec-conformant skills** | `agents/skills/<skill>/SKILL.md` directories with `references/`, `scripts/`, `assets/` inside each | The SKILL.md format is portable across compliant tools (Agent Skills spec). Projection emits `.claude/skills/` for Claude Code, `.kiro/skills/` for Kiro, and tool-specific instruction-file inlining for Copilot/Codex (`.github/copilot-instructions.md` and root `AGENTS.md` respectively — they lack a skills system). |
| **2 — Claude-and-Kiro extensions** | Subagents (`agents/subagents/`), hooks (`.claude/settings.local.json` shape), bundled-skill composition (`/run-skill-generator` integration), Ralph harness | Claude Code and Kiro 0.9+ support custom subagents in equivalent shapes. Projection emits `.claude/agents/` for the former, `.kiro/subagents/` (or Kiro's equivalent path per their docs) for the latter. GitHub Copilot and Codex skip Layer 2 entirely — they have no subagent concept. |

### Per-IDE projection

The install step asks (or sniffs) which IDEs the adopter uses, then
projects accordingly. Multi-IDE teams get multiple projections from the
same source.

| Source bundle element | Claude Code | Kiro | GitHub Copilot | OpenAI Codex |
|---|---|---|---|---|
| `agents/AGENTS.md` (Layer 0) | root `AGENTS.md` + `.claude/CLAUDE.md` symlink | root `AGENTS.md` + `.kiro/steering/` entries per Kiro's steering inclusion modes | root `AGENTS.md` + `.github/copilot-instructions.md` mirror | root `AGENTS.md` |
| `agents/skills/<name>/` (Layer 1) | `.claude/skills/<name>/` — full directory preserved (SKILL.md, scripts, references, assets) | `.kiro/skills/<name>/` † — full directory preserved per Kiro's Agent Skills support | SKILL.md `description:`, inlined into a managed block in `.github/copilot-instructions.md` ‡ | SKILL.md `description:`, inlined into a managed block in root `AGENTS.md` ‡ |
| `agents/subagents/<name>.md` (Layer 2) | `.claude/agents/<name>.md` | `.kiro/subagents/<name>.md` † — Kiro 0.9 added custom subagents | dropped | dropped |
| Hooks (Layer 2) | `.claude/settings.local.json` snippet | Kiro hook config † | dropped | dropped |

† Kiro paths and feature parity subject to verification; see
[Unresolved Question 3](#unresolved-questions) for the deferred
design call.
‡ Copilot/Codex managed-block delimiter syntax and conflict policy
deferred to the Per-IDE projection adapters spec; see
[Unresolved Question 2](#unresolved-questions).

The Copilot/Codex Layer 1 projection contract: SKILL.md `description:`
field gets inlined into a delimited managed block in the IDE's
instruction file; `/adopt-repo --update` rewrites *only* the managed
block on subsequent syncs; adopter hand-edits outside the block
survive.

Claude Code and Kiro are first-class — full Layer 0 + 1 + 2 with
directory-scoped skills and custom subagents. GitHub Copilot and Codex
get Layer 0 plus a degraded Layer 1 (skill *descriptions* inlined into
their instruction files, not the full SKILL.md bodies — they have no
mechanism to load skill content on demand). The Drawbacks section names
this honestly: Copilot and Codex adopters get the governance scaffold
and the agent's awareness that the skills exist, but not the skills'
full behavioral effect.

### Skills go directory-scoped

Concrete moves from today's structure:

- `docs/_templates/spec.md` → `agents/skills/new-spec/assets/spec.md`
- `docs/_templates/plan.md` → `agents/skills/new-spec/assets/plan.md`
- `docs/_templates/state.json` → `agents/skills/work-loop/assets/state.json`
- `tools/check-done.py` → `agents/skills/work-loop/scripts/check-done.py`
- Reviewer agents stay under `agents/subagents/` (Layer 2), unchanged in
  contract (they already declare `dependencies: []` and reference
  `AGENTS.md` / spec docs by shape).
- The custom `dependencies:` frontmatter key is **dropped entirely**.
  Each skill ships self-contained per the spec's directory-scoped model;
  closure isn't manifest-driven anymore, it's filesystem-derived from
  the skill's own directory. The existing `tools/lint-skill-deps.sh`
  (which parses that frontmatter key) is **replaced**, not "tightened" —
  the new lint is a body-scanner that greps each `SKILL.md` for links
  and paths escaping the skill directory. New name (working title):
  `tools/lint-skill-isolation.py`. Stated explicitly because the framing
  difference matters: this is a tool rewrite, not a configuration change.
- The work-loop skill's four `CONVENTIONS.md` anchor references
  (`#contract-vs-construction-tests`, `#work-loop-state`,
  `#supervisor-mode`, `#knowledge-base`) get **inlined** into the
  work-loop skill's `references/` directory. This closes the
  CONVENTIONS-anchor subclass of the drift bug — work-loop reads its
  own snapshot, not the adopter's possibly-renamed conventions.

Skill bodies are rewritten to reference *shape, not file path*. Work-loop
refers to "the spec the new-spec skill produces" by structural contract
("a document that names observable outcomes, structural rules, and a
verification mode"), not by section heading.

#### Graceful-degrade discipline

Skills must work in isolation, even when sibling skills or Layer 0
governance docs aren't present. Every external reference in a skill body
carries an *if-available, otherwise…* clause, written explicitly:

| Touchpoint | Degrade clause |
|---|---|
| Knowledge base (`docs/knowledge/patterns.jsonl`) | "If the file exists, append. If not, the adopter doesn't use a knowledge base — note the lesson in the PR description instead." |
| Hooks (e.g. `tools/hooks/session-start.py`) | Hooks are harness-level, not skill-runtime. If Layer 0 isn't installed, the hook never fires; the skill runs without the pre-priming. |
| `CONVENTIONS.md` references | Inlined into the skill's `references/` directory. Skills don't anchor-chase into adopter docs. |
| Sibling subagents (e.g. `adversarial-reviewer`) | "Use the adversarial-reviewer subagent if available; otherwise self-review against this checklist." The checklist already exists in the SKILL.md. |
| Sibling skills (e.g. `new-spec`) | Recommendations, not dependencies. "If this repo has a spec workflow, run it first; otherwise sharpen the trio yourself." |

The new `lint-skill-isolation.py` enforces: a skill body contains no
path outside its own directory **and** every external concept is paired
with a graceful-degrade clause. The first rule is mechanically
checkable (grep-driven); the second is a checklist enforced during
review.

### Install routes

Three install routes share the same bundle, manifest, and placeholder
format. Adopters pick the route their environment allows.

| Route | Tool | Network needs | Update mechanism | Conflict handling |
|---|---|---|---|---|
| **Primary** | **Copier** (`copier copy`, `copier update`) | git clone + git pull + one-time `pip install copier` through Artifactory PAT | `copier update` | Three-way merge driver |
| **Fallback** | `python3 bootstrap.py` (stdlib only) | git clone + git pull only | Re-run `bootstrap.py --update` after `git pull` in cache | Diff + surface conflicts as text |
| **Adaptation overlay** | `/adopt-repo` (Claude Code skill, optionally wraps Copier or bootstrap.py) | git clone + git pull + Claude Code | `/adopt-repo --update` | LLM-assisted conflict surfacing |

Copier is the primary because it earns its keep: `copier update`'s
three-way merge driver, conditional file inclusion, and template-update
ergonomics are real features we'd otherwise reinvent. The one-time
`pip install copier` through Artifactory + PAT is friction, not a block,
in the named corporate environment — but it is *per-developer* friction.
A team of N adopters needs N PATs configured. Adopters should treat
"set up pip + Artifactory + PAT" as a documented new-hire onboarding
line item; the alternative is the `bootstrap.py` fallback, which runs
on pure stdlib and skips the PAT entirely (at the cost of Copier's
merge driver).

`bootstrap.py` exists for the genuinely-no-Copier case — CI bots, fresh
Windows machines, environments where Artifactory PAT setup isn't
available. Pure stdlib (`tomllib`, `pathlib`, `shutil`), no external
dependencies. Same manifest, same placeholder format, thinner update
mechanic (text-diff conflict surfacing instead of merge driver).

`/adopt-repo` is the Claude Code overlay: it wraps either of the above
and adds LLM inference for the placeholder substitution pass (see
[`/adopt-repo` — the Claude Code overlay](#adopt-repo--the-claude-code-overlay)
below, step 3). For adopters running Claude Code, it's the one-command
entry point.

### The install mechanic

The only network operations the install path uses are `git clone` and
`git pull` against GitHub or an internal GitLab mirror, plus the
one-time `pip install copier` through Artifactory (for the primary
route). No raw-file fetches, no `npx`, no curl one-liners.

**Initial install (Copier primary):**

```
1. pip install copier            # one-time, through Artifactory PAT
2. copier copy gh:<template-repo> target-dir/
3. (Optional) cd target-dir/ && /adopt-repo
   — Claude Code overlay for LLM-assisted placeholder substitution
```

**Initial install (bootstrap.py fallback):**

```
1. git clone <template-repo> .template-cache
2. cd into your target repo
3. python3 .template-cache/bootstrap.py
4. The installer projects bundle contents into the target, substitutes
   placeholders, writes .template-version with the cache's commit SHA.
```

**Update later:**

Copier path: `copier update` (handles fetch, merge, conflict resolution
through its merge driver).

Fallback path: `git -C .template-cache pull && python3
.template-cache/bootstrap.py --update`. The installer diffs the new
cache against the SHA in `.template-version`, surfaces what changed,
applies what the adopter accepts (or what `--ci` mode auto-applies for
scheduled runs — see Upgrade scalability).

### `/adopt-repo` — the Claude Code overlay

`/adopt-repo` is a Claude Code skill (itself part of Layer 2). Its
responsibilities, when run as the install route:

1. **Detect target context.** Which IDEs is this repo configured for?
   (Look for `.claude/`, `.kiro/`, `.github/copilot-instructions.md`,
   `AGENTS.md` already at root, etc.) Drive the per-IDE projection step
   accordingly.
2. **Project the bundle.** Apply the per-IDE adapter table above.
3. **Substitute placeholders.** Read the placeholder format (described
   below), infer values from the repo, and apply the
   ambiguity-handling discipline (the per-mode rules below):
   - **One candidate found** (exactly one `pyproject.toml`, one
     `package.json`, one `Cargo.toml`, etc.): substitute silently.
   - **More than one candidate**: surface them with their source files
     cited and ask the adopter to pick.
   - **No candidate found**: write a clearly-marked `TODO` into the
     target file at the placeholder's location and continue.
   The inferred set stays small — lint, test, build, install commands,
   primary language. Conventions, architectural choices, and team
   shape are out of scope; those are decisions the human owns.
4. **Compose with `/run-skill-generator`.** Optionally invoke Claude
   Code's bundled `/run-skill-generator` to capture a project-specific
   launch recipe as a sibling skill.
5. **Safety posture.** Dry-run by default. Show the file list before
   writing. Require explicit confirmation. Never paper over inference
   failures with plausible defaults — surface them.

The pattern is hand-curated-with-assistance, not agent-generated. Naive
agent-generated context files measurably reduce task success rates
(~3%) and increase inference cost (~20%+) per published research; the
value of `/adopt-repo` is in narrowing the human's choices, not in
eliminating them.

### Placeholder format

Placeholders use `<placeholder-name>` markers — readable by Python sed,
by Copier's Jinja layer (which can match angle-bracket patterns), by an
LLM, and by humans reviewing diffs. Angle brackets render as visible
TODO-like hints in unrendered Markdown and don't collide with template
engines the adopter may run later in their own pipelines.

One render caveat: some Markdown previewers treat angle-bracket strings
as HTML tags and may de-emphasize unknown tags in fenced code blocks.
The installer's placeholder detector matches only standalone
`<kebab-name>` patterns (lowercase, hyphens only, no whitespace, no
attributes) so substitution doesn't accidentally rewrite legitimate
HTML embedded in template prose. Adopters who preview templates in an
HTML-aware tool may see placeholders rendered oddly; the on-disk
substitution is unaffected.

Example in a template `AGENTS.md`:

````markdown
A monorepo for `<project-name>` — a `<project-one-liner>`.

## Commands you'll need

```bash
<install-command>           # one-time setup
<test-command>              # run tests for the package you're in
<lint-command>              # lint + format check
<build-command>             # produce build artifacts
```
````

Copier, `bootstrap.py`, and `/adopt-repo` all understand the same
format. Same template, three install routes, depending on what the
adopter's environment allows.

### Python-everywhere, no shell scripts in the install path

To support corporate Windows + PowerShell environments without a
dual-implementation burden:

- Hook scripts move from `.sh` to `.py`: `tools/hooks/session-start.py`,
  `tools/hooks/pre-pr.py`. Claude Code's hook system invokes any
  executable; Python runs identically on Mac, Linux, and Windows.
- Skill `scripts/*` are Python by default. Per the Agent Skills spec,
  "Supported languages depend on the agent implementation. Common
  options include Python, Bash, and JavaScript." Python is the most
  portable.
- The no-LLM fallback installer (`bootstrap.py`) is pure-stdlib Python.
- The Ralph harness (`tools/ralph.sh`) stays shell — explicitly
  Mac/Linux only, documented as such. Subprocess management, signal
  handling, and loop control don't map 1:1 from bash to Python, and
  Ralph is a minority-use tool. Windows adopters who want AFK Claude
  runs use WSL.
- Dynamic-context blocks inside skills that genuinely need shell can
  declare `shell: powershell` in frontmatter; Claude Code's hook system
  routes the command appropriately on Windows.

### Manifest format

The catalog manifest is `bundle.toml` at the repo root. **TOML** because
`tomllib` is in Python stdlib (3.11+), comments are allowed, the syntax
matches `pyproject.toml` / `Cargo.toml` conventions adopters already know,
and the manifest's shape (a small set of `[skill.X]` and `[bundle.Y]`
tables) sits well within TOML's strengths. YAML loses on parser dependency
and whitespace footguns; JSON loses on comments.

### Catalog shape: core and extensions

The bundle's installable atoms split into two **types** (skills and
agents) and two **tiers** (core and extensions), named in the catalog
manifest:

| Set | Type | Contents | Installed by default |
|---|---|---|---|
| **Core layout pack** | layouts | `layout.agents-md` (root `AGENTS.md`), `layout.docs` (`docs/` scaffold + `_templates/`), `layout.package-example` (`packages/_example/`) | Yes — these are Layer 0; install identically across every IDE target |
| **Core skills pack** | skills | `work-loop`, `new-spec`, `bug-fix` | Yes (on every IDE target) |
| **Core agents pack** | agents | `adversarial-reviewer`, `security-reviewer`, `quality-engineer`, `implementer` | Yes — on Claude Code and Kiro (which have a subagent concept). On Copilot and Codex the agents pack is a no-op projection (no subagent equivalent); the installer surfaces this as an info-level message at install time so the adopter isn't surprised. |
| **Extension skills** | skills | `new-rfc`, `new-adr`, `new-package` | Opt-in per adopter |

Core is the minimum coherent surface that delivers what this template
exists for — the plan → execute → verify → review loop, with the spec
discipline and bug-fix variant that compose with it. Core ships as
**skills pack + agents pack together** because work-loop dispatches the
four reviewer/implementer agents as part of its REVIEW and supervisor
phases; shipping the skills without the agents would mean the loop's
review step degrades to the inline checklist (graceful but
significantly less capable). Extensions add governance ceremony (RFCs,
ADRs) and monorepo scaffolding.

Skills, agents, and layouts are all first-class atoms — adopters can
install each pack as a whole, compose individual items, or skip
pieces. The default is "install core (all three packs)"; the install
commands below show the full composition surface. Common
layout-composition examples: `--without layout.package-example` for a
single-package repo that doesn't need monorepo scaffolding; `--only
layout.agents-md` for an existing repo that wants just the root
AGENTS.md skeleton without the full `docs/` shape.

**Per-agent degrade behavior** when an adopter installs core but
excludes a specific agent (e.g. `--without implementer`):

| Excluded agent | What work-loop does without it |
|---|---|
| `adversarial-reviewer` | REVIEW runs only the inline self-review checklist; the spec-mode reviewer pass at the PLAN gate is skipped, so `state.json.plan_review_status` auto-advances to `approved` without an adversarial pass. The loop proceeds without an external review signal. |
| `security-reviewer` | REVIEW skips the security-lens pass. The work-loop's "consider security-reviewer when the diff crosses an auth/secrets/user-input boundary" instruction becomes a no-op recommendation. |
| `quality-engineer` | REVIEW skips the maintenance-lens pass and the spec-close coverage check. Work-loop's anti-pattern "Declaring spec-complete from per-task gates" loses its mechanical guard. |
| `implementer` | Supervisor mode is unavailable. Work-loop falls back to single-agent mode for every task, regardless of `Depends on: none` parallelism. The skill body's supervisor section surfaces this at PLAN time. |

These are the contract; each agent's SKILL/agent file states what its
absence means in its own opening section. Excluding an agent is a
supported configuration, not drift — see the corresponding Drawbacks
note.

The previous `update-conventions` skill is **dropped from the bundle
entirely**. Changing governance docs is a per-adopter editorial action
that doesn't need its own skill — adopters who want a workflow for it
write their own skill in their own repo.

We deliberately don't ship bundles split by team size or tech stack.
"Solo / team / monorepo" partitions are an editorial taxonomy that
ages with the adopter's growth; "frontend / backend / devops" partitions
are a tech-stack taxonomy this template is not in the business of
shaping (per the four-principle test for what earns its keep here).
Adopters who want layered bundles on top of core+extensions define them
in their own repo (see below).

In the manifest:

```toml
# Core layout pack — Layer 0 atoms; install identically across IDEs
[layout.agents-md]
path = "template/AGENTS.md"
tier = "core"

[layout.docs]
path = "template/docs/"
tier = "core"

[layout.package-example]
path = "template/packages/_example/"
tier = "core"

# Core skills pack
[skill.work-loop]
path = "agents/skills/work-loop"
tier = "core"

[skill.new-spec]
path = "agents/skills/new-spec"
tier = "core"

[skill.bug-fix]
path = "agents/skills/bug-fix"
tier = "core"

# Core agents pack
[agent.adversarial-reviewer]
path = "agents/subagents/adversarial-reviewer.md"
tier = "core"

[agent.security-reviewer]
path = "agents/subagents/security-reviewer.md"
tier = "core"

[agent.quality-engineer]
path = "agents/subagents/quality-engineer.md"
tier = "core"

[agent.implementer]
path = "agents/subagents/implementer.md"
tier = "core"

# Extension skills
[skill.new-rfc]
path = "agents/skills/new-rfc"
tier = "extension"

# new-adr, new-package: tier = "extension"

# Extension agents — none today, but the schema supports them.
# Example (not currently shipped):
# [agent.performance-reviewer]
# path = "agents/subagents/performance-reviewer.md"
# tier = "extension"
```

Install commands. The same `--with` / `--without` / `--only` flags work
for both skills and agents (the manifest type tells the installer
which it is):

```
/adopt-repo                              # core: skills pack + agents pack
/adopt-repo --with new-rfc               # core plus one extension skill
/adopt-repo --with new-rfc --with new-adr  # core plus two extensions
/adopt-repo --all                        # core plus every extension (skills and agents)

# Agent-pack composition
/adopt-repo --without implementer        # core minus one agent
/adopt-repo --skills-only                # skills only — skip the agents pack
/adopt-repo --agents-only                # agents only — skip the skills pack
/adopt-repo --only adversarial-reviewer  # just one atom (overrides defaults)
```

**Flag precedence.** Explicit flags (`--with`, `--without`, `--only`)
beat categorical flags (`--skills-only`, `--agents-only`, `--all`).
- `--skills-only --with adversarial-reviewer` → core skills + that one
  agent (explicit `--with` overrides the type filter).
- `--agents-only --with new-rfc` → core agents + that extension skill.
- `--only X --without Y` → just X (the `--without` is redundant; the
  installer emits a warning).
- Type-mismatched `--only` is allowed (`--only new-rfc` works against a
  skill; `--only implementer` works against an agent — the installer
  doesn't restrict by type, only by name).
- `--only` and `--skills-only` / `--agents-only` override the
  default-install rule: they install *exactly* what's named (plus
  anything added with `--with`), nothing else.
- `--only X --skills-only` (or `--only X --agents-only`): `--only`
  wins (it's the most explicit). The installer emits a warning that
  the categorical flag is redundant given the explicit `--only`.

`bootstrap.py` and `copier copy` honour the same flags through their
own argument styles.

**Composition persistence across updates.** The adopter's composition
choices are persisted in `.template-version` (alongside the cache SHA)
as **deltas against the upstream tier**, not as a resolved set. The
schema:

```toml
template_sha = "a2bc58d..."           # what was installed from
excluded = ["implementer"]            # core items the adopter skipped
added = ["new-rfc"]                   # extensions the adopter added
mode = "default"                      # "default", "skills-only", "agents-only", or "only"
only_set = []                         # populated when mode = "only"
```

`/adopt-repo --update`, `bootstrap.py --update`, and `copier update`
all read this and re-resolve against the upstream tier: a new core
atom added in `v1.2.0` lands automatically on the next sync (because
the adopter never excluded it), and the adopter's `excluded = [...]`
list stays durable across versions. The PR description surfaces both
("Adds core agent `performance-reviewer`; respects your existing
exclusion of `implementer`"). The scheduled-action pattern runs
`--update` without composition flags, so weekly syncs never silently
change the adopter's deltas.

**Upstream renames and deletions:**

- **Rename.** When an upstream release renames an atom (e.g. `implementer`
  → `task-executor` in `v1.3.0`), the release notes carry a `renamed =
  { "implementer" = "task-executor" }` migration entry. The installer
  applies the rename to the adopter's `excluded` and `added` lists at
  update time, so an excluded atom stays excluded under its new name
  rather than silently landing as if it were a new addition. When an
  adopter jumps multiple versions in one update, **rename entries
  compose in release order across the skipped range** — `implementer`
  → `task-executor` → `runner` resolves to `runner` in the adopter's
  delta list.
- **Delete.** When an upstream release removes an atom from the
  catalog, any reference to it in the adopter's `excluded` or `added`
  list is pruned at update time and surfaced as a one-line info
  message in the PR. Keeping a stale tombstone serves no one — the
  atom is already gone upstream. **Name reuse guard:** if a later
  release ships a new atom under a previously-deleted atom's old name
  within the adopter's known history, the installer surfaces this as
  an explicit warning rather than silently landing it as a fresh
  addition; the adopter confirms whether the new atom is a genuine
  fresh ship or a name collision they want to opt out of.

### Downstream-defined bundles

Adopters who want a curated bundle on top of core+extensions define it
in their own repo's `bundle.toml`, referencing skills by name. **Bundles
are local aliases over locally-installed skills** — there is no
`extends` chain across repos, no cross-repo resolution at bundle-resolve
time. If a bundle references a skill the adopter hasn't installed yet,
the installer surfaces the gap and names the `--with` flags they need
to add first.

Example: an adopter's `bundle.toml`:

```toml
[bundle.our-platform-default]
description = "What new repos at our org get on day one."
skills = ["work-loop", "new-spec", "bug-fix", "new-rfc", "new-adr"]
```

The skill names refer to the adopter's local copies — which they
installed from us via `/adopt-repo --all` (or `--with new-rfc --with
new-adr` etc.). The upstream relationship lives in the cache layout
(`.template-cache/` knows where it was cloned from) and is used only
for the `--update` channel, never for bundle resolution. The mental
model at the adopter level stays flat: you have skills (locally), and
you have bundles (which are local aliases over those skills).

### Upgrade scalability

Per-adopter coordination doesn't scale. The upgrade story has to work
self-serve, without the template maintainer doing N things for N
adopters.

**Semver tags on the template repo.** Every restructure-grade change
gets a tag (`v1.0.0`, `v1.1.0`, etc.). Patch-level changes (lint fix,
typo, single-skill edit) get patch tags. Minor changes (new extension
skill, new placeholder) get minor tags. Major changes (restructure of
the bundle's layout, breaking placeholder rename, dropped skill) get
major tags. Adopters pin to a version in their `.template-version`.

**Scheduled-action upgrade pattern.** Adopters drop a GitHub Action
(or GitLab CI job) into their own repo that runs on a cadence:

```yaml
# .github/workflows/template-sync.yml (sketch)
on:
  schedule: [{ cron: '0 9 * * 1' }]   # Mondays 09:00
  workflow_dispatch:
permissions:
  contents: write
  pull-requests: write
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Ensure template cache exists
        run: |
          if [ ! -d .template-cache ]; then
            git clone <template-repo-url> .template-cache
          else
            git -C .template-cache pull --ff-only
          fi
      - run: python3 .template-cache/bootstrap.py --update --ci
      - uses: peter-evans/create-pull-request@v6
        with:
          title: "chore(template): sync upstream changes"
          body: "Automated template sync. Review the diff before merge."
```

**Prereq the adopter grants once:** Settings → Actions → Workflow
permissions must allow workflows to create pull requests. Many
organisations disable this by default; the scheduled-action pattern is
inert until that bit flips. The template ships the workflow with a
header comment naming this prereq explicitly.

**`--ci` mode contract:**

- Headless: no interactive prompts, no stdin reads.
- Writes file changes to disk; uses git-style `<<<<<<<` / `=======` /
  `>>>>>>>` conflict markers when the adopter has locally modified a
  file the update wants to change.
- Exit codes: `0` when the update applied (cleanly or with conflict
  markers staged on disk — the PR step picks both cases up via `git
  status`); `1` when the installer itself failed (manifest parse error,
  missing cache, permission error). No "soft warning" exit codes —
  conflicts are content for review, not an installer failure.
- Output: stdout is a one-paragraph human summary of what changed
  (file count, conflict count, skills and agents affected). The PR-
  creating step consumes the file changes from disk; it does *not*
  parse stdout for state.
- Informational messages (the Copilot/Codex no-op-projection notice,
  rename/delete migration surfacing) go to **stderr** with an
  `[info]` prefix. They are always emitted (not suppressed by
  `--ci`) and do not affect the exit code. One line per message.
  Example:
  ```
  [info] Copilot target: agents pack projects as no-op (no subagent equivalent).
  ```
- The `--update` of the Copier route has an analogous pattern using
  `copier update --pretend` (dry-run) chained with `copier update`
  (apply), wrapped in the same scheduled-action shell. Copier's merge
  driver replaces the explicit conflict-marker step.

The template ships an example `template-sync.yml` adopters can copy
verbatim.

**Why this is scalable:** adopters opt in to the upgrade cadence
themselves; the template maintainer doesn't reach out, doesn't track
who's on what version, doesn't coordinate cutovers. Adopter sees a PR
weekly with whatever changed; the adopter's normal code review process
gates merges. If a release is breaking, the version pin in
`.template-version` means the bot only pulls major-version updates when
the adopter explicitly bumps it.

### From design to spec — the trajectory

This RFC defines the bundle design — *our* catalog, our install routes,
our projection rules. Two follow-up RFCs are in flight to lift the
design into a reusable shape:

- **RFC-0002 — Self-hosting.** This repo becomes the first adopter of
  its own bundle. The Layer 0 atoms (`layout.agents-md`, `layout.docs`,
  `layout.package-example`) are applied to this repo itself, so its
  `AGENTS.md`, `docs/` scaffold, and `packages/_example/` come from the
  bundle rather than being hand-maintained. The bundle's source-of-
  truth (under `agents/`, `template/`, `tools/`) and the repo's own
  rendered content split cleanly. Closes the no-specs-in-template
  constraint by making "what the bundle ships to adopters" vs "what
  this repo runs" structurally distinct.

- **RFC-0003 — Bundle Format Specification and CLI.** Extract the
  `bundle.toml` schema, the `<placeholder>` syntax, the per-IDE
  projection adapter contract, the `.template-version` deltas schema,
  and the `--ci` mode behavior into a published spec other catalog
  publishers can comply with. Ships a CLI (working name
  `agentbundle`) as the spec's reference implementation: spec-URI
  dispatch, catalog discovery, compliance validation, and a
  structured agent-inform contract for downstream harnesses to
  consume. The CLI is what turns the spec from a paper artifact into
  an executable contract — and turns this template from "our bundle"
  into "the reference implementation of an open bundle format."

The sequence matters: RFC-0001 ships the reference implementation;
RFC-0002 makes the repo self-host on it; RFC-0003 publishes the spec
and the CLI. Each is an independently shippable step, and each
naturally produces the conditions the next one needs.

### Success criteria

Three checks gate this RFC as delivered. The first two are mechanical
and self-attesting; the third is the content gate the reviewer flagged
as missing in the earlier draft.

1. **`lint-skill-isolation.py` rejects out-of-skill references.** Every
   skill body either references a path inside its own directory, or
   names an external concept paired with a graceful-degrade clause.
   The drift bug we just fixed would have failed this check. Future
   drift bugs of the same subclass will fail it too. CI runs this on
   every PR.
2. **CI runs the full install path end-to-end against a clean test
   repo each PR cycle.** Both `copier copy` and `python3 bootstrap.py`
   get exercised against a freshly-cloned target; the build is green
   only when both routes produce a working repo without crashing. CI
   exercises at least four compositions per route — default (core
   only), `--all`, `--without implementer`, and `--skills-only` —
   against at least two IDE targets each (one with subagent support
   and one without), so the no-op-projection branch for Copilot/Codex
   gets covered too. This keeps the composition surface from shipping
   untested.
3. **Content gate: the projected repo has no dangling references.**
   Every internal link in projected `.claude/skills/**/*.md`,
   `.kiro/skills/**/*.md`, and `AGENTS.md` resolves to an existing
   file or anchor. Every `<placeholder>` marker is either substituted
   or marked TODO. Every cross-reference between a skill body and a
   Layer 0 doc names a section that exists in that doc. This catches
   the drift bug's content-shape signature even when the installer
   doesn't crash.

External adopter reports (downstream `--update` cycles, non-Claude IDE
projections) are nice-to-have signals but not the gate — that channel
may never arrive at scale we can measure.

## Alternatives considered

**Alt 1 — Light-touch lint rule only.** Extend the existing
`lint-skill-deps.sh` to flag any skill reference to a `docs/_templates/`
section by name; keep
the current single-bundle distribution. Lowest disruption. Closes the
specific drift class from the recent bug. **Why not chosen:** preserves
the structural coupling; new drift bugs appear in other shapes (anchor
refs, tool-CLI refs, sibling-skill restructure). The lint rule patches
symptoms; the structural model is what's wrong.

**Alt 2 — Heavy bundle, status quo.** Keep everything as one git
template, document a manual three-way merge for adopters. **Why not
chosen:** no clean update path, no multi-IDE story, no per-IDE
projection, no upgrade scalability.

**Alt 3 — `bootstrap.py` as primary, Copier as optional.** Earlier draft
of this RFC. **Why not chosen:** Copier earns its keep — `copier update`
already solves three-way merge, conditional file inclusion, and
template-update conflict resolution. Demoting it to "optional" forces
`bootstrap.py` to reinvent these. In the named corporate environment,
`pip install copier` through Artifactory PAT is one-time per-developer
friction, not a block. The honest framing is Copier-primary with
`bootstrap.py` as the genuinely-no-Python fallback.

**Alt 4 — Dual shell scripts (`bootstrap.sh` + `bootstrap.ps1`).** Native
to each platform. **Why not chosen:** two implementations to maintain in
sync. Every feature lands in both. Python wins on maintenance cost given
that most environments already have it.

**Alt 5 — Plugin-market hybrid (Layer 1 via Claude Code's `/plugin`,
Layer 0 in the bundle).** Publish skills to Claude Code's `/plugin`
market while keeping Layer 0 in the git template. **Why not chosen:**
the corporate environment that motivates this RFC can't reach
`/plugin`'s registry endpoints (no raw HTTP API access against the
marketplace). Plugin-market distribution presupposes general internet
access; we can't presuppose that. Worth revisiting if a later RFC
narrows the constrained-network requirement.

**Alt 6 — Tech-stack bundles (frontend / backend / devops).** Mirror
the partitions the leading skill catalogs use. **Why not chosen:** none
of our skills are tech-stack-shaped — they're governance and workflow.
Authoring tech-stack skills to populate the bundles fails the
four-principle test (universal across stacks, substantive, habit not
tool, used often). Adopters compose tech-stack skills from other
catalogs alongside ours; our value is in the loop, not the language.

**Alt 7 — Team-size bundles (solo / team / monorepo).** Provide
editorial entry points by ceremony level. **Why not chosen:** team size
is the adopter's lifecycle decision, not ours. Core + extensions lets
adopters define those layers without us guessing wrong.

**Alt 8 — Do nothing.** The drift bug is fixed; downstream adopters
already manage. **Why not chosen:** the bug class will recur, the
corporate-network gap stays, the multi-IDE gap stays, the upgrade-
scalability gap stays. The cost of doing nothing isn't zero; it's just
deferred.

## Drawbacks

**Migration cost is one-time but non-trivial.** Skills-decoupling
touches every skill body, every reviewer agent, and every shell script
in `tools/hooks/`. Layer 0 conversion to placeholder-aware templates
touches every governance doc and `AGENTS.md`. The work decomposes into
the follow-on specs listed below; no aggregate effort estimate is given
here (an estimate without a work-breakdown erodes trust in the rest of
the proposal).

**Mild duplication risk in Layer 1.** If two skills genuinely share an
asset, we ship two copies. None do today. The duplication risk shows up
later if (e.g.) the spec template grows to be useful in both `new-spec`
and a hypothetical `new-rfc-with-spec` skill; at that point the
duplication is the right answer per the spec's directory-scoped model,
but it's still real.

**Three install routes (Copier + `bootstrap.py` + `/adopt-repo`).**
The three routes have to stay in sync — same placeholders understood
the same way, same per-IDE projection rules, same safety posture.
Mitigation: all three consume the same `bundle.toml` manifest; the
routes are thin wrappers around shared resolution logic. The shared-
logic discipline is mechanically enforceable (the install-path CI test
exercises all three against the same target and asserts they produce
identical projected output).

**Copilot and Codex adopters get a degraded Layer 1.** They have no
skills system; the projection inlines skill *descriptions* into their
instruction files but cannot deliver the skills' full behavioral effect
(no on-demand loading, no `references/`, no `scripts/`). This is honest:
the value the template delivers depends on the IDE supporting the Agent
Skills spec, and two of the four targets don't. Claude Code and Kiro
remain first-class.

**Ralph stays Mac/Linux-only.** The AFK harness is the one explicit
platform exception to the Python-everywhere discipline. Windows adopters
who want unattended Claude runs route through WSL. Documented as such;
not promised cross-platform. If a real Windows adopter requests it,
port then — speculative cross-platform support pays no rent today.

**No grace-period deprecation for existing adopters.** The restructure
ships clean. Existing adopters take a one-time manual three-way merge
guided by `MIGRATION.md`; from then on the scheduled-action upgrade
pattern carries them. Adopter coordination during the cutover is the
maintainer's call (out of scope for this RFC); the design assumption is
that scheduled-action upgrades make per-adopter coordination unnecessary
at steady state.

**Bug-class closure is bounded.** This RFC closes the
**literal-heading-reference-from-skill-body-into-Layer-0** subclass —
the original drift bug. Skills snapshot what they need; cross-skill
file paths are forbidden by the new lint. Two adjacent classes remain
unaddressed:

- **Layer 0 → Layer 0 drift** (one governance doc renames a heading
  another references). The same mechanism that produced the original
  bug still applies inside Layer 0 prose; the content gate (Success
  Criterion 3) catches the dangling-link signature but the restructure
  doesn't prevent the rename in the first place.
- **Sibling-availability drift** (a dispatched subagent isn't installed;
  the skill silently no-ops). Graceful-degrade turns this from a crash
  into a quiet capability gap, which is better but still invisible —
  the adopter doesn't see what they're missing. With the new
  `--without <agent>` / `--only <agent>` composition surface, this is
  also a *configured* state, not just a possible state — adopters can
  intentionally exclude an agent. The per-agent degrade table in
  *Catalog shape* names what each loop phase does in that case, so the
  degraded behavior is explicit rather than emergent. The lint can
  surface the configured-vs-accidental case (`.template-version` says
  whether the agent was excluded by the adopter or simply absent on
  the IDE target).

Tool-CLI signature drift (a tool inside a skill's `scripts/` changes
its CLI without updating the skill body) is a separate class — intra-
skill consistency rather than coupling-by-name — and is out of scope
here. It's a Layer 1 internal concern, addressed by the skill's own
tests.

**The `/adopt-repo` skill is the riskiest piece.** Naive LLM-generated
context files perform worse than hand-written ones. `/adopt-repo` must
be conservative — propose, don't write; surface unknowns; never paper
over inference failures with plausible defaults. Dry-run mode by
default.

## Unresolved questions

The RFC-level design decisions are settled in the body. Three items are
explicitly deferred to the follow-on specs named below — not because the
RFC ducks them, but because the right altitude for these answers is the
spec that owns them:

1. **Shared resolution logic across the three install routes.** Copier,
   `bootstrap.py`, and `/adopt-repo` all consume the same `bundle.toml`
   and produce the same projection. *Where* the shared logic lives —
   one Python module the three routes import, or three independent
   implementations validated against the same CI fixture — is the
   **Placeholder + manifest format** spec's call.

2. **Copilot/Codex managed-block delimiter and conflict policy.** The
   description-only inlining contract is named at the RFC level; the
   delimiter syntax (`<!-- skills:begin -->` / `<!-- skills:end -->` or
   similar), the destination path on each IDE, and what happens when
   the adopter hand-edits inside the managed block are the **Per-IDE
   projection adapters** spec's call.

3. **Kiro path conventions and feature parity.** This RFC asserts Kiro
   supports the Agent Skills spec and Kiro 0.9 added custom subagents,
   pulling from Kiro docs at `kiro.dev/docs/skills` and the Kiro 0.9
   release notes. The exact directory layout (`.kiro/skills/`,
   `.kiro/subagents/`, `.kiro/steering/`), hook configuration shape,
   and any spec-version-skew between Kiro and Claude Code are subject
   to verification in the **Per-IDE projection adapters** spec. If
   verification reveals a parity gap, Motivation #4's framing of Kiro
   as a first-class target may need to weaken to "Layer 0 + 1, Layer 2
   subject to feature confirmation."

## Follow-on artifacts

If accepted, this RFC produces these downstream pieces of work, grouped
by dependency. No aggregate estimate — implementers will scope each
spec individually.

### Tier 1 — Unblocking specs (run in parallel)

- **F1 — Skills decoupling.** Move templates and tooling into owning
  skills; inline the four `CONVENTIONS.md` anchors into work-loop's
  `references/`; rewrite cross-skill references; replace
  `lint-skill-deps.sh` with `lint-skill-isolation.py`; add
  graceful-degrade clauses to every external reference in a skill
  body. Drop the custom `dependencies:` frontmatter key. **Bundles the
  convention change** into `docs/CONVENTIONS.md` § Skills (the new
  rules are F1's contract — they restate that skills are directory-
  scoped, no cross-skill file refs, no custom frontmatter dependency
  keys, every external reference has a graceful-degrade clause).
- **F2 — Python-everywhere migration.** Port `tools/hooks/*.sh` to
  Python; document Ralph as Mac/Linux-only. Scope is **only**
  `tools/hooks/` and Ralph documentation — skill `scripts/*` files
  are relocated by F1 and authored as Python at that step, so they
  don't appear in F2's scope. Runs in parallel with F1 without
  collision because the two specs touch disjoint paths.
- **F3 — Placeholder + manifest format.** Define the `<placeholder>`
  syntax, the `bundle.toml` schema, the `tier` field, and the
  contract all three install routes consume. Settle the shared-
  resolution-logic shape (Unresolved Question 1).

### Tier 2 — Per-IDE adapter (after F3)

- **F4 — Per-IDE projection adapters.** Concrete adapter shapes for
  Claude Code (full Layer 0+1+2), Kiro (full Layer 0+1+2 — verify
  paths against current Kiro docs), GitHub Copilot (Layer 0 + degraded
  Layer 1 inlined into `.github/copilot-instructions.md`), Codex
  (Layer 0 + degraded Layer 1 inlined into root `AGENTS.md`). Defines
  the managed-block delimiter, destination paths, and update-time
  conflict policy. Settles Unresolved Questions 2 and 3.

### Tier 3 — Install routes and gates (after F3 and F4)

- **F5 — `/adopt-repo` Claude Code overlay.** Build the install +
  update flow, IDE-detection logic, safety posture (dry-run default,
  surface unknowns), composition with `/run-skill-generator`,
  non-interactive `--ci` mode for scheduled actions.
- **F6 — `bootstrap.py` fallback installer.** Pure-stdlib Python
  installer for non-Copier environments. Same manifest, same
  placeholder format, thinner inference, headless `--ci` mode.
  Consumes F4's adapter contract for per-IDE projection.
- **F7 — Content gate (Success criterion 3).** Mechanical check that
  every internal link in projected repos resolves, every placeholder
  is substituted or TODO-marked, every skill→Layer-0 cross-reference
  names an existing section. Runs in CI on every PR. Operates on the
  projected tree, so it consumes F4's adapter contract.
- **F8 — Upgrade scalability.** Semver tagging convention on the
  template repo; example `template-sync.yml` GitHub Action that
  adopters copy verbatim; analogous Copier-route example; the
  non-interactive `--ci` mode contract.

### Tier 4 — Cutover docs (must ship with Tier 3)

- **F9 — `MIGRATION.md` at the repo root.** Single page. Names every
  file that moved (old path → new path), the one-time three-way merge
  for existing forks, and the scheduled-action `--update` flow for
  future syncs. No grace-period commitment. Load-bearing: the
  Drawbacks section's "existing adopters take a one-time manual
  three-way merge guided by MIGRATION.md" promise requires this to
  exist at cutover.
- **F10 — `CHANGELOG.md` entry.** Concrete before/after for the
  restructure, cross-referenced from `MIGRATION.md`.
- **F11 — ADR.** `docs/adr/NNNN-one-bundle-three-layers.md` records
  the decision once accepted, citing this RFC.
