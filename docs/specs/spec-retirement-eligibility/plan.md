# Plan: Spec-retirement eligibility projection

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
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
| Decision rationale — RFC-0096 Errata 2026-09-24 | T0 | The accepted erratum in tree | Wave 7e's objective and non-goals match what shipped |
| Current architecture — `work-intake-and-artifact-routing.md` | T8 | Whole-surface read | The file states who reports eligibility and who may act on it |
| Release history — `docs/product/changelog.md` | T9 | Core-led entry | Topmost dated `[core]` heading equals `packs/core/pack.toml` |
| Pack release surface — `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` | T9 | Matching patch bump, plus a clean `self-host --check` | Both manifests agree, and every `.claude/` and `.agents/` projection of the two edited skills matches its `.apm/` source |
| Eval harness — `workspace-status/evals/evals.json` | T9 | A case per added behaviour, or a recorded deviation | `packs/AGENTS.md`'s non-cosmetic-update rule is satisfied, or its deviation is stated and reviewed as a deviation rather than as compliance |
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

### Data & schema

The `[areas]` table carries a schema version, a `sha256-bytes-v1` fingerprint of
the repository shape it was derived from, the inferred namespace list, and the
per-spec attribution. Both a version and a fingerprint are present because a
derived cache sharing a file with hand-curated content goes stale silently
otherwise; fingerprint-only designs have documented silent-staleness gaps, and
the repository already uses `sha256-bytes-v1` as a digest kind.

The brief `Spec map` gains one column carrying the commit where the spec was
`Shipped`. `parse_spec_map` reads the first column as the slug and the **last** column as
the status, and returns nothing in between, so position alone cannot tell a pin
cell from the Shape-B `Story` cell its docstring already anticipates in that
slot. The pin is therefore identified by its column header, not its index, and
existing two-column and three-column maps continue to parse unchanged.

### Interfaces & contracts

`retirement-candidates` emits one JSON document validated by
`contracts/jsonschema/spec-retirement-candidates.schema.json`. The envelope
carries the supplied run date, the cutoff derived from it, the in-memory area
attribution, one entry per spec, and a refusal list. This delivery writes
nothing.

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
directory behind it, a directory holding no `spec.md`, and a `spec.md` that
cannot be read. Each carries its own refusal code, because a maintainer acts
differently on each and a shared code erases the difference.

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

### T5: Each blocker holds a candidate back

**Depends on:** T0b, T0c

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

**Depends on:** T3, T7

**Tests:**
- End-to-end invocation against a disposable fixture returns the documented exit
  code and a schema-valid document.
- Every refusal code `retirement-candidates` can emit has a fixture that produces
  it, enumerated from the schema enum filtered to this command's surface rather
  than listed here, so a code added without a fixture fails the case. A code
  belonging to another surface is out of the domain rather than an unsatisfiable
  member of it.
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
- `workspace-status/evals/evals.json` gains a case covering the subcommand this
  delivery adds, or the plan records a deviation naming why no case changes.
  Only this skill is edited; `author-delivery-brief` left with the brief half.
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

- **Delivery:** purely additive. One new read-only subcommand and one new
  schema; no existing file changes behaviour and nothing is written. Reversible
  by removing the subcommand.
- **Infrastructure:** none.
- **External-system integration:** none. `git` is already required by the skill.
- **Deployment sequencing:** each task's `Depends on:` is the canonical
  ordering; this section adds none. T0 precedes spec approval because the
  erratum is the authority the criteria cite.

## Risks

- **A spec held by a `Shipped` brief stays unretirable until the
  brief-retirability follow-on ships.** This capability reports the hold and
  names what would clear it; it cannot clear it.
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
- **A spec mapped by a `Shipped` brief cannot be retired at all until the
  brief-retirability follow-on ships.** This capability reports
  `shipped-brief-member` and names the hold; it cannot clear it. Exposure grows
  with each brief that ships.

## Changelog

- 2026-09-23 — Drafted.
- 2026-09-24 — Approved shape: Wave 7e, age reported from change history, and
  the blocker vocabulary derived from the RFC's named set.
- 2026-09-24 — Cut to a read-only core; brief retirability and the persisted
  area map sliced out as separate deliveries.
- 2026-09-24 — Spec and plan approved by eugenelim.
- 2026-09-24 — Spec and plan approved by eugenelim.
