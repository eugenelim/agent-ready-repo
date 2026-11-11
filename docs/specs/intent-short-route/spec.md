# Spec: intent-short-route

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0107 (D1, D2, D6); ADR-0140; RFC-0067 (clean retire)
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

A team shaping product work names its outcome, tests the bet, and breaks it down
through one `intent` skill that shows where they are in the intent lifecycle, loads
only the step they asked for, and offers the next step. Success means shaping requests trigger `intent` within 3 percentage points of
how often they triggered the three skills it replaces, and no operative surface names
those skills.

## What Changes

- A new `intent` skill lives in `packs/product-engineering/.apm/skills/intent/`.
  - It has a read-only route mode and three verb modes: `frame`, `de-risk`, and
    `decompose`.
  - Each verb mode's procedure lives in `references/<mode>.md`.
  - A lifecycle map in the skill body shows every route and stage. Each mode states
    where the user is on that map, and offers the next logical mode when it
    finishes.
  - The source skills' references, assets, and examples move under `intent/`.
- `frame-intent/`, `de-risk-intent/`, and `decompose-intent/` are removed.
- frame-intent's `## Pick a route` menu becomes `intent`'s route mode.
- `discovery-loop` and the `discovery-lead` agent call `intent` modes at G0, G1, G3,
  and the product lens.
  - `discovery-loop`'s description names its handoff through `work-intake`.
  - Its trigger phrases are unchanged, so its evals stay as they are.
- The three skills' eval files merge into `intent/evals/`. A routing-classification
  evidence note sits in `notes/`.
- Every operative caller moves to the new name:
  - Core's `work-intake`, `workspace-status`, `init-project`, and `work-loop`;
  - `packages/agentbundle`;
  - `experience-design`, `governance-extras`, and `product-strategy`;
  - tools, tests, guides, site pages, pack docs, and live architecture and journey
    records.
- Versions and release:
  - `product-engineering` goes to 1.0.0.
  - Every other pack this change edits takes a patch. The plan's release step owns
    releasing them together.
  - `packages/agentbundle` bumps under its own rule.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | Guides tell adopters which skill to call for shaping | `guides/` files that name the retired skills | eugenelim | Edited guides; regenerated lifecycle graphic | AC-0010, AC-0027, AC-0034 pass |
| Current product truth | Pack pages state the skill roster | `packs/product-engineering/{README,JOURNEY,DESIGN}.md`, `web/src/content/` | eugenelim | Edited pages | AC-0010 passes |
| Current architecture | The lifecycle flow names shaping skills | `docs/architecture/lifecycle-flow.md` | eugenelim | Edited flow | AC-0010 passes |
| Release history | A breaking removal needs an adopter action | `docs/product/changelog.md` | eugenelim | Entries for each released pack | AC-0025, AC-0029, AC-0031, AC-0032 pass |
| Decision rationale | De-risk's reviewer boundary is read at mode scope | ADR-0111 § Errata, plus ADR-0140 | eugenelim | A dated, approver-signed erratum | AC-0040 passes |

## Agent Rules

### Always do

- Move each source procedure into its mode reference. Change only skill names and
  paths, and add the orientation line and `## Next` section this spec requires.
- Follow `packs/AGENTS.md` and `packages/AGENTS.md` for version bumps, eval harness
  updates, and self-host.
- Record in `notes/verification-ledger.md` every eval case or fixture dropped, every
  test assertion replaced or dropped, and why.

### Ask first

- Changing what any procedure does. Three changes are exempt:
  - retargeting skill names and paths;
  - adding the orientation line and `## Next` section this spec requires;
  - rescoping `de-risk`'s sentence "This skill never dispatches it" to say the
    `de-risk` mode never dispatches `adversarial-reviewer`. The ledger records this
    under AC-0007, with the replaced test assertion.

  Frame's review sections move unchanged. Its `## Next` section may take the three
  states AC-0037 lists, and it offers the shaping review only while the intent has
  no current review.
- Changing any description after the post-fold probe has run, if the probe shows it
  as a candidate.
- Editing a frozen record (a shipped spec, or an accepted RFC or ADR) beyond an
  erratum.
- Retargeting a name inside `packs/core/tests/skills/work-loop/fixtures/corpus/`.
- Adding `allowed-tools` to `intent`'s frontmatter, which AC-0006 forbids.

### Never do

- Add an alias, shim, or stub directory for a retired name.
- Give route mode state, retries, or gate control.
- Retire or fold any shaping skill other than the three named here.
- Edit `.claude/` or `.agents/` projections by hand.
- Add a top-level directory or a new dependency.

## Testing Strategy

- **Skill structure (AC-0001, AC-0002, AC-0003, AC-0006, AC-0009, AC-0024, AC-0026, AC-0030):**
  goal-based. Lint and pack tests decide these.
- **Lifecycle orientation (AC-0036, AC-0037):** goal-based. A pack test pins:
  - the lifecycle map, including its match with `frame-situation`'s sequence;
  - each mode's orientation line;
  - each mode's `## Next` options, including the `discovery-loop` deferral line.
- **Route mode (AC-0004, AC-0005):** goal-based. A pack test pins the route table and
  the words the route section must not contain.
- **Retargeted behavior (AC-0007, AC-0012, AC-0013, AC-0014, AC-0015, AC-0028):**
  goal-based. The existing pack, roster, and Core tests are retargeted to `intent` and
  must pass.
- **Workspace-status shaping default (AC-0011):** TDD.
  `tools/test_workspace_status.py` expectations change first, then the engine and its
  mirror.
- **Registration sweep, docs, and release records (AC-0010, AC-0025, AC-0027, AC-0029, AC-0031, AC-0032, AC-0034, AC-0040):**
  goal-based. A search with a stated scope and exceptions, the changelog entries, the
  guide text, the regenerated graphic, and a recorded install observation decide these.
- **Eval carry-over (AC-0016, AC-0017, AC-0018):** goal-based. Checks run over the
  merged eval files and the ledger.
- **Mode routing (AC-0019, AC-0020, AC-0021, AC-0022, AC-0033, AC-0035):** bounded
  routing-classification evidence, following the experience-design fold.
  - The eval runner cannot assert a mode, so this is the only mode evidence in this
    slice.
  - This departs from RFC-0107 Experiment's bar, which asks for mode accuracy within 3
    percentage points.
  - eugenelim approved the departure on 2026-10-10, when choosing this evidence route
    for the slice.
- **Activation (AC-0023):** a headless run of `pack_evals` over held-out queries,
  comparing trigger rates before and after the fold. This is the release gate set by
  RFC-0107's Experiment section.
- **The clarifying question (AC-0008):** manual QA, recorded in the ledger.
- **Guided walk (AC-0038, AC-0039):** manual QA, recorded in the ledger. One walk
  covers the route reply and the short route.

## Acceptance Criteria

### The `intent` skill

- [x] **AC-0001.** `intent/SKILL.md` has, in order, the sections `## When to invoke`,
      `## The intent lifecycle`, `## Route mode`, and `## Modes`. `## Modes` holds one table with exactly four
      rows: `route`, `frame`, `de-risk`, and `decompose`. *(goal-based)*
- [x] **AC-0002.** Each verb mode's procedure is in `intent/references/frame.md`,
      `de-risk.md`, or `decompose.md`. The mode's table row names that file.
      *(goal-based)*
- [x] **AC-0003.** The `intent` description is at most 1024 characters.
      - It contains `frame`, `de-risk`, and `decompose` as whole words.
      - A whole word here means one not joined to a neighbouring character by a hyphen
        or a letter, so `frame-situation` does not count.

      *(goal-based)*
- [x] **AC-0004.** `## Route mode` names exactly three routes, each with its first
      step:
      - short: `intent frame`;
      - longer: `frame-situation`;
      - supervised: `discovery-loop`.

      It separately names three out-of-stage owners: `bug-fix`, `work-intake`, and
      `architect-design`. It names no other skill. *(goal-based)*
- [x] **AC-0005.** The text of `## Route mode` matches none of these stems:
      `writ`, `save`, `saving`, `creat`, `remember`, `retr(y|ie)`, `gate`, `record`,
      `persist`, `updat`, `append`, `stor`, and `edit`.
      - Matching is case-insensitive.
      - The pattern is `\b<stem>`, so each stem also matches its inflections.

      *(goal-based)*
- [x] **AC-0006.** `intent`'s frontmatter declares no `allowed-tools`, so no mode is
      pre-approved to write, edit, or dispatch an agent. Its boundaries are exactly
      `filesystem_write` and `filesystem_read_untrusted`.
      *(goal-based)*
- [x] **AC-0007.** Every assertion that names one of the three source skills is
      handled. This covers assertions in `test_frame_intent_shaping_review.py`,
      `test_frame_intent_experience_handoff.py`,
      `test_de_risk_intent_reviewer_boundary.py`,
      `test_intent_triad_execution_wiring.py`,
      `test_shaping_handoff_pack_surface.py`,
      `test_shaping_intake_handoff_matrix.py`,
      `test_intent_template_shape_conformance.py`, and
      `test_rfc0099_activation_coverage.py`. Each such assertion either:
      - passes against its new path under `intent/`, or
      - appears in the ledger as replaced by a named criterion, or as dropped with a
        reason.

      *(goal-based)*
- [x] **AC-0008.** A request whose facts fit both the short and the longer route gets
      one question from route mode and causes no file change. The ledger records the
      request, the reply, and `git status` before and after. *(manual QA)*
- [x] **AC-0036.** `## The intent lifecycle` lays out the three routes as ordered
      stages:
      - **short:** `frame`, `de-risk`, `decompose`, then the hand-off to build
        through `work-intake`;
      - **longer:** the six steps `frame-situation` states in its entry-point step,
        in the same order, with its validate step shown as `de-risk`;
      - **supervised:** `discovery-loop`.

      The section marks which stages are `intent` modes and which are separate
      skills. It also marks the review gates where they fall:
      - after `frame`, the `shaping-reviewer` intent-mode well-formedness check. It
        is marked as a gate when a review route is available, and as optional
        otherwise.
      - before `de-risk`, the `adversarial-reviewer` intent-mode assumption read,
        marked as advisory;
      - after the hand-off, the review gates that the owning skill runs, citing
        `author-delivery-brief` for a brief and `new-spec` for a spec.

      A pack test compares the longer route's list with `frame-situation`'s
      sequence, so the two cannot drift apart. *(goal-based)*
- [x] **AC-0037.** Each of `references/frame.md`, `de-risk.md`, and `decompose.md`:
      - opens with one line that names its stage, names every route in
        `## The intent lifecycle` that includes it, and gives its position on each;
      - ends with a `## Next` section.

      The `## Next` section's first line says that when `discovery-loop` or its
      `discovery-lead` agent called the mode, control returns to the loop's next gate,
      and no offer is made.

      The `## Next` section offers at most three options, with the first one marked
      as recommended, and names the outcome that selects each:
      - **frame:** the outcome is the intent written.
        - While the intent has no shaping review for its current revision, or a
          material edit has invalidated that review, the recommended offer is the
          `shaping-reviewer` intent-mode review.
        - After a review with no unresolved `MALFORMED` token, the recommended offer
          is `intent de-risk`, and the `adversarial-reviewer` intent-mode read is
          also offered.
        - When the review is unavailable, or its dispatch did not complete,
          `## Next` repeats the source's unavailable or did-not-complete report and
          claims no review result. It recommends `intent de-risk`, and offers the
          adversarial read only when that reviewer is installed.
        - `intent decompose` is offered only for a bet that has already survived
          de-risk.
      - **de-risk:** the outcomes are survive and kill.
        - On survive, `de-risk.md` offers both next stages, each labelled with its
          route: `intent decompose` for the short route and `place-bet` for the
          longer route. The one for the route the conversation shows is marked
          recommended. When no route shows, the section asks which route applies.
        - On kill, the offer is `intent frame`.
      - **decompose:** the outcomes are a leaf and a non-leaf. A leaf is offered the
        hand-off through `work-intake`, with the review gates that the artifact's
        owner will run named but not run. A non-leaf is offered `intent decompose` or
        `intent frame` for a child.

      The survive branch and the frame branch are the two exceptions to the rule
      that the first option is the recommended one. In each, the recommendation
      depends on the conversation's state.
      - The pack test checks each offer against the lifecycle map.
      - For the survive branch, it requires both route-labelled offers, plus the
        instruction to recommend the conversation's route or ask.
      - For the frame branch, it requires the shaping-review offer, the
        adversarial-read offer, the unavailable-review state, and the conditions
        that decide which one is recommended.
      - The AC-0039 walk checks the recommendation at run time.
      *(goal-based)*
- [x] **AC-0038.** `## Route mode` tells the user their chosen route and where it
      starts on the lifecycle map. It offers the route's first step as an option,
      not as an action already taken. *(manual QA)*
- [x] **AC-0039.** The walk runs with Core's `shaping-reviewer` installed. One sample
      intent starts with a route-mode reply that selects the short route. The ledger records that reply as AC-0038's evidence. The intent is
      then walked through `frame`, `de-risk`, and `decompose`.
      - Every reply names the user's stage and offers the next options.
      - No mode starts the next mode before the user chooses it.
      - After `frame`, the reply recommends the shaping review. After that review
        passes, the reply recommends `intent de-risk` and also offers the adversarial
        read.
      - The `de-risk` survive reply marks `intent decompose` as recommended.

      A second `de-risk` survive reply, with no route shown in the conversation, asks
      which route applies. The ledger records both. *(manual QA)*
- [x] **AC-0030.** The moved files never share a path. That covers the source skills'
      `references/`, `assets/`, and `examples/` files, plus the three new
      `references/<mode>.md` files, all once they sit under `intent/`. *(goal-based)*

### Retirement

- [x] **AC-0009.** `frame-intent/`, `de-risk-intent/`, and `decompose-intent/` are
      absent. `[pack.evals].skills` in `packs/product-engineering/pack.toml` lists
      `intent` and none of the three retired names. Every name it lists has a directory
      under `.apm/skills/`. *(goal-based)*
- [x] **AC-0010.** A case-sensitive search for `frame-intent`, `de-risk-intent`, and
      `decompose-intent` finds no match in:
      - `packs/`, `guides/`, `web/src/`, `tools/`, `tests/`, `packages/`, and
        `contracts/`;
      - `workspace.toml`;
      - `docs/architecture/`, `docs/product/journeys/`, `docs/guides/`, and
        `docs/product/workspace-toml-deps.md`;
      - the root files `AGENTS.md`, `ARCHITECTURE.md`, and `README.md`, plus
        `docs/CHARTER.md`.

      Only three kinds of match are allowed:
      - lines inside a test-module constant named `RETIRED_SHAPING_SKILLS`;
      - files under `packs/core/tests/skills/work-loop/fixtures/corpus/`;
      - a match inside the directory name of a `docs/specs/` spec whose `Status` reads
        `Shipped`, such as `frame-intent-escape-verdicts`.

      `docs/design/` is a dated design record and is out of scope.

      *(goal-based)*
- [x] **AC-0011.** `workspace-status` maps the `shape` entry type, and its fallback, to
      `intent`. The engine under `packs/core`, its mirror under `packages/agentbundle`,
      and `workspace_mcp.py` agree, and `tools/test_workspace_status.py` passes.
      *(TDD)*
- [x] **AC-0012.** `work-intake`'s routing-precedence owner list names `intent`, and
      `test_routing_precedence.py` passes. *(goal-based)*
- [x] **AC-0013.** These integration entries read as follows:
      - `core-delivery-handoff` consumers: `["skill:discovery-loop", "skill:intent"]`;
      - `core-intent-shaping-review` consumers: `["skill:intent"]`;
      - `governance-extras` `design-proposal-product-engineering` providers:
        `["skill:intent"]`.

      *(goal-based)*
- [x] **AC-0014.** `discovery-lead.md` and `discovery-loop/SKILL.md` name:
      - `intent frame` at G0;
      - `intent de-risk` and `intent decompose` at G1;
      - `intent decompose` at G3 and in the product lens.

      *(goal-based)*
- [x] **AC-0015.** `discovery-loop`'s description names `work-intake` as its G3
      handoff, and does not name `work-loop`. *(goal-based)*
- [x] **AC-0028.** `guides/product-engineering/how-to/frame-the-intent.md` describes
      `discovery-loop` as starting from a raw idea, not from an approved intent.
      *(goal-based)*

### Evals and routing evidence

- [x] **AC-0016.** `intent/evals/eval_queries.json` holds every distinct query from the
      three source files. The ledger labels each query with its owner, either a folded
      skill or another named skill.
      - A query whose owner is a folded skill is positive and carries a `mode` key
        naming that skill's mode.
      - Every other query is negative.
      - No query appears twice.

      *(goal-based)*
- [x] **AC-0017.** `intent/evals/eval_queries.json` holds at least four negative
      queries owned by `intake-intent`. Each asks to record a stated outcome as a
      minimum repository intent. *(goal-based)*
- [x] **AC-0018.** Each source skill's `evals/evals.json` case and `evals/files/`
      fixture is either in `intent/evals/` or listed in the ledger with its drop
      reason. *(goal-based)*
- [x] **AC-0019.** `notes/routing-classification-evidence.md` records 44 scored cold
      classifications, made with descriptions only:
      - **Pre-fold:** the eleven cases, once each.
      - **Post-fold:** the eleven cases, three runs each, all from one scored attempt
        made after the 2026-10-11 repeated-run amendment. Every run in the attempt uses
        one byte-identical candidate set.
      - **No retries:** no run inside a scored attempt is repeated or dropped.
      - **History:** earlier post-fold attempts stay in the note, marked unscored. They
        supply no run to a scored attempt.
      - **New attempt:** a new scored attempt starts only after a recorded AC-0020 or
        AC-0023 failure, once a dated ledger entry records `eugenelim`'s choice to
        revise after that failure, and only when at least one candidate description
        differs from the attempt before it. The attempt it replaces, and that
        attempt's post-fold run, become unscored history.

      The expected selections are:

      | Case | Pre-fold | Post-fold |
      | --- | --- | --- |
      | 2 framing requests | `frame-intent` | `intent` (`frame`) |
      | 2 assumption-testing requests | `de-risk-intent` | `intent` (`de-risk`) |
      | 2 break-down requests | `decompose-intent` | `intent` (`decompose`) |
      | 1 "which way should we shape this" request | `frame-intent` | `intent` (`route`) |
      | 1 whole-product discovery request | `discovery-loop` | `discovery-loop` |
      | 1 record-this-outcome request | `intake-intent` | `intake-intent` |
      | 1 write-a-spec request | `new-spec` | `new-spec` |
      | 1 raw market-signal request | `frame-situation` | `frame-situation` |

      *(bounded routing-classification evidence)*
- [x] **AC-0035.** The probe uses the same kind of candidate set in each world:
      - every `product-engineering` skill installed in that world;
      - `intake-intent`, `new-spec`, `bug-fix`, and `architect-design`.

      *(bounded routing-classification evidence)*
- [x] **AC-0033.** The note records:
      - for the pre-fold world and for each post-fold attempt, every candidate
        description, verbatim, once;
      - for each case, the prompt and the expected selection;
      - for each run, the selected skill, its mode when that skill has modes, and the
        confidence. Runs in a scored post-fold attempt are numbered 1 to 3. A case that
        ran once, whether pre-fold or in an unscored history attempt, needs no run
        number.

      *(bounded routing-classification evidence)*
- [x] **AC-0020.** Each of the eleven post-fold cases passes when all three of its
      runs match AC-0019's table in skill and mode, and at least two of the three are
      at high confidence. The eleven pre-fold selections are a recorded baseline only,
      and no pre-fold result gates the slice. A post-fold case that fails stops the
      slice before any source directory is deleted. `eugenelim` then decides whether
      to revise a candidate description under the Ask-first rule and make a new
      scored attempt under AC-0019, or to end the slice.
      *(bounded routing-classification evidence)*
- [x] **AC-0021.** Every AC-0035 candidate description that this change edits ships
      byte-identical to its text in the candidate set of the scored post-fold attempt
      that passed AC-0020. That includes
      `intent`, `discovery-loop`, and every edited `product-engineering` sibling. The
      edited experience-design descriptions are not probe candidates.
      *(bounded routing-classification evidence)*
- [x] **AC-0022.** The note states that it is a classification proxy, not a `Skill`
      activation event. It states that each case ran once pre-fold and three times
      post-fold, and that neither sample size establishes recall or repeatability. *(bounded routing-classification evidence)*
- [x] **AC-0023.** The held-out set has 30 positive queries, ten per verb, and 12
      negative queries. The probe sees none of them.
      - **Runner:** `pack_evals` headless runs each held-out query 3 times on Claude
        Code. It also runs on Codex if a Codex detector ships before this check.
      - **Installation:** each world runs in a prepared projection that installs that
        world's `product-engineering` together with `core` and `architect`. The skills
        owning the negatives can therefore be chosen.
      - **Isolation:** each projection sits outside every repository, including the
        disposable worktrees. Each run passes `--setting-sources project,local`, which
        hides every user-scope skill.
        - The discoverable skills are the three projected packs' skills plus the
          host's built-in skills.
        - The built-in skills are identical in both worlds, and none is a shaping
          skill.
        - The ledger records the skill set the host listed for each world.
      - **Errors:** every held-out query ends with zero errored runs in both worlds.
        An errored query is re-run before scoring.
      - **Post-fold:** all queries run against `intent`, in a worktree where the three
        source directories are deleted and self-host has run.
      - **Positive trigger rate:** the mean, over the 30 positives, of each query's
        `trigger_rate` as `pack_evals` records it.
        - Before the fold, each positive is measured against its owning source.
        - After the fold, it is measured against `intent`.
        - The post-fold rate is no more than 3 percentage points below the pre-fold
          rate.
      - **False-trigger rate:** the mean, over the 12 negatives, of each query's
        recorded `trigger_rate`.
        - Before the fold, each negative is placed in all three source files, and its
          rate is the highest of the three.
        - After the fold, its rate is `intent`'s.
        - The post-fold rate is no more than 3 percentage points above the pre-fold
          rate.
      - **Held-out set:** it shares no query with any source eval file or with
        `intent/evals/eval_queries.json`.

      The ledger records every run. If either bound fails, nothing is deleted, and
      `eugenelim` decides among three paths:
      - split the weakest mode back out;
      - revise a candidate description under the Ask-first rule, then make a new
        scored attempt under AC-0019 and AC-0020 and a new post-fold run. No held-out
        query appears verbatim in a revised description. Beside the re-measured
        result, the ledger states that the held-out misses informed the revision;
      - end the slice.

      Each scored attempt admits exactly one post-fold run; re-running its errored
      queries is the only exception. That run covers every host measured, and both
      bounds apply to each host separately. The post-fold run made on the descriptions of the
      scored attempt that passed AC-0020 is the one this criterion judges. Earlier
      post-fold runs stay in the ledger as unscored history. *(activation)*

### Release records

- [x] **AC-0024.** `product-engineering`'s `pack.toml` and `plugin.json` both read
      `1.0.0`. Every other pack that the version bump rule in `packs/AGENTS.md`
      reaches has a patch bump. The one exemption is an edit confined to a pack's
      `tests/` fixtures, because tests are not projected. `packages/agentbundle`
      follows `packages/AGENTS.md`. *(goal-based)*
- [x] **AC-0025.** `docs/product/changelog.md` has a `product-engineering` 1.0.0 entry
      with a `### Removed` section. That section names each retired skill and its
      replacement mode. *(goal-based)*
- [x] **AC-0031.** The 1.0.0 entry's `### Removed` gives the adopter step for a stale
      installed directory. That step matches the install and update behavior recorded
      in the ledger for a removed skill directory. *(goal-based)*
- [x] **AC-0029.** Two changelog entries in `docs/product/changelog.md` carry the same
      compatibility note: the Core entry and the `agentbundle` entry for this change.
      `packages/agentbundle/CHANGELOG.md` also carries it.
      - The note says the shaping suggestion, or the `shape` dispatch, names `intent`.
      - It says this needs `product-engineering` 1.0.0 or later.

      *(goal-based)*
- [x] **AC-0032.** The 1.0.0 entry names the hosts the activation run measured. It
      states that Cursor, Copilot, and Gemini CLI were not measured. It also states
      that mode accuracy was evidenced by a classification probe, not by an activation
      run. It names every pre-fold classification that missed AC-0019's expected
      selection or fell below high confidence. *(goal-based)*
- [x] **AC-0040.** `docs/adr/0111-intent-review-splits-well-formedness-from-assumption-attack.md`
      carries a dated, approver-signed `## Errata` entry. The entry states that D8
      binds `intent`'s `de-risk` mode, and that `intent`'s `frame` mode may offer the
      `adversarial-reviewer` intent-mode read. It also states that this keeps D8's
      reason: the mode that authors the kill condition is never handed hooks to mark.
      *(goal-based)*
- [x] **AC-0026.** `agentbundle catalogue lint --root . --deep` and
      `agentbundle catalogue verify --root .` pass after self-host. *(goal-based)*
- [x] **AC-0027.** `guides/_shared/explanation/the-operating-model.md` names `intent frame`,
      `intent de-risk`, and `intent decompose` for the short route. *(goal-based)*
- [x] **AC-0034.** Re-running `tools/render-lifecycle-graphics.py` leaves
      `guides/_shared/explanation/the-operating-model-full-map.svg` unchanged.
      *(goal-based)*

## Follow-ons

- eugenelim: `docs/specs/intent-longer-and-supervised-verbs/` covers the follow-on work:
  - the remaining nine shaping skills;
  - the rest of `discovery-loop`'s gates;
  - the stale statements in `frame-domain` and `run-a-discovery.md`;
  - the stale `work-loop` hand-off lines in `discovery-lead.md` (its description and
    the G3 hand-off paragraphs) and in `discovery-loop/SKILL.md`'s opening section,
    which still say the loop hands off to `work-loop` at G3 while the description and
    G3 row say `work-intake`;
  - the description trim, together with its eval update.
- eugenelim: six Draft tracker and progress-review specs named the deleted source
  paths; this change repointed them to `intent/` paths, and their own authoring
  confirms the destinations.

## Assumptions

- Technical: Cursor, Copilot, and Gemini CLI have no activation runner here, so
  activation on those hosts is ungrounded.
