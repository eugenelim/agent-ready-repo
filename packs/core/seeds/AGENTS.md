# AGENTS.md

> This is the canonical agent context file. Replace the marked project and
> command details with verified repository facts. Preserve equivalent existing
> sources and keep subtree-specific deltas in the nearest scoped `AGENTS.md`.

## Project overview

This is <project-name>—<one-line description of what it does and for whom>.

Link the repository's existing architecture or design source here when one
exists. Do not relocate it to match a pack convention.

## Development workflow

Follow the repository's existing contributor workflow. Use the `work-loop`
skill for repository changes when installed; it owns planning, verification,
review, and recovery.

If the repository has `CONTRIBUTING.md` or equivalent guidance, link to it here.
If it has none, the seeded [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md) is an
optional starting point to adopt with maintainer approval, not an authority that
outranks existing guidance.

## Build and test commands

```bash
<install command>
<test command>
<lint command>
<build command>
```

Use commands verified from repository guidance, manifests, task runners, or CI.
Do not guess them from the detected language alone.

## Coding conventions

Follow documented repository conventions and the nearest scoped `AGENTS.md`.
When no documented rule exists, use repository-owned framework primitives as
the strongest evidence. Two matching production examples may guide a proposal;
one nearby example must not become a rule.

<!--
Recommended additional guidance — add only after verifying its trigger. Each
option should link to the owning source instead of copying its rules.

- `Documentation` — trigger: two or more authoritative sources need routing.
  Benefit: agents can find architecture, decisions, and contributor guidance
  without imposing a new document layout.
- `Security considerations` — trigger: security/privacy boundaries, sanctioned
  helpers, sensitive-data rules, or an external quality gate change behavior.
  Benefit: agents use the repository's approved controls.
- `Scoped instructions` — trigger: existing scoped files or a subtree has
  materially different commands, ownership, generated sources, or rules.
  Benefit: agents load action-changing deltas only where they apply.
- `Repository structure` — trigger: ownership or change boundaries are not
  obvious, such as generated projections, multiple build roots, or unusual test
  ownership. Benefit: agents see responsibility and change guidance without a
  generic directory tree.

Omit every additional section whose content is not verified.
-->
