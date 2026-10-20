---
title: Get a physical architecture and bill of materials
summary: Turn a finished design into where each part runs and what it costs, as a physical architecture and a priced bill of materials.
pack: architect
kind: how-to
---

# Get a physical architecture and bill of materials

You can turn a finished design into a physical architecture, which shows where each part of the system runs, and a bill of materials (BOM), which lists every item the design needs and what it costs.

## Install the pack

To get this job, install the `architect` pack:

```bash
agentbundle install --pack architect
```

Without Core, the result comes back in chat or goes to a folder you choose; with Core, it is saved beside the design in your repository.

## Ask for it after a design

Once you accept a design from `architect-design`, ask for the physical view:

```text
Add a physical architecture and bill of materials to this design.
```

The agent drafts where each deployable part runs, then lists every item it needs.

## Read the bill of materials

To see what each line costs and what is still missing, ask:

```text
Which BOM lines are unpriced, and why?
```

Each line names the exact item, such as a cloud plan, a container image address, or a library and its version, and shows whether its price is cited, unpriced, or has no direct cost.

## Price a change

To see what a change to an existing system adds or removes, ask:

```text
Show the delta BOM for this change.
```

Each line is marked add, remove, or resize, and the total shows the net monthly change: added cost minus removed cost, per month.

## Save it

To keep the result, say:

```text
Save the physical architecture beside the design.
```

The agent shows the file path, waits for your yes, and saves `physical-architecture.md` in the design's folder.
