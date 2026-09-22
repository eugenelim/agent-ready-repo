# Plan: git_commit scope confinement

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/workspace-mcp/design.md` (Git
  tools validate output paths before subprocess use); analogous
  implementations `_publishable_output_pattern` and `_resolve_output_pattern`
  in `packages/agentbundle/agentbundle/workspace_mcp.py`, with
  `packages/agentbundle/tests/test_workspace_mcp_layout_override.py` as the
  sibling's construction path; named uncertainty — `git_commit` has no
  executable coverage today, so this plan creates the first.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan.

## Approach

The refusal lands where the git path resolves its pattern list, not where
`git_commit` builds scope entries. That list is computed once and stored on the
instance, and an unusable value already has a path to "`git_commit`
unavailable", so refusing at resolution reuses it and leaves the scope grammar
untouched — which the spec's `Never do` requires.

The risky part is not the refusal but the rows that must not move. Two of the
four patterned item types legitimately produce an empty literal suffix, so the
check keys on the configured base value and never on the shape of the
substituted pattern. Order of work: land the staging matrix first so the
leak is observable on the one row that produces it, then the refusal, then the release and architecture
surfaces.

## Constraints

- [RFC-0078](../../rfc/0078-workspace-mcp.md) (Accepted) governs workspace-mcp.
- `docs/specs/workspace-mcp/spec.md` is Shipped and needs no supersession
  pointer: this work restores AC14's existing scoping promise rather than
  changing it, and the frozen-spec route is owned by
  [`docs/specs/README.md`](../README.md) either way.
- Four item types carry an output pattern — `research`, `shape`, `strategy`,
  `design` — and the built-in manifest is the only source of patterns, so it
  bounds which types any criterion here can reach.
- `packages/AGENTS.local.md`: changes under `packages/agentbundle/agentbundle/`
  carry an `Engine-Change-RFC:` commit footer, and package source carries no
  internal governance ordinals.
- `packages/AGENTS.md`: a non-cosmetic package change moves `version.py` and
  `pyproject.toml`; engine tests live under `packages/agentbundle/tests/`.
- `docs/specs/workspace-mcp/notes/workspace-mcp-output-base-containment.md`
  owns the containment-base question, which keeps this plan out of `_in_scope`.

## Construction tests

One cross-cutting suite is the shared oracle for AC-0001, AC-0003, AC-0004 and AC-0005: a
staging matrix that drives the real `git_commit` in a temporary git repository
and reads back the staged set. It is cross-cutting because a single run
exercises every reserved character and both must-not-regress rows, and because asserting
against a copy of the scope grammar would agree with a wrong implementation.

## Durable-output map

| Spec durable output | Task |
| --- | --- |
| Release history | T3 |
| User promise | T3 |
| Current architecture | T4 |

## Design (LLD)

### Design decisions

Owned by: T2, T5

- **Refuse at pattern resolution.** `_resolve_output_pattern` returns the
  pattern list that `__init__` stores; returning `None` there is the existing
  route to an unavailable `git_commit`, so the refusal needs no new branch in
  `git_commit` and the scope-entry grammar is not touched.
- **Key the check on the configured base, not the pattern.** Keying on the
  substituted pattern would have to distinguish a manifest wildcard from a
  configured one, and the two are textually identical after substitution. The
  base is the only adopter-controlled input, so it is the only thing to check.
- **The refused set is `*`, `?`, `[`, `{`, `}`, and the five are not one
  class.** Measured against the real `git_commit`: only `*` reaches the scope
  grammar, which keys on the literal sequence `/*`; `{` or `}` is consumed by
  `p.format(slug=slug)`, which runs after the base is substituted, so
  `docs/{slug}` relocates the staged tree to `docs/<slug>`; `?` and `[` reach
  neither the staging grammar nor slug formatting, so they are reserved to keep
  the set one rule an adopter can hold rather than because they relocate
  anything. Do not collapse the three into one justification — an earlier draft
  claimed all five reached the grammar, which execution disproved.
  `_public_canonical_path` is not reusable here: the git path legitimately
  carries an absolute out-of-repository base for a user-scope value, which that
  policy refuses outright.
- **The accepted-base invariant is structural, so it can be checked over a
  family rather than one example.** For any accepted base `B`, the staging
  scope's static root is `repo_root / B / <the manifest pattern's own static
  tail>` and its wildcard structure is the manifest's alone. That is decidable
  for a generated family of accepted bases, which is what makes AC-0004's
  universal checkable rather than sampled at one point.
- **The screen reads the selection, never a reconstruction of it.** The value
  AC-0002 speaks of is the one the layout resolver selected, and only that
  resolver knows which scope won. A second reader that reproduces the selection
  is the two-answers defect returning: `_read_scope` wraps its three-key loop in
  one `contextlib.suppress(Exception)`, so any raise from `Path(raw)`,
  `is_absolute()` or `resolve()` abandons the rest of that scope and hands the
  decision to the other one, and a hand-written mirror must reproduce every
  such raise on every supported interpreter. Three review rounds each found a
  different one. One selection therefore yields both forms, and
  `_read_layout_bases` becomes a projection of it that keeps its own signature,
  return type and callers unchanged.
- **A refusal must not engage discovery mode.** `_GitTools.__init__` currently
  derives `self._discovery_mode` from `dispatched`, and the existing
  malformed-item branch clears `dispatched` when the pattern list is `None`.
  Reusing that branch would disable `git_branch` and `git_push` and answer
  `git_commit` with the generic discovery error — the opposite of AC-0008 and
  AC-0002. A refused configured base is therefore represented distinctly from
  an absent or malformed dispatched item at that same seam, so the session stays
  dispatched and only `git_commit` refuses.

### Interfaces & contracts

Owned by: T2

`git_commit`'s returned shape is unchanged: it already returns
`{"error": ...}` when no pattern is available. Only the error's text is new,
and it names the configuration section. `git_status`, `git_branch` and
`git_push` do not read the pattern list, but they do read the discovery-mode
derivation that the refusal must leave alone — see the design decision above.

### Behavior & rules

Owned by: T2

A refused configured base is represented distinctly from an absent or malformed
dispatched item, so the session stays dispatched and only `git_commit` refuses.
The log line keeps distinguishing the two as the adopter-facing diagnostic.

### Failure, edge cases & resilience

Owned by: T2

The refusal is fail-closed: it removes a capability rather than narrowing one,
so no partially-scoped commit is reachable from a refused value.

### Dependencies & integration

Owned by: T2

None added.

## Tasks

### T1: The staging matrix reds only on the glob-bearing row

**Depends on:** none

**Tests:**
- A new suite under `packages/agentbundle/tests/` builds a temporary git
  repository, sets `WORKSPACE_MCP_DISPATCHED_ITEM`, writes one file inside the
  dispatched item's output and one unrelated file elsewhere, calls the real
  `git_commit`, and asserts the staged set. Rows: no configured base, a plain
  configured base, and one row per character AC-0002 names — `*`, `?`, `[`,
  `{`, `}`. Covers AC-0001 and AC-0004.
- The unrelated file is asserted absent from the staged set on every row.
- The accepted-base rows are a generated family crossed with all four
  patterned item types, not one example. The base classes are: a single
  segment; a nested base; a deep base; one carrying `.`, `_` and `-`; an
  absolute base inside the repository; an absolute base outside it, which the
  design accepts for a user-scope value; and one whose raw value carries dot
  segments that resolution normalises away.
- For each of those, the test asserts the structural invariant directly against
  the production scope computation — the static root is
  `repo_root / B / <the manifest pattern's own static tail>` and the wildcard
  structure is the manifest's — and not only that the staged set is the item's
  own file. Asserting the staged set alone passes wherever the fixture happens
  to have no file at the widened location, which is how a sampled oracle agrees
  with a wrong implementation. Together these discharge AC-0004's universal.

**Touches:** packages/agentbundle/tests/test_workspace_mcp_git_scope.py

**Done when:** every assertion in this task's `Tests` holds except the `*`
row's, which fails by staging the unrelated file and is what makes the defect
observable. The refusal, warning and stdout assertions belong to T2.

### T2: git_commit refuses a glob-bearing configured base

**Depends on:** T1

**Tests:**
- Every refusal row passes with nothing staged, and T1's whole accepted-base
  family still holds its staged-set and invariant assertions. Covers AC-0001,
  AC-0004.
- `HEAD` is captured before each refusing call and asserted unchanged after it,
  so a refusal that first creates an empty commit fails. Covers AC-0003.
- For each character AC-0002 names, the returned error names the configuration
  section, stderr carries a warning naming that section, and stdout is empty.
  Covers AC-0002 and AC-0006.
- A deep file under a `{slug}`-bearing static prefix is still staged for
  `shape`, `strategy` and `design`. Covers AC-0005.
- With a refused base configured, `git_branch` and `git_push` return the same
  successful results as with no configured base, under the same repository
  state and arguments. Covers AC-0008.

**Approach:** the check runs inside `_resolve_output_pattern` before
`_apply_layout_overrides` substitutes, so a refused value never reaches the
pattern list at all.

**Touches:** packages/agentbundle/agentbundle/workspace_mcp.py,
packages/agentbundle/tests/test_workspace_mcp_git_scope.py

**Done when:** every assertion in T1's and this task's `Tests` holds.

### T3: Released surfaces name one version

**Depends on:** T2

**Tests:**
- Goal-based, in `tests/roster/test_okf_catalogue_discovery.py`: `version.py`
  and `pyproject.toml` both read `0.47.3` by equality; the package changelog's
  topmost `## [` heading, the product changelog's first `## [agentbundle][`
  heading, and `README-pypi.md`'s newest `## What's new in` heading each name
  that version. The three heading checks are positional, not containment: a
  newer heading placed above the released one is the half-finished-release
  state AC-0007 pins against, and a containment check stays green through it.
  Covers AC-0007.
- `tools/test_build_site_routing.py` passes. It checks changelog parsing, the
  `[Unreleased]` region's classification, and blank-line separation between
  sections. It asserts no ordering property, so the product changelog keeping
  core's newest entry adjacent to `[Unreleased]` is a convention this task
  follows and no suite mechanically checks.

**Touches:** packages/agentbundle/agentbundle/version.py,
packages/agentbundle/pyproject.toml, packages/agentbundle/CHANGELOG.md,
packages/agentbundle/README-pypi.md, docs/product/changelog.md,
tests/roster/test_okf_catalogue_discovery.py

**Done when:** AC-0007 holds, each of its five surfaces is pinned by equality
or by position in `tests/roster/test_okf_catalogue_discovery.py`, and the
routing suite passes.

### T5: One selection decides the configured base, and the screen reads it

**Depends on:** T3

**Tests:**
- The reserved-character screen reads the configured value paired with the
  resolved base by the same selection, so no input can make it screen a value
  other than the one that produced the base. Covers AC-0001, AC-0002, AC-0004.
- Driven through the real `git_commit` in a temporary repository, each of these
  refuses and stages nothing, and `HEAD` is unchanged: a repository-scope
  `output_dir` of `["x"]` with a user-scope base carrying `*`; a repository
  file whose `research` value is a container and whose `product` value is clean,
  with a user-scope `product` whose reserved character normalises away under
  resolution. Covers AC-0002, AC-0003.
- A clean configured base at either scope still stages exactly the dispatched
  item's own file, including under a repository path containing `*`. Covers
  AC-0001.
- `git_branch` and `git_push` return their unconfigured results under every
  refusing configuration above. Covers AC-0008.
- The `workspace_status` payload reports the same resolved location as the git
  path for a configured base, which `test_workspace_mcp_layout_override.py`
  already pins and this task must not regress.

**Touches:** packages/agentbundle/agentbundle/workspace_mcp.py,
packages/agentbundle/tests/test_workspace_mcp_git_scope.py

**Done when:** no second reader of the layout configuration exists, every
assertion above holds, and `test_workspace_mcp_layout_override.py` still passes
unchanged.

### T4: The design document states where wildcard structure comes from

**Depends on:** T2

**Tests:**
- Goal-based: the Git-tools description names the built-in manifest as the
  source of a staging scope's wildcard structure.

**Touches:** docs/architecture/workspace-mcp/design.md

**Done when:** the statement matches the shipped behaviour.

## Rollout

One pull request. The branch already carries the unmerged publication-screen
work, which the spec's sibling review covers and which ships together with
this.

## Risks

- The staging matrix runs real `git` subprocesses, so it is slower than a unit
  test. Accepted: the oracle has to be the production grammar, and a faster
  test over a copy of it would agree with a wrong implementation.
- An adopter whose `output_dir` contains `*` loses `git_commit` for that item
  type, having had a commit path that worked. One whose base carries another
  reserved character loses nothing measurable — commits there already matched
  nothing — and gains an explicit error. Both are the intended fail-closed
  outcome; T3's release surfaces state the remedy.

## Changelog

- Drafting: authored against the confirmed `Never do` set.
- Approved 2026-09-21 by eugenelim: scope and build strategy approved together
  after three adversarial rounds and one shaping round, all findings disposed.
- Amended 2026-09-21 under owner authority recorded in
  `notes/verification-ledger.md`, which also quotes the pre-amendment text
  verbatim. Two errors in T3's `Tests`: it credited
  `tools/test_build_site_routing.py` with an adjacency check that file does not
  make, and it named no suite for the version checks while asking of
  `README-pypi.md` only that a `What's new` section exist — neither the version
  it carries nor its position. It did already ask for the package changelog's
  topmost entry and the product changelog's first `agentbundle` entry, and that
  wording is kept. `Tests` and `Done when` now state what is asserted and where.
  `Touches` is unchanged: the routing suite is run, not edited. No acceptance
  criterion, outcome, or task boundary moved.
- Scope re-approved 2026-09-21 by eugenelim after the amendment: the acceptance
  criteria are unchanged, so the re-approval confirms the same scope.
- Build strategy re-approved 2026-09-21 by eugenelim: T3's corrected `Tests`
  and `Done when` reached clean on the third pre-EXECUTE round, the first of
  which sustained a contract-tier implementation defect now carried into
  EXECUTE and recorded in `notes/verification-ledger.md`.
- Amended 2026-09-21 under owner authority recorded in
  `notes/verification-ledger.md`. The spec's `Never do` barred modifying
  `_read_layout_bases`, which forced the reserved-character screen to read a
  second, independently computed answer about the configured base. Two review
  rounds sustained a different divergence between the two readers each, and a
  third raised a `resolve()` divergence that was adjudicated indeterminate
  because it turns on interpreter behaviour this environment cannot exercise.
  The rule now bars a second *selection* rather than a change to that function,
  which is
  what its stated purpose was always protecting. T5 carries the work; T1 and T2
  are sealed and unedited.
- Scope re-approved 2026-09-21 by eugenelim after the second amendment: the
  acceptance criteria are unchanged and one `Never do` entry was rewritten to
  bar a second selection rather than a change to `_read_layout_bases`.
- Build strategy re-approved 2026-09-21 by eugenelim: T5 added to carry the
  single-selection work, reached clean on the second pre-EXECUTE round after
  one sustained Changelog correction and one refuted decidability finding.
