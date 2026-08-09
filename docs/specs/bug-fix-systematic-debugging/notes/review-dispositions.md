# Review dispositions

Every implementation-review finding is closed:

- Applied: removed the manual-QA stop-rule overclaim; the behavior eval owns
  that branch.
- Applied: pinned `flaky` activation in both the deterministic test and its plan
  stub.
- Applied: replaced the production-hotfix deferred-test exception with labelled
  containment followed by the permanent red-test workflow.
- Applied: added AC18, guide verification, the correct AC count, and repaired
  source-relative links in the changed guide.
- Applied: production mutations require confirmation of the exact action,
  intended scope, and blast radius unless already approved in the current turn.
- Applied: incident evidence is minimized; sensitive fields are redacted or
  sequestered; raw user data and secrets stay out of model context and durable
  repository or tracker artifacts.
- Applied: diagnostic artifacts are untrusted data. Embedded directives are
  ignored, and attempts to redirect scope, tools, or authority are surfaced.
- Applied: the production-emergency eval now contains a concrete malicious log
  directive and requires the response to ignore it without widening authority.
- Rejected with repository evidence: adding a `deploy_action` metadata boundary.
  The published catalogue vocabulary documents singular `metadata.boundary`
  values `filesystem_read`, `filesystem_write`, `network_fetch`, and
  `shell_exec`; the skill grants no deployment tool. Defining a new public
  boundary enum is outside this focused patch.

Final re-reviews returned `Clean — ready to commit.` from adversarial, quality,
and security reviewers.
