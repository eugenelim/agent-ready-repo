# Plan: conventions-retirement

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)
- **Repository anchors:** `packages/agentbundle/agentbundle/build/self_host.py:465-580`
  (projection classification), `packs/AGENTS.local.md:10-14` (projections are
  do-not-edit targets), `tools/lint-agents-md.py:29-33` (caps),
  `packs/AGENTS.local.md:28-30` (release rule).

## Approach

Build the new homes before removing the old one. Each task owns one section: it
moves that section's prose to a named destination and re-points that section's
consumers, so no heading disappears while a consumer still addresses it.

The plan decides *which file owns what*. It does not enumerate consumers or
destination headings — execution discovers those against the real files, under
the procedure below, and the procedure's own check is the completion evidence.
That keeps freeze-time detail out of the approval gate and puts the oracle where
it belongs.

## The task procedure

Every relocation task runs the same four steps. The plan names the section and its
destination; execution discovers the rest against the real files, which are the
only reliable oracle for what references a section and how a destination reads.

1. **Scope.** The task names one source section, including every subsection inside
   it, a repo destination, and an adopter destination. Where the adopter
   destination is `none`, the section's seed references are deleted rather than
   re-pointed, and the task records why the content was maintainer-only. One owned region has **no heading** — the Skills
   paragraph at `docs/CONVENTIONS.md:1291-1300`, which `author-a-skill.md` cites as
   "§ Skills". Scope by line range where no heading exists; a heading-based sweep
   silently skips it.
2. **Discover.** Run the single recorded predicate, which matches `CONVENTIONS`
   with or without the `.md` suffix, because live sources cite the document by
   section alone and a suffixed pattern misses them:
   ```bash
   sh docs/specs/conventions-retirement/notes/ac2-scan.sh                  # every consumer
   sh docs/specs/conventions-retirement/notes/ac2-scan.sh 'CONVENTIONS.md#<anchor>'
   sh docs/specs/conventions-retirement/notes/ac2-scan.sh 'CONVENTIONS.\{0,40\}<section>'
   ```
   Run the third form once per heading and named subsection in the task's declared
   source range, not once per task. Record the output in the verification ledger. A
   consumer the plan did not anticipate is expected, not a plan amendment.
3. **Relocate and re-point.** Move the prose into the destination in that
   destination's own voice, then re-point every consumer discovery returned. A
   consumer is re-pointed, never deleted, unless deletion is its recorded
   disposition.
4. **Check.** Three conditions, all of them machine-readable:
   - the task's discovery forms return empty;
   - every anchor the task owned has a replacement resolving to the heading written
     back into its `notes/anchor-map.txt` row, and that heading is the one the
     relocated content actually landed under — decided at move time against the
     real file. A destination often already carries a plausible generic heading;
     resolving to one of those misdirects the reader while passing the check;
   - **no seed the task touched links outside the installed scaffold.** A seed may
     link only to one of the 15 installed paths, or state the rule inline. This is
     the condition `docs/architecture/pack-layout.md` would have failed.
   - **every presence assertion in this plan matches against content with HTML
     comments and fenced code blocks stripped, standard library only, and matches
     within the governing section.** A token parked in a comment, a heading or a
     link title satisfies a naive substring check while governing nothing. This
     applies to every `states`, `carries` and `names` assertion below, not only
     the preservation ones;
   - where the ownership table names an adopter destination, one assertion finds
     the named rule in that seed file by distinguishing token, recorded red first —
     the link criteria count links, so deleting a link rather than inlining the
     rule passes them;
   - **at least one assertion in `tests/roster/test_conventions_retirement.py`
     names operative content from the moved section and finds it in the
     destination.** Without it a task goes green by deleting the section, since
     deletion satisfies an empty-discovery check perfectly.
   - **The red is produced by stripping, not by timing.** Run that assertion
     against a copy of the destination with the named content removed and record
     the failure, naming the test node and the expected failure identity. This is
     the form AC8 already uses for the credential contract. Do not rely on the
     pre-move destination being red: a destination is often the topic's natural
     owner and already states the rule, so a red-before-the-move requirement is
     unobtainable for much of this plan and would block the task rather than prove
     anything.
   - Where the destination already holds the named content in visible prose, that
     is a finding about the move, not a failure: record it as an already-present
     duplicate under step 1's recorded-reason seam, and point the assertion at
     content from the same section the destination does not hold.

   Which tokens the preservation assertion names is an execution-time choice. That
   it exists, and that its red was produced by stripping the destination, is not.

Destination headings are chosen during execution. The plan fixes which file owns a
section, because that is a design decision; it does not fix the heading text,
because the destination's existing structure decides it and only the real file can
show that. Where `notes/anchor-map.txt` names a directory rather than a file, the
owning task writes the selected file and heading back into that row before AC6 is
evaluated.

## Constraints

**Every commit in this changeset carries an `Engine-Change-RFC:` trailer.**
`tools/lint-catalogue-curation-guard.py` protects all of `packages/agentbundle/`
outside `agentbundle/build/recipes/` and any `/tests/` path, and it runs as a step
of the `build-check` chain (`tools/repo/build_gate_chain.py:336-339`) that T25 and
T26 both require. T3 edits `catalogue_tooling/lint.py` and T25 edits
`self_host.py`, so the guard fires; `has_exemption` searches the changeset's commit
messages for that trailer. Value it under `packs/AGENTS.local.md:24` — an existing
engine or credbroker-scoped RFC reference, or the literal `n/a — <reason>` form.
Never invent an ordinal.

T3 and T25 also decide whether their `agentbundle/` edits constitute an engine
change requiring matching `pyproject.toml` and `agentbundle/version.py` bumps
(`packs/AGENTS.local.md:22-23`), and record the verdict. That rule is explicitly
not machine-enforced, so nothing catches a wrong answer.

[`notes/ac2-scan.sh`](notes/ac2-scan.sh) is the single executable form of the
exclusion predicate — historical records and projection targets. Step 2 discovery,
step 4 checks and the AC2b guard all invoke it unchanged, so the enforced domain
cannot drift from the criterion's prose. AC2c is its canary.

Two baselines derived 2026-09-14 record what it returned, for comparison rather
than as a domain: [`notes/consumer-inventory.txt`](notes/consumer-inventory.txt)
and [`notes/anchor-inventory.txt`](notes/anchor-inventory.txt). Each records what
its command returned on that date; the command, not the tally, is the authority.
[`notes/anchor-map.txt`](notes/anchor-map.txt) records which file owns each anchor;
rows are completed with the chosen heading during execution, and AC6 compares
against the completed rows.

Every new guard lands in `tests/roster/test_conventions_retirement.py`; repo-level
coverage belongs in the roster suite, not a pack test. Every task writes that one
module, so the task chain is **linear**: a shared write target with no ordering is
how two tasks silently overwrite each other, and this plan has exactly one.

Section ownership. Each section has **two** destinations, because this document
serves maintainers and adopters differently:

- **Repo destination** — where the maintainer-facing text lives.
- **Adopter destination** — a path inside the installed scaffold. Where an adopter
  needs the rule, it is **inlined in the README of the directory it governs**, so
  the guidance travels with what it applies to. Core already seeds a README in
  `docs/architecture/`, `docs/product/`, `docs/knowledge/` and `docs/specs/`, so
  those homes exist. Where the content is about authoring this catalogue, the
  destination is `none` and the seed reference is deleted with a recorded reason.

The installed set is `tests/fixtures/install_snapshot/core.paths.txt`. It carries
no `packs/`, no `guides/`, no `packages/`, no `CONTRIBUTING.md`, and no
`docs/adr/` or `docs/rfc/` — the last two are governance-extras' generated indexes.

| Source section | Repo destination | Adopter destination |
| --- | --- | --- |
| § Document hierarchy | `docs/README.md` | **new** seeded `docs/README.md` — the doc tree explained where a reader first enters `docs/` |
| § Document lifecycle | `docs/README.md` | the living / frozen / governance rule in seeded `docs/README.md`, cross-referenced from `docs/product/README.md` in place of its link out |
| § 1 Charter | deleted | the revision rule inlined in seeded `docs/CHARTER.md`, beside the mandate it governs |
| § 2 ADR | `guides/governance-extras/how-to/new-adr.md` | none — `docs/adr/` is governance-extras' seeded index |
| § 3 RFC | `guides/governance-extras/how-to/new-rfc.md` | the minimum lifecycle and the no-RFC-process fallback inlined in seeded `docs/CHARTER.md`, where the RFC mandate already sits |
| § 4 Specs and Plans, all subsections | `packs/core/.apm/skills/new-spec/` | the spec / plan distinction and the status vocabulary in seeded `docs/specs/README.md`, replacing its link; a seed cannot link to an adapter-specific skill path |
| § 5 wrapper and its living-layer intro | `docs/README.md` | the living-layer definition folded into `docs/README.md`'s lifecycle rows; `guides/` is named there as an area an adopter adds |
| § 5a architecture | `docs/architecture/README.md` | seeded `docs/architecture/README.md` |
| § 5b product | `docs/product/README.md` | seeded `docs/product/README.md` |
| § 5c guides | the four Diátaxis authoring contracts and the link-out discipline to `guides/_shared/`; the completion obligation to the `work-loop` Finish checklist | none — no `guides/` path is installed |
| § Repository work intake index | `packs/core/.apm/skills/work-intake/` | the rule that `workspace.toml` is a lifecycle index and not a second requirements store, in seeded `docs/specs/README.md` |
| § Knowledge base | the maintainer prose, including the `session-start.py --show-knowledge` behaviour, to `packs/core/.apm/skills/work-loop/references/` | the kinds and their glob scoping in seeded `docs/knowledge/README.md` |
| § How we do non-trivial work | split by genre across `guides/core/` and `packs/core/.apm/skills/work-loop/references/` | none — the `work-loop` skill ships the mechanics and carries its own rationale |
| § Pack source-of-truth split | `docs/architecture/pack-layout.md` | none — describes authoring this catalogue; an adopter has no `packs/` |
| § Credentialed skills | `guides/credential-brokers/how-to/add-a-credentialed-skill.md`, which already carries the contract | none — no `guides/` path is installed |
| § Scaling profiles | `CONTRIBUTING.md` | none |
| § Common rationalizations, § When this file is wrong | deleted | none — root `AGENTS.md` already tells an agent to report stale instructions rather than work around them |
| The unheaded Skills paragraph | `guides/_shared/how-to/author-a-skill.md` | none |
| § Commits, § Pull requests, § Privacy | root `AGENTS.md` | seeded `AGENTS.md` |

`docs/README.md` is the one new file this change creates. It is the natural home
for the hierarchy: a reader entering `docs/` needs to know what belongs where
before they need any single directory's rules. Creating it adds an installed path,
so `core.paths.txt` and the install snapshot move with it.

Every seed that cites the retired document is resolved by inlining the rule in the
seed that governs it or by deleting a catalogue-authoring note — never by linking
out of the scaffold.


The seed files citing the retired path are what an adopter would see break.
`notes/consumer-inventory.txt` is the dated inventory; the live set is whatever
`notes/ac2-scan.sh` reports, because a list written here goes stale as the work
lands. Every one is resolved by inlining the rule in the seed that governs it
or by deleting a maintainer-only note — never by linking out of the scaffold.

`tools/lint-agents-md.py` owns the seed line cap, and the cap rises by whatever
the relocated rules need. The linter is the statement of what fits; naming the
value here would date it inside this very change, which is what happened to the
figure this sentence replaced.

## Durable-output map

| Spec durable output | Tasks |
| --- | --- |
| Current architecture | T2, T3 |
| Maintainer procedure | T4, T6, T8 |
| Interface compatibility | T1 |
| Decision rationale | T5, T7, T8 |
| Release history | T11 |
| Verification mechanism | T0 |

## Design (LLD)

### Design decisions

Each destination is the artifact already cited as that surface's owner.
`new-spec/SKILL.md:330` and `:350` already cite "CONVENTIONS § 4 *Contracts*",
so `new-spec` owns every §4 subsection including "Low-level design lives in the
plan" and "Contract vs. construction tests". §5c's completion obligation ("the
spec workflow is not done until those are updated") is a completion gate, so it
lands in the `work-loop` skill's Finish checklist where a gate reads it.

§ How we do non-trivial work is split by Diátaxis genre rather than moved whole:
`guides/core/how-to/plan-and-execute-non-trivial-work.md:20` declares itself
task-oriented and routes rationale to `../explanation/core-pack.md`, so the "why"
half goes to the explanation and the model-selection reference goes to the
`work-loop` references.

§ Pull requests' tail-triage block is deleted, not relocated: `work-loop/SKILL.md`
already states it, and that copy is the one the loop reads.

### Dependencies & integration

No new dependency. Code changes are confined to emptying one tuple in
`self_host.py`, removing one dict entry in `catalogue_tooling/lint.py`, and
amending the tests that read them.

## Tasks

### T0: Build the guard module, anchor resolver and canary

**Depends on:** none

**Verification mode:** TDD

**Section:** none — this task moves no prose
**Destination:** `tests/roster/test_conventions_retirement.py`

**Tests:**
- The resolver reads `notes/anchor-map.txt` and `notes/anchor-inventory.txt` and resolves each recorded use's mapped destination file and heading. No repository tooling resolves a Markdown anchor today, so this is construction, not reuse.
- **Recorded red against the current tree**, with the failure naming the unresolved uses and the test node it came from. A resolver that has never been red cannot be trusted to red later.
- **Positive control**: the same resolver against a fixture anchor that does resolve returns green, so a resolver red because it crashes is distinguishable from one red because the work is undone.
- The canary: the live `notes/ac2-scan.sh` matches the digest recorded in this module. Covers AC2c. A class-by-class check cannot see a pathspec added after it was written, and one added exclusion shrinks every later task's discovery domain.
- A test asserts this module invokes `notes/ac2-scan.sh` rather than restating its pathspecs — a second copy of the predicate is how the guard and the criterion drift apart.

**Approach:**
- Write the module. It is the only home for this spec's guards, which is why it comes first and why the chain is linear.

**Done when:** every test in this task's `Tests:` block is green.

### T1: Raise the seed AGENTS.md line cap

**Depends on:** T0

**Verification mode:** TDD

**Section:** none — policy only
**Destination:** `tools/lint-agents-md.py`

**Tests:**
- `python tools/lint-agents-md.py` runs clean.
- The raise is sized from the measured source material, not an estimate: the
  promoted prose exists today in `docs/CONVENTIONS.md` and the repo's own
  `AGENTS.md`, so the added line count is measurable before any of it moves.
  Record the measurement.
- **The headroom condition itself is checked at T8**, after the last seed edit.
  At T1 the accumulated content does not exist, so any cap above the current
  count passes and the rest would be graded from the implementer's own estimate.

**Approach:**
- Raise `MAX_SEED_LINES`. This is a policy edit with no content, deliberately separate so it is reviewable on its own terms rather than arriving inside a prose diff.
- Anchor it: `docs/product/research/agents-md-size-survey.md` Finding 5 holds that a numeric size budget decays as a claim and Finding 9 traces the line-budget heuristic to an unreplicated community source. The cap is adjustable, not load-bearing.

**Done when:** every test in this task's `Tests:` block is green.

### T2: Seat the session-priming rules in both AGENTS.md files

**Depends on:** T1

**Verification mode:** TDD

**Section:** § Commits, § Pull requests (questions 1-4), § Privacy
**Destination:** root `AGENTS.md` and `packs/core/seeds/AGENTS.md`

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_conventions_retirement.py` asserts the Conventional Commits type list, the four pull-request question texts, and the privacy rule are present in both files by distinguishing token within the governing section, recorded red first. Covers AC4 and AC5.
- `packs/core/tests/pack/test_razor_guidance.py` and
  `tests/roster/test_razor_guidance_repository.py` stay green. Both count numbered
  rungs across the **whole** file and require exactly seven; four numbered
  pull-request questions would make eleven. Render the questions so the
  line-initial-digit pattern does not match, or reconcile both guards without
  narrowing their whole-file reach — that reach is what detects a second ladder,
  which is why they exist.

**Approach:**
- Run the procedure.

**Done when:** every test in this task's `Tests:` block is green.

### T3: Create docs/README.md as the doc map

**Depends on:** T2

**Verification mode:** TDD

**Section:** § Document hierarchy, § Document lifecycle, and the § 5 wrapper
heading with its living-layer intro — the wrapper defines `docs/architecture/`,
`docs/product/` and `guides/` as the living layer, and T3 is the only task that
writes its destination
**Destination:** new `docs/README.md`, seed and repo

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_adapt_reference_architecture.py` re-pointed at
  `docs/README.md`, recorded failing when the `reference.md` seating is stripped.
  The seating is this task's content, not T9's.
- `tests/roster/test_conventions_retirement.py` asserts seeded `docs/README.md` names each docs area core seeds with what belongs there and its lifecycle class, carries the three lifecycle classes and their maintenance rules, and carries the adopter-extension placeholder. Recorded red before the file exists. Covers AC15 and AC18.
- The same suite asserts the living-layer definition from the § 5 wrapper resolves
  in both of that row's declared destinations — one preservation assertion per
  destination, recorded red first. A row with a destination and no owning task is
  the shape that let T19 and T20 drop a half each.
- `agentbundle catalogue lint` accepts the new seed. Covers AC19.
- `tests/roster/test_install_snapshot.py` passes with the path added. Covers AC16.

**Approach:**
- Run the procedure.
- Write the map: one row per seeded area — `architecture/`, `product/`, `specs/`, `knowledge/` — modelled on the repo's own § Documentation table but scoped to what core installs.
- Declare the seed in `_SEEDS_REQUIRED_PLACEHOLDERS` (`packages/agentbundle/agentbundle/catalogue_tooling/lint.py`). Every seed declares a shape there or the lint rejects it as unknown, fail-loud. The seeded rows are prefilled, so the declared marker covers only the adopter-extension row. This is the dict a later task removes the retired seed's entry from.
- Add the path to `core.paths.txt` and the install snapshot. This is the one new file the change creates and the only place the installed path set grows.

**Done when:** every test in this task's `Tests:` block is green.

### T4: Promote § Documentation into the seed

**Depends on:** T3

**Verification mode:** TDD

**Section:** the repo's own § Documentation table, adapted
**Destination:** `packs/core/seeds/AGENTS.md`

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_conventions_retirement.py` asserts the seed carries a `## Documentation` section routing to `docs/README.md`. Covers AC17.
- The same suite asserts that table names no path absent from `tests/fixtures/install_snapshot/core.paths.txt`. Covers AC20's scoping half — copying the repo's table verbatim would ship `docs/adr/`, `docs/rfc/`, `guides/` and `ARCHITECTURE.md` as dangling references.
- This task's preservation assertion names the two universal rows as the operative
  content the seed must hold: that a repeating agent workflow lives in its own
  `SKILL.md`, and that a mechanically knowable fact lives in code, schema,
  manifest, test or linter. Covers AC20's row half — once `docs/README.md` is
  installed, a single-row table satisfies both other predicates.

**Approach:**
- Run the procedure.
- Place it after § Rule lookups, as in the repo's own file.
- Amend the contracts this edit breaks, in this step: `packs/core/tests/pack/test_repository_context_seed.py`
  pins the seed's exact heading set and requires the "optional starting point"
  text this task replaces, and `packs/core/tests/pack/test_work_intake_surface.py`
  pins the seed's relative-link set. Neither contains a `CONVENTIONS` token, so
  no discovery form in this plan surfaces them.
- Carry over the two universal rows unchanged: a repeating agent workflow lives in its own `SKILL.md`, and a mechanically knowable fact lives in code, schema, manifest, test or linter. Both stop an agent hunting documentation for facts code owns.
- Replace the seed's line-64 pointer to the retired file. That line is currently its only reference to anything under `docs/`.

**Done when:** every test in this task's `Tests:` block is green.

### T5: Promote the development-workflow rules into the seed

**Depends on:** T4

**Verification mode:** TDD

**Section:** the repo's four § Development workflow bullets
**Destination:** `packs/core/seeds/AGENTS.md`

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_conventions_retirement.py` asserts the seed states, under § Development workflow, that changes are scoped precisely with conflicts surfaced before building, that destructive or irreversible operations need confirmation, that a new top-level directory goes through the repository decision process, and that unrelated discoveries stay out of the current change. Recorded red first. Covers AC21.

**Approach:**
- Run the procedure.
- Keep the seed's existing `when installed` hedge on the `work-loop` skill: an adopter may not have the pack.

**Done when:** every test in this task's `Tests:` block is green.

### T6: Promote the coding-convention rules into the seed

**Depends on:** T5

**Verification mode:** TDD

**Section:** three repo-only § Coding conventions rules
**Destination:** `packs/core/seeds/AGENTS.md`

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_conventions_retirement.py` asserts the seed states that changed code gets types and docstrings with crossed boundaries validated, that a new dependency is recorded in the owning package instructions or an ADR before it is added, and that a guidance-versus-code conflict is never silently resolved. Recorded red first. Covers AC22.

**Approach:**
- Run the procedure.
- Keep the seed's existing framework-primitives rule, which is stronger for an adopter than the repo's equivalent.

**Done when:** every test in this task's `Tests:` block is green.

### T7: Promote the security and stale-instruction rules into the seed

**Depends on:** T6

**Verification mode:** TDD

**Section:** the repo's never-commit rule and its report-stale rule
**Destination:** `packs/core/seeds/AGENTS.md`

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_conventions_retirement.py` asserts the seed states that credentials and personal information are never committed with generic placeholders used in repository artifacts, and that stale or conflicting instructions are reported rather than worked around. Recorded red first. Covers AC23.

**Approach:**
- Run the procedure.
- Leave the blessed-helpers list out: it is repo-specific. Leave the slot for an adopter to fill.
- Amend `packs/core/tests/pack/test_repository_context_seed.py`'s heading set for
  the sections this task adds.

**Done when:** every test in this task's `Tests:` block is green.

### T8: Trim the seed's recommended-additional-guidance comment

**Depends on:** T7

**Verification mode:** TDD

**Section:** none — the seed's own trailing comment
**Destination:** `packs/core/seeds/AGENTS.md`

**Tests:**
- `tests/roster/test_conventions_retirement.py` asserts the comment no longer offers `Documentation`, `Security considerations` or `Scoped instructions`, and still offers `Repository structure`. Covers AC24.
- `python tools/lint-agents-md.py` reports `packs/core/seeds/AGENTS.md` within
  `MAX_SEED_LINES` with every T2-T8 addition present. This is the task where the
  cap raised in T1 is actually tested; an insufficient cap would otherwise surface
  only at T25's `make build-check`, after every seed edit has landed.

**Approach:**
- The comment lists optional sections awaiting a trigger. T4 through T7 promote three of them, so continuing to offer them would invite an adopter to add what they already have.
- Amend `packs/core/tests/pack/test_repository_context_seed.py`'s backticked-name
  assertions, which today require the promoted names to remain in this comment.

**Done when:** every test in this task's `Tests:` block is green.

### T9: Re-home § 5a into the architecture README

**Depends on:** T8

**Verification mode:** TDD

**Section:** § 5a
**Destination:** `docs/architecture/README.md` and its seed twin

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_adapt_reference_architecture.py` re-pointed at the destination, recorded failing when the `reference.md` seating is removed.

**Approach:**
- Run the procedure.

**Done when:** every test in this task's `Tests:` block is green.

### T10: Re-home § 5b into the product README

**Depends on:** T9

**Verification mode:** TDD

**Section:** § 5b
**Destination:** `docs/product/README.md` and its seed twin

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_conventions_retirement.py` asserts the seeded product README
  names § 5b's product-area ownership list — `intents/`, `briefs/`, `shaping/`,
  `findings/`, `initiatives/`, `research/` (`docs/CONVENTIONS.md:729-767`) — none
  of which the seed holds today. The living-docs rule the seed already states at
  `:3-6` and `:30-33` is recorded as an already-present duplicate rather than
  asserted.

**Approach:**
- Run the procedure.
- Replace the seed's link out with a cross-reference to `docs/README.md`.

**Done when:** every test in this task's `Tests:` block is green.

### T11: Re-home § Pack source-of-truth split

**Depends on:** T10

**Verification mode:** TDD

**Section:** § Pack source-of-truth split and its two sub-sections
**Destination:** `docs/architecture/pack-layout.md`

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_conventions_retirement.py` asserts the destination states the Projected-versus-Manual classification and the edit-the-upstream-then-`make build-self` rule, each recorded red first. Naming the content is what stops a freely chosen token discharging the section.

**Approach:**
- Run the procedure.
- The seeded architecture README's note is **deleted, not re-pointed**: it describes authoring this catalogue and an adopter scaffold has no `packs/`.

**Done when:** every test in this task's `Tests:` block is green.

### T12: Re-home § 2 ADR

**Depends on:** T11

**Verification mode:** TDD

**Section:** § 2 ADR
**Destination:** `guides/governance-extras/how-to/new-adr.md`

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.

**Approach:**
- Run the procedure.

**Done when:** every test in this task's `Tests:` block is green.

### T13: Re-home § 3 RFC and seat its minimum lifecycle

**Depends on:** T12

**Verification mode:** TDD

**Section:** § 3 RFC
**Destination:** `guides/governance-extras/how-to/new-rfc.md`; the minimum lifecycle and the no-RFC-process fallback into seeded `docs/CHARTER.md`

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_conventions_retirement.py` asserts the RFC lifecycle states that `rfc-status/SKILL.md` cites resolve in the guide, and that seeded `docs/CHARTER.md` states the minimum lifecycle and the fallback. Recorded red first.
- This is what stops the retirement leaving an installed mandate with no installed definition: seeded `docs/CHARTER.md` and `docs/product/roadmap.md` order an RFC, and `docs/rfc/` is not a core install path.

**Approach:**
- Run the procedure.

**Done when:** every test in this task's `Tests:` block is green.

### T14: Seat the charter revision rule

**Depends on:** T13

**Verification mode:** TDD

**Section:** § 1 Charter
**Destination:** seeded `docs/CHARTER.md`

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_conventions_retirement.py` asserts seeded `docs/CHARTER.md` states the revision rule beside the mandate it governs, recorded red first.

**Approach:**
- Run the procedure.

**Done when:** every test in this task's `Tests:` block is green.

### T15: Re-home § 4 in full

**Depends on:** T14

**Verification mode:** TDD

**Section:** § 4 and all four of its subsections
**Destination:** `packs/core/.apm/skills/new-spec/`; the adopter half into seeded `docs/specs/README.md`

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_conventions_retirement.py` asserts the spec-metadata vocabulary, the plan-owns-LLD rule, the contract-versus-construction-test distinction, and the `contracts/<type>/` convention each resolve in the skill destination, and that seeded `docs/specs/README.md` states the spec/plan distinction and the status vocabulary rather than linking out. Four subsections move and a prose move can drop one.
- The task writes the file and heading it chose back into the `#4-specs-and-plans--docsspecsfeature` row of `notes/anchor-map.txt` before AC6 is evaluated.

**Approach:**
- Run the procedure.

**Done when:** every test in this task's `Tests:` block is green.

### T16: Split § How we do non-trivial work by genre

**Depends on:** T15

**Verification mode:** TDD

**Section:** § How we do non-trivial work, including § Supervisor mode,
§ Enforcement and § Model selection. **Excluding** § Knowledge base, owned by T20,
and the unheaded Skills paragraph at `docs/CONVENTIONS.md:1291-1300`, owned by
T22 — step 1's "every subsection" rule would otherwise claim both, and this task
runs first, leaving their recorded-red assertions unobtainable.
**Destination:** rationale to `guides/core/explanation/core-pack.md`, procedure to the core how-to, reference to `packs/core/.apm/skills/work-loop/references/`

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_conventions_retirement.py` asserts the explanation destination states why the loop exists and why the retry cap pauses for replanning rather than completing intent, recorded red first.
- The same suite asserts `work-loop/SKILL.md` is the only live source carrying the full tail-triage definition — thresholds with their consequence. Bounded restatements of the vocabulary elsewhere stay legal.

**Approach:**
- Run the procedure.
- Delete the tail-triage and bundled-fixes prose; `work-loop/SKILL.md` owns it.
- Write the chosen file and heading back into the `#supervisor-mode` and `#model-selection` rows of `notes/anchor-map.txt`.

**Done when:** every test in this task's `Tests:` block is green.

### T17: Re-home § Credentialed skills

**Depends on:** T16

**Verification mode:** TDD

**Section:** § Credentialed skills, including § The argv ban and § Corporate-network requirements
**Destination:** `guides/credential-brokers/how-to/add-a-credentialed-skill.md`

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_credential_broker_contract_docs.py` re-pointed at the
  destination, asserting the four broker ids and `metadata.auth`. Covers AC7.
- The same assertion run against the destination with the broker list stripped,
  and the failure recorded. Covers AC8. The how-to already states these, which is
  why the red comes from stripping rather than from the pre-move state.

**Approach:**
- Run the procedure.
- The how-to already states `metadata.auth`, the four broker ids and the argv ban,
  and `author-a-skill.md` routes authors there — so this is a consolidation into an
  existing owner, not a new home. Relocate only what the how-to does not already
  hold, and record the rest as already-present duplicates.
- `packages/credbroker/README.md` is not the destination. An earlier draft named it
  on a citation that does not exist.

**Done when:** every test in this task's `Tests:` block is green.

### T18: Re-home § Repository work intake index

**Depends on:** T17

**Verification mode:** TDD

**Section:** § Repository work intake and lifecycle index
**Destination:** `packs/core/.apm/skills/work-intake/`; the index rule into seeded `docs/specs/README.md`

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_conventions_retirement.py` asserts the workspace-entry field list resolves in the skill, and that seeded `docs/specs/README.md` states that `workspace.toml` is a lifecycle index and not a second requirements store. Recorded red first.

**Approach:**
- Run the procedure.

**Done when:** every test in this task's `Tests:` block is green.

### T19: Re-home the § 5c completion gate

**Depends on:** T18

**Verification mode:** TDD

**Section:** § 5c
**Destination:** the completion obligation to the `work-loop` skill's Finish
checklist; the four Diátaxis authoring contracts and the link-out discipline to
`guides/_shared/`. Both halves, because the section carries more than the
completion sentence and an unmapped remainder is deleted rather than disposed.

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_conventions_retirement.py` asserts the shipped-feature documentation completion obligation resolves in the Finish checklist, recorded red first — a completion gate reads it there, which is the point of moving it.
- The same suite asserts the four Diátaxis authoring contracts and the link-out
  discipline resolve in `guides/_shared/`, recorded red first.
- `tools/test_workspace_status.py` passes. Its `_WORK_LOOP_FINISH_HASH` pins a
  content hash over the Finish-checklist window this task edits, and it contains
  no `CONVENTIONS` token so no discovery form surfaces it. Reconcile the changed
  content, then update the constant with its explanatory note, in this step —
  the pin's own comment requires exactly that order.

**Approach:**
- Run the procedure.

**Done when:** every test in this task's `Tests:` block is green.

### T20: Re-home § Knowledge base

**Depends on:** T19

**Verification mode:** TDD

**Section:** § Knowledge base
**Destination:** the kinds and their glob scoping to seeded
`docs/knowledge/README.md`; the maintainer prose, including the
`session-start.py --show-knowledge` behaviour, to
`packs/core/.apm/skills/work-loop/references/`

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_conventions_retirement.py` asserts the seeded README states the pattern, gotcha and antipattern kinds and their glob scoping, recorded red first.
- The same suite asserts the `work-loop` references state the
  `session-start.py --show-knowledge` behaviour, recorded red first.

**Approach:**
- Run the procedure.

**Done when:** every test in this task's `Tests:` block is green.

### T21: Re-home § Scaling profiles

**Depends on:** T20

**Verification mode:** TDD

**Section:** § Scaling profiles
**Destination:** `CONTRIBUTING.md`

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_conventions_retirement.py` asserts `CONTRIBUTING.md` states the scaling-profile names and their contributor ranges, recorded red first. Covers AC13.

**Approach:**
- Run the procedure.

**Done when:** every test in this task's `Tests:` block is green.

### T22: Re-home the unheaded Skills paragraph

**Depends on:** T21

**Verification mode:** TDD

**Section:** the unheaded Skills paragraph at `docs/CONVENTIONS.md:1291-1300`
**Destination:** `guides/_shared/how-to/author-a-skill.md`

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- `tests/roster/test_conventions_retirement.py` asserts the destination states the add-a-skill-after-three-repeats rule, recorded red first.

**Approach:**
- Run the procedure.
- This region has **no heading**, so scope it by line range. `author-a-skill.md` cites it as "§ Skills" and a heading-based sweep skips it silently.

**Done when:** every test in this task's `Tests:` block is green.

### T23: Delete the unowned sections

**Depends on:** T22

**Verification mode:** TDD

**Section:** § Common rationalizations, § When this file is wrong
**Destination:** none — deleted

**Tests:**
- The task procedure's step-4 check for this section: the discovery forms return
  empty, every anchor the task owned resolves to its written-back heading, no seed
  the task touched links outside the installed scaffold, and the preservation
  assertion below was recorded red against the destination before the move.
- The task procedure's step-4 check confirms no consumer addresses either section before deletion.

**Approach:**
- Run the procedure.
- Root `AGENTS.md` already tells an agent to report stale instructions rather than work around them, which is the only part of § When this file is wrong that governs behaviour.

**Done when:** every test in this task's `Tests:` block is green.

### T24: Re-point the non-section consumers

**Depends on:** T23

**Verification mode:** TDD

**Tests:**
- `tests/roster/test_conventions_retirement.py` ranges over **every member of
  `notes/consumer-inventory.txt`** and asserts each carries either a recorded
  disposition or a recorded owning task. The domain is the fixed baseline AC2
  already uses — a record this task does not write — because a gate quantified
  over what the executor records is discharged by recording nothing.
- The ledger assertion is the control that catches deletion: the scan alone
  observes string removal, so deleting a sentence, a docstring or a test would
  otherwise pass, and § Boundaries forbids deleting a test rather than
  re-pointing it. AC2b is baseline-relative, so this task needs no exclusion
  list; the whole-tree emptiness checks belong at T25.
- The same suite asserts every member of
  `tests/roster/test_tdd_stub_lifecycle_contract.py`'s `live_sources` tuple exists
  before it is read, so a negative assertion over a vanished source cannot pass
  vacuously. Covers AC9.
- The same suite asserts every re-pointed test carries its recorded failure
  against a stripped owner.

**Approach:**
- Run the procedure's discovery over the whole tree rather than one section. What
  it returns after T1-T8 is the generic remainder: references that name the file
  without naming a section.
- Re-point each by its kind, which discovery makes visible:
  - **Agent briefs** — point them at `AGENTS.md` alone. Edit the brief in **its
    owning pack's** `.apm/agents/`, never `.claude/`, `.agents/` or `.codex/`.
    Briefs exist outside `core`: `packs/product-engineering/.apm/agents/discovery-lead.md`
    and `packs/release-engineering/.apm/agents/release-lead.md`, and neither pack is
    in the self-host recipe, so `make build-self` regenerates only the recipe's
    packs and the rest are edited at source with no regeneration step.
  - **Linter and tooling path lists** — remove the retired path from the list.
    `tools/lint-agents-md.py` and the `_SEEDS_REQUIRED_PLACEHOLDERS` map in
    `packages/agentbundle/agentbundle/catalogue_tooling/lint.py` are the two known
    at plan time; amend their dependent tests in the same step.
  - **Tests naming the path** — re-point at the new owner and record each failing
    against an owner with the relocated content removed. Never delete one.
  - **Repository chrome** — the README, `llms.txt`, the charters, `.gitattributes`,
    `workspace.toml`, issue and PR templates: repoint the link or drop the row.
  - **Prose about the document** — a consumer that discusses the conventions file
    as a concept rather than linking to it, where "re-point" has no meaning:
    `guides/_shared/how-to/author-a-skill.md`, `packs/governance-extras/DESIGN.md`,
    and doctrine prose in several `SKILL.md` files. Default disposition: restate the
    rule in place, or delete the sentence with a recorded reason. Without this kind
    the ledger gate is unsatisfiable, because AC2 still requires the scan to return
    these files empty.

**Done when:** every test in this task's `Tests:` block is green.

### T25: Delete the files and empty the projection allow-list

**Depends on:** T24

**Verification mode:** Goal-based check plus TDD

**Tests:**
- Existence check over both paths. Covers AC1.
- `test_self_host_check.py` amended to assert `PROJECTED_README_OVERRIDES` is
  empty. Covers AC3.
- `tests/roster/test_install_snapshot.py`'s
  `test_core_conventions_relative_links_resolve_after_scaffold` reworked to scan
  relative links across every Markdown file the core scaffold produces, rather
  than reading one named seed. Covers AC10.
- `sh notes/ac2-scan.sh` returns nothing, now that the deletion-bound consumers
  are amended and the source is gone. Covers AC2b.
- The T0 anchor resolver reports no live use still addressing the retired path.
  Covers AC6b. Both checks sit here rather than at T24 because T11 through T16 own
  live anchors that T24 cannot repair.

**Approach:**
- Delete both files; empty `PROJECTED_README_OVERRIDES` and update its comment.
- Update `tests/fixtures/install_snapshot/core.paths.txt`, `_support.py:170`,
  `test_pack_schema.py:127`, `test_install_seed_delivery.py`, and
  `test_install_cmd.py:656`.
- Run `make build-self` and commit the regenerated output.

**Done when:** every test in this task's `Tests:` block is green and
`make build-check` exits zero.

### T26: Release

**Depends on:** T25

**Verification mode:** TDD

**Tests:**
- `tests/roster/test_conventions_retirement.py` reads the `core` changelog entry's
  body and asserts it names the seed withdrawal; a heading check cannot observe
  this. Covers AC11.
- The same suite asserts the topmost free-standing `core` changelog heading carries
  the same version as both manifests. The repository's own coupling check
  (`tests/roster/test_workspace_status_projection.py:517-519`) sits outside
  `build-check`, so without this an entry headed with any other version satisfies
  AC11 and AC12 together.
- The same suite reads `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json` and asserts the versions are equal and
  greater than the previous release. Covers AC12.
- `make lint-ruff lint-mypy` and `make build-check` as plan verification; these are
  the repository's standing gates and carry no criterion of their own.

**Approach:**
- Bump `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` to
  `2.27.0`.
- Decide the `Highlights` disposition in this step, as `packs/AGENTS.local.md:30-42`
  step 4 requires: read the release diff, answer whether a pack consumer's
  capability changes, and either write the `### Highlights` bullets or record the
  verdict and its reason in the PR's *What did you not change that you considered?*
  answer. The `/now/` projection is a pure parser over the changelog bytes with no
  model in CI, so an unwritten block is silently a release the public page never
  mentions. Leave the verdict to execution; this change withdraws a seed from an
  installed pack, so it is not obviously a no. A minor bump keeps core inside the `^2.0` range that
  `governance-extras`, `iac-terraform`, `monorepo-extras` and
  `release-engineering` declare — `^2.0` has an exclusive upper bound of `3.0.0`
  (`version_ranges.py:103-110`), so a major would raise CAT-V-007 for all four
  (`verify.py:717-731`, `:592-601`) at the `catalogue-verify` step of
  `build-check` this task's own Done-when requires, and drag four unrelated packs
  into the change. The owner's reasoning is recorded in the spec's Assumptions.
- Add the free-standing `core` entry.

**Done when:** every test in this task's `Tests:` block is green.


## Rollout

A linear chain, T0 through T26. One concern per task, so each is independently
reviewable and an agent can be handed exactly one without reading the rest.

The chain is serial rather than waved because the tasks share write targets: every
guard lands in one new roster module, and T2 through T8 all edit
`packs/core/seeds/AGENTS.md`. A shared write target with no ordering is how two
tasks silently overwrite each other. Execution-time discovery keeps each step cheap
enough that serial costs little.

Three tasks carry no prose move and exist because they unblock the rest: T0 builds
the guards and proves the resolver red, T1 raises the seed cap as a policy edit
reviewable on its own terms, and T8 trims the seed's optional-sections comment once
its entries have been promoted. T3 creates the one new file. Nothing is deleted
until T25, so a revert before it costs nothing.

## Risks

- A relocated section loses an obligation no test named. Mitigation: T5, T7 and
  T8 assert over operative content (broker ids, field lists, the completion
  obligation) rather than section presence.
- The consumer inventory ages between authoring and execution. Mitigation: it is
  committed as a note and regenerable by the command recorded in the spec's
  Assumptions.
- Adopters keep an orphaned copy. Accepted and recorded in the spec.

## Changelog

- 2026-09-14 — Initial plan.
- 2026-09-15 — Split the AGENTS.md work into one concern per task. The old T1 had
  grown to carry the relocated rules, four promoted sections and a cap change in
  one file; it is now T1 through T8. Section relocations are one task each.
- 2026-09-14 — Round 4 follow-up: section ownership split into repo and adopter
  destinations after confirming the installed scaffold carries no `packs/`,
  `guides/`, `packages/` or `CONTRIBUTING.md`. Catalogue-authoring sections have
  their seed references deleted; every section an adopter needs is inlined in the
  README of the directory it governs, all of which core already seeds. AC14 guards
  the boundary, narrowed to the links this change touches.
- 2026-09-14 — Round 4: six working cheats closed (fail-first preservation, a
  canary on the scan script, visible-prose matching, heading write-back on every
  row, bound failure identity, and a real version baseline of 2.26.1); T9's gate
  widened past the four consumers T10 owns; a fifth disposition kind added for
  prose about the document; agent briefs sourced from their owning pack; and the
  unheaded Skills paragraph claimed by T8.
- 2026-09-14 — Round 3: one recorded scan predicate replaces three restatements;
  the pattern widened to catch the 17 sources citing the document without `.md`;
  T0 added to build the guard module and prove its resolver red; the chain
  linearised because seven tasks share one test module; step 4 gained a
  preservation assertion so deletion cannot pass as relocation.
- 2026-09-14 — Rebuilt against the measured consumer inventory and the
  12-anchor set after review round 1; section relocations now carry their own
  consumer re-pointing, and projections are regenerated rather than hand-edited.
