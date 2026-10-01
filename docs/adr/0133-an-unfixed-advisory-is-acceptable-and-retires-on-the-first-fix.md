# ADR-0133: An advisory with no published fix is acceptable, and it retires on the first fix rather than on a version floor

- **Status:** Accepted
- **Date:** 2026-09-30
- **Areas:** security, ci
- **Reversibility:** high
- **Decision-makers:** repository maintainers
- **Supersedes:** none
- **Supersedes in part:** ADR-0131 D6
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0131 (the allowlist this extends; its D6 cross-checks
  `fixed_in` against the advisory's `fix_versions`, and this record adds the
  case where there are none), ADR-0017 (D8 — pip-audit
  is the SCA gate), ADR-0113 (`gate-sast` owns the scan)

## Decision summary

- **Decision:** `fixed_in = "none"` is a valid allowlist entry, declaring that
  upstream has published no fix. Its retirement trigger is inverted: it fires
  when the feed first publishes **any** fix version, not when a resolved
  version reaches a floor.
- **Why:** ADR-0131 assumed every advisory names a release that fixes it. An
  advisory with an empty `fix_versions` could be neither remediated nor
  accepted, and parked `gate-sast` at exit 2 on every pull request.
- **Cost if wrong:** An unfixed acceptance is a longer-lived mute than a fixed
  one, because no version bump clears it. Mitigated by the inverted trigger,
  which is mechanical.

## Context

CVE-2026-103001 was published against PyJWT on 2026-09-30 with an empty
`fix_versions`: it is a regression of a 2021 defect fixed in 2022 by PR #743
and silently reintroduced by PR #1045 in 2025, so it is present in every
release since and no release remediates it.

ADR-0131's vehicle could not express this, and the failure arrived in two
stages. Both exit codes below were measured on 2026-09-30 against the live
feed; the distinction matters, because anyone reproducing this will meet the
first one and not the second.

Uncovered, the advisory simply blocks: the gate exits **1** and reports
`BLOCKING pyjwt 2.13.0 CVE-2026-103001 (fix: none)`. Every pull request in the
repository went red, including unrelated ones.

The obvious remedy makes it worse. D6 cross-checks `fixed_in` against the
advisory's own `fix_versions` so that an unreachable value cannot suppress
today and never retire. With `fix_versions` empty there is nothing to compare,
so adding an ordinary release-valued entry moves the gate from exit 1 to exit
**2** — "the gate could not render a trustworthy verdict". That is the correct
instinct and the wrong outcome: exit 2 reads as *the gate is broken*, when the
truth is *upstream has shipped no fix*.

So the repository was left with a red gate, no remediation to reach, and an
acceptance vehicle that escalated the failure instead of recording it — the
same shape ADR-0131 was written to end, arriving through the case it did not
cover.

The trap is worth naming, because the schema does not show it. Exit 2 is
reachable ONLY from a release-valued entry, so a maintainer who reaches for
the obvious remedy ends up worse off than one who does nothing. Removing that
asymmetry is as much the point of this record as expressing the acceptance:
D1's opt-in boundary keeps the empty-feed message in place for a release-valued
entry, and that message now names the sentinel rather than leaving the reader
with a verdict and no move.

## Decision

- **D1:** `fixed_in = "none"` declares an advisory upstream has not fixed. It
  is matched case-insensitively and whitespace-trimmed, because the file is
  hand-edited. It is opt-in: an empty `fix_versions` is never read as implying
  it, so a release-valued entry against an empty feed still exits 2.
- **D2:** The sentinel suspends D6's cross-check and replaces it with its
  mirror. A release-valued entry is wrong when the feed does not recognise its
  `fixed_in`; an unfixed entry is wrong the moment the feed recognises **any**
  fix. On that event the gate exits 2 and names the published version.
- **D3:** D5 still governs absence. An unfixed advisory that stops being
  reported cannot mean the fix arrived — there is no release to compare — so
  that branch withholds the remove instruction and holds. The one branch that
  may tell a maintainer to delete a written acceptance stays unreachable for
  these entries.
- **D4:** The other four required fields are unchanged. An unfixed entry still
  needs a per-advisory reachability `reason` and an `unblocked_when`; the
  sentinel relaxes the version check, never the written justification.

## Consequences

An unfixed advisory is now expressible, so `gate-sast` distinguishes "no fix
exists and we have reasoned about reachability" from "the gate cannot tell".
Both still appear in every run's output; neither is silent.

The exposure is real and asymmetric: an unfixed acceptance has no version bump
coming to clear it, so it can outlive its reasoning for longer than a
release-valued one. D2 is what keeps it honest, and D2 depends on the feed
continuing to carry the advisory. A feed that drops it entirely lands in D3,
which holds rather than retires — deliberately preferring a stale entry a human
must resolve over an automatic deletion of a risk acceptance.

What is **not** mechanical, exactly as in ADR-0131: the reachability argument.
For CVE-2026-103001 it was verified on 2026-09-30 against the installed
distributions by three independent checks, recorded in the entry itself —
Semgrep's single `jwt.decode` call site, its fresh per-call `options` literal,
and the `verify_signature` guard that makes the mutating branch unreachable.
Nothing re-checks those. A Semgrep upgrade that changes its token verifier
invalidates them, and the entry must be re-verified rather than assumed.

**Revisit if:** (1) a second unfixed advisory arrives for a package whose
reachability argument is weaker than this one's, because the sentinel would
then be carrying a judgement call rather than a mechanical impossibility; or
(2) the feed starts dropping advisories it still considers live, which would
move these entries into D3's hold branch permanently and turn a governed
acceptance into a stale one no trigger can clear.

## Confirmation

- **Mode:** enforced. Every branch the sentinel adds is driven directly through
  the gate's decision seam; no part of it rests on a human remembering.
- **Signal:** cases 28a-28e below. They red on a sentinel that stops being
  honoured, a fix appearing without the entry failing, an absence misread as a
  remediation, an empty feed silently implying the sentinel, or either
  `ACTION:` token drifting into the wrong branch.
- **Owner:** eugenelim.

`tools/test-run-pip-audit-gate.py` cases 28a-28e drive the decision seam
directly: acceptance on an empty feed, exit 2 with the version named when a fix
appears, hold-not-retire when the advisory goes absent, the opt-in boundary,
and the two tolerated spellings. Cases 28b and 28c assert `ACTION: change
nothing yet` is present and `ACTION: remove this entry` is absent, so the
safety property of D3 is checked by name rather than by exit code alone.

## Alternatives considered

- **Wait for an upstream fix.** Rejected: no fix is scheduled, the defect has
  been latent since 2025, and the whole repository stays blocked meanwhile.
- **Copy a plausible future version into `fixed_in`.** Rejected: ADR-0131's own
  D6 exists to stop exactly this, and it would park the entry permanently in
  the could-not-compare branch.
- **Drop the `fix_versions` cross-check.** Rejected: it would weaken every
  release-valued entry to repair one unfixed case.
- **Remove PyJWT from the SAST resolve.** Rejected: it arrives through
  Semgrep's own `pyjwt[crypto]~=2.13.0` dependency; excluding it would narrow
  the audited floor rather than remediate anything.
