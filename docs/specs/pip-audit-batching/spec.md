# Spec: pip-audit-batching

- **Status:** Archived <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0017 (pip-audit is the SCA gate, auditing the dependency
  manifests the repo owns), ADR-0086 (the SAST/SCA leg is its own `gate-sast` job and
  is the critical path)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — no code shipped.
- **Shape:** service

> **Archived, not shipped.** This spec proposed consolidating the seven per-manifest
> `pip-audit` invocations in `make sast` into one batched invocation. Investigation
> established that the proposal cannot be implemented without permanently reducing SCA
> fidelity, and the trade was declined on 2026-08-17. No gate behaviour changed;
> `Makefile`, `tools/audit-requirements.py`, and `tools/test-audit-requirements.py` are
> byte-identical to commit `823cd174`.
>
> This document is retained because the investigation produced measurements and defect
> findings that are independent of the batching idea, and re-deriving them costs about
> two hours. **If you are here to make `make sast` faster, read § Why this was declined
> first — the obvious approach does not work.**

## Why this was declined

The saving *is* the fidelity loss. They are not separable properties.

`pip-audit`'s cost is network dependency resolution, not process startup. Seven
manifests audited separately means seven resolutions; one batched invocation means one
resolution over the union of all seven. Batching does not make resolution cheaper — it
makes it happen once. And a single resolution over the union applies every constraint
in the union, including upper bounds that live in **upstream package metadata**, which
no rule over this repo's own requirements files can see:

```
httpx          -> httpcore==1.*
markdownify    -> beautifulsoup4<5,>=4.9 , six<2,>=1.15
markdown-it-py -> mdurl~=0.1
```

So the batched audit can resolve a shared transitive dependency to a *lower* version
than a per-manifest audit would, and the set of `(name, version)` pairs it examines is
then a strict **subset** of the per-manifest union. It is never a superset, so the
error direction is always "quieter gate", never "louder". A CVE introduced in a newer
release — precisely what an SCA gate exists to catch — is the class that goes missing.

ADR-0017 decides that pip-audit audits *the manifests the repo owns*. A merged
resolution audits a version combination no adopter installs. Accepting that is an
ADR-level change to the repo's security posture, not a spec-level implementation
detail. Offered as an explicit trade — about 36s locally and 30s in CI, against a
residual that is empirically null today — it was declined in favour of keeping
per-manifest fidelity.

A textual guard *can* close the narrowing this repo would introduce by editing its own
pins (an `==`, `<`, `<=`, `~=`, `!=`, a pip option line, a PEP 508 direct reference, or
a pre-release lower bound). It cannot close the upstream-metadata half. Two independent
reviews converged on this, and the mechanism was verified directly rather than
inferred.

## What was measured

Method: timestamp every output line; attribute any gap `>=4s` locally, `>=5s` in CI, to
the line *after* the gap. Baseline `make sast` was green (exit 0).

| Surface | Total | 7-file loop | Other 3 pip-audits | bandit | semgrep |
| --- | ---: | ---: | ---: | ---: | ---: |
| local `make sast` | 172.0s | 61.4s | 38.0s | 10.9s | 41.4s |
| CI `gate-sast` (run 32063058843) | 160s (job) | 50.6s | 25.1s | 11.0s | 50.8s |

- `make sast` spawns **ten** `pip-audit` processes, of which only **seven** were ever
  collapsible. `flow-metrics/requirements.txt` is comments-only and
  `credential-setup/requirements.txt` holds only the first-party `credbroker` pin, so
  both partition to empty. The remaining three — `--build-system`,
  `tools/requirements-sast.txt`, `/dev/stdin` — must stay separate.
- Batching all seven measured **11.1s**. Batching them with a merge-safety guard that
  sends `tools/requirements.txt` solo (it carries `tomlkit==0.15.1`) measured **25.1s**
  — 14.3s solo plus 10.8s for the batch of six.
- **The remaining lever is semgrep** (41.4s local, 50.8s CI: a 42.3s main scan plus an
  8.5s positive-fixture check), then bandit at ~11s. Neither was investigated.

## Verified facts about `pip-audit` 2.10.1

Kept because each cost a probe and each would otherwise be re-derived. `pip-audit` is
pinned `>=2.10,<3` in `tools/requirements-sast.txt`, so a bump within that range is a
re-probe point.

- `-r` **is** repeatable, and audits every named file in one process.
- All `-r` files are resolved into **one** environment. Two files with conflicting pins
  fail the whole invocation:
  `-r (urllib3==1.26.5) -r (urllib3==2.0.0)` → `ResolutionImpossible`, exit 1.
- **No output format names the requirements file a finding came from.** `columns` has
  no such column; `json` carries only `name` / `version` / `vulns`. So a per-file temp
  name can never restore attribution — the wrapper must print the mapping itself.
- **Exit 1 is the only failure code.** The two `sys.exit` sites in the installed
  package are `_cli.py:192` and `_cli.py:638`, both `sys.exit(1)`, so a finding and a
  resolution failure are indistinguishable by exit code. `2` is argparse's bad-argv
  code, not a pip-audit failure mode.
- **A batch can fail where every member passes.** Reproducible in three commands with
  two CVE-free but conflicting pins:

  ```
  tomlkit==0.13.0  +  tomlkit==0.13.2  in one invocation
    batch    exit 1        (resolution conflict)
    member 1 exit 0
    member 2 exit 0
  ```

  Any batching design must therefore treat a batch's failure as final; a design that
  took its verdict from a per-file re-run would turn this into a green gate.
- For the nine manifests as they stand, the merged resolution **currently** equals the
  union of the per-manifest resolutions — 25 `(name, version)` pairs on each side, no
  divergence in either direction. This is a point-in-time fact about today's graph, not
  a property of batching.

## Pre-existing gate weaknesses found on the way

None of these are caused by batching; all are live in `make sast` today, and all were
recorded in `workspace.toml [backlog].open` rather than fixed here, because each is its
own decision with its own blast radius.

- `sca-requirements-include-lines-unaudited` — a manifest whose only content is
  `-r nested.txt`, `-c constraints.txt`, or `-e .` prints "no third-party requirements
  to audit" and is audited **zero** times, at exit 0. `partition()` passes `-`-prefixed
  lines into the audited half, and the emptiness test then excludes exactly those
  lines. Latent today (no such manifest exists) but the shape is already supported by
  the self-test.
- `sca-ambient-env-can-green-the-gate` — `pip-audit` defaults its vulnerability
  service, OSV URL, format, and output from `PIP_AUDIT_*`, and the resolution venv's
  pip honours `PIP_INDEX_URL` / `PIP_EXTRA_INDEX_URL`. A stale local export can
  re-point the advisory feed or the index and produce "No known vulnerabilities found"
  at exit 0 without touching a tracked file.
- `sca-audited-set-has-no-floor` — argv comes from
  `$(find packs -name requirements.txt | sort)`, whose exit status is swallowed by the
  pipeline. A renamed or missing manifest shrinks the audited set silently at exit 0;
  nothing asserts the expected count.
- `sca-no-strict-flag` — without `-S`, a resolved dependency the advisory service
  cannot serve (a PyPI 404 for that `(name, version)`) is skipped while the process
  still exits 0. Measured free to adopt: 11.3s with `--strict` versus 11.1s without,
  on the same input. This is the cheapest item on this list.
- `sca-no-timeout-on-pip-audit` — no invocation carries a `timeout=`, so a pathological
  resolver backtrack hangs the gate rather than failing it.
- `sca-temp-manifest-leaves-its-directory` — the audited copy is written to the shared
  system temp directory, so any relative `-r` / `-c` / `--find-links` / local-path
  reference in a manifest re-resolves against a world-writable directory. Mode is safe
  (`NamedTemporaryFile`, `O_EXCL`, 0600); the directory is the issue.
- `sast-semgrep-cve-allowlist-pointer-stale` — `Makefile:259` cites
  `docs/backlog.md § semgrep-mcp-cve-allowlist`, but that file is a tombstone and the
  entry lives in `workspace.toml`. It is the only recorded unblock condition for four
  live `--ignore-vuln` suppressions.
- `tools/requirements-evals-locked.txt` is unaudited and falls outside the existing
  `sast-requirements-not-audited` slug, which names only `tools/requirements-sast.txt`
  and `tools/requirements-ci-security-locked.txt`.

## If someone retries this

Two directions survive the analysis:

1. **Attack semgrep, not pip-audit.** It is the larger cost on both surfaces (41.4s
   local, 50.8s CI) and carries no per-manifest fidelity property to lose.
2. **If batching is revisited, it needs an ADR first**, and the guard must be an
   *allow-list*, not a deny-list: a manifest is mergeable only if every audited line is
   `name[extras]` with no specifier or exclusively `>=` / `>` against a final release,
   with no `@` / URL / VCS / local-version part and no option line — anything the
   parser cannot classify goes solo. A deny-list on `==`, `<`, `<=`, `~=`, `!=` is
   default-allow and admits a PEP 508 direct reference, which pins exactly and was
   verified to conflict with a `>=` pin on the same package. That still leaves the
   upstream-metadata residual, which is the reason this was declined.

Do **not** fold `tools/requirements-sast.txt` or the `/dev/stdin` extras audit into any
batch: `--ignore-vuln` is invocation-global, and merging either would extend its four
CVE suppressions to every other manifest.
