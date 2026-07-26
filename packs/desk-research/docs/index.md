# Desk Research

> A user-scope pack of 12 skills and two retrieval subagents for evidence-grounded research — from quick lookups to sustained multi-week investigations — grounded in seven convergent methodologies.

## Why this pack exists

Without structured research tooling, agents retrieve the nearest plausible answer from a single source without assessing quality, triangulating evidence, or flagging what they don't know. A prompt like "research the market for X" produces a confident summary with no provenance and no adversarial check. With this pack, every research output is multi-source, source-ranked, adversarially reviewed for counter-evidence, and available in typed artifact formats that downstream governance and strategy workflows can consume directly.

## What it is

**Skills (12) in two families:**

*Single-shot skills:* `desk-research` (evidence-grounded research with four depth modes: quick, standard, applied, deep), `build-outline` (decompose a research question into sub-questions using STORM and PRISMA framing), `source-map` (curate authoritative sources by surveying adjacent material), `identify-perspectives` (enumerate named camps on a contested topic before research begins), `compare-hypotheses` (compare competing hypotheses via an ACH evidence matrix with parallel per-hypothesis retrieval), `devils-advocate` (adversarial review of a research artifact for counter-evidence and irreducible tensions), `decision-archaeology` (reconstruct the rationale for a past decision from time-ordered artifacts).

*Project-mode lifecycle (four skills):* `desk-research-project-start` (scaffold a stateful multi-week research project), `desk-research-project-status` (read-only orient to the current project phase, hypothesis, and stop-signal), `desk-research-project-check` (qualitatively assess whether the corpus has reached saturation), `desk-research-project-digest` (build a synthesis matrix and analytic memos), `desk-research-project-synthesize` (produce a typed verdict and governance brief from the completed corpus).

**Subagents (2):** `evidence-retriever` (parallel retrieval across web and local sources), `source-extractor` (per-URL extraction and synthesis).

No seeds.

See the README for the complete manifest table.

## What it is not

- Not a web scraper or crawler — it retrieves and synthesizes; it does not crawl sites at scale or maintain a local index.
- Not a citation manager — it produces citations in-context for each research output, not a persistent bibliography database.
- Not a replacement for primary research — it synthesizes secondary sources (published literature, public data, expert writing); it does not conduct surveys, interviews, or experiments.

## How it relates to other packs

No required pack dependencies. Research outputs frequently feed `governance-extras` (to inform an RFC) or `architect` (to ground a design document). The `product-strategy` pack uses research methodology as the foundation for market analysis and competitive intelligence workflows.
