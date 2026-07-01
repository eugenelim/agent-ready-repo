# Notation routing — intent → Mermaid notation

Pick the notation from intent, not from what's familiar. The wrong
notation is the most common reason a diagram is unreadable.

## Decision table

| User intent (paraphrase) | Notation | Mermaid kind |
| --- | --- | --- |
| "What talks to what" — structural / topology | C4 Context, C4 Container | `C4Context`, `C4Container`, or `flowchart TB` with subgraphs |
| "What happens when X arrives" — flow | Sequence diagram | `sequenceDiagram` |
| "What states does this go through" — lifecycle | State diagram | `stateDiagram-v2` |
| "What is the shape of the data" — model | Entity-relationship | `erDiagram` |
| "Where does it run" — deployment / infra | Deployment view | `flowchart TB` with subgraph nesting for region / VPC / subnet |
| "Who decided what when" — workflow / approvals | Flowchart with decision diamonds | `flowchart TD` |
| "What happened when" — roadmap / chronology / release history | Timeline † | `timeline` |
| "Prioritize these" — 2×2 / effort-vs-impact / positioning | Quadrant † | `quadrantChart` |
| "Break this down" — decomposition / hierarchy / mind map | Mindmap † | `mindmap` |
| Comparison ("X vs Y") | Markdown table — **not** Mermaid | — |
| Internal class structure | Class diagram | `classDiagram` *(rarely the right answer for architecture; usually means the question is "code" not "architecture")* |

† **Newer grammars — offer with a rendering caveat, don't default.**
`timeline`, `quadrantChart`, and `mindmap` are the same class as
`architecture-beta`: they render inconsistently across enterprise wikis.
Route to them by intent, but offer them the same way — only when the venue
is confirmed to render them, otherwise fall back (timeline → date/milestone
table; quadrant → effort/impact table; mindmap → nested bullet list). Load
`references/mermaid-{timeline,quadrant,mindmap}.md` for the per-type
skeleton, the fallback, and the complexity budget.

## Mode interaction

- **design** mode: pick by intent; if the user named a notation but the
  intent disagrees, push back once and offer both.
- **document** mode: the *system you can read* often dictates notation.
  A repo of stateless microservices wants a Container view; a repo of
  state machines wants a state diagram.
- **review** / **update** mode: stay in the user's chosen notation
  unless changing it would prevent a rubric failure.

## When to split

One Mermaid diagram should fit on one screen — roughly ≤15 nodes. When
the system is bigger:

- Split by *scope sentence*. Diagram A is "the request path"; diagram
  B is "the build and deploy path"; diagram C is "the data
  lifecycle". Each diagram earns its scope sentence in the prose.
- Avoid splitting by notation alone — three flowcharts that should
  have been one Container view are worse than one big flowchart.

## When *not* to draw

- The system has two components and one arrow. Write a sentence.
- The user wants a comparison. Use a Markdown table.
- The user wants a checklist. Use Markdown bullets.

A diagram earns its place by being the most compact representation,
not by being a diagram.
