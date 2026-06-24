# Spec-stage review — product-rung (RFC-0043 follow-on)

Reviewers: adversarial-reviewer + design-reviewer (parallel), 2026-06-23.
Design verdict: SHIP WITH CHANGES. No Blockers from either.

All findings resolved in the same PR:
1. (adv) ADR-0019 lacked a forward pointer → added `Refined by: ADR-0033` metadata line.
2. (adv) `Constrained by:` overstated OQ3 (decide-by is post-ship) → reworded.
3. (adv) market-existence viability half not checkable → AC now requires both halves named.
4. (design M1) ADR title under-described the enum reopening → retitled to lead with it.
5. (design M2) "refines only part 1" absorbed D5 (net-new seam) → framing split (D1–D4 refine / D5 net-new).
6. (design M3) Status Proposed inconsistent with Accepted RFC + ADR-0032 precedent → flipped to Accepted.
7. (design m4) ADR D1–D5 vs RFC D1–D6 numbering → added a one-line map.
8. (design R2) core seam should be optional-upstream → seam AC + plan T7 now require "when product-engineering is installed" framing.

No action: adv#2 (spec already cites :143-146 correctly), adv#5 (AC count fine),
design#5 (house pattern, now truthful post-review), risk register R1/R3/R4/R5 (documented risk-acceptance).
