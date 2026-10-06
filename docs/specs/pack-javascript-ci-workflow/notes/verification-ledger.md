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

## T2 — lock generation, in the order AC-0015 requires

2026-10-05, Node v24.21.0 via nvm with npm 11.19.0. Local default Node is
v26.7.0; the plan pins Node 24 and `test-corpus.yml` sets `node-version: "24"`,
so generation used the pinned line rather than the shell default.

The controls ran before any fetch, in this order, and all four passed:

1. Filename-only `.npmrc` scan — no match, confirmed independently with `find`.
2. `NPM_CONFIG_REGISTRY=https://registry.npmjs.org/` and
   `NPM_CONFIG_REPLACE_REGISTRY_HOST=never` set, then read back through
   `npm config get`: `https://registry.npmjs.org/` and `never`.
3. User and global config neutralized. First attempt pointed both at
   `/dev/null` and npm refused — `double-loading config "/dev/null" as
   "global", previously loaded as "user"` — so two distinct empty files were
   used instead. Worth knowing: the obvious neutralization does not work.
4. Effective configuration carries no scoped-registry override and no auth key.

Generated with `npm install --package-lock-only --ignore-scripts --no-audit`.
Result: `markdown-to-html` 2 non-root entries, `render-proof` 126, both
`lockfileVersion` 3.

### The first lockfile shipped a live advisory, and the gate caught it

`tools/audit-npm.py` reported against the freshly generated tree:

```
✖ packs/converters/.apm/skills/render-proof: 1 blocking advisory(ies)
    GHSA-55q2-fjhq-7xh7 (moderate) dompurify: IN_PLACE hook removal leaves a
    detached subtree executable, causing XSS
```

This is ADR-0083's leg working on content that did not exist until this task
created it, and it is the whole argument for admitting canonical pack lockfiles
into that walk: the advisory was present the moment the lock was written.

Resolved with `npm audit fix --package-lock-only --ignore-scripts`, which moved
the transitive resolution only. The manifest was byte-compared before and after
and is unchanged apart from the `allowScripts` key added separately, so no
direct dependency range moved and the spec's ask-first rule on ranges is not
engaged. Re-audited: both projects report no blocking advisories.

### allowScripts is empty, explicitly

No entry in either lockfile sets `hasInstallScript`, so both manifests carry
`"allowScripts": {}` rather than omitting the key. AC-0007 requires the map to
be present; VI-1006 requires an empty set to produce an explicit empty map. The
distinction matters because an absent key and an empty map read the same to a
human and differently to the lint.

### VI-1007, observed rather than argued

Before the `.gitignore` change both lock paths reported ignored; after it both
report committable, while `node_modules` beneath either skill stays ignored.
The negation is written as `!packs/*/.apm/skills/*/package-lock.json` — a shape
rather than two named projects — so a new canonical project joins the committed
set without editing `.gitignore`, matching the roster-free rule AC-0004 states
for discovery.

## T4 — the workflow shipped with a configuration that could never have run

2026-10-05. The first `.github/workflows/pack-javascript.yml` set both npm
config slots to the same path at job level:

```yaml
NPM_CONFIG_GLOBALCONFIG: /dev/null
NPM_CONFIG_USERCONFIG: /dev/null
```

That is the exact form T2 had already measured as broken four hours earlier:
npm refuses with `double-loading config "/dev/null" as "global", previously
loaded as "user"` and exits before resolving any configuration, so every npm
command in the job dies. Reproduced again under npm 11.19.0 before changing
anything.

The job would have failed rather than passed unsafely — the verify step's
`test "$(npm config get userconfig)" = /dev/null` compares against npm's error
text — so the consequence was a workflow that could never go green, not a
silent hole. Replaced with a step that writes two distinct empty files under
`$RUNNER_TEMP` and exports their paths through `$GITHUB_ENV`. `$RUNNER_TEMP` is
platform-issued and carries no pull-request-controlled value.

The construction test had pinned the broken form as a required setting, so it
was asserting that the workflow must be unusable. It now asserts the working
neutralization and carries an explicit regression case: collapsing both slots
onto one path must be reported as a contract violation.

### Three fixture corpora had to learn the new runner file

AC-0010 puts `.github/workflows/pack-javascript.yml` in `_RUNNER_FILES`, and
the lint refuses a named runner file that does not exist. Three synthetic
corpora build their own catalogues and none of them built it:
`tools/test-lint-pack-test-boundary.py` (via the golden fixture builder),
`tools/test-lint-boundary-golden.py`'s `_FIXTURE_RUNNER_FILES` and its workflow
writer, and `tools/test-lint-boundary-structural.py`'s `_build_min_fixture`.

The last one failed through a byte-exact anchor — `the
every-suite-dir-has-a-runner summary is byte-exact` — because a check with
findings returns no summary at all, so the assertion saw `None`.

A first attempt filtered `runner_files` down to entries the fixture happens to
build. That went green and was wrong: it silently defeated the
`missing-runner-file` plant, whose entire job is to prove the lint notices an
absent runner file. Reverted. The corpora now build the workflow, which is what
mirrors the production inventory rather than hiding a divergence from it.

`tools/test-lint-boundary-golden.py` and `tools/test-lint-boundary-structural.py`
are outside T4's pinned `Touches`. They are admitted as ride-alongs: each change
is a one-line fixture-corpus mirror of an inventory entry the task is required
to add, it alters no behaviour and resolves no design question, and it is
verified by the suite that owns it returning green. Without them AC-0010 cannot
be satisfied and the gate cannot pass.

### External validation

`actionlint .github/workflows/pack-javascript.yml` exits 0. `zizmor` reports no
findings. The parsed workflow carries exactly `workflow_dispatch` (no inputs)
and `pull_request` with paths, `permissions: contents: read`, `ubuntu-latest`
with `timeout-minutes: 20`, and concurrency keyed on the platform-issued PR
number or run ID. It contains no `pull_request_target`, no `secrets.`
reference, no cache action, no `npm audit`, no `npm install`, and no
pull-request-controlled expression — no `pull_request.title`, `body`,
`head.ref`, or `github.head_ref`.

## T5 — release state and current documentation

2026-10-05. The Converters pack and Claude plugin version pair now both read
`0.9.7`; `pack.toml`'s separate `[pack.adapter-contract]` version remains
`0.8`. The non-cosmetic pack-content change includes the two committed
lockfiles and their manifest edits, so the patch bump follows `packs/AGENTS.md`.

The repository's root `.claude-plugin/marketplace.json` is a generated
projection: `packages/agentbundle/agentbundle/build/self_host.py` aggregates
the pack plugin manifests in `_aggregate_marketplace`. It is not hand-edited.
`make build-self` must regenerate it before VI-1014 can be recorded green.

The changelog has a free-standing `## [converters][0.9.7] — 2026-10-05` entry
directly below `[Unreleased]`. It intentionally has no `Highlights` subsection:
this delivery changes maintainer verification and dependency reproducibility,
not a skill outcome or user task.

`docs/architecture/verification-graph.md` now records `pack-javascript.yml` as
path-scoped and dispatchable, with pack installation and render-proof suites as
its responsibility. It explicitly keeps npm audit with `make sast`. Root
`AGENTS.md` now gives the matching `gh workflow run pack-javascript.yml --ref
"$B"` command and labels its result as scoped evidence, not a full gate.

VI-1017 assessment: this delivery adds no prompt, activation surface, rendering
behavior, or output-contract change to Converters. The mandatory eval-harness
rule therefore needs the owner's no-change waiver rather than a harness edit.
No waiver is recorded here.

## T5 — VI-1017, the owner's no-change eval waiver

2026-10-05. `packs/AGENTS.md` requires either a meaningful eval-harness change
or an owner-approved no-change waiver for a pack release. The owner granted the
waiver on the following assessment, which both the implementer and the
supervisor reached independently:

This delivery changed no prompt, no activation surface, no rendering behaviour
and no output contract. What it changed is maintainer verification (a new
path-scoped workflow and a parity/provenance lint), dependency state (two
committed lockfiles and two explicit empty `allowScripts` maps), and
documentation. The Converters skills themselves are untouched, so there is no
skill-facing behaviour for an eval to cover and no eval whose expected result
this change could alter.

## T5 — the artifact AC-0012 names is built by `catalogue build`, not `catalogue package`

2026-10-05, recorded because the first attempt reached the wrong conclusion
with a clean-looking result.

`agentbundle catalogue package --bundle converters` produces an archive holding
no Converters content at all. `--bundle` names the output path only;
`catalogue.toml`'s `[catalogue.package].include` is `["packs/core"]`, so the
archive was core, 701 entries, zero `package-lock.json`. Read without checking
the include list, that looks like AC-0012 failing.

`agentbundle catalogue build --root . --output <dir>` is the command that emits
the Converters tree. Under it AC-0012 holds on all three distribution routes:

| Route | Lockfiles | Sibling manifest present |
| --- | --- | --- |
| `apm/converters/.apm/skills/` | 2 | yes |
| `claude-plugins/converters/skills/` | 2 | yes |
| `agent-plugins/converters/skills/` | 2 | yes |

Six lockfiles, each beside its manifest, and no `node_modules`, `.npm`,
`.yarn`, `.pnpm-store` or `.cache` entry anywhere in the artifact. After
removing the build output the source tree was clean apart from the regenerated
`.claude-plugin/marketplace.json`, which is the authored version pair's
projection and is committed with it.

## T5 — gate results

| Gate | Result |
| --- | --- |
| `make build-self` | ok; marketplace 0.9.6 -> 0.9.7, no other generated drift |
| `agentbundle catalogue verify --root .` | ok |
| `make lint-ruff lint-mypy` | clean, 155 source files |
| `lint-spec-status.py --root .` | spec metadata clean |
| `pytest tools/test_documentation_entry_links.py` | 2 passed |
| `pytest tools/ -k changelog` | 10 passed |

The fleet roster in `verification-graph.md` claimed sixteen workflows against a
tree holding eighteen: `test-corpus.yml`, `test-roster.yml` and
`release-jsonl-otlp-exporter.yml` had never been rostered. All three rows were
added and both counts corrected, verified by comparing the table's row count to
`.github/workflows/*.yml` — 18 and 18. These are ride-alongs: a roster that
states an exact count cannot be left stating a false one by a change that adds
a row to it.
