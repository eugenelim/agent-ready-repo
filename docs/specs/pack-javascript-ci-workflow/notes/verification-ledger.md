# Verification ledger — pack-javascript-ci-workflow

Execution observations. The spec holds the contract and the plan holds the
strategy; neither is edited to record what happened here.

## VI-1008 — the stub was materialized byte-identical, then lost one blank line

2026-10-05. VI-1008 requires the candidate self-test to be materialized
"unchanged" as `tools/test-pack-javascript-workflow.py`. It was: the fenced
python block in `plan.md` and the file on disk hashed identically
(`sha256` prefix `6f60badd8ec48d9d`), and the intended red was earned before
the parser change — `node renderer.test.js` produced no recognized runner
tokens, exactly as the plan's validation note predicted.

Then `make lint-ruff` failed on that file, and only that file:

```
unsorted-imports: [*] Import block is un-sorted or un-formatted
  --> tools/test-pack-javascript-workflow.py:4:1
```

`pyproject.toml` sets `preview = true` for ruff, and under preview the isort
rule wants one blank line after the import block where the stub carries two.
The whole difference is one blank line between `from selftest_harness import
run_cases` and `BOUNDARY_PATH`.

This is not a defect introduced while revising the spec. The stub as approved on
2026-10-02 carries the same two blank lines — checked against
`origin/main:docs/specs/pack-javascript-ci-workflow/plan.md`, not inferred. So
the approved plan contains a stub that cannot coexist with a required gate.

Owner decision 2026-10-05: delete the blank line in the materialized file and
record the deviation here, rather than amend the plan or relax ruff. The reasons
the owner was given, and chose on:

- Byte identity had already been proven and the red already earned, so the two
  things VI-1008's "unchanged" instruction protects — that the test is not
  quietly rewritten, and that its red is real — are both discharged. What
  changed afterwards is whitespace with no semantic effect.
- Amending the plan would be the most literally correct route but costs a
  reapproval and a fresh baseline seal for one blank line.
- Adding an `I001` per-file-ignore was offered and declined: that is moving past
  a failing gate by editing the gate.

After the edit, `make lint-ruff` passes and the self-test still reports its one
case green.

## AC-0005's two routes are not one rule, and the first implementation conflated them

2026-10-05. The `.npmrc` scan in `tools/lint-pack-npm-projects.py` first shipped
refusing every symlink it met. Run against the real repository it reported:

```
lint-pack-npm-projects: npm configuration scan refused linked directory
  .../CLAUDE.md
```

`CLAUDE.md` is a tracked symlink to `AGENTS.md`, and the repository carries one
in several directories, so the check would have redded the build-check gate on a
clean tree.

Only a linked *directory* can hide an `.npmrc`: a linked regular file has no
children, and a symlink actually named `.npmrc` is refused by the name check
that runs before the link test. The branch now resolves the link and refuses
only when the target is a directory, or when it resolves outside the repository
root.

With that corrected the lint reports the real state of the tree — both canonical
manifests have no sibling lockfile — which is the condition T2 exists to clear.

## Mutation proofs for the two guards most able to fail open

2026-10-05, against `tools/test-lint-pack-npm-projects.py`.

| Invariant | Mutation | Result |
| --- | --- | --- |
| AC-0014 cannot pass vacuously | `if not examined:` → `if False:` | 2 cases red |
| AC-0014 integrity floor is `sha512` | `startswith("sha512-")` → `startswith("sha")` | 2 cases red |

Both were restored by editing the line back, not by `git checkout`, and the
suite returned to green. These two were chosen because each failure mode is a
silent pass rather than a crash: an empty quantification and a weak digest both
exit 0 while reporting that provenance was checked.

## A fixture written in a shape no real workflow uses, and what generalizing for it cost

2026-10-05. VI-1009's stale-exemption case first wrote its workflow as a
nameless step:

```yaml
steps:
  - working-directory: packs/demo/tests/skills/demo
    run: node renderer.test.js
```

`_workflow_runner_lines` clears the inherited directory on `- name:` and reads
it from a bare `working-directory:`, so a `- working-directory:` opening a step
matched neither. The node line got no tokens, never counted as a runner for that
directory, and the inverse stale-exemption check it was meant to exercise never
fired.

The first repair generalized the parser: track the step indent and clear the
inherited directory on any `- ` at or above it. That made the fixture pass and
broke the real tree. `tools/test-lint-pack-test-boundary.py` went from one
failing assertion to thirteen, every one of them a false positive against
`.github/workflows/build-check.yml` — `one pytest invocation spans packs
['architect', 'atlassian']` and similar at lines 730-741 and 1258-1259 — because
one step's `working-directory` now leaked into the pytest lines of the steps
after it.

Reverted. The `- name:` reset is correct for this repository: every workflow
step here names itself, which is also the shape VI-1008's own stub uses and the
shape T4's workflow will use. The fixture was the thing written wrong, so the
fixture was fixed — it now opens its step with `- name: renderer suite`. The
companion case added to pin the generalized behaviour was removed with it.

The lesson worth keeping: a fixture in a shape the production corpus never uses
will happily drive a parser change that the production corpus then rejects. The
real tree is the control, and it is cheap to run.

After the revert: `tools/test-lint-pack-test-boundary.py` reports 158 cases
passed, `tools/lint-pack-test-boundary.py --root .` passes 8 of 8 checks over
71 destinations, and the general inverse check — `<suite> is declared unrun in
_NO_RUNNER but a runner names it` — already existed and now fires for Node
runners too.

## Mutation proof for Node runner recognition

2026-10-05. Dropping `_NODE_SUITE.search(line)` from the recognition condition
in `_workflow_runner_lines` turns VI-1008 red (`FAIL (1 of 1)`) and takes two
VI-1009 assertions with it — the suite-inheritance case and the
stale-exemption case. Restored by editing the condition back; both return to
green. The guard is therefore load-bearing for both verification items rather
than only the stub that introduced it.
