# Amendment record — 2026-09-20

## Authority

The scope owner (eugenelim) directed, in session on 2026-09-20, that the
overlay probe's `Follow-ons` entry be removed from `spec.md` because the probe
is being run now rather than deferred, and that the spec be updated from the
spike's results before it ships.

## Reason

`spec.md`'s `Follow-ons` described the probe as separately-owned future work.
That was accurate when it was written: the probe had been cut from this
contract after eight review rounds established its open questions were
empirical rather than specificational. It stopped being accurate when the
spike started, in the same session, against the baseline the axis had not yet
displaced.

The spike's artifacts and its frozen baseline are recorded in the session
scratchpad; arm A is authored and frozen, arm B waits on T1 so that it is
authored against the shipped marker-delimited region rather than a paraphrase.

*Recorded later, 2026-09-20, and left here rather than rewritten because this
is a dated amendment record:* arm B read T1's working-tree draft of that
region, and review changed two sentences in it afterwards, so the intent above
was met only up to those two sentences. `notes/probe/method.md` names them.

## What this amendment changes

Every section the amendment touched, so an auditor reconciling the file against
this record finds no changed text the record does not name.

- `spec.md` `## Follow-ons`: the probe entry removed; the revert entry rewritten
  off "that spike" and rescoped to the one residual case, which is reachable
  only if the `Always do` release rail is broken; the S2/S3 entry reworded off
  "the spike above". The probe's defining gloss, which the removed entry had
  carried, now sits in the `Always do` rail at its first contract-tier use.
- `spec.md` `## Assumptions`: the entry replaced, recording the probe as running
  against this delivery rather than deferred behind it.
- `spec.md` `## Agent Rules`: one `Always do` item added — update this spec
  from the probe's findings before T5 releases. An `Ask first` item about
  shipping after a killed verdict was also added at the time, and **later
  removed**: the probe returned no verdict, so a kill can now only arrive
  after release, and the rail contradicted the Follow-on that owns that case.
  The sealed spec carries one `Ask first` item, about the equality-pinned
  description ends.
- Nothing in the acceptance-criterion set or `Testing Strategy`. The twelve
  criteria AC-0084–AC-0090, AC-0094–AC-0096, AC-0099 and AC-0101 are unchanged,
  and no task is edited or removed.

## Ordering consequence, traced after the fact

Moving the verdict before the release makes the killed-verdict revert
unreachable as it was written: nothing is released, so there is nothing to
revert. The revert Follow-on is now scoped to one residual case — the release
rail being broken — and says so plainly rather than claiming a trigger the
rails forbid. The kill-before-release case is an `Ask first` rail instead.

Two rounds were needed for this. The first repair rescoped the entry and the
record called that "a reachable trigger", which was wrong: the same amendment's
`Always do` rail forecloses it. Neither the ordering consequence nor its second
unreachability was traced by the author; a reviewer found both.

The plan carried the superseded ordering in three places — `## Approach`,
`## Risks`, and T5's `Approach`, the last stating outright that the probe
verdict "does not enter this decision". All three were corrected in the same
amendment window, while the cleared baseline left the plan editable. The
release boundary is now named once, in the spec's `Always do` rail, and T5's
`Approach` references it rather than restating it.

## Why an amendment was required for a working-material section

`Follow-ons` is working material under the spec template, correctable in place
without a review round. The approved-baseline digest is not scoped to the
contract tier, though: `canonical_contract` normalizes only the status token
and the acceptance-criterion checkboxes, so the digest covers the whole file
and a `Follow-ons` edit moves it. Measured on this spec: `0117963376fc` before
a Follow-ons-only edit, `f612b15953` after. The sealed baseline therefore had
to be released through `contract-amendment` rather than corrected in place.

## Consequence accepted

Updating the spec from the spike's results before shipping re-couples this
delivery to the probe. That coupling is to the spike's *findings* rather than
to a specification of it, which is the ordering the intent's `prototype-led`
approach calls for.

**Superseded on the same day.** This paragraph originally said the tasks would
not ship "until the spike returns a verdict". The spike returned none, and the
shipped rail says *findings*, not verdict — gating a release on a verdict that
does not exist would have made T5 unstartable. The tasks ship on the spec
having been updated from what the probe found.

---

# Amendment 2 — 2026-09-20, AC-0096's placement clause

## Authority

Post-implementation review found AC-0096 unsatisfiable against a green gate.
The scope owner's standing direction for this delivery is to build it through;
this amendment corrects a criterion that cannot be met rather than changing
what the delivery does.

## The conflict

AC-0096 required the architect entry to be `docs/product/changelog.md`'s
"topmost release heading". `tests/roster/test_verification_ledger_contract.py`
carries `test_the_core_release_heading_sits_directly_beneath_unreleased`, which
pins `[core]` to that slot. Both cannot hold, and the file's own history shows
which wins: `## [architect][0.15.12]` already sits below `## [core][2.26.20]`
despite the later date.

The clause also had no verification artifact. Neither test the spec's Testing
Strategy names for AC-0096 checks topmost-ness; they check section separation
and unreleased-region nesting.

## What changes

`spec.md` AC-0096's placement clause only: from the changelog's topmost release
heading to the topmost **architect** release entry, which is what the file
admits and what `tests/roster/test_okf_catalogue_discovery.py` actually reads.
The free-standing `##` requirement and the not-nested-under-an-unreleased-region
requirement are unchanged, and both keep the artifacts already named for them.

Nothing else changes. No task, no other criterion, and no shipped file.
