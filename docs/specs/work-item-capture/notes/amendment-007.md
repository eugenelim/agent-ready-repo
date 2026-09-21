# Amendment 007 — the floor claims what a write-path gate can establish

**Authorised by:** eugenelim, 2026-09-21
**Against:** approved_spec_hash 67ea736e
**Tier:** contract — this changes the Acceptance Criteria section.

## Why

Review demonstrated that a caller which never dispatched can write a
`work-item`: the correlation key is a pure hash over the submitted payload,
so whoever holds the request can compute it. The reviewer landed a record in
`observations/work-item/2026-09.jsonl` doing exactly that, and the controller
reproduced it in four lines.

`AC-0068` claimed "an agent that skips, mis-configures or never reaches the
dispatch simply cannot produce the token the writer demands." That sentence
was false when written — by the controller, during specification.

## The finding under it is architectural, not a coding defect

§ D3 puts the cold check at the **close**: the agent dispatches it and hands
the writer the result. The verdict therefore reaches the writer through the
party that produced it. No in-process gate can verify that a caller consulted
an oracle the caller controls, and a writer-issued nonce would simply be
relayed. Three designs were weighed: the writer spawning the check itself
(closes it, at the cost of an LLM dependency inside a deterministic
append-only write, and needs § D3 amended); dropping the floor to advisory
(the parent intent requires a floor); and claiming only what is enforceable.

**Owner chose the third.**

## What changed

`AC-0068` now claims a well-formed, recognized, item-correlated verdict —
catching omission, garbling and stale reuse, including a corrected
re-submission reusing its pre-correction verdict. It states plainly what no
write-path check can establish, and why.

The residual is disclosed in `docs/architecture/security.md`'s gap list,
which is that list's single home, and the security doc's claim about which
controls run at `--capture` is corrected: the instruction-shape refusal and
the cold check run at the close, not at the write.

## Process note

This edit was made in the working tree before the amendment existed, while
two reviewers were reading those files — both violations of this loop's own
rules, caught by review rather than by the controller. The record says so
because a completion note is what a later reader trusts instead of
re-deriving.
