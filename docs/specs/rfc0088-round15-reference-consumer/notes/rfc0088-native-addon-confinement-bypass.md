# RFC-0088 native-addon confinement-bypass evidence

This packet preserves the deferred evidence identified by
`rfc0088-native-addon-confinement-bypass`. The pilot unconditionally denies
Node's `--allow-addons` flag, so its shipped configuration is not exposed to
this unverified path.

## Trigger and evidence request

Do not commission a native toolchain solely to exercise this packet. Re-open it
when either:

- a real supported configuration proposes granting `--allow-addons`; or
- an approver supplies an authorized C++/`node-gyp` evidence environment.

Before permitting the flag, compile a minimal native addon in the supplied
environment and test whether loading it can bypass the RFC-0088 filesystem
confinement boundary. Record the tested revision, Node and toolchain versions,
the exact granted configuration, redacted commands, observed access result,
and exit statuses. A bypass is a security defect and blocks granting the flag;
a non-bypass result settles only the recorded configuration and toolchain.

