# Spec: Code-intelligence pack on Wicked Estate 0.18

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

An agent using the code-intelligence pack can ask Wicked Estate for the route
from one symbol to another and can tell a blast radius that the depth limit cut
short from a complete one. Every surface the pack ships names Wicked Estate
0.18.0 as both the floor and the pin, and no surface still teaches the path
query or the depth cut as missing.

## What Changes

- Version floor and pin are 0.18 / 0.18.0 — `pack.toml`, `scripts/estate_preflight.py`, `SKILL.md`, both agents, `README.md`, the guides under `guides/code-intelligence/`.
- `wicked-estate path` and MCP `Path` are in the capability map, the gaps assessment, and the investigation patterns — `references/`.
- `blast-radius --depth N` and its `searched_depth` / `depth_horizon_reached` / `node_cap_reached` fields replace the "silent depth-12 horizon" guidance — `SKILL.md`, `references/`, both agents, `README.md`, guides.
- MCP-only 0.17/0.18 additions are schema-derived rows: `Path`, `Lineage{relation:"flows_to"}`, `SearchEntity{include_values}`, `rules.recall{projects}`, the cut fields on `TraverseGraph`/`BlastRadius`/`Lineage`, and the tool counts — `references/capability-map.md`, `references/gaps.md`, `pack.toml`, `README.md`, guides.
- The vocabulary allowlist, the live-binary contract suite, and a retired-claim scan follow the 0.18.0 surface — `packs/code-intelligence/tests/`.
- An eval case covers a route question — `evals/evals.json`.
- Pack release 0.1.3 — `pack.toml`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Adopters read what the pack can answer and what it needs installed | `packs/code-intelligence/README.md`, `guides/code-intelligence/` (README, reference/capability-surface, tutorials/first-session, how-to/investigate-a-codebase) | Pack maintainer | Guides name 0.18.0 and describe `path` and `--depth` | AC-0006, AC-0027, AC-0029 green; each guide read whole once |
| Current product truth | The skill's references are the agent-facing statement of the upstream surface | `packs/code-intelligence/.apm/` (skill, references, agents) | Pack maintainer | Vocabulary and contract suites green against 0.18.0 | AC-0007 through AC-0031 green |
| Release history | A pack bump is the adopter-visible change record | `pack.toml`, `plugin.json`, `marketplace.json`, `docs/product/changelog.md` | Pack maintainer | 0.1.3 on all three manifests; changelog entry with its Highlights decision | AC-0032 through AC-0034 green |
| Decision rationale | RFC-0104 records the floor `>= 0.16` and the 0.16.7 pin; this change moves both, and the owner decided not to edit the RFC | `pack.toml` is the live authority for floor and pin; this spec records the divergence | Pack maintainer | This row | none beyond this spec |

## Agent Rules

### Always do

- Follow `packs/AGENTS.md` and `packs/AGENTS.local.md` for the version bump, eval update, self-host, marketplace rebuild, and changelog entry.
- State each new claim's provenance in the pack's three-way scheme: executed (CLI, run against 0.18.0), schema-derived (every MCP row), or source-read.
- Teach a CLI behaviour only when a criterion below pins it, or label it source-read.

### Ask first

- Raising the pin past 0.18.0, or documenting a release later than 0.18.0.
- Building or registering `wicked-estate-mcp` to execute MCP rows.
- Editing RFC-0104 or any other governance record.

### Never do

- Add a Python or Rust dependency, a new script, or a new skill or agent to the pack.
- Present an MCP-only capability as available on the CLI, or a schema-derived MCP row as executed.
- Replace the `wicked-estate` installed in the user's `PATH`; build test binaries into a scratch root.

## Testing Strategy

Every check below is either a pack test under `packs/code-intelligence/tests/` or a named command. "Shipped surface" means `packs/code-intelligence/.apm/`, `packs/code-intelligence/README.md`, and `packs/code-intelligence/pack.toml`.

- **Preflight (AC-0001, AC-0002):** TDD — a version comparison behind the `read_version` seam the existing suite monkeypatches.
- **Floor and pin (AC-0003, AC-0004, AC-0005):** goal-based static pack tests over `pack.toml`, the shipped surface, and the pin scanner's planted samples.
- **Guide pins (AC-0006):** goal-based command, because a pack test may not read outside its pack: the pin scanner in the pack test module, run over `guides/code-intelligence/`.
- **Vocabulary, static (AC-0007, AC-0009, AC-0010, AC-0011, AC-0012):** goal-based static pack tests.
- **Vocabulary, live (AC-0008):** integration — the live-binary dispatch check, under the same binary-on-`PATH` evidence rule as the CLI shapes.
- **CLI shapes (AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026):** integration — the live-binary suite indexes the three-file fixture with a real 0.18.0 binary. It skips without the binary, so the run evidence records a 0.18.0 binary on `PATH`.
- **Scanner input guard (AC-0038):** goal-based static pack test over a missing path and an empty temporary directory.
- **Retired claims (AC-0027, AC-0028, AC-0029):** goal-based — the retired-claim scanner as a pack test over the shipped surface and its planted samples, and as a command over the guides.
- **Route teaching (AC-0030, AC-0031):** goal-based static pack tests.
- **Release (AC-0032, AC-0033, AC-0034):** goal-based — manifest tests and file reads.
- **Eval (AC-0035):** goal-based static pack test.
- **Projection (AC-0036, AC-0037):** goal-based commands.
- **End to end:** manual QA — `estate_preflight.py --check`, `path`, and `blast-radius --depth` on the fixture with the built binary, recorded in the verification ledger.

## Acceptance Criteria

- [x] **AC-0001.** `estate_preflight.py --check` exits 4 and reports `required` as `0.18` when the binary reports version 0.17.0.
- [x] **AC-0002.** `estate_preflight.py --check` exits 0 when the binary reports version 0.18.0 and an index exists.
- [x] **AC-0003.** Both `[[pack.runtime-dependencies]]` entries in `pack.toml` declare `version = ">=0.18"`, equal to the preflight's `MINIMUM_VERSION`.
- [x] **AC-0004.** In the shipped surface, every `cargo install wicked-estate` or `cargo install wicked-estate-mcp` occurrence is followed by `--version 0.18.0 --locked`, and `0.18.0` equals the preflight's `PINNED_VERSION`.
- [x] **AC-0005.** The pin scanner accepts the planted `cargo install wicked-estate --version 0.18.0 --locked` and rejects the planted `cargo install wicked-estate --locked` and `cargo install wicked-estate --version 0.16.7 --locked`.
- [x] **AC-0006.** `main(["guides/code-intelligence"], scanner="pin")` in the guidance test module exits 0.
- [x] **AC-0007.** The vocabulary allowlist's CLI verbs include `path`.
- [x] **AC-0008.** A 0.18.0 binary dispatches every CLI verb in the vocabulary allowlist.
- [x] **AC-0009.** The vocabulary allowlist's MCP estate tools include `Path`.
- [x] **AC-0010.** `references/capability-map.md` names every MCP estate tool in the vocabulary allowlist.
- [x] **AC-0011.** The vocabulary allowlist records `VERIFIED_AGAINST = "0.18"`.
- [x] **AC-0012.** `references/capability-map.md` contains the allowlist's `VERIFIED_AGAINST` value.
- [x] **AC-0013.** On the fixture, `blast-radius <name> --json` returns exactly the keys `target`, `dependents`, `unresolved`, `truncated_dependents`, `searched_depth`, `depth_horizon_reached`, `node_cap_reached`.
- [x] **AC-0014.** On the fixture, `blast-radius helper --json` with no `--depth` reports `searched_depth` 12.
- [x] **AC-0015.** On the fixture, `blast-radius helper --depth 1 --json` reports `depth_horizon_reached: true` and `searched_depth: 1`.
- [x] **AC-0016.** On the fixture, `blast-radius helper --depth 24` exits 0 and `--depth 25` exits non-zero.
- [x] **AC-0017.** On the fixture, `blast-radius helper --depth 1` (text) prints a line containing `CUT AT depth=1`.
- [x] **AC-0018.** On the fixture, `path entry helper --json` returns `found: true` and two hops, each carrying the keys `kind`, `confidence`, `provenance`, `resolved_by`, `source`, `target`.
- [x] **AC-0019.** On the fixture, `path helper entry --json` returns `found: false` with `depth_bounded: false` and `node_bounded: false`.
- [x] **AC-0020.** On the fixture, `path entry helper --max-depth 1 --json` returns `found: false` with `depth_bounded: true`.
- [x] **AC-0021.** On the fixture, `path entry helper --max-depth 2 --json` returns `found: true` with `depth_bounded: true`.
- [x] **AC-0022.** On the fixture, `path nope helper --json` exits 0 and returns `unresolved: "from"`.
- [x] **AC-0023.** On the fixture, `path entry nope --json` exits 0 and returns `unresolved: "to"`.
- [x] **AC-0024.** On the fixture, `path entry helper --max-depth 17 --json` exits 0 and returns `found: true`.
- [x] **AC-0025.** On the fixture, every `path entry helper --json` hop endpoint has `line_1based` equal to `line + 1`.
- [x] **AC-0026.** On the fixture, the `path entry helper --json` endpoint named `helper` has `line_1based` equal to the `line` that `resolve helper --json` reports.
- [x] **AC-0027.** The retired-claim scanner finds no match in the shipped surface.
- [x] **AC-0028.** The retired-claim scanner matches every sentence in its planted stale sample and no sentence in its planted current sample.
- [x] **AC-0029.** `main(["guides/code-intelligence"], scanner="retired")` in the guidance test module exits 0.
- [x] **AC-0030.** `SKILL.md`, `references/capability-map.md`, and `references/investigation-patterns.md` each contain `wicked-estate path`.
- [x] **AC-0031.** `SKILL.md` and `references/capability-map.md` each contain a line holding both `blast-radius` and `--depth`.
- [x] **AC-0032.** `pack.toml` and `.claude-plugin/plugin.json` both carry version `0.1.3`.
- [x] **AC-0033.** The `code-intelligence` entry in `.claude-plugin/marketplace.json` carries version `0.1.3`.
- [x] **AC-0034.** `docs/product/changelog.md` contains a line matching `^## \[code-intelligence\]\[0\.1\.3\] — \d{4}-\d{2}-\d{2}$`.
- [x] **AC-0035.** `evals/evals.json` contains a case whose prompt contains `reach` and whose assertions contain both `wicked-estate path` and `depth_bounded`.
- [x] **AC-0036.** On the PR head, one `agentbundle catalogue self-host --root . --write` run leaves `git status --porcelain` output empty: no tracked file changes and no untracked file appears.
- [x] **AC-0037.** `agentbundle catalogue verify --root .` exits 0.
- [x] **AC-0038.** The guidance test module's `main` exits non-zero when a given path does not exist and when the given paths contain no file to scan.

## Follow-ons

none

## Assumptions

- Technical: the allowlist equals upstream 0.18.0's dispatch set by source-read (upstream `main.rs` diff, 34 → 35 names, `path` added). No check fails on a verb upstream dispatches but the allowlist omits.
- Technical: every MCP row rests on upstream schemas and release notes; `wicked-estate-mcp` is not run, so those rows stay labelled schema-derived.
