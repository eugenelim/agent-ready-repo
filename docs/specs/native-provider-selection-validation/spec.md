# Spec: Code-intelligence real-world usage validation

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0079
- **Brief:** none
- **Discovery:** docs/product/intents/FEAT-0032-native-provider-selection-validation.md
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. Verification must
> be derivable from it. This pair is reopened for the owner's scope amendment;
> the earlier approval does not approve these revised criteria.

## Outcome

CAP-0011's owner receives evidence of whether maintainers or adopters can use
the `code-intelligence` pack to understand their own legacy apps and investigate
a real change after setup and training. Findings are checked against source.
The result distinguishes useful findings, incorrect claims, setup problems,
help needed, and evidence gaps, then recommends retaining or changing the
pack's grounding and exploration role or onboarding.

## What Changes

- A self-serve protocol and participant worksheet link the first-session guide
  for setup and provide skill practice, task prompts, source checks, and fill-in
  response fields for an actual app task.
- Participants use their own authorized existing legacy-app repositories.
  Training and sample prompts are built into the documents. Help is optional;
  participants do not need a facilitator to complete and return the worksheet.
- A minimized result records what was useful, what failed, what remains
  unknown, and a recommendation for CAP-0011's owner.
- Blind provider selection, unaided recognition of tool limits, and comparison
  across native provider shapes are outside this delivery. No new intent or
  backlog work is created for those future questions.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Guided protocol | Declare the method before observation | `docs/product/research/native-provider-selection-validation/protocol.md` | FEAT-0032 owner | Approved revision, observation fields, interpretation rules | Result cites the revision used and any deviations |
| Self-serve participant worksheet | Teach pack use and collect participants' coded responses | `docs/product/research/native-provider-selection-validation/instrument.md` | Participant; FEAT-0032 owner maintains the blank template | Linked setup, practice, task prompts, source checks, fill-in fields | Unassisted reader dry-run completes the flow or reports setup blockers |
| First-session walkthrough | Reuse the existing public setup and usage guide | `guides/code-intelligence/tutorials/first-session.md` | Pack documentation owner | Copyable prompts and clear checkpoints | Worksheet links the guide; source and guide checks pass |
| Minimized observations and result | Support a bounded usefulness judgment | `docs/product/research/native-provider-selection-validation/result.md` | Participants and FEAT-0032 owner | Coded task observations, source-verification summaries, gaps, recommendation | No identifying data or raw app content retained |
| Parent decision route | Keep the owner responsible for the decision | `docs/product/intents/CAP-0011-optional-code-intelligence-composition.md` | CAP-0011 owner | Linked owner decision or explicit pending field in the result | No automatic change to the parent verdict |

## Agent Rules

### Always do

- Approve the guided protocol revision before invitations or participant attempts.
- Make `instrument.md` the participant entry point and response worksheet.
  Link setup to the existing first-session guide; avoid duplicate setup commands.
- Teach the `code-intelligence` skill through prompts and source checks. Allow
  practice, follow-up questions, and optional help; record assistance as evidence.
- Let participants fill in and return their coded response fields themselves.
  Provide an approved feedback channel; require no facilitator or app access.
- Anchor the exercise to a real pending change in an existing legacy app.
- Verify important claims in source and distinguish graph evidence, verified
  facts, incorrect claims, and unresolved questions.
- Keep authorized app content local; retain only short coded summaries.
- Report the actual sample and environment coverage without generalizing beyond it.
- Route the result to CAP-0011's owner for a separate decision.

### Ask first

- Distribute the study invitation or collect responses, make recordings, or use an app or
  agent environment that is not already authorized for the intended activity.
- Change the approved method after observations become visible. Keep deviations
  explicit; revised methods require separate approval and cannot retroactively repair observations.

### Never do

- Collect credentials, protected configuration, private endpoints, customer
  data, personal or repository identity, or app source in committed records.
- Require public source: authorized private app use may remain entirely within
  the participant's approved environment, with no repository access granted to
  the research team and no private content retained.
- Treat coaching as failure, score unaided provider selection, require a second
  provider shape, or apply the historical five-of-six pass line.
- Convert a successful guided trial into proof of arbitrary-provider
  generalization or population-wide adoption.
- Normalize provider interfaces into a shared schema or change Core's
  no-provider path.
- Invent observations, omit failures, or interpret an execution gap as a
  negative usefulness result.

## Testing Strategy

Goal-based document checks cover the guided method, training steps, sample
prompts, observation fields, privacy boundaries, and links. Guide validators
check the existing public walkthrough. An unassisted reader dry-run checks the
entry point, linked setup, prompts, fill-in fields, and return path on authorized
content before invitations. Participant-completed worksheets supply self-reported
usefulness evidence; a live observed session is not required. A second reader checks that
interpretation follows the approved qualitative rules and is supported by the
minimized observations. Historical blind classifier checks are not delivery gates.

- **VI-0013 (AC-0013):** Approved method revision and pre-session receipt.
- **VI-0014 (AC-0014):** Worksheet/link audit; unassisted reader dry-run.
- **VI-0015 (AC-0015):** Consent/access preflight and coded completed tasks or gaps.
- **VI-0016 (AC-0016):** Coded actual app, host, pack, and index-readiness coverage.
- **VI-0017 (AC-0017):** Source-verification summaries for important findings.
- **VI-0018 (AC-0018):** Investigation checklist and feedback on usefulness.
- **VI-0019 (AC-0019):** Evidence-linked retain-role recommendation.
- **VI-0020 (AC-0020):** Evidence-linked change-role/onboarding recommendation.
- **VI-0021 (AC-0021):** Explicit execution-gap or insufficient-evidence record.
- **VI-0022 (AC-0022):** Field allowlist check and manual free-text privacy audit.
- **VI-0023 (AC-0023):** Independent interpretation receipt.
- **VI-0024 (AC-0024):** Owner-decision link or explicit pending field.

## Acceptance Criteria

- [ ] **AC-0013.** Before observations, the owner approves a guided protocol
  revision declaring recruitment scope, planned session coverage, the task
  workflow, observation fields, interpretation rules, and privacy boundaries.
  The result cites that revision and records deviations.
- [ ] **AC-0014.** `instrument.md` is a self-serve fill-in Markdown worksheet.
  A participant reads its goal and app/task requirements, follows its link to
  first-session steps 1–5 for setup, returns for practice and investigation
  prompts, and fills in coded response fields before submitting through the
  provided feedback channel. No facilitator is required. The prompts cover
  definition/callers, wider impact, a dependency path, repository authority,
  and historical co-change; setup blockers can be submitted without guessing
  answers to unattempted steps.
- [ ] **AC-0015.** Consenting maintainers or adopters use their own authorized
  existing legacy-app repositories and actual pending changes. The result
  reports planned attempts and returned worksheets, completed or stopped steps,
  and optional assistance. Evidence is labeled participant self-report, with
  source checks performed locally rather than independently observed. Missing or interrupted
  sessions are explicit gaps; there is no three-person pass threshold.
- [ ] **AC-0016.** Completed sessions use the installed code-intelligence pack
  in an authorized live agent environment with a usable local index. The result
  records coded host/setup coverage and failures. There is no requirement for
  two environments or different provider shapes.
- [ ] **AC-0017.** Important findings are checked against actual source by the
  participant. Coded observations distinguish verified claims, incorrect or
  unsupported claims, and unresolved evidence gaps. Participants need not
  independently discover a provider or recite expected limit wording.
- [ ] **AC-0018.** Each completed investigation produces a local checklist for
  the chosen change. Feedback states which findings helped, what still required
  manual investigation, and where setup or assistance was needed. Authority
  uses governing documents and co-change uses Git history; the code graph alone
  establishes neither claim.
- [ ] **AC-0019.** A `retain role` recommendation cites relevant,
  source-verified findings participants used in their actual investigation,
  along with setup/help costs and remaining limits. It is bounded to observed
  use and does not assert an adoption rate or provider generalization.
- [ ] **AC-0020.** A `change role or onboarding` recommendation cites setup
  barriers, incorrect claims, hidden gaps, or a lack of usable verified findings
  that prevented a usable result. It identifies the affected workflow and
  proposed correction without applying a blind pass/fail score.
- [ ] **AC-0021.** An `insufficient evidence` result names missing execution or
  interpretive evidence instead of inventing observations or a verdict. When
  verified useful findings and blocking problems coexist, the result retains
  both and explains its bounded recommendation; unresolved interpretation is
  insufficient evidence. No numerical blind threshold is relaxed or reused.
- [ ] **AC-0022.** Committed records contain only participant codes, coded
  environment/setup labels, setup outcomes and readiness summaries, generic task
  class, assistance summaries, verified usefulness, incorrect claims, gaps, participant-written generic feedback, coded recruitment
  scope, planned and actual session/setup coverage, approved protocol and worksheet
  revisions, deviations, completed/interrupted/missing activity with generic
  reasons, interpretation, second-reader agreement or disagreement, and owner-route
  fields. No personal data, credentials, organization or repository identity,
  file paths, symbol names, app source or source snippets, protected configuration,
  private endpoints, customer data, quotations, screenshots, recordings,
  transcripts, or raw tool/error output is retained. Free text receives manual
  privacy review against these exclusions as well as field checks.
- [ ] **AC-0023.** A second reader reproduces the evidence-to-recommendation
  reasoning from the minimized observations without unpublished context,
  records disagreements, and confirms that training and help were not treated
  as selection failure. Unresolved disagreements take AC-0021.
- [ ] **AC-0024.** The result names CAP-0011's owner as decider and links the
  subsequent role/onboarding decision or explicitly records it as pending.
  The result cannot mutate the parent verdict itself.

## Follow-ons

None created. Blind selection remains outside this delivery, as recorded in
[CAP-0011's current validation scope](../../product/intents/CAP-0011-optional-code-intelligence-composition.md#current-validation-scope).

## Assumptions

None. Recruitment scope and planned coverage are declared before sessions
under AC-0013; participant consent and authorization are execution preconditions.

## Amendment

- 2026-10-08: owner requested removal of the blind task and guided real-world
  pack validation. Reopened this existing contract as Draft; earlier blind
  criteria and construction receipts are historical, not current gates.
  The existing FEAT-0032 identifier and directory are retained. The child intent
  is historical discovery input; CAP-0011's current scope and this owner-directed
  amendment govern the revised contract. No new intent or backlog item is created.

- 2026-10-08: owner requested self-serve participation: instrument → linked
  first-session setup → prompts and participant-filled response fields. No
  facilitator is required. The pair remains open for renewed review/approval.

## Retired identifiers

The owner removed the blind validation contract on 2026-10-08. Its identifiers
remain historical evidence references and must not be reused for guided use.

- `AC-0001`
- `AC-0002`
- `AC-0003`
- `AC-0004`
- `AC-0005`
- `AC-0006`
- `AC-0007`
- `AC-0008`
- `AC-0009`
- `AC-0010`
- `AC-0011`
- `AC-0012`
- `VI-0001`
- `VI-0002`
- `VI-0003`
- `VI-0004`
- `VI-0005`
- `VI-0006`
- `VI-0007`
- `VI-0008`
- `VI-0009`
- `VI-0010`
- `VI-0011`
- `VI-0012`
