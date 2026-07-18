# Charter

> The foundational document for this project. One page, read whole.
> Modeled on the [CNCF project charter pattern](https://contribute.cncf.io/maintainers/governance/charter/):
> mission, scope, and principles in a single place, kept stable and short.

Changes to this file go through an RFC. The rest of the docs in this repo
are scaffolding around it; this file is the why.

---

## Mission

AI coding agents are getting good enough to do real engineering work, and
the work goes better when the repo is set up for them — with a context
anchor they actually use, documentation they can navigate, conventions
that hold up at scale, and reviewers that catch what they miss. Most
repos aren't built that way; this catalogue is an attempt to build one.

## Scope

What this project does:

- Works for any project — service, library, platform — and scales from
  solo developer up to a team of fifty. The shape of the repo stays the
  same; what changes with scale is the amount of process carried.
- Ships agent-context (`AGENTS.md`), documentation hierarchy (charter,
  ADR, RFC, spec, plan, architecture, product, guides), a tight
  spec-and-plan loop, an explicit work loop with stop conditions, three
  review lenses (adversarial, security, quality), a bug-fix discipline,
  and travelling skills that install into adopter projects via Claude
  Code plugins, APM, or the `agentbundle` CLI.
- Self-hosts: linters check the disciplines, CI gates them, and the
  catalogue's build pipeline projects the bundled primitives onto this
  repo so what we ship to adopters and what we run ourselves cannot
  diverge by construction.
- Ships opt-in **tech-stack accelerator packs** for common infrastructure
  tooling, CI/CD platforms, and SaaS integrations — ready-to-run
  scaffolding for adopters who have already chosen a stack, not a
  prescription for those who haven't. Each accelerator pack clears the
  four principles below, plus: a named maintainer, a stated maturity
  scope (validated / contract-complete / experimental), and an
  archiving/deprecation path. The `iac-terraform` pack is the
  establishing precedent; future packs are judged against it.

What this project does **not** do:

- **Not a marketplace of specialized agents.** Three reviewers is the
  ceiling. New skills earn a place by clearing the four principles
  below; most candidates fail at least one.
- **Not prescriptive about tech-stack choices through the default install.**
  Frontend, backend, agentic, CLI, mobile, data — the core structure works
  for any of them. Opt-in accelerator packs (above) are tech-stack-specific
  by design; they serve adopters who have already picked a stack and want
  governed scaffolding for it. What this project never does is impose a
  stack choice through the default install or make core doctrine contingent
  on a specific framework.
- **Not a single-tool template.** `AGENTS.md` is the open format. Tools
  that read it natively (Cursor, Codex, Gemini CLI, Copilot) get the
  universal layer immediately; tools with their own primitives (Claude
  Code hooks, custom subagents) layer those on top.

The "does not" list is at least as important as the "does" list. It's
how we — and AI agents working in the repo — know when a request is
out of bounds. If you find the project being asked to do things that
aren't on either list, that's a signal to refine this section, not to
drift.

## Principles

Every artifact in the catalogue earns its place by clearing the same
four bars. These are the canonical principles referenced everywhere
else in this repo when we discuss what to add and what to refuse.

1. **Universal across tech stacks (core layer).** The core works for any
   adopter, not just a specific framework or language. Opt-in accelerator
   packs are tech-stack-specific by design — their specificity is the point;
   they clear the remaining three principles instead of this one.
2. **Substantive, not duplicative.** Adds what the template doesn't
   already encode somewhere.
3. **A habit, not a tool.** Captures a way of working, not a piece of
   infrastructure.
4. **Used often enough to stick.** Reached for regularly, not once a
   year and forgotten.

Most proposed additions don't clear all four. That's the point.

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
