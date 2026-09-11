# Code-graph review benchmark

- **Status:** Draft
- **Level:** feature

## Outcome

Measure whether graph-assisted exploration improves code-review findings over
repository-native targeted exploration.

## Opportunity

Use controlled A/B review tasks to compare valid finding yield, false-positive
rate, review time, and graph setup and maintenance cost before deciding whether
code-graph infrastructure is worth adopting.

## Authoring-side evidence, 2026-09-10

[The grounding-probes survey](../research/repository-grounding-probes-survey.md)
answers the adjacent question for *authoring* rather than review, and reaches the
same position from the other side: seed-bounded probes over a change's touched
paths are cheap and find real constraints, while a global repository map is the
wrong shape because its cost scales with the repository and its truncation drops
the rare edge. It also records what the benchmark here would have to beat — five
working probes, their calibration thresholds, and five mechanisms this repository
already built and killed.

That survey does not discharge this benchmark. It measures cost and records one
slice's defect history; it does not run the controlled A/B this intent asks for,
and it says so under its own known-unknowns.

## Assumptions

- Current evidence does not establish that a repository graph improves review
  effectiveness.
- The benchmark can hold reviewer instructions, task corpus, and adjudication
  criteria constant while varying the exploration method.
- This intent does not authorize adopting or requiring a code-graph provider.

## Source

- Mode: repo-origin
- Locator: docs/specs/work-loop-review-verdicts/notes/code-graph-code-review-effectiveness-survey.md
- Revision: local-2026-08-23
