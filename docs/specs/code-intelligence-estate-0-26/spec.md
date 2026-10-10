# Spec: Code-intelligence pack on Wicked Estate 0.26

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

Every `wicked-estate` command the code-intelligence pack teaches runs as
written against Wicked Estate 0.26.0, and every shape the pack describes is the
shape 0.26.0 returns. Every shipped surface names 0.26.0 as both the floor and
the pin, and no shipped surface or guide repeats a 0.21-era claim that 0.26.0
falsifies.

## What Changes

- Floor and pin are 0.26 / 0.26.0 for both crates — `pack.toml`, `scripts/estate_preflight.py`, `SKILL.md`, both agents, `README.md`, `guides/code-intelligence/`.
- `lineage` is taught in its positional form, `wicked-estate lineage <symbol>`, which accepts a name or a symbol id and prints the result object directly; under `--json` its diagnostics go to stderr, and in text mode they follow the result on stdout.
- `blast-radius --json` rows carry a per-row `depth`, so one call separates direct from transitive dependents; `impact-analyst` and the investigation patterns use it.
- Closed gaps leave `references/gaps.md`: `--version` prints one line and `query --json` exists; that `--help` lists every command is taught as source-read.
- The evidence reference and the capability map teach `compiler` provenance and that a SCIP import adds reference support, never call edges; value lineage covers TypeScript, TSX and JavaScript, and its new hops are mostly `may_influence`.
- The annotation envelope carries `source_type`, `extraction_method` and `last_verified`, and `stale-annotations` takes a Unix time, a date, or `--older-than`.
- Strict argument parsing: a malformed value, a surplus operand, a repeated flag, or a missing `--db` exits 1 with nothing on stdout, and the pack tells agents to read that as a command error, not an empty answer.
- The vocabulary allowlist, the live-binary contract suite, the guidance scanners and the eval set follow the 0.26.0 surface.
- Pack release 0.1.8.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Adopters read what the pack can answer and what it needs installed | `packs/code-intelligence/README.md`, `guides/code-intelligence/` | Pack maintainer | Guides name 0.26.0 | AC-0006, AC-0036 green; each touched guide read whole once |
| Current product truth | The skill's references are the agent-facing statement of the upstream surface | `packs/code-intelligence/.apm/` | Pack maintainer | Vocabulary, contract and guidance suites green against 0.26.0 | AC-0007 through AC-0044 green |
| Release history | A pack bump is the adopter-visible change record | `pack.toml`, `plugin.json`, `marketplace.json`, `docs/product/changelog.md` | Pack maintainer | 0.1.8 on all three manifests; changelog entry | AC-0045 through AC-0047 green |
| Decision rationale | RFC-0104 records the original floor and pin; this change moves both, and the RFC stays unedited | `pack.toml` is the live authority for floor and pin; this spec records the divergence | Pack maintainer | This row | none beyond this spec |

## Agent Rules

### Always do

- Follow `packs/AGENTS.md` and `packs/AGENTS.local.md` for the version bump, eval update, self-host, marketplace rebuild, and changelog entry.
- State each new claim's provenance in the pack's three-way scheme: executed (CLI, run against 0.26.0), schema-derived (MCP rows), or source-read (read from the 0.26.0 crate sources).
- Teach a CLI behaviour only when a criterion below pins it, or label it source-read.

### Ask first

- Raising the pin past 0.26.0, or documenting behaviour from upstream's unreleased changelog section.
- Building or registering `wicked-estate-mcp` to execute MCP rows.
- Editing RFC-0104 or any other governance record.

### Never do

- Add a Python or Rust dependency, a new script, or a new skill or agent to the pack.
- Teach `evidence`, `scip`, or `annotate` as investigation verbs; they write to the graph.
- Change the preflight's exit codes, its `WICKED_ESTATE_DB` confinement, or its install consent gate.

## Testing Strategy

Every check below is either a pack test under `packs/code-intelligence/tests/` or a named command. "Shipped surface" means `packs/code-intelligence/.apm/`, `packs/code-intelligence/README.md`, and `packs/code-intelligence/pack.toml`. "Live suite" means `tests/skills/code-intelligence/test_estate_cli_contract.py` run with a 0.26.0 binary first on `PATH`; it skips without a binary, so the run evidence records the binary.

- **Preflight (AC-0001, AC-0002):** TDD — version comparison behind the `read_version` seam the existing suite monkeypatches.
- **Floor and pin (AC-0003, AC-0004, AC-0005):** goal-based static pack tests.
- **Guide pins (AC-0006):** goal-based command, because a pack test may not read outside its pack.
- **Vocabulary (AC-0007, AC-0008, AC-0009, AC-0010):** static pack tests; AC-0009 is the live dispatch check.
- **CLI shapes (AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028, AC-0029, AC-0030, AC-0031, AC-0032, AC-0033):** integration — the live suite on the three-file fixture.
- **Retired claims (AC-0034, AC-0035, AC-0036):** goal-based — the retired-claim scanner as a pack test and as a command over the guides.
- **Teaching and evals (AC-0037, AC-0038, AC-0039, AC-0040, AC-0041, AC-0042, AC-0043, AC-0044):** goal-based static pack tests.
- **Release (AC-0045, AC-0046, AC-0047):** goal-based — manifest tests and a file read.
- **Projection (AC-0048, AC-0049):** goal-based commands.
- **Citations (AC-0050):** goal-based — the named grep.
- **End to end:** manual QA — `estate_preflight.py --check`, `lineage <name>` and `blast-radius --json` on the fixture with the built binary, recorded in the verification ledger.

## Acceptance Criteria

- [ ] **AC-0001.** `estate_preflight.py --check` exits 4 and reports `required` as `0.26` when the binary reports version 0.25.0.
- [ ] **AC-0002.** `estate_preflight.py --check` exits 0 when the binary reports version 0.26.0 and an index exists.
- [ ] **AC-0003.** Both `[[pack.runtime-dependencies]]` entries in `pack.toml` declare `version = ">=0.26"`, equal to the preflight's `MINIMUM_VERSION`.
- [ ] **AC-0004.** In the shipped surface, every `cargo install wicked-estate` or `cargo install wicked-estate-mcp` occurrence is followed by `--version 0.26.0 --locked`, and `0.26.0` equals the preflight's `PINNED_VERSION`.
- [ ] **AC-0005.** The pin scanner accepts the planted `cargo install wicked-estate --version 0.26.0 --locked` and rejects the planted `cargo install wicked-estate --version 0.21.0 --locked`.
- [ ] **AC-0006.** `main(["guides/code-intelligence"], scanner="pin")` in the guidance test module exits 0.
- [ ] **AC-0007.** The vocabulary allowlist records `VERIFIED_AGAINST = "0.26"`.
- [ ] **AC-0008.** The vocabulary allowlist's CLI verbs include `evidence` and `version`.
- [ ] **AC-0009.** A 0.26.0 binary dispatches every CLI verb in the vocabulary allowlist.
- [ ] **AC-0010.** `references/capability-map.md` contains the allowlist's `VERIFIED_AGAINST` value.
- [ ] **AC-0011.** On the fixture, every `blast-radius helper --json` dependent carries exactly the keys `id`, `name`, `kind`, `file`, `line`, `depth`.
- [ ] **AC-0012.** On the fixture, the `blast-radius helper --json` row for the `core.py` `handle` has `depth` 1.
- [ ] **AC-0013.** On the fixture, `lineage <entry id> --json` exits 0 and stdout parses to exactly the keys `dependencies`, `total`, `truncated`, `confidence`, `relation`, `searched_depth`, `depth_horizon_reached`, `node_cap_reached`.
- [ ] **AC-0014.** On the fixture, `lineage <entry id> --json` reports `relation` as `dependency`.
- [ ] **AC-0015.** On the fixture, `lineage <entry id> --json` reports `searched_depth` 8.
- [ ] **AC-0016.** On the fixture, `lineage <entry id> --json` lists `handle` at depth 1 and `helper` at depth 2.
- [ ] **AC-0017.** On the fixture, the `helper` row of `lineage <entry id> --json` has a `line` one less than the `line` `resolve helper --json` reports.
- [ ] **AC-0018.** On the fixture, `lineage entry --json` (a unique name) exits 0 and lists `helper` at depth 2.
- [ ] **AC-0019.** On the fixture, `lineage handle --json` (an ambiguous name) exits non-zero with empty stdout.
- [ ] **AC-0020.** On the fixture, `lineage --symbol <entry id> --json` exits non-zero with empty stdout.
- [ ] **AC-0021.** On the fixture, `lineage <entry id> --depth 25 --json` exits 0, writes a line starting `CLAMPED:` to stderr, and reports `searched_depth` 24.
- [ ] **AC-0022.** On the fixture, `lineage <entry id> --relation flow_to` exits non-zero.
- [ ] **AC-0023.** `wicked-estate --version` exits 0 and its stdout is exactly `wicked-estate 0.26.0` followed by one newline.
- [ ] **AC-0024.** On the fixture, `query helper --json` exits 0 and parses to a list whose rows carry `symbol_id`, `name`, `kind`, `file`, `line`.
- [ ] **AC-0025.** On the fixture, `path entry helper --max-depth 2 --json` returns `found` true and `depth_bounded` false.
- [ ] **AC-0026.** On the fixture, after `annotate`, each `annotations <name> --json` annotation carries `source_type`, `extraction_method` and `last_verified`.
- [ ] **AC-0027.** On the fixture, `stale-annotations 9999999999 --json`, `stale-annotations 2026-01-01 --json` and `stale-annotations --older-than 90d --json` each exit 0.
- [ ] **AC-0028.** On the fixture, `stale-annotations 90 --older-than 9d` exits non-zero.
- [ ] **AC-0029.** On the fixture, `stats foo` (a surplus operand) exits non-zero with empty stdout.
- [ ] **AC-0030.** On the fixture, `blast-radius helper --depth abc --json` (a malformed value) exits non-zero with empty stdout.
- [ ] **AC-0031.** On the fixture, `nodes --kind function --kind class` (a repeated flag) exits non-zero with empty stdout.
- [ ] **AC-0032.** `blast-radius helper --db <missing path>` exits non-zero with empty stdout and does not create the file.
- [ ] **AC-0033.** On the fixture, `lineage <entry id> --json` stdout parses as JSON while a line starting `STALENESS:` appears on stderr.
- [ ] **AC-0034.** The retired-claim scanner finds no match in the shipped surface.
- [ ] **AC-0035.** The retired-claim scanner matches every sentence in its planted stale sample, every pattern has a stale sample, and no sentence in its planted current sample matches.
- [ ] **AC-0036.** `main(["guides/code-intelligence"], scanner="retired")` in the guidance test module exits 0.
- [ ] **AC-0037.** `SKILL.md`, `references/capability-map.md`, `references/investigation-patterns.md` and `references/evidence.md` each contain `wicked-estate lineage <`.
- [ ] **AC-0038.** `agents/impact-analyst.md` and `references/investigation-patterns.md` each contain `` per-row `depth` ``.
- [ ] **AC-0039.** `references/evidence.md` and `references/capability-map.md` each contain `` `compiler` `` and `never call edges`.
- [ ] **AC-0040.** The value-lineage row of `references/capability-map.md` contains `TSX` and `JavaScript`.
- [ ] **AC-0041.** `SKILL.md` contains `nothing on stdout`.
- [ ] **AC-0042.** `references/evidence.md` contains `last_verified` and `--older-than`.
- [ ] **AC-0043.** `SKILL.md` and `agents/code-investigator.md` each contain `` `evidence` ``.
- [ ] **AC-0044.** `evals/evals.json` contains a case whose assertions contain both `wicked-estate lineage <` and `resolve`.
- [ ] **AC-0045.** `pack.toml` and `.claude-plugin/plugin.json` both carry version `0.1.8`.
- [ ] **AC-0046.** The `code-intelligence` entry in `.claude-plugin/marketplace.json` carries version `0.1.8`.
- [ ] **AC-0047.** `docs/product/changelog.md` contains a line matching `^## \[code-intelligence\]\[0\.1\.8\] — \d{4}-\d{2}-\d{2}$`.
- [ ] **AC-0048.** On the PR head, one `agentbundle catalogue self-host --root . --write` run leaves `git status --porcelain` output empty.
- [ ] **AC-0049.** `agentbundle catalogue verify --root .` exits 0.
- [ ] **AC-0050.** The `packs/AGENTS.local.md` internal-citation grep, run over the pack test modules this change edits, finds no match.

## Follow-ons

none

## Assumptions

- Technical: every MCP row rests on upstream schemas; `wicked-estate-mcp` is not run, so those rows stay labelled schema-derived. The MCP tool names are unchanged from 0.21.0.
- Technical: the new `flows_to` constructs (callbacks, `await`, destructuring, loops, closures) and the TSX/JavaScript coverage are source-read from the 0.26.0 changelog and crates; the Python fixture produces no value flow, so no live check reaches them.
