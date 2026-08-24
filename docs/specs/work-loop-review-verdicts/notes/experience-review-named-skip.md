# Experience review named skip

- **Code:** `experience-reviewer-unavailable`
- **Category:** warranted non-mandatory reviewer unavailable
- **Reason:** the changelog-derived `/now/` highlight changes reader-visible content, but no subagent matching `experience-reviewer` is exposed in this session.
- **Residual eligible:** true
- **Evidence:** `tools/build-site.py` regenerated the `/now/` projection and `tools/test_build_site_routing.py` passed 77 tests with one expected skip; no rendered browser runtime is exposed.
