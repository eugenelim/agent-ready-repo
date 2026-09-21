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
