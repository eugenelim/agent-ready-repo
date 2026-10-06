# Plan: Native-provider selection validation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `docs/product/intents/CAP-0011-optional-code-intelligence-composition.md`; `docs/product/intents/FEAT-0032-native-provider-selection-validation.md`; `packs/product-engineering/.apm/skills/plan-validation/SKILL.md`; `docs/rfc/0079-codebase-context-pack.md`; no established validation-results directory, so the confirmed product-research destination is used.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> execution observations belong in `notes/verification-ledger.md`.

## Approach

Use `plan-validation` to scaffold, not run, a blind six-question exercise under
`docs/product/research/native-provider-selection-validation/`. First author and
approve the protocol and human instrument, and prove their disposition logic
against the synthetic result set named by the spec. A human facilitator then
runs the required independent sessions across the live environment and provider-
shape coverage required by the spec and writes only the minimized coded
observations. Finally, a second reader reproduces the scores and the FEAT-0032
owner records one disposition for CAP-0011's owner.

## Constraints

- Spec AC-0002, AC-0005, AC-0006, AC-0007, AC-0008, and AC-0009 are the single
  owner of the question set, counting rules, disposition thresholds, and no-
  schema boundary; AC-0004 owns live-environment and provider-shape coverage.
  RFC-0079 and CAP-0011 govern those criteria.
- `plan-validation` scaffolds and synthesizes; a human recruits and facilitates
  sessions. No interview, survey, transcript, or research-execution engine is
  built.
- Human participation, use of each live environment, and any recording require
  ordinary consent and authorization. The committed artifact retains no raw
  recording, transcript, screenshot, source, or identifying metadata.
- Protocol changes after results are visible require stopping the run and a
  reviewed spec/plan amendment; they cannot repair the current result.
- An inconclusive result triggers repair and rerun, not threshold relaxation.

## Construction tests

**Integration tests:** a document-level classifier applies the frozen rules to
four synthetic cases—survive, unexplained-fallback failure, coached-selection
failure, and missing-shape inconclusive—and obtains exactly one disposition for
each. A privacy fixture containing every forbidden field is rejected from the
committed result shape.

**Manual verification:** a human dry-run confirms the instrument has no answer
key or RFC/golden-example vocabulary. A second reader independently rescoring
the minimized session records or the inconclusive execution record must
reproduce every recorded question score and the final disposition.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `protocol.md` | T1 | Synthetic disposition table and approved revision | `result.md` names the same revision |
| `instrument.md` | T1 | Blindness and privacy audit plus human dry-run | Every completed session used the frozen instrument |
| `result.md` | T2, T3 | Three coded records or an explicit execution gap, coverage table, scoring table, second-reader check | CAP-0011 decision link or explicit pending status |
| CAP-0011 decision route | T3 | Owner notification and linked result | Owner decision linked or pending without silent mutation |

## Design (LLD)

### Design decisions

The protocol, instrument, and result are separate sections in one product-
research directory so the predeclared method is reviewable without exposing raw
session material. Git revision plus the approved spec/plan baseline freezes the
method. The result records the protocol revision and no editable copy of the
thresholds. Traces to AC-0001, AC-0002, AC-0007, AC-0008, AC-0009, AC-0010,
AC-0011, and AC-0012. Owned by T1 and T3.

### Data & schema

This delivery defines a human-readable record shape, not a provider schema.
Each completed session row contains: participant code (`P1`-`P3`), a
prior-RFC-familiarity boolean, environment-shape labels, question identifier
(`Q1`-`Q6`), choice class (`native-action`, `explained-rejection`, or
`repository-baseline`), a short rationale, one material limit where AC-0005
requires it, pass/fail with the cited protocol rule, and facilitator safety
stop if applicable. An inconclusive execution row names the missing
participant, shape, metadata, or safety condition instead of inventing scores.
The aggregate adds coded live-environment count and provider-shape coverage,
per-participant totals where present,
threshold comparison, disposition, second-reader agreement, and CAP-owner
decision link or `pending`. Traces to AC-0003, AC-0004, AC-0005, AC-0006,
AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, and AC-0012. Owned by T1-T3.

### Interfaces & contracts

Participants interact only with authorized live host/provider surfaces and the
human instrument. No repository tool receives a normalized request and no raw
provider output enters the durable record. The result hands a link and one of
three dispositions to CAP-0011's human owner; it does not edit the intent's
verdict automatically. Traces to AC-0004, AC-0005, AC-0006, AC-0010, AC-0011,
and AC-0012. Owned by T2-T3.

## Tasks

### T1: The blind protocol and instrument are fixed before observation

**Depends on:** none

**Touches:** `docs/product/research/native-provider-selection-validation/protocol.md`, `docs/product/research/native-provider-selection-validation/instrument.md`, `docs/specs/native-provider-selection-validation/notes/**`

**Verification mode:** Goal-based document checks plus manual QA; synthetic
classifier output, the human dry-run receipt, and the approved protocol revision
are recorded in `notes/verification-ledger.md`.

**Tests:**
- The protocol contains the six CAP-0011 questions and the exact AC-0005,
  AC-0006, AC-0007, AC-0008, and AC-0009 scoring and disposition rules
  (AC-0001, AC-0002, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009).
- Four synthetic result sets each map to exactly one expected disposition
  without threshold changes (AC-0007, AC-0008, AC-0009).
- A forbidden-field fixture proves the result form excludes every class named
  by AC-0010.
- A human dry-run finds no answer key, RFC-0079 language, golden-example cues,
  expected provider identity, or expected evidence-limit wording (AC-0003, AC-0005).

**Done when:** the protocol and instrument have an approved revision recorded
before any participant session and the dry-run and synthetic checks are green.

### T2: Human-run sessions produce minimized independent observations

**Depends on:** T1

**Touches:** `docs/product/research/native-provider-selection-validation/result.md`

**Verification mode:** Manual QA at the human-session boundary; the minimized
session records or honest execution-gap record in `result.md` are the evidence
artifact.

**Tests:**
- Preflight records consent and authorized access status for participant, live-
  environment count, and provider-shape coverage without recording environment
  identity, credentials, endpoints, or repository details (AC-0003, AC-0004,
  AC-0010).
- Each coded participant record covers Q1-Q6 independently and contains only the
  approved fields (AC-0003, AC-0005, AC-0006, AC-0010).
- Any missing participant, second live environment, provider shape, metadata,
  or safety-interrupted session takes the inconclusive path and cannot be
  scored as participant failure (AC-0009).

**Approach:** A human facilitator runs the frozen instrument and reduces notes
to the approved coded fields before anything is committed. The agent may check
shape and score supplied records but does not recruit, facilitate, or observe
the live sessions.

**Done when:** `result.md` contains the complete minimized records and live-
environment and provider-shape coverage required by AC-0003 and AC-0004, or an
honest inconclusive record naming the missing execution condition under
AC-0009.

### T3: Independent rescoring produces one owner-routed disposition

**Depends on:** T2

**Touches:** `docs/product/research/native-provider-selection-validation/result.md`, `docs/product/intents/CAP-0011-optional-code-intelligence-composition.md`, `workspace.toml`, `docs/specs/native-provider-selection-validation/notes/**`

**Verification mode:** Goal-based scoring checks plus manual second-reader QA;
the reproducible scoring table, reader receipt, and owner-routing field in
`result.md` are the evidence boundary.

**Tests:**
- The aggregate applies AC-0007, AC-0008, and AC-0009 without changing
  thresholds and names exactly one disposition (AC-0007, AC-0008, AC-0009).
- A second reader reproduces all recorded question scores, participant totals
  or execution gaps, live-environment and provider-shape coverage, and the final disposition from
  committed data (AC-0011).
- Privacy and secret scans plus human review find none of the forbidden content
  in AC-0010.
- The result links a CAP-0011 owner decision or explicitly records `pending`
  without changing the parent verdict (AC-0012).

**Done when:** the minimized artifact is reproducibly scored, CAP-0011's owner
has the disposition, and the verification ledger maps AC-0001, AC-0002,
AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010,
AC-0011, and AC-0012 to evidence.

## Rollout

Approval of T1 authorizes only the frozen research materials, not participant
recruitment or access to a live environment. T2 begins only after separate
human consent and environment authorization. There is no infrastructure,
runtime deployment, provider installation, or data migration. An inconclusive
run remains a durable result and can be followed by a separately approved rerun.

## Risks

- Ordinary tool descriptions may contain vocabulary similar to the withheld
  example; the protocol records exactly what metadata was exposed by shape,
  without storing raw output, so the owner can judge contamination.
- Participants may know RFC-0079 already; recruitment records prior familiarity
  as a coded yes/no covariate and does not coach or exclude post hoc.
- Minimization can make rescoring impossible; the approved rationale and cited
  rule fields retain only what the second reader needs.
- Two environments may differ in repository language or indexing quality; the
  result reports shape coverage and environment failures rather than treating
  them as participant mistakes.

## Changelog

- 2026-10-04: spec approved by eugenelim as part of the CAP-0011 feature cohort.
- 2026-10-04: plan approved by eugenelim as part of the CAP-0011 feature cohort.
