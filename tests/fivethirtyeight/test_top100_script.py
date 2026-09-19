from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.common.constant import BASKETLAB_COMPLETE_FILE_BASE, BASKETLAB_WITH_RAPTORS_FILE
from tests.conftest import run_cli_script


@pytest.fixture
def fivethirtyeight_test_files(tmp_path: Path) -> dict[str, Path]:
    data_directory = tmp_path / "538"
    data_directory.mkdir(parents=True)

    input_file = tmp_path / "top100_complete.csv"
    with input_file.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["first_name", "last_name", "player_id", "season"],
            delimiter=";",
        )
        writer.writeheader()
        writer.writerow(
            {
                "first_name": "lebron",
                "last_name": "james",
                "player_id": "jamesle01",
                "season": "2010-2011",
            }
        )

    historical_file = data_directory / "historical_RAPTOR_by_player.csv"
    with historical_file.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "player_name",
                "player_id",
                "season",
                "poss",
                "mp",
                "raptor_offense",
                "raptor_defense",
                "raptor_total",
                "war_total",
                "war_reg_season",
                "war_playoffs",
                "predator_offense",
                "predator_defense",
                "predator_total",
                "pace_impact",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "player_name": "LeBron James",
                "player_id": "jamesle01",
                "season": "2011",
                "poss": "15648",
                "mp": "3063",
                "raptor_offense": "6.3",
                "raptor_defense": "1.8",
                "raptor_total": "8.1",
                "war_total": "7.8",
                "war_reg_season": "7.5",
                "war_playoffs": "0.3",
                "predator_offense": "6.1",
                "predator_defense": "1.5",
                "predator_total": "7.6",
                "pace_impact": "0.20",
            }
        )

    return {
        "data_directory": data_directory,
        "input_file": input_file,
        "output_file": tmp_path / "top100_with_raptors.csv",
    }


@pytest.mark.parametrize("argv", [[], ["season"]])
def test_should_exit_with_code_one_when_year_argument_is_missing_or_invalid(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
) -> None:
    # Given / When / Then
    with pytest.raises(SystemExit) as raised_error:
        run_cli_script(monkeypatch, "src/538/top100.py", argv)

    assert raised_error.value.code == 1


def test_should_merge_matching_raptor_columns_when_player_and_season_exist(
    monkeypatch: pytest.MonkeyPatch,
    fivethirtyeight_test_files: dict[str, Path],
) -> None:
    # Given
    import src.common.constant as constant_module
    import src.common.file_processor as file_processor_module

    monkeypatch.setattr(
        constant_module,
        "FIVETHIRTYEIGHT_DATA_DIRECTORY",
        str(fivethirtyeight_test_files["data_directory"]),
    )

    def _fake_build_top100_csv_file_name(file_name: str, min_year: str, max_year: str | None = None) -> str:
        if file_name == BASKETLAB_COMPLETE_FILE_BASE:
            return str(fivethirtyeight_test_files["input_file"])
        if file_name == BASKETLAB_WITH_RAPTORS_FILE:
            return str(fivethirtyeight_test_files["output_file"])
        raise AssertionError(f"Unexpected file name: {file_name}")

    monkeypatch.setattr(
        file_processor_module,
        "build_top100_csv_file_name",
        _fake_build_top100_csv_file_name,
    )

    # When
    run_cli_script(monkeypatch, "src/538/top100.py", ["2011", "2011", "local"])

    # Then
    with fivethirtyeight_test_files["output_file"].open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file, delimiter=";"))

    assert len(rows) == 1
    assert rows[0]["player_id"] == "jamesle01"
    assert rows[0]["raptor_total"] == "8.1"
    assert rows[0]["war_total"] == "7.8"
    assert rows[0]["pace_impact"] == "0.20"

