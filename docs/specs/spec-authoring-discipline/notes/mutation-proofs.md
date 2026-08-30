# Mutation proofs — AC14

AC14 requires that every rule's removal be caught and "the proof recorded".
A claim in a commit message is not a record. This is the record.

Method: for each invariant, delete its sentence from the owning file with a
wrap-tolerant pattern, run `pytest packs/core/tests/skills/new-spec/`, observe
the failure, then restore the file by editing the text back — never by a git
operation, since the stash stack is shared across worktrees. Every file was
verified byte-identical to its original after restore.

| invariant | owning file | mutation | result | failing node |
| --- | --- | --- | --- | --- |
| `criterion-independence` | `spec` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[criterion-independence]` |
| `template-citation` | `skill` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[template-citation]` |
| `bound-ledger` | `spec` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[bound-ledger]` |
| `two-limits` | `spec` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[two-limits]` |
| `corpus-trigger` | `skill` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[corpus-trigger]` |
| `corpus-oracle` | `skill` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[corpus-oracle]` |
| `unreachable-corpus` | `skill` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[unreachable-corpus]` |
| `cite-owner` | `skill` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[cite-owner]` |
| `resolve-duplicate` | `skill` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[resolve-duplicate]` |
| `step-four-pointers` | `skill` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[step-four-pointers]` |
| `deletion-pass` | `skill` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[deletion-pass]` |
| `claim-minimality` | `spec` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[claim-minimality]` |
| `limit-origin` | `spec` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[limit-origin]` |
| `limit-value` | `spec` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[limit-value]` |
| `observable-outcome` | `spec` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[observable-outcome]` |
| `plan-mechanism` | `skill` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[plan-mechanism]` |
| `reduce-over-specified-plan` | `skill` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[reduce-over-specified-plan]` |
| `conjunction-cue` | `spec` | sentence deleted | red | `test_acceptance_criterion_rule_has_one_owner[conjunction-cue]` |
| `E1` | `spec` | sentence deleted | red | `test_worked_example_has_one_owner_and_occurs_once[E1]` |
| `E2` | `spec` | sentence deleted | red | `test_worked_example_has_one_owner_and_occurs_once[E2]` |
| `E3` | `spec` | sentence deleted | red | `test_worked_example_has_one_owner_and_occurs_once[E3]` |
| `E4` | `spec` | sentence deleted | red | `test_worked_example_has_one_owner_and_occurs_once[E4]` |
| `E5` | `spec` | sentence deleted | red | `test_worked_example_has_one_owner_and_occurs_once[E5]` |

proved: 23/23 rule and example-block pins — dead pins: 0

## Exemplar proofs (all five)

Replacing an example's quoted criterion while leaving its rationale intact:

| example | mutation | result |
| --- | --- | --- |
| E1 | exemplar replaced | caught |
| E2 | exemplar replaced | caught |
| E3 | exemplar replaced | caught |
| E4 | exemplar replaced | caught |
| E5 | exemplar replaced | caught |

## Targeted proofs for the pins added during post-implementation review

| finding | mutation | result |
| --- | --- | --- |
| F5 exemplar unpinned | replace E2's quoted criterion, leave its rationale intact | caught |
| F4 trigger unpinned | narrow AC6's input class to "third-party input" | caught |
| F8 ordinals unbound | renumber step 8 to step 9 | caught |
| B1 citation narrowed | repoint the citation at `assets/plan.md`'s `## Foo` | caught |
| B5 ordering unguarded | move the corpus rule back below the sign-off gate | caught |
| C8 exemplar absence | copy E5's exemplar into `assets/plan.md` | caught |

## Portability check (Testing Strategy, recorded)

    git diff origin/main...HEAD -- 'packs/**' | grep '^+' \
      | grep -E 'docs/|workspace.toml|AC[0-9]+'

Matches in added lines under `packs/`: **0**. No shipped rule cites this
catalogue's records, criteria, or repository-only paths.

## Residual

Whole-file pins prove a rule exists in its owning file, not *where* in it, so
relocating a rule within its owner passes the phrase assertions. Two positional
guards now close the instances that actually occurred or were constructed: the
corpus-absence rule must precede the sign-off gate, and step 4's pointers must
name headings that still exist.

An earlier version of this note claimed the remainder was accepted because a
section-windowed pin "would deviate from an approved contract". That reasoning
was wrong and is withdrawn: the positional assertions above were added without
amending AC13, and AC13 prescribes a floor — pin each rule's phrasing against
its owning file — not a ceiling forbidding further assertions. The remainder is
accepted because no further instance has been constructed, not because the
contract forbids covering it.
