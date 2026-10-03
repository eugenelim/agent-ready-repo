# STUB: AC-0011 — the unique longest JFrog profile is selected and pinned
import json
import os
import shlex
from pathlib import Path

import pytest

from credbroker import JfrogCliHttpAccess, resolve_http_access


@pytest.mark.skipif(os.name == "nt", reason="stub fixture requires POSIX executable bits")
def test_jfrog_longest_profile_returns_pinned_binding(
    tmp_path: Path,
) -> None:
    jf = tmp_path / "jf"
    profiles = [
        {
            "serverId": "broad",
            "url": "https://platform.example.test/",
            "artifactoryUrl": "https://platform.example.test/artifactory/",
            "isDefault": True,
        },
        {
            "serverId": "catalogues",
            "url": "https://platform.example.test/",
            "artifactoryUrl": "https://platform.example.test/artifactory/catalogues/",
            "isDefault": False,
        },
    ]
    # `/bin/sh` is an absolute interpreter, so the fixture runs under the
    # allowlisted child environment without needing `python3` on `PATH`.
    jf.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "config" ] && [ "$2" = "show" ] && [ "$3" = "--format=json" ]; then\n'
        f"  printf '%s' {shlex.quote(json.dumps(profiles))}\n"
        'elif [ "$1" = "--version" ]; then\n'
        '  echo "jf version 2.105.0"\n'
        "else\n"
        "  exit 2\n"
        "fi\n",
        encoding="utf-8",
    )
    jf.chmod(0o755)

    result = resolve_http_access(
        "https://platform.example.test/artifactory/catalogues/team/catalogue.toml",
        env={"PATH": str(tmp_path)},
    )

    assert isinstance(result, JfrogCliHttpAccess)
    assert result.server_id == "catalogues"
    assert result.artifactory_url.endswith("/artifactory/catalogues/")
