---
title: "The operating model: how work flows from idea to production"
summary: See the four stages every piece of work moves through, which packs help in each, where you decide, and why discovery, build, and release run as three separate loops.
pack: _shared
kind: explanation
---

# The operating model: how work flows from idea to production

This page shows how one piece of work moves from idea to production, which
packs help at each stage, and where you make the calls.

## The handoff chain

Follow one piece of work from idea to production and it passes through four
stages. Each stage ends when a person on your team makes a decision. The guides
call the stages *Decide what to build*, *Shape it*, *Build it*, and *Ship it*.

Most work doesn't travel the whole way. A bug fix starts at *Build it*. A small
change to an existing product often goes from a written intent straight to the
build loop.

[![Four stages, left to right: Decide what to build, which ends when you pick the outcome. Shape it, which ends when you commit to build. Build it, which ends when you merge. Ship it, which ends when you ship. Below them, architecture by stage: before any work, once per repository, architect-assess maps what exists and adapt-to-project or init-project writes reference.md, which every plan follows. Then you assess the area the work touches in Decide, design and revise the capabilities in Shape, and close-work offers to fold the design into the current-state map after the merge in Build. Ship usually needs no architecture skill. The step-by-step list further down gives the full flow in words.](the-operating-model-overview.svg)](the-operating-model-overview.svg)

Start at the stage your work is in. The gold, pointed tags are the points where
the agent stops and waits for you. The band underneath shows when you use the
architecture skills in each stage. [Where architecture comes in](#where-architecture-comes-in)
walks through it.

The full map below shows every route, step, skill, and decision, plus who runs
each stage. Select either picture to open it at full size.

[![Open the full map at full size: the architecture documents set up before any work, then every route, step, skill, and decision across the four stages. The step-by-step list and the architecture section further down give the same content in words.](the-operating-model-full-map.svg)](the-operating-model-full-map.svg)

When any piece of work finishes, or you abandon it, `close-work` from `core`
tidies it up.

### Three ways through *Shape it*

Every route through *Shape it* ends the same way: you decide the work is ready
and hand it to the build loop. They differ in how much ground they cover first.

- **The short route** is where most teams start. You write the intent, test its
  riskiest assumption, and break it into pieces the build loop can take. Plan on
  about three hours. If framing hits a question about how the system is
  built, `frame-intent` offers to shape an architecture concept before you
  break it down. If that concept changes the
  capabilities, switch to the longer route.
- **The longer route** replaces the short one with six steps: a situation,
  opportunities, options, a test of the riskiest assumption, a bet, and a
  capability map with a suggested build order. Take it when you can't yet say
  what the problem is, or when the bet is big enough that someone will ask for
  the reasoning later. Here, the capability map and the architecture go back and
  forth until you judge they've settled.
- **The supervised loop** is the right-hand column of *Shape it*. `discovery-lead`
  walks every gate, brings in design, architecture, and contract work side by
  side, and has two reviewers check for threats and reliability problems before
  you see the brief. Use it for a new product area.

[Shape what to build](../../README.md#p2--shape-what-to-build--3-hours) walks
the short and longer routes. [Walk a discovery end to end](../../product-engineering/tutorials/walk-a-discovery-end-to-end.md)
walks the supervised loop.

### Which pack does what

| Stage | What happens | Pack | What you decide |
| --- | --- | --- | --- |
| Decide what to build | Gather evidence, graded by how much you can trust it | `desk-research` | Whether the evidence is enough to act on |
| Decide what to build | Make the strategic call | `product-strategy` | Which outcome you are committing to |
| Shape it | Frame the intent and test the bet | `product-engineering` | Whether the problem is specific enough |
| Shape it | Map the journey and the screens | `experience-design` | Whether the design is ready |
| Shape it | Design the system, a subsystem, or its interfaces | `architect`, `contracts` | Whether the concept holds up |
| Shape it | Pull it together into a decision brief and a backlog | `product-engineering` | Whether to commit to build |
| Build it | Write the spec and plan, then build and review | `core` | The spec, the plan, and the merge |
| Ship it | Deploy somewhere safe, test it, and watch it run | `release-engineering` | Whether it goes to production |

A few packs don't belong to one stage. You reach for them whenever the moment
comes up:

- `code-intelligence` when you need to know what the code really does before
  you change it.
- `architect` to map what exists, keep that map current, or review a design.
  [Where architecture comes in](#where-architecture-comes-in) covers when.
- `frontend-engineering` and `iac-terraform` for UI and infrastructure work
  inside the build.
- `atlassian`, `github`, `linear`, and `figma` to pull work in from your team's
  tools and report progress back out.
- `converters` to turn PDFs, slides, and other files into text an agent can read.
- `governance-extras` to write down a decision as an ADR or RFC, at any stage.
- `product-documentation` to document what you shipped.

### If you see a gate code

The agents print a short code when they stop for you. This is what each one is
asking.

| Code | What you're deciding | Product Engineering calls it |
| --- | --- | --- |
| G0 | Is the problem real, and is this the right bet? | Approve the intent |
| G1 | Does the de-risked plan still hold? Usually automatic | |
| G1.5 | What's in the first version, and what's out? | |
| G2 | Is the decision brief good enough to build from? | Approve the decision brief |
| G3 | Are you ready to hand this to the build loop? | Commit to build |
| G4 | Is this merged change ready for release testing? | |
| G5 | Does it go to production? | |

Discovery, build, and release each have their own supervising agent:
`discovery-lead`, the `work-loop` supervisor, and `release-lead`. None of them
runs inside another. They meet at G3 and G4, and nothing crosses either line,
or reaches production at G5, until you say so.

### The same flow, step by step

This list, with [Where architecture comes in](#where-architecture-comes-in),
carries everything the pictures show, in words.

1. **Decide what to build** (optional). `desk-research` finds out what's true.
   If the bet touches a system that already exists, `architect-assess` can
   assess the area first.
   `product-strategy` makes the strategic call with skills such as
   `write-prfaq`, `run-okr-cascade`, or `define-ux-strategy`. The stage ends
   when you pick the outcome.
2. **Shape it**, by one of three routes. Each one ends at G3, when you commit
   to build.
   - *Short route, the default:* `frame-intent`, then you approve the intent
     (G0), then `de-risk-intent`. If framing hits a question about how the
     system is built, `frame-intent` parks it as an open design question and
     offers `architect-design`. Take that one-pass concept any time before you
     break the work down. If that concept changes the
     capabilities, take the longer route instead. `decompose-intent` breaks it
     into pieces the build loop can take.
   - *Longer route:* `frame-situation`, `identify-opportunities`,
     `diverge-solutions`, `de-risk-intent`, `place-bet`, and `map-capabilities`.
     Once the build order is set, `map-capabilities` offers `architect-design`
     to design against the capabilities, and you revise them until each one has
     a home. `architect-design` designs
     the subsystems that earn a doc, and `architect-review` checks them. The
     route passes on a capability map with a suggested build order.
   - *Supervised loop:* `frame-intent` and G0, then `de-risk-intent` and
     `explore-options`. G1 usually passes on its own. `frame-domain` grounds
     the domain and you set the MVP (G1.5). Design, system, and contract work
     run in parallel: `journey-mapping`, `user-flow`, `architect-design`,
     `architect-diagram`, and `api-contract`. A threat and reliability review
     follows. You approve
     the brief (G2), and `decompose-intent` breaks it into buildable pieces.
3. **Build it.** `work-intake` picks a spec, a delivery brief, or a minimum
   intent. `new-spec` writes the spec and plan, and you approve both. The
   plan's design follows your `reference.md`, and `new-spec` reads any design
   the delivery contract carries as context.
   `work-loop` builds, runs lint, type checks, and tests, and gets three cold
   reviews. A small, low-risk change skips the spec. The stage ends at G4, when
   you merge. When the work is done, `close-work` offers to fold the shipped
   design into the current-state map.
4. **Ship it.** `define-slo` sets an error budget if you want one.
   `release-loop` deploys to a throwaway environment, tests end to end, and
   watches telemetry. A deployed failure goes back to the build loop as a build
   task. You read the readiness record, and the stage ends at G5, when you ship
   it to production.

## Where architecture comes in

Architecture work runs on two rhythms. A few documents are set up once and
kept current. Then each piece of work uses the architecture skills at set
points in each stage. When the `architect` pack is installed, some shaping
skills offer the architecture step they own, and you choose whether to take
it. The table below names who offers each step. You start the others
yourself. On the supervised loop, `discovery-lead` runs the architecture lens
for you.

### Before any work: once per repository

Two documents come first. The architect skills ground their work in them, and
`new-spec` follows `reference.md` when it writes a plan:

- **The current-state map.** `architect-assess` maps what exists, with the
  hotspots and an action plan. You correct it before you rely on it.
- **The engineering patterns.** `reference.md` is a file, not a skill. It names
  your constraints, stack, building blocks, and shared standards.
  In `core`, `adapt-to-project` writes it from an existing codebase, and
  `init-project` writes it for a new one. An opt-in stack pack can ship one
  too. When `architect-design` finds no reference architecture, it offers to
  hand off to whichever of those two skills fits.

### Stage by stage

| Stage | When | What runs | What it settles |
| --- | --- | --- | --- |
| Decide what to build | The bet touches a system that already exists | You run `architect-assess` on that area | What's feasible and what's costly, before the strategic call |
| Shape it | Feasibility is the riskiest assumption | `de-risk-intent` tests it against the current-state map, or offers `architect-assess` when there is none | Whether it can be built on what exists |
| Shape it | Framing hits a question about how the system is built | `frame-intent` parks it as an open design question and offers `architect-design` at the scope it needs | The system's shape, kept out of the intent |
| Shape it | The build order is set | `map-capabilities` offers `architect-design` at system scope | Whether the capabilities fit the system's boundaries |
| Shape it | The capabilities have settled | `architect-design` at subsystem scope, then `architect-review` | A design doc for each part that earns one |
| Shape it | The domain you're framing sits in a system that already exists | `frame-domain` starts from the current-state map, or offers `architect-assess` when there is none | How the existing system works today |
| Shape it | The work is cut into pieces | `decompose-intent` checks each piece against the subsystem boundaries and carries the design into the delivery contract | Pieces that name the contracts they cross |
| Build it | `new-spec` writes the plan | Nothing extra | The plan's design follows `reference.md`, and `new-spec` reads the design the contract carries as context |
| Build it | The build shows a design is wrong | You run `architect-design` at change scope | A change to the design, made in the open |
| Build it, after the merge | The work closes | `close-work` offers to fold the shipped design into the current-state map. `architect-diagram` can redraw it | The map stays true for the next piece of work |
| Ship it | Usually nothing | — | A production problem can prompt your next assessment |

### The capability and architecture loop

In *Shape it*, capabilities and architecture shape each other. Neither one
finishes before the other starts. The skills supply the offers named here. The
order and the stop rule are a recommended practice that no skill enforces:

1. **Frame the problem.** `frame-intent` stays on the problem. When framing
   hits a question about how the system is built, it records the question and
   offers `architect-design`. When feasibility is the riskiest assumption,
   `de-risk-intent` tests it against the current-state map.
2. **Propose the capabilities.** `map-capabilities` does this on the longer
   route. On the short route, the intent itself is the starting point.
3. **Design against them.** Once the build order is set, `map-capabilities`
   offers `architect-design` at system scope, which shapes a half-page concept
   against the capabilities.
4. **Let the architecture talk back.** A capability that crosses a boundary,
   forces a new subsystem, or costs more than the bet can carry is a reason
   to go back to step 2 and revise the capabilities.
5. **Stop when it settles.** A good test: every capability has a home in a
   subsystem or an element, no open architecture decision blocks slicing, and
   the decisions worth an ADR are written down. Then design the subsystems that earn a doc,
   and check them with `architect-review`.
6. **Cut the work.** `decompose-intent` cuts pieces by what can ship on its
   own, not by component. A piece that crosses a subsystem boundary names the
   contract it depends on. If a capability needs a structural split before it
   can be cut, `decompose-intent` offers `architect-design` at subsystem
   scope. You commit to build at G3.

The short route usually makes one pass. If its concept changes the
capabilities, take the longer route. On the supervised loop, `discovery-lead`
runs this loop for you: the architecture and product lenses work in parallel
and push back on each other through the open-questions queue.

### System, subsystem, or change

`architect-design` works at one of three sizes:

- **The whole system:** one application or service, end to end.
- **One subsystem:** a part with its own runtime, contracts, and operations,
  carved out of a larger system.
- **A change:** a difference against what already runs. It starts from the
  existing system or subsystem design it amends.

A part becomes a candidate for its own design doc when it has an architectural
decision of its own plus one more reason. That reason can be a different
trust, identity, data-ownership, or deployment boundary. It can be its own
release or failure unit, a different system shape or workload class, different
owners or reviewers, or its own quality scenarios. Then ask who has the standing to accept
that decision. If it's this design's owners, the part gets its own doc. If it
sits above them, the decision moves up to the parent design. Any other part
stays a row in the parent design.

### How it reaches the spec

The plan `new-spec` writes has a design section. That section follows
`reference.md` when it exists, and any current architecture your `AGENTS.md`
maps. A design doc reaches the spec by two routes:

- **Through the delivery contract.** When `decompose-intent` cuts a feature a
  design covers, it carries the design's location in the contract's design
  context. `new-spec` reads it there as context, not as a rule to follow.
- **Through the current-state map.** After the work ships, `close-work` offers
  to fold the design into the current-state map. Later specs read it from
  there when your `AGENTS.md` maps that map.

A `workspace.toml` `needs` entry naming a design only orders the work: the
spec waits until the design lands, and the entry carries no content.

→ [Architect guides](../../architect/) · [Establish a reference architecture](../../architect/how-to/establish-reference-architecture.md)

## Why three loops, not one

Shipping software is three jobs: working out what to build, building it, and
getting it into production. One agent loop can't run all three well, so the
catalogue gives each job its own loop.

**Some mistakes are cheap and some aren't.** You can explore five product
shapes in an afternoon and throw four away. A bad production release can't be
taken back as easily. One level of caution is wrong for both: too slow for
exploring, too loose for shipping.

**Different people make the calls.** Whether an idea is worth building is a
business decision. Whether the code compiles is a mechanical check. Whether a
running system meets its service levels is an operations judgment.

**Each loop fails in its own way.** Discovery fails when it settles on the
wrong product. Build fails when the code doesn't work. Release fails when
something breaks in production. Each needs its own checks and its own
reviewers.

## The discovery loop

**Pack:** `product-engineering` | **Agent:** `discovery-lead` | **Scope:** user

Discovery takes a raw product signal and shapes it before anyone writes code.
What you end with is an intent you approved, written at the right size: an
initiative, a capability, or a single feature. Product Engineering doesn't need
`core` installed, and it doesn't write the repository's delivery contract.

How it works:

- **It compares before it chooses.** The agent explores five candidate product
  shapes side by side against the customer and the job they're trying to do,
  so the best one wins on comparison instead of the first idea getting polished.
- **Several specialists work at once.** Product, UX, architecture, and safety
  lenses each write their findings to a shared workspace the agent calls the
  blackboard. They never pass results to each other through chat.
- **Sub-problems stay in the same tree.** A sub-problem you find along the way
  becomes a child of the intent you're working on, and the same loop shapes it.
  It doesn't turn into a separate project.
- **Your decisions can't be rewritten.** Each verdict goes into an append-only
  log, chained by hash, so the agent can't forge or change a decision after you
  made it.

You decide at four points:

- **G0:** the value. Is the problem real, who has it, and is it worth a bet?
- **G1.5:** the MVP boundary. Which features are in the first bet?
- **G2:** the converged intent, including its riskiest assumptions and how
  you'll test them.
- **G3:** the hand-off. Is this ready for the repository's build loop?

→ [Discovery loop guide](../../product-engineering/) · [Walk a discovery end-to-end](../../product-engineering/tutorials/walk-a-discovery-end-to-end.md)

## The build loop

**Pack:** `core` | **Agent:** `work-loop` supervisor | **Scope:** repo

This is the inner loop, and it works on its own. `work-intake` reads what you
describe and picks a route. `intake-intent` records a minimum intent.
`author-delivery-brief create|continue` coordinates work that spans several
specs or repositories. `new-spec` writes one contract for one change you can
ship by itself. An intent from Product Engineering uses the same routes, and
`core` doesn't need that pack installed. Every build then runs plan, execute,
gate, review, and decide.

How it works:

- **The spec is reviewed twice before you see it.** A cold shaping review checks
  that the contract is observable and bounded. Then an adversarial review reads
  the spec and plan together and checks that the plan can deliver the contract.
  Neither replaces the code review that comes after.
- **The ceremony matches the risk.** Small, low-risk work runs in direct-light
  mode, straight from your request, with an adversarial review and no saved
  spec. Full mode writes a spec and plan when something raises the risk: a
  design you can't predict, a new dependency, a compliance surface, work shared
  between people, or a destructive operation. File count doesn't decide it.
- **The gates are real.** Lint, type checks, and tests run as gates. The agent
  can't report success while one of them is red.
- **Three reviewers read every change cold.** The adversarial reviewer looks for
  drift between spec, plan, and code. The security reviewer works from OWASP
  2025, ASVS, and STRIDE. The quality reviewer looks at testability,
  observability, and reliability. Each starts fresh, with no stake in the design.
  The loop keeps fixing until they say `Clean — ready to commit.`
- **Security depth follows the change.** The security checklist loads only the
  sections for the boundaries a change crosses, such as auth, secrets, user
  input, deserialization, file I/O, or LLM code.
- **Lessons stick.** When a run finds a gap in the project's conventions, it
  proposes an edit to the file that owns the rule. The fix stays with the
  project instead of vanishing when the session ends.

In full mode you approve the spec, then the plan, before any code is written.
The merge at the end is yours in both modes. Direct-light mode saves no spec, so
it skips the approval pair. Between those points the loop runs on its own. It
brings blockers to you, and it sorts concerns and nits by whether a tool can fix
them.

→ [Core pack guide](../../core/) · [The `core` pack as a system](../../core/explanation/core-pack.md)

## The release loop

**Pack:** `release-engineering` | **Agent:** `release-lead` | **Scope:** repo

This is the outer loop. It takes the build the inner loop finished and tests it
**deployed**: running in an environment like production, not on a developer's
machine.

How it works:

- **It only deploys to throwaway environments.** The release loop never touches
  production. Its environments hold no real user data, can't reach production,
  are kept apart from each other, and are torn down afterwards. That isolation is
  what makes it safe to leave running.
- **What can be undone runs on its own.** Deploying to a throwaway environment,
  running end-to-end tests, watching telemetry, redeploying, and tearing down
  all run without you. First real users, data migrations, spend over a
  threshold, and the production ship always wait for you.
- **A deployed failure goes back to the build loop.** It arrives in `work-loop`
  as a build task, not as a raw error for you to pass along. The inner loop
  fixes it and the outer loop redeploys.
- **It stops when the evidence says so.** The loop keeps going until the canary
  meets its service levels, the changed areas have end-to-end coverage, flaky
  tests are below the threshold, and the error budget isn't spent.
- **You get a record, not a thumbs-up.** The release-readiness record gives the
  convergence result, the operations and security verdicts, and the cost and
  budget status.

You decide once, at **G5**: does it go to production? No setting, mode, or
flag skips it, and the agent never moves past it on its own.

→ [Release loop guide](../../release-engineering/) · [The release loop explained](../../release-engineering/explanation/the-release-loop.md)

## Where each loop is installed

Each loop installs where its work happens:

- **Discovery installs per person (user scope).** Shaping happens in documents
  like Notion pages, Figma files, and slide decks, not in a repository. That's
  why `discovery-lead` brings its own reviewer agents: it can't count on `core`
  being installed.
- **Build installs per repository (repo scope).** `core` goes into the
  repository that holds the code. Its reviewer agents are available to any other
  pack installed in that repository.
- **Release installs in the same repository as build.** It needs `core` and
  reuses its reviewers, which only works because both live in the same
  repository.

So G3 is where the work moves from your documents into the repository. Any
design that covers the feature moves with it in the delivery contract. What it turns into depends on
its size. A single feature can become one spec. A
capability or an initiative can become an RFC, several child intents, or a
delivery brief that coordinates RFCs and specs. A repository without Product
Engineering starts at the same intent, delivery brief, or spec.

## How much the agents do on their own

The more permanent an action, the more the agent waits for you:

| What happens | Examples | How the agent behaves |
| --- | --- | --- |
| Runs on its own | Exploring product shapes, writing and running tests, deploying to throwaway environments, fixing build failures | Keeps going without you |
| Brings it to you | A blocker in the build loop, or the release loop reaching its stop point | Pauses and shows you where things stand |
| Waits for your yes | G0, G1.5, G2, and G3 in discovery, the merge, and G5 in release | Doesn't move until you approve |

## Install the loops

Install them in this order:

```bash
# 1. The build loop. The release loop needs it.
agentbundle install --pack core

# 2. The discovery loop, at user scope so it follows you across repositories
agentbundle install --pack product-engineering --scope user

# 3. The release loop, into the same repository as core
agentbundle install --pack release-engineering
```

Or install the `full-ceremony` profile. It installs `core` with
`governance-extras`, `product-documentation`, and `monorepo-extras` in one
command. Add the other loops as your team needs them.

You only need the loops your team uses. Most teams start with `core`. They add
`product-engineering` once product conversations start happening in documents
instead of in GitHub issues.
