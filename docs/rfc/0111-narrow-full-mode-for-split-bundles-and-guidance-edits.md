# RFC-0111: Narrow full mode for independent bundles and plain guidance edits

- **Status:** Draft
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-10-28
- **Date closed:**
- **Decision weight:** standard (it changes a shipped governance workflow that adopters run, but not the charter, maintainer authority, a security trust model, or a stable compatibility promise)
- **Related:** [ADR-0088](../adr/0088-risk-triggers-have-a-single-documented-home.md) (the risk-trigger block has one home), [RFC-0094](0094-direct-light-execution-without-durable-planning-artifacts.md) (light work runs with no durable spec), [RFC-0099](0099-cut-before-adding-and-artifact-shaping.md) (cut before adding, and every spec-plan approval gate stays), [work-loop-evidence-modes](../specs/work-loop-evidence-modes/spec.md) (the spec behind PR #1635, which added a spike rule, a bug-fix handoff, two verification modes and proof by a run to `work-loop`)

A few terms used throughout. They are grouped so a reader can skip what they know.

**The workflow**

- A **pack** is an installable bundle of agent skills, subagents, commands, hooks and seed documents. **Core** is the base pack, and **adopters** are the repositories that install it. A pack ships when its version is bumped; that is a **core release**.
- **`work-loop`** is core's build workflow. It runs every change in one of two modes.
- **Gates** are the mechanical checks a change must pass: lint, type checks and tests.
- **Adversarial review** is a separate reviewer agent that attacks a spec, plan or diff for defects. It runs in **rounds**. A round that finds nothing above a deferred nit is **clean**.
- **Light mode** runs the change in the current session. It has gates and adversarial review run until clean. It has no spec, no plan and no human approval stop. Before the first write it records a session-only **decision record**: authority source, bounded scope, non-goals, risk-trigger assessment, assumptions and verification plan. Its procedure lives in `work-loop/references/light-mode.md`. That file has two tables. **Eligibility rows** must all hold for work to run light, for example "One bounded logical change". **Durability rows**: any one sends work to the durable spec-and-plan path, for example "A public or durable product behavior contract". Its **late-trigger rule** says what happens when a trigger is found mid-run: stop, write a spec and plan, keep the diff as observed work, and go through full mode's approvals.
- **Full mode** writes a spec with numbered acceptance criteria (such as AC-0003) and a plan. It runs **shaping review**, a reviewer agent that checks the spec states the right outcome, then adversarial review. Then it stops for two human approvals, of the spec and of the plan. Then it builds under a tracked run state with more reviewers. The **spec stage** (also **pre-execute**) is everything before code. The **code stage** (also **post-gates**) is review after the gates pass. **Experience review** is a reviewer for what a reader or adopter sees. An **owner-resolution record** is the author's written ruling on a disputed finding.
- A **plan** lists tasks. Each task declares `Depends on:` (the earlier tasks it needs, or `none`) and may declare `Touches:` (the paths it will write). **Supervisor mode**, in `references/supervisor-mode.md`, dispatches plan tasks in dependency order, one at a time by default; its parallel path is opt-in and disabled for now. Its `Touches:` screen reports `predicted-disjoint: yes|no|unknown` and can only force tasks to run one at a time.
- The **bundled-fixes carve-out** in `work-loop` lets a small verified fix ride along with another change. Its clause (iv) bars any ride-along that touches agent guidance.

**The triggers**

- **Risk triggers** are the list that picks the mode. If any one fires, the work goes to full mode. There are nine:
  - compliance, governance or security boundary;
  - structural or public-interface change;
  - persistent representation or mixed-version deployment;
  - destructive or irreversible operation;
  - backfill, replay, import or export;
  - new dependency;
  - **Unfamiliar**, when you cannot predict the design (a **spike**, a throwaway probe that writes nothing to the repository, may settle this one);
  - multi-person;
  - **multi-feature or dependent tasks**.
- The list lives only in `packs/core/.apm/skills/work-loop/SKILL.md`, between the `risk-triggers:start` and `risk-triggers:end` markers. **Projections** are generated copies of a pack file for each agent host, under `.claude/`, `.agents/` and `.codex/`. `tools/lint-agents-md.py` check 10g fails if the block appears anywhere else, or if the source and its `.claude/` and `.agents/` projections differ.
- **Fail-closed** means that when you can't tell, you take the safer route, here full mode.

**The guidance**

- **Agent guidance** is prose an agent follows as a rule: a skill, an agent definition, an `AGENTS.md`, a reference a skill loads. An **interface document** is prose that defines a contract others build against.
- A **content-pin test** is a test that reads a guidance file and asserts the exact phrases a rule depends on, such as `packs/core/tests/skills/work-loop/test_evidence_modes_contract.py`. That test uses a `_section(...)` helper to read only the text between two markers.
- **Pack evals** are recorded cases in each skill's `evals/evals.json`: a prompt and the behavior an agent should show.

**Related work**

- **RFC-0094** let light work run with no spec file. **RFC-0099** §7 keeps every spec-plan review and both human approvals in full mode. **ADR-0088** gave the trigger list a single home.
- **plan-stage-altitude** is a spec in progress on its own branch, with **ADR-0150** accepted there and not yet on `main` at 2026-10-28. It makes plans shorter and less detailed. A separate later ADR will cover how much review runs after code.
- **poteto-mode** is a set of public agent playbooks in the `cursor/plugins` repository. It is cited below as outside practice.

## Reviewer brief

- **Decision:** Whether work stops going to full mode in two cases where full mode buys little: a bundle of tasks that don't depend on each other, and an edit to an existing agent-guidance file that changes no tool, authority or gate, security boundary or published schema.
- **Recommended outcome:** Accept D1 to D3.
- **Change if accepted:**
  - A bundle whose tasks are shown to be independent splits into one unit per task. Each unit then faces every other trigger on its own.
  - A plain guidance edit no longer counts as a governance surface, public interface or published behavior contract just because the prose is the rule. It runs light, with content-pin tests on the edited section.
  - One follow-on delivery spec edits the trigger block, the light-mode durability row, and their pin tests.
- **Affected surface:** the risk-trigger block and `references/light-mode.md` in core's `work-loop`, their two projections, and the tests that pin them. Every adopter of core gets the change on the next core release.
- **Stakes:** a two-way door. Reverting the delivery spec restores today's routing, and no stored state changes. The cost of being wrong is a bad rule shipped to adopters through light mode; see [Exposure](#exposure-and-what-catches-it).
- **Review focus:** whether the split predicate in D1 is strict enough, and whether the four exclusions in D2 cover every guidance edit that should stay full.
- **Not in scope:**
  - editing the trigger block, any skill, or any pack version in this RFC;
  - plan shape, which plan-stage-altitude and ADR-0150 own (accepted on that branch, not yet on `main` at 2026-10-28);
  - review tiers after code, and merging shaping review with spec-stage adversarial review, which a later ADR owns;
  - the bundled-fixes carve-out, whose clause (iv) still bars ride-alongs that touch agent guidance;
  - any spec-required change, which stays full.

## The ask

**Recommendation:** accept all three decisions. Full mode is right for risky change. Today, though, two triggers send almost every pack edit there. The block treats "prose that *is* the rule — agent guidance, policy" as the thing itself, and this repository mostly ships agent guidance. The multi-feature trigger fires on any bundle, even when its parts never touch.

**Why now:** PR #1635, the latest change to the block, shows what full mode costs on guidance-heavy work: 11 spec-stage review rounds before any code. That PR would still go full under this RFC, because it edited the trigger block and what a reviewer finding may block. The cost it shows lands on every guidance edit today, including the many that change neither. The block was last rewritten in that PR, so the cited text is current.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Should the multi-feature trigger split a bundle of independent tasks instead of firing full mode? | Split when independence is verified for every unit before any unit merges; otherwise stay full | Each part is judged on its own risk, and a bundle that can't be shown independent loses nothing | 2026-11-11 | Accept, or tighten the predicate |
| D2 | Should an edit to existing agent guidance that changes no tool, authority or gate, security boundary or published schema run light? | Yes, with content-pin tests scoped to the edited section | The edit's risk is its effect on agents, and those four are the effects full mode exists for | 2026-11-11 | Accept, or add an exclusion |
| D3 | How does this ship? | One follow-on delivery spec, run in full mode | The block is lint-guarded as its only home, and editing it changes the governance surface D2 excludes | 2026-11-11 | Accept |

## Problem & goals

### The merged trigger text

The block as merged in 42d02f315 (PR #1635, squash-merged 2026-10-28) opens with the rule both proposals narrow:

> Prose *about* such a thing is exempt; prose that *is* the rule — agent guidance, policy, an interface document — is the thing itself. Where you cannot tell whether the change reached the thing, it did.

Read with the triggers above it, a skill edit modifies "a compliance or governance surface" or "a public or published interface". Since the skill text is the thing, almost any edit to it fires.

The last trigger reads:

> **Multi-feature or dependent tasks** — it decomposes a multi-feature brief, or its tasks depend on one another.

It fires on the bundle, not on any part of it. Two edits that share nothing still send both to full mode.

The same PR added a spike paragraph to the **Unfamiliar** trigger:

> Before this trigger fires on unfamiliarity alone, you may run one spike to ground the design: a throwaway script or sketch outside the tracked tree, held to `new-spec`'s side-effect-free probe constraint, and never committed. Record what it observed as the grounding above. A spike settles only this trigger; every other trigger is decided on the real change, and the real change runs the normal loop.

That paragraph narrows Unfamiliar already. This RFC leaves it as it is and relies on its last sentence: a split unit or a guidance edit is still judged against every other trigger on the real change.

### What full mode cost on a change it fit poorly

PR #1635 (`work-loop-evidence-modes`) added a spike, a bug-fix handoff, two verification modes and proof by a run. It fired two triggers: it edited agent guidance, and it bundled four features. No security, structural, persistent, destructive, dependency or Unfamiliar trigger fired.

Its diff, counting pack source once and not its two projections:

- 112 added lines of pack guidance prose, plus 10 lines of guides and a 20-line changelog fragment;
- 53 lines of evals and 314 lines of tests;
- a 261-line spec and plan.

Its saved run records show:

- 6 shaping rounds and 5 adversarial rounds on the spec and plan before approval;
- 2 adversarial and 2 experience-review rounds after code;
- 2 owner-resolution records, plus the spec and plan approvals. The author counts 7 human stops in all.

After round 2, almost every spec finding came from the author's own repairs. Shaping round 2 resolved all 7 round-1 findings. Rounds 3 to 6 then reviewed fixes to earlier fixes. Two criteria, AC-0003 and AC-0004, are named in 5 of the 11 spec-stage rounds. The author counts 7 rounds across the two reviewers.

### This RFC would not have rerouted PR #1635

PR #1635 is evidence of the cost, not a case this RFC saves. Under D1 and D2 it still goes full on three counts:

- The spike paragraph edits the trigger block itself, which is the authority over every gate.
- Proof by a run makes a behavior finding with no run "a Concern at most". That changes what may block a gate, which is D2's authority exclusion.
- Its four features all wrote to `packs/core/.apm/skills/work-loop/SKILL.md`, so the bundle fails D1's write-set check and can't split.

What this RFC moves to light is the smaller, commoner change that pays the same toll today. One example is a procedure step reworded or reordered. Another is a missing case added to a reference, or a contradiction between two sections fixed. Neither changes a tool, an authority or gate, a security control or a schema. Today both fire because the prose is the rule.

### The pattern beyond one PR

On 2026-10-28, 24 of the last 40 commits on `main` touched `docs/specs/`, and the repository holds 597 spec folders. Local worktrees hold 501 saved review files from 18 runs. Of those, 357 are reviewer reports rather than adjudications or summaries: 203 at the spec stage and 154 at the code stage. The heaviest spec stage among them drew 9 shaping, 12 adversarial and 6 security report files before code. These are local files, not a sample of all runs, and a file is not always one round. They show that the spec stage, not the code, is where full-mode effort goes.

### Goals

- Route each part of a bundle by its own risk, when the parts are shown to be independent.
- Route a plain edit to existing guidance to light mode, while edits that change tools, authority or gates, security or a published schema keep their triggers.
- Keep every existing approval gate where it stands.

### Non-goals

- Weakening any trigger beyond what D1 and D2 name. D1 narrows the multi-feature trigger. D2 narrows the "prose that *is* the rule" sentence, the public-interface reading of the structural trigger for edits to existing guidance, and the matching durability row. Nothing else moves.
- A third mode between light and full. RFC-0099's cut-before-adding rule weighs against new surface, and light mode already has the shape needed.
- Changing what full mode does once it is selected.

## Constraints this proposal keeps

- **Approval gates stay.** RFC-0099 §7 ("Preserve every spec-plan and human approval gate") and the `AGENTS.md` rule never to cut "required … human approval" are untouched. Light mode has no approval gate today (RFC-0094: "light mode never had a human approval gate"). Both routes only decide whether work enters full mode. Once there, nothing changes.
- **The other triggers keep working.** Security boundary, persistent representation, destructive, backfill, new dependency, Unfamiliar and multi-person triggers are decided on each unit and on each guidance edit as today. The structural trigger is too, except that D2 narrows its public-interface reading for edits to existing guidance on purpose. New modules, layers, boundaries and guidance files still fire it.
- **A spec-required change stays full.** An explicit request for a spec, a supplied governing spec, or any durability row in `light-mode.md` still routes to the durable path. D2 narrows one of those rows on purpose, "A public or durable product behavior contract", and says exactly how.
- **Fail-closed stays.** "Where you cannot tell whether the change reached the thing, it did" keeps its force. D1 and D2 each say what to do when the predicate can't be shown: stay full.
- **The block keeps one home.** ADR-0088 and lint check 10g stand. This RFC proposes text. The delivery spec in D3 makes the change.

## Proposal

### D1. Split a bundle whose tasks are shown independent

Change the multi-feature trigger so that it fires on a bundle only when its tasks cannot be shown independent. When they can, each task becomes its own unit. Each unit faces every other trigger and every direct-light eligibility row on its own, and ships as its own branch and pull request.

The bundle as a whole must still pass the session rows in `light-mode.md`: "Expected to complete in the current session", "Expected multi-session work" and "Queueing for later". A split happens inside one session, and the decision record that holds it is session-only. A bundle whose units together need more than one session, or would sit queued, stays whole and goes full.

**The split predicate.** Tasks in a bundle are independent only when all three hold:

1. **No dependency edge.** No task's `Depends on:` names another task in the bundle. In light mode, which has no plan file, the tasks and their `Depends on:` lines go in the session decision record that `light-mode.md` already requires before the first write.
2. **No shared write set.** Each task declares the paths it will write, in the same `Touches:` form plans use. No path or glob in one task's set matches a path in another's.
3. **The diff agrees.** At review, each unit's real diff stays inside its declared set and touches no file in another unit's set.

**How the split is verified.** Checks 1 and 2 run before the first write, from the decision record. Check 3 runs on every unit's finished diff. Check 3 is the check that counts, for the same reason `supervisor-mode.md` gives for its `Touches:` screen: a declared set is a prediction, and its `yes` and `unknown` results "**never** greenlight". Generated projections of a pack file (`.claude/`, `.agents/`, `.codex/`) count as writes to the source path, so two units that edit one skill through different projections overlap.

**No unit merges until every unit passes.** Units may be reviewed in any order. No unit's pull request merges on the light route until every unit still in the bundle has a finished diff that passes check 3. So a late unit can't stray into a set whose unit has already shipped.

**The fallback.** When any check fails, or can't be shown, the bundle stays whole and the multi-feature trigger fires: full mode, as today. A unit whose diff leaves its declared set stops the whole bundle. Nothing has merged at that point, so the bundle moves to full mode with every unit's diff kept as observed work, under the late-trigger rule `light-mode.md` already has.

Splitting does not make a unit light. A split unit that fires another trigger leaves the bundle and goes to full mode by itself. It takes its declared write set with it. Its spec and plan carry that set, and the units still in the bundle run check 3 against it before they merge. The light units then merge without waiting for the full unit, so the session rule above still holds.

This keeps the property the no-merge rule exists for: no work ships without the gate it needs. If the full unit's diff later strays into a merged light unit's files, that overlap is reviewed under the full unit's own spec, adversarial review and two human approvals. If check 3 fails for any unit still in the bundle, the fallback above applies to the bundle, as before.

### D2. Route a plain edit to existing agent guidance to light mode

D2 covers edits to guidance files that already exist. Adding a skill, an agent definition, a hook, a command, or a reference a skill newly loads is a new module or boundary. It still fires the structural trigger.

Narrow the "prose that *is* the rule" sentence for agent guidance. An edit to existing guidance modifies a trigger's thing only when it does one of these:

- **Tool surface:** it changes which tools, commands, hooks or scripts an agent may run, or how they're invoked.
- **Authority or gate:** it changes who or what may approve, decide, merge, or skip a gate. It also counts when it changes what a gate requires, what counts as clean, what evidence `work-loop`'s finish checklist (its last readiness check) needs, what a finding may block, or which text an agent treats as instruction.
- **Security boundary:** it changes a control the security trigger names, including how untrusted input, secrets, confinement or LLM authority (what an AI agent is allowed to do) are handled.
- **Published schema:** it changes a format other tools or adopters parse, such as frontmatter fields, a record grammar, a verdict schema or a manifest.

Compliance and policy prose is not covered here. An edit to a compliance or policy rule keeps the compliance and governance trigger as today. D2 covers guidance that tells an agent how to do its work. It does not cover what the work must satisfy.

A guidance edit that does none of these fires no trigger by being guidance. It still faces every trigger on its other effects. "Where you cannot tell whether the change reached the thing, it did" still applies. If you can't tell whether an edit changes one of the four, it does, and the edit goes full.

**What this narrows, named.** Shipped pack guidance reaches every adopter, so today it reads as a "public or published interface" (the structural trigger), and as "A public or durable product behavior contract" (a durability row in `light-mode.md`). D2 narrows both for edits to existing guidance. Such an edit is a published interface or behavior contract change only when it hits one of the four cases above. A plain edit changes how an agent carries out a step, inside the same tools, authority, gates, controls and formats. It is not a contract change. The delivery spec edits the trigger sentence and that durability row together, so the two can't disagree.

**What the route runs.** The route is light mode with one added obligation:

- **Content-pin tests scoped to the edited section.** Each changed rule gets a pin test, or an updated one, asserting the phrases it depends on. The test is read from that section, as `_section(...)` does in the existing work-loop tests.
- **Adversarial review as light mode runs it today.** Rounds run until clean, with the stop-and-ask check when rounds stop converging. This RFC adds no review tier.
- **No shaping review, no spec, no plan, no human approval stop.** Light mode has none of these now.

It follows the shape the reference practice below uses: check structure, test what is structural, scale review to the change.

### D3. Ship through one delivery spec

One follow-on spec edits the block and `references/light-mode.md` in `packs/core/.apm/skills/work-loop/`, regenerates the projections, and adds pin tests and evals. That spec runs in full mode. It changes the trigger block, which decides every gate, so it is exactly the authority-or-gate case D2 keeps full. See [Follow-on artifacts](#follow-on-artifacts).

## Exposure and what catches it

A guidance edit on this route loses shaping review and a spec. It reaches every adopter on the next core release. A bad rule therefore spreads further than a bad line of code in one repository, and nothing on this route asks a human before it ships.

What catches it instead:

- **Content-pin tests** catch a rule that drifts, or contradicts pinned wording elsewhere, on every run of the suite.
- **Adversarial review run until clean** reads the diff against the surrounding guidance and the repository's conventions.
- **Pack evals** (each skill's `evals/evals.json`) catch a rule that changes what an agent does on a recorded case.
- **The pull request** is still reviewed and merged by a maintainer. That is a merge decision, not a spec approval.

What none of these catches is a rule that is well-formed, consistent and wrong. Shaping review exists for that. Its yield fell off quickly on PR #1635: rounds 3 to 6 mostly reviewed the author's own repairs rather than finding new wrong rules. The four exclusions in D2, the structural trigger for new guidance files, and the compliance trigger together keep the edits where a wrong rule does the most harm in full mode.

## Options considered

The axis is what the two triggers do with a change that fires them for these reasons only.

| Option | What happens | Assessment |
| --- | --- | --- |
| Do nothing | Every bundle and every guidance edit go full | Keeps full-mode spec cost, measured above, on most pack edits. Safe |
| Only D1 | Bundles split; every guidance edit still fires | Solves bundling. Each split unit of a pack edit still goes full because it is guidance, so in a guidance-heavy repository little moves to light |
| Only D2 | Plain guidance edits run light; bundles stay full | A bundle of plain guidance edits still goes full whole |
| D1 and D2 (recommended) | Both narrow, each with a fail-closed fallback | Routes each part by its own risk |
| A third mode | A new tier between light and full | Adds surface RFC-0099 asks us to cut, and duplicates light mode |
| Split on the author's word | Bundles split on a declared independence with no diff check | Fails the block's fail-closed rule and the `Touches:` precedent that a prediction never greenlights |

## Risks & what would make this wrong

- **A split hides a link.** Two units share no file but share a meaning, such as one rule that cites another. Mitigation: the adversarial review on each unit reads the surrounding guidance, and pin tests on the cited rule fail if it moves. If this happens, add "a unit's text cites another unit's changed section" to the predicate.
- **The four exclusions miss a case.** A guidance edit changes agent behaviour in a way none of the four names, and the change is harmful. This RFC is wrong if a route edit needs a revert or a fix in a later release for a reason shaping review would have caught. The delivery spec turns each such case into an eval and a review of the exclusions.
- **Authors read the exclusions narrowly.** Mitigation: "where you cannot tell, it did" stays, and the adversarial reviewer checks the stated classification against the diff.
- **Saved effort is smaller than hoped.** Some pack edits also fire Unfamiliar, and some split units fire other triggers. The route still leaves them full. That is the intended result.

## Evidence & prior art

- **The merged trigger block.** `packs/core/.apm/skills/work-loop/SKILL.md`, the `risk-triggers` span at 42d02f315, quoted under [Problem & goals](#problem--goals).
- **PR #1635's run records.** Local saved review files for `work-loop-evidence-modes`: six shaping summaries, five pre-execute adversarial raw reports, two post-gates adversarial and two experience reports, and two owner-resolution records. They are local working files, not tracked in the repository.
- **Light mode today.** `references/light-mode.md` runs adversarial rounds to clean, and lists the eligibility and durability rows each split unit must pass, including "One bounded logical change" and "Dependent delivery tasks needing durable sequencing".
- **The `Touches:` precedent.** `references/supervisor-mode.md` treats a declared write set as serialize-only, never a green light. That is why D1 checks the real diff.
- **Reference practice.** The `cursor/plugins` poteto-mode playbooks at commit `ab1f702ce8e8b6557edb56b09f52cde8bfb83f17` have no light/full switch. Each claim below was checked against the fetched file:
  - [`authoring-a-skill`](https://raw.githubusercontent.com/cursor/plugins/ab1f702ce8e8b6557edb56b09f52cde8bfb83f17/pstack/skills/poteto-mode/playbooks/authoring-a-skill.md): validate frontmatter and links; "Test cases if structural. Skip if subjective."
  - [`multi-phase-plan`](https://raw.githubusercontent.com/cursor/plugins/ab1f702ce8e8b6557edb56b09f52cde8bfb83f17/pstack/skills/poteto-mode/playbooks/multi-phase-plan.md) step 1: "When the change is one or two files with an obvious approach, skip the plan. Say so and stop."
  - [`opening-a-pr`](https://raw.githubusercontent.com/cursor/plugins/ab1f702ce8e8b6557edb56b09f52cde8bfb83f17/pstack/skills/poteto-mode/playbooks/opening-a-pr.md): "Prefer five narrow PRs to one large PR."
  - [`autopilot-full`](https://raw.githubusercontent.com/cursor/plugins/ab1f702ce8e8b6557edb56b09f52cde8bfb83f17/pstack/skills/poteto-mode/playbooks/autopilot-full.md) step 4: one full swarm; a minor fix gets a single verifier, and "a wording-only change gets none."

These playbooks back the idea of scaling review to the change. They do not show that this repository's exclusions are the right ones.

## Experiment / validation

**Hypothesis:** with D1 and D2, plain edits to existing guidance, and bundles of them with disjoint write sets, run light with no loss of caught defects. Changes shaped like PR #1635, which edit gates or the trigger block, still go full.

- **Measure:** for the first 10 pack changes after the delivery spec ships, record which triggers fired, which route ran, review rounds, and any later fix to the change.
- **Success:** at least half of the guidance edits that would have gone full run light, and none of them needs a revert or follow-up fix that shaping review would have caught.
- **Failure:** one such revert or fix. That reopens D2's exclusions.

Two measurements would sharpen this but aren't needed to decide:

- how often Unfamiliar is the only trigger that fires;
- what the bug-fix handoff costs per run.

## Follow-on artifacts

- **Delivery spec `work-loop-narrow-full-mode`** (full mode):
  - edits the multi-feature trigger and the "prose that *is* the rule" sentence in the `risk-triggers` span;
  - adds the split predicate, the bundle-level session rows, the no-merge-until-all-pass rule and the guidance-edit obligation to `references/light-mode.md`;
  - narrows the "A public or durable product behavior contract" durability row in the same words as the trigger sentence;
  - regenerates the `.claude/` and `.agents/` projections so lint check 10g passes;
  - adds content-pin tests for the new wording in `packs/core/tests/skills/work-loop/`;
  - adds evals for a split bundle, an unsplittable bundle, a late unit that strays, a plain guidance edit, a new guidance file, and one guidance edit per exclusion;
  - bumps core as its release.

  Its implementing commits end `Spec: docs/specs/work-loop-narrow-full-mode/spec.md`, and the spec cites RFC-0111.

No ADR is needed. The decision lives in the block, and this RFC records why.
