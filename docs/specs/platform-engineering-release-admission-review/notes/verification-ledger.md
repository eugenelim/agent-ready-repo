# Verification ledger: release evidence collection, admission and focused review

Observations from the 2026-11-13 to 2026-11-15 supervised run (run `run-c2c74550a26c4281`). Execution notes only; the spec and plan keep the obligations.

## Run shape

- 40 plan tasks: T1 to T8 as planned (admission, review check, stage check, repair handoff, collector skill, reviewers and procedure, core-absent journeys, packaging), then T9 to T40 as repair tasks added from acceptance and review findings. Every implementer, acceptance verifier and reviewer ran as headless Codex (`gpt-6.1-sol`); Claude orchestrated, ran the supervisor and reported results.
- 33 acceptance rounds (every AC checked against the real artifacts) and 19 full-mode review rounds (adversarial, security, quality) before the final round came back clean from all three reviewers. About 80 findings were repaired across the rounds.
- Two owner-approved spec amendments: (1) AC-0028 and AC-0029 and the Repair routing section changed from an unconditional "never contains a secret-shaped string" to a documented best-effort redaction contract after eight rounds each found a new credential layout; (2) the `final` row of the stage table and AC-0027 were corrected where the text contradicted AC-0022 and AC-0018. Both used the parked-gate, `adopt-history`, re-`start` route.

## Final gate results (closeout tree)

- `release-loop` suite: 3,929 passed; `prepare-release-handoff` suite: 176 passed (separate pytest processes).
- `make lint-ruff lint-mypy`: clean. `tools/lint-pack-test-boundary.py`: exit 0. `make precheck`: clean (bandit not installed locally, skipped).
- Acceptance round 33 and review round 19: 44 of 44 criteria pass; adversarial, security and quality reviewers each reported `Clean — ready to commit.`
- Roster (`tests/roster/`) in the sandboxed Codex environment: 14 failures and 18 errors, all traced to a blocked `/bin/ps` or a missing `pip` / installed `agentbundle`; the `ps` group passes when run outside the sandbox. CI is the authority for the roster.
- One closeout edit outside the run: the `test_redaction_linear_time` subprocess limit went from 10 s to 60 s. Redaction is linear (8 times the input takes about 8 times as long; worst case about 4.8 s at 4 MiB), but the fixed limit failed under a machine load average near 20. The proportional-growth assertion is unchanged.

## Reviewer context size and seeded-fault detection (single run each)

Context measured as bytes of the agent definition plus the role reference it loads, against the previous brief (core `quality-engineer` plus the six `operational-safety` modules the loop routed; core `security-reviewer` plus four boundary modules). The same 1.7 KB packet is included in each brief.

| Role | Context before | Context after | Bytes (before / after) |
| --- | --- | --- | --- |
| Reliability / operational | quality-engineer + 6 modules + packet | reliability reviewer + checklist + packet | 56,555 / 10,183 |
| Security | security-reviewer + 4 modules + packet | security reviewer + checklist + packet | 33,009 / 9,351 |

At about 4 bytes per token that is roughly 14,100 against 2,500 tokens for the operational lens and 8,300 against 2,300 for security. The core roles also load their own SKILL and agent text that the new roles do not need.

Seeded faults: 12 faults in one synthetic pre-deploy packet (6 reliability, 6 security), one Codex read-only run per role, scored by hand.

| Role | Faults found | Notes |
| --- | --- | --- |
| New reliability reviewer | 6 of 6 | Returned the closed record shape with `insufficient-evidence`, because the packet carries no digests or evidence ids. |
| Old quality-engineer (operational lens) | 5 of 6, 1 partial | Named the 100% rollout but not the service-before-infrastructure ordering; added two extra concerns (production-role reach, destructive-migration gate). |
| New security reviewer | 6 of 6 | Also flagged the missing scan as a coverage gap. |
| Old security-reviewer | 6 of 6 | Also noted the missing scan. |

Limits: one packet, one run per role, hand scoring, no repeat runs. This supports a context-size reduction for the stated briefs and equal detection on this packet; it does not show equal detection in general. No shipped file claims a token saving.

## Limits left open

- Redaction in the repair handoff is a best-effort safety net. Excerpts are withheld whole when the text holds a credential word, a client command (substring match), a URL userinfo, anchors beside such content, or a recognised credential shape; evidence of kind plan or state, or matching an admitted plan by digest, is never excerpted. Languages other than English, quoted-printable and custom encodings are outside the guarantee, as the guide states. A human must review a handoff before it leaves the team.
- Collection, admission, review and stage checks verify structure, digests, bindings and evidence resolution. They do not prove a reviewer read evidence honestly, and none grants execution or production authority (`authority_checks_required: true` on every success).
- No live deployment, registry or CI source was contacted; external locators stay `unverified` until an authorised adapter exists. Section 4 owns execution authority.
- The manifest dependencies on core and repo-governance are unchanged until Section 5.
