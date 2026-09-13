# Verification ledger — decision-record-ordinal-uniqueness

Execution observations. The spec holds the contract and the plan holds the
strategy; neither is edited to record what happened here.

## Manual QA — the artifact a user invokes

`next-ordinal.py` is invoked directly by an adopter, so a passing unit gate does
not discharge it. Run against the real tree on 2026-09-12:

| Invocation | Observed |
| --- | --- |
| `--check docs/adr` (pre-repair) | exit 1, named `0055` and `0106` with both competing filenames |
| `--check docs/rfc` (pre-repair) | exit 1, named `0047` and `0074` |
| `--check docs/adr` (post-repair) | exit 0, `no duplicate ordinals` on stderr, stdout empty |
| `--check docs/rfc` (post-repair) | exit 0, same |
| `--check docs/typo-does-not-exist` | exit 1, `could not inspect … directory does not exist` |
| `docs/adr` | `0111` — 108 ordinals read from `origin/main`, local max 110 |
| `docs/rfc` | `0102` — 98 ordinals read from `origin/main`, local max 101 |

## Mutation evidence

A green control that has never been observed red is indistinguishable from one
that cannot fail, so every criterion was driven red first.

**Record predicate (7/7 killed).** Both fail-open paths, the symlink skip, a
swallowed classification error, both companion exclusions, and the digit
boundary were each reintroduced independently; each failed the suite.

**Post-review fixes (3/3 killed).** Reverting the `lstat` classification, the
`ls-tree -z` flag, or the narrowed `resolve()` handler each reds the suite.

**Gate.** Seeded a duplicate into `docs/adr`, observed the chain step exit 1;
removed it, observed 0. Repeated independently through the `docs/rfc` step,
because one seeded route leaves the other free to be absent and still green.

**Index check.** The column-versus-link predicate finds 2 mismatched rows on the
pre-repair index and 0 on the repaired one, over 110 ADR rows and 97 RFC rows.

## Observations worth keeping

**The union was a no-op in production while its suite was green.** The first
implementation ran `ls-tree` from the target directory while passing a
repository-root-relative pathspec. Git resolves a pathspec relative to the
current directory, so it searched for `docs/adr/` underneath `docs/adr/` and
matched nothing, silently. The fixture built its records at the repository root,
the one shape where that pathspec resolves and one no real caller has. After
defaulting the fixture to a subdirectory, reintroducing the defect fails 8 tests
rather than the 1 that had caught it by accident.

**The fail-closed check was not fail-closed.** `Path.is_symlink()` and
`Path.is_file()` return False on any `OSError` rather than raising, so the
`except OSError` around them was unreachable and an entry that vanished between
listing and classification was dropped silently. The covering test had patched
`Path.is_symlink` to raise, proving the handler against behaviour the real call
never exhibits.

**A clean gate is invisible in a build log.** A silent success makes a step that
passed and a step that was never wired look identical. The check now confirms on
stderr, which leaves AC4's stdout silence intact.

**The index had already absorbed both collisions, in three different ways** — a
suffixed `0055a`/`0055b` form the conventions define nowhere, a duplicated bare
`0106` with a note asserting neither record would be renumbered, and, in the RFC
index, a dropped row: both keepers had no entry at all. The column-versus-link
check could never have found the `0106` pair, because those rows agreed with
their own targets and disagreed only with each other.

## Environment

`make build-check` was green before the merge with `origin/main`. After the
merge a bare self-host failed on `packs/architect/pack.toml` — a file this
branch never touched — because the installed `agentbundle` was 0.43.0 against a
0.44.0 worktree and the bundled schema predated upstream's `section` field. The
repository's own `contracts/pack.schema.json` allows it. Resolved by reinstalling
the package from `packages/agentbundle`, not by routing around it.

One `semgrep --strict` timeout was observed on `loop-cohort.py` at a 1-minute
load average of 85 on 10 CPUs. The file is outside this diff and passes in
isolation; the condition is already registered as
`docs/product/intents/semgrep-registry-ruleset-pinning.md`.
