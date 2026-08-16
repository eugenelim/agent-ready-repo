# Enquire Mode

Read only the committed topic map and eligible topic bodies. Freshness checks
select the source from the committed topic and return verification metadata;
they never expose source bytes to enquiry mode.

This mode cannot read observation journals and cannot invoke mutation helpers.
