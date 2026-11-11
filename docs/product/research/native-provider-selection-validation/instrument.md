# Try the code-intelligence pack on your legacy app

**Self-serve worksheet revision:** `NPV-SELF-SERVE-2026-10-08-r1`.

Use one real change in your legacy app to see whether the code-intelligence
pack helps you understand the code and plan a change. No facilitator is required.

1. Save a local copy of this Markdown file as your response worksheet. Keep
   this original page open for working links and prompts; use the copy for answers.
2. Choose your app and task below, then follow the linked first-session guide
   for setup. Return here when setup is ready, or record where it stopped.
3. Run the prompts below, check important findings in source, and fill in
   **Your response** at the end. Keep the prompts and revision line unchanged.
4. Send only your filled worksheet through the study owner's existing approved
   feedback channel. Do not put it in your app's Git history or open a public PR.

Taking part is voluntary. Use only an app and agent/indexer environment you
are authorized to use. You may stop at any time. Keep app source, concrete task
names, file paths, and raw results local; the returned worksheet contains only
short non-identifying summaries. You do not need to share your repository.
Sample prompts provide the training. Agent help and optional human help are
allowed; record any help you used. This is a usefulness exercise.

## 1. Pick your app and a real task

Open an existing legacy app repository you are allowed to use with your agent.
Keep the source and findings in your approved working environment. You do not
need to send us the repository or give us access to it.

Choose a small change you already need to make. Our example is:

> Add an optional field to an existing request. Find where the app handles,
> validates, and saves that request, then check what the change could affect.

Use your own change if this example does not fit your app. Keep these details
in separate local notes or your agent chat, not in the worksheet you return.
Replace placeholders only when pasting prompts into your agent:

```text
My change: <one sentence>
Starting function: <function or request-handler name>
File: <path to that function>
```

**Ready when:** you can point to the starting function and explain your task.

## 2. Follow the first-session guide for setup

Open [Your first code-intelligence session](../../../../guides/code-intelligence/tutorials/first-session.md).
Complete **steps 1–5** there: choose the task, install the packs and indexer,
build the index, and check agent readiness. That guide owns all setup commands;
you do not need to repeat setup elsewhere. It currently uses Claude Code.

Return here when preflight reports `status: ready` and the graph is populated
without a staleness warning. If setup fails, or you use a host not covered by
the guide, stop and fill in **Your response** with the blocked step and a generic
reason. Do not copy an error log, path, or machine name into the worksheet.
Optional help is fine; installation or policy blocks need your usual IT/support
route. You can submit setup feedback without completing the investigation.

## 3. Practice using the skill

The pack has one main skill, `code-intelligence`. Ask for it by name, give a
specific question, and include your starting function and file. It uses the
code map, reads source, and reports what it could not establish.

Paste this practice prompt:

```text
Use the code-intelligence skill to locate <starting function> in <file>.
Read its source and explain what it does in plain language. Give the file
and line reference. Do not edit code or the graph.
```

Open the cited file yourself. Does the explanation match the function? If the
agent picked the wrong function, give it the exact file and ask it to try again.
You can ask the agent to explain or refine the prompt; human help is optional.

**Practice complete when:** you have checked one claim against the actual code.

## 4. Investigate your change

Stay with the task from step 1. Paste these prompts in order. You may ask
follow-up questions and use optional help. Keep the same task throughout.

### Understand the current code path

```text
Use the code-intelligence skill to investigate <starting function> in <file>.
My planned change is: <my change>.
Show where it is defined and what directly calls it. Then trace today's
behavior through validation and storage, where those exist. Read the important
source files. Separate graph findings, source-verified facts, and open questions.
Give file and line references. Do not edit code or the graph.
```

**Look for:** an explanation of today's behavior that you can check in source.

### Find the wider impact

```text
Use the code-intelligence skill to find what changing <starting function>
in <file> could affect, directly and indirectly. The proposed change is:
<my change>.
Read the important dependent code and explain whether it uses the behavior
being changed. Show unresolved references and any search or index limits at
the top of the report. Do not edit code or the graph.
```

**Look for:** affected code with reasons, plus an honest account of what is missing.
An unresolved connection or a search limit means the list may be incomplete.

### Check one connection you care about

Choose one downstream function from the report. Paste:

```text
Use the code-intelligence skill to check whether there is a dependency path
from <starting function> to <downstream function>. Show the connection and
check the important links in source. If no path is found, explain what that
result can and cannot establish. Do not edit code or the graph.
```

**Look for:** a supported path, or a clear explanation of why the connection
could not be established. Do not treat an empty result as proof that no
dependency exists.

The pack also includes two helper agents. `code-investigator` traces behavior;
`impact-analyst` investigates change impact. If your host exposes them, you can
ask it to delegate the matching prompt to that agent. The main skill is enough
to complete this exercise.

## 5. Check the evidence outside the code map

The code map does not decide which repository instructions govern a file or
which files changed together in the past. Ask your main agent:

```text
Read the repository instructions and relevant decision records that govern
<file>. Explain which apply and cite them. Use the actual documents for
authority, not the code graph. Do not edit anything.
```

Then ask:

```text
Use a bounded review of Git history to find files that have changed alongside
<file>. State the history range you examined. Explain what this shows and what
it does not show about dependencies. Do not edit anything.
```

**Look for:** cited instructions and a history-based answer. Files changing
together is a clue to inspect, not proof of a dependency.

## 6. Make a checklist and give feedback

Paste:

```text
From this investigation, list the existing tests and code paths I should inspect
before making <my change>. Tie each item to source evidence. Separate verified
findings from gaps needing manual checks. Do not implement the change or claim
it is safe to make.
```

Keep the detailed checklist locally. Now fill in the worksheet below in your
own words. If you stopped early, write `not attempted` for later steps rather
than guessing. If no incorrect claim was found, write `none found`.

## Your response

Replace each bracketed placeholder. Use generic descriptions such as "found a
validation step I had missed" rather than app names, paths, symbols, or code.
Do not paste agent answers. Leave the revision line at the top unchanged.

- **Participant code:** [use the supplied code, or choose a random code such as
  P-7K2M9Q; do not use your name, initials, email, or employee ID]
- **Environment/setup label:** [use the supplied code, or E1 for this attempt;
  the reviewer combines it with your participant code]
- **Generic task class:** [for example, request-field change or behavior fix;
  no concrete app/task names]
- **Setup outcome:** [ready / blocked / not attempted]
- **Setup checkpoint and reason:** [last completed guide step; generic reason
  if blocked, or ready with a populated index and successful preflight]
- **Exercise progress:** [completed / stopped / not started; last completed
  worksheet step and a generic reason if stopped]
- **Help used:** [none / documentation / agent / human; short summary of what
  helped, without identifying the helper]
- **Source check:** [what kind of claim you checked and whether it matched the
  code; or not attempted]
- **Useful verified finding:** [one generic finding you checked in source and
  how it helped your actual task; or none found / not attempted]
- **Incorrect or unsupported claim:** [a generic summary and how you noticed
  it; or none found / not attempted]
- **Remaining gaps or manual work:** [what you still had to investigate; no
  private task details]
- **Checklist usefulness:** [how the local checklist helped you decide what to
  inspect before editing; or not attempted]
- **Overall feedback:** [useful / partly useful / not useful / could not assess;
  one or two sentences explaining why and what would improve the experience]

## Before returning your worksheet

Read your answers once more. Remove names, organizations, repository identity,
file paths, symbol names, source snippets, credentials, protected configuration,
private endpoints, customer data, quotations, screenshots, recordings, transcripts,
and raw tool/error output.
Keep only the coded fields and generic summaries above. If a useful detail cannot
be safely summarized, write `omitted for privacy` and name only the type of gap.

Return this completed copy through the feedback channel the study owner gave
you. If no channel was provided, keep it locally and ask the study owner where
to send it; do not publish it. Keep your code references, actual task notes,
and investigation output in your own approved working environment.
