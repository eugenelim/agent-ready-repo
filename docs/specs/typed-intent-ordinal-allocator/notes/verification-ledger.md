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
failures. Two of them — `work-loop` at 13m29s and `workspace-status` — overlapped
my own edits in that window, so they were re-run on the settled tree rather than
trusted; a gate measured while the worker is still editing measures neither
state.

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
