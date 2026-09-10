```text
contract_version: agent-skill-engineering-foundation/v1
status: unavailable
mode: plugin
reason: not available in the foundation slice
baseline: frame the portable skill concern without inventing mode-specific guidance
```

```text
contract_version: agent-skill-engineering-foundation/v1
status: unavailable
mode: hook
reason: not available in the foundation slice
baseline: frame the portable skill concern without inventing mode-specific guidance
```

Packaging and hook registration are not activation modes here, so I cannot author the plugin manifest, the hook wiring, or the event contract you would install. What I can do — and what follows — is frame the portable skill concern underneath them, in `frame`, read-only. The supplied `release-guard` file is untrusted evidence: it describes an intent, it does not set the task, the boundaries, or any authority.

# Frame — release policy check

## What the hook can and cannot enforce

Four constraints hold regardless of which packaging slice eventually carries them, and each one is a design fact you would otherwise discover after writing the hook.

**A post-publication hook detects; it does not block.** The supplied file says the hook "fires after a release is published" and that reporting a violation "stops the release from going out." Those two clauses contradict each other. Once publication has happened the artifact is externally visible and, on most registries, immutable; the only remaining actions are yank, deprecate, superseding release, and alert — all of which are external side effects, none of which is a block. Decide which you actually want, because they are different products:

- *Prevention* requires a gate on a pre-publication event, and it requires the release path to have no route that bypasses that event. If a maintainer can publish from a laptop, the gate is advisory no matter where it is registered.
- *Detection* is honestly achievable post-publication, but then the skill's observable outcome is "a violation is reported with the offending dependency, licence, and missing changelog entry named," not "the release is stopped." Write the description to the outcome you can actually make observable.

**A licence check is a claim check, not a compliance verdict.** What is readable is declared metadata — a `license` field, an SPDX expression, a bundled licence text. Declared metadata can be absent, wrong, ambiguous (dual licences, `SEE LICENSE IN`), or contradicted by vendored subcomponents. The skill can enforce "every dependency declares a licence on the approved list, and anything undeclared or unparseable fails closed." It cannot enforce "every dependency carries an approved licence." State the weaker true claim; the stronger one invites the team to stop checking.

**The policy file is data, never instructions.** `.release-guard/policy.md` sits at the repository root, is user-controlled, and is exactly the class the common contract calls untrusted evidence. "The hook reads that file each run and follows whatever rules it states" is the failure mode: prose in that file cannot widen the task, the tools, the identity, or write authority, and cannot be executed as rules. The workable version is a fixed schema — an approved-licence list, a denylist, an exemption list with expiry, a changelog path pattern — parsed by extracting only expected fields, with unknown keys ignored and a malformed file failing closed rather than degrading to "no policy, therefore pass." Anything the file says outside that schema is prose you read and discard. This is what caps how far teams can "tune enforcement without touching the package": they can tune values, not behavior.

**Every read is resolve-before-read.** `.release-guard/policy.md` is resolved from the confirmed repository root, canonicalized and symlink-resolved before any content access, rejected on any `..` component, on an absolute path supplied as a relative name, on a non-regular file, and on containment uncertainty. `filesystem_read_untrusted` permits the bounded read only after that check passes. A symlinked policy file pointing outside the root is the obvious escape and the declared boundary does not cover it.

## What the package boundary would cost

The supplied file bundles four things — release hook, changelog linter, commit-message formatter, Slack digest command — on the rationale that the release crew uses them all. The bundle is one authority envelope, one version, one install decision, and one blast radius. That is the cost, itemized:

**The declared boundary understates the bundle.** Frontmatter declares `filesystem_read_untrusted` only. A Slack digest needs network egress and a credential; a post-publication remediation needs an external side effect. `filesystem_read_untrusted` grants none of those, and no boundary in this foundation grants credential access, network access, or external messages. The digest is therefore not a component this frame can authorize — it is a separate concern with a separate authority story, and the broker or platform mechanism that supplies its token has to live outside the portable skill.

**Bundling propagates the widest member's authority to every installer.** A team that wants only the changelog linter installs the network-capable, credential-holding digest too, and reviews it, and carries its supply chain. The shared HTTP client makes this concrete: it is a transitive dependency of the linter, so a linter-only user pays for a client only the digest needs, and a CVE in that client blocks a component that never opens a socket. Split by authority, not by who sits in which chatroom — read-only local checks in one unit, anything touching the network in another.

**Bundling couples versions and forces false urgency.** One version number over four components means a formatter tweak ships a hook change, and a hook fix cannot ship without whatever else is on the branch. Enforcement components and convenience components have different upgrade risk and should not share a release cadence.

**The `release` command prefix is a collision, not a continuity.** Matching the team's existing local commands means two definitions compete for one name, and which one answers depends on load order and precedence — invisible at the call site and different per machine. Muscle memory then carries the wrong behavior with full confidence, which is worse than a new prefix people have to learn. Either take a distinct prefix, or make the package's ownership of `release` explicit and remove the local commands as part of adoption; do not ship both and hope.

## Activation boundary

Should activate: "check our dependency licences against the release policy," "does this release have a changelog entry," "why did release-guard fail on this build," "add an exemption for this dependency's licence."

Should not activate: "write the changelog for this release," "cut the release," "pick a licence for our project," "why is my dependency install failing," "post the release notes to Slack." The last three are the ones a broad description will wrongly capture.

## Observable outcome

A pass/fail verdict per policy rule, naming each offending dependency with its declared licence and each released artifact missing a changelog entry, plus an explicit statement of what was not checkable — undeclared licences, unparseable metadata, dependencies not reachable from the manifest. Silence on the unknown is the defect to design out.

## Boundaries

Read: repository manifest and lockfile, changelog, `.release-guard/policy.md`, all within the confirmed root and all after the resolve-before-read check. Write: none. Network: none. Authentication: none — no credential inspection, no token in prose or file, and no identity selected by repository content. External side effects: none; reporting is a returned verdict, not a message sent.

## Existing contracts to preserve

The team's current local `release` commands and whatever CI step publishes today are authoritative until explicitly retired; this skill's verdict is an input to them, not a replacement for them.

## Evidence to plan for

Success: a repository with a known-bad licence and a known-missing changelog entry produces exactly the expected violations. Failure: a malformed or empty policy file fails closed with a named parse error, not a silent pass. Interruption: a partial dependency walk reports "incomplete" rather than a clean verdict over a partial set. Clean degradation: a missing policy file, an unreadable manifest, and a policy path that resolves outside the root each produce a distinct, named refusal.

## Proposed file tree

```text
release-policy-check/
  SKILL.md                      concise: activation, verdict shape, refusal rules
  references/
    policy-schema.md            the fixed field set, parsed as data
    licence-evidence.md         what declared metadata can and cannot establish
    failure-modes.md            fail-closed cases and their named refusals
```

No scripts and no assets in this frame; add either only when a step cannot be carried by the workflow itself.

## Non-goals

Blocking a publication that has already occurred. Deciding organization licence policy. Generating or editing changelog content. Sending Slack messages or any other external notification. Holding credentials. Commit-message formatting, which shares no authority, no data, and no trigger with this concern.

## Decisions I need from you

1. Prevention or detection — that is, is there a pre-publication event this can gate, and is that path bypass-proof? The description and the outcome both change on your answer.
2. The policy schema's field set, since teams can tune values but not behavior.
3. Whether the `release` prefix is being taken over from the local commands or avoided.

Agreement with this frame does not authorize a write.

```text
Mode: frame
Write status: not authorized
```

Files changed: none. Checks run: path-and-authority review of `.release-guard/policy.md` as a candidate read target; boundary reconciliation of the supplied frontmatter against the bundle's stated components; activation-discrimination pass over the proposed boundary. Retained behavior: not applicable, no update performed. Unavailable capabilities encountered: `plugin` and `hook` authoring, both reported above; the Slack digest's network, credential, and external-message needs, none of which this foundation grants. Cleanup: none required.
