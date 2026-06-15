"""T1 (pack-profiles AC1, AC2): profile-manifest schema + reader.

Compressible invariant: valid manifests parse into a typed structure with id
derived from the filename stem and order preserved; invalid manifests (missing
``scope``, unknown field, non-kebab id, empty/non-list ``packs``, bad enum) are
rejected with a clear, profile-named error.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentbundle.commands.profile import (
    Profile,
    ProfileError,
    list_profiles,
    load_profile,
)


def _write(catalogue: Path, name: str, body: str) -> Path:
    pdir = catalogue / "profiles"
    pdir.mkdir(parents=True, exist_ok=True)
    path = pdir / name
    path.write_text(body, encoding="utf-8")
    return path


_VALID = """\
scope = "user"
description = "Solution architect's portable toolkit."

[[packs]]
pack = "architect"

[[packs]]
pack = "research"

[[packs]]
pack = "contracts"
"""


def test_valid_manifest_parses_with_id_from_stem_and_order_preserved(tmp_path):
    _write(tmp_path, "solution-architect.toml", _VALID)
    prof = load_profile(tmp_path, "solution-architect")
    assert isinstance(prof, Profile)
    assert prof.id == "solution-architect"
    assert prof.scope == "user"
    assert prof.description == "Solution architect's portable toolkit."
    # Authored deps-first order is preserved verbatim.
    assert prof.packs == ("architect", "research", "contracts")


def test_repo_scope_manifest_parses(tmp_path):
    _write(
        tmp_path,
        "full-ceremony.toml",
        'scope = "repo"\ndescription = "x"\n[[packs]]\npack = "core"\n',
    )
    prof = load_profile(tmp_path, "full-ceremony")
    assert prof.scope == "repo"
    assert prof.packs == ("core",)


def test_missing_scope_is_rejected(tmp_path):
    _write(tmp_path, "p.toml", 'description = "x"\n[[packs]]\npack = "core"\n')
    with pytest.raises(ProfileError) as exc:
        load_profile(tmp_path, "p")
    assert "scope" in str(exc.value)


def test_missing_description_is_rejected(tmp_path):
    _write(tmp_path, "p.toml", 'scope = "repo"\n[[packs]]\npack = "core"\n')
    with pytest.raises(ProfileError):
        load_profile(tmp_path, "p")


def test_unknown_top_level_field_is_rejected(tmp_path):
    _write(
        tmp_path,
        "p.toml",
        'scope = "repo"\ndescription = "x"\nadapter = "claude-code"\n'
        '[[packs]]\npack = "core"\n',
    )
    with pytest.raises(ProfileError):
        load_profile(tmp_path, "p")


def test_unknown_pack_entry_field_is_rejected(tmp_path):
    _write(
        tmp_path,
        "p.toml",
        'scope = "repo"\ndescription = "x"\n[[packs]]\npack = "core"\nversion = "^0.1"\n',
    )
    with pytest.raises(ProfileError):
        load_profile(tmp_path, "p")


def test_scope_not_in_enum_is_rejected(tmp_path):
    _write(
        tmp_path,
        "p.toml",
        'scope = "both"\ndescription = "x"\n[[packs]]\npack = "core"\n',
    )
    with pytest.raises(ProfileError):
        load_profile(tmp_path, "p")


def test_empty_packs_list_is_rejected(tmp_path):
    _write(tmp_path, "p.toml", 'scope = "repo"\ndescription = "x"\npacks = []\n')
    with pytest.raises(ProfileError):
        load_profile(tmp_path, "p")


def test_packs_entry_missing_pack_key_is_rejected(tmp_path):
    _write(
        tmp_path,
        "p.toml",
        'scope = "repo"\ndescription = "x"\n[[packs]]\nname = "core"\n',
    )
    with pytest.raises(ProfileError):
        load_profile(tmp_path, "p")


def test_non_kebab_id_is_rejected(tmp_path):
    _write(tmp_path, "Bad_Name.toml", _VALID)
    with pytest.raises(ProfileError) as exc:
        load_profile(tmp_path, "Bad_Name")
    assert "invalid id" in str(exc.value)


def test_missing_file_is_rejected(tmp_path):
    (tmp_path / "profiles").mkdir()
    with pytest.raises(ProfileError) as exc:
        load_profile(tmp_path, "nope")
    assert "not found" in str(exc.value)


def test_invalid_toml_is_rejected(tmp_path):
    _write(tmp_path, "p.toml", "scope = = =\n")
    with pytest.raises(ProfileError) as exc:
        load_profile(tmp_path, "p")
    assert "invalid TOML" in str(exc.value)


def test_list_profiles_returns_sorted_valid_profiles(tmp_path):
    _write(tmp_path, "solution-architect.toml", _VALID)
    _write(
        tmp_path,
        "full-ceremony.toml",
        'scope = "repo"\ndescription = "y"\n[[packs]]\npack = "core"\n',
    )
    profs = list_profiles(tmp_path)
    assert [p.id for p in profs] == ["full-ceremony", "solution-architect"]


def test_list_profiles_skips_malformed(tmp_path, capsys):
    _write(
        tmp_path,
        "good.toml",
        'scope = "repo"\ndescription = "y"\n[[packs]]\npack = "core"\n',
    )
    _write(tmp_path, "bad.toml", 'description = "no scope"\n[[packs]]\npack = "core"\n')
    profs = list_profiles(tmp_path)
    assert [p.id for p in profs] == ["good"]
    assert "skipping bad.toml" in capsys.readouterr().err


def test_list_profiles_empty_when_no_dir(tmp_path):
    assert list_profiles(tmp_path) == []
