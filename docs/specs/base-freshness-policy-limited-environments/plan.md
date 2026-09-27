# Plan: Base freshness in policy-limited environments

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `packs/core/AGENTS.md` and `packs/AGENTS.local.md`
  own pack release and projection rules;
  `packs/core/.apm/skills/work-loop/scripts/check-base-freshness.py` and
  `packs/core/tests/skills/work-loop/test_check_base_freshness.py` are the
  production/test pair; `docs/specs/check-base-freshness-guidance-fixes/spec.md`
  is the shipped behavioral precedent. No structural analogue is required;
  the named uncertainty is which Git diagnostics belong to environmental
  unavailability, resolved by retaining the existing narrow missing-branch
  classifier, adding closed remote-unavailable and metadata-denied categories,
  and surfacing every unclassified remote-query or fetch failure.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, execution observations belong in
> `notes/verification-ledger.md`.

## Approach

Extend the helper's closed result vocabulary with `skipped`. Classify
`ls-remote` and fetch C-locale diagnostics through closed tables: timeouts and
named remote transport/authentication failures skip; fetch metadata
permission/policy failures also skip; missing targets and every unclassified
failure surface. Then teach the work-loop to notify once and continue only on
`skipped`, and declare its existing network-fetch boundary and narrow Git
containment in source metadata and prose. Keep target validation and
post-fetch comparison unchanged. Add the failing cases first, update the eval
harness, then bump and regenerate the core pack.

## Constraints

- No new dependency, module boundary, retry, credential probe, or policy bypass.
- `skipped` exits 0 so enterprise runners do not stop on a capability gap, but
  its message and caller handling must never imply that HEAD is current.
- Existing `ok` and `surface` meanings and JSON field names remain unchanged.
- `packs/core/.apm/` is source; `.agents/` and other adapter trees are generated.
- Pack source and plugin versions move together; the changelog entry is
  free-standing beneath `[Unreleased]` and includes a `Highlights` bullet.
- The spec and plan are repository-durable until normal lifecycle closeout.
  Raw review reports remain local-only under ignored `.context/reviews/` and
  are retained only through the review/approval gate. The spec, plan, tests,
  skill source, and release entry are the stable evidence read by maintainers,
  reviewers, CI, and future work-loop sessions.

## Construction tests

**Integration tests:** the existing real-Git pytest module exercises helper
entry-to-JSON behavior; the work-loop eval case exercises the bundled caller
instruction.

**Manual verification:** invoke the projected helper in the current
policy-limited checkout and record exit 0 plus `status: "skipped"`, then run a
temporary-repository stale-base case and record exit 1 plus `status: "surface"`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Work-loop promise and procedure | T2 | eval case and source/projection comparison | source and installed projection agree |
| Bundled helper behavior | T1 | targeted pytest and manual invocation | unavailable and stale observations match the spec |
| Core release history | T3 | version checks, self-host and changelog lint/build checks | release entry and manifests name the same patch release |

## Design (LLD)

### Design decisions

<!-- Owned by: T1. -->

- Add one result constructor, `_skipped`, and one closed fetch-failure
  classifier for each remote Git operation rather than teaching the caller to
  parse human-readable error strings. The helper remains the owner of Git
  failure classification. Traces to AC-0001, AC-0002, and AC-0006. Owned by T1.
- Return exit 0 for `skipped`; a new non-zero code would still appear as a
  failed prerequisite in the restricted hosts this change serves. Traces to
  AC-0001 and AC-0002. Owned by T1.
- Keep Git's existing missing-branch wording as the target correction. Skip
  only timeout, named remote transport/authentication failures, and permission
  or policy denials tied to Git fetch metadata. Surface the unclassified
  remainder from either `ls-remote` or fetch because it may describe unsafe
  local state. Traces to AC-0001, AC-0002, AC-0003, and AC-0009. Owned by T1.
- Add the existing repository vocabulary value `network_fetch` to the skill
  boundary metadata and state the narrower runtime containment in prose:
  retain required local read-only Git checks, confine network-capable Git
  subprocesses to discovery and fetch against configured remotes, confine Git
  metadata writes to the current repository, and perform no credential
  inspection or policy bypass. Traces to AC-0010. Owned by T2.

### Interfaces & contracts

<!-- Owned by: T1, T2. -->

The helper emits the existing `message` and `target` fields plus a `status`
from the closed set `ok | skipped | surface`. Its bundled work-loop caller is
the only independent consumer found by the bounded reference search, so the
script docstring, skill guidance, tests, and eval are the co-versioned private
contract; no standalone schema is added. Traces to AC-0001-AC-0007. Owned by T1 and T2.

### Failure, edge cases & resilience

<!-- Owned by: T1, T2. -->

Timeout and classified transport/authentication remote-query results skip.
Timeout and classified transport/authentication or metadata-policy fetch
failures skip. Missing branch, unclassified remote-query or fetch failure,
invalid target, unsafe local state, stale base, and comparison failures
surface. No failure is retried. Traces to AC-0001, AC-0002, AC-0003, AC-0004,
AC-0005, AC-0006, and AC-0009. Owned by T1 and T2.

## Tasks

### T1: The freshness helper separates unavailable checks from blocking findings

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/scripts/check-base-freshness.py`, `packs/core/tests/skills/work-loop/test_check_base_freshness.py`

**Tests:**

- TDD in `test_check_base_freshness.py`: add real-Git cases for unavailable
  automatic `ls-remote` and a fetch whose remote-tracking ref cannot be locked;
  assert exit 0, `status == "skipped"`, and notice text (AC-0001, AC-0002).
- Add `test_ls_remote_timeout_skips` and `test_fetch_timeout_skips`: import the
  helper as a module, monkeypatch `_run_with_stderr` to return its established
  timeout code only for the named network operation, invoke `main()` against a
  valid temporary repository with discovered and explicit targets, and assert
  exit 0 plus the bounded `skipped` notice (AC-0001, AC-0002).
- Add table-driven remote-query and fetch classifier cases proving that named
  sanitized unavailable categories skip while unmatched diagnostics remain
  `surface` and raw stderr is not emitted (AC-0001, AC-0009).
- Retain the missing-branch, behind-base, rebase-in-progress, multi-remote, and
  malformed-target cases as blocking regression coverage (AC-0003, AC-0004,
  AC-0005).
- `stub: true`; materialize this contract-surface assertion first:

```python
def test_unavailable_remote_head_skips(tmp: Path) -> None:
    repo = tmp / "unavailable-remote-head"
    repo.mkdir()
    git(tmp, "init", str(repo))
    (repo / "f.txt").write_text("init")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "init")
    git(repo, "remote", "add", "origin", str(tmp / "missing.git"))

    rc, out, _err = run_freshness(repo)
    data = json.loads(out)

    assert rc == 0
    assert data["status"] == "skipped"
    assert "not verified" in data["message"]
    assert "separately" in data["message"]
```

**Approach:** Add `_skipped(reason, target="")` beside `_ok` and `_surface`.
It owns the notice suffix so both unavailable routes stay byte-consistent.

**Done when:** the targeted pytest module passes with unavailable cases green
and every retained blocking case still returning exit 1.

### T2: Work-loop guidance and evals act on the tri-state result

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/work-loop/evals/evals.json`

**Tests:**

- Goal-based check: add an eval whose prompt supplies `status: "skipped"` and
  whose assertions require a user notice, continued work, no retry, and no
  current-base claim (AC-0006, AC-0007).
- Goal-based check: bounded searches show the source guidance documents all
  three statuses once and contains no instruction to Surface a skipped check.
- Goal-based check: source frontmatter declares `network_fetch`, source prose
  retains required local read-only checks while confining network-capable Git
  calls and metadata writes to the accepted boundary, and the generated
  projections preserve both without adding credential or policy workarounds
  (AC-0010).

**Done when:** the eval fixture and source guidance give one unambiguous action
for each helper status and accurately declare the skill's minimum authority.

### T3: The core release and projections carry the same behavior

**Depends on:** T1, T2

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`, generated adapter projections

**Tests:**

- Goal-based check: bump the core patch version in its matching source
  manifests, run `FORCE=1 make build-self`, and verify generated projections
  have no drift (AC-0008).
- Goal-based check: run the repository local gates and catalogue verification;
  run the targeted pack suite after projection (AC-0007, AC-0008).
- Manual QA: invoke the projected helper through unavailable and stale paths
  and record exit code and JSON in the verification ledger (AC-0001, AC-0002,
  AC-0003, AC-0004, AC-0005, AC-0006, AC-0009).

**Done when:** manifests, projections, tests, gates, and the free-standing
changelog release entry agree on one patch release.

## Rollout

This ships as one core pack patch. Rollback is the prior pack version; there is
no data migration, infrastructure change, external-system sequencing, or
irreversible step.

## Risks

- A broad skip could hide a wrong target. The retained missing-branch and
  target-validation cases plus the unclassified remote-query and fetch
  fallbacks keep configuration and local repository failures blocking.
- Undeclared Git/network authority could hide the real containment boundary
  from platforms and reviewers. Source metadata, narrow procedure prose, and
  projection checks keep the declaration aligned with runtime behavior.
- Exit 0 could be read as current without inspecting JSON. The caller guidance,
  eval, and manual invocation require an explicit `skipped` notice.
- A source-only edit could leave installed adapters stale. Self-hosting and
  catalogue verification own that drift check.

## Changelog

<!-- Approval entries are added by their human gates. -->

- 2026-09-26: spec approved by owner.
- 2026-09-26: plan approved by owner.
