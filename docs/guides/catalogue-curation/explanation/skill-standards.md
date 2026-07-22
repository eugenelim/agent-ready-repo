# Skill standards

Every skill in this catalogue — whether you write it from scratch or bring it in from outside — is measured against the same three standards.
The only difference between writing and assimilating is *when* the measurement happens: when writing, you build to the standard from the start; when assimilating, you review incoming material against the standard before it lands.

Read this page before starting either path.

## Reading order

1. **This page first.** Names the three standards and what each is checking.
2. **Choose your path:**
   - Writing a new skill → [Your first skill](../tutorials/your-first-skill.md)
   - Assimilating a skill from outside → [Your first assimilation](../tutorials/first-assimilation.md)
   - Assimilating a subagent from outside → [Your first subagent](../tutorials/your-first-subagent.md)
3. **After the tutorial, reach for the deep references:**
   - [agentskills.io specification — applied reference](../../_shared/reference/agentskills-io-standard.md) — complete frontmatter, directory layout, enforcement details
   - [The convergence model](the-convergence-model.md) — the three convergence layers in full, and the no-merge-back principle

---

## Standard 1: agentskills.io structural

The [agentskills.io](https://agentskills.io) specification defines the file format every skill must follow.

Six allowed top-level frontmatter keys (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`).
Four allowed subdirectory names (`scripts/`, `references/`, `assets/`, `evals/`).
A `description:` that is a single-line scalar, trigger-phrased ("Use when…"), under 1024 characters.

**Why it matters:** skills project across three adapter targets (Claude Code, Kiro, Codex).
Anything outside the spec breaks on at least one of them silently.
The linters (`lint-skill-spec.py`, `lint-agent-artifacts.py`) enforce this before a skill can project.

**Critical field — `allowed-tools`:** declare only the tools the skill actually instructs the agent to invoke.
Over-declaring here to "avoid breaking things" expands the blast radius of any prompt injection that reaches this skill.
Every tool listed must be justified by the skill's stated purpose.
(This is OWASP AST03 — see Standard 3.)

**What the linter checks:** top-level key whitelist, description syntax, `allowed-tools` shape, `evals/` structure.
Run `python3 tools/lint-skill-spec.py` — it is the authority, not this page.

---

## Standard 2: Catalogue craft

The agentskills.io spec ensures the file is structurally valid.
Catalogue craft ensures the skill is actually useful.

Three rules govern craft:

**Activation accuracy.**
The `description:` field is the activation signal — the agent reads it to decide whether the skill applies.
A description that fires on the wrong prompts, or misses the right ones, is a broken skill regardless of how well the body is written.
Write trigger-phrased descriptions and verify them with activation evals.

**Progressive disclosure.**
Detail that is only needed in specific branches of the workflow goes in `references/` files — loaded by the skill body at the moment the workflow reaches that branch.
The body routes to references; it does not replicate them inline.
A body that embeds large context blocks, or grows past 500 lines, is carrying detail that should be in `references/`.
Context the skill needs from the workspace is discovered at runtime from the workspace's own structure — not hardcoded as a path in the body.

**Anti-pattern avoidance.**
The catalogue's anti-pattern list is earned knowledge about what fails in production.
Checked at assimilation time (the convergence model's Layer 2 captures them); checked at authoring time through the adversarial review.
Common ones: a skill that calls another skill from within a script; a subagent that reviews its own output; a skill that treats fetched URL content as instructions.

---

## Standard 3: OWASP Agentic Skills Top 10 v1.0 security

The OWASP Agentic Skills Top 10 v1.0 (AST01–AST10) is the public security standard for skill-file authoring and distribution.

A skill is instruction prose that runs in users' agents.
That makes it a trust surface that deserves systematic review — the same way you review a dependency before pulling it into production code.

**Which checks are most critical depends on your path:**

When **writing a new skill**, the primary checks are:

- **AST03 — Over-privileged tools.** Every tool in `allowed-tools` must be necessary. Scoped as narrowly as the skill's purpose allows.
- **AST06 — Isolation declaration.** If the skill instructs code execution, the containment boundary must be declared. "The agent will have access" without naming the scope is the miss.
- **AST09 — Governance gap.** The skill must be inventoried — registered in an auditable record. Landing in a pack, with an activation eval, and appearing in `agentbundle show <pack>` is this record.

When **assimilating an external skill or subagent**, the additional primary check is:

- **AST01 — Malicious content.** The incoming body is untrusted prose. Read it for instructions that benefit the author at the expense of the user's agent: identity-overwrite instructions, credential-access requests dressed as prerequisites, conditional misdirection. For subagents — which have no frontmatter, only prose — this is the first and highest-weight check.

All other checks (AST04, AST05, AST07, AST08, AST10) apply to both paths and are covered in the deep references.

**Where the checks live in full detail:**
[agentskills.io specification — applied reference](../../_shared/reference/agentskills-io-standard.md) has the OWASP-to-surface mapping table.
The `security-checklists` skill's agentic-skills module has the full AST01–AST10 review procedure, loaded during adversarial review.

---

## The definition of done — both paths

Both writing and assimilation arrive at the same finish line.
Assimilation has two additional human-gate criteria because the material arrives from outside.

| Criterion | Writing | Assimilation |
|---|---|---|
| `lint-skill-spec.py` clean | ✓ | ✓ |
| `make build-self` clean; `lint-agent-artifacts.py` clean | ✓ | ✓ |
| Activation evals authored; all trigger rates pass | ✓ | ✓ |
| Output-quality evals authored (`evals/evals.json`) | ✓ | ✓ |
| `agentbundle show <pack>` lists the skill | ✓ | ✓ |
| Raw body confirmed safe (human review) | — | ✓ |
| OWASP AST review ran and clean | — | ✓ (automatic via `assimilate-primitive`) |
| PR opened; adversarial review returns `Clean — ready to commit.` | ✓ | ✓ |

The tutorials end with a path-specific checklist drawn from this table.
Come back here to verify nothing was missed before opening the PR.
