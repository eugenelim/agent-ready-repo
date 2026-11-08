# Spec: run grant

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0113, ADR-0159, ADR-0157, ADR-0150, RFC-0099
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none — the grant file and the runner's output are skill data documented in the work-loop brief-runner reference; no `contracts/` schema changes
- **Shape:** service
- **Risk triggers:** security-boundary, structural-interface

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

A maintainer who readies a delivery brief can set its unattended run's limits once, at the same stop as Ready and the slice cut: when the grant expires, when the run counts as done, which slices may run, how many retries a failed task gets, and which extra actions they keep. The brief-level runner then does only what a run with no grant would do, stops at the first spent limit, refuses a grant that is missing, stale or malformed, and starts no work from any brief before its Ready confirmation.

## What Changes

- The brief-level runner reads an optional run grant at the base, binds it to the brief and standing orders, and answers `next`, `status` and `classify` within its limits — `packs/core/.apm/skills/work-loop/scripts/brief-runner.py`.
- The runner names no `start-slice` from a brief that is not `Ready` or `Executing`, with a resume-only exemption for slices already in flight — same file.
- A new read-only runner verb, `guard`, fails a change that mixes a grant change with other work, and a build-check step runs it from the base revision — `brief-runner.py`, `.github/workflows/build-check.yml`.
- Grant files at `docs/product/run-grants/<brief-slug>.toml`, and a `- **Run grant:**` record line in the brief preamble.
- The controller's grant duties — `packs/core/.apm/skills/work-loop/references/brief-runner.md`, with a pointer from work-loop `SKILL.md`.
- A grant path at the Ready stop, beside today's separate stops — `packs/core/.apm/skills/author-delivery-brief/SKILL.md` continue mode.
- Eval cases for both skills, the run-grant trust model in `docs/architecture/security.md`, and a link from RFC-0113 to this spec.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Accepted RFC; D8 says no new ADR | `docs/rfc/0113-run-grant-at-brief-ready.md` | eugenelim | RFC links this spec | AC-0027 holds |
| Maintainer procedure | Controllers and brief authors follow the skills | work-loop `references/brief-runner.md` and `SKILL.md`; author-delivery-brief `SKILL.md` | core pack maintainers | Content tests green | AC-0020, AC-0021, AC-0022 hold |
| Current architecture | A new trust boundary | `docs/architecture/security.md` | core pack maintainers | Run-grant entry names the trust model and the three disclosed limits | AC-0024 holds |
| Release history | Core content changes | `docs/product/changelog.d/<uuid>.md`; `packs/core/pack.toml`; `packs/core/.claude-plugin/plugin.json` | core pack maintainers | Release check green | AC-0025 holds |
| Reusable learning | none — the RFC and this spec hold the rationale | — | — | — | — |

## Agent Rules

### Always do

- Read the grant, the brief and the standing orders only from the base commit, through the runner's existing confined blob read, and judge every grant value before any value is used.
- Fail closed: any grant evidence the runner cannot fully judge makes the grant `refused`, never absent and never clamped.
- Emit grant values only as the typed fields AC-0010 names; never emit grant file text, a TOML error message, or `confirmed_by`.
- Keep every grant check in `brief-runner.py` and `references/brief-runner.md`, before the runner names a slice.

### Ask first

- Any grant key, value, refusal reason or `next` action kind beyond those this spec names.
- Any change to the fixed human-only list (AC-0011) other than adding an entry.
- Any grant enforcement that would need supervisor support; that waits for verified-infrastructure-parallelism (Slice 7) to land.

### Never do

- Never let a grant approve, park, merge, push, relax a review, gate or security control, or remove an entry from the human-only list.
- Never widen a limit past what the same brief would get with no grant, and never clamp an out-of-range value into range.
- Never edit `_supervisor_records.py`, `_supervisor_git.py`, `_supervisor_commit.py`, `_supervisor_integration.py`, `_supervisor_projector.py`, `_supervisor_product_ref.py`, `_supervisor_launcher.py`, `_supervisor_ingestion.py`, `work-supervisor.py` or any `_supervisor_concurrency_*.py` module, and never add a counter inside supervisor attempts.
- Never write a file, commit, ref, branch or worktree from the runner, the `guard` verb included.
- Never treat spend as bounded: no spend field exists, and the human is told spend is unbounded.

## Testing Strategy

- **Grant format and validation (AC-0003, AC-0004, AC-0005, AC-0011): TDD, unit**, one failing case per rule, including a forged grant that tries to raise each limit and one that tries to shorten the human-only list.
- **Binding, grant states, Ready-only and exemption (AC-0001, AC-0002, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016): TDD, integration** over fixture repositories with real Git, a bare `origin` and linked worktrees, extending the brief-runner harness, because each rule is a function of committed history.
- **Retry budget through `classify` (AC-0017): TDD, integration** with the real supervisor `status --json`.
- **Guard (AC-0018, AC-0028, AC-0019): TDD, integration** over fixture commit pairs, including a two-change route that drops a brief out of Ready and back, plus a goal-based posture check that the build-check step runs the base revision's script.
- **Guidance, evals and the trust-model entry (AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0027): goal-based**, content tests over the owning files and the eval harness schema checks.
- **Release and self-host (AC-0025, AC-0026): goal-based**, the release and catalogue checks.

## Acceptance Criteria

### No work before Ready

- [ ] **AC-0001.** For a brief whose `Status:` at the base is anything other than `Ready` or `Executing`, `next` never answers `start-slice`; every row without a slice worktree is `ready` false and, when `next` answers `blocked`, carries reason `brief-not-ready`, which takes the place of `earlier-row-not-stopped` and `not-dispatchable` for such rows.
- [ ] **AC-0002.** On such a brief with no grant evidence (AC-0006), and only while the runner host's current UTC time is before the fixed end time `2026-11-30T00:00:00Z` written in the runner's code, `next` may answer `resume-slice` for a row that meets every resume condition of the no-grant rule (worktree present, stop `none`, a resumable stage, no gate entry) and whose slice branch head holds `docs/specs/<slug>/spec.md`, so a `drafting` row with no spec is never exempt; that answer carries `exemption: "pre-ready-in-flight"`, and no other action carries `exemption`. At or after the end time no row of such a brief is resumed.

### Grant format

- [ ] **AC-0003.** A grant is `docs/product/run-grants/<brief-slug>.toml` at the base: a regular UTF-8 blob of at most 4096 bytes with no character the standing-orders hidden-text rule refuses, parsed by `tomllib`, holding exactly the keys `schema_version` (integer 1), `brief` (the brief slug), `confirmed_by` (1 to 39 ASCII letters, digits and single inner hyphens), `confirmed_at` and `expires_at` (TOML offset date-times at UTC offset zero with whole seconds), `done_when` (`all-granted-merged` or `all-granted-stopped`), `slices` (a non-empty array of distinct slugs, each a Spec map row of the brief at the base), `retry_budget` (an integer from 0 to `lease.retry_budget`), `max_slices_in_flight` (the integer 1) and `held_actions` (an array of distinct values from `push` and `open-pull-request`, possibly empty). A boolean never counts as an integer.
- [ ] **AC-0004.** A grant is malformed when any AC-0003 rule fails, when it holds any other key or any table (so a `spend_cap`, `human_only` or `max_retries` key is malformed), when `expires_at` is not after `confirmed_at` or is more than 14 days after it, or when `confirmed_at` is more than 5 minutes after the runner host's current UTC time. A malformed value is never clamped or ignored.
- [ ] **AC-0005.** The grant-path record is one preamble line, outside any HTML comment, of the form `- **Run grant:** required (confirmed <confirmed_at>)`, where `<confirmed_at>` is written `YYYY-MM-DDTHH:MM:SSZ`. Any occurrence of `**Run grant:**` anywhere in the brief, comments and body included, is record evidence. The record is malformed when the brief holds more than one occurrence, when the one occurrence is not that preamble line, or when its timestamp differs from the grant's `confirmed_at`.

### Grant states

- [ ] **AC-0006.** Grant evidence is any record evidence (AC-0005), any tree entry at the grant path at the base of whatever type or size, or both. With neither, the run is a no-grant run and `grant` is `null`. Otherwise the grant's state is decided once per call, in this order, by the first rule that applies: `spent` with reason `brief-closed` when the brief is `Shipped`, `Withdrawn` or `Cancelled`; `refused` with `brief-not-ready` when the brief is not `Ready` or `Executing`; `refused` with `missing` when record evidence exists and no tree entry does; `refused` with `malformed` when a tree entry exists and no record evidence does, when the entry is not a regular blob within the size limit, or when AC-0004 or AC-0005 finds the grant or record malformed; `refused` with `stale` under AC-0007; `spent` with `expired` when the runner host's current UTC time is at or after `expires_at`; `spent` with `done` under AC-0008; otherwise `valid`.
- [ ] **AC-0007.** The bound form of a brief is its bytes with only the status token of its one preamble `Status:` line, the token the runner's status parser reads, replaced by a fixed placeholder; every other byte, the rest of that line included, is kept. Let the anchor be the most recent commit on the base's first-parent history that changed the grant file. The grant is `stale` when no anchor is found; when the brief's bound form at the base differs from its bound form at the anchor; when the standing-orders file at the base differs from the one at the anchor, its presence or absence included; or when the anchor's first parent already holds a record line with the same `confirmed_at`, which means the grant changed without a fresh confirmation.
- [ ] **AC-0008.** A `valid`-so-far grant is `spent` with `done` when `done_when` is `all-granted-merged` and every granted slice's stop is `merged`, or when `done_when` is `all-granted-stopped` and every granted slice's stop is `merge-ready` or `merged`.
- [ ] **AC-0009.** Each refused or spent grant carries a `detail` from this fixed vocabulary and no other value: for `malformed`, one of `no-record`, `not-regular`, `oversize`, `not-utf8`, `hidden-text`, `not-toml`, `unknown-key`, `table`, `key:<name>` for each AC-0003 key, `expiry-order`, `expiry-too-long`, `confirmed-in-future`, `record-repeated`, `record-form` or `record-mismatch`; for `stale`, one of `anchor-not-found`, `brief-changed`, `standing-orders-changed` or `not-reconfirmed`; and `null` for `brief-not-ready`, `missing`, `brief-closed`, `expired` and `done`. No detail carries text from the grant file or a parser message.

### Runner answers

- [ ] **AC-0010.** `next` and `status` answers carry `brief_status` (the brief's `Status:` token at the base when it is one of `Draft`, `Ready`, `Executing`, `Shipped`, `Withdrawn` or `Cancelled`, else `null`) and `grant`. A `refused` grant, and a `spent` grant with reason `brief-closed`, is `{"state", "reason", "detail", "human_only", "held_actions"}`, with `held_actions` equal to `["open-pull-request", "push"]`. A `valid` grant, and a `spent` grant with reason `expired` or `done`, adds `anchor`, `expires_at`, `done_when`, `slices`, `retry_budget` and `max_slices_in_flight`, and its `held_actions` is the grant's own, sorted; `reason` and `detail` are `null` for a valid grant. Every `next` answer and refusal carries `schema_version` 2.
- [ ] **AC-0011.** `human_only` is a fixed list in the runner's code, not read from any file: `accept-protected-class-risk`, `approve-plan`, `approve-spec`, `irreversible-operation`, `merge`, `reapprove-after-material-change`. No grant value adds to it or removes from it.
- [ ] **AC-0012.** With a `refused` grant, `next` answers `grant-refused`; with a `spent` grant, `grant-spent`, except that a `brief-closed` grant answers `complete` when every row is `merged`. `grant-refused` and `grant-spent` carry `reason`, `detail`, every `pending` gate as `await-gates` lists them, and `merge_ready` with `spec_paths` for each `merge-ready` row, and name no slice to start or resume, even when a row is resumable.
- [ ] **AC-0013.** With a `valid` grant, `next` decides over every row exactly as the no-grant rule does, with the pilot, the earlier-row rule and the in-flight count all taken over every row, granted or not, and the in-flight cap set to 1; the one difference is that a row not in `slices` is never named by `resume-slice` or `start-slice`. In a `blocked` answer, a non-granted row keeps any of the reasons `unreadable`, `supervisor-changed`, `refused`, `awaiting-decision`, `gate-not-clean` and `terminal-not-ready` that applies, and otherwise reads `not-granted`. A granted row that a non-granted row holds back reads `waits-on-ungranted`, which the controller puts to a human: behind a non-granted pilot, behind a non-granted earlier row whose stop is `none`, or under an in-flight cap filled by a non-granted row.
- [ ] **AC-0014.** For every fixture brief in the grant suite, the set of slices a `valid` grant lets `next` start or resume is a subset of the set the same brief allows with its grant evidence removed.
- [ ] **AC-0015.** Removing both the grant file and the record turns a granted brief into a no-grant run, removing only one makes it `refused`, and a grant file deleted while the record stays reads `missing`.
- [ ] **AC-0016.** After any verb, the repository's Git state, every working-tree file and every slice worktree's supervisor store are byte-identical to before, apart from the supervisor's own security-event log, as AC-0001 of the brief-level-runner spec allows.
- [ ] **AC-0017.** With a `valid` grant, `classify` uses the grant's `retry_budget` in place of `lease.retry_budget`; with a `refused` or `spent` grant, `classify` answers `surface-to-human` for every class.

### Guarded changes

- [ ] **AC-0018.** `brief-runner.py guard --from <rev> --to <rev>` lists the grant changes between the merge base of the two revisions and `--to`, with rename detection off so both sides of a rename count, each with one kind: `grant-file` for a changed path under `docs/product/run-grants/`; `standing-orders` for one under `docs/product/standing-orders/`; and, for a changed brief under `docs/product/briefs/`, judged with the runner's status parser, `brief-granted` when it holds grant evidence on either side, its bound form (AC-0007) changed, and it is not `Shipped`, `Withdrawn` or `Cancelled` at `--to`, `brief-made-runnable` when it is `Ready` or `Executing` at `--to` but not at the merge base (a new brief included), and `brief-spec-map` when it is `Ready` or `Executing` on either side and its Spec map rows changed. The change fails with refusal `grant-change-mixed` when it holds at least one grant change and at least one other changed path, except that, for a slug the change adds to a Spec map, a new `docs/specs/<slug>/spec.md` whose `Status:` is `Draft` at `--to` and a new `docs/specs/<slug>/plan.md` whose `Status:` is `Drafting` there are allowed companions; any other path, a `delivery/` record or an approval record included, is an other path.
- [ ] **AC-0028.** `guard` prints one JSON object, `{"merge_base", "to", "grant_changes": [{"path", "kind"}], "companions": [path], "guard_surface": [path], "other_paths", "verdict"}`, where `guard_surface` lists any changed path in the work-loop scripts directory, `references/brief-runner.md`, the author-delivery-brief `SKILL.md` or `.github/workflows/`, `other_paths` counts the changed paths that are neither grant changes nor allowed companions, `verdict` is `pass` with exit 0 or `fail` with exit 1, and a failing answer adds `refusal` `{"code": "grant-change-mixed", "detail": "grant changes are mixed with other paths"}`, a fixed text naming no path. Any path the runner's unsafe-path rule refuses prints as `withheld`. It refuses with exit 1 and only `{"refusal": {"code", "detail"}}` on `unsupported-git-version`, `git-unavailable`, `unknown-revision` or `internal-error`, and it writes nothing.
- [ ] **AC-0019.** A build-check step runs on every pull request: it extracts the work-loop scripts directory from the pull request's base revision and runs that copy's `guard` with `--from` the base and `--to` the head, writing the answer to the job summary inside a code block; on any other event the step does not run. It runs the head copy instead only when the base tree's `brief-runner.py` holds no `guard` verb, decided by reading the base tree, never from an exit code; the summary then says so.

### Guidance

- [ ] **AC-0020.** `references/brief-runner.md` tells the controller to read grant values only from the runner's answer, never from the grant file; to get a fresh `next` or `status` answer before every start, resume, retry or new dispatch, and to act on a `refused` or `spent` grant seen in any answer, heartbeat `status` included; to start, resume, retry and dispatch nothing for a brief whose grant is `refused` or `spent` while letting a task already running finish; to show the human every listed pending gate and merge-ready slice in that case; that a `valid` grant authorises nothing, so no human-only action and no held action is taken without a human; to push nothing and open no pull request without a human while the grant is `refused` or the runner refuses; to cap session retries of stub writers, reviewers, assessors and slice sessions at the grant's `retry_budget` when a grant is `valid`; that spend is unbounded and no limit is extended by silence, a timeout or a lost session; that "push" means publishing to the repository's shared remote, and excludes saving work to a separate checkpoint remote that accepts refs in one namespace only; to show the human every `pre-ready-in-flight` exemption, with its end time and that a forged slice branch can earn it until then; that an edit to a granted brief's text lands in its own change and makes the grant stale until a new grant stop; and that the guard protects only where the repository runs the base revision's `guard` as a required check on every change to the default branch, with how to wire it. `SKILL.md` points to that section and does not restate it.
- [ ] **AC-0021.** author-delivery-brief continue mode offers a grant path beside today's separate stops, which stay the default. On the grant path, the shaping review's `Clean` covers the proposed slice cut, and one stop asks three separate yes-or-no questions: Ready, the slice cut, the grant. A "no" to Ready writes nothing; a "no" to the cut writes Ready only; a "no" to the grant writes Ready and the confirmed Spec map rows only. On the grant path no answer invokes `new-spec`: a confirmed row's spec is authored later, by the run's `author-spec` mode or in its own change. Only confirmed slices enter the Spec map. For a brief already `Ready` or `Executing`, a grant stop asks only the grant question, with the same display and re-read as AC-0022, and is how a grant is first added or renewed. On today's default path, the Spec map change for confirmed slices lands in a change holding only that brief edit, and the added rows' new Draft `spec.md` and Drafting `plan.md`, so the guard accepts it; a knowledge capture lands in its own change.
- [ ] **AC-0022.** At every grant stop, renewal included, the skill shows the full brief text the grant will bind to, its Spec map included, the exact grant file it will write, the standing orders or that there are none, the fixed human-only list, the held actions, that spend is unbounded, that expiry follows the runner host's clock, and that the grant takes effect only after a reviewed merge of a change holding only grant changes. It also shows every disclosed limit: a worker that can write the main checkout can move the base and remove or rewrite the grant; the guard protects only where the repository runs the base revision's `guard` as a required check that the change cannot edit, and where none runs nothing guards grant changes; direct pushes and bypassed checks skip the guard; a change to the grant-enforcing code can redefine what a grant is; the grant binds to the merged commit, so any edit made in the grant's own change after this stop is bound unless the reviewer catches it; a later change editing brief, grant and record together re-binds it; and the change that first adds the guard is judged by its own copy. The shipped text names no repository-specific workflow. Before writing, it re-reads the brief and standing orders and writes nothing when either differs byte for byte from what it showed; it writes the grant file before the brief, and on a failed brief edit it records a non-dispatchable reconciliation finding.
- [ ] **AC-0023.** work-loop `evals.json` carries two grant cases: one where the grant is `refused` as stale beside a pending gate, whose assertions require the controller to start or resume nothing, show the gate, push nothing and open no pull request; and one with a `valid` grant holding `push` as a held action beside a pending gate and a `merge-ready` slice, whose assertions require the gate to stay unapproved, no merge, and no push without a human. author-delivery-brief `evals.json` carries a grant-path case whose assertions require three separate answers, the disclosures of AC-0022, and no grant written after a "no" to the grant, and a renewal case on an `Executing` brief whose assertions require the full brief shown and only the grant question asked.
- [ ] **AC-0024.** `docs/architecture/security.md` carries a run-grant entry naming the grant as narrowing-only data with no authority, the commit-anchored binding, the guard and every condition under which it does not protect (AC-0022), the base-writer limit, and that spend is unbounded.

### Release

- [ ] **AC-0025.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the same version, one patch above `packs/core/pack.toml` at the merge base with freshly fetched `origin/main`, and a `docs/product/changelog.d/` fragment names the change.
- [ ] **AC-0026.** After self-host, `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .` exit 0 and the tree is clean.
- [ ] **AC-0027.** RFC-0113 links this spec.

## Terminal Intent

`code` — ship the grant reading, the Ready-only rule, the guard, both skills' guidance and evals, the trust-model entry and the Core release with its projections.

## Follow-ons

- eugenelim: `docs/product/captured/read-once-filter-names-race.md` — the runner's existing accepted read race, unchanged here.
- eugenelim: a spend limit, once a host reports usage that the capped agent cannot edit; this spec defines no spend field.
- eugenelim: a `max_slices_in_flight` above 1, once the runner can run slices concurrently.

## Accepted Risk

- A worker that can run Git in a slice worktree and write the main checkout can move the local base, and so delete or rewrite a grant and its record together, returning the brief to its no-grant limits, or remove one and stop the run (AC-0015). The cost is spend and slice order, never an approval or merge. Closing it needs a base the host attests.
- The guard protects only where the repository runs the base revision's `guard` as a required check whose workflow the judged change cannot edit, and where nobody pushes past it. Elsewhere a reviewed change can still carry a grant change, re-bind a grant, or change the grant-enforcing code, and only the reviewing human catches it. The cost is again spend and slice order.
- The agent on the grant path records the handle the person gave and cannot verify who answered, as approval records already accept; a faked grant can only narrow.
- Until the exemption's end time, a worker that can create a slice branch and commit a spec on it can earn a `pre-ready-in-flight` resume for a `Draft` brief's row, the branch-forging route the brief-level runner already accepts. The cost is spend on authoring work that still waits at every approval gate.
- The exemption ends at a fixed calendar time in shipped code, so an installation that upgrades after it gets no exemption for briefs already running without Ready; those briefs wait for a Ready confirmation.
- A wrong host clock moves expiry and the end of the pre-Ready exemption, never past the no-grant limits.
- Spend is unbounded: hosts report no usage that the capped agent cannot edit.

## Assumptions

none
