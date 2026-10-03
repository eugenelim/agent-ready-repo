# Codex headless run 6: where one stronger route is worth more

Provider block `codex-headless-via-claude-run6-r1`. Written 2026-09-29T04:13:37.593154Z. `integration_status: not-integrated`.

## The answer

**On balance the stronger route did more in the planning call, but the margin is thin.** 2 separating measure(s) favour spending it on the planner against 1 favouring the constructor. Whole-trajectory error and cleanliness were flat across all four cells, so whatever the routes differed in did not reach the trajectory's end state. Cost is not flat: the planner-stronger arm spent +543 output tokens and +12.5 seconds per trajectory against the constructor-stronger arm.

Equal-budget comparison. Both arms spend exactly one call on the stronger route; they differ only in which stage gets it. The sign of a mean task effect is read against that measure's own better-direction, which the `favours` column already resolves — do not read a positive number as good on its own.

| stage | measure | kind | mean task effect | task-cluster interval | favours |
| --- | --- | --- | --- | --- | --- |
| planner | incorrect_decisions | lexical | +0.5833 | [+0.0833, +1.3334] | construction call |
| planner | self_audit_false_positives | hybrid | -0.7500 | [-0.9167, -0.6667] | planning call |
| constructor | decisions_complete | structural | +1.0834 | [+0.1667, +1.6667] | planning call |

Only measures whose task-cluster interval excludes zero appear above. Every other directional measure in the primary contrast either sat at a ceiling or had an interval straddling zero, and none of those is allowed to count toward the answer. The full contrast, separating and non-separating measures alike, is below.

Read an interval as spread across four task clusters, not as a significance test.

The three separating measures do not agree, and none of them is an end-state quality measure. The one that most directly reads as plan quality — the count of unacceptable construction choices a planner made — favours *not* spending the stronger route on the planner. The two on the other side are a self-audit calibration measure and a field-completeness measure. Read together with the flat trajectory outcomes and the extra cost, the fair summary is that this corpus does not establish a worthwhile allocation advantage either way.

## What was run, and what it can support

A *trajectory* is two cold headless calls. A **planner** receives a frozen task contract and returns a planning artifact as bounded JSON. Its exact bytes are then handed to a **constructor**, which returns a bounded decision record and a proposed change manifest, also as JSON. No code is written and none is run.

Two requested routes: standard `gpt-5.6-luna` and stronger `gpt-5.6-sol`. `model_reasoning_effort` was set explicitly to `medium` on both, so a route difference is not an effort difference. The controller never sees which model served a call — every route statement here is about what was *requested*.

Four route cells:

| cell | planner route | constructor route |
| --- | --- | --- |
| standard-planner__standard-constructor | gpt-5.6-luna | gpt-5.6-luna |
| stronger-planner__standard-constructor | gpt-5.6-sol | gpt-5.6-luna |
| standard-planner__stronger-constructor | gpt-5.6-luna | gpt-5.6-sol |
| stronger-planner__stronger-constructor | gpt-5.6-sol | gpt-5.6-sol |

Four tasks x four cells x three replications = 48 planner reservations and 48 constructor reservations, 96 main starts.

## The task corpus

Four public task packages, balanced two medium against two complex and two pre-build against two reconstructed. Each carries a stable outcome, acceptance atoms, ordered facts, permitted and prohibited paths, and one construction evidence trigger — a fact a constructor 'discovers' that a good plan should let it amend.

| task package | complexity | provenance |
| --- | --- | --- |
| decision-record-ordinal-uniqueness | medium | pre-build |
| atomic-write-symlink-hardening | medium | reconstructed |
| pack-profiles | complex | pre-build |
| catalogue-corporate-trust-store | complex | reconstructed |

Every command in the task material is inert text. Workers were given no shell, filesystem, web, network, messaging or delegation authority, and a tool event would have terminally failed the response. None occurred.

## How responses were measured

Two kinds of measure, labelled separately throughout:

- **structural** — a hard check on shape or identity: does a proposed path fall inside the permitted globs, does a digest match, is an acceptance atom mapped.
- **lexical** — a frozen keyword-group match over the response text. A semantic atom or a decision choice counts as present when every keyword in one alternative group appears. This is auditable and repeatable, and it detects *presence of wording*, not correctness of reasoning.

The controller-only registry names, per task, the explicit acceptable and unacceptable construction choices — not merely a keyword list. It was frozen before the first calibration start and never entered a worker prompt; the blinding check re-read all dispatched payload bytes and found 0 leak(s).

Ceiling rates for the lexical measures, pooled over all cells — how often the keyword match fires at all, which bounds how much room it has to separate two cells:

- planner semantic atoms matched: 99.6%
- constructor semantic atoms matched: 99.6%
- planner acceptable decision choices credited: 89.6%
- constructor acceptable decision choices credited: 97.4%

A measure already near its ceiling cannot show a route difference even if one exists.

### Measures with no variance in this corpus

A measure that took one value across all 48 responses of a stage cannot separate two route cells, whatever the routes did. These are named rather than quietly reported as a zero difference.

| stage | measure | the single value it took |
| --- | --- | --- |
| planner | acceptance_atoms_covered_by_a_task | 3 |
| planner | acceptance_atoms_expected | 3 |
| planner | acceptance_atoms_verified_by_a_check | 3 |
| planner | acceptance_correct | 3 |
| planner | acceptance_extra | 0 |
| planner | acceptance_mapped | 3 |
| planner | acceptance_missing | 0 |
| planner | boundary_violations_in_proposed_paths | 0 |
| planner | correct_decisions_available | 4 |
| planner | dependencies_naming_an_undeclared_task | 0 |
| planner | fact_coverage | +1.0000 |
| planner | incorrect_decisions_available | 4 |
| planner | semantic_atoms_total | 5 |
| planner | spurious_unresolved_questions | 0 |
| planner | unresolved_questions | 0 |
| planner | unsupported_promises | 0 |
| planner | useful_unresolved_questions | 0 |
| constructor | acceptance_atoms_expected | 3 |
| constructor | acceptance_correct | 3 |
| constructor | acceptance_duplicates | 0 |
| constructor | acceptance_extra | 0 |
| constructor | acceptance_mapped | 3 |
| constructor | acceptance_missing | 0 |
| constructor | correct_decisions_available | 4 |
| constructor | incorrect_decisions_available | 4 |
| constructor | prohibited_path_hits | 0 |
| constructor | protocol_deviations_self_reported | 0 |
| constructor | scope_additions | 0 |
| constructor | self_audit_false_positives | 0 |
| constructor | self_audit_true_positives | 0 |
| constructor | semantic_atoms_total | 5 |
| constructor | unsupported_promises | 0 |

## Planner-stage results

| measure (cell mean) | standard-planner / standard-constructor | stronger-planner / standard-constructor | standard-planner / stronger-constructor | stronger-planner / stronger-constructor |
| --- | --- | --- | --- | --- |
| semantic_coverage | 1.0000 | 0.9833 | 1.0000 | 1.0000 |
| fact_coverage | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| correct_decisions | 3.5000 | 3.6667 | 3.5000 | 3.6667 |
| incorrect_decisions | 1.7500 | 2.2500 | 1.6667 | 2.1667 |
| acceptance_correct | 3.0000 | 3.0000 | 3.0000 | 3.0000 |
| self_audit_missed_risks | 0 | 0.0833 | 0 | 0 |
| raw_words | 628.5833 | 830.4167 | 633.0000 | 838.8333 |
| output_tokens | 1885.5833 | 2845.1667 | 1828.1667 | 3262.4167 |
| wall_clock_seconds | 39.0267 | 61.3322 | 38.1107 | 68.3433 |

## Constructor-stage results

| measure (cell mean) | standard-planner / standard-constructor | stronger-planner / standard-constructor | standard-planner / stronger-constructor | stronger-planner / stronger-constructor |
| --- | --- | --- | --- | --- |
| semantic_coverage | 1.0000 | 0.9833 | 1.0000 | 1.0000 |
| correct_decisions | 4.0000 | 3.9167 | 3.8333 | 3.8333 |
| incorrect_decisions | 1.7500 | 1.8333 | 1.9167 | 2.0000 |
| scope_additions | 0 | 0 | 0 | 0 |
| acceptance_correct | 3.0000 | 3.0000 | 3.0000 | 3.0000 |
| plan_identity_exact | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| self_audit_missed_risks | 0 | 0.1667 | 0 | 0 |
| raw_words | 324.8333 | 374.0000 | 558.0833 | 586.6667 |
| output_tokens | 1191.5833 | 1385.7500 | 1859.3333 | 1957.9167 |
| wall_clock_seconds | 26.9378 | 30.6639 | 41.3925 | 41.4357 |

Stage measures are kept apart on purpose. A better planner score is not a construction claim, and this report never collapses one into the other.

## Whole-trajectory results

| measure (cell mean) | standard-planner / standard-constructor | stronger-planner / standard-constructor | standard-planner / stronger-constructor | stronger-planner / stronger-constructor |
| --- | --- | --- | --- | --- |
| final_correct_decisions | 4.0000 | 3.9167 | 3.8333 | 3.8333 |
| residual_severe_errors | 1.7500 | 1.9167 | 1.9167 | 2.0000 |
| defect_propagated | 0.8333 | 0.8333 | 0.7500 | 0.9167 |
| defect_repaired | 0.0833 | 0.0833 | 0.0833 | 0 |
| new_defect_appeared | 0.0833 | 0.0833 | 0.1667 | 0.0833 |
| clean_throughout | 0 | 0 | 0 | 0 |
| plan_identity_exact | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| stable_outcome_preserved | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| visible_words | 953.4167 | 1204.4167 | 1191.0833 | 1425.5000 |
| output_tokens | 3077.1667 | 4230.9167 | 3687.5000 | 5220.3333 |
| summed_worker_seconds | 65.9645 | 91.9962 | 79.5032 | 109.7790 |
| terminal_elapsed_seconds | 812.0588 | 818.2898 | 827.7174 | 824.5019 |

## The equal-budget primary comparison, in full

`stronger-planner__standard-constructor` minus `standard-planner__stronger-constructor`.

### planner stage

| measure | kind | better | mean task effect | numerator | denominator (matched pairs) | task-cluster interval | tasks | direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| acceptance_correct | structural | higher | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| acceptance_missing | structural | lower | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| boundaries_stated | structural | neutral | +0.9167 | +11.0000 | 12 | [+0.6667, +1.4167] | 4 | n/a |
| contradictions | lexical | lower | 0 | 0 | 12 | [-0.4167, +0.3333] | 4 | no difference |
| correct_decisions | lexical | higher | +0.1666 | +2.0000 | 12 | [+0.0000, +0.3333] | 4 | favours stronger-planner__standard-constructor |
| dependencies_naming_an_undeclared_task | structural | lower | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| fact_coverage | structural | higher | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| incorrect_decisions | lexical | lower | +0.5833 | +7.0000 | 12 | [+0.0833, +1.3334] | 4 | favours standard-planner__stronger-constructor |
| input_tokens | structural | neutral | +1490.8333 | +17890.0000 | 12 | [+1486.0000, +1499.7500] | 4 | n/a |
| output_tokens | structural | neutral | +1017.0000 | +12204.0000 | 12 | [+778.5000, +1288.3333] | 4 | n/a |
| raw_words | structural | neutral | +197.4167 | +2369.0000 | 12 | [+169.6667, +225.1667] | 4 | n/a |
| self_audit_false_positives | hybrid | lower | -0.7500 | -9.0000 | 12 | [-0.9167, -0.6667] | 4 | favours stronger-planner__standard-constructor |
| self_audit_missed_risks | hybrid | lower | +0.0833 | +1.0000 | 12 | [+0.0000, +0.2500] | 4 | favours standard-planner__stronger-constructor |
| self_audit_true_positives | hybrid | higher | +0.0833 | +1.0000 | 12 | [+0.0000, +0.2500] | 4 | favours stronger-planner__standard-constructor |
| semantic_coverage | lexical | higher | -0.0167 | -0.2000 | 12 | [-0.0500, +0.0000] | 4 | favours standard-planner__stronger-constructor |
| semantic_omissions | lexical | lower | +0.0833 | +1.0000 | 12 | [+0.0000, +0.2500] | 4 | favours standard-planner__stronger-constructor |
| spurious_unresolved_questions | lexical | lower | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| unsupported_promises | lexical | lower | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| useful_unresolved_questions | lexical | neutral | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | n/a |
| wall_clock_seconds | structural | neutral | +23.2216 | +278.6590 | 12 | [+18.0449, +28.8412] | 4 | n/a |

### constructor stage

| measure | kind | better | mean task effect | numerator | denominator (matched pairs) | task-cluster interval | tasks | direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| acceptance_correct | structural | higher | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| acceptance_missing | structural | lower | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| contradictions | lexical | lower | +0.0833 | +1.0000 | 12 | [+0.0000, +0.2500] | 4 | favours standard-planner__stronger-constructor |
| correct_decisions | lexical | higher | +0.0833 | +1.0000 | 12 | [+0.0000, +0.2500] | 4 | favours stronger-planner__standard-constructor |
| decisions_complete | structural | higher | +1.0834 | +13.0000 | 12 | [+0.1667, +1.6667] | 4 | favours stronger-planner__standard-constructor |
| incorrect_decisions | lexical | lower | -0.0833 | -1.0000 | 12 | [-0.3333, +0.1666] | 4 | favours stronger-planner__standard-constructor |
| input_tokens | structural | neutral | -1098.8333 | -13186.0000 | 12 | [-1159.6667, -1038.0000] | 4 | n/a |
| output_tokens | structural | neutral | -473.5833 | -5683.0000 | 12 | [-895.4167, -123.1667] | 4 | n/a |
| prohibited_path_hits | structural | lower | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| raw_words | structural | neutral | -184.0833 | -2209.0000 | 12 | [-242.5000, -107.7500] | 4 | n/a |
| scope_additions | structural | lower | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| self_audit_false_positives | hybrid | lower | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| self_audit_missed_risks | hybrid | lower | +0.1667 | +2.0000 | 12 | [+0.0000, +0.5000] | 4 | favours standard-planner__stronger-constructor |
| self_audit_true_positives | hybrid | higher | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| semantic_coverage | lexical | higher | -0.0167 | -0.2000 | 12 | [-0.0500, +0.0000] | 4 | favours standard-planner__stronger-constructor |
| semantic_omissions | lexical | lower | +0.0833 | +1.0000 | 12 | [+0.0000, +0.2500] | 4 | favours standard-planner__stronger-constructor |
| unresolved_questions | lexical | neutral | -1.0000 | -12.0000 | 12 | [-2.0000, -0.0000] | 4 | n/a |
| unsupported_promises | lexical | lower | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| wall_clock_seconds | structural | neutral | -10.7286 | -128.7430 | 12 | [-21.0907, -3.0510] | 4 | n/a |

### whole trajectory

| measure | kind | better | mean task effect | numerator | denominator (matched pairs) | task-cluster interval | tasks | direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clean_throughout | hybrid | higher | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| defect_propagated | hybrid | lower | +0.0833 | +1.0000 | 12 | [+0.0000, +0.2500] | 4 | favours standard-planner__stronger-constructor |
| defect_repaired | hybrid | higher | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| final_correct_decisions | lexical | higher | +0.0833 | +1.0000 | 12 | [+0.0000, +0.2500] | 4 | favours stronger-planner__standard-constructor |
| input_tokens | structural | neutral | +392.0000 | +4704.0000 | 12 | [+335.5000, +450.0833] | 4 | n/a |
| new_defect_appeared | hybrid | lower | -0.0833 | -1.0000 | 12 | [-0.2500, +0.0000] | 4 | favours stronger-planner__standard-constructor |
| output_tokens | structural | neutral | +543.4167 | +6521.0000 | 12 | [+168.9167, +868.0000] | 4 | n/a |
| plan_identity_exact | hybrid | higher | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| residual_severe_errors | hybrid | lower | 0 | 0 | 12 | [-0.2500, +0.2500] | 4 | no difference |
| stable_outcome_preserved | hybrid | higher | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| summed_worker_seconds | structural | neutral | +12.4930 | +149.9160 | 12 | [+2.5725, +19.9127] | 4 | n/a |
| terminal_elapsed_seconds | structural | neutral | -9.4276 | -113.1320 | 12 | [-25.2310, +1.3211] | 4 | n/a |
| visible_words | structural | neutral | +13.3333 | +160.0000 | 12 | [-67.8333, +114.8333] | 4 | n/a |

## Every other predeclared contrast

### both stronger minus both standard

`stronger-planner__stronger-constructor minus standard-planner__standard-constructor` — both stronger minus both standard; double the stronger budget, not an equal-budget comparison

| measure | kind | better | mean task effect | numerator | denominator (matched pairs) | task-cluster interval | tasks | direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| final_correct_decisions | lexical | higher | -0.1667 | -2.0000 | 12 | [-0.5000, +0.0000] | 4 | favours standard-planner__standard-constructor |
| residual_severe_errors | hybrid | lower | +0.2500 | +3.0000 | 12 | [+0.0000, +0.5000] | 4 | favours standard-planner__standard-constructor |
| clean_throughout | hybrid | higher | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| output_tokens | structural | neutral | +2143.1667 | +25718.0000 | 12 | [+1653.5000, +2632.8333] | 4 | n/a |
| summed_worker_seconds | structural | neutral | +43.8145 | +525.7740 | 12 | [+32.2253, +55.4036] | 4 | n/a |

### constructor route effect standard planner

`standard-planner__stronger-constructor minus standard-planner__standard-constructor` — constructor route effect with the planner route held at standard

| measure | kind | better | mean task effect | numerator | denominator (matched pairs) | task-cluster interval | tasks | direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| final_correct_decisions | lexical | higher | -0.1667 | -2.0000 | 12 | [-0.5000, +0.0000] | 4 | favours standard-planner__standard-constructor |
| residual_severe_errors | hybrid | lower | +0.1666 | +2.0000 | 12 | [-0.6667, +0.8333] | 4 | favours standard-planner__standard-constructor |
| clean_throughout | hybrid | higher | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| output_tokens | structural | neutral | +610.3333 | +7324.0000 | 12 | [+313.0000, +907.6667] | 4 | n/a |
| summed_worker_seconds | structural | neutral | +13.5387 | +162.4640 | 12 | [+7.2744, +20.2712] | 4 | n/a |

### constructor route effect stronger planner

`stronger-planner__stronger-constructor minus stronger-planner__standard-constructor` — constructor route effect with the planner route held at stronger

| measure | kind | better | mean task effect | numerator | denominator (matched pairs) | task-cluster interval | tasks | direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| final_correct_decisions | lexical | higher | -0.0833 | -1.0000 | 12 | [-0.2500, +0.0000] | 4 | favours stronger-planner__standard-constructor |
| residual_severe_errors | hybrid | lower | +0.0833 | +1.0000 | 12 | [-0.4167, +0.5000] | 4 | favours stronger-planner__standard-constructor |
| clean_throughout | hybrid | higher | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| output_tokens | structural | neutral | +989.4167 | +11873.0000 | 12 | [+473.1667, +1550.7500] | 4 | n/a |
| summed_worker_seconds | structural | neutral | +17.7828 | +213.3940 | 12 | [+6.4203, +29.2130] | 4 | n/a |

### planner route effect standard constructor

`stronger-planner__standard-constructor minus standard-planner__standard-constructor` — planner route effect with the constructor route held at standard

| measure | kind | better | mean task effect | numerator | denominator (matched pairs) | task-cluster interval | tasks | direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| final_correct_decisions | lexical | higher | -0.0833 | -1.0000 | 12 | [-0.2500, +0.0000] | 4 | favours standard-planner__standard-constructor |
| residual_severe_errors | hybrid | lower | +0.1666 | +2.0000 | 12 | [-0.4167, +0.5833] | 4 | favours standard-planner__standard-constructor |
| clean_throughout | hybrid | higher | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| output_tokens | structural | neutral | +1153.7500 | +13845.0000 | 12 | [+964.0000, +1343.5000] | 4 | n/a |
| summed_worker_seconds | structural | neutral | +26.0317 | +312.3800 | 12 | [+22.5872, +29.4762] | 4 | n/a |

### planner route effect stronger constructor

`stronger-planner__stronger-constructor minus standard-planner__stronger-constructor` — planner route effect with the constructor route held at stronger

| measure | kind | better | mean task effect | numerator | denominator (matched pairs) | task-cluster interval | tasks | direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| final_correct_decisions | lexical | higher | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| residual_severe_errors | hybrid | lower | +0.0833 | +1.0000 | 12 | [-0.6667, +0.7500] | 4 | favours standard-planner__stronger-constructor |
| clean_throughout | hybrid | higher | 0 | 0 | 12 | [+0.0000, +0.0000] | 4 | no difference |
| output_tokens | structural | neutral | +1532.8333 | +18394.0000 | 12 | [+991.1667, +1945.6667] | 4 | n/a |
| summed_worker_seconds | structural | neutral | +30.2758 | +363.3100 | 12 | [+19.4012, +40.9098] | 4 | n/a |

## Planner x constructor interaction

Defined as (both-stronger minus stronger-planner) minus (stronger-constructor minus both-standard). Zero means the two route upgrades simply add; a non-zero value means the second upgrade buys a different amount once the other stage is already upgraded.

| measure | kind | mean task interaction | task-cluster interval |
| --- | --- | --- | --- |
| clean_throughout | hybrid | 0 | [+0.0000, +0.0000] |
| defect_propagated | hybrid | +0.1667 | [+0.0000, +0.5000] |
| defect_repaired | hybrid | -0.0833 | [-0.5000, +0.2500] |
| final_correct_decisions | lexical | +0.0833 | [+0.0000, +0.2500] |
| input_tokens | structural | +31.7500 | [-111.5000, +109.5833] |
| new_defect_appeared | hybrid | -0.0833 | [-0.2500, +0.0000] |
| output_tokens | structural | +379.0833 | [-274.9167, +797.6667] |
| plan_identity_exact | hybrid | 0 | [+0.0000, +0.0000] |
| residual_severe_errors | hybrid | -0.0833 | [-1.2500, +1.1667] |
| stable_outcome_preserved | hybrid | 0 | [+0.0000, +0.0000] |
| summed_worker_seconds | structural | +4.2442 | [-7.5442, +12.8791] |
| terminal_elapsed_seconds | structural | -9.4465 | [-18.0487, +1.5481] |
| visible_words | structural | -16.5833 | [-178.5833, +132.1667] |

## Complexity and provenance strata

| stage | measure | medium | complex | pre-build | reconstructed |
| --- | --- | --- | --- | --- | --- |
| planner | semantic_coverage | -0.0333 | 0 | -0.0333 | 0 |
| planner | correct_decisions | 0 | +0.3333 | +0.1666 | +0.1666 |
| planner | incorrect_decisions | +0.1666 | +1.0000 | +1.0000 | +0.1666 |
| constructor | semantic_coverage | -0.0333 | 0 | -0.0333 | 0 |
| constructor | correct_decisions | +0.1666 | 0 | +0.1666 | 0 |
| constructor | incorrect_decisions | -0.1666 | 0 | -0.3333 | +0.1666 |
| trajectory | final_correct_decisions | +0.1666 | 0 | +0.1666 | 0 |
| trajectory | residual_severe_errors | 0 | 0 | -0.1666 | +0.1666 |

Two tasks sit in each stratum, so a stratum figure is a two-task average. It describes this corpus and carries no interval.

## Costs

| cost | value |
| --- | --- |
| planner input tokens | 1135557 |
| planner output tokens | 117856 |
| constructor input tokens | 1203392 |
| constructor output tokens | 76735 |
| main input tokens | 2338949 |
| main output tokens | 194591 |
| summed worker seconds (main) | 4166.92 |
| calibration summed worker seconds | 52.27 |

## Exact accounting

Calibration is reconciled separately and is not a study measure. 8 calibration starts, 8 observed model starts, gate passed: True.

| line | count |
| --- | --- |
| expected main reservations | 96 |
| reservations accounted | 96 |
| CLI process starts | 96 |
| controller-observed model starts | 96 |
| explicitly stopped constructor cells (unstarted) | 0 |
| planner terminal records | 48 |
| constructor terminal records | 48 |
| tool-use violations | 0 |
| schema parse failures | 0 |
| responses with prose outside the JSON | 0 |
| process failures | 0 |
| timeouts | 0 |
| response repairs | 0 |
| retries after a model start | 0 |
| zero-model-start quarantines | 0 |
| served model identity available | 0 of all starts |
| token telemetry unavailable | 0 |

Requested-route counts — planner: {"gpt-5.6-luna": 24, "gpt-5.6-sol": 24}; constructor: {"gpt-5.6-luna": 24, "gpt-5.6-sol": 24}.

Reconciliation: main reservations equal expected: True; main starts equal 96 minus stopped cells: True.

No constructor cell was stopped: every planner returned a usable artifact.

Missing data stays unavailable. Nothing in this block is recorded as zero because it was not observed.

## Incidents

| when | what | how it was handled |
| --- | --- | --- |
| planner stage, ordinal 28 | The planner on `pack-profiles|r1` / standard-planner__stronger-constructor (requested route gpt-5.6-luna) echoed its alias as `J6Z4-N46` instead of the assigned `J6Z4-N46C` — one trailing character dropped. | Recorded, not repaired. The response reached a model start and is therefore terminal. Its artifact was schema-valid and its stable-outcome digest echo was exact, so it was passed byte-for-byte to its constructor like every other cell. The defect is carried in the row-level measure `alias_exact` and affects no outcome measure. |

### Rule amendments

Two controller-side rules were amended after the 48 planner starts and before the first constructor start. Both were mechanically derived, neither was driven by an interim outcome, and both counts are reported.

**blinding-amendment-001.** The as-frozen list contained the bare adjective 'stronger'. Three constructor payloads carried it inside planner-authored prose about identity binding ('a stronger identity-preserving boundary', 'stronger identity binding or revalidation', 'a stronger guarded operation'). None names a route, a stage pairing, or a cell. A bare adjective in ordinary technical English is not a treatment label, and failing the block on it would be a false positive. As-frozen hits: 3; after the correction: 0. Only label-shaped forms fail: the four cell names, the two route names, and the adjective paired with a stage, route, model or arm.

**grading-amendment-001.** A contradiction marker that appears verbatim in the worker-visible material a response was given is void for that response. For a planner that material is its block's task facts, acceptance atoms, stable outcome and evidence trigger. For a constructor it is additionally the planner artifact it was handed. A response quoting its own input faithfully would otherwise be counted as contradicting the stable outcome. Constructor voidness is computed per BLOCK as the union over that block's four cells, not per cell. Each cell here has its own planner, so a per-cell void set would depend on the treatment and would absorb part of the very effect being measured. The union is identical for all four constructors in a block, so no cell gains or loses a marker relative to another and the within-block matched contrast is preserved. The cost is that the union is conservative: it voids a marker for a cell whose own input did not carry it.

18 of 48 constructor payloads carried a marker written by their own planner. Void markers: `after replacement`, `non-blocking warning`, `unbounded`; blocks with a constructor void: 7 of 12. No planner block needed a void. Every row carries both `contradictions_as_frozen` and the voided `contradictions`.

## Propagation, described and not claimed

**Post-treatment and non-causal.** plan-defect state is an outcome of the planner route, so grouping trajectories by it conditions on a mediator. This table describes what happened; it does not identify an effect.

| plan state | trajectories | propagated | repaired | new defect | clean throughout | mean residual severe errors |
| --- | --- | --- | --- | --- | --- | --- |
| plan_clean | 5 | 0 | 0 | 5 | 0 | +1.6000 |
| plan_defect | 43 | 40 | 3 | 0 | 0 | +1.9302 |

## Limits

- The controller requests a route name and never observes which model served it; every route claim is a requested-routing claim.
- Semantic coverage, decision correctness, contradiction and promise measures are lexical keyword-group matches over response text. They detect presence of wording, not correctness of reasoning.
- Constructors produce bounded decision records and proposed change manifests. No model-authored code was written, run, or evaluated, so nothing here is an implementation or build performance result.
- Four task clusters. Intervals describe spread across this corpus and establish neither population significance nor noninferiority.
- Three replications per task estimate response variance within a task. They are not independent task samples.
- Several measures took a single value across all 48 responses of a stage. Those measures cannot separate two route cells and are named in the report rather than reported as a zero difference.
- Two controller-side rules were amended after the planner stage and before the first constructor start, both mechanically derived and applied uniformly: the blinding label list dropped the bare adjectives, and a contradiction marker quoted verbatim from a response's own input is void. The contradiction void is computed per block as the union over that block's four cells, so it is cell-invariant; both the as-frozen and the voided counts are carried on every row.
- Repository visibility during a worker call is a declared limitation, not a confinement claim: the sandbox was requested read-only and no tool event was observed, which is evidence of non-use rather than proof of impossibility.

## Evidence

- Working root: `.context/experiments/codex-headless-via-claude-run6-r1/`
- Design freeze: `sha256:784b024d61d7230e7020d4cdeb3aea7e6d72269ca5ff0f312469f358e0848ad5`
- JSON receipt: `.context/codex-headless-run6-result.json`. The two handoffs cross-reference each other, so neither can carry the other's final digest inside itself. The JSON records this report's digest; both final digests are recorded together in `controller/handoff-digests.json`.
- Prior headless Codex evidence, bound by digest and not pooled with this block:
  - `.context/codex-headless-run1-result.json` `sha256:231b40c25637ae702108a0a44a5f0761eb4a2b429473f5c5c080fc5b2a01e503` — digest verified present in `docs/product/research/plan-evolution-experiments/codex-headless-review-policy-run-1.json`
  - `.context/codex-headless-runs2-5-result.json` `sha256:b51fb1ac58489d81b10f1b3f69b676a93820b55cb0d31a12f4aee2e9e6e8a187` — digest verified present in `docs/product/research/plan-evolution-experiments/codex-headless-construction-panel-runs-2-5.json`

