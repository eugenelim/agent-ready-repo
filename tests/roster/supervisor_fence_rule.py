"""The installed-skill import fence's rule, shared by the fenced run and its controls.

A path is allowed when it sits, by whole path components, inside the skill's scripts
directory, the platform's extension-module directory, or the standard library directory
outside any site-packages.
"""
import os
import pathlib


def _real(path):
    return os.path.normcase(os.path.realpath(path))


def _inside(path, root):
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:
        return False


def make_allowed(stdlib, extension_dir, scripts):
    stdlib, extension_dir, scripts = _real(stdlib), _real(extension_dir), _real(scripts)

    def allowed(path):
        real = _real(path)
        if _inside(real, scripts) or _inside(real, extension_dir):
            return True
        if not _inside(real, stdlib):
            return False
        parts = pathlib.PurePath(os.path.relpath(real, stdlib)).parts
        return not {"site-packages", "dist-packages"} & set(parts)

    return allowed
