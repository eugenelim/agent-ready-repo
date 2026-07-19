# Research methodology — the why behind the pack

The `desk-research` pack ships eleven skills (seven for episodic depth, four for the project lifecycle) and two retrieval subagents. This page is about the *episodic* skills' methodology — the shapes look obvious in retrospect — modes on `/desk-research`, a flat directory layout, citations forced per claim — but each is a deliberate choice driven either by a mature discipline borrowed from a neighboring field or by an architectural finding from multi-agent research. This page tells the story behind those choices. For the project lifecycle and the two-axis model, see [episodic vs project research](episodic-vs-project-research.md).

For the catalogue of what the pack ships, see the [reference](../reference/desk-research-pack.md). For how to use it, see the [how-to guide on pipelines](../how-to/desk-research-pipelines.md) or the [first-session tutorial](../tutorials/desk-research-first-session.md).

## Seven convergent methodologies

The pack rests on seven disciplines from mature fields — academic research, intelligence analysis, journalism, clinical evidence synthesis, and large-scale collaborative encyclopedia practice. None is novel; the contribution is that they *converge* on the same five moves.

### STORM

Stanford's Synthesis of Topic Outlines through Retrieval and Multi-perspective question-asking builds Wikipedia-style topical outlines by surveying adjacent material and asking what sections such an article would need. The load-bearing finding: **direct question- asking does not work well for source discovery**. Asking the LLM "who is authoritative on X" produces a generic, training-data-shaped list. Surveying adjacent material and letting authorities fall out of the citation pattern produces a better one. This is the methodology under `/source-map`. Co-STORM (the moderator variant) contributes the **unused-snippet pass** — scan retrieved-but-uncited material at the end and consider one more query from the highest-signal unused snippet.

### PRISMA

Preferred Reporting Items for Systematic Reviews and Meta-Analyses — the standard for reporting clinical systematic reviews since 2009 — contributes two disciplines. **PICO** (Population, Intervention, Comparison, Outcome) is a decomposition shape that generalises beyond medicine: every research question has a target, a variable, an alternative, and a criterion. PICO is the mechanic under `/build-outline`. The **triangulation discipline** — a finding must rest on multiple independent studies — supplies the ≥3 independent sources rule for `/desk-research` standard and deep modes.

### ACH

Analysis of Competing Hypotheses — Richards Heuer, CIA, 1999 — forces the analyst to enumerate competing explanations before evaluating any of them. ACH supplies three moves: **enumeration-first** (every viable hypothesis named before scoring) under `/identify-perspectives`; the **matrix** (hypotheses × evidence-for / against) under `/compare-hypotheses`; and the **evidence-against column** — explicitly listing what contradicts each hypothesis — under `/devils-advocate`. The discipline catches premature closure: the model finds three supporting sources, stops, declares done. ACH refuses that move.

### Wikipedia (V/RS/NPOV)

Wikipedia's three core content policies — Verifiability, Reliable Sources, Neutral Point of View — have proven robust at encyclopedia scale. The pack borrows three disciplines: **citation-forcing per claim** (every factual claim is cited or marked `[synthesis]` / `[inference]`); **source-curation by primacy** (primary / secondary / tertiary); and **NPOV proportional representation** — `/identify-perspectives` doesn't just name the camp the model finds most credible.

### OSINT

Open-Source Intelligence tradecraft contributes the **triangulation discipline** convergently with PRISMA, plus the **primacy taxonomy** and the rule that **three tertiary sources citing the same primary source count as one**. Codified in `/source-map`'s primacy tagging.

### GIJN

Global Investigative Journalism Network's handbook supplies the **seek-the-other-side discipline** — before publication, ask "what does the other side say?" and seek it out. The pack borrows this as the methodology under `/devils-advocate` and as a final-step gate in `/desk-research` deep mode. GIJN also supplies the **document trail walking** discipline behind `/decision-archaeology`.

### GRADE

Grading of Recommendations Assessment, Development and Evaluation — used in clinical practice guidelines worldwide — supplies the pack's **confidence schema**: every finding is rated `high` / `moderate` / `low` / `uncertain`, with **named downgrade factors**. GRADE's load-bearing discipline is that confidence is **computed against an explicit framework, not asserted**, and downgrades are named, not silently applied.

### Convergence

The seven disciplines independently emphasise five moves: enumerate positions before evaluating, cite every claim, triangulate against multiple independent sources, seek the other side, and rate confidence explicitly with named reasons. The pack's skill bodies codify these five convergent moves.

## Architectural choices

Five design decisions shaped the pack. Each one fell out of a specific failure mode in earlier drafts or a specific finding in the multi-agent research literature.

### Mode-on-research (the mode parameter)

`/desk-research` carries a formal `mode: quick | standard | deep` parameter with `quick` as default. The alternative considered was splitting into separate skills — `/lookup` for casual, `/desk-research` for standard, `/deep-research` for deep. We rejected the split.

The misfire mode is **description-collision**: an LLM seeing both `/lookup` and `/desk-research` descriptions has to choose which to fire on a casual prompt, and the casual prompt's wording rarely disambiguates cleanly between two skills whose descriptions both name "research" cues. The mode parameter consolidates the cues into one skill body and lets the description bias clearly — casual phrasings stay `quick`, explicit phrasings escalate. The collision argument that motivates mode here does *not* apply to the other six skills, so they use depth-via-prompt cues rather than formal modes (and the pack defers any formal-mode promotion until misfire evidence emerges).

One follow-on consequence worth naming: the depth-cue vocabulary on the other six skills (`quickly`, `comprehensively`, `in depth`, etc.) overlaps the cue tokens that bias `/desk-research` between modes. The disambiguation is **the skill name in the prompt**, not the cue token alone — `comprehensively map the sources` is a depth cue to `/source-map`, not a re-dispatch into `/desk-research` deep mode. The cue applies at whichever skill the user named.

### Applied mode — the practitioner-discipline extension

The original mode parameter shipped three values — `quick`, `standard`, `deep` — across one axis (depth). Use-case feedback surfaced a second axis the schema had collapsed onto standard: **discipline**. A prompt like "best ways to optimise inventory for shipping" wants prior-art / best-practice work across practitioner grey literature (blogs, conference talks, vendor case studies, community threads), not peer-reviewed material. Running it in standard mode produced findings rated `[low]` by construction — the GRADE schema's `no peer review` downgrade factor applied to every finding, because the domain has no peer-reviewed alternative.

The alternative considered was a standalone `/applied-research` or `/patterns` skill. We rejected it on the same description-collision grounds that motivated mode-on-research in the first place — a user saying "look up best practices for X" should not have to think about which slash command to type. Instead the mode parameter extends to four values (`quick | standard | applied | deep`), with applied as the fourth flat value alongside the existing three. The discipline extension lives in the same skill body; the dispatcher picks the mode from the prompt's cues.

The mechanism the overlay introduces is in `references/confidence-schema.md`: an `Applied-mode overlay` section drops `no peer review` from the closed downgrade-factor set (practitioner domains have no alternative by construction), and adds `survivorship bias` (only successes blog; failures rarely do) and `stale prior art` (>5-year-old patterns in fast-moving domains are suspect). The `mode` parameter is the rule-set selector; the artifact's discipline marker — `> Discipline: applied (practitioner-pattern survey)` — is the post-condition audit signal, not a way to retroactively re-rate findings.

Cue precedence — **applied cues are scored before standard / deep cues** — closes the obvious collision: a prompt like "comprehensively survey the applied patterns for X" contains both `comprehensively` (a standard cue) and `applied patterns for` (an applied cue); precedence puts it in applied mode. The four applied cue phrases (`applied patterns for`, `best practice for`, `prior art on`, `grey literature`) are phrase-shaped rather than bare words — refusing the failure mode where `applied` alone would trigger on incidental academic mentions ("GRADE has been applied to clinical reviewing").

### Retrieval-only subagents

The pack ships two subagents — `evidence-retriever` and `source-extractor` — both strictly read-only and strictly retrieval- shaped. The alternative considered was reasoning subagents that would synthesise findings, propose ratings, or compose pipelines. We rejected reasoning subagents on three lines of evidence:

- Cognition's "Don't Build Multi-Agents" essay: multi-agent reasoning pipelines lose information at each handoff and produce worse results than a single agent at equal token budget.
- A UC Berkeley study reporting ~79% handoff-failure rate on multi-agent reasoning tasks.
- arXiv 2604.02460: single-agent outperforms multi-agent at equal token budget on multi-hop reasoning.

Retrieval, in contrast, is parallelizable and context-bounded — exactly the +81% parallelizable-task case the multi-agent literature identifies. The two subagents do retrieval-and-condense; reasoning stays in the main session.

### Flat directory layout

`references/` and `scripts/` under each skill are kept flat — one level of files, no nested subdirectories. The agentskills.io specification recommends one-level-deep file references, and the convergent in-pack precedent (`packs/converters/` and others) follows it. The rule is in the pack's Boundaries as a hard `Never do`. The benefit is that adopters reaching into the skill don't have to walk a tree to find a specific reference document or retriever script.

### Citation-forcing per claim

Every artifact-producing skill documents the rule: a factual claim in an artifact carries a citation, or is marked `[synthesis]` (an integration across cited material) or `[inference]` (a defensible deduction from cited material). The discipline comes from Wikipedia Verifiability and GRADE convergence. The failure mode it prevents is **plausible-sounding LLM output with no traceable backing** — the most common research-mode misfire on an LLM that's been trained on a lot of unattributed material.

### Moderator unused-snippet pass

Before declaring a standard or deep artifact done, the skill scans retrieved-but-uncited material and considers one more query from the highest-signal unused snippet. This is Co-STORM's contribution. The failure mode it prevents is the **almost-citation** — the model retrieved the piece of material that would have shifted a rating, but never reached for it in the synthesis. The moderator pass is documented in `/desk-research`'s and `/devils-advocate`'s SKILL.md bodies.

### Internal knowledge surfaces, not just the open web

Quick mode reads the open web — WebFetch and WebSearch, nothing else. Standard and deep mode go wider. Before dispatching, `/desk-research` enumerates retrievers from three surfaces: the built-in web tools, any retrieval-shaped MCP tools the session exposes (search engines, vector stores, **internal knowledge bases**, authenticated services), and user-registered script retrievers at `scripts/<name>-retriever.py`. A question that turns on your org's private knowledge isn't capped at what's publicly indexed — it pulls from the internal surfaces available in the session, and each claim's citation records which retriever it came from.

## Where this lives

Every architectural choice above is enforced by the spec's acceptance criteria. The pack's `references/methodologies.md` catalogues each discipline's distinct contribution; this explanation tells the story across them.
