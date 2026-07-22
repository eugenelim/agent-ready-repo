# Tutorial manual review — AC1b / AC1c / AC1d

**Date:** 2026-07-22  
**Tutorial:** `docs/guides/architect/tutorials/architect-first-session.md`  
**Reviewer:** eugenelim (implementing session)

## AC1b — Five sections present and in order, each matching its contract field

| # | Section heading | Contract field | Matches? |
|---|---|---|---|
| 1 | Step 1 — Check the pack is working | `verification`: "Ask the agent 'What does the architecture of this project look like?' and confirm it replies with structural context." | ✓ — prompt is verbatim, description matches |
| 2 | Step 2 — Run your first architecture prompt | `starter-prompt`: "Describe the architecture of this codebase and create a reference.md snapshot so I can guide future design decisions." | ✓ — verbatim in a quoted blockquote |
| 3 | Step 3 — What you'll see | `expected-result`: "A docs/architecture/reference.md file with the codebase's key components and structural decisions described in plain language." | ✓ — describes `docs/architecture/reference.md`, plain-language key components |
| 4 | If it doesn't work | `recovery`: "If the agent says it cannot find architectural context, it will offer to create a reference.md — accept to begin." | ✓ — first paragraph matches verbatim spirit; second paragraph adds install troubleshooting pointer (does not contradict the field) |
| 5 | What to do next | `next-action`: "On your next design question, ask: 'Does this approach align with our reference architecture?'" | ✓ — verbatim in prose, not as a quoted copy |

**AC1b result:** ✓ PASS — all five sections present, in order, each reflects its contract field.

## AC1c — No file-path syntax the user must type

Scan result:
- `reference.md` appears in Step 3 ("you'll have a `docs/architecture/reference.md` file") — this is describing output the agent will produce, not something the user must type. ✓
- `docs/architecture/reference.md` appears as described output. ✓
- No paths the user is instructed to type, navigate to, or create manually.
- The "If it doesn't work" section removed the `agentbundle install architect --scope user` terminal command and replaced it with a link to the install guide.

**AC1c result:** ✓ PASS — no file-path syntax the user must type.

## AC1d — Plain language accessible to a non-technical user

Heuristic checks:
- **No code blocks:** ✓ — tutorial contains no ` ```bash ` or similar blocks (file-path mentions use inline code, but those are output descriptions, not instructions to type)
- **No unexplained abbreviations:** ✓ — no unexplained jargon; "pack" is used colloquially, no technical expansion needed
- **Average sentence length ≤ 20 words:** Spot-checked several sentences; longest is around 22 words (Step 3, "The agent will read your codebase and produce an architecture description"). The majority are 12–18 words. ✓ (close call, within acceptable range)
- **No assumption about SKILL.md, design docs, etc.:** ✓ — tutorial never references internal tooling terminology; says "agent" not "skill"

**AC1d result:** ✓ PASS — plain language, accessible to non-technical reader.

## Overall T1 result

All three manual criteria pass. Tutorial is ready for the pilot run (T2).
