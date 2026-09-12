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

## Owner decision, 2026-09-10 — deferred for single-repository use

**Graphs are deferred, not rejected.** A graph is a derived artifact, so it
carries a freshness problem: it answers from a snapshot, and the answer degrades
silently between builds. Cheap on-demand exploration reads live state, so it
cannot be stale — which is the whole argument for a single repository, where the
seed set is small and a search costs seconds. This repository already holds the
same position in one place and says why: a fingerprint baseline is the *one*
stored value allowed to go stale, and only because its going stale is the
mechanism rather than the answer.

**Graphs across repositories are a different question and outside this system's
scope.** A cross-repository edge cannot be found by searching one repository's
live tree, so the trade reverses and a built index starts to earn its cost. That
is not deferred on evidence; it is out of scope, and this intent does not carry
it.

What stays live here is the narrow benchmark: if a graph is ever proposed for
single-repository use, it is measured against on-demand exploration rather than
adopted on the strength of the idea.

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
