# ADR-0113: The SAST/SCA guarantee moves from the local gate to `gate-sast`

- **Status:** Accepted
- **Date:** 2026-09-13
- **Decision-makers:** eugenelim
- **Consulted:** adversarial review (Codex, read-only)
- **Supersedes:** the **dogfooding sub-decision** in [ADR-0017](0017-adopt-bandit-pip-audit-semgrep-sast-gate.md) only — that the SAST/SCA leg is chained into `make build-check` so that a developer running the local gate scans. That ADR's tool choices, severity floor, three-way real-fix-first ladder, and the requirement that the scanners stay CI-only dev dependencies all stand
- **Related:** [ADR-0086](0086-split-the-sast-gate-into-its-own-ci-job.md), [ADR-0083](0083-extend-sast-sca-gate-to-npm-with-audit-and-allowlist.md), PR #1285

## Decision summary

- **Decision:** The guarantee that this repository's own code is scanned rests on the `gate-sast` job, not on a developer running the local gate.
- **Because:** A guarantee has to be enforced rather than asserted, and after ADR-0086 nothing executes the chained branch by default.
- **Applies to:** The SAST/SCA leg only. ADR-0086's command-line-origin provenance rule for `SAST_DELEGATED` is untouched.
- **Tradeoff accepted:** `tools/assert-sast-chain-reachable.py` now guards a path that is reachable rather than routinely exercised.
- **Revisit if:** the aggregator stops requiring `gate-sast`, the reachability pin is removed, or contributors resume running the local gate routinely.

## Context

ADR-0017 chained `make sast` into `make build-check` and accepted a slower local
gate for it, because the alternative was "a separate, skippable workflow". Its
stated reason was that the gate would then be "actually dogfooded (the
maintainer's explicit priority over inner-loop speed)". The same ADR recorded the
escape hatch under Neutral / to revisit: "If the slower `build-check` proves
painful in the inner loop, a fast/slow split … can be revisited — but the default
is the single dogfooded gate."

ADR-0086 split the leg into its own `gate-sast` job. It read ADR-0017 for its
rationale rather than its letter, and deliberately kept the Makefile chain:
"`make build-check` on a developer machine still runs `$(MAKE) sast`. That is
ADR-0017's dogfooding requirement." It also recorded that after the split "**no
CI path executes that branch**", which is why `tools/assert-sast-chain-reachable.py`
exists — it pins reachability, and is mutation-proven against both deletion and
neutering.

That arrangement left the dogfooding requirement resting entirely on developers
choosing to run the local gate. PR #1285 removes that assumption. Root `AGENTS.md`
now tells contributors not to run `make ci`, `make build-check` or `make test`
locally. Two things drove it:

- **Cost.** The linter pair `make lint-ruff lint-mypy` takes no coordination lease
  and finishes in seconds; measured at roughly 1.5s and 6s on one developer machine
  under heavy parallel load on 2026-09-13. Treat the magnitude, not the figures, as
  the durable fact. The rest of `make ci` is minutes, and its last leg is the
  network-bound SAST/SCA scan.
- **Test coverage, which runs one way.** Local `make ci` reaches 19 `tools/` suites
  and 79 `tests/roster/` suites that `build-check.yml` does not name. But
  `test-corpus.yml` runs `make test` verbatim and `test-roster.yml` sweeps
  `tests/roster/` wholesale, so a pull request plus those two dispatches is a
  superset **of `make ci`'s test coverage**, on CI hardware. Separately, the
  path-filtered workflows add Windows, CodeQL and the catalogue-tooling gates, and
  `gate-export-boundary` and `gate-credbroker` add the `[crypto]` import and `-rs`
  skip probes that no local command runs at all, whenever their filters match.

So the chained branch now executes nowhere by default, and ADR-0017's dogfooding
rationale is vestigial.

What it protected is mostly, but not entirely, preserved. `gate-sast` owns the
scan — every leg of `make sast`: Bandit, pip-audit, Semgrep and the npm audit —
and the aggregator's `Require every gate` step exits 1 unless `GATE_SAST_RESULT`
is `success`. Two limits are load-bearing and must be stated rather than assumed
away:

- **On a pull request the scan is conditional.** The `Detect whether SAST-relevant
  files changed` step sets `skip_sast=true` when nothing under `SAST_DIRS` and no
  `SAST_CONFIG` file changed, and `Run make sast` is the predicate's only consumer.
  The job then succeeds without scanning. Its three acquisition failures are
  fail-closed — an unreadable `SAST_DIRS`, `SAST_CONFIG` or diff each force
  `skip_sast=false` — and any other failure in the step fails the job under
  `set -euo pipefail`. **Job success is not proof a scan ran.**
- **The predicate has a path-encoding false negative.** `git diff --name-only`
  C-quotes a path containing non-ASCII or special characters, emitting e.g.
  `"tools/we ird\303\251.py"`. The leading quote makes it miss the anchored
  `^(<dirs>)/` match, so a genuinely SAST-relevant change under a scanned
  directory can set `skip_sast=true`. Verified by construction on 2026-09-13.
  This ADR **records it as a residual and does not fix it** — the repair is a
  change to a security gate and needs its own review. A NUL-safe
  `git diff --name-only -z` is the likely shape.
- **Push-to-main and dispatch runs are unconditional**, because the detect step is
  gated on `github.event_name == 'pull_request'`. That is the belt-and-braces
  ADR-0086 relied on, and it is why that ADR asserts the push trigger.

Both limits are ADR-0086's accepted residuals — the self-certifying head-ref
predicate and "a green aggregator does not prove a scan executed". This ADR
**inherits them unchanged and closes neither.** What it changes is only where the
guarantee is claimed to live.

## Decision

We will treat `gate-sast` as the enforcement point for the SAST/SCA gate, and the
`$(MAKE) sast` branch inside `make build-check` as a supported reproduction path
rather than the dogfooding mechanism.

Specifically:

- `make sast` is the named local command for running the scan directly. It does
  not require `make build-check`. It is **not** an offline path: pip-audit and the
  npm audit query their advisory sources, and ADR-0017 records that "Semgrep pulls
  its rulesets from the registry at scan time". Scanning locally needs network.
- The Makefile chain and `tools/assert-sast-chain-reachable.py` stay **unchanged**.
  This is a boundary on the decision, not a second decision: leaving them in place
  is the no-op, and removing them would be its own ADR. Their stated purpose is
  restated — they keep `make build-check` a faithful reproduction of `gate-main`'s
  **anchor step** plus the SAST leg, and keep the branch from rotting or being
  silently neutered — and the living comments that still call this "dogfooding"
  are corrected in the same change. `gate-main`'s other ~50 pytest and lint steps
  are not reproduced by that one command; `build-check.yml`'s header maps them to
  `make test`, `lint-ruff`, `lint-mypy` and `pre-pr`.
- No change to `SAST_DELEGATED`. ADR-0086's command-line-origin rule is
  load-bearing and untouched: an ambient environment variable still neither
  reaches the quiet banner nor skips the leg. `SAST_DELEGATED` remains CI's
  signal, not a developer default.
- No change to `SKIP_SAST`, which keeps its `INCOMPLETE` banner.

This decision is about where the guarantee lives. It does not relax the severity
floor, the tool set, or the real-fix-first ladder.

## Decision drivers

- **The guarantee must be enforced, not asserted.** ADR-0086's own standard, and
  the reason it added the reachability pin.
- **Inner-loop cost is now a named constraint**, which ADR-0017 explicitly
  deferred and explicitly invited reopening.
- **No reduction in scan coverage** is acceptable as a price for either.

## Consequences

**Positive:**

- The claim and the mechanism agree. Previously the repository asserted local
  dogfooding while documenting a workflow in which no CI path and, increasingly,
  no developer ran that branch.
- The enforcement point is a job whose failure the aggregator converts into a
  failed run, so it cannot be skipped by omission.
- The inner loop is seconds rather than minutes, on a machine that is frequently
  saturated by parallel agent sessions.

**Negative:**

- Nothing routinely executes the chained branch. `assert-sast-chain-reachable.py`
  proves it *can* run, not that it *does*. That is a weaker property than
  ADR-0017 wanted, and this ADR accepts it knowingly.
- A contributor gets no scan on their own machine unless they run `make sast`
  deliberately, and that command needs network access, so there is no offline
  scan at all. Local scanning is now opt-in rather than incidental.
- Findings surface later — at PR time rather than pre-push. The three-way
  real-fix-first ladder is unchanged, but the feedback arrives on a slower loop.
- The guarantee is now **entirely** carried by a job whose scan step is conditional
  on a head-ref predicate. Previously a developer running the local gate scanned
  unconditionally, which incidentally covered the self-certification residual on
  their own change. That incidental cover is gone; the push-to-main run is what
  remains.

**Revisit if:** the aggregator stops requiring `gate-sast`, the reachability pin
is removed, or contributors resume running the local gate routinely.

## Confirmation

- **Mode:** lint/CI
- **Signal:** two independent checks, plus one named gap.
  `.github/workflows/build-check.yml`'s aggregator step `Require every gate` exits
  1 unless `GATE_SAST_RESULT` is `success`, so the job cannot be dropped by
  omission. `tools/assert-sast-chain-reachable.py`, chained into
  `make build-check`, fails if the `$(MAKE) sast` branch stops being reachable — by
  deletion or by being made unreachable while still present.
  **The gap:** neither signal proves a scan executed on a given pull request, for
  the conditional-predicate reason in Context. Confirming that remains ADR-0086's
  open residual `ci-gate-parallelization-required-workflow-pinned-ref`, which this
  ADR does not close.
- **Owner:** repository maintainers.

## Alternatives considered

- **Keep the dogfooding claim and tell contributors to run `make ci` before
  pushing.** Rejected against the inner-loop driver. It also fails the coverage
  driver in an unexpected direction: `make ci` is strictly *weaker* than a pull
  request, so the advice would trade minutes of local time for less assurance.
- **Delete the Makefile chain and `assert-sast-chain-reachable.py` as dead
  weight.** Rejected against the coverage driver. The offline and
  reproduce-a-CI-failure cases are real, and an unpinned branch that no path
  exercises is exactly the state ADR-0086 identified as rot-prone.
- **Document `SAST_DELEGATED=1` as the local default.** Rejected. ADR-0086 made
  command-line origin load-bearing precisely to stop this becoming ambient, and it
  would leave `make ci` quietly not scanning while printing a calm verdict —
  ADR-0086 names that outcome as "strictly worse than the state ADR-0017 left".
- **A fast/slow split — Bandit chained locally, the network-bound legs on a
  separate cadence.** This is ADR-0017's own named revisit. Not taken: it keeps a
  local leg that this decision has just established nobody runs, and splits one
  gate into two maintenance surfaces for no measured gain.

## References

- ADR-0017 § Consequences, Negative — "Chaining `make sast` into `make build-check`
  slows the repo's own gate … We accept this so the gate is actually dogfooded".
- ADR-0017 § Neutral / to revisit — the fast/slow split this ADR declines.
- ADR-0086 § Decision detail — "The Makefile chain is untouched" and the
  command-line-origin provenance rule.
- PR #1285 — the `AGENTS.md` and `Makefile` changes that make this decision live.
