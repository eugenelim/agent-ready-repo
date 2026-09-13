# Mutation log

Mutations run by the orchestrator against `tools/score_finding_responses.py`,
each restored by editing the source back. Recorded here because a claim that a
guard reds under mutation is unsupported unless the run is retained.

Every entry was executed; none is predicted. The command in each case was
`python3 -m pytest tools/test_score_finding_responses.py -q`.

| Guard | Mutation applied | Observed |
| --- | --- | --- |
| correspondence, `missing` fires alone | report `missing` only when an `extra` also exists | before isolated tests existed: **3 passed** (guard invisible); after: `test_missing_identifier_is_named_when_every_other_response_is_correct` **failed** |
| disposition vocabulary | `if False` on membership check | **DID NOT RAISE**, test failed |
| both artifacts read | `answered_criteria_count` reads the baseline path | **4 failed** |
| canonical emission order | `sorted(set(DISPOSITIONS))` in place of declared order | `test_render_score_emits_exact_canonical_report_bytes` **failed** |
| criteria-section scoping | count every checkbox in the file, ignoring the section | **6 failed** |
| rendering digest binds bytes | append one byte to a committed rendering file | corpus test **failed**; restoring greened it |
| rendering path binds arm | repoint the fix arm at the neutral rendering with a valid digest for it | corpus test **failed**; restoring greened it |
| rendering non-emptiness | empty a rendering and set its digest to the empty-bytes hash | corpus test **failed**; restoring greened it |

The first row is the reason isolated single-violation fixtures exist: an
aggregate fixture carrying several faults at once kept a broken guard green.
