# ADR-0085: Lints resolve Git-ignore status in one batched call over stdin

- **Status:** Accepted
- **Date:** 2026-08-17
- **Decision-makers:** eugenelim
- **Consulted:** security review, adversarial review
- **Supersedes:** the **`--` terminator** requirement in
  [`docs/specs/pack-test-boundary-remaining-packs/`](../specs/pack-test-boundary-remaining-packs/spec.md)'s
  `AC10a` only — that spec's `os.walk(followlinks=False)` symlink prune, its
  per-pack projection assertion, and every other acceptance criterion stand
- **Related:** the implementing spec
  [`docs/specs/lint-performance-p0/`](../specs/lint-performance-p0/spec.md);
  `tools/lint_git_ignore.py` carries the operative rules and
  `tools/lint-no-direct-check-ignore.py` enforces them

## Decision summary

- **Decision:** A lint that needs Git-ignore status sends its whole candidate
  set through one `git check-ignore --stdin -z` call, with candidates
  NUL-delimited on **stdin** as bytes. No production lint launches one process
  per path, and the `--` argv terminator becomes moot because no path reaches
  argv at all.
- **Because:** the per-path form cost hundreds of subprocesses and tens of
  seconds on every run of one lint, which pushed its falsification suite past the
  work-loop's five-minute inner-loop budget. Measured figures: the implementing
  spec's audit note.
- **Applies to:** every production lint under `tools/`, `packs/` and
  `packages/`. Portable `agentbundle` code and shipped pack content are
  unaffected — measurement found neither queries Git ignore at all.
- **Tradeoff accepted:** one process now answers for the whole set, so a single
  unusable candidate spoils the entire batch rather than just itself. That is
  why a non-0/1 exit is a hard error here instead of a policy outcome.
- **Revisit if:** Git changes `check-ignore --stdin` to report per-path status
  rather than echoing only matches, or gains a mode that reports *why* a path is
  ignored without a per-path invocation.

## Context

[`docs/specs/pack-test-boundary-remaining-packs/plan.md:636`](../specs/pack-test-boundary-remaining-packs/plan.md)
already specified this work:

> Add the `--` terminator to `git check-ignore` **and batch paths over stdin
> rather than one subprocess per file.**

Only the first clause shipped. `tools/lint-pack-test-boundary.py` gained the
terminator; the batching was never implemented, and the per-path loop survived
inside the tree walk, invisible in review because each call is individually
unremarkable.

The cost was not. One lint invocation launched a `check-ignore` process per
candidate path and took tens of seconds; that lint's own falsification suite
launched it twelve times, landing just past the 300 s budget. A local run reached
71% and never completed — read at the time as a stall, but in fact a correct suite
sitting a few seconds the wrong side of a cutoff. Exact counts and timings are in
the implementing spec's audit note.

## Decision

Candidates go over **stdin**, NUL-delimited, encoded with `os.fsencode`:

```
git check-ignore --stdin -z
```

Four properties of that spelling are load-bearing, each settled against a probe
of git 2.50.1 rather than from documentation:

1. **NUL framing is the only safe delimiter.** A filename may contain a space, a
   tab, a newline, a leading dash, or arbitrary Unicode. All five round-trip
   intact; a newline in particular would corrupt any line-oriented protocol.

2. **Bytes, not `str`.** A filename need not be valid UTF-8 on Linux, and
   `str.encode` on a surrogate-escaped name raises `UnicodeEncodeError` — a
   `ValueError`, which neither `OSError` nor `SubprocessError` handling catches.

3. **`--no-index` stays absent.** Its omission is what keeps tracked files
   excluded from the ignored set, exactly as the per-path call had it. Adding it
   would silently change which files count as authored.

4. **A `:`-prefixed candidate is refused before the call.** `check-ignore
  --stdin` *does* parse pathspec magic: `:!x`, `:(exclude)x`, `:(glob)x`,
  `:(icase)x` and `:(attr:…)x` each exit 128 while echoing only the candidates
  processed before them. A `:(literal)` prefix is not an escape hatch — this
  subcommand rejects it outright.

### Why the `--` terminator is superseded rather than dropped

`--` existed to stop a path that looks like an option from being parsed as one.
With `--stdin` there are no argv paths for it to disambiguate, and the
protection is *stronger*, not weaker: candidates leave argv entirely for a
NUL-framed stream that no option parser reads. `AC10a`'s literal wording is
nonetheless now false, hence this ADR and the `Status`-field pointer on that
spec.

### Partial results are a hard error

Git exits 128 for the **whole invocation** on one unusable path — outside the
repository, inside a nested Git root, or carrying unsupported pathspec magic —
while still echoing the candidates it processed first. That partial result is the
trap the batched form introduces: discarding it silently loses ignore
information, and trusting it silently under-reports. Under the per-path form the
blast radius was one path; under batching it is the entire set. So any exit other
than 0 or 1 raises, carrying Git's stderr, and is never routed through the
missing-Git policy.

### "Nothing is ignored" is not a safe default

The resolver reports *degradation* separately from an empty result, because the
two are different facts and at least one caller cannot tell them apart safely.
`tools/lint-pack-test-boundary.py` **subtracts** the ignored set from what its
walk found, and two of its findings fire on the *emptiness* of what remains — so
reporting "nothing is ignored" when Git never answered converts those failures
into passes. Both call sites therefore treat a degraded resolution as fatal:
diagnose it, and refuse to report an ignore-derived verdict from an unresolved
layer.

Git absence already behaved this way before this decision. What is new is the
bounded timeout the batched call requires, which is a second, quieter route to
the same state.

### Every Git subprocess is hermetic

Every Git subprocess — the resolver's, and every staged-subject run in the
capture harness — goes through one shared helper, `hermetic_git_env`. A second
implementation is how a fix lands in one place and not the other, and one of
those places is the path that *writes* the committed baseline.

The scrub sets `GIT_CONFIG_NOSYSTEM=1`, points `GIT_CONFIG_GLOBAL` and
`GIT_CONFIG_SYSTEM` at an empty file, and unsets `GIT_DIR`, `GIT_WORK_TREE`,
`GIT_INDEX_FILE`, `GIT_COMMON_DIR`, `GIT_CEILING_DIRECTORIES`,
`GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES` and `GIT_CONFIG`.

It must also drop **`GIT_CONFIG_COUNT` and its `GIT_CONFIG_KEY_n` /
`GIT_CONFIG_VALUE_n` pairs**, and that one is easy to miss: it survives
`GIT_CONFIG_NOSYSTEM` and the redirected config files, and it is the only channel
that leaks *silently*. Verified — with `GIT_CONFIG_COUNT=1` pointing
`core.excludesFile` at a hostile file, `check-ignore --stdin -z` reported an extra
path as ignored and exited **0**. By contrast `GIT_GLOB_PATHSPECS`,
`GIT_ICASE_PATHSPECS` and `GIT_LITERAL_PATHSPECS` make the subcommand exit 128,
which the hard-error rule above already catches; they are dropped too, but they
were never the dangerous case.

This is not hygiene for its own sake. A `git init`-ed directory still honours
`core.excludesFile`: with a global ignore file matching `tests/`, a fixture's pack
test comes back *ignored*, and given the subtraction above those failures would be
captured as required **passes** and reproduce green indefinitely — the exact
outcome the capture harness exists to prevent. The same leak is live outside test
fixtures: Git sets `GIT_DIR` and `GIT_INDEX_FILE` for hook processes, and these
lints run from a pre-PR hook.

## Alternatives considered

- **Keep one process per path.** Correct, and simple. Rejected on measured cost:
  it is the entire defect.
- **A third-party pathspec library.** Would remove the subprocess entirely, and
  was rejected twice over: dependencies are forever
  ([`AGENTS.md`](../../AGENTS.md) § *Check before acting*), and a reimplementation
  of Git's ignore semantics that disagrees with Git in any corner is worse than
  a slow call that agrees by construction. [RFC-0079](../rfc/0079-codebase-context-pack.md)
  reached the same conclusion from the other direction.
- **A persistent ignore cache.** Buys the remaining seconds, at the price of a
  cache that can be stale about what is on disk. A stale answer is worse than a
  slow one, and per-invocation scope cannot go stale.
- **Three resolvers, one per distribution boundary** (repo-only, portable
  `agentbundle`, shipped pack content). Rejected because measurement found the
  latter two have no caller: portable catalogue lint issues zero Git
  subprocesses, `catalogue verify` issues one already-batched `git ls-files`, and
  all seven shipped pack lints call Git only for root discovery. A helper with no
  caller is a boundary with nothing behind it.
- **Escaping pathspec magic with `:(literal)`.** Proposed in review and rejected
  on evidence: this subcommand rejects the prefix, so the fix would have broken
  every candidate.

## Consequences

- One `check-ignore` process per lint invocation, and none for an empty candidate
  set. The measured before/after figures live in
  [`docs/specs/lint-performance-p0/notes/lint-inventory.md`](../specs/lint-performance-p0/notes/lint-inventory.md)
  § *After evidence*, which the implementing spec designates as their single
  canonical home. They are deliberately not repeated here: this record is frozen
  on acceptance, so a figure that drifts would need a second ADR to correct.
- `tools/lint-no-direct-check-ignore.py` refuses a direct `check-ignore`
  subprocess outside `tools/lint_git_ignore.py`, matching the pattern anywhere in
  an argv sequence and in shell-string form. It is a drift guard, not a proof —
  an AST allowlist cannot see an argv assembled at runtime — and the strong
  property remains the runtime process count asserted in
  `tools/test-lint-boundary-structural.py`.
- Callers must prune symlinks before batching. Git declines to answer for a path
  whose ancestor chain crosses a symlink, so such a candidate raises. Both
  current callers already prune while collecting; detecting the condition inside
  the resolver would mean an `lstat` walk per candidate, reintroducing the
  per-path filesystem work the decision removes.
- `AC10a` of the **superseded** spec is now wrong in a frozen document. A reader
  who starts there needs the `Status`-field pointer to find the live rule — the same
  residue [ADR-0084](0084-nosec-reason-delimiter-and-stderr-as-a-gate.md)
  accepted, and for the same reason: the operative rule lives in a Living file at
  the point of use, not in a patched record.
