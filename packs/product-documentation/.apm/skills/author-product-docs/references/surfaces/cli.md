# Command-line tool documentation

Evidence narrow: AWS CLI, GitHub CLI, Git, and the community CLI Guidelines, plus one kubectl page. AWS counts as one vendor and clig.dev as one source. Pages were read through a summarising fetch, and no study compares example placement. Read each rule as a default plus its condition.

Load this file only when surface discovery names a CLI.

## First screen

**Option:** purpose in one or two sentences, then the first command or a router to it. AWS and GitHub CLI do this; kubectl's quick reference leads with a task-grouped cheat sheet instead.[^2][^3][^4] Confidence is low; do not treat it as a rule.

## First reader action

A command the reader types, with its real output shown. The sampled tools start with setup (`aws configure`, `gh auth login`), because those tools need credentials; a tool with no setup would start with its main job. This is an observation, not guidance.[^2][^3]

## Sample style

**Default:**
- Show short real output. Put input and output in separate blocks.[^1][^5]
- Add output only where it helps the reader verify or copy a value.[^5]
- Explain placeholders after the command.[^5]
- Text and code blocks only; no screenshots appeared on the pages opened.

## Reference shape

**Default:** every command entry carries at least one runnable example.[^1]

**Option, chosen by reader state:**
- A fixed layout per command (synopsis, options, examples) for lookup. AWS, Git, and GitHub CLI do this.[^3][^6]
- A cheat sheet grouped by task for readers who know the tool and want a recipe. kubectl's quick reference does this.[^4]

Sources disagree on example order: clig.dev says "Lead with examples", while AWS and Git place examples last.[^1][^6] No study measures either. Pick by reader state and say which you chose.

**Option:** keep help text, man page, and web docs on the same content, with the web as the fullest layer.[^1] clig.dev is the only source.

## Troubleshooting

**Option:** group by symptom. AWS opens with six checks to try first, then groups by symptom ("Command not found", "Access denied") and quotes real error text so a reader can search for it.[^7] One vendor only, so confidence is low.

## Failures to refuse

- **Named example:** AWS `s3 ls` puts its six examples after Options and 20 Global Options, so the useful part sits at the foot.[^6]
- A command entry with no example. The supportable form is "an entry with an example is stronger than one without", per clig.dev.[^1] A 2025 blog post criticising the `ls` man page is opinion from one author and is not evidence of prevalence.[^8]
- Examples a reader must edit by hand after copying.[^5]
- A man page as the only surface.[^1]

## Sources

[^1]: Command Line Interface Guidelines, https://clig.dev/, accessed 2026-11-06 and re-opened ("Lead with examples"; "Users tend to use examples over other forms of documentation"). Confidence: medium (one community source, no date shown).
[^2]: AWS CLI User Guide, Setting up the AWS CLI, https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html, accessed 2026-11-06. Confidence: medium.
[^3]: GitHub CLI manual, https://cli.github.com/manual/, accessed 2026-11-06. Confidence: medium.
[^4]: Kubernetes, kubectl quick reference, https://kubernetes.io/docs/reference/kubectl/quick-reference/, accessed 2026-11-06 (first 100,000 of 121,608 characters read). Confidence: medium.
[^5]: Google developer documentation style guide, Command-line syntax and output, https://developers.google.com/style/code-syntax, accessed 2026-11-06 and re-opened. Confidence: medium.
[^6]: AWS CLI reference, `s3 ls`, https://docs.aws.amazon.com/cli/latest/reference/s3/ls.html, accessed 2026-11-06 and re-opened (20 global options). Confidence: high for layout.
[^7]: AWS CLI User Guide, Troubleshooting errors, https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-troubleshooting.html, accessed 2026-11-06. Confidence: low as a shape (one vendor).
[^8]: Noel Santos, "Opinion: Man Pages are Bad", 2025-03-09, https://www.virtualcuriosities.com/?p=4337, accessed 2026-11-06. Confidence: low (one author).
