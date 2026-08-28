# AGENTS.md

> This is the canonical agent context file. Replace the marked project and
> command details with verified repository facts. Preserve equivalent existing
> sources and keep subtree-specific deltas in the nearest scoped `AGENTS.md`.

## Project overview

This is <project-name>—<one-line description of what it does and for whom>.

Link the repository's existing architecture or design source here when one
exists. Do not relocate it to match a pack convention.

## Rule lookups

Before your first user-facing response or unrelated tool call, silently read [`AGENT_RULES.md`](AGENT_RULES.md), then every `always` rule and every conditional rule there that matches the work.

For work under `docs/`, also read the scoped [`docs/AGENTS.md`](docs/AGENTS.md).

Read both lookup files with one bounded, repository-confined operation that rejects links, reparse points, non-regular files, multiple links, oversized files, and identity changes while opening. If the host loaded a file before agent control, do not claim this check covered the host load.

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

### Cut before adding

After understanding the code a change touches, stop at the first sufficient
rung:

1. If the requested addition is not genuinely needed, skip it and say so once.
2. Search once, within the current decision boundary, for an adequate existing
   repository solution; reuse a hit or move on after a decisive empty result.
3. Prefer the standard library when it satisfies the outcome.
4. Prefer a native platform capability when it satisfies the outcome.
5. Prefer an already-installed dependency when it satisfies the outcome; an
   import absent from the owning manifest is a new dependency.
6. Use one obvious line when it is the complete, maintainable solution.
7. Otherwise write the minimum correct solution in the fewest statements and
   files that preserve ownership and tests.

Prefer the obvious solution, not merely the shortest text. The bounded search
in rung 2 limits discovery, not verification: do not ignore contradictory
evidence, freshness-sensitive facts, required gates, or correctness review.

Never cut validation at a trust boundary; error handling that prevents data
loss; security or privacy controls; accessibility; an explicit accepted
requirement; required tests, migrations, documentation, or human approval; or
a policy or platform restriction the user cannot waive.

Delete claims that do not affect the accepted outcome. Before stating a
necessary claim about a named repository target as fact, perform one bounded
read or search of that target. If it remains ungrounded, label it as an
assumption or a condition to discover during the work.

Lead with the useful outcome and omit routine tool narration. Preserve required
interactive updates, and end a completion receipt with changed state,
verification, and remaining work.

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
