# Plan: Spec-retirement eligibility projection

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** [`AGENTS.md`](../../../AGENTS.md); [`packs/AGENTS.md`](../../../packs/AGENTS.md); [`packs/core/AGENTS.md`](../../../packs/core/AGENTS.md) § skill dependencies; [`tests/AGENTS.md`](../../../tests/AGENTS.md); [RFC-0096](../../rfc/0096-portable-delivery-artifact-lifecycle.md) §§2, 4, 6, 7 and the Wave 7e Errata

## Approach

Candidate discovery joins `workspace-status` as a read-only subcommand because
its refusal vocabulary, confinement rails, and JSON envelope already exist
there, and RFC-0096 §7 assigns eligibility reporting to a deterministic helper.

Two orderings carry the delivery. Brief retirability lands before the projector,
because `shipped-brief-member` has no correct behaviour to assert until a spec
under a brief can legitimately retire. The area writer lands before its readers,
because three subcommands read a map none of them may create.

`.context/spec-retirement-inventory.py` is the behavioural reference for the
git-log walk and the citation buckets, not a file to move: `.context/` is
gitignored, and its `eligible` column is replaced by the blocker list.

**A blocker a maintainer cannot clear is a defect, not a safeguard.** RFC-0096 §7
says a completion receipt "remains only while live downstream work depends on
it", so a `needs` edge left in a shipped entry is residue. Blocking on it
permanently makes the spec it names unretirable by any available action.
Ignoring it is worse: `workspace_status_prune.py` has no `needs` handling, so
deletion leaves the edge dangling — the breakage the previous wave hit. So
retirement removes its inbound edges in the same change that deletes the spec,
on the pattern the brief already uses, and the projector names each edge so the
action is visible rather than inferred.

**An unresolvable input refuses; it is never defaulted.** This is what makes the
capability portable. An adopter carries collection names, `needs` shapes, and
`Status:` values this repository does not, and a projector that silently skips
what it cannot parse reports a shorter candidate list with no sign anything was
dropped — a false negative in the deletion-permissive direction. Every substrate
reader classifies its input or refuses it by name, and the refusal codes are part
of the emitted contract. T0b enumerates the shapes that exist; this rule governs
the ones it does not find.

## Constraints

- `workspace-status` scripts are stdlib-only except the guarded, CLI-only
  `tomlkit` import that `repair-apply` owns. `packs/core/AGENTS.md` declares it
  at `==0.15.1` and states the runtime-detection contract. This capability adds
  no dependency and does not reach for that one.
- Python 3.11 floor (`pyproject.toml`: `target-version = "py311"`,
  `python_version = "3.11"`).
- A test under `packs/<pack>/tests/` may not read above its own pack, and
  `tools/test-lint-pack-test-boundary.py` enforces it. Repository-level
  assertions go to `tests/roster/`.
- A new `tests/roster/` module obliges a named `build-check.yml` step placed
  **above** the bulk pytest step, a matching `STEP_DISPOSITION` entry in
  `tools/lint-ci-parity.py`, and a `.workspace-prune-protected.toml` entry where
  the test names a `docs/specs/<slug>` path as a literal (`tests/AGENTS.md`).
- `lint-brief-coverage.py` is a shipped fail-closed CI gate. Exit `0` means
  clean, exit `1` means drift; both meanings are load-bearing for adopter CI.
- `workspace.toml` is a seed, and install must not overwrite an adopter-edited
  seed — asserted in the agentbundle integration suite's seed-delivery test.
  That guarantee is what makes it a safe home for the area map.
- Any write to `workspace.toml` goes through the skill's existing lock and
  atomic-write rails, which `references/mutate.md` owns.
- Under `packs/`, write portable guidance only: no citation of this catalogue's
  internal records, acceptance criteria, or repository-only paths
  (`packs/AGENTS.md`). The shipped `SKILL.md` therefore states each blocker's
  rule directly and names no RFC, ADR, or `docs/` path, even though every
  blocker is derived from RFC-0096.

## Construction tests

Area attribution is inferred across every tracked top-level namespace because a
spike ranked three strategies by how many candidates each left with no area,
worst first:

1. `packs/` grep over `spec.md` — the prototype's strategy.
2. `packs/` grep over `spec.md` and `plan.md`.
3. Every tracked top-level namespace over both files.

Single-namespace inference reproduces the prototype's attribution exactly,
because it asks the same question of the same text; only multi-namespace
inference closes the remaining gap. The measured figures live in the
verification ledger, as a snapshot of a growing corpus that no criterion or test
asserts.

A second spike confirmed the brief mechanism against real history: for a spec
deleted in `d7aa82b8d`, `git cat-file -e <parent>:docs/specs/<slug>/spec.md`
resolves and `git show` recovers `- **Status:** Shipped`. The pin is verifiable,
not trusted.

`inbound-cited` is a blocker rather than a report-only column because a large
fraction of the specs the prototype reports eligible carry an inbound citation
from a surface RFC-0096's Wave 7d carve-out enumerates. The fraction is a
property of the corpus on one day, so it is not recorded here.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface contract — `spec-retirement-candidates.schema.json` | T6, T7 | Schema validation over emitted output | Schema carries `x-spec`; emitter validates |
| User promise — `workspace-status/SKILL.md` | T8 | Roster test plus end-to-end fixture invocation | Documented invocations, blocker vocabulary, and refusal codes match shipped behaviour |
| Interface compatibility — `lint-brief-coverage.py` and its owning guide | T1, T2 | Three resolutions driven through the lint entry point, plus the unpinned-row regression | Documented `Spec map` shape names the commit-pin column |
| Decision rationale — RFC-0096 Errata 2026-09-24 | T0 | The accepted erratum in tree | Wave 7e's objective and non-goals match what shipped |
| Current architecture — `work-intake-and-artifact-routing.md` | T8 | Whole-surface read | The file states who reports eligibility and who may act on it |
| Release history — `docs/product/changelog.md` | T9 | Core-led entry | Topmost dated `[core]` heading equals `packs/core/pack.toml` |
| Pack release surface — `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` | T9 | Matching patch bump, plus a clean `self-host --check` | Both manifests agree, and every `.claude/` and `.agents/` projection of the two edited skills matches its `.apm/` source |
| Eval harness — each edited skill's `evals/evals.json` | T9 | A case per added behaviour, or a recorded deviation | `packs/AGENTS.md`'s non-cosmetic-update rule is satisfied, or its deviation is stated and reviewed as a deviation rather than as compliance |
| Reusable learning — `notes/repo-root-layout-survey.md` | T9 | The survey, already written | Accepted capture receipt or explicit not-applicable finding |

## Design (LLD)

### Design decisions

**Eligibility is a blocker list, not a boolean.** The prototype collapses its
guards into one bit, so a maintainer reading a `0` cannot tell whether the spec
is protected, cited, depended on, or simply young. Emitting the blockers makes
each guard separately observable, which is what lets a construction test prove a
guard fired rather than prove a sweep came back clean.

**Authority for the blocker set is split.** RFC-0096's Wave 7e erratum owns the
coverage obligation — which conditions must be reported, and that fingerprint
drift and uncertain authority are excluded because they read lifecycle-record
fields this capability never opens. The schema enum owns the code vocabulary.
Neither restates the other.

**Age comes from change history, and is never called a cooling verdict.** §6's
clock runs from `completed_on` on a lifecycle record, and §6 says "creation,
Ready, edits, and session end never start the clock". `docs/lifecycle/` holds
only its README because cooling is opt-in, so there is no record to read. The
report therefore carries the last recorded change, labelled as such, and the
blocker is `recently-changed` rather than §6's vocabulary. An edit-derived age is
not conservative in a fixed direction, so it is a triage signal, never a
disposition; §6's clock still governs every deletion, which Wave 7c enforces.

Importing `close-work`'s cooling module is not available:
`guides/_shared/reference/skill-script-conventions.md` § Sharing code across
skills bans cross-skill relative imports, and `lint-brief-coverage.py` already
hand-duplicates a helper for that reason. Shared code would have to move to
`.apm/shared-libs/`, which is larger than this capability needs.

**Brief resolution touches three resolutions and five consumers, enumerated by
line rather than by description.** The count went 1→3→4→5→6 across review rounds
while it was stated as responsibilities; the verification ledger's T0b pass
pinned it to call sites, and that enumeration is what T1's revert condition
cites. Resolutions: `L263` (mapped rows, feeding `derived`), `L291` (untracked
back-links), `L317` (renderer, which re-resolves rather than reusing `derived`).
Consumers: `L160`, `L166`, `L270`, `L309`, and the renderer's own row output.
Each carries a different consequence. A `Retired` state reaching the renderer alone is worse than no
change at all.

- `_brief_lifecycle_is_valid`'s `Shipped` branch requires the child set to
  normalise to exactly `{"shipped"}`. A `Retired` child makes the lifecycle
  invalid and **returns exit 1** — the opposite of the criterion.
- The same function's `execution_evidence` term is computed from
  `{"implementing", "shipped"}` before any branch runs. A `Retired` child is
  absent from it, so a `Draft`, `Ready`, or `Withdrawn` brief whose children have
  all retired **passes** while carrying the strongest evidence that execution
  happened, and an `Executing` or `Cancelled` brief whose children have all
  retired **fails**. Both directions are wrong, and neither touches the `Shipped`
  path above.
- The `delivered` predicate requires every derived state to equal `shipped`. It
  feeds the printed delivery line only and never the exit code, so a test
  asserting exit codes alone cannot observe it.
- The recorded-cell drift check compares the map's status cell against the
  derived status, and fires a hard violation **exiting 1** on its own,
  independently of every branch above.
- The renderer decides which token a reader sees.
- A sixth site resolves an untracked back-linked child independently. It is
  unreachable for a retired child — the spec index globs `docs/specs/*/spec.md`,
  so a deleted spec never enters it — and is listed because the argument that
  retires it is the part worth recording.

Four of the six learn a permitted child set; the drift check and the renderer
learn the resolution instead. Each reachable site independently returns the exit
code the criterion forbids, which is why T1 drives the lint's entry point rather
than its resolver and asserts the delivery line alongside the exit code.

**Every consumer admits two new derived states, and they differ.** `Retired` and
`unverifiable` both join `missing` as outcomes for an absent child, but they
carry different evidential weight and the consumers must not treat them alike.

`Retired` means the pin resolved and the object carried a `Shipped` body, so
execution is proven: the `Shipped` branch admits it, and the execution-evidence
term admits it. `unverifiable` means nothing could be proven, so it is **not**
execution evidence — a `Draft` brief carrying one stays valid, and an
`Executing` brief carrying only unverifiable children does not. The `Shipped`
branch admits it because a delivered brief whose spec is gone and whose pin no
longer resolves is not evidence the brief failed. The drift check treats it as
non-drift, because a pin that cannot resolve says nothing about whether the
recorded cell is stale.

The child-state domain also contains `governance-reference`, which L261 appends
for a row naming a governance record rather than a spec. It is already a hard
violation on its own, so no new state interacts with it — but it is in the
domain, and a permitted-set statement that omits it is incomplete.

**Retiring a spec edits two cells, not one.** The pin column takes the commit and
the status cell takes `Retired`. A pin without the cell update leaves the row
stale and the drift check fires; a cell without a pin renders `missing`. They
travel together, and the shipped guide says so.

### Data & schema

The `[areas]` table carries a schema version, a `sha256-bytes-v1` fingerprint of
the repository shape it was derived from, the inferred namespace list, and the
per-spec attribution. Both a version and a fingerprint are present because a
derived cache sharing a file with hand-curated content goes stale silently
otherwise; fingerprint-only designs have documented silent-staleness gaps, and
the repository already uses `sha256-bytes-v1` as a digest kind.

`Retired` is a rendering derived from an absent directory plus a resolving
commit pin. It is never a `Status:` token, and it is distinct from `Archived`,
which is a status a present spec carries and which this delivery leaves
untouched.

The brief `Spec map` gains one column carrying the commit where the spec was
`Shipped`. `parse_spec_map` reads the first column as the slug and the **last** column as
the status, and returns nothing in between, so position alone cannot tell a pin
cell from the Shape-B `Story` cell its docstring already anticipates in that
slot. The pin is therefore identified by its column header, not its index, and
existing two-column and three-column maps continue to parse unchanged.

**`areas-refresh` splices one table; it never round-trips the document.**
`workspace.toml` is hand-curated and comment-bearing, and `tomllib` has no
writer — dumping a parsed document back would strip every comment in the file.
`tomlkit` is declared for `repair-apply` only (`packs/core/AGENTS.md` § skill
dependencies) and this capability does not widen that declaration. So the write
locates the `[areas]` table's byte span and replaces exactly that span, or
appends the table where none exists. The byte-preservation criterion is then the
property the mechanism guarantees rather than one it hopes for, and the
re-refresh case exists because replacing a span and appending one are different
code paths.

### Interfaces & contracts

`retirement-candidates` emits one JSON document validated by
`contracts/jsonschema/spec-retirement-candidates.schema.json`. The envelope
carries the cutoff used, the area-map freshness verdict, one entry per spec, and
a refusal list. `areas-refresh` is the delivery's only writer and emits the
skill's existing mutate-shaped result.

### Component / module decomposition

Both subcommands land in a new module beside `workspace_status_prune.py` rather
than inside `workspace_status.py`, which is already 3,234 lines. The dispatch in
`main()` gains two branches; blocker detection, obligation classification, and
area inference are separately testable functions.

Area inference derives its namespace set from tracked top-level directories. It
does not read `.adapt-discovery.toml`: that file's typed loader silently drops
unknown tables on round-trip, measured directly, and its module contract names
`adapt-to-project` as the write owner.

### Behavior & rules

The envelope's cutoff is the run date minus `stale_after_days`, and each
candidate's age is its last recorded change.

`stale_after_days` has its default fixed by the criterion. Its origin is the
prototype's own default and the thirty-day interval this repository already uses
for delivery artifacts, not RFC-0096 §6 — borrowing §6's number would imply borrowing its clock, which this
capability does not read. The value is a triage threshold a caller overrides, so
it carries no authority: nothing is deleted because a candidate crossed it. The prototype shipped with `date -u -v-30d`, which is BSD-only — on Linux
CI the cutoff became the empty string, every comparison went False, and every
spec reported ineligible with a clean exit. That shape, a control reporting
success while doing nothing, is why a criterion pins the cutoff to a calendar
date on the run where no candidate carries a record.

### Failure, edge cases & resilience

Three absences are distinct: a `workspace.toml` entry naming a slug with no
directory behind it, a directory holding no `spec.md`, and a mapped spec whose
commit pin does not resolve. The third must not fail closed, because a shallow
clone cannot resolve any pin and an adopter's CI would break on a condition they
cannot fix.

### Quality attributes (NFRs)

The prototype walks the whole tree per run and completed in 9.3s against the
corpus as it stood on 2026-09-23. That is inside an interactive budget and no
optimisation is planned; the risk register records where it stops holding.

### Dependencies & integration

No new dependency. See Constraints for the one this skill already declares.

## Tasks

### T0: Wave 7e exists as accepted governance

**Depends on:** none

**Tests:**
- The erratum is in tree, dated, and names an approver.
- Every line citation in the erratum resolves to the text it claims.

**Done when:** a reader following the erratum alone can tell which wave owns
candidate discovery, on what date it was decided, and by whom — and no citation
in it resolves to text that does not support the sentence quoting it.

### T0b: The substrate's real shapes are enumerated, not assumed

**Depends on:** none

**Tests:**
- A probe enumerates, from the repository it runs in: every distinct `needs`
  value shape; every collection name and the `path` shape each holds; every
  distinct `Status:` value including absence; every read of a child status in
  `lint-brief-coverage.py`; and every non-writing branch of the `workspace-status`
  dispatch.
- Re-running the probe over an unchanged tree returns the same enumeration.
- The probe reports a shape it has no rule for, rather than omitting it.

**Approach:**
- This task exists because five review rounds each found one substrate fact
  established by reading rather than by enumeration, and each was wrong: the
  count of child-status read sites went one, three, four, five, six; the
  collection set was wrong twice; and `needs` was taken for a list of tables when
  the file also carries a bare string. A probe answers each in seconds and does
  not sample.
- The probe is throwaway and is not committed. What ships is its consequence:
  every criterion that names a substrate shape is written from its output, and
  every shape it cannot classify becomes a refusal code rather than a default.
- It runs against the adopter's repository, not this one. Its value is that the
  shapes it finds there will differ, and the capability must refuse what it
  cannot resolve instead of silently skipping it.

**Done when:** the enumeration is recorded in the verification ledger, every
criterion naming a substrate shape matches it, and introducing an unclassifiable
shape into a fixture produces a refusal rather than a missing candidate.

**When the enumeration disagrees with a criterion**, the criterion is wrong: the
probe reads the substrate and the criterion only described it. Before approval
the criterion is rewritten from the ledger. After approval it takes the
controlled amendment route in
[`delivery-contract-lifecycle.md`](../../../.claude/skills/work-loop/references/delivery-contract-lifecycle.md);
it is never reconciled by widening the probe.

### T0c: Every reader fails closed, and no path escapes the root

**Depends on:** T0b

**Tests:**
- Each substrate input in turn — `workspace.toml`, the protected manifest, a
  contract carrying `x-spec`, a brief body, a spec body — made unreadable, then
  unparseable: each produces a named refusal naming that input, and every
  candidate whose blockers depend on it is withheld from eligible. Verifies the
  three fail-closed criteria.
- A `needs` slug of `../../../../etc/passwd` and a spec directory symlinked
  outside the root are each refused `path-escapes-root` and never opened,
  asserted by the absence of the read rather than by the refusal alone.
- Every repository read routes through the skill's own confinement helper;
  removing that call turns a case red.

**Approach:**
- The helper is `workspace-status`'s own, in the same skill, so importing it is
  legal where a cross-skill import would not be. The blessed
  `agentbundle.catalogue_tooling.file_safety` helpers are not reachable from
  shipped pack content an adopter installs without that package.
- The unreadable case is distinct from the unparseable case and both are tested:
  a permission error and a syntax error arrive by different paths and only one
  of them raises where a naive reader expects it.

**Done when:** deleting any single fail-closed branch makes a candidate whose
evidence is missing report eligible, and that is what turns the case red.

### T0d: A commit pin cannot be a revision expression or an option

**Depends on:** T0b

**Tests:**
- A pin of `HEAD`, of `:/Status`, and of a branch name are each rejected on
  shape and render `unverifiable` without git being invoked. Verifies the shape
  and the never-reaches-git criteria.
- A pin of `--output=/tmp/x` is rejected on shape; a full object id beginning
  with `-` cannot occur, and the positional-after-`--` form is asserted by
  inspecting the invocation rather than by its result.
- A full object id that resolves but does not contain the mapped spec's
  `spec.md` renders `unverifiable`, not `Retired`.
- A full object id whose `spec.md` carries an annotated `Shipped (<date>)`
  renders `Retired`, exercising the leading-token reduction on the pin path too.

**Approach:**
- Shape validation precedes resolution because the attack is against the
  argument parser, not the object store: `git cat-file -e --output=x` reports
  `unknown option`, which means the value was read as an option, and a check
  that runs after invocation has already lost.

**Done when:** each rejected form is proven not to reach git — by a stub that
fails the test if called — rather than by observing a benign result.

### T1: A retired spec passes its brief's lint through the entry point

**Depends on:** T0b

**Tests:**
- Temporary repository, spec committed `Shipped` then deleted, row carries the
  pin: the lint's entry point exits `0` and renders the child `Retired`.
  Verifies the `Retired` criterion.
- Same fixture, pin points at a commit not containing the path: exits `0`,
  renders `unverifiable`. Verifies the unverifiable criterion.
- Same fixture, no pin column: exits `1`, renders `missing`. Verifies the
  unchanged-path criterion.
- `git` absent from `PATH`: every pinned row renders `unverifiable`, exit `0`.
- An `Executing` brief with one `Retired` and one `Shipped` child exits `0`, and
  a `Draft` brief with a `Retired` child exits `1`.
- A `Draft` brief with an `unverifiable` child exits `0`, and an `Executing`
  brief whose children are all `unverifiable` exits `1`. Verifies that an
  unresolvable pin is not execution evidence. Verifies the two
  execution-evidence criteria.
- The `Shipped` fixture's printed delivery line reports delivered, which is the
  only case that observes the `delivered` predicate.
- A mapped child present and carrying `Status: Archived` renders `Archived`.
- A row whose cell reads `Retired` with a resolving pin reports no drift; a row
  whose cell still reads `Shipped` with the spec absent reports drift and exits
  `1`. Verifies the two drift criteria, and covers the consumer that fires
  independently of every lifecycle branch.

**Approach:**
- Cases drive `main()`, not the resolver, because the defect this task exists to
  prevent lives in the two consumers downstream of the resolver — the lifecycle
  validity check and the delivered predicate — and a resolver-level test passes
  while both are still wrong.
- The fixture is a real git object store rather than a mock, because the
  property under test is that a deleted file is recoverable from history; a mock
  would assert the test's own model of git instead.

**Done when:** every case is green through the lint's entry point, and reverting
any one of the enumerated reachable consumers individually turns at least one
case red.

### T2: Unpinned rows are untouched

**Depends on:** T1

**Tests:**
- For every brief whose `Spec map` carries at least one row and no commit pin,
  each row renders the mapped spec's own `Status:` value. Verifies the
  additivity criterion as a property rather than a snapshot, so it still runs
  after the change ships and needs no recorded file.
- A three-column map and a two-column map both parse, confirming the pin column
  does not displace the last-column status read.

**Approach:**
- The corpus is enumerated at run time from `docs/product/briefs/` rather than
  from a recorded count, so a brief added after this plan is covered rather than
  silently skipped.

**Done when:** the property holds for every brief the run enumerates, and a
mapped row whose spec carries a status the property does not predict fails it.
The pre-change behaviour needs no recorded file: it is recoverable from the
commit that precedes this change.

### T3: Area inference is a pure function of repository shape

**Depends on:** none

**Tests:**
- Fixture whose only top-level source directory is named something other than
  `packs`: a spec naming it is attributed to it. Verifies the portability
  criterion.
- A spec matching no inferred namespace is attributed `unscoped`, never blank.
- Two calls over an unchanged tracked file list return equal results.
- No spec that names an inferred namespace is left unattributed.

**Approach:**
- Cases run against constructed fixtures, so the task's home is the
  `workspace-status` pack suite. The repository-wide sweep belongs to T8's
  roster module, because a pack test may not read above its pack.

**Done when:** the four cases are green in the pack suite, and the current
repository's unattributed count is recorded in the verification ledger rather
than asserted.

### T4: Only `areas-refresh` writes, and it writes under the lock

**Depends on:** T0b, T3

**Tests:**
- `areas-refresh` creates `[areas]` carrying a schema version, a
  `sha256-bytes-v1` fingerprint, the namespace list, and the attributions.
- Hand-curated content elsewhere in `workspace.toml` is byte-identical across
  the write. Verifies the isolation criterion.
- `areas-refresh` refuses with `lock_busy` when the lock is already held.
- A shape change alters the recorded fingerprint; an unchanged shape leaves it
  equal. Verifies the fingerprint criterion.
- Every non-writing branch of the subcommand dispatch leaves `workspace.toml`
  byte-identical, with the map absent and with it stale. The case enumerates the
  branches by reading the dispatch table, so a subcommand added later is covered
  without editing the test.

**Approach:**
- The write reuses the prune's existing lock and atomic-write seam rather than a
  second one, so a concurrent intake transaction serialises against it the same
  way every other workspace writer does.

**Done when:** deleting the lock acquisition turns the `lock_busy` case red, and
the byte-identity case fails if a non-writing branch is added to the dispatch
without being covered.

### T5: Each blocker holds a candidate back

**Depends on:** T0b, T1, T2

**Tests:**
- One fixture candidate per blocker code, enumerated from the schema enum rather
  than from a list in this task, each asserting that its code appears and that
  the candidate is not eligible. A code added to the enum without a fixture fails
  the case rather than being silently uncovered.
- A candidate with two dependents lists both, and each entry carries the `needs`
  edge that clears it. Verifies the two `needed-by` naming criteria.
- Removing every declaring edge from the fixture clears the blocker, and removing
  only one of two does not. Verifies the clearability criterion, which is the
  half a permanently-blocking implementation would still pass.
- A candidate cited from a governance surface carries `inbound-cited` naming
  that surface. Verifies the `inbound-cited` criteria.
- A candidate free of every blocker is eligible with an empty list. Verifies the
  positive-path criterion.
- A spec whose status reads `Shipped (2026-05-26)` is classified terminal, not
  refused. Verifies the normalisation criterion against the shape T0b found on
  276 of 481 specs — the defect that sent this contract back to drafting.
- The recognised status set equals `lint-spec-status`'s, asserted by comparing
  the two sets, so a divergence fails rather than drifting silently.
- A collection name absent from both the terminal and non-terminal lists is
  refused `collection-unrecognised` rather than defaulted to `inflight`.
- The emitted `cutoff_date` is a calendar date equal to the run date minus
  `stale_after_days`, and the output records the `stale_after_days` it used.
  Verifies the recording criterion, which a run that computes correctly but
  reports nothing would otherwise pass. Verifies the two cutoff criteria; the historical failure it
  guards is a cutoff that silently became empty and made every comparison False.

**Approach:**
- The `needs` walk, the protected-list read, and the `x-spec` scan reuse the
  prototype's parsing shapes rather than its greps: each grep it started with
  was wrong by a factor, and the `x-spec` count was the worst of them.

**Done when:** every blocker code has a case in which it is the sole reason the
candidate is held back, so no case passes by a candidate being ineligible for a
different reason.

### T6: Obligations fire on a proxy and name their role

**Depends on:** T5

**Tests:**
- A candidate whose directory holds a `notes/` file that no surface outside the
  directory cites carries `lasting-facts-unsettled` with its RFC-0096 §2 role
  named. That uncited-`notes/` condition is the mechanical proxy the blocker
  fires on; the role attached to it is advisory classification, which is why the
  criterion pins the proxy and not the judgement.
- A candidate carrying a durable invariant, and one carrying non-inferable
  policy, name their distinct roles.
- A candidate whose claims are recoverable elsewhere carries no obligation.
- A candidate whose last recorded change is newer than the cutoff carries
  `recently-changed`; one whose change is older does not. Verifies the two age
  criteria.
- No emitted field is named for a lifecycle record or presents an age as a §6
  cooling verdict. Verifies the vocabulary criterion.

**Approach:**
- Where §4's precedence order resolves a role to a location, the destination is
  emitted; where it does not, the role is emitted alone. The alternative —
  emitting a guessed path — would present an unmade decision as a made one.

**Done when:** the proxy case fails if the blocker fires on a directory whose
`notes/` file is cited from outside it, and the three obligation classes are
distinguishable from one another in the output.

### T7: The output matches its contract

**Depends on:** T6

**Tests:**
- Emitted output validates against the schema.
- The schema's `x-spec` resolves to this spec's directory.
- A blocker code absent from the schema enum fails validation.

**Done when:** validation is driven from the schema rather than a copy of it —
adding an unlisted blocker code, and changing the `x-spec` pointer, each turn a
case red.

### T8: The subcommands are reachable, documented, and refuse cleanly

**Depends on:** T4, T7

**Tests:**
- End-to-end invocation against a disposable fixture returns the documented exit
  code and a schema-valid document.
- Every refusal code the schema enum carries has a fixture that produces it,
  enumerated from the enum rather than listed here, so a code added without a
  fixture fails the case. Verifies the refusal criteria.
- Two invocations over an unchanged tree emit byte-identical output.
- `status` includes the map when present and emits its remaining output
  unchanged when absent.
- The repository-wide sweep T3 could not host: no spec naming an inferred
  namespace is unattributed across the real corpus.

**Approach:**
- The roster module's named `build-check.yml` step is placed **above** the bulk
  pytest step, because a step below it still executes but reports the failure
  against a broad target instead of the named one.

**Done when:** `python3 -m pytest tests/roster/<module> -q` is green,
`tools/lint-ci-parity.py` reports the new `STEP_DISPOSITION` entry present,
`tools/test-lint-pack-test-boundary.py` passes, and — where the module names a
`docs/specs/<slug>` path as a literal — `.workspace-prune-protected.toml` carries
its entry, which a prune preview against that slug proves by refusing it.

### T9: The delivery's durable surfaces match shipped behaviour

**Depends on:** T8

**Tests:**
- `tools/lint-ci-parity.py` and the build-check posture test both pass.
- `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the
  same version, one patch above the value they shared before this delivery.
  Both edited skills live in `packs/core`, so this is one bump, not two.
- `python3 -m agentbundle catalogue self-host --root . --check` exits clean after
  the `.apm/` edits, proving the `.claude/` and `.agents/` projections of both
  edited skills match their sources. The `--write` form is how they are brought
  into line; the `--check` form is the test.
- Each edited skill's `evals/evals.json` gains a case covering the behaviour this
  delivery adds, or the plan records a deviation naming why no case changes.
- The topmost dated `[core]` changelog heading equals `packs/core/pack.toml`.
- A whole-surface read of `docs/architecture/work-intake-and-artifact-routing.md`
  against shipped behaviour, recorded in the verification ledger.

**Approach:**
- The bump is a patch, not a minor: the rule sizes a minor by new *primitives*,
  and this adds subcommands to an existing skill rather than a new skill,
  subagent, command, or hook.
- The version is read from the pre-delivery value at implementation time rather
  than written into this plan. An unpushed bump collides silently with a peer's,
  so a number frozen at approval is a number that is already wrong.
- Self-host runs after the last `.apm/` edit, not alongside it. Projections
  generated mid-change are stale by the end of the task and pass their own check.

**Done when:** `make lint-ruff lint-mypy` is clean, the gate chain is green, a
self-host `--check` run is clean against a tree with no uncommitted `.apm/`
edits, and each durable-output row's closeout condition is evidenced in the
ledger.

## Rollout

- **Delivery:** additive for every brief map row carrying no commit pin, which
  is every row today. The subcommands are new and the `[areas]` table is absent
  until `areas-refresh` runs. Reversible by removing both subcommands and the
  two new brief resolutions.
- **Infrastructure:** none.
- **External-system integration:** none. `git` is already required by the skill.
- **Deployment sequencing:** each task's `Depends on:` is the canonical
  ordering; this section adds none. T0 precedes spec approval because the
  erratum is the authority the criteria cite.

## Risks

- **A shallow-cloned adopter cannot resolve any commit pin.** The `unverifiable`
  resolution keeps their CI passing, but their brief-derived specs stay
  unretirable in practice. No adopter corpus was reachable to size this.
- **The reported age is not RFC-0096 §6's cooling clock, and a reader may treat
  it as one.** §6 runs from a selected delivery-completion event; this runs from
  the last recorded change, which §6 says never starts the clock. A squash or
  rebase moves it. The output labels the signal and the erratum states the
  limit, but neither prevents a human from acting on it as though it were a
  disposition. The mitigation is that eligibility authorizes nothing and Wave 7c
  re-checks every §6 condition at the mutation.
- **The `[areas]` table is a derived cache in a hand-curated seeded file.** The
  fingerprint makes staleness detectable rather than impossible; a hand edit
  between refreshes is reported, not prevented.
- **The whole-tree walk grows with the corpus.** At roughly three times the
  measured corpus it leaves an interactive budget, and the report would then
  need incremental input.
- **Every spec mapped by a `Shipped` brief ages past the cooling window and
  becomes a retirement candidate.** Until T1 ships, retiring any of them fails
  `gate-main`. Exposure grows with each brief that ships, and the currently
  mapped set ages in within weeks of this plan.

## Changelog

- 2026-09-23 — Drafted.
- 2026-09-24 — Approved shape: Wave 7e, age reported from change history, and
  the blocker vocabulary derived from the RFC's named set.
- 2026-09-24 — Spec and plan approved by eugenelim.
