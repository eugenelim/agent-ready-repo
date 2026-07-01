# RFC-0057: Research methodology shape

- **Status:** Open <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-30
- **Date closed:** <!-- filled in when status reaches a terminal state -->
- **Decision weight:** standard <!-- extends (does not reverse) RFC-0039/ADR-0029; additive; two surfaces but prompt-only, reversible -->
- **Related:** RFC-0039 (research project mode + typed artifacts — the two-axis model this extends), ADR-0029 (depth × lifecycle), `packs/research` (the pack this extends), `packs/converters` skill `markdown-to-pptx` (the downstream slide consumer), `packs/product-engineering` skill `frame-domain` and `packs/experience` skill `map-internal-process` (the two neighbours this fences off)

## Reviewer brief

- **Decision:** should the `research` pack gain a **`methodology` output shape** — a staged, contingency-adapted, maturity-aware, evidence-grounded description of *how an activity is done end-to-end* — available both one-shot and in a multi-week project?
- **Recommended outcome:** accept.
- **Change if accepted:**
  - `research` gains a `methodology` shape emitting `<topic-slug>-methodology.md` (one-shot).
  - Project mode's shape vocabulary gains `methodology`; `research-project-synthesize` emits `methodology.md` (sustained/multi-week).
  - A new `references/methodology-shape-template.md` encodes the six-section artifact template + its disciplinary grounding.
- **Affected surface:** `packs/research` skills + references only. No code, no new dependency. The `converters` pack is a *consumer*, not a coupling.
- **Stakes:** reversible — an additive shape, prompt-only, no migration of existing artifacts.
- **Review focus:** (1) is `methodology` a genuinely distinct *shape* or a survey with headings? (D1) (2) is the boundary against `frame-domain` / `map-internal-process` clean? (D4)
- **Not in scope:** a runtime engine; a new standalone skill or skill-family (deliberately declined for v1 in favour of a shape — see Options); hard-wiring the slide converter.

## The ask

**Recommendation (BLUF — bottom line up front):** Add a **`methodology`** output shape to the `research` pack — an artifact that documents *the canonical way to do X, adapted to the reader's situation*, structured as a journey (scope → stages → contingency branches → maturity ladder → failure modes, all evidence-graded). Ship it on **both** research surfaces the pack already has: one-shot (episodic) via a new `<type>` on `/research`, and sustained (project mode) via a new `shape:` value. The artifact is authored heading-per-stage so it drops straight into the existing `markdown-to-pptx` skill for a slide deck.

**Why now (SCQA — Situation · Complication · Question · Answer):**
- *Situation:* the `research` pack does evidence-grounded research well, and already routes to several **shapes** — an output form the answer takes: a `survey`, a decision `comparison-matrix`, a ranked `shortlist`, a structural `blueprint`, a `hypotheses` adjudication (RFC-0039).
- *Complication:* a whole class of questions — "what's the best way to run a data-migration workbench", "…to progress a training plan for my situation", "…to bring AI-SDLC modernization to a stream", "…to train this dog breed", "…to pick the right college applications" — asks for a **process/lifecycle**, not a claim-organized survey. The pack has the retrieval machinery but no shape whose *topology* is a sequence-with-contingency-and-progression. Users improvise it, and nothing lands slide-ready.
- *Question:* should the pack grow a `methodology` shape on both its surfaces, grounded so it stays a habit (Charter Principle 3) not infrastructure, and fenced cleanly against the two neighbouring "process" skills in other packs?

**Decisions requested:**

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Where does the capability live — mode, shape, or new skill? | A new **`methodology` shape** on `research` | Lowest footprint that delivers a distinct output topology; a "mode" is the *depth* axis, not a shape; a standalone skill re-wraps applied research at 6-adapter cost | this review | Confirm shape (not mode/skill) |
| D2 | What does the artifact contain? | The **six-section** template (scope · stages · contingency · maturity · failure-modes · evidence) | Each section grounded 1:1 in a source discipline; contingency + maturity are what a survey lacks | this review | Confirm the six sections |
| D3 | What depth does it default to? | **`applied`** (grey-literature best-practice), `standard`/`deep` on cue | "The best way to do X" is practitioner knowledge; scholarly domains can override | this review | Confirm default |
| D4 | How is it fenced from `frame-domain` / `map-internal-process`? | Phrasing routing **+ explicit "do NOT use" pointers** | Every pack skill draws its own boundary; overlap is real and must be named | this review | Rule on the boundary |
| D5 | How does the PowerPoint handoff work? | **Structure-only** — heading-per-stage → `markdown-to-pptx`, prompt-driven | Keeps the research pack portable (no hard dep on `converters`) | this review | Confirm no hard coupling |
| D6 | One-shot only, or multi-week too? | **Both** — episodic shape **and** a project-mode `shape:` value | The motivating cases (migration workbench, SDLC-modernization roadmap) are multi-week source-accumulating investigations | this review | Confirm both surfaces |

## Problem & goals

The pack's shapes are all organized around a **claim**: a `survey` says what is known about X; a `comparison-matrix` says which option wins; a `hypotheses` artifact adjudicates competing explanations. None of them is organized around a **process** — an ordered set of stages, the branches that make the process fit *your* situation, and the progression from beginner to expert execution. That output *topology* is simply absent.

The result: when the question is "how do I *do* this, end to end, given my situation", the best current tool is `applied`-mode research (grey-literature best-practice), which returns a findings list — true things about the activity — that the user then has to re-shape by hand into a sequence before it is usable, and again before it is presentable. For the multi-week cases (a migration workbench built up over weeks of vendor docs, case studies, and internal artifacts; an AI-SDLC-modernization roadmap for a whole delivery stream) there is nowhere for the accumulating methodology to *live* as it forms.

**Goals.**
- Add a **`methodology` shape** whose artifact is a staged, contingency-adapted, maturity-aware, evidence-graded description of how an activity is done end-to-end.
- Ship it on **both** research surfaces: one-shot (`/research`) and sustained (project mode).
- Ground each section of the artifact in an established discipline, mirroring how the pack already rests on convergent disciplines (STORM, PRISMA, ACH, GRADE — topic-survey, systematic-review, competing-hypotheses, and evidence-grading methods respectively).
- Make the artifact **slide-ready** — heading-per-stage so `markdown-to-pptx` renders it with no reshaping.
- **Fence** the shape cleanly against `frame-domain` (product/MVP grounding) and `map-internal-process` (an org's own as-is/to-be operations).

**Non-goals.**
- *A runtime engine or index.* The shape is prompt-only — the filename and structure are produced by the agent following the skill, exactly like every existing shape (Charter Principle 3).
- *A standalone skill or skill-family (for v1).* Deliberately declined in favour of a shape; the door to graduate is left open (see Options and Open questions).
- *Hard-wiring the slide converter.* The handoff is structure-only; `research` gains no dependency on `converters`.
- *Owning "process" work that already has a home.* Product-MVP grounding stays with `frame-domain`; an org's own internal operations stay with `map-internal-process`.
- *A new confidence rail.* The shape inherits GRADE confidence (a four-level per-finding rating — high/moderate/low/uncertain — with named downgrade reasons) + ≥3-source triangulation unchanged.

## Proposal

### D1 — a new `methodology` shape (not a mode, not a skill)

`research` already routes the answer to a **shape** via the "Type vocabulary" table in its skill body — a shape is the *form the answer takes*, distinct from the **depth** axis (quick/standard/applied/deep, which is *how hard the pack looks*). The `methodology` shape is one more row:

| Mode / answer shape | Artifact |
|---|---|
| standard / applied survey | `<topic-slug>-survey.md` |
| comparison / decision | `<topic-slug>-comparison-matrix.md` |
| ranked candidates | `<topic-slug>-shortlist.md` |
| spatial / structural | `<topic-slug>-blueprint.md` |
| hypothesis adjudication | `<topic-slug>-hypotheses.md` |
| **process / methodology / lifecycle** | **`<topic-slug>-methodology.md`** |

It fires on phrasing like *"the best way to do / run / build / train X"*, *"the process / lifecycle / playbook for X"*, *"how do you go about X end to end"*. Prompt-only: the agent produces the filename and structure by following the skill (no script), exactly as the existing shapes do.

Shape name **`methodology`** over `playbook` — it matches the user's framing and covers lifecycle/process; "playbook" reads as narrower ops-jargon.

**Terminology (the two field names are distinct).** "Shape" is this RFC's umbrella word for *the form the answer takes*. In the skills the field names differ by surface: the episodic side has a **`<type>` stem** (this adds `methodology`), while the project side has a **`shape:` frontmatter value** (this also adds `methodology`). The spec must add the episodic `<type>` and the project `shape:` value — not invent a new `shape`-named episodic field, which does not exist today.

### D2 — the six-section artifact, each section grounded in a discipline

`<topic-slug>-methodology.md` carries six sections. Each section is authored as an `H1` (so `markdown-to-pptx` renders a section slide) and each **stage** within the spine (§2) is an `H2` so it becomes its own slide; finer sub-steps render as bullet lists, **not** deeper headings — the converter maps only `H1`/`H2` to slides (D5), so an `H3` would fold into its parent slide's body (and the renderer keeps the literal `###` text, so sub-steps must be authored as bullets, never `H3`):

1. **Scope frame** — what the activity takes in and produces, its boundary, and the actors/roles. *Grounds on SIPOC* (Suppliers · Inputs · Process · Outputs · Customers — a high-level process-scoping tool).
2. **Stage spine (the journey)** — the ordered end-to-end phases; each stage has entry criteria → activities → exit gate → artifacts, decomposed hierarchically. *Grounds on process discovery* (deriving a process model — its stages and control flow — from how the activity is actually performed) *and hierarchical task decomposition*.
3. **Contingency branches** — how the method flexes to the reader's situation (the "*for you / for this breed / for this stream*" part): the situational factors that select a path, and how the stages change under each. *Grounds on situational method engineering* (assembling a situation-specific method from reusable fragments) *and project contingency factors*.
4. **Maturity ladder** — where the reader is now and the next rung: the progression from beginner to expert execution (or, for a one-off deliverable with no skill-progression, an adoption/capability-maturity axis — crawl → walk → run of the deliverable). *Grounds on the Dreyfus stages* (novice → advanced beginner → competent → proficient → expert).
5. **Failure modes** — the naive way each stage goes wrong: the expert-vs-novice gap the method exists to close. *Grounds on cognitive task analysis* (eliciting the tacit cues and decisions experts use that novices miss).
6. **Evidence & confidence** — the best-practice provenance behind the above, per-finding GRADE-tagged and ≥3-source triangulated — inherited from the pack unchanged.

Contingency (§3) and maturity (§4) are the **non-negotiable** differentiators from a survey; a `methodology` artifact without them is a survey with headings.

### D3 — defaults to `applied` depth

"The best way to do X" is overwhelmingly *practitioner* knowledge — runbooks, field guides, post-mortems, vendor playbooks — so the shape defaults to **`applied`** depth (the pack's grey-literature mode, with its practitioner-calibrated triangulation, where multiple posts from one vendor count as one source). Domains with a genuine scholarly methodology literature (clinical care pathways, pedagogy) can override to `standard`/`deep` via the ordinary depth cues.

### D4 — the boundary against the two neighbours

The shape ships explicit "do NOT use" pointers in its trigger prose, and reciprocal ones are added to the neighbours' disambiguation lines:

| If the work is… | Use | Not |
|---|---|---|
| the canonical, best-practice, domain-general way to do X (any domain) | **`research` methodology shape** | — |
| grounding a *product* in its real-world activity + bounding an MVP | `frame-domain` (product-engineering) | the methodology shape |
| documenting *your own org's* as-is / to-be internal operations | `map-internal-process` (experience) | the methodology shape |

The distinction is source-and-scope: the methodology shape does **outside-in discovery of world best practice for an arbitrary domain**; `frame-domain` is product/MVP-scoped and wraps other skills; `map-internal-process` is *your* existing operations, inside-out, swimlane-shaped (APQC — a standard process-classification framework).

**Honest overlap.** Two of the six grounding disciplines are *not* exclusive to this shape: §1 (SIPOC scope frame) and §2 (process-discovery spine) draw on the same lean/process-mapping canon `map-internal-process` already uses. The boundary therefore does **not** rest on those. It rests on (a) source + direction — world best-practice, outside-in, for any domain vs *your own* operations, inside-out — and (b) the three sections that have **no** `map-internal-process` equivalent: contingency branches (§3, situational method engineering), the maturity ladder (§4, Dreyfus), and failure modes (§5, cognitive task analysis). Those three, plus the direction axis, are the real differentiators.

### D5 — structure-only PowerPoint handoff

The artifact is authored heading-per-section/stage precisely because the `converters` pack's `markdown-to-pptx` skill maps each `H1`/`H2` → one slide, list items → bullet rows, and a Markdown table → a slide table. The artifact therefore keeps sections at `H1` and stages at `H2` and pushes all finer detail to bullets — anything at `H3` renders as body, not its own slide (D2). So "turn this into a deck" is a one-prompt handoff to an existing skill. `research` gains **no dependency** on `converters` — a repo without the converters pack still gets the artifact; it just renders the slides elsewhere. The methodology skill body names `markdown-to-pptx` as the natural consumer without importing or requiring it.

### D6 — both surfaces (one-shot and multi-week)

- **Episodic (one-shot):** the new row in the Type vocabulary table (D1).
- **Project mode (multi-week):** `methodology` is added to the `shape:` frontmatter vocabulary in `research-project-start` (today: `survey | comparison | decision | structural | adjudication`), and `research-project-synthesize` gains a branch: a `methodology` shape writes `methodology.md` (bare-named inside the project folder, per the existing convention) alongside the single-file `<topic-slug>-brief.md` governance handoff. The middle layer (the synthesis matrix + memos) accumulates sources over the weeks; synthesis shapes them into the six-section methodology.

**Migration:** none. This is purely additive — a new shape value and a new synthesize branch. No existing artifact is renamed; no consumer changes.

## Options considered

**D1 axis — surface footprint** (how much new surface the capability adds), increasing. Collectively exhaustive: you add no surface, reuse the depth axis, add a shape, add a skill, or add a skill family.

| Option | Footprint | Prior art | Trade-off |
|---|---|---|---|
| **Do nothing** | none | status quo | zero cost; but the process-shaped output never materializes — every methodology re-improvised from an `applied` survey, none slide-ready |
| **New depth "mode"** | overloads the depth axis | — | familiar word, but *miscategorizes*: RFC-0039/ADR-0029 fix depth (quick/standard/applied/deep) as *how hard the pack looks*; a methodology is an output *shape* — this fights the two-axis model |
| **★ New `shape` on `research`** | one `<type>` row + one project `shape:` value + one reference file | the existing shapes (`comparison-matrix`, `shortlist`, `blueprint`) — distinct topologies over shared retrieval | matches the pack's shapes-as-rows precedent; inherits the evidence rails; prompt-only. The new `references/methodology-shape-template.md` records the *artifact's* six-section structure and its grounding — distinct in kind from the existing `references/methodologies.md`, which catalogues the pack's *research-method* disciplines and stays as-is (no existing shape carries a per-shape template file; this one is justified by the six-section authoring load). Cost: two skill bodies touched (episodic + project) |
| **New standalone skill** (`discover-methodology`) | full skill: trigger, projection, 6-adapter parity, tests | — | own front door, but re-wraps `applied` research and pays full surface cost for the same output |
| **New skill family** (project-mode analog) | four+ skills | RFC-0039 project mode | warranted only if the *process* (not the output) diverges from ordinary research; over-built for v1 |

The shape sits one rung above do-nothing/mode and one below a skill because the output topology is new but the *process* to produce it (retrieve → triangulate → synthesize) is the pack's existing one. Do-nothing's cost of delay: the pack cannot serve a whole recurring question-class ("how is X done") and every such investigation re-improvises its structure.

**D2 sub-axis — artifact fidelity to the source disciplines.** Minimal (stages only) is a bare process list — it drops contingency and maturity, i.e. exactly the "*for you*" and "the journey" parts. Maximal (add RACI — a responsibility-assignment grid — KPIs, per-stage tooling) risks bloat. The six-section template is the MECE (mutually exclusive, collectively exhaustive) middle: one section per discipline, contingency + maturity retained as the differentiators, extras deferred to optional per-stage fields. Chosen: six-section (D2).

## Risks & what would make this wrong

**Pre-mortem.**
- *The shape collapses into a survey* — agents emit a claim-list under process headings, skipping contingency/maturity. *Mitigation:* the reference template makes §3 (contingency) and §4 (maturity) mandatory sections with worked exemplars; a methodology missing them is flagged incomplete.
- *Boundary bleed* — users fire it for product-MVP grounding or their own ops, duplicating `frame-domain` / `map-internal-process`. *Mitigation:* explicit reciprocal "do NOT use" pointers (D4).
- *Slide coupling creep* — a later change hard-wires the converter. *Mitigation:* D5 states the no-dependency rule; the skill names the consumer by reference only.
- *Multi-week over-reach* — the project-mode shape tempts users into project mode for a one-shot methodology. *Mitigation:* project mode still triggers only on explicit "start a research project" phrasing; the episodic shape is the default front door.

**Key assumptions (falsifiable).**
- *`methodology` is a distinct output topology, not a survey with headings* — falsified if, in practice, methodology artifacts are indistinguishable from `applied` surveys (see De-risk — currently confirmed on topology grounds).
- *A single shape template serves domains as far apart as dog-training and SDLC-modernization* — falsified if the six sections need per-domain specialization to be coherent (the thing to watch on the first real runs).
- *Contingency + maturity can be evidence-grounded from grey literature* — falsified if best-practice sources support the stages but not the situational branches or the progression ladder.

**Drawbacks.** One more shape enlarges the pack's surface (against the catalogue's bias toward few sharp primitives). Two skill bodies are touched (episodic + project). The six-section artifact asks more authoring judgment than a survey. These are accepted for a recurring, currently-unserved question-class.

## Evidence & prior art

**Spike / de-risk result.** *Riskiest assumption:* that `methodology` is a genuinely distinct shape and not redundant with `applied`-mode research — if false, the proposal duplicates an existing capability. *Result: distinct by construction (topology); empirical confirmation predeclared in Experiment / validation below, not asserted here.* An `applied` survey is organized by **claim** (what is true about X); a methodology is organized by **sequence + contingency + progression** (what to do, in what order, given the reader's situation). The lifecycle spine, the situational branches, and the maturity ladder are structurally absent from the survey form — this is the same relationship the pack already accepts between `survey`, `comparison-matrix`, `shortlist`, and `blueprint` (distinct shapes over one retrieval engine). But this is a *definitional* argument, and §1–§2 reuse tooling the neighbour `map-internal-process` also uses (see D4), so the claim that the *whole* artifact is a distinct topology — and not a survey the agent happened to structure under process headings — is worth a cheap check. That check is a **dogfood comparison**, not a code spike (the shape is prompt-only, like every existing shape — filename and structure produced by the agent, Charter Principle 3), and is predeclared below to run post-acceptance.

**Repo precedent.**
- `packs/research/.apm/skills/research/SKILL.md` — the "Type vocabulary" table; a shape is a row + trigger prose, filename by agent. Direct precedent for adding `methodology`.
- `packs/research/.apm/skills/research/references/methodologies.md` — the pack's existing catalogue of *research-method* disciplines (STORM, PRISMA, ACH, Wikipedia, OSINT, GIJN, GRADE). The methodology shape's six groundings are *artifact-structure* disciplines (one per section), a different kind, so they go in the new `methodology-shape-template.md` rather than extending this catalogue; the spec confirms the placement.
- `packs/research/.apm/skills/research-project-start/SKILL.md` (the `shape:` frontmatter vocabulary) + `research-project-synthesize/SKILL.md` (the shape→`<type>.md` mapping) — the project-mode surface D6 extends.
- RFC-0039 / ADR-0029 — the depth × lifecycle two-axis model; this extends the shape set on the depth/episodic side and the project `shape:` vocabulary, and reverses nothing.
- `packs/converters/.apm/skills/markdown-to-pptx/SKILL.md` — H1/H2 → slide, list → bullets, table → table: the concrete, already-shipped PowerPoint handoff (D5).
- `packs/product-engineering/.apm/skills/frame-domain` and `packs/experience/.apm/skills/map-internal-process` — the two neighbours D4 fences off.
- `docs/CHARTER.md` — the four bars, all cleared: **universal** (the shape is domain-agnostic — the motivating cases span data migration, fitness, consulting, dog-training, admissions); **substantive, not duplicative** (new topology, reused retrieval); **habit, not a tool** (prompt-only); **used often enough** (a recurring question-class).

**External prior art** (each fetched and confirmed to contain the borrowed claim):
- **Cognitive Task Analysis** — "a family of psychological research methods for uncovering and representing what people know and how they think", run as elicitation → analysis → representation ([Global Cognition](https://www.globalcognition.org/cognitive-task-analysis/)). → §5 failure modes.
- **Situational Method Engineering** — "the construction of methods which are tuned to specific situations" by selecting, tailoring and integrating reusable method components ([Method engineering, Wikipedia](https://en.wikipedia.org/wiki/Method_engineering)); a compiled set of **28 project contingency factors** to guide method selection to the situation ([Heupers & van Hillegersberg, 2011](https://aisel.aisnet.org/irwitpm2011/6/)). → §3 contingency branches.
- **Process mining / discovery** — "the main goal of process discovery is to transform the event log into a process model", used "when no formal description of the process can be obtained by other approaches" ([Process mining, Wikipedia](https://en.wikipedia.org/wiki/Process_mining)). → §2 stage spine.
- **SIPOC** — Suppliers · Inputs · Process · Outputs · Customers, a "high-level process snapshot … for quickly sorting out the boundaries and key elements of the process" ([SIPOC in VSM](https://boardmix.com/articles/sipoc-in-value-stream-mapping/)). → §1 scope frame.
- **Dreyfus model** — a progression through novice → advanced beginner → competent → proficient → expert (plus mastery) ([Dreyfus model, Wikipedia](https://en.wikipedia.org/wiki/Dreyfus_model_of_skill_acquisition)). → §4 maturity ladder.

These six disciplines converge on the same object from independent origins (cognitive psychology, software-method research, data science, lean/quality, expertise studies) — the same convergence pattern the pack already uses to justify its existing methodology.

## Experiment / validation

The shape's distinctness (the riskiest assumption) is argued definitionally above but not yet shown empirically. This validates it after ship; it does not reopen the decision to build the shape.

- **Hypothesis:** a `methodology` artifact is *structurally* distinct from an `applied` survey of the same topic — it carries a stage spine, contingency branches, and a maturity ladder the survey lacks, and the agent does not merely re-emit survey findings under process headings.
- **What we measure:** across the first 2–3 real methodology runs (e.g. one of the motivating cases — dog-training-by-breed, or the Ab-Initio→Databricks migration workbench), whether the artifact contains §3 contingency and §4 maturity content that a same-topic `applied` survey does not, and whether §1–§2 add sequencing/scoping beyond the survey's claim list.
- **Success / failure:** success = the methodology artifact is materially more than a re-headed survey on ≥2 of 3 runs; failure (→ revisit the shape vs. a survey-template via a superseding ADR) = artifacts are indistinguishable from an `applied` survey with process headings. Results in a linked spike note, not pasted here.

## Open questions

1. **Should the maturity ladder (§4) be mandatory for one-off deliverables** (a single migration) or reframed as an adoption/capability-maturity axis? Recommended default: **reframe, never omit silently** — mark the section as a capability-maturity axis when skill-progression doesn't apply, so the "journey" slide always exists. · owner: eugenelim · decide-by: implementing spec.
2. **Should a `methodology` project ever graduate to its own skill** if the six sections need per-domain specialization? Recommended default: **no for v1** — revisit only if the first real runs show the shape template can't stay domain-general. · owner: eugenelim · decide-by: post-ship review of the first 2–3 methodology projects.

## Follow-on artifacts

Filled in on acceptance. Anticipated:
- **ADR** — a *new* ADR (which *references*, never edits, the immutable Accepted ADR-0029) recording that shapes/types are the extension point for new output topologies and that `methodology` is the first to span both surfaces — only if the decision warrants its own record.
- **Spec** — `docs/specs/research-methodology-shape/`: the six-section template, the episodic row, the project-mode `shape:` value + synthesize branch, the D4 disambiguation edits, the D5 handoff note.
- **Reference** — `packs/research/.apm/skills/research/references/methodology-shape-template.md` (named distinctly from the existing `methodologies.md` to avoid misfiling): the artifact template + disciplinary grounding + worked exemplar.
- **Pack bump** — `packs/research` minor version; `docs/product/changelog.md` `[Unreleased]` entry.
