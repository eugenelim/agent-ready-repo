# Plan: Decision-record ordinal uniqueness

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/CONVENTIONS.md` §§ 2–3 own the record and
  companion forms; `tools/repo/build_gate_chain.py:249-278` carries two analogous
  productions of the same pattern (`lint-spec-status`, `lint-brief-coverage`),
  each a `_pytest_step` on the pack's own test followed by a `_script_step` on the
  projected copy, with `packs/core/tests/skills/work-loop/test_lint_spec_status.py`
  as the corresponding test. Named uncertainty: `next_ordinal`'s filename contract
  is pinned by an existing parametrized test, so the union must extend the answer
  without moving the predicate.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md`.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material.

## Approach

Two independent halves that meet at the gate. The script half extends the
bundled `next-ordinal.py` in `.apm/` — a record predicate and a `--check` mode,
then a git union for `next` — and reaches its six projections only through
self-host. The repair half renames four collided records and rewrites their
citations. The gate lands last, because wiring a fail-closed check before the
repair would red the chain on the first run.

The riskiest part is citation attribution, not the script. Every `ADR-0055` and
`RFC-0047` reference in the tree is ambiguous between two records, so each one
must be read and attributed before it is rewritten; a blind substitution
corrupts the citations belonging to the member that keeps its number. The index
tables carry the ordinal twice per row — once in the link and once as a bare
display column — and a substitution on the citation form or the filename fixes
the link while leaving the column wrong.

Ordering is: script, then projection and release surface, then the two repairs,
then the governance record, then the gate, then the corpus walk that proves the
whole thing over the real tree, and finally a post-review fetch that re-derives
the four ordinals and repeats that walk immediately before landing.

## Constraints

- ADR-0007 — a governance lint ships as a skill script and the catalogue runs the
  projected copy. This is why the gate invokes `.claude/skills/…` rather than a
  new file under `tools/`.
- `packs/AGENTS.md` — `.apm/` is the source of truth; every non-cosmetic pack
  change bumps `pack.toml` and `.claude-plugin/plugin.json` together and updates
  the pack's eval harness; shipped pack content carries no repository-only
  citations.
- `tools/AGENTS.md` — new `tools/` additions are pure-stdlib `.py`, and path
  triggers in `.github/workflows/docs.yml` invoke scripts as `python3 <script>`.
- `docs/CONVENTIONS.md` § 2 — an ADR is never edited after acceptance. T6 records
  the carve-out that makes the identity repair in T4 legitimate.

## Construction tests

**Integration tests:** the git-union test in T2 drives a real temporary
repository with a real remote, because the union only proves out across the git
boundary.

**Manual verification:** run the installed `new-adr` procedure end-to-end once
after T3 and record the ordinal it proposes and the `--check` exit code in the
verification ledger. The script is an artifact a user invokes directly, so a
passing unit gate does not discharge it.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale — `docs/CONVENTIONS.md` § 2 | T6 | § 2 carries the collision-repair carve-out and the git-first-landed tiebreak | The rule the repository follows is written where a maintainer looks for it |
| Interface compatibility — `docs/CONVENTIONS.md` § 3 | T6 | § 3 lists the research-sibling companion form | The predicate's companion set and § 3 agree |
| Maintainer procedure — both `SKILL.md` files | T3 | Re-derive-before-PR and `--check` appear in both procedures | Self-host projects both edits to all six copies |
| User-facing promise — `guides/governance-extras/how-to/new-adr.md` | T3 | The guide documents `--check` and the union | `python3 tools/validate_guides.py` passes |
| Release history — `pack.toml`, `plugin.json` | T3 | Both read `0.10.6` | Versions match; self-host reports no drift |
| Reusable learning — project-knowledge | T9 | Capture receipt, or `project-knowledge unavailable` | A future branch-local-invariant question finds the note |

## Design (LLD)

### Design decisions

Two predicates, not one. `next` keeps its existing filename contract unchanged —
any entry whose name starts with four or more digits followed by `-` or `.` —
because a parametrized test pins it and a `NNNN-notes/` directory sharing its
RFC's number never changes `max`. `--check` uses the stricter record predicate,
adding *is a regular file* and *does not end in `-research.md`*. Collapsing them
into one predicate would move pinned `next` behaviour for no gain. Traces to:
AC5, AC9.

The companion set is stated positively — what counts as a record — rather than as
a blocklist of companion shapes, so a new companion form is inert by default
instead of being counted as a duplicate record. Traces to: AC3, AC5.

Rejected: an allowlist of known-duplicate ordinals. It would let the gate ship
before the repair, but it converts a defect into configuration and the next
collision lands green. The repair is cheap enough that the allowlist buys
nothing.

### Interfaces & contracts

`next-ordinal.py` gains one flag, and no existing invocation changes its
output. The observable contract for both modes lives in the spec and is not
restated here. What the spec cannot say: `--check` is added as an `argparse`
flag while the bare positional path keeps its current parsing, so an adopter's
existing `next-ordinal.py <dir>` call site is untouched. Traces to: AC1–AC9.

### Quality attributes (NFRs)

The script is shipped content that runs in repositories its authors do not
control, and it gains its first subprocess call here. Three properties follow.
It never uses a shell. It never lets the calling environment redirect which
repository answers the union, which is what makes AC22 checkable rather than
aspirational. And it bounds every external call at 5 seconds, because an
allocator that hangs is worse for an adopter than one that degrades. Traces to:
AC21, AC22.

The fail-open inventory is the security-load-bearing part of this design.
`--check` is a guarding control, so every path by which it can answer "clean"
without having looked is a defect of the same kind as a missing check. The
inventory is: an absent or non-directory target, an unreadable directory, an
entry that cannot be classified, and a record-looking symlink. AC19 and AC20
close them. Traces to: AC19, AC20.

### Failure, edge cases & resilience

Every git step is best-effort. `symbolic-ref` returning non-zero, `ls-tree`
returning non-zero, a missing `git` binary, and a directory outside a repository
all degrade to the working-tree answer with exit 0. The union narrows the
collision window; it does not close it, because an unfetched remote cannot see
an ordinal that merged a minute ago. `--check` in the gate is what closes it.
Traces to: AC7, AC8.

## Tasks

### T1: `--check` names every duplicated ordinal and exits non-zero

**Depends on:** none

**Touches:** packs/governance-extras/.apm/skills/new-adr/scripts/next-ordinal.py,
packs/governance-extras/.apm/skills/new-rfc/scripts/next-ordinal.py,
packs/governance-extras/tests/skills/new-adr/test_next_ordinal.py,
packs/governance-extras/tests/skills/new-rfc/test_next_ordinal.py

**Tests:**
- Extend the existing parametrized suite in
  `packs/governance-extras/tests/skills/new-adr/test_next_ordinal.py`, which
  already loads the `.apm/` module by explicit path under a pack-and-skill-unique
  module name — reuse that loader rather than adding a second one. Verifies AC1,
  AC2, AC3, AC4, AC5.
- A seeded-collision case is the red: two records sharing one ordinal in
  `tmp_path` must make `--check` exit non-zero *before* any clean case is
  asserted, so the control is observed failing.
- A second fixture carries *two* duplicated ordinals, and asserts the full report
  text rather than the exit status. Exit status and report content are separate
  channels: a run that exits non-zero while naming only the first duplicate
  satisfies AC1 and fails AC2, and a single-duplicate fixture cannot tell them
  apart.
- Table-driven prefix cases pin AC5's digit boundary on both sides — `0042.md`
  and `12345-foo.md` are records, `42-foo.md` and `0042foo.md` are not. Without
  these a `--check` that accepted a two-digit prefix would still pass, because
  the companion fixtures only exercise the directory and research exclusions.
- The companion cases carry both forms in one directory — a `NNNN-notes`
  directory and a `NNNN-<slug>-research.md` file sharing a prefix with a record —
  because the two exclusions have separate causes and a single-form fixture would
  pass with either one missing.
- The `new-rfc` suite is the same assertions against its own copy; it is what
  catches the two scripts drifting apart.
- The fail-open cases are the security-critical half and each one is its own
  assertion: a missing target, a target that is a regular file rather than a
  directory, a directory whose read permission is removed, a record-looking
  symlink, and an enumerated entry whose classification itself fails. That last
  case is distinct and needs its own fixture: enumeration succeeds and the
  failure happens per entry, so an implementation that catches or suppresses a
  per-entry error satisfies all three directory-level cases while completing a
  partial scan and reporting clean. Each must exit non-zero. These are the cases that decide whether the
  gate is a control or a decoration — a `--check` that answers "clean" for a
  mistyped path passes every duplicate fixture above and still protects nothing.
  Verifies AC19, AC20.
- A byte comparison of the two `.apm/` copies is its own assertion, in both pack
  suites. Verifies AC10. Self-host proves each copy matches its own source; it
  cannot see the two canonical scripts drifting apart from each other.
- `stub: true` — the contract-surface assertion is `MODULE.duplicate_ordinals(d)`
  returning an empty mapping for a clean directory.

**Approach:**
- Add the record predicate and a `duplicate_ordinals(dirpath)` helper returning
  ordinal → sorted record names. It raises on an uninspectable directory rather
  than returning an empty mapping; `next_ordinal`'s existing "missing directory
  means `0001`" convention stays where it is and is deliberately not reused here,
  because for `--check` that convention is a fail-open.
- Add `--check` to `__main__` via `argparse`, keeping the bare-positional path
  unchanged.
- Copy the finished file to the `new-rfc` scripts directory.

**Done when:** both pack suites are green, including the seeded-collision case
observed red first, and the byte-identity comparison passes.

### T2: `next` answers from the union of the working tree and the remote default branch

**Depends on:** T1

**Touches:** packs/governance-extras/.apm/skills/new-adr/scripts/next-ordinal.py,
packs/governance-extras/.apm/skills/new-rfc/scripts/next-ordinal.py,
packs/governance-extras/tests/skills/new-adr/test_next_ordinal.py,
packs/governance-extras/tests/skills/new-rfc/test_next_ordinal.py

**Tests:**
- The union test builds a real temporary repository: commit `0001-a.md`, clone
  it, add `0009-b.md` on the origin, fetch, and delete the local file. The
  assertion is on the printed ordinal, which binds the test to the state change
  — a spy asserting `ls-tree` was called passes against an implementation that
  discards the output. Verifies AC6.
- The fallback cases are four, not three: not a repository, a repository with no
  remote, a remote whose HEAD ref is unset, and no `git` binary on `PATH`. The
  last is the one that cannot be produced by arranging a repository — it needs
  `PATH` emptied for the call — and it is the case a pure-repository fixture set
  silently omits. Each asserts the working-tree answer (AC7) and exit 0 (AC8)
  separately, because a fallback that returns the right number and exits
  non-zero breaks every caller.
- A blocking `git` substitute placed earlier on `PATH` proves the timeout: the
  call returns the working-tree answer within the bound instead of hanging.
  Without this the timeout is only an Approach sentence, and no gate reads
  Approach. Verifies AC21.
- The decoy-repository case is parameterized over all five variables AC22 names
  — `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY` and
  `GIT_ALTERNATE_OBJECT_DIRECTORIES` — not the two most familiar ones. Stripping
  a subset passes a two-variable test and stays redirectable through the rest.
  One further case uses a directory name carrying pathspec magic. Verifies AC22.
- The existing parametrized cases stay untouched and must stay green; they are
  the pin on `next`'s filename contract. Verifies AC9.

**Approach:**
- Resolve the ref with `git symbolic-ref --quiet refs/remotes/origin/HEAD`, read
  names with `git ls-tree --name-only <ref> -- <dir>/`, union the parsed
  ordinals with the working-tree set.
- Wrap every subprocess call so a non-zero exit, a missing binary, or a timeout
  returns the empty set rather than raising. Keep that fallback boundary strictly
  around the git calls: a broad wrapper spanning both modes would convert a
  filesystem or decoding error inside `--check` into a clean result, which is the
  fail-open AC19 forbids.
- Harden each invocation: `--literal-pathspecs` so a directory name carrying
  pathspec magic cannot change which entries are selected, `stdin` closed, a
  5-second timeout, `shell=False`, and a child environment with the
  repository-redirecting `GIT_*` variables removed. Validate that the resolved
  ref sits in the expected remote-ref namespace before using it.

**Done when:** the union test is green against a real temporary remote and all
four fallback cases return the working-tree answer at exit 0.

### T3: the script reaches all six projections and the release surface is consistent

**Depends on:** T1, T2

**Touches:** packs/governance-extras/pack.toml,
packs/governance-extras/.claude-plugin/plugin.json,
packs/governance-extras/.apm/skills/new-adr/SKILL.md,
packs/governance-extras/.apm/skills/new-rfc/SKILL.md,
packs/governance-extras/.apm/skills/new-adr/evals/evals.json,
packs/governance-extras/.apm/skills/new-rfc/evals/evals.json,
guides/governance-extras/how-to/new-adr.md, .claude/**, .agents/**

**Tests:**
- `agentbundle catalogue self-host --root . --check` is the oracle for
  projection parity; it compares all six copies against `.apm/`. Note the
  blind spot: it proves the copies match, not that the two canonical scripts
  match each other — AC10 in T1 owns that. Verifies AC18. The two version files
  are read directly for AC17.
- `python3 tools/validate_guides.py` for the guide's frontmatter contract.
- The eval files are a register, not a suite — no repository runner scores them,
  so their evidence is the presence-and-shape linters that already read them, not
  a passing eval run.

**Approach:**
- Bump both version files to `0.10.6`.
- Add the re-derive-before-PR instruction and the `--check` step to both
  `SKILL.md` procedures, in portable wording with no repository-only citation.
- Run `make build-self` on a clean tree — it refuses a dirty one.

**Done when:** self-host `--check` reports no drift and `validate_guides.py`
passes.

### T4: `docs/adr` holds one record per ordinal

**Depends on:** none

**Touches:** docs/adr/**, docs/specs/**, docs/product/**, docs/knowledge/**,
packages/agentbundle/CHANGELOG.md, tools/**, web/astro.config.ts, .gitignore,
tests/roster/**, packs/core/tests/skills/work-loop/fixtures/**

**Tests:**
- `git mv` both files, then resolve every citation. The attribution step is the
  work: enumerate `ADR-0055` and `ADR-0106` occurrences and decide per occurrence
  which record it means, using the surrounding sentence. Verifies AC13, AC16.
- The index-column assertion is separate from the link assertion because a
  substitution fixes one and silently leaves the other: after the rewrite, grep
  `docs/adr/README.md` for rows whose leading bare ordinal differs from the
  ordinal in the same row's link target. Verifies AC14.
- A markdown link-resolution pass over the changed files catches a citation
  pointing at a path that no longer exists.

**Approach:**
- `docs/adr/0055-starlight-replaces-mkdocs-for-reference-docs.md` → `0109-…`;
  `docs/adr/0106-cooled-child-scope-is-declared-on-the-entry-not-inferred-from-absence.md`
  → `0110-…`. Re-derive both targets against `origin/main` first.
- Add a `Renumbered:` line to each moved record naming its former ordinal, so the
  old number stays greppable.

**Done when:** `--check docs/adr` exits 0 and the index-column grep returns no rows.

### T5: `docs/rfc` holds one record per ordinal

**Depends on:** none

**Touches:** docs/rfc/**, docs/specs/**, docs/product/**, docs/adr/**,
docs/knowledge/**, packs/**, tests/roster/**

**Tests:**
- Same two-assertion shape as T4. `docs/rfc/README.md` rows put the ordinal
  inside the link text as `| [0092](0092-slug.md) |`, a different shape from the
  ADR index, so the column check needs its own pattern rather than a reused one.
  Verifies AC13, AC14, AC16.
- RFC-0047 is cited in 21 files and RFC-0074 in 14, mostly in the ambiguous
  `RFC-NNNN` form; the attribution pass is per-occurrence.

**Approach:**
- `docs/rfc/0047-adopter-and-org-supplied-grounding.md` → `0100-…`;
  `docs/rfc/0074-pack-config-and-oplog.md` → `0101-…`. Re-derive against
  `origin/main` first.
- Leave `0021-greenfield-inception-research.md` where it is; T6 records its form.

**Done when:** `--check docs/rfc` exits 0 and the index-column grep returns no rows.

### T6: the conventions state the rule the repository now follows

**Depends on:** T4, T5

**Touches:** docs/CONVENTIONS.md

**Contract status:** non-contract durable-output work. It owns two Durable
Outputs rows and traces to no acceptance criterion by design — its outcome is
prose, and an obligation whose only check is that a sentence exists is design
material, not a criterion. It gates closeout, not the AC set.

**Tests:**
- None. Its evidence is the reviewer pass, recorded here so the plan does not
  claim a control it does not have.

**Approach:**
- § 2 gains the carve-out: a duplicate ordinal is a defect in a record's
  identity, not its content; repairing it is the one sanctioned edit to an
  Accepted ADR, and the member that landed on the default branch first keeps the
  number.
- § 3 gains one line recording `NNNN-<slug>-research.md` alongside `NNNN-notes/`.

**Done when:** both sections state the rules T4, T5 and T1 implement, and the
`Follow-ons` entry in `spec.md` names the unconsolidated companion form.

### T7: the chain reds on a duplicated ordinal

**Depends on:** T3, T4, T5

**Touches:** tools/repo/build_gate_chain.py, .github/workflows/docs.yml

**Tests:**
- Seed a duplicate into a scratch copy of `docs/adr`, run the chain step, observe
  non-zero; remove it, observe zero. Then repeat through the `docs/rfc` step.
  Both routes are seeded, because one seeded route leaves the other free to be
  absent or miswired and still green. Red before green. Verifies AC11.
- The step's script path is asserted to resolve under `.claude/skills/` — that is
  what makes it the projected copy an adopter would also run. Verifies AC12.

**Approach:**
- Add to `build_check`, following the existing pair shape: a `_pytest_step` on
  `packs/governance-extras/tests/skills/new-adr/test_next_ordinal.py`, then two
  `_script_step`s invoking the projected `new-adr` and `new-rfc` copies with
  `--check docs/adr` and `--check docs/rfc`.
- Add the touched script and test paths to the `docs.yml` path triggers.

**Done when:** a seeded collision in each of the two directories exits non-zero
and the clean run exits 0.

### T8: the predicate is walked against the real corpus

**Depends on:** T1, T4, T5

**Touches:** tests/roster/test_decision_record_ordinal_uniqueness.py

**Tests:**
- Walk every shared-ordinal group in `docs/adr` and `docs/rfc` and print the
  cross-product of ordinal against classification, so a reader can tell a clean
  tree from a walk that reached nothing. Verifies AC13.
- Assert the group count is non-zero before asserting no group is a duplicate;
  without that floor the test passes on an empty directory.
- Assert each retained record still holds its ordinal by filename, as four
  separately reported cases rather than one conjunction, so a partial repair
  names which pair failed. Verifies AC16.
- Search every tracked path for each of the four pre-repair filenames and require
  zero matches outside this spec's own directory. This is the decisive oracle for
  AC15: T4 and T5 resolve citations in the files they touch, which cannot see a
  stale reference in a file neither task opened. The suite builds each needle by
  joining its ordinal to its slug at runtime rather than storing the contiguous
  filename, so the test does not match itself and turn a clean tree red.
  Verifies AC15.

**Approach:**
- New roster suite; load the projected module by explicit path under a unique
  module name, per the pack test-boundary rule.

**Done when:** the suite is green and its printed cross-product lists twenty
companion groups and no duplicate group.

### T9: the learning is captured

**Depends on:** T7, T8

**Touches:** docs/knowledge/**

**Contract status:** non-contract closeout work, outside the acceptance task
graph. It traces to no acceptance criterion, and the `unavailable` branch is a
genuine outcome rather than a skipped obligation — the capture seam may not be
installed.

**Tests:**
- None. The capture receipt is the evidence, or `project-knowledge unavailable`
  is recorded.

**Approach:**
- Capture the generalisable lesson: an invariant that holds within a branch and
  breaks only against the default branch is invisible to review by construction,
  so it needs a pre-push or CI check rather than another review round.

**Done when:** the receipt exists, or the unavailable marker is recorded.

### T10: the four ordinals are still free at the moment of landing

**Depends on:** T4, T5, T7, T8

**Touches:** docs/adr/**, docs/rfc/**

**Contract status:** this task exists because the repair can instantiate its own
root cause. T4 and T5 re-derive before *choosing* the rename; nothing in them
re-derives before *landing* it, and the interval between the last push and the
merge is exactly the window this spec was written about. A mitigation that lives
only in the Risks section is prose no gate reads.

**Tests:**
- `git fetch origin`, then derive the four targets from the **fetched remote
  snapshot alone**, never through the union allocator. After T4 and T5 the
  working tree already occupies `0109`, `0110`, `0100` and `0101`, so the union
  allocator would return `0111` and `0102` even when upstream has not moved, and
  the comparison would fail every time for the wrong reason. The derivation is:
  take the highest record ordinal in `docs/adr` on the fetched ref, assign the
  next two sequentially, and do the same for `docs/rfc`. Compare those four with
  the branch's four. A difference is a stop, not a warning.
- Re-run the T8 corpus walk after the fetch, against the updated remote state.
  Verifies AC13, AC15, AC16 hold at land time and not merely at rename time.

**Approach:**
- Run immediately before merge, after the final review round. If any target
  ordinal has been taken upstream, redo the affected rename and its citation
  pass rather than merging over the collision.

**Done when:** the post-fetch re-derivation returns the four ordinals already on
the branch, and the corpus walk is green against the fetched state.

## Rollout

Pure repository change — no infrastructure, no external system, no deployment
sequencing. One ordering constraint: the gate (T7) lands after the repairs (T4,
T5), because a fail-closed check wired before the repair reds the chain on its
first run. Rollback is `git revert`; the renames are reversible and nothing is
published outside the repository.

## Risks

- **Citation attribution is per-occurrence judgement.** `ADR-0055` and `RFC-0047`
  are each ambiguous between two records across roughly 48 files combined. A
  blind substitution is fast and wrong. Mitigation: the two-assertion shape in T4
  and T5 catches the index columns; a link-resolution pass catches dead paths;
  neither catches a citation rewritten to the wrong sibling, so that stays a
  reviewer obligation.
- **The four target ordinals can be taken while this branch is in review.** This
  is the exact defect the spec exists to fix, and the repair can instantiate its
  own root cause. Mitigation: T10 re-derives after the final review round and
  immediately before landing, which is the interval a pre-push check alone leaves
  open. Re-deriving at branch start is what fails.
- **`make build-self` refuses a dirty tree**, so T3 must run against committed
  work, not mid-edit.
- **Local suite selection.** `make test` is roughly eighty suites and runs for
  minutes; run only the touched suites. pytest and build-check cannot run
  concurrently in this worktree, and `build/` and `dist/` are cleaned before any
  `make ci`.

## Changelog

- 2026-09-12: initial plan.
- 2026-09-12: a throwaway spike over the real corpus confirmed the record
  predicate finds exactly the four known collisions with no false positive across
  all twenty companion cases, and that the union resolves
  `refs/remotes/origin/main` and re-derives ADR `0109` / RFC `0100` in 1.4s wall.
  The spike was not committed. It did not change the approach; it removed the
  open question of whether the companion exclusions were sufficient.
- 2026-09-12: split the record predicate from `next`'s filename predicate after
  reading the existing parametrized test, which pins `0042.md` as counting and
  `0042foo.md` and `42-foo.md` as not. A single shared predicate would have moved
  pinned behaviour for no gain.
- 2026-09-12: spec review round 1 (Codex, read-only). Two Blockers sustained — the
  collision-repair mitigation was prose with no owning task, now T10; and the two
  canonical scripts had no byte-identity criterion, now AC10. Nine Concerns
  sustained, mostly missing red cases (absent-`git` fallback, the `--check` digit
  boundary, the second seeded gate route, a decisive repository-wide filename
  search). Four "split this criterion" Concerns were refuted: AC11, AC13, AC14 and
  AC16 each substitute one predicate over an enumerated set, which the spec's
  worked example E2 keeps as one criterion, and the reviewer's rationale appealed
  to task decomposition rather than predicate shape. Criteria renumbered to
  AC1–AC18 as a result.
- 2026-09-12: spec review round 2, delta-bounded. All four findings carried
  `prior-round-repair` origin — round 1's own repairs produced them, which is the
  convergence signal. The Blocker was real: round 1's strengthened AC15 was
  unsatisfiable, because `plan.md` necessarily names the four pre-repair
  filenames and the roster suite would have matched itself. AC15 now excludes
  this spec's directory, and T8 builds its needles at runtime. T10's
  re-derivation was ambiguous — after T4 and T5 the union allocator returns
  `0111`/`0102` rather than the branch's targets — so it now derives from the
  fetched remote snapshot alone.
- 2026-09-12: spec-stage security review. Two Blockers. The first was a genuine
  fail-open: nothing in the contract distinguished "proved clean" from "could not
  inspect", and the pre-change `next_ordinal` precedent of answering `0001` for a
  missing directory would have made `--check` exit 0 on a mistyped path — a gate
  that protects nothing while passing every duplicate fixture. AC19 and AC20 close
  that, plus the symlink ambiguity in AC5's "regular file". The second Blocker —
  two branches independently choosing one ordinal and both going green — is real
  but narrower than reported: `build-check.yml` runs on `pull_request`, so the
  gate already evaluates the pull-request merge reference against the current
  base. The residual stale-green window needs an up-to-date-branch rule or a
  merge queue, which are repository settings and are recorded under Follow-ons
  rather than claimed here. Two Concerns and one Low sustained: the timeout was
  Approach-only prose that no gate reads (now AC21), and git pathspec magic plus
  `GIT_*` redirection could steer the union (now AC22).
- 2026-09-12: security confirming round. Three findings, all narrow gaps between
  a criterion and its test rather than new defects. AC19 named an
  unclassifiable-entry condition that T1's four fixtures did not reach — a
  per-entry failure leaves enumeration working, so the three directory-level
  cases all pass while the scan silently completes partial. AC22 named five
  redirecting variables while the test exercised two, which a subset-stripping
  implementation would survive. One unconditional clause survived in the
  Objective after the merge-reference rewrite and is now qualified.
