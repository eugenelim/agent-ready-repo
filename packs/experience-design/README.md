# Experience Design

Your agent can design an experience from the user's outcome to the finished screen: journey, flow, look and feel, copy, and review.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install it once for your user account:

```bash
agentbundle install --pack experience-design
```

In Claude Code you can install it as a plugin instead:

```bash
claude plugin install experience-design@agent-ready-repo
```

## What your agent can do

- Map what a customer goes through, with stages, pains, and opportunities.
- Turn an approved journey into screens, transitions, failure paths, and a brief for each screen.
- Pick a visual direction for a page or screen that should feel a certain way, and resolve it into a design system.
- Plan what goes where on a screen, and how each component responds to actions.
- Set the message and tone of the copy before the words are written.
- Critique a finished screen, flow, or mockup against a quality floor.

## Skills

- **`journey-mapping`** — Maps a customer journey from one meaningful outcome to the next.
- **`user-flow`** — Turns a journey into a screen sequence with a brief for each screen.
- **`creative-direction`** — Names a shared visual direction for a product.
- **`design-system`** — Decides typography, color, spacing, shape, depth, and motion for a build to follow.
- **`information-architecture`** — Lays out hierarchy and reading order for a screen or flow.
- **`interaction-design`** — Specifies how a screen or component responds, validates, and recovers.
- **`content-design`** — Sets message, narrative, and tone for copy.
- **`design-principles`** — Writes 3 to 5 named design rules, each with an arbitration test.
- **`service-blueprint`** — Shows the people and systems behind each journey step.
- **`process-mapping`** — Maps how an internal operation works today or should work.
- **`design-review`** — Critiques a rendered screen with severity-rated findings.
- **`experience-status`** — Shows which design artifacts exist and what to run next. Read-only.

Subagent: **`experience-reviewer`** gives an independent, read-only review in a fresh context.

## Works with

Works with Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, Kiro IDE, and Kiro CLI. [Product Strategy](../product-strategy/README.md) can supply a UX and content strategy that the journey and content skills read. [Frontend Engineering](../frontend-engineering/README.md) builds from the design handoff. See [Design the experience](../../guides/experience-design/README.md).

## Questions

**Where do I start?** Describe the user, the outcome, and where the experience breaks down, then ask for a journey map. Run `experience-status` any time to see where you are.

**Does it need a strategy first?** No. If a UX or content strategy file exists, it uses it. If not, it carries on.

**Does it produce code?** No. It produces design documents. Building comes from the screen briefs.

**Does it grade its own work?** The `experience-reviewer` subagent reviews in a fresh context, so the design's author is not the reviewer.

## Details

Scope: user (default), repo · Version: 4.1.6 · Source: [packs/experience-design](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/experience-design)
