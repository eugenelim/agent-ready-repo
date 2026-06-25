"""Hook-wiring ``.toml`` → ``.json`` serialiser for the copilot
``hook-wiring`` projection.

GitHub Copilot (app + CLI, verified 1.0.59) reads **every** ``*.json`` file
in its hooks dir (``.github/hooks/`` repo, ``~/.copilot/hooks/`` user). So,
unlike codex's single mergeable ``hooks.json``, each source hook-wiring
``.toml`` serialises to its own self-contained file:

    {"version": 1,
     "hooks": {"<copilotEvent>": [{"type": "command",
                                   "bash": "<cmd>",
                                   "powershell": "<cmd>"}]}}

The one-source-file → one-output-file shape mirrors ``codex-agent-toml``; the
per-file (vs. merged) distinction is the new part, and the reason this is a
separate mode rather than a reuse of ``merge-json``.

Event-name map (frozen; all six verified to fire — RFC-0024 § Acceptance
Runs 2–4, CLI + app 1.0.59). A source event with no entry **fails the build**
(fail-closed; never emit an unrecognised event key).

Shell-agnostic-source precondition: the source command is carried into
**both** the ``bash`` and ``powershell`` handler keys. Our shipped wiring is
shell-agnostic (``python tools/...``). A wiring whose command is bash-only
would emit a broken ``powershell`` handler; per-shell source commands are a
follow-on, out of scope here (no shipped wiring needs them).

Hook-body path rewrite: copilot retargets ``hook-body`` from ``tools/hooks/``
to ``.github/hooks/`` (contract v0.10). A wiring command that references the
body by its legacy path (``python tools/hooks/<name>.py``) is rewritten to the
new location so the emitted JSON references the script where it actually lands
(spec AC9-repo: "the scripts land alongside the ``<name>.json`` wiring that
references them"). Without this, an adopter's ``sessionStart`` hook fires but
fails to find its script. **Repo-scope only:** the rewrite targets the
``.github/hooks/`` repo-relpath; resolving the command at *user* scope
(``~/.copilot/hooks/``, where the session CWD is arbitrary) is an unsolved
follow-on — no shipped pack ships a user-scope copilot hook (core is
repo-only), so it is not exercised here.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path


# copilot's hook-body retarget (contract v0.10): legacy `tools/hooks/` →
# `.github/hooks/`. A carried command that references a hook body by its legacy
# path is rewritten so it points where `direct-file` actually lands the script.
_LEGACY_HOOK_BODY_PREFIX = "tools/hooks/"
_COPILOT_HOOK_BODY_PREFIX = ".github/hooks/"


def _rewrite_hook_body_path(command: str) -> str:
    return command.replace(_LEGACY_HOOK_BODY_PREFIX, _COPILOT_HOOK_BODY_PREFIX)


# Our hook event vocabulary → Copilot's. Frozen; version-sensitive (Copilot is
# preview). `errorOccurred` exists upstream but we ship no wiring for it.
_EVENT_MAP: dict[str, str] = {
    "SessionStart": "sessionStart",
    "SessionEnd": "sessionEnd",
    "UserPromptSubmit": "userPromptSubmitted",
    "PreToolUse": "preToolUse",
    "PostToolUse": "postToolUse",
    "Stop": "agentStop",
}


def _to_copilot_event(source_event: str) -> str:
    try:
        return _EVENT_MAP[source_event]
    except KeyError:
        raise ValueError(
            f"copilot-hooks-json: hook event {source_event!r} has no entry in "
            f"the frozen Copilot event-name map "
            f"({', '.join(sorted(_EVENT_MAP))}); refusing to emit an "
            f"unrecognised event key"
        ) from None


def project_copilot_hooks_json(
    source_dir: Path,
    output_root: Path,
    rule: dict,
) -> None:
    """Project each ``<source_dir>/<name>.toml`` → ``<output>/<target>/<name>.json``.

    Source shape is the Claude-Code nested-event form::

        [[hooks.<Event>]]
        hooks = [ { type = "command", command = "<cmd>" } ]

    Each ``<Event>`` is translated through the frozen event map (unmapped →
    build error), and each inner handler becomes
    ``{"type": ..., "bash": <cmd>, "powershell": <cmd>}``.
    """
    target_dir = output_root / rule["target-path"].rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source_dir.iterdir()):
        if not (entry.is_file() and entry.suffix == ".toml"):
            continue
        data = tomllib.loads(entry.read_text(encoding="utf-8"))
        events = data.get("hooks", {})
        copilot_hooks: dict[str, list[dict]] = {}
        for source_event in sorted(events):
            copilot_event = _to_copilot_event(source_event)
            handlers: list[dict] = copilot_hooks.setdefault(copilot_event, [])
            for outer in events[source_event]:
                for handler in outer.get("hooks", []):
                    # Fail-closed with an actionable message (naming the file)
                    # on a malformed handler — a bare `handler["command"]` would
                    # raise an uncaught KeyError (not in the install handler's
                    # `except (FileNotFoundError, ValueError)`), crashing with an
                    # unlocated traceback instead of a clean refusal.
                    handler_type = handler.get("type")
                    command = handler.get("command")
                    if handler_type != "command" or not isinstance(command, str):
                        raise ValueError(
                            f"copilot-hooks-json: {entry.name}: hook handler for "
                            f"event {source_event!r} must declare "
                            f'`type = "command"` and a string `command`; got '
                            f"type={handler_type!r}, command={command!r}"
                        )
                    command = _rewrite_hook_body_path(command)
                    handlers.append(
                        {
                            "type": handler_type,
                            "bash": command,
                            "powershell": command,
                        }
                    )
        # A wiring file with no events emits `{"version":1,"hooks":{}}` — one
        # output file per source file is the contract (mirrors codex-agent-toml),
        # and Copilot reads an empty-hooks file as a harmless no-op.
        document = {"version": 1, "hooks": copilot_hooks}
        destination = target_dir / (entry.stem + ".json")
        destination.write_text(
            json.dumps(document, indent=2, sort_keys=False) + "\n",
            encoding="utf-8", newline="\n",
        )
