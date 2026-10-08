# Plan: Code-intelligence pack on Wicked Estate 0.21

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packs/AGENTS.md` and `packs/AGENTS.local.md` (version bump, eval, self-host, marketplace, changelog); `tests/AGENTS.md` (a pack test may not read above its pack); the shipped precedent `docs/specs/code-intelligence-estate-0-18/` and its suites under `packs/code-intelligence/tests/`; the `code-intelligence` pytest lines in the `Makefile` test chain, where only the live-binary module skips without `wicked-estate`. Non-structural: no new module or boundary.

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

Tests first, then prose, then release — the 0.18 shape. T1 moves every suite to
the 0.21.0 surface; the new static checks go red against today's prose. T2
rewrites the preflight, manifest, skill, references, agents, README and guides
until every pack test is green. T3 adds the evals, bumps the version, rebuilds
the marketplace, writes the changelog entry, and re-projects. The riskiest part
is prose accuracy, which the live suite and the retired-claim scanner bound.

## Constraints

- RFC-0104's three-tier runtime-dependency policy stays: exact pin, detect first, install only on consent. Only the floor and pin values move. The RFC stays unedited, as in the 0.18 change.
- `packs/AGENTS.md`: patch bump for changed content (no new primitive), eval update, self-host after `.apm/` edits, no internal-governance citations under `packs/`.
- `packs/AGENTS.local.md`: `FORCE=1 make build-self` for the marketplace; free-standing changelog entry with a Highlights decision.
- `tests/AGENTS.md`: a pack test reads only inside its pack, so guide checks run as commands.
- Root `AGENTS.md`: the local gate is `make lint-ruff lint-mypy` plus the touched suites.

## Construction tests

**Integration tests:** the live suite with the 0.21.0 binary first on `PATH`, built by `cargo install wicked-estate --version 0.21.0 --locked --root /tmp/we021`.
**Manual verification:** `estate_preflight.py --check` in a scratch repository holding an index, plus `lineage`, `traverse`, and `rank --seeds` text output, recorded in `notes/verification-ledger.md`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing promise — pack README, guides | T2 | AC-0006 and AC-0026 commands; AC-0024 pack test | Commands and tests green on the PR head |
| Current product truth — skill, references, agents | T1, T2 | Vocabulary, contract and guidance suites green against 0.21.0 | Same suites green |
| Release history — manifests, marketplace, changelog | T3 | Manifest tests; `marketplace.json`; changelog heading | 0.1.5 everywhere; Highlights decision recorded |
| Decision rationale — RFC divergence | none | Spec Durable Outputs row | — |

## Design (LLD)

### Interfaces & contracts

Upstream facts the prose relies on, observed on the three-file fixture with 0.21.0 unless marked source-read.

- `blast-radius --json` adds `confidence {min, avg, edge_count}` over the edges that admitted the rows; rows still carry no per-row depth or confidence. Text adds an `evidence:` line. The structural `contains` exclusion is source-read (`main.rs`), so prose labels it and says MCP `BlastRadius` can report higher figures. (AC-0010, AC-0011)
- Strict flags: a bespoke command exits 1 on a flag it does not read. `nodes --symbol` therefore fails rather than returning the whole graph. `source` text mode honours `--symbols`; that it also honours `--cluster`, `--file`, `--signatures-only` is source-read. `--max-total-chars` without `--json` exits non-zero. (AC-0012, AC-0016)
- `rank`/`hotspots [--limit N] [--seeds s1,s2] [--json]`: JSON `{hotspots[], total, truncated}`; each hotspot `{symbol, name, kind, file, line, line_1based, score}`. `--seeds` personalises PageRank over the **whole graph** — seeded output includes symbols the seeds cannot reach — so it biases rather than filters. An ambiguous seed name exits 1 listing its ids. Default 20 rows, ceiling 200, and a 25,000-character budget are source-read (`wicked-estate-retrieve` `RANK_LIMIT_CEILING`, `R4_CHAR_BUDGET`). Ranking a dependent set is therefore a composition: `rank --seeds <dependent ids> --limit 200 --json`, keep only rows whose `symbol` is in the set, and report any member absent from the output as unranked (cut by the limit or budget, `truncated` says which). `--seeds` splits its value on commas ("no commas" in upstream help; source-read, `tool_bridge.rs`), so a dependent whose id contains a comma cannot be seeded; the recipe leaves it out of the seed list and reports it as unranked for that reason. (AC-0013, AC-0014, AC-0015)
- `lineage --symbol <SYMBOL_ID> [--depth N] [--relation flows_to] [--json]`: exact id only. A name returns an empty result with exit 0 — the pack teaches `resolve` first. `--json` wraps the tool result as `{content, diagnostics}`; `content` holds `dependencies[] {symbol, name, kind, file, line, depth}`, `total`, `truncated`, `confidence`, and the three cut fields. Default depth 8; `line` is 0-based; above 24 or an unsupported `--relation` exits 1. With `--relation flows_to`, `content.flows[]` rows carry `producer`, `consumer`, `confidence`, `provenance`, `resolved_by`, and when present `flow_semantics` (`value_preserving` / `may_influence`), `flow_evidence` (`syntax` / `call_derived` / `convention`), `constructs`, `flow_rules`, `flow_support`, `flow_support_truncated`, `flow_confidence_min`, `file`, `line` — source-read from `wicked-estate-retrieve` 0.21.0 `flow_hop_row`; the prose names `flow_semantics` and `flow_evidence` and says the list is not exhaustive. (AC-0017, AC-0018, AC-0019)
- `traverse <symbol> [--depth N] [--direction dependencies|dependents|both] [--edge-kinds a,b] [--max-nodes N] [--json]`: `<symbol>` is a name or id; JSON is the MCP `TraverseGraph` content `{nodes, edges, depths, truncated, searched_depth, depth_horizon_reached, node_cap_reached}`; each edge carries `kind`, `confidence`, `provenance`, `resolved_by`. Over-ceiling `--depth` or `--max-nodes` is clamped with a `CLAMPED:` line on stderr. A value outside a closed set exits 1. (AC-0020, AC-0021)
- `rules-inventory [--json]` and `rules-recall [--severity|--rule-type|--language|--layer|--framework|--scope|--projects|--limit] [--json]`: the MCP tools' content; an empty graph returns an empty document, exit 0; strict flags. (AC-0022)
- Bridged commands (`traverse`, `rank`, `rules-inventory`, `rules-recall`) write `STALENESS:` and other diagnostics to stderr even under `--json` (pinned on `rank`; the rest source-read from `tool_bridge.rs`), and refuse a missing `--db` without creating it (pinned on `traverse`). `lineage --json` puts diagnostics in its `diagnostics` array: always a placeholder entry, plus a real `STALENESS: commits_behind=N` entry when the graph is behind HEAD (source-read, `main.rs` lineage arm). `blast-radius` and `path` still suppress `STALENESS:` under `--json`. The pack does not teach `blast-radius` missing-`--db` behaviour. (AC-0021, AC-0023)
- `graph-view` edges carry `kind`, `confidence`, `provenance`, `resolved_by`; prose adds that upstream does not commit to `graph-view`'s JSON shape. (AC-0036)
- Dispatch set: 35 top-level arms in `main.rs` plus 4 bridged commands; 40 names counting the `hotspots` alias (source-read). `supports owners|edge|retract` exists; `retract` writes. No producer writes edge support in 0.21.0, so the pack names `supports` only in the allowlist and the write list.
- `wicked-estate --version` still prints the usage banner whose first line carries the version; the preflight parser is unchanged.
- MCP surface: tool names and counts are unchanged since 0.18 (30 tools, 31 with `SemanticSearch`; `--readonly` leaves 20/21). Schema-derived; not re-run. The MCP-only set is the one the spec's Outcome names.

Traces to AC-0010 through AC-0023, AC-0027, AC-0028, AC-0029, AC-0036.

Owned by: T1, T2.

### Behavior & rules

The guidance module is renamed `tests/pack/test_estate_guidance.py` so its name stops naming a release, and every acceptance-criterion citation in the five pack test modules this change edits is replaced by a plain statement of what the test checks (AC-0037). `REQUIRED_PIN` becomes `0.21.0`. Its planted stale pins add `--version 0.18.0`.

The retired-claim scanner keeps every 0.18 pattern and adds a 0.21 group. Matching uses the existing normalisation (lowercase, strip `*`, `_`, `` ` ``, collapse whitespace). Each pattern has a planted stale sentence taken from today's pack or guides:

- MCP-only CLI capabilities: `\bno lineage subcommand\b`, `\blineage (?:and rules discovery )?(?:is|are) mcp-only\b`, `\brules discovery (?:is|are) mcp-only\b`, `\bmcp only — (?:lineage|rulesinventory|rules\.recall|traversegraph)\b`, `\bfour (?:capabilities|capability areas|mcp-only capabilities)\b`, `\b(?:lineage|rulesinventory|rules\.recall|traversegraph)[^.]{0,80}\bno cli verb\b`, `\bno cli counterpart with the same shape\b`, `\byou need mcp lineage\b`, `\bonly when the session needs lineage\b`
- rank without seeds: `\bglobal top-25\b`, `\bcapped at 25(?![,\dk])`, `\btakes no seed\b`, `\bwith no seed\b`, `\bno seed bias\b`
- source selectors: `\btext path ignores\b`, `\bevery selector is silently ignored\b`, `\bsilently ignored without --json\b`, `\bsilently ignores --symbols\b`, `\bselectors silently no-op\b`, `\bignored rather than rejected\b`, `\baccepted and then ignored\b`
- staleness: `\bsix subcommands\b`, `\bsix commands only\b`, `\bonly reliable place to see\b`, `\bthe only place you will see one\b`
- stale version: `\b0\.1[78]\b`, which matches `0.17`, `0.18`, and `0.18.0`

Planted current sentences that must not match: "`rank --seeds` biases a graph-wide ranking; keep only the rows in your set.", "Output is capped at 25,000 characters.", "The row list is capped at 25K characters.", "The memory and knowledge domains are MCP-only.", "Register it for the memory, knowledge, and proposal domains, which have no CLI verb.", "Measured on Wicked Estate 0.16.7 against a real repository.", and "`blast-radius` rows carry no per-row confidence."

A passing scanner proves only that these patterns are absent. T2 also reads each touched shipped file and guide whole once, and the ledger records it.

`main(paths, scanner)` is unchanged. The guide checks:

```bash
python3 -c "import importlib.util as u,sys; s=u.spec_from_file_location('ci_guidance','packs/code-intelligence/tests/pack/test_estate_guidance.py'); m=u.module_from_spec(s); s.loader.exec_module(m); sys.exit(m.main(['guides/code-intelligence'], scanner='pin'))"
python3 -c "import importlib.util as u,sys; s=u.spec_from_file_location('ci_guidance','packs/code-intelligence/tests/pack/test_estate_guidance.py'); m=u.module_from_spec(s); s.loader.exec_module(m); sys.exit(m.main(['guides/code-intelligence'], scanner='retired'))"
```

Traces to AC-0004, AC-0005, AC-0006, AC-0024, AC-0025, AC-0026, AC-0037.

Owned by: T1.

### Dependencies & integration

The only external dependency is the `wicked-estate` crate family; floor and pin live in `pack.toml` and `estate_preflight.py`, and every install command repeats the pin. Traces to AC-0001 through AC-0006.

Owned by: T2.

## Tasks

### T1: Suites describe the 0.21.0 surface

**Depends on:** none
**Touches:** `packs/code-intelligence/tests/**`

**Tests:**
- `test_estate_preflight.py`: the floor test stubs 0.20.0 and expects exit 4 with `required == "0.21"` (AC-0001); every other `read_version` stub uses 0.21.0 (AC-0002).
- `test_manifest.py`: both floors read `>=0.21` and equal `>=` plus `MINIMUM_VERSION` (AC-0003); manifest versions are 0.1.5 (AC-0031).
- `test_estate_surface_vocabulary.py`: `VERIFIED_AGAINST = "0.21"`; `CLI_VERBS` adds `lineage`, `traverse`, `rules-inventory`, `rules-recall`, `supports` (AC-0007). The existing capability-map version test carries AC-0009; the existing live dispatch test carries AC-0008.
- `test_estate_cli_contract.py`: blast-radius key set with `confidence` (AC-0010) and text `evidence:` (AC-0011) replace the old key-set test; `nodes --symbol` and `blast-radius --bogus` exit non-zero (AC-0012) replace the no-filter test; rank JSON shape, `--limit`, `--seeds` (AC-0013, AC-0014, AC-0015) replace the ignores-json test; source text honours `--symbols` (AC-0016) replaces the require-json assertion; new lineage (AC-0017, AC-0018, AC-0019), traverse (AC-0020, AC-0021), rules (AC-0022), missing-db (AC-0023) and graph-view edge (AC-0036) tests. Docstring and skip reason name 0.21.0.
- `tests/pack/test_estate_guidance.py` (renamed): pin and retired scanners per Design (AC-0004, AC-0005, AC-0024, AC-0025); teaching tests (AC-0027, AC-0028, AC-0029); eval cases (AC-0030) and the eval-6 correction (AC-0038); the 0.18 route-teaching, depth-teaching and route-eval tests stay. No module cites an acceptance-criterion ID (AC-0037).

**Done when:** with the 0.21.0 binary first on `PATH`, `python3 -m pytest packs/code-intelligence/tests -q` fails only tests on prose or manifests T2 or T3 own: the preflight floor test, the floor and version tests in `test_manifest.py`, `test_capability_map_records_the_verified_version`, `test_required_pin_equals_preflight_pinned_version`, and the shipped-surface pin, shipped-surface retired-claim, teaching, eval and eval-6 tests. Every live-suite test and both planted-sample tests pass.

### T2: Preflight, manifest, skill, references, agents, README and guides teach 0.21.0

**Depends on:** T1
**Touches:** `packs/code-intelligence/.apm/**` except `evals/evals.json`, `packs/code-intelligence/README.md`, `packs/code-intelligence/pack.toml`, `guides/code-intelligence/**`

**Tests:**
- Every T1 test except the eval (AC-0030), eval-6 (AC-0038) and version (AC-0031) tests turns green, including `test_required_pin_equals_preflight_pinned_version`.
- The guide commands for AC-0006 and AC-0026 exit 0.
- `python3 -m pytest tools/test_check_output_readability.py -q` passes.

**Approach:**
- `estate_preflight.py`: `MINIMUM_VERSION = (0, 21)`, `PINNED_VERSION = "0.21.0"`, banner docstring.
- `pack.toml`: floors, pins, recovery text; the MCP note names the MCP-only set from the spec's Outcome.
- `capability-map.md`: `VERIFIED_AGAINST` 0.21; CLI evidence row lists the new pinned verbs; dispatch count 40 names; forward-dependency table becomes CLI `lineage` rows with the resolve-first rule and `flows` fields; `traverse` row; rank row with `--seeds/--limit/--json`; rules rows become CLI; `source` bulk row drops the mandatory-`--json` claim; blast-radius `confidence`; freshness row for bridged stderr; `CLAMPED:`; `supports retract` in the write list; MCP registration only for the MCP-only set from the spec's Outcome.
- `gaps.md`: header version; §5 Traverse Direct; §10/§11 blast-radius confidence summary; §14 discovery; found-gaps list drops lineage-MCP-only, rules-MCP-only, rank, and source-selector items and renumbers; provenance text names 0.21.0 fixture runs.
- `investigation-patterns.md`: forward dependencies via `resolve` then `lineage`; order a blast radius by the seed-then-filter composition in Design, naming the 200-row and character limits and the comma limit on seed ids; rules tracing with `traverse --edge-kinds invoked_by` and `rules-inventory`; source selectors.
- `evidence.md`: staleness channels; `CLAMPED:`; blast-radius confidence summary versus MCP; `flows_to` semantics.
- `SKILL.md`, both agents, `example-prompts.md`, `composition-example.md`, `README.md`, the four guides: the same claims, rescoped.
- `evals/files/composition-preflight-exit0.txt` and `composition-preflight-exit2.txt`: the sample preflight output names 0.21.0, because the pin scanner reads `.apm/`.

**Done when:** the T2 Tests hold with the 0.21.0 binary first on `PATH`.

### T3: Evals, release, projection

**Depends on:** T2
**Touches:** `packs/code-intelligence/.apm/skills/code-intelligence/evals/evals.json`, `packs/code-intelligence/pack.toml`, `packs/code-intelligence/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md`, self-host projections

**Tests:**
- The eval (AC-0030), eval-6 (AC-0038) and version (AC-0031) tests turn green. Eval 6 keeps its prompt (its hash is pinned) and its `expected_output` and third assertion say blast-radius rows carry no per-row depth or confidence while `--json` carries a `confidence` summary.
- `FORCE=1 make build-self` regenerates `marketplace.json` with `code-intelligence` at 0.1.5 (AC-0032).
- `docs/product/changelog.md` carries `## [code-intelligence][0.1.5] — <YYYY-MM-DD>` (AC-0033) with a Highlights decision.
- AC-0034 self-host run on the committed head; `agentbundle catalogue verify --root .` (AC-0035).

**Done when:** the T3 Tests hold, the whole pack suite passes with the 0.21.0 binary first on `PATH`, and `make lint-ruff lint-mypy` passes.

## Rollout

One PR, reversible by revert. An adopter on 0.18–0.20 sees preflight exit 4 until they run the pinned install; a release-version bump re-extracts the index automatically. No data migration.

## Risks

- The live suite skips in CI without the binary, so run evidence comes from the local 0.21.0 build recorded in the ledger.
- `flows_to` fields cannot be observed on the Python fixture; prose labels them source-read.

## Changelog
- 2026-10-08: spec approved by eugenelim
- 2026-10-08: plan approved by eugenelim
