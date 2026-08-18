# Launch highlight review

- **Status:** Recorded
- **Reviewer:** eugenelim (ordinary PR review, per AC6)
- **Spec:** [`../spec.md`](../spec.md) — AC5, AC6
- **Date:** 2026-08-18

AC6 makes ordinary implementation review the only approval gate for a highlight,
and AC5 requires the launch seed to be grounded in released changelog entries
rather than reconstructed from plans or commits. This is that record. It exists
because the criteria are otherwise satisfied only by prose in the plan, and a
reader cannot tell an unrecorded review from an unperformed one.

## Launch window

Launch day **2026-08-18**; the inclusive seven-day window is
**2026-08-12 … 2026-08-18**.

Released entries inside it: exactly **one**.

| Release | Date | Eligible | Why |
| --- | --- | :---: | --- |
| `governance-extras` 0.9.7 | 2026-08-16 | yes | `##`-level entry, versioned and dated, outside every `[Unreleased]` region |
| 28 further entries | 2026-08-12 … 2026-08-17 | no | `###` children of the first `## [Unreleased]` heading |

The 28 are not a gap. `changelog.md` carries three separate `## [Unreleased]`
regions, and its newest dated entries are nested inside the first. The spec is
explicit that Unreleased content never projects "even if they contain
Highlights", so recency does not make them eligible. They publish when their
entries are promoted out of `[Unreleased]` at release time, with no further work.

## The one seeded highlight

Written into `## [governance-extras][0.9.7] — 2026-08-16` as a `### Highlights`
subsection:

> **Writing an RFC or an ADR now files its reusable lessons for you, and only
> once the decision is actually settled.** Supporting lessons are handed to
> project knowledge at clean handoff and accepted-decision points, so a draft you
> abandon leaves nothing behind. If project knowledge is not installed, authoring
> proceeds unchanged and writes no stand-in file.

**Grounding — checked against the released entry, not written from memory.** The
entry's own `### Changed` text reads: "RFC and ADR authoring now hand reusable
supporting lessons to project knowledge only at clean handoff and
accepted-decision gates. Missing project knowledge leaves no fallback file, and
enquiry remains an explicit, bounded, untrusted-evidence step."

Every clause above traces to it:

| Highlight clause | Source in the released entry |
| --- | --- |
| "files its reusable lessons for you" | "hand reusable supporting lessons to project knowledge" |
| "only once the decision is actually settled" | "only at clean handoff and accepted-decision gates" |
| "a draft you abandon leaves nothing behind" | the same gate restriction, stated as its consequence |
| "writes no stand-in file" | "Missing project knowledge leaves no fallback file" |

**What was deliberately dropped.** The entry's third sentence — that enquiry
remains "an explicit, bounded, untrusted-evidence step" — is a property of the
mechanism, not an outcome a reader can act on, and it needs vocabulary the public
page does not establish. Omitted rather than translated.

**Review checks.**

- Outcome-led: opens with what someone can now do, not with what changed.
- No development state: no plan, queue, backlog, commit, PR, or "working on".
- No invented credibility: no customer, adoption figure, testimonial, or claim
  not present in the released entry.
- Not a restatement of the release title.
- Verifiable: the page links to this exact changelog entry, so a skeptical reader
  can check the claim against its source in one click.

**Result: accepted.** One highlight, one release group at launch.

## Not covered here

Physical-device review is a separate manual release gate owned by
`site-browser-quality-gate` AC15. Deterministic browser evidence for `/now/`
(five widths, overflow, axe) is implementation evidence recorded in the PR, not
content review.
