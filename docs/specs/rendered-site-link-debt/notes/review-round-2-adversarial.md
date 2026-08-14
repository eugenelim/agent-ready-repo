# Adversarial implementation review — round 2

## Findings

- **Concern:** two fixture links hard-coded the current Pages base rather than
  using the marketing site's `withBase()` helper.
- **Concern:** a fixture action labelled as GitHub authentication pointed to an
  Atlassian SSO guide.
- **Nit:** the changelog described every remediation as an authored-source fix,
  omitting the four targets repaired by their owning projection rule.

## Resolution

Both fixture routes now use `withBase()`. The authentication action now names
GitHub milestone intake and targets that guide's prerequisites section. The
changelog names authored sources and owning projection rules.

