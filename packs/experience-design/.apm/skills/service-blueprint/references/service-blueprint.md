# Service blueprinting — the four-row method

A service blueprint is a cross-functional diagram that maps every step in a
customer journey to the employee actions, system calls, and internal support
that make it happen. The method is defined and maintained by Nielsen Norman
Group: https://www.nngroup.com/articles/service-blueprints-definition/

## Why a blueprint

The blueprint solves the **screen↔service gap**: a screen can be designed
without knowing what backs it, and a service can be built without knowing
which screen surfaces it. The blueprint makes that tie explicit — it is the
contract between the experience layer and the build layer. The backstage column
is the **slicing instrument**: each named backstage service is a candidate
component for `architect` decomposition and an input to the spec LLD.

## The four rows

Every column in the blueprint represents one step in the customer journey.
Every row represents a different layer of the service. Read a column
top-to-bottom to understand what happens at one moment; read a row
left-to-right to understand one layer across the whole journey.

### Frontstage

What the customer **sees and touches** — their actions and the touchpoints that
deliver value to them. Examples: filling in a form field, tapping a button,
receiving a notification, interacting with a support agent face-to-face. This
row comes directly from the journey's stages and actions (see
`journey-mapping`).

### Line of visibility

The **structural boundary** separating what the customer sees from what they do
not. It is not a row to fill in — it is a horizontal line drawn between
frontstage and backstage. Making it explicit forces the blueprinter to decide
what is in view and what is hidden, and prevents frontstage items from silently
depending on backstage items with no declared visibility.

### Backstage

Employee actions and system calls that **directly fulfil the frontstage
touchpoint** but are invisible to the customer. Examples: an API call that
validates a payment, a staff member who manually reviews a flagged order, a
system that generates a one-time code. Each entry in this row is a
**named-service candidate** — a stable service name that `architect` can use
as a C4 component and `contracts` can use as an interface target.

**The backstage column is the slicing instrument.** Every distinct backstage
service entry is one candidate for component decomposition. This is the
mechanism by which a service blueprint becomes an architectural input — not
by prescribing the architecture, but by making the service boundaries visible
so a structural lens can decide where to draw component lines.

### Support

Internal systems, processes, and vendors that **back the backstage actions**
but have no direct frontstage effect. Examples: an authentication service the
backstage API calls, a logging platform, a third-party payment processor, an
internal billing ledger. This row is the enabling layer — it must exist for
the backstage to work, but the customer never touches it directly.

## The hand-off seam

When the blueprint is done, the **backstage services are named by-reference**:

- **`architect` / `contracts` present in session:** use the stable service name
  the `architect` skill would use — short, noun-phrase (e.g. "Order Service").
  Do not draft the C4 diagram or the contract here. Record the name in the
  `## Hand-off` section of the blueprint so `architect` can pick it up.
- **`architect` / `contracts` absent:** name each service textually with a
  one-line role description. The names are still hand-off candidates —
  record them so they survive until those packs are available.

The by-reference rule prevents this skill from duplicating `architect`'s work.
The detect-and-degrade rule prevents it from blocking when `architect` isn't
installed.

## Column gaps

A frontstage action with no backstage entry is a gap — a screen action the
service cannot fulfil. Name every gap explicitly in the backstage row
(e.g. "— gap: no backing service identified for this action —") rather than
leaving the cell blank. Gaps are design debt, not omissions; they must be
visible so the spec LLD can plan for them.
