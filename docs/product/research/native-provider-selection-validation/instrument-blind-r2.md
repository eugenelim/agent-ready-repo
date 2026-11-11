> **Historical snapshot only.** The owner removed blind selection from the
> current spec and plan. This script is not a current task or session instrument;
> use [instrument.md](instrument.md) for guided pack use.

# Six repository questions: facilitator script

**Script revision:** `NPV-T1-2026-10-08-r2`.

Read the quoted passages aloud. Run each person separately. Before starting,
confirm consent and authorized access, prepare the task targets locally, and
assign a participant code and a coded environment label. Keep targets and all
identifying details out of the form. Leave scoring until the person has finished.

## Opening

> You will work through six questions about this repository. Use the descriptions
> and actions already available in this environment. For each question, choose
> how you would find the evidence and explain why. You may decide an available
> action is unsuitable; explain your reason. Work on your own. I can repeat a
> question, but I cannot suggest an answer.
>
> For the first four questions, also tell me one limit of the evidence you would
> use. For the last two, explain why your chosen evidence supports the claim and
> why the other available actions do not establish it.
>
> Use only content and actions you are authorized to use. Do not share private
> source, customer information, credentials, account details, or protected
> settings. We will retain only coded, short paraphrases of your choices and
> reasons. There will be no recordings, screenshots, copied source, or copied
> tool output. You may stop at any time.

Establish prior familiarity without naming or showing a document:

> Before today, had you read the proposal that led to this exercise? Please
> answer yes or no. You do not need to describe it.

Record yes as `true` and no as `false` in the prior-RFC-familiarity boolean.
Do not explain that proposal or discuss its examples.

## Questions

Point to the prepared target in the authorized environment; do not copy its
name or content into the form. Read each question in order.

1. **Q1:** Where is this symbol defined?
2. **Q2:** What directly calls this function?
3. **Q3:** What could be affected, directly or indirectly, by a change to this
   symbol? Where could the available evidence leave connections unresolved?
4. **Q4:** Is there a dependency path from symbol A to symbol B?
5. **Q5:** Which repository instruction or decision governs this file?
6. **Q6:** Which files have historically changed together?

After each question, use only these neutral prompts as needed:

> What would you use, and why?
>
> If you would rule out an available action, what is your reason?

For Q1–Q4, if the person has not stated a limit:

> What is one limit of that evidence for this question?

For Q5–Q6, if the explanation is missing:

> Why do the other available actions not establish this claim?

Repeat prompts without adding examples, tool suggestions, technical vocabulary,
or possible limits. If ordinary descriptions are unavailable or safety requires
a stop, end the attempt and report the coded execution gap outside this form.
Do not score an environment failure as a wrong answer.

## Coded form

Record short paraphrases only. Do not quote the person or retain their identity,
task targets, repository details, or tool payloads. Use one form per person.

- **Participant code:** `P1` / `P2` / `P3`.
- **Prior-RFC-familiarity boolean:** `true` / `false`.
- **Environment-shape label:** coded environment and shape only.

Choice classes describe the observed choice: `native-action` means choosing an
available action; `explained-rejection` means ruling one out with a reason;
`repository-baseline` means using repository evidence directly. Do not show
these codes as suggested answers. If the person cannot explain a choice, leave
that absence clear in the rationale instead of filling it in for them.

| Question | Choice class | Rationale | One material limit (Q1–Q4) | Pass/fail |
| --- | --- | --- | --- | --- |
| Q1 | | | | |
| Q2 | | | | |
| Q3 | | | | |
| Q4 | | | | |
| Q5 | | | | |
| Q6 | | | | |

The scorer fills pass/fail and its rule citation after the independent attempt.
Keep any need for hints visible in the rationale; do not replace the original
choice with a later assisted answer.

## Closing

> Thank you. Your choices will be reviewed using the rules fixed before this
> exercise. We will retain only the coded form described at the start.
