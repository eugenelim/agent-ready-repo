# Enforce one spec format tightly, instead of parsing every variant

- **Status:** Draft
- **Level:** feature

## Outcome

`docs/specs/*/spec.md` has one supported shape and the linter enforces it, so
the tooling never has to decide what a variant means. Where a spec can still
express something the readers disagree about, that shape is a lint error rather
than a parsing problem.

## Opportunity

The format half of this is already done and it worked: 6 drifted specs were
normalized, the corpus is 405 canonical / 0 variants, and the heading matcher is
now exact with a near-miss warning, so drift cannot reseed silently. What
remains is smaller than it first looked, and the measurements say so.

**Comments and code spans cannot be removed, so "ban the constructs" is not the
route.** Measured across 407 specs: 251 contain a real HTML comment, 245 contain
one in the metadata preamble, and all 407 use inline code spans. The new-spec
template itself emits 16 comments, including on the `- **Status:**` line. Both
constructs are load-bearing spec detail.

**The readers are not accidentally inconsistent; they have different jobs.**
`acceptance_criteria_opt_out` scans only the metadata preamble, where 245 specs
carry template comments, so it *must* strip them — a commented-out marker must
never count. The section detector and criterion collector scan the body, where
**0 specs** have a commented-out Acceptance-Criteria section, so stripping buys
them nothing and costs correctness: the naive `<!--.*?-->` pattern has no notion
of code spans, and `docs/specs/digital-experience-contract/spec.md` pairs two
backticked *mentions* at `:163` and `:186` into a false span over its real
heading at `:177`.

So the residual risk is one shape — an Acceptance-Criteria section that is
commented out or fenced — and the cheap answer is to make that shape a lint
error, not to teach four readers CommonMark. Four review rounds of the parsing
approach produced a cubically-backtracking regex, a Θ(L^1.5) replacement,
fence state read from raw text, and comment-blind fence pairing; each passed its
own verification. Enforcement is the smaller and more durable lever.

## Assumptions

- Enforcement covers the format-shaped residue. The opt-out marker regex anchors
  on a literal `^- `, so an indented marker, a `*` bullet, or a colon outside the
  bold escapes both readers and passes clean; pinning the exact marker line
  closes that by construction rather than by widening the matcher.
- Enforcement does NOT cover two robustness defects, which are unrelated to
  format: an explicit `--base-ref` is never validated, so an unresolvable one
  makes every spec look new and converts grandfathering into a repo-wide hard
  failure with none of the documented warnings; and a spec that is unreadable or
  over the size cap is skipped silently, so the invariant passes vacuously on it.
  Both need fixing on their own terms.
- Enforcement does NOT cover `tools/build-site.py`, which strips HTML comments
  with the same code-span-blind pattern over changelog prose rather than spec
  text. That one is not hypothetical: it already fired, pairing a backticked
  opener with a closer 5,083 lines later and leaving
  `parse_changelog_releases` with 1 release instead of ~100. Different module,
  different file, different reader — it needs its own change and is recorded
  here only so it is not lost.
- Our own specs are ours to clean up; adopter specs are not. Any new enforcement
  should warn adopters toward the supported shape rather than red-lining a
  corpus they did not write, and must never silently stop checking a spec —
  measured this session, a strict collector took an adopter shipping an unmet
  criterion from a hard invariant (ii) violation to exit 0.
- Complexity claims in this area need at least three doublings. A withdrawn fix
  was declared correct on a single benchmark point, which moved a constant and
  hid an exponent.
- Full history, reproducing fixtures, and measurements are in PR #1139.

## Source

- Mode: repo-origin
- Locator: packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py
- Revision: sha256-bytes-v1:45492bdceb9a6ddb3d3fa7ec03c0aeacd9d27d7d970105f83e14905c511c2c9c
