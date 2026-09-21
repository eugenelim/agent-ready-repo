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

AC-0018 was amended three times off this entry, each in its own commit:

| Commit | Amendment |
| --- | --- |
| `f5ce1ffce` | replaced argument inspection with `GIT_NO_LAZY_FETCH=1` plus a configuration refusal |
| `87a72df57` | covered both promisor designations, after the second security round sustained a finding that the first amendment checked only the per-remote key |
| `e8ab68b45` | moved the configuration refusal **before** any object-reading git command, after the third round sustained a finding that the check was unobservable behind the environment variable on a git that honours it |

The third is the one worth remembering: a backup control that only ever runs
behind a working primary cannot be distinguished from an absent control, and the
git version where the primary fails is exactly the one the backup exists for.

**Not established.** Live transport behaviour on a git older than 2.41 was not
exercised; the installed git is 2.50.1. The configuration refusal is what covers
that case, and it is a configuration check rather than a version check precisely
because the version could not be observed here.

## 2026-09-20 — the entry bound's origin, in the unit the bound governs

**Why run it.** AC-0021's entry bound cited this repository's largest tracked
directory at 215 entries. Adversarial review pointed out that 215 counts blobs,
while the allocator consumes every entry a listing yields — so the figure was
not measured in the unit the bound governs.

**What was run.** At revision `e8ab68b45`, from the repository root:

```
git ls-tree -z HEAD -- tools/ | tr '\0' '\n' | awk '{print $2}' | sort | uniq -c
```

**Observed.** `215 blob`, `7 tree` — **222 entries**, not 215.

**What it settles.** The bound's origin now reads 222 entries consumed, which is
~295× rather than ~305×. The value itself does not move: 65,536 was never
derived from the measurement, it is bounded below by it. What the correction
buys is that the origin and the bound are expressed in one unit, so a later
reader re-measuring finds the same number.

## 2026-09-20 — the surfaces promising the unprefixed intent path

**Why run it.** Adversarial review named two published guides still promising
`docs/product/intents/<slug>.md` for an admitted intent. Two files a reviewer
named is not the population, so the tree was swept.

**First attempt, and why it was wrong.** The first sweep restricted itself to
`guides/`, `docs/guides/` and `packs/*/.apm/`, found 29 occurrences across 14
files, and this ledger recorded that as a repository-wide result. It was not:
the next review round found `docs/product/README.md` and its seed at
`packs/core/seeds/docs/product/README.md`, both live and both outside those
roots, and `packages/agentbundle/agentbundle/workspace_mcp.py:91`, which
composes the path in **code** rather than describing it in prose. The claim was
written from the command's intent rather than from what the command covered.

**Second attempt.** At revision `099878dc6`, no root restriction:

```
grep -rn 'intents/<slug>\.md\|intents/{slug}' --include='*.md' --include='*.py' \
  --include='*.json' . | grep -v '^\./\.git/'
```

**Observed.** 65 occurrences across 48 files, of which 10 are the `.claude/` and
`.agents/` self-host projections of pack sources already counted, and the
remainder split by what they describe:

| What it describes | Surfaces | Bearing on this slice |
| --- | --- | --- |
| Admission — prose | `guides/core/reference/work-intake-routing-and-lifecycle.md`, `guides/core/how-to/start-the-work.md`, `guides/core/reference/workspace-toml-schema.md`, `docs/product/README.md`, `packs/core/seeds/docs/product/README.md`, `packs/core/.apm/skills/work-intake/SKILL.md`, `packs/core/.apm/skills/intake-intent/SKILL.md` | in scope |
| ~~Admission — code~~ | `packages/agentbundle/agentbundle/workspace_mcp.py:88-94`, `packs/core/.apm/skills/intake-intent/scripts/intent_renderer.py:69` | **both misclassified; corrected below** |
| Authoring — `frame-intent` | `guides/product-engineering/**` (4 files), `guides/_shared/how-to/run-a-full-inception.md`, `packs/product-engineering/.apm/skills/frame-intent/**`, `align-value-stream` references and templates | out of scope: authoring, not admission |
| Historical record | `docs/adr/0078`, `docs/rfc/0083`, `docs/product/changelog.md`, `docs/product/findings/`, seven other `docs/specs/*` | out of scope: immutable or already-shipped records |

**Correction, same day.** Both code rows were wrong, and the next review round
caught them. `workspace_mcp.py:88-94` is the `"shape"` dispatch entry whose
`dispatch_skill` is `frame-intent` — authoring, not admission, so out of scope
on the same ground as the guides beside it. And `intent_renderer.py:69` composes
its target from the `slug` argument it is given, so a caller passing
`FEAT-0006-my-thing` yields the prefixed path with no edit at all; the seam was
already there. The affected set is **seven prose surfaces and no code** outside
the new allocator, which is a materially smaller slice than the ledger first
recorded.

**What it settles.** The affected set was first recorded as nine surfaces, two of them code — not the
two a reviewer named, and not the five the first sweep's narrow roots suggested.
The lesson is the claim rather than the count: a sweep's summary must be written
from what the command actually covered, and this one said "repository-wide" of a
three-root search.

## 2026-09-20 — owner decisions that reversed three review rounds

**Why it is here.** Two findings reached the owner rather than being resolved by
the author, and both reversed a direction three adversarial rounds had pushed
the contract toward. Recording them here keeps the reasoning with the evidence
that produced it.

**What the review had found.** First, the authoring route could never yield a
typed intent: `frame-intent` writes `docs/product/intents/<slug>.md`, admission
preserves an existing path, so the ordinal was never assigned — a contradiction
with AC-0001 that no amount of criterion wording would fix. Second, the spec had
drifted into stopping a mapped-level admission when the allocator could not
number it, while the governing brief promises at `:26` that "a refused ordinal
still leaves the intent admitted and registered" and at `:22` that an intent
whose altitude is unmapped "keeps full `kind:slug` identity, admission and graph
participation".

**How the drift happened, since that is the transferable part.** Each step was
locally defensible. Round 4 closed a hole where a supplied prefix was accepted
as proof of allocation; the fix was to refuse the supplied prefix, and refusing
the *admission* came along with it unexamined. Nothing in the next three rounds
re-read the brief, because each round measured the spec against the previous
round's spec. An accepted upstream artifact is not a reviewer input unless the
author supplies it.

**The decisions, 2026-09-20.** Admission always proceeds. Five cases, and the
distinction that matters is which of them leaves a marker:

| Case | Filename | Marker in `## Unresolved questions` |
| --- | --- | --- |
| `work-intake` creates, altitude maps | typed | none |
| `work-intake` creates, altitude unmapped | unprefixed | **none** — the intended outcome for that altitude, not a gap |
| `work-intake` creates, allocator refused | unprefixed | the refusal's reason |
| direct `intake-intent` creates | unprefixed | that no ordinal was allocated |
| intent already on disk, any path | unchanged | none |

Marking the unmapped case would train a reader to ignore the marker the two
middle rows depend on, which is why it is deliberately absent rather than
overlooked. A second decision — that a not-yet-admitted intent be allocated and
renamed — was taken the same day and withdrawn the same day; see below.


**Superseded the same day, on evidence the decision did not have.** The second
decision — that a not-yet-admitted intent be allocated and renamed — was
withdrawn after review established that no admission surface can rename a file:
`intake-intent`'s `allowed-tools` carry no move and no delete, `work-intake`'s
`Bash` is declared for local Python validation and the `workspace-status`
backend, and `intake_transaction.py`'s validated target is the only path the
materializer may write. Honouring it would have cost a transaction-core change,
a capability widening and a fresh secure-design pass — none of which was visible
when the options were put to the owner. The case went to
`intent-renumber-and-reissue`. The reason is the capability wall,
not a judgement about where a rename fits best. The pre-registration argument
that made the rename look cheap — that registration follows the artifact write,
so an entry would be created once at the final path — was the rationale for the
withdrawn decision and is superseded by it: no admission surface can perform the
move that argument assumed. AC-0022 and AC-0023 are retired in the spec.

The transferable part is the shape of the mistake: the options offered to the
owner were priced without first checking what the affected surfaces are
permitted to do. A capability declaration is cheap to read and was not read.

**The capability evidence, with its commands.** Recorded at revision `fbcd5f8ff`
so the conclusions are reproducible rather than asserted:

| Claim | Command | Observed |
| --- | --- | --- |
| `intake-intent` holds no move or delete | `sed -n '195,212p' packs/core/.apm/skills/intake-intent/SKILL.md` | `allowed-tools` lists `Read`, `Write`, `Edit`, `Agent`, and states "No network, shell, tracker, credential, or external-locator filesystem access is permitted" |
| `work-intake`'s `Bash` is not declared for moving files | `sed -n '428,437p' packs/core/.apm/skills/work-intake/SKILL.md` | "Bash - run local Python validation or the `workspace-status` backend with discrete arguments; do not use network commands" |
| the materializer may write one path only | `sed -n '298,316p' packs/core/.apm/skills/work-intake/SKILL.md` | "its validated target is the only path the materializer may write" |
| registration follows the artifact write | `sed -n '336,340p' packs/core/.apm/skills/work-intake/SKILL.md` | "After the owner returns a durable artifact, register it as a Draft, non-dispatchable entry" |

**What the withdrawn decision had argued, and why it did not survive.** This paragraph is the reasoning *for* the rename, recorded because it was load-bearing at the time and is now superseded — not as a current-state claim. `work-intake/SKILL.md:336-340` registers *after*
the owner returns a durable artifact, so a rename that happens before
registration writes the entry once at the final path. There is no lockstep edit
and no citation sweep, which is what keeps this out of
`intent-renumber-and-reissue`'s territory.

## 2026-09-21 — T1 materialized, red proven, then green

**Materialization.** The plan's fenced block was written to
`packs/core/tests/skills/work-intake/test_intent_ordinal.py` and byte identity
against that block asserted at the moment of writing, per `tdd-stubs.md`. The
suite then failed at collection — the module did not exist — which is the
intended red for a not-yet-written seam.

**Two edits after materialization,** both construction-level and both recorded
because the byte-identity claim above is scoped to materialization and not to
the file's later life. First, `ruff` `PTH101` rejected the stub's own
`os.chmod(...)` in favour of `Path.chmod(...)`; ruff is a gate, so the
repository copy took the fix and the plan's block now differs from it by those
two lines. Second, three deferred assertions were filled: bytecode on the
production path, an `origin` whose default branch will not resolve, and the
byte bound stopping a read loop.

**One implementation change the tests forced, and it is not test-fitting.**
`_is_promisor` first compared `extensions.partialclone` only. Git's own
`config --list` lowercases a key, while the documented spelling is
`extensions.partialClone`, and a caller may hand over either — matching one
leaves the other designation open. The comparison folds case now.

**Green.** `python3 -m pytest packs/core/tests/skills/work-intake/ -q` →
**160 passed**. `packs/core/tests/skills/intake-intent/ -q` → **23 passed**,
unamended. `make lint-ruff lint-mypy` → clean, 148 source files.

**Zero writes, observed rather than argued.** A real invocation —
`python3 intent_ordinal.py --dir d --token FEAT` from a scratch directory —
printed `FEAT-0002` and left no `__pycache__` beside the script. An earlier
`__pycache__` there was written by my own `python3 -m py_compile`, not by the
allocator; `test_a_real_invocation_writes_no_bytecode` now runs the CLI as a
subprocess so the claim is standing rather than a one-off, and it must be a
subprocess because the suite sets `sys.dont_write_bytecode` itself and would
mask a script that does not.

## 2026-09-21 — where the security review actually stands

**Round 6 found the third promisor designation.** `remote.<name>.partialclonefilter`
designates a promisor remote **on its own** — git builds one from the filter by
itself — and every fixture I had built carried it *alongside* `promisor=true`, so
the case was never isolated. Verified on git 2.50.1 by removing both other keys
and pointing a `--filter=tree:0` clone at an unreachable remote: the transport
was attempted. `_is_promisor` covers all three now, with nine parametrized
cases, and the fixture refuses end to end with `remote-unavailable`.

That is three rounds in a row where the finding was a set I had enumerated
incompletely: git's true values, git's promisor keys, and the `GIT_*` variables
that reach a child. Two of the three are now closed by construction — the false
set and the environment allowlist are complements rather than lists — and this
one is not, because git's designation keys have no complement to take. It stays
an enumeration, and a git that adds a fourth key would defeat it silently.

**No round has returned Clean.** Six rounds, nineteen findings, every premise
reproduced and every fix carrying a standing test — and round 5 still found
four. The rate is not obviously converging, and saying so is more useful than a
summary that implies it is.

A sixth round was run at `37490f57b` for a specific reason rather than to chase
the count: round 5's own fixes replaced the security-critical environment
handling *after* the reviewer last saw it. Leaving that change unreviewed would
be exactly the gap this exercise exists to close.

**What the nineteen say about the earlier passes.** Two spec-stage rounds
returned Clean on the contract, and the contract was right. Every one of the
nineteen was an implementation that agreed with the criteria's words and not
their intent — a bound that inverted when its input was zero, an allowlist that
failed open on a value nobody enumerated, a status code standing in for a
message. A criterion cannot catch that, which is the argument for this pass
existing rather than being folded into the earlier ones.

**Two patterns, both worth carrying forward.** Four findings were one
conflation — *could not run* versus *ran and said no* — fixed by giving `_git`
an exit code rather than a truthy string. And three were a set enumerated in the
wrong direction: an allowlist where the closed set was its complement, a status
where the message was the signal. The denylist of `GIT_*` variables grew four
times before becoming an allowlist; each growth was a real hole someone else
found.

## 2026-09-21 — the implementation-stage security review, and four real defects

**Why it ran.** Owed at GATES once code existed. Two spec-stage passes had
turned findings into criteria; this one asked whether the code upholds them.
Diff against merge-base `3031b9fce`, source review only.

**Four findings, every premise reproduced before fixing.** None was a false
positive, and two of them inverted a control into its own absence:

| Finding | Reproduced | Fix |
| --- | --- | --- |
| `git config --list` is newline-delimited, and a config *value* may contain a newline — so an adopter-controlled repository can forge a `remote.origin.promisor=false` line and cancel the promisor check | a three-line parse showed the forged key appearing in the dict | `--list -z`, NUL-delimited, key and value split on the first newline *inside* a record. An unreadable configuration now refuses rather than reading as "no promisor" |
| A failed `rev-parse` or `remote` was classified `absent`, so a command that answered nothing about the view was treated as an empty view — the exact way a duplicate ordinal gets handed out | read directly from the branches at `:239-256` | `absent` only where git positively reports nothing to consult; every failure is `failed` |
| `max(0.0, deadline - now)` then `wait(timeout=remaining or None)` — an expired deadline produced `0.0`, which is falsy, so the bound became an unbounded wait. And `stdout.read()` could block before the wait was ever reached | `max(0.0, -1.0)` → `0.0` → falsy | an expired deadline raises `bound-exceeded`; the deadline is checked inside the read loop; `wait` never receives a falsy timeout |
| `\d{4,}` is unbounded, and CPython refuses `int()` above 4,300 digits — so a remote entry with a long digit run passed the shape and then raised, and a traceback is the one outcome that stops an admission | `int('9' * 5000)` → `ValueError: Exceeds the limit (4300 digits)` | the grammar bounds the run at twelve digits, so an over-long name is *malformed* and refuses. AC-0004 records the bound and its origin |

**Round 2 found three more, all sharper versions of my own fixes.** That is the
useful part: each one was a control I had just written, defeated on a case I had
not considered.

| Finding | Reproduced | Fix |
| --- | --- | --- |
| `config --list -z` renders a **valueless** key as a bare record, and git reads a bare `promisor` line as `true` — my parse mapped it to `""`, which is falsy, so the no-egress guard was bypassed on exactly the git versions that ignore `GIT_NO_LAZY_FETCH` | a fixture with `[remote "origin"]` + bare `promisor`: `git config --type=bool --get` returned `true`, and `--list -z` showed the record with no value | a valueless key maps to `"true"`, which is git's own reading |
| The deadline could not fire while `stdout.read()` blocked, so an adopter-controlled config include stalling on a FIFO defeated both wall-clock bounds | read from the loop's own shape | the pipe is polled with `selectors` and the remaining budget, so no read begins without the deadline being live; a platform whose pipes cannot be selected falls back to a bounded `communicate` with that degradation stated in the source; and a `finally` kills and reaps the child whichever way the function leaves |
| `rev-parse` returning nothing conflated "no repository" with "git refused" — unsafe ownership, a timeout or any non-zero status became `absent` and permitted a local-only ordinal | `git rev-parse --show-toplevel` outside a repository exits **128**, a distinguishable signal | `_git` now returns `(output, code)`, and only exit 128 yields `absent`. Everything else refuses |

**Round 3 found three more, and two of them were my round-2 fixes being too
literal.**

| Finding | Reproduced | Fix |
| --- | --- | --- |
| `_is_promisor` allowed `{true, 1, yes, on}`. Git reads **any** non-false value as true | `git config --type=bool --get` returned `true` for `2`, `-1`, `TRUE`, `yes`, `on`, and `false` only for the empty string, `0`, `no`, `off` | the check inverted: a key designates unless its value is in git's *false* set. An allowlist of true forms fails open on every value nobody thought of; the false set is the one that is closed |
| `BufferedReader.read(65_536)` loops until it has the full count, so it can block past the deadline *after* the selector reported readiness — a short prefix then a stalled FIFO include defeats the bound again | read from the buffered-IO contract | `os.read` on the raw descriptor, which returns whatever is available |
| Exit 128 is git's status for *every* fatal error, so a dubious-ownership refusal read as "no repository" and skipped the `origin` view | `LC_ALL=C git rev-parse --show-toplevel` outside a repository prints `fatal: not a git repository (or any of the parent directories): .git` and exits 128 | `absent` now requires that message as well as the status, with `LC_ALL=C` pinned in the child so the wording is not luck. Stderr is captured for one comparison, bounded at 4 KiB, read only after the child exits so it cannot deadlock against stdout, and never reflected |

Two runs against real git confirm the probe end to end: inside this repository the
allocator unions with `origin` and still answers `VISION-0002`, `STRAT-0005`,
`CAP-0005`, `FEAT-0006`; in a scratch directory outside any repository it reads
`absent` and allocates from the working tree alone.

**Round 4 found four more, and none was a blocker — but all four were defects
rather than accepted risk, which is the distinction the round was asked to
make.**

| Finding | Fix |
| --- | --- |
| `GIT_CONFIG`, `GIT_CONFIG_GLOBAL` and the `GIT_CONFIG_COUNT`/`_KEY_n` family redirect what `git config` *reports* without changing what an object read *obeys*, so an inherited one could hide a promisor designation from the guard while `ls-tree` still honoured it | the whole `GIT_CONFIG` prefix is scrubbed from the child, alongside the five redirect variables already there |
| `max + 1` could leave the grammar: a directory holding `FEAT-999999999999-x.md` returned `FEAT-1000000000000` with exit 0, which the caller writes once and every later scan then refuses as malformed — a success that poisons the directory | a successor wider than the twelve-digit bound refuses as `bound-exceeded` |
| The whole-invocation deadline began at the first git call, so 65,536 local metadata inspections happened outside it — the stated bound was not the bound | one deadline is created in `allocate` and threaded through the local scan, `git_config_values` and `remote_view`, checked per entry |
| The selector fallback used `communicate`, which allocates the whole git result before any ceiling applies — a platform-dependent hole in the byte bound | the selector is gone. One path everywhere: the descriptor is set non-blocking and polled with `os.read` against the deadline, so the ceiling is enforced while reading on every platform rather than on the lucky ones |

Four standing cases added, one per finding. The last fix is also a
simplification — the branch that existed to be a fallback was the branch that
could not hold the bound, so removing it left one read path instead of two.

**Round 5 found four more, and two of them ended the denylist.**

| Finding | Fix |
| --- | --- |
| `GIT_TRACE` and `GIT_TRACE2_EVENT` make a read-only probe **write files** at an inherited path, which breaks AC-0003's zero-write promise outright | — |
| `GIT_CEILING_DIRECTORIES` fences discovery below the real root, so `rev-parse` emits the very not-a-repository diagnostic the `absent` branch trusts — and the `origin` view is skipped | both closed by the same change: the child's environment is built from an **allowlist** (`PATH`, `HOME`, and the platform temp names) rather than inherited and pruned |
| An `OSError` from `os.read` was treated as EOF, so a truncated read was accepted while git exited zero — hiding a promisor key or dropping the highest remote ordinal | a read error invalidates the whole result |
| `Path(path).name` splits on a backslash under Windows, so a POSIX-authored `FEAT-0005-a.md\FEAT-0001-b.md` on `origin` reads as ordinal 1 and lets 5 be allocated twice | the basename comes from `rsplit("/")`, because git's path grammar is slash-only on every host |

The allowlist is the finding worth keeping. The denylist grew four times across
these rounds — the redirect set, then `GIT_CONFIG*`, then `GIT_TRACE*`, then
`GIT_CEILING_DIRECTORIES` — and each addition was a real hole found by someone
else. The next one would have been whichever variable nobody had thought of. An
allowlist inverts the failure: an unknown variable is excluded by default, and
the cost is that a genuinely needed name must be added deliberately.

The `(output, code)` shape is the change worth naming: "could not run" and "ran
and said no" were the same value before, and four of the eighteen findings
across five rounds were that one conflation wearing different clothes. The other
pattern is narrower and worth naming too: three findings were a set I had
enumerated in the wrong direction — an allowlist where the closed set was the
complement, or a status where the message was the signal.

A further one was raised in round 1 and is real but narrower: the remote entry bound counted
surviving names rather than records consumed, so a tree of unrelated names cost
the work the bound exists to cap. It counts records now.

**Standing coverage, not one-off checks.** Six cases added, one per finding plus
the entry-bound one: `test_a_newline_in_a_config_value_cannot_forge_a_promisor_key`,
`test_unreadable_configuration_refuses_rather_than_assuming_no_promisor`,
`test_absent_is_a_positive_finding_not_a_failed_command`,
`test_an_expired_deadline_refuses_instead_of_waiting_without_limit`,
`test_an_absurd_digit_run_is_malformed_not_a_crash`, and
`test_a_remote_tree_of_outside_names_still_hits_the_entry_bound`.

**After the fixes.** 80 cases in the allocator suite, 199 across the two pack
suites, `make lint-ruff lint-mypy` clean. The real corpus still answers
`VISION-0002`, `STRAT-0005`, `CAP-0005`, `FEAT-0006` with a clean duplicate
check, so the hardening changed no answer it should not have.

**What this says about the spec-stage passes.** Both returned Clean on the
contract, and the contract was right; the code still had four defects, two of
which were bounds that inverted. A criterion cannot catch an implementation that
agrees with its words and not its intent — which is the argument for this pass
existing rather than being folded into the earlier ones.

## 2026-09-21 — the allocator agrees with the numbers a human chose

**Why run it.** The plan's named uncertainty was that the existing typed corpus
was authored by hand, so the allocator's first real run has to agree with
choices nobody derived. That is checkable, so it was checked rather than
assumed — and this run is also the only one so far that exercised the `origin`
union for real, since every unit fixture is a bare directory with no remote.

**What was run.** At revision `1bca9160e`, from the repository root, against the live
`docs/product/intents/`:

```
python3 packs/core/.apm/skills/work-intake/scripts/intent_ordinal.py --dir docs/product/intents --token <TOKEN>
python3 packs/core/.apm/skills/work-intake/scripts/intent_ordinal.py --check docs/product/intents
```

**Observed.**

| Token | Highest on disk | Allocator |
| --- | --- | --- |
| `VISION` | `VISION-0001` | `VISION-0002` |
| `STRAT` | `STRAT-0004` | `STRAT-0005` |
| `CAP` | `CAP-0004` | `CAP-0005` |
| `FEAT` | `FEAT-0005` | `FEAT-0006` |

`--check` exited 0 with `no duplicate ordinals` on stderr and nothing on stdout.

**What it settles.** Four for four, and the duplicate check is clean on a corpus
it actually read — the distinction that matters, since the helper this replaces
reports clean for a directory it never matched. The remaining gap is the one the
Assumptions section already owns: a peer's unpushed record is invisible to this
view by construction, so two concurrent sessions can still take the same number
and `--check` is what surfaces it afterwards.

## 2026-09-21 — T2 and T3 executed

**T2, verified remotely by instruction.** `tests/roster/` is not run on this
machine: the suite costs 7–12 minutes a run and CI runs it on every push, so a
roster-only control is a remote result and saying otherwise would overstate what
was checked. What was checked locally: the file compiles, the owner-table parser
returns the four expected pairs against the real intent, and
`tools/lint-ci-parity.py` accepts the three roster-admission edits — the named
step above the bulk `pytest tests/ -q` step, the matching `STEP_DISPOSITION`, and
no `.workspace-prune-protected.toml` entry, since this test names no
`docs/specs/<slug>` literal.

I should record that I ran `tests/roster/test_workspace_status_projection.py`
several times earlier in this session before re-reading that instruction. Those
runs are not evidence this slice relies on, and the habit stopped here.

**T3's release surface.** core `2.26.22` → `2.26.23`, a patch: a script added
inside an existing skill is changed content of that skill, not a new projected
primitive. The changelog Highlights were checked against the `/now/` projection's
vocabulary gate — none of `unreleased`, `work index`, `backlog`, `queue`,
`in progress`, and balanced emphasis so no literal `**` survives rendering. The
three release gates themselves are roster-owned and therefore remote.

**The sixteen core suites.** `2,547 passed, 6 skipped, 147 subtests`, no
failures. Two of them — `work-loop` at 13m29s and `workspace-status` —
overlapped my own edits in that window, so they were re-run on the settled tree
rather than trusted; a gate measured while the worker is still editing measures
neither state. The re-run agreed exactly — `work-loop` 1227 passed, 5 skipped,
68 subtests in 13m36s; `workspace-status` 130 passed, 1 skipped — so the overlap
cost nothing this time. Recorded anyway, because the agreement is the outcome
and not the reason: a result read off an overlapping run is not evidence about
either tree, whichever way it lands.

**One collection defect found and left alone.** `pytest packs/core/tests/ -q`
fails at collection on a basename clash between
`skills/author-delivery-brief/test_project_knowledge_handoff.py` and
`skills/work-loop/test_project_knowledge_handoff.py`. It predates this slice —
both files come from `3031b9fce` — and it is why the Makefile runs these sixteen
by directory rather than as one tree. Not this slice's to fix, and recorded so
the next reader does not mistake the tree-wide invocation for the supported one.

## 2026-09-20 — T1's stub earns its red

**Why run it.** `work-loop/SKILL.md:252` requires a TDD task's exact stub to
compile and earn its red from disposable scratch during PLAN, without creating a
repository test file.

**What was run.** The stub extracted from `plan.md` verbatim, compiled with
`python3 -m py_compile`, then run against a deliberately-wrong skeleton
(`token_for_level` → `None`, `classify` → `"outside"`, `next_typed_ordinal` →
`1`, `remote_view` → `absent`, `main` → `0`).

**Observed.** Compiles. **57 failed, 11 passed.**

**What it settles.** The assertions are reachable rather than vacuous. The 11
passing are the cases whose expected value the degenerate skeleton happens to
return; each is pinned by a sibling in the same parametrization rather than
standing alone, and the split is recorded so a later reader does not mistake the
stub for fully discriminating on its own.
