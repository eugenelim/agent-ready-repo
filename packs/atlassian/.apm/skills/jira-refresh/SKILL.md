---
name: jira-refresh
description: Reviewed refresh and confirmed Jira coordination write-back processor for tracker-origin artifacts.
allowed-tools: Read Bash
metadata:
  boundaries:
    - network_fetch
    - filesystem_read_untrusted
    - filesystem_write
  credentialed: true
  primitive-class: credentialed-cli
  auth: sso-cookie
  auth-fallback: creds
  namespace: jira
  keys: ["API_TOKEN"]
---

# Jira Refresh

This processor is invoked by `work-intake` refresh after the shared refresh
runtime has resolved the artifact, lifecycle, authority record, approver, and
confirmation. It does not create artifacts, classify tracker content, or select
processors.

Supported write-back is limited to existing Jira client commands:

- `comment` uses `add_comment`.
- `display-status` uses `transition_issue`.
- `closure` uses `transition_issue`.

Trace links, pull-request links, requirement fields, and arbitrary custom field
updates are unsupported unless a future Jira client adds a narrow command for
that action. Jira SSO-cookie authentication remains read-only for refresh:
every non-GET/HEAD write-back action refuses before the client transport is
called.
