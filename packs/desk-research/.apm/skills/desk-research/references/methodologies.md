# Methodologies

The `/desk-research` pack rests on seven convergent disciplines from mature
fields. None of the seven is novel; the contribution is the convergence
— the same disciplines fall out of independently developed research,
journalism, intelligence, and evidence-synthesis traditions.

This reference catalogues each discipline's distinct contribution to
the skill bodies. The skill bodies themselves codify the convergent
moves; this document records which discipline is doing the work.

---

## STORM

STORM (Synthesis of Topic Outlines through Retrieval and
Multi-perspective question-asking) — Stanford NLP, 2024 — builds
Wikipedia-style topical outlines by surveying adjacent material and
asking what sections such an article would need. STORM's load-bearing
finding for this pack: **direct question-asking does not work well for
source discovery**. Asking the LLM "who is authoritative on X"
produces a training-data-shaped list; surveying adjacent material and
letting authorities fall out of the citation pattern produces a better
list. The discipline is **survey-by-adjacency**, and it is the
methodology under `/source-map` and the outline-stage in `/build-outline`.
Co-STORM (the moderator variant) contributes the **unused-snippet
pass**: scan retrieved-but-uncited material at the end and consider
one more query from the highest-signal unused snippet — that's the
trail you almost left on the table.

## PRISMA

PRISMA (Preferred Reporting Items for Systematic Reviews and
Meta-Analyses) — clinical research; the standard since 2009 — codifies
how systematic reviews report their methodology. PRISMA contributes
two disciplines to this pack. First, the **PICO framework**
(Population / Intervention / Comparison / Outcome) — a decomposition
shape that generalises beyond medicine: every research question has a
target, a variable, an alternative, and a criterion. PICO is the
decomposition mechanic under `/build-outline`. Second, the
**triangulation discipline**: a finding in a systematic review must
rest on multiple independent studies, not a single paper. This pack
borrows the ≥3 independent sources rule for material claims in
`/desk-research` standard / deep mode.

## ACH

ACH (Analysis of Competing Hypotheses) — Richards Heuer, CIA, 1999 —
is the intelligence-analysis discipline for forcing the analyst to
enumerate competing explanations before evaluating any of them. ACH
contributes three moves: **enumeration-first** (every viable
hypothesis named before scoring) — the methodology under
`/identify-perspectives`; the **matrix** (hypotheses × evidence-for /
evidence-against) — the methodology under `/compare-hypotheses`; and
the **evidence-against column** — explicitly listing what contradicts
each hypothesis, catching premature closure — the methodology under
`/devils-advocate`.

## Wikipedia (V/RS/NPOV)

Wikipedia's three core content policies have proven robust at scale:
**Verifiability** (every contested claim cites a reliable source),
**Reliable Sources** (a published source-curation discipline), and
**Neutral Point of View** (fairly represent significant views
proportionally to their prominence in reliable sources). The pack
borrows three disciplines from this triple: **citation-forcing per
claim** (every factual claim is cited or marked `[synthesis]` /
`[inference]`) — applies across every artifact-producing skill;
**source-curation by primacy** (primary / secondary / tertiary) —
codified in `/source-map`; and **NPOV proportional representation**
— the methodology under `/identify-perspectives`.

## OSINT

OSINT (Open-Source Intelligence) — intelligence-community tradecraft
applied to publicly available sources — contributes the
**triangulation discipline** convergently with PRISMA: no claim from a
single source should be treated as established. OSINT's contribution
beyond PRISMA is the **primacy taxonomy** (primary / secondary /
tertiary) and the rule that **three tertiary sources citing the same
primary source count as one**. Convergent with Wikipedia's
Reliable-Sources policy; codified in `/source-map`'s primacy tagging
and `/desk-research`'s ≥3 independent-sources rule.

## GIJN

GIJN (Global Investigative Journalism Network) journalism handbook —
the standard for serious investigative reporting — contributes the
**seek-the-other-side discipline**: before publication, ask "what
does the other side say?" and seek out the answer. The pack borrows
this as the methodology under `/devils-advocate` (convergent with
ACH's evidence-against column) and as a final-step gate in `/desk-research`
deep mode. GIJN also contributes the discipline of **document trail
walking**, which the pack borrows in `/decision-archaeology`'s
chronology-by-artifact procedure.

## GRADE

GRADE (Grading of Recommendations Assessment, Development and
Evaluation) — the evidence-quality framework used in clinical
practice guidelines worldwide — contributes the pack's **confidence
schema**: every finding is rated `high` / `moderate` / `low` /
`uncertain`, with **named downgrade factors** (single source, no peer
review, vendor-blogged, contested-in-field, heterogeneity,
indirectness). GRADE's load-bearing discipline: confidence is not
asserted, it is rated against an explicit framework, and downgrades
are named, not silently applied. The full schema lives in
`confidence-schema.md`.

---

## Convergence

The seven disciplines independently emphasise five moves: enumerate
positions before evaluating, cite every claim, triangulate against
multiple independent sources, seek the other side, and rate
confidence explicitly with named reasons. The pack's skill bodies
codify these five convergent moves; this reference catalogues which
discipline supplies which.
