# Manual QA walks: intent-longer-and-supervised-verbs

These walks exercised the one-skill build of 2026-10-12, which was reverted when the slice ended. They are kept as history; no shipped skill matches them.

Walks ran headless on 2026-10-12, each in a fresh git-tracked copy of the post-fold projection (`product-engineering` with the nine sources deleted, `core`, `architect`). Each call used `claude -p --permission-mode acceptEdits --allowed-tools "Skill Read Write Edit Agent Glob Grep" --setting-sources project,local`, resuming one session per walk. Requests supplied an owner, non-goals, and a save path so each mode could reach its end. Requests and replies are verbatim; `git status --short` is recorded before and after each turn.

An earlier round of walks showed the standalone `ground` and `de-risk` validation-plan replies not naming their stage, and `canvas` and `ground` not recommending their first offer first. Each mode's `Stage:` line then gained the sentence "Name this stage in the first line of every reply this mode gives.", and the `canvas` and `ground` offers state which comes first. The walks below ran on that text; the verification ledger records the earlier round.

## Longer route, turn 1

**Request:**

> Owner: Sam Rivera (product lead). Non-goals: no pricing changes, no new mobile app. Save any shaping artifacts under docs/product/shaping/. Signal: our self-serve trial-to-paid conversion fell from 9% to 5% over two quarters, and sales says mid-size teams stall during setup. I'm not sure what the problem really is yet. Which way should we shape this?

**Reply:**

> Take the **longer route**, starting with `intent situate`.
>
> ## Why the longer route fits
>
> You said yourself the real problem isn't clear yet, and that's exactly what the longer route is for. You have a raw signal: conversion fell from 9% to 5%, which means roughly 4 out of every 9 trials that used to convert now don't. You also have a guess from sales about mid-size teams stalling during setup. Neither is an outcome you can commit to yet.
>
> - **The short route doesn't fit yet.** It starts by framing one outcome. Framing "fix setup for mid-size teams" now would treat the sales explanation as fact before anyone has checked it. The drop could also come from a change in trial mix, from a different step in activation, or from something else entirely.
> - **The supervised route doesn't fit.** That route (`discovery-loop`) is for an idea for a whole new product. This is a problem inside a product you already have.
>
> ## Where it starts
>
> The longer route runs `situate` → `find` → `diverge` → `de-risk` → `bet` → `map`, then hands off to build through `work-intake`. You'd be at step 1 of 6.
>
> `situate` sorts out what kind of signal this is and where to start. It separates what you've seen (the conversion drop, which is in your data) from what people believe (sales' view that setup is where teams stall). It also decides whether the next step is mapping what jobs users are trying to get done or checking a specific assumption first. Your non-goals (no pricing changes, no new mobile app) and Sam Rivera as owner would go into it as constraints from the start.
>
> ## Next step
>
> Want me to run `intent situate` on this signal? It would save its output under `docs/product/shaping/`. I haven't created or changed any files yet.

`git status --short` before: `(clean)`; after: `(clean)`

## Longer route, turn 2

**Request:**

> Yes, take the longer route. Start with the first step.

**Reply:**

> You're on the longer route, step 1 of 6: situate. I've written it up, and it recommends **`intent find`** as the next step, because the cause of the drop isn't known yet.
>
> I saved it to `docs/product/shaping/trial-conversion-decline/situation-framing.md`. There was no layout config in the repo, so I used the folder you named.
>
> ## What the framing says
>
> - **Scope:** This affects the whole self-serve trial journey, not one screen or feature.
> - **Type of problem:** A gap. Conversion has fallen below your own earlier level, and nothing yet points to a competitor or other outside cause.
> - **What's measured vs. assumed:** Only the fall from 9% to 5% is measured, which means about 44% fewer trials now convert. Sales' report that mid-size teams stall during setup hasn't been measured. Neither has the idea that setup stalls caused the drop.
> - **Possible causes:**
>   - The trial mix shifted toward smaller or less serious teams.
>   - Mid-size teams hit friction during setup (the sales view).
>   - A release or onboarding change made it harder to get started.
>   - Teams finish setup but don't see the product's value before the trial ends.
> - **How established each area is:** The framing rates each area on a scale from novel and hand-built to off-the-shelf utility.
>   - **Onboarding and team setup:** Probably built specifically for your product. If it turns out to be the cause, it's worth investing in.
>   - **Funnel analytics by team size:** Unknown, and it needs checking first. Without it, `find` can't test the sales explanation. If it's missing, adopting a standard analytics tool is better than building one.
>   - **What mid-size teams need during setup:** Unknown until `find` names the specific jobs.
>
> The constraints are in the file: Sam Rivera owns it, there are no pricing changes, and there's no new mobile app.
>
> ## Before or during `find`, three data questions to answer
>
> 1. Did the trial mix change by team size over the two quarters?
> 2. At which funnel step does conversion drop for mid-size teams compared with smaller ones?
> 3. Did a release or onboarding change start around the same time as the decline?
>
> The file also contains a suggested `workspace.toml` entry. I didn't add it, so you can register it through `work-intake` or add it to the initiative's backlog by hand.
>
> ## Next step
>
> - **Run `intent find` (recommended):** It ranks the jobs mid-size trial teams need done, starting with the three questions above.
> - **Answer the three questions first:** You'd bring the funnel data back before running `find`.
>
> Which would you like?

`git status --short` before: `(clean)`; after: `?? docs/`

## Longer route, turn 3

**Request:**

> Go ahead with the step you recommended.

**Reply:**

> You're on the longer route, step 2 of 6: find. The top opportunity is helping mid-size teams **get set up and reach real value within the trial, without the person running the trial losing weeks to it**.
>
> I saved the assessment to `docs/product/shaping/trial-conversion-decline/opportunity-assessment.md`, next to the situation framing.
>
> **I had no interviews or funnel data, so I estimated every rating myself.** Treat the ranking as a starting guess for Sam Rivera to correct.
>
> ## How it was scored
>
> The jobs belong to the trial champion at a mid-size team: the person who starts the trial, sets it up for colleagues, and makes the case to buy. I listed 12 jobs: 7 about getting things done, 3 about how the champion wants to feel, and 2 about how others see them.
>
> Each job gets an importance score and a satisfaction score from 1 to 10, combined as: opportunity score = importance + max(importance − satisfaction, 0). Jobs that matter a lot but are poorly served today score highest.
>
> ## Top opportunities
>
> | Rank | Job | Type | Score |
> |---:|---|---|---:|
> | 1 | Get the whole team set up and working together within the trial window | Getting things done | 15 |
> | 2 | Prove the product works on a real team workflow before the trial ends | Getting things done | 14 |
> | 3 | Feel confident that setup won't take weeks of my time | Feeling | 13 |
> | 4 | Bring existing work and data across from current tools | Getting things done | 12 |
> | 5 | Avoid the worry of a failed rollout I personally championed | Feeling | 12 |
>
> Ranks 1–3 describe the same underlying opportunity, so I'd focus the next step on them. Data import (rank 4) and getting unstuck when setup goes wrong (rank 7, score 11) look like the most likely specific blockers within it. The lowest scores went to meeting company access policy (7) and feeling in control of what teammates can see (5).
>
> ## What could change the ranking
>
> The ranking assumes sales is broadly right that setup is the problem. Three checks could change that:
>
> - **Trial mix by team size:** If more small or casual trials came in, part of the drop is just a change in who's trialing.
> - **Where mid-size teams drop off:** This shows whether setup (rank 1) or proving value (rank 2) is the bigger gap.
> - **Release timing:** A product change that lines up with the start of the decline would point to a specific cause.
>
> Five to eight short interviews with champions from mid-size trials, both converted and lapsed, would replace my estimated importance scores with real ones.
>
> ## Next step
>
> - **Run `intent diverge` on ranks 1–3 (recommended):** It produces several comparable options for helping mid-size teams set up and reach value within the trial.
> - **Correct the scores first:** You or Sam adjust the ratings, and I re-rank before diverging.
> - **Get the data first:** Run the three checks or the interviews, then come back to re-score.
>
> Which would you like?

`git status --short` before: `?? docs/`; after: `?? docs/`

## Longer route, turn 4

**Request:**

> Go ahead with the step you recommended.

**Reply:**

> You're on the longer route, step 3 of 6: diverge. I wrote up five options and recommend **assisted setup for mid-size trials**: a short setup session with a specialist, plus done-for-you data import. It's the cheapest option to undo, and each session shows where teams really get stuck, which the other options need to know before anyone builds them.
>
> The options are saved to `docs/product/shaping/trial-conversion-decline/solution-options.md`.
>
> ## The options
>
> | Option | What it is | Main bet | Status |
> |---|---|---|---|
> | Assisted setup for mid-size trials | Spot mid-size trials early and offer a specialist setup session plus help with data import | Human help lifts conversion and costs less than the revenue it brings back | Recommended |
> | Guided team setup | A self-serve setup path built for teams: bulk invites, role templates, guided import | Setup steps like inviting, roles and import are where teams stall | Parked |
> | Value before full setup | A ready-made workspace so a team can run one real workflow on day one | Seeing value early converts teams better than finishing setup | Parked |
> | Champion toolkit | Team progress view and a shareable trial summary for whoever approves the budget | Teams stall on internal buy-in and approval, not on setup | Parked |
> | Activation-based trial clock | The trial runs on team progress instead of the calendar | Teams run out of time before they run out of patience | Parked |
>
> Each parked option says when it would come back. For example, "value before full setup" is the strongest fallback if teams finish setup but still don't buy. Nothing has been deleted, so any option can be picked up later.
>
> This is my recommendation, not a decision. Sam Rivera chooses the option.
>
> ## Decisions for Sam Rivera
>
> - **Does the trial clock count as a pricing change?** The activation-based trial clock changes trial terms, which may fall under "no pricing changes." If Sam says it does, that option is rejected.
> - **Can we staff it?** Assisted setup moves cost onto people, so it needs onboarding or customer-success capacity.
>
> ## What must be true for any option
>
> - **The drop is mostly among mid-size teams.** If it isn't, none of these options will recover it.
> - **Mid-size trials can be spotted soon after signup.**
> - **Conversion can be measured by team size.** This is still unconfirmed.
> - **No single release caused the drop.** If one did, fixing it might beat every option here.
>
> ## Next step
>
> - **Run `intent de-risk` on assisted setup (recommended):** It tests that option's riskiest assumption, which is that human help measurably lifts mid-size conversion compared with a group that gets no help. It also sets a kill condition, meaning the result that would make you drop the option.
> - **Go straight to `intent bet`:** Commit to a direction now and skip the assumption test.
> - **Revise the options first:** Sam weighs in on the trial-clock question or picks a different option before de-risking.
>
> Which would you like?

`git status --short` before: `?? docs/`; after: `?? docs/`

## Longer route, turn 5

**Request:**

> Go ahead with the step you recommended.

**Reply:**

> You're on the longer route, step 4 of 6: de-risk. The test plan for assisted setup is written, but **there's no result yet**. Someone has to run a data check and a pilot first, and each has a pass/fail line set in advance.
>
> It's saved to `docs/product/shaping/trial-conversion-decline/validation-notes.md`. That's the file the next step, `bet`, looks for.
>
> ## What's being tested
>
> **Riskiest assumption:** Having a person help mid-size teams through setup raises how many convert, compared with similar teams that get no help. So far, the only evidence that setup is the problem is what sales has said.
>
> **Cost of being wrong:** Low and easy to undo. The pilot needs no product changes, involves only a small group of trials, and can stop at any time. So the pilot itself is the test: specialists do the setup by hand and log every place a team gets stuck.
>
> ## The pass/fail lines, set before any results
>
> These lines were fixed on 2026-10-12. They must not be moved after results come in.
>
> **Gate 0 is a data pull before the pilot starts.**
> - Stop if mid-size trials account for less than half of the lost conversions. In that case assisted setup can't recover the decline, and the next move is to go back to `intent find`.
> - Stop if fewer than 70% of mid-size trials can be identified by day 2 of the trial.
>
> **Gate 1 is the pilot itself.** New mid-size trials are split at random: half are offered help, half aren't. You pick one of two rules from last quarter's volume before starting:
> - **About 435 mid-size trials per group or more:** The pilot passes only if the helped group converts at least 4 points higher, at 95% confidence. That's the size of the overall drop. The 435 figure assumes mid-size teams convert at about 5% like everyone else. Recalculate it once Gate 0 gives the real mid-size rate.
> - **Fewer trials (more likely):** The pilot uses 15 helped teams and passes only if all three hold:
>   - At least 10 of the 15 teams have most invited teammates active by the end of week 1.
>   - Specialists spend 3 hours or less per team on average.
>   - The helped group converts better than the unhelped group, even if the gap is too small to prove.
> - **Change direction instead of stopping** if at least 8 of the 15 logs show teams stuck on getting approval or budget rather than on setup. That points to the champion toolkit option instead.
>
> ## Before the pilot can start
>
> - **Who runs it:** Someone needs to pull the Gate 0 data and staff the specialist sessions. I can't run those.
> - **Sam Rivera confirms the 3-hour cap:** It's my proposal. Sam should check it against average contract value, so that specialist time per paying team costs less than that team's first-year revenue.
>
> ## Next step
>
> - **Run Gate 0 and the pilot, then come back to `intent de-risk` (recommended):** I'll compare the results with the lines above and give a go or no-go verdict.
> - **Go to `intent bet` now:** Commit to a direction without results. The bet would record "untested" as a risk you're knowingly taking on.
>
> Which would you like?

`git status --short` before: `?? docs/`; after: `?? docs/`

## Longer route, turn 6

**Request:**

> The riskiest assumption survives: assume the test passed. Continue with the step you recommended for the longer route.

**Reply:**

> You're on the longer route, step 5 of 6: bet. The bet is placed on **assisted setup for mid-size trials**, with a proposed 12-week window and medium confidence.
>
> It's saved to `docs/product/shaping/trial-conversion-decline/bet.md`. I also marked the test plan in `validation-notes.md` as passed. The note says you told me to treat it as passed on 2026-10-12, and that no data has been gathered yet.
>
> ## The bet
>
> - **Option:** Spot mid-size trials by day 2, offer each a setup session with a specialist plus done-for-you data import, and log every place a team gets stuck.
> - **Time budget:** 12 weeks, one quarter. This is my proposal, and Sam Rivera should confirm it.
> - **Confidence:** Medium, because the test result is assumed rather than measured. Real results would justify raising it.
> - **Other options:** Guided team setup, value before full setup, champion toolkit, and activation-based trial clock stay parked, not rejected.
>
> ## Why this option
>
> - It addresses the three top-ranked jobs at once: getting the team set up, proving value within the trial, and not costing the champion weeks.
> - It needs no product changes and can stop at any time.
> - The session logs will show which parked option to build next, if any.
>
> ## Risks taken on knowingly
>
> - **Assumed, not tested:** The test result is assumed, not measured.
> - **Doesn't scale by itself:** Costs grow with each new mid-size trial.
> - **Needs people:** It needs onboarding or customer-success staff the team may not have.
> - **Shows that help works, not what to build:** Even if it works, it won't show which product change could replace the specialists.
> - **Some of the drop may be unreachable:** Any part of the drop caused by a shift in who signs up is out of its reach.
>
> ## What would reverse it
>
> The pass/fail lines set on 2026-10-12 still apply, so the bet reverses if real results miss them:
>
> - **Fewer than half of the lost conversions are mid-size.**
> - **Fewer than 70% of mid-size trials can be spotted by day 2.**
> - **The pilot misses its bar.** That bar is either a 4-point lift at higher volume, or the three-part check across 15 helped teams.
>
> If teams mostly stall on approval or budget rather than setup, the plan switches to the champion toolkit instead.
>
> ## Next step
>
> - **Run `intent map` (recommended):** It lists what the program needs to work and whether to build, buy, partner for, or adopt each piece. Examples are spotting mid-size trials, scheduling specialist sessions, assisted data import, session logging, and measuring conversion by team size.
> - **Adjust the bet first:** Sam changes the 12-week window or the confidence level before mapping.
>
> Which would you like?

`git status --short` before: `?? docs/`; after: `?? docs/`

## Longer route, turn 7

**Request:**

> Go ahead with the step you recommended.

**Reply:**

> You're on the longer route, step 6 of 6: map. This was the last shaping step, so the bet is ready to hand off to build.
>
> The map is saved to `docs/product/shaping/trial-conversion-decline/capability-map.md`. It lists 11 things the program needs, in three groups, and says for each whether to build it or buy it. I proposed all of these labels, so Sam Rivera should confirm them.
>
> ## What the program needs
>
> | Group | Build | Buy |
> |---|---|---|
> | Finding and routing trials | Ask for team size at signup; flag mid-size trials by day 2 | Random split into helped and unhelped groups; offering and booking sessions |
> | Delivering the help | Setup playbook; specialist setup session; help with data import | — |
> | Learning and measuring | Turning session logs into a ranked list of where teams get stuck | Session logging; conversion by team size; specialist cost per paying team |
>
> "Build" here includes people and process the team owns, such as the playbook and the sessions, not just code. No item was marked both standard and differentiating, so there were no conflicts to resolve.
>
> ## Suggested build order
>
> This is a recommendation, not a requirement:
>
> 1. Ask for team size at signup.
> 2. Flag mid-size trials by day 2.
> 3. Write the setup playbook.
> 4. Run the specialist setup sessions.
> 5. Add help with data import.
> 6. Turn the session logs into a ranked list of where teams get stuck.
>
> **Conversion reporting by team size has to be in place before step 1.** It's on the buy list, so it isn't in the build order, but the first data check depends on it. For the other bought items, use tools you already have wherever possible: an experimentation or feature-flag tool, a scheduling tool, fields in your CRM, and a spreadsheet.
>
> ## Decisions for Sam Rivera
>
> - **Specialist capacity:** If no one can be moved onto the sessions, an outside onboarding firm could run them instead.
> - **Customer data during import:** Specialists would handle trial teams' data. That needs a consent step and access rules before sessions start.
> - **The build-or-buy labels:** Every item's label is my proposal.
>
> ## Suggested workspace.toml entry
>
> ```toml
> {path = "docs/product/shaping/trial-conversion-decline/capability-map.md", kind = "design", source = {mode = "repo-origin"}, summary = "Capability map for assisted setup for mid-size trials: 6 Build, 5 Buy, signup team size first", needs = ["docs/product/shaping/trial-conversion-decline/bet.md"]},
> ```
>
> I haven't added this to `workspace.toml`. You can register it through `work-intake` or add it by hand.
>
> ## Next step
>
> - **Hand off to build through `work-intake` (recommended):** It registers the shaping work and turns the six build items into delivery work.
> - **Write an initiative brief with `intent canvas`:** A one-page Lean Canvas summary of the initiative, useful for getting sign-off from Sam and others.
> - **Design the build items with `architect-design`:** This mainly covers how detection plugs into signup and the import tooling.
>
> Which would you like?

`git status --short` before: `?? docs/`; after: `?? docs/`

## Standalone ground

**Request:**

> Owner: Sam Rivera. Non-goals: no billing, no mobile app. Save artifacts under docs/discovery/home-care/. Standalone, no full discovery: ground our home-care visit scheduling product in how care coordinators actually plan visits today, and bound the MVP scope.

**Reply:**

> Ground mode is done: I wrote the two files under `docs/discovery/home-care/`. **None of the domain claims in them have been checked against a source yet.** The research skill (`desk-research`) isn't installed and web search was declined, so I worked from my own knowledge. Each claim is written as a hypothesis with an ID from R1 to R14, and each ID lists how to check it.
>
> ## What I wrote
>
> - **`domain-framing.md`** describes how care coordinators likely plan visits today:
>   - They copy a recurring weekly schedule forward and edit the exceptions.
>   - They put keeping the same caregiver with a client ahead of shorter travel.
>   - Much of their day goes to re-planning after call-offs.
>   - The schedule on file drifts from what actually happened.
>   - It lists six obvious designs likely to fail, such as automatic travel optimization, building each week from scratch, and making caregivers install an app. It treats this as a new product with no existing system, because the repo has no product code.
> - **`scope-boundary.md`** sets the MVP: one agency's coordinators keep a recurring schedule, assign caregivers with the constraints in view, and re-plan quickly. The coordinator makes the calls; the tool doesn't auto-assign. It lists 14 excluded features, each with its reason:
>   - Your two non-goals, billing and a mobile app, plus payroll as part of billing.
>   - Electronic visit verification (the required check-in/check-out record for some publicly funded visits), because it needs a device at the visit and feeds billing.
>   - Automatic scheduling and route optimization, integrations, a client or family portal, a shift marketplace, credential management, multi-branch reporting, and built-in chat.
>
> ## Decisions for Sam
>
> - **Which segment comes first (R1):** non-medical personal care, which runs as multi-hour shifts, or skilled home health, which is short visits by a nurse or therapist. This changes visit length, matching rules and constraints, so settle it first.
> - **Is this really a new product (R13)?** Confirm no scheduling system of ours already exists outside this repo.
> - **Clients' authorized hours:** tracking them as a ledger is out of scope. Coordinators type in a weekly hour cap instead. This line is the one most likely to creep, so it's worth confirming now.
>
> ## Next steps
>
> 1. **Test the riskiest assumption (recommended):** probably R5, that re-planning after call-offs is most of a coordinator's day. The scope depends on it. A one-week time diary with 2–3 coordinators would settle it.
> 2. **Re-run grounding with real sources:** once `desk-research` is installed or web search is allowed, check R1–R14 and update both files.
> 3. **Hand off to build:** pass the work to `work-intake` once you accept the boundary.
>
> Want me to start any of these?

`git status --short` before: `(clean)`; after: `?? docs/`

## Standalone canvas

**Request:**

> Owner: Sam Rivera. Non-goals: no pricing changes. Save the brief at the default location. Write a simple lean canvas initiative brief for our self-serve onboarding initiative (slug ini-onboarding): problem is setup stalls for mid-size teams, segment is 20-200 seat teams, value proposition is a guided setup in under a day.

**Reply:**

> I wrote the initiative brief (this is the canvas step of the intent skill, which isn't part of any route). It's at `docs/product/initiatives/ini-onboarding.md`.
>
> It uses the simple 5-box Lean Canvas:
>
> - **Owner:** Sam Rivera
> - **Problem:** Setup stalls for mid-size teams.
> - **Customer Segments:** Teams of 20–200 seats.
> - **Unique Value Proposition:** A guided setup that gets a team running in under a day.
> - **Solution:** TBD, because the shape of the guided setup hasn't been chosen.
> - **Key Metrics:** TBD, because there's no baseline yet. I suggested one to start with: the share of 20–200 seat teams that finish setup within a day.
> - **Non-goals:** No pricing changes.
>
> The repo has no `docs/product/initiatives/_template.md` and no `agentbundle-layout.toml`. So I saved to the default path and used a minimal structure: frontmatter, then Value Proposition, then Scope with the non-goals, then open questions. I found no earlier shaping files to pre-fill from.
>
> You may want to add `["ini-onboarding"]` to `workspace.toml` so it shows in the queue. I didn't edit that file.
>
> Next steps you could take:
> 1. Hand it to `work-intake` to start the move to build? The two TBD boxes can stay open for now.
> 2. Run `intent diverge` to compare options for the guided-setup solution?
> 3. Run `intent de-risk` to test whether "under a day" is achievable for teams this size?

`git status --short` before: `(clean)`; after: `?? docs/`

## Diverge, candidate product shapes

**Request:**

> Owner: Sam Rivera. Non-goals: no hardware. Standalone, not a full discovery run: give me candidate product shapes for a neighbourhood tool-lending idea, from a narrow slice to a whole platform, each with its riskiest assumption.

**Reply:**

> **intent diverge mode (shapes), run on its own outside a discovery run.** Owner: Sam Rivera. Non-goal: no hardware, so there are no smart lockers, tracking tags or kiosks. I haven't written any files because there's no discovery plan-tree to attach these to, so the candidates are below.
>
> One thing to know first: there's no framed outcome behind these yet. I've assumed the outcome is "neighbours get the tool they need for a job without buying one." If Sam means something else, like less waste, more community ties or cheaper repairs, the ranking below changes.
>
> ## Candidate shapes
>
> The shapes run from the narrowest slice to a whole platform. Each one also uses a different way of working (the "mechanic").
>
> | # | Shape | Size and mechanic | Riskiest assumption (what would have to be true) |
> |---|---|---|---|
> | 1 | **"Who's got a…?" request board.** One street or building posts a need ("ladder, Saturday") and an owner nearby replies. | Narrowest slice; post a request, an owner answers | Enough people within walking distance own the right tools and will say yes when asked, quickly enough that the borrower doesn't just buy one. |
> | 2 | **Neighbourhood tool catalogue.** Owners list what they have, and borrowers search a map and book. | Neighbourhood; a shared inventory comes first | Owners will list their tools up front and keep the list accurate, even though listing gives them nothing until someone asks. |
> | 3 | **Project kits.** "I'm hanging shelves" brings up the set of tools needed, who nearby has them, and a neighbour who has done the job before. | Goes deeper into one area, from project to tasks to tools and skills; a matching mechanic | People think in projects rather than single tools, and the borrowed know-how is worth enough that they come back. |
> | 4 | **Software for existing tool libraries.** Membership, checkout, reservations and overdue reminders for volunteer-run libraries that already have a physical shelf. | Many libraries; runs the operations of groups that already exist | Volunteer libraries will switch to it from spreadsheets or the tools they already use, such as myTurn or Lend Engine. That needs a clear reason better than "it's newer." |
> | 5 | **Neighbourhood sharing platform.** Tools plus trust profiles, deposits, damage cover and payments, later widening to other items. | Whole platform; a marketplace with trust and money built in | Trust and liability can be handled in software alone, through deposits, ratings and cover, at a cost per loan that's below the price of buying a cheap tool. |
>
> ## Recommendation: start with shape 1
>
> I recommend shape 1, the request board. Its riskiest assumption sits under shapes 2, 3 and 5 too: if neighbours won't lend when asked, none of the peer-to-peer shapes work. It can also be tested in a week or two with a group chat on one street, before any software is built.
>
> The other four are parked, not rejected:
>
> - **Shape 2 (catalogue):** parked. It's the natural next step if shape 1 shows demand but slow replies.
> - **Shape 3 (project kits):** parked. It's the strongest way to stand out, but it rests on shapes 1 or 2 working first.
> - **Shape 4 (library software):** parked. It's a different customer, the library organiser rather than the neighbour, and it competes with existing products. Revisit it if Sam's real audience turns out to be existing tool libraries.
> - **Shape 5 (whole platform):** parked. Liability is a big unknown, and it's the most expensive shape to be wrong about.
>
> **How big to go is Sam's decision.** It's a judgement about value and scope, so I haven't settled it. Shape 1 is the cheapest way to learn. Shapes 4 and 5 are different businesses, not later versions of shape 1.
>
> ## Next steps
>
> Pick one if you like; I won't start any of them on my own:
>
> 1. **De-risk shape 1 (recommended):** set a fail condition for the "neighbours will lend when asked" assumption and plan a small test on one street.
> 2. **Frame the outcome first:** pin down what Sam is actually after so the shapes can be re-ranked against it.
> 3. **Place the bet:** commit to one shape, including the decision on how big to go.

`git status --short` before: `(clean)`; after: `(clean)`

## De-risk, validation plan

**Request:**

> Owner: Sam Rivera. Non-goals: we will not run the sessions ourselves this week. Our converged onboarding product still marks three assumptions to-validate: teams stall on SSO setup, admins want a checklist, and a guided call doubles activation. Turn them into a validation plan with kill conditions and draft the interview guide.

**Reply:**

> This is the validation-plan part of de-risk mode. I've written the plan, the kill conditions and the interview guide to `docs/discovery/onboarding/validation-plan.md`. Sam Rivera is the owner. Per your non-goal, the plan is written for whoever Sam assigns to run the sessions. Nothing is scheduled for us this week.
>
> **The kill conditions.** These are proposals until Sam locks them. Each one is fixed before any session runs.
>
> | Assumption | Kill condition | Activity |
> | --- | --- | --- |
> | A1: Teams stall on SSO | Fewer than 4 of 8 admins name SSO as their sticking point without being prompted. If funnel data exists, it's also killed when SSO isn't the biggest single drop-off. | Admin interviews, plus a look at the onboarding funnel |
> | A2: Admins want a checklist | Both of these fail: fewer than 3 of 8 admins built or used their own tracker for their last rollout, **and** fewer than 4 of 6 test users find their next step using the checklist without help | Same interviews, plus a usability test of a clickable checklist |
> | A3: A guided call doubles activation | The group offered a call activates at less than 2× the rate of the group that isn't. It's also killed if fewer than 30% of offered admins book a call. | A pilot where a person runs the calls by hand, with no product build |
>
> **A3 is the riskiest.** It makes the strongest claim, it's the only one that would cost ongoing staff time, and interviews can't prove that a call causes higher activation. So it gets a pilot with two groups of new sign-ups. Teams are assigned by alternating sign-up order, and the whole offered group is compared, including teams that decline the call. That way, teams who choose to book can't inflate the result. A result between 1.5× and 2× means the claim gets reworded to "improves activation" rather than dropped.
>
> **The interview guide** covers A1 and A2 in one 30-minute session with 8 admins. It asks admins to walk through their actual setup step by step. SSO and checklists are never mentioned until the admin raises them, and only SSO mentions they make without prompting count toward A1. For A2, it asks whether they already kept a checklist or tracker of their own, rather than whether they'd like one. The file also has:
> - the usability-test plan for the checklist
> - a short form for whoever runs the pilot calls to fill in after each call
> - a template for summing up results against each kill condition
>
> **Sam needs to decide four things before any session runs:**
> 1. Lock or change the kill conditions, and date them.
> 2. Define "activation", and set the pilot's length and minimum group size.
> 3. Assign who recruits participants, who runs the interviews and who runs the calls.
> 4. Confirm whether onboarding funnel data exists for the A1 check.
>
> The repo had no discovery workspace file to update, so the plan is a standalone document. I haven't committed it.
>
> When the transcripts and pilot results come back, would you like me to run de-risk mode again to compare them against each kill condition and mark each assumption as validated or refuted?

`git status --short` before: `(clean)`; after: `?? docs/`

