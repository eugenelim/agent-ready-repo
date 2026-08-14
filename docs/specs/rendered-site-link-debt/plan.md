# Plan: rendered-site-link-debt

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as the implementation learns. Substantial
> changes are recorded in the changelog.

## Approach

Build the complete site and turn the recorded whole-site crawl into a concrete
remediation inventory. In parallel, develop a pure-stdlib HTML link checker from
focused failing fixtures. Correct each broken target at its authored source or
the projection rule that owns it, then wire the green checker into the local
site gate and Pages workflow after both Astro builds and before upload. The
atomic landing order prevents enforcement from deliberately leaving the branch
red.

## Constraints

- The workspace comment for `rendered-site-link-debt` requires one atomic
  remediation-plus-gate change; spec AC1 is the canonical baseline contract.
- The root `AGENTS.md` requires new `tools/` scripts to be pure-stdlib Python.
- `Makefile` and `.github/workflows/pages.yml` define the load-bearing build
  order: marketing first, technical docs second.
- Generated documentation content is a projection. Fix its source or generator,
  not only `docs-site/src/content/docs/` output.
- This plan has no task or workspace dependency on `m6-live-demo-guide`.

## Construction tests

**Integration tests:** Build the complete combined site and run
`python3 tools/check-rendered-site-links.py --build-dir build`; the final audit
must report zero unresolved internal page and fragment targets.

**Manual verification:** Inspect at least one corrected page from each failure
class in the generated tree and compare its final href and anchor with the
remediation inventory. Confirm the Pages step sits after both builds and before
artifact upload.

## Design (LLD)

### Design decisions

- Scan rendered HTML because source-only checks cannot model Astro directory
  routes and emitted fragments. Traces to: AC1–AC5, AC7.
- Keep remediation data reviewable in the implementation notes or test fixture,
  but do not create a permanent allowlist. Traces to: AC1–AC2, AC10.
- Use Python's `html.parser`, `urllib.parse`, and `pathlib`; no parser dependency
  is needed for the constrained href/id/name contract. Traces to: AC3–AC6.

### Component / module decomposition

- `tools/check-rendered-site-links.py`: confined build-tree discovery, HTML
  extraction, URL normalization, page/fragment resolution, deterministic
  diagnostics, and CLI exit policy.
- `tools/test_check_rendered_site_links.py`: temp-tree construction tests for
  route and fragment behavior plus CLI outcomes.
- Authored guide/site sources and, only where ownership requires it,
  `tools/build-site.py`: repairs identified by the baseline inventory.
- `Makefile` and `.github/workflows/pages.yml`: local and CI integration after
  the complete build.

Traces to: AC2–AC9.

### State & control flow

The checker inventories every HTML page first, records each page's `id` and
legacy `name` anchors, then walks hrefs in sorted source order. Each internal
href is normalized against its source route and the Pages base, resolved to an
emitted file, and—when present—matched to an anchor. Diagnostics are sorted
before rendering so filesystem enumeration order cannot affect output. Traces
to: AC3–AC6.

### Behavior & rules

- External origins and non-navigation schemes do not enter the internal target
  resolver.
- An internal target cannot be excused because its source page is old or
  generated.
- Query strings do not affect page identity; fragments do.
- Directory routes resolve through their emitted `index.html`.
- A baseline-count change requires the reconciliation defined by AC1, not an
  artificial historical result.

Traces to: AC1–AC7, AC10.

### Failure, edge cases & resilience

Invalid invocation, missing build roots, unreadable files, and structurally
invalid build trees exit 2. Broken internal pages or fragments exit 1. The
checker reports all deterministic link failures in one pass so repair does not
devolve into a one-error-at-a-time loop. Traces to: AC4–AC6.

### Quality attributes (NFRs)

The checker is deterministic, dependency-free, platform-neutral, confined to
the selected build directory, and fast enough to run on every Pages build.
Traces to: AC3–AC9.

### Dependencies & integration

The implementation consumes only the existing combined `build/` artifact and
Python standard library. It adds no dependency on another spec or external
service. Traces to: AC3, AC7–AC10.

## Tasks

### T1: The rendered-link checker rejects broken pages and fragments deterministically

**Depends on:** none

**Touches:** tools/check-rendered-site-links.py, tools/test_check_rendered_site_links.py

**Verification mode:** TDD + goal-based end-to-end check

`stub: true`

**Stub:** draft (uncompiled) — the new checker module and CLI do not exist at
spec authoring, and `new-spec` prohibits committing implementation stubs at this
gate. The first implementation action materializes this compilable failing test
shape before any checker source is added:

```python
# STUB: AC3, AC5 — the checker reports a missing internal page deterministically.
def test_missing_page_exits_one_with_stable_diagnostic(tmp_path):
    build = tmp_path / "build"
    build.mkdir()
    (build / "index.html").write_text('<a href="missing/">Missing</a>')

    result = run_checker(build)

    assert result.returncode == 1
    assert result.stdout.splitlines() == [
        "BROKEN index.html: missing/ -> missing/index.html (missing page)",
        "rendered-site-links: 1 broken target across 1 page",
    ]


# STUB: AC4, AC6 — Pages-base, encoded paths, queries, and fragments resolve.
def test_pages_base_encoded_path_query_and_fragment_resolve(tmp_path):
    build = rendered_fixture(
        tmp_path,
        {
            "index.html": (
                '<a href="/agent-ready-repo/docs/a%20b/?view=demo#result">Result</a>'
            ),
            "docs/a b/index.html": '<h2 id="result">Result</h2>',
        },
    )

    result = run_checker(build)

    assert result.returncode == 0
    assert result.stdout == "rendered-site-links: 1 link across 2 pages; clean\n"


# STUB: AC3, AC5, AC6 — a symlink target outside the build root fails closed.
def test_symlink_escape_exits_two_without_reading_target(tmp_path):
    build = rendered_fixture(
        tmp_path,
        {"index.html": '<a href="escape/secret.html">Secret</a>'},
    )
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.html").write_text("outside")
    (build / "escape").symlink_to(outside, target_is_directory=True)

    result = run_checker(build)

    assert result.returncode == 2
    assert "escapes build root" in result.stderr
```

The helper names are the contract surface the focused test file will define;
the draft is not collected until that file is materialized in EXECUTE.

**Tests:**

- TDD cases for relative and root-relative pages, both Pages-base forms,
  directory indexes, queries, encoded components, valid and missing fragments,
  and ignored external/non-navigation schemes. Traces to: AC3–AC6.
- TDD cases for stable diagnostic ordering and exit 0/1/2 behavior. Traces to:
  AC5–AC6.
- Confinement cases ensure resolution stays within the selected build tree.
  Traces to: AC3–AC5.

**Approach:**

- Add focused failing tests using temporary generated-site fixtures.
- Implement extraction, normalization, resolution, reporting, and the CLI with
  standard-library modules only.
- Keep the public invocation to `--build-dir`; add no speculative configuration
  or allowlist surface.

**Done when:** the focused suite passes and deliberate missing-page and
missing-fragment fixtures both exit 1 with stable diagnostics.

### T2: Every recorded rendered-link failure is reconciled and corrected at its owner

**Depends on:** T1

**Touches:** guides/**, web/**, docs-site/**, tools/build-site.py, docs/specs/rendered-site-link-debt/notes/**

**Verification mode:** goal-based end-to-end check

**Stub:** no stub (goal-based)

**Tests:**

- The first complete build plus checker output is reconciled against the AC1
  baseline and classifies every current failure. Traces to: AC1.
- Source/projection fixed-point checks prove regenerated content retains each
  correction. Traces to: AC2.
- Focused existing guide and build-site tests cover every changed projection
  behavior. Traces to: AC2, AC7.

**Approach:**

- Record the current source/href/resolved-target inventory and reconcile count
  drift explicitly.
- Fix authored guide or site sources directly; fix `tools/build-site.py` only
  for failures produced by a shared rewrite rule.
- Rebuild and repeat until the checker reports zero without exclusions.

**Done when:** the complete combined build has zero broken internal page or
fragment targets and every correction maps to an authored owner.

### T3: Local and Pages publication refuse rendered-link regressions

**Depends on:** T1, T2

**Touches:** Makefile, .github/workflows/pages.yml

**Verification mode:** goal-based check

**Stub:** no stub (goal-based)

**Tests:**

- A build-chain construction test asserts the checker runs after both site
  builds and before Pages upload. Traces to: AC8–AC9.
- Workflow path-trigger checks assert edits to the checker and focused suite run
  the Pages job. Traces to: AC8.
- The named local gate runs the same checker command against `build/`. Traces
  to: AC9.

**Approach:**

- Add the checker to the repository's site/documentation test aggregation.
- Expose the post-build audit through the existing site gate or a narrowly
  named Make target.
- Add the required Pages step and path triggers without changing build order or
  deployment permissions.

**Done when:** local and CI gate-shape tests pass and the workflow cannot upload
an artifact after a failing rendered-link audit.

### T4: The complete remediation and enforcement slice passes review

**Depends on:** T1, T2, T3

**Verification mode:** goal-based check + visual/manual QA

**Stub:** no stub (goal-based and manual QA)

**Tests:**

- `python3 tools/test_check_rendered_site_links.py` passes. Traces to: AC3–AC6.
- `make site-build` and
  `python3 tools/check-rendered-site-links.py --build-dir build` pass. Traces
  to: AC7.
- Guide validation, focused projection tests, Ruff, `git diff --check`, and the
  spec-status lint pass. Traces to: AC2, AC8–AC11.

**Approach:**

- Run the narrow gates, then the complete site build and audit.
- Inspect the scoped diff for generated-only fixes, exclusions, route moves,
  unrelated backlog work, and forbidden workspace edits.
- Run adversarial and quality review at the depth selected by `work-loop`.

**Done when:** every acceptance criterion is evidenced, all required gates are
green, and reviewers report no unresolved blocker or major finding.

## Rollout

- **Delivery:** one atomic change containing remediation, checker, tests, and
  gate wiring. Reverting the change restores the prior non-enforcing state.
- **Infrastructure:** none.
- **External-system integration:** GitHub Pages CI consumes the existing built
  artifact; no service or credential is added.
- **Deployment sequencing:** build marketing, build docs, audit combined output,
  then upload. The audit is never enabled against a knowingly broken tree.

## Risks

- The AC1 inventory may drift before implementation. The plan reconciles the
  new baseline rather than losing new failures or preserving already-fixed ones
  artificially.
- A source correction may be overwritten by `build-site.py`. Fixed-point checks
  and projection-focused tests keep ownership at the source.
- URL normalization may accidentally skip a class of internal link. Explicit
  fixtures cover both Pages-base forms, relative routes, indexes, queries, and
  fragments before the real-tree gate is trusted.
- A broad remediation sweep may invite editorial cleanup. The inventory limits
  edits to broken targets and required projection rules.

## Changelog

- 2026-08-13: Initial Draft plan.
