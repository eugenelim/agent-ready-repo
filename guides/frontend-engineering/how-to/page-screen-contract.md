---
title: Write a Page/Screen Contract
summary: Decide whether a frontend change needs a page/screen contract and write the right-sized artifact before implementation.
pack: frontend-engineering
kind: how-to
journey: frontend-engineering
---

# Write a Page/Screen Contract

Use this when you are about to build or materially change a web surface and need to decide how much contract is warranted. The result is either a completed page/screen contract, a proportional subset for a smaller change, or an explicit no-contract decision for trivial work.

Start with a request like:

> Write the right-sized page/screen contract for this surface before implementation.

The agent reads the product brief, spec, existing surface evidence, design direction, and relevant source files you name. It drafts or updates the contract artifact. It does not implement the UI; approve the contract and its scope before significant UI code starts.

Record a completed full contract or proportional subset in the feature spec before writing HTML. A no-contract decision belongs in the plan or PR note so reviewers can see why the contract was unnecessary.

## Decide the size

Write the full 12-field contract for a new route, a key onboarding surface, a feature-gating screen, or any significant surface where the first screen, primary action, data consequence, states, responsiveness, accessibility, or measurement could change the implementation shape.

Write a proportional subset for a smaller component change when only some decisions can change the implementation. A new form field, tooltip, minor component variant, or local empty-state copy change usually needs only the fields that settle user intent, consequence, states, and accessibility.

Write no contract for a trivial change that cannot alter user flow, state handling, layout, accessibility, data reads or writes, or measurement. Record the no-contract decision in the plan or PR note so the omission is explicit.

## Use the canonical fields

Preserve these field names exactly when you write a contract or subset:

| Field | What it means |
|---|---|
| target user | The specific user type or persona this surface serves |
| primary job | The one job the user comes here to complete |
| primary action | The single most important action available on this surface |
| expected result | What the user sees or has after completing the primary action |
| next action | What the user does after the primary action is complete |
| first-screen content | What must be visible above the fold without scrolling |
| product proof | The value signal, such as a stat, social proof, or outcome indicator, present above the fold |
| read/write consequence | Whether the primary action reads or mutates data, and what happens on error |
| critical states | Which applicable states the surface must handle; for a significant surface include at least loading, empty or first-run, error, and content |
| responsive behavior | How the layout adapts across breakpoints; what collapses, reorders, or hides |
| a11y requirements | WCAG 2.2 AA requirements and any state-specific needs such as focus management or live regions |
| measurement event | The analytics event that fires on primary action completion |

Do not rename fields to fit local language. Add local detail inside the field value.

## Write a full contract

Use the full contract when the surface is large enough that several implementation choices depend on the answer. This example is for a new workspace invitation page.

| Field | Contract |
|---|---|
| target user | Workspace admin inviting colleagues during setup |
| primary job | Invite the first team members so the workspace can move from solo setup to shared use |
| primary action | Submit one or more email addresses with assigned roles |
| expected result | Invitations are sent, invited people appear in a pending list, and the admin sees which addresses need correction |
| next action | Review pending invitations, copy an invite link if needed, or continue to the next setup step |
| first-screen content | Page title, one-sentence setup context, email entry field, role selector, pending invite list, primary submit button, and setup progress |
| product proof | Setup progress indicator showing that inviting colleagues unlocks the next workspace step |
| read/write consequence | Submitting writes invitations; duplicate or invalid addresses stay editable with inline errors and no valid address is lost |
| critical states | loading, first-run, empty, error, content, success, disabled, permission/denied, offline, keyboard-only, high-zoom, reduced-motion |
| responsive behavior | Desktop shows entry form beside pending invites; tablet stacks form above list; mobile keeps the submit action visible after the email field and collapses secondary setup help |
| a11y requirements | WCAG 2.2 AA; invalid emails announce through an inline error and live region; focus moves to the first failed address after submit; role selector is keyboard operable |
| measurement event | `workspace_invites_sent` fires after at least one invitation is accepted by the API, with count and role mix |

After approval, implementation can proceed against this contract. If the design later changes the primary action, write consequence, critical states, or first-screen content, update and re-approve the contract before continuing.

## Write a proportional subset

Use a subset when the work is local but still affects user interpretation or accessibility. This example adds helper text and validation to an existing billing email field.

| Field | Contract |
|---|---|
| target user | Account owner updating billing settings |
| primary job | Enter the email address that receives billing notices |
| primary action | Save the billing email field |
| expected result | The saved email appears in the billing settings form with a confirmation message |
| read/write consequence | Saving writes the billing contact email; invalid input blocks save and keeps the typed value visible |
| critical states | error, content, success, disabled, keyboard-only |
| a11y requirements | Error text is associated with the field; confirmation is announced without moving focus away from the field |
| measurement event | Reuse the existing billing-settings save event; do not add a new event for helper text |

This subset is enough because the change does not create a new route, change first-screen hierarchy, introduce a new responsive layout, or add a new product proof requirement.

## Record no contract

Skip the contract only when the work is plainly trivial. Examples: correcting a typo in static copy, changing an icon to the approved equivalent without changing meaning, or adjusting a token value that already belongs to a broader approved design change.

Record the decision in one sentence:

> No page/screen contract: copy typo only; no user flow, state, layout, accessibility, data, or measurement behavior changes.

If that sentence is hard to write truthfully, use a subset instead.

## What to approve

Approve the contract scope before significant UI code. Check three things:

- The chosen size matches the risk: full contract, subset, or no-contract decision.
- Any included field uses the canonical field name and contains enough detail to guide implementation.
- The read/write consequence, critical states, responsive behavior, accessibility requirements, and measurement event are not left implicit when they can affect the build.

The likely next step is to implement the surface under the approved contract. For an existing surface with unknown quality, run an audit or status pass before implementing.
