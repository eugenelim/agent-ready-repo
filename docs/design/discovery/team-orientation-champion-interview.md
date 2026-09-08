---
type: research-instrument
slug: team-orientation-champion-interview
status: ready-to-run
surface: cross-platform
method: semi-structured interview with critical-incident recall
duration: 45 minutes
participants_needed: 1
updated: 2026-09-04
---

# Champion interview guide — 45 minutes, one participant

The instrument that converts one hypothesis into an observation. Everything else
in the Discover packet either comes from the repository or from the 14-day
traffic window; this is the only primary evidence in the engagement.

**The hypothesis under test**, recorded in
`docs/product/journeys/team-evaluates-and-adopts.md` as the highest-opportunity
pain: *"I've done three live demos and every one felt like I was improvising. The
platform is genuinely good — the demo isn't."*

That sentence is currently an assumption written by the team about its own users.
This session either grounds it, refines it, or refutes it. All three outcomes are
useful; a refutation is the most useful, because the redesign is currently
oriented around it.

## Who to recruit

One person who has **actually stood up in front of a decision maker and
demonstrated this platform**, at least once, in the last three months.

Do not substitute someone who has only installed it, only read about it, or only
run it solo. The hypothesis is about the act of transferring conviction to
someone who has not used the tool. Somebody who has never attempted that
transfer cannot speak to it.

If nobody fits, say so rather than recruiting the nearest available person. A
wrong participant produces evidence-shaped assumption, which is worse than a
labelled assumption.

## How to run it

Two rules that decide whether the output is usable:

1. **Ask about the last real occurrence, never about preferences.** "Walk me
   through the most recent time you demoed this" produces evidence. "Would a
   diagram help?" produces a polite yes and nothing else.
2. **Never show the redesign, the canvas concept, or any option.** This session
   measures the current state. Showing a solution converts the participant into a
   reviewer and destroys the baseline.

Record it if they consent. Take verbatim quotes — the journey artifacts need the
participant's own words, not a paraphrase of their sentiment.

## Part 1 — Warm-up and context (5 minutes)

1. Tell me about your role and your team.
2. How did you first come across this platform?
3. Who did you have to convince, and what was their role?

## Part 2 — Critical incident: the last demo (15 minutes)

The core of the session. Anchor on one specific real event and stay in it.

4. Think of the most recent time you demonstrated this to someone who had not
   used it. When was that, and who was in the room?
5. Walk me through it from the moment before you started. What did you have open?
6. What did you say first?
7. Where did you feel it going well?
8. Where did you feel it going badly? What was happening at that exact moment?
9. What did they ask you that you could not answer well?
10. How did it end? What did they say, and what happened afterwards?
11. If you had to do the same session again tomorrow, what would you change?

Probes to keep in reserve, used only when an answer stays abstract: *What did
that look like on the screen? What did you actually type? What did they say,
in their words?*

## Part 3 — The transfer problem (10 minutes)

The engagement premise is that the champion must transfer understanding to
engineers, a platform team, and a budget holder — three audiences with different
questions.

12. After that session, did you have to explain this to anyone else? Who?
13. What did you send them? Walk me through exactly what you shared — a link, a
    document, a screenshot, a message.
14. Which of the three audiences is hardest to explain this to, and what
    specifically breaks down with them?
15. Has anyone you explained it to gone on to explain it to someone else? What
    happened?

Question 13 has a specific purpose. The traffic data shows twelve people opened a
repository link pasted into Microsoft Teams — more than the entire published site
referred. This question tests whether that mechanism is what it appears to be.
Ask it neutrally and do not mention the traffic finding.

## Part 4 — Baseline explain-it-back (10 minutes)

This is the five-question comprehension check the engagement requires, run **now,
against the current surfaces**, to establish a baseline. Without a baseline
number the same check after ship measures nothing.

Frame it honestly and without pressure: *"I'd like to check how well our own
materials explain the model. This is a test of the materials, not of you — if you
can't answer, that's the finding."*

Ask them to answer from memory, in their own words. Do not offer the site.

1. What happens to a single piece of work, from the moment someone has an idea to
   the moment it is running in production? Name the steps in order.
2. At which points does a human have to make a decision, and what is each
   decision actually about?
3. What changes for a *team* as it takes this on, from first look to it being
   the normal way they work?
4. If your team already uses Jira or Linear, what is the relationship between
   that tool and this system? Which one is the source of truth?
5. What does this system refuse to do on its own, no matter how it is configured?

Score each answer: **correct**, **partial**, or **absent**, and keep the verbatim
answer. Question 4 tests the one-way projection contract and question 5 tests the
irreversible-action boundary; both are model claims the current surfaces make and
neither has ever been checked against a reader.

Note the wording constraint this check inherits: the answers must be judged on
whether the *decision* is understood, not on whether the participant reproduces
an internal gate code. A participant who says "someone has to approve the plan
before code gets written" is correct. Reciting "G3" is not a better answer.

## Part 5 — Close (5 minutes)

16. What would have made your last demo go better?
17. Is there anything I should have asked you and did not?

## What comes back into the thread

| Output | Feeds |
| --- | --- |
| Verbatim quotes on the demo incident | Stage 3 of the current-state marketing journey, upgrading it from `assumption-based` to `observational` |
| The answer to question 13 | The canvas context requirement — whether a pasteable static artifact is the real transfer vehicle |
| The hardest-audience answer to question 14 | Whether the champion, the engineer, the platform team, or the budget holder is the dominant reader above the fold |
| Baseline explain-it-back scores, out of 5 | The post-ship comparison the engagement's Gap D requires |
| Any refutation of the improvising hypothesis | The dominance argument, which currently rests on it |

## If this session does not happen

The redesign drops to `evidence_level: assumption-based` for every stage emotion
and pain, the improvising hypothesis stays labelled as a hypothesis in every
artifact that uses it, and the explain-it-back check becomes a blocking
pre-launch gate on the next cohort rather than a post-ship measure. Record that
outcome here rather than letting the label drift.
