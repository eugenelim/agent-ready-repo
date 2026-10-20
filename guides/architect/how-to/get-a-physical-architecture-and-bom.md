---
title: Get a physical architecture and bill of materials
summary: Turn a finished design into where each part runs and what it costs, as a physical architecture and a priced bill of materials.
pack: architect
kind: how-to
---

# Get a physical architecture and bill of materials

You can turn a converged design into a physical architecture, which shows where each deployment unit runs, and a bill of materials (BOM), which lists each item with its size and cost.

## Install the pack

This job needs the `architect` pack. Core is optional and only decides where the file is saved:

```bash
agentbundle install --pack architect
```

The pack is now available to your agent in this repository.

## Ask for it after a design

Finish a design with `architect-design` first. Once the design has converged, the agent offers a physical architecture and BOM once, and you can also ask for one on an existing design:

```text
Add a physical architecture and bill of materials to this design.
```

A design with no deployment section gets no BOM. The agent asks you to write the design first rather than invent deployment units.

## Read the bill of materials

Each line has a kind: cloud service, container image, open-source library, hardware, network connection, or licence. The `Identifier` column says what the item is, such as a provider SKU, an image URI, or a package URL with its licence. The `Tier / size` column says how big it is:

```text
Which BOM lines are unpriced, and why?
```

Each line is `priced` with a source, date, and region, `unpriced` when no grounded price exists, or `no direct cost`. Unpriced lines are counted and left out of the total, and no price comes from model memory. Prices are in USD unless you name another currency.

## Price a change

For a change to an existing architecture, the agent writes a delta BOM instead of a full one:

```text
Show the delta BOM for this change.
```

Each line is marked add, remove, or resize, and the BOM ends with the net monthly change.

## Save it

The agent saves `physical-architecture.md` beside the design, in the same folder, after you confirm. If the design is not saved yet, one confirmation covers both files. If the physical choices contradict the design, the agent raises that as a design finding and changes nothing silently.
