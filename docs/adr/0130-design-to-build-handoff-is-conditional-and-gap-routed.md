# ADR-0130: The design-to-build handoff is conditional, and implementation never fills an upstream gap

- **Status:** Accepted
- **Date:** 2026-09-28
- **Areas:** experience, packaging
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** ADR-0139 D2
- **Related:** ADR-0128 (one `design-system` skill resolves project values — this record decides who owns a value that skill did not resolve); RFC-0071 (Digital Experience Doctrine — the cross-pack thread this completes at the design-to-build seam); ADR-0024 / RFC-0033 (agnosticism guardrails — the "no universal defaults" rule this preserves on both sides of the seam); ADR-0052 (the rename that made `design-system` the canonical name used here)

## Decision summary

- **Decision:** We will make the design-to-build handoff conditional and gap-routed: frontend implementation resolves a visual value itself only where no upstream design authority still owes it, and routes every axis upstream owes back to the owner the design artifact records.
- **Because:** a design thread that resolves concrete values is worth nothing if the build step silently re-decides them whenever an artifact is missing, so the gap has to be a routing signal rather than a licence.
- **Applies to:** the seam between the `experience-design` pack's `design-system` artifact at `<output_dir>/tokens/<slug>.md` and the `frontend-engineering` pack's shared pre-flight; it does not change the handoff read's confinement controls or either pack's skill inventory.
- **Tradeoff accepted:** a run can now stop part-way with work routed upstream instead of producing a complete surface, and two shipped acceptance criteria are superseded to pay for it.
- **Revisit if:** an adopter with a partially-covering incumbent system finds the gap routes work upstream that the incumbent should have owned, or the frontend entrypoint can no longer state the contract within its body budget.

## Context

`design-system` resolves project-specific values and records a domain no
authority reached as unresolved, naming who resolves it. The frontend pack's
shared pre-flight resolves visual authority from a four-rung precedence and,
when neither a token taxonomy nor an incumbent system supplies a value, reads a
bundled fallback token block or states a local premise in-session.

Those two contracts meet badly. The frontend precedence treats "no taxonomy
resolved" and "no design authority exists" as the same state, so an approved
direction with no derived system demotes straight past the design thread to a
rung that invents values. The terminal `local-premise` rung is documented as
always available, which makes inventing a value the guaranteed terminal outcome
of every chain. And a taxonomy that explicitly marks a domain unresolved —
the design thread's way of saying "nobody decided this, and here is who must" —
reads downstream as silence, because nothing consumes that record.

The published orchestration says the same thing from the other side: the design
thread's journey and its public how-to both label `design-system` broadly
optional, so an adopter who skips it is following the documentation.

The result is that the values a product's design thread exists to decide are
decided instead by whichever agent writes the code, at the surface with the
least design context, from category habit. That is the failure the agnosticism
guardrails already forbid a pack from shipping — relocated one step downstream,
where no rule reached it.

## Decision

We will make the design-to-build handoff conditional and gap-routed.

- **D1:** Frontend implementation resolves a visual value itself only for an
  axis that every higher rung left open **and** that no upstream design
  authority still owes.
- **D2:** An **upstream gap** is a hold-and-route state, not a rung. It has
  exactly two sources: a resolved direction artifact beside a *named-skip*
  taxonomy slot that no incumbent system covers, and a conforming taxonomy that
  records a needed domain unresolved. A refusal never becomes a gap: a refusal
  halts the mode and reaches no rung and no gap at all.
- **D3:** A lower rung fills an axis only when every higher rung genuinely left
  it open and that rung is the accepted owner of it. An incumbent system is the
  accepted owner of what it actually covers; an explicitly unresolved domain has
  no lower owner, because the upstream skill already consulted every rung it
  could and found none.
- **D4:** The terminal `local-premise` rung is admissible only for genuinely
  standalone work — no applicable design artifact, no incumbent system, and no
  upstream authority left to complete — and only from a handoff read that
  completed rather than refused.
- **D5:** The bundled fallback token block is a **separate** gate from D4's
  standalone admission, because a repository can carry an incumbent visual
  system and no incumbent token system, and so reach the fallback for values
  while standing on the incumbent rung for composition. It is read only when no
  token taxonomy resolved, no incumbent token system exists to extend, and no
  upstream gap holds the axis. Conflating the two gates mis-states the
  brownfield case that has a house style but no token file.
- **D6:** `design-system` is required when a direction exists and neither a
  completed design system nor a coherent incumbent system supplies every
  concrete value the surface needs, and optional otherwise. Its published
  optionality is therefore `Conditional`, a first-class value alongside
  `Required`, `Optional` and `Choose one` on the design thread's tables.
- **D7:** The frontend entrypoint states this contract inline rather than only
  by reference, because the pre-flight is what an agent always loads. Its body
  budget rises from 960 to 968 lines to pay for that.
- **D8:** The owner or operation read out of an adopter-controlled artifact to
  route a gap is live/display-only data. It carries no instruction authority, is
  never loaded, invoked, executed, opened, resolved as a path, used to locate
  another file, or matched against any skill, tool, command or agent name. The
  committed gap record persists only the held axes plus one fixed non-sensitive
  operation kind (`taxonomy-supply-required` or `domain-completion-required`);
  literal artifact owner or operation values are never committed.

## Decision drivers

- **A missing artifact must not read as permission.** The seam is only worth
  building if absence routes rather than licenses.
- **Neither pack may depend on the other.** Both install standalone, so the rule
  has to be expressed over adopter-owned artifact addresses and the owner an
  artifact records, never over an upstream pack or skill name.
- **The standalone path stays usable.** A frontend contributor with no design
  tree at all must still be able to finish a surface.
- **No new universal defaults.** Nothing here may introduce a house palette,
  scale, or motion table on either side of the seam.

## Consequences

**Positive:**

- A resolved taxonomy's project-specific values reach implementation unchanged
  except for documented accessibility or platform adaptations.
- An explicitly unresolved domain becomes an actionable routing signal with a
  named owner, instead of a blank another agent fills.
- The condition under which the design system is genuinely optional — an
  incumbent system that already covers the work — is stated rather than implied
  by a blanket "Optional".

**Negative:**

- A run can stop part-way, leaving an operator with routed work rather than a
  finished surface. That is the intended behaviour and it is still a cost.
- Two shipped acceptance criteria are superseded in part: the frontend
  entrypoint's 960-line body budget, and the three-member optionality
  vocabulary on the design thread's published tables.
- An adopter whose incumbent system covers a surface only partially may find the
  boundary between "the incumbent owns this" and "upstream owes this" needs
  judgement that no check makes for them.

**Revisit if:** an adopter with a partially-covering incumbent system finds the
gap routes work upstream that the incumbent should have owned, or the frontend
entrypoint can no longer state the contract within its body budget.

## Alternatives considered

- **Add `upstream-gap` as a fifth rung.** Rejected against the driver that the
  rule must stay legible: a rung answers "where does this value come from", and
  a gap withholds a value, so a stop-row inside a table of suppliers would read
  as a supplier and would break the demotion chain the precedence already pins.
- **Make `design-system` unconditionally required.** Rejected against the
  standalone-usability driver and against honesty: an adopter whose incumbent
  system fully covers the surface does not need a new one, and a table saying
  otherwise would be wrong in the common brownfield case.
- **Leave the rule in the reference only.** Rejected because the reference is
  loaded on a predicate while the pre-flight is always loaded, so a contract
  stated only in the reference is a contract an agent can complete without
  reading.

## Confirmation

- **Mode:** lint/CI
- **Signal:** the rule tables in the frontend pack's visual-observation
  reference are read by a pack construction suite rather than restated by it,
  and the two packs' eval corpora each carry a case that grades routing rather
  than inventing; the cross-tree prose agreement is asserted in the roster
  suite, which is the only tree allowed to read both packs and the guides.
- **Owner:** the `experience-design` and `frontend-engineering` pack maintainers.
