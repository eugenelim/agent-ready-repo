# Module design red flags — shapes the next contributor will misuse

Load this when a subsystem or architecture-change design names its internal
modules, packages, or interfaces. Skip it for an application/system design,
which stays above per-module detail. Screen every candidate shape against
these flags before choosing one, and screen the chosen shape again before
showing the draft.

## Who the design is for

Design for the contributor most likely to make the next change: an agent, or a
hurried person working the same way. That contributor sees only the files it
opened. It copies the nearest example it finds. It takes the shortest path
that compiles.

A good shape makes that behavior safe. The change that looks right from one
file is also right for the whole system. A flag below names a shape where it
is not.

## Interface depth

Judge each module by how much it hides compared with how much it shows. A deep
module puts a small, simple interface in front of substantial behavior. A
shallow module shows almost as much as it hides, so callers learn the
implementation anyway.

Depth is not the length of a call chain. A long chain spreads one decision
across many layers, and a reader has to walk all of them. A deep module keeps
the decision in one place behind one interface.

When two candidate shapes both work, prefer the one with the smaller public
surface. Accept a more complex implementation to get it.

## The flags

Each flag is a reason to revise the shape or reject it.

| Flag | What it looks like | Repair |
| --- | --- | --- |
| Shallow module | Callers call several methods in order to finish one operation. Options expose internal stages. | Offer the whole operation as one call and keep the stages inside. |
| Information leakage | One internal decision — a storage schema, wire format, or policy — appears in two or more modules, so changing it needs coordinated edits. | Give the decision one home. Parse external data into domain types at the boundary and keep transport types off the public interface. |
| Temporal decomposition | Modules are split by when code runs — load, check, transform, save — so each stage repeats the same representation and its rules. | Group code by the knowledge it owns. Steps that run at different times can share a module when they guard the same decision. |
| Pass-through method | A method forwards its arguments unchanged to another method of the same shape. | Remove the layer, or give it real policy, adaptation, or abstraction to own. |
| Split ownership | Two modules write the same state, or each keeps its own copy. A contributor who edits one writer cannot see the other, and their rules drift apart. | Give each piece of state one owner. Others read it or ask the owner to change it. |
| Two ways to do one task | The design offers more than one route to the same result. Each route keeps gaining callers, because contributors copy whichever they find first. | Keep one route. Move its callers over and delete the others in the same change. |
| Importable internals | Code outside a module can import its internals. A contributor taking the shortest path imports them, and they quietly become interface. | Make internals unreachable from outside, so an outside import fails the build. |
| Hand-synced list | The same set of items is listed in two or more places, and adding an item means editing every list. A contributor who sees one list updates only that one. | Keep one list and derive the rest. When a list cannot be derived, make the build fail when the lists disagree. |

## Where a flag lands in the document

Record the screen in the sections the template already has. Do not add a
section for it.

- A repaired flag changes the structural model or the contract table. No
  separate record is needed.
- A flag kept on purpose is named once, in the rationale of the structural
  section — Structural Model, or Structural Change in an architecture-change
  design. Say why the shape keeps it and what catches the misuse it invites.
- Where the document has an alternatives list, a rejected candidate shape that
  failed on a flag goes there, with the flag as its rejection reason.
