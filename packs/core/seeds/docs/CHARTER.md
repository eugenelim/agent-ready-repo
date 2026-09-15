# Charter

> The foundational document for this project. One page, read whole.
> Modeled on the [CNCF project charter pattern](https://contribute.cncf.io/maintainers/governance/charter/):
> mission, scope, and principles in a single place, kept stable and short.

Changes to this file go through an RFC. The rest of the docs in this repo
are scaffolding around it; this file is the why.

---

## Mission

<!-- One sentence. What this project is, in language anyone could understand.
     Example: "A monorepo template that helps small-to-medium teams ship
     faster by giving Claude Code and other AI agents the structure they
     need to be reliable contributors." -->

<replace with one sentence>

## Scope

What this project does:

- <bullet>
- <bullet>

What this project does **not** do:

- <bullet>
- <bullet>

The "does not" list is at least as important as the "does" list. It's how
we — and AI agents working in the repo — know when a request is out of
bounds. If you find the project being asked to do things that aren't on
either list, that's a signal to refine this section, not to drift.

## Principles

The values that resolve ties when reasonable people disagree. Five to
seven, no more.

1. **<principle>.** <one-sentence elaboration with a concrete example of
   how we've applied it.>
2. **<principle>.** ...
3. **<principle>.** ...
4. **<principle>.** ...
5. **<principle>.** ...

## What's NOT in this charter

To keep this file from becoming everything-and-the-kitchen-sink:

- **Decision history** lives in [`adr/`](adr/). The charter is what we
  believe; ADRs are the choices we made because of those beliefs.
- **Current product state** lives in [`product/`](product/). The charter
  is direction; product/ is where we are.
- **Current architecture state** lives in [`architecture/`](architecture/).
- **Conventions for how we work** live in [`CONVENTIONS.md`](CONVENTIONS.md).
- **Governance** (roles, decision-making processes, voting) lives in
  [`GOVERNANCE.md`](GOVERNANCE.md) if and when the project is large
  enough to need it. Most small/medium projects don't — a single
  maintainer or small group operating by consensus is fine, and forcing
  governance ceremony on a project that doesn't need it produces theater,
  not clarity.

## When to revise

Revise this charter when:

- The mission has actually changed (rare — usually means a fork).
- The scope has shifted enough that PRs are routinely landing for things
  the current scope doesn't cover.
- A principle has stopped resolving ties — it's being ignored, or it
  contradicts another principle in ways we haven't acknowledged.

Revise via RFC. Editing the charter directly without discussion is the
single fastest way to lose the trust this document is meant to build.

## What a charter revision needs

**What:** one page. Mission, scope, and principles. The foundational
document. Modeled on the [CNCF charter pattern](https://contribute.cncf.io/maintainers/governance/charter/).

**Lifecycle:** living, but rarely changed. Mission, scope, and foundational-principle
changes are reserved; wording, clarification, examples, typos, broken links, and
accepted decisions are normal PRs regardless of pathname.

**What goes here:**

- **Mission.** One sentence. What the project is, in language anyone
  could understand.
- **Scope.** What the project does, and — equally important — what it
  doesn't. The "doesn't" list is what tells contributors and agents when
  a request is out of bounds.
- **Principles.** Five to seven values that resolve ties. Each principle
  has a one-sentence elaboration with a concrete example.

**What does NOT go here:**

- Decision history → ADRs.
- Current product state → `product/`.
- Roles, voting, decision-making → `GOVERNANCE.md`, *if* the project is
  large enough to need one.
- A glossary → `guides/reference/`. Vocabulary is reference material.

**On governance docs:** small and medium projects don't need a separate
`GOVERNANCE.md`. A maintainer or small group operating by consensus is
fine. Add governance documentation when there are roles, decision
procedures, or election processes worth writing down — typically when
the project has external contributors who need clarity on how to gain
authority. Forcing governance ceremony on a project that doesn't need
it produces theater, not clarity.
