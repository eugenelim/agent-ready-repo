---
pack: credential-brokers
scope: user
tagline: "Credential resolution — env → OS keyring → dotfile. Never cleartext."
prerequisitePacks: []
contract:
  useItWhen: "You are setting up a credentialed pack for the first time, or a previously stored credential has stopped resolving."
  youProvide: "The service name, the credential type, and your preferred storage location."
  youReceive: "A credential stored in the resolution chain, verified by a live test invocation."
  yourDecisions:
    - "Confirm credential type and storage location"
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

## 1. Identify the credential needed

- **You provide:** the name of the service and the credential type it requires — API key, personal access token, or SSO cookie.
- **Agent does:** walks you through identifying what credential type the service requires and which resolution path to use.
- **You decide:** confirm credential type and storage location at the G-setup gate — choose where the credential will live: environment variable (CI-friendly), OS keyring (secure, persistent), or dotfile (portable); for most developer workstations, the OS keyring is the right choice.
- **Output:** an agreed credential type and resolution path.

---

## 2. Set up and verify

- **Agent does:** runs `credential-setup`, prompts for the token value (which is never logged), stores it via the configured resolution chain, and then runs a test invocation to confirm the credential resolves correctly.
- **You do:** provide the token value when prompted; verify the test invocation succeeded; if it fails, work through the resolution chain with the agent — is the environment variable exported? Is the keyring unlocked? Is the dotfile in the expected location and readable?
- **Output:** a stored credential verified by a successful test invocation.

---

## 3. Credential available to all sessions

- **Agent does:** confirms the credential is stored and will resolve automatically in every subsequent session that needs it — the token value never passes through the model again.
- **You do:** confirm that the first real invocation of the credentialed skill works end-to-end; if a skill returns an auth error after a successful setup, the first check is always whether the token has the right scope for this operation.
- **Output:** a fully operational credential available to all subsequent sessions.
