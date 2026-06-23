# Survey: Best practices for managing a sustained research project

> Discipline: applied (practitioner-pattern survey)
>
> Research note for [RFC-0039](../0039-research-project-mode-and-typed-artifacts.md). Promoted from session scratch to durable state 2026-06-22. This is the distilled brief; the raw retriever corpus (four `evidence-retriever` outputs) was session scratch and is not committed.

Question: how do the established research disciplines manage a sustained,
multi-source investigation — continually gathering sources, managing a growing
corpus, then extracting, synthesising, and forming/refining a hypothesis toward
an actionable verdict? And what artifact/file taxonomy maps to *research type*
rather than a single generic `research.md`?

Surveyed four disciplines: systematic review (PRISMA/Cochrane + Webster & Watson),
personal knowledge management (Zettelkasten, PARA, LYT/MOC, Progressive Summarization,
evergreen notes), qualitative research (grounded theory, thematic analysis), and
intelligence analysis (ACH, SATs, ICD 203, Admiralty code).

## The convergent pattern (the load-bearing finding)

Every discipline, independently, splits a sustained research effort into **three
layers with distinct artifacts**, and *none* of them keeps the whole thing in one
file. [high]

| Layer | Systematic review | PKM (Zettelkasten) | Qualitative | Intelligence (ACH) |
|---|---|---|---|---|
| **1. Raw capture** | search log, screening sheet, included studies | fleeting + literature notes | transcripts / field notes | evidence & arguments list |
| **2. Working / "thinking on paper"** | extraction table, **concept/synthesis matrix** | permanent notes (zettels) | **codebook + analytic memos** | **ACH matrix** (evidence × hypotheses) |
| **3. Synthesised output** | the review + GRADE summary-of-findings | MOC / outline note → manuscript | themes / grounded theory | analytic assessment |

The middle layer is the one our pack lacks. It is where the corpus is *digested* so
that growth stays tractable — you reason over the matrix/memos, not by re-reading every
source. Webster & Watson's concept matrix (rows = sources, columns = concepts), grounded
theory's analytic memos, and the ACH matrix are the same idea in three vocabularies. [high]

## Findings

**F1 — Distinct, named artifacts per stage; never one generic doc.** [high]
PRISMA/Cochrane name ~12 artifacts (protocol, PICO statement, per-database search
strategy, search log, dedup record, screening forms, extraction form, characteristics
table, risk-of-bias table, GRADE profile, flow diagram, manuscript). Zettelkasten names
three note tiers; qualitative names codebook/memos/themes; ACH names five (hypothesis set,
evidence list, matrix, sensitivity analysis, key-indicator list). The artifact *type* is
the unit, and each carries its own schema. This is direct evidence for naming a research
file by its type, not `research.md`.
Sources: PRISMA 2020 (PMC8007028, primary); Cochrane Handbook ch.1/ch.5 (primary);
Heuer, *Psychology of Intelligence Analysis* ch.8 (primary).

**F2 — Raw capture is separated from synthesis by an explicit, never-overwritten
boundary.** [high] Cochrane: retain "as-extracted" data distinct from the consensus
version, with provenance of every datum (source document vs. calculated). Zettelkasten:
fleeting → literature → permanent, with a forcing function (drain fleeting notes within
days). Progressive Summarization: layers are *additive* (L0 source always survives under
L4 summary). Grounded theory: raw transcript ≠ coded excerpt ≠ memo ≠ theory.
Sources: Cochrane ch.5 (primary); zettelkasten.de Collector's-Fallacy (primary);
fortelabs.com Progressive Summarization (primary); SimplyPsychology GT (primary).

**F3 — Two distinct hypothesis-timing modes — and this is the crux for "form a
hypothesis".** [high] The disciplines split cleanly:
- **Hypothesis-first (top-down, confirm/refute):** ACH enumerates *all* plausible
  hypotheses before marshalling evidence and scores the matrix for *inconsistency*
  (the survivor is least-disconfirmed, not most-supported — Popperian). PRISMA locks a
  PICO question and protocol *before* searching.
- **Hypothesis-emergent (bottom-up):** Grounded theory forbids entering with a prior
  theory — theory emerges via open→axial→selective coding and constant comparison, and
  is *revised continuously* as theoretical sampling pulls new data to fill gaps.
  Zettelkasten's slip-box "talks back": the thesis emerges from accumulated links.

A research-project tool must support both. A hard "refuse without a central claim" gate
(the wiki-kit v1 rule) is correct for the ACH/PICO path and *wrong* for the grounded-theory
path, where forcing a premature claim is itself the named failure mode ("forcing data into
preconceived categories"). The reconciliation: a **working hypothesis** that is allowed to
be provisional/empty and is explicitly revised as evidence accumulates. [synthesis]
Sources: Heuer ch.8 (primary); ICD 203 std.4 (primary); SimplyPsychology GT (primary);
Springer emergence-vs-forcing (primary); ICD 203 std.7 "analytic line" (primary).

**F4 — Every discipline has a *stop signal* tied to corpus change, not headcount.** [high]
Grounded theory: **theoretical saturation** (new data yields no new codes; core category
stable). Thematic analysis (Braun & Clarke 2019) explicitly *rejects* saturation-as-a-
sample-size-number — it's a property of theme development. ACH: sensitivity analysis +
key-indicator list re-open a closed judgment. PKM: the "mental squeeze point" (Milo) and
diminishing-returns on the inbox drain. The convergent rule: **stop when new sources stop
changing the structure.** This is exactly wiki-kit's passive verdict-check, with academic
backing.
Sources: delvetool GT (secondary); PMC9879167 Braun & Clarke (primary); Heuer ch.8
(primary); Obsidian-Rocks MOC (secondary).

**F5 — Source provenance is graded, not binary.** [high] Intelligence uses the
Admiralty code: two *independent* axes — source reliability (A–F) and information
credibility (1–6); credibility "1" *requires* independent corroboration. Systematic review
grades risk-of-bias per study and certainty per outcome (GRADE). Zettelkasten keeps a
two-hop provenance chain (zettel → literature note → source). Our pack's GRADE confidence
+ ≥3-source triangulation already sits in this family and is *stronger* than wiki-kit v1's
binary Two-Source Rule; the upgrade is to record reliability and corroboration as separate
axes per source (Admiralty's independence discipline).
Sources: Admiralty code / NATO AJP-2.1 (primary); PRISMA 2020 (primary); zettelkasten.de
(primary).

**F6 — The named failure modes converge across all four disciplines.** [high]

| Failure mode | Named by | Guard |
|---|---|---|
| Browsing without a claim / **collector's fallacy** | Zettelkasten; ACH | working hypothesis or question up front; drain the inbox |
| **Premature closure** | Heuer; GT; PRISMA | complete the matrix / reach saturation before concluding; pre-registered protocol |
| **Confirmation / single-hypothesis bias** | ACH; ICD 203 | enumerate *all* hypotheses; score for disconfirmation; analysis-of-alternatives |
| **Single-source over-reliance** | Admiralty; PRISMA | corroboration required for top credibility; multi-database mandate |
| **Forcing data into preconceived categories** | Glaserian GT | let codes/themes emerge; delay frameworks |
| **Mistaking consistency for diagnosticity** | ACH | drop evidence consistent with *all* hypotheses from the matrix |

Sources: as above; PMC9879167 (primary); Heuer ch.4/ch.8 (primary).

## What this means for quick-vs-project (synthesis)

A **one-shot lookup** has no corpus to manage, so layers 1–3 collapse into a single
inline answer — no separation, no middle layer, no stop signal needed. This is our `quick`
mode, and it is *correct* that it produces no artifact. [synthesis]

A **research project** is defined precisely by the things a lookup lacks: a corpus that
grows over time, a never-overwritten raw layer, a working/digest layer that keeps growth
tractable, a working hypothesis that is tracked and revised, and a saturation/stop signal.
These are not "more research" — they are a *different kind* of object with its own
lifecycle. [synthesis]

## Known unknowns

- **Known-unknown:** which middle-layer artifact (a Webster-style concept matrix vs.
  grounded-theory memos vs. the ACH matrix) is the best default for an LLM-driven project.
  Would be closed by: a small bake-off across 2–3 real projects.
- **Known-unknown:** whether a fixed column set (wiki-kit's four pillars) or emergent
  columns (grounded theory) digests a corpus better in practice. Closed by: the same bake-off.
- **Unknowable (as posed):** whether these disciplines' guards actually improve *accuracy*
  rather than just documentation discipline — the ACH/ICD 203 empirical literature is
  inconclusive (RAND RR1408; Dhami 2019), so this can't be settled from available evidence.

## Stale-pattern flags

- Webster & Watson (2002) predates modern citation tooling; the concept-matrix pattern
  holds, the manual forward/backward citation trace is now tool-assisted.
- The Admiralty F6 rating is now the *modal* OSINT case (machine-generated content),
  eroding its discrimination at the low-reliability end.
- LYT/evergreen patterns assume bidirectional linking; they degrade in flat-file systems.

## Citations (selected; full lists in retriever outputs)

Primary: PRISMA 2020 (PMC8007028); Cochrane Handbook ch.1, ch.5; Heuer, *Psychology of
Intelligence Analysis* (CIA CSI); ICD 203 (ODNI); Admiralty/NATO AJP-2.1; Braun & Clarke
2022 (PMC9879167); Thomas & Harden 2008 (PMC2478656); Matuschak evergreen notes;
fortelabs.com PARA + Progressive Summarization; zettelkasten.de Collector's Fallacy.
Secondary: delvetool GT/TA; Webster & Watson summaries; Pherson SAT taxonomy;
McGill/KCL search-recording guides; USI literature-matrix guide.
