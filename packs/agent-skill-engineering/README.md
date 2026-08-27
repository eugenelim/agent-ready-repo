# Agent Skill Engineering

Frame a portable skill before writing it, create or update it under an explicit
write boundary, or review it before making a measured optimization. You receive
a bounded plan or a verified skill change without handing repository content
authority over your tools.

Start with an ordinary request:

```text
Help me frame a new skill for reviewing database migrations. Do not write files yet.
```

The authoring workflow starts in read-only `frame` mode. It names activation
prompts and near misses, the portable file surface, authority, resources,
evaluations, and non-goals. Ask it to enter `create` or `update` only when you
want the confirmed target changed.

For an existing skill, start with:

```text
Review this agent skill for trigger precision, progressive disclosure, script
failure behavior, portability, and authority. Keep the review read-only.
```

Review reports applicable checks and evidence. Optimization is available only
after an observed failure or measured baseline and a separate, explicit write
transition. The result includes before-and-after verification.

## What the pack reads and changes

Both user-facing workflows can read untrusted candidate files after resolving
and confining each path. Both declare a write boundary because their explicit
mutation modes may change the confirmed skill root; activation alone never
authorizes a write. The generated reference router is read-only.

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

After framing, your next decision is whether to authorize `create` or `update`.
After review, decide whether a measured defect warrants `optimize` or should
remain a reported finding.

