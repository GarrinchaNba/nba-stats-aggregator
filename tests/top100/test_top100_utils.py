from __future__ import annotations
from pathlib import Path
import pytest
from config.config import Environment
from src.common.constant import BASKETLAB_WITH_SPOTRAC_FILE, SRC_DIRECTORY
from src.common.file_processor import build_export_json_file_name, build_top100_csv_file_name
from src.top100 import top100_utils
def test_should_execute_top100_processors_in_expected_order_when_generating_full(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    executed_commands: list[str] = []
    converted_files: list[tuple[str, str]] = []
    monkeypatch.setattr(top100_utils.os, "system", lambda command: executed_commands.append(command) or 0)
    monkeypatch.setattr(top100_utils, "csv_to_json", lambda source, target: converted_files.append((source, target)))
    expected_scripts = [
        Path(SRC_DIRECTORY) / "bbref" / "top100.py",
        Path(SRC_DIRECTORY) / "538" / "top100.py",
        Path(SRC_DIRECTORY) / "bbindex" / "top100.py",
        Path(SRC_DIRECTORY) / "spotrac" / "top100.py",
    ]
    # When
    top100_utils.generate_full("2023", "2024", Environment.PROD)
    # Then
    assert executed_commands == [
        f"python3 {script} 2023 2024 prod"
        for script in expected_scripts
    ]
    assert converted_files == [
        (
            build_top100_csv_file_name(BASKETLAB_WITH_SPOTRAC_FILE, "2023", "2024"),
            build_export_json_file_name("", "2023", "2024"),
        )
    ]
