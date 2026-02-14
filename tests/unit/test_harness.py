"""Tests for ate.harness — execution harness for treatments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from ate.harness import (
    PreflightError,
    build_treatment0_command,
    get_opening_prompt,
    get_patch_path,
    get_run_dir,
    preflight_check,
    render_session_guide,
    render_treatment0_prompt,
    run_treatment0,
    save_metadata,
    scaffold_interactive_run,
)
from ate.models import Bug, ExecutionMode, Treatment

# ---------------------------------------------------------------------------
# TestGetRunDir
# ---------------------------------------------------------------------------


class TestGetRunDir:
    def test_creates_directory(self, tmp_path: Path) -> None:
        run_dir = get_run_dir(0, 20945, base_dir=tmp_path)
        assert run_dir.exists()
        assert run_dir.is_dir()

    def test_correct_path_structure(self, tmp_path: Path) -> None:
        run_dir = get_run_dir(0, 20945, base_dir=tmp_path)
        assert run_dir == tmp_path / "treatment-0" / "bug-20945"

    def test_idempotent(self, tmp_path: Path) -> None:
        dir1 = get_run_dir(0, 20945, base_dir=tmp_path)
        dir2 = get_run_dir(0, 20945, base_dir=tmp_path)
        assert dir1 == dir2

    def test_string_treatment_id(self, tmp_path: Path) -> None:
        run_dir = get_run_dir("2a", 7847, base_dir=tmp_path)
        assert run_dir == tmp_path / "treatment-2a" / "bug-7847"


# ---------------------------------------------------------------------------
# TestGetPatchPath
# ---------------------------------------------------------------------------


class TestGetPatchPath:
    def test_correct_path(self, tmp_path: Path) -> None:
        path = get_patch_path(0, 20945, base_dir=tmp_path)
        assert path == tmp_path / "treatment-0" / "bug-20945.patch"

    def test_string_treatment_id(self, tmp_path: Path) -> None:
        path = get_patch_path("2a", 7847, base_dir=tmp_path)
        assert path == tmp_path / "treatment-2a" / "bug-7847.patch"

    def test_parent_directory_created(self, tmp_path: Path) -> None:
        path = get_patch_path(0, 20945, base_dir=tmp_path)
        assert path.parent.exists()


# ---------------------------------------------------------------------------
# TestSaveMetadata
# ---------------------------------------------------------------------------


class TestSaveMetadata:
    def test_saves_json(self, tmp_path: Path) -> None:
        metadata = {"treatment_id": 0, "bug_id": 20945, "mode": "programmatic"}
        path = save_metadata(metadata, tmp_path)
        assert path.exists()
        assert path.name == "metadata.json"
        loaded = json.loads(path.read_text())
        assert loaded["treatment_id"] == 0

    def test_overwrites_existing(self, tmp_path: Path) -> None:
        save_metadata({"version": 1}, tmp_path)
        save_metadata({"version": 2}, tmp_path)
        loaded = json.loads((tmp_path / "metadata.json").read_text())
        assert loaded["version"] == 2


# ---------------------------------------------------------------------------
# TestPreflightCheck
# ---------------------------------------------------------------------------


class TestPreflightCheck:
    def test_all_clear(self, tmp_path: Path, sample_bug: Bug) -> None:
        ruff_dir = tmp_path / "ruff"
        binary = ruff_dir / "target" / "debug" / "ruff"
        binary.parent.mkdir(parents=True)
        binary.write_text("fake")
        with patch("ate.harness.get_ruff_version", return_value="0.14.14"):
            issues = preflight_check(ruff_dir, bug_id=20945)
        assert issues == []

    def test_missing_binary(self, tmp_path: Path) -> None:
        ruff_dir = tmp_path / "ruff"
        ruff_dir.mkdir()
        issues = preflight_check(ruff_dir)
        assert any("binary" in i.lower() or "not found" in i.lower() for i in issues)

    def test_wrong_version(self, tmp_path: Path) -> None:
        ruff_dir = tmp_path / "ruff"
        binary = ruff_dir / "target" / "debug" / "ruff"
        binary.parent.mkdir(parents=True)
        binary.write_text("fake")
        with patch("ate.harness.get_ruff_version", return_value="0.15.0"):
            issues = preflight_check(ruff_dir)
        assert any("version" in i.lower() or "0.14.14" in i for i in issues)


# ---------------------------------------------------------------------------
# TestRenderTreatment0Prompt
# ---------------------------------------------------------------------------


class TestRenderTreatment0Prompt:
    def test_all_fields_substituted(self, sample_bug: Bug) -> None:
        patch_path = Path("data/patches/treatment-0/bug-20945.patch")
        prompt = render_treatment0_prompt(sample_bug, patch_path)
        assert "{" not in prompt or "{{" in prompt  # no unresolved placeholders
        assert "20945" in prompt
        assert "FAST001" in prompt
        assert str(patch_path) in prompt

    def test_contains_bug_details(self, sample_bug: Bug) -> None:
        patch_path = Path("data/patches/treatment-0/bug-20945.patch")
        prompt = render_treatment0_prompt(sample_bug, patch_path)
        assert sample_bug.title in prompt
        assert sample_bug.url in prompt
        assert sample_bug.reproduction in prompt

    def test_contains_ruff_reference(self, sample_bug: Bug) -> None:
        patch_path = Path("data/patches/treatment-0/bug-20945.patch")
        prompt = render_treatment0_prompt(sample_bug, patch_path)
        assert "data/ruff" in prompt or "ruff" in prompt.lower()


# ---------------------------------------------------------------------------
# TestBuildTreatment0Command
# ---------------------------------------------------------------------------


class TestBuildTreatment0Command:
    def test_default_flags(self) -> None:
        cmd = build_treatment0_command("Fix this bug", max_turns=50, model="haiku")
        assert cmd[0] == "claude"
        assert "-p" in cmd
        assert "--output-format" in cmd
        idx = cmd.index("--output-format")
        assert cmd[idx + 1] == "json"
        assert "--max-turns" in cmd
        idx = cmd.index("--max-turns")
        assert cmd[idx + 1] == "50"

    def test_custom_model(self) -> None:
        cmd = build_treatment0_command("Fix this", max_turns=30, model="opus")
        assert "--model" in cmd
        idx = cmd.index("--model")
        assert cmd[idx + 1] == "opus"

    def test_prompt_included(self) -> None:
        prompt = "Investigate bug #20945"
        cmd = build_treatment0_command(prompt, max_turns=50, model="haiku")
        assert prompt in cmd

    def test_allowed_tools(self) -> None:
        cmd = build_treatment0_command(
            "Fix this",
            max_turns=50,
            model="haiku",
            allowed_tools=["Read", "Grep", "Glob", "Bash", "Edit", "Write"],
        )
        assert "--allowedTools" in cmd


# ---------------------------------------------------------------------------
# TestRunTreatment0
# ---------------------------------------------------------------------------


class TestRunTreatment0:
    def test_dry_run(self, tmp_path: Path, sample_bug: Bug) -> None:
        ruff_dir = tmp_path / "ruff"
        binary = ruff_dir / "target" / "debug" / "ruff"
        binary.parent.mkdir(parents=True)
        binary.write_text("fake")
        with patch("ate.harness.get_ruff_version", return_value="0.14.14"):
            result = run_treatment0(
                sample_bug,
                ruff_dir=ruff_dir,
                max_turns=50,
                timeout=1800,
                model="haiku",
                dry_run=True,
                transcripts_dir=tmp_path / "transcripts",
                patches_dir=tmp_path / "patches",
            )
        assert result is None  # dry run returns None

    def test_subprocess_called(
        self,
        tmp_path: Path,
        sample_bug: Bug,
        mock_claude_json_output: dict[str, Any],
    ) -> None:
        ruff_dir = tmp_path / "ruff"
        binary = ruff_dir / "target" / "debug" / "ruff"
        binary.parent.mkdir(parents=True)
        binary.write_text("fake")
        mock_output = json.dumps(mock_claude_json_output)
        with (
            patch("ate.harness.get_ruff_version", return_value="0.14.14"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.stdout = mock_output
            mock_run.return_value.returncode = 0
            result = run_treatment0(
                sample_bug,
                ruff_dir=ruff_dir,
                max_turns=50,
                timeout=1800,
                model="haiku",
                dry_run=False,
                transcripts_dir=tmp_path / "transcripts",
                patches_dir=tmp_path / "patches",
            )
        assert result is not None
        assert result.metadata.bug_id == 20945
        assert result.metadata.mode == ExecutionMode.PROGRAMMATIC
        mock_run.assert_called_once()

    def test_timeout_captured_as_data(
        self,
        tmp_path: Path,
        sample_bug: Bug,
    ) -> None:
        import subprocess

        ruff_dir = tmp_path / "ruff"
        binary = ruff_dir / "target" / "debug" / "ruff"
        binary.parent.mkdir(parents=True)
        binary.write_text("fake")
        with (
            patch("ate.harness.get_ruff_version", return_value="0.14.14"),
            patch("subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 1800)),
        ):
            result = run_treatment0(
                sample_bug,
                ruff_dir=ruff_dir,
                max_turns=50,
                timeout=1800,
                model="haiku",
                dry_run=False,
                transcripts_dir=tmp_path / "transcripts",
                patches_dir=tmp_path / "patches",
            )
        assert result is not None
        assert result.metadata.exit_code == -1

    def test_invalid_json_handled(
        self,
        tmp_path: Path,
        sample_bug: Bug,
    ) -> None:
        ruff_dir = tmp_path / "ruff"
        binary = ruff_dir / "target" / "debug" / "ruff"
        binary.parent.mkdir(parents=True)
        binary.write_text("fake")
        with (
            patch("ate.harness.get_ruff_version", return_value="0.14.14"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.stdout = "not valid json"
            mock_run.return_value.returncode = 0
            result = run_treatment0(
                sample_bug,
                ruff_dir=ruff_dir,
                max_turns=50,
                timeout=1800,
                model="haiku",
                dry_run=False,
                transcripts_dir=tmp_path / "transcripts",
                patches_dir=tmp_path / "patches",
            )
        assert result is not None
        assert result.metadata.session_id is None

    def test_metadata_saved(
        self,
        tmp_path: Path,
        sample_bug: Bug,
        mock_claude_json_output: dict[str, Any],
    ) -> None:
        ruff_dir = tmp_path / "ruff"
        binary = ruff_dir / "target" / "debug" / "ruff"
        binary.parent.mkdir(parents=True)
        binary.write_text("fake")
        mock_output = json.dumps(mock_claude_json_output)
        with (
            patch("ate.harness.get_ruff_version", return_value="0.14.14"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.stdout = mock_output
            mock_run.return_value.returncode = 0
            run_treatment0(
                sample_bug,
                ruff_dir=ruff_dir,
                max_turns=50,
                timeout=1800,
                model="haiku",
                dry_run=False,
                transcripts_dir=tmp_path / "transcripts",
                patches_dir=tmp_path / "patches",
            )
        meta_path = tmp_path / "transcripts" / "treatment-0" / "bug-20945" / "metadata.json"
        assert meta_path.exists()

    def test_preflight_failure_raises(self, tmp_path: Path, sample_bug: Bug) -> None:
        ruff_dir = tmp_path / "nonexistent"
        with pytest.raises(PreflightError):
            run_treatment0(
                sample_bug,
                ruff_dir=ruff_dir,
                max_turns=50,
                timeout=1800,
                model="haiku",
                dry_run=False,
                transcripts_dir=tmp_path / "transcripts",
                patches_dir=tmp_path / "patches",
            )


# ---------------------------------------------------------------------------
# TestGetOpeningPrompt
# ---------------------------------------------------------------------------


class TestGetOpeningPrompt:
    def test_detailed_includes_reproduction(
        self, sample_bug: Bug, sample_treatment_0: Treatment
    ) -> None:
        prompt = get_opening_prompt(sample_treatment_0, sample_bug)
        assert sample_bug.reproduction in prompt
        assert str(sample_bug.id) in prompt

    def test_vague_is_minimal(
        self, sample_bug: Bug, sample_interactive_treatment: Treatment
    ) -> None:
        prompt = get_opening_prompt(sample_interactive_treatment, sample_bug)
        assert str(sample_bug.id) in prompt
        assert sample_bug.url in prompt
        # Vague should not include full reproduction
        assert sample_bug.reproduction not in prompt


# ---------------------------------------------------------------------------
# TestRenderSessionGuide
# ---------------------------------------------------------------------------


class TestRenderSessionGuide:
    def test_contains_treatment_info(
        self, sample_bug: Bug, sample_interactive_treatment: Treatment
    ) -> None:
        run_dir = Path("/tmp/test-run")
        guide = render_session_guide(
            sample_interactive_treatment,
            sample_bug,
            assignment_text="Bugs #20945, #22528",
            run_dir=run_dir,
        )
        assert sample_interactive_treatment.label in guide
        assert "2a" in guide

    def test_contains_bug_details(
        self, sample_bug: Bug, sample_interactive_treatment: Treatment
    ) -> None:
        run_dir = Path("/tmp/test-run")
        guide = render_session_guide(
            sample_interactive_treatment,
            sample_bug,
            assignment_text="Bugs #20945",
            run_dir=run_dir,
        )
        assert str(sample_bug.id) in guide
        assert sample_bug.title in guide

    def test_encourage_communication(
        self, sample_bug: Bug, sample_interactive_treatment: Treatment
    ) -> None:
        run_dir = Path("/tmp/test-run")
        guide = render_session_guide(
            sample_interactive_treatment,
            sample_bug,
            assignment_text="Bugs #20945",
            run_dir=run_dir,
        )
        # Treatment has communication="encourage"
        assert "encourage" in guide.lower() or "communicat" in guide.lower()


# ---------------------------------------------------------------------------
# TestScaffoldInteractiveRun
# ---------------------------------------------------------------------------


class TestScaffoldInteractiveRun:
    def test_creates_files(
        self,
        tmp_path: Path,
        sample_bug: Bug,
        sample_interactive_treatment: Treatment,
    ) -> None:
        run_dir = scaffold_interactive_run(
            sample_interactive_treatment,
            sample_bug,
            bug_assignments="Bugs #20945, #22528",
            transcripts_dir=tmp_path / "transcripts",
        )
        assert (run_dir / "session_guide.md").exists()
        assert (run_dir / "notes.md").exists()
        assert (run_dir / "metadata.json").exists()

    def test_notes_not_overwritten(
        self,
        tmp_path: Path,
        sample_bug: Bug,
        sample_interactive_treatment: Treatment,
    ) -> None:
        transcripts_dir = tmp_path / "transcripts"
        run_dir = scaffold_interactive_run(
            sample_interactive_treatment,
            sample_bug,
            bug_assignments="Bugs #20945",
            transcripts_dir=transcripts_dir,
        )
        # Write custom content to notes
        notes_path = run_dir / "notes.md"
        notes_path.write_text("My custom notes")
        # Scaffold again — notes should NOT be overwritten
        scaffold_interactive_run(
            sample_interactive_treatment,
            sample_bug,
            bug_assignments="Bugs #20945",
            transcripts_dir=transcripts_dir,
        )
        assert notes_path.read_text() == "My custom notes"
