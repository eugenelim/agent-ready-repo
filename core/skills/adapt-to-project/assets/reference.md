# Reference architecture

> **Normative.** This document is your repo's *golden path* — the stack, the
> internal building blocks, the component stereotypes, and the cross-cutting
> standards that new work is expected to **conform to**. A feature's low-level
> design (in its plan) reads this as steering: it names which building blocks it
> reuses and which standards it follows, and it justifies any deviation.
>
> This is the **normative** sibling of `overview.md`. `overview.md` *describes*
> how the code is organized today (a map you read to find things);
> `reference.md` *prescribes* how new code should be shaped (a target you build
> toward). When the two disagree, that gap is either drift to fix or a decision
> to record.
>
> **Fill this in only when you have real architecture decisions to record.** A
> thin or early-stage repo has no golden path yet — leave the template
> un-instantiated rather than inventing constraints nobody agreed to. Add a
> section when a decision becomes real; delete guidance prompts as you replace
> them with your repo's actual answers. Every claim here should be one a
> reviewer could hold a pull request to.

<!--
  This is an arc42-shaped template (sections 2, 4, 5, 8 — the four that carry
  normative steering). Replace each prompt with your repo's real answer, or
  remove the section if the decision genuinely doesn't exist yet. Keep it
  stack-neutral in the template; your filled-in copy names your actual stack.
-->

## Constraints

*What the architecture must respect, no matter the feature.* The boundaries
that are not up for negotiation in a normal change: the languages and runtimes
in play, the platforms you must support, regulatory or contractual obligations,
performance or availability targets, and the team conventions that outrank
local preference.

- **Technical constraints.** <Runtimes, language versions, platforms, and
  hard external dependencies every component lives within. Name the
  **managed-runtime or deployment platform** you target (the serverless
  runtime, the orchestrator, the managed service) — the work-loop infra
  preflight reads this as a starting coordinate rather than rediscovering it.>
- **Organizational / process constraints.** <Conventions, review rules,
  release cadence, or compliance obligations that shape how code is built.>
- **Constraints you cannot change here.** <Anything a single feature must work
  around rather than revisit — call it out so designs don't fight it.>

## Solution strategy

*The top-level approach — the few decisions that explain most of the codebase.*
The architectural style and the key technology choices, each with the one-line
reason it won. This is the section a new contributor reads first to understand
"how we build things here."

- **Architectural style.** <The dominant shape — e.g. how the system is
  partitioned, how components communicate, where state lives — and why.>
- **Key technology decisions.** <The load-bearing choices: framework, data
  store, transport, build tooling. One line each on *what* and *why this over
  the obvious alternative*. Where a choice carries a **framework- or
  library-level contract** new work must honour — the entrypoint / packaging
  model, a required base class or decorator, a config-loading convention — name
  that contract here so a design conforms to it instead of guessing it.>
- **Quality-goal strategy.** <For each top-priority quality (e.g. throughput,
  recoverability, security posture), the architectural move that delivers it.>

## Building-block view / component catalogue

*The reusable internal building blocks and the component stereotypes new code
is expected to reuse rather than reinvent.* This is the heart of the golden
path: when a design needs a thing this project already names, it uses that
thing. Reach for something new only with a recorded reason.

- **Component stereotypes.** <The recurring *kinds* of component in this repo
  and the responsibility each owns — e.g. "an X handles inbound requests, a Y
  owns persistence, a Z is a pure transform." Name the stereotype so designs
  can say "this is a new Y" and inherit its rules.>
- **Reusable building blocks.** <The shared internal libraries, base types,
  clients, and utilities a feature should reach for first. Name each and what
  it's for, so a design references it instead of writing a parallel one.>
- **Composition rules.** <How the blocks fit together — allowed dependency
  directions, what may call what, where a boundary must not be crossed.>

## Crosscutting concepts / standards

*The standards every component conforms to, regardless of what it does.* These
are the concerns that, left to each feature's discretion, drift into N
incompatible implementations. Naming them once here makes "follow the standard"
the default and "deviate" the thing that needs justifying.

- **Error handling.** <How errors are raised, wrapped, surfaced, and logged —
  the one shape all components use.>
- **Observability.** <Logging, metrics, and tracing conventions: what gets
  recorded, in what shape, at what boundary — and *where* the logs and metrics
  surface for a deployed change (the dashboard, the log group), so a verifier
  knows where to read ground truth.>
- **Security & data handling.** <Authn/authz approach, secret handling, input
  validation at trust boundaries, data-classification rules.>
- **Configuration & environments.** <How configuration is supplied and
  validated; what differs across environments and what must not.>
- **Testing standards.** <The expected test shape per component stereotype —
  what's unit-tested, what's contract-tested, what's verified end-to-end — and
  **where the verification tooling lives**: the smoke / verify-status check, the
  deploy and teardown harness, the test-data seeding (the commands their
  one-liners live under in `AGENTS.md`). Naming where they live lets the
  work-loop infra preflight seed acquisition from them instead of cold.>
