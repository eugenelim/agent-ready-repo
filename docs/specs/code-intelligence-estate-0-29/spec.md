# Spec: Code-intelligence pack on Wicked Estate 0.29

- **Status:** Shipped
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

An agent using the code-intelligence pack retrieves the whole of a large
blast radius or lineage answer from the `wicked-estate` CLI, instead of
reporting a 25,000-character first page as a floor. It follows `next_cursor`
with `--cursor` until the cursor is `null`, and treats a refused cursor as
"start again", never as the end of the answer. It knows `lineage` now walks to
depth 24 by default. Every shipped surface names Wicked Estate 0.29.2 as the
pin and 0.29 as the floor, and no shipped surface or guide repeats a 0.26-era
claim that 0.29.2 falsifies.

## What Changes

- Floor and pin are 0.29 / 0.29.2 for both crates — `pack.toml`, `scripts/estate_preflight.py`, `SKILL.md`, both agents, `README.md`, `guides/code-intelligence/`.
- Paging (upstream 0.28.0): `blast-radius` and `lineage` take `--cursor`; their `--json` replies carry `next_cursor` and `page`. `truncated_dependents` now counts rows on later pages, which are retrievable, not lost. Rows are ordered by depth, then symbol id. A cursor is refused (exit 1, nothing on stdout) when the answer it pages has changed — another query or `--depth`, another build, or different rows after a re-index — and a malformed cursor is refused with its own message. An accepted cursor proves nothing about freshness; `stats --json` still does. The MCP `BlastRadius` and `Lineage` tools take `cursor` the same way (schema-derived).
- `lineage` defaults to depth 24 (was 8). A lineage reply's `truncated` is true while more pages remain, as well as on a depth or node cut.
- `local object properties` leaves the value-lineage hop list (upstream 0.27.0 removed them).
- A `wicked-estate-mcp --readonly` server pointed at a store that does not exist creates no file and serves that store as an empty in-memory store, noting it on stderr (source-read, upstream 0.29.0). This applies to the graph (`--db`) and to the memory, knowledge and cross-store databases (`WICKED_MEMORY_DB`, `WICKED_KNOWLEDGE_DB`, `WICKED_XEDGE_DB`, or `WICKED_HOME`). The pack tells an agent to check those paths when every answer from a domain is empty.
- The vocabulary allowlist, the live-binary contract suite, the guidance scanners and the eval set follow the 0.29.2 surface.
- Pack release 0.1.9.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Adopters read what the pack can answer and what it needs installed | `packs/code-intelligence/README.md`, `guides/code-intelligence/` | Pack maintainer | Guides name 0.29.2 and paging | AC-0006, AC-0033, AC-0034 green; each touched guide read whole once |
| Current product truth | The skill's references are the agent-facing statement of the upstream surface | `packs/code-intelligence/.apm/` | Pack maintainer | Vocabulary, contract and guidance suites green against 0.29.2 | AC-0007 through AC-0032 green |
| Release history | A pack bump is the adopter-visible change record | `pack.toml`, `plugin.json`, `marketplace.json`, `docs/product/changelog.md` | Pack maintainer | 0.1.9 on all three manifests; changelog entry | AC-0035 through AC-0037 green |
| Decision rationale | RFC-0104 records the original floor and pin; this change moves both, and the RFC stays unedited | `pack.toml` is the live authority for floor and pin; this spec records the divergence | Pack maintainer | This row | none beyond this spec |

## Agent Rules

### Always do

- Follow `packs/AGENTS.md` and `packs/AGENTS.local.md` for the version bump, eval update, self-host, marketplace rebuild, and changelog entry.
- State each new claim's provenance in the pack's three-way scheme: executed (CLI, run against 0.29.2), schema-derived (MCP rows), or source-read (read from the 0.29.2 crate sources).
- Teach a CLI behaviour only when a criterion below pins it, or label it source-read.

### Ask first

- Raising the pin past 0.29.2, or documenting behaviour from upstream's unreleased changelog section.
- Building or registering `wicked-estate-mcp` to execute MCP rows.
- Editing RFC-0104 or any other governance record.
- Building a workflow on the memory, knowledge, or proposal domains.

### Never do

- Add a Python or Rust dependency, a new script, or a new skill or agent to the pack.
- Teach `evidence`, `scip`, or `annotate` as investigation verbs; they write to the graph.
- Change the preflight's exit codes, its `WICKED_ESTATE_DB` confinement, or its install consent gate.

## Testing Strategy

Every check below is either a pack test under `packs/code-intelligence/tests/` or a named command. "Shipped surface" means `packs/code-intelligence/.apm/`, `packs/code-intelligence/README.md`, and `packs/code-intelligence/pack.toml`. "Live suite" means `tests/skills/code-intelligence/test_estate_cli_contract.py` run with a 0.29.2 binary first on `PATH`; it skips without a binary, so the run evidence records the binary. "Wide fixture" means a second generated micro-repository in the live suite whose `helper` has 300 callers and whose `fan_out` calls all 300, so one reply cannot hold either answer.

- **Preflight (AC-0001, AC-0002):** TDD — version comparison behind the `read_version` seam the existing suite monkeypatches.
- **Floor and pin (AC-0003, AC-0004, AC-0005):** goal-based static pack tests.
- **Guide pins (AC-0006):** goal-based command, because a pack test may not read outside its pack.
- **Vocabulary (AC-0007, AC-0008, AC-0009):** static pack tests; AC-0008 is the live dispatch check.
- **CLI shapes and paging (AC-0010 through AC-0021):** integration — the live suite on the three-file fixture and the wide fixture.
- **Teaching and evals (AC-0022 through AC-0030):** goal-based static pack tests.
- **Retired claims (AC-0031, AC-0032, AC-0033):** goal-based — the retired-claim scanner as a pack test and as a command over the guides.
- **Guide paging (AC-0034):** goal-based command, because a pack test may not read outside its pack.
- **Release (AC-0035, AC-0036, AC-0037):** goal-based — manifest tests and a file read.
- **Projection (AC-0038, AC-0039):** goal-based commands.
- **Citations (AC-0040):** goal-based — the named grep.
- **End to end:** manual QA — `estate_preflight.py --check`, then `blast-radius --json` and `lineage --json` paged to a `null` cursor on a scratch repository with the built binary, recorded in the verification ledger.

## Acceptance Criteria

- [x] **AC-0001.** `estate_preflight.py --check` exits 4 and reports `required` as `0.29` when the binary reports version 0.28.0.
- [x] **AC-0002.** `estate_preflight.py --check` exits 0 when the binary reports version 0.29.2 and an index exists.
- [x] **AC-0003.** Both `[[pack.runtime-dependencies]]` entries in `pack.toml` declare `version = ">=0.29"`, equal to the preflight's `MINIMUM_VERSION`.
- [x] **AC-0004.** In the shipped surface, every `cargo install wicked-estate` or `cargo install wicked-estate-mcp` occurrence is followed by `--version 0.29.2 --locked`, and `0.29.2` equals the preflight's `PINNED_VERSION`.
- [x] **AC-0005.** The pin scanner accepts the planted `cargo install wicked-estate --version 0.29.2 --locked` and rejects the planted `cargo install wicked-estate --version 0.26.0 --locked`.
- [x] **AC-0006.** `main(["guides/code-intelligence"], scanner="pin")` in the guidance test module exits 0.
- [x] **AC-0007.** The vocabulary allowlist records `VERIFIED_AGAINST = "0.29"`.
- [x] **AC-0008.** A 0.29.2 binary dispatches every CLI verb in the vocabulary allowlist.
- [x] **AC-0009.** `references/capability-map.md` contains the allowlist's `VERIFIED_AGAINST` value.
- [x] **AC-0010.** `wicked-estate --version` exits 0 and its stdout is exactly `wicked-estate 0.29.2` followed by one newline.
- [x] **AC-0011.** On the fixture, `blast-radius helper --json` returns exactly the keys `target`, `dependents`, `unresolved`, `truncated_dependents`, `searched_depth`, `depth_horizon_reached`, `node_cap_reached`, `confidence`, `next_cursor`, `page`; `next_cursor` is `null`; and `page` equals `{from: 0, count: n, total: n}` where `n` is the number of dependents.
- [x] **AC-0012.** On the fixture, `lineage <entry id> --json` returns exactly the keys `dependencies`, `total`, `truncated`, `next_cursor`, `page`, `confidence`, `relation`, `searched_depth`, `depth_horizon_reached`, `node_cap_reached`, with `next_cursor` `null`.
- [x] **AC-0013.** On the fixture, `lineage <entry id> --json` with no `--depth` reports `searched_depth` 24.
- [x] **AC-0014.** On the wide fixture, the first `blast-radius helper --json` reply has a non-null `next_cursor`, a `truncated_dependents` greater than 0, and `page.count` plus `truncated_dependents` equal to `page.total`.
- [x] **AC-0015.** On the wide fixture, following `next_cursor` with `blast-radius helper --cursor <c> --json` until it is `null` returns `page.total` rows with distinct `id`s, ordered by `depth` and then `id`, and the last reply reports `truncated_dependents` 0.
- [x] **AC-0016.** On the wide fixture, the first `lineage fan_out --json` reply has `truncated` true and a non-null `next_cursor`.
- [x] **AC-0017.** On the wide fixture, following `next_cursor` with `lineage fan_out --cursor <c> --json` until it is `null` returns `total` rows with distinct `symbol`s, and the last reply reports `truncated` false.
- [x] **AC-0018.** On the wide fixture, a first-page blast-radius cursor passed with `--depth 3` exits non-zero with empty stdout.
- [x] **AC-0019.** On the wide fixture, `blast-radius helper --cursor garbage --json` exits non-zero with empty stdout.
- [x] **AC-0020.** On a copy of the wide fixture re-indexed with one more `helper` caller, the first-page blast-radius cursor from the original graph exits non-zero with empty stdout.
- [x] **AC-0021.** On the wide fixture, `blast-radius helper` in text mode prints a line containing `--cursor `.
- [x] **AC-0022.** `SKILL.md`, `references/evidence.md`, `references/capability-map.md`, `references/investigation-patterns.md` and `agents/impact-analyst.md` each contain `--cursor` and `next_cursor`.
- [x] **AC-0023.** `SKILL.md` and `references/evidence.md` each contain `` `next_cursor` is `null` ``.
- [x] **AC-0024.** `SKILL.md`, `references/evidence.md` and `agents/impact-analyst.md` each contain `rows on later pages`.
- [x] **AC-0025.** `SKILL.md` and `references/evidence.md` each contain `start again from the first page`.
- [x] **AC-0026.** `references/evidence.md` contains `more pages remain`.
- [x] **AC-0027.** The `lineage` row of `references/capability-map.md` contains `Default depth 24`.
- [x] **AC-0028.** `references/capability-map.md` and `README.md` each contain `empty in-memory` and `WICKED_MEMORY_DB`.
- [x] **AC-0029.** `evals/evals.json` contains a case whose assertions contain both `next_cursor` and `--cursor`, and a case whose assertions contain `first page`.
- [x] **AC-0030.** Every `blast-radius` JSON file under `evals/files/` carries `next_cursor` and `page`.
- [x] **AC-0031.** The retired-claim scanner finds no match in the shipped surface.
- [x] **AC-0032.** The retired-claim scanner matches every sentence in its planted stale sample, every pattern has a stale sample, and no sentence in its planted current sample matches.
- [x] **AC-0033.** `main(["guides/code-intelligence"], scanner="retired")` in the guidance test module exits 0.
- [x] **AC-0034.** `grep -F -- '--cursor' guides/code-intelligence/reference/capability-surface.md` and `grep -F 'next_cursor' guides/code-intelligence/reference/capability-surface.md` each exit 0.
- [x] **AC-0035.** `pack.toml` and `.claude-plugin/plugin.json` both carry version `0.1.9`.
- [x] **AC-0036.** The `code-intelligence` entry in `.claude-plugin/marketplace.json` carries version `0.1.9`.
- [x] **AC-0037.** `docs/product/changelog.md` contains a line matching `^## \[code-intelligence\]\[0\.1\.9\] — \d{4}-\d{2}-\d{2}$`.
- [x] **AC-0038.** On the PR head, one `agentbundle catalogue self-host --root . --write` run leaves `git status --porcelain` output empty.
- [x] **AC-0039.** `agentbundle catalogue verify --root .` exits 0.
- [x] **AC-0040.** The `packs/AGENTS.local.md` internal-citation grep, run over the pack test modules this change edits, finds no match.

## Follow-ons

none

## Assumptions

- Technical: the CLI delta from 0.26.0 to 0.29.2 is paging, the `lineage` depth default, and the removed TypeScript local-object flows. The dispatch arms and bridged commands are identical (source-read diff of `main.rs` and `tool_bridge.rs`), and `--help` differs only in the version line, the two `--cursor` flags, and the `lineage --depth` default (executed and source-read).
- Technical: every MCP row rests on upstream source and schemas; `wicked-estate-mcp` is not run, so those rows stay labelled schema-derived or source-read. The MCP tool names and the ten write tools are unchanged; MCP `BlastRadius` still defaults to depth 8.
- Technical: the 0.29.x memory changes (Working memory expiry, consolidation in `memory.reflect`, `kind` and `created_at` on recall items, knowledge proposals) touch only the MCP memory, knowledge and proposal domains, on which the pack builds no workflow. The pack's tool inventory stays accurate without teaching them.
