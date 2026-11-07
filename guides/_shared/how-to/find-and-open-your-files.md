---
title: "Find and open the files your agent writes"
summary: "Find a file your agent wrote, open it in a free app, and move its text into Word or Confluence."
pack: _shared
kind: how-to
---

# Find and open the files your agent writes

Your agent saves its work as plain files in the folder where you started it, and a free app opens them.

## Know the two terms

A repository folder is an ordinary folder that holds one project's files. A `.md` file is a Markdown file: plain text with light marks, such as `#` before a heading.

## Find the file

The agent names the path of every file it writes, such as `docs/adr/0007-use-postgresql.md`. A path starts from the folder where you started the agent. To see it again, ask:

```text
Where did you save that file? Give me the full path.
```

The agent answers with the full path, which you can paste into your file browser.

## Open the file

Open a `.md` file in any text editor. [Visual Studio Code](https://code.visualstudio.com/) and [Obsidian](https://obsidian.md/) are free, and both show headings and lists as formatted text.

## Move the text into Word or Confluence

Copy the formatted text from the editor's preview and paste it into Word or Confluence. Headings, lists, and tables carry over. For a Word file in your team's template, install the `converters` pack and ask:

```text
Turn docs/adr/0007-use-postgresql.md into a Word document.
```

The agent fills the template from the file. It does not invent a layout.

## Know when you need git

Reading, opening, and copying files needs no git. Installing the `core` pack does not need git. Its build loop reads git history and diffs, so use it inside a git repository.

## Know what the Claude apps do

The Claude chat apps do not read files from your computer, so the agent shows its result in the conversation. Copy it from there.[^apps]

Next: [Get started](/agent-ready-repo/docs/getting-started/).

[^apps]: [Claude apps practitioner journey](https://github.com/eugenelim/agent-ready-repo/blob/main/docs/design/journeys/claude-apps-practitioner-current-state.md), Stage 3: "the chat surface reads nothing from disk". Documentation-verified, not run.
