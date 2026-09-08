# Pin the dispatch-only workflows' posture against drift

- **Status:** Draft
- **Owner:** eugenelim

## Outcome

`test-corpus.yml` and `test-roster.yml` carry posture assertions of their own,
so an edit that widens their token, drops their timeout, adds a trigger, adds a
dispatch input, or moves them off a standard hosted runner fails a check instead
of shipping.

## Boundary

- Assert the properties, do not re-describe the file. A check that restates the
  workflow line by line fails on formatting and proves nothing.
- Every assertion carries a mutation that fails it. An assertion family
  evaluated without one is not a proof.
- New files under `tools/` are pure-stdlib, so this parses no YAML with a
  third-party library.
- Do not weaken what already covers these files. `actionlint` and `zizmor` in
  `ci-security.yml` verified them clean at every severity; this adds drift
  protection beside that, not instead of it.

## Owner

Repository maintainers.

## Unresolved questions

- **Own check, or an extension of an existing one?** `test-build-check-workflow.py`
  carries a bespoke mutation driver; `test-ci-security-workflow.py` owns its
  mutation list and delegates to `tools/posture_harness.py`. The harness
  requires one mutation per assertion *family*, not per indexed instance, so a
  per-job assertion over a multi-job workflow needs either one job or a mutation
  per instance.
- **How wide must the key grammar be?** "No job-level `permissions` key under
  any spelling" cannot be held by matching the spellings someone thought of. The
  existing workflow check needed a quote-aware key matcher plus explicit
  rejection of explicit-key and escape-encoded syntax, duplicate keys, and flow
  forms — and GitHub Actions also supports anchors and aliases. The honest shape
  is a declared canonical subset that fails closed on every unmodelled form.

## Opportunity

The two workflows shipped with their posture verified but unpinned. What is
already covered, measured 2026-09-08: `actionlint` clean, `zizmor` clean at
`--min-severity low` and `high`, and `lint-ci-parity` fails on an unclassified
workflow so neither can silently leave the scope map.

What is not covered is drift. The repository-wide excessive-permissions pass in
`tools/check-zizmor-excessive-permissions.py` is scoped to three named
workflows, and `ci-security.yml` runs the broad scanner at
`--min-severity high`, above where that finding class ranks — so a later edit
adding `permissions: contents: write` to either file passes every gate.

The exposure is bounded but real: both workflows are `workflow_dispatch`-only
and a dispatched run executes the selected ref's copy of the file, which
`docs/architecture/verification-graph.md` §7.6 records as an accepted residual.
An assertion here does not close that residual — nothing in-workflow can — but
it does make an unreviewed widening on the default branch fail.

## Projection

- Decide the driver question above before writing assertions, because it
  determines whether the workflows may keep more than one job.
- Assert at minimum: the exact trigger set, the absence of
  `workflow_dispatch.inputs`, top-level `permissions: contents: read` with no
  job-level key, `timeout-minutes` present on every job, `runs-on` an exact
  standard hosted label, `persist-credentials: false` on every checkout, and the
  absence of any `secrets.` reference.
- Wire the check through `tools/repo/build_gate_chain.py` — not the shim at
  `tools/build_gate_chain.py` — and update the ordered literal in
  `tools/test_build_gate_chain.py`, which is a separate edit that fails that
  test if omitted. Wire the paired self-test beside it, per the chain's
  convention.
- Add both paths to `tools/check-zizmor-excessive-permissions.py`'s tuple as
  well, so the permissions class stays scanner-owned rather than review-owned.
  If you do, correct any prose claiming that scanner decides nothing about these
  files.

## Assumptions

- Technical: the two workflows declare `workflow_dispatch` and no other
  trigger, so neither runs on a pull request and neither can be proven by one
  (source: those files).
- Technical: `timeout-minutes` in both is an estimate labelled as such, pending
  a first recorded dispatch (source: those files).

## Source

Deferred from `remote-gate-dispatch` when that slice was cut to dispatch reach
only. Its spec carried an acceptance criterion for exactly this check; the
criterion was not met, and registering it was preferred over building it in
haste, because the reviewers' grammar requirement is the part most likely to
produce a check that cannot fail.
