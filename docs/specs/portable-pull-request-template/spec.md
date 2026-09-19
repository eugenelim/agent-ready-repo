# Spec: portable pull-request template

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
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
| Current product truth | Applicable — an adopter-visible asset is new | `guides/core/how-to/adapt-to-project.md`, section `Install the pull-request template` | maintainer | AC-0011 passes | Both forges have a copy step, proved by target-set equality |
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
  `tools/check-core-release.py`; `tools/test_check_core_release.py`;
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
- **Adopter-visible surface (AC-0011)**: goal-based check, scoped to a named
  section of a named guide page. The two commands' target set is compared for
  equality against the two destinations, so two commands aimed at the same forge
  fail.
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

- [ ] **AC-0001.** `packs/core/.apm/skills/work-loop/assets/pull-request-template.md` exists.
- [ ] **AC-0002.** That file's rendered `##` headings are exactly, in order: `What does this change?`, `Why?`, `Review focus`, `How do I verify it?`, `What did you not change that you considered?`.
- [ ] **AC-0003.** That file contains no Markdown task-list marker (`- [ ]` or `- [x]`).
- [ ] **AC-0004.** That file's install block names both `.github/pull_request_template.md` and `.gitlab/merge_request_templates/Default.md`.
- [ ] **AC-0005.** In neither that file nor `packs/core/.apm/skills/work-loop/references/pr-authoring.md` does any extracted candidate path resolve to an existing target of any kind in this repository — file, directory, or link — except the two destinations of AC-0004. A candidate path is the content of a backtick code span, or a whitespace-delimited word inside a fenced block, that contains `/` and no whitespace; a candidate containing `<` or `>` is an adopter-generic placeholder and is not tested.
- [ ] **AC-0006.** `packs/core/.apm/skills/work-loop/references/pr-authoring.md` exists.
- [ ] **AC-0007.** That reference contains exactly two fenced blocks, each carrying the heading `## What does this change?`.
- [ ] **AC-0008.** The conditional-reference routing table in `packs/core/.apm/skills/work-loop/SKILL.md` carries exactly one row whose link target is `references/pr-authoring.md`, and whose predicate cell equals, after collapsing runs of whitespace to one space and stripping ends, `Authoring a pull-request body`.
- [ ] **AC-0009.** This repository's `.github/pull_request_template.md` contains no Markdown task-list marker.
- [ ] **AC-0010.** In `packs/core/.apm/skills/work-loop/references/supervisor-mode.md`, the sentence containing `standard template` carries a Markdown link whose target is the asset of AC-0001.
- [ ] **AC-0011.** Under a section headed `Install the pull-request template` in `guides/core/how-to/adapt-to-project.md`, exactly two copy commands appear, each taking the same source path that ends in `work-loop/assets/pull-request-template.md` and is rooted at an adapter-independent variable rather than a literal skills directory, and the set of their two targets equals exactly the two destinations of AC-0004.
- [ ] **AC-0012.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` declare the same core version.
- [ ] **AC-0013.** The version of AC-0012 has the same major and minor components as the core version at the supplied base commit, and a patch component exactly one greater.
- [ ] **AC-0014.** The topmost core entry in `docs/product/changelog.md` names the version of AC-0012.
- [ ] **AC-0015.** That changelog entry carries a `### Highlights` subsection with at least one bullet.
- [ ] **AC-0016.** In the `/now/` payload built from `docs/product/changelog.md`, exactly one group carries a `packages[]` entry whose name is the core pack and whose version is the version of AC-0012, and that group's ordered `highlights[*].source` values equal the ordered bullet texts read from the AC-0015 subsection by a reader that does not use the projection's own parser.

## Assumptions

none

## Follow-ons

none
