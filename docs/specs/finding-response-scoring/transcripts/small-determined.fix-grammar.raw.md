# Answer: small-determined (fix-grammar)

## F1
Repair. I will make AC18 enumerate each publisher-derived value that can reach CLI or JSON output, rather than relying on a broad description of the input set. AC21 will continue to put diagnostic `path` at the top level, but will say explicitly that this is also true when the path is publisher-chosen. AC18 will require escaped, non-forgeable human rendering of that path after a logical-path refusal, while retaining the diagnostic value needed for structured output. This removes the conflict without treating an unsafe path as trusted publisher data.

## F2
Repair the plan. T2 will add code-side refusal fixtures for every non-skill manifest key that T0b established is schema-admitted. That closes the gap between the measured schema surface and the direct-manifest contract, so the implementation cannot silently admit a key that the specification rejects.

## F3
Repair. AC5 will add the injectable clock and progress seams to the list of channels that cannot raise a bound. Their validated values may only tighten the applicable bound. This makes the rule cover every injectable control named by the criterion.

## F4
Repair the plan. T5 will gain mutation fixtures that fail if `lstat`, `stat`, `fstat`, or `resolve` appears outside AC34's named carve-out, and if `probe_measured_path` returns admission data rather than a refusal-only decision. The fixtures test both halves of the static safety claim.

## F5
Repair after owner approval. AC22 will state the per-invocation aggregate `--check` limits explicitly: a 90-second deadline, 25 distinct post-dedup resolutions, five in-flight resolutions, and 256 MiB downloaded. It will retain the rule that a cap, deadline, budget, or resolution failure renders the affected row `unknown` without raising the limits. This bounds the aggregate work from all stored sources instead of allowing the per-fetch cost to multiply without limit.

## F6
Repair the plan and deliverable. T3 will include AC35 and AC36 in its criterion line, and the regenerated AC35 corpus-verdict table will be committed for both E14 collection-root shapes and the E15 envelope-relative depth rule. This records the evidence whose regeneration trigger was reached and binds the budget-setting task to both required criteria.

## F7
Repair the plan. T9's criterion line will include AC4, matching its stored-provenance differential fixture. The plan will then state the criterion that the fixture actually verifies.

## Acceptance-criteria count after these decisions
36, from a starting count of 36.
