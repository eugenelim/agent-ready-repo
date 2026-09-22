# Verification ledger — git_commit scope confinement

Execution observations for the frozen spec and plan. Nothing here amends
either document; corrections to them go through controlled amendment.

## Engine run

Run `9c3fb714-77a1-45de-b2d4-e2ab76a6c209`, mode `code`, opened 2026-09-21.
The pre-EXECUTE reviewer passes were run before this session, in the one that
authored the contract — three adversarial rounds and one shaping round, all
findings disposed, as `plan.md`'s Changelog records. This session opened the
engine at `SPEC-PLAN-DRAFTING` and walked it to `CODE-IMPLEMENTATION` over an
already-approved spec and plan, so its `reviewers-clean`, `spec-approved` and
`plan-approved` transitions record decisions already taken rather than new
ones.

All four tasks were implemented by the controller session. Each carries a
`dispatch-receipt` decline of `human-directed`: the invoking brief directed the
execution task by task and supplied measured, session-specific context — the
spike harness, the `None`-return trap at the `_GitTools.__init__` seam, and the
release surfaces — that a fresh implementer subagent would not have held.

## T1 — the staging matrix reds only on the glob-bearing row

`python3 -m pytest packages/agentbundle/tests/test_workspace_mcp_git_scope.py`
at commit `59b7f1a5f`: **4 failed, 48 passed in 36.4s**. Every failure is
`test_a_reserved_character_never_widens_the_staged_set[<type>-*]`, one per
patterned item type, each staging `docs/unrelated/other.md` alongside the
item's own file. That is the plan's `Done when` for T1 exactly: the red is the
defect, observable through the real tool.

The other four reserved characters were green at T1, and that agrees with the
measurement the design decision records: only `*` reaches the scope grammar.

## T2 — what the pre-fix revert measured

With `workspace_mcp.py` reverted to its pre-fix bytes and the new tests kept,
the refusal-bearing selection ran **32 failed, 28 passed**. Restoring the fix
returns the whole file to **98 passed in 92.7s**.

That measures one thing: each of those 32 cases reaches a first failing
assertion without the fix. It is not per-assertion mutation proof — the stderr,
empty-stdout, `HEAD` and `git diff --cached` assertions grouped inside
`test_a_reserved_character_is_refused_and_leaves_the_repository_alone` are not
shown individually mutation-sensitive by a whole-file revert, and this ledger
does not claim they are.

The load-bearing rows in that red are
`test_a_refused_base_leaves_the_sibling_git_tools_working[<type>-{]` and
`[<type>-}]`. Pre-fix, a base containing `{` or `}` makes
`p.format(slug=slug)` raise, `_resolve_output_pattern` returns `None`,
`__init__` clears `dispatched`, and the session drops into discovery mode —
`git_branch` and `git_push` answer with the generic discovery error. That is
the failure mode AC-0008 forbids, and the test catches it, which is why the
refusal is represented distinctly at that seam rather than by returning `None`.

## Suite placement

The new suite sits at `packages/agentbundle/tests/test_workspace_mcp_git_scope.py`,
the path `plan.md`'s pinned `Touches` names. `packages/agentbundle/tests/test_workspace_mcp_git.py`
says its disk-and-subprocess counterparts live under `tests/integration/`, and
`packages/AGENTS.md` routes engine-distribution tests to the three
subdirectories. The established local practice disagrees with both: all seven
`test_workspace_mcp_*.py` files already sit at the tests root, and this suite
joins them there. It reads no repository path, so the sdist artifact gate is
unaffected.

## Gate observations

`packages/agentbundle/pyproject.toml` sets `addopts = "-q"`, so a run invoked
with `-q` doubles to `-qq` and suppresses the pass/fail summary line. Every
count above was taken with `-o addopts= -q`.

## Review round 1 — two artifact errors worth the owner's attention

The `adversarial-reviewer` round sustained one Concern and one Advisory.

The Concern was real and is repaired: `tests/roster/test_okf_catalogue_discovery.py`
asserted AC-0007's version by substring containment and never read
`docs/product/changelog.md` at all, so a package changelog whose `## [0.47.3]`
sat below a newer heading passed the gate. The test now asserts position for
both changelogs. That control was checked by replaying its predicate over the
real files and over a mutated copy with a newer heading inserted above the
released one; the suite itself runs on CI, not on this machine.

The Advisory is an error in the frozen plan and is **not** repaired here,
because a frozen plan takes controlled amendment and that is the owner's call.
T3's `Tests` says the product changelog "keeps core's newest entry adjacent to
`[Unreleased]`, checked by `tools/test_build_site_routing.py`", and `Done when`
rests on that suite passing. That file asserts changelog parsing,
`[Unreleased]` classification, and blank-line separation — no adjacency,
topmost, or newest-entry property — and it is absent from T3's `Touches`. The
adjacency property itself holds in the shipped file and the `agentbundle` entry
sits immediately below core's newest, but no suite asserts it. Either T3's
`Tests` should name a check that exists, or the claim should be recorded as
unverified.

## Owner authorization for the T3 plan amendment

2026-09-21, owner eugenelim, in session: "authorized the plan change" — the
controlled amendment correcting T3's `Tests` and `Touches` so they name a check
that exists. The defect is the one recorded directly above: T3 credited
`tools/test_build_site_routing.py` with an adjacency, topmost, or newest-entry
assertion that file does not make, and did not name that file in `Touches`
either.

The substance is already shipped. `tests/roster/test_okf_catalogue_discovery.py`
now asserts position for all three ordered release surfaces — the package
changelog's topmost `## [` heading, the product changelog's first
`## [agentbundle][` heading, and the README's newest `## What's new in`
heading. The amendment makes T3's pinned fields say so.

T1 and T2 are the completed tasks at the time of the amendment (waves 0 and 1;
wave 2 holds T3 and T4). This file is their evidence binding: T1's red and its
counts, and T2's pre-fix revert measurement, are recorded above.

## Carried into EXECUTE: the screen reads the resolved base, not the configured value

The pre-EXECUTE review of the T3 amendment found a defect in the shipped guard
rather than in the amendment. It is sustained, contract-tier, and measured
against the running code, so it is required work — not a plan change. The
contract already forbids both behaviours; the implementation does not match it.

`_read_layout_bases` returns `str(candidate.resolve())`, and the screen tested
that resolved string. Two consequences, both reproduced:

- `output_dir = "scratch*/../artifacts"` contains `*` and resolves to
  `<repo>/artifacts`, so `_refused_layout_key` stayed `None`. AC-0002 requires
  a configured value containing any of the five characters to be refused.
- In a repository whose own path contains `*`, the clean value
  `output_dir = "artifacts"` produced `_refused_layout_key == "product"`.
  AC-0001 requires unchanged staging for a base carrying none of them.

The fix screens the selected configured value before resolution.
`_read_layout_bases` is not modified — the spec's `Never do` forbids it — so the
raw value comes from a sibling read that reproduces the same per-key scope
precedence: user-scope wins for `research`, repo-scope for `product` and
`design`. Duplicated precedence drifts silently, so a test pins the two readers
to one answer rather than trusting them to stay aligned.

No acceptance criterion, task boundary, or plan field moves for this. T2's
`Tests` and `Done when` already cover AC-0001, AC-0002 and AC-0004.

## T3's pre-amendment text, quoted for the record

An amendment should leave the text it replaced where a later reader can see it
without a git archaeology step. This is T3 exactly as it stood at the approved
baseline, before the 2026-09-21 amendment:

```markdown
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
```

## The raw-value screen, and one control that could not fail

Targeted mutations, each reverting one token of the fix:

| Mutation | Caught by |
| --- | --- |
| The screen reads `configured` (resolved) instead of `raw_configured` | both new defect tests |
| The raw reader's `research`/`product` precedence flipped | the agreement test, `both-scopes` row only |

The second row is the finding worth keeping. The agreement test's first version
parametrised five configurations and every one wrote only the repo-scope file,
so the user-scope side was always empty and a precedence flip passed all five.
It asserted agreement without exercising the only thing the two readers can
disagree about. The `both-scopes` row — both files present, different values on
every key — is what makes it fail, and the mutation confirms it is the only row
that does.

Full `workspace_mcp` selection after the fix: 161 passed, 42 skipped, 132s.

## The raw-value screen reopened the defect it closed

Round 4 returned two Blockers against commit `131385a64`, and the second is
reproduced. A repository-scope `output_dir` of `["x"]` — a TOML array — is kept
by the raw reader and dropped by the shared one, because
`_read_layout_bases`'s `_read_scope` calls `Path(raw).expanduser()` on it and
`contextlib.suppress(Exception)` swallows the `TypeError`. The two readers then
disagree about which scope supplies the value:

```
raw     : {'product': ['x']}
resolved: {'product': '<repo>/docs/*'}
refused : None
pattern : ['<repo>/docs/*/intents/alpha.md', '<repo>/docs/*/shaping/alpha/**']
```

The screen ran `"*" in ["x"]`, which is element equality and not a substring
test, returned `False`, and let the user-scope `*` base straight through to
`_apply_layout_overrides`. That is AC-0002 and AC-0004 broken again, by the
commit that fixed them.

The lesson is the one the spec's own design decision already recorded and this
repair did not carry over: the screen must read the value the resolver actually
used. Reading a *second*, independently-computed answer reintroduces the class
whatever that second read is — resolved, raw, or otherwise. Mirroring a
function's precedence is not the same as reusing its result, and a test that
pins the two readers on well-typed input says nothing about the inputs where
one of them bails out.

## The repair: refuse on disagreement, rather than enumerate the divergences

The sustained Blocker's prescribed mechanism was to mirror
`Path(raw).expanduser()` inside `_raw_scope`, so a non-string aborts the raw
reader's loop exactly as it aborts the shared one. That was not taken, and the
deviation is deliberate.

Mirroring closes the divergence someone found and says nothing about the next
one. This defect class has now been shipped twice by enumeration: first
screening the resolved base, which both hides a configured character and
invents one; then mirroring the readers' scope precedence while missing that
they also differ on which *types* they accept. The third enumeration would have
no better claim than the first two.

The screen now refuses unless the raw value, resolved, equals the base
`_read_layout_bases` returned. That is total: either the two agree, in which
case screening the raw value is screening what produced the base, or they
disagree for any reason at all — type, precedence, a malformed file, a file
rewritten between the reads — and the commit is refused. `_read_layout_bases`
is still untouched, so no amendment to the spec's `Never do` was needed.

It is also the better answer for the adopter. Under the prescribed fix a
repository-scope `output_dir = ["x"]` silently falls back to user scope; under
this one the session says the value could not be read as one consistent value.

Mutation: deleting `not agrees or` from the condition reds
`test_a_container_typed_value_cannot_smuggle_a_reserved_base_past_the_screen`
and nothing else.

One defect no reviewer raised, found while writing the row the adjudicator did
ask for: the agreement matrix's `_write_layout` helper emitted every value as a
quoted string, so no row could express an array or an inline table — the matrix
could not reach the case it was being extended to cover. It now emits a value
already carrying a bracket or brace unquoted. This is the same shape as the
`both-scopes` row: a parametrisation that looks exhaustive and cannot reach
what matters.

Full `workspace_mcp` selection after the repair: 163 passed, 42 skipped, 130s.

## The agreement check is a backstop, not a substitute for the mirror

Round 5 sustained a Blocker that refutes the previous entry's reasoning, and the
correction belongs on the record next to the claim it corrects.

The claim was that refusing on disagreement is *total*, so reproducing
`_read_layout_bases`'s selection is unnecessary. It is not. Two different raw
values can resolve to the same path, and equality of the resolved forms
therefore does not establish that the screened value is the one the resolver
selected.

The case: `_read_scope` suppresses around its whole per-key loop, so
`[research] output_dir = ["x"]` — read before `product` — abandons the rest of
the repository scope and hands `product` to the user scope. The raw reader kept
reading and returned the repository's `"artifacts"`. The user value,
`<repo>/scratch*/../artifacts`, resolves to `<repo>/artifacts`, so the two
agreed and a value from a different file and scope was screened.

What follows and what does not. AC-0002's refusal was missed for the effective
configured value, which carries `*`. AC-0004 was not breached: what reaches
`_apply_layout_overrides` is the resolved base `<repo>/artifacts`, carrying no
reserved character, and a reserved character surviving resolution is still
refused. The reviewer's stated consequence — that the star-bearing value
reaches the splice — is false as written, measured before dispatch and
confirmed on adjudication.

The repair reproduces `_read_scope` step for step, including the
`Path(raw).expanduser()` call and the scope-wide abort its raise causes. The
agreement check stays, in its correct role: a backstop for divergences the
mirror fails to reproduce, which cost a commit rather than a containment.

Mutation: removing the abort mirror reds both
`test_a_bad_key_earlier_in_one_scope_does_not_let_the_other_scope_go_unscreened`
and the `container-typed-preferred-value` agreement row, and nothing else. That
row changed meaning with the repair — it previously asserted the two readers
diverge, which was the defect.

Full `workspace_mcp` selection after the repair: 164 passed, 42 skipped, 115s.

## Owner authorization: amend the `Never do`, and close the live instance

2026-09-21, owner eugenelim, in session: "1 and 2" — in answer to a surfaced
loud stop offering (1) amending the spec's `Never do` so `_read_layout_bases`
can yield the selected raw value alongside the resolved one, and (2) adding
`resolve()` to the raw reader's mirror to close the round-6 instance.

Option 1 subsumes option 2. It deletes `_read_raw_layout_output_dirs`, so no
second reader survives for a `resolve()` mirror to be added to, and the
divergence round 6 names cannot exist. Option 2 is retained as the fallback if
the refactor proves unworkable, not implemented alongside.

### Why the rule is being amended rather than worked around

The `Never do` reads: "Never modify `_read_layout_bases`. It is shared with the
status payload and legitimately yields an absolute out-of-repository base for a
user-scope value." Its purpose is that one process must not give two answers
about where an item's output goes — the defect
`docs/specs/workspace-mcp/` fixed before this spec.

Reproducing that function's *selection* in a second reader is the thing that
reopens the two-answers defect, and three review rounds demonstrated it:

| Round | Divergence between the two readers | Settled |
| --- | --- | --- |
| 4 | `_read_scope` calls `Path(raw)`; the raw reader accepted a TOML array | sustained, repaired |
| 5 | That raise aborts the *whole scope*; the raw reader kept reading | sustained, repaired |
| 6 | `resolve()` is a third raise site in the same suppressed block | indeterminate — unverifiable here |

`_read_scope` wraps a three-key loop in one `contextlib.suppress(Exception)`,
so any raise from `Path(raw)`, `is_absolute()`, or `resolve()` abandons the rest
of that scope and hands the decision to the other one. A hand-written mirror has
to reproduce every exception all three can raise on every supported interpreter
(`requires-python = ">=3.11"`), and round 6 turned on behaviour that could not be
exercised in this environment at all.

The amendment therefore preserves the rule's purpose while removing its
prohibition on the one change that serves it: a single selection, read once,
yielding both forms. No existing caller's behaviour changes —
`_read_layout_bases` keeps its signature and its return type, and becomes a thin
projection of the richer reader.

## T5: one selection, and what it cost to get here

`_select_layout_bases` opens, parses and selects once, returning
`(configured, resolved)` per key. `_read_layout_bases` keeps its signature,
return type and every caller, and is now a projection of the resolved half that
opens nothing and decides nothing. `_read_raw_layout_output_dirs` is deleted,
and the agreement check with it — with one selection there is nothing left to
disagree.

Both bypasses this defect class produced are closed, driven through the real
`git_commit`:

| Scenario | Result |
| --- | --- |
| repo `output_dir = ["x"]`, user base carrying `*` | refused, no pattern |
| repo `research = ["x"]` before a clean `product`, user base whose `*` normalises away | refused, no pattern |
| clean configured base, nothing else | accepted, pattern set |

Mutations:

| Mutation | Caught by |
| --- | --- |
| screen reads `pair[1]` (resolved) instead of `pair[0]` (configured) | the two resolution-asymmetry tests and the scope-abort test |
| the selection stores a raw form that is not the adopter's value | the repository-path-with-`*` test and the `both-scopes` selection row |

`test_workspace_mcp_layout_override.py` passes unchanged, which is T5's guard
against this refactor reopening the status-payload disagreement the amended
rule exists to prevent. 122 passed across both suites, 94s.

### What the three rounds actually taught

Not "screen the raw value" or "mirror the precedence" — both were tried and both
shipped the defect again. The lesson is narrower and it is now a spec rule: a
check about a selected value has to read the selection, because any second
computation of "which value won" is a second answer, and two answers is the
defect the layout resolver was consolidated to prevent in the first place. The
mirror was not a weaker version of the right fix; it was the original defect
wearing the fix's name.

## The screen was never the whole defect

Round 7 sustained a Blocker at contract tier that no earlier round reached, and
it is the one the spec's `What Changes` was actually about.

`git_commit` derived its split point by scanning the *fully substituted
absolute path* for the literal `/*`. So the wildcard boundary was rediscovered
from the final string rather than known from the manifest, and any `*` arriving
by resolution became pattern syntax. Measured, with a clean configured value:

```
[product] output_dir = "out"          # carries no reserved character
<repo>/out -> <repo>/*/actual         # a directory literally named *
committed: ['*/actual/intents/alpha.md', 'agentbundle-layout.toml',
            'out', 'unrelated/other.md']
```

Every changed file in the repository. AC-0002 cannot help and must not try:
`out` is innocent, and AC-0001 requires it to keep working. Rounds 1 through 6
all asked *which value the screen reads*; this is a second, independent hole in
*where the structure comes from*.

The repair splits each manifest pattern at its own `/*` before any base is
spliced in. `_resolve_output_spec` owns the boundary and hands `git_commit`
ready-made entries; `_resolve_output_pattern` is a projection of it, the same
shape as `_read_layout_bases` over `_select_layout_bases`. After the repair the
same configuration stages `['*/actual/intents/alpha.md']` and nothing else, and
a clean configured base is unaffected.

Mutation: restoring the scan over the joined path reds
`test_a_star_the_base_resolves_through_is_not_pattern_syntax` and
`test_the_pattern_strings_are_projected_from_the_scope_spec`, and nothing else.

### A test that could not fail, and read as though it could

`test_a_clean_base_is_accepted_under_a_repository_path_carrying_a_reserved_character`
puts the `*` mid-segment, in a repository directory named `pro*ject`.
`find("/*")` needs the star to follow a separator, so that arrangement can never
trip the scan. The test passes, it names resolved-path stars, and it covers the
one shape that is safe by construction. The new test uses a directory literally
named `*`; its docstring records the distinction so the mid-segment case is not
mistaken for coverage again.

Full `workspace_mcp` selection after the repair: 167 passed, 42 skipped, 78s.

## Three vacuous assertions, in the tests written to close the last defect

Round 8's quality pass sustained three Concerns, all in the tests added by the
two preceding repairs. Adversarial was clean on the same commits.

| Defect | Why it could not fail |
| --- | --- |
| The projection test's `for spec in specs` loop | An empty spec left `specs is not None` true, made the projection assertion `[] == []`, and iterated nothing |
| The selection test's per-key loop | A silently dropped key left nothing to iterate, and the projection comparison compared two equally-reduced dicts |
| `str(spec[1]).startswith(base)` | `"artifacts-escape".startswith("artifacts")` is `True`, so the assertion admitted a sibling directory outside the base it claimed containment under |

Repairs: the projection test asserts its entry count against the manifest before
iterating; every selection row now declares the key set it must select, with
`nothing-configured` declaring the empty set, since a blanket non-empty
assertion would be wrong for it; and containment is compared with
`Path.is_relative_to` rather than a string prefix.

Mutations, each caught only by the assertion added for it:

| Mutation | Caught by |
| --- | --- |
| `_resolve_output_spec` returns `[]` | the projection test's entry-count assertion |
| the selection drops `product` | eight selection rows and the projection test |
| the resolved base becomes a `-escape` sibling | the projection test's containment assertion |

The first attempt at that third mutation appended `-escape` to the *leaf* rather
than the base, which stays inside the base and was correctly not caught. The
mutation was wrong, not the test — worth recording, because a mutation that
fails to kill is otherwise read as evidence the assertion is weak.

### The pattern, named

This is the fifth control in this suite that could not fail: the agreement
matrix whose rows all configured one scope, the resolved-path test whose `*` sat
mid-segment, and now these three. Every one was written while repairing a real
defect, and every one asserted the property in a form that the defect's own
absence guaranteed. The suite's docstring says its checks must not agree with a
wrong implementation; that is a claim about each assertion, and it needs a
mutation per assertion to hold, not a passing run.

Both suites after the repairs: 124 passed, 76s.

## The same class through a third mechanism, and its structural statement

Round 9's security pass sustained a Blocker at contract tier: a clean
`output_dir` of `out`, symlinked to a directory literally named `{slug}`, had
its own resolved base rewritten by the `{slug}` substitution.

```
selected : ('out', '<repo>/{slug}/actual')   # AC-0002 correctly does not refuse
pattern  : ['<repo>/alpha/actual/intents/alpha.md', ...]
committed: ['alpha/actual/intents/alpha.md']
```

AC-0004 and AC-0001 broken together: a file outside the directory `out` names
was staged, and the file inside it was not. The adjudicator settled a question
the reviewer did not raise — an unmatched brace does reach the `except
Exception` and clear the dispatched item, but AC-0008's precondition is a base
AC-0002 *refuses*, and this value is clean, so that path is real behaviour and
not a criterion breach.

Repair: `.format(slug=slug)` now runs on the manifest prefix before
`_apply_layout_overrides` splices the base in. Behaviour-preserving for
AC-0005's `{slug}`-bearing prefixes, because every `_LAYOUT_TYPE_BASES`
convention base is brace-free.

Mutation: restoring `.format` to after the splice reds both rows of
`test_braces_the_base_resolves_through_are_not_substitution_syntax` — one per
entry kind, since a single line feeds the exact-file entry and the wildcard
static root — and nothing else.

### The class, stated so it can be checked rather than enumerated

The staging scope joins trusted manifest text to an untrusted resolved base.
Every step that *interprets* the joined string can read the base's characters as
syntax. Two such steps existed, and both now run on manifest text before the
join:

| Step | Interprets | Runs on |
| --- | --- | --- |
| wildcard split | `/*` | the manifest pattern alone |
| slug substitution | `{…}` | the manifest prefix alone |

Rounds 1 through 6 all asked *which value the screen reads*, which is a
different question and could never have reached either of these. A third
interpreting step, if one exists, has this signature: something that scans or
substitutes over a string the base has already been spliced into.

Full `workspace_mcp` selection after the repair: 169 passed, 42 skipped, 167s.
