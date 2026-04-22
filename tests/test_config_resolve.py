"""Tests for lib.config._resolve_data_dir — canonical data dir contract.

The plugin always uses ``~/.human-voice``. Environment variables like
``CLAUDE_PLUGIN_DATA`` or ``HUMAN_VOICE_DATA_DIR`` do NOT redirect it —
this is intentional so that the data lives in exactly one place across
multiple Claude accounts and plugin-runtime layouts.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import lib.config as config_mod


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
    monkeypatch.delenv("HUMAN_VOICE_DATA_DIR", raising=False)
    monkeypatch.setattr(config_mod, "_CONFIG_DIR_CACHED", None, raising=False)


def test_resolves_to_home_human_voice() -> None:
    assert config_mod._resolve_data_dir() == Path.home() / ".human-voice"


def test_claude_plugin_data_env_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", "/tmp/some-other-plugin")
    assert config_mod._resolve_data_dir() == Path.home() / ".human-voice"


def test_human_voice_data_dir_env_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HUMAN_VOICE_DATA_DIR", "/tmp/override-attempt")
    assert config_mod._resolve_data_dir() == Path.home() / ".human-voice"


def test_module_level_data_dir_constant() -> None:
    assert config_mod.DATA_DIR == Path.home() / ".human-voice"


def test_migrate_legacy_data_is_noop() -> None:
    assert config_mod.migrate_legacy_data() is False
