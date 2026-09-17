# Spec: telemetry-sender-owns-its-configuration

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0115](../../adr/0115-loop-telemetry-sender-is-a-separately-installed-distribution.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — the sender's public surface is owned by
  [`jsonl-otlp-exporter`](../jsonl-otlp-exporter/spec.md), which this delivery amends
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

## Objective

A caller that sends loop telemetry needs nothing from `agentbundle`. It builds
five static paths from a repository root and a user layout directory, hands them
to `jsonl-otlp-export`, and the sender resolves the `[telemetry]` configuration
itself from both layout scopes.

The caller this serves is a hook. Every hook this repository ships is
deliberately standard-library-only, and importing any `agentbundle` module parses
a 45,349-byte contract file at import time to populate `SPEC_VERSION`. A hook that
had to resolve telemetry settings would be the first to take a package
dependency, and would pay that parse on every invocation to learn two strings.

Configuration lives where it already lived: a `[telemetry]` table in
`agentbundle-layout.toml`, in a repository scope and a user scope. A setting the
repository file declares wins; only a setting it omits falls through to the user
file. What changes is that the sender reads both files, rather than a
repository-side resolver reading them and re-rendering their values as flags.

Two properties hold across the change. Sending stays off until an endpoint is
configured, so installing anything still transmits nothing. And a `[telemetry]`
key the sender cannot deliver is refused, naming the scope it came from, rather
than silently dropped.

That refusal is what carries cross-version safety, and its reach is bounded by
which senders have it. A sender refuses every key outside its own admitted set,
so one meeting a layout newer than itself fails loudly instead of ignoring a
setting the adopter believes is active — but only from the version that
introduced the refusal onward. The bound costs nothing in the field because that
version, `0.2.0`, is the sender's **first published** one: no released sender
predates the refusal, so there is no older-sender case for an adopter to hit.
Nothing enforces a minimum sender version, and nothing here adds one — the
optional runtime dependency in `packs/core/pack.toml` carries no version pin
because the lint that reads it tests only presence.

**Where the sender's own criteria live.** The endpoint precedence chain, the
`--user-config` flag, the per-setting merge rule, the admitted-key set and its
refusal are the sender's published CLI contract, owned by
[`jsonl-otlp-exporter/spec.md`](../jsonl-otlp-exporter/spec.md). This delivery
amends that spec and does not restate its criteria here; one fact, one home. The
criteria below are about this repository's use of the sender: that the documented
invocation needs no `agentbundle` import, that it resolves to the right
arguments, that both scopes reach a real run, and that the retired resolver
leaves no reference behind.

**Why the shipped consumer contract needs no edit, and owns what is not restated
here.** [`loop-telemetry-export`](../loop-telemetry-export/spec.md) is `Shipped`,
so no meaning-changing edit to its body is licensed; a correction goes to the
code, or to an ADR with a Status-field annotation
(`docs/CONVENTIONS.md:430-432`). Only meaning-preserving mechanical rewrites,
such as a moved path, are carved out (`:178-182`). It needs neither. Its AC-0041,
AC-0043 and AC-0044 each constrain "the documented invocation" rather than the
package implementing it, so all three stay true once resolution moves into the
sender.

Those three criteria therefore remain the **owner** of the obligations they
state: that the invocation resolves `--input` to the repository's event log, that
it passes the work-loop profile to `--profile`, and that each `[telemetry]`
setting resolves repository-first across the two scopes. This spec authors no
criterion for any of them. What this delivery adds is the missing *verification*:
all three are ticked with no test behind them, and the roster test named in the
Testing Strategy pins them for the first time. A criterion here would be a second
home for a responsibility that already has one. A reader who later reaches for
AC-0041 to relocate it should stop: there is nothing to move.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — the documented invocation is the surface an adopter copies | `guides/core/how-to/export-loop-telemetry.md` | spec owner | AC-0001 and AC-0003 green | Both Python blocks run with `agentbundle` unimportable, and name the two layout files as separate paths |
| Interface compatibility | Applicable — the sender gains a flag and refuses a previously ignored key | `docs/specs/jsonl-otlp-exporter/spec.md` | spec owner | That spec's amended AC-0002 and AC-0007, plus its new criteria for `--user-config`, the merge, and the refusal | Amendment recorded with its reason, and the sender suite green against it |
| Current architecture | Applicable — § 5.3 describes this configuration path in the conditional mood while it now ships | `docs/architecture/telemetry.md` § 5.3 | spec owner | § 5.3 describes the two-flag mechanism as shipped; `test_loop_telemetry_disclosure_contract.py` still green | Section names the two flags, and no shipped invariant (AC-0021, AC-0022, AC-0045, AC-0054) regresses |
| Current product truth | Applicable — the PyPI README advertises the retired resolver | `packages/agentbundle/README-pypi.md` | spec owner | AC-0004 green | No live surface references the retired module |
| Interface compatibility — the sender's published description | Applicable — the sender gains a flag and changes flag semantics, and its README is what PyPI shows | `packages/jsonl-otlp-exporter/README-pypi.md`, its `CHANGELOG.md`, its `pyproject.toml` | spec owner | Option table and four-source precedence list name `--user-config`; version bumped | Published prose matches the shipped flag set, and the behaviour change is named |
| Release history | Applicable — a public module is removed from a released distribution | `packages/agentbundle/CHANGELOG.md`, `docs/product/changelog.md` | spec owner | Entry naming the removal under the bumped version | `pyproject.toml` and `version.py` agree, and the changelog names the removal |
| Decision rationale | Applicable — a live shaping question is answered by this delivery | `docs/product/intents/loop-telemetry-contract-corrections.md` | repository maintainers | The undeliverable-setting question recorded as answered, with AC-0031's half explicitly untouched | The intent states which of its two questions this delivery closed and which remains |
| Reusable learning | Applicable — every new control needs mutation proof before it is trusted | `docs/specs/telemetry-sender-owns-its-configuration/notes/verification-ledger.md` | spec owner | Per-control mutation record: the mutation, the observed red, the suite | Every control added by this delivery has a recorded failing mutation |
| Operations | Not applicable | — | — | — | — |
| Maintainer procedure | Not applicable — no new maintainer step; the existing release and roster procedures cover it | — | — | — | — |

## Boundaries

### Always do

- Keep the standard library the only runtime dependency of both packages.
- Honour the sender's unconditional-read criterion, which T1 adds to
  `docs/specs/jsonl-otlp-exporter/spec.md`, rather than restating the behaviour
  here — that spec owns it.
- Keep sending off until an endpoint resolves, so installing or configuring a
  layout section transmits nothing on its own.
- Prove each new control fails against a wrong implementation before trusting it.

### Ask first

- Adding a setting to the admitted `[telemetry]` set, or changing which scope
  wins for a setting.
- Extending the install-time layout projection to write telemetry configuration.
- Changing the sender's exit-code behaviour for a refused configuration file.

### Never do

- Add a runtime dependency to either package, or make `agentbundle` import the
  sender — the sender is an *optional* dependency of `packs/core`, so the import
  would not resolve.
- Name a specific consumer, product, repository or catalogue in a criterion of
  the sender's contract, including the `agentbundle-layout.toml` filename, the
  `.loop-run/events.jsonl` input path, and the work-loop profile path.
- Edit anything under `docs/specs/loop-telemetry-export/` — the spec is `Shipped`
  and its directory is frozen.
- Let the sender derive a configuration filename from a directory. The caller
  supplies each file path.

## Testing Strategy

Five outcomes, each paired with a mode and the reason for it. All five are
repository-level claims — they read `guides/`, `packs/` and the installed
package together — so they live in `tests/roster/`, anchored at
`Path(__file__).resolve().parents[2]`, per
[`tests/AGENTS.md`](../../../tests/AGENTS.md). The sender's own behaviour is
verified in `packages/jsonl-otlp-exporter/tests/` against fixtures, under the
amended sender spec's Testing Strategy; none of it may read above that package.

- **VI-0001 — the documented invocation takes no package dependency (AC-0001):**
  goal-based check, exercised as an integration test. Each block runs in a
  **subprocess**, not in the test's own interpreter, under a `sys.meta_path`
  finder that refuses `agentbundle`. The subprocess is what makes the control
  sound: an in-process finder is never consulted for a module already in
  `sys.modules`, and the test runner itself may well have imported `agentbundle`,
  so the same assertion in-process could pass a guide that does import it. Two
  weaker forms were rejected — a lexical subset test over parsed imports is
  vacuously true for a guide with no blocks and blind to
  `__import__("agentbundle")`, and a lexical blacklist of dynamic-import spellings
  is defeated by an alias, `runpy` or `exec`. Executing the block is the only form
  that carries the semantic claim, so it is the whole criterion; the block-count
  floor stops the vacuous case.
- **VI-0002 — the retired module is gone and unreferenced (AC-0002, AC-0004):**
  goal-based check. AC-0002 is one `find_spec` call, which resolves the module
  path without executing it, so a tombstone module that raises
  `ModuleNotFoundError` from its body cannot pass. AC-0004 is a tree sweep over
  the live surfaces. They are separate criteria because a deleted module with a
  surviving README claim passes the spec lookup and still misleads a reader, and a
  stale claim is the failure that outlives the deletion. The exemption is pinned to
  two contexts rather than to the filename, and each is admitted for its own
  reason: the `## [0.45.0]` heading, whose entry describes what that release
  shipped and stays accurate about it, and any `### Removed` subsection, which is
  where this delivery must name the module it removed. Every other position fails,
  so a current-version `Added` or `Changed` entry still advertising the resolver —
  the exact shape of a live stale claim — is caught rather than exempted.
- **VI-0003 — the two-scope invocation shape (AC-0003):** TDD. The criterion names
  the two literal paths, which is the observable; the test additionally parses the
  documented argument list with the sender's own `build_parser()`, so a renamed
  flag fails here rather than at an adopter's first run. The parser is the
  mechanism and stays in this strategy, not in the criterion.
- **VI-0004 — the frozen consumer criteria gain their first test (owner:
  `loop-telemetry-export` AC-0041, AC-0043, AC-0044):** TDD, exercised as an
  integration test across the guide, the profile and the sender. This spec authors
  no criterion for these; it supplies the control they never had. Three arms,
  because AC-0041 is about *precedence* and not merely about arrival:
  a conflicting arm where both scopes declare the same setting and the repository
  value must win — disjoint settings cannot prove precedence and stay green if the
  two flags are swapped; a fallthrough arm where the repository file omits a
  setting the user file supplies; and, for AC-0043 and AC-0044, the sole event
  placed only at `.loop-run/events.jsonl` under the real work-loop profile, so a
  wrong `--input` or `--profile` fails rather than being unobserved. All arms
  assert on the emitted request and its destination through the sender's
  `connection_factory` seam, after a positive emitted-record count — a run that
  emits nothing satisfies any claim quantified over emitted records, and an
  assertion on a returned mapping would prove the parse rather than the delivery.

Every control this delivery adds carries a recorded mutation proving it red
against a wrong implementation, in
[`notes/verification-ledger.md`](notes/verification-ledger.md). The sweep at
`packages/jsonl-otlp-exporter/tests/wiring_sweep.py` must report no survivor
this delivery introduced; the two it already reports — `profile.py:65` and
`transport.py:109` — are out of scope.

## Acceptance Criteria

- [x] **AC-0001.** Each of the two Python blocks the guide's invocation section
  documents runs to completion in a fresh interpreter in which importing
  `agentbundle` fails, and both blocks are present.
- [x] **AC-0002.** `importlib.util.find_spec("agentbundle.telemetry_layout")`
  returns `None`, so no module provides that path and the answer does not depend
  on executing one.
- [x] **AC-0003.** The documented invocation passes `--config` the repository
  root's `agentbundle-layout.toml` and `--user-config` the user layout
  directory's `agentbundle-layout.toml`, as two separate file paths.
- [x] **AC-0004.** No file under `packages/`, `guides/`, `packs/` or `tools/`
  contains the string `telemetry_layout`, except in
  `packages/agentbundle/CHANGELOG.md`, where every occurrence sits either under
  the `## [0.45.0]` heading or in a `### Removed` subsection.

## Follow-ons

- AgentBundle distribution maintainers:
  [`docs/product/intents/catalogue-level-telemetry-endpoint-default.md`](../../product/intents/catalogue-level-telemetry-endpoint-default.md)
  — let an enterprise operator bake a telemetry endpoint once in its catalogue so
  every user installing the core pack exports to it with no setup. That runs
  through RFC-0101's pack-defaults cascade, not the `[telemetry]` resolution this
  spec ships, and needs no schema change: `[pack-defaults.<pack>]` is an open map
  of string keys. The missing hop is that the baked layer is reachable only via
  `agentbundle.config.load_pack_config()`, while both readers here are
  standard-library-only — which is the same gap
  [`credential-pack-defaults-projection`](../../product/intents/credential-pack-defaults-projection.md)
  records for credentials, so the two share one projection. It also needs this
  spec's Objective to admit an operator consenting on its users' behalf, since an
  enterprise default means installing does begin sending.

- repository maintainers:
  [`docs/product/intents/loop-telemetry-contract-corrections.md`](../../product/intents/loop-telemetry-contract-corrections.md)
  — AC-0031's four-of-six gate enumeration remains open. This delivery answers
  only that intent's second question, by giving the undeliverable-setting refusal
  a criterion in the sender's contract.

## Assumptions

- Technical: `telemetry_layout.resolve` has no production caller. Its only
  references outside its own module and test are two documentation snippets, one
  README paragraph, two changelog entries and one shaping intent (source: `grep -rn
  telemetry_layout` returns `guides/core/how-to/export-loop-telemetry.md:133,167`,
  `packages/agentbundle/README-pypi.md:41`,
  `packages/agentbundle/CHANGELOG.md:35`, `docs/product/changelog.md:187`,
  `docs/product/intents/loop-telemetry-contract-corrections.md:23`, and
  `packages/agentbundle/tests/unit/test_telemetry_layout.py:13`)
- Technical: no install-time, catalogue or schema path reads a `[telemetry]`
  table. `agentbundle-layout.toml` is read by 84 `.py` files, but for other
  sections — `lint-traceability.py:231` reads `[traceability]` and
  `workspace_mcp.py:1577` reads `output_dir` (source: `grep -rn agentbundle-layout
  --include='*.py'`, then `grep -rn telemetry packages/agentbundle/agentbundle/`,
  which matches only `telemetry_layout.py` itself)
- Technical: a catalogue-level default cannot carry an endpoint because
  `_append_layout_section` types its value as a scope-confined directory, so a
  URL is silently anchored as a path rather than refused (source:
  `docs/architecture/telemetry.md:169-180`)
- Technical: `pack.layout.{repo,user}` admits exactly `parent`, `template`,
  `output_dir` and `section` under `additionalProperties: false` (source:
  `contracts/pack.schema.json`)
- Technical: the sender already owns every open-time guard this needs, all
  standard library — no-follow open, fstat regular-file proof on the descriptor,
  a 64 KiB ceiling, and a short-read refusal (source:
  `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/config.py:39-84`)
- Technical: `read_config_file` is reached only when both endpoint environment
  variables are absent — the logs-specific variable returns early at `:106-108`
  and the base variable guards the file read at `:110-112` — so a refusal placed
  inside that branch cannot fire when either is set (source:
  `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/config.py:106-112`)
- Technical: a `version` pin on the optional runtime dependency would be inert —
  the schema admits one, but the lint only tests presence via
  `importlib_metadata.distribution(package)` (source:
  `packages/agentbundle/agentbundle/catalogue_tooling/lint.py:1663-1666`)
- Technical: the exporter's declared public surface is the console script;
  `__init__.__all__` is `["__version__"]` only (source:
  `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/__init__.py`)
- Technical: the guide already hardcodes `Path.home() / ".agentbundle"` and does
  not honour `AGENTBUNDLE_USER_ROOT`, so a standard-library-only snippet loses
  nothing that works today (source: `export-loop-telemetry.md:136` against the
  resolver at `packages/agentbundle/agentbundle/scope.py:203`)
- Process: `loop-telemetry-export` is `Shipped`, so no meaning-changing edit to
  its body is licensed — a correction goes to the code or to an ADR with a
  Status-field annotation, and only meaning-preserving mechanical rewrites are
  carved out; its AC-0041, AC-0043 and AC-0044 constrain "the documented
  invocation" rather than the implementing package, so they remain their
  obligations' owner (source: `docs/specs/loop-telemetry-export/spec.md:3,151-163`,
  `docs/CONVENTIONS.md:430-432` and `:178-182`)
- Process: registering a roster test obliges a `build-check.yml` step, a
  `STEP_DISPOSITION` of `LOCAL("test-after-build-check")` in
  `tools/lint-ci-parity.py`, and a `.workspace-prune-protected.toml` entry when it
  names a `docs/specs/<slug>` literal (source: `tests/AGENTS.md` § Roster is not
  auto-discovered)
- Process: the guide is already pinned by
  `tests/roster/test_loop_telemetry_disclosure_contract.py` for AC-0020's heading
  and three literals and AC-0042's reserved exit-code band (source: that file,
  lines 82-155)
- Process: removing a library module is not a release trigger — release is scoped
  to a public CLI verb, flag semantics, output layout, or a schema change
  invalidating previously valid files — but it is non-cosmetic, so both
  `pyproject.toml` and `version.py` bump (source: `packages/AGENTS.local.md` §
  release-coupling, `packages/AGENTS.md` § Version bump rule)
- Product: the motivating caller is a telemetry hook that does not exist yet —
  `tools/hooks/` holds only `session-start.py`, `pre-pr.py` and
  `work-loop-check.py`. This change buys headroom for that hook rather than
  fixing a live defect (source: user confirmation 2026-09-16)
- Product: refusing a previously ignored `[telemetry]` key is chosen over a
  warning so a cross-version mismatch fails loudly rather than dropping a
  setting. Corrected during T7: the sender is *not* yet published — its
  changelog heads `## 0.2.0 — unreleased`, `0.1.0` was replaced before it was
  ever published, and no tag exists — so this breaks no installed adopter. The reason for refusing stands, since it is about future
  pairings rather than current ones (source: user confirmation 2026-09-16;
  release state measured 2026-09-16)
- Product: the `--service-name` flag outranks a repository-scope
  `[telemetry].service_name`, so a single run stays overridable (source: user
  confirmation 2026-09-16)
- Product: `agentbundle.telemetry_layout` is retired rather than kept behind a
  drift guard, accepting the loss of a separate early error (source: user
  confirmation 2026-09-16)
- Product: a future enterprise-baked default binds the individual user rather
  than a team repository, so it occupies the same rank as the user layout file
  and needs no additional configuration source here. This is why the chain stops
  at two files: a scope outranking `--config` would have had to be specified now
  (source: user confirmation 2026-09-16, recorded in
  [`catalogue-level-telemetry-endpoint-default`](../../product/intents/catalogue-level-telemetry-endpoint-default.md))
