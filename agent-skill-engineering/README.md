# Agent Skill Engineering

Frame a portable skill before writing it, create or update it under an explicit
write boundary, or review it before making a measured optimization. You receive
a bounded plan or a verified skill change without handing repository content
authority over your tools.

## Start here

| Say this | What you get |
| --- | --- |
| “Frame a skill for reviewing database migrations. Don't write files yet.” | A read-only frame — activation boundary, outcome, authority, file surface, evaluations, non-goals — through `author-or-update-agent-skill` |
| “Create that skill.” / “Update this SKILL.md.” | The smallest portable change to a confined target, after you authorize the write |
| “Review this skill for trigger precision and portability.” | A findings report by stable check id, read-only, through `review-or-optimize-agent-skill` |
| “Optimize it against the false-positive rate I measured.” | A measured before/after change — only with an observed failure or baseline, and a separate authorization |

New or changed skill **content** is the authoring workflow. Judging a skill, or
repairing a defect a review **measured**, is the review workflow — optimization
changes files too, which is why the split is what you are starting from rather
than what you end up with.

The generated `ase-okf-reference` skill is an internal knowledge router. You do
not invoke it directly; the two workflows load only the concepts their current
question needs.

Framing returns a plan, not files:

```text
Mode: frame
Write status: not authorized
Activation: "review the migrations on this branch" / not "write me a migration"
Outcome: a ranked findings report with severity and remediation
Non-goals: authoring migrations, running them
```

Review returns findings against stable check ids:

```text
Mode: review (read-only)

ASE-DET-01  Determinism and exit contract  — Blocker
  Evidence:    helper embeds datetime.now(); no declared inputs or exit classes
  Consequence: identical inputs produce different managed output
  Smallest fix: take the timestamp as an argument and declare the exit classes

… 9 further checks reported, each applicable or explicitly not applicable
Unexecuted: nondeterministic-helper.py — reported as a coverage gap, not run
```

Optimization is available only after an observed failure or measured baseline
and a separate, explicit write transition. The result includes before-and-after
verification.

After framing, your next decision is whether to authorize `create` or `update`.
After review, decide whether a measured defect warrants `optimize` or should
remain a reported finding.

## Install

```bash
agentbundle install --pack agent-skill-engineering --scope user
```

Or, through the Claude plugin marketplace:

```bash
claude plugin install agent-skill-engineering@agent-ready-repo
```

Adapters: `claude-code`, `codex`, `copilot`, `kiro-ide`, `kiro-cli`, `cursor`,
`gemini`. Default scope: user; repo scope is also allowed.

## What the pack reads and changes

Both user-facing workflows can read untrusted candidate files after resolving
and confining each path. Both declare a write boundary because their explicit
mutation modes may change the confirmed skill root; activation alone never
authorizes a write. The generated reference router is read-only, is never
selected on its own, and answers no request directly.

The workflows never inspect credentials. Authentication stays outside model
context and any later authenticated operation must use an external
least-authority mechanism.

## Knowledge grounding

Three governed foundation topics cover trigger quality, progressive disclosure,
and deterministic resource and script contracts. The committed reference skill
is compiler-generated; raw OKF remains same-pack build input and is not a
runtime lookup surface.

Direct repository authorities such as effective `AGENTS.md`, declared
standards, and architecture decisions keep their normal routing. When an
independent organization, framework, architecture, or agent-skills knowledge
provider is exposed, the workflows validate its public capability metadata and
invoke it explicitly. Missing, ambiguous, stale, or invalid providers produce
one bounded diagnostic and leave the baseline workflow available. The
workflows never crawl another pack's raw corpus.

## Foundation limits

The foundation recognizes Python/pytest and TypeScript/Node as future extension
families but ships no language-specific guidance. Provider authoring, runtime
packaging, runtime profiles, plugins, hooks, subagents, installation,
projection, publication, and catalogue governance belong to later slices or
external delivery tooling.
