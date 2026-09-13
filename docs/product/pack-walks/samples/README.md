# Worked output samples

One real artifact per skill that ships no output template.

## Why these exist

A guidebook step shows the reader an excerpt of the artifact they are about to
receive. Where a skill ships a template, the excerpt is taken verbatim from it
and the lint checks it is still there, so it cannot drift.

Where a skill ships **no** template, there was nothing to excerpt — and a
shape-only preview built from section names is precisely where a guide can
quietly teach the wrong thing. A reader cannot tell whether a stage is a
paragraph or a table, how long the artifact runs, or what a good entry looks
like next to a weak one, from a list of headings.

So the skill is **run**: its procedure is followed step by step against one
scenario, and the artifact it produces is kept here. The guidebook excerpts
from the result, and the lint compares the excerpt against this file exactly as
it does against a real template.

## What they are and are not

- **They are** worked examples — one plausible run of the skill, with real
  content, produced by following the skill's own procedure.
- **They are not** a specification. The skill decides its own output; if the two
  disagree, the skill is right and the sample is stale.
- The scenario is **fictional throughout**, so nothing here is a claim about a
  real company, market or number.

Each file says at the top which skill produced it and against what scenario.

## Adding one

Run the skill's procedure against a small, self-contained scenario — the same
one across a pack, so the artifacts read as one coherent thread rather than
several unrelated demos. Keep it short enough that the first twenty lines convey
the form, because that is what the guidebook shows.
