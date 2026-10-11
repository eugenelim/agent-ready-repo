# Plan: Code-intelligence pack on Wicked Estate 0.29

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packs/AGENTS.md` and `packs/AGENTS.local.md` (version bump, eval, self-host, marketplace, changelog); `tests/AGENTS.md` (a pack test may not read above its pack); the shipped precedent `docs/specs/code-intelligence-estate-0-26/` and its suites under `packs/code-intelligence/tests/`. Non-structural: no new module or boundary.

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

Tests first, then prose, then release — the 0.26 shape. T1 moves every suite to
the 0.29.2 surface and adds the wide fixture, so the static checks go red
against today's prose. T2 rewrites the preflight, manifest, skill, references,
agents, evals, README and guides until every pack test is green. T3 bumps the
version, rebuilds the marketplace, writes the changelog entry, and re-projects.
The riskiest part is the paging prose: what `truncated_dependents` now means,
and that a refused cursor is a restart, not an end.

## Constraints

- RFC-0104's three-tier runtime-dependency policy stays: exact pin, detect first, install only on consent. Only the floor and pin values move, and the RFC stays unedited.
- `packs/AGENTS.md`: patch bump for changed content (no new primitive), eval update, self-host after `.apm/` edits, no internal-governance citations under `packs/`.
- `packs/AGENTS.local.md`: `FORCE=1 make build-self` for the marketplace; free-standing changelog entry with a Highlights decision.
- `tests/AGENTS.md`: a pack test reads only inside its pack, so guide checks run as commands.
- `packs/AGENTS.md` test cost: the wide fixture is session-scoped and indexed once; each probe runs against a copy only when it mutates.

## Construction tests

**Integration tests:** the live suite with the 0.29.2 binary first on `PATH`, built by `cargo install --root /tmp/we-0292-bin wicked-estate --version 0.29.2 --locked`.
**Manual verification:** `estate_preflight.py --check` in a scratch repository holding an index, plus `blast-radius --json` and `lineage --json` paged to a `null` cursor, recorded in `notes/verification-ledger.md`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing promise — pack README, guides | T2 | AC-0006, AC-0033 and AC-0034 commands; AC-0031 pack test | Commands and tests green on the PR head |
| Current product truth — skill, references, agents | T1, T2 | Vocabulary, contract and guidance suites green against 0.29.2 | Same suites green |
| Release history — manifests, marketplace, changelog | T3 | Manifest tests; `marketplace.json`; changelog heading | 0.1.9 everywhere; Highlights decision recorded |
| Decision rationale — RFC divergence | none | Spec Durable Outputs row | — |

## Design (LLD)

### Interfaces & contracts

Upstream facts the prose relies on, observed with 0.29.2 on a scratch repository whose `helper` had 1,500 callers, unless marked source-read.

- **Paging.** One reply stays under 25,000 characters, except that a single row wider than the budget is carried whole on its own page with a stderr note (source-read); the answer is not bounded. `blast-radius --json` adds `next_cursor` (string or `null`) and `page {from, count, total}`. `truncated_dependents` is the number of rows on later pages, so on every page `page.from + page.count + truncated_dependents == page.total`. Blast-radius text mode prints `…and N more (one reply is bounded at 25K chars): --cursor <c>`. `lineage --json` adds `next_cursor` and `page {dependencies {from, count, total}, flows {from, count, total}}`; its `truncated` is true while more pages remain or on a depth or node cut, and its `total` counts the whole answer. Lineage writes its page note — ``pass `cursor`: "<c>" for the rest`` — with its other diagnostics: stderr under `--json`, stdout after the result in text mode; the pack does not teach the blast-radius text form for lineage. Rows are ordered by depth, then symbol id, so pages from separate runs join exactly. Observed: `blast-radius helper` returned 1,503 rows (1,500 callers plus file nodes) over 12 pages and `lineage fan_out` 1,501 over 12 pages, all distinct. Following `next_cursor` until `null` returns the whole answer; a depth or node cut stays reported on the last page.
- **Refused cursors.** The cursor fingerprints the crate version, the tool, the query, and every row of the answer (source-read, `paging.rs`). So a cursor is refused — exit 1, nothing on stdout — when the answer it pages has changed: another query or `--depth`, another build, or different rows after a re-index. The message is ``this `cursor` belongs to another query, or the graph changed since it was issued; restart without `cursor` to page the current answer``. A malformed cursor gets its own message, ``malformed `cursor` "<c>"; pass back the `next_cursor` of the previous page unchanged, or omit `cursor` for the first page``. A re-index that leaves the answer's rows unchanged does not refuse the cursor, so cursor acceptance is never a freshness signal; `stats --json` stays the freshness check. The pack teaches: on refusal, start again from the first page; never splice pages from two answers.
- **Lineage depth.** Default 24, the ceiling (was 8); `--depth` above 24 still clamps with `CLAMPED:` on stderr.
- **MCP.** `BlastRadius` and `Lineage` accept `cursor` and return `next_cursor` and `page` (schema-derived, upstream 0.28.0). MCP `BlastRadius` still defaults to depth 8. `wicked-estate-mcp --readonly` with a store path that does not exist creates no file and serves that store empty in memory, printing `read-only: no <store> store at '<path>'; serving it empty in memory` on stderr (source-read, `wicked-estate-mcp` 0.29.2 `main.rs`). The same applies to the memory, knowledge and cross-store databases, whose paths come from `WICKED_MEMORY_DB`, `WICKED_KNOWLEDGE_DB`, `WICKED_XEDGE_DB`, or `WICKED_HOME`. Tool names and the ten write tools are unchanged (source-read).
- **Value lineage.** The local-object-property hops are gone (upstream 0.27.0); callbacks, `await` and `.then`, destructuring, loops, and closure returns remain (source-read).
- **Re-index.** A version bump re-extracts each graph on its next `index`; the pack's existing version-mismatch guidance already covers this.

Traces to AC-0010 through AC-0030, AC-0034.

Owned by: T1, T2.

### Behavior & rules

`REQUIRED_PIN` becomes `0.29.2`; the planted stale pins add `--version 0.26.0`. The retired-claim scanner keeps every earlier pattern and adds a 0.29 group, each with a planted stale sentence copied from the line it retires:

Patterns are matched after the existing normalisation (lowercase, strip `*`, `_`, `` ` ``, collapse whitespace), so `truncated_dependents` is matched as `truncateddependents`.

- order: `\bwhatever the store returned\b` (`evidence.md:79-80`)
- prefix: `\bthe list is a prefix\b` (`capability-map.md:210`)
- dropped rows: `\btruncateddependents \(rows dropped\)` (`capability-map.md:210`); `\btruncateddependents counts rows dropped\b` (`impact-analyst.md:49`, `investigation-patterns.md:100`); `\breports how many rows it dropped\b` (`evidence.md:78`); `\bthe --depth 1 run truncated\b` (`evidence.md:110`)
- old key sets: `\bnodecapreached, confidence\}` (`capability-map.md:87`, blast-radius); `\brelation, searcheddepth, depthhorizonreached, nodecapreached\}` (`capability-map.md:127`, lineage — scoped by `relation` so the unchanged `traverse` key set does not match)
- lineage depth: `\bdefault depth 8; line is 0-based\b` (`capability-map.md:127`); `\bdefault depth is 8\b` (`investigation-patterns.md:68`, the only occurrence in the shipped surface and guides)
- removed hops: `\blocal object properties\b` (`evidence.md:237`, `capability-map.md:128`)
- stale version: `\b0\.2[6-8](?:\.\d)?(?![\d,])`, checked during T1 against every decimal the shipped surface uses

T1 greps the shipped surface and guides for each retired claim's paraphrases and adds a pattern for any it finds. A pattern may be adjusted during T1 to match its real sentence; the stale sample stays the real sentence. Planted current sentences that must not match include "`truncated_dependents` counts the rows on later pages.", "Follow `next_cursor` until it is `null`.", "MCP `BlastRadius` defaults to depth 8.", "`traverse --json` returns `{nodes, edges, depths, truncated, searched_depth, depth_horizon_reached, node_cap_reached}`.", "Output is capped at 25,000 characters per reply.", and "Measured on Wicked Estate 0.16.7 against a real repository."

The guide checks reuse the 0.26 commands with `scanner='pin'` and `scanner='retired'`.

Traces to AC-0004, AC-0005, AC-0006, AC-0031, AC-0032, AC-0033.

Owned by: T1.

### Dependencies & integration

The only external dependency is the `wicked-estate` crate family; floor and pin live in `pack.toml` and `estate_preflight.py`, and every install command repeats the pin. Traces to AC-0001 through AC-0006.

Owned by: T2.

## Tasks

### T1: Suites describe the 0.29.2 surface

**Depends on:** none
**Touches:** `packs/code-intelligence/tests/**`

**Tests:**
- `test_estate_preflight.py`: the floor test stubs 0.28.0 and expects exit 4 with `required == "0.29"` (AC-0001); every other `read_version` stub uses 0.29.2 (AC-0002).
- `test_manifest.py`: both floors read `>=0.29` (AC-0003); the version test becomes `test_pack_version_is_0_1_9` (AC-0035).
- `test_estate_surface_vocabulary.py`: `VERIFIED_AGAINST = "0.29"` (AC-0007). The live dispatch test carries AC-0008 and the capability-map version test AC-0009.
- `test_estate_cli_contract.py`: the version test reads `wicked-estate 0.29.2` (AC-0010); the blast-radius and lineage key-set tests add `next_cursor` and `page` and assert the single-page values (AC-0011, AC-0012); the lineage default-depth test asserts 24 (AC-0013). A session-scoped wide fixture — `helper` with 300 callers named `caller_with_a_reasonably_long_name_NNNN`, and `fan_out` calling all 300 — backs one test per criterion AC-0014 through AC-0021; AC-0020 indexes a second source tree with one more caller into its own database. Module docstring and skip reason name 0.29.2.
- `test_composition_evals.py` or `test_composition_example.py`: every `blast-radius` JSON file under `evals/files/` carries `next_cursor` and `page` (AC-0030).
- `tests/pack/test_estate_guidance.py`: pin and retired scanners per Design (AC-0004, AC-0005, AC-0031, AC-0032); new teaching tests (AC-0022 through AC-0028); a paging and restart eval test (AC-0029). No module cites an acceptance-criterion ID (AC-0040).

**Done when:** with the 0.29.2 binary first on `PATH`, `python3 -m pytest packs/code-intelligence/tests -q` fails only tests on prose, evals or manifests T2 or T3 own. Every live-suite test and both planted-sample tests pass.

### T2: Preflight, manifest, skill, references, agents, evals, README and guides teach 0.29.2

**Depends on:** T1
**Touches:** `packs/code-intelligence/.apm/**`, `packs/code-intelligence/README.md`, `packs/code-intelligence/JOURNEY.md`, `packs/code-intelligence/pack.toml` except its `version` field, `guides/code-intelligence/**`

**Tests:**
- Every T1 test except the version test (AC-0035) turns green.
- The guide commands for AC-0006, AC-0033 and AC-0034 exit 0.
- `python3 -m pytest tools/test_check_output_readability.py -q` passes.

**Approach:**
- `estate_preflight.py`: `MINIMUM_VERSION = (0, 29)`, `PINNED_VERSION = "0.29.2"`, surface comment and docstring.
- `pack.toml`: floors, pins, recovery text, and the MCP note's mention of paging if it lists response shapes.
- `SKILL.md`: the floor-not-total rule says a non-zero `truncated_dependents` counts rows on later pages, retrieved with `--cursor <next_cursor>` until `next_cursor` is `null`; only then is the list the whole resolved answer within `searched_depth`. On a refused cursor, start again from the first page; an accepted cursor says nothing about freshness. Lineage default depth 24, and lineage `truncated` is true while more pages remain or on a cut.
- `evidence.md`: rewrite § `truncated_dependents` (rows on later pages, ordered by depth then id, retrievable, start again from the first page on refusal); the direct-and-transitive section's "`--depth 1` run truncated" case becomes "page the `--depth 1` run to `null` first"; lineage `truncated` is true while more pages remain or on a cut; remove local object properties.
- `capability-map.md`: `VERIFIED_AGAINST` 0.29; blast-radius and lineage rows gain `--cursor` and the full 0.29.2 key sets with `next_cursor` and `page`; lineage `Default depth 24`; output-cut row says later pages are retrievable on both surfaces; MCP `cursor`; the `--readonly` empty in-memory note naming `--db`, `WICKED_MEMORY_DB`, `WICKED_KNOWLEDGE_DB`, `WICKED_XEDGE_DB` and `WICKED_HOME`; remove local object properties.
- `gaps.md`: header version; output-cut rows; any gap closed by paging is closed.
- `impact-analyst.md`, `code-investigator.md`, `investigation-patterns.md`, `example-prompts.md`, `composition-example.md`: page before reporting; the same claims rescoped.
- `README.md`, `JOURNEY.md`, the guides: version, paging (the guide reference `capability-surface.md` names `--cursor` and `next_cursor`), and the `--readonly` empty in-memory note with the store paths where `--readonly` is recommended.
- `evals/evals.json`: a paging case whose assertions name `next_cursor` and `--cursor`, and a refused-cursor case whose assertions require starting again from the first page; existing cases that call a truncated list a floor read "page it, then report"; the lineage case ("a larger `--depth` (up to 24) when the horizon was reached") reports a horizon cut at 24 as a cut and pages a `truncated: true` reply first. `evals/files/` blast-radius JSON gains `next_cursor: null` and `page`; preflight and stats files name 0.29.2.

**Done when:** the T2 Tests hold with the 0.29.2 binary first on `PATH`, and each touched shipped file and guide has been read whole once after editing.

### T3: Release and projection

**Depends on:** T2
**Touches:** `packs/code-intelligence/pack.toml` `version`, `packs/code-intelligence/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md`, self-host projections

**Tests:**
- The version test (AC-0035) turns green.
- `FORCE=1 make build-self` regenerates `marketplace.json` with `code-intelligence` at 0.1.9 (AC-0036).
- `docs/product/changelog.md` carries `## [code-intelligence][0.1.9] — <YYYY-MM-DD>` (AC-0037) with a Highlights decision.
- The self-host run on the committed head (AC-0038); `agentbundle catalogue verify --root .` (AC-0039).
- The internal-citation grep over the edited test modules (AC-0040).

**Done when:** the T3 Tests hold, the whole pack suite passes with the 0.29.2 binary first on `PATH`, and `make lint-ruff lint-mypy` passes.

## Rollout

One PR, reversible by revert. An adopter on 0.26–0.28 sees preflight exit 4 until they run the pinned install; the first `index` after upgrading re-extracts the whole graph automatically. No data migration.

## Risks

- The live suite skips in CI without the binary, so run evidence comes from the local 0.29.2 build recorded in the ledger.
- Upstream shipped 0.27.0 through 0.29.2 on one day; a further patch would need its own pin bump.
- The wide fixture adds index time to the live suite; 300 callers indexed in well under a second on the scratch probe.

## Changelog
- 2026-10-11: spec approved by eugenelim
- 2026-10-11: plan approved by eugenelim
