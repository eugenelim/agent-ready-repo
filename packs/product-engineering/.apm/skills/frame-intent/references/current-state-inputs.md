# Current-state inputs — a brownfield-only tool

These are **optional inputs**, gated by the per-intent **maturity** flag. They
attach to the opportunity (outside-in) or the eventual spec (inside-out) — never
to the intent's *requirements* directly.

## The maturity gate

- **greenfield** (building something new): **skip** current-state maps. There is
  no existing process or experience to model, and mapping one you're about to
  replace paves cow paths. Frame the job forward with a JTBD job map.
- **brownfield** (an existing system / process / experience): **offer** the two
  inputs below — they earn their place when there's a real current state to
  account for.

## The two inputs

- **Journey map (outside-in).** Surfaces *where the existing experience breaks*,
  which points at the opportunity. The modern default is the lighter **JTBD job
  map** (what the user is trying to get done, solution-independent); reach for a
  full customer-journey map only in the heavier CX / enterprise case. Either way
  it *feeds the opportunity*, it is not the requirement.
- **Process map (inside-out, L3).** The operational reality the solution must fit
  — used as a **constraint on the eventual spec**, never as the requirements
  anchor. Right in regulated / ERP / ops work where the process exists and must
  persist; a trap as the source of requirements (it bakes in the incumbent
  solution). The detailed map belongs downstream at the spec stage, not in the
  intent.

## The rule

Both are *inputs that feed a node of the intent*, not nodes themselves, and both
are **optional**. Their value rises from `app`/greenfield (rarely worth it) to
`business-unit`/brownfield (often load-bearing). When in doubt, frame the job
forward and skip them — you can always add a constraint at the spec stage.
