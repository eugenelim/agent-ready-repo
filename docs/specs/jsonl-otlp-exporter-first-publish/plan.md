# Plan: jsonl-otlp-exporter first publication

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `.github/workflows/release-jsonl-otlp-exporter.yml`
  (the only publication route; its `publish-pypi` job is gated on
  `github.ref_type == 'tag'` and uses OIDC trusted publishing with
  `id-token: write` and no stored credential);
  `.github/workflows/release-credbroker.yml` and
  `.github/workflows/release-agentbundle.yml` as the two existing precedents for
  a published package in this repository;
  `packages/jsonl-otlp-exporter/CHANGELOG.md` and `pyproject.toml` as the
  version pair the tag must match;
  [`jsonl-otlp-exporter`](../jsonl-otlp-exporter/spec.md) and its
  `notes/verification-ledger.md`, which already record the pre-publication
  evidence this spec does not repeat. Named deviation: none — this spec adds no
  module, dependency or boundary.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/jsonl-otlp-exporter-first-publish/notes/verification-ledger.md`.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material.

## Approach

Three steps in a fixed order, because the middle one is irreversible and the
other two exist to bracket it. An agent prepares the changelog so the tag has
something truthful to name; the maintainer pushes the tag; an agent then reads
the result from outside the repository. Nothing here builds or changes the
distribution — the parent spec did that and closed with all 76 of its criteria
discharged.

## Constraints

- The agent half is preparation and verification only. Publication is a
  maintainer action, and no task below authorizes an agent to cause one.
- A published version cannot be reused. A mistake in the version pair is cheap
  before the tag and permanent after it, which is why T1 precedes T2.
- The release workflow is pinned by the parent spec's AC-0046, AC-0057, AC-0058
  and AC-0059. This delivery reads it and does not edit it.
- No new dependency, module, top-level directory or interface.

## Construction tests

**Integration tests:** none apply — there is no new code. The repository's
required local lint and type gate runs against the changelog change.

**Manual verification:** the workflow run, the public index response, and the
installed command's output, each recorded verbatim in the verification ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Release heading in `packages/jsonl-otlp-exporter/CHANGELOG.md` | T1 | Version pair compared against `pyproject.toml` | `close-work` confirms no `unreleased` heading names a published version |
| Delivery evidence in `notes/verification-ledger.md` | T1-T3 | Run reference, index response, installed-command output | `close-work` confirms every acceptance criterion carries a recorded observation |

## Design (LLD)

### Interfaces & contracts

No repository interface changes. The operational interface is the tag name
`jsonl-otlp-exporter-v<version>`, which the release workflow already matches and
whose version half it already asserts against `pyproject.toml`. Traces to:
AC-0002. Owned by: T2.

### Failure, edge cases & resilience

The version pair disagreeing is the one failure the repository can prevent, and
the workflow already fails closed on it before build or publish. The failures it
cannot prevent are external: the project name being taken, and the trusted-
publisher identity not being configured on PyPI. Both surface as a failed
`publish-pypi` job rather than a partial publication, and both are maintainer
decisions rather than repairs. Traces to: AC-0002, AC-0003. Owned by: T2, T3.

## Tasks

### T1: The changelog names a release rather than an unreleased version

**Depends on:** none

**Touches:** `packages/jsonl-otlp-exporter/CHANGELOG.md`,
`docs/specs/jsonl-otlp-exporter-first-publish/notes/verification-ledger.md`

**Review shape:** NARROW — one heading and its date.

**Grounding:** `CHANGELOG.md` currently carries `## 0.2.0 — unreleased` with the
complete entry beneath it; `pyproject.toml` declares the matching version.

**Tests:**

- **VI-2001 (AC-0001):** `no stub (goal-based check)` — the `0.2.0` heading
  carries a date and no `unreleased` marker, and a direct comparison shows the
  heading's version equals `pyproject.toml`'s `version`.
- **VI-2002:** `no stub (goal-based check)` — `make lint-ruff lint-mypy` passes.

**Approach:** Change the heading only. The entry body is already written and
accurate.

**Done when:** VI-2001 and VI-2002 are green and the diff changes no production
code, package source, or packaging metadata — only the changelog heading, the
ledger, and the lifecycle bookkeeping this loop mandates (the spec's `Status`
token, its acceptance-criteria checkboxes, and the `workspace.toml` membership
move).

### T2: The maintainer publishes, and the run is recorded

**Depends on:** T1

**Touches:** `docs/specs/jsonl-otlp-exporter-first-publish/notes/verification-ledger.md`

**Review shape:** external evidence capture only.

**Grounding:** `publish-pypi` runs only on a tag push. The workflow declares
`environment: pypi` in-repo at
`.github/workflows/release-jsonl-otlp-exporter.yml:109`, so the repository
controls the *reference*; what it does not control is the pair behind that
name — the GitHub environment object and the PyPI trusted-publisher binding —
and either being absent fails the job.

**Tests:**

- **VI-2003a (AC-0002, precondition):** `no stub (manual QA)` — before the tag
  is pushed, the maintainer confirms the GitHub `pypi` environment exists and the
  PyPI pending publisher is configured for this repository and workflow filename,
  and that confirmation is recorded. This is a read that takes seconds; skipping
  it means the irreversible step is the first thing that tests the configuration,
  and the cost of being wrong is a permanently consumed `0.2.0`.
- **VI-2003 (AC-0002):** `no stub (manual QA)` — after T1 merges and VI-2003a is
  recorded, the maintainer pushes `jsonl-otlp-exporter-v0.2.0`. Record the run
  URL, the commit SHA, both job conclusions, and who authorized the push.

**Approach:** An agent may prepare and show the exact tag command and confirm the
version pair, and may read the run afterward. An agent does not push the tag.

**Done when:** VI-2003a is recorded, and VI-2003 is recorded with both jobs
concluding success. A failed `publish-pypi` stops here and surfaces to the
maintainer rather than retrying.

### T3: The published artifact is verified from outside this repository

**Depends on:** T2

**Touches:** `docs/specs/jsonl-otlp-exporter-first-publish/notes/verification-ledger.md`

**Review shape:** external evidence capture only.

**Grounding:** The parent ledger's "AC-0014 — the real console script" section
records the same shape of check against the locally built wheel on 2026-09-13.
This task repeats it against the published artifact, which is the part that
build could not prove.

**Tests:**

- **VI-2004 (AC-0003):** `no stub (manual QA)` — the public index serves
  `jsonl-otlp-exporter` at `0.2.0`; record the response.
- **VI-2005 (AC-0004):** `no stub (visual / manual QA)` — in a temporary
  directory outside this working tree, install from the public index, run
  `jsonl-otlp-export --version` and confirm `0.2.0`, then run it against a JSONL
  input and a profile with no endpoint configured and confirm both exit 0 and the
  unconfigured-endpoint note on stderr. Record both invocations and all three
  observations verbatim. Do not assert that nothing was sent: that is the parent
  spec's AC-0001, proved structurally, and exit 0 alone cannot distinguish a send
  from a no-send.

**Done when:** VI-2004 and VI-2005 are recorded and all four acceptance criteria
are checked.

## Rollout

- **Delivery:** the changelog edit is reversible; the publication is not. There
  is no rollback for a published version — only a yank, which is a maintainer
  decision and leaves the version number consumed.
- **Infrastructure:** the existing release workflow and the existing `pypi`
  environment. Nothing new.
- **Deployment sequencing:** T1 merges to the default branch, then the tag is
  pushed from it, then T3 observes. The tag must name a commit that already
  carries the T1 changelog heading.

## Risks

- The PyPI project name may be unavailable. The spec records this as an
  assumption rather than a task, because the remedy is a renaming decision the
  maintainer owns.
- The trusted-publisher identity may not be configured on PyPI, which fails
  `publish-pypi` after a successful build. The tag is then consumed; republishing
  needs a new version. T2 stops and surfaces rather than retrying.

## Changelog

- 2026-10-05 — Split from [`jsonl-otlp-exporter`](../jsonl-otlp-exporter/plan.md)
  on owner authority, so a finished 76-criterion contract could close while the
  one gesture only the maintainer can make keeps its own owner and evidence.
