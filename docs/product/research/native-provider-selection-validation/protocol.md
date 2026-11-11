# Self-serve code-intelligence usage validation protocol

**Draft revision:** `NPV-SELF-SERVE-PROTOCOL-2026-10-08-r1`.
**Approval:** pending owner approval before participant sessions.
**Participant worksheet:** [instrument.md](instrument.md), `NPV-SELF-SERVE-2026-10-08-r1`.

Use the code-intelligence pack to investigate a real pending change in an
existing legacy app. The worksheet supplies training, links setup to the
first-session guide, and provides prompts and coded response fields. Participants
complete it themselves and check findings in their own source. No facilitator
is required; optional help is allowed and recorded.
[The amended spec](../../../specs/native-provider-selection-validation/spec.md)
owns the acceptance criteria; [CAP-0011](../../intents/CAP-0011-optional-code-intelligence-composition.md#current-validation-scope)
owns the current validation scope.

Blind selection is outside this protocol. The earlier blind script and
[construction receipts](../../../specs/native-provider-selection-validation/notes/verification-ledger.md)
are historical only. Do not use their questions as a pass/fail test, their
five-of-six line, withheld vocabulary, three-person threshold, or provider-shape
coverage as current gates. No new intent or backlog work is created for them.

## Approve the run before observation

The owner approves this protocol and worksheet revision before invitations.
The owner declares a positive planned participant count, coded recruitment and
setup coverage, task-selection constraints, and an approved feedback channel.
An unassisted reader dry-run follows the worksheet's linked setup, returns for
the prompts, fills in a response copy, and checks the return path. Approval
remains pending until that declaration and dry-run are recorded. Distribution
contains the worksheet and feedback channel; participants do not need to read
this protocol or receive a live briefing. No receipt is fabricated.

The result later cites the approved revisions and planned versus actual
coverage. Keep deviations visible. Once observations are visible, stop before
changing the method; any revision requires separate approval and separate
interpretation of earlier observations.

## Participant flow

1. Read and save a response copy of `instrument.md`. Participation is voluntary;
   confirm authorization for the app, agent, and local indexer. Use an actual
   pending change in an existing legacy app. Keep private source and concrete
   task details in the approved local environment; grant no team app access.
2. Follow the worksheet's link to first-session steps 1–5 for setup. Return to
   the worksheet when ready. On a setup block, stop and fill in the outcome,
   checkpoint, and generic reason; later answers are `not attempted`.
3. Run the practice and investigation prompts in the worksheet. Check important
   claims locally against source. Optional agent or human help is fine and is
   recorded. Keep actual paths, symbols, task notes, and output out of the copy
   to be returned. Do not grade independent discovery or limit recall.
4. Fill in **Your response**, review it for private content, and return only
   that copy through the provided feedback channel. Use an assigned or random
   non-identifying participant code and a coded environment label. If no channel
   was supplied, keep the response local until the owner provides one.

## Investigation prompts

Use the worksheet in order. Anchor all prompts to the participant's chosen change:

- Locate the starting definition and incoming callers; explain current behavior.
- Investigate direct and indirect impact, then inspect important dependent code.
- Check a dependency path that matters to the task; retain uncertainty about
  absent paths, unresolved references, and index/search limits.
- Read governing repository documents for authority and bounded Git history
  for co-change. A graph claim cannot substitute for either evidence source.
- Make a local pre-edit inspection checklist, check important claims in source,
  and summarize usefulness, errors, manual work, setup friction, and assistance
  in the response fields.

Missing history or another unavailable task evidence source is a reported gap,
not a fabricated answer. The exercise investigates the task; it does not
implement the change or assert that a proposed edit is safe.

## Response handling and retained fields

The participant-filled worksheet is the primary self-report, not a transcript.
The owner checks and safely reduces its response fields before committing them
in `result.md`; raw app output and the participant's detailed local notes are
never requested. Label source checks as participant-reported local verification,
not independent observation by the team.

Per returned worksheet, retain only:

- Participant code and coded environment/setup label.
- Generic task class; setup outcome and readiness summary.
- Assistance summary, including training or prompt refinement beyond the script.
- Source-verification summary: useful verified findings, wrong or unsupported
  claims, and unresolved gaps, paraphrased without app content.
- Participant feedback on task usefulness and manual investigation still needed.
- Completed, interrupted, or missing activity and a non-identifying reason.

The aggregate adds approved protocol/worksheet revisions, declared recruitment
scope and planned coverage, actual coverage, deviations, evidence-linked
recommendation, second-reader agreement or unresolved disagreement, and the
CAP-0011 owner-decision link or `pending`. These are human research records,
not a shared provider schema. Readiness, source-check, checklist-usefulness, and overall-feedback fields map
to the setup, verification, usefulness, and feedback summaries above. The owner
adds aggregate metadata; participants fill only the worksheet response fields.
No prior-RFC familiarity, native-choice class,
material-limit recall score, or question pass/fail is collected.

## Interpretation

Apply the amended spec's AC-0019–AC-0021, keeping both benefits and problems:

- **`retain role`:** cite relevant, source-verified findings the participant used
  in the actual investigation. Include help/setup costs and remaining limits;
  bound the recommendation to observed tasks and environments.
- **`change role or onboarding`:** cite observed setup barriers, incorrect
  claims, hidden gaps, or missing usable findings that prevented a usable result.
  Name the affected workflow and a proposed correction.
- **`insufficient evidence`:** name absent execution, missing interpretive
  evidence, or unresolved reader disagreement. An attempt that never ran cannot
  support a usefulness judgment. An observed failed setup can support an
  onboarding correction even though no investigation followed. Non-returned worksheets are coverage
  gaps, not evidence of failed setup or low usefulness.

When useful findings and blockers coexist, preserve both and explain the
bounded recommendation. If the reduced record cannot support that explanation,
use insufficient evidence. No numeric selection threshold applies. No outcome
proves unaided selection, arbitrary-provider generalization, or an adoption rate.

## Privacy and independent review

Apply AC-0022's field boundary and manually inspect free text. Do not retain
personal data, credentials, organization or app/repository identity, file paths,
symbol names, protected configuration, private endpoints, customer data,
source/snippets, quotations, screenshots, recordings, transcripts, or raw
tool/error output. Fields alone do not
make private content safe. Reduce it to a generic summary or record a gap.

A second reader checks the evidence-to-recommendation reasoning using only the
minimized records, records agreement or disagreement, and applies AC-0023.
Unresolved disagreement is insufficient evidence. Route the result to
CAP-0011's owner under AC-0024; link a separate decision or retain `pending`.
No result automatically changes the parent verdict.
