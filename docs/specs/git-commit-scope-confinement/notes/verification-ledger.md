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
