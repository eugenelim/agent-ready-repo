# Spec: git_commit scope confinement

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0078](../../rfc/0078-workspace-mcp.md) (Accepted)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

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

An adopter running a workspace-mcp session gets `git_commit` staging only the
files belonging to the dispatched item, whatever directory they configure for
that item type's output. A configured directory that cannot bound a staging
scope is refused with an explicit error, so no configuration value widens what
a commit picks up.

## What Changes

- The wildcard structure of a staging scope — taken only from the built-in
  lifecycle manifest, in `packages/agentbundle/agentbundle/workspace_mcp.py`
- A configured `output_dir` carrying a glob metacharacter — refused, leaving
  `git_commit` unavailable for that item with an explicit error
- The first executable coverage of `git_commit`'s staging scope — under
  `packages/agentbundle/tests/`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Release history | Applicable: adopter-visible refusal behaviour ships in a released package | `packages/agentbundle/CHANGELOG.md` and `docs/product/changelog.md` | implementing workflow | A release entry whose version equals both version pins, with a `Highlights` decision recorded | Entries present, version pins agree, core's newest entry stays adjacent to `[Unreleased]` |
| User promise | Applicable: an adopter whose base contains `*` loses a commit path that worked, and one whose base carries another reserved character gets an explicit error where commits previously matched nothing | `packages/agentbundle/README-pypi.md` | implementing workflow | A `What's new` section naming the refusal and the remedy | Section present at the released version |
| Current architecture | Applicable: the design document states that Git tools validate output paths, and the validated property changes | `docs/architecture/workspace-mcp/design.md` | implementing workflow | The Git-tools description names the manifest as the source of wildcard structure | Statement matches the shipped behaviour |
| Decision rationale | Not applicable: refusing an unusable value changes no repository-wide convention, and this spec is the record of the choice | — | — | — | — |
| Reusable learning | Not applicable: no generalizable practice beyond this defect class | — | — | — | — |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Assert against the staged set that the real `git_commit` produces in a
  temporary repository, never against a reimplementation of its scope grammar.
- Exercise every configured-base case the criteria name, not only the failing
  one.
- Move the package version and every release surface in the same change.

### Ask first

- Before changing the shape of what `git_commit` returns on refusal, because
  the six git tools are pre-approved in an adopter's `permissions.allow`.
- Before extending the refusal to any consumer of the layout configuration
  other than the staging scope.

### Never do

- Never alter `_in_scope`'s containment test. The defect is where the scope's
  split point comes from; containment is a separately registered question.
- Never add a dependency, a module boundary, or a top-level directory.
- Never modify `_read_layout_bases`. It is shared with the status payload and
  legitimately yields an absolute out-of-repository base for a user-scope
  value.
- Never let a refusal be silent, and never fall back to the built-in base when
  a configured one is refused.
- Never reject a wildcard pattern for carrying an empty literal suffix; that
  shape is correct wherever the static prefix already contains `{slug}`.

## Testing Strategy

Each group verifies the criteria named in its heading, and every criterion sits
in exactly one group.

- **VI-0101. Staging scope, driven through the real tool (AC-0001, AC-0003,
  AC-0004, AC-0005).** TDD, integration surface. Builds a temporary git
  repository, calls `git_commit`, and reads back the staged set and `HEAD`. The
  invariant is a set membership, which compresses, but the oracle has to be the
  production scope computation: a check over a copy of the grammar would agree
  with a wrong implementation.
- **VI-0102. Refusal, its diagnostics, and the sibling tools (AC-0002,
  AC-0006, AC-0008).** TDD, integration surface. The same temporary
  repository, exercising every character AC-0002 names and asserting the
  returned tool error, the stderr warning, an empty stdout, and that
  `git_branch` and `git_push` still succeed.
- **VI-0103. Released surfaces (AC-0007).** Goal-based check. Compares the two
  version pins against the newest entry of each release surface. The roster pin
  is verified on CI rather than locally.

## Acceptance Criteria

- [ ] **AC-0001.** **Unchanged staging for a usable base.** For an item type with
      no configured `output_dir` and for one configured with a base containing
      none of the characters AC-0002 names, `git_commit` stages exactly the
      uncommitted files matching the dispatched item's pattern and no other
      file.
- [ ] **AC-0002.** **A base carrying a reserved character is refused.** When the
      configured `output_dir` for the dispatched item's type contains any of the
      five reserved characters `*`, `?`, `[`, `{`, or `}`, `git_commit` returns
      an error naming the configuration section. Those five are the whole
      reserved set.
- [ ] **AC-0003.** **A refusal changes nothing.** When `git_commit` refuses under
      AC-0002, no file is staged and the commit `HEAD` names is unchanged.
- [ ] **AC-0004.** **No configured value widens the scope.** No configured
      `output_dir` value that AC-0002 does not refuse causes `git_commit` to
      stage a file outside the directory that value names.
- [ ] **AC-0005.** **Deep output keeps committing.** For the `shape`, `strategy`,
      and `design` item types, whose pattern's static prefix already contains
      `{slug}`, `git_commit` stages a matching file at any depth beneath that
      prefix.
- [ ] **AC-0006.** **A refusal is announced, and not on the protocol channel.** A
      refusal under AC-0002 reaches the caller as a tool error and emits a
      warning naming the configuration section on stderr; stdout carries no
      diagnostic text.
- [ ] **AC-0007.** **Released surfaces name 0.47.3.** `version.py`,
      `pyproject.toml`, the package changelog's topmost entry, the product
      changelog's first `agentbundle` entry, and `README-pypi.md`'s newest
      `What's new` section all name `0.47.3`.
- [ ] **AC-0008.** **The sibling git tools keep working.** With a base that
      AC-0002 refuses configured for the dispatched item's type, `git_branch`
      and `git_push` return the same successful results they return with no
      configured `output_dir`, under the same repository state and the same
      arguments.

## Follow-ons

- eugenelim: `docs/specs/workspace-mcp/notes/workspace-mcp-output-base-containment.md`
  — tightening the containment base to the item type's own output base, which
  this spec's `Never do` keeps out of scope.

## Assumptions

none
