# Planner-constructor model allocation: independent evidence report

Date: 2026-09-28  
Evidence block: `codex-headless-via-claude-run6-r1`  
Evidence class: bounded, non-inferential requested-routing case study  
Status: complete

## Result

This corpus does not show that a stronger requested route should be assigned
to planning or construction by default. The equal-one-stronger-call comparison
produced three separating intermediate measures, and they disagree. Final
correct decisions, residual severe errors, and clean trajectories did not
separate the two allocations.

The all-standard route was also not improved by adding the stronger route at
either stage. A stronger planner with a standard constructor produced 0.08
fewer final correct decisions, 0.17 more residual severe errors, 1,154 more
output tokens, and 26 more summed worker seconds per trajectory than the
all-standard cell. A standard planner with a stronger constructor produced
0.17 fewer final correct decisions, 0.17 more residual severe errors, 610 more
output tokens, and 13.5 more worker seconds. These small quality differences
are descriptive and their four-task intervals do not establish a population
effect, but the cost increases are clear.

The practical default for similarly bounded document work is therefore the
standard requested route at both stages, with stronger-route escalation based
on observed uncertainty or failed checks rather than a fixed phase policy.
If exactly one stronger call must be used, construction is the cheaper weak
preference: it used 543 fewer output tokens and 12.5 fewer worker seconds than
putting that call in planning, while the end-state quality measures remained
flat. That is a cost preference, not an accuracy finding.

## What was tested

A trajectory contained two cold headless calls. The planner produced a bounded
planning artifact. A separate constructor received its exact bytes plus common
construction evidence and produced a decision record and proposed change
manifest. No model-authored code was written, run, or graded.

The controller crossed two requested routes at both stages:

- standard: `gpt-5.6-luna`;
- stronger: `gpt-5.6-sol`.

Both requested `medium` reasoning effort. The runtime did not expose served
model identity, so every comparison concerns requested routing only.

Four public task packages were balanced across medium/complex and
pre-build/reconstructed provenance. Four tasks by four route cells by three
replications produced 48 trajectories and 96 main model starts. Each cell had
12 trajectories. The task, not the replication, is the unit of
generalization.

| Cell | Planner request | Constructor request |
| --- | --- | --- |
| All standard | `gpt-5.6-luna` | `gpt-5.6-luna` |
| Stronger planner | `gpt-5.6-sol` | `gpt-5.6-luna` |
| Stronger constructor | `gpt-5.6-luna` | `gpt-5.6-sol` |
| Both stronger | `gpt-5.6-sol` | `gpt-5.6-sol` |

Eight fresh calibration starts—one planner and constructor pair per cell—passed
before the main panel. Blocked launch order held exactly. Every constructor
echoed the exact digest of its planner artifact, and all 48 planner artifacts
were usable.

## Equal-budget primary comparison

The primary contrast is stronger planner plus standard constructor minus
standard planner plus stronger constructor. Both policies request one stronger
and one standard call.

Only three directional measures had a task-cluster interval excluding zero:

| Stage | Measure | Mean difference | Four-task interval | Direction |
| --- | --- | ---: | --- | --- |
| Planner | Incorrect construction choices | +0.58 | +0.08 to +1.33 | Favors standard planner plus stronger constructor |
| Planner | Self-audit false positives | -0.75 | -0.92 to -0.67 | Favors stronger planner plus standard constructor |
| Constructor | Complete decision fields | +1.08 | +0.17 to +1.67 | Favors stronger planner plus standard constructor |

The incorrect-choice count is the closest of the three to direct plan quality.
The other two measure calibration and response completeness. They should not be
combined into a vote: the measures have different meanings and are not an
approved composite endpoint.

End-state measures were effectively tied:

| Whole-trajectory measure | Stronger planner | Stronger constructor | Difference |
| --- | ---: | ---: | ---: |
| Final correct decisions | 3.9167 | 3.8333 | +0.0833 |
| Residual severe errors | 1.9167 | 1.9167 | 0 |
| Defects propagated | 0.8333 | 0.7500 | +0.0833 |
| Clean throughout | 0 | 0 | 0 |

The one-response difference in final correct decisions had an interval of
0.00 to 0.25 and came from one of four task clusters. Residual severe errors
had an interval of -0.25 to +0.25. Neither supports a practical allocation
claim.

Cost favored placing the stronger request at construction if it had to be used:

| Cost per trajectory | Stronger planner minus stronger constructor |
| --- | ---: |
| Input tokens | +392 |
| Output tokens | +543 |
| Summed worker time | +12.49 s |
| Visible words | +13 |
| End-to-end terminal elapsed time | -9.43 s, interval crosses zero |

## All four policies

| Measure | All standard | Stronger planner | Stronger constructor | Both stronger |
| --- | ---: | ---: | ---: | ---: |
| Final correct decisions | 4.0000 | 3.9167 | 3.8333 | 3.8333 |
| Residual severe errors | 1.7500 | 1.9167 | 1.9167 | 2.0000 |
| Output tokens | 3,077 | 4,231 | 3,688 | 5,220 |
| Summed worker seconds | 65.96 | 92.00 | 79.50 | 109.78 |
| Visible words | 953 | 1,204 | 1,191 | 1,426 |

Requesting the stronger route at both stages used 2,143 more output tokens and
43.8 more worker seconds per trajectory than all standard. It produced 0.17
fewer final correct decisions and 0.25 more residual severe errors in this
corpus. The quality intervals touch zero, so the defensible interpretation is
“no detected gain at substantially higher cost,” not “the stronger route is
worse in general.”

## Measurement sensitivity

The panel was much better at measuring transport and response shape than final
reasoning quality. Seventeen planner measures and fourteen constructor
measures took one value across all 48 responses at their stage. Acceptance
mapping, permitted scope, unsupported promises, and unresolved questions were
at a ceiling or floor and could not distinguish route cells.

Lexical semantic coverage was also near ceiling: 99.6% at both stages.
Acceptable decision-choice coverage was 89.6% for planners and 97.4% for
constructors. Lexical checks detect whether frozen wording is present; they do
not prove that reasoning is sound.

No trajectory was classed as clean throughout, and every cell averaged 1.75 to
2.00 residual severe errors. The route intervention did not move that outcome.
This may mean route placement has little effect on the sampled tasks, but it
also shows that the current document grader is a blunt instrument for small
capability differences.

With only four task clusters, the bootstrap intervals describe this corpus.
They are not significance tests and cannot establish noninferiority. The two
tasks in each complexity or provenance stratum are too few for a credible
interaction claim.

## Rule amendments

Two controller rules changed after all planner starts and before the first
constructor start. Neither was driven by an outcome comparison.

The blinding scanner originally treated the bare adjective `stronger` as a
treatment label. It falsely matched three ordinary identity-binding phrases in
planner artifacts. The amended rule rejects only route- or stage-shaped label
forms. The reported count changed from three hits to zero.

The contradiction grader found that 18 constructor payloads contained a
frozen contradiction marker inside the planner artifact they were required to
quote or act on. It therefore voided a marker when worker-visible input already
contained it. Because each cell had a different planner artifact, voidness was
computed as the union across all four cells in a task-replication block. This
kept the void set equal across treatment cells, at the cost of conservatively
voiding some markers for cells that did not contain them. The receipt retains
both as-frozen and corrected row counts and a per-cell sensitivity view.

The rules are reasonable protections against false positives and differential
grading. They were not part of the original frozen tool bytes, however, which
creates the integrity limitation below.

## Evidence integrity review

The fixed handoff JSON and report match their current files. The independent
review also verified the design-freeze, aliases, blocks, hidden registry,
launch order, four schemas, and thirteen unchanged frozen tools.

Two current tool files do not match their original design-freeze digests:

| Tool | Frozen digest prefix | Current digest prefix | Reason recorded |
| --- | --- | --- | --- |
| `blinding.py` | `1c19f35e…` | `f56d3044…` | Blinding false-positive amendment |
| `score.py` | `0b4e6662…` | `6f066a2b…` | Input-marker void amendment |

The source amendment records describe the changes and timing, but do not bind
the before and after tool digests. The durable JSON beside this report binds
the current tool and amendment-record digests independently. This preserves
the evidence now on disk, but cannot prove from bytes alone that no other code
changed between the frozen and current versions. The result is usable as a
transparent non-inferential case study, not as a fully mutation-proved causal
result.

Controller measures, contrasts, accounting, blinding results, and calibration
gate are also independently hashed in the durable record. Both earlier
headless Codex handoffs matched their integrated digests and were used as
transport context only; no outcomes were pooled.

## Exact accounting

| Stage | Reservations | Starts | Observed model starts | Terminals | Failures | Tool events |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Calibration | 8 | 8 | 8 | 8 | 0 | 0 |
| Planner | 48 | 48 | 48 | 48 | 0 | 0 |
| Constructor | 48 | 48 | 48 | 48 | 0 | 0 |

There were no stopped constructor cells, schema failures, prose outside JSON,
timeouts, quarantines, response repairs, or retries after a model start.
Planner ordinal 28 dropped the final character of its alias. It remained
terminal, its otherwise valid artifact was passed byte-for-byte to its
constructor, and no outcome measure depended on the alias.

Main calls used 2,338,949 input tokens, 194,591 output tokens, and 4,166.92
summed worker seconds. Calibration used 179,474 input tokens, 682 output
tokens, and 52.27 seconds.

## Decision for the workflow

Do not encode “use the strongest model in planning” or “use the strongest
model in construction” as a general workflow rule from this experiment.
Use the standard route for bounded planning and construction documents when
structural checks are available. Escalate on an observable trigger such as a
failed quality gate, unresolved high-risk decision, or task complexity that
exceeds the standard route's demonstrated envelope.

This conclusion is about document-loop allocation. It does not measure code
implementation, tests, build speed, or served model capability.

## Source evidence

Raw payloads, event streams, reservations, receipts, measures, contrasts, and
checkpoints remain under
`.context/experiments/codex-headless-via-claude-run6-r1/`. The durable JSON
beside this report records source hashes, current amendment hashes, accounting,
the primary contrasts, ceiling measures, and the decision implication.
