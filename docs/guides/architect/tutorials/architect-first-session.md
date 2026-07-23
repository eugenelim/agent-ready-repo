# Your first architecture session

**What you'll build:** A `docs/architecture/reference.md` plain-language snapshot of your codebase's main components and structural decisions.
**Prerequisites:** The `architect` pack installed in your repo.
**Time:** 15–20 minutes.

> At the end of this tutorial you'll have asked the agent to describe your codebase's architecture and seen it produce a plain-language snapshot you can use to guide design decisions.

This is a learning walkthrough for a fresh start. It covers one complete first session: checking the pack is working, running your first architecture prompt, understanding what you'll see, and knowing what to do if something goes wrong.

## Step 1 — Check the pack is working

In your Claude Code chat, type:

> What does the architecture of this project look like?

The agent should reply with a description of the codebase's structure — what the main components are, how they relate, what the key decisions appear to be. You might see a brief summary, a list of modules, or a short narrative.

If the response sounds like the agent is actually describing your project (not a generic answer), the pack is working and you're ready to continue.

## Step 2 — Run your first architecture prompt

Copy the following prompt exactly and paste it into the chat:

> Describe the architecture of this codebase and create a reference.md snapshot so I can guide future design decisions.

The agent will read your codebase and produce an architecture description. You don't need to know anything about the codebase in advance — the agent reads it directly.

## Step 3 — What you'll see

When the session completes, you'll have a `docs/architecture/reference.md` file with your codebase's key components and structural decisions written in plain language. The agent will tell you where it wrote the file and offer a brief summary of what it captured.

Open the file in your editor and read through it. It should describe the real decisions your team has made — not invented standards. If something looks wrong or invented, you can simply tell the agent: "The section about X is not accurate" and ask it to revise.

## If it doesn't work

If the agent says it cannot find architectural context, it will offer to create a `reference.md` from scratch — accept to begin. The agent will guide you through filling in the first section.

If the agent seems confused or gives a generic response unrelated to your project, the pack may not be installed. See [Installing the architect pack](../../_shared/) for installation steps.

## What to do next

On your next design question, ask the agent:

> Does this approach align with our reference architecture?

The reference.md you just created becomes the foundation the architect skills build on. Every subsequent design doc, diagram, and critique will measure against it.

To learn more about the three architect skills and what each one does, see the [architect guides home](../README.md).
