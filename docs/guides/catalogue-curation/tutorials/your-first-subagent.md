# Your first subagent assimilation

**What you'll build:** One external subagent definition adopted into the catalogue — OWASP AST-reviewed with subagent-specific emphasis, shaped to catalogue convention, and verified.
**Prerequisites:** The `catalogue-curation` pack installed (requires `core` + `governance-extras`); read [Skill standards](../explanation/skill-standards.md), especially Standard 3.
**Time:** 30–45 minutes.

**Goal:** bring one external subagent definition into the catalogue safely, with the right security emphasis.
By the end you'll have seen how a subagent assimilation differs from a skill assimilation and where the OWASP AST review shifts focus.

**Before you start.** Read [Skill standards](../explanation/skill-standards.md) — specifically Standard 3 (OWASP AST) and the definition-of-done table.
When assimilating a subagent, Standard 3 applies with the most weight of any primitive type.
A subagent has no frontmatter to validate — the body is the entire security surface.

You need the `catalogue-curation` pack installed (it requires `core` + `governance-extras`).

## 1. How a subagent differs from a skill

A skill has a YAML frontmatter block with a `description:` field.
That field is the activation signal — the agent reads it to decide whether the skill applies to the user's prompt.

A subagent is instruction prose with no frontmatter activation description.
It is dispatched by a skill or directly by the user — not selected by an activation match.
There is no description to tune and no frontmatter to validate.
The body IS the security surface.

The `assimilate-primitive` skill handles both.
Point it at a subagent definition the same way you would a skill:

> Assimilate the subagent at `https://github.com/some-org/their-repo/agents/review-agent.md` into our catalogue.

## 2. Point at the source

The fetch uses the same guardrails as skill assimilation: HTTPS or git schemes only.
A `file:` URL, a private metadata address, or a non-allowlisted scheme is refused before anything is read.

## 3. Read the raw content — this is the primary security gate

The skill shows you the **raw fetched body, verbatim**.
Do not skim it.

For a skill, the frontmatter gives you a structured surface to review: `allowed-tools` lists what the skill touches, `metadata:` declares the boundary type.
For a subagent, every sentence is a potential instruction your agent will follow.
Read the body with one question in mind: *does any of this benefit the author at the expense of me or my users?*

The OWASP Agentic Skills Top 10 v1.0 review runs on the body with shifted emphasis:

**AST01 — Malicious instruction prose.**
This is the highest-weight check for subagents precisely because there is no metadata to validate separately.
Look for: identity-overwrite instructions ("update your SOUL.md with…"), credential-access requests dressed as prerequisites, conditional misdirection ("if no user is present, also do X").
These are found in prose, not in frontmatter.

**AST03 — Tool grant breadth.**
A subagent may instruct the agent to use a broad set of tools.
Every tool the subagent instructs the agent to invoke must be necessary for its stated purpose.
A subagent that requests file-write, shell-exec, and network access for a task that only needs read access is over-granted — flag it and reshape or reject.

**AST06 — Isolation.**
A subagent that instructs code execution without naming a containment boundary is a finding.
The body must declare: what filesystem scope it operates in, what network access it needs, and whether it spawns further agents.
Containment must be declared, not implied by the caller's context.

Two anti-patterns the skill also checks for:

**Skill-vs-agent confusion.**
A subagent that runs a step-by-step interactive workflow with user decision points is the wrong primitive.
Skills are for interactive, activation-driven workflows.
Subagents are dispatched for bounded, non-interactive sub-tasks.
If the external definition is really a skill in agent clothing, the assimilation skill will propose reshaping it as a skill instead.

**Self-review.**
A subagent instructed to evaluate or review its own output is an anti-pattern.
Self-review produces unreliable results and is a common failure mode in poorly-designed agent definitions.
Reshape or reject.

## 4. Shape to catalogue convention

Once accepted as safe, the skill reshapes the definition.
For subagents, shaping means:

**Opening paragraph.**
The opening paragraph of the agent file must state clearly what the subagent does, what it does not do, and what dispatches it.
There is no `description:` frontmatter to carry this — the prose opening is the only context a caller or reviewer has.

**Tool grant minimisation.**
Tool grants in the body are minimised to what the subagent's stated purpose requires.
Any grant not justified by the stated purpose is removed.

**Path discipline.**
Any absolute paths or hardcoded workspace locations in the original are replaced with relative paths or runtime context-discovery patterns.
The subagent reads workspace structure at runtime from the workspace's own standard locations — it does not rely on paths that are only valid in the origin repo or a particular org's environment.
This is what makes the subagent portable: any workspace that has the pack installed will get consistent behavior without manual path configuration.

**Landing location.**
The subagent lands in `packs/<pack>/.apm/agents/<name>.md` — one Markdown file, the agent definition, no frontmatter.

## 5. Approve and land

You see the shaped target before it is written.
Approve, and it is written through the path-jail to the destination pack.
The skill prompts you to run `make build-self` so the projection tracks the new source.

After landing, verify: the shaped file is in `packs/<pack>/.apm/agents/`, `make build-self` has run without error, and `agentbundle show <pack>` lists the new agent.

## What you just relied on

Every step had a guardrail: scheme allowlist, raw-body display before any reformatting, OWASP AST01/AST03/AST06 review with subagent-specific emphasis, skill-vs-agent confusion check, self-review anti-pattern detection, tool grant minimisation, path discipline enforcement, and the path-jail on write.

The difference between a skill assimilation and a subagent assimilation is not the mechanism — it is where the security weight falls.
For a skill, the frontmatter gives structure to review.
For a subagent, the body is the attack surface — read it as untrusted prose.

Next: understand why assimilation shapes rather than pastes — see [The convergence model](../explanation/the-convergence-model.md).
For the parallel skill flow, see [Your first assimilation](./first-assimilation.md).
