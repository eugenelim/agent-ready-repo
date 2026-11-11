# Spec: Spec supervisor

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0162, ADR-0163, ADR-0157, RFC-0115
- **Brief:** brief:everyday-supervisors-delivery
- **Discovery:** none
- **Depends on:** spec:supervisor-manifest-contract
- **Contract:** none — the interface is the six commands of ADR-0162 D1 and the manifest of spec supervisor-manifest-contract
- **Shape:** service
- **Risk triggers:** security-boundary, structural-interface, persistent-representation
<!-- If this spec intentionally has no criteria, remove the section below and add `- **Acceptance Criteria:** none — <one-line reason>` to the metadata header. -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

<!-- **Durable-spec fill.** This template governs work that needs a durable
behavior contract for one delivery slice. Fill Outcome, What Changes, Agent
Rules, Testing Strategy, and Acceptance Criteria to the depth the durable work
requires, and Assumptions only where something is unresolved. The sibling plan carries the implementation and verification strategy.
Eligible direct-light work does not create this artifact. -->

<!-- **Present tense, as-built.** Write every body section below as if the
feature already exists and always worked this way — no "will be", no
"previously X, now Y", no deprecation timelines, no version-stamped history.
The body describes the current contract; decision history lives in ADRs and the
release changelog. `plan.md` holds to the same rule: its `## Changelog` records
approvals, not how the approach evolved. -->

## Outcome

A user in an ordinary interactive session takes a drafted spec and plan through review rounds to both approvals by calling six commands, and a fresh session resumes the work from the repository after a lost context. The supervisor never approves anything, stops at every human gate, and hands the approved pair to `work-supervisor` through a delegated `start`.

## What Changes

- `spec-supervisor.py`, the manifest `supervisor.toml` and `spec-policy.json` — `packs/core/.apm/skills/new-spec/`
- The session instruction text and the spec-plan driver line — `packs/core/.apm/skills/new-spec/` and `packs/core/.apm/skills/work-loop/` (non-pinned files only)
- A how-to for driving it in a session — `guides/core/how-to/`
- Pack tests for each verb and rule — `packs/core/tests/skills/new-spec/`
- A core pack release with its changelog fragment, self-host projections and a `new-spec` eval update — `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `packs/core/.apm/skills/new-spec/evals/`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | A user drives spec review through a supervisor in a session | a how-to under `guides/core/how-to/` | repository owner | the how-to exists, passes the guide lints and names the prerequisites | the how-to matches the shipped commands |
| Interface compatibility | The six commands, the request kinds and the answer record are read by a controller later | the supervisor script, its manifest and `spec-policy.json` | repository owner | the conformance and verb tests green | the manifest validates against `supervisor-manifest.v1` |
| Maintainer procedure | The five session rules and the spec-plan driver line direct a session agent | `new-spec` and `work-loop` instruction text | repository owner | the content-pin test green | both files name the supervisor and the fallback |
| Release history | A core pack file changes | `packs/core/pack.toml`, `plugin.json` and `docs/product/changelog.d/` | repository owner | the changelog validates and the core release check passes | the core version is one patch above `main` at merge |
| Decision rationale | ADR-0162, ADR-0163 and ADR-0157 record the contract, the placement and approval | `docs/adr/` | repository owner | the ADRs Accepted | none further |
| Operations, current architecture | not applicable: the architecture set already describes this supervisor, and no deployment changes | none | none | none | none |

## Agent Rules

### Always do

- Run the pack tests for the supervisor before reporting a task done.
- Keep the supervisor stdlib-only, as `work-supervisor.py` is.
- Cite ADR-0157 D4 wherever the supervisor stops at an approval.

### Ask first

- Adding a request kind, a stage value or a command to the supervisor.
- Changing a default in `spec-policy.json`.

### Never do

- Edit `work-supervisor.py` or any file in its pin set (ADR-0144).
- Give the supervisor a verb, flag or default that approves a gate.
- Add a new top-level dependency or a runtime import of a third-party package.
- Let a worker write the answer record, the ledger or the store: only the supervisor and the human `answer` verb write them.

## Testing Strategy

- **Admission (AC-0001, AC-0002, AC-0003):** TDD, because each refusal is a compressible invariant over a temporary repository.
- **Requests and manifest (AC-0004, AC-0005):** TDD for the request shape, and goal-based for the manifest, which a schema validator and a set comparison decide.
- **Resume and ledger (AC-0006, AC-0007, AC-0008, AC-0009):** TDD over a temporary repository with real commits, killing and restarting the process between steps.
- **Review rounds (AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015):** TDD over recorded reviewer reports, because convergence, weakness and the cap are state transitions.
- **Gates and answers (AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021):** TDD over a temporary repository, driving `answer` through a pseudo-terminal for the terminal rule.
- **Pin and scope (AC-0022, AC-0023):** goal-based, a digest comparison and a diff check against the work-loop pin set.
- **Instruction text and how-to (AC-0024, AC-0025, AC-0026):** goal-based content pins and a guide lint.
- **Live resume trial (AC-0027):** manual QA in three live sessions on different CLIs, recorded in the verification ledger.

## Acceptance Criteria

- [ ] **AC-0001.** `start` on a spec directory that holds `spec.md` and `plan.md` admits the subject and records the admission as one ledger line in one commit.
- [ ] **AC-0002.** `start` refuses, and writes nothing, when the current branch is the repository's default branch or when the working tree has uncommitted changes.
- [ ] **AC-0003.** `start` refuses, and writes nothing, on a directory with no `spec.md` or no `plan.md`.
- [ ] **AC-0004.** Every request `next` returns carries the five keys of `supervisor-request-envelope.v1`, a `kind` from `author-spec`, `review-round`, `adjudicate`, `revise`, `delegate-verb`, `consent` and `human-decision`, and a `stage` from `authoring`, `reviewing`, `revising`, `awaiting-human`, `delegating` and `terminal`.
- [ ] **AC-0005.** The request kinds listed in the supervisor's manifest equal the kinds `next` can return, and the manifest validates against `supervisor-manifest.v1`.
- [ ] **AC-0006.** A fresh process that runs `status` and then `next` on a subject with an open request returns that request's id, and the ledger holds no line lost or repeated.
- [ ] **AC-0007.** `report` refuses a request id other than the open one, and refuses a second report on a request id already reported.
- [ ] **AC-0008.** Each completed step adds exactly one commit that holds one new ledger line and the files the step changed, and no earlier ledger line ever changes.
- [ ] **AC-0009.** `report` refuses when a commit the supervisor did not make has landed since the request was issued.
- [ ] **AC-0010.** A `review-round` request names a reviewer role and the agent definition to exclude, which is the author's, and the supervisor issues no `review-round` to the author's agent definition.
- [ ] **AC-0011.** A round reported with a reviewer whose agent definition equals the author's is recorded `weak`, and `next` after it issues a `human-decision` that names the weakness and offers `continue`, `accept-residue` and `stop`, never a `consent` for `spec-approved`.
- [ ] **AC-0012.** After a round that is not weak and whose adjudicated findings are all refuted or absent, `next` issues the `consent` request for `spec-approved`.
- [ ] **AC-0013.** After a round with a sustained finding, `next` issues `revise` and then a further `review-round`, until a round converges or `max_review_rounds` rounds have run.
- [ ] **AC-0014.** When `max_review_rounds` rounds have run without a converged round, `next` issues a `human-decision` that names the open findings and offers `continue`, `accept-residue` and `stop`; `max_review_rounds` is read from `spec-policy.json` and defaults to 3.
- [ ] **AC-0015.** `continue` allows exactly one further round, `accept-residue` leads to the `spec-approved` consent request, and `stop` ends the run with no further request.
- [ ] **AC-0016.** For each of `spec-approved` and `plan-approved`, `next` issues a `delegate-verb` request whose command is `park` on `work-supervisor` for that gate, and then a `consent` request that only a human answers.
- [ ] **AC-0017.** `answer <gate> --decision <approve|reject|request-changes> --by <name>` refuses without a controlling terminal, refuses when the gate is not pending or the digest is not the parked one, and otherwise records one answer line with the gate, decision, digest, name and time that states the identity is unverified.
- [ ] **AC-0018.** `report` refuses a `consent` result that has no answer record, and no verb, flag or default of the supervisor turns a parked gate into an approval.
- [ ] **AC-0019.** `status` shows each gate's answer and decision, and `next` returns a `parked` refusal while a gate waits.
- [ ] **AC-0020.** After a `request-changes` answer, `next` issues `revise` with the human's note labelled untrusted, and after a `reject` answer `next` issues a `human-decision` that offers `revise` or `abandon`.
- [ ] **AC-0021.** After both gates are approved, `next` issues a `delegate-verb` request whose command is `start` on `work-supervisor` carrying both approved digests, and the subject is `terminal` once `start` answers `admitted`.
- [ ] **AC-0022.** `start` pins the digests of the files the manifest names, and a later `next` refuses with `supervisor-changed` when one differs.
- [ ] **AC-0023.** The E1 change edits no file under `packs/core/.apm/skills/work-loop/scripts/` and none of that skill's policy JSON files.
- [ ] **AC-0024.** `work-loop`'s spec-plan instructions name `spec-supervisor` as the driver when it is installed and `references/pre-execute-review.md` otherwise.
- [ ] **AC-0025.** The shipped instruction text carries the five session rules: read the decision from `status`, never run `answer` or write an answer record or the store, run one command per verb, name the file-write tool generically, and carry a compact table of request kinds with their result-fact shapes.
- [ ] **AC-0026.** A how-to for driving the spec supervisor in a session exists, states that `ferryman` is later and optional, and names the install prerequisites and routing.
- [ ] **AC-0027.** In a live session, across three tries on different CLIs, a fresh session resumes a real `spec-supervisor` run from `status` alone, reaches the same request id and loses no record, and the result is recorded in the verification ledger.

## Follow-ons

- repository owner: `ferryman` driving this supervisor unattended, the scribe, the approval-fields guard, `--known-commits` and `next --width` — phase P0 of brief `ferryman-local-delivery`.
- repository owner: `author-brief` and the `brief-ready` consent — they follow with the intake flow, and this supervisor starts at `author-spec`.
- repository owner: the stronger human-attribution check than `answer --by` — the Brief 1 waiver ends when `ferryman`'s guard and scribe run the supervisors.

## Assumptions

- Defaulted: Process: the cap gate is a `human-decision` request offering `continue`, `accept-residue` and `stop`, since the sources name only `human-decision` as a gate that offers choices (page 05 lines 173 and 211) — default: that kind; if wrong: a new request kind needs a manifest and an ADR-0162 amendment (settled by: repository owner).
- Defaulted: Technical: the five stage values and the answer-record fields are defined here, because the sources give the envelope and the record shape but not the stage names — default: `authoring`, `reviewing`, `revising`, `awaiting-human`, `delegating` and `terminal`; if wrong: they change before the first manifest ships (settled by: repository owner).
- Defaulted: Technical: the ledger sits in the spec's own directory, committed one line per step, and the supervisor refuses on the default branch and on a dirty tree — default: that placement; if wrong: the ledger moves and the resume tests change (settled by: repository owner, who chose commit-per-step).
- Defaulted: Technical: the supervisor's own digest pins are the files its manifest names, as the sources say, and its pinned-file code is a tested equivalent of the work supervisor's because those scripts are not importable by name — default: an equivalent copy with a behavior test; if wrong: a shared module needs a work-loop change this spec forbids (settled by: repository owner).
- Defaulted: Process: the kill-condition trial uses Claude Code, Codex and Copilot, the three CLIs earlier tested against `work-supervisor` — default: those three; if wrong: the trial's CLI set changes (settled by: repository owner).
- Technical: whether `spec-supervisor` and `work-supervisor` can both keep gate records without the work supervisor tolerating the sibling's files — the sources leave the work supervisor's tolerance of foreign gate records unverified, so the supervisor writes only under its own store (settled by: a test against the real work supervisor in the live trial).
