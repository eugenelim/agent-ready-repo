# Spec: loop-telemetry-export

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0111](../../adr/0111-loop-telemetry-sender-is-a-separately-installed-distribution.md)
- **Depends on:** [`jsonl-otlp-exporter`](../jsonl-otlp-exporter/spec.md) — the sender, which ships first
- **Brief:** none
- **Discovery:** none
- **Contract:** none — the package's public surface is owned by `jsonl-otlp-exporter`
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites.
>
> **This contract is repository-scoped, and deliberately so.** Every criterion
> below is an obligation of *this* catalogue: the mapping profile for its event
> envelope, the declaration in its pack, the enumeration in its gates, the truth
> of its architecture documents. The sender's own behaviour is not specified
> here — it belongs to `jsonl-otlp-exporter`, whose contract may never name this
> consumer.

## Objective

An adopter of this catalogue who wants their work-loop runs visible in an
observability backend installs `jsonl-otlp-exporter`, points it at a Collector,
and sees a log record per phase transition. This spec is what makes that work
*here*: the mapping profile that turns this repository's versioned event envelope
into OTLP, the optional-dependency declaration that tells an adopter the tool
exists, the gate enumeration that keeps the package honest, and the documents
that disclose the capability while it ships sending nothing.

Nothing in any installed pack can send. That guarantee is structural rather than
configured, and it survives precisely because the sender is a separate
distribution an adopter installs on purpose.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable — a sender outside every pack reverses stated current architecture | [`docs/adr/0111-loop-telemetry-sender-is-a-separately-installed-distribution.md`](../../adr/0111-loop-telemetry-sender-is-a-separately-installed-distribution.md) | spec owner | Accepted ADR naming the § 5.2 interpretation and the per-engine default | ADR merged and cited by `telemetry.md` |
| Current architecture | Applicable — `telemetry.md` § 2 states "No exporter ships" and § 5.3 carried a stale blockquote | `docs/architecture/telemetry.md` | spec owner | §§ 2, 5.2, 5.3 and 8 read true against the shipped tool; both anchors resolve | Anchors resolve; no claim contradicts the shipped tool |
| User-facing promise | Applicable — an adopter must learn the capability exists, what it sends, and where | `guides/core/how-to/export-loop-telemetry.md` | spec owner | Disclosure sentence naming capability, payload and destination | Guide indexed |
| Optional-dependency reporting | Applicable — the first reader of `[[pack.runtime-dependencies]]` | `packs/core/pack.toml` + the catalogue lint's reporting path | spec owner | Lint run naming the unsatisfied optional dependency | AC-0039 green |
| Release history | Applicable — a `packs/core` content change | `docs/product/changelog.md` | release workflow | Version bump with entry | Entry present |
| Current product truth | Applicable — the spec must be discoverable | `docs/specs/README.md` | spec owner | Row in the active list | Row present |
| Reusable learning | Applicable — the capability/consumer contract split generalises | `project-knowledge` public seam | work-loop closeout | Capture receipt | Receipt or `project-knowledge unavailable` |
| Operations | Not applicable — no deployed infrastructure is owned here | — | — | — | — |

## Boundaries

### Always do

- Keep the sender outside every pack. This catalogue declares and documents it;
  it does not vendor it.
- Read the repository layout file before the user layout file. Sending data off
  the machine is a team decision, not a personal one.
- Disclose the capability wherever an adopter meets it, while it ships sending
  nothing.

### Ask first

- Making the dependency required rather than optional.
- Having the installer acquire the package rather than report it.

### Never do

- Add a network path to any pack.
- Put `run_id` in a metric dimension. It is a search key; Splunk runs a
  cardinality analysis before indexing a tag and rejects unbounded ones.
- Ship a catalogue-level `[pack.layout.*]` default for telemetry. `output_dir`
  is semantically a confined directory, so an endpoint URL is silently anchored
  under the repository root rather than refused (`telemetry.md` § 5.3).
- Specify the sender's own behaviour here. That contract is
  `jsonl-otlp-exporter`'s, and duplicating it creates a second home that drifts.

## Testing Strategy

**TDD stub dispositions.** Three plan tasks are TDD: T1, T2 and T6. T6 carries a
validated stub with its recorded compile and intended-red results, because its
seam — the existing envelope suite — already exists. T1 and T2 carry `no stub
(implementation-discovered)` with a discovery predicate and proof obligation,
because both depend on interfaces `jsonl-otlp-exporter` publishes and that
package does not exist at plan approval. The remaining tasks are goal-based and
take no stub.

- **VI-0001 — the work-loop mapping profile (AC-0040, AC-0044):** TDD, in the package's profile suite. The profile is data plus a declaration, so its cases are assertions: the envelope's `at` is declared the timestamp, `result` the severity, and `run_id` with `seq` the record identity.
- **VI-0002 — configuration wiring (AC-0041, AC-0043):** TDD. Repository-before-user precedence over two layout files, provable with no network. The order is the deliberate inversion of `desk-research`'s, and `telemetry.md` § 5.3 owns the reason.
- **VI-0003 — optional-dependency reporting (AC-0039):** goal-based check over a lint run with the distribution absent. Reporting only: the assertion includes that no package manager is invoked.
- **VI-0004 — the gates reach the distribution (AC-0031):** goal-based check. Each enumeration site is read and asserted to name the package, because every one is a literal list rather than a glob.
- **VI-0007 — the event line carries its version (AC-0046, AC-0047):** TDD, in the existing envelope suite. A field on a dict and a replay passthrough, both observable from the written file. AC-0047 is the case the rest of the suite cannot see: a build that retro-stamps every replayed record passes everything else.
- **VI-0008 — the event-line contract schema (AC-0048, AC-0049, AC-0050):** goal-based check. The corpus is recorded from real transitions rather than authored, so a line shape the engine emits cannot pass by construction, and the rejection cases stop an empty schema from satisfying the validation half.
- **VI-0009 — an owned reader treats absence as v1 (AC-0051, AC-0052):** goal-based check over the one reader this repository owns besides the engine.
- **VI-0005 — disclosure and the architecture records (AC-0020, AC-0021, AC-0022, AC-0045):** goal-based check over the authored files. Anchor resolution is mechanical; the disclosure sentence is checked for presence, not wording.
- **VI-0006 — exit-band compatibility (AC-0042):** goal-based check. The package reserves 2 through 9; this asserts that reservation is compatible with the band this catalogue's credentialed CLIs already own, so a consumer reading an exit code is never misled.

## Acceptance Criteria

- [ ] **AC-0020.** `guides/core/how-to/export-loop-telemetry.md` contains a
  level-2 heading `## What leaves your machine`, and the section under it
  contains each of the literal strings `.loop-run/events.jsonl`, `OTLP logs`,
  and `nothing is sent until you configure an endpoint`.

- [ ] **AC-0021.** `docs/architecture/telemetry.md` contains neither the literal
  string `does not work today` nor `writes nothing for any pack`.
- [ ] **AC-0045.** Every `agentbundle.md` anchor cited by
  `docs/architecture/telemetry.md` resolves to a heading present in
  `docs/architecture/agentbundle.md`.

- [ ] **AC-0022.** `docs/architecture/telemetry.md` § 2 contains neither the
  literal string `No exporter ships` nor `Nothing transmits`.

- [ ] **AC-0031.** `jsonl-otlp-exporter` appears in the root `pyproject.toml`
  `pythonpath`, mypy's `files`, the `Makefile` test-suite invocations, and the
  pip-audit build-system leg, so its tests and type checks are run by this
  repository's gates.
- [ ] **AC-0039.** With the distribution absent, `agentbundle catalogue lint`
  reports `jsonl-otlp-exporter` as an optional, unsatisfied runtime dependency of
  `core` and exits 0, invoking no package manager.
- [ ] **AC-0040.** This repository ships a profile at
  `packs/core/.apm/skills/work-loop/profiles/work-loop.toml` declaring
  `timestamp_field = "at"`, `timestamp_format = "rfc3339"`,
  `severity_field = "result"`, a `severity_map` covering every value in
  `loop-engine.py`'s `_GATE_RESULTS`, `identity = ["run_id", "seq"]`, and an
  `allowlist` naming every envelope field this catalogue intends to send.

- [ ] **AC-0043.** The documented invocation resolves `--input` to the
  repository root's `.loop-run/events.jsonl`.
- [ ] **AC-0044.** The documented invocation selects the registered `work_loop`
  profile, and a line the engine actually emitted reaches the Collector with its
  `at`, `result`, `run_id` and `seq` at the destinations that profile declares.
- [ ] **AC-0041.** The documented invocation resolves each `[telemetry]` setting
  from the repository `agentbundle-layout.toml` when that file declares it, and
  from the user `agentbundle-layout.toml` when the repository file exists but
  declares no value for it.

- [ ] **AC-0042.** No exit code this catalogue documents for the exporter falls in
  the 2–9 band reserved by
  [`credentialed-cli-exit-code-contract`](../credentialed-cli-exit-code-contract/spec.md).

- [ ] **AC-0046.** Every event line `loop-engine` constructs for a transition and
  appends to `.loop-run/events.jsonl` carries `schema` with integer value 1.
  This governs freshly constructed records only; a replayed record is AC-0047's.

- [ ] **AC-0047.** An `events.pending` record that carries no `schema` key is
  appended to `events.jsonl` unchanged, still carrying no `schema` key.
- [ ] **AC-0048.** The recorded corpus at
  `packs/core/tests/skills/work-loop/fixtures/event-corpus.jsonl` holds at least
  one record carrying `schema` and at least one legacy record carrying none, and
  `contracts/jsonschema/loop-run-event.schema.json` validates every line of it.
- [ ] **AC-0049.** That schema rejects a record whose `schema` is any value other
  than a positive integer, and rejects a record missing any of the seven identity
  fields `seq`, `run_id`, `spec`, `from`, `event`, `to`, `at`.
- [ ] **AC-0050.** `contracts/README.md`'s file table names
  `contracts/jsonschema/loop-run-event.schema.json`.
- [ ] **AC-0051.** The integer written as the field count in
  `docs/architecture/telemetry.md` § 5.1 equals the number of keys on a line the
  engine emits.
- [ ] **AC-0052.** `workspace_mcp.py`'s events poller yields the same parsed
  result for a legacy record carrying no `schema` as for the otherwise identical
  record carrying `schema: 1`.

## Retired identifiers

<!-- Identity is append-only: a retired identifier is never reused. Entries are
     bare identifiers; the narrative belongs above, not on the entry line. -->

AC-0017 through AC-0019 were retired 2026-09-12 when the event-line version was
carved into a separate spec. That spec was folded back here on 2026-09-13, so
their obligations live in this spec again under AC-0046 through AC-0052 — new
identifiers, because identity is append-only and a retired one is never revived.
The remainder were retired on 2026-09-12 to
[`jsonl-otlp-exporter`](../jsonl-otlp-exporter/spec.md) when the sender's
behaviour was separated from this catalogue's integration of it, and are
re-authored there under that spec's own identifiers. None is reused here.

- AC-0001
- AC-0002
- AC-0003
- AC-0004
- AC-0005
- AC-0006
- AC-0007
- AC-0008
- AC-0009
- AC-0010
- AC-0011
- AC-0012
- AC-0013
- AC-0014
- AC-0015
- AC-0016
- AC-0017
- AC-0018
- AC-0019
- AC-0023
- AC-0024
- AC-0025
- AC-0026
- AC-0027
- AC-0028
- AC-0029
- AC-0030
- AC-0032
- AC-0033
- AC-0034
- AC-0035
- AC-0036
- AC-0037
- AC-0038

## Follow-ons

- work-intake: the `adapter-root-bins` upgrade gap — `collect_pack_root_bins` has
  one production caller inside the user-scope install path and no reference in
  `upgrade.py`, so `packs/credential-brokers`'s shipped `sso-broker.py` is
  delivered once and never refreshed. Recorded in
  [`loop-telemetry-export-counterpoints.md`](../../product/research/loop-telemetry-export-counterpoints.md);
  routed as its own item on a separate branch.

## Assumptions

- Technical: gate enumeration in this repository is literal, not glob-based (source: `Makefile:515-516`, `pyproject.toml:16`, `pyproject.toml:94-96`, `Makefile:361-366`)
- Technical: `[[pack.runtime-dependencies]]` exists in the pack schema and has no reader (source: `packages/agentbundle/agentbundle/_data/pack.schema.json:217-246`)
- Technical: the envelope carries fourteen fields once AC-0046 ships, of which `at`, `result`, `run_id` and `seq` are the four the profile needs (source: `docs/architecture/telemetry.md` § 5.1; `loop-engine.py:1608-1623`)
- Process: Tier 1 detect → fail-clean is mandatory and the default (source: `guides/_shared/how-to/author-a-skill.md:104-117`)
- Process: an ADR is sufficient governance here; no RFC is required (source: user confirmation 2026-09-12)
- Product: the sender's contract is capability-scoped and may not name this consumer (source: user confirmation 2026-09-12)
