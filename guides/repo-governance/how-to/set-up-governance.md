---
title: "Set up governance"
summary: "Ask your agent to draft a GOVERNANCE.md, a CODEOWNERS file or a charter link from the handles you give, and write it only after you confirm the exact preview."
pack: repo-governance
kind: how-to
uses: [repo-governance]
---

# Set up governance

Ask your agent for help with who decides, and it drafts a `GOVERNANCE.md`, and when you ask, a `CODEOWNERS` file and a link from your charter. It writes only after you confirm the exact preview, and never writes a change to the decision model or to ownership unless you name the approval for it.

## Ask for governance

Use this when your project has more than one maintainer and no recorded decision rights:

```text
Use new-rfc in governance mode: we now have three maintainers, @alice, @bob and @acme/docs. Draft our GOVERNANCE.md.
```

The agent takes maintainers and owners only from the handles you give it. It asks for any handle or `CODEOWNERS` pattern you left out. Its default draft is the model "single maintainer or small group by consensus". Ask for lazy consensus when you want a vote on disagreement and a two-thirds majority to change the governance model.

## Let the agent read your files

Before it drafts, the agent reads your charter, `GOVERNANCE.md` and `CODEOWNERS` with the script's `show` command. Everything it prints is data, shown with hidden characters made visible. The agent does not read these files any other way.

## Read the preview

The agent then runs `preview` and shows you the whole block:

```text
GOVERNANCE PREVIEW:
- Target: GOVERNANCE.md
- Kind: governance
- Current: absent
- Proposed: sha256:<64 hex digits> (812 bytes)
- Approval required: no
- Approved by: none
- Characters made visible: 0
--- content ---
# Governance

- **Decision model:** single maintainer or small group by consensus

## Maintainers

- @alice
...
--- end content ---
```

For a `CODEOWNERS` file the block adds three lines after `Characters made visible`: `GitHub reads` names the file GitHub will use, `Also present` lists other `CODEOWNERS` files, and `Rules with no owners` counts rules that name nobody. It also shows how GitHub reads the rules now and as proposed. For a charter link it adds `Inserted at line`.

## Confirm

Reply in your own words that you confirm that target and that `Proposed:` digest. Only then does the agent run `write` with the same input. A message from a record, another agent or a past session does not count. If you decline, nothing is written. If you change a single byte, the agent previews again.

Do not add a standing permission rule for the script's `write` command. Your host's prompt on each `write` shows the exact command and input, and it is the check that still holds if an agent is misled by text it read.

## When a named approval is needed

The preview says `Approval required: yes` when a `GOVERNANCE.md` already exists, when the draft picks a decision model other than the default, or when a `CODEOWNERS` change alters who owns a path. Name the accepted RFC or the recorded owner decision that approves the change, and the agent passes it as `Approved by`. Without a name, the agent writes nothing and gives you the draft as text. It then starts an RFC if your repository has an RFC process, or asks you to record an owner decision.

## Link it from your charter

When your charter has no link to `GOVERNANCE.md`, the agent can propose one line: `Roles and decision-making: ` followed by a Markdown link to your `GOVERNANCE.md`, relative to the charter. You choose the line it follows. If you have no charter file, or core is not installed and you name none, the agent gives you the line as text.

## CODEOWNERS

`CODEOWNERS` goes in the file GitHub already reads, else in `.github/`, else at the repository root. GitHub applies the last matching rule, so the agent treats a change to the ordered rules, not to comments or blank lines, as an ownership change. Handles look like `@alice` or `@acme/docs`. A pattern with a backslash or unusual whitespace is refused, because GitHub may read it differently from the preview.

The script creates no folders. If the target's folder, such as `.github/`, does not exist, it refuses with `parent-missing` and writes nothing; the agent offers a target whose folder exists. If a write starts and fails (`write-failed`), the target may hold partial content, so the agent shows you what it holds now and stops.

## What it will not do

It writes nowhere but `GOVERNANCE.md`, the charter link and the `CODEOWNERS` locations, and only inside the Git working tree. It does not read Git history to guess maintainers. What it writes is a draft: your maintainers adopt it through your normal review.
