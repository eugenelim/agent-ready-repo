# Spec: Spec supervisor gates and hand-off

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0162, ADR-0163, ADR-0157, RFC-0115
- **Brief:** brief:everyday-supervisors-delivery
- **Discovery:** none
- **Depends on:** spec:spec-supervisor-core
- **Contract:** none — the interface is the six commands of ADR-0162 D1 plus the human-run `answer` verb, and the manifest of spec supervisor-manifest-contract
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

## Outcome

A human approver answers each parked gate of the spec supervisor through a human-run `answer` verb that binds the answer to the digest of the files the human was shown, and the supervisor advances a gate only on a matching answer record. After both approvals the supervisor hands the approved pair to `work-supervisor` through delegated `park` and `start` commands and ends the subject only when it has itself confirmed that `work-supervisor` admitted exactly those digests.

## What Changes

- The `answer` verb, answer records, the `report` consent rules and the human-decision mapping, added to `spec-supervisor.py` (owned by `spec:spec-supervisor-core`) — `packs/core/.apm/skills/new-spec/scripts/`
- The hand-off record, a human-written file that supplies the values of the real `park` and `start` — `<spec-dir>/handoff.json`
- The delegated `park` and `start` requests with their argument sources, the digest re-check and the terminal confirmation — `packs/core/.apm/skills/new-spec/scripts/`
- The manifest, extended with `delegate-verb`, `human-decision` and `delegates_to` — `packs/core/.apm/skills/new-spec/supervisor.toml`
- The session instruction text and the compact request-kind table — `packs/core/.apm/skills/new-spec/SKILL.md`
- The spec-plan driver line — `packs/core/.apm/skills/work-loop/SKILL.md`, a file outside the work supervisor's pin set
- A how-to for driving the spec supervisor in a session, with a repository-level check — `guides/core/how-to/` and a suite under `tools/`
- Pack tests for the verb, the rules and the real `park` and `start` — `packs/core/tests/skills/new-spec/`
- A core pack release after the core release of `spec:spec-supervisor-core`, with changelog fragment, self-host projections and a `new-spec` eval update — `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `packs/core/.apm/skills/new-spec/evals/`
- Scope runs from `author-spec` through `plan-approved` and the hand-off, and stops short of `author-brief` and `brief-ready`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | A user drives spec approval through a supervisor in a session | a how-to under `guides/core/how-to/` | repository owner | the how-to exists, passes the guide lints and is checked by a repository-level test | the how-to matches the shipped commands |
| Interface compatibility | The `answer` verb, the answer record, the hand-off record and the refusal codes are read by a controller later | the supervisor script, the manifest and the shipped instruction text | repository owner | the verb, gate and end-to-end tests green | the instruction text defines `no-tty`, `no-human-answer`, `stale-digest` and `supervisor-changed` |
| Maintainer procedure | The session rules and the spec-plan driver line direct a session agent | `new-spec` and `work-loop` instruction text | repository owner | the content-pin tests green | both files name the supervisor, and `work-loop` names the fallback |
| Release history | A core pack file changes | `packs/core/pack.toml`, `plugin.json` and `docs/product/changelog.d/` | repository owner | the changelog validates and the core release check passes | the core version is one patch above `main` at merge |
| Verification record | The live trials are manual evidence | `docs/specs/spec-supervisor-gates/notes/verification-ledger.md` | repository owner | one ledger entry per trial | both trial entries exist |
| Current architecture | Page 05 of the unattended-delivery-runner set describes the gates | `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md` | repository owner | the page reads the same as this spec where they overlap | no contradiction remains |
| Decision rationale | ADR-0162, ADR-0163 and ADR-0157 record the contract, the placement and approval | `docs/adr/` | repository owner | the ADRs Accepted | none further |

## Agent Rules

### Always do

- Run the pack tests for the supervisor before reporting a task done.
- Run the answer verb tests through a pseudo-terminal, never by stubbing the terminal check.
- Keep the supervisor stdlib-only, as `work-supervisor.py` is.
- Cite ADR-0157 D4 in the plan wherever the supervisor stops at an approval, and keep every citation out of anything shipped under `packs/`.

### Ask first

- Adding a request kind, a command or an answer-record field.
- Changing where the hand-off record or the answers file lives.
- Changing the options a `human-decision` request offers.

### Never do

- Edit `work-supervisor.py` or any file in its pin set.
- Give the supervisor a verb, flag or default that writes `Status: Approved` or a Changelog approval line.
- Supply code trust, an authority ref or an intent from a supervisor default or from an agent's report.
- Add a new top-level dependency or a runtime import of a third-party package.
- Let a worker or the session agent write an answer record, the hand-off record, the ledger, an attempt record or the store: only the supervisor, the human-run `answer` verb and the human write them.

## Testing Strategy

- **Answer verb (AC-0001, AC-0002, AC-0003, AC-0004):** TDD over a temporary repository with a parked gate made by the real `work-supervisor park`, driving `answer` through a pseudo-terminal, because each refusal is a compressible invariant on bytes and a terminal.
- **Report consent rules, status and decisions (AC-0005, AC-0006, AC-0007, AC-0008, AC-0009):** TDD over a temporary repository with real commits and recorded answers, killing and restarting the process at a waiting gate, because each decision is a state transition.
- **Manifest (AC-0010):** goal-based, the schema validator and a driven run.
- **Hand-off and delegated park (AC-0011, AC-0013, AC-0014, AC-0015):** TDD against the real installed `work-supervisor park`, because the argument and status refusals live in that script.
- **Delegated start and terminal confirmation (AC-0012, AC-0016):** TDD against the real installed `work-supervisor start`, because admission is that script's decision.
- **Instruction text and driver line (AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022):** goal-based content pins in pack tests and a `git diff` check against the work supervisor's pin set.
- **How-to (AC-0023, AC-0024):** goal-based, a repository-level suite and the guide lints, because guides sit outside every pack.
- **Release records (AC-0025):** goal-based, the changelog validator, the core release check, the self-host drift check and an eval-file check.
- **Whole flow (AC-0026):** an end-to-end pack test over a temporary repository that runs the real `park` and `start`.
- **Live trials (AC-0027, AC-0028):** manual QA in live sessions, recorded in the verification ledger.

## Acceptance Criteria

- [ ] **AC-0001.** `answer <gate>` records nothing, writes no file and makes no commit, and refuses with the named code, in each case of this closed set: no controlling terminal (`no-tty`), the gate is not parked or not listed `pending` (`gate-not-pending`), the gate digest of the working-tree files, of the files at the parked commit and the parked digest are not all equal (`stale-digest`), the digest the human types differs from the digest shown (`digest-not-confirmed`), or the decision or option is not offered (`option-not-offered`).
- [ ] **AC-0002.** The digest on a recorded answer line equals the gate digest the supervisor computes from `spec.md` and `plan.md`, which equals the digest in the `pending` entry of the listing the gate's owner gives (the work supervisor's read-only `gates` for `spec-approved` and `plan-approved`, this supervisor's `gates` for `review-cap` and `review-weak`), and no digest in a worker report or an `answer` argument is read.
- [ ] **AC-0003.** The prompt `answer` shows the human is supervisor-owned text that names the gate, the digest, the commit and the files to read, and carries no text taken from a report, a request or an artifact.
- [ ] **AC-0004.** A recorded answer is one line carrying the gate, the decision or option, the digest, `by`, the time and a field that states the identity is unverified, in the answers file in the spec directory, in one commit that changes no other file, and `next` and `report` accept that commit.
- [ ] **AC-0005.** `report` advances a `consent` request only when the answers file holds a line for that gate whose digest is the current park's and whose time is after that park, and refuses `no-human-answer` otherwise, whatever decision the result states.
- [ ] **AC-0006.** `report` on a `human-decision` request refuses `no-human-answer` unless the answers file holds a line for that request naming an option the request offered, and accepts `revise` and `abandon` only on such a line.
- [ ] **AC-0007.** `status` shows, for each gate, its answer and its decision.
- [ ] **AC-0008.** After an answer to `review-cap` or `review-weak`, `next` issues the `consent` request for `spec-approved` on `approve`, issues one `review-round` request on `request-changes` and no second one until a further answer is recorded, and ends the run at stage `terminal` with no further request on `reject`.
- [ ] **AC-0009.** After an answer to `spec-approved` or `plan-approved`, `next` follows the closed table the plan states: `approve` leads to the next gate or the delegated `start`, `request-changes` leads to a `revise` request that carries the human's note labelled untrusted, `reject` leads to a `human-decision` request that offers `revise` and `abandon`, and an `abandon` option ends the run at stage `terminal` with the reason `abandoned`.
- [ ] **AC-0010.** `supervisor.toml` validates against `supervisor-manifest.v1`, lists exactly the kinds `next` returns across a driven run of this release (the five kinds of `spec:spec-supervisor-core`, `delegate-verb` and `human-decision`), and lists `delegates_to` entries for `work-supervisor` `park` and `start` only.
- [ ] **AC-0011.** For each of `spec-approved` and `plan-approved`, `next` issues a `delegate-verb` request before its `consent` request, whose command is `work-supervisor park <spec-dir> --gate <gate> --intent <intent> --code-trust <trust>`, with `<intent>` and `<trust>` equal to the values in the hand-off record at `HEAD`.
- [ ] **AC-0012.** The `work-supervisor start` command carries `--approved-spec-digest` equal to the spec digest in the `spec-approved` answer, `--approved-plan-digest` equal to the plan digest in the `plan-approved` answer, and `--intent`, `--code-trust`, `--authority-ref` and `--review-authority-ref` equal to the hand-off record's values, and `next` refuses `stale-digest` and issues no `start` request when a recorded answer digest differs from the current gate digest.
- [ ] **AC-0013.** `next` refuses `hand-off-input-missing` and issues no `delegate-verb` request when the hand-off record at `HEAD` is absent, is not valid JSON, lacks one of its four keys or holds a value outside the argument form `work-supervisor` takes, and no value comes from a default or from an agent's report.
- [ ] **AC-0014.** No commit a supervisor verb makes changes a `Status:` line or a plan approval-entry line, and `next` and `report` accept the commit a human makes to write `Status: Approved` and the plan Changelog line.
- [ ] **AC-0015.** When `work-supervisor park` or `work-supervisor start` refuses, `report` records the refusal code and `next` issues a `human-decision` request that names the code and offers `revise` and `abandon`.
- [ ] **AC-0016.** The subject becomes `terminal` with the reason `admitted` only when the supervisor's own read-only check of `work-supervisor` shows admission of exactly the approved digests, and `report` refuses a `start` result that says it was admitted when that check shows no such admission.
- [ ] **AC-0017.** The shipped instruction text states that the agent never runs `answer` and never writes an answer record, the hand-off record, the ledger, an attempt record, the policy file, a pinned file, `Status: Approved` or a Changelog approval line.
- [ ] **AC-0018.** The shipped instruction text states that the agent reads the decision from `status`, runs one command per verb, and names the file-write tool as 'Write, apply_patch or equivalent', and it defines `no-tty`, `no-human-answer`, `stale-digest` and `supervisor-changed`, each with the action it calls for.
- [ ] **AC-0019.** The compact table of request kinds in the shipped instruction text lists exactly the kinds in the supervisor's manifest, each with its result-fact shape.
- [ ] **AC-0020.** No file this spec adds or changes under `packs/` matches an internal-record citation (`ADR-`, `RFC-`, or a path under `docs/adr`, `docs/rfc`, `docs/specs` or `docs/architecture`).
- [ ] **AC-0021.** `work-loop`'s spec-plan instructions name `spec-supervisor` as the driver when it is installed and `references/pre-execute-review.md` otherwise.
- [ ] **AC-0022.** The change set modifies no file under `packs/core/.apm/skills/work-loop/scripts/` and neither `supervisor-policy.json` nor `review-rules.json` of that skill.
- [ ] **AC-0023.** The how-to states that `ferryman` is later and optional, names the install prerequisites for driving the spec supervisor in a session, and names the routing: a user keeps invoking `new-spec` or `work-loop`, and `work-loop` drives the supervisor when it is installed.
- [ ] **AC-0024.** The guide lints `lint-guide-titles.py`, `check-guide-index.py` and `lint-guides-no-repo-only-refs.py` pass with the how-to present.
- [ ] **AC-0025.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the same version, one patch above the version on `main`; `python3 tools/changelog.py validate` passes with this release's fragment; `make build-self` leaves no diff in the `new-spec` and `work-loop` projections under `.claude/skills/` and `.agents/skills/`; and the `new-spec` eval file holds a case that drives the supervisor path.
- [ ] **AC-0026.** An end-to-end pack test runs the real installed `work-supervisor park` for both gates and `work-supervisor start`, with human-written approval commits between them, and ends with the subject `terminal`.
- [ ] **AC-0027.** In live sessions, across three tries on different CLIs, a fresh session resumes a real `spec-supervisor` run from `status` alone and reaches the same request id with no lost record, and the verification ledger records each try.
- [ ] **AC-0028.** One real spec goes from Draft to plan-approved through the real `work-supervisor park` in a live session, and the verification ledger records it.

## Follow-ons

- repository owner: `ferryman` driving this supervisor with the scribe and the approval-fields guard — phase P0 of brief `ferryman-local-delivery`.
- repository owner: `author-brief` and the `brief-ready` consent — they follow with the intake flow, and this spec stops at `plan-approved` and the hand-off.
- repository owner: a stronger human-attribution check than `answer --by` — the Brief 1 owner waiver ends when `ferryman`'s guard and scribe run the supervisors.
- repository owner: under `ferryman`, the hand-off values move to its trusted configuration set, and the `handoff.json` file stays the session-level source.

## Assumptions

- Accepted risk: the terminal check does not separate a human from an agent, because an agent can spawn a pseudo-terminal, and an agent can write a well-formed answer record or hand-off record. The shipped instruction text is the only mitigation until `ferryman`'s guard and scribe exist. The Brief 1 owner waiver in the brief covers an unchecked identity only (the `by` name is not verified). It does not cover an agent that forges a record or answers through a pseudo-terminal; the committed answers file shows a forged record in history and nothing prevents it (settled by: repository owner, accepted for Brief 1).
- Accepted risk: a history rewrite between steps is not detected by this supervisor, because it compares digests and commits but keeps no signed anchor (settled by: repository owner, accepted for Brief 1).
- Accepted risk: the `review-weak` flag rests on the agent definition the session agent reports about its own reviewer, so a wrong report hides a weak round (settled by: repository owner, accepted for Brief 1).
- Defaulted: Technical: the hand-off record is `handoff.json` in the spec directory with the keys `intent`, `code_trust`, `authority_ref` and `review_authority_ref`, written and committed by a human and never by a supervisor verb, a default or an agent — the sources say only that an authority reference comes from the human and never from a worker's output, and are silent on `--intent` and `--code-trust`; `next` reads the committed bytes at `HEAD` each time it issues a delegate request, and a change to it is accepted only in a commit that changes no other file while no `delegate-verb` request is open — default: that file; if wrong: the path and the instruction text change, or the values move to a trusted-configuration file (settled by: repository owner, eugenelim).
- Defaulted: Technical: the answers file is `answers.jsonl` in the spec directory and `answer` commits it itself, and a change to it is protected content except an appended well-formed line in a commit that changes only that file — default: that file and one commit per answer; if wrong: the path and the commit rule change, and AC-0004 follows (settled by: repository owner, eugenelim).
- Defaulted: Technical: an `answer` line holds the spec gate digest and the plan gate digest the park recorded, and the `spec-approved` answer supplies the spec digest to `start` while the `plan-approved` answer supplies the plan digest, as the work supervisor's reference says each approver's own answer supplies its digest — default: both values on each line; if wrong: AC-0012 reads one value per answer (settled by: repository owner, eugenelim).
- Defaulted: Technical: the refusal codes `gate-not-pending`, `digest-not-confirmed`, `option-not-offered` and `hand-off-input-missing` are this spec's own names, while `no-tty`, `no-human-answer`, `stale-digest`, `parked` and `supervisor-changed` come from the sources — default: these names; if wrong: the criteria, the instruction text and the tests rename them (settled by: repository owner, eugenelim).
- Defaulted: Technical: an optional `--note <text>` on `answer` carries the human's note for `request-changes` and is recorded on the answer line, because the sources name the note and not how it arrives — default: `--note`; if wrong: AC-0009's source for the note changes (settled by: repository owner, eugenelim).
- Defaulted: Technical: a refused `park` or `start` leads to a `human-decision` offering `revise` and `abandon`, the two options the sources give for a rejected gate — default: those two; if wrong: the option set and AC-0015 change (settled by: repository owner, eugenelim).
- Defaulted: Technical: the `human-decision` option `abandon` ends the run at stage `terminal` with the reason `abandoned`, and the option `revise` leads to a `revise` request — default: those effects; if wrong: AC-0009 changes (settled by: repository owner, eugenelim).
- Defaulted: Technical: the supervisor confirms admission by reading the record `work-supervisor start` commits, because no field of its read-only `status` or `gates` output carries an admitted digest pair — default: the record read the plan describes; if wrong: the work supervisor gains a read-only field in a separate change, which this repository's pin rules make a release event (settled by: repository owner, eugenelim).
