## Adversarial Review — Pass 1

**1. Duplicate changelog entry.** `docs/product/changelog.md`. Stale phantom line 76 claimed rename in 0.13.0 (linked to non-existent spec). Fix: deleted stale entry; kept accurate new entry.

**2. RFC-0066 body edited — Never-do violation.** `docs/rfc/0066-...md:402`. `_(Discharged…)_` appended to Follow-on-artifacts bullet. Fix: reverted append; Errata #1 alone carries the discharge.

**3. Grep-verified count inaccurate.** `spec.md:53`. Count said 20; correct is 21 (includes SKILL.md + evals.json in renamed dir). Fix: updated to 21 in spec and errata text.

**4. Single-entry errata uses table shape.** RFC-0055 D2: single entry stays a plain dated bullet. Fix: converted to bullet form.
