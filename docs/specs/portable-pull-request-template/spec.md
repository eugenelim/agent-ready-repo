# Spec: portable pull-request template

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Outcome

A repository that installs the core pack has a pull-request template and an
authoring reference it can copy to GitHub or GitLab, and a Finish step whose
instruction tells the loop to probe before offering and to stay silent
otherwise. Success is those artifacts present, portable, and reachable from the
guides; the loop's observed behavior is reviewed, not gated, because no
available runner can watch it probe.

## What Changes

- A pull-request template ships as a work-loop asset — `packs/core/.apm/skills/work-loop/assets/pull-request-template.md`
- Worked bodies and writing guidance for an agent authoring a PR — `packs/core/.apm/skills/work-loop/references/pr-authoring.md`
- The Finish step tests whether it can open a pull request, then offers or stays silent — the Finish checklist in `packs/core/.apm/skills/work-loop/SKILL.md`
- The phrase "the standard template" gains the referent it currently lacks — `packs/core/.apm/skills/work-loop/references/supervisor-mode.md`
- This repository's own pull-request form drops its twelve checkboxes — `.github/pull_request_template.md`
- The core pack releases the change — `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Applicable — the asset and the reference are the artifact this delivery exists to create | `packs/core/.apm/skills/work-loop/assets/pull-request-template.md`, `packs/core/.apm/skills/work-loop/references/pr-authoring.md` | `work-loop` skill | AC-0001 to AC-0008 and AC-0010 pass | Both files exist, are portable, and the routing row and supervisor link resolve |
| Interface compatibility | Applicable — the Finish step changes what work-loop does at the end of a run | `packs/core/.apm/skills/work-loop/SKILL.md` Finish checklist | `work-loop` skill | The deletion pin on the Finish item passes; no behavioral criterion, because no available runner can observe the probe | The instruction states the two-command probe and its four branches, and the pin would fail on its removal |
| Contribution interface | Applicable — this repository's own pull-request form changes | `.github/pull_request_template.md` | maintainer | AC-0009 passes | The form carries no checklist |
| Current product truth | Applicable — an adopter-visible asset and installer are new | `packs/core/.apm/skills/work-loop/scripts/install-pr-template.py`, and `guides/core/how-to/adapt-to-project.md` section `Install the pull-request template` | maintainer | AC-0011, AC-0017 pass | The installer is observed installing both forges, and the guide invokes it |
| Release history | Applicable — core pack content changes and adds consumer capability | `docs/product/changelog.md` | release workflow | AC-0012 to AC-0016 pass | The derived version ships with a `Highlights` block the real-changelog projection carries into `/now/` |

## Agent Rules

The repository already owns portability, the protected tree, the top-level
directory audit, the version-bump rule, and the self-host projection rule; this
section does not restate them. Cite `packs/AGENTS.md` and
`tools/lint-catalogue-curation-guard.py` rather than copying their text.

### Always do

- Decide pull-request capability from a command's exit status, never from a
  numeric threshold whose value an external platform owns.
- Give every rule in the shipped template a form an author can check against
  their own draft without leaving the template.

### Ask first

- Before adding any section to the template beyond the five AC-0002 names.
- Before changing the four-question wording in the root `AGENTS.md` or in
  `packs/core/seeds/AGENTS.md`.
- Before raising a line cap or re-pinning a content hash to make an edit fit.

### Never do

- Never let this delivery write outside this closed set — structural: the
  boundary is what keeps the delivery patch-sized and outside the protected
  tree. `packs/core/.apm/skills/work-loop/assets/pull-request-template.md`;
  `packs/core/.apm/skills/work-loop/references/pr-authoring.md`;
  `packs/core/.apm/skills/work-loop/SKILL.md`;
  `packs/core/.apm/skills/work-loop/references/supervisor-mode.md`;
  `packs/core/tests/skills/work-loop/`; `packs/core/pack.toml`;
  `packs/core/.claude-plugin/plugin.json`; `docs/product/changelog.md`;
  `packs/core/.apm/skills/work-loop/evals/`;
  `packs/core/.apm/skills/work-loop/scripts/install-pr-template.py`;
  `tools/check-core-release.py`; `tools/test_check_core_release.py`;
  `Makefile`;
  `.github/workflows/build-check.yml`; `tools/lint-ci-parity.py`;
  `tools/test_pull_request_template_adoption.py`;
  `guides/core/`; `.github/pull_request_template.md`;
  `docs/specs/portable-pull-request-template/`; and the generated `.agents/`
  and `.claude/` projections.
- Never treat a `gh` error string, `gh auth status` output, or any other prose a
  blocked credential store can forge as a capability input.
- Never add a checklist to the shipped template.

## Testing Strategy

Every criterion below is settled by a parse or by an observed run. The
template's and reference's *wording* — the prohibitions, the per-section
guidance, the `Review focus` discriminator, the keep-your-own-convention
clause, and the worked bodies demonstrating them — is required work carried by
the plan's `## Design (LLD)`, not contract. That material is prose whose only
possible contract check is either a semantic term no parse decides or an exact
literal that byte-pins the file against any future edit; it is therefore
protected by deletion-only content pins in the suite and corrected in place by
an implementer, without an amendment. Each such pin's docstring states that it
catches removal and does not certify wording.

- **Artifact shape (AC-0001, AC-0002, AC-0003, AC-0004, AC-0006, AC-0007,
  AC-0008, AC-0009, AC-0010)**: goal-based check. A file exists, a heading
  sequence, a marker's absence, a located install block, a routing row's two
  cells compared by equality, a link target.
- **Portability (AC-0005)**: goal-based check. Every path-like token in the two
  shipped files is extracted and rejected when it resolves to a file in this
  repository, unless it is one of the two install destinations. An
  adopter-generic form carrying a `<placeholder>` segment resolves nowhere and
  passes. Blind spot: the extraction grammar reaches a backtick code span and a
  word inside a fence, so a path written in bare prose is not tested.
- **Installer behaviour (AC-0011)**: goal-based check, exercised by RUNNING the
  shipped script in temporary repositories. Reading its text cannot catch a
  wrong search depth, an exit code that lies when a copy is skipped, or a path
  that escapes the repository through a symlinked ancestor; all three shipped
  and were found only by execution.
- **Adopter-visible surface (AC-0017)**: goal-based check, scoped to the named
  guide section, asserting it invokes the script rather than restating it.
- **Gate registration (AC-0018)**: goal-based check. Both behavioural suites
  shipped once with no roster entry and no workflow step, so they ran only by
  hand — a control nobody runs reports nothing. `lint-ci-parity.py` decides the
  two-way disposition.
- **Release surface (AC-0012, AC-0013, AC-0014, AC-0015, AC-0016)**: goal-based
  check run once at delivery, not shipped as a standing test. The expected
  version is derived from an explicit base commit, so it neither goes stale when
  a later core release lands nor can be satisfied by borrowing an unrelated
  unreleased bump. AC-0016 reads the changelog entry independently of the
  projection's own parser: the repository's existing real-changelog tests build
  both their expected and their actual values from that parser, so an entry the
  parser cannot see is absent from both sides and those tests pass while the
  entry never reaches the page.

The Finish step's capability behavior is **not** contract. The pack eval harness
runs a skill with only the `Skill` tool available and excludes network and
credential skills by scope, so no available runner can observe the loop probing
`gh`. Specifying a behavioral criterion no instrument can settle would put a
checkbox on the contract that nothing could ever red. The instruction's required
content is therefore carried by the plan's `## Design (LLD)` and protected by a
deletion-only pin, exactly as the template's wording is.

## Acceptance Criteria

- [x] **AC-0001.** `packs/core/.apm/skills/work-loop/assets/pull-request-template.md` exists.
- [x] **AC-0002.** That file's rendered `##` headings are exactly, in order: `What does this change?`, `Why?`, `Review focus`, `How do I verify it?`, `What did you not change that you considered?`.
- [x] **AC-0003.** That file contains no Markdown task-list marker (`- [ ]` or `- [x]`).
- [x] **AC-0004.** That file's install block names both `.github/pull_request_template.md` and `.gitlab/merge_request_templates/Default.md`.
- [x] **AC-0005.** In neither that file nor `packs/core/.apm/skills/work-loop/references/pr-authoring.md` does any extracted candidate path resolve to an existing target of any kind in this repository — file, directory, or link — except the two destinations of AC-0004. A candidate path is the content of a backtick code span, or a whitespace-delimited word inside a fenced block, that contains `/` and no whitespace; a candidate containing `<` or `>` is an adopter-generic placeholder and is not tested.
- [x] **AC-0006.** `packs/core/.apm/skills/work-loop/references/pr-authoring.md` exists.
- [x] **AC-0007.** That reference contains exactly two fenced blocks, each carrying the heading `## What does this change?`.
- [x] **AC-0008.** The conditional-reference routing table in `packs/core/.apm/skills/work-loop/SKILL.md` carries exactly one row whose link target is `references/pr-authoring.md`, and whose predicate cell equals, after collapsing runs of whitespace to one space and stripping ends, `Authoring a pull-request body`.
- [x] **AC-0009.** This repository's `.github/pull_request_template.md` contains no Markdown task-list marker.
- [x] **AC-0010.** In `packs/core/.apm/skills/work-loop/references/supervisor-mode.md`, the sentence containing `standard template` carries a Markdown link whose target is the asset of AC-0001.
- [x] **AC-0011.** `packs/core/.apm/skills/work-loop/scripts/install-pr-template.py`, run from a repository root that carries the asset under any adapter root, installs the asset byte-identically to both destinations of AC-0004 and exits zero; run where no asset is installed it writes neither destination and exits non-zero.
- [x] **AC-0012.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` declare the same core version.
- [x] **AC-0013.** The version of AC-0012 has the same major and minor components as the core version at the supplied base commit, and a patch component exactly one greater.
- [x] **AC-0014.** The topmost core entry in `docs/product/changelog.md` names the version of AC-0012.
- [x] **AC-0015.** That changelog entry carries a `### Highlights` subsection with at least one bullet.
- [x] **AC-0016.** In the `/now/` payload built from `docs/product/changelog.md`, exactly one group carries a `packages[]` entry whose name is the core pack and whose version is the version of AC-0012, and that group's ordered `highlights[*].source` values equal the ordered bullet texts read from the AC-0015 subsection by a reader that does not use the projection's own parser.
- [x] **AC-0017.** Under a section headed `Install the pull-request template` in `guides/core/how-to/adapt-to-project.md`, exactly one fenced `bash` block appears, carrying exactly one command line, and that line invokes the script of AC-0011.
- [x] **AC-0018.** `tools/test_pull_request_template_adoption.py` and `tools/test_check_core_release.py` are each named by a `run-test-suite` line in `Makefile` and by a step in `.github/workflows/build-check.yml`, and `tools/lint-ci-parity.py` exits zero.
## Assumptions

none

## Follow-ons

none
