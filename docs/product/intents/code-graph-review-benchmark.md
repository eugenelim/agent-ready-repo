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
