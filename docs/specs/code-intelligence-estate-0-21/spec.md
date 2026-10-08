# Spec: Code-intelligence pack on Wicked Estate 0.21

- **Status:** Implementing
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0104
- **Brief:** none
- **Discovery:** none
- **Contract:** none — the pack drives an upstream CLI; it publishes no interface of its own beyond its manifest and guidance
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

An agent using the code-intelligence pack can answer forward-dependency and
rules-engine questions from the `wicked-estate` CLI alone. It can also order a
dependent set by importance from the CLI, by seeding `rank` with the set and
keeping only the set's members. **What stays MCP-only** — stated here once and
referenced elsewhere — is the memory, knowledge, and proposal domains, plus the
richer MCP response shapes (per-dependent `depth` and `summary.top_by_pagerank`
on `BlastRadius`, `Communities` summaries, `ContextBundle`). Every surface the
pack ships names Wicked Estate 0.21.0 as both the floor and the pin. The stale
0.18-era claims the retired-claim scanner lists are gone from the shipped
surface and guides.

## What Changes

- Version floor and pin are 0.21 / 0.21.0 for both crates — `pack.toml`, `scripts/estate_preflight.py`, `SKILL.md`, both agents, `README.md`, the guides under `guides/code-intelligence/`.
- `wicked-estate lineage`, `traverse`, `rules-inventory`, and `rules-recall` become CLI rows; the MCP opt-in shrinks to the MCP-only set named in the Outcome — `references/capability-map.md`, `references/gaps.md`, `SKILL.md`, `README.md`, `pack.toml` note, guides.
- `rank --seeds/--limit/--json` is taught as a graph-wide personalised ranking. Ranking a dependent set is a composition: seed with the set, then keep only rows whose `symbol` is in it, and report members the row limit or character budget cut — `references/investigation-patterns.md`, `impact-analyst.md`, `example-prompts.md`, `gaps.md`, guides.
- `blast-radius --json` `confidence`, the text `evidence:` line, `graph-view` edge evidence, `CLAMPED:` diagnostics, and bridged-command `STALENESS:` on stderr are taught — `references/capability-map.md`, `references/evidence.md`, `SKILL.md`.
- Strict flag parsing: `source` text mode honours its selectors; a flag a command does not read exits 1 — `SKILL.md`, `references/`, guides.
- `flows_to` lineage hops carry `flow_semantics` and `flow_evidence` (source-read) — `references/capability-map.md`, `references/evidence.md`.
- The vocabulary allowlist, the live-binary contract suite, the guidance scanners, and the eval set follow the 0.21.0 surface — `packs/code-intelligence/tests/`, `evals/evals.json`.
- Pack release 0.1.5 — `pack.toml`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Adopters read what the pack can answer and what it needs installed | `packs/code-intelligence/README.md`, `guides/code-intelligence/` | Pack maintainer | Guides name 0.21.0 and describe the new CLI rows | AC-0006, AC-0026 green; each touched guide read whole once |
| Current product truth | The skill's references are the agent-facing statement of the upstream surface | `packs/code-intelligence/.apm/` | Pack maintainer | Vocabulary, contract and guidance suites green against 0.21.0 | AC-0007 through AC-0030 green |
| Release history | A pack bump is the adopter-visible change record | `pack.toml`, `plugin.json`, `marketplace.json`, `docs/product/changelog.md` | Pack maintainer | 0.1.5 on all three manifests; changelog entry with its Highlights decision | AC-0031 through AC-0033 green |
| Decision rationale | RFC-0104 records the original floor and pin; this change moves both, as the 0.18 change did, and the RFC stays unedited | `pack.toml` is the live authority for floor and pin; this spec records the divergence | Pack maintainer | This row | none beyond this spec |

## Agent Rules

### Always do

- Follow `packs/AGENTS.md` and `packs/AGENTS.local.md` for the version bump, eval update, self-host, marketplace rebuild, and changelog entry.
- State each new claim's provenance in the pack's three-way scheme: executed (CLI, run against 0.21.0), schema-derived (MCP rows), or source-read (read from the 0.21.0 crate sources).
- Teach a CLI behaviour only when a criterion below pins it, or label it source-read.

### Ask first

- Raising the pin past 0.21.0, or documenting behaviour from upstream's unreleased changelog section.
- Building or registering `wicked-estate-mcp` to execute MCP rows.
- Editing RFC-0104 or any other governance record.

### Never do

- Add a Python or Rust dependency, a new script, or a new skill or agent to the pack.
- Teach `supports` as an investigation verb; no producer writes edge support in 0.21.0.
- Replace any `wicked-estate` on the user's `PATH`; build test binaries into a scratch root.

## Testing Strategy

Every check below is either a pack test under `packs/code-intelligence/tests/` or a named command. "Shipped surface" means `packs/code-intelligence/.apm/`, `packs/code-intelligence/README.md`, and `packs/code-intelligence/pack.toml`. "Live suite" means `tests/skills/code-intelligence/test_estate_cli_contract.py` run with a 0.21.0 binary first on `PATH`; it skips without a binary, so the run evidence records the binary.

- **Preflight (AC-0001, AC-0002):** TDD — version comparison behind the `read_version` seam the existing suite monkeypatches.
- **Floor and pin (AC-0003, AC-0004, AC-0005):** goal-based static pack tests.
- **Guide pins (AC-0006):** goal-based command, because a pack test may not read outside its pack.
- **Vocabulary (AC-0007, AC-0008, AC-0009):** static pack tests; AC-0008 is the live dispatch check.
- **CLI shapes (AC-0010 through AC-0023, AC-0036):** integration — the live suite on the three-file fixture.
- **Citations and evals (AC-0037, AC-0038):** goal-based — the named grep and a static pack test.
- **Retired claims (AC-0024, AC-0025, AC-0026):** goal-based — the retired-claim scanner as a pack test and as a command over the guides.
- **Teaching (AC-0027, AC-0028, AC-0029, AC-0030):** goal-based static pack tests.
- **Release (AC-0031, AC-0032, AC-0033):** goal-based — manifest tests and a file read.
- **Projection (AC-0034, AC-0035):** goal-based commands.
- **End to end:** manual QA — `estate_preflight.py --check`, `lineage`, `traverse`, and `rank --seeds` on the fixture with the built binary, recorded in the verification ledger.

## Acceptance Criteria

- [ ] **AC-0001.** `estate_preflight.py --check` exits 4 and reports `required` as `0.21` when the binary reports version 0.20.0.
- [ ] **AC-0002.** `estate_preflight.py --check` exits 0 when the binary reports version 0.21.0 and an index exists.
- [ ] **AC-0003.** Both `[[pack.runtime-dependencies]]` entries in `pack.toml` declare `version = ">=0.21"`, equal to the preflight's `MINIMUM_VERSION`.
- [ ] **AC-0004.** In the shipped surface, every `cargo install wicked-estate` or `cargo install wicked-estate-mcp` occurrence is followed by `--version 0.21.0 --locked`, and `0.21.0` equals the preflight's `PINNED_VERSION`.
- [ ] **AC-0005.** The pin scanner accepts the planted `cargo install wicked-estate --version 0.21.0 --locked` and rejects the planted `cargo install wicked-estate --version 0.18.0 --locked`.
- [ ] **AC-0006.** `main(["guides/code-intelligence"], scanner="pin")` in the guidance test module exits 0.
- [ ] **AC-0007.** The vocabulary allowlist records `VERIFIED_AGAINST = "0.21"`, and its CLI verbs include `lineage`, `traverse`, `rules-inventory`, `rules-recall`, and `supports`.
- [ ] **AC-0008.** A 0.21.0 binary dispatches every CLI verb in the vocabulary allowlist.
- [ ] **AC-0009.** `references/capability-map.md` contains the allowlist's `VERIFIED_AGAINST` value.
- [ ] **AC-0010.** On the fixture, `blast-radius <name> --json` returns exactly the keys `target`, `dependents`, `unresolved`, `truncated_dependents`, `searched_depth`, `depth_horizon_reached`, `node_cap_reached`, `confidence`, and `confidence` holds `min`, `avg`, `edge_count`.
- [ ] **AC-0011.** On the fixture, `blast-radius helper` (text) prints a line starting `evidence:`.
- [ ] **AC-0012.** On the fixture, `nodes --symbol <id> --json` and `blast-radius helper --bogus 1` each exit non-zero.
- [ ] **AC-0013.** On the fixture, `rank --json` stdout parses as one JSON document with keys `hotspots`, `total`, `truncated`, and each hotspot carries `symbol`, `name`, `kind`, `file`, `line_1based`, `score`.
- [ ] **AC-0014.** On the fixture, `rank --limit 2 --json` returns two hotspots.
- [ ] **AC-0015.** On the fixture, `rank --seeds <id-of-entry> --json` exits 0 and its hotspots include the `other.py` `handle`, which `entry` cannot reach; `rank --seeds handle` exits non-zero because `handle` names two symbols.
- [ ] **AC-0016.** On the fixture, `source --symbols <one handle id>` in text mode exits 0 and prints exactly one body, and `source helper --max-total-chars 10` without `--json` exits non-zero.
- [ ] **AC-0017.** On the fixture, `lineage --symbol <entry id> --json` stdout parses to keys `content` and `diagnostics`; `content.searched_depth` is 8; `content.dependencies` lists `handle` at depth 1 and `helper` at depth 2; and the `helper` row's `line` is one less than the `line` `resolve helper --json` reports.
- [ ] **AC-0018.** On the fixture, `lineage --symbol entry --json` (a name, not an id) exits 0 with an empty `content.dependencies`.
- [ ] **AC-0019.** On the fixture, `lineage --symbol <entry id> --depth 25` and `lineage --symbol <entry id> --relation flow_to` each exit non-zero.
- [ ] **AC-0020.** On the fixture, `traverse helper --direction dependents --json` stdout parses to keys `nodes`, `edges`, `depths`, `truncated`, `searched_depth`, `depth_horizon_reached`, `node_cap_reached`, and each edge carries `kind`, `confidence`, `provenance`, `resolved_by`.
- [ ] **AC-0021.** On the fixture, `traverse helper --direction sideways` exits non-zero; `traverse helper --depth 99 --json` and `traverse helper --max-nodes 999999 --json` each write a line starting `CLAMPED:` to stderr while stdout still parses as JSON; and `rank --json` writes a line starting `STALENESS:` to stderr while stdout parses as JSON.
- [ ] **AC-0022.** On the fixture, `rules-inventory --json` and `rules-recall --json` each exit 0 with stdout that parses as JSON, and `rules-recall --bogus x` exits non-zero.
- [ ] **AC-0023.** `traverse helper --db <missing path>` exits non-zero and does not create the file.
- [ ] **AC-0024.** The retired-claim scanner finds no match in the shipped surface.
- [ ] **AC-0025.** The retired-claim scanner matches every sentence in its planted stale sample, every pattern has a stale sample, and no sentence in its planted current sample matches.
- [ ] **AC-0026.** `main(["guides/code-intelligence"], scanner="retired")` in the guidance test module exits 0.
- [ ] **AC-0027.** `SKILL.md`, `references/capability-map.md`, and `references/investigation-patterns.md` each contain `wicked-estate lineage`.
- [ ] **AC-0028.** `references/capability-map.md` contains `wicked-estate traverse`, `wicked-estate rules-inventory`, and `wicked-estate rules-recall`.
- [ ] **AC-0029.** `references/investigation-patterns.md` and `agents/impact-analyst.md` each contain `rank --seeds`.
- [ ] **AC-0030.** `evals/evals.json` contains a case whose assertions contain both `wicked-estate lineage` and `resolve`, and a case whose assertions contain `rank --seeds`.
- [ ] **AC-0031.** `pack.toml` and `.claude-plugin/plugin.json` both carry version `0.1.5`.
- [ ] **AC-0032.** The `code-intelligence` entry in `.claude-plugin/marketplace.json` carries version `0.1.5`.
- [ ] **AC-0033.** `docs/product/changelog.md` contains a line matching `^## \[code-intelligence\]\[0\.1\.5\] — \d{4}-\d{2}-\d{2}$`.
- [ ] **AC-0034.** On the PR head, one `agentbundle catalogue self-host --root . --write` run leaves `git status --porcelain` output empty.
- [ ] **AC-0035.** `agentbundle catalogue verify --root .` exits 0.
- [ ] **AC-0036.** On the fixture, `graph-view --limit 5` stdout parses as JSON and every edge carries `kind`, `confidence`, `provenance`, `resolved_by`.
- [ ] **AC-0037.** The `packs/AGENTS.local.md` internal-citation grep, run over the five pack test modules this change edits, finds no match.
- [ ] **AC-0038.** No `expected_output` or assertion in `evals/evals.json` says the CLI blast radius lacks confidence.

## Follow-ons

none

## Assumptions

- Technical: the allowlist equals upstream 0.21.0's dispatch set by source-read — 35 top-level arms in `main.rs` plus 4 `tool_bridge::COMMANDS` rows, 40 names with the `hotspots` alias. AC-0008 checks the allowlist is dispatched; no check fails on a verb upstream dispatches but the allowlist omits.
- Technical: every MCP row rests on upstream schemas; `wicked-estate-mcp` is not run, so those rows stay labelled schema-derived.
- Technical: `flows_to` per-hop fields are source-read from the 0.21.0 `wicked-estate-retrieve` crate; the Python fixture produces no value flow, so no live check reaches them.
