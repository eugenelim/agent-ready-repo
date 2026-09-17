# Intent: a team using frontend-engineering stops shipping layout defects a glance would have caught

- **Slug:** `rendered-page-visual-inspection`
- **Level:** `feature`
- **Scale:** `app`
- **Maturity:** `brownfield`
- **Parent intent:** none

## Who this is for

A team that installs the `frontend-engineering` pack and builds a web surface
with an agent. They follow the journey: choose a mode, approve the surface
contract, implement, run gates, produce an evidence manifest, get an independent
review. At the end they have a signal that says the surface is done.

The signal can be green while the page is visibly broken to anyone who opens it.

## The gap, stated at pack level

The pack asks for the right thing and cannot make it happen.

- **It asks.** The journey's step 4 promises to run "visual QA against applicable
  states" (`packs/frontend-engineering/JOURNEY.md:157`). The skill's visual-QA
  checklist says "Screenshot taken and observed… assert on what you see, not on
  internal state"
  (`packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md:571`).
- **Nothing executes it.** That checklist is headed "agent-executable, no
  tooling" (`SKILL.md:566`), and its other three items are HTML reading, a CSS
  grep, and a print preview. The pack *does* drive a browser elsewhere — pa11y
  and axe run against headless Chromium (`SKILL.md:531-542`), and `fe-performance`
  directs Lighthouse and DevTools (`fe-performance/SKILL.md:94-103`). So a browser
  is already in the adopter's hands. **No skill drives one in order to look.**
- **Nothing records it.** The manifest's 11 required fields (`SKILL.md:613-623`)
  have `screenshots` — "filenames, Playwright capture, or devtools screenshots" —
  but no field for *what was seen in them*. A filename satisfies the field.
- **Nothing requires it.** `unverified items` accepts "no Chromium" as a written
  reason (`SKILL.md:623`), and `accept-frontend-evidence` asks a human to accept
  the exceptions (`JOURNEY.md:169`). The surface completes.
- **The reviewer cannot cover it.** `frontend-reviewer` reads the diff
  (`tools: Read, Grep, Glob` — `frontend-reviewer.md:4`). Nothing in a diff shows
  one element covering another.

So the pack's own instruction — look at the page — is the one step with no
mechanism, no record, and no consequence for skipping. That is the feature.

## Outcome

- **Input (steerable):** the share of surfaces completed through this pack where
  the rendered page was actually looked at — captured at more than one viewport
  and scroll position, judged, and the judgement written down — rather than
  recorded as a filename or skipped with a reason.
- **Outcome (lagging):** a reader-visible layout failure stops escaping to the
  adopter's users. Concretely: the defects their users or stakeholders report
  after release, of the kind a person notices in seconds — something covering
  something else, text running off its container, a control too small to hit —
  trend to zero, and the ones that do occur were seen and accepted, not missed.
- **Guardrail:**
  1. Bounded cost. A few captures per surface, not a sweep. If this needs dozens
     of states per page, the adopter turns it off and the feature is worthless.
  2. Findings name a reader-visible failure, never a difference from before. A
     deliberate redesign that still holds together produces nothing. *Not* "an
     unchanged page produces nothing" — an unchanged page can be broken, and
     saying otherwise would license suppressing the defects this exists to find.
  3. No new required dependency, and a clean degradation where a browser is not
     reachable (§ When there is no browser).

**Falsifiable proof.** Rebuild the recorded defects below as fixtures, run the
inspection, and require it to name each in reader-visible terms — with at least
one **holdout** fixture it was not built against. Defect 4 is excluded on purpose
(§ What the evidence shows, point 4).

## Opportunity

- **Functional job:** know whether the page a reader will actually get holds
  together — before a reader gets it.
- **Emotional job:** stop privately distrusting a green signal. The cost of a
  check that cannot fail is not the one defect; it is that no later green means
  anything.
- **Social job:** be the team whose pages hold, not the one whose users report
  the obvious thing first.
- **Struggling moment:** deciding what to assert about a page nobody has seen.
  Every assertion available comes from the same understanding that produced the
  defect, so it agrees with the defect and goes green.

## Scope — one shippable behaviour

**In:** the pack's verify/gate step gains an executed visual inspection. The
agent drives a browser it already has, captures the surface across a small set of
viewports and scroll positions, judges the images with its own vision against
what a reader would notice, and writes named findings into the evidence manifest.
`accept-frontend-evidence` then has something to accept.

**Out, deliberately** — each is a separate decision, not a detail of this one:

- Turning a finding into a durable regression assertion.
- Changing what a skipped inspection costs at the human gate.
- Any change to `frontend-reviewer`'s tools or role.
- Screenshot baselines or pixel diffing (ruled out below).
- Anything about driving a *third-party* site (§ What this is not).

## Why vision, and why not more assertions

**Finding is open-ended; pinning is closed.** You cannot enumerate in advance what
might look wrong, which is why enumeration keeps failing. Vision suits the open
half: it answers "does this look broken to a reader" without being told what to
look for. Once a defect is named, an ordinary geometry assertion holds it down —
and adopters already know how to write those. This feature is the open half, which
is the half nothing in the pack can do.

**This also settles the baseline question.** Vision reports *what is wrong*, not
*what changed*. There is no baseline to approve, so nothing rots — which is the
usual way visual QA dies.

**The honest status of the independence claim.** The appeal of vision is that it
does not run the author's model of the layout; it sees what is there. But the
agent doing the looking may be the same agent, in the same session, that wrote the
page — so it may inherit the framing that caused the defect. A screenshot adds an
observational channel; it does not by itself make an independent oracle. **Treat
independence as the bet, not the premise.** It is the first thing `de-risk-intent`
should attack, and the holdout fixture is how.

## When there is no browser

The pack must not assume one. Its own contract already permits "no Chromium" as an
unverified item (`SKILL.md:623`), and its structural and accessibility steps
deliberately accept a supplied HTML file or a local `file://` path
(`SKILL.md:520-542`) rather than a running stack.

The working premise is that **a team doing frontend work with an agent generally
has a drivable browser already**. This is better grounded than an assertion: the
pack's own accessibility and performance steps already drive headless Chromium
(`SKILL.md:531-542`, `fe-performance/SKILL.md:94-103`), so an adopter following
the journey has one in hand before this feature asks for anything. Where that
holds, the feature adds no dependency. Where it does not, the inspection degrades
to a **named skip**, the way the pack already names a missing co-install rather
than omitting it (`SKILL.md:81-86`). Whether that skip should also *cost*
something at the human gate is out of scope above, and is the natural follow-on.

## What this is not

**Not web automation.** Driving websites an adopter does not own is a different
problem with a different cost: persistent authenticated profiles, credential
boundaries, admitted executable drivers, a browser identity with a lifecycle. None
of that is in play here. This is an agent screenshotting the page it just wrote,
in the project it is already working in, with the same headless Chromium the
pack's accessibility step already uses against a `file://` path
(`SKILL.md:531-542`). Keeping the two apart matters: conflating them imports a
heavy runtime-ownership and security decision into a feature that needs neither.

**Not a reviewer.** `frontend-reviewer`'s independence comes from being a **forked
context that has not seen the authoring session** (`frontend-reviewer.md:15`) —
not from its tool list. So the argument is not that a browser would corrupt it;
it is that this is a different job at a different time. This runs *inside* the
implementing loop, producing evidence; the reviewer runs after, judging. What the
reviewer is seeded with today — known exceptions and the most recent gate results
(`frontend-reviewer.md:21-24`) — has no field for a visual finding. Giving it one
is a consequence of this feature worth naming, not a redesign of the reviewer.

## The worked instance — this repository

*Everything below this heading is specific to this repository, which self-hosts
the pack it publishes and is therefore the one place the gap can be watched
biting. None of it is a claim about an adopter's project.*

### What the gap cost here

**1. Four layout defects reached a reader in one session**, on a surface built
with this pack's doctrine. Prompt code blocks overflowed by **1,863px**
(`web/src/test/e2e/guidebook-walk.spec.ts`, "overflowed by 1,863px");
a navigation rail rendered behind the site header at rest, losing its first
**36px** (`docs-site/src/styles/starlight.css`, "first 36px of the rail");
once pinned, the rail's own header covered entries **2 and 3** of its list
(`guidebook-walk.spec.ts`, "hiding items 2 and 3"); and an in-page table of
contents held **one entry** because the headings were `####` against a
site that indexes `h2`–`h3` (`docs/guides/guidebook-step-contract.md:84-87`). A
human found all four by looking.

**2. The automated checks passed while each was live, three times over.** `y >= 0`
passed while the element sat behind the header; a padding assertion passed while
content scrolled underneath it; "the header is not covered" passed while the
header covered its own list. The repository records the shape: "Both mutations of
the fix passed that check, which is how a control that cannot fail looks from
the outside" (`guidebook-walk.spec.ts`, "the fix passed that check"). Note
what ended it — not a better assertion, a person looking.

**3. It is not one bad session.** The same shape — content behind fixed chrome,
past every gate, found by looking — had already happened on a different surface
under a different spec: "The occlusion clause exists because a real defect shipped
past every other gate… dropping the whole declaration put the first 48px of
content" behind the fixed mobile table of contents
(`web/src/test/e2e/site-quality-gate.spec.ts:513-520`). 48px there, 36px here,
each closed afterwards by an assertion aimed at the instance.

**4. One of the four needed a contract, not a browser.** The `####` heading defect
is a static authoring rule and is now written down
(`guidebook-step-contract.md:84-87`). Reaching for a browser where a rule would do
is how cost becomes unbounded, which is why it is excluded from the proof above.

**5. Capture already happens and is not checked as inspection.** The repository
captures PNGs across five viewports and then asserts `expect(path).toBeTruthy()`
(`web/src/test/e2e/screenshots.spec.ts:37-39`, repeated at `:51` and `:69`) —
a check that a string is non-empty. The owning criterion does record that
components were "verified… via Playwright screenshots"
(`docs/specs/site-ui-primitives/spec.md:173`), so an inspection happened at least
once; what is absent is anything that makes it recur or that fails when it does
not. The governing spec's **Never do** list names the pattern exactly: "Treat
screenshot
existence, a truthy path, source shape, or inferred CSS geometry as proof of
browser behavior" (`docs/specs/site-browser-quality-gate/spec.md:57-58`). The
adopter-general reading: capture is cheap and already common; *inspection* is what
has no mechanism.

### Where the framing this came from was wrong

**1. "WCAG 2.2 Focus Appearance and Target Size — the two manual-verification
items automated tooling misses" is wrong reasoning.** The phrasing is the pack's
own (`frontend-reviewer.md:3`, `:107-109`). But browser automation in this
repository measures a focus indicator mechanically: it reads the focused style,
blurs, reads the resting style, restores focus, and requires the element to *gain*
an indicator rather than merely differ (`quality-assertions.ts:235-284`), plus
ring contrast across real Tab stops (`:619-730`). That coverage is partial — the
contrast helper skips box-shadow rings and approximates image backdrops (`:677`,
`:711`), and SC 2.4.13's area (Focus Appearance) and SC 2.4.11's non-obscuration
(Focus Not Obscured) are not measured at all.
The narrow, correct claim: **parts of these criteria are demonstrably measurable
by an executing agent.** What blocks the pack's reviewer is not the criteria's
nature — it is that a reader of a diff executes nothing. Attributing the gap to
"automated tooling" points adopters at the wrong fix.

**2. The recorded numbers differ from the ones this started with.** 1,863px not
1,775; one TOC entry not zero; entries 2 and 3; 36px. The 128-state sweep is not
in the repository — what shipped is 90 (3 viewports × 5 steps × 3 page-scroll ×
2 rail-scroll, as the sweep stood at `f2b1f5ab4`). That arithmetic is a frozen
historical record and is deliberately not pointed at the live tables, which no
longer yield it. The
sweep has since grown, and this note no longer states its current state count.
That figure was wrong here twice — once by outliving its inputs, once when both
inputs were stated a viewport short and the total survived because the errors
cancelled — and the recipe given for re-deriving it was itself incomplete: which
viewports reach the scroll loops is decided by Starlight's own `72rem` query in
`node_modules`, not by anything this note cites. A count that needs an input
from outside the repository to stay true does not belong in a durable note. The
90 above is the figure as shipped, and stays as the historical measure.

Citations into the files that change alongside this note quote a fragment
instead of naming a line, because a line number into a file under active edit
is stale by the next commit. Citations into files this change does not touch
keep their line ranges.

**3. Two of my own earlier claims are withdrawn.** "Every reviewer is read-only"
is false — `adversarial-reviewer.md:4`, `quality-engineer.md:4` and
`security-reviewer.md:4` carry Bash. And "no frontend skill references Astro" is
false — `fe-performance/SKILL.md:249` and `rendering-strategy/SKILL.md:134-139`
name it, as one framework example among Next.js, Remix, Nuxt, Qwik and Eleventy.

### The existing browser gate here

`docs/specs/site-browser-quality-gate` is Shipped and owns a 60-case
deploy-blocking matrix over this repository's own sites
(`tools/test_browser_gate_subset.py:412-452`). **This proposes no second gate and
supersedes nothing.** If the feature is exercised here, any new e2e spec must
satisfy the existing allowlist rather than route around it: `test:e2e:gate` names
its specs exactly, and `tools/test_browser_gate_subset.py:106-142` requires every
spec on disk to be in that script or in `EXCLUDED` with a substantive reason.

A related repository-only governance point, recorded so it is not re-litigated:
RFC-0088's `web-pilot` owns the authenticated-browser question for adopters. It
is deliberately not this feature's business (§ What this is not), and this intent
neither extends nor depends on it.

## De-risk verdict — two kills, a survival, and a model-dependence finding

Run 2026-09-13 under `de-risk-intent`. Two-way door, so `prototype-led`: the probe
was built and the build was the test. The kill condition was written to a file
before any image existed, and amended once — also before any image existed — to
drop defect 4, which the intent already excludes.

**The probe.** The real guidebook pages from this repository were rendered in
headless Chromium. The three geometry defects were recreated in the live page; a
**holdout** was added from a class the feature's story was not built on (body text
at very low contrast); and unmodified pages were captured as controls. Each image
was judged by a **fresh session that had never seen this conversation, the intent,
or the defect list**, under a prompt that named no defect and no defect class.
Rounds 1-3 used `codex exec --image`; round 4 repeated round 3 with a different
model family. In every round the browser was driven by the orchestrator and the
viewer received only a finished image — the viewer never needed browser access of
its own, which is what made adding a second model cheap.

### Round 1 — killed on false positives

Detection was strong. All three geometry defects were named in reader-visible
terms, and so was the holdout — "most of the main article text is nearly invisible
… making the page unreadable."

**K3 fired.** An unmodified page drew a confident *stops use* finding: "the main
content is cut off at the bottom of the screenshot." A reader does not consider
the bottom edge of their own window a defect. Four of five false or mis-ranked
observations were about the **boundary of the image**, not the page.

Round 1 also showed, outside what the kill condition asked:

- **Severity ranking is unreliable in both directions.** The defect every reader
  meets on every page — the rail clipped under the site header — was ranked
  *cosmetic*, while a non-defect was ranked *stops use*.
- **One control was contaminated and the viewer was right about it.** A
  `scrollIntoView` had parked content under the sticky header; the viewer
  described a real condition the fixture created. A point for the oracle, and a
  warning about fixture design.

### Round 2 — killed on the fix

Diagnosis: the viewer was never told a screenshot is a *window* into a scrollable
page. One sentence was added saying so. Nothing else changed, and a new kill
condition was declared before running.

The false positives disappeared — both clean controls came back clean, one with
"Nothing is wrong with this page."

**K1' fired.** The rail-clipped-under-the-header defect was **lost**: "Nothing is
wrong with this page." Teaching the viewer to forgive the top edge taught it to
forgive the defect, because from a single viewport crop **the two look identical**.

### Round 3 — survived

The reframe said the oracle needs **state**. Before building any paired-capture
machinery, the cheapest thing that could supply it was tested: **one line telling
the viewer where the page is scrolled to.** Cut before adding — if a label
suffices, pairing is machinery nobody has to maintain.

The label makes one rule available. *At rest:* nothing may be cut off at the top,
so anything clipped there is a fault. *Scrolled:* content continuing past an edge
is normal.

The set was balanced so the label could not become a shortcut — four at-rest
images, one of them clean, and three scrolled, two of them clean. The kill
condition was declared before running.

| Image | Told | Truth | Blind viewer said |
|---|---|---|---|
| page-4 | at rest | defect: rail under header | "clipped at the top… hidden behind the top header **even though the page has not been scrolled**" |
| page-5 | at rest | defect: box over its own list | "Stops use: …white overlay… covers part of the step list" |
| page-6 | at rest | holdout: low contrast | "Stops the reader using the page: most of the main article text is nearly invisible" |
| page-1 | at rest | clean | **"Nothing is wrong with this page"** |
| page-3 | scrolled | defect: code clipped right | "Stops use: …clipped on the right. Several lines continue behind the right sidebar" |
| page-7 | scrolled | clean | **"Nothing is wrong with this page"** |
| page-8 | scrolled | clean | **"Nothing is wrong with this page"** |

None of K1'', K2'', K3'' fired. Four defects named, three clean pages returned
clean, and on page-4 the viewer reasoned *from* the state it was given — the exact
discrimination both earlier rounds died on.

**VERDICT: SURVIVED**, on the cheapest available mechanism. No paired capture, no
baseline, no new dependency: one sentence of state alongside the image.

### Round 4 — the cross-model check, and what it cost the claim

Rounds 1-3 used one model. Round 4 repeated **round 3 unchanged** — same seven
images, same state labels, same neutral prompt, fresh context per image — with a
viewer from a different model family. The kill condition was declared first and
was identical.

**Detection reproduced, and sharpened.** All three geometry defects and the
holdout were named, several more precisely than before. On page-5 the second
viewer identified the hidden entries as **steps 2 and 3** — matching the recorded
defect exactly, where the first viewer had said "items 2-4". On page-4 it called
the defect "a real usability fault, not purely cosmetic - navigation content is
unreachable at rest", correcting the *cosmetic* ranking that was round 3's one
blemish.

**Discrimination did not reproduce.** Round 3's three clean controls returned
three literal "Nothing is wrong with this page" replies. The second viewer
returned a finding on **all three**:

| Clean control | Round 3 (viewer A) | Round 4 (viewer B) |
|---|---|---|
| page-1, at rest | "Nothing is wrong with this page" | nav bar "clipped… top edge cut off" — *cosmetic* |
| page-7, scrolled | "Nothing is wrong with this page" | code block "clipped on the right" — *"potentially blocking… if truncated, unusable; if merely touching the edge, cosmetic"* |
| page-8, scrolled | "Nothing is wrong with this page" | table column "cut off at the panel's right edge" — *cosmetic-to-moderate* |

**The first two kill clauses did not fire. The third did not fire on the letter** —
it required a *stops use* finding, and the closest was explicitly hedged with an
if/else, which round 1 had already established is not a kill.

**But the letter is not the finding.** Three of three clean pages drew a report
where three of three had been clean. The bet survives; the claim that survived is
narrower than round 3 suggested.

### Round 5 — what the difference is NOT, and the variable that stays uncontrolled

Round 4's phrasing — "discrimination is model-dependent" — assumed the two viewers
differed in *perception*. Two other explanations were live, and one of them is
testable here.

**Explanation A, testable: report format.** The prompt offered a scripted exit —
*'If nothing is wrong, say "Nothing is wrong with this page" and stop.'* Viewer A
returned that sentence verbatim on all three clean pages, which is a
literal-compliance signature. A model that takes a scripted exit more readily
looks quieter without seeing any less.

Round 5 re-ran only the three clean controls through viewer A with the scripted
exit **removed**, replaced by an instruction to describe anything wrong. Nothing
else changed. It still found almost nothing: *"No visible issues"*, *"No visible
usability faults"*, and on the third a single cosmetic note that the code example
*"wraps many lines awkwardly"* — explicitly adding *"no visible issue stops the
reader from using the page"*.

**Explanation A is refuted.** The quietness is not an artifact of the exit
sentence. The behavioural difference between the two viewers is real and holds
across two prompt formats.

**Explanation B, not testable here: environment.** These viewer-A sessions run
under an enterprise-managed profile. One override is visible in the logs —
`approval_policy` forced to `OnRequest` by a managed requirement — and it has
nothing to do with vision. The banner shows the requested model and reasoning
effort were honoured, and the images were demonstrably received, since the defect
descriptions were specific and correct. But **the absence of other server-side
profile effects cannot be established from inside this environment.**

**So the cause of the difference is unattributed.** It is a genuine difference
between two viewer *configurations*; whether the operative variable is the model
or the environment around it is not established, and the distinction matters. "Use
this model" is portable advice; "one lab's managed profile made its viewer quiet"
is not portable at all.

One more observation, which is its own small finding: on the same clean image the
two viewers gave **contradictory** descriptions — one reported the code block
*clipped on the right*, the other reported it *wrapping awkwardly*. Both cannot be
true of one image. Disagreement of that kind on a page that is fine is the
false-positive problem restated, not a separate one.

### What the five rounds establish

- **Perception generalises.** Two model families, told nothing about what to look
  for, named every defect put in front of them — including a holdout from a class
  the feature's story was never built on.
- **State is the load-bearing input.** The same model on the same image went found
  → missed → found as the state it was given changed. A capture that does not
  record what state the page was in is the version that fails silently.
- **The false-positive rate varies by viewer configuration, and that is the live
  risk.** Guardrail 2 — the one that kills visual QA quietly — went from zero of
  three clean pages to three of three between two viewer setups on identical
  inputs, and held when the prompt format was changed. Whether the operative
  variable is the model or the environment around it is **not established**. The
  practical consequence is the same either way, and it is the one an adopter must
  act on: **this rate has to be measured where the feature will run.** It cannot
  be inherited from this probe or from anyone's benchmark.
- **Severity is unreliable, and unreliable differently per model.** Viewer A
  ranked the worst defect *cosmetic* and a non-defect *stops use*; viewer B ranked
  the defects well and hedged its false positives. Neither is trustworthy as
  output.

### The design constraints these rounds produced

1. **Every capture records the page state it was taken in.** Without it the
   feature fails, and fails silently.
2. **Do not ask vision for severity.** Report what was seen and where; derive
   severity by rule from the class of finding — content hidden behind fixed chrome
   at rest is a blocker by rule, not by opinion.
3. **The false-positive rate is measured locally or it is not known.** Any
   adopter-facing claim about noise is a claim about one viewer in one
   environment, and this probe shows it does not transfer. Ship the fixtures and
   the measurement, not a number.

### Routing

Ready for `decompose-intent`, carrying the three constraints above. The open risk
is no longer "does vision work" — it is **how noisy vision is on a page that is
fine**, which rounds 4 and 5 showed varies by viewer configuration for reasons
this probe could not isolate. That makes local measurement part of the feature,
not a footnote to it.

```yaml
validation_hook:
  assumption: >
    An agent looking at a rendered page, TOLD what state the page is in, names the
    defects a reader would notice and does not report non-defects.
  kill_condition: >
    Detection: any recorded geometry defect unnamed, or the holdout missed.
    Discrimination: any unmodified control page draws a "stops use" finding.
    Round 1 fired discrimination (unlabelled image). Round 2 fired detection (the
    edge forgiven wholesale). Round 3, adding a one-line state label, fired
    neither. Round 4 repeated round 3 on a second viewer: detection reproduced and
    improved, no clause fired on the letter, but all three clean controls drew a
    finding where all three had been clean. Round 5 refuted the prompt-format
    explanation for that gap.
  uncontrolled_variable: >
    Viewer A ran under an enterprise-managed profile. One override is visible in
    the logs (approval policy) and is unrelated to vision; the requested model and
    reasoning effort were honoured and the images were demonstrably received. The
    absence of other server-side profile effects CANNOT be established from inside
    this environment. So the round-4 difference is a difference between viewer
    CONFIGURATIONS, and model-versus-environment is not attributed. Do not carry
    the false-positive numbers out of this probe as a property of either model.
  activity: >
    Desk probe only - 8 renders, 31 blind judgements, two viewer configurations,
    one site. NOT validated with humans, and that is the gap that matters:
    "defects a reader would notice" has never been checked against a reader. Put
    the same images in front of several readers of an adopter's docs, unprompted,
    and compare what they report against what each viewer reported - that single
    activity settles both the detection claim and the false-positive claim, in the
    currency the outcome is written in. Three axes remain untested: whether the
    result holds on a surface that is not a documentation page; whether the
    false-positive gap is model or environment; and INDEPENDENCE - every viewer
    here was a different model in a different session from the one that built the
    page, a stronger separation than the shipped feature would have.
```

## Assumptions

- ~~An agent looking at a screenshot reliably names the defects a reader would
  notice.~~ **Tested 2026-09-13 over four rounds and 28 blind judgements.**
  Detection holds across two model families. A bare screenshot does not carry
  enough state to separate normal scrolling from occlusion; a one-line state label
  does. See § De-risk verdict. Replaced by the three below.
- **The false-positive rate on a page that is fine is low enough to trust.**
  *Riskiest, and now the live one.* Measured at zero of three clean pages on one
  viewer configuration and three of three on another, same inputs, and the gap
  survived a change of prompt format. Guardrail 2 depends entirely on this. Whether
  the operative variable is the model or the enterprise-managed environment around
  it was not established, so the number transfers nowhere and must be re-measured
  where the feature runs.
- ~~Severity ranking from vision is trustworthy enough to act on.~~ **Measured
  false on both models, in both directions.** Design around it: derive severity by
  rule, do not ask for it.
- That judgement is independent enough of the authoring context to catch what the
  author's own assertions could not. *Still untested, and no round could test it —
  every viewer was a different model in a different session from the one that
  built the page, a stronger separation than the shipped feature would have.*
- A team doing frontend work with an agent generally has a drivable browser
  already. *Partly grounded rather than assumed: the pack's accessibility step
  already requires headless Chromium (`SKILL.md:531`). But the pack also permits
  "no Chromium" as an unverified item (`:623`), so the degradation path must exist
  regardless.*
- A small number of captures — a few viewports × a few scroll positions — is
  enough. Viewport **height** and **scroll position** are load-bearing: the defect
  that survived three assertions was only visible at 1280×600 after scrolling.
- Vision produces few enough false positives to survive real adopter surfaces.
  Untested, and this is the failure mode that kills the feature quietly.
- The manifest can carry a visual finding without a schema change large enough to
  break existing adopters' manifests.
- **Knowledge surface:** in-repo documentation set (`packs/`, `docs/specs/`,
  `docs/rfc/`, `docs/product/`), consulted for the business-domain and in-flight
  areas. No MCP knowledge tool or internal CLI was detected in this session; no
  external web search was used as a substitute.

## Decomposition

-
