# Implementation review round 1

## Blockers

**1. Runtime command output exposes a literal placeholder.** `packs/atlassian/.apm/skills/jira/scripts/_client.py:65`
Script-emitted Jira remediation and Markdown-to-HTML help expose `<skill-dir>`
instead of constructing command text from the resolved installed entry point.
Fix: derive the runtime command display from each script's resolved path and
update tests to reject the placeholder.

**2. Crawler diagnostics expose a raw headed broker command.** `packs/atlassian/.apm/skills/confluence-crawler/scripts/_client.py:325`
Confluence Crawler can emit raw `sso-broker register` guidance from an agent-run
crawl error. Fix: route the bounded message through the skill-owned resolved
`setup_sso.py` operator command and forbid raw broker registration in
non-operator diagnostic surfaces.

**3. Manual QA has no reviewable record.** `docs/specs/skill-script-exit-2-collision/plan.md:328`
Required project-root and missing-entry manual QA has no reviewable artifact.
Fix: add a bounded record with generic paths, outcomes, and the environment's
dependency limitation.

## Concerns

**4. Jira recovery can relay raw broker diagnostics.** `packs/atlassian/.apm/skills/jira/scripts/jira.py:709`
Jira automatic headless recovery can relay broker exception and inherited
stderr text. Fix: suppress inherited stderr, log only the exception type, and
emit fixed bounded operator remediation with secret/path-shaped regression
cases.

**5. Confluence setup helper points at Jira.** `packs/atlassian/.apm/skills/confluence-crawler/scripts/setup_sso.py:16`
Confluence Crawler's setup helper still describes Jira's ordinary first-run
command. Fix: describe `crawl_space.py --check` and `setup_sso.py`, and assert
that Crawler surfaces do not name `jira.py`.

**6. Installed-entry prose contains literal newline escapes.** `packs/atlassian/.apm/skills/jira/SKILL.md:30`
All eight installed-entry contracts contain literal `\n` escape sequences.
Fix: replace them with real line breaks and protect the rendered prose.

## Nits

None.

## Procedural note

The adversarial reviewer also asked for `Shipped`/`Done` metadata. The work-loop
requires those transitions only after every warranted reviewer returns clean,
so that item is deferred to the clean-review finish step rather than treated as
an implementation finding.

## Remediation disposition

1. Resolved command renderers now feed Jira remediation and every affected
   runtime help surface; behavioral tests require the resolved entry and reject
   literal `<skill-dir>` output.
2. Confluence Crawler 401/redirect diagnostics now point to its resolved,
   skill-owned `setup_sso.py`; tests reject raw `sso-broker register` output.
3. `notes/manual-qa.md` records the three project-root class probes, the final
   six-launch verification requirement, and the unavailable disposable-agent
   harness without claiming results the environment cannot produce.
4. Jira logs only the broker exception type and emits fixed operator
   remediation; a secret/path-shaped regression proves caller-owned exception
   text is absent. The broker child still inherits stderr before the exception
   reaches Jira. Changing that private broker boundary is outside the approved
   four-pack caller-contract patch, so `credbroker-refresh-stderr-bounding` is
   captured in `workspace.toml` with a cold-start fix description.
5. The byte-parity-governed Jira/Crawler helper now neutrally directs users to
   the primary check documented by the active `SKILL.md`; Crawler's skill names
   `crawl_space.py --check`, and its source-contract test rejects `jira.py`
   anywhere in the shipped Crawler skill.
6. All eight prose contracts now use real Markdown line breaks.
