# Adversarial implementation review — round 1

## Findings

- **Blocker:** `os.walk` had no `onerror` callback, so an unreadable subtree
  could be omitted while another readable HTML page allowed the audit to exit
  clean.
- **Concern:** repeated copies of the same broken href on one page produced
  repeated diagnostics, contrary to the one source/href/target diagnostic
  contract.

## Resolution

The walker now raises an exit-2 `AuditError` for unreadable directories. Broken
diagnostics are accumulated in a set and sorted before rendering. Focused tests
cover both behaviors.

