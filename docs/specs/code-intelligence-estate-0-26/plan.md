# Plan: Code-intelligence pack on Wicked Estate 0.26

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packs/AGENTS.md` and `packs/AGENTS.local.md` (version bump, eval, self-host, marketplace, changelog); `tests/AGENTS.md` (a pack test may not read above its pack); the shipped precedent `docs/specs/code-intelligence-estate-0-21/` and its suites under `packs/code-intelligence/tests/`; the `code-intelligence` pytest lines in the `Makefile` test chain, where only the live-binary module skips without `wicked-estate`. Non-structural: no new module or boundary.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan.

## Approach

Tests first, then prose, then release — the 0.21 shape. T1 moves every suite to
the 0.26.0 surface, so the static checks go red against today's prose. T2
rewrites the preflight, manifest, skill, references, agents, README and guides
until every pack test is green. T3 updates the evals, bumps the version,
rebuilds the marketplace, writes the changelog entry, and re-projects. The
riskiest part is prose accuracy, which the live suite and the retired-claim
scanner bound.

## Constraints

- RFC-0104's three-tier runtime-dependency policy stays: exact pin, detect first, install only on consent. Only the floor and pin values move, and the RFC stays unedited.
- `packs/AGENTS.md`: patch bump for changed content (no new primitive), eval update, self-host after `.apm/` edits, no internal-governance citations under `packs/`.
- `packs/AGENTS.local.md`: `FORCE=1 make build-self` for the marketplace; free-standing changelog entry with a Highlights decision.
- `tests/AGENTS.md`: a pack test reads only inside its pack, so guide checks run as commands.
- Root `AGENTS.md`: the local gate is `make lint-ruff lint-mypy` plus the touched suites.

## Construction tests

**Integration tests:** the live suite with the 0.26.0 binary first on `PATH`, built by `cargo install --root /tmp/we-026-bin wicked-estate --version 0.26.0 --locked`.
**Manual verification:** `estate_preflight.py --check` in a scratch repository holding an index, plus `lineage <name>` and `blast-radius --json` output, recorded in `notes/verification-ledger.md`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing promise — pack README, guides | T2 | AC-0006 and AC-0036 commands; AC-0034 pack test | Commands and tests green on the PR head |
| Current product truth — skill, references, agents | T1, T2 | Vocabulary, contract and guidance suites green against 0.26.0 | Same suites green |
| Release history — manifests, marketplace, changelog | T3 | Manifest tests; `marketplace.json`; changelog heading | 0.1.8 everywhere; Highlights decision recorded |
| Decision rationale — RFC divergence | none | Spec Durable Outputs row | — |

## Design (LLD)

### Interfaces & contracts

Upstream facts the prose relies on, observed on the three-file fixture with 0.26.0 unless marked source-read.

- `lineage <symbol> [--depth N] [--relation flows_to] [--json]`: `<symbol>` is a name or an exact symbol id; `--symbol` is an unknown flag (exit 1). An unknown or ambiguous name exits non-zero with nothing on stdout, so the pack still teaches `resolve` first when a name may be ambiguous. `--json` prints the tool content directly: `{dependencies[] {symbol, name, kind, file, line, depth}, total, truncated, confidence, relation, searched_depth, depth_horizon_reached, node_cap_reached}`. `relation` echoes `dependency` or `flows_to`. Default depth 8; `line` is 0-based; `--depth` above 24 is clamped to 24 with `CLAMPED:` on stderr; any `--relation` other than `flows_to` exits 1. Under `--json`, `STALENESS:`, `CLAMPED:` and other diagnostics go to stderr; in text mode they print on stdout after the result (source-read, `tool_bridge.rs`). A value-slot seed (parameter or local) is found with `resolve <name> --include-values --json`, because plain `resolve` returns structural symbols only (source-read, upstream 0.22.0). With `--relation flows_to`, `flows[]` rows carry `producer`, `consumer`, `confidence`, `provenance`, `resolved_by`, and when present `flow_semantics` and `flow_evidence` (`syntax` / `call_derived` / `convention` / `compiler`) — source-read. Value flow covers `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`; callbacks, `await`/`.then`, destructuring, loops, local object properties and closure returns add hops, almost all `may_influence` (source-read, upstream CHANGELOG 0.23.0–0.26.0). (AC-0013 through AC-0022, AC-0033)
- `blast-radius --json` dependent rows are `{id, name, kind, file, line, depth}`; `depth` 1 is a direct dependent. Rows still carry no per-row confidence; the top-level `confidence` summary is unchanged. `--depth 1` stays valid when only direct dependents are wanted, and the truncation conditions in `evidence.md` § Direct and transitive dependents still apply to it. (AC-0011, AC-0012)
- Strict argv: a malformed value, a surplus or missing operand, a repeated non-repeating flag, or a flag ignored in combination exits 1 before any store opens, with usage on stderr and empty stdout. Read commands refuse a missing or zero-byte `--db` with `no graph at <db>` and do not create it. (AC-0029 through AC-0032)
- `--version`, `-V` and `version` print `wicked-estate <version>`, one line (`-V` and `version` source-read). The preflight's `_VERSION_RE` search already parses this; only its docstring changes. (AC-0023)
- `query <name> --json` returns `resolve --json`'s rows. `resolve` returns structural symbols only; `--include-values` adds value slots (source-read). `--help` lists every dispatched command (source-read, upstream `tests/cli_surface.rs`). (AC-0024)
- `path` `depth_bounded` is true only when something lay beyond the horizon, found route or not. (AC-0025)
- Annotations: `--json` rows add `source_type`, `extraction_method`, `last_verified`; `annotate` sets them with `--source-type`, `--extraction-method`, `--last-verified now|<secs>|YYYY-MM-DD`. `stale-annotations` takes exactly one cutoff: Unix seconds, `YYYY-MM-DD`, or `--older-than <N>{s,m,h,d,w}`. (AC-0026, AC-0027, AC-0028)
- Provenance: `Compiler` is a new resolution tier and provenance. `scip` writes support-plane `References` and never call edges; `evidence <envelope.json>` ingests compiler evidence such as Angular input and output bindings (source-read). Both are write verbs.
- Dispatch set: 42 names — 0.21.0's 40 plus `evidence` and `version`. 35 bespoke arms (`lineage` left them, `evidence` joined), 5 bridged commands (`lineage`, `traverse`, `rank`, `rules-inventory`, `rules-recall`), the `hotspots` alias, and `version` matched before dispatch (source-read, `main.rs` and `tool_bridge.rs` v0.26.0). Every bridged command writes `STALENESS:` to stderr under `--json` and to stdout after the result in text mode.
- MCP surface: tool names unchanged; `tools/call` rejects arguments outside the advertised schema; `Lineage` echoes `relation`; `rules.recall` gains `steering_type` (schema-derived, conformance schemas v0.26.0).

Traces to AC-0011 through AC-0033, AC-0037 through AC-0043.

Owned by: T1, T2.

### Behavior & rules

`REQUIRED_PIN` becomes `0.26.0`; the planted stale pins add `--version 0.21.0`. The retired-claim scanner keeps every earlier pattern and adds a 0.26 group, matched after the existing normalisation (lowercase, strip `*`, `_`, `` ` ``, collapse whitespace). Each pattern gets a planted stale sentence taken from today's pack or guides:

- lineage flag form: `\blineage --symbol\b`, `\btakes an exact symbolid only\b`, `\{content, diagnostics\}`, `\bin the diagnostics array\b`, `\bdepth above 24[^.]{0,60}\bexits 1\b`
- blast-radius depth: `\bomit per-dependent depth\b`, `\bcli does not offer per-row depth\b`, `\bper-dependent depth[^|]{0,160}\bmcp-only\b`, `\| per-dependent depth \| no \|`, `\bthe cli form (?:returns neither|does not)\b`, `\{id, name, kind, file, line\}`
- closed gaps: `\bno --version flag\b`, `\bquery has no --json\b`, `(?<!\S)--help is not a complete command inventory\b`, `\bhelp text is therefore not a complete inventory\b`, and the `query` capability-map cell `\bno --json\. use resolve --json\b`
- provenance: `\bscip-backed edge\b`
- value-lineage reach: `\btypescript only\b`
- annotation envelope: `\bno lastverified\b`, `\bcarries ts, not lastverified\b`, `\bexactly these fields\b`, `\ba date string is rejected\b`
- MCP-only depth: `\bmcp-only set\b[^|]{0,200}\bper-dependent depth\b`
- lineage name form: `\ba name returns empty\b`
- dispatch counts: `\b40 names\b`, `\b4 bridged commands\b`
- stale version: `\b0\.2[0-5](?:\.\d)?(?![\d,])`, checked during T1 against every decimal the shipped surface uses

Each stale sample is copied from the line it retires (for example `capability-map.md:35`, `gaps.md:184`, `SKILL.md:206`, `gaps.md:304`, `gaps.md:250`, `capability-map.md:48`, `capability-map.md:110`, `evidence.md:230`, `evidence.md:251`, `example-prompts.md:137`, `README.md:115`), so a pattern that misses its real sentence fails AC-0035. A pattern may be adjusted during T1 to match its real sentence; the stale sample stays the real sentence.

Planted current sentences that must not match include: "`lineage <symbol>` accepts a name or a symbol id.", "Angular conventions apply to TypeScript files; JavaScript has none.", "`blast-radius` rows carry no per-row confidence.", "Each dependent carries its own per-row `depth`.", "Confidence ranges 0.0–1.0.", and "Measured on Wicked Estate 0.16.7 against a real repository."

A passing scanner proves only that these patterns are absent. T2 also reads each touched shipped file and guide whole once, and the ledger records it.

The guide checks reuse the 0.21 commands:

```bash
python3 -c "import importlib.util as u,sys; s=u.spec_from_file_location('ci_guidance','packs/code-intelligence/tests/pack/test_estate_guidance.py'); m=u.module_from_spec(s); s.loader.exec_module(m); sys.exit(m.main(['guides/code-intelligence'], scanner='pin'))"
python3 -c "import importlib.util as u,sys; s=u.spec_from_file_location('ci_guidance','packs/code-intelligence/tests/pack/test_estate_guidance.py'); m=u.module_from_spec(s); s.loader.exec_module(m); sys.exit(m.main(['guides/code-intelligence'], scanner='retired'))"
```

Traces to AC-0004, AC-0005, AC-0006, AC-0034, AC-0035, AC-0036.

Owned by: T1.

### Dependencies & integration

The only external dependency is the `wicked-estate` crate family; floor and pin live in `pack.toml` and `estate_preflight.py`, and every install command repeats the pin. Traces to AC-0001 through AC-0006.

Owned by: T2.

## Tasks

### T1: Suites describe the 0.26.0 surface

**Depends on:** none
**Touches:** `packs/code-intelligence/tests/**`

**Tests:**
- `test_estate_preflight.py`: the floor test stubs 0.25.0 and expects exit 4 with `required == "0.26"` (AC-0001); every other `read_version` stub uses 0.26.0 (AC-0002).
- `test_manifest.py`: both floors read `>=0.26` (AC-0003); the version test becomes `test_pack_version_is_0_1_8` (AC-0045).
- `test_estate_surface_vocabulary.py`: `VERIFIED_AGAINST = "0.26"` (AC-0007); `CLI_VERBS` adds `evidence` and `version` (AC-0008). The existing live dispatch test carries AC-0009 and the capability-map version test AC-0010.
- `test_estate_cli_contract.py`: the no-depth row test becomes two per-row depth tests (AC-0011, AC-0012); the lineage shape, name and depth tests become one test per criterion in the positional form (AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022); the banner test becomes the version test, reading stdout only (AC-0023); new `query --json` test (AC-0024); the found-with-depth-bounded path test asserts `depth_bounded` false (AC-0025); the no-`last_verified` test becomes the envelope test (AC-0026); the Unix-seconds test becomes the accepted-cutoffs and conflicting-cutoff tests (AC-0027, AC-0028); new strict-argv tests (AC-0029, AC-0030, AC-0031) and missing-db test (AC-0032); new lineage staleness test (AC-0033). `test_undocumented_but_dispatched_verbs_are_accepted` keeps its assertions and its docstring stops citing "absent from --help". Module docstring and skip reason name 0.26.0.
- `test_composition_example.py`: `_ESTATE_CLI_VERBS` equals the vocabulary allowlist's `CLI_VERBS`.
- `tests/pack/test_estate_guidance.py`: pin and retired scanners per Design (AC-0004, AC-0005, AC-0034, AC-0035); the lineage teaching test asserts `wicked-estate lineage <` in the four files (AC-0037); new teaching tests (AC-0038, AC-0039, AC-0040, AC-0041, AC-0042, AC-0043); the lineage eval test asserts the positional form (AC-0044). No module cites an acceptance-criterion ID (AC-0050).

**Done when:** with the 0.26.0 binary first on `PATH`, `python3 -m pytest packs/code-intelligence/tests -q` fails only tests on prose or manifests T2 or T3 own: the preflight floor test, the floor and version tests in `test_manifest.py`, the capability-map version test, the required-pin test, and the shipped-surface pin, retired-claim, teaching and eval tests. Every live-suite test and both planted-sample tests pass.

### T2: Preflight, manifest, skill, references, agents, evals, README and guides teach 0.26.0

**Depends on:** T1
**Touches:** `packs/code-intelligence/.apm/**`, `packs/code-intelligence/README.md`, `packs/code-intelligence/JOURNEY.md`, `packs/code-intelligence/pack.toml` except its `version` field, `guides/code-intelligence/**`

**Tests:**
- Every T1 test except the version test (AC-0045) turns green.
- The guide commands for AC-0006 and AC-0036 exit 0.
- `python3 -m pytest tools/test_check_output_readability.py -q` passes.

**Approach:**
- Every claim in the shipped surface and guides about where a bridged command's `CLAMPED:` or `STALENESS:` line goes says stderr under `--json` and stdout after the result in text mode; the whole-file read checks each one.
- `estate_preflight.py`: `MINIMUM_VERSION = (0, 26)`, `PINNED_VERSION = "0.26.0"`, `read_version` docstring describes the one-line version output.
- `pack.toml`: floors, pins, recovery text.
- `capability-map.md`: `VERIFIED_AGAINST` 0.26; dispatch count per Design; lineage rows in positional form with the direct JSON shape and clamping; value-lineage row names TS, TSX, JavaScript, the new hop kinds and `resolve --include-values` for a value-slot seed; blast-radius row adds per-row `depth`; `query --json`; annotation and `stale-annotations` rows; `compiler` provenance and SCIP's reference-only role (`never call edges`); `evidence` in the write list; strict-argv note.
- `gaps.md`: header version; blast-radius CLI/MCP table and §Impact gain per-row depth on the CLI side; §Capability discovery stays capability 14 with a better verdict, so "Fourteen" stays everywhere; the found-gaps list drops the `--version`, `query --json` and `--help` items and renumbers.
- `evidence.md`: resolver tiers name `compiler` and SCIP's reference-only role; lineage and staleness channels, with `lineage` in the bridged list; annotation envelope fields and cutoff forms; direct-versus-transitive section reads per-row `depth` first; value-lineage seed via `resolve --include-values`.
- `SKILL.md`: positional lineage; exit 1 with nothing on stdout is a command error; bridged list includes `lineage`; Writes section adds `evidence`. `code-investigator.md` adds `evidence` to its not-yours-to-run list; `impact-analyst.md` reads per-row `depth`.
- `investigation-patterns.md`, `example-prompts.md`, `composition-example.md`, `README.md`, `JOURNEY.md`, the guides: the same claims, rescoped, including write lists and verb counts.
- `evals/evals.json`: lineage cases use the positional form; the MCP-depth case's `expected_output` and assertions say CLI rows carry per-row `depth`. Pinned eval prompts keep their text.
- `evals/files/composition-preflight-exit0.txt` and `composition-preflight-exit2.txt` name 0.26.0; `composition-blast-radius.json` and `composition-blast-radius-b.json` rows gain `depth`.

**Done when:** the T2 Tests hold with the 0.26.0 binary first on `PATH`.

### T3: Release and projection

**Depends on:** T2
**Touches:** `packs/code-intelligence/pack.toml` `version`, `packs/code-intelligence/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md`, self-host projections

**Tests:**
- The version test (AC-0045) turns green.
- `FORCE=1 make build-self` regenerates `marketplace.json` with `code-intelligence` at 0.1.8 (AC-0046).
- `docs/product/changelog.md` carries `## [code-intelligence][0.1.8] — <YYYY-MM-DD>` (AC-0047) with a Highlights decision.
- The self-host run on the committed head (AC-0048); `agentbundle catalogue verify --root .` (AC-0049).
- The internal-citation grep over the edited test modules (AC-0050).

**Done when:** the T3 Tests hold, the whole pack suite passes with the 0.26.0 binary first on `PATH`, and `make lint-ruff lint-mypy` passes.

## Rollout

One PR, reversible by revert. An adopter on 0.21–0.25 sees preflight exit 4 until they run the pinned install; the first `index` after upgrading re-extracts the whole graph automatically. No data migration.

After the PR opens, the maintainer's own `~/.cargo/bin/wicked-estate` is replaced with the 0.26.0 build and the main checkout is reindexed with `wicked-estate index .`; the ledger records both. This is a local step, not part of the diff.

## Risks

- The live suite skips in CI without the binary, so run evidence comes from the local 0.26.0 build recorded in the ledger.
- 0.24.0, 0.25.0 and 0.26.0 all shipped on 2026-10-10; a quick 0.26.x patch would need its own pin bump.
- `flows_to` fields cannot be observed on the Python fixture; prose labels them source-read.

## Changelog
- 2026-10-10: spec approved by eugenelim
- 2026-10-10: plan approved by eugenelim
