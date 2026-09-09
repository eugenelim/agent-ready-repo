# Security-checklist evidence — direct skill identity and upgrade

Records the resolved findings for the five lenses required for the direct-skill
upgrade route: resolved path/file, outbound acquisition, supply chain,
exceptional condition, and agentic skills. Each lens states the relevant
finding or why it does not add a new obligation.

---

## Resolved path/file

| Check | Disposition | Evidence and control |
| --- | --- | --- |
| Stored source and `source-path` confinement | Resolved | Upgrade re-establishes the source root and re-runs the shared admissibility and confinement path before planning or writing. A moved or missing `source-path` refuses instead of selecting a replacement envelope. |
| Destination inspection | Resolved | A destination that cannot be inspected fails closed. It is not treated as byte-identical or unedited, so an unsafe or unreadable target cannot pass into replacement. |
| AC12 deletion pass: obsolete owned file | Resolved | AC12's deletion pass validates the target's parent beneath the projection root before `unlink`. An unsafe parent is retained; an `unlink` failure refuses under `CAT-D020` without a state write that disowns the surviving file. |
| AC12 deletion pass: empty-directory prune | Resolved | AC12's deletion pass independently validates each directory beneath the projection root before `rmdir`. A failed prune refuses under `CAT-D021`; it cannot redirect pruning outside the agent instruction directory. |
| Ordering of destructive work | Resolved | AC12's deletion pass runs before the state write. The state row therefore cannot claim that a still-present file was removed after an incomplete destructive step. |

AC12 is the first route in this feature that removes files from an agent
instruction directory. Its confinement checks are therefore required at both
destructive operations, not inferred from the earlier write plan.

## Outbound acquisition

| Check | Disposition | Evidence and control |
| --- | --- | --- |
| New outbound destination | Not applicable | Upgrade reuses the credential-free `git+https://github.com/<owner>/<repo>@<ref>` acquisition path and its same-repository redirect policy. It introduces no host, protocol, credential, or redirect exception. |
| Acquisition before consent | Resolved | A remote upgrade without `--yes` refuses before acquisition; `--dry-run` is the non-writing route that may resolve and display the consent surface. |
| Mutable-ref substitution in remediation | Resolved | When capability widening refuses, the printed remove-then-install remediation is pinned to the already resolved revision rather than the mutable ref. A later ref move cannot substitute different bytes into the command the adopter was shown. |

The outbound-acquisition lens adds no transport exception, but it remains
applicable because standalone upgrade can initiate the existing remote fetch.

## Supply chain

| Check | Disposition | Evidence and control |
| --- | --- | --- |
| Prior capability history supplied by adopter-writable bytes | Resolved | The prior `SKILL.md` read is integrity-bound to the selected row's recorded file digest. The digest comparison precedes metadata parsing, so pre-writing the candidate bytes cannot make a widening compare against itself. |
| Uninspectable prior declaration | Resolved | Missing, unreadable, malformed, unsafe, or digest-mismatched prior bytes produce an unknown prior surface and fail closed rather than being treated as unchanged. |
| Candidate revision binding | Resolved | Acquisition records and uses the resolved revision and source digest. Update availability is based on admitted bytes, not on the manifestless version sentinel or a mutable ref label. |
| Capability widening | Resolved for this route | Upgrade compares `allowed-tools`, `metadata.boundaries`, and `metadata.credentialed`; any widening or unknown prior surface refuses before confirmation and before writes. Content-only and capability-narrowing changes remain reachable. Explicit re-consent remains separate work. |
| Identity-refusal suppression | Resolved | The `CAT-D022` suppression flag is set only after the selected row and supplied source pass the identity comparison. It suppresses exactly the one install-side different-ref refusal needed for the upgrade path; it does not suppress source, ownership, destination, or capability refusals. |

## Exceptional condition

| Check | Disposition | Evidence and control |
| --- | --- | --- |
| Refusal or declined confirmation writes state | Resolved | Re-admission, capability comparison, plan rendering, and confirmation precede projection and state mutation. Each refusal and a declined prompt leave the recorded row and projection unchanged. |
| AC12 deletion pass: ownership cannot be established | Resolved | AC12's deletion pass keeps the file and its ownership entry when either scope's state cannot be read. Uncertainty is not converted into permission to delete. |
| AC12 deletion pass: `unlink` failure | Resolved | A failed obsolete-file removal exits under `CAT-D020`; the file and owning row remain. The failure cannot fall through to the state write. |
| AC12 deletion pass: prune failure | Resolved | A failed empty-directory prune exits under `CAT-D021`; the already removed file stays removed, the empty directory remains, and the owning row is not rewritten as a completed upgrade. |
| State-write ordering | Resolved | Destructive deletion completes before the state write, closing the residual where an interrupted write-first sequence could leave an absent file still represented as installed. |

AC12's deletion pass deliberately has different incomplete outcomes for an
unknown owner, a failed unlink, and a failed prune. Treating them as one cleanup
case would hide which bytes and ownership claims still exist after failure.

## Agentic skills

| Check | Disposition | Evidence and control |
| --- | --- | --- |
| Malicious instruction content | Accepted residual | Admission bounds shape, metadata, and bytes; it does not establish benign intent. Upgrade repeats the install consent surface and never executes publisher code during installation. |
| Permission widening | Resolved for non-consenting upgrade | The prior integrity-bound and candidate capability surfaces are compared before mutation. Widening tools, boundaries, or credentialed status refuses; there is no acceptance flag on this route. |
| Untrusted metadata parsing | Resolved | Candidate and prior declarations use the bounded metadata parser. The prior bytes must also match the recorded digest before parsing. |
| Version drift | Resolved | The row records resolved revision and digest, and the upgrade summary distinguishes stored from re-resolved identity. A pinned remediation uses the resolved revision. |
| Governance and recovery | Resolved | Refusals carry registered diagnostics and executable remediation. Different-ref and moved-path refusals terminate through remove-then-install when the direct upgrade route cannot apply. |

## Residuals and provenance

No unstated blocker remains in these five lenses. The accepted residual is the
same one as direct installation: deterministic admission and capability consent
do not prove that natural-language instructions are safe.

This record consolidates the implementation's completed review rounds and the
tests that make their controls falsifiable. It is evidence to re-check against
the implementation, not a claim that prose itself enforces the controls.
