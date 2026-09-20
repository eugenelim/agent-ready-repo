# Verification ledger — typed-intent-ordinal-allocator

Execution observations for this slice. Each entry records what was run, what was
observed, and what the observation settles. A claim that rests on an entry here
cites it; an entry that settles nothing is not recorded.

## 2026-09-20 — `git ls-tree` reaches the network on a partial clone

**Why run it.** The spec-stage security review claimed AC-0018's no-network
boundary did not hold, because `git ls-tree` can resolve a missing object
through a promisor remote. The finding adjudicator returned it indeterminate,
naming the missing item as fixture evidence that the planned invocation can
trigger a transport. That is machine-checkable, so it was measured rather than
argued.

**Environment.** git 2.50.1, macOS. Fixture built under `/tmp`, discarded after.

**What was run.** An upstream repository with `uploadpack.allowfilter=true`
holding three records; a `git clone --filter=tree:0 --no-checkout` of it; then
the clone's remote URL repointed at a non-existent path so any transport attempt
fails loudly rather than silently succeeding.

**Observed.**

| Invocation | Result |
| --- | --- |
| `git ls-tree -z origin/HEAD -- records/` | `fatal: could not fetch <oid> from promisor remote` — a transport was attempted |
| the same with `GIT_NO_LAZY_FETCH=1` | `fatal: not a tree object` — failed closed, no transport |
| the same with `-c remote.origin.promisor=false` | transport attempted again — **not** a control |
| the clone's config, as git wrote it | `remote.origin.promisor=true`, `remote.origin.partialclonefilter=tree:0`, and **no** `extensions.partialClone` |
| the same fixture with the per-remote key removed and `extensions.partialClone=origin` set | transport attempted — the repository-level key alone is sufficient |

**What it settles.** Three things. An argument vector free of `fetch` does not
establish that an invocation cannot reach the network, so AC-0018 could not rest
on argument inspection. `GIT_NO_LAZY_FETCH=1` is an effective control on a git
that honours it, and it landed in git 2.41 while this repository declares no git
floor — so it cannot be the only control. And git designates a promisor remote
two ways, either of which is sufficient on its own, so a check covering one key
leaves the path open on exactly the configurations an older git produces.

AC-0018 was amended twice off this entry: first to replace argument inspection
with the environment variable plus a configuration refusal, then to cover both
designations after the second security round sustained a finding that the first
amendment checked only the per-remote key.

**Not established.** Live transport behaviour on a git older than 2.41 was not
exercised; the installed git is 2.50.1. The configuration refusal is what covers
that case, and it is a configuration check rather than a version check precisely
because the version could not be observed here.

## 2026-09-20 — T1's stub earns its red

**Why run it.** `work-loop/SKILL.md:252` requires a TDD task's exact stub to
compile and earn its red from disposable scratch during PLAN, without creating a
repository test file.

**What was run.** The stub extracted from `plan.md` verbatim, compiled with
`python3 -m py_compile`, then run against a deliberately-wrong skeleton
(`token_for_level` → `None`, `classify` → `"outside"`, `next_typed_ordinal` →
`1`, `remote_view` → `absent`, `main` → `0`).

**Observed.** Compiles. **56 failed, 11 passed.**

**What it settles.** The assertions are reachable rather than vacuous. The 11
passing are the cases whose expected value the degenerate skeleton happens to
return; each is pinned by a sibling in the same parametrization rather than
standing alone, and the split is recorded so a later reader does not mistake the
stub for fully discriminating on its own.
