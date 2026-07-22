# agentskills.io specification — applied reference

The [agentskills.io](https://agentskills.io) specification is the external standard every skill in this catalogue follows.
This page is the applied reference: what the spec requires, how this catalogue adds to it, and how the enforcement tools verify it.
The authoritative specification lives at agentskills.io; this page covers the catalogue-local application.

For how to author a skill from scratch, see [How to author a skill](../how-to/author-a-skill.md).

## Frontmatter keys

Six top-level keys are allowed; all others are rejected by the linter.

| Key | Required | Purpose |
|---|---|---|
| `name` | yes | Kebab-case identifier. Must be unique within the catalogue. |
| `description` | yes | One-line trigger sentence. The activation signal the agent reads. |
| `license` | yes | SPDX identifier (`MIT`, `Apache-2.0`, etc.). |
| `compatibility` | yes | Agent platforms this skill is validated on. |
| `metadata` | no | Project-specific fields — the escape hatch. |
| `allowed-tools` | no | The tools the skill instructs the agent to invoke. Omit if none. |

Everything project-specific that doesn't belong at the top level goes under `metadata:`.

## The `metadata:` escape hatch

The `metadata:` key is the catalogue's extension point within the spec.
Project-specific fields that don't belong at the top level live here:

```yaml
metadata:
  type: skill           # skill | hook | command
  boundaries:
    - filesystem_write
    - network_fetch
```

The linter enforces that `metadata:` is a YAML mapping (not a scalar or list).
Its sub-keys are not validated by the spec — they are the catalogue's own domain and must be self-consistent across the pack.

## Description rules

The `description:` field drives activation — it is the single field the agent reads when deciding whether to invoke the skill.
Getting it wrong means the skill either fires on the wrong prompts or fails to fire on the right ones.

Four rules the linter enforces:

1. **Single-line scalar.** No YAML folded (`>`) or literal (`|`) blocks.
   No continuation lines (an indented next line).
   These parse as valid YAML but break on some adapter targets.
2. **No structural YAML characters unquoted.** A bare `: ` mid-description, a leading `#`, `&`, `*`, or `[`, or whitespace-then-`#` change the parse.
   Wrap the whole value in double quotes if you need any of these characters.
3. **Trigger-phrased.** Start with "Use when…" or name the trigger condition explicitly.
   Describe when to activate, not what the implementation does.
4. **Under 1024 characters.** Some adapter targets truncate beyond this.

Run `python3 tools/lint-skill-spec.py` — it checks all four rules and is the authoritative source.
Do not memorise the rules from this page; run the linter.

## Directory layout

A skill is a directory with `SKILL.md` and four optional subdirectories.
The linter only blesses these four:

| Subdirectory | Contents |
|---|---|
| `scripts/` | Helper code the skill invokes — `python scripts/foo.py`. One level deep only. |
| `references/` | Detail the skill loads on demand when the workflow reaches it. Not pre-loaded. |
| `assets/` | Templates and fixtures the skill copies or fills in at runtime. |
| `evals/` | Activation and output-quality evals. Canonical nesting: `evals/eval_queries.json` (Tier-A), `evals/evals.json` + `evals/files/` (Tier-B). |

### How `references/` works — context on demand

Context that a skill needs but does not use on every invocation belongs in `references/`, not in the skill body.
The skill body loads a reference file at the moment the workflow reaches the branch that needs it — "load `references/strategy-X.md` now" — and routes to exactly one branch per run.

This has two effects: the skill body stays lean at the point of activation, and the agent carries only the context relevant to the current invocation rather than all possible branches.
A skill body that exceeds 500 lines is a signal that detail is embedded that should be in `references/`.
A skill that pre-loads all its reference files unconditionally, or embeds large knowledge blocks inline in the body, violates this pattern.

### Path discipline

All paths within a skill (scripts, references, assets) are relative to the skill's own directory.
A skill must not reference:

- Absolute filesystem paths
- Paths outside the pack's source tree (`packs/<pack>/.apm/skills/<name>/`)
- Paths that are only valid in a particular repo checkout or deployment
- Hardcoded org-specific locations or knowledge stores

Context the skill needs from the workspace (the CHARTER, the active adapter, the pack inventory) is read by the skill's own procedures at runtime from the workspace's standard structure — not embedded as a hardcoded path.
This is what makes a skill portable: any team can install it and have it behave consistently, without configuring input locations.

## Independent installation

Skills are self-contained by design.
A skill that requires a tool, package, or sibling skill declares its dependencies explicitly, detects their presence at the start of its workflow, and fails with a clear remediation message if they are absent.
No installation happens silently.

Three tiers govern how dependencies are handled:

**Tier 1 — Declare, detect, fail clean (the default for all dependencies).**
Name the dependency in `## Prerequisites`.
Detect it with `shutil.which()` for binaries or a library import probe for packages.
On absence: stop and emit the exact install command from Prerequisites — nothing more.
This is the correct tier for almost all skill dependencies.
The user's environment is not the skill's to modify without explicit consent.

**Tier 2 — Opt-in, gated, idempotent (allowed, not the default).**
A skill may install a dependency only when: the install is a single deterministic command, it needs no root, and it uses a package manager the user demonstrably already has.
The pattern is always: detect → ask for consent → install → re-verify.
Silent install and assumed PATH after install are both disallowed even in Tier 2.

**Tier 3 — Banned.**
Silent auto-install.
Assumed root or sudo.
Pipe-to-shell installers without explicit consent.
Trusting PATH without re-verifying after install.
None of these are acceptable regardless of convenience.

The three tiers are what make independent installation safe: any team member can install any profile and have every skill work — or fail clean with a precise remediation — without coordinating a shared environment or configuring shared file locations.

## OWASP Agentic Skills Top 10 v1.0 — mapping to the agentskills.io surface

The OWASP Agentic Skills Top 10 v1.0 (AST01–AST10) is a public security standard for skill-file authoring, distribution, and installation.
The checks map directly onto the agentskills.io surface:

| Check | Surface | What to verify |
|---|---|---|
| AST01 Malicious content | Skill body and agent definitions | No instructions that benefit the author at the expense of the user's agent |
| AST03 Over-privileged tools | `allowed-tools` | Every listed tool is necessary; high-impact tools scoped to the narrowest action set |
| AST04 Insecure metadata | Frontmatter fields | Validated against schema; no zero-width Unicode or base64 payloads in display fields |
| AST05 External references | Body instructions that fetch URLs | References pinned; fetched content treated as data, not instructions |
| AST06 Isolation | Body instructions for code execution | Containment mechanism declared, not implied |
| AST07 Version drift | Dependencies in manifests | All pinned; no open ranges or `latest` |
| AST09 Governance | Installation and execution record | Skill appears in an auditable inventory with name, version, content hash, and source |
| AST10 Cross-platform | Security metadata | Risk tier and permission manifest survive projection across all adapter targets |

AST02 (supply chain) is handled by the supply-chain security module.
AST08 is addressed structurally by the `tool`/`hybrid`/`reason` review taxonomy built into the adversarial review process.

Every skill converged into this catalogue is reviewed against AST01–AST10 before landing.
Every skill authored here is reviewed against the same checks in the adversarial review step of the work-loop.

## Enforcement tools

| Tool | When to run | What it checks |
|---|---|---|
| `python3 tools/lint-skill-spec.py` | Before every PR | Top-level key whitelist, description syntax, `allowed-tools` shape, `evals/` structure — on source under `packs/` |
| `python3 tools/lint-agent-artifacts.py` | After `make build-self` | Spec-compliant shape preserved across all adapter projections |
| `security-checklists` skill, agentic-skills module | During adversarial review and skill assimilation | Full AST01–AST10 check reference |

The linters are the mechanical authority.
Where this page conflicts with the linters or the specification at agentskills.io, the linters and the upstream spec are correct.
