# ADR-0101: A Semgrep exclusion may be path-scoped for scanner performance, if it states its residual and carries a retirement trigger

- **Status:** Accepted
- **Date:** 2026-08-29
- **Decision-makers:** eugenelim
- **Supersedes:** [ADR-0017](0017-adopt-bandit-pip-audit-semgrep-sast-gate.md) in part — its **exclusion-list sub-decision** only (that Semgrep's exclusions are the four listed rule-scoped ones chosen for duplicating Bandit); that ADR's tool choices, severity floor, three-way suppression policy, and the four exclusions themselves all stand
- **Related:** [ADR-0084](0084-nosec-reason-delimiter-and-stderr-as-a-gate.md) (a quiet scanner signal becomes a gate through a wrapper with a self-test, not a recipe flag)

## Decision summary

- **Decision:** `SEMGREP_EXCLUDE` may carry a path-scoped `--exclude` taken for scanner-performance reasons, not only the rule-scoped `--exclude-rule` entries ADR-0017 enumerates. Such an entry must state, beside itself, which detections it drops, what still covers them, and the condition under which it retires.
- **Because:** ADR-0017 fixed the exclusion list at "four rules that duplicate Bandit's coverage … with no loss of coverage." A per-rule timeout is neither a duplicate nor lossless, so the gate acquired a suppression category its governing record did not describe.
- **Applies to:** Every entry in the `SEMGREP_EXCLUDE` variable in the `make sast` recipe.
- **Tradeoff accepted:** A path-scoped exclusion drops *every* rule on the named path, which is wider in the rule dimension than an `--exclude-rule` would be. That is accepted only when the narrower form would cost blocking coverage on production code.
- **Revisit if:** (1) semgrep gains rule+path scoping in one flag, which would make both forms unnecessary; (2) a path-scoped entry is added without a stated residual or retirement trigger; or (3) the staleness gap below is closed and an exclusion is found to have outlived its cause.

## Context

ADR-0017 recorded the Semgrep half of the gate as a fixed list of four
rule-scoped exclusions, each justified by Bandit owning the same class
line-precisely, and each therefore costing nothing. Its three-way suppression
policy — real fix, `# nosec`, `.snyk` — describes what to do about a *finding*.

Neither covers what happened next. Two interprocedural env→subprocess taint
rules from `p/security-audit` exceeded semgrep's default 5s-per-rule-per-file
budget on two large dev-CLI test harnesses. The timeout is not a finding and not
a false positive; it is a tool-performance failure, and under `--strict` it is
build-fatal.

The obvious remedy — `--exclude-rule` on the two rules — was measured before it
was taken, and rejected. A canary `subprocess.run([os.environ["TOOL"],
"--version"])` planted under `packs/` is reported by
`dangerous-subprocess-use-tainted-env-args` with the rules enabled and by nothing
at all with them disabled: not by Bandit, whose matching subprocess checks
(B603/B606/B607) are LOW severity while `tools/run-bandit-gate.py` pins the gate
at `--severity-level medium`; and not blockingly by CodeQL, which is not a
required check on `main`. Excluding the rules repo-wide would have left the
credential broker and the auto-run session-start hook — the surface
`tools/semgrep/env-path-taint.yml` names as the one place the threat is real —
with no blocking detector for env-tainted subprocess argv.

Excluding the two *files* instead keeps both rules live everywhere else.

## Decision

### 1. Path-scoped exclusion is a legitimate fourth vehicle

`--exclude <path>` may be used in `SEMGREP_EXCLUDE` when a rule/file interaction
makes the gate unrunnable and the rule-scoped alternative would cost blocking
coverage on production code. It is preferred over raising `--timeout`, which
leaves the pathological interaction in place and merely stops it failing.

### 2. Every such entry states its residual

Beside the entry, in the same comment block as the existing four, record: the
detections dropped on that path, what still covers them (naming the gate's own
severity floor where that matters — "Bandit scans it" is not a residual for a
class Bandit reports below the floor), and the measured current finding count on
the excluded path, so a later reader can tell a clean exclusion from a hidden
one.

### 3. Every such entry carries a retirement trigger

State the condition under which the entry is removed. A trigger with no detector
is aspirational: semgrep accepts an `--exclude` naming a path that no longer
exists, silently and with exit 0, so a stale entry outlives its cause with
nothing to notice. Building that detector is tracked as
`sast-semgrep-exclude-has-no-staleness-detector`; until it exists, the trigger is
a documented obligation on the next author, not an enforced one.

### 4. ADR-0017's exclusion-list clause is superseded only in scope

The four rule-scoped exclusions ADR-0017 names, their Bandit-duplication
justification, its three-way suppression policy, its tool choices and its
severity floor all stand unchanged. Only the claim that the exclusion list *is*
those four rules is widened.

## Consequences

A future maintainer meeting a timing-out rule has a sanctioned remedy and a
required shape for it, rather than the two undocumented options — raise
`--timeout`, or suppress the rule repo-wide — that the absence of this record
left open. The cost is that a path-scoped entry drops more rules on its path than
a rule-scoped one would, so the residual statement in decision 2 is doing real
work and must not degrade into a formality.

The staleness gap in decision 3 is the known weakness of this ADR. It is recorded
rather than solved because the detector belongs in scheduled CI, not in
`make sast`: re-scanning the excluded paths at a raised timeout on every
developer run would reintroduce the cost the exclusion exists to avoid.
