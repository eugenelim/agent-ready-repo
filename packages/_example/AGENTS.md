# AGENTS.md (package: `_example`)

> Per-package agent context. The root `AGENTS.md` already covers monorepo-wide
> conventions — don't repeat them here. Only put things specific to this package.

## What this package is

<!-- One sentence. Replace this. -->
This is a placeholder package showing the per-package AGENTS.md pattern.

## Public surface

<!--
What does this package export? What's internal vs. external? Be specific
about what counts as a "public" interface — those are the things changes
need to be coordinated with consumers.

- Public: everything in `src/index.<ext>`
- Internal: everything under `src/internal/`
- Tests: under `tests/`, do not import from any other package's `src/internal/`
-->

## Constraints particular to this package

<!--
Things an agent would otherwise have to discover by reading the code:

- Targets <runtime> version <X>.
- Avoids <dependency Y> for <reason>.
- Performance budget: <metric> under <threshold>.
- Backward compatibility window: <duration> for the public API.
-->

## How to test this package

<!--
If the test command differs from the monorepo default, document it here.
Otherwise omit this section.
-->

## When changes here need an ADR

<!--
Some packages have heightened sensitivity — auth packages, data layer,
public SDKs. If this is one of those, list the categories of change that
trigger an ADR.

Example:
- Any change to the wire format requires an ADR.
- Any new dependency with non-MIT/Apache license requires an ADR.
-->
