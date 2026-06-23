# `research` — guides

Evidence-grounded research, with the depth dialed to the question. `/research` runs anything from a quick look-up to a deep investigation, grading its confidence as it goes. Around it sit the pipeline skills — `build-outline`, `source-map`, `identify-perspectives`, `compare-hypotheses`, `devils-advocate`, `decision-archaeology` — and two retrieval subagents that do the fetching.

The pack has two axes. **Depth** (above) is episodic — one-shot questions. **Lifecycle** is *project mode*: four `research-project-*` skills for a sustained, multi-week investigation that accumulates a corpus and ends in a brief you can hand to a decision. [Episodic vs project research](explanation/episodic-vs-project-research.md) explains when to reach for which.

New here? Walk [your first research session](tutorials/research-first-session.md), then reach for [the pipelines](how-to/research-pipelines.md) when one question needs several skills working together. For a sustained investigation, walk [your first research project](tutorials/your-first-research-project.md).

## Tutorials

- [Your first research session](tutorials/research-first-session.md) — install the pack and run `/research` across all four depth modes.
- [Your first research project](tutorials/your-first-research-project.md) — run the project lifecycle end to end: start, capture, digest, synthesize a brief.

## How-to

- [Run the research pipelines](how-to/research-pipelines.md) — the survey, decision, and archaeology recipes, and what each one produces.
- [Run a research project and feed it into an RFC](how-to/run-a-research-project-into-an-rfc.md) — drive the lifecycle, then promote the brief into an RFC's `NNNN-notes/` companion and *Evidence & prior art*.

## Reference

- [Research pack reference](reference/research-pack.md) — every skill (episodic and project), the two retrieval subagents, the depth modes, the project folder layout and `research-layout.toml`, and the GRADE confidence schema.

## Explanation

- [Research methodology — the why behind the pack](explanation/research-methodology.md) — why depth is selectable, why sourcing comes before answering, and where confidence grades come from.
- [Episodic vs project research — the two axes](explanation/episodic-vs-project-research.md) — depth vs lifecycle, the digest middle layer, and when a question deserves a project.

---

Installing, upgrading, and the adapter support matrix live in [`../_shared/`](../_shared/).
