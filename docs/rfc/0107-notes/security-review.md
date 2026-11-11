# RFC-0107 security review record

- **Reviewer:** `security-reviewer` subagent, spec-stage secure-design mode
- **Date:** 2026-10-10
- **Scope:** D3 (the write switch in `work-intake`), D4 (status collection), and D5
  (reading another repository), at proposal depth
- **Result:** clean. The final pass returned `Clean — ready to commit.`

## Findings resolved in the RFC text

| Pass | Finding | Resolution in D3–D5 |
| ---: | --- | --- |
| 1 | The read silently reversed the rule that an external locator is never read | Supersession scoped to component-slice sources; every other locator stays opaque |
| 1 | Untrusted content was not bounded in either direction | Slice and brief text can never select a route, target, destination, tool, status, Ready, or approval |
| 1 | Pin and identity were not tied to anything checkable | Repository identity is proven before a read; the pin is an immutable commit; reads return committed content |
| 1 | Anyone could set the write switch | Only the current human request sets it |
| 1 | The provider transport and record privacy were unbounded | The provider boundary is inherited; records carry no absolute path |
| 2 | No provider read surface for repository content existed | A new provider read surface with its own boundary and an explicit credential choice |
| 2 | Parent-pointer interpretation could steer reads | Interpreting the pointer grants no read; read targets come from human-reviewed records |
| 2 | A commit pin proved immutability, not review | Reachability from the designated reviewed branch is checked |
| 3 | The local read path lacked the confinement rejection set | Regular-file entries only; symbolic-link and submodule entries refused unresolved; size limit |
| 3 | Status collection and receipt writes sat outside human control | Collection runs only on human request; every receipt write needs the human-set switch; the repo list changes only by reviewed change |
| 3 | The source of the designated branch was unstated | The branch comes from the same trusted record; specs name the ref for a local checkout |
| 3 | Brief text could leak into the meta-repo | A receipt records only the status fact, the pin, and locators |
| 3 | The provider boundary omitted authentication and redirect confinement | Authentication, redirect, and DNS stay confined to the host; the credential never goes elsewhere |
| 4 | The source of a receipt's status fact was unstated | Only the brief's lifecycle field in a commit on the designated reviewed branch counts |
| 4 | Replacement refs, grafts, or borrowed object stores could change what a pin returns | A local read applies none of them |
| 5 | A receipt could be written from an unreachable pin | No receipt is ever written from an unreachable pin |

## Deferred to spec-stage security review

- How Core proves a local checkout's identity.
- Which ref counts as the designated branch for a local checkout.
- The git invocation flags and config isolation for the commit-history read path.
- Whether the `github` provider pack's allowed actions match "read verbs only".
