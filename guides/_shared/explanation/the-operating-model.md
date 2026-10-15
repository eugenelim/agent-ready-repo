---
title: "Operating model"
summary: Know which stage your work is in, which packs help there, and where the agent waits for your decision.
pack: _shared
kind: explanation
---

# Operating model

Every piece of work moves through four stages: decide what to build, shape it, build it, and ship it. Agents do the work inside each stage. Each stage ends with a decision a person makes.

[![Four stages, left to right: Decide what to build, which ends when you pick the outcome. Shape it, which ends when you commit to build. Build it, which ends when you merge. Ship it, which ends when you ship. Below them, architecture by stage: before any work, architect-assess maps what exists and adapt-to-project or init-project writes reference.md; then you assess the area in Decide, design in Shape, and close-work folds the design into the current-state map after the merge.](the-operating-model-overview.svg)](the-operating-model-overview.svg)

[Open the full map](the-operating-model-full-map.svg) for every route, skill, and decision.

## The four stages

Start at the stage your work is in. A bug fix starts at Build it.

| Stage | What happens | Packs | It ends when you |
| --- | --- | --- | --- |
| Decide what to build | Gather evidence and make the strategic call | `desk-research`, `product-strategy` | Pick the outcome |
| Shape it | Frame the idea, test the riskiest assumption, design it, cut it into pieces | `product-engineering`, `experience-design`, `architect`, `contracts` | Commit to build |
| Build it | Write the spec, build, run the checks, review | `core` | Merge |
| Ship it | Deploy to a throwaway environment, test it, watch it run | `release-engineering` | Ship to production |

Some packs help at any stage: `code-intelligence` to learn what the code does, `governance-extras` to record a decision, `product-documentation` to document what shipped, and `atlassian`, `github`, `linear`, and `figma` to connect your team's tools.

## Decide what to build

You find out what is true, then choose what to bet on. `desk-research` answers questions with sources and a confidence rating for each finding. `product-strategy` turns the picture into a direction, such as a SWOT, an OKR cascade, or a press release written before the product. See [Research a question](../../desk-research/how-to/run-the-research.md) and [Set direction and goals](../../product-strategy/how-to/set-the-direction.md).

## Shape it

You turn the outcome into work the build can take. There are three routes, and all end when you commit to build:

- **Short.** Write the intent, test its riskiest assumption, and break it into pieces. Most teams start here.
- **Longer.** Map the situation, the opportunities, and the options before you bet. Use it when the problem itself is unclear.
- **Supervised.** The `discovery-lead` agent runs product, design, architecture, and contract work side by side, and two reviewers check threats and reliability before you see the brief. Use it for a new product area.

See [Shape an idea](../../product-engineering/how-to/frame-the-intent.md).

## Build it

The `core` pack's work loop builds the piece: features, fixes, refactors, migrations, and upgrades. Small, low-risk work runs straight from your request. Riskier work gets a written spec and plan, which you approve before any code is written.

Lint, type checks, and tests are real gates: the agent cannot report success while one fails. A shaping review checks the spec before code starts, and three reviewers then read every change cold: an adversarial reviewer for drift between spec and code, a security reviewer, and a quality reviewer. The merge is always yours. See [Run the build loop](../../core/how-to/start-the-work.md).

## Ship it

The `release-engineering` pack deploys the merged work to a throwaway environment, runs end-to-end tests, and watches telemetry until it meets its service levels. A failure goes back to the build loop as a task. It never touches production: you read the release-readiness record and decide whether to ship. See [Release a change](../../release-engineering/how-to/run-a-release.md).

## Where the agent waits for you

The more permanent the action, the more the agent waits:

| What happens | Examples | The agent |
| --- | --- | --- |
| Can be undone | Exploring options, writing and running tests, deploying to throwaway environments | Keeps going |
| Needs a call | A blocker, or the release loop reaching its stop point | Stops and shows you where things stand |
| Can't be undone | Committing to build, merging, shipping to production | Waits for your yes |

When an agent stops, it may print a short code:

| Code | You decide |
| --- | --- |
| G0 | Is the problem real, and worth a bet? |
| G1.5 | What is in the first version? |
| G2 | Is the brief good enough to build from? |
| G3 | Is it ready for the build loop? |
| G4 | Is the merged change ready for release testing? |
| G5 | Does it go to production? |

## Where architecture comes in

Before any work, the `architect-assess` skill maps the system you have, and `adapt-to-project` (for an existing codebase) or `init-project` (for a new one) writes `reference.md`, the file that names your stack and standards. Every plan follows it.

After that, architecture joins each stage when it is needed: you assess the area a bet touches while deciding, design against the capabilities while shaping, and change the design in the open if the build proves it wrong. After the merge, `close-work` offers to fold the shipped design back into the map. See [Design the architecture](../../architect/how-to/shape-an-architecture-concept.md).

## Why three loops

Working out what to build, building it, and shipping it are different jobs. Exploring five product ideas is cheap and a bad release is not, so each job runs in its own loop with its own checks: `discovery-lead` for shaping, the work loop for building, and `release-lead` for shipping. None runs inside another, and nothing crosses from one to the next without your decision.

## Where each loop installs

Each loop installs where its work happens. Shaping happens in documents, so it installs for you; building and shipping happen in the repository, so they install there:

```bash
agentbundle install --pack product-engineering --scope user
cd path/to/your-repo
agentbundle install --pack core
agentbundle install --pack release-engineering
```

Install only the loops your team uses. Most teams start with `core`.
