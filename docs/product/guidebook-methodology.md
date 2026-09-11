# Guidebook methodology

How we write a pack guidebook: the shape of a step, the reason each part is
there, and the failure each one prevents.

**Living document.** It changes when a reader hits something we did not expect.
Every rule below earned its place by a reader failing without it, and the
`Why it is here` column is the record of that — do not add a rule without one.

The mechanically enforced half of this lives in
[`guides/AGENTS.md`](../../guides/AGENTS.md) § The guidebook step contract and
is checked by `tools/lint-guidebook-steps.py`. That file is normative; this one
explains it and carries the parts no lint can decide. Where the two disagree,
the contract wins and this page is stale.

The evidence behind the obligations is in
[`research/workflow-guidebooks-survey.md`](research/workflow-guidebooks-survey.md),
which also records where evidence is absent and a rule is a house choice.

## The one-line version

**Every step is one screen and answers the same questions in the same order.
The pack's own skill and journey files stay authoritative; each step projects
from them and points back.**

Two consequences worth stating plainly. Same questions in the same order means
a reader learns the shape once and then reads by position rather than by
hunting. Projecting rather than restating means a step cannot drift from the
pack it documents without a check failing.

## The shape of a step

In this order. A reader who has read one step knows where to look on every
other.

| Order | Section | What it must do | Why it is here |
| --: | --- | --- | --- |
| 1 | **Where you are** | Position in the sequence, in the page body | A reader arriving from search sees no sidebar. Page-body primacy is the survey's finding |
| 2 | **What changes** | What this step makes different, and what it costs to skip | A step with no stated purpose reads as ceremony |
| 3 | **What you need first** | The input, and what skipping it costs | "Optional" with unstated consequences is a documented single-point failure |
| 4 | **How it goes** | What you type, what comes back, and **one turn where you push back** | A single clean response is a halo effect: readers accept confident draft output as finished work |
| 5 | **Where you decide** | The human gate, or an explicit statement there is none | Silence means both "no gate" and "nobody recorded one" |
| 6 | **How to tell it worked** | The judgement a machine cannot make, paired with what the question surfaces | A check that duplicates a lint degrades the judgement checks beside it |
| 7 | **What it writes** | The artifact, its path, and the headings to expect | Naming an output without its location is a named anti-pattern |
| 8 | **Watch out for** | The failure modes, how to notice each, and only then where to route | A review with nowhere to route a problem gets approved anyway |
| 9 | **What you run next** | Named, and linked | A step that ends without an onward move is pinball documentation |
| 10 | **Go deeper** | One line, pointing at the authoritative source | The pack's own files stay the truth; the step is a projection |

### Sections that carry more than their name suggests

**"How it goes" is a loop, not a demo.** Show the request, the agent's turn
attributed separately from your input, and then **a correction** — a reader
telling the agent it got something wrong, and the agent adjusting. A step that
only shows success teaches a reader to accept the first draft. Say that output
varies at the step, not once at the front: a single disclaimer does not raise
how carefully people check, while a repeated one does.

**"How to tell it worked" pairs the question with its yield.** Not "is the
problem specific enough?" but a two-column table — the question, and what
asking it surfaces. A reader who knows what a question catches will actually
ask it. Where a mechanical check exists, give the reading rule too: state what
its output *means*, because a number with no interpretation is not a check.

**"Watch out for" is diagnosis before routing.** Name the failure mode, say how
a reader notices it, and then give the move. The most important entry is
usually the same one: the draft is confident everywhere, including where it is
guessing. A reader who does not know that accepts polish as correctness.

**Provenance is a risk signal, not bookkeeping.** Where a value came from
matters to a reader only when it tells them where to distrust the draft. Say
which parts came from their own context and which from a general pattern, and
say the general ones are where to argue first. Do **not** publish
rung-by-rung provenance as visible prose — it reads as noise and a reader will
ask what it means. The rung goes in an HTML comment for the lint; the
*risk* goes in the text.

## Navigation and information architecture

| Rule | Why |
| --- | --- |
| The path is the order you will do it. Group steps into named parts, and state the ordering principle on the entry page | Sequence organises navigation; page type governs authoring. They are compatible |
| Separate the path from reference material, and say reference is not needed to use the thing | A reader who must open a design document to proceed has failed the walk. Linking beats absorbing, because inlining explanation into a task page is content drift |
| State position twice: on entry and on exit | Orientation on arrival, and confirmation on leaving |
| Prev and next carry titles, never arrows alone | A reader should know what is next before clicking |
| A guidebook needs an **entry page** stating who it is for, what it assumes, and how it is laid out | Without one, a reader does not know where to type anything. This was a real first-reader failure |
| Every step ends by naming the next by title, with a resolving link | A prose promise like "continue with the build workflow" names nothing clickable |

### Numbering, and splitting a step without renumbering

Number steps `1..N` against the pack's journey stages. When one step grows too
large, split it with a **letter suffix** — `4`, then `4a`, `4b`, `4c` — rather
than renumbering the rest of the path. A step carrying eight skills is the case
this exists for: renumbering breaks every inbound link and every reader's
mental model, and a suffix costs nothing.

## Explaining a concept without an image

**A guide cannot carry an image.** The projector rewrites Markdown image paths
into page URLs and copies no assets, so nothing renders on both GitHub and the
docs site. That is a constraint, not a loss — the better patterns do not need
one:

1. **A captioned text artifact.** Show the real thing the step produces — a
   table, a tree, a fragment of output — and put the explanation in the
   caption. The caption does the teaching: not "a sample map" but what the
   reader should notice about its shape and why it matters.
2. **A two-column table as the explainer.** Question and what it finds. Before
   and after. Input and consequence. A table earns its place when it makes a
   relationship easier to see, and not otherwise.
3. **Real output, unpolished.** Paste what the tool actually prints, including
   the parts that look untidy. Tidied output teaches a reader to expect
   something they will not get.

## What we deliberately do not do

| Not this | Because |
| --- | --- |
| Claim a reader adopts faster, finishes more, or reaches value sooner | No evidence supports it and the install-to-first-value probe is unrun. The contract enumerates the prohibited terms and the lint scans for them |
| Reading-time estimates per step | We have never measured one, and a guessed number is a claim |
| A persuasive before-and-after framing on the guides hub | That surface's content brief forbids persuasion register. Take the two-column structure; drop the comparative sell |
| Inline a full explanation of a concept | Content drift, and the most consistently documented anti-pattern in the type-separation literature. Link out, and author a bounded explanation only where nothing exists to link to |
| Present a subagent or a reviewer role as something to run | A reader cannot type it. Describe it instead |
| Publish a step for a skill that writes nothing without saying so | Use the explicit writes-nothing declaration; silence is ambiguous |

## How to iterate on this

Add a rule when a reader fails without it, and record the failure in the
`Why it is here` column. Prefer making a rule mechanical: if a lint can decide
it, move it to the contract in `guides/AGENTS.md` and leave only the reasoning
here. A rule that stays here is one no check can settle — which is exactly the
set a cold read owns.

**Only a mechanically decidable finding blocks a wave of authoring.** A finding
about the adequacy of prose is guidance, recorded and dispositioned. Severity is
not a reviewer's to assign, and two readers arguing about malleable wording is
not a gate.

## Changelog

- 2026-09-11 — First version. Written while building the first pack guidebook,
  from the survey's evidence plus the patterns a first-reader failure exposed:
  reader-facing section names, the correction turn, judgement paired with its
  yield, diagnosis before routing, provenance as a risk signal, the entry page,
  the path/reference split, letter-suffix splitting, and explaining without
  images.
