# The approach behind agent-ready-repo

The thinking that shaped how this template is built, what's in it, and what we chose to leave out.

## The four principles for what we keep

Every artifact in the template earns its place by clearing the same four bars. These are the canonical principles referenced everywhere else in this repo when we discuss what to add and what to refuse.

1. **Universal across tech stacks.** Works for any adopter, not just a specific framework or language.
2. **Substantive, not duplicative.** Adds what the template doesn't already encode somewhere.
3. **A habit, not a tool.** Captures a way of working, not a piece of infrastructure.
4. **Used often enough to stick.** Reached for regularly, not once a year and forgotten.

Most proposed additions don't clear all four. That's the point.

## The wager

AI coding agents are getting good enough to do real engineering work. The work goes better, though, when the repo is set up for them: a context anchor they actually use, documentation they can navigate, conventions that hold up at scale, and reviewers that catch what they miss. Most repos aren't built that way. This template is an attempt to build one.

It works for any project — service, library, platform — and scales from solo developer up to a team of fifty. What changes with scale is the amount of process you carry; the shape of the repo stays the same.

## What's inside (and why)

`AGENTS.md` is the first thing any coding agent reads when it starts work in your repo. We keep it under 250 lines and lint it in CI, because the discipline matters: recent research found that hand-curated context files measurably lift agent task success, while auto-generated ones make things worse. `CLAUDE.md` is a symlink to the same file, and other tools — Cursor, Codex, Gemini CLI, Copilot — read it natively.

Documentation has eight homes (charter, ADR, RFC, spec, plan, architecture, product, guides), and each one carries a lifecycle. Living documents update with each PR. Frozen documents like accepted ADRs are immutable; CI rejects silent edits. Governance documents move through review. The effect is that nobody — agent or human — has to wonder where a piece of information belongs.

Features go through a spec-and-plan loop tight enough to drive implementation. Specs and plans are written together, Acceptance Criteria are written before any code, and each plan task points back to a specific criterion in the spec. The spec-author skill helps you sharpen vague objectives into testable criteria early, so the work doesn't drift later.

The work loop — plan, execute, verify with gates, review, decide — has explicit stop conditions: an iteration cap, a "same finding twice" rule, signals for when you're patching symptoms rather than addressing root cause. These matter because coding agents are good at starting work and less good at recognizing when to stop.

Three review lenses cover the rest. The adversarial reviewer reads the diff against the spec and catches drift, scope creep, and missed edge cases. The security reviewer applies OWASP and STRIDE thinking, and stays honest about what it didn't check. The quality engineer looks at the cost of living with the code over the next two years — testability, observability, reliability, maintainability. Three lenses are enough to cover what matters, and we made that the ceiling by design.

There's also a bug-fix discipline worth knowing about. Reproduce first; write a failing test that pins the actual contract being violated; trace where the defect lives and grep for sibling cases; keep the diff minimum; verify you've fixed the root rather than the symptom; document the reasoning in the commit body. If your team uses a tracker, loop back to it when the PR lands.

Skills travel. The workflows under `.claude/skills/` aren't template-only — `tools/install-skill.py` copies a skill and its declared dependency closure into any other repo. The rule that makes this work: skill bodies don't read specific content from adopter-owned files (`AGENTS.md`, `docs/CONVENTIONS.md`, `docs/CHARTER.md`). They reference shape ("your project's lint command, wherever you document it") or read what's there at runtime. That's why the three reviewer agents declare `dependencies: []` even while telling the agent to read AGENTS.md first — the contract is that an AGENTS.md exists, not that ours does. `tools/lint-skill-deps.py` enforces the constraint so it doesn't drift back in.

Everything above scales without restructuring. Three profiles — microservice, library, medium platform — share the same structure. A small project skips the cross-team governance pieces; a larger one picks them up later without moving anything around. And these disciplines aren't only written down: linters check them, CI gates them, and the bootstrap script has its own self-test so the template doesn't quietly drift over time.

## What we left out, on purpose

This is not a marketplace of specialized agents. Three reviewers is the ceiling. New skills earn a place by clearing the four principles above: universal across tech stacks, substantive rather than duplicative, a habit rather than a tool, used often enough to stick. Most candidates fail at least one of those.

It is not a framework that picks your tech stack. Frontend, backend, agentic, CLI, mobile, data — the structure works for any of them. The conventions are aware of architectural layers (API, UI, CLI, agentic) but never of specific frameworks.

And it is not a single-tool template. AGENTS.md is the open format. Tools that read it natively get the universal layer immediately. Tools with their own primitives — Claude Code hooks, custom subagents — layer those on top.

## Why this shape rather than the alternatives

Two approaches dominate the agent-ready-repo space right now. One is a large catalog of specialized agents and skills, which adopters pick from. The other is to live inside a specific IDE that bundles agent capabilities into the editor. Both can work, and both have known costs: catalogs grow until nobody remembers what's in them, and IDE-bundled workflows go away when you change tools.

This template takes a different bet — most of its value is in what it leaves out. Every artifact earned its place by clearing the four principles above. The proposals we passed on were measured the same way; the gap report under `.context/` keeps the record of what we kept, what we declined, and why. That trail is what makes the rules trustworthy as the project grows.
