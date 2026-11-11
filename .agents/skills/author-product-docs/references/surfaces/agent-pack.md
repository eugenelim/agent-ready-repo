# Agent-context pack documentation

Evidence narrow: Claude Code, the Agent Skills specification, and Anthropic's best-practices page are one vendor cohort; Codex, BMAD, and the Copilot cookbook add three others, and BMAD and Codex follow the same skill format. Nothing opened tests how readers phrase requests or whether sample asks change discovery. Read each rule as a default plus its condition.

Load this file only when surface discovery names a shipped agent-context pack.

## First screen

**Default:** each skill's description says what it does and when to use it, in the reader's words and in third person ("Extracts text and tables from PDF files... Use when working with PDF documents").[^1][^2][^3] "Helps with PDFs" is the named poor form.[^3] Put the key use case first, because hosts shorten long descriptions.[^1][^2] Confidence: medium; the rule is a format requirement, but no reader evidence shows readers want it.

**Option:** route by the reader's situation ("You are working in an existing codebase") before any skill list, as BMAD does.[^4]

## First reader action

**Default:** one install command, then a typed ask. Claude Code's quickstart tests a skill by typing "What did I change?"; plugin docs install one example and confirm by typing `/` and looking for the skill.[^1][^5] The Codex page's only example is an install command, which gives a non-coder no wording to copy.[^6] Confidence: medium.

## Sample style

**Default:** the ask as text, plus a one-line outcome, labelled as an example ("a short summary of your edit and a list of risks").[^1] No source opened used screenshots for skills.

**Option:** show two differently phrased asks, or label the sample "for example", so readers do not treat one wording as the only accepted form. No source reports harm from a single sample, and none tests whether samples help discovery, so make no claim either way.

## Reference shape

**Option, ordering** (judgement; supported only by BMAD and the Copilot cookbook):[^4][^7]
- lifecycle order when the skills form a real sequence;
- job grouping when they are independent jobs;
- alphabetical inside a group, or for a long list readers search by name.

State the rule on the page and keep the order stable. Install-count order needs data a new pack does not have.

**Option, helpers:** hosts can hide a helper from the menu (`user-invocable: false`) or stop automatic use.[^1][^6] BMAD lists helpers with the skills that call them. No source documents how to explain a hidden helper to readers. Confidence: low.

## Troubleshooting

**Default:** key each entry to a symptom: "Skill not triggering", "Claude stops following a skill", "Skill descriptions are cut short".[^1] Codex lists "change not showing", "skill missing from the list", and duplicate names.[^6] Common fixes are a restart or reload and a better description.

## Failures to refuse

- **Names without a request to type.** Named example: the skills.sh leaderboard lists rank, name, source, and install count, with no description or sample ask; its try-it line is an install command.[^8] The site does not call this a flaw; it is a reading of the page.
- Vague names or descriptions such as `helper`, `utils`, or "Helps with documents".[^3]
- Claiming that sample asks improve discovery. No source supports it.

## Sources

[^1]: Extend Claude with skills, https://code.claude.com/docs/en/skills, accessed 2026-11-06 (read to character 100,000 of 118,986). Confidence: medium.
[^2]: Agent Skills specification, https://agentskills.io/specification, accessed 2026-11-06 and re-opened (1,024-character description limit). Confidence: high for the limit; same vendor cohort as the others from Anthropic.
[^3]: Skill authoring best practices, https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices, accessed 2026-11-06 and re-opened (good and poor descriptions, vague-name advice, 500-line limit). Confidence: high.
[^4]: BMAD Method documentation home, https://docs.bmad-method.org/, accessed 2026-11-06. Confidence: medium.
[^5]: Install and manage plugins, https://code.claude.com/docs/en/discover-plugins, accessed 2026-11-06. Confidence: medium.
[^6]: Build skills (OpenAI), https://learn.chatgpt.com/docs/build-skills, accessed 2026-11-06. Confidence: medium (independent vendor).
[^7]: Copilot Chat cookbook, https://docs.github.com/en/copilot/tutorials/copilot-chat-cookbook, accessed 2026-11-06. Confidence: low (task list with no sample wording).
[^8]: skills.sh, https://skills.sh, accessed 2026-11-06 and re-opened (install command present, no per-row description). Confidence: low as a failure example.
