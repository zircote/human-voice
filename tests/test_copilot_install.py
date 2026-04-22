"""Tests for lib.copilot_install — render + install into a target repo."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import lib.config as config_mod
import lib.profile_registry as reg
from lib import copilot_install


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the plugin data dir and reset the registry cache."""
    data = tmp_path / "human-voice-data"
    data.mkdir()
    monkeypatch.setattr(config_mod, "CONFIG_DIR", data)
    monkeypatch.setattr(config_mod, "CONFIG_PATH", data / "config.json")
    return data


def _sample_profile(slug: str) -> dict:
    return {
        "metadata": {
            "session_id": f"session-{slug}",
            "timestamp": "2026-04-22T00:00:00Z",
            "pipeline_version": "1.0",
            "notes": "raw session notes that should be redacted",
        },
        "dimensions": {
            "formality": {"score": 55.0, "band": "neutral"},
            "directness": {"score": 72.0, "band": "high"},
        },
        "calibration": {
            "formality": {"self": 60, "observed": 55, "delta": -5},
            "summary": "Minor calibration delta; mostly aligned.",
        },
        "distinctive_features": ["oxford commas", "no em dashes"],
        "voice_aspirations": {
            "most_distinctive_trait": "technical honesty",
        },
        "mechanics": {
            "contractions": True,
            "oxford_comma": True,
            "em_dash": False,
        },
        "identity_summary": f"A technical writer voice for {slug}.",
        "known_gaps": {"consistency": "insufficient data points"},
    }


def _install_profiles(_data: Path, *slugs: str) -> None:
    """Store sample profiles via the real registry code path."""
    for slug in slugs:
        reg.store_profile(
            slug,
            _sample_profile(slug),
            display_name=slug.replace("-", " ").title(),
        )
    reg.activate_profile(slugs[0])


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------


class TestRedact:
    def test_drops_metadata_and_known_gaps(self) -> None:
        redacted = copilot_install.redact_profile(_sample_profile("x"))
        assert "metadata" not in redacted
        assert "known_gaps" not in redacted

    def test_trims_calibration_to_summary(self) -> None:
        redacted = copilot_install.redact_profile(_sample_profile("x"))
        assert redacted["calibration"] == {
            "summary": "Minor calibration delta; mostly aligned."
        }

    def test_preserves_voice_signals(self) -> None:
        redacted = copilot_install.redact_profile(_sample_profile("x"))
        assert "dimensions" in redacted
        assert "mechanics" in redacted
        assert "distinctive_features" in redacted
        assert "voice_aspirations" in redacted
        assert "identity_summary" in redacted


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


class TestRouting:
    def test_parse_route_single(self) -> None:
        assert copilot_install.parse_route("docs/**=tech") == [("docs/**", "tech")]

    def test_parse_route_multi(self) -> None:
        out = copilot_install.parse_route("docs/**=a;**/*.md=b")
        assert out == [("docs/**", "a"), ("**/*.md", "b")]

    def test_parse_route_empty(self) -> None:
        assert copilot_install.parse_route("") == []
        assert copilot_install.parse_route(" ; ") == []

    def test_parse_route_rejects_invalid(self) -> None:
        with pytest.raises(ValueError):
            copilot_install.parse_route("bad-entry-no-equals")
        with pytest.raises(ValueError):
            copilot_install.parse_route("glob=")
        with pytest.raises(ValueError):
            copilot_install.parse_route("=slug")

    def test_options_rejects_route_to_uninstalled_slug(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="not in installed slugs"):
            copilot_install.InstallOptions(
                target=tmp_path,
                slugs=["a"],
                default_slug="a",
                routing=[("docs/**", "missing")],
            )


# ---------------------------------------------------------------------------
# Install — structural
# ---------------------------------------------------------------------------


class TestInstallSingleProfile:
    def test_writes_full_surface(self, isolated_data: Path, tmp_path: Path) -> None:
        _install_profiles(isolated_data, "fixture")
        target = tmp_path / "repo"
        target.mkdir()
        opts = copilot_install.InstallOptions(
            target=target, slugs=["fixture"], default_slug="fixture"
        )
        copilot_install.install(opts)

        expected = [
            ".github/copilot-instructions.md",
            "AGENTS.md",
            ".github/instructions/human-voice-fixture.instructions.md",
            ".github/prompts/voice-review.prompt.md",
            ".github/prompts/voice-fix.prompt.md",
            ".github/prompts/voice-draft.prompt.md",
            ".github/agents/human-voice-fixture.agent.md",
            ".github/human-voice/fixture/profile.json",
            ".github/human-voice/fixture/voice-prompt.txt",
            ".github/workflows/voice-review.yml",
        ]
        for rel in expected:
            assert (target / rel).is_file(), f"missing {rel}"

    def test_profile_json_is_redacted_by_default(
        self, isolated_data: Path, tmp_path: Path
    ) -> None:
        _install_profiles(isolated_data, "fixture")
        target = tmp_path / "repo"
        target.mkdir()
        copilot_install.install(
            copilot_install.InstallOptions(
                target=target, slugs=["fixture"], default_slug="fixture"
            )
        )
        data = json.loads(
            (target / ".github/human-voice/fixture/profile.json").read_text()
        )
        assert "metadata" not in data
        assert "known_gaps" not in data

    def test_no_redact_writes_full_profile(
        self, isolated_data: Path, tmp_path: Path
    ) -> None:
        _install_profiles(isolated_data, "fixture")
        target = tmp_path / "repo"
        target.mkdir()
        copilot_install.install(
            copilot_install.InstallOptions(
                target=target, slugs=["fixture"], default_slug="fixture", redact=False
            )
        )
        data = json.loads(
            (target / ".github/human-voice/fixture/profile.json").read_text()
        )
        assert "metadata" in data
        assert "known_gaps" in data

    def test_instructions_file_has_applyto_frontmatter(
        self, isolated_data: Path, tmp_path: Path
    ) -> None:
        _install_profiles(isolated_data, "fixture")
        target = tmp_path / "repo"
        target.mkdir()
        copilot_install.install(
            copilot_install.InstallOptions(
                target=target, slugs=["fixture"], default_slug="fixture"
            )
        )
        content = (
            target / ".github/instructions/human-voice-fixture.instructions.md"
        ).read_text()
        assert content.startswith("---\n")
        assert 'applyTo: "**/*.{md,mdx,txt}"' in content

    def test_workflow_yaml_is_parseable(
        self, isolated_data: Path, tmp_path: Path
    ) -> None:
        yaml = pytest.importorskip("yaml")
        _install_profiles(isolated_data, "fixture")
        target = tmp_path / "repo"
        target.mkdir()
        copilot_install.install(
            copilot_install.InstallOptions(
                target=target, slugs=["fixture"], default_slug="fixture"
            )
        )
        wf = yaml.safe_load(
            (target / ".github/workflows/voice-review.yml").read_text()
        )
        assert wf["name"] == "Human-voice review"
        assert "pull_request" in wf["on"]
        assert wf["on"]["pull_request"]["paths"] == [
            "docs/**",
            "README*",
            "CHANGELOG*",
            "CONTRIBUTING*",
            "**/*.{md,mdx}",
        ]

    def test_no_workflow_flag_skips_workflow(
        self, isolated_data: Path, tmp_path: Path
    ) -> None:
        _install_profiles(isolated_data, "fixture")
        target = tmp_path / "repo"
        target.mkdir()
        copilot_install.install(
            copilot_install.InstallOptions(
                target=target,
                slugs=["fixture"],
                default_slug="fixture",
                with_workflow=False,
            )
        )
        assert not (target / ".github/workflows/voice-review.yml").exists()


# ---------------------------------------------------------------------------
# Install — multi-profile
# ---------------------------------------------------------------------------


class TestInstallMultiProfile:
    def test_writes_one_instructions_file_per_profile(
        self, isolated_data: Path, tmp_path: Path
    ) -> None:
        _install_profiles(isolated_data, "alpha", "beta")
        target = tmp_path / "repo"
        target.mkdir()
        copilot_install.install(
            copilot_install.InstallOptions(
                target=target,
                slugs=["alpha", "beta"],
                default_slug="alpha",
                routing=copilot_install.parse_route("docs/**=beta"),
            )
        )
        inst_dir = target / ".github/instructions"
        files = sorted(p.name for p in inst_dir.iterdir())
        assert files == [
            "human-voice-alpha.instructions.md",
            "human-voice-beta.instructions.md",
        ]

    def test_routing_applies_glob_to_nondefault_profile(
        self, isolated_data: Path, tmp_path: Path
    ) -> None:
        _install_profiles(isolated_data, "alpha", "beta")
        target = tmp_path / "repo"
        target.mkdir()
        copilot_install.install(
            copilot_install.InstallOptions(
                target=target,
                slugs=["alpha", "beta"],
                default_slug="alpha",
                routing=copilot_install.parse_route("docs/**=beta"),
            )
        )
        beta = (
            target / ".github/instructions/human-voice-beta.instructions.md"
        ).read_text()
        alpha = (
            target / ".github/instructions/human-voice-alpha.instructions.md"
        ).read_text()
        assert 'applyTo: "docs/**"' in beta
        assert 'applyTo: "**/*.{md,mdx,txt}"' in alpha


# ---------------------------------------------------------------------------
# Overwrite policies + idempotency
# ---------------------------------------------------------------------------


class TestOverwritePolicy:
    def test_merge_is_idempotent(self, isolated_data: Path, tmp_path: Path) -> None:
        _install_profiles(isolated_data, "fixture")
        target = tmp_path / "repo"
        target.mkdir()
        opts = copilot_install.InstallOptions(
            target=target, slugs=["fixture"], default_slug="fixture"
        )
        copilot_install.install(opts)
        first = (target / ".github/copilot-instructions.md").read_text()
        copilot_install.install(opts)
        second = (target / ".github/copilot-instructions.md").read_text()
        assert first == second

    def test_merge_preserves_user_content(
        self, isolated_data: Path, tmp_path: Path
    ) -> None:
        _install_profiles(isolated_data, "fixture")
        target = tmp_path / "repo"
        (target / ".github").mkdir(parents=True)
        user_content = "# My repo instructions\n\nUser-written rules.\n"
        (target / ".github/copilot-instructions.md").write_text(user_content)
        copilot_install.install(
            copilot_install.InstallOptions(
                target=target, slugs=["fixture"], default_slug="fixture"
            )
        )
        after = (target / ".github/copilot-instructions.md").read_text()
        assert after.startswith("# My repo instructions")
        assert copilot_install.MARKER_START in after

    def test_error_policy_skips_existing(
        self, isolated_data: Path, tmp_path: Path
    ) -> None:
        _install_profiles(isolated_data, "fixture")
        target = tmp_path / "repo"
        (target / ".github").mkdir(parents=True)
        pre = "pre-existing content\n"
        (target / ".github/copilot-instructions.md").write_text(pre)
        result = copilot_install.install(
            copilot_install.InstallOptions(
                target=target,
                slugs=["fixture"],
                default_slug="fixture",
                overwrite=copilot_install.OVERWRITE_ERROR,
            )
        )
        after = (target / ".github/copilot-instructions.md").read_text()
        assert after == pre
        assert any(
            "already exists" in reason for _path, reason in result.skipped
        )

    def test_force_overwrites(self, isolated_data: Path, tmp_path: Path) -> None:
        _install_profiles(isolated_data, "fixture")
        target = tmp_path / "repo"
        (target / ".github").mkdir(parents=True)
        (target / ".github/copilot-instructions.md").write_text("old\n")
        copilot_install.install(
            copilot_install.InstallOptions(
                target=target,
                slugs=["fixture"],
                default_slug="fixture",
                overwrite=copilot_install.OVERWRITE_FORCE,
            )
        )
        after = (target / ".github/copilot-instructions.md").read_text()
        assert "Human-Voice Instructions for GitHub Copilot" in after


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------


class TestDryRun:
    def test_dry_run_writes_nothing(
        self, isolated_data: Path, tmp_path: Path
    ) -> None:
        _install_profiles(isolated_data, "fixture")
        target = tmp_path / "repo"
        target.mkdir()
        result = copilot_install.install(
            copilot_install.InstallOptions(
                target=target, slugs=["fixture"], default_slug="fixture", dry_run=True
            )
        )
        assert not (target / ".github").exists()
        assert len(result.would_write) >= 10
