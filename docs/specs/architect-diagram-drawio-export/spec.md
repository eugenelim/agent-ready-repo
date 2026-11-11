# Spec: architect-diagram-drawio-export

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Contract:** none
- **Shape:** mixed

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

A user of the `architect-diagram` skill who asks for draw.io output gets an
editable `.drawio` file of the same diagram, saved beside its Mermaid source,
and a user who does not ask sees no change. When the draw.io desktop CLI is
missing, the skill offers one fixed package-manager install command for the
user's system and installs nothing without a clear yes; on a no, the user still
gets a `.drawio` file the agent transcribes from the saved Mermaid plus the
draw.io Insert › Mermaid steps.

## What Changes

- An opt-in draw.io export path in the skill procedure and description — `packs/architect/.apm/skills/architect-diagram/SKILL.md`
- A new reference covering CLI detection, the fixed install allowlist, conversion, output and link-safety checks, and the agent-written XML fallback — `packs/architect/.apm/skills/architect-diagram/references/drawio-export.md`
- `.drawio` as a permitted sibling of the saved `.mmd`, under the same path rules — `references/agentbundle-layout.md`
- Three `.drawio` fixtures converted by the real CLI from existing `.mmd` fixtures, and a standard-library test over them, the reference's XML skeleton, and its install allowlist — `packs/architect/tests/skills/architect-diagram/`
- Activation queries and behavior evals for the draw.io path — `evals/eval_queries.json`, `evals/evals.json`
- `network_egress` added to the skill's `metadata.boundaries`, because an approved install reaches a package registry — `SKILL.md` frontmatter
- The pack's "Mermaid only" invariant narrowed to "every diagram is authored in Mermaid; a draw.io file is derived from the saved Mermaid" — `packs/architect/DESIGN.md`
- User guides: a draw.io section in the how-to and a revised "Why Mermaid" explanation — `guides/architect/`
- architect 0.15.17 → 0.15.18 with a changelog fragment — `pack.toml`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.d/`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | The skill gains an opt-in output users invoke | `guides/architect/how-to/diagram-a-system.md` (new "Get a draw.io file" section); `packs/architect/README.md` capability row | architect pack maintainer | Guide validators pass; section names opt-in, install consent, fallback | Guide states the same behavior as the shipped skill |
| Decision rationale | Changes the documented "Why Mermaid" trade-off and a pack safety invariant | `guides/architect/explanation/architect-diagram-skill-design.md` § Why Mermaid; `packs/architect/DESIGN.md` §§ 2 (principle 6), 9 (invariant 5), and "Why Mermaid only" | architect pack maintainer | Both state Mermaid as the authored source and draw.io as an optional export derived from it | No surface still says the pack emits no other format |
| Current product truth | Skill behavior lives in the skill and its reference | `SKILL.md`, `references/drawio-export.md`, `references/agentbundle-layout.md` | architect pack maintainer | Fixture test, evals, catalogue lint | Shipped skill matches AC-0001 to AC-0007 |
| Release history | Version bump owes an entry | `docs/product/changelog.d/` fragment via `tools/changelog.py new` | release author | Fragment validates | Fragment names architect 0.15.18 and the draw.io export |
| Reusable learning | The CLI accepts malformed Mermaid and exits 0 | `references/drawio-export.md` output-check section | architect pack maintainer | Reference text plus eval assertion | — |

Current architecture, interface compatibility, operations, and maintainer procedure do not apply: the change adds no module, API, service, or maintainer workflow.

## Agent Rules

### Always do

- Keep Mermaid the default and the source of truth: a draw.io file is produced only when the user asks for draw.io, and only from a saved `.mmd` — by the CLI, or on the fallback path as a node-for-node, edge-for-edge transcription of that `.mmd`.
- Apply the existing save-step path rules unchanged to the `.drawio` sibling, surface both final paths before the first write, ask before replacing an existing `.drawio`, and report the path the CLI actually wrote.
- Limit what the skill runs to: the detected draw.io CLI (`--version` and the conversion command), an `xvfb-run -a` prefix on a headless Linux host, and, after a yes, exactly one command from the reference's install allowlist. Writes stay in the one confined save directory.
- Run every pack test with the standard library only; never invoke the draw.io CLI, a package manager, or the network from a test.

### Ask first

- Any change to the save step's confinement rules beyond admitting the `.drawio` sibling.
- Adding PNG, SVG, or PDF export, or reading a user-supplied `.drawio` file.
- Changing the version bump level from patch.

### Never do

- Never let the skill install software without the user's explicit yes, given after the exact command was shown; a yes covers only that command, and wording in the original request does not count as one. Never download an installer, compose a URL, or pipe anything into a shell.
- Never add a runtime dependency on another skill, plugin, MCP server, or Python package; the draw.io CLI stays an optional user-installed tool.
- Never add a new skill, script, or module boundary to the pack for this feature.

## Testing Strategy

- **Fixture, skeleton, and allowlist structure (AC-0003, AC-0004, AC-0005, AC-0007): TDD.** A standard-library test parses the shipped XML and the reference's allowlist block; a compressed, malformed, dangling-edge, or link-bearing file and an extra or network-fetching install line are compressible invariants a test reds on.
- **Skill behavior (AC-0001, AC-0002): goal-based check, exercised by the eval harness.** The behavior lives in agent-read prose; frozen eval cases with assertions are the mechanical judge, and `agentbundle catalogue lint --deep` validates their shape.
- **Live activation run: manual QA.** Before the PR opens, the headless activation run `agentbundle pack evals run --pack architect` runs on Claude Code and its per-query results for the architect-diagram queries, including the new draw.io ones, are recorded in the verification ledger.
- **Fixture provenance: manual QA.** The three fixtures are produced by running the draw.io desktop CLI on the repository's own `.mmd` files; the command and exit code are recorded in the verification ledger.
- **Release surfaces (AC-0006): goal-based check.** `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .` pass, and the changelog validator accepts the fragment.

## Acceptance Criteria

- [x] **AC-0001.** `evals/eval_queries.json` contains at least two `should_trigger: true` queries asking for draw.io output and one `should_trigger: false` query asking to edit an existing `.drawio` file in draw.io without drawing anything.
- [x] **AC-0002.** `evals/evals.json` contains four new cases, each with assertions that a judge can score against the transcript: (a) CLI present: both final paths are surfaced before the first write, the `.mmd` is saved first, an existing `.drawio` is not replaced without a yes, the conversion runs with `-x -f xml -u` on the saved file, and the output passes the structure and link-safety checks; (b) CLI absent: the skill shows one allowlisted install command for the user's OS, waits, installs nothing without a yes, and on a no writes an uncompressed `.drawio` transcribed from the saved `.mmd`, with every label XML-escaped and no cell style setting `html=1`, runs the same output check on it before presenting it, and gives the Insert › Mermaid steps; in (a) and (b) every command the skill runs is the detected CLI, an `xvfb-run -a` prefix, or one allowlisted install command; (c) a plain diagram request produces Mermaid only, with no draw.io offer and no `.drawio` file; (d) a draw.io request in chat-only or repository-handoff mode writes no file, and the handoff lists the `.drawio` as a needed write.
- [x] **AC-0003.** `packs/architect/tests/skills/architect-diagram/testdata/` holds `.drawio` fixtures converted from `flowchart-tb.mmd`, `sequence.mmd`, and `architecture-beta.mmd`, and the fixture test asserts for every `.drawio` there: a same-stem `.mmd` sibling exists; root element `mxfile`; each `diagram` holds an inline `mxGraphModel` (uncompressed); at least one vertex; unique cell ids; every `source` or `target` an edge carries names an existing cell (CLI sequence output may leave one end of a message edge floating); the link-safety rule — no element carries a `link`, `href`, or `xlink:href` attribute; no `value`, `label`, or `tooltip` attribute, case-folded with control characters removed, matches an anchor tag (`<a` followed by whitespace, `/`, or `>`) or an `href` attribute (`href` followed by optional whitespace and `=`); and every `image=` entry inside a `style` value, with whitespace and control characters removed, starts with `data:image/`.
- [x] **AC-0004.** The same test extracts the single fenced `xml` block from `references/drawio-export.md` and applies every AC-0003 assertion except the `.mmd` sibling check, and asserts every skeleton edge has both a `source` and a `target` and no skeleton cell style sets `html=1`, so the shipped fallback skeleton parses, passes the link-safety rule, and renders labels as plain text.
- [x] **AC-0005.** Every AC-0003 assertion reds when its property is broken: a mutation run (missing `.mmd` sibling, compressed diagram, no vertex, duplicate id, dangling edge, `link` attribute, `<a href` in a label, a style `image=` entry of `java` + tab + `script:alert(1)`, a skeleton edge without `source`) fails the test, while control mutations adding the labels `Metadata: store`, `a < b`, and `x <and y` pass; recorded in the verification ledger.
- [x] **AC-0006.** `pack.toml`, `.claude-plugin/plugin.json`, and the architect entry in `.claude-plugin/marketplace.json` read `0.15.18`; a changelog fragment for architect 0.15.18 exists; `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .` exit 0.
- [x] **AC-0007.** The fixture test reads the one block in `references/drawio-export.md` fenced as `text install-allowlist` and asserts its non-empty lines are exactly `brew install --cask drawio`, `winget install -e --id JGraph.Draw`, and `sudo snap install drawio`; it also asserts `SKILL.md` frontmatter `metadata.boundaries` is exactly `[filesystem_read_untrusted, filesystem_write, network_egress]`.

## Follow-ons

none

## Assumptions

none
