# Credential broker contract manual qa

- **Status:** Open
- **Kind:** defect

## Summary

Six real platform-by-mode manual-QA transcripts remain unrecorded under `docs/specs/credential-broker-contract/notes/`; they are the oracle for criterion 42 of the shipped `credential-broker-contract` spec:

- `creds` × macOS
- `creds` × Windows
- `creds` × Linux
- `sso-cookie` × macOS
- `sso-cookie` × Windows
- `sso-cookie` × Linux

Settle when every row uses its real platform store and an approved corporate-SSO endpoint, and records PAT resolution and an `sso-broker` test exit of 0. Its subject matter is otherwise the same as the `live-credential-transcripts` slice.
