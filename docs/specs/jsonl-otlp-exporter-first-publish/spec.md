# Spec: jsonl-otlp-exporter first publication

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0115](../../adr/0115-loop-telemetry-sender-is-a-separately-installed-distribution.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — the published surface is already specified by [`jsonl-otlp-exporter`](../jsonl-otlp-exporter/spec.md)
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author
> corrects them in place as the work teaches, without an amendment and without
> a review round.

## Outcome

`jsonl-otlp-exporter` exists on PyPI, and a stranger who runs `uv tool install
jsonl-otlp-exporter` gets a working `jsonl-otlp-export` command at the version
this repository says it published.

## What Changes

- Nothing in the package. The distribution is built, tested and documented;
  [`jsonl-otlp-exporter`](../jsonl-otlp-exporter/spec.md) shipped with all 76 of
  its criteria discharged, and this spec adds no code.
- `packages/jsonl-otlp-exporter/CHANGELOG.md` moves `0.2.0` from `unreleased` to
  a dated release heading.
- A `jsonl-otlp-exporter-v0.2.0` tag is pushed by the maintainer, which is the
  only trigger `.github/workflows/release-jsonl-otlp-exporter.yml` accepts for
  its `publish-pypi` job.
- The verification ledger gains the published-artifact evidence.

## Why this is a separate spec

The parent spec's contract is about the distribution's behaviour, and every
criterion in it is met. Publication is not one of those criteria — it is a
maintainer gesture with a consequence the repository cannot undo. The release
workflow states the reason at its own `publish-pypi` job: "Publishing claims the
PyPI name, and a name cannot be reclaimed -- so the first publish is the
maintainer's call." Holding a complete 76-criterion contract open for a gesture
it never asked for hid a finished delivery behind an unticked checklist.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Release history | Applicable — a first publication of a public distribution | `packages/jsonl-otlp-exporter/CHANGELOG.md` | AgentBundle maintainers | A dated `0.2.0` heading matching `pyproject.toml` | The changelog carries no `unreleased` heading for a published version |
| Delivery evidence | Applicable — the published artifact can only be observed after the fact | [`notes/verification-ledger.md`](notes/verification-ledger.md) | Implementer | Workflow run reference, index response, and the installed command's observed output | Every criterion below has a recorded observation |
| Decision rationale | Not applicable — ADR-0115 already settles that this is a separately installed distribution | — | — | ADR-0115 | No artifact claims a new distribution decision |

## Agent Rules

### Always do

- Treat the maintainer's tag push as the only route to publication, and record
  the authorizing person and the exact tag in the ledger.
- Verify the published artifact from the public index, in a fresh environment
  that cannot reach this working tree.

### Ask first

- Publish any version other than the `0.2.0` that `pyproject.toml` declares.
- Change the release workflow, which the parent spec's AC-0046, AC-0057,
  AC-0058 and AC-0059 pin.

### Never do

- Never push the release tag, create a PyPI project or token, or otherwise cause
  a publication, on an agent's own authority. The gesture is the maintainer's.
- Never yank, delete or re-upload a published version to correct a mistake
  without the maintainer deciding it; a version number cannot be reused.
- Never substitute a local `pip install` of the built wheel for installation from
  the public index — that proves the wheel, not the publication.

## Testing Strategy

- **Changelog release heading (AC-0001): goal-based check.** The `0.2.0` heading
  carries a date and no `unreleased` marker, and its version equals
  `pyproject.toml`'s.
- **Tag and workflow activation (AC-0002): manual QA.** Only a real tag push can
  start `publish-pypi`; the run reference is read from GitHub.
- **Published-index presence (AC-0003): manual QA.** Read from the public index
  rather than from the build.
- **Installed-artifact behaviour (AC-0004): visual / manual QA.** Install from
  the public index into a fresh environment and run the real console script,
  recording the version string, the exit status, and the stderr note. The
  no-socket property is the parent spec's AC-0001 and is not re-asserted here,
  because no black-box check can observe it.
- **No stub applies.** Every criterion observes an artifact that does not exist
  until the maintainer acts, so none is reachable by a construction test.

## Acceptance Criteria

- [ ] **AC-0001.** `packages/jsonl-otlp-exporter/CHANGELOG.md` records `0.2.0`
  under a dated release heading with no `unreleased` marker, and that version
  string equals `version` in `packages/jsonl-otlp-exporter/pyproject.toml`.
- [ ] **AC-0002.** A `jsonl-otlp-exporter-v0.2.0` tag pushed by the maintainer
  produced a successful `release-jsonl-otlp-exporter` run whose `build-and-smoke`
  and `publish-pypi` jobs both concluded success; the ledger records the run URL,
  the commit SHA, and who authorized the push.
- [ ] **AC-0003.** The public index serves `jsonl-otlp-exporter` at version
  `0.2.0`, observed from the index itself rather than from any build output in
  this repository.
- [ ] **AC-0004.** In an environment with no access to this working tree,
  installing the distribution from the public index produces a `jsonl-otlp-export`
  command for which all three of the following are observed and recorded verbatim
  in the ledger: `--version` prints `0.2.0`; given a JSONL input and a profile but
  no configured endpoint, the command exits 0; and that same run writes the
  unconfigured-endpoint note to stderr that the parent spec's AC-0060 contracts.
  This criterion deliberately does not assert that nothing was sent. The parent
  spec establishes that structurally in AC-0001, by proving the transport seam is
  never constructed, and a black-box install check cannot reproduce it — exit 0 is
  equally consistent with a successful send. The stderr line is the strongest
  no-send signal an outside installer can actually observe.

## Follow-ons

- The parent spec's `Follow-ons` section already owns the four value-level
  conversion questions it deliberately left open; publication does not settle
  them and this spec does not inherit them.

## Assumptions

- The PyPI project name `jsonl-otlp-exporter` is available, or already claimed by
  this maintainer. If it is taken by someone else, AC-0003 is unreachable and the
  distribution needs a renaming decision, which is outside this spec.
