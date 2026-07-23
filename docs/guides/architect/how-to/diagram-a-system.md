# Diagram a system

**Use this when:** You know what you want drawn and need a Mermaid diagram of a system, flow, state machine, data model, or deployment topology.
**Prerequisites:** The `architect` pack installed; optionally a `docs/architecture/reference.md` for document-mode diagrams grounded in your stack.
**Result:** A self-checked Mermaid diagram in the right notation, with an offer to save it to the repo.

> Get a Mermaid diagram of a system, flow, state, data model, or deployment topology out of the `architect-diagram` skill. Assumes you know what you want drawn; if you're still framing the problem, that's a design conversation — reach for [`architect-design`](../../../../packs/architect/.apm/skills/architect-design) instead.

You have something to draw. Ask in plain language and the [`architect-diagram`](../../../../packs/architect/.apm/skills/architect-diagram) skill picks the notation, drafts the diagram inline, and self-checks it before you ever see it.

## Just ask

There's no flag to set and no mode to declare. Describe what you want drawn and the skill routes the notation from your intent:

- "Draw the checkout flow." → a flowchart.
- "Show me the sequence when a request hits the API." → a `sequenceDiagram`.
- "Give me a C4 Container view of the billing service." → a C4 container diagram.
- "Diagram the order state machine." → a `stateDiagram-v2`.
- "Show the data model for users and orders." → an `erDiagram`.

The intent in your words picks the notation:

```text
  your ask                          intent                 notation
  ────────────────────────────────────────────────────────────────────
  "draw the checkout flow"     →    a process / flow   →   flowchart TB
  "the sequence when a              ordered calls
   request hits the API"      →     over time         →   sequenceDiagram
  "C4 Container view of X"     →    what talks to what →   C4 container
  "the order state machine"    →    states + transitions→  stateDiagram-v2
  "the data model for          →    entities +
   users and orders"                relationships     →   erDiagram
```

The output is Mermaid that renders cleanly in GitHub, Confluence, Azure DevOps Wiki, and GitLab. The skill defaults to `flowchart TB` with nested subgraphs because that's what survives enterprise wiki rendering. It knows about `architecture-beta`, but it won't default to it — rendering is uneven across wikis, so you'll only get it offered when your target renderer is known to support it.

## Tell it which world it's in

The skill reads the message and routes once between four modes. You don't flag the mode, but knowing them tells you what to expect:

```text
  what's in your message                        mode        what it does
  ──────────────────────────────────────────────────────────────────────────
  vague idea, no code or paths          →    design     draws from your words;
                                                         flags invented names
  a repo path / "the system today"      →    document   reads code first; only
                                                         draws what's there
  a pasted diagram + "what's wrong?"    →    review     quick rubric pass →
                                                         hands off to
                                                         architect-review for
                                                         severity-tagged findings
  an existing diagram + a diff          →    update     applies the change;
   ("add a cache", "drop the queue")                     surfaces side-effects
                                                         (orphans, broken
                                                         trust boundaries)

  two modes plausibly fit?  →  it asks once which you meant.
```

- **design** — you describe an idea with no code in scope. It draws from your words and flags any component names it had to invent.
- **document** — you point it at a repo path or "the system as it is today." It reads the code first and diagrams only what's actually there. It never invents names; an unnamed node is marked, not guessed.
- **review** — you paste a diagram and ask "what's wrong with this." For a full severity-tagged critique it hands off to [`architect-review`](review-an-architecture-artifact.md).
- **update** — you give it an existing diagram and a diff ("add a caching layer", "drop the queue"). It applies the change and surfaces side-effects you didn't ask about, like orphaned nodes or a broken trust boundary.

If two modes plausibly fit, it asks once which you meant.

## When the system runs beyond the repo

In **document** and **update** mode, "read the repo" extends to "read the landscape." When the as-is system integrates past the repo boundary and an *internal* knowledge surface is reachable this session — an enterprise-knowledge MCP tool, an internal CLI, an in-repo doc set (public web doesn't count) — the skill consults it to ground the beyond-repo boxes, arrows, and edge labels, and it **names what it drew from** ("from the architecture wiki", or "repo only"). An edge it can't ground stays a question, not a guess; an edge the repo contradicts gets flagged rather than quietly drawn over. This grounding doesn't apply in **design** mode (you're drawing a hypothesis) or **review** mode (that routes to `architect-review`).

## Diagramming the cloud

Name a cloud and the skill layers in the right boundary vocabulary. It knows AWS, Azure, and GCP, primitives providers like Hetzner, and agentic platforms — Bedrock AgentCore, AI Foundry, Vertex Agent Engine. A diagram of AgentCore is not "AWS with a Lambda in it," and the skill draws it accordingly. Multi-cloud diagrams pull in the vocabulary for each cloud they cross.

Trust boundaries are non-negotiable here. A cross-account or cross-tenant arrow without a labeled boundary is a security hazard rendered as art, and the skill refuses to draw one that way. Expect dashed subgraph borders or explicit boundary comments wherever the diagram crosses a trust line.

## Let your `reference.md` steer it

If your repo has a `docs/architecture/reference.md`, the architect skills design against it — your stack, your patterns, your constraints — so document-mode diagrams match how this codebase is actually built rather than a generic shape. No `reference.md` yet? [Establish your repo's reference architecture](establish-reference-architecture.md) first; it gives the skills something to draw against.

## What you get back

Every diagram is self-checked against the skill's rubric before it reaches you. The non-negotiables it enforces:

- Every Container carries a technology label.
- No bare relation labels — every arrow says what it carries.
- It fits one screen (roughly 15 nodes or fewer); bigger systems get split.
- Document mode never fabricates a name.
- Trust boundaries are visible.

When the diagram is ready, the skill offers to save it. It scans for an obvious home (`docs/architecture/`, `diagrams/`, `docs/`) and suggests a kebab-case `.mmd` filename. Saving is always an offer, never automatic — you decide where it lands.

## When not to reach for it

A diagram isn't always the answer. The skill will push back rather than draw:

- A comparison of options is a Markdown table, not a diagram.
- A checklist is a list.
- A two-component "A calls B" flow doesn't need a picture.
- If you ask for a "sequence diagram" of *what talks to what*, the right answer is a Container view. The skill offers both and tells you why.

## See also

- [Review an architecture artifact](review-an-architecture-artifact.md) — get a severity-tagged critique of a diagram, design doc, RFC, or ADR.
- [Establish your repo's reference architecture](establish-reference-architecture.md) — give the skills the golden path they design against.
- [`reference.md` sections and the stack-pack contract](../reference/reference-architecture.md) — what the golden-path file holds.
