# Plan: Code-intelligence pack on Wicked Estate 0.18

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `packs/AGENTS.md` and `packs/AGENTS.local.md` (version bump, eval, self-host, marketplace, changelog); `tests/AGENTS.md` (a pack test may not read above its pack); the pack's suites `packs/code-intelligence/tests/pack/test_estate_surface_vocabulary.py`, `tests/pack/test_manifest.py`, `tests/skills/code-intelligence/test_estate_cli_contract.py`, `tests/skills/code-intelligence/test_estate_preflight.py`; the `code-intelligence` pytest lines in the `Makefile` test chain, which always run `tests/pack/` and `skills/code-intelligence/`; only the live-binary contract module inside the latter skips when `wicked-estate` is absent; `tools/build-site.py` (changelog heading form). Non-structural: no new module or boundary.

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

Tests first, then prose, then release. T1 moves every suite to the 0.18.0
surface and adds the two scanners; the new static checks go red against the
current prose. T2 rewrites the preflight, manifest pins, skill, references,
agents, README and guides until every pack test is green. T3 adds the eval,
bumps the version, rebuilds the marketplace, writes the changelog entry, and
re-projects. The riskiest part is prose accuracy, which the live-binary suite
and the retired-claim scanner bound.

## Constraints

- RFC-0104 admits the pack with a three-tier runtime-dependency policy: exact pin, detect first, install only on consent. It records the floor `>= 0.16` and the 0.16.7 pin. This plan keeps the policy and moves both values to 0.18 / 0.18.0. The RFC stays unedited by owner decision; `pack.toml` is the live authority.
- `packs/AGENTS.md` and `packs/AGENTS.local.md`: matching version bump, eval update, self-host after `.apm/` edits, `FORCE=1 make build-self` for the marketplace, a free-standing changelog entry with a Highlights decision, no internal-governance citations under `packs/`.
- `tests/AGENTS.md`: a pack test reads only inside its pack, so guide checks run as commands.
- `tools/build-site.py` rejects a release heading without a trailing ISO date.
- Root `AGENTS.md`: the local gate is `make lint-ruff lint-mypy` plus the touched suites.

## Construction tests

**Integration tests:** the live-binary suite (`test_estate_cli_contract.py`) with a 0.18.0 binary first on `PATH`, built by `cargo install wicked-estate --version 0.18.0 --locked --root <scratch>`.
**Manual verification:** `estate_preflight.py --check` in a scratch repository holding an index, plus `path` and `blast-radius --depth` text output, recorded in `notes/verification-ledger.md`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing promise — pack README, guides | T2 | AC-0006 and AC-0029 commands; AC-0027 pack test | Commands and tests green on the PR head; guides read whole once |
| Current product truth — skill, references, agents | T1, T2 | Vocabulary, contract and guidance suites green against 0.18.0 | Same suites green |
| Release history — manifests, marketplace, changelog | T3 | Manifest tests; `marketplace.json`; changelog heading | 0.1.3 everywhere; Highlights decision recorded |
| Decision rationale — RFC divergence | none | Spec Durable Outputs row | — |

## Design (LLD)

### Interfaces & contracts

Upstream facts the prose relies on. "Pinned" marks a fact a criterion holds. "Source-read" marks one read from upstream 0.18.0 source; the prose labels it so.

- `path <from> <to> [--max-depth N] [--json]` follows dependency edges only, caller to callee, over every edge kind (source-read). With an ambiguous `<from>` it returns one shortest route across all candidates (source-read). `--max-depth` takes 1–16, defaults to 12, and clamps values above 16 to 16 (source-read); a value above 16 is accepted (pinned by AC-0024).
- `path --json`: `{from, to, hops[], found, depth_bounded, node_bounded, unresolved}`. Each hop carries `{source, target, kind, confidence, provenance, resolved_by}` (pinned by AC-0018). Each endpoint carries `{symbol, name, kind, file, line, line_1based}`, and `line` is 0-based, unlike `resolve` and `blast-radius` (pinned by AC-0025, AC-0026). `depth_bounded` is true whenever the walk touched its frontier, even when a route was found (pinned by AC-0021). An unresolved input on either side exits 0 (pinned by AC-0022, AC-0023). Text mode prints `STALENESS:`, so six commands print it (source-read).
- `blast-radius --depth N`: default 12, maximum 24, above 24 refused (pinned by AC-0014, AC-0016). JSON adds `searched_depth`, `depth_horizon_reached`, `node_cap_reached` (pinned by AC-0013). The text coverage line reads `CUT AT depth=N` on a cut (pinned by AC-0017). Rows still carry no per-dependent depth or confidence; `--depth 1` gives the direct set, and the difference against the full run is the transitive set.
- MCP, schema-derived: `Path{from, to, depth 1–16 default 8, max_nodes ≤ 5000 default 1000}`; `Lineage{relation:"flows_to"}`, TypeScript-only value flow; `SearchEntity{include_values}`; `rules.recall{projects}`; `TraverseGraph`, `BlastRadius` and `Lineage` add `depth_horizon_reached`, `node_cap_reached`, `searched_depth`.
- MCP counts, all on one basis: the server advertises 30 tools without an embedding backend and 31 with one (`SemanticSearch`). That is 11 estate tools plus 19 dotted tools. `--readonly` drops the 10 write tools, leaving 20 (21 with `SemanticSearch`). The vocabulary allowlist lists 12 estate names, because it includes `SemanticSearch`.
- The real-repository counts in `gaps.md` (65,807 nodes, dead-code 65%, 727 truncated) were measured on 0.16.7 and stay attributed to it. Nothing in 0.17 or 0.18 changes those verbs.

Traces to AC-0013 through AC-0026, AC-0030, AC-0031.

Owned by: T1, T2.

### Behavior & rules

Both scanners live in `tests/pack/test_estate_0_18_guidance.py` and take paths. The shipped surface is `.apm/`, `README.md` and `pack.toml`; the pack's `tests/` tree is outside it, so the planted samples and the preflight remediation assertion never scan themselves.

The retired-claim scanner lowercases text, strips the Markdown emphasis characters `*`, `_` and `` ` ``, and collapses every whitespace run, including line breaks, to one space before matching. That lets it see a phrase split across a wrapped line or broken by emphasis. Its patterns are regular expressions with word boundaries:

- path absent: `\bno path query\b`, `\bnothing returns the path between\b`, `\bno "how does a reach b" primitive\b`, `\breachability, not the route\b`, `reachability is answerable; the route is not\b`, `reachability yes, the route no\b`, `\bpaths (?:\||—) absent\b`
- silent depth: `\btwelve[- ]hops?\b`, `\bfixed depth of 12\b`, `\bhardcod(?:ed|es)\b`, `\bdepth cap unreported\b`, `\bhorizon is silent\b`, `\bsilent (?:depth-12 )?horizon\b`, `\bdepth-12 traversal cap\b`, `\bthird limit (?:is|and it is) (?:not reported|unreported)\b`, `\bfourth limit that is not reported\b`
- no CLI depth: `\bimpact cannot be separated\b`, `\bdepth on a cli blast radius\b`, `\bflat list with no depth\b`
- no CLI edge evidence: `\bnot printed on the cli read paths\b`, `\bper-edge confidence or provenance on cli read paths\b`, `\babsent from (?:the )?cli output\b`
- stale counts: `\b29 tool`, `\bleaving 19\b`, `\bfive subcommands\b`
- stale version: `\b0\.16(?!\.\d)`, which matches a bare `0.16` floor or version claim but not `0.16.7` provenance

Its planted stale sample holds one current-tree sentence per pattern. Its planted current sample holds correct 0.18 sentences that must not match, including: "A `found: false` with `depth_bounded: true` means the route is not proven absent", "Measured on Wicked Estate 0.16.7 against a real repository", "`--depth 1` returns the direct dependents", and "`path` hops carry confidence and provenance; `blast-radius` rows do not".

The pin scanner matches every `cargo install wicked-estate(-mcp)?` occurrence and requires `--version 0.18.0 --locked` to follow it.

`main(paths, scanner)` runs the scanner named `pin` or `retired`. It exits 2 when a given path does not exist or the paths hold no file to scan, 1 with each `file:line` hit, and 0 otherwise. The guide checks run it from the repository root, once per scanner:

```bash
python3 -c "import importlib.util as u,sys; s=u.spec_from_file_location('ci_guidance','packs/code-intelligence/tests/pack/test_estate_0_18_guidance.py'); m=u.module_from_spec(s); s.loader.exec_module(m); sys.exit(m.main(['guides/code-intelligence'], scanner='pin'))"
python3 -c "import importlib.util as u,sys; s=u.spec_from_file_location('ci_guidance','packs/code-intelligence/tests/pack/test_estate_0_18_guidance.py'); m=u.module_from_spec(s); s.loader.exec_module(m); sys.exit(m.main(['guides/code-intelligence'], scanner='retired'))"
```

Traces to AC-0004, AC-0005, AC-0006, AC-0027, AC-0028, AC-0029, AC-0038.

Owned by: T1.

### Dependencies & integration

The only external dependency is the `wicked-estate` crate. Its floor and pin live in `pack.toml` and `estate_preflight.py`, and every install command repeats the pin. Traces to AC-0001 through AC-0006.

Owned by: T2.

## Tasks

### T1: Suites describe the 0.18.0 surface

**Depends on:** none
**Touches:** `packs/code-intelligence/tests/**`

**Tests:**
- `test_estate_preflight.py`: the floor test uses a 0.17.0 version and expects exit 4 with `required == "0.18"` (AC-0001). Every other test that stubs `read_version` uses 0.18.0, including the ready test (AC-0002), `test_present_binary_without_index_exits_three`, and `test_refused_override_reports_exit_six_and_names_the_fix`.
- `test_manifest.py`: both runtime-dependency floors read exactly `>=0.18` and equal `>=` plus `MINIMUM_VERSION` (AC-0003); manifest versions are 0.1.3 (AC-0032). The preflight loads under a pack-qualified module name.
- `test_estate_surface_vocabulary.py`: `path` in `CLI_VERBS` (AC-0007), `Path` in `MCP_ESTATE_TOOLS` (AC-0009), `VERIFIED_AGAINST = "0.18"` (AC-0011). The existing capability-map tests carry AC-0010 and AC-0012; the existing live dispatch test carries AC-0008.
- `test_estate_cli_contract.py`: key set (AC-0013); default depth (AC-0014); cut (AC-0015); ceiling (AC-0016); text cut line (AC-0017); path found (AC-0018), proven absence (AC-0019), depth-bounded absence (AC-0020), bounded found (AC-0021), unresolved from (AC-0022), unresolved to (AC-0023), above-16 accepted (AC-0024), line numbering (AC-0025, AC-0026). The docstring and skip reason name 0.18.0, and docstrings cite `gaps.md` sections by name, not number.
- New `tests/pack/test_estate_0_18_guidance.py`: pin scanner over the shipped surface (AC-0004) and its planted samples (AC-0005); retired-claim scanner over the shipped surface (AC-0027) and its planted samples (AC-0028); route teaching (AC-0030, AC-0031); eval case (AC-0035); `main(paths, scanner)` for the guide commands, and its refusal of a missing path and of an empty directory (AC-0038).

**Done when:** with a 0.18.0 binary first on `PATH`, `python3 -m pytest packs/code-intelligence/tests -q` fails only these tests, each on prose or manifests T2 or T3 owns: the preflight floor test, the floor and version tests in `test_manifest.py`, `test_capability_map_names_every_estate_tool`, `test_capability_map_records_the_verified_version`, and the shipped-surface pin, shipped-surface retired-claim, route-teaching and eval tests. The planted-sample tests (AC-0005, AC-0028) pass.

### T2: Preflight, manifest, skill, references, agents, README and guides teach 0.18.0

**Depends on:** T1
**Touches:** `packs/code-intelligence/.apm/**`, `packs/code-intelligence/README.md`, `packs/code-intelligence/pack.toml`, `guides/code-intelligence/**`

**Tests:**
- Every T1 test except the eval (AC-0035) and version (AC-0032) tests turns green.
- The guide commands for AC-0006 and AC-0029 exit 0.
- `python3 -m pytest tools/test_check_output_readability.py -q` passes, because it scores the pack's `evals/files/cognitive-load/ordinary-prose.md` fixture, which T2 rewords.

**Approach:**
- `gaps.md`: Paths is Direct on CLI and MCP; the Impact table gains the depth parameter and cut fields, and its "flat list with no depth" caveat becomes the `--depth 1` direct-set route; §10 and §11 say `path` hops carry confidence and provenance while `blast-radius` rows do not; Completeness reports the depth cut; the summary table and found-gaps list drop the path and silent-depth items and renumber; a caveat covers the 0-based `line` in `path`.
- `capability-map.md`: `path` and MCP `Path` rows; `blast-radius --depth` row; completeness table depth row; `STALENESS:` list gains `path`; MCP counts per Design; `Lineage` `flows_to`, `include_values`, `rules.recall` `projects`.
- `investigation-patterns.md`: pattern 3 uses `path` for "how does A reach B"; pattern 2 step 3 reads the cut fields and raises `--depth`; step 4 separates direct from transitive with `--depth 1`.
- `evidence.md`: the depth section is about the reported cut; bounded versus proven absence for `path`.
- `agents/impact-analyst.md`, `agents/code-investigator.md`, `references/example-prompts.md`, `evals/files/cognitive-load/ordinary-prose.md`, `README.md`, and the four guides: the same claims, rescoped.

**Done when:** the T2 Tests hold with a 0.18.0 binary first on `PATH`.

### T3: Eval, release, projection

**Depends on:** T2
**Touches:** `packs/code-intelligence/.apm/skills/code-intelligence/evals/evals.json`, `packs/code-intelligence/pack.toml`, `packs/code-intelligence/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md`, self-host projections

**Tests:**
- The eval (AC-0035) and version (AC-0032) tests from T1 turn green.
- `FORCE=1 make build-self` regenerates `marketplace.json`; its `code-intelligence` entry reads 0.1.3 (AC-0033).
- `docs/product/changelog.md` carries a free-standing `## [code-intelligence][0.1.3] — <YYYY-MM-DD>` entry (AC-0034) with a Highlights decision per `packs/AGENTS.local.md`.
- The self-host run of AC-0036 on the committed head; `agentbundle catalogue verify --root .` (AC-0037).

**Done when:** the T3 Tests hold, the whole pack suite passes with a 0.18.0 binary first on `PATH`, and `make lint-ruff lint-mypy` passes.

## Rollout

Big bang in one PR, reversible by revert. An adopter on 0.16 or 0.17 sees preflight exit 4 until they run the pinned install. There is no data migration.

## Risks

- Upstream prose versus behaviour: three earlier CLI claims from upstream docs were wrong when run. The live-binary suite pins each CLI behaviour the prose teaches as executed.
- The live-binary suite skips in CI without the binary, so run evidence comes from a local 0.18.0 build recorded in the ledger.

## Changelog

- 2026-10-03: spec approved by eugenelim
- 2026-10-03: plan approved by eugenelim
