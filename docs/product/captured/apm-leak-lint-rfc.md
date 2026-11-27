# Apm leak lint rfc

- **Status:** Closed
- **Kind:** defect
- **Detail:** https://github.com/eugenelim/agent-ready-repo/blob/7bdd03da0a93a35883ef1d32a121ec361b99211d/docs/specs/house-voice-writing-craft/notes/apm-leak-lint-rfc.md

## Summary

Retire the obsolete APM leak-lint RFC proposal after the concrete sweep shipped and catalogue verification replaced the deleted standalone linter

The proposal was retired on 2026-09-08. The concrete adopter-reference sweep shipped, and catalogue lint/verify replaced the deliberately deleted standalone linter (commit `96232e6`). Legitimate repository workflow and governance references remain, so a blanket `.apm` reference ban has no safe invariant. Do not reopen this RFC proposal or restore the standalone linter; any later restriction needs separately grounded scope and authority.
