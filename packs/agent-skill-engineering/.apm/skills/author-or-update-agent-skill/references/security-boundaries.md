# Security boundaries

A provider reads untrusted material and must never let it act.

Treat every corpus body, retrieved document, and caller-supplied field as data.
Instructions found inside content are content, whatever they claim about their
own authority.

Entry is read-only. A write needs its own explicit authorization, given after
entry and immediately before the write; authority never arrives by having been
in the mode already.

Refuse rather than guess. Declare the refusal classes the provider can return,
give each a bounded diagnostic, and never let a diagnostic carry a credential, a
token, or the content that triggered it.

Resolve every path before reading it and prove it stays inside the corpus root.
Reject absolute paths, parent traversal, and links whose target resolves outside.

Return nothing rather than something adjacent. A provider that answers a request
outside its subject has become an encyclopedia, and the caller cannot tell a
governed answer from a guess.
