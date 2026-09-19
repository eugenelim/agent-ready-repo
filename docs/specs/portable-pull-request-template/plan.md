# Plan: portable pull-request template

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (version-bump rule; the
  portable-content rule forbidding repository-only paths in shipped packs; the
  self-hosting projection rule). `packs/core/AGENTS.md` (core-pack deltas).
  Analogous implementations: `packs/core/.apm/skills/new-spec/assets/spec.md`
  and `plan.md` are the precedent for a skill shipping a fill-in Markdown asset;
  their construction path is `packs/core/tests/skills/new-spec/`. Named
  uncertainty: no lint enforces the portable-content rule over pack prose, so
  T2 builds that check rather than relying on review.

## Approach

The template is a skill asset rather than a pack seed. A seed would reach
`.github/` automatically on install, but the declaration it requires lives in
`packages/agentbundle/`, which is a protected tree; the asset route delivers the
same file inside the skill with no protected-tree edit and no engine-scoped RFC.
The adopter copies one file, and the reference tells them where.

## Constraints

- `packages/agentbundle/**` is off-limits. Any change needing it is out of
  scope by the spec's `Never do` boundary.
- `packs/core/.apm/skills/work-loop/SKILL.md` sits under a line cap asserted by
  `tests/roster/test_wave4_durable_outputs_and_release.py`. Read the current
  count and the cap from that suite before editing rather than from a figure
  recorded here; a stored count decays while still governing the conclusion.
- The span from `## Finish checklist` to the `Conventional commit format` line
  is SHA-256 pinned by `tools/test_workspace_status.py`. The pull-request item
  sits after that line and is editable; nothing inside the span may move. That
  suite is the gate of record and is run, not restated as a criterion.
- `agentbundle catalogue self-host --check` owns projection drift and is
  likewise run rather than restated as a criterion.
- Shipped pack prose may not cite a repository-only path. AC-0005 is that
  rule's first mechanism — no existing lint scans pack prose, as
  `tools/lint-conformance-portability.py` reaches only `tests/conformance/`.
  Its extraction grammar is bounded and stated in the criterion: a backtick code
  span, or a whitespace-delimited word inside a fence, containing `/` and no
  whitespace. A path written in plain prose without backticks is outside that
  grammar and is the check's named blind spot; the house style writes paths in
  code spans, so the grammar covers the form the files actually use.

## Construction tests

Tests are owned per task below. Two existing suites carry obligations this
change must not break: `packs/core/tests/skills/work-loop/test_reference_routing.py`
(every routing row's anchor resolves) and `tools/test_workspace_status.py` (the
pinned Finish span). Both are re-run rather than extended, except where T3 adds
the routing row the first suite then covers.

## Durable-output map

| Spec durable output | Task | Evidence it hands `close-work` |
| --- | --- | --- |
| Maintainer procedure | T1, T2, T3, T5 | AC-0001 to AC-0008 and AC-0010 green |
| Interface compatibility | T4 | The Finish item's deletion pin passes |
| Contribution interface | T5 | AC-0009 green |
| Current product truth | T6 | AC-0011 green |
| Release history | T7 | AC-0012 to AC-0016 green |

Reusable learning is not mapped here: the work-loop capture gate already owns
it, and a second owner in this plan would be an obligation with no new mechanism.

## Design (LLD)

### Design decisions
<!-- Traces to: AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0011 · no contract file. -->
<!-- Owned by: T1, T3, T5, T6. -->

This section is **living design**, not contract. The spec deliberately carries
no criterion for the wording below: its only possible contract checks are a
semantic term no parse decides or an exact literal that byte-pins the file. An
implementer corrects this wording in place without an amendment, and the suite
protects each element with a deletion-only pin.

**The template's required content.** Above the first heading, in a comment:

1. A statement that the template is a starting point and that a repository with
   an existing pull-request convention keeps it instead.
2. The two install destinations, one per forge.
3. Three prohibitions, stated as one numbered list because they describe a
   single failure — writing the session rather than the state — and splitting
   them across five section comments would state the shared cause three times
   while letting a reader meet only one:
   - what was attempted: no round counts, no findings tallies, no dead ends;
   - the method behind a result: a result is evidence, the run is not;
   - the diff, restated: the reviewer already has it.
4. A line budget of **40 lines of rendered body**, labelled a house convention.
   No optimum is established for pull-request length, so the number orients an
   author without claiming an authority it does not have.

**Per-section guidance sits in comments, which do not render.** An author reads
them while writing and a reviewer never sees them in the published body. In
rendered prose, every pull request would carry its own instructions.

**`Review focus` is optional and its comment forbids narrating difficulty.** It
is the highest-value section available and also the one most likely to attract
the narrative the other rules remove, so its comment carries the discriminator:
a question about the code, not an account of what was hard.

**The reference ships writing rules and two worked bodies.** The rules live
under one heading, `Writing rules`, and are exactly these seven, each pinned
only within that section:

1. Lead with the result: the first sentence says what is true now.
2. Ground every claim in a path, command, count, measurement, or error text.
3. Never describe intended work as done; state partial work as partial.
4. Prose carries reasoning; bullets carry independent items, one idea each.
5. A table earns its place when three or more items share two or more fields a
   reader must compare.
6. Collapse only the optional: risk, rationale, and verification stay visible.
7. Draft for completeness, then make one editing pass that preserves every name,
   number, scope boundary, and stated uncertainty.

Worked examples are the better-evidenced instrument for style control, so two
follow the rules under their own heading. The two differ in size on purpose: the
second omits `Review focus`, uses no bullets, and shows the shape scaling down.
Neither may contradict a rule it illustrates — an example that narrates its
method is a counter-model that outweighs the rule above it.

**The guide section** is headed `Install the pull-request template` in
`guides/core/how-to/adapt-to-project.md`. It carries a single invocation of the
shipped installer, which AC-0017 parses, and — as prose rather than criterion —
the statement that a repository with an existing convention keeps it. The
installer is a script rather than a recipe pasted here: hardening it in prose
produced a confinement helper, an adapter loop and a failure accumulator, which
is a program, not documentation.

**The routing predicate cell** is exactly `Authoring a pull-request body`.
AC-0008 compares it by equality after collapsing whitespace, so the value is
fixed here rather than left to an implementer's phrasing.

**Deletion-only pins.** One pin per required element: the starting-point
statement, the install destinations, the prohibition list, the line budget, each
of the five section comments, the `Review focus` discriminator, each of the seven
rules under the reference's `Writing rules` heading, pinned within that section, both worked bodies, the Finish item's required
content, and the guide's keep-your-own-convention sentence. Each test's docstring
states that the pin catches removal and does not certify wording.

### Interfaces & contracts
<!-- Traces to: no criterion — demoted; protected by T4's deletion pin · no contract file. -->
<!-- Owned by: T4. -->

**This sub-section is demoted material, not contract.** The pack eval harness
runs a skill with only the `Skill` tool available and excludes network and
credential skills by scope, so no available runner can observe the loop issuing
a `gh` command. A behavioral criterion here could never red, so the required
content lives below and T4 pins it against deletion.

Capability is decided by two read-only commands, in order. `gh api user` exits
zero with usable credentials and non-zero without. `gh repo view OWNER/REPO
--json viewerPermission --jq .viewerPermission` then returns the role, and
`WRITE`, `MAINTAIN`, or `ADMIN` is sufficient. Any other outcome, including an
unavailable role, is silent: no offer, no message.

The probe reads an exit status rather than a number because both alternatives
fail. A `gh` error string misreports: where a credential store is unreadable,
`gh auth status` reports an invalid token and `gh repo view` reports a
connection failure, while the account is in fact authenticated elsewhere on the
same machine — both name a cause that is not the cause. A rate-limit threshold
avoids that but stores 60 as GitHub's anonymous ceiling, an external constant
whose change would silently invert the decision. An exit status carries neither
defect.

A passing probe does not guarantee creation succeeds — branch protection, an
archived repository, or an empty diff between branches each refuse afterwards.
The instruction therefore governs whether to offer, never whether creation will
succeed, and the silent branches exist so a refusal after a passing probe costs
the reader nothing.

### Dependencies & integration
<!-- Traces to: AC-0015, AC-0016 · no contract file. -->
<!-- Owned by: T7. -->

No new dependency. `gh` is already assumed by the Finish step this replaces.
The release path adds one consumer relationship: the changelog's `### Highlights`
block is read by the `/now/` projection. AC-0016 is verified by reading that
block directly and comparing it with the built payload, not by the repository's
existing real-changelog tests: those build both their expected and their actual
values from `build_site.parse_changelog_releases`, so an entry that parser
cannot see is missing from both sides and they pass regardless.

## Tasks

### T1: The shipped template exists and has the required shape

**Depends on:** none

**Tests:**
- Asserts the asset exists (AC-0001); its rendered `##` headings equal the five
  of AC-0002 in order, parsed rather than matched as one block (AC-0002); no
  task-list marker occurs (AC-0003); both destinations appear inside the install
  block, located by its `Install:` line rather than by containment anywhere in
  the file (AC-0004).
- Deletion-only pins for each element the LLD names: the starting-point
  statement, the prohibition list, the line budget, the five section comments,
  and the `Review focus` discriminator. Each docstring states that the pin
  catches removal and does not certify wording.

**Approach:**
- The module is a new file under `packs/core/tests/skills/work-loop/`, not an
  addition to a shared module — two shared work-loop modules are node-count and
  SHA pinned, and a new file avoids re-pinning them.

**Done when:** the four criteria cases and every pin pass.

**Touches:** packs/core/.apm/skills/work-loop/assets/pull-request-template.md, packs/core/tests/skills/work-loop/

### T2: Shipped prose cites no path that exists only here

**Depends on:** T1, T3

**Tests:**
- Extracts every path-like token from both shipped files and asserts none
  resolves to an existing file in this repository, except the two install
  destinations (AC-0005).

**Approach:**
- Extraction plus resolution replaces the hand-written deny list an earlier
  draft carried. A deny list catches only the forms its author thought of.
  Resolution against the real tree removes that gap for every path inside the
  grammar: an adopter-generic form such as `docs/specs/<feature>/spec.md`
  carries `<` and is skipped, while a real repository path fails whether or not
  anyone anticipated it. The grammar itself is the remaining bound — a path
  written in bare prose is not extracted — and the docstring names it rather
  than implying the check is exhaustive.
- The two destinations are allowlisted because the template must name them.

**Done when:** the case passes against both files.

**Touches:** packs/core/tests/skills/work-loop/

### T3: The reference exists and routes

**Depends on:** none

**Tests:**
- Asserts the reference exists (AC-0006) and contains exactly two fenced blocks
  each carrying `## What does this change?` (AC-0007).
- Asserts the routing table carries exactly one row whose link target is
  `references/pr-authoring.md` and whose predicate cell equals
  `Authoring a pull-request body` after whitespace collapse (AC-0008).
- Existing `test_reference_routing.py` passes, covering anchor resolution.
- Deletion-only pins for each writing rule the LLD requires and for both
  worked bodies.

**Approach:**
- AC-0008 compares the predicate cell by equality against the value fixed in the
  LLD, because the existing routing suite checks anchor resolution and observes
  neither a file-only link nor the predicate.

**Done when:** all three criteria cases, the existing suite, and both pins pass.

**Touches:** packs/core/.apm/skills/work-loop/references/pr-authoring.md, packs/core/.apm/skills/work-loop/SKILL.md

### T4: The Finish step probes by exit status, then offers or stays silent

**Depends on:** T3

**Tests:**
- Existing `tools/test_workspace_status.py` passes, establishing the pinned span
  is byte-unchanged.
- Deletion-only pin on the Finish item's required content: the two-command
  probe, the three refusing branches, and the accepting branch. The docstring
  states that the pin catches removal and does not observe the loop's behavior.
- A separate region-bounded assertion over the Finish item: within its bounds,
  no instruction names `gh auth status`, and none reads, captures, or compares
  `gh` diagnostic or error prose. Comparing the `viewerPermission` value against
  the three accepting roles is required and therefore explicitly permitted — the
  forbidden thing is deciding from prose a blocked credential store can forge,
  not reading a documented enum. A presence pin cannot establish an absence, and
  it would not catch a conflicting instruction added beside the required ones.

**Approach:**
- Edit only below the `Conventional commit format` line. The pinned span ends
  there, and an edit above it fails the hash and forces a re-pin this change has
  no reason to spend.
- The behavior carries no criterion because no available runner can observe it;
  the reasoning is in `## Design (LLD)` and the limitation is stated in the
  spec's Testing Strategy rather than left for a reader to discover.

- The pack's eval harness gains one guidance eval for the changed Finish step,
  covering the credential gate, the three accepting roles, and silent refusal.
  It asserts what the skill instructs, and claims no `gh` execution: the harness
  runs a skill with only the `Skill` tool available, so an eval that implied
  otherwise would be asserting something it never ran.

**Done when:** the existing suite, the deletion pin, the region-bounded
assertion, and the new guidance eval all pass.

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md, packs/core/.apm/skills/work-loop/evals/, packs/core/tests/skills/work-loop/

### T5: This repository's form matches, and the dangling reference resolves

**Depends on:** T1

**Tests:**
- Asserts `.github/pull_request_template.md` carries no task-list marker
  (AC-0009).
- Asserts the `standard template` sentence in `supervisor-mode.md` carries a
  link whose target is the asset (AC-0010).

**Approach:**
- The link lands here rather than in T3 because the referent must exist and this
  repository's form must already match it before the link means anything.

**Done when:** both cases pass.

**Touches:** .github/pull_request_template.md, packs/core/.apm/skills/work-loop/references/supervisor-mode.md

### T6: An adopter can install the template, and the guide says how

**Depends on:** T1, T3

**Tests:**
- Executable: the shipped `install-pr-template.py` is run in temporary
  repositories covering a fresh install, a second adapter root, no asset
  installed, a re-run, an existing convention, a dangling-symlink destination,
  a symlinked destination ancestor, a symlinked source ancestor, differing
  adapter installs, and an unwritable destination (AC-0011).
- Asserts the guide's install section carries exactly one fenced `bash` block
  of exactly one line, invoking that script (AC-0017).
- Asserts both behavioural suites are named by a `run-test-suite` line in
  `Makefile` and by a `build-check.yml` step, and that `lint-ci-parity.py`
  exits zero (AC-0018). Gate wiring is in scope because a suite this delivery
  creates and nothing runs is a control that reports nothing; removing the
  wiring to stay inside the original boundary would restore that defect.
- Deletion-only pin for the keep-your-own-convention sentence.
- Existing `tools/test_check_rendered_site_links.py` passes.

**Approach:**
- The installer is a shipped script rather than a recipe pasted into the guide.
  Hardening it in prose produced a confinement walk, an adapter loop, a failure
  accumulator and a subshell — executable logic a reader was expected to copy
  and maintain. A script is testable, versioned, and invoked in one line.
- Every scenario runs the script; reading its text cannot catch a wrong search
  depth, an exit code that lies on a skip, or a path that escapes through a
  symlink. All three shipped and were found only by execution.

**Done when:** every scenario passes, the guide carries one invocation, and the
pin and existing suite pass.

**Touches:** packs/core/.apm/skills/work-loop/scripts/install-pr-template.py, guides/core/how-to/adapt-to-project.md, tools/test_pull_request_template_adoption.py, Makefile, .github/workflows/build-check.yml, tools/lint-ci-parity.py

### T7: The release checker is correct, and the core pack releases

**Depends on:** T1, T2, T3, T4, T5, T6

**Tests:**
- `tools/test_check_core_release.py` drives `tools/check-core-release.py` over
  this case table. Every row must reach its stated exit.

  | Case | Fixture | Exit |
  | --- | --- | --- |
  | Valid successor | patch = base + 1, both manifests agree, topmost entry names it, entry has a bullet | zero |
  | Major changed | major differs from base | non-zero |
  | Minor changed | minor differs from base | non-zero |
  | Patch unchanged | patch = base | non-zero |
  | Patch lower | patch = base − 1 | non-zero |
  | Patch overshoot | patch = base + 2 | non-zero |
  | `pack.toml` wrong | `pack.toml` alone carries the wrong version | non-zero |
  | `plugin.json` wrong | `plugin.json` alone carries the wrong version | non-zero |
  | Wrong topmost entry | topmost entry names another version; the expected version appears in a **later** entry | non-zero |
  | Target entry unbulleted | target entry's `Highlights` is empty; a **later** entry carries a valid bullet | non-zero |
  | Unresolvable base | base commit does not resolve | non-zero |

- The delivery run of `tools/check-core-release.py --base <merge-base commit>`
  exits zero, establishing AC-0012, AC-0013, AC-0014, and AC-0015 together. Its
  output is retained as closeout evidence.
- `tools/test_check_core_release.py` also asserts AC-0016: from the `/now/`
  payload built over the changelog, exactly one group carries a `packages[]`
  entry naming the core pack at the released version, and that group's ordered
  `highlights[*].source` values equal the ordered bullet texts read from the
  `### Highlights` subsection by a reader independent of the projection parser.
- `agentbundle catalogue self-host --check` reports no drift.

**Approach:**
- The two manifest cases are directed at one file each. A single
  "manifest mismatch" case is satisfied by a checker that reads only
  `pack.toml` and by one that reads only `plugin.json`, so it rejects neither.
- The last two changelog rows carry decoys on purpose: the expected version
  appears in a later entry, and a valid bullet appears in a later entry. Without
  them, a checker that searches the whole file for the version, or for any
  `Highlights` bullet anywhere, passes while checking nothing about the topmost
  entry.
- The refusing rows bound the successor from both sides. Rows that only bound it
  from above are satisfied by a checker accepting anything up to `base + 1`.
- The checker owns AC-0012, AC-0013, AC-0014, and AC-0015 rather than leaving them to a prose
  assertion in this task. An obligation named in a task but owned by no
  executable is discharged by whoever reads the task, which is not a check.
- AC-0016's reader is independent of `build_site.parse_changelog_releases`
  because the repository's existing real-changelog tests derive both their
  expected and their actual values from it: an entry that parser cannot see is
  absent from both sides and those tests stay green while the entry never
  reaches the page.
- The version check is delivery-time, not a shipped assertion pinning one
  version: that would fail on the next unrelated core release. The checker
  itself is permanent; the pinned expectation is not.
- `Highlights` bullets are required because this change adds consumer
  capability — a new installable asset and a changed Finish behavior — and an
  unwritten block is a release the public page never mentions.
- `make build-self` runs before the delivery run, because the projections are
  part of the released state.

**Done when:** every row of the case table reaches its stated exit, the delivery
run exits zero and its output is retained, the AC-0016 comparison passes, the
drift check is clean, and `git status` is clean.

**Touches:** tools/check-core-release.py, tools/test_check_core_release.py, packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.md, .agents/, .claude/

## Rollout

- **Delivery:** one pull request, reversible by reverting it. The asset is
  additive; the only removal is this repository's checklist.
- **Infrastructure:** none.
- **External-system integration:** none. The `gh` probe is read-only and the
  binary is already assumed by the Finish step it replaces.
- **Deployment sequencing:** T7 last, because the release surface must describe
  a finished tree.

## Risks

- The template's wording, the reference's wording, and the Finish instruction
  are pinned for deletion, not certified for quality or observed in use.
  Mitigation: stated in the spec's Testing Strategy and in each pin's docstring,
  so a green suite is never mistaken for a behavioral guarantee.
- The Finish behavior ships unverified by any runner. Mitigation: both `gh`
  commands' real exit behavior was measured in a credentialed shell and in a
  credential-blocked sandbox before the design was fixed, so the instruction
  encodes an observed contract rather than an assumed one.
- `tools/check-core-release.py` is new code this delivery creates. Mitigation:
  T7's case table is its construction suite, covering the accepting path and
  every refusing path the table names, rather than trusting its one passing
  delivery run. The table is the single statement of that count; no prose
  repeats it.

## Changelog

- 2026-09-18: spec approved by eugenelim
- 2026-09-18: plan approved by eugenelim
