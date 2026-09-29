# Plan: Read-only base freshness probe

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `packs/AGENTS.md`, `packs/AGENTS.local.md`, and
  `packs/core/AGENTS.md` own pack source, tests, versioning, and projection;
  `packs/core/.apm/skills/work-loop/scripts/check-base-freshness.py` and
  `packs/core/tests/skills/work-loop/test_check_base_freshness.py` are the
  production/test pair; `docs/specs/base-freshness-policy-limited-environments/spec.md`
  owns the shipped tri-state behavior. This is non-structural. The named
  uncertainty is older Git support for fetch `--porcelain`; an exact
  unsupported-option fallback to read-only `ls-remote` preserves the contract.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records
> its baseline. After approval, execution observations belong in
> `notes/verification-ledger.md`.

## Approach

Add a read-only advertisement stage before the existing fetch. On Git versions
that support it, `git fetch --dry-run --porcelain --verbose` supplies the live
target object ID without updating refs or `FETCH_HEAD`; an exact unsupported
option result falls back to `ls-remote`. An explicit target advertises its exact
branch; the normal single-remote path advertises remote `HEAD` directly into the
dry-run destination `refs/remotes/<remote>/HEAD`, so it needs no preliminary
branch discovery. Compare that object ID directly with `HEAD`. Return `ok`
without a write-capable fetch when it is an ancestor, and run the existing
exact-ref fetch only after staleness is established so its success can prepare
an update offer and its policy denial can produce a blocking separate-update
instruction. When the remote moves between those operations, the fetched live
target is authoritative: a now-contained target is current and a still-missing
target remains stale.

## Constraints

- Preserve the private JSON fields and the meanings of `ok`, `skipped`, and
  `surface`.
- Preserve target validation, missing-branch detection, safe rebase guidance,
  dirty-tree handling, unrelated-history refusal, timeout, and closed diagnostic
  classifiers unless an acceptance criterion changes them.
- Use only the Python standard library and installed Git.
- Keep every network-capable Git subprocess repository-scoped and limited to a
  remote name returned by that repository's Git configuration. `--target`
  remains a remote-plus-branch selector, never a raw URL.
- Preserve `metadata.boundaries = ["network_fetch"]` in the source skill and
  generated projections without broadening tool authority.
- `.apm/` is source. Generated adapter projections are refreshed only through
  the self-host build.
- The spec and plan are repository-durable until normal lifecycle closeout.
  Review reports remain local-only under ignored `.context/reviews/` through
  their gates; code, tests, skill guidance, and changelog are stable evidence.
- The dry-run fetch contract is grounded by Git's documentation and a Git 2.50.1
  local-transport probe that returned machine-readable equal object IDs without
  changing metadata. A second dry-run against a different existing local ref
  returned "+ <old> <new> <destination>" while leaving the destination ref
  unchanged, disconfirming the assumption that a changed advertisement needs a
  write-capable fetch before staleness can be detected.
- Declined: a new Git abstraction layer — Cut-before-adding rung 1; the helper
  already owns the command boundary and one additional function is sufficient.
- Declined: a new dependency — Cut-before-adding rung 3; subprocess and strict
  parsing are sufficient.
- Declined: a writable capability-probe file — trust-boundary control; a trial
  write would mutate repository metadata before staleness is known.
- Declined: direct HTTP or a raw-URL Git target — trust-boundary control; the
  configured-remote boundary already supplies the required destination scope.

## Construction tests

**Integration tests:** the existing real-Git pytest module exercises helper
entry-to-JSON behavior across fresh, writable-stale, denied-stale, missing, and
unavailable paths.

**Manual verification:** run the source helper against local-transport fresh and
stale repositories. Record the fresh command trace with no write-capable fetch,
the writable stale update offer, and the denied stale separate-update message.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Work-loop promise and procedure | T2 | eval case and source/projection comparison | source and installed projections agree |
| Bundled helper behavior | T1 | targeted pytest and real invocation | fresh and both stale observations match the spec |
| Core release history | T3 | manifest equality, changelog entry, self-host check | one published patch version carries the behavior |

## Design (LLD)

### Design decisions

<!-- Owned by: T1. -->

- The primary probe is a dry-run fetch with porcelain and verbose output. Dry-run
  makes no changes; porcelain exposes old and new object IDs; verbose forces the
  up-to-date record needed for the fresh path. Traces to AC-0001 through
  AC-0005. Owned by T1.
- With an explicit target the source is `refs/heads/<branch>` and the destination
  is its remote-tracking ref. With one remote and no target, the source is
  remote `HEAD` and the destination is `refs/remotes/<remote>/HEAD`; the target
  label and stale remediation use `<remote>/HEAD`. This keeps live default
  selection inside the same advertisement that decides freshness. Traces to
  AC-0009. Owned by T1.
- The parser accepts one record for the requested destination, a documented flag,
  and full hexadecimal object IDs of the same repository hash width. Empty,
  duplicate, unexpected-destination, abbreviated, or extra output surfaces as a
  malformed advertisement. Traces to AC-0005. Owned by T1.
- An exact unsupported-option diagnostic selects the `ls-remote` fallback.
  Other dry-run failures retain the closed unavailable/unclassified routing.
  Traces to AC-0004 through AC-0006. Owned by T1.
- A live target is current when `git merge-base --is-ancestor <advertised> HEAD`
  exits 0. Exit 1 proves stale. Other comparison failures surface unless the
  target object is absent locally, which is itself proof that `HEAD` cannot
  reach it and therefore proves stale. Traces to AC-0001, AC-0003, and AC-0005.
  Owned by T1.
- Only the stale path runs the existing exact-ref fetch. Success retains the
  existing count, history, worktree, and rebase safety checks; a classified
  metadata denial stays stale and changes only the next action. If the remote
  moves during that fetch, the fetched live target replaces the earlier
  advertisement as the authority: return `ok` only when it is now contained,
  otherwise retain the stale result. Traces to AC-0002 and AC-0003. Owned by T1.
- Resolve remote names only from the current repository and keep every fetch or
  `ls-remote` call on that configured-name boundary. The parser continues to
  accept `--target` only as configured remote plus branch; no URL or transport
  implementation is added. Traces to AC-0012. Owned by T1.

### Interfaces & contracts

<!-- Owned by: T1, T2. -->

The private helper output remains `status`, `message`, and `target`.
Messages distinguish unavailable, writable stale, and unwritable stale results;
the work-loop caller maps them to continue, update offer, or separate update.
No public schema is added. The source skill and projections retain the existing
`network_fetch` boundary metadata. Traces to AC-0001 through AC-0007 and
AC-0011. Owned by T1 and T2.

### Failure, edge cases & resilience

<!-- Owned by: T1, T2. -->

Remote advertisement timeout and existing classified transport or
authentication failures skip. Unsupported porcelain alone falls back.
Malformed output, unclassified failures, invalid targets, unsafe local state,
and comparison errors surface. A stale-only metadata denial surfaces as stale
instead of skipping. Remote names remain repository-configured, raw URLs are
rejected, and no remote operation retries. Traces to AC-0003 through AC-0007
and AC-0012. Owned by T1 and T2.

### Dependencies & integration

<!-- Owned by: T1, T3. -->

The implementation depends only on the installed Git CLI. Git documentation is
the command contract; the test suite supplies local remotes for deterministic
coverage. Core self-hosting projects the changed skill and script into adapter
trees. Traces to AC-0006 and AC-0008. Owned by T1 and T3.

## Tasks

### T1: Fresh bases pass without a write-capable fetch and stale bases remain blocking

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/scripts/check-base-freshness.py`, `packs/core/tests/skills/work-loop/test_check_base_freshness.py`

**Tests:**

- TDD in `test_check_base_freshness.py`: record the helper's fetch commands and
  prove a fresh advertised target returns `ok` without any fetch lacking
  `--dry-run` (AC-0001).
- TDD on the no-`--target`, single-remote entry point: deny `ls-remote`, return a
  fresh remote-`HEAD` porcelain record, and prove the helper returns `ok`
  without `ls-remote` or a write-capable fetch (AC-0009).
- TDD with real local remotes: prove a stale writable repository reaches the
  existing protected update path, while a classified metadata denial returns a
  blocking separate-update message; cover an advertised commit that is absent
  locally as stale rather than as an ancestry error, and prove that a remote
  which moves to an already-contained target during the stale-only fetch returns
  `ok` from that fetched live target (AC-0002, AC-0003, AC-0005).
- TDD with command seams: prove unavailable advertisement stays `skipped`,
  malformed porcelain and unclassified failure surface, and the exact
  unsupported-option diagnostic takes the `ls-remote` fallback (AC-0004,
  AC-0005, AC-0006).
- Retain all target-validation, rebase-state, dirty-tree, unrelated-history, and
  missing-branch tests as regression coverage (AC-0005).
- Command-trace tests prove every fetch and `ls-remote` uses a configured remote
  name in the current repository, while raw-URL targets fail validation before
  a network subprocess starts (AC-0012).
- `stub: true`; materialize this contract-surface assertion first:

```python
def test_fresh_dry_run_never_attempts_write_fetch(
    tmp: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    origin = tmp / "fresh-origin"
    origin.mkdir()
    git(tmp, "init", "-b", "main", str(origin))
    (origin / "a.txt").write_text("a")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "A")
    repo = tmp / "fresh-clone"
    subprocess.run(
        ["git", "clone", str(origin), str(repo)],
        check=True,
        capture_output=True,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    module = load_freshness_module()
    original = module._run_with_stderr
    fetch_commands: list[list[str]] = []

    def fake_run_with_stderr(
        cmd: list[str], *, timeout: int | None = None
    ) -> tuple[int, str, str]:
        if len(cmd) > 1 and cmd[1] == "ls-remote":
            pytest.fail("default freshness attempted separate remote discovery")
        if len(cmd) > 1 and cmd[1] == "fetch":
            fetch_commands.append(cmd)
            if "--dry-run" not in cmd:
                pytest.fail("freshness attempted a write-capable fetch")
            return 0, f"= {head} {head} refs/remotes/origin/HEAD", ""
        return original(cmd, timeout=timeout)

    monkeypatch.chdir(repo)
    monkeypatch.setattr(sys, "argv", ["check-base-freshness"])
    monkeypatch.setattr(module, "_run_with_stderr", fake_run_with_stderr)

    assert module.main() == 0
    assert json.loads(capsys.readouterr().out)["status"] == "ok"
    assert fetch_commands and all("--dry-run" in cmd for cmd in fetch_commands)
    assert any("+HEAD:refs/remotes/origin/HEAD" in cmd for cmd in fetch_commands)
```

**Approach:** keep command construction and parsing inside the helper. Reuse the
existing subprocess seam and classifiers so tests observe the real entry point
without adding an abstraction layer.

**Done when:** the targeted pytest module passes and its fresh-path trace contains
only the dry-run fetch.

### T2: Work-loop guidance offers the available update and names the unavailable one

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/work-loop/evals/evals.json`

**Tests:**

- Goal-based eval: a writable stale result stops and asks before running the
  supplied safe update path (AC-0002, AC-0007).
- Goal-based eval: an unwritable stale result stops, recommends a separate user
  update, and never treats the result as `skipped` (AC-0003, AC-0007).
- Bounded source checks keep `ok`, `skipped`, and both stale messages
  unambiguous and retain the no-retry, no-credential, and no-policy-bypass rules
  (AC-0004, AC-0007).
- Bounded source and projection checks retain the `network_fetch` metadata
  boundary without broadening declared authority (AC-0011).

**Done when:** the skill and eval fixtures give one action for every helper
outcome without changing the JSON vocabulary.

### T3: Core release surfaces carry the read-only-first behavior

**Depends on:** T1, T2

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`, generated adapter projections

**Tests:**

- Goal-based check: bump both core manifests from their current matching version
  to one patch release and add a free-standing changelog entry with a
  consumer-facing highlight (AC-0010).
- Goal-based check: run self-hosting, targeted pytest, repository lint/type
  gates, and catalogue verification; confirm regenerated projections have no
  drift and retain the `network_fetch` boundary metadata (AC-0008, AC-0011).
- Manual QA: invoke the projected helper through fresh and both stale paths and
  record JSON, exit code, and fetch command class in the verification ledger
  (AC-0001, AC-0002, AC-0003, AC-0009).

**Done when:** manifests, source, projections, tests, gates, and changelog agree
on one patch release.

## Rollout

This ships as one core pack patch. Rollback is the prior pack version; there is
no data migration, infrastructure change, external-system sequencing, or
irreversible step.

## Risks

- A loose parser could accept an unrelated ref advertisement. Exact destination
  and object-ID validation fail closed.
- A compatibility fallback could silently weaken freshness to a cached ref. It
  uses only a live `ls-remote` query and otherwise returns the existing
  unavailable or surface result.
- A remote can move between advertisement and stale-only fetch. The post-fetch
  comparison is authoritative: it returns current only if the fetched live
  target is already contained, and otherwise remains stale.
- A new fallback could widen the outbound destination. Command construction is
  confined to configured remote names in the current repository; raw URLs and
  alternate HTTP code remain outside the contract.
- A source-only change could leave installed adapters stale. Self-hosting and
  catalogue verification own projection drift.

## Changelog

<!-- Approval entries are added by their human gates. -->

- 2026-09-29: spec approved by owner.
- 2026-09-29: plan approved by owner.
