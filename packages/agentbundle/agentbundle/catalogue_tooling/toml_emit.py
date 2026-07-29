"""Minimal safe TOML emitter for generated catalogue configuration.

Produces deterministic, human-readable TOML from a small set of primitives.
No third-party dependencies — stdlib only.
"""

from __future__ import annotations


def emit_str(value: str) -> str:
    """Return *value* as a TOML basic-string literal (double-quoted, minimal escaping)."""
    escaped = (
        value
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    # Escape remaining C0/DEL control characters (TOML 1.0 §2.1 forbids them unescaped).
    result = []
    for ch in escaped:
        cp = ord(ch)
        if (0x00 <= cp <= 0x08) or cp in (0x0B, 0x0C) or (0x0E <= cp <= 0x1F) or cp == 0x7F:
            result.append(f"\\u{cp:04X}")
        else:
            result.append(ch)
    return '"' + "".join(result) + '"'


def emit_bool(value: bool) -> str:
    return "true" if value else "false"


def emit_int(value: int) -> str:
    return str(value)


def emit_array_of_strings(values: list[str]) -> str:
    """Emit a TOML inline array of strings."""
    if not values:
        return "[]"
    inner = ", ".join(emit_str(v) for v in values)
    return f"[{inner}]"


def emit_multiline_array_of_strings(values: list[str]) -> str:
    """Emit a TOML array of strings in multi-line style."""
    if not values:
        return "[]"
    lines = ["["]
    for v in values:
        lines.append(f"  {emit_str(v)},")
    lines.append("]")
    return "\n".join(lines)


def emit_section_header(header: str) -> str:
    return f"[{header}]"


def emit_catalogue_toml(
    name: str,
    display_name: str,
    description: str,
    minimum_agentbundle_version: str,
    owner_name: str,
    preferred_adapter: str,
) -> str:
    """Generate a complete blank catalogue.toml as a deterministic TOML string.

    UTF-8, LF newlines, final newline.  No credentials, no absolute paths,
    no placeholder remote URLs.
    """
    lines: list[str] = []

    def ln(s: str = "") -> None:
        lines.append(s)

    ln("schema = 1")
    ln()
    ln("[catalogue]")
    ln(f"name                        = {emit_str(name)}")
    ln(f'display-name                = {emit_str(display_name)}')
    ln(f'description                 = {emit_str(description)}')
    ln(f'minimum-agentbundle-version = {emit_str(minimum_agentbundle_version)}')
    ln()
    ln("[catalogue.owner]")
    ln(f"name = {emit_str(owner_name)}")
    ln()
    ln("[catalogue.paths]")
    ln('packs        = "packs"')
    ln('profiles     = "profiles"')
    ln('marketplace  = ".claude-plugin/marketplace.json"')
    ln('build-output = "dist"')
    ln()
    ln("[catalogue.build]")
    ln('recipes                 = ["default"]')
    ln("self-host               = false")
    ln('claude-plugin-branch    = "main"')
    ln(f'marketplace-description = {emit_str(description)}')
    ln()
    ln("[catalogue.package]")
    ln("include  = []")
    ln('required = [')
    ln('  "packs",')
    ln('  ".claude-plugin/marketplace.json",')
    ln("]")
    ln()
    ln("[distribution.agentbundle]")
    ln(f"preferred-adapter = {emit_str(preferred_adapter)}")
    ln()
    ln("[distribution.agentbundle.artifactory]")
    ln("enabled = false")
    ln()

    return "\n".join(lines)
