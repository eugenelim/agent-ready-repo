# Adversarial implementation review — round 1

## Blockers

**1. Reference names the wrong layout table.** `guides/experience-design/reference/experience-design.md:339`

The updated adopter reference tells readers to use an `[experience]` layout,
but the current pack and skill contracts read `[design] output_dir`, so a reader
following the reference would configure a table the skills ignore.

Disposition: applied. The guide home and reference now name `[design]`.

**2. QA evidence points at missing ignored screenshots.** `docs/specs/xd-skill-boundaries/qa.md:21`

The QA record cited screenshots under ignored `build/`, including baseline and
reference images no longer present, so AC10's evidence was not durable.

Disposition: applied. Screenshot paths were replaced by durable inline finding
records, rendered DOM assertions, viewport measurements, and focus-order
evidence. Ignored screenshots are identified as ephemeral review aids only.

**3. AC12 and spec metadata are still open.** `workspace.toml:271`

The workspace entry remains queued, the spec and plan remain in execution
states, the index says Approved, and the acceptance criteria are unchecked.

Disposition: apply at the final lifecycle gate, after all required reviewers are
clean, because AC12 requires every other criterion to pass first.
