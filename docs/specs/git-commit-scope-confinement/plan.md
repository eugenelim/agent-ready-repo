# Plan: git_commit scope confinement

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
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

Owned by: T2

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
- Goal-based: `version.py` and `pyproject.toml` both read `0.47.3`; the package changelog's
  topmost entry and the product changelog's first `agentbundle` entry carry
  that version; `README-pypi.md` has its `What's new` section. Covers AC-0007.
- The product changelog keeps core's newest entry adjacent to `[Unreleased]`,
  checked by `tools/test_build_site_routing.py`.

**Touches:** packages/agentbundle/agentbundle/version.py,
packages/agentbundle/pyproject.toml, packages/agentbundle/CHANGELOG.md,
packages/agentbundle/README-pypi.md, docs/product/changelog.md,
tests/roster/test_okf_catalogue_discovery.py

**Done when:** AC-0007 holds and the routing suite passes.

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
