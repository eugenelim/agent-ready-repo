# Desk Research

Your agent can research a question from sources it cites, grade how sure it is, and keep a long investigation going across sessions.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install it once for your user account:

```bash
agentbundle install --pack desk-research
```

In Claude Code you can install it as a plugin instead:

```bash
claude plugin install desk-research@agent-ready-repo
```

## What your agent can do

- Answer a look-up, fact-check, or survey with citations, at a depth you pick from quick to deep.
- Map the authoritative sources and the competing viewpoints on a topic before it searches.
- Compare competing hypotheses in an evidence matrix.
- Argue against its own findings and downgrade claims that do not hold up.
- Run a research project over days or weeks, then write a brief with each claim graded by evidence quality.
- Reconstruct why a past decision was made from commits, pull requests, and design docs.

## Skills

- **`desk-research`** — Researches one question in one session, with citations and graded claims.
- **`source-map`** — Curates the authoritative sources on a topic before research starts.
- **`build-outline`** — Breaks a question into the sub-questions a full answer must cover.
- **`identify-perspectives`** — Names the camps on a contested topic before research begins.
- **`compare-hypotheses`** — Scores competing hypotheses in an evidence matrix.
- **`devils-advocate`** — Searches for counter-evidence and names the strongest objections.
- **`decision-archaeology`** — Reconstructs the reasoning behind a past decision.
- **`desk-research-project-start`** — Starts a multi-week research project.
- **`desk-research-project-status`** — Shows the project's phase, working hypothesis, and next step.
- **`desk-research-project-check`** — Reports whether new sources have stopped changing your picture.
- **`desk-research-project-digest`** — Builds the synthesis matrix and notes from your sources.
- **`desk-research-project-synthesize`** — Writes the verdict and a self-contained brief.

Subagents, called for you: **`evidence-retriever`** fetches sources with citations, and **`source-extractor`** pulls the content out of each one. Both are read-only.

## Works with

Works with Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, and Kiro IDE. [Product Strategy](../product-strategy/README.md) reads your survey as evidence for its stakeholder research. [Architect](../architect/README.md) can cite a research brief in a design decision. See [Research a question](../../guides/desk-research/how-to/run-the-research.md), which also covers research projects.

## Questions

**How do I pick between a quick answer and a project?** Use one session for a look-up, a fact-check, or a brief. Start a project when the question needs days or a growing pile of sources.

**Can I trust the citations?** Each claim carries a grade and its sources, and the devil's advocate pass looks for counter-evidence. Check any claim that matters against its source.

**Does it save my research into project memory?** Not unless you choose to. Research keeps its own sources and verdicts. After a finished repository survey or project synthesis, it may offer a reusable lesson to `project-knowledge`.

**Does it edit my code?** No. The retrieval subagents are read-only.

## Details

Scope: user (default), repo · Version: 1.1.10 · Source: [packs/desk-research](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/desk-research)
