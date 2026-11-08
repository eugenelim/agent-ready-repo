# RFC merge-accepts wording versus Open circulation

- **Status:** Open
- **Kind:** design
- **Detail:** docs/rfc/0114-lighter-rfcs.md

## Summary

RFC-0114 says a maintainer's merge accepts an RFC: its flowchart (line 68) and D2 (line 73), the template comment (`docs/rfc/template.md.tmpl` line 23 and the new-rfc skill's `assets/rfc.md` line 23), and the seeded governance text (`docs/GOVERNANCE.md` line 11 and the skill's `assets/governance-default.md` line 14). Its tooling still checks in-flight RFCs on main (`docs/rfc/rfc.py`), and the new-rfc skill moves an RFC from Draft to Open to circulate it (`SKILL.md` steps 6, 7 and 9). The owner wants an RFC to be able to stay Open for circulation, merged or not, without the merge accepting it. That changes an Accepted decision, so it needs an amendment to RFC-0114 D2 and its flowchart, plus the matching template and governance wording; it is not a bug fix in the skill. Found while finalising RFC-0113 on 2026-11-07.
