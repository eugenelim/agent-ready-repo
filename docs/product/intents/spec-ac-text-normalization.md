# Residual Acceptance-Criteria reader divergence

- **Status:** Draft
- **Level:** feature

## Outcome

A decision on whether the remaining disagreement between the four
Acceptance-Criteria readers is worth closing, now that its one reachable shape
is a hard error. Either close it deliberately, or record that the guard is the
answer and stop revisiting it.

## Opportunity

Enforcement did the work that was worth doing, and this is what it did not
reach.

Shipped in PR #1139: one supported heading (`## Acceptance Criteria`, exact,
with a near-miss warning naming the exact form); six drifted specs normalized,
verified meaning-preserving; a commented-out Acceptance-Criteria section is a
hard error; every attempted opt-out shape is diagnosed rather than silently
escaping; an unresolvable `--base-ref` warns and skips instead of red-lining a
clean corpus; and a spec the linter cannot read is warned about rather than
reported clean.

What remains is only this: the readers still hold different notions of which
text counts. `acceptance_criteria_opt_out` and its near-miss sibling strip HTML
comments — they must, because 245 of 407 specs carry template comments in the
metadata preamble they scan. The section detector and criterion collector do
not, because no spec needs it. The shipped guard makes the one shape where that
disagreement is reachable — a commented-out section — a hard error, so the
divergence cannot produce a passing spec. It is bounded, not resolved.

The question is whether bounded is enough. Four review rounds of *resolving* it
produced, in sequence, a cubically backtracking code-span regex (12 KB line →
106 s), a Θ(L^1.5) replacement (1 MB → 15.0 s), fence state read from raw text
that let a commented-out fence swallow a live section, and comment-blind fence
pairing that made an example heading count as a real section. Each passed its
own verification before review caught it.

## Assumptions

- Banning the constructs is not available. 251 of 407 specs carry a real HTML
  comment, 245 of those in the metadata preamble, all 407 use inline code spans,
  and the new-spec template emits 16 comments itself — including on the
  `- **Status:**` line. Both are load-bearing spec detail.
- The readers having different jobs is not itself the bug. The preamble reader
  must strip comments; the body readers gain nothing by it and lose correctness,
  because the naive `<!--.*?-->` pattern has no notion of code spans and
  `docs/specs/digital-experience-contract/spec.md` pairs two backticked
  *mentions* into a false span over its real heading and all 17 criteria.
- If this is picked up, it is a parsing decision, not a regex tweak: a real
  Markdown parser (a dependency decision for a script that projects into adopter
  trees) versus narrowing what the readers must understand so the question does
  not arise.
- Any complexity claim here needs at least three doublings. A withdrawn fix was
  declared correct on a single benchmark point, which moved a constant and hid
  an exponent.
- Every precedence rule needs a test that dies under mutation. Three rules in a
  withdrawn attempt could each be neutered with the whole suite green, including
  the one whose docstring cited a live spec.
- `tools/build-site.py` carries the same code-span blindness over changelog
  prose. It is tracked separately as
  `build-site-comment-strip-ignores-code-spans` — different module, different
  file, and it has already fired.
- Reproducing fixtures and measurements are in PR #1139's review history.

## Source

- Mode: repo-origin
- Locator: packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py
- Revision: sha256-bytes-v1:45492bdceb9a6ddb3d3fa7ec03c0aeacd9d27d7d970105f83e14905c511c2c9c
