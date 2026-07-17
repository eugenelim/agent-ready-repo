---
pack: credential-brokers
scope: user
tagline: "Credential resolution — env → OS keyring → dotfile. Never cleartext."
prerequisitePacks: []
whatChanges: "After installing credential-brokers, every credentialed skill in your toolkit resolves its token in-process — environment variable, OS keyring, or a local dotfile — without the value ever reaching the model. You set up a credential once; every subsequent session that needs it resolves it automatically."
skills:
  - name: credential-setup
    description: "Walks through establishing a credential for a service — API key, personal access token, or SSO cookie — and stores it via the configured resolution chain."
    humanTouches: 1
humanGates:
  - id: G-setup
    globalGate: null
    label: "Confirm credential type and storage location"
    trigger: "Before credential-setup runs — to select the right resolution path"
    duration: "3–8 minutes"
    whatToCheck:
      - "What type of credential does the service require — API key, personal access token, OAuth token, or SSO cookie?"
      - "Which resolution path fits your environment: environment variable (fast, CI-friendly), OS keyring (secure, persistent across shells), or dotfile (portable, requires file-permission discipline)?"
      - "Does the credential have a scope or permission level requirement? (A read-only token that a write-capable skill needs will fail at runtime, not at setup.)"
      - "Is this credential shared across multiple services — or per-service? (A Figma token for personal files is different from a team-scoped token.)"
    whatGoodLooksLike: "A credential stored in the right resolver for your environment, with the correct scope for every skill that will use it — confirmed by a test invocation before you leave the setup session."
    whatBadLooksLike: "A credential stored in an environment variable that only exists in the current shell — it works now, silently fails in a new terminal or CI. Or a token set up for read access when the skills you're installing need write access."
    consequence: "A credential that works in setup but fails at runtime is the most common source of confusing mid-session errors. Credentialed skills report auth failures with opaque messages — the setup gate is the cheap place to discover the mismatch."
typicalSession:
  agentTurns: "2–4"
  humanTouches: 1
  wallClockMinutes: "5–15"
docsUrl: /docs/guides/credential-brokers/
packUrl: /packs/credential-brokers/
relatedJourneys:
  - figma
  - atlassian
---

## Stage 1 — Identify the credential needed

You decided to install a credentialed pack — figma, atlassian, or another service that requires an API key or personal access token. The agent walked you through identifying what credential type the service required and which resolution path to use.

**You did:** Decided where the credential would live — environment variable, OS keyring, or dotfile — based on your environment and security preferences. Read the `credential-setup` output to confirm the resolution path made sense. For most developer workstations, the OS keyring is the right choice: it persists across terminal sessions and is encrypted at rest. For CI environments, an environment variable is the right choice.

---

## Stage 2 — Set up and verify

The agent ran `credential-setup`, prompted for the token value (which was never logged), and stored it via the configured resolution chain. It then ran a test invocation to confirm the credential resolved correctly before ending the session.

**You did:** Provided the token value when prompted — this is the one moment the credential passes through your clipboard or input. Verified the test invocation succeeded. If it failed, worked through the resolution chain with the agent: is the environment variable exported in the current shell? Is the keyring unlocked? Is the dotfile in the expected location and readable?

---

## Stage 3 — Credential available to all sessions

After setup, the credential resolved automatically in every subsequent session that needed it. No repeat entry. The token value was stored in the configured location and never passed through the model again.

**You did:** Confirmed that the first real invocation of the credentialed skill worked end-to-end. The most common post-setup failure is a scope mismatch — the token was set up correctly but lacks the permissions the skill needs. If a skill returns an auth error after a successful setup, the first check is always: does this token have the right scope for this operation?
