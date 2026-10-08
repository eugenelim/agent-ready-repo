# Plan: Code-intelligence real-world usage validation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `docs/product/intents/CAP-0011-optional-code-intelligence-composition.md`; `guides/code-intelligence/tutorials/first-session.md`; `packs/code-intelligence/`; `docs/product/research/native-provider-selection-validation/`

> **Plan contract:** this is the implementation strategy. The owner-directed
> scope amendment reopens it for review. Earlier approval does not approve this
> revised plan. Substantive changes after renewed approval require amendment;
> observations belong in `notes/verification-ledger.md`.

## Approach

Help maintainers or adopters use the code-intelligence pack on a real pending
change in their own existing legacy app. Prepare the guided protocol and
worksheet, check the linked setup and practice prompts, and approve the method
before inviting participants. Participants complete the worksheet on their own,
using their authorized app and optional help, then return coded responses through
an approved feedback channel. The owner reviews those self-reports for a bounded
usefulness recommendation.

Blind selection is outside this delivery. The old six-question classifier,
three-person threshold, two-provider-shape requirement, and withholding rules
are historical construction evidence. They are not tasks or gates here.
No new intent or backlog work is created for them.

## Constraints

- The amended spec owns guided scope, privacy, coverage reporting, qualitative
  interpretation, and the owner decision boundary.
- Use the existing pack and first-session walkthrough. No provider schema,
  research engine, integration, or Core routing change is built.
- Participation is voluntary. Participants confirm app, tool, and environment
  authorization locally; the owner provides the approved feedback channel.
  Authorized private apps remain local; the team needs no app access or content.
- Training, sample prompts, practice, and help are expected. Record assistance
  without treating it as independent-selection failure.
- Protocol approval must precede observations. Preserve failures, mixed
  evidence, and gaps. A changed method requires separate approval and explicit
  separation from earlier observations.

## Construction and manual checks

**Document checks:** protocol and worksheet cover the task workflow, setup,
training, source verification, assistance, feedback, and minimized fields.
Links, guide metadata, and copyable prompts pass the existing guide checks.
The allowed-field check rejects forbidden fields; a human reviews free text.

**Interpretation checks:** synthetic guided records cover useful verified
findings, setup blocked before investigation, incorrect unsupported claims,
and missing observations. Each recommendation cites its evidence and limits.
There is no numeric pass line or blind classifier gate.

**Manual verification:** an unassisted reader dry-run starts at `instrument.md`,
follows the linked first-session setup, returns for prompts, and fills in a
response copy or reports a blocker without a facilitator. A second reader later
checks that the minimized
records support the recommendation without access to app source or raw output.
Neither check is replaced by an agent-authored receipt.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `protocol.md` | T1 | Guided method, fields, interpretation cases, approved revision | Result names the method revision and deviations |
| `instrument.md` and existing first-session tutorial | T1 | Linked setup, prompts, fill-in fields, unassisted reader dry-run | Returned worksheets retain the instrument revision used |
| `notes/verification-ledger.md` | T1–T3 | Document checks, dry-run, privacy and interpretation receipts | Evidence links to the amended ACs without reusing blind receipts |
| `result.md` | T2, T3 | Coded session summaries or honest gaps, source-check summaries | Independent interpretation and owner-decision link or pending |
| CAP-0011 decision route | T3 | Evidence-linked recommendation | Separate owner decision or explicit pending field |

## Design (LLD)

### Guided workflow

Owned by: T1, T2.

Participants read and copy `instrument.md` as their response worksheet. It
links first-session steps 1–5 for setup, then provides practice/task prompts and
fill-in fields. They return the completed copy through the provided feedback
channel. No facilitator is required. Its task
example is adding an optional request field; participants may choose another
small real change. The workflow covers definition/callers, behavior through
validation/storage where applicable, wider impact, a dependency path, governing
documents, Git co-change, and a pre-edit checklist. Source verification and
feedback make the findings useful for grounding and exploration. These are
investigation steps, not six independently scored questions.

### Observation shape

Owned by: T1, T2, T3.

Retain only participant code, coded environment/setup label, generic task class,
setup outcome, assistance summary, source-verified usefulness, incorrect claims,
unresolved gaps, participant-written generic feedback, progress/stop reason, and coverage. Add method/worksheet revision,
deviations, evidence-linked interpretation, second-reader agreement or unresolved
disagreement, and owner-decision link or `pending` at aggregation.
The worksheet response fields are the primary participant self-report. The
owner validates and, where needed, reduces those fields before retaining them
in `result.md`; only the owner adds aggregate interpretation and reader/decision
metadata. Detailed source checks are performed locally, not observed by the team.
App paths, symbols, app identity, source, and raw outputs remain local. Do not
retain prior-RFC familiarity, expected provider identity, or blind choice scores.

### Interpretation

Owned by: T1, T3.

Use the spec's `retain role`, `change role or onboarding`, and `insufficient
evidence` recommendations. Describe both benefits and blockers when they coexist.
A barrier observed during an authorized setup attempt is onboarding evidence;
a session that never ran is a gap. A completed task with useful verified
findings supplies bounded positive evidence, not universal adoption proof.

## Tasks

### T1: Guided materials prepare people to use the pack on their legacy app

**Depends on:** none

**Touches:** `docs/product/research/native-provider-selection-validation/protocol.md`, `docs/product/research/native-provider-selection-validation/instrument.md`, `guides/code-intelligence/tutorials/first-session.md`, `docs/specs/native-provider-selection-validation/notes/**`

**Verification mode:** goal-based document checks and unassisted reader manual QA.

**Tests:**
- The guided protocol declares recruitment scope, planned coverage, method,
  coded fields, privacy rules, and evidence-based interpretation before sessions
  (AC-0013, AC-0015, AC-0016, AC-0019, AC-0020, AC-0021, AC-0022).
- The worksheet teaches goal, app/task choice, setup, skill activation, practice,
  investigation prompts, source checks, fill-in responses, and return path (AC-0014, AC-0017, AC-0018).
- The existing walkthrough passes guide checks; prompt names and commands match
  the installed pack's documented contract (AC-0014).
- Guided interpretation fixtures cover useful verified findings, observed setup
  barriers, incorrect claims, and absent observations; field checks and manual
  content review protect the record (AC-0019, AC-0020, AC-0021, AC-0022).
- An unassisted reader dry-run follows instrument → linked guide setup →
  prompts → filled response copy, including setup-blocked and not-attempted
  answers and the approved return channel (AC-0014).

**Done when:** the owner approves the guided method revision before observations,
source/guide/interpretation checks pass, and the unassisted reader dry-run receipt is
recorded. Historical blind checks do not satisfy this task.

### T2: Participants return self-serve worksheets from real app tasks

**Depends on:** T1

**Touches:** `docs/product/research/native-provider-selection-validation/result.md`

**Verification mode:** returned-worksheet checks and manual privacy review.

**Tests:**
- Voluntary participation and authorized use are explained in the entry point;
  worksheet progress and planned versus returned/completed coverage are checked
  without retaining identity or app details (AC-0015, AC-0016).
- Participant-filled fields summarize setup, optional help, locally checked
  findings, wrong claims, gaps, and task usefulness; self-report is clearly
  distinguished from observed or independently verified evidence
  (AC-0014, AC-0017, AC-0018, AC-0022).
- Source and outputs stay local. Reduced summaries contain no forbidden content;
  missing or interrupted activity remains an explicit gap (AC-0021, AC-0022).

**Approach:** distribute the existing worksheet and approved return channel;
participants complete it themselves. The owner checks returned fields against
the allowlist, removes unsafe content, and records generic responses in
`result.md`. The agent can check supplied minimized records but cannot invent
participation or claim to have observed local source verification.

**Done when:** the approved planned coverage is honestly accounted for through
completed coded observations and explicit gaps. No absent session receives a
fabricated usefulness judgment.

### T3: Independent interpretation gives the owner a bounded recommendation

**Depends on:** T2

**Touches:** `docs/product/research/native-provider-selection-validation/result.md`, `docs/product/intents/CAP-0011-optional-code-intelligence-composition.md`, `docs/specs/native-provider-selection-validation/notes/**`

**Verification mode:** goal-based evidence checks and independent human review.

**Tests:**
- Each recommendation follows the guided interpretation rules and cites both
  useful evidence and relevant barriers or gaps (AC-0019, AC-0020, AC-0021).
- A second reader reproduces the reasoning from minimized records; unresolved
  disagreement is insufficient evidence (AC-0023).
- Field checks and human free-text review find no forbidden content (AC-0022).
- The result routes the recommendation to CAP-0011's owner and links the separate
  decision or records it as pending (AC-0024).

**Done when:** `result.md` contains an independently checked, bounded
recommendation or an honest insufficient-evidence record; the owner route is
explicit; and the ledger maps evidence to the amended ACs.

## Rollout

Authoring does not authorize distribution, access to participant apps,
installation, or recording. The owner approves the method and feedback channel
before invitations; participants confirm their own app/tool authorization. No infrastructure deployment or migration is included.

## Risks

- Setup friction can consume a session; retain it as observed onboarding evidence.
- Trained answers may overstate usefulness; check important claims against source
  and record manual work still needed.
- Too little retained detail can prevent independent interpretation; use generic
  evidence summaries without app identity or content, or record insufficiency.
- A narrow sample cannot establish broad adoption or cross-provider generalization.

## Changelog

- 2026-10-04: the original blind spec and plan were approved.
- 2026-10-08: owner requested removal of the blind task. Reopened this existing
  plan as Drafting for guided real-world code-intelligence use. No task has a
  completion receipt; no completed task is removed or renamed. No new intent or
  backlog item is created.

- 2026-10-08: owner requested a self-serve worksheet linked to first-session
  setup, followed by participant-filled responses; facilitator-led sessions are
  removed from the task flow.
