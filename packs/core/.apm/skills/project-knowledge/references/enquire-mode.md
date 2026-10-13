# Enquire Mode

Read only the committed topic map and eligible topic bodies. Freshness checks
select the source from the committed topic and return verification metadata;
they never expose source bytes to enquiry mode.

This mode cannot read observation journals and cannot invoke mutation helpers.

## Work-loop producer profile

Use `project-knowledge --enquire --producer-profile work-loop --semantic-gate
<gate>`. It performs no write. Each gate constructs a fixed competency query:

- `change`: semantic input is `task_summary`, `scope`, and declared `risk`; it
  constructs `CQ-CHANGE` and accepts `--refinement`.
- `verify`: semantic input is `task_summary`, `scope`, and declared `risk`; it
  constructs `CQ-VERIFY` and accepts `--refinement`.
- `review`: semantic input is only `task_summary` and `scope`; it constructs
  consequential `CQ-REVIEW` and refuses `--refinement`.

The calling workflow owns any one-refinement budget; this read-only command
enforces only whether the selected gate accepts refinement.

For consequential change or verify enquiries, an unverified owning source
returns `abstained: true`; canonical contracts remain authoritative.

## Invalid committed records

An invalid topic, an invalid topic-map entry, or a map entry that points at an
excluded topic is left out of the answer, and the rest of the enquiry still
answers. The result gains a top-level `quarantine` list and, when it is not
empty, the rendered text gains a separate
`<knowledge-quarantine version="knowledge-quarantine.v1">` element after the
evidence element. The evidence element and the receipt are unchanged.

Each entry holds one reason code and one location. The location is a validated
repository path under `docs/knowledge/` with a journal `line` or a map `entry`
position, or an `ordinal` when the path is unsafe to show. The reason code is
one of `malformed`, `unsafe`, `unknown_version`, `policy_invalid`,
`inconsistent`, `oversized`, `orphaned`, `dependent`, `partition_hidden`, or
`overflow`. At most 100 entries are listed, followed by one counted `overflow`
entry. No record text or hash of it appears.

A missing, unparseable, wrong-version, or link-like map file still refuses the
whole enquiry, as does a read of a topic by name when that topic is excluded.
The enquiry opens no observation journal, and a topic stays usable when a
capture it cites is excluded elsewhere.
