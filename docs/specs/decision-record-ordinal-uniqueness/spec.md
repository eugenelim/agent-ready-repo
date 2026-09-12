# Spec: Decision-record ordinal uniqueness

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0007 (a governance lint ships as a skill script, and the catalogue runs the projected copy)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — the changed surface is a bundled skill script's command line, not a versioned interface file under `contracts/`.
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Objective

A maintainer opening an ADR or an RFC gets an ordinal that is theirs. The
bundled `next-ordinal.py` answers `next` from the union of the working tree and
the remote default branch, so a branch that has sat in review stops proposing a
number that merged upstream while it waited. Its `--check` mode answers the
other half: given a decision-record directory, it names every ordinal held by
more than one record and exits non-zero, so a collision present in the
prospective merge when the gate runs is caught there rather than on the default
branch. This repository runs that check
fail-closed over `docs/adr` and `docs/rfc`, and both directories hold one record
per ordinal.

The user is any adopter of the `governance-extras` pack, which installs the same
script into `new-adr` and `new-rfc` for every supported assistant. Success is
that the number a maintainer is handed is free across the working tree and the
resolved remote default branch, and that a duplicate present in the prospective
merge reds the gate. Both halves are snapshots rather than reservations. The
allocator's snapshot is the weaker one: an ordinal that merges upstream after it
runs is invisible to `next`. The gate's is stronger, because it runs on the
pull-request merge reference and so sees the head merged into the current base —
and the protected branch requires an up-to-date base, so a branch whose base has
moved re-runs the gate before it can merge. Two branches that each pick `0123`
under different slugs would otherwise both go green and the second would merge on
a stale pass, because the differing filenames give git no conflict to raise; the
up-to-date requirement is what forecloses that, and it sits in branch
protection rather than in this script.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable — ordinal uniqueness had no owner, and the repair edits Accepted records | `docs/CONVENTIONS.md` § 2 | Repository maintainer | The § 2 carve-out names collision repair as the one sanctioned edit to an Accepted ADR's identity, and names the git-first-landed tiebreak | § 2 states the rule the repository now follows |
| Interface compatibility | Applicable — `NNNN-<slug>-research.md` is a companion form § 3 did not record | `docs/CONVENTIONS.md` § 3 | Repository maintainer | § 3 lists the research-sibling form alongside `NNNN-notes/` | The predicate's companion set and § 3 agree |
| Maintainer procedure | Applicable — the re-derive-before-push rule is the behavioural half the script cannot enforce | `SKILL.md` in `new-adr` and `new-rfc` | Pack maintainer | Both procedures tell the author to re-derive the ordinal immediately before opening the PR and to run `--check` | Self-host projects both edits |
| User-facing promise | Applicable — the how-to documents this script | `guides/governance-extras/how-to/new-adr.md` | Pack maintainer | The guide names `--check` and the union behaviour | `python3 tools/validate_guides.py` passes |
| Release history | Applicable — pack content changed | `packs/governance-extras/pack.toml` and `.claude-plugin/plugin.json` | Pack maintainer | Both read `0.10.6` | Versions match and self-host reports no drift |
| Reusable learning | Applicable — the collision is invisible to review by construction | `project-knowledge` capture at the work-loop gates | Work-loop | A captured observation that a branch-local invariant cannot be reviewed against the default branch | Capture receipt exists or `project-knowledge unavailable` is recorded |
| Current architecture | Not applicable | — | — | — | No module boundary, layer, or ownership line moves; the script keeps its home and its callers |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit `packs/governance-extras/.apm/skills/<skill>/scripts/next-ordinal.py` and
  reach the `.claude/` and `.agents/` copies by running self-host.
- Keep the `new-adr` and `new-rfc` copies of the script byte-identical to each
  other.
- Read an ambiguous `ADR-NNNN` or `RFC-NNNN` citation and attribute it to one
  member of its pair before rewriting it.
- Re-derive the four target ordinals against `origin/main` immediately before
  pushing.

### Ask first

- Changing which member of a collided pair keeps its ordinal.
- Adding an allowlist, suppression, or exemption to `--check` for any directory.
- Moving `0021-greenfield-inception-research.md`, or any other existing record,
  to a different companion form.

### Never do

- Wire this check into `tools/hooks/pre-pr.py`. That file is projected to
  adopters and would call a script absent from their tree.
- Add a new top-level directory, a new module boundary, or a dependency outside
  the Python standard library. The script stays stdlib-only, and the gate adds
  no file under `tools/`.
- Rewrite an ordinal citation by blind substitution. Every pair has a member
  that keeps its number, and a blind pass corrupts that member's citations.
- Edit a `.claude/` or `.agents/` projection directly.
- Let `next` fail because git is absent, the directory is outside a repository,
  or the remote ref is unfetched.

## Testing Strategy

**TDD** for the record predicate and the duplicate report (AC1–AC5). The
predicate is a compressible invariant over a filename: a closed set of inputs
maps to a two-valued answer, which is the shape a unit test pins exactly. AC1 and
AC2 are exercised separately because exit status and report content are separate
channels — a run that exits non-zero while omitting the second duplicated ordinal
satisfies one and fails the other. AC5 needs cases on both sides of the digit
boundary, not only the two companion exclusions, or an implementation that
accepted `42-foo.md` would still pass.

**TDD** for the union and its fallback (AC6–AC9), exercised as an **integration**
test. The union only proves out across the git boundary, so the test drives a
real temporary repository with a real remote rather than a patched `subprocess`:
a spy that proves the call happened would pass against an implementation that
discards the result. Every degraded condition in AC7 is exercised — the plan
enumerates four fixtures across them, because an unresolvable ref arises both
from a repository with no remote and from a remote whose HEAD is unset. The
absent-`git` case is the one that cannot be produced by arranging a repository
at all, and needs the binary hidden from `PATH`.

**Goal-based check** for byte identity (AC10) — a file comparison is the whole
assertion.

**Corpus walk** — a TDD-mode test whose inputs are the recorded repository rather
than a fixture (AC13, AC16). The predicate is walked against every shared-ordinal
group in `docs/adr` and `docs/rfc` and the cross-product is printed, because a
spot-check cannot distinguish "no duplicates" from "the walk reached nothing".
AC16's four pairs are reported case by case so a partial repair is visible rather
than averaged into one pass.

**Goal-based check** for the gate wiring and the release surface (AC11, AC12,
AC14, AC15, AC17, AC18). Each is verified by one command whose exit code is the
answer — a chain run, a grep over the index rows, a tracked-path search, a
version read, a self-host check. A unit test here would assert what the command
already proves. AC11 is seeded through both the `docs/adr` and the `docs/rfc`
route, because one seeded route leaves the other free to be absent or miswired.

The red-before-green rule applies to every criterion above: the check is shown
failing against a seeded collision before it is shown passing against the
repaired tree. A control that has only ever been observed green is
indistinguishable from one that cannot fail.

## Acceptance Criteria

- [ ] **AC1 — `--check` reds on a duplicated ordinal.** Given a directory where
      two records share one ordinal, `next-ordinal.py --check <dir>` exits
      non-zero.
- [ ] **AC2 — `--check` reports every duplicate.** On that same run it names
      every ordinal held by more than one record, each with its competing record
      names. A directory holding more than one duplicated ordinal reports all of
      them.
- [ ] **AC3 — `--check` greens on a companion.** Given a directory whose only
      repeated ordinal prefixes belong to companions, `next-ordinal.py --check
      <dir>` exits zero.
- [ ] **AC4 — A clean `--check` is silent.** On that same run it prints nothing
      to stdout.
- [ ] **AC5 — A record is a regular file with an ordinal prefix and no research
      suffix.** `--check` counts as a record exactly those directory entries that
      are regular files, whose name begins with four or more digits followed by
      `-` or `.`, and whose name does not end in `-research.md`. A directory
      entry is never a record.
- [ ] **AC6 — `next` answers from the union.** `next-ordinal.py <dir>` prints one
      more than the highest record ordinal in the union of the working tree and
      the remote default branch.
- [ ] **AC7 — `next` degrades to the working tree.** `next-ordinal.py <dir>`
      prints the working-tree-only answer when no remote default branch ref
      resolves, when the directory is outside a repository, and when no `git`
      binary is available.
- [ ] **AC8 — A degraded `next` still succeeds.** On each of those runs it exits
      zero.
- [ ] **AC9 — `next` keeps its pinned filename contract.** `next-ordinal.py
      <dir>` returns its pre-change answer for every name the existing
      parametrized suite pins: `0042.md` counts, `0042foo.md` and `42-foo.md` do
      not, and `00099-bar.md` yields `0100`.
- [ ] **AC10 — The two shipped scripts are one script.** The `new-adr` and
      `new-rfc` copies of `next-ordinal.py` under `.apm/` are byte-identical to
      each other.
- [ ] **AC11 — The chain reds on a duplicate.** The `build-check` chain exits
      non-zero when either `docs/adr` or `docs/rfc` holds a duplicated ordinal.
- [ ] **AC12 — The chain runs the artifact adopters run.** Each ordinal-check
      step in the `build-check` chain executes a projected copy rather than the
      `.apm/` source, observable as a step whose script path resolves under
      `.claude/skills/`.
- [ ] **AC13 — Both record directories are clean.** `--check` exits zero against
      `docs/adr` and against `docs/rfc`.
- [ ] **AC14 — Each index row agrees with itself.** Every row of
      `docs/adr/README.md` and `docs/rfc/README.md` carries a bare ordinal column
      equal to the ordinal in that row's link target.
- [ ] **AC15 — No pre-repair filename survives outside the rename's own
      record.** A search over every tracked path for each of the four pre-repair
      filenames returns zero matches, excluding
      `docs/specs/decision-record-ordinal-uniqueness/`. That directory is
      excluded because it is the audit record of the rename and has to name what
      moved; every other path naming an old filename is a stale reference.
- [ ] **AC16 — The retained member keeps its ordinal.** For each of the four
      collided pairs, the retained record still carries its original ordinal, and
      each pair is reported separately so a partial repair is visible: ADR-0055 is
      `wave1-docs-restructure-contracts-and-guides-to-repo-root`, ADR-0106 is
      `direct-skill-identity-and-upgrade-revision-route`, RFC-0047 is
      `default-source-on-discovery-verbs`, and RFC-0074 is
      `fidelity-ladder-and-ephemeral-env-qualification`.
- [ ] **AC17 — The release surface moves together.**
      `packs/governance-extras/pack.toml` and
      `packs/governance-extras/.claude-plugin/plugin.json` both read `0.10.6`.
- [ ] **AC18 — The projections match their source.** `agentbundle catalogue
      self-host --root . --check` reports no drift.
- [ ] **AC19 — An incomplete scan is not a pass.** `--check` exits zero only
      after completely enumerating an existing directory. A target that is
      missing or is not a directory, a directory that cannot be enumerated, and
      an entry that cannot be classified each exit non-zero and say which
      condition fired. "Proved clean" and "could not inspect" are different
      answers, and the pre-change `next_ordinal` convention of returning `0001`
      for a missing directory is not carried into `--check`.
- [ ] **AC20 — A record-looking symlink is an integrity error.** A directory
      entry whose name satisfies the record predicate but which is a symlink
      rather than a regular file exits non-zero naming that entry, rather than
      being silently counted or silently skipped. Silently skipping it would let
      two record-looking paths share an ordinal while the gate stayed green.
- [ ] **AC21 — A hung `git` does not hang the caller.** Each git invocation
      carries a finite timeout of 5 seconds. On expiry `next` returns the
      working-tree answer and exits zero, the same as every other degraded
      condition.
- [ ] **AC22 — The environment cannot redirect the union.** `next` returns the
      same ordinal when `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`,
      `GIT_OBJECT_DIRECTORY` or `GIT_ALTERNATE_OBJECT_DIRECTORIES` are set in the
      calling environment to another repository, and a directory whose name
      contains git pathspec magic such as `:(glob)` does not change which entries
      are counted.

## Follow-ons

- Repository maintainer: `docs/CONVENTIONS.md` § 3 — the `NNNN-<slug>-research.md`
  companion form is recorded rather than consolidated. Whether the repository
  keeps two companion forms or folds research siblings into `NNNN-notes/` is a
  separate governance call, and the predicate accepts either.

## Assumptions

- Technical: every `.claude/` and `.agents/` projection of `next-ordinal.py` is
  byte-identical to its `.apm/` source across both skills (source: `cmp -s` over
  all four pairs, 4/4 identical, 2026-09-12).
- Technical: the remote default branch resolves as
  `git symbolic-ref refs/remotes/origin/HEAD`, and record names are readable with
  `git ls-tree --name-only <ref> -- <dir>/` (source: probe on this checkout
  returning `refs/remotes/origin/main`, 2026-09-12).
- Technical: a governance lint is wired into the chain as a `_pytest_step` on the
  pack's own test followed by a `_script_step` on the projected copy (source:
  `tools/repo/build_gate_chain.py:249-257`).
- Technical: chain gates that resolve a base ref fail open without full history;
  `--check` resolves no base ref (source:
  `.github/workflows/build-check.yml:77`).
- Technical: the corpus is four genuine collisions and twenty companion cases —
  nineteen `NNNN-notes/` directories and one research sibling (source: directory
  walk over `docs/adr` and `docs/rfc`, 2026-09-12).
- Process: the pack version lives in two files that move together (source:
  `packs/governance-extras/pack.toml:3` and `.claude-plugin/plugin.json:3`, both
  `0.10.5`).
- Process: `evals.json` is a register checked for presence and shape, not a suite
  any repository runner scores (source: its only consumers are
  `tools/test_check_output_readability.py:85` and
  `tools/check-atlassian-phase3-readiness.py:491`).
- Process: the member of a collided pair that landed on the default branch first
  keeps its ordinal; the `**Date:**` field records when a decision was made and
  inverts the real claim order on both ADR pairs (source: user confirmation
  2026-09-12, over `git log --diff-filter=A` evidence).
- Process: `docs/CONVENTIONS.md` § 2 gains a carve-out naming collision repair as
  the one sanctioned edit to an Accepted ADR (source: user confirmation
  2026-09-12).
- Product: the check ships to adopters in the pack rather than staying a
  repository-only lint (source: user confirmation 2026-09-11).
- Process: `main` requires an up-to-date base before merging and lists `make
  build-check` among its five required status checks (source:
  `gh api repos/:owner/:repo/branches/main/protection` returning
  `strict: true` and that context, 2026-09-12). Both facts are load-bearing:
  placing the ordinal check inside the `build-check` chain is what makes it
  merge-blocking, and the up-to-date requirement is what stops a branch whose
  base has moved from merging on a stale pass. An adopter without either setting
  gets a check that reports but does not block.
- Process: the acceptance criteria use this repository's dominant `ACn` label
  form, which 131 of the indexed specs share and which
  `lint-contract-item-alignment.py` does not read — it recognises only the
  `AC-0001.` form, used by exactly one spec. That lint therefore reports this
  spec as "skipped as unlabelled" rather than checking it, so its green result is
  not evidence here. Identifier uniqueness and criterion-to-task tracing were
  established by review instead: 18 of 18 criteria traced to a task's `Tests:`
  bullet (source: measured counts and spec review round 2, 2026-09-12).
