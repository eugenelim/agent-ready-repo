# Plan: design-handoff-read

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` § Security and authoring rules, which
  binds every pack, and root `AGENTS.md`'s non-waivable list. Analogous
  implementation: `packs/experience-design/.apm/skills/copy-direction/SKILL.md`
  steps 1, 3 and 6 — the only place in either pack that approves a resolved
  `output_dir`, re-canonicalizes a final target, surfaces a user-profile artifact
  for the user to confirm, and states an extraction contract over a loaded
  artifact. Second anchor:
  `packs/experience-design/.apm/skills/creative-direction/references/containment.md`,
  the module `design-output-addressing` shipped — its `## Known limits` section is
  where product belonging is recorded as having no discriminator, and its
  `## Slug validation` section is where refuse-do-not-repair is recorded. Third
  anchor: the three writers' templates
  (`creative-direction/assets/creative-direction-template.md`,
  `user-flow/assets/screen-brief-template.md`,
  `design-system/assets/token-taxonomy-template.md`), which fix the extracted sets
  the reference transcribes. Named uncertainty: the containment module's own
  one-line summary of the frontmatter contract is under-enumerated for these three
  artifacts, so the templates — not that summary — are the source for the sets.
  Its construction path is prose review, not a test: no gate reads pack
  instruction text. Named deviation: `frontend-engineering/SKILL.md` carries no
  containment prose at all, so this change authors the pattern into that pack for
  the first time rather than extending an existing step. That is compliance with
  a rule binding every pack, not a new design.

> **Plan contract:** implementation strategy. It may change substantively only
> while Status is `Drafting`. Execution observations belong in
> `notes/verification-ledger.md`.

## Approach

Six tasks. T1 comes first because the reference is the contract the read step
implements — authoring the step first would leave the contract to be inferred from
the step. After T2 the graph forks: T3 (fixture runs) and T4 (guides) both depend
on T2 and not on each other, and they own disjoint files — T4 owns both existing
guide pages, so the fork cannot collide. T5, the corpus-agreement test, needs T1
for the parseable contract and T3 for the written ledger its ledger floor scans.
T6 rejoins T3, T4 and T5.

In the review-decomposition scheme that sizes a task's review — the WIDE / MIXED /
DEEP axis, not the spec's `Shape:` field, which selects LLD scaffolding — this work
is **DEEP**. There is no mechanically uniform work: every task is either a
trust-boundary control or its verification.

## Constraints

- No gate reads pack instruction prose, so nothing here fails closed. That is why
  the spec's `Never do` makes an unpaired control a blocking condition needing a
  named owner waiver rather than an accepted gap.
- A single observed refusal from a non-deterministic agent establishes that a
  control fired once, not that it holds. The paired-run requirement is the
  honest ceiling available, and each recorded observation says which half it is.
- `design-output-addressing` has shipped, so all three artifacts have addresses
  and every fixture in T3 is stageable.
- Product belonging cannot be decided mechanically. The containment module that
  spec shipped states that no frontmatter field discriminates it, and the owner
  deferred adding one. So the read path takes operator confirmation instead, and
  the criteria say confirmation rather than confirmed belonging.
- A control that fires and then continues is a failure, not a pass. Recording
  "the refusal appeared" cannot distinguish the two, so every negative
  observation carries the terminal-effect statements the spec's Testing Strategy
  enumerates — that list is the one home, named here rather than counted.
- Four controls specified in rounds two and three were dropped in round four on the
  owner's decision, because prose cannot carry them. The spec's Follow-ons records
  which and why. Nothing in this plan should re-introduce them by implication.
- Real design artifacts do not conform to their writer templates. Measured on
  2026-09-18: all six `screen-flow-brief` files in `docs/design/` carry all nine
  of their template's sections, the one real `creative-direction` file carries
  none of its four, and no `token-taxonomy` file exists. The templates are
  scaffolds an author edits, so what is consumed keys on no section name.

## Construction tests

**One new automated test**, added on the owner's authorization after round three:
a corpus-agreement check, owned by T5. It reads every file under `docs/design/`
and asserts the contract in `references/design-handoff.md` classifies each one as
§ What is consumed requires. It is not a prose-presence checker — it asserts
agreement between a contract and a real tree, not that a sentence exists, and it
can fail. This repository has a recorded instance of the checker that cannot
fail, where a validator named `_validated_root` that validated nothing scanned
clean; the distinguishing question is whether a wrong contract makes it red, and
here it does.

No test asserts agent behaviour. Whether the agent refuses rather than repairs is
what T3's paired runs exist to observe, and a prose-presence test claiming to
prove it would certify phrasing.

Two static goal-based checks stand in where they can:

- **Reference content.** `references/design-handoff.md` carries the machine-readable
  per-artifact table, states the `type:`-mismatch-is-a-skip rule and the `type:`
  caveat, and names the `[design]` section without restating its base.
- **No duplicated base.** The reference states no base path of its own, resolving
  `[design]` by name. The companion check that it contains no `docs/` path literal
  is a **proxy** for the deferred `docs/ux` flip, not proof of the closeout
  condition: a duplicated adopter base need not contain `docs/`. Read the reference
  for the property; run the literal check for the flip.

Everything else is paired manual QA, recorded in the ledger.

## Durable-output map

| Durable output | Tasks | Evidence |
| --- | --- | --- |
| User-facing promise | T4 | Guide present, linked, `lint-guidebook-steps.py` exits 0 |
| Interface compatibility | T1, T5 | Reference names the section, states no base; the corpus test holds the contract to the real tree |
| Operations | T3 | Paired runs recorded per control |
| Release history | T6 | Topmost `frontend-engineering` entry names the new version |
| Reusable learning | T6 | `project-knowledge` receipt or recorded unavailability |
| Current product truth | T5 | The corpus test reds when the contract mishandles any file in `docs/design/` |

## Design (LLD)

### Design decisions

**Approval precedes confinement.** Without approving the resolved `output_dir`,
a prefix check confirms only that a path is under a root the adopter's config
named — and a hostile `agentbundle-layout.toml` in a cloned repository names any
absolute root. The two are one control in two parts, and this spec's first
criterion is the half that was missing.

**`type:` is a collision guard, not authentication.** It sits in the same
adopter-writable file as the content it labels, so anyone who can place the
artifact can set it. It usefully separates a token taxonomy from a direction doc;
it establishes nothing about provenance. The closed field set is the real control,
and the reference says so rather than letting a reader infer trust from a marker.

**The field set is the contract, so it lives in the reference.** A criterion
describing what an agent extracts at runtime cannot be falsified by reading
anything. A criterion requiring the reference to enumerate the set can.

**The extracted set is frontmatter plus an opaque body.** A section-name-keyed
contract would extract nothing from the only real aesthetic-direction artifact in
the tree, which is the artifact the Objective is about. Taking frontmatter as found
and the body whole is what the corpus supports.

**A `type:` mismatch is a skip, not a refusal.** `docs/design/` holds 28 distinct
`type:` values across its 38 typed files, including a `design-system` file under
`direction/`. Refusing on a foreign type would refuse this repository's own tree,
and the sibling `experience-status` skill already documents skipping a non-brief
file in that position.

**The slice ships what prose can carry, and names what it cannot.** Four
controls — a code-point denylist, value redaction, display bounds, and a
transcription predicate — were specified across rounds two and three and dropped
in round four on the owner's decision. Each needs a function, not a paragraph; the
spec's Follow-ons records the reasoning per control. Dropping them removed five of
round four's seven adversarial blockers and four of its five security blockers,
because the controls those findings attacked no longer exist. What remains —
resolution, approval, confinement, the `type:` filter, the bounds, the skip and
refusal states, and operator confirmation — are things an instruction can state and
a reader can check.

**Confinement is stated as a predicate, not as a preposition.** "Within the
approved root" means realpath equality or descendant on resolved path components.
A string prefix admits `/home/u/repo-backup/design` as within `/home/u/repo`, and
naming the predicate costs one sentence.

**A heightened root is the union, not either key alone.** Keying the per-artifact
confirmation on the configuration source misses a cloned repository whose
repo-root config names an absolute path outside the tree. Keying it on out-of-tree
misses the shared-vault case `packs/AGENTS.md` mandates, because a user-profile
root can resolve inside the repository tree. Both keys, or a mandated case goes
uncovered.

**The corpus test is the convergence mechanism.** Rounds one, two and three found
twenty, thirty and twenty-four findings, and the recurring class in each was a
hand-transcribed claim about the design artifacts that the real tree contradicts.
Another review round finds the next instance; it cannot fix the process. T5 reads
the real tree and reds when the contract mishandles any file in it.

**Bounds are stated with their provenance.** The values live in the spec's
§ The read bounds — one home, named from here rather than restated. Only the
matching-file count rests on a measurement, and it is a chosen ceiling over it; the
plan says so rather than letting "calibrated" cover all four.

### Interfaces & contracts

The read resolves `[design] output_dir` by name — the same section
`experience-design` declares — and reads three fixed paths beneath it. It is a
consumer of that section, not a declarer: the reference is named
`design-handoff.md` rather than `agentbundle-layout.md` precisely because in this
repository the latter name means the pack writes there, and the layout
conformance test reads only files with that name.

### Failure, edge cases & resilience

| Condition | Result |
| --- | --- |
| No `agentbundle-layout.toml`, or no `[design]` section | Named skip; canonical reference set used |
| Section resolves, no conforming artifact for any slot | Differently worded named skip |
| Root at or beneath a reserved tree | Named refusal, before any read; never confirmable |
| A directory component or artifact path resolving into a reserved tree under an approved root that merely contains one | Named refusal at that point, before the component's listing is surfaced or its depth counted |
| Repo-root value resolving outside the repository tree | Explicit confirmation before use; the root is then heightened |
| User-profile value | Approved against the declared absolute root; the root is heightened whether or not it resolves in-tree |
| Approval of the root refused or failed | Named refusal, before any artifact is read |
| Slug not matching `^[a-z0-9]+(-[a-z0-9]+)*$`, or over 64 characters | Named refusal before any path is composed; never sanitized, stripped, or replaced by a derived slug |
| No slug obtainable after elicitation | Named refusal; the step does not guess one |
| Artifact real path not equal to, or a descendant of, the approved root on resolved components | Named refusal; reports the resolved path |
| A file under a read path whose frontmatter `type:` is absent, unparseable, or not that path's literal | Not this artifact: skip the file, keep scanning |
| A frontmatter key a template declares but the file omits | Recorded absent; the artifact is still consumed |
| Heightened root, per artifact | Surface root, config file, relative path, source token, first heading and frontmatter; consume only on explicit confirmation |
| Confirmation missing or refused | Named refusal |
| Layout file unparseable; `[design] output_dir` missing, empty or not a string; a type-matched file unreadable; canonicalization raising, symlink loop included | Named refusal, not a skip |
| A bound in § The read bounds exceeded | Named refusal; surface which bound, evaluated in the order the criteria state |
| An entry whose resolution leaves the approved root during enumeration | Named confinement-failure refusal at that entry, before its listing is surfaced |
| Some slots filled, others with no conforming artifact | Named skip per empty slot; the canonical set fills those slots alone |

Every row naming a refusal ends the whole handoff read and halts the mode in a
named state, carrying the terminal effect the spec's Testing Strategy
enumerates — the canonical list this plan points at rather than restating. The skip
rows are the only ones reaching the canonical product-reference set: the two
directory-level skips for the whole read, and the per-slot skip for one slot.

**Product belonging is confirmed by the operator, never by a check.** Nothing in
the three artifacts discriminates a product: `slug` is documented as naming the
surface **or product** a direction serves and the system a taxonomy serves, the
screen brief carries no `slug` at all, the first heading may name either, and no
field is reserved for a product. The only honest options are to add a
discriminator — a writer-side change with a migration, deferred by owner decision —
or to show the operator what was found and let them decide. This slice takes the
second.

**What the operator is shown, and why it stops at the frontmatter.** The prompt
carries the approved root, the configuration file it was read from, the artifact's
`output_dir`-relative path, the configuration-source token, its first heading, and
its frontmatter. Not the body.

An earlier draft put the body in the prompt, on the argument that confirming
belonging over frontmatter alone asks the operator to judge on exactly the values
the spec has declared unable to judge. That argument is sound, and the first
heading is the repair for it — it is the line all three templates put a product
name in, it is one line, and it is now in the prompt. The body is not, because
including it made the confirmation worse rather than better: every real artifact
body exceeds the display bound that would have to bound it, so the operator would
have confirmed a fraction of what the emit step receives, which is a confirmation
that authorizes unseen content. Showing the whole body unbounded is the other
direction and is a prompt nobody reads. Making display and consumption the same
bytes needs one code path producing both, which is the follow-on.

**The root is in the prompt because a heightened root approves itself.** A
user-profile value is checked against a root declared in the same adopter-writable
file; a repo-root value pointing outside the tree is admitted on one confirmation.
Circular either way, as the shipped module records. The operator is the only thing
that can catch a root of `/`, and they cannot catch one they are not shown. That is
why the absolute-path ban is scoped to persisted artifacts rather than to the live
prompt; the shipped module makes the same trade for the same reason.

## Tasks

### T1: The handoff reference

**Depends on:** none

**Tests:**
- Goal-based: the reference's per-artifact table matches the spec's § What is
  consumed row for row — read path, required `type:` literal, frontmatter taken as
  found, body as one opaque block — and names the frontmatter marker as the one
  validated for the screen brief.
- Goal-based: that table is machine-readable — one markdown table with a fixed
  header, one row per artifact — so T5 parses the shipped reference rather than
  carrying its own copy of the contract. A test with its own copy would pass while
  the reference was wrong, which is the defect T5 exists to catch.
- Goal-based: the reference states that the step keys on no section name, reads
  raw text, discards HTML comments, extracts the first H1, and treats an
  instruction inside a body as content rather than an instruction to follow.
- Goal-based: the reference states that a `type:` mismatch on a path-matched file
  means not-this-artifact and is skipped, not refused.
- Goal-based: the reference resolves the `[design]` section by name.
- Goal-based: the reference states no base path of its own. Read for the property;
  the companion `docs/`-literal check below is a proxy for the deferred base flip,
  not proof of it.
- Goal-based: the reference contains no `docs/` path literal (a proxy, see
  Construction tests).
- Goal-based: the reference states that nothing in the three artifacts
  discriminates a product, so belonging is confirmed by the operator and never
  reported as mechanically confirmed.
- Goal-based: the reference names the spec's Testing Strategy terminal-effect list
  as the obligation every refusal carries, rather than restating its items.
- Goal-based: the reference states that a declared `type:` is a collision guard and
  not an authenticity claim, because it sits in the same adopter-writable file as
  the content it labels.
- Goal-based: the reference states the residual — a refusal cannot unread the
  bytes, and an adopter needing content never to enter the agent's context enforces
  that outside the agent.

**Approach:**
- Author `references/design-handoff.md` as the contract the read step implements:
  what is extracted from each of the three artifacts, what is discarded, what
  `type:` does and does not establish, where the section comes from, what the
  operator is shown for a user-profile artifact, and what every refusal forbids
  afterwards.
- Take the three required `type:` literals from the templates —
  `creative-direction`, `screen-flow-brief`, `token-taxonomy` — and nothing else.
  The reference names no section and no required frontmatter key beyond `type:`,
  because the corpus shows neither holds.
- State the collision the corpus shows: a foreign `type:` under a read path is a
  skip rather than a refusal. The `.handover.md` case needs no special rule —
  `user-flow` writes that sibling only when no design-tool MCP is present, the tree
  holds none, and the template ships no frontmatter, so the `type:` filter already
  skips it.
- State that the first `# ` heading is extracted for the operator to read while
  never being matched or compared, and that the first is taken when a file holds
  several.
- State the adopter-facing limit: these controls are agent instructions with no
  gate behind them, and an adopter needing a guarantee enforces confinement
  outside the agent.
- Name it for reading. `agentbundle-layout.md` means the pack writes there, and
  the layout conformance test keys on that filename.

**Done when:** all eleven checks pass against the file. T1 does not wait on T5 —
T5 depends on T1, not the reverse.

### T2: The read step

**Depends on:** T1

**Tests:**
- Goal-based: the step states every condition in the Design table above and its
  result. The check names the table rather than a count, so a row added later
  cannot leave the check reading as passed.
- Goal-based: the step sits ahead of the canonical product-reference set in the
  shared pre-flight, so the fallback is reached only from a skip.
- Goal-based: the step names its six refusals as the complete set, in the spec's
  vocabulary, binds each to the spec's terminal-effect list including the halt, and
  states which states reach the canonical set — the two directory-level skips, and
  a per-slot skip.
- Goal-based: the step states the bound evaluation order, the reserved-tree
  refusal, and the resolved-component comparison predicate.
- Goal-based: the step states every surfaced path as `output_dir`-relative plus one
  of the two configuration-source tokens.
- Goal-based: the step binds `<slug>` to the operator-named slug, eliciting it
  when absent, and resolves all three slots under it.
- Goal-based: every enumeration of the pre-flight's steps inside the pack and its
  guides resolves after the insertion. In `SKILL.md` those are the opening summary
  at `:10-11`, the pre-flight's own "Complete all four steps" count at `:55`, and
  the two "Run steps 1, 1b, 2, and 3" lines — `:286` under `### Mode: create` and
  `:313` under `### Mode: retrofit`; audit and verify carry no such line. Outside
  `SKILL.md` they are the pre-flight sequence in `JOURNEY.md:148`, the starter
  prompt and expected result in `pack.toml:39-40`, the pre-flight list in
  `guides/frontend-engineering/reference/frontend-engineering.md:21-22`, and the
  numbered walk in `guides/frontend-engineering/tutorials/scaffold-a-component.md`
  at `:47`, `:61` and `:173`.

**Approach:**
- Insert the step into the shared pre-flight, which all four modes run: approve
  `output_dir` — refusing a reserved tree — execute a real-path resolution of each
  artifact and read its output, filter by frontmatter `type:`, take operator
  confirmation under a heightened root, enforce the bounds in their stated order,
  then consume what § What is consumed names.
- Scope the criteria to that reach. The step is not create-mode-only: retrofit
  also emits committed code, and audit and verify read the same pre-flight, so the
  controls bind wherever the step runs.
- Fix every step-inventory back-reference the insertion falsifies in the pack, in
  the same edit that inserts the step. The two guide pages under
  `guides/frontend-engineering/` are **T4's**, not T2's — one owner per file, so the
  two tasks cannot edit the same lines on the fork after T2.
- State every surfaced path relative to `output_dir` plus one of the two
  configuration-source tokens, so no absolute home path can reach an artifact, the
  operator prompt, or the ledger.
- Word the two whole-read skips differently from each other, from the per-slot
  absence skip, and from each refusal, and make the unconfirmed-artifact refusal
  distinct from both the confinement refusal and the approval refusal. One
  confirmation-refusal vocabulary covers the approval step and the artifact step.

**Done when:** all seven checks pass and the step precedes the reference set.

### T3: Paired fixture runs

**Depends on:** T2.

**Tests:**
- Visual / manual QA, paired per control: a benign fixture holding a conforming
  artifact in each slot, then one fixture per control that must make it fire — a
  root at `.apm/`, a repo-root `output_dir` outside the tree whose confirmation is
  declined, a symlinked `direction/` resolving outside the approved root, an
  artifact carrying an embedded instruction, an artifact under a heightened root
  whose confirmation is refused, an unparseable layout file, a `[design]` section
  with no `output_dir` value, and a set breaching each bound.
- Visual / manual QA: no `[design]` section, then a directory with no conforming
  artifact in any slot, confirming the two skips read differently and each reaches
  the canonical set.
- Visual / manual QA: a directory holding a file under a read path with a foreign
  `type:` — the `design-system` case this repository's own `direction/` carries —
  confirming it is skipped and the read continues rather than refusing.
- Visual / manual QA: a partial tree with a conforming `tokens/<slug>.md` and no
  conforming `direction/<slug>.md`, confirming the direction slot falls back while
  the taxonomy is consumed.
- Visual / manual QA: at least one fixture breaching two adjacent bounds at once
  per adjacent pair in the stated order, so the negative half records which bound
  was reported rather than only that a bound fired.

**Approach:**
- Stage fixtures with an absolute `output_dir` pointed at a temporary tree, which
  is what makes the symlink and heightened-root cases stageable rather than
  hypothetical.
- Record, per run, the fixture, the observed output, and which half of the pair it
  is. Every negative run additionally records all five terminal-effect statements
  from the spec's Testing Strategy, each read off that run's own output. A run
  missing any of the five is re-run, not recorded.
- Redact before writing. The prompt under a heightened root shows the approved
  root, so the raw observed output carries the fixture's absolute path; replace it
  with a fixed token in the ledger entry. Root `AGENTS.md` puts a real home path in
  the non-waivable class, and a fixture root is a real path on the machine that ran
  it.
- Re-run every negative fixture after the last edit to the instruction text. A
  passing observation recorded against superseded prose is evidence about a control
  that no longer exists.
- A run that cannot be staged is a blocking condition needing a named owner waiver
  in the spec, not an unverified pass.

**Done when:** every control criterion has both halves recorded in the ledger
against the final instruction text, or a waiver recorded in the spec with its
owner.

### T4: Guide

**Depends on:** T2

**Tests:**
- Goal-based: `tools/validate_guides.py` and `tools/lint-guide-titles.py` exit 0
  against the new page — these are the two the owning `guides/AGENTS.md` names and
  the two that red when the page is wrong.
- Goal-based: `tools/lint-guidebook-steps.py` exits 0, recorded as covering nothing
  here: no page under `guides/frontend-engineering/` carries `order:` frontmatter,
  so it reports OK with or without the new file.
- Goal-based: the new guide is linked from `guides/frontend-engineering/README.md`.

**Approach:**
- Update the two existing guide pages the insertion makes stale, which T4 owns
  outright: `reference/frontend-engineering.md`'s pre-flight list and
  `tutorials/scaffold-a-component.md`'s numbered walk.
- Write `how-to/read-the-design-handoff.md`: what the agent reads, from where, what
  it ignores, what each skip and each refusal in the spec's closed set mean to a
  reader,
  and — stated plainly, because the Durable Outputs row promises an adopter knows
  the trust posture — that these controls are agent instructions with no gate
  behind them, naming what an adopter needing a guarantee does instead. Add its
  index row. `tools/check-guide-index.py` cannot observe page reachability, so the
  index row is checked by reading it, not by that tool.

**Done when:** the lint exits 0, the index row resolves, and both existing pages'
pre-flight enumerations match the inserted step.

### T5: The corpus-agreement test

**Depends on:** T1 for the parseable contract, and T3 for the written ledger the
ledger floor scans. The corpus and contract floors could run after T1 alone; the
ledger floor cannot be demonstrated against a file that does not exist yet, and a
floor that cannot be shown to red is not a floor.

**Tests:**
- Construction: the test reads every file under `docs/design/` and asserts the
  contract parsed from `references/design-handoff.md` puts each one in exactly one
  of four states — consumed, skipped as not-this-artifact, off every read path, or
  refused. "Off every read path" is its own state, not folded into the `type:`
  skip: conflating the two would let a widened read path still classify everything
  as skipped. The expected count is **per bound slug**, not over the slug union:
  of 42 files, `team-orientation` matches 7 and leaves 35 off-path, and
  `tech-site-amendment` matches 1 and leaves 41. The union figure of 33 is produced
  by no parametrized run and must not be asserted.
- Floor: the test fails when the parsed contract is empty, when the corpus walk
  finds no files, when no file lands in the consumed state, or when the parsed
  contract does not carry exactly three artifact rows with the read paths and
  `type:` literals § What is consumed fixes. A test that asserts nothing scans
  clean, which is the failure mode this task exists to prevent. The structural
  floor is also the only thing holding the `token-taxonomy` row: no corpus file
  carries that type, so dropping the row changes no classification.
- Ledger floor: the test fails when any recorded observation in
  `notes/verification-ledger.md` carries an absolute filesystem path, **and** when
  that ledger is absent, empty, or holds no recorded observation. Without the
  second half the assertion scans nothing and greens, which is the
  control-that-cannot-fail shape this whole task exists to prevent. That is also
  why T5 depends on T3: the ledger does not exist until T3's runs are recorded, so
  a T5 that landed first could not demonstrate the floor reds.
- Differential: prove it by mutation, not by assertion. Two mutations the current
  corpus witnesses **under the slugs this test binds** — flip the `type:` rule from
  skip to refuse, which reds on
  `docs/design/screens/team-orientation/operating-model-canvas-composition.md`
  (`type: canvas-composition`), the only path-matched type mismatch either bound
  slug reaches; and drop `screen-flow-brief` from the brief's required literal,
  which reds on all six conforming briefs. Restore and confirm green. A mutation
  the corpus cannot witness under a bound slug is not admissible as the
  differential arm — a witness off every read path changes no classification and
  greens either way, which is how the first draft of this arm was vacuous.

**Approach:**
- Home it at `tests/roster/`, anchored at `Path(__file__).resolve().parents[2]`.
  It cannot live in the pack suite: `tests/AGENTS.md` and
  `tools/test-lint-pack-test-boundary.py` forbid a pack test reading above its own
  pack, and `docs/design/` does not exist in an installed adopter tree, so the test
  would error or pass vacuously wherever the pack ships.
- Wire it to run on pull requests, which roster placement does not give for free:
  a step in `.github/workflows/build-check.yml` naming the file, and a matching
  `STEP_DISPOSITION` entry in `tools/lint-ci-parity.py` with
  `LOCAL("test-after-build-check")`. Without both it runs on no pull request and
  stays green by never executing.
- Parse the contract out of `references/design-handoff.md` — the machine-readable
  table T1 is required to emit — rather than restating it in the test. A test
  carrying its own copy would pass while the reference was wrong, which is exactly
  the drift this task closes.
- Bind `<slug>` explicitly. Classification depends on it and a test has no
  operator, so the test parametrizes over the slugs the corpus actually contains —
  `team-orientation` reaches the six briefs, `tech-site-amendment` reaches the
  direction artifact — and states the expected classification per file under each.
- Parse frontmatter with a safe loader. This is the one place the change reads
  adopter-authored metadata in code; `yaml.safe_load` or an equivalent, never
  `yaml.load`, so the repository's SAST leg has nothing to flag.
- Assert classification, never agent behaviour. The test decides what the contract
  says about a file; it says nothing about what an agent does with it.

**Done when:** the test passes against the current tree, each of the two mutations
reds it, each floor condition reds it, and `tools/lint-ci-parity.py` exits 0.

### T6: Release surface

**Depends on:** T3, T4, T5

**Tests:**
- Goal-based: `agentbundle catalogue verify --root .` exits 0, which owns the
  `pack.toml` / `plugin.json` version agreement.
- Goal-based: the topmost `frontend-engineering` changelog heading names its new version.
- Goal-based: the skill's `evals/evals.json` carries a case covering the handoff read.

**Approach:**
- Bump `frontend-engineering` (minor — a new reference, a new pre-flight step and
  a new pack test)
  in `pack.toml` and `plugin.json`; regenerate `marketplace.json` by self-host.
- Add the eval case `packs/AGENTS.md` requires of a non-cosmetic pack update, to
  the skill's existing eval surface rather than a new one.
- Route learnings through the `project-knowledge` seam.

**Done when:** the three checks pass and `git status` is clean.

## Rollout

No runtime component. An adopter with no `[design]` section sees the named skip and
the unchanged canonical reference list, which is the current behaviour — so a
frontend-only adopter is unaffected. An adopter with the design pack installed and
configured gains the handoff on upgrade.

## Risks

- **The controls cannot be verified beyond a paired run.** Accepted and stated:
  no gate reads pack prose. The mitigation is that the pairing is required rather
  than optional, and an unstageable case blocks on a named waiver.
- **A fixture cannot be staged honestly.** Most likely for the user-profile
  confirmation case, which needs a user-profile config pointing outside the
  repository. If it cannot be staged, the criterion is waived by a named owner,
  not quietly passed.
- **Operator confirmation is a weaker control than a discriminator, and is meant
  to be.** It moves the decision to someone who can make it instead of reporting a
  check that cannot. It does not stop an operator who confirms without looking,
  which is why the prompt shows the artifact's first heading and its frontmatter
  rather than only asking. The body is **not** shown: bounding it made the
  confirmation worse, because every real artifact body exceeds any bound short
  enough to read, and showing it unbounded is a prompt nobody reads. The first
  heading is the repair — it is the one line all three templates put a product name
  in, and it costs one line.
- **So the operator confirms less than the emit step consumes.** Stated rather than
  solved: making display and consumption the same bytes needs one code path
  producing both, which is the follow-on. What confirmation establishes today is
  that a human saw which artifact, under which root, with what declared metadata —
  not that they read everything that will reach the code.
- **No `token-taxonomy` artifact exists in any tree available.** The contract's
  third row is therefore unevidenced by classification: T5's corpus walk cannot
  exercise it, and its structural floor is what holds the row against being
  dropped or mistyped. The first taxonomy an adopter writes is what will test the
  contract's fit.
- **The four dropped controls leave a real gap until the follow-on lands.** Until
  an executable read path exists, an artifact body reaches the emit step with
  whatever it carries: no code-point normalization, no redaction, no bound on what
  an operator is shown of it. The controls that remain — approval, confinement, the
  `type:` filter, the read bounds, confirmation under a heightened root, and
  content-is-never-instruction — bound *which* files are read and *whether* a human
  saw them, not what is inside one. This is stated rather than closed because
  closing it needs code, and the spec's Follow-ons says so.
- **The bound values prove wrong in practice.** Only the matching-file count is
  measured, against one tree — this repository's. The per-file byte bound and the
  per-directory enumeration cap are chosen ceilings, and the depth follows from the
  read paths; § The read bounds holds the values and says which is which. If an adopter's legitimate
  tree exceeds any of them the surfaced bound tells them which, which is why the
  criterion requires naming it.

## Changelog

- 2026-09-18 — Pre-approval review round 6. Twenty-five findings raised, eleven
  blockers; twenty-four sustained, one refuted. The refutation matters as much as
  the sustains: "T3 stages no fixture for eight criteria" was refuted because T3's
  test and `Done when` are both stated universally over control criteria, and the
  spec-stage standard holds a finished edge-case matrix to be build-time guidance.

  The security lane's one blocker was the most consequential finding since round 3
  and was mine to have caught: `<slug>` is operator input that becomes three
  filesystem paths, and the spec carried **no validation of it at all** — no form,
  no length cap, no ordering, and no refuse-do-not-repair rule — while the shipped
  containment module two directories away carries exactly that rule, written
  against an observed run where an agent silently substituted a tidy slug and
  reported success. This spec cites that failure as the reason its terminal-effect
  list exists. The gap opened in round 4: shape validation was dropped for
  *frontmatter*, and the slug went with it even though it is operator input, not
  artifact content. A silently rewritten slug needs no traversal to do harm — it
  resolves inside the approved root, passes confinement, trips no heightening, and
  composes one product's direction with another's taxonomy, falsifying the
  guarantee § What is consumed makes. Now a control criterion, a failure-table row,
  and a T3 fixture pair.

  The closed refusal set was falsified by its own siblings: round 5 added a
  reserved-tree test on artifact paths and an enumeration-time confinement refusal,
  and neither was an instance of any of the five named members ("of the root", "on
  an artifact"). The set is now six, each stated to cover every point the control
  fires at, and the reserved-tree test applies wherever the confinement predicate
  does.

  Three findings were the same defect in the new test: T5's `type:`-flip mutation
  named a witness off every read path under both slugs T5 itself binds, so the arm
  greened either way — the second time a differential arm of mine has been vacuous;
  its off-path floor asserted 33, a slug-union figure no parametrized run produces
  (it is 35 and 41 per slug); and its ledger floor scanned a file T3 writes while
  T5 depended only on T1, so it could pass over nothing. All three are corrected
  against measurement, and T5 now depends on T3.

  One control could not fail: `lint-guidebook-steps.py` was T4's only mechanical
  check, and it treats a page as a step only when frontmatter carries `order:` —
  which no page under `guides/frontend-engineering/` does, so it reports OK with or
  without the new file. `validate_guides.py` and `lint-guide-titles.py`, the two the
  owning `guides/AGENTS.md` names, now carry the criterion.

  Also: the step-enumeration list missed the `Steps 1–3` heading and
  `token-architecture/SKILL.md`'s reference to a numbered step, and is now stated as
  known-sites-plus-sweep rather than a closed list; the out-of-tree residual was
  priced as costing a hostile clone nothing it already had, which was wrong — it
  grants unconfirmed reads *outside the repository* — and now says so; T1 gained two
  checks for the `[design]`-by-name criterion; T4 owns both existing guide pages
  outright so the post-T2 fork cannot collide; and four measurements were corrected
  against the tree, including the 4 KiB figure, which was 15–27% computed over the
  largest file in the whole tree and is 26.9–71.4% over the nine read-path bodies.
- 2026-09-18 — Pre-approval review round 5. Twenty-seven findings raised, five
  blockers; twenty-two sustained, five refuted. Blockers across the five rounds ran
  12, 15, 10, 12, 5, so the narrowing converged the review rather than only
  shrinking the spec. Two blockers were repaired: the corpus-agreement test was
  owned by T6 in five live sites and T5 in four, including two gate-read fields, so
  an implementer would have built it inside the release task; and two contract
  criteria requiring the reference to state the `type:` collision-guard caveat and
  the unread-bytes residual had no check in T1's closed seven, which its `Done when`
  made binding.

  The security lane's one blocker was a real hole: the bounds required checking each
  entry for a link during enumeration but never said what a found link *does*, and
  the confinement predicate reached only artifacts about to be read — so a symlinked
  `screens/<slug>/` would have been walked, its listing surfaced and its depth
  counted before anything tested it. The predicate now applies at every directory
  component as it is reached, and such an entry is a confinement-failure refusal
  there.

  Three repairs turned promises into checks or honest records. The ledger-redaction
  obligation was an implementer's promise; T5 now reds when any recorded observation
  carries an absolute path. T5's floors could not witness a change to the
  `token-taxonomy` row, since no corpus file exercises it; a structural floor now
  asserts the parsed contract carries exactly the three rows with their read paths
  and literals. And a fifth control — shape validation — had left the slice in round
  four without being recorded as dropped; it is now named with the other four, with
  the reason the corpus gave: real artifacts carry keys no template declares and omit
  keys every template does, so validating a shape the writer never promised refuses
  correct artifacts.

  Corrected measurements: the screen-brief template carries nine sections, not eight
  (`Done` sits inside the fenced block, and all six real briefs carry nine); the
  worst-case walk is 40,200 entries, not 40,201; the off-path corpus is exactly 33
  files; the criteria median across 471 specs is 13, not the mean 15.9 the Assumption
  had been reading as one, so this spec is about 2.5× the median rather than near it.
  Also: the reserved-tree test now applies to each resolved artifact path, not only
  the root; the guide must disclose what the slice does not inspect inside an
  artifact, which is the larger residual; the directory-level skip fires only after
  both branches of the resolution order have been tried; and the worktree-root
  determination is recorded as repository-controlled, making the out-of-tree key
  advisory against a hostile clone while the user-profile half of the union stands.
- 2026-09-18 — Pre-approval review round 4, and the owner's decision to narrow the
  slice. Round four raised 32 findings across the two reviewers, twelve of them
  blockers, and the blocker count across four rounds had gone 12, 15, 10, 12 — flat,
  against a spec that had grown from 207 to 623 lines with no implementation
  started. But round four's blockers were a single new class, distinct from round
  three's: controls specified in prose to a precision prose cannot carry. A
  code-point denylist that four rounds could not close and round four still found
  seven gaps in. Prefix-anchored redaction with no reach over a whole-file value —
  and the one case cited to justify it sits mid-body. A 4 KiB display bound against
  128 KiB of consumption, when every real artifact body on a read path runs 5,736 to
  15,231 bytes, so the operator would have confirmed 26.9–71.4% of what the emit
  step receives (the figures first recorded here were measured over the wrong file
  set and are corrected in the round-6 entry above). Two
  sanitization controls scoped to "renders or records" when the production path on
  an in-tree root does neither. And three terminal-effect statements that no run's
  output can show, because the bytes are in context before any control can fire.

  The owner's decision was to ship the read without those four and name them as a
  follow-on needing an executable read path, rather than specify them a fifth time.
  The spec's `## What this slice does not attempt` and its Follow-ons record which
  and why, per control. That removed five of round four's seven adversarial
  blockers and four of its five security blockers, because the controls those
  findings attacked stopped existing.

  Repaired from the rest: the reserved-tree refusal is carried from the shipped
  containment module rather than re-derived narrower — without it an `output_dir`
  of `.apm/` would have fed the agent's own instruction files to the emit step;
  a heightened root is now the **union** of user-profile-sourced and out-of-tree,
  because round three's re-keying had dropped the belonging check `packs/AGENTS.md`
  mandates and a user-profile root can resolve in-tree; confinement is stated as
  equality-or-descendant on resolved components rather than the preposition
  "within"; the terminal-effect list is five observable statements ending in a
  required halt, with the unobservable three replaced and the residual stated; the
  confirmation prompt gained the first heading and lost the body, which is the
  honest repair for "frontmatter alone cannot decide belonging"; and the
  corpus-agreement test moved to `tests/roster/` with its two CI wiring edits,
  gained a fourth classification for the 33 off-path files, an empty-parse floor,
  a slug binding, corpus-witnessed mutations, and a safe-loader requirement.
- 2026-09-18 — Pre-approval review round 3, and a design change the owner
  authorized. Twenty-four findings sustained, five refuted. Round three checked
  the spec against the **real** `docs/design/` corpus rather than the writer
  templates, and that is what settled the slice's shape: all six
  `screen-flow-brief` artifacts carry all eight of their template's sections, the
  one real `creative-direction` artifact carries **none** of its four and omits
  both `slug` and `date` while carrying five keys the template never declares, and
  no `token-taxonomy` artifact exists. The templates are scaffolds an author
  edits, not a format, so a section-name-keyed extracted set would have extracted
  nothing from the very artifact the Objective is about.

  On the owner's decision the extracted set became **frontmatter as found plus the
  body as one opaque block**, keying on no section name. No control was lost:
  confinement, the `type:` guard, shape validation, code-point rejection,
  redaction, the display bounds and operator confirmation all apply to a body
  block as they did to named sections.

  Also on the owner's decision, and the reason this is the last transcription
  round: T6 adds a **corpus-agreement construction test**. Rounds one, two and
  three found twenty, thirty and twenty-four findings, and the recurring class in
  every round was a hand-transcribed claim about the design artifacts that the real
  tree contradicts. A review round finds the next instance; it cannot fix the
  process. T6 reads the real tree and reds when the contract mishandles any file
  in it.

  The other load-bearing repairs: a `type:` mismatch on a path-matched file is now
  a **skip**, not a refusal — the tree holds 28 distinct `type:` values across 42
  files, including a `design-system` file under `direction/`, so refusing would
  have refused this repository's own tree; the heightened controls now key on
  whether the approved root resolves **outside the repository tree** rather than on
  which config file named it, closing the hostile cloned-repo case; the code-point
  set is enumerated with `\t`, `\n` and `\r` carved out, because the round-2
  wording refused every multi-line body; redaction now covers the same scope as
  code-point rejection and names its prefixes; `<slug>` is bound to the
  operator-named slug with all three slots under it and an ambiguous multi-match
  refused; terminal items 5 and 8 moved to whole-read scope; display bounds were
  added for a value and for the prompt; extraction reads raw text and discards HTML
  comments; and T4 took on the two existing guide pages the insertion makes stale.
- 2026-09-18 — Pre-approval review round 2. Thirty findings sustained across
  adversarial and security adjudication, five refuted. The load-bearing repairs:
  the screen-brief read path also matched the `.handover.md` sibling `user-flow`
  writes beside every brief, so a correctly written design tree would have failed
  the `type:` check and refused the whole read — the path now excludes it; four of
  the screen brief's eight section headings were paraphrased rather than
  transcribed, so a literal match would have dropped half the brief; all three
  templates carry a product name in the H1 and the extracted set discarded exactly
  that line, so the operator prompt withheld the one piece of evidence that could
  decide belonging — the H1 is now extracted, and shown as unvalidated free text
  that is never matched; `slug` is documented as naming a surface **or** a product,
  which falsifies the round-1 restatement of why no field discriminates, so the
  premise is restated as "may name either, therefore discriminates nothing"; a
  refused approval of the root and a partial artifact tree were in no named state,
  and the second barred the fallback entirely, leaving the pre-flight with no
  aesthetic reference; shape and code-point validation covered only frontmatter
  while the prompt had been enlarged to render bodies; `direction` and `screen`
  were being held to a kebab shape their templates do not declare; the stated bound
  order contradicted the enumeration cap's own rationale; the operator could not
  see the root they were approving; and no control criterion carried
  instruction-versus-data over the content actually extracted. The bound values now
  have one home in § The read bounds, and the terminal-effect list gained an eighth
  statement so a refusal on the third artifact discards the first two.
- 2026-09-18 — Pre-approval review round 1. Two blockers and eighteen further
  findings sustained across adversarial and security adjudication. The
  load-bearing repairs: the per-artifact frontmatter sets were wrong in every
  statement of them (the screen brief carries no `slug` and no `date`), so the
  spec now carries a transcribed § The extracted set and the no-discriminator
  conclusion is restated against the real sets; the extracted surface was
  undetermined between frontmatter-only and body, so the body sections are now
  named per artifact; the criteria said "create mode" while the mechanism lands in
  the shared pre-flight all four modes run, so the scope and the
  fallback-reachability claim now match; AC2's "confirm" admitted a check
  discharged by reasoning, and now requires the resolution be executed and its
  output read; the operator prompt disclosed only the fields the spec declares
  non-discriminating, and now carries the whole extracted set; error states were
  assigned to neither skip nor refusal, and are now refusals; extracted values are
  now shape-validated before display; the bound-ordering claim was false and is
  replaced by a required evaluation order plus a per-level enumeration cap; the
  128 KiB bound is now stated as a chosen ceiling rather than a calibration; the
  confinement rail was narrower than the work; and the terminal-effect list now
  has one canonical home the other sites point at.
- 2026-09-17 — Pre-approval correction. The product-belonging criterion was not
  implementable as written: it required confirming an artifact belongs to the
  current product, and the containment module `design-output-addressing` shipped
  states no frontmatter field can establish that. Replaced with bounded operator
  confirmation over a closed disclosure set, with a named refusal when
  confirmation is missing or refused; the discriminator and its migration stay
  deferred as writer-side work. Added the terminal-effect obligations to the
  Testing Strategy, the failure table and T3, carrying forward the control failure
  that spec recorded — a control that fires, repairs its input and continues is a
  failure, not a pass. Added the eval-surface obligation to T5, and marked the
  dependency satisfied.
- 2026-09-16 — Initial plan. Separated from `design-output-addressing` on the
  owner's instruction after two review rounds established that the read path is the
  only new trust boundary in that work and was carrying nine criteria and all of
  the security findings inside a spec otherwise made of mechanical declarations.
