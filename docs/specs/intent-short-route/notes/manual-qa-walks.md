# Manual QA walks: intent-short-route

Run on 2026-10-11 with `claude -p` in fresh git-tracked copies of the post-fold projection (product-engineering, core, and architect, including Core's `shaping-reviewer`), with `--setting-sources project,local`, `--permission-mode acceptEdits`, and `--allowed-tools "Skill Read Write Edit Agent Glob Grep"`. The walk's write, edit, and dispatch permissions come from those command-line grants, not from the skill's frontmatter. Requests and replies are quoted verbatim.

The AC-0039 walk runs on the `intent` skill after it gained the instruction to open each mode's reply with the user's stage. The no-route step runs after that instruction gained "do not assume a route". Earlier walks, before either instruction, are summarised at the end.

## AC-0008: a request that fits both routes

**Request:** We want to add usage-based pricing for our API product. It is one feature that one team can build in a few weeks, but it also changes how we make money and we have not looked at what competitors charge. Which way should we shape this?

> This fits two routes, and one answer decides which.
>
> - **Short route:** the build is one feature for one team over a few weeks. That points to this route, which starts with `intent frame` (naming the outcome you want and the bet behind it).
> - **Longer route:** the change affects how you make money, and you haven't looked at competitor pricing yet. That makes it a big bet, which points to this route. It starts with `frame-situation`, which turns the idea into a clear problem statement, then looks at opportunities and compares options before you commit.
>
> The full-product discovery route doesn't apply, because this is one change to an existing product.
>
> **One question:** has the person who owns revenue already decided to move to usage-based pricing, so the open work is mainly setting the price and building it? Or is it still open whether usage-based pricing is right for you at all?
>
> - **Already decided:** take the short route. Checking competitor prices becomes the first test during `de-risk`, the step that tests the bet's riskiest assumption.
> - **Still open:** take the longer route. Competitor pricing and the effect on revenue get looked at before anything is built.
>
> Once you answer, I can start the first step of whichever route fits, or you can skip it.

- `git status --porcelain` before: (clean)
- `git status --porcelain` after: (clean)

Result: one question, no file change. **Pass.**

## AC-0038 and AC-0039: the route reply

**Request:** We are thinking about letting teams export their dashboards as PDF files. It is one feature for one team, a few weeks of work, and customers have asked for it. Which way should we shape it?

> I'd take the **short route**. You can already name one outcome (teams can export a dashboard as a PDF), it belongs to one team, it's a few weeks of work, and customers have asked for it. The longer route is for problems that are still unclear or bets that are large. The supervised route is for a raw idea for a whole product. Neither fits here.
>
> The short route has three steps:
>
> 1. **Frame:** state the outcome and why customers want it. For example: are they sharing dashboards with people who have no login, keeping records for audits, or presenting in meetings?
> 2. **De-risk:** find the assumption most likely to sink the plan and test it cheaply. Decide in advance what result would make you drop it. Here the obvious candidate is whether a plain PDF actually solves the customers' problem. If what they really need is a scheduled email or a shareable link, a PDF misses.
> 3. **Decompose:** split the tested plan into pieces you can build, then hand it off to be built.
>
> You'd start at step 1. Want me to run **frame** now? You can also skip it. If you're already sure what "done" looks like, the feature counts as shaped and can go straight to build intake.

Result: names the short route, lays out its three steps, says the user starts at step 1, and offers `frame` without running it. **Pass.**

## AC-0039: frame

**Request:** Take the short route. Frame it. Facts: owner is the Head of Analytics; scale is app; non-goals are scheduled email reports, live share links, and formats other than PDF; the riskiest assumption is that customers need a static file rather than a share link; in September 2026 interviews 8 of 10 customer admins said they would use it weekly. Save it in this repo at docs/product/intents/dashboard-pdf-export.md.

> I've framed the intent and saved it at `docs/product/intents/dashboard-pdf-export.md`. It isn't committed yet. **Short route, step 1 of 3: frame.**
>
> **What it records**
> - **Level and status:** a feature-level intent, Draft, owned by the Head of Analytics.
> - **Scale and maturity:** scale is `app`. I marked it as `brownfield` (adding to a product that already exists) because the dashboards already exist. Please confirm that.
> - **Non-goals:** scheduled email reports, live share links, and formats other than PDF.
> - **Riskiest assumption:** customers need a static file rather than a share link. This is listed first.
> - **Evidence:** 8 of 10 admins interviewed in September 2026 said they would use it weekly.
>
> **Parts I drafted that need your confirmation**
> - **Outcome metrics:** you didn't give any, so I proposed some and labeled them as proposals.
>   - What you track and can move: the weekly share of admins who export a PDF.
>   - What it should lead to: fewer customer requests to get dashboards out of the product.
>   - What must not get worse: load time, export reliability, and exported numbers matching the dashboard.
> - **The customer need:** I inferred why customers want this from the requests and interviews. Please check it.
> - **Unknown:** I couldn't check your roadmap or notes. The Google Drive search wasn't permitted in this session, and the file records that.
>
> **One gap in the evidence:** the 8-of-10 figure is what people said they'd do, not what they've been seen doing. The interviews also didn't ask whether people want a file or a link, so they don't test your riskiest assumption. Step 2 (de-risk) would need to.
>
> **Next step:** run a quick review to check the intent is well-formed before de-risk. A reviewer agent reads it with no context from this conversation. Want me to run it?

Result: names the stage ("Short route, step 1 of 3: frame"), recommends the shaping review, and starts nothing. **Pass.**

## AC-0039: after the shaping review passes

**Request:** Run the shaping review.

> The intent passed the shaping review with no problems found. A reviewer agent with no context from this conversation checked it against seven conditions:
>
> - it states an outcome, not a solution
> - it has non-goals
> - it names the riskiest assumption
> - its level fits (no parent intent is named, so there was nothing to compare against)
> - its decomposition is still empty, which is correct before it's broken down
> - it has its own owner
> - its header fields are complete
>
> I added `Shaping-reviewed: 2026-10-11` to the intent's header fields. That edit doesn't change what the intent says, so the review still holds. If you later change the outcome, the customer need, the assumptions, or the non-goals, run the review again. The file is still not committed.
>
> **Short route, step 1 of 3 (frame) is complete.** Two possible next steps:
>
> 1. **De-risk (recommended):** test whether customers need a static file rather than a share link, and decide in advance what result would make you drop the feature. The September interviews don't settle this, because they measured stated interest and didn't ask about file versus link.
> 2. **Adversarial read first (optional):** a reviewer tries to break the riskiest assumption and the non-goals before you de-risk. It might return an open question or a test idea, or nothing at all.
>
> Which would you like?

Result: names the stage, recommends `de-risk`, and offers the adversarial read as optional. **Pass.**

## AC-0039: de-risk sets the bar

**Request:** Skip the adversarial read. De-risk it and set the bar for a 4-week concierge test with the 8 admins who said weekly.

> **Short route, step 2 of 3: de-risk.** I've set the bar for the 4-week concierge test, a test where your team makes each PDF by hand when an admin asks for one. The bar is saved in the intent file. The test hasn't run, so the verdict is marked pending. The file is still not committed.
>
> **The bar (set 2026-10-11, before the test)**
>
> The bet survives only if both of these hold at the end of week 4:
>
> 1. **They keep coming back:** at least 5 of the 8 admins ask for a PDF in at least 3 of the 4 weeks.
> 2. **They pick the file over a link:** at least 5 of the 8 choose the PDF over a link to the live dashboard in most of their requests. Each of them must say why the link wouldn't have worked.
>
> If either line misses, the bet is dropped. You can change the bar before the first request but not after.
>
> **Rules that keep the result honest**
> - **Wait for requests:** make one standing offer at the start. Don't send reminders or PDFs nobody asked for. Otherwise you'd be measuring your own follow-up, not their demand.
> - **Offer both every time:** each request gets a choice of a PDF or a live link. That is the only part of the test that checks your riskiest assumption.
> - **Log every request:** record the admin, the week, which they picked, and their reason.
>
> **Why 5 of 8:** it's a majority, and it allows for the usual drop-off between what people say in interviews and what they actually do. It's a judgment call, not a statistic. As owner, the Head of Analytics can move it before the test starts.
>
> These 8 are the most enthusiastic people from your interviews, so this is a best-case group. If the bet fails with them, it fails. If it passes, that still doesn't prove broad demand. The weekly-export metric tracks that after launch.
>
> **Process notes**
> - **A deviation from the usual approach:** for a change this easy to reverse, the default would be to build a cheap version early and learn from it. You chose to test before building, and the file records that choice.
> - **What's left blank:** the `De-risked` date stays empty until the test has run.
>
> **Next steps**
> - **Record the verdict when the test ends:** bring me the request log and I'll compare it to the bar. If the bet survives, the next step is breaking it into buildable pieces (step 3). If it's killed, the next step is reframing the intent.
> - **Optional, before you start:** I can write the runbook for the test, covering the offer email, the request log, and the check-in questions.
> - **Commit:** want me to commit the intent file now?

Result: names the stage, predeclares the bar, and leaves the verdict pending. **Pass.**

## AC-0039 (supporting): results that do not match the bar

**Request:** For this walk, treat today as 9 November 2026: the concierge test you set ran 12 October to 8 November 2026. 7 of the 8 admins asked for and forwarded a PDF at least twice, both largest accounts did the same, and in the follow-up none said a link or email would have served better. Record the verdict.

> **Short route, step 2 of 3: de-risk.** I recorded the verdict as **undetermined**, not survived. The results look strong, but they're reported in different terms from the bar we set on 2026-10-11, so neither line can be checked against them yet. I logged the results in the intent file and left the bar unchanged.
>
> **How the results compare to the bar**
>
> | Line in the bar | What you reported | What's still needed |
> | --- | --- | --- |
> | At least 5 of 8 ask for a PDF in at least 3 of the 4 weeks | 7 of 8 asked and forwarded at least twice | For each admin, how many different weeks they asked. "Twice" could mean 2 weeks, which is below the bar. |
> | At least 5 of 8 pick the PDF over a live link in most requests, each giving a reason | None said a link or email would have served better | Whether each request offered a choice between a PDF and a link, which one each admin picked, and their reason |
>
> The point about the largest accounts is encouraging, but it isn't part of the bar, so it doesn't change the verdict.
>
> **The fastest way to settle it:** send me the request log from the test. From it I need:
> - each admin's requests by week
> - the choice they made on each request, if one was offered
> - the reason each admin gave
>
> If both lines are met, the bet survives and I'll set the `De-risked` date. Then you're ready for step 3: breaking the work into buildable pieces.
>
> The bet does **not** survive as declared if either of these is true:
> - fewer than 5 admins asked in 3 or more weeks
> - the link option wasn't offered on each request
>
> If it doesn't survive, you can rerun the second line as a short test that offers the choice on every request, or reframe the intent. The bar shouldn't be loosened after the fact to fit the result.
>
> The intent file is still not committed. Want me to commit it now, or wait until the verdict is settled?

Result: names the stage and records the verdict as undetermined because the reported results do not map onto the predeclared bar. It does not loosen the bar. Recorded as evidence that the mode holds its gate.

## AC-0039 (supporting): decompose refused before a verdict

**Request:** Re-run the shaping review if it is needed, then decompose it.

> I re-ran the shaping review, and it passed. I haven't decomposed the intent, because the bet hasn't passed its test yet.
>
> **Shaping review:** a re-run was needed. Adding the concierge test results changed the intent's evidence, which cancels the 2026-10-11 review. The fresh review found no problems, and I updated `Shaping-reviewed` to `2026-11-09`.
>
> **Why I stopped before decomposing:** step 3 only runs on a bet that survived step 2. Right now the verdict is undetermined. If I break it into buildable pieces now, every piece inherits an assumption nobody has confirmed: that customers need a file rather than a link. The results look promising, but they don't yet show whether either line of the bar was met.
>
> The intent file is still not committed. Three ways forward:
>
> 1. **Send the request log (recommended).** I need each admin's requests by week, whether a PDF-or-link choice was offered each time, and what they picked and why. If both lines hold, I'll record the bet as survived and decompose it in the same pass.
> 2. **Rerun the file-versus-link line.** If the link option wasn't offered on each request, you can't score that line from this test. A short follow-up that offers the choice every time would settle it.
> 3. **Have the owner accept the risk.** The Head of Analytics can decide to build without a clear verdict. I'd record that decision and who made it in the intent, then decompose. The file would show the riskiest assumption was never confirmed, not that it passed.
>
> Which would you like?

Result: re-runs the shaping review the evidence change required, then declines to decompose an undetermined bet and offers three options. Recorded as evidence that no mode runs ahead of its gate. This reply names no stage. It led to the instruction covering replies that stop at a gate; the re-test is in § AC-0039: decompose stopping at its gate.

## AC-0039: de-risk survive, short route shown

**Request:** Here is the request log, weeks 1 to 4. Every request offered a choice of a PDF or a link to the live dashboard. Admins A, B, C, D, E and F each asked in 3 or 4 of the weeks; G asked in 2 weeks; H asked once. A to F picked the PDF on every request; G and H picked the link. Reasons for the PDF: A, B and C send it to executives without logins; D and E attach it to monthly client reports; F files it for audit. Record the verdict.

> **Short route, step 2 of 3: de-risk. Verdict: survived.** Both lines of the bar set on 2026-10-11 were met, and the bar wasn't changed. The choice of a PDF or a live link was offered on every request, so both lines count.
>
> | Line | Bar | Result |
> | --- | --- | --- |
> | They kept coming back | At least 5 of 8 asked in 3 or more of the 4 weeks | 6 of 8 (A to F) |
> | They picked the file over a link | At least 5 of 8 picked the PDF in most requests and gave a reason | 6 of 8 (A to F) picked the PDF every time, each with a reason |
>
> The reasons fall into three needs, and each one depends on the file staying fixed:
> - **Reaching people without a login:** A, B and C send it to executives.
> - **Client reports:** D and E attach it to monthly reports.
> - **Audit records:** F files it.
>
> G and H chose the link and asked rarely. A link suits some admins, but it doesn't meet the main need here. These 8 were still a best-case group, so wider demand is something to measure after launch.
>
> **What I updated in the intent file**
> - **Test results:** added the request log and the verdict.
> - **De-risked date:** set to `2026-11-08`, the day the test ended.
> - **Riskiest assumption:** now marked as having passed the test.
> - **Evidence:** replaced "assumed" with what the test actually observed.
>
> The request log counts as new evidence, so this morning's shaping review no longer covers the current file. I added a note next to `Shaping-reviewed` saying a fresh review is due. The file is still not committed.
>
> **Next:**
> 1. **Re-run the shaping review, then decompose (recommended).** This is step 3 of the short route. It breaks the intent into pieces that can each be shipped and tested on their own, then hands them to build.
> 2. **Place the bet formally instead.** This is the longer route's commitment step. It's usually more process than one feature needs.
>
> Shall I do option 1?

Result: names the stage, records survive against the unchanged bar, and marks decompose (step 3 of the short route) as recommended. **Pass.**

## AC-0039: decompose

**Request:** Decompose it.

> **Short route, step 3 of 3: decompose. Done.** The intent breaks down into a single piece of buildable work: an admin exports the dashboard they're looking at as a PDF. The PDF shows the same figures as the screen at that moment and never changes afterwards. That piece covers the intent's whole outcome and can ship and be tested on its own.
>
> **Shaping review:** I re-ran it on the final version, which includes the request log, the verdict and the decomposition. It found no problems. `Shaping-reviewed` and `Decomposed` are both set to `2026-11-09`.
>
> **What the handoff to spec writing contains**
> - **Context:** the outcome, the three uses the test found, the proposed metrics, the non-goals, and the design notes. The uses were sending to executives without a login, attaching to client reports, and filing for audit.
> - **Boundaries:** one dashboard per export, as it's currently shown, released behind a feature flag. It depends only on the existing dashboard view.
> - **Questions for the spec to answer:**
>   - **Data access:** who may export, and whose data permissions decide what the PDF contains? This is the important one, because the file leaves the product.
>   - **Audit details:** does the PDF need to show when it was exported, from which dashboard, and by whom?
>   - **Page breaks:** how long or wide dashboards split across pages without losing figures.
>   - **Unsupported charts:** which chart types must render, and what happens to one that can't.
>
> **Why one piece, not several (also recorded in the file)**
> - **Not one per use:** all three uses need the same fixed, faithful file, so splitting by use would give three copies of one feature.
> - **Audit details stay inside:** they're a question for this piece, because nobody asked for them without the PDF itself.
> - **No "basic export first, layout later":** a PDF that loses figures on long dashboards wouldn't be usable on its own.
>
> **Next: hand it off to build (recommended).** The spec-writing step takes it from here and runs its own approval gates on the spec and the plan. The data-access question will probably also trigger a security review there. I haven't started any of that.
>
> The intent file is still not committed. Want me to commit it and start the hand-off?

Result: names the stage ("Short route, step 3 of 3: decompose"), produces one leaf delivery contract, recommends the hand-off to build, and names the spec stage's own approval gates without running them. It calls the hand-off "the spec-writing step" rather than naming `work-intake`. **Pass**, with that wording noted.

## AC-0039: decompose stopping at its gate

Run after `intent/SKILL.md` § Modes was extended to replies that stop at a gate or decline to run. Fixture: a copy of the framed, reviewed, not yet de-risked intent from the review-pass walk.

**Request (new session):** We are on the short route. Decompose docs/product/intents/dashboard-pdf-export.md.

> Short route, step 3 of 3: decompose. I haven't decomposed this intent yet, because it hasn't been de-risked.
>
> `docs/product/intents/dashboard-pdf-export.md` shows `De-risked: no`. I found no de-risk verdict anywhere else under `docs/`. Decompose needs the riskiest assumption to have passed its test first. Otherwise a wrong bet gets split into specs that inherit it.
>
> That risk is real here. The intent names its own riskiest assumption: customers need a static file, not a share link. If a share link would do the same job, the work needs a different shape. Share links are currently a non-goal, so specs built on the PDF version would have to be thrown away. Two other gaps would also matter in a test:
> - The evidence is stated intent only: 8 of 10 admins in the September 2026 interviews said they'd export weekly.
> - The workaround admins use today isn't recorded.
>
> I haven't changed any files.
>
> Once the assumption survives, decomposing should be quick. The intent is `feature` level at `app` scale, so it's already a leaf. Decompose would produce one delivery contract for `new-spec` (a handoff package for the spec step), with no child intents.
>
> How would you like to continue?
> 1. **Run `intent de-risk` (recommended).** It picks a cheap test for the file-versus-share-link assumption and sets the kill condition (the result that would stop the bet) before the test runs.
> 2. **Record an existing verdict.** If you've already tested this assumption, share the result. If it survived, I'll update the intent and then decompose.
> 3. **Decompose anyway.** If you choose this, I'll log in the intent's `Decomposition` section that the assumption hasn't been tested.

- `git status --porcelain` before and after: unchanged (only the copied skill files and the untracked fixture).

Result: names the stage ("Short route, step 3 of 3: decompose"), declines to run ahead of the de-risk gate, changes no file, and offers three options. **Pass.**

## AC-0039: de-risk survive, no route shown

Fixture: a copy of an earlier walk's intent with the test window and predeclaration dates moved into the past, so the result could be reported as finished. The kill condition text is unchanged.

**Request (new session):** The concierge test in docs/product/intents/dashboard-pdf-export.md ran 1 to 28 September 2026. Results: 7 of the 8 admins asked for and forwarded a PDF at least twice; both of the two largest accounts did the same; in the follow-up, none said a link or a scheduled email would have served them better. Record the de-risk verdict.

> The bet survived. I've recorded the verdict in `docs/product/intents/dashboard-pdf-export.md`. (This was de-risk mode, the step that tests a bet's riskiest assumption before anything is built.)
>
> Each result cleared the line that was set on 30 August 2026, before the test ran:
> - **Admins:** 7 of 8 asked for and forwarded a PDF at least twice. Survive needed at least 5, and 3 or fewer would have killed the bet.
> - **Largest accounts:** both did the same. Survive needed at least one.
> - **Link or email:** in the follow-up, nobody said a link or a scheduled email would have served them better. A single such answer would have killed the bet.
>
> **What I changed in the file:**
> - Added `De-risked: 2026-09-28` to the header.
> - Added a **Verdict** section under the validation hook. It states that the predeclared line was not changed after the results came in.
> - Updated the handoff's evidence and unknowns. Repeat use is now observed. The remaining open question is whether people will keep exporting once they have to do it themselves.
>
> **Two gaps the test doesn't close, also recorded in the file:**
> - The PDFs were made by hand on request. The test shows people want the file, not that they'll use a self-serve export. The post-launch export-rate metric will measure that.
> - The test group was the same admins who asked for the feature. So the assumption that they represent the wider customer base is still untested.
>
> I left Status at `Draft`, because accepting the intent is the owner's call.
>
> Which route are you on? That decides the next step:
> 1. **Short route:** `intent decompose`, which breaks this into a delivery brief or spec.
> 2. **Longer route:** `place-bet`, which formally commits to this bet.

Result: names the mode alone ("de-risk mode"), records survive, and asks which route applies before recommending a next step. **Pass.**

## Earlier walks

- The first walk asked for `de-risk` before the shaping review had passed and never supplied an owner, and its no-route session reported a test that, by the file's dates, had not started.
- A second walk, on the skill before the stage instruction, passed every AC-0039 offer check but most replies did not name the user's stage, and the no-route reply named the short route although none was shown. Those two gaps are why the stage instruction and its "do not assume a route" clause were added.
- None of these is the evidence for AC-0039.
