"""Tests for lib.config._resolve_data_dir — plugin data dir resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

import lib.config as config_mod


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
    monkeypatch.delenv("HUMAN_VOICE_DATA_DIR", raising=False)
    # Reset the lazy cache so each test re-resolves from env.
    monkeypatch.setattr(config_mod, "_CONFIG_DIR_CACHED", None, raising=False)


def test_falls_back_to_legacy_when_env_unset() -> None:
    assert config_mod._resolve_data_dir() == config_mod._LEGACY_DIR


def test_honors_claude_plugin_data_for_own_plugin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ours = tmp_path / "plugins" / "data" / "human-voice"
    ours.mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(ours))
    assert config_mod._resolve_data_dir() == ours


def test_ignores_leaked_claude_plugin_data_from_other_plugin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    foreign = tmp_path / "plugins" / "data" / "codex-openai-codex"
    foreign.mkdir(parents=True)
    (foreign / "profiles").mkdir()  # similar layout, no voice marker
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(foreign))
    assert config_mod._resolve_data_dir() == config_mod._LEGACY_DIR


def test_accepts_foreign_named_dir_with_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stamped = tmp_path / "some-runtime" / "storage"
    stamped.mkdir(parents=True)
    (stamped / config_mod._DATA_DIR_MARKER).write_text("ok\n", encoding="utf-8")
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(stamped))
    assert config_mod._resolve_data_dir() == stamped


def test_accepts_dir_with_voice_prompt_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dir_ = tmp_path / "cowork-data"
    dir_.mkdir()
    (dir_ / "voice-prompt.txt").write_text("x\n", encoding="utf-8")
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(dir_))
    assert config_mod._resolve_data_dir() == dir_


def test_human_voice_data_dir_override_wins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    override = tmp_path / "override"
    foreign = tmp_path / "plugins" / "data" / "other-plugin"
    foreign.mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(foreign))
    monkeypatch.setenv("HUMAN_VOICE_DATA_DIR", str(override))
    assert config_mod._resolve_data_dir() == override


def test_override_expanduser(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HUMAN_VOICE_DATA_DIR", "~/voice-dir-test")
    assert config_mod._resolve_data_dir() == Path.home() / "voice-dir-test"


def test_stamp_is_idempotent_and_recognised(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dir_ = tmp_path / "data"
    dir_.mkdir()
    # Not recognised initially (basename doesn't match).
    assert not config_mod._belongs_to_this_plugin(dir_)
    config_mod._stamp_data_dir(dir_)
    config_mod._stamp_data_dir(dir_)  # idempotent
    assert config_mod._belongs_to_this_plugin(dir_)


def test_belongs_basename_variants(tmp_path: Path) -> None:
    for name in ("human-voice", "zircote-human-voice", "plugins-data-human-voice"):
        p = tmp_path / name
        p.mkdir()
        assert config_mod._belongs_to_this_plugin(p), name


def test_belongs_rejects_generic_names(tmp_path: Path) -> None:
    for name in ("codex-openai-codex", "other-plugin", "voice", "audio"):
        p = tmp_path / name
        p.mkdir()
        assert not config_mod._belongs_to_this_plugin(p), name
