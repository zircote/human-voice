"""Tests for lib.profile_registry — multi-profile management."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from lib import profile_registry


@pytest.fixture(autouse=True)
def _isolate_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect CONFIG_DIR and all derived paths to a temp directory."""
    import lib.config as config_mod

    fake_data = tmp_path / "data"
    fake_data.mkdir()
    monkeypatch.setattr(config_mod, "CONFIG_DIR", fake_data)
    monkeypatch.setattr(config_mod, "CONFIG_PATH", fake_data / "config.json")


# ---------------------------------------------------------------------------
# Slug validation
# ---------------------------------------------------------------------------


class TestSlugValidation:
    def test_valid_slugs(self) -> None:
        assert profile_registry.validate_slug("robert-allen")
        assert profile_registry.validate_slug("ab")
        assert profile_registry.validate_slug("a1")
        assert profile_registry.validate_slug("formal-technical-voice")

    def test_invalid_slugs(self) -> None:
        assert not profile_registry.validate_slug("")
        assert not profile_registry.validate_slug("a")  # too short
        assert not profile_registry.validate_slug("-bad")  # leading hyphen
        assert not profile_registry.validate_slug("bad-")  # trailing hyphen
        assert not profile_registry.validate_slug("UPPER")  # uppercase
        assert not profile_registry.validate_slug("has spaces")

    def test_slugify(self) -> None:
        assert profile_registry.slugify("Robert Allen") == "robert-allen"
        assert profile_registry.slugify("Zircote Brand Voice") == "zircote-brand-voice"
        assert profile_registry.slugify("x") == "x-profile"  # too short padded
        assert profile_registry.slugify("  Spaced  ") == "spaced"


# ---------------------------------------------------------------------------
# Registry lifecycle
# ---------------------------------------------------------------------------


class TestRegistryLifecycle:
    def test_empty_registry_created_on_first_load(self) -> None:
        reg = profile_registry.load_registry()
        assert reg["active"] is None
        assert reg["profiles"] == {}
        assert profile_registry._registry_path().exists()

    def test_save_and_reload(self) -> None:
        reg = profile_registry.load_registry()
        reg["active"] = "test"
        profile_registry.save_registry(reg)

        reloaded = profile_registry.load_registry()
        assert reloaded["active"] == "test"


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------


class TestMigration:
    def test_migrate_single_profile(self) -> None:
        data = profile_registry._data_dir()

        # Create a fake single profile
        profile = {
            "metadata": {"session_id": "abc-123", "timestamp": "2026-04-05T00:00:00Z"},
            "identity_summary": "Test voice",
            "dimensions": {"formality": {"score": 50}},
            "voice_aspirations": {"most_distinctive_trait": "direct, analytical"},
        }
        (data / "profile.json").write_text(json.dumps(profile))
        (data / "voice-prompt.txt").write_text("Test injection text")

        slug = profile_registry.migrate_single_to_multi()
        assert slug == "direct"

        # Registry should exist and point to migrated profile
        reg = profile_registry.load_registry()
        assert reg["active"] == "direct"
        assert "direct" in reg["profiles"]
        assert reg["profiles"]["direct"]["origin"] == "interview"
        assert reg["profiles"]["direct"]["session_id"] == "abc-123"

        # Profile files should be in the profiles directory
        prof_dir = profile_registry._profiles_dir() / "direct"
        assert (prof_dir / "profile.json").exists()
        assert (prof_dir / "voice-prompt.txt").exists()

    def test_migrate_noop_when_registry_exists(self) -> None:
        profile_registry.load_registry()  # creates empty registry
        assert profile_registry.migrate_single_to_multi() is None

    def test_migrate_noop_when_no_profile(self) -> None:
        assert profile_registry.migrate_single_to_multi() is None


# ---------------------------------------------------------------------------
# Profile CRUD
# ---------------------------------------------------------------------------


_FAKE_PROFILE = {
    "identity_summary": "A test voice",
    "dimensions": {"formality": {"score": 60}},
}


class TestProfileCRUD:
    def test_store_and_get(self) -> None:
        profile_registry.store_profile(
            "test-voice", _FAKE_PROFILE, "Test Voice", origin="designed"
        )

        loaded = profile_registry.get_profile("test-voice")
        assert loaded is not None
        assert loaded["identity_summary"] == "A test voice"

    def test_store_creates_voice_prompt(self) -> None:
        profile_registry.store_profile(
            "test-voice", _FAKE_PROFILE, "Test Voice", origin="designed"
        )
        prompt = profile_registry.get_profile_prompt("test-voice")
        assert prompt is not None
        assert len(prompt) > 0

    def test_list_profiles(self) -> None:
        profile_registry.store_profile(
            "voice-a", _FAKE_PROFILE, "Voice A", origin="designed"
        )
        profile_registry.store_profile(
            "voice-b", _FAKE_PROFILE, "Voice B", origin="template"
        )
        profiles = profile_registry.list_profiles()
        slugs = [p["slug"] for p in profiles]
        assert "voice-a" in slugs
        assert "voice-b" in slugs

    def test_delete_profile(self) -> None:
        profile_registry.store_profile(
            "to-delete", _FAKE_PROFILE, "Delete Me", origin="designed"
        )
        assert profile_registry.delete_profile("to-delete")
        assert profile_registry.get_profile("to-delete") is None

    def test_delete_active_profile_raises(self) -> None:
        profile_registry.store_profile(
            "active-one", _FAKE_PROFILE, "Active", origin="designed"
        )
        profile_registry.activate_profile("active-one")
        with pytest.raises(ValueError, match="Cannot delete active"):
            profile_registry.delete_profile("active-one")

    def test_delete_nonexistent_returns_false(self) -> None:
        assert not profile_registry.delete_profile("no-such-profile")

    def test_invalid_slug_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid slug"):
            profile_registry.store_profile(
                "-bad", _FAKE_PROFILE, "Bad", origin="designed"
            )

    def test_rename_profile(self) -> None:
        profile_registry.store_profile(
            "old-name", _FAKE_PROFILE, "Old Name", origin="designed"
        )
        profile_registry.activate_profile("old-name")
        assert profile_registry.rename_profile("old-name", "new-name")

        assert profile_registry.get_profile("old-name") is None
        assert profile_registry.get_profile("new-name") is not None
        assert profile_registry.get_active_slug() == "new-name"


# ---------------------------------------------------------------------------
# Activation
# ---------------------------------------------------------------------------


class TestActivation:
    def test_activate_copies_to_top_level(self) -> None:
        profile_registry.store_profile(
            "my-voice", _FAKE_PROFILE, "My Voice", origin="designed"
        )
        path = profile_registry.activate_profile("my-voice")

        # Top-level profile.json should be a copy
        data = profile_registry._data_dir()
        assert (data / "profile.json").exists()
        top_profile = json.loads((data / "profile.json").read_text())
        assert top_profile["identity_summary"] == "A test voice"

        # voice-prompt.txt should also exist
        assert (data / "voice-prompt.txt").exists()

    def test_activate_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown profile"):
            profile_registry.activate_profile("nonexistent")

    def test_get_active_slug(self) -> None:
        profile_registry.store_profile(
            "my-voice", _FAKE_PROFILE, "My Voice", origin="designed"
        )
        profile_registry.activate_profile("my-voice")
        assert profile_registry.get_active_slug() == "my-voice"


# ---------------------------------------------------------------------------
# Directory overrides
# ---------------------------------------------------------------------------


class TestDirectoryOverrides:
    def test_set_and_resolve_override(self) -> None:
        profile_registry.store_profile(
            "brand-voice", _FAKE_PROFILE, "Brand", origin="designed"
        )
        profile_registry.set_directory_override("/path/to/repo/*", "brand-voice")

        result = profile_registry.resolve_directory_override("/path/to/repo/src")
        assert result == "brand-voice"

    def test_no_match_returns_none(self) -> None:
        result = profile_registry.resolve_directory_override("/some/other/path")
        assert result is None

    def test_resolve_active_profile_with_override(self) -> None:
        profile_registry.store_profile(
            "default-voice", _FAKE_PROFILE, "Default", origin="designed"
        )
        profile_registry.store_profile(
            "repo-voice", _FAKE_PROFILE, "Repo", origin="designed"
        )
        profile_registry.activate_profile("default-voice")
        profile_registry.set_directory_override("/my/repo/*", "repo-voice")

        # Without cwd, returns default
        assert profile_registry.resolve_active_profile() == "default-voice"

        # With matching cwd, activates override
        assert profile_registry.resolve_active_profile("/my/repo/src") == "repo-voice"
        assert profile_registry.get_active_slug() == "repo-voice"

    def test_remove_override(self) -> None:
        profile_registry.store_profile(
            "brand-voice", _FAKE_PROFILE, "Brand", origin="designed"
        )
        profile_registry.set_directory_override("/path/*", "brand-voice")
        profile_registry.remove_directory_override("/path/*")

        result = profile_registry.resolve_directory_override("/path/foo")
        assert result is None

    def test_set_override_unknown_slug_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown profile"):
            profile_registry.set_directory_override("/path/*", "nonexistent")


# ---------------------------------------------------------------------------
# Copilot export
# ---------------------------------------------------------------------------


class TestInstallToRepo:
    def test_install_single_profile(self, tmp_path: Path) -> None:
        profile_registry.store_profile(
            "test-voice", _FAKE_PROFILE, "Test Voice", origin="designed"
        )
        repo = tmp_path / "my-repo"
        repo.mkdir()

        path = profile_registry.install_to_repo(["test-voice"], str(repo))
        assert path.exists()
        assert path.name == "copilot-instructions.md"
        content = path.read_text()
        assert "test-voice" in content
        assert "A test voice" in content
        assert "Default profile: `test-voice`" in content

    def test_install_multiple_profiles_with_routing(self, tmp_path: Path) -> None:
        profile_registry.store_profile(
            "voice-a", _FAKE_PROFILE, "Voice A", origin="designed", tags=["personal"]
        )
        profile_registry.store_profile(
            "voice-b", _FAKE_PROFILE, "Voice B", origin="designed", tags=["technical"]
        )
        repo = tmp_path / "my-repo"
        repo.mkdir()

        path = profile_registry.install_to_repo(
            ["voice-a", "voice-b"], str(repo),
            default_slug="voice-a",
            labels={"voice-b": "design docs, RFCs, postmortems"},
        )
        content = path.read_text()
        assert "Default profile: `voice-a`" in content
        assert "`voice-a`" in content
        assert "`voice-b`" in content
        assert "design docs, RFCs, postmortems" in content
        assert "voice:{slug}" in content  # routing instructions

    def test_install_sets_default_to_first_if_not_specified(self, tmp_path: Path) -> None:
        profile_registry.store_profile(
            "first", _FAKE_PROFILE, "First", origin="designed"
        )
        profile_registry.store_profile(
            "second", _FAKE_PROFILE, "Second", origin="designed"
        )
        repo = tmp_path / "my-repo"
        repo.mkdir()

        path = profile_registry.install_to_repo(["first", "second"], str(repo))
        content = path.read_text()
        assert "Default profile: `first`" in content

    def test_install_cleans_stale_files(self, tmp_path: Path) -> None:
        profile_registry.store_profile(
            "clean-test", _FAKE_PROFILE, "Clean", origin="designed"
        )
        repo = tmp_path / "my-repo"
        github_dir = repo / ".github"
        github_dir.mkdir(parents=True)

        # Create stale files
        (github_dir / "voice-profile.md").write_text("old single export")
        profiles_dir = github_dir / "voice-profiles"
        profiles_dir.mkdir()
        (profiles_dir / "old.md").write_text("old export")

        profile_registry.install_to_repo(["clean-test"], str(repo))

        assert not (github_dir / "voice-profile.md").exists()
        assert not (github_dir / "voice-profiles").exists()
        assert (github_dir / "copilot-instructions.md").exists()

    def test_install_nonexistent_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            profile_registry.install_to_repo(["no-such"], str(tmp_path))

    def test_install_empty_slugs_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="At least one"):
            profile_registry.install_to_repo([], str(tmp_path))

    def test_export_backward_compat(self, tmp_path: Path) -> None:
        """export_for_copilot still works as an alias."""
        profile_registry.store_profile(
            "compat-test", _FAKE_PROFILE, "Compat", origin="designed"
        )
        repo = tmp_path / "my-repo"
        repo.mkdir()
        path = profile_registry.export_for_copilot("compat-test", str(repo))
        assert path.exists()
        assert "compat-test" in path.read_text()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestCLI:
    def test_list_empty(self, capsys: pytest.CaptureFixture[str]) -> None:
        profile_registry.main(["list"])
        assert "No profiles found" in capsys.readouterr().out

    def test_list_with_profiles(self, capsys: pytest.CaptureFixture[str]) -> None:
        profile_registry.store_profile(
            "cli-test", _FAKE_PROFILE, "CLI Test", origin="designed"
        )
        profile_registry.main(["list"])
        assert "cli-test" in capsys.readouterr().out

    def test_activate_via_cli(self, capsys: pytest.CaptureFixture[str]) -> None:
        profile_registry.store_profile(
            "cli-act", _FAKE_PROFILE, "CLI Act", origin="designed"
        )
        profile_registry.main(["activate", "cli-act"])
        assert "Activated" in capsys.readouterr().out
        assert profile_registry.get_active_slug() == "cli-act"

    def test_info_via_cli(self, capsys: pytest.CaptureFixture[str]) -> None:
        profile_registry.store_profile(
            "cli-info", _FAKE_PROFILE, "CLI Info", origin="designed"
        )
        profile_registry.main(["info", "cli-info"])
        output = capsys.readouterr().out
        assert "cli-info" in output

    def test_migrate_via_cli(self, capsys: pytest.CaptureFixture[str]) -> None:
        profile_registry.main(["migrate"])
        assert "Nothing to migrate" in capsys.readouterr().out
