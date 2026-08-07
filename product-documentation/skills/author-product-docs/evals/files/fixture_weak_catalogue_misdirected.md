<!-- WEAK FIXTURE: catalogue-facing content written to docs/guides/ (wrong tree) -->
<!-- Demonstrates the anti-pattern of routing external user content to the
     internal maintainer tree — should have gone to guides/<pack>/ not docs/guides/ -->

# How to use the desk-research pack

This guide was written to docs/guides/how-to/use-desk-research.md, which is the
internal maintainer documentation tree. This is wrong: the desk-research pack's
user-facing how-to belongs in guides/desk-research/how-to/ instead.

Writing external product documentation to docs/guides/ means it is never
projected to adopters — they will not see it in the docs-site or web interface.
The audience (adopters using the pack) will not find it.

Additionally, this guide:
- Leads with the skill name (`desk-research`) before showing what the user can accomplish
- Opens with "This guide will explain how to use the desk-research skill" rather than a user goal
- Lists all available skill modes before showing the first useful request
- Does not show a natural-language starter request in the first 120 words
- Claims the research "produces high-quality results" without citing what was verified
- Links to docs/architecture/overview.md which is not a user-facing resource
