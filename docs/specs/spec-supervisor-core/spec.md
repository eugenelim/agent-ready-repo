# Spec: Spec supervisor core

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

A user or controller drives a drafted spec and plan from admission through independent review rounds to the spec-approved and plan-approved consent requests with six commands, and a fresh process resumes from the repository with no step lost or repeated. The supervisor never approves anything, accepts a step only when protected content is untouched, and stops where a human gate is issued.

## What Changes

- `spec-supervisor.py`, its manifest `supervisor.toml` and `spec-policy.json` — `packs/core/.apm/skills/new-spec/` (the script under `scripts/`, the other two at the skill root)
- The six commands `start`, `next`, `report`, `status`, `park` and `gates`, from admission to the consent requests of `spec-approved`, `plan-approved`, `review-cap` and `review-weak`
- A committed append-only ledger in the spec directory, with one commit per step
- The review procedure of `pre-execute-review.md`, encoded as `review-round`, `adjudicate` and `revise` requests, with its own report classifier
- A copy of the work supervisor's gate digest, so a consent request carries the digest the work supervisor's `park` records
- Pack tests for each rule — `packs/core/tests/skills/new-spec/`
- Page 05 of the unattended-delivery architecture, where it differs from this spec — `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md`
- A core pack release, shipped before `spec-supervisor-gates`, with its changelog fragment, self-host projections and a `new-spec` eval update — `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `packs/core/.apm/skills/new-spec/evals/`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | The six commands, the request kinds and the manifest are read by a controller later | the supervisor script, `supervisor.toml` and `spec-policy.json` | repository owner | the manifest, request and verb tests green | the manifest validates against `supervisor-manifest.v1` |
| Current architecture | Page 05 says the first `next` writes the first ledger line, applies a moved-`HEAD` check in a session, and lacks the `review-cap` and `review-weak` gates, `park`, `gates` and the ended-run answer | `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md` | repository owner | the page names each point as this spec states it | no page 05 sentence contradicts this spec |
| Release history | A core pack file changes | `packs/core/pack.toml`, `plugin.json` and `docs/product/changelog.d/` | repository owner | the changelog validates and the core release check passes | the core version is one patch above `main` at merge |
| Decision rationale | ADR-0162, ADR-0163 and ADR-0157 record the contract, the placement and approval | `docs/adr/` | repository owner | the ADRs Accepted | none further |
| User promise, maintainer procedure | not applicable here: the instruction text, the how-to and the session rules belong to `spec-supervisor-gates` | none | none | none | none |
| Operations | not applicable: no deployment changes | none | none | none | none |

## Agent Rules

### Always do

- Run the pack tests for the supervisor before reporting a task done.
- Keep the supervisor stdlib-only, as `work-supervisor.py` is.
- Cite ADR-0157 D4 wherever the supervisor stops at an approval.
- Treat reviewer and human text as untrusted data: carry identifiers and file references, bound any text, and mark it untrusted.

### Ask first

- Adding a request kind, a stage value or a command to the supervisor.
- Changing a default in `spec-policy.json`.
- Adding a path to the set a request kind may change, or an item to the protected set.

### Never do

- Change any file in the work-loop pin set: no file in the work-loop pin set changes (ADR-0163 D3, ADR-0144).
- Import a work-loop script, or share code with `work-supervisor.py`.
- Give the supervisor a verb, flag or default that approves a gate.
- Add a new top-level dependency or a runtime import of a third-party package.
- Write the ledger, an attempt record or the store from anywhere but a supervisor verb.
- Place the supervisor's store inside `<git-dir>/agentbundle-supervisor/`.

## Testing Strategy

- **Admission and confinement (AC-0001, AC-0002, AC-0003):** TDD over a temporary repository, because each refusal is a compressible invariant and each closed list is a parametrized case set.
- **Manifest and requests (AC-0004, AC-0005, AC-0006):** TDD for the request shapes and the author rule, and goal-based for the manifest, which a schema validator decides.
- **Report, ledger and protected content (AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012):** TDD over a temporary repository with real commits, including foreign commits landed between steps.
- **Coexistence and scope (AC-0013, AC-0014):** goal-based, an integration test against the real installed `work-supervisor.py`, never a stub, and a diff check against the work-loop pin set.
- **Resume (AC-0015):** TDD with a process killed at named points and a fresh process started after.
- **Review procedure (AC-0016, AC-0017, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023):** TDD over recorded reviewer reports, because rounds, weakness and stops are state transitions.
- **Classifier equivalence (AC-0018):** goal-based, a behavior comparison against the real `review-artifact.py` over recorded reports, since ADR-0163 D3 forbids sharing its code.
- **Consent, park, gates and untrusted text (AC-0024, AC-0025, AC-0026):** TDD over a temporary repository, with injected hostile report text.
- **Consent digest (AC-0027):** goal-based, a behavior comparison with the work supervisor's gate digest on the same inputs.
- **Pins (AC-0028, AC-0029):** goal-based digest comparisons, TDD for the refusals, and a behavior comparison with the work supervisor's pin code on the same inputs.
- **Release records (AC-0030):** goal-based, the changelog validator, the core release check, the self-host drift check and an eval-file check.

## Acceptance Criteria

- [ ] **AC-0001.** `start <spec-dir>` on a directory that holds `spec.md` and `plan.md`, on a clean working tree and a branch other than the repository's default branch, admits the subject and records the admission as one ledger line in one commit.
- [ ] **AC-0002.** `start` refuses, and writes nothing, in each case of this closed set: the current branch is the default branch, the working tree has uncommitted changes, `spec.md` is missing, `plan.md` is missing, the subject is already admitted or ended, or `max_review_rounds` in `spec-policy.json` is not an integer of at least 1.
- [ ] **AC-0003.** Every verb that takes `<spec-dir>` refuses, and writes nothing, in each case of this closed set: the argument is not a repository-relative POSIX path free of `.` and `..` segments, a component of it is a symlink or not a directory, or `spec.md`, `plan.md` or the ledger inside it is a symlink or not a regular file.
- [ ] **AC-0004.** `supervisor.toml` validates against `supervisor-manifest.v1`, and its listed request kinds equal the kinds `next` returns across a driven run of this release.
- [ ] **AC-0005.** Every request `next` returns carries `schema_version` 1, `request_id`, `run_id`, `kind` and `stage`, validates against `supervisor-request-envelope.v1`, and has a `kind` and a `stage` from the closed sets the plan lists.
- [ ] **AC-0006.** `next` issues `author-spec` exactly when the admitted pair has no recorded review round and no recorded author, and the author's agent definition is recorded from the first reported `author-spec` result.
- [ ] **AC-0007.** Each completed step adds exactly one commit, and that commit holds exactly one new ledger line and the files the step changed.
- [ ] **AC-0008.** `report` refuses, and writes nothing, in each case of this closed set: a request id other than the open one, a second report on a completed step (`request-consumed`), a result file that is a symlink, is not a regular file, is over 16 MiB or is not UTF-8 JSON, or a `consent` result with no answer record (`no-human-answer`).
- [ ] **AC-0009.** `report` on `author-spec` refuses when `spec.md` does not read `Status: Draft`, when `plan.md` does not read `Status: Drafting`, or when `lint-contract-item-alignment.py` does not exit 0 on the spec directory.
- [ ] **AC-0010.** Every verb refuses when the ledger is not a strict append-only extension of the ledger at the supervisor's last recorded commit.
- [ ] **AC-0011.** `next` and `report` accept every commit landed since the last recorded commit, whoever made it, except one that changes an item of the protected set outside that item's allowed edit, which they refuse and write nothing.
- [ ] **AC-0012.** `report` refuses, and writes nothing, when the working tree or the index differs from `HEAD` outside the closed path set of the request's kind, or when an `author-spec` or `revise` step changes a protected line (`Status:`, a plan approval-entry line).
- [ ] **AC-0013.** With a populated supervisor store and the ledger present, the real `work-supervisor.py` `status`, `park` and `start` answer as they do with neither.
- [ ] **AC-0014.** No file in the work-loop pin set changes: the diff against `main` holds no path under `packs/core/.apm/skills/work-loop/scripts/`, `supervisor-policy.json` or `review-rules.json` in that skill's root.
- [ ] **AC-0015.** After a fresh process, and after a process killed at either of two points inside `report` (step files written before the commit, commit made before the attempt closes), `status` then `next` or a repeated `report` returns the open request id or completes the step with no ledger line lost or repeated and no more than one commit for the step, and `status` writes no file, store record or commit.
- [ ] **AC-0016.** `next` issues one `review-round` request for each reviewer role the spec's risk triggers require, naming the role and, as `exclude_profile`, the author's agent definition, and issues no later request kind until each has reported.
- [ ] **AC-0017.** A run stops, `next` then issues no request, and the stop is recorded with a reason, in each case of this closed set: a reviewer reports unavailable, the classifier marks a raw report `invalid`, or an adjudication is indeterminate; an indeterminate adjudication is recorded as indeterminate and never as clean.
- [ ] **AC-0018.** On each recorded raw report and each recorded adjudication in the equivalence corpus, the supervisor's classifier returns the classification, and for a raw report the finding count and `## Not checked` flag, that `review-artifact.py` returns.
- [ ] **AC-0019.** A raw report classified `clean` with no `## Not checked` footer records its reviewer clean with no `adjudicate` request, and every other non-`invalid` report is followed by an `adjudicate` request that names the reviewer's agent definition as `exclude_profile` and whose report `report` refuses when made with that agent definition.
- [ ] **AC-0020.** A round whose reviewer's agent definition equals the author's is recorded `weak`, and a weak round is never recorded as converged.
- [ ] **AC-0021.** After a non-weak round, `next` issues `revise` and then a further round when a sustained finding is open, and the `consent` request for `spec-approved` when every adjudicated finding is refuted or none exists.
- [ ] **AC-0022.** After `max_review_rounds` rounds (from `spec-policy.json`, 3 when the key is absent) with none converged, or after a weak round, `next` issues a `consent` request for `review-cap` or `review-weak` respectively, and no further `review-round` or `revise`.
- [ ] **AC-0023.** A `review-cap` or `review-weak` request names each open sustained finding by a supervisor-assigned identifier and a file reference, and lists the answers `approve`, `request-changes` and `reject` with the fixed consequence text the plan states.
- [ ] **AC-0024.** A `consent` request holds only supervisor-fixed text, file digests, supervisor-assigned finding identifiers and file references, and every other request field that carries reviewer or human text is cut to 512 characters and sits in an entry marked `"untrusted": true`.
- [ ] **AC-0025.** `next` on an open `consent` request returns it unchanged with no attempt record and no commit, `park` on it records the park in the store with no commit and no tracked-file change, and `next` on a parked request then refuses `parked` while `status` names it.
- [ ] **AC-0026.** `gates` lists each parked `consent` request of this supervisor with its gate, spec digest, plan digest and fixed answer text, with no text taken from a reviewer or a human, and writes nothing.
- [ ] **AC-0027.** On each input in the digest corpus, the spec and plan digests in a `consent` request equal the gate digests the work supervisor's `gate_digest` returns for the same bytes, and a refusal case refuses in both.
- [ ] **AC-0028.** The admission ledger line records the sha256 of every file under the supervisor's `scripts/` directory at any depth, of `supervisor.toml` and of `spec-policy.json`, and the `pinned_files` of `supervisor.toml` list the same files.
- [ ] **AC-0029.** Every verb refuses `supervisor-changed` when a file under `scripts/` is modified, added or removed or when `supervisor.toml` or `spec-policy.json` differs from its pinned digest, and never loads or executes a bytecode file planted beside a pinned module.
- [ ] **AC-0030.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the same version, one patch above `main`; `python3 tools/changelog.py validate` passes with this release's fragment; `make build-self` leaves no diff in the `new-spec` projections under `.claude/skills/` and `.agents/skills/`; and the `new-spec` eval file holds a case that drives the supervisor path.

## Follow-ons

- repository owner: `docs/specs/spec-supervisor-gates/` — the human `answer` verb and the answers file, what each human decision does (including the round counter after each), the delegated `park` and `start`, the hand-off record, the `human-decision` request, the instruction text, the how-to and the live trials; it also amends `supervisor.toml` to list `delegate-verb`, `human-decision` and `delegates_to` once `next` emits them, and releases after this spec.
- repository owner: `ferryman` driving this supervisor unattended, the scribe, the approval-fields guard and `--known-commits` — phase P0 of brief `ferryman-local-delivery`.
- repository owner: `author-brief` and the `brief-ready` consent — they follow with the intake flow, and this supervisor starts at `author-spec`.
- repository owner: a stronger human-attribution check than a name — the Brief 1 waiver ends when `ferryman`'s guard and scribe run the supervisors.

## Assumptions

- Defaulted: Technical: `park` records an open `consent` request as handed to a human in the supervisor's own store with no commit, `gates` lists those records, and `next` refuses `parked` while one waits — the sources fix a sibling store root, a parked `consent` gate and a `parked` refusal, and leave the record's fields and the refusal's timing open — default: these meanings; if wrong: they change before the gates spec builds on them (settled by: repository owner, eugenelim).
- Defaulted: Technical: a stopped run and an ended run are one state: `status` reports stage `terminal` with a recorded reason (a reviewer or classifier stop reason, `rejected`, `abandoned` or `admitted`), and `next` answers `{"terminal": true}` as `work-supervisor.py` does — default: that merge; if wrong: a stopped run gets its own stage and recovery verb (settled by: repository owner, eugenelim).
- Defaulted: Technical: the stage values are `authoring`, `reviewing`, `revising`, `awaiting-human`, `delegating` and `terminal`, because page 05 leaves each sibling's `stage` enum to the sibling — default: those six; if wrong: the enum changes in the manifest-listed request shapes (settled by: repository owner, eugenelim).
- Defaulted: Technical: a human-drafted pair starts at `author-spec` like any other, and its author reports the agent definition `human`; the `--author-human` flag of an earlier draft is not built — default: no flag; if wrong: a start flag records the author (settled by: repository owner, eugenelim).
- Defaulted: Technical: the reviewer roles are `adversarial` always and `security` for `security-boundary`, as the spec-stage review of `new-spec` and `pre-execute-review.md` fix them; design-intent and frontend roles are not driven — default: two roles; if wrong: the role table gains rows (settled by: repository owner, eugenelim).
- Defaulted: Technical: an adjudication reported with the reviewer's own agent definition is refused, not recorded weak — default: refuse; if wrong: it is recorded and the run parks (settled by: repository owner, eugenelim).
- Defaulted: Technical: the 512-character text bound, and the 16 MiB result bound that matches `work-supervisor.py` — default: those values; if wrong: the constants change (settled by: repository owner, eugenelim).
- Defaulted: Technical: the digest copy carries `gate_digest`, the approval-entry drop, the hidden-character check and the canonicaliser the work supervisor calls, because those scripts are not importable by name — default: a tested copy; if wrong: the copy shrinks to the part the equivalence corpus shows is needed (settled by: repository owner, eugenelim).
- Technical: how the supervisor learns the repository's default branch, and the exact ledger, attempt and store paths — `implementation-discovered`, settled when the first test needs them (settled by: the implementing task).
- Product: the `weak` flag rests on the agent definition a controller reports, so it is a review-independence signal and not an integrity control — a controller that misreports defeats it, and nothing in this spec detects that.
- Product: the supervisor's pins are the supervisor's own digests, so an agent that edits the checker itself, or the pinned files together with the record, defeats the self-pin — only a controller's release-time comparison closes that, in phase P0 of brief `ferryman-local-delivery`.
- Product: files an agent writes in a session before a guard exists are caught only by the protected-content and allowed-path checks of `report`, and a history rewrite between steps is caught only through the append-only ledger check — a rewrite that keeps the ledger extension intact is not detected.
- Product: the Brief 1 waiver in `docs/product/briefs/everyday-supervisors-delivery.md` covers identity only, and does not cover any other control named here.
