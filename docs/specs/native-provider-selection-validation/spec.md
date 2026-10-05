# Spec: Native-provider selection validation

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0079
- **Brief:** none
- **Discovery:** docs/product/intents/FEAT-0032-native-provider-selection-validation.md
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Outcome

CAP-0011's owner receives a blind, question-level result showing whether people
can select suitable native provider actions and carry their limits without a
catalogue-defined schema or RFC-derived coaching. The result unambiguously
routes the parent assumption to survive, do not survive unchanged, or
inconclusive under rules fixed before any live session.

## What Changes

- A frozen six-question protocol, participant instrument, environment preflight,
  observation form, and scoring rule become durable research artifacts.
- The exercise targets three consenting maintainers or adopters across an
  authorized editor/LSP environment and an authorized indexed graph environment;
  missing participant or environment coverage is recorded as inconclusive.
- A minimized result record applies the predeclared disposition rule and routes
  the outcome to CAP-0011's owner without changing the parent automatically.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Validation protocol | Thresholds and blindness must predate observation | `docs/product/research/native-provider-selection-validation/protocol.md` | FEAT-0032 owner | Approval revision and synthetic-case check | Result cites the frozen revision used by every session |
| Human-facing instrument | A human, not the agent, runs each session | `docs/product/research/native-provider-selection-validation/instrument.md` | Human facilitator | Dry-run and prompt audit | Instrument contains no answer key or RFC/golden-example vocabulary |
| Minimized observations and result | The parent needs question-level evidence and a disposition | `docs/product/research/native-provider-selection-validation/result.md` | Human facilitator and FEAT-0032 owner | Three coded sessions or an explicit execution gap, coverage check, scoring table, disposition | No personal, credential, private-source, or customer data is retained |
| Parent decision route | Evidence cannot mutate CAP-0011 by itself | `docs/product/intents/CAP-0011-optional-code-intelligence-composition.md` or a successor intent chosen by its owner | CAP-0011 owner | Explicit survive/reframe/kill decision after reviewing the result | Closeout links the owner decision or records it as still pending |

## Agent Rules

### Always do

- Freeze the questions, success rule, failure rule, inconclusive rule, and
  observation fields before the first participant sees the instrument.
- Give participants only the repository questions, ordinary exposed tool
  metadata, authorized native surfaces, and safety constraints needed to act.
- Use participant codes and provider-shape labels; retain question-level choices,
  explanations, material limits, fallback reasons, and environment coverage.
- Separate environment or metadata failure from participant performance and
  classify inadequate coverage as inconclusive.
- Route the recorded disposition to CAP-0011's owner for a separate decision.

### Ask first

- Recruit a participant, schedule or record a live session, or use a repository
  that is not already authorized for the participant and facilitator.
- Retain quotations, recordings, screenshots, source snippets, personal data,
  organization names, repository names, or provider account identifiers.
- Change the protocol, thresholds, questions, coaching boundary, or evidence
  fields after any participant result is visible.

### Never do

- Request, collect, expose, or store participant credentials, tokens, protected
  configuration, private endpoints, customer data, or private repository content.
- Supply RFC-0079, the golden example, an answer key, expected provider names,
  or the material-limit vocabulary being tested before scoring completes.
- Count an unexplained repository-native fallback as success when a task-fit
  native action is exposed.
- Normalize provider metadata or results into a shared provider schema.
- Weaken a threshold, substitute a participant, or reinterpret inadequate
  environment coverage to obtain a preferred disposition.

## Testing Strategy

Protocol logic uses **TDD-style synthetic cases**: survive, do-not-survive for
unexplained fallback, do-not-survive for coaching dependence, and inconclusive
for missing environment coverage must each map to exactly one disposition.
Instrument blindness and data minimization use **goal-based document checks**.
The three live sessions use **manual QA**: a human facilitator records only the
approved coded observations, and a second reader verifies scoring against the
frozen protocol.

- **VI-0001 — frozen protocol (AC-0001):** goal-based document check over the
  approved revision and session timestamps.
- **VI-0002 — question set (AC-0002):** instrument audit against the six named
  questions.
- **VI-0003 — participant coverage (AC-0003):** manual QA over coded completed
  sessions or the execution-gap record.
- **VI-0004 — environment coverage (AC-0004):** manual QA over minimized live-
  environment coverage fields.
- **VI-0005 — provider-fit scoring (AC-0005):** goal-based scoring check over
  coded provider-fit question records.
- **VI-0006 — baseline scoring (AC-0006):** goal-based scoring check over coded
  authority and co-change records.
- **VI-0007 — survive rule (AC-0007):** synthetic classifier case and final
  scoring table.
- **VI-0008 — failure rule (AC-0008):** synthetic classifier cases and final
  scoring table.
- **VI-0009 — inconclusive rule (AC-0009):** missing-coverage and safety-stop
  synthetic cases plus the result record.
- **VI-0010 — minimized record (AC-0010):** forbidden-field fixture and manual
  privacy audit.
- **VI-0011 — reproducible score (AC-0011):** independent manual rescoring
  receipt.
- **VI-0012 — owner route (AC-0012):** result owner-decision field and linked or
  pending decision record.

## Acceptance Criteria

- [ ] **AC-0001.** The protocol is frozen first: the approved protocol revision
  contains all six questions, scoring fields, thresholds, disposition rules,
  privacy rules, and environment requirements before the first live session.
- [ ] **AC-0002.** The question set matches CAP-0011: the instrument tests symbol
  definition, incoming callers, transitive blast radius, a dependency path,
  repository authority, and historical co-change without embedding expected
  provider choices.
- [ ] **AC-0003.** Participant coverage is explicit: a `survive` or `do not
  survive unchanged` result counts only after three consenting maintainers or
  adopters each route all six questions independently and without answer
  coaching; fewer, interrupted, or non-independent sessions are recorded as
  `inconclusive` under AC-0009.
- [ ] **AC-0004.** Environment coverage is explicit: a `survive` or `do not
  survive unchanged` result counts only after sessions use at least two
  authorized live host/provider environments that collectively expose an
  editor/LSP shape and an indexed graph CLI or MCP shape; fewer than two live
  environments or failure to obtain both shapes is recorded as `inconclusive`
  under AC-0009.
- [ ] **AC-0005.** Counted provider-fit answers are explained: a provider-fit
  question counts only when the participant selects an exposed native action or
  explains why that exposed action is unsuitable and records one material
  evidence limit.
- [ ] **AC-0006.** Baseline choices are deliberate: authority and co-change
  answers count only when the participant selects repository-native evidence
  and explains why the exposed semantic providers do not establish the claim.
- [ ] **AC-0007.** The survive line is fixed: the result is `survive` only when at
  least two of three participants independently clear at least five of six
  questions, both native shapes satisfy AC-0004, and no counted answer invents a
  shared provider contract.
- [ ] **AC-0008.** Failure remains actionable: with adequate participants and
  environment coverage, missing the AC-0007 line, needing withheld vocabulary,
  or inventing a shared provider contract yields `do not survive unchanged`.
  An unexplained fallback on a provider-fit question fails that question under
  AC-0005 and is handled by the same AC-0007 threshold rather than a second
  fallback threshold.
- [ ] **AC-0009.** Inadequate execution is not failure: fewer than three completed
  sessions, fewer than two authorized live host/provider environments, failure
  to expose both provider shapes, unavailable ordinary tool metadata, or a
  session interrupted for safety yields `inconclusive` and does not lower
  AC-0007 or satisfy AC-0008.
- [ ] **AC-0010.** The record is minimized: the committed result contains only
  participant codes, a prior-RFC-familiarity boolean, provider-shape labels,
  question-level choices, explanations, material limits, coverage, scores, and
  disposition; it contains no personal data, credentials, organization or
  repository identity, private source, screenshots, recordings, or raw provider
  output.
- [ ] **AC-0011.** Scoring is independently reproducible: a second reader applies
  the frozen protocol to the minimized observations and reaches the recorded
  scores and disposition without unpublished context.
- [ ] **AC-0012.** The result does not govern itself: the record names the CAP-0011
  owner as decider and links the subsequent survive, reframe, or kill decision,
  or states that the owner decision remains pending.

## Follow-ons

- CAP-0011 owner: apply the recorded disposition; a `do not survive unchanged`
  result requires a refreshed capability intent before implementation expands.
- FEAT-0031 owner: run its separate cold-reader generalization hook if the
  golden example still risks being copied as a universal provider contract.

## Assumptions

none
