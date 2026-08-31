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
