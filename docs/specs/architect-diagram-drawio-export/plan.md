# Plan: architect-diagram-drawio-export

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (version bump, eval harness, test rules); analogous change: `docs/specs/architect-diagram-product-types/` (added references, fixtures, evals to the same skill); existing suite `packs/architect/tests/skills/architect-diagram/test_fixtures.py`. Deviation: the new suite needs no external binary, unlike the `mmdc` suite.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md`. A genuine artifact error
> follows the controlled-amendment path.

## Approach

Prose-first change to one skill. The riskiest part is the agent-facing
procedure, so the reference carries the full CLI recipe and the skill body
carries only the routing hook and the save-step delta. Structure checks land
first so the fixtures and the reference skeleton are pinned before prose
grows around them. Docs, evals, and release surfaces follow the skill text
they describe.

## Constraints

- `packs/AGENTS.md`: patch bump for changed content; non-cosmetic pack change updates the eval harness; tests never call a package manager or external binary; shipped pack content cites no internal records.
- `packs/architect/DESIGN.md` § 9 invariant 5 ("Mermaid only") is amended by this change, with the owner's request as the authority.
- `docs/product/changelog.md` header: fragments via `tools/changelog.py new`.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** convert the fixtures with the draw.io desktop CLI and record its version, command, and exit code in the verification ledger; confirm one converted fixture's cell labels match the Mermaid node labels; run the live activation run the spec's Testing Strategy names and record its per-query results (required before the PR opens; owned by T6).

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing promise — how-to + README | T5 | `tools/validate_guides.py`, `tools/check-guide-index.py` pass | Section matches shipped behavior |
| Decision rationale — explanation guide + DESIGN.md | T5 | Diff of the three DESIGN.md passages and § Why Mermaid | No surface still claims "no other format" (grep) |
| Current product truth — skill, reference, layout | T1–T4 | Fixture test, evals, catalogue lint | AC-0001 to AC-0005 and AC-0007 checked |
| Release history — changelog fragment | T6 | Fragment validator | AC-0006 checked |
| Reusable learning — lenient-parser warning | T2 | Reference output-check section; eval (a) assertion | — |

## Design (LLD)

### Design decisions

Owned by: T2, T3

- **Mermaid is the authored source.** The CLI converts the saved `.mmd`. On the fallback path the agent transcribes that `.mmd` node for node and edge for edge; it never draws a different diagram. Traces to: AC-0002.
- **Conversion command** `<cli> --disable-update -x -f xml -u -o <dir>/<stem>.drawio <dir>/<stem>.mmd`, where `<dir>` is the confined save directory's resolved absolute path, run with arguments passed as a list, not a shell string. The overwrite check targets the same `<dir>/<stem>.drawio`. `-u` pins uncompressed output; `--disable-update` stops the app's update check. The stem is the kebab-case slug the save step already confines. Traces to: AC-0002.
- **No overwrite without a yes.** The skill checks whether `<stem>.drawio` exists and asks before replacing it. It does not pass `-k`, because `-k` makes the CLI write an unsurfaced `<stem>-1.drawio`. Traces to: AC-0002.
- **Install allowlist is package managers only** — the three commands AC-0007 pins. Each verifies the package itself (cask SHA-256, winget manifest hash, signed snap). Without the matching package manager, the skill links the official release page `https://github.com/jgraph/drawio-desktop/releases` for the user to install by hand and runs nothing. The reference carries the allowlist in one `text install-allowlist` block. Traces to: AC-0007.
- **Boundary declaration:** `metadata.boundaries` gains `network_egress`, because an approved install reaches a package registry through the shell. No `network_fetch`: the skill fetches nothing itself. Traces to: AC-0007.
- **Minimum CLI version 31.7.0**, the first release with command-line Mermaid import. An older CLI gets the same allowlisted command as an upgrade offer, under the same consent rule.
- **Chat-only mode** has no file to convert: the skill gives the Insert › Mermaid steps or offers to save first. **repository-handoff** lists the `.drawio` as one more needed write and stops with zero effects. Traces to: AC-0002.
- **Security review:** the spec-stage `security-reviewer` pass covers the install and execution flow; the diff-stage pass runs at REVIEW.
- **Rejected:** depending on jgraph's `drawio` skill or `@drawio/mcp` (Never-do rule); a Python converter (needs a JavaScript layout engine, a new dependency); direct `.deb`/`.rpm`/`.dmg` downloads (would need agent-run checksum checks); PNG/SVG export (out of scope).

### Behavior & rules

Owned by: T1, T2

CLI detection order: `drawio` then `draw.io` on PATH; macOS `/Applications/draw.io.app/Contents/MacOS/draw.io` and `~/Applications/draw.io.app/Contents/MacOS/draw.io`; Windows `%ProgramFiles%\draw.io\draw.io.exe` and `%LOCALAPPDATA%\Programs\draw.io\draw.io.exe`. Confirm with `--version`. A headless Linux host prefixes `xvfb-run -a`. Snap builds cannot read `/tmp`; the save directory must sit under the user's home.

Output check, run on every `.drawio` before it is presented — CLI output and the agent-written fallback alike: the file parses as an uncompressed `mxfile` with at least one vertex; it passes the AC-0003 link-safety rule, which allows the CLI's own `image=data:image/...` icon encoding and nothing else as a URL; and every node and participant label in the saved `.mmd`, after XML unescape and whitespace normalisation, equals some cell's `value` or `label` after the same normalisation (edge labels and subgraph titles are not compared). For the agent-written fallback only, the check also rejects any cell style that sets `html=1`; CLI output legitimately carries it. A failed check blocks: it is reported, and the `.drawio` is not presented as done.

Link safety: Mermaid `click` and `href` lines are left out of a diagram meant for draw.io export. When a saved `.mmd` already has them, the skill names them and asks the user to remove them before export.

Agent-written XML fallback: uncompressed `mxfile` → `diagram` → `mxGraphModel` → `root`; cells `0` and `1` first; every vertex has `mxGeometry` with x/y/width/height on a simple grid; every edge has `source`, `target`, and `<mxGeometry relative="1" as="geometry"/>`; ids unique; every label XML-escaped and emitted as plain text (no `html=1` in any cell style); no `link` attribute; flagged as hand-placed with a pointer to Arrange › Layout. The reference carries one fenced `xml` skeleton.

### Failure, edge cases & resilience

Owned by: T2

- Empty or unsupported Mermaid: the CLI exits 1 with "Error parsing Mermaid" and writes nothing → report the error.
- Malformed Mermaid: the CLI's parser is lenient and can exit 0 with a wrong diagram (a broken edge line became part of a node label) → the rubric self-check runs before conversion, and the label check after it catches a missing node.
- `architecture-beta` icons convert as image cells, not editable shapes → the reference notes it.

## Tasks

### T1: Fixture structure test is red on a missing skeleton and green on CLI-converted fixtures

**Depends on:** none
**Touches:** packs/architect/tests/skills/architect-diagram/test_drawio_fixtures.py, packs/architect/tests/skills/architect-diagram/testdata/*.drawio

**Tests:**
- New suite `test_drawio_fixtures.py`, standard library only (`xml.etree.ElementTree`, `re`, `pathlib`), parametrized over `testdata/*.drawio`, asserting the same-stem `.mmd` sibling plus every AC-0003 structural and link-safety property; fails loudly (not a silent skip) when any of the three named fixtures is missing. Covers AC-0003.
- One case reads `references/drawio-export.md`, requires exactly one fenced `xml` block, runs the same checks minus the sibling check, and asserts no cell style sets `html=1`. Covers AC-0004.
- One case reads the `text install-allowlist` block and the `SKILL.md` frontmatter boundaries. Covers AC-0007.
- The anchor-tag and `href=` matching in the link-safety check follows AC-0003; the AC-0005 mutation run includes the three control labels (`Metadata: store`, `a < b`, `x <and y`), which must pass.
- The AC-0004 and AC-0007 cases are red until T2 and T3; T1's commit marks neither `xfail`, so the red is visible until those tasks land in the same PR.
- Fixtures `flowchart-tb.drawio`, `sequence.drawio`, and `architecture-beta.drawio` are produced by the conversion command in Design from the existing same-stem `.mmd` files.

**Done when:** the suite passes for the three fixture cases and fails exactly the skeleton (AC-0004) and allowlist-plus-boundaries (AC-0007) cases; the AC-0005 mutation run, with every mutation red and all three control labels green, is recorded in the verification ledger.

### T2: The draw.io reference carries the full CLI recipe, a skeleton, and the install allowlist that pass T1

**Depends on:** T1
**Touches:** packs/architect/.apm/skills/architect-diagram/references/drawio-export.md

**Tests:**
- T1's skeleton case and the allowlist half of the AC-0007 case turn green.

**Done when:** every `test_drawio_fixtures.py` case passes except the AC-0007 case, whose allowlist assertion now passes and whose boundaries assertion stays red for T3.

### T3: The skill routes draw.io requests and saves the sibling under the existing path rules

**Depends on:** T2
**Touches:** packs/architect/.apm/skills/architect-diagram/SKILL.md, packs/architect/.apm/skills/architect-diagram/references/agentbundle-layout.md

**Tests:**
- T1's boundaries assertion turns green once the frontmatter carries `network_egress`.
- no stub (goal-based): description names draw.io as an opt-in output; step 8 admits `<stem>.drawio` beside the `.mmd` with the same checks and loads `references/drawio-export.md`.

**Done when:** `test_drawio_fixtures.py` passes in full; `grep -c "drawio-export.md" SKILL.md` and `grep -c "<topic-slug>.drawio" references/agentbundle-layout.md` (both under the skill directory) are each at least 1; `agentbundle catalogue lint --root . --deep` passes.

### T4: Evals cover the draw.io path and the unchanged default

**Depends on:** T3
**Touches:** packs/architect/.apm/skills/architect-diagram/evals/eval_queries.json, packs/architect/.apm/skills/architect-diagram/evals/evals.json

**Tests:**
- no stub (goal-based): AC-0001 and AC-0002 cases present; catalogue lint validates their shape.

**Done when:** `agentbundle catalogue lint --root . --deep` passes.

### T5: Guides and pack design state the draw.io export consistently

**Depends on:** T3
**Touches:** guides/architect/how-to/diagram-a-system.md, guides/architect/explanation/architect-diagram-skill-design.md, packs/architect/DESIGN.md, packs/architect/README.md

**Tests:**
- no stub (goal-based): guide validators pass; `grep -c "any other diagramming format" packs/architect/DESIGN.md` is 0 and `grep -c "Mermaid only for diagrams" packs/architect/DESIGN.md` is 0, so § 9 invariant 5 and § 2 principle 6 no longer forbid a derived export.

**Done when:** `tools/validate_guides.py`, `tools/check-guide-index.py`, and `tools/lint-guide-titles.py` exit 0.

### T6: Release surfaces read 0.15.18 and the catalogue verifies

**Depends on:** T1, T2, T3, T4, T5
**Touches:** packs/architect/pack.toml, packs/architect/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.d/*

**Tests:**
- no stub (goal-based): AC-0006 commands.

**Done when:** AC-0006 commands exit 0, `catalogue self-host --write` leaves no diff, `make lint-ruff lint-mypy` passes, and the live activation run's per-query results are in the verification ledger.

## Rollout

Ships with the next catalogue release; no flag, no infrastructure, no migration. Rollback is a revert of the PR.

## Risks

- The CLI's Mermaid converter changes between draw.io releases; the fixtures record the converting version in the ledger, and the reference names the minimum version.
- The required live run scores activation queries only; the AC-0002 behavior cases parse but stay unscored by a live judge.

## Changelog

- 2026-10-15: spec approved by eugenelim
- 2026-10-15: plan approved by eugenelim
