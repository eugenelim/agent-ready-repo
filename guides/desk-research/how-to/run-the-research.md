---
title: Research a question
summary: Turn a question into an evidence-graded answer, with the strongest objections written down.
pack: desk-research
uses: [desk-research]
kind: how-to
aliases:
  - guides/desk-research/how-to/scope-the-question
  - guides/desk-research/how-to/challenge-the-result
  - guides/desk-research/how-to/run-it-as-a-project
---

# Research a question

Ask your agent a question in plain words, and each step below writes one file named after your topic.

## Scope the question

To split the question into the sub-questions a thorough answer must cover, ask:

```text
Decompose this question into the sub-questions a thorough answer has to cover: should we adopt server-side rendering for our marketing site?
```

The agent writes `<topic-slug>-outline.md`, where the slug is a short name for the topic. Before it gathers evidence, it asks you to confirm the scope and depth. For a contested question, ask for `identify-perspectives` to name the camps and `source-map` to rank the sources.

## Run the research

To gather evidence at a depth you choose, ask:

```text
Research this at applied depth: what do teams actually report after moving a marketing site to server-side rendering? Cite primary sources.
```

The agent writes `<topic-slug>-survey.md` with a confidence tag on every finding and a list of what the evidence could not answer.

## Challenge the result

To find where the survey is weakest, ask:

```text
Argue against this survey. Find the strongest counter-evidence for each finding and tell me which ones should be downgraded.
```

The agent writes `<topic-slug>-counterpoints.md`, giving each finding a verdict. For a decision between options, `compare-hypotheses` scores each option against the same evidence.

## Run it as a project

For a question that needs weeks, start a research project instead:

```text
Start a research project on how teams operate design systems at scale. This runs over several weeks.
```

The agent creates a project folder with an overview and a working hypothesis. Ask for `desk-research-project-status` at any point to see the phase and what to do next.

## Write the final brief

When new sources stop changing the findings, ask:

```text
Synthesize the project into its verdict and write the governance brief.
```

The agent writes the verdict file and `<topic-slug>-brief.md` in the project folder, with gaps named rather than smoothed over. You review the synthesis before you act on it.

Next, [analyse the market](../../product-strategy/how-to/run-a-market-and-competitive-analysis.md) with what you found.
