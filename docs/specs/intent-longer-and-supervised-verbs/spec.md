# Spec: intent-longer-and-supervised-verbs

- **Status:** Archived
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0107 (D1, D2, D6); ADR-0140 (D2, D3, D5, and D4 as ADR-0145 D3 restates it); ADR-0145; ADR-0111 (D8, as its Errata reads); RFC-0067 (clean retire)
- **Brief:** brief:verb-mode-skills-and-slice-handover
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

## Outcome

A team shaping product work reaches every shaping step through two verb-mode skills that
show where they are and offer the next step: `intent` for one intent's lifecycle, and
`initiative` for the initiative-scale longer route, while `discovery-loop` runs its gates
on their modes and hands off through `work-intake`. Success means held-out shaping
requests trigger within 3 percentage points of how often they triggered the skills the two
replace, and no operative surface names those skills.

## What Changes

- `intent` gains the `ground` mode (from `frame-domain`), and its `de-risk` mode gains
  `plan-validation`'s procedure as a validation-plan section.
- A new `initiative` skill lives in `packs/product-engineering/.apm/skills/initiative/`,
  with six verb modes, each procedure in `references/<mode>.md`:
  - `situate` from `frame-situation`;
  - `find` from `identify-opportunities`;
  - `diverge` from `diverge-solutions` (initiative options) and `explore-options`
    (candidate product shapes);
  - `bet` from `place-bet`;
  - `map` from `map-capabilities`;
  - `canvas` from `lean-canvas`.
- The source skills' assets and examples move under the skill that holds their mode.
  Their eval queries and cases merge into that skill's `evals/`.
- `intent`'s lifecycle map draws the longer route through `initiative` modes and
  `intent de-risk`, the supervised route's gate calls, and `initiative canvas` as an
  off-route aid. Route mode's longer route starts at `initiative situate`.
- `initiative/SKILL.md` lists the longer route in the same order.
- `tools/add-rendering-directives.py` gives `intent` and `initiative` one shape-directive
  entry each, in place of the nine sources' entries.
- The `intent` and `initiative` descriptions each fit in 1024 characters.
- The nine source directories are removed:
  - `frame-situation`, `identify-opportunities`, `diverge-solutions`, `explore-options`;
  - `plan-validation`, `place-bet`, `map-capabilities`, `frame-domain`, `lean-canvas`.
- `discovery-loop`:
  - Its description is trimmed.
  - Its gate table, references, and assets name `initiative diverge`, `intent ground`,
    and `intent de-risk`.
  - Its opening section, and `discovery-lead`'s description and G3 paragraphs, say the
    hand-off goes through `work-intake`.
  - Its requirements ingest names `author-delivery-brief create`, which matches that
    skill's rule that `continue` takes only an existing repository brief.
  - Its evals gain negatives that send one standalone discovery artifact to `intent` or
    `initiative`.
- `run-a-discovery.md` says the loop hands off through `work-intake`.
- `ground`'s procedure no longer calls `discovery-loop` "unbuilt".
- Core's `workspace-status` sends the `strategy` entry type to `initiative`. The
  `agentbundle` mirror and `workspace_mcp.py` follow, and so does `work-loop`'s
  shaping-item guard.
- Every other operative caller moves to `intent <mode>` or `initiative <mode>`:
  - Core's `new-spec` contract reference;
  - `desk-research`, `product-strategy`, and `experience-design`;
  - tools, tests, guides, site pages, pack docs, the skill census, and the live
    architecture and journey records;
  - the two Draft specs that name a retired skill.
- ADR-0145 is accepted once the evidence passes; RFC-0107 then gains an erratum that
  points D1 at it. The brief's Outcome, success metric, mode map, and `discovery-loop`
  line name both skills.
- Versions: `product-engineering` 2.0.0. Every other edited pack takes a patch, and
  `agentbundle` follows its own rule.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | Guides tell adopters which skill and mode to call for each shaping step | `guides/` files that name the retired skills; the regenerated lifecycle graphic | eugenelim | Edited guides; regenerated SVG | AC-0016, AC-0018, AC-0034 pass |
| Current product truth | Pack and site pages state the skill roster | `packs/product-engineering/{README,JOURNEY,DESIGN}.md`, `web/src/content/` | eugenelim | Edited pages | AC-0016 passes |
| Current architecture | The lifecycle flow names shaping skills | `docs/architecture/lifecycle-flow.md` | eugenelim | Edited flow | AC-0016 passes |
| Decision rationale | The shaping entry points split across two skills | ADR-0145; RFC-0107 § Errata; the brief | eugenelim | The accepted ADR, a dated erratum, and the edited brief | AC-0044, AC-0046, AC-0047 pass |
| Release history | A breaking removal needs an adopter action | `docs/product/changelog.md`, `packages/agentbundle/CHANGELOG.md` | eugenelim | Entries for each released pack and the package | AC-0030, AC-0031, AC-0032, AC-0033 pass |

## Agent Rules

### Always do

- Move each source procedure into its mode reference unchanged, except for the edits
  the first Ask-first item exempts.
- Follow `packs/AGENTS.md` and `packages/AGENTS.md` for version bumps, eval harness
  updates, and self-host.
- Record in `notes/verification-ledger.md` every eval case or fixture dropped, every
  test assertion replaced or dropped, and why.

### Ask first

- Changing what any procedure does. These edits are exempt:
  - retargeting skill names and paths, including "this skill" to "this mode";
  - adding the `Stage:` line and the `## Next` section this spec requires;
  - removing a readiness note that fires only when a now-folded skill is absent, since
    a mode of `intent` or `initiative` cannot be absent;
  - deleting the two stale statements: `place-bet`'s "until `diverge-solutions` ships"
    note, and `frame-domain`'s "(which is unbuilt)";
  - joining `diverge`'s two procedures, and `de-risk`'s two, with one entry rule each
    that picks the procedure;
  - dropping a source's managed output-rendering block and shape-directive lines,
    since each skill's `SKILL.md` carries one managed block.

  The ledger lists each exempt edit by file.
- Changing any probe-candidate description after the post-fold probe has run.
- Editing a frozen record (a shipped spec, or an accepted RFC or ADR) beyond an
  erratum.
- Retargeting a name inside `packs/core/tests/skills/work-loop/fixtures/corpus/`.
- Renaming or deleting a guide page.

### Never do

- Add an alias, shim, or stub directory for a retired name.
- Give route mode state, retries, or gate control, or give `initiative` a route mode.
- Add `allowed-tools` to `intent` or `initiative`, or a boundary beyond
  `filesystem_write` and `filesystem_read_untrusted`.
- Let the `de-risk` mode, including its validation-plan section, dispatch
  `adversarial-reviewer`.
- Fold `align-value-stream`, `discovery-loop`, or `ux-writing`, or change `work-intake`'s
  modes.
- Edit `.claude/` or `.agents/` projections by hand.
- Add a top-level directory or a new dependency.

## Testing Strategy

- **Skill structure (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0011, AC-0012, AC-0036, AC-0039, AC-0041, AC-0042, AC-0043):**
  goal-based. `test_intent_skill_structure.py`, an `initiative` structure test, and
  their siblings decide these, and the directive tool's `--check` run decides AC-0036's
  tool half.
- **Lifecycle orientation (AC-0007, AC-0008, AC-0009):** goal-based. The structure tests
  pin the map, each `Stage:` line, and each `## Next` section's offers. They compare the
  longer route in both skills with `situate`'s entry-point sequence.
- **Discovery loop (AC-0013, AC-0014, AC-0015, AC-0038, AC-0040):** goal-based.
  `test_intent_triad_execution_wiring.py` is extended for the pack's own files. AC-0015's
  guide file is checked by a roster test, and AC-0040's owners by the ledger.
- **Faithful move (AC-0037):** goal-based. A recorded diff decides it, because a
  procedure moved with a hidden change passes every structural test.
- **Retirement sweep and callers (AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0048, AC-0049):**
  goal-based, except AC-0017, which is TDD: `tools/test_workspace_status.py`'s
  expectation changes first, then the engine and its mirror.
- **Eval carry-over (AC-0021, AC-0022, AC-0023, AC-0045):** goal-based. Checks run over the merged
  eval files and the ledger.
- **Mode routing (AC-0024, AC-0025, AC-0026, AC-0027, AC-0028):** bounded
  routing-classification evidence.
  - The eval runner cannot assert a mode, so a cold classification probe is the only
    mode evidence in this slice.
  - This departs from RFC-0107 Experiment's bar, which asks for mode accuracy within 3
    percentage points. eugenelim approved the departure for this slice on 2026-10-11.
- **Activation (AC-0029):** a headless `pack_evals` run over a fresh held-out set,
  comparing trigger rates before and after the fold. This is RFC-0107 Experiment's
  release gate.
- **Guided walks (AC-0010):** manual QA, recorded in the ledger.
- **Release and decision records (AC-0030, AC-0031, AC-0032, AC-0033, AC-0034, AC-0035, AC-0044, AC-0046, AC-0047):**
  goal-based. Changelog entries, an install observation, version fields, lint and verify
  runs, a regenerated graphic, the erratum, the brief text, and the ADR status decide
  these.

## Acceptance Criteria

### The `intent` and `initiative` skills

- [ ] **AC-0001.** `intent/SKILL.md` has, in order, the sections `## When to invoke`,
      `## The intent lifecycle`, `## Route mode`, and `## Modes`. `## Modes` holds one
      table with exactly five rows, in this order: `route`, `frame`, `de-risk`,
      `decompose`, `ground`. *(goal-based)*
- [ ] **AC-0043.** `initiative/SKILL.md` has, in order, the sections `## When to invoke`,
      `## The initiative route`, and `## Modes`, and no route mode. `## Modes` holds one
      table with exactly six rows, in this order: `situate`, `find`, `diverge`, `bet`,
      `map`, `canvas`. *(goal-based)*
- [ ] **AC-0002.** Each verb mode's procedure is in `references/<mode>.md` of the skill
      whose `## Modes` table lists it, and its table row names that file. *(goal-based)*
- [ ] **AC-0003.** The `intent` description is at most 1024 characters, and names
      `` `frame` ``, `` `de-risk` ``, `` `decompose` ``, and `` `ground` `` in backticks.
      *(goal-based)*
- [ ] **AC-0004.** The `intent` description names `intake-intent`, `new-spec`,
      `discovery-loop`, and `initiative`, each in backticks. *(goal-based)*
- [ ] **AC-0041.** The `initiative` description is at most 1024 characters. It names
      `` `situate` ``, `` `find` ``, `` `diverge` ``, `` `bet` ``, `` `map` ``, and
      `` `canvas` `` in backticks, and names `intent` and `discovery-loop` in backticks.
      *(goal-based)*
- [ ] **AC-0005.** `intent`'s `## Route mode` names exactly three routes, each with its
      first step: short `intent frame`, longer `initiative situate`, supervised
      `discovery-loop`. It names three out-of-stage owners, `bug-fix`, `work-intake`, and
      `architect-design`, and no other hyphenated skill name. Its text matches none of the
      stems `writ`, `save`, `saving`, `creat`, `remember`, `retr(y|ie)`, `gate`, `record`,
      `persist`, `updat`, `append`, `stor`, and `edit`, matched case-insensitively as
      `\b<stem>`. *(goal-based)*
- [ ] **AC-0006.** Neither `intent` nor `initiative` declares `allowed-tools` in its
      frontmatter, and each one's boundaries are exactly `filesystem_write` and
      `filesystem_read_untrusted`. *(goal-based)*
- [ ] **AC-0007.** `intent`'s `## The intent lifecycle` lays out three routes as ordered
      stages, and marks each stage as an `intent` mode, an `initiative` mode, or a
      separate skill:
      - **short:** `frame`, `de-risk`, `decompose`, then the hand-off to build through
        `work-intake`. The `shaping-reviewer` well-formedness check follows `frame`, the
        advisory `adversarial-reviewer` read comes before `de-risk`, and the
        `author-delivery-brief` review gates for a brief, or the `new-spec` review gates
        for a spec, follow the hand-off;
      - **longer:** `initiative situate`, `initiative find`, `initiative diverge`,
        `intent de-risk`, `initiative bet`, `initiative map`, then the hand-off through
        `work-intake`;
      - **supervised:** `discovery-loop`, with the modes it calls: `intent frame` at G0,
        `intent de-risk` and `intent decompose` at G1, `initiative diverge` at the
        divergence stage, `intent ground` at G1.5, `intent decompose` at G3, and
        `intent de-risk`'s validation-plan section when a plan-tree node ratifies. The map
        adds no gate or stage to the loop.

      Outside the three routes, the section names `initiative canvas` as an optional aid
      offered after `initiative map`. `initiative/SKILL.md`'s `## The initiative route`
      lists the same six longer-route stages in the same order. A pack test compares both
      lists with the sequence `initiative/references/situate.md` states in its
      entry-point step, with its validate step shown as `intent de-risk`. *(goal-based)*
- [ ] **AC-0008.** Each of the ten mode references opens with one `Stage:` line. The line
      names its skill, each route in `## The intent lifecycle` that includes the mode,
      with its position on that route, and each route that does not use it. `canvas`'s
      line says it sits on no route. *(goal-based)*
- [ ] **AC-0009.** Each of the ten mode references ends with a `## Next` section.
      - Its first line says that when `discovery-loop` or its `discovery-lead` agent
        called the mode, control returns to the loop's next gate and no offer is made.
      - It offers at most three options per outcome. Every offered skill or mode is a
        stage or review on the lifecycle map, or `initiative canvas`, the off-route aid
        the map names.
      - `frame` and `decompose` keep their slice 1 offers.
      - The other modes offer, with the first one recommended:

      | Mode | Outcome | Offers |
      | --- | --- | --- |
      | `situate` | entry point chosen | the mode for that entry: `initiative find`, `initiative diverge`, or `initiative bet` |
      | `find` | opportunities ranked | `initiative diverge` |
      | `diverge` | options written | `intent de-risk`, then `initiative bet` |
      | `de-risk` | survive | `intent decompose` (short route) and `initiative bet` (longer route), recommending the route the conversation shows, or asking when none shows |
      | `de-risk` | kill | `intent frame` |
      | `de-risk` | validation plan written | `intent de-risk` once the field results return |
      | `bet` | bet placed | `initiative map` |
      | `map` | map written | the hand-off through `work-intake`, then `initiative canvas` |
      | `ground` | artifacts written | `intent de-risk`, then the hand-off through `work-intake` |
      | `canvas` | brief written | the hand-off through `work-intake` |

      *(goal-based)*
- [ ] **AC-0010.** Headless walks, recorded verbatim in `notes/manual-qa-walks.md`, show:
      - one longer-route walk that starts with an `intent` route reply selecting the
        longer route, then runs `situate`, `find`, `diverge`, `de-risk`, `bet`, and `map`
        on one sample signal;
      - one standalone `ground` reply and one standalone `canvas` reply;
      - one `diverge` reply to a request for candidate product shapes, which runs the
        shapes procedure, and one `de-risk` reply to a request for a validation plan,
        which runs the validation-plan section. The ledger names the procedure each ran;
      - in every reply, the user's stage named on the first line, and the next options
        offered as AC-0009 lists them;
      - no reply that starts the next mode before the user chooses it.

      *(manual QA)*
- [ ] **AC-0011.** The files under each skill's `references/`, `assets/`, and `examples/`
      are exactly these, and no two in one skill share a path:
      - `intent`: the slice 1 files, plus `references/ground.md` and
        `examples/example-assistant.md`;
      - `initiative`: `references/situate.md`, `find.md`, `diverge.md`, `bet.md`,
        `map.md`, and `canvas.md`; `assets/opportunity-assessment-template.md` and
        `capability-map-template.md`; `examples/signal-to-finding.md`,
        `opportunity-assessment-worked-example.md`, `opportunity-to-options.md`,
        `placing-a-bet.md`, `ini-003-ai-developer-brief.md`, `acme-crm/bet.md`,
        `acme-crm/capability-map.md`, `bloom-marketplace/bet.md`, and
        `bloom-marketplace/capability-map.md`.

      *(goal-based)*
- [ ] **AC-0012.** `intent/references/de-risk.md`, including its validation-plan section,
      names `adversarial-reviewer` only in the bullet that refuses to dispatch it, and
      `test_de_risk_intent_reviewer_boundary.py` passes. *(goal-based)*
- [ ] **AC-0042.** A case-sensitive search for `(?<![\w-])intent (situate|find|diverge|bet|map|canvas)\b`
      and for `(?<![\w-])initiative (frame|de-risk|decompose|ground)\b` finds no match in
      any file under `intent/` or `initiative/`, or in any surface AC-0016 searches.
      `initiative` has no route mode, so the phrase "initiative route" is not a mode name
      and is not searched. *(goal-based)*
- [ ] **AC-0036.** No file under `intent/references/` or `initiative/references/` contains
      the `agentbundle:output-rendering:start` marker. `tools/add-rendering-directives.py`'s
      skill map has an `intent` entry with the narrative, key-value, and tree shapes and an
      `initiative` entry with the table, narrative, and key-value shapes, and each
      `SKILL.md` carries the directive lines its entry produces.
      `python3 tools/add-rendering-directives.py --check` exits 0 or 1 and prints no line
      starting `output-rendering: packs/product-engineering/.apm/skills/intent/SKILL.md:`
      or `output-rendering: packs/product-engineering/.apm/skills/initiative/SKILL.md:` on
      stdout or stderr. Drift it reports for other skills is out of scope, and this change
      leaves those skills' `SKILL.md` files byte-identical. *(goal-based)*
- [ ] **AC-0037.** Before any source is deleted, the ledger records a named base commit
      and a diff of each of the nine source bodies at that base against its mode
      reference, and attributes every differing hunk to an exempt edit listed by file.
      Before the branch is pushed, and right after `git fetch origin main`, the ledger
      records the fetched commit, and `git diff <recorded base> <fetched commit>` over
      the nine source directories is empty, or the diff is recorded again against the
      fetched commit with every hunk attributed. *(goal-based)*

### `discovery-loop`

- [ ] **AC-0013.** `discovery-loop/SKILL.md`'s gate table and `discovery-lead.md`'s gate
      walk name `initiative diverge` at the divergence stage and `intent ground` at G1.5,
      and `discovery-loop/assets/plan-tree.md`'s validation step names `intent de-risk`
      as the source of a ratified node's validation hook. None of the three files gains
      a gate or stage row. *(goal-based)*
- [ ] **AC-0014.** `discovery-loop`'s description is at most 600 characters, names
      `work-intake` as its G3 hand-off, and does not contain `work-loop`. *(goal-based)*
- [ ] **AC-0015.** With each file's whitespace collapsed to single spaces, no sentence in
      `discovery-loop/SKILL.md`, `discovery-lead.md`, or
      `guides/product-engineering/how-to/run-a-discovery.md` matches
      ``\bhand(s|ed|ing)?\b[^.]*\bto `?work-loop``, case-insensitively. The test also
      asserts, as fixed cases, that the pattern matches "hand the approved delivery item
      to `work-loop`" and does not match "hands off through `work-intake`".
      *(goal-based)*
- [ ] **AC-0038.** `discovery-loop/references/requirements-crosswalk.md` does not
      contain `author-delivery-brief continue`, and names `author-delivery-brief create`
      for the requirements ingest. `discovery-loop/SKILL.md` § Folding in traditional
      requirements capture does the same. *(goal-based)*
- [ ] **AC-0039.** `intent/references/ground.md` does not contain `unbuilt`.
      *(goal-based)*
- [ ] **AC-0040.** `discovery-loop/evals/eval_queries.json` holds at least two negative
      queries that each ask for one standalone discovery artifact: at least one domain
      grounding, which the ledger owns to `intent`, and at least one set of candidate
      product shapes, which the ledger owns to `initiative`. *(goal-based)*

### Retirement

- [ ] **AC-0016.** The nine source directories are absent. A case-sensitive search for
      the nine names finds no match in:
      - `packs/`, `guides/`, `web/src/`, `tools/`, `tests/`, `packages/`, and
        `contracts/`;
      - `workspace.toml`;
      - `docs/architecture/`, `docs/product/journeys/`, `docs/guides/`,
        `docs/product/workspace-toml-deps.md`, and `docs/product/initiatives/_template.md`;
      - `docs/specs/guide-invocation-outcome-coverage/` and
        `docs/specs/how-to-sample-output-coverage/`;
      - the root `AGENTS.md`, `ARCHITECTURE.md`, `README.md`, and `docs/CHARTER.md`.

      Only four kinds of match are allowed:
      - lines inside a test-module constant named `RETIRED_SHAPING_SKILLS`;
      - files under `packs/core/tests/skills/work-loop/fixtures/corpus/`;
      - a match inside the directory name of a `docs/specs/` spec whose `Status` reads
        `Shipped`, such as `m2-place-bet`;
      - a link or path to the guide pages
        `guides/product-engineering/how-to/identify-opportunities.md`,
        `guides/product-engineering/how-to/map-capabilities.md`, and
        `guides/product-engineering/how-to/create-a-lean-canvas.md`.

      *(goal-based)*
- [ ] **AC-0017.** `workspace-status` maps the `strategy` entry type to `initiative`. The
      engine under `packs/core`, its mirror under `packages/agentbundle`, and
      `workspace_mcp.py` agree, and `tools/test_workspace_status.py` passes. *(TDD)*
- [ ] **AC-0048.** The engine surfaces that state where the `strategy` entry type goes name
      `initiative`: `workspace-status/SKILL.md`, `work-loop/SKILL.md`'s shaping-item
      guard, `guides/core/explanation/two-room-model.md`,
      `guides/core/tutorials/your-first-workspace.md`, and
      `docs/product/workspace-toml-deps.md`. *(goal-based)*
- [ ] **AC-0049.** A case-insensitive search over the surfaces AC-0016 searches, for lines
      that contain the backticked token `` `intent` `` and any of `strategy`, `situate`,
      `longer route`, `opportunit`, `capability map`, `lean canvas`, `product shape`, `OKR`,
      or the word `bet`, finds only lines the ledger lists with one of three dispositions:
      - it names `initiative` or an `initiative` mode for that work;
      - it keeps `intent` because the work is one of `intent`'s own modes, with the
        reason stated;
      - it keeps `intent` because the line uses it as the artifact's name, a typed-pointer
        prefix, a reviewer mode, or a historical record, not as where work goes, with the
        reason stated.

      The ledger states each line's disposition and reason.
      `guides/product-strategy/how-to/route-it-to-work.md`'s route for queued gap entries,
      and `run-okr-cascade`'s PE-pack diagnostic in its `SKILL.md`,
      `references/cross-pack-routing.md`, and `evals/evals.json`, name `initiative`.
      *(goal-based)*
- [ ] **AC-0018.** Each `guides/` page that named a retired skill as the skill to invoke
      names the matching `intent <mode>` or `initiative <mode>` instead, and
      `python3 tools/lint-guidebook-steps.py guides/product-engineering` passes.
      *(goal-based)*
- [ ] **AC-0019.** `[pack.evals].skills` in `packs/product-engineering/pack.toml` lists
      `intent`, `initiative`, `align-value-stream`, `discovery-loop`, and `ux-writing`,
      and every name it lists has a directory under `.apm/skills/`. *(goal-based)*
- [ ] **AC-0020.** The `product-engineering` integration that named `map-capabilities`
      reads `consumers = ["skill:intent", "skill:initiative"]`, and the one that named
      `frame-domain` reads `consumers = ["skill:intent"]`. *(goal-based)*

### Evals and routing evidence

- [ ] **AC-0021.** Every distinct query from the `explore-options` query file is in
      `initiative/evals/eval_queries.json`, and every distinct query from the
      `plan-validation` and `frame-domain` query files is in
      `intent/evals/eval_queries.json`.
      - The ledger labels each carried query with its owner.
      - A query whose owner is a mode of the skill whose file it lands in is positive and
        carries a `mode` key naming that mode.
      - Every other query, including one owned by a mode of the other skill, is negative
        and carries no `mode` key.
      - No query appears twice in one file.

      *(goal-based)*
- [ ] **AC-0022.** `initiative/evals/eval_queries.json` holds at least three positive
      queries for each of `situate`, `find`, `bet`, `map`, and `canvas`, and for `diverge`
      at initiative altitude. Each skill's file holds at least four negative queries
      owned in the ledger by the other skill, and the two files together hold at least
      six negatives owned by a named skill that is neither. *(goal-based)*
- [ ] **AC-0045.** In each skill's query file, every positive carries a `mode` key naming
      one of that skill's own modes, and every query the ledger owns to the other skill is
      negative. *(goal-based)*
- [ ] **AC-0023.** Each `frame-domain` `evals/evals.json` case and `evals/files/` fixture
      is in `intent/evals/` or listed in the ledger with its drop reason. *(goal-based)*
- [ ] **AC-0024.** `notes/routing-classification-evidence.md` records the 24 pre-fold
      classifications of 2026-10-11 as a recorded baseline that gates nothing, and one
      scored post-fold attempt for the two-skill fold: the 24 cases, three runs each, on
      one byte-identical candidate set.
      - **No retries:** no run inside a scored attempt is repeated or dropped.
      - **New attempt:** a new scored attempt starts only after a recorded AC-0025 or
        AC-0029 failure, a dated ledger entry recording eugenelim's choice to revise, and
        a change to at least one candidate description. The attempt it replaces, and that
        attempt's post-fold activation run, become unscored history, as do the one-skill
        attempts 1 to 3.

      The expected post-fold selections are:

      | Cases | Post-fold |
      | --- | --- |
      | SI1, SI2 (raw signal) | `initiative` (`situate`) |
      | FI1, FI2 (job mapping) | `initiative` (`find`) |
      | DV1, DV2 (initiative options; product shapes) | `initiative` (`diverge`) |
      | VP1, VP2 (validation plan) | `intent` (`de-risk`) |
      | BT1, BT2 (bet) | `initiative` (`bet`) |
      | MP1, MP2 (capability map) | `initiative` (`map`) |
      | GR1, GR2 (domain grounding) | `intent` (`ground`) |
      | CV1, CV2 (lean canvas) | `initiative` (`canvas`) |
      | F1, D1, C1, R1 | `intent` (`frame`, `de-risk`, `decompose`, `route`) |
      | S1, I1, N1, A1 | `discovery-loop`, `intake-intent`, `new-spec`, `align-value-stream` |

      *(bounded routing-classification evidence)*
- [ ] **AC-0025.** Each of the 24 post-fold cases passes when all three of its runs match
      AC-0024's table in skill and mode, and at least two of the three are at high
      confidence. A failing case stops the slice before any source directory is deleted,
      and eugenelim decides whether to revise a candidate description under the Ask-first
      rule or to end the slice. *(bounded routing-classification evidence)*
- [ ] **AC-0026.** In each world, the probe's candidate set is every `product-engineering`
      skill installed in that world, plus `intake-intent`, `new-spec`, `bug-fix`, and
      `architect-design`. The note records each candidate description verbatim once per
      world or attempt, each case's prompt and expected selection, and each run's selected
      skill, mode, and confidence. *(bounded routing-classification evidence)*
- [ ] **AC-0027.** The `intent`, `initiative`, and `discovery-loop` descriptions ship
      byte-identical to their text in the candidate set of the scored attempt that passed
      AC-0025. *(bounded routing-classification evidence)*
- [ ] **AC-0028.** The note states that it is a classification proxy, not a `Skill`
      activation event, and that neither one pre-fold run nor three post-fold runs per
      case establishes recall or repeatability. *(bounded routing-classification evidence)*
- [ ] **AC-0029.** A fresh held-out set has 60 positive and 12 negative queries. It shares
      no query with the held-out set of 2026-10-11, and the probe sees none of them.
      - **Positives:** five for each of twelve groups: `situate`, `find`, `diverge`
        initiative options, `diverge` product shapes, `de-risk` validation plans, `bet`,
        `map`, `ground`, `canvas`, `frame`, `de-risk` assumption tests, and `decompose`.
      - **Negatives:** two each owned by `intake-intent`, `new-spec`, `discovery-loop`,
        `align-value-stream`, `bug-fix`, and `architect-design`.
      - **Runner:** `pack_evals` headless, three runs per query, on Claude Code. It also
        runs on Codex if a Codex detector ships before this check.
      - **Worlds:** the pre-fold world is the base commit the post-fold world is built
        from. Each world is a projection outside every repository holding that world's
        `product-engineering`, plus `core` and `architect`. Each run passes
        `--setting-sources project,local`. The ledger records the skills the host listed
        in each world.
      - **Errors:** every query ends with zero errored runs in both worlds. An errored
        query is re-run before scoring.
      - **Positive trigger rate:** the mean of each positive's `trigger_rate`, measured
        against its owning source before the fold and against the skill that holds its
        mode after it. The post-fold rate is no more than 3 percentage points below the
        pre-fold rate.
      - **False-trigger rate:** the mean, over the negatives, of the share of runs in
        which `intent`, `initiative`, or any of the nine sources fired, read from each
        run's fired skills. The post-fold rate is no more than 3 percentage points above
        the pre-fold rate.
      - **`discovery-loop`:** its `evals/eval_queries.json` as it stands before this
        change runs unchanged in both worlds. Every query that `pack_evals` marks passed
        in the pre-fold world is also marked passed in the post-fold world.
      - **Held-out set:** it shares no query with any source eval file or with either
        skill's `evals/eval_queries.json`. The ledger records the hash of each candidate
        description this change edits before the set is written, and the hash of each
        revised description before its new scored attempt, and each scored attempt's
        candidate descriptions match one of those recorded hashes. No held-out query, and no run
        of five consecutive words from one, appears in any candidate description; words
        are whitespace-split tokens, compared lowercased with punctuation stripped.

      If any bound fails, nothing is deleted. eugenelim chooses one of three paths:
      - split the weakest mode back out;
      - revise a candidate description under the Ask-first rule, then make a new scored
        attempt under AC-0024 and a new post-fold run. The ledger states beside the
        re-measured result that held-out misses informed the revision;
      - end the slice.

      Each scored attempt admits exactly one post-fold run, and re-running its errored
      queries is the only exception. The run on the descriptions of the scored attempt
      that passed AC-0025 is the one this criterion judges. *(activation)*

### Release and decision records

- [ ] **AC-0030.** `product-engineering`'s `pack.toml` and `plugin.json` both read
      `2.0.0`. Every other pack whose `.apm/` content this change edits has a patch bump.
      `packages/agentbundle` follows `packages/AGENTS.md`. *(goal-based)*
- [ ] **AC-0031.** `docs/product/changelog.md` has a `product-engineering` 2.0.0 entry
      with a `### Removed` section. That section names each retired skill with its
      replacement skill and mode, and gives the adopter step for a stale installed
      directory that matches the install-then-upgrade behavior recorded in the ledger.
      *(goal-based)*
- [ ] **AC-0032.** The Core entry and the `agentbundle` entry in
      `docs/product/changelog.md`, and `packages/agentbundle/CHANGELOG.md`, each say the
      `strategy` dispatch names `initiative` and needs `product-engineering` 2.0.0 or
      later. The newest Core entry sits directly under `[Unreleased]`. *(goal-based)*
- [ ] **AC-0033.** The 2.0.0 entry names the hosts the activation run measured, states
      that Cursor, Copilot, and Gemini CLI were not measured, states that mode accuracy
      rests on a classification probe, and names every pre-fold classification that
      missed its expected pre-fold selection, the `pre` value in `notes/probe-cases.json`,
      or fell below high confidence. *(goal-based)*
- [ ] **AC-0034.** Re-running `tools/render-lifecycle-graphics.py` leaves
      `guides/_shared/explanation/the-operating-model-full-map.svg` unchanged.
      *(goal-based)*
- [ ] **AC-0035.** `agentbundle catalogue lint --root . --deep` and
      `agentbundle catalogue verify --root .` pass after self-host. *(goal-based)*
- [ ] **AC-0047.** ADR-0145's `Status` reads `Accepted`, and `docs/adr/README.md`'s row for
      it says so. The ledger's dated sign-off entry comes after the entries recording a
      passing AC-0025 and AC-0029 result, and before the entries recording the RFC-0107
      erratum, the brief edit, and the deletion of any source directory. ADR-0140's
      `Superseded in part: ADR-0145 D1` mirror predates acceptance because the ADR shape
      lint requires both records to carry the relation from the moment ADR-0145 exists.
      *(goal-based)*
- [ ] **AC-0044.** `docs/rfc/0107-verb-mode-shaping-and-intake-with-slice-handover.md`
      carries a dated, approver-signed `## Errata` entry stating that ADR-0145 supersedes
      ADR-0140 D1 in part, so the shaping modes span `intent` and `initiative` rather than
      one skill. *(goal-based)*
- [ ] **AC-0046.** `docs/product/briefs/verb-mode-skills-and-slice-handover.md` matches
      ADR-0145:
      - its Outcome and Scope say shaping runs through `intent` and `initiative`, not one
        `intent` skill;
      - its success metric names four skills: `intent`, `initiative`, `discovery-loop`,
        and `align-value-stream`;
      - its mode map assigns each of the ten verb modes and route mode to the skill
        AC-0001 and AC-0043 give it;
      - its eval lines send `frame-intent`'s, `de-risk-intent`'s, `decompose-intent`'s,
        `plan-validation`'s, and `frame-domain`'s queries to `intent` and
        `explore-options`'s to `initiative`, give a mode assertion only to a query owned
        by a mode of the skill whose file it lands in, call every other carried query a negative, and put the new `situate`, `find`,
        `diverge`, `bet`, `map`, and `canvas` queries under `initiative`;
      - its `discovery-loop` line names `initiative diverge`, `intent ground`, and
        `intent de-risk`.

      *(goal-based)*

## Follow-ons

- eugenelim: `docs/specs/ux-writing-to-experience-design/` — move `ux-writing` to
  `experience-design`.
- eugenelim: `docs/specs/work-intake-modes/` — `work-intake`'s modes, including the
  retirement of `intake-intent`.

## Assumptions

- Technical: Cursor, Copilot, and Gemini CLI have no activation runner here, so
  activation on those hosts is ungrounded.
- Technical: whether two descriptions recover the activation the nine narrow skills had
  — a failure stops the slice before deletion (settled by: the scored probe and the
  activation run on the fresh held-out set).
