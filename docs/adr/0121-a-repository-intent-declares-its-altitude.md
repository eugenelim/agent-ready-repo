# ADR-0121: A repository intent declares its altitude

- **Status:** Accepted
- **Date:** 2026-09-21
- **Areas:** shaping
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** ADR-0098 D3
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0033; ADR-0098; RFC-0102

## Decision summary

- **Decision:** `Level` is a required field on a repository intent, not optional enrichment. Its value set stays open.
- **Because:** the corpus lint refuses an intent without it, and `intake-intent` writes into the directory that lint guards, so an optional `Level` lets admission create an artifact the gate immediately rejects.
- **Applies to:** every file in `docs/product/intents/`, `intake-intent`'s renderer, and `frame-intent`'s template.
- **Tradeoff accepted:** admission asks for one more fact, and a caller that genuinely does not know the altitude must decide one rather than defer it.
- **Revisit if:** a legitimate intake route is found that cannot know the altitude at admission time.

## Context

ADR-0098 D3 grouped `level` with opportunity, assumptions, scale and JTBD as
"product fields" that "stay optional enrichment on a repository intent". That
was right when written: nothing read `Level`, so requiring it would have been
ceremony.

Something now reads it. The intent metadata shape contract makes `Owner`,
`Slug`, `Level` and `Status` the required tier of a live intent's preamble, a
corpus lint refuses a live intent missing any of them, and a gate runs that
lint over `docs/product/intents/`.

`intake-intent` writes its admitted intent to `docs/product/intents/<slug>.md`
— the same directory. Its renderer takes `level` as an optional argument and
emits no `Level:` line when it is absent, which every one of its existing
construction tests exercises. So under D3 the two rules meet head-on: admission
legitimately produces an artifact the gate legitimately rejects, and the author
who ran the admission is handed a failing gate for obeying the contract.

The disagreement is not about whether `Level` is useful. It is about whether a
repository intent may exist without one. Only one answer can hold, because the
lint and the renderer address the same files.

ADR-0033 D2 is untouched by this and stays authoritative: the *value* set is
open, and a lint cannot enforce a closed one. This record changes whether the
field is present, never what it may say.

## Decision

- **D1:** `Level` is required on a repository intent. ADR-0098 D3's grouping of `level` with optional enrichment is superseded; opportunity, assumptions, scale and JTBD keep their optional status under that clause.
- **D2:** `Level`'s value set stays open, per ADR-0033 D2. A lint checks presence and never membership.
- **D3:** `intake-intent` requires an altitude at admission and renders it. A caller that supplies none is refused rather than defaulted, because a guessed altitude is a declared fact the artifact did not carry.

## Decision drivers

- A contract that admission can satisfy and a gate can reject is not one contract.
- A required field with an open value set costs an author one decision and costs a reader nothing to interpret.
- Defaulting is worse than refusing here: the field's whole purpose is to place the intent on the tree, and a wrong placement is harder to notice than a missing one.

## Consequences

Admission gains one required input. `intake-intent`'s callers must supply an
altitude, and the renderer refuses rather than omitting the line.

The five product fields D3 named are no longer one group. Four remain optional
enrichment; `level` does not. A reader of D3 alone would draw the wrong
conclusion, which is why this record names the clause it supersedes in part
rather than restating D3 whole.

Existing intents are unaffected: every file in `docs/product/intents/` already
carries `Level:`.

- **Revisit if:** a legitimate intake route is found that cannot know the
  altitude at admission time, or `Level` stops being read by any check.

## Confirmation

- **Mode:** lint/CI
- **Signal:** the intent corpus lint
  (`packs/core/.apm/skills/work-intake/scripts/intent_corpus_lint.py`) exits
  zero over `docs/product/intents/` and non-zero for a live intent with no
  `Level:`, and `intake-intent`'s renderer output is fed to the same validator
  in the core pack's construction tests — so a renderer that omits the field
  fails a suite rather than only a corpus scan.
- **Owner:** eugenelim

## Alternatives considered

**Default the altitude when the caller supplies none.** Cheapest, and rejected:
it makes the renderer invent a declared fact. The shape contract forbids
inferring a declared field from a side channel for exactly this reason, and a
confidently wrong altitude misplaces the intent on the tree where an absent one
merely stalls it.

**Record the change as an erratum on ADR-0098.** Cheaper than a new record, and
rejected on instrument grounds: RFC-0102 freezes an accepted record's body,
permits status-only edits, and states that "anything else is a *new* ADR that
supersedes". An erratum corrects an error in the record, and D3 was correct
when written.

**Exempt the renderer's output from the required tier.** Rejected: it leaves
the gate failing on any newly admitted intent, which converts a contract
disagreement into a standing defect rather than resolving it.

## References

- [ADR-0098](0098-artifact-admission-and-delivery-brief-lifecycle.md) D2, D3 — the admission minimum contract, and the optional-enrichment clause this record supersedes in part.
- [ADR-0033](0033-intent-level-open-recognized-set-decoupled-from-scale.md) D2 — `Level`'s open value set, unchanged here.
- [RFC-0102](../rfc/0102-mechanically-checkable-adrs.md) § 2 — the prose freeze and the supersession grammar that make this a new record rather than an edit.
- `docs/specs/intent-metadata-shape-contract/spec.md` — the required tier, the corpus lint, and the gate that together force the question.
