from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pytest

from config.config import Environment
from src.sportpress import team_calendar_processor
from tests.conftest import PROJECT_ROOT


@pytest.fixture
def sportpress_calendar_files(tmp_path: Path) -> dict[str, Path]:
    input_file = PROJECT_ROOT / "data" / "bbref" / "sas_calendar_2024_2025.csv"
    expected_output_file = PROJECT_ROOT / "data" / "bbref" / "sas_calendar_2024_2025_sportpress.csv"
    copied_input_file = tmp_path / input_file.name
    shutil.copyfile(input_file, copied_input_file)
    return {
        "expected_output_file": expected_output_file,
        "output_file": tmp_path / expected_output_file.name,
    }


def test_should_generate_expected_sportpress_calendar_when_source_calendar_exists(
    monkeypatch: pytest.MonkeyPatch,
    sportpress_calendar_files: dict[str, Path],
) -> None:
    # Given
    monkeypatch.setattr(team_calendar_processor, "BBREF_DATA_DIRECTORY", str(sportpress_calendar_files["output_file"].parent))

    # When
    team_calendar_processor.generate_sportpress_calendar_for_season("2024_2025", "sas", Environment.LOCAL)

    # Then
    assert sportpress_calendar_files["output_file"].read_text(encoding="utf-8") == sportpress_calendar_files[
        "expected_output_file"
    ].read_text(encoding="utf-8")


def test_should_generate_sportpress_calendar_after_fallback_calendar_generation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Given
    monkeypatch.setattr(team_calendar_processor, "BBREF_DATA_DIRECTORY", str(tmp_path))

    def _fake_generate_calendar_for_season(_season: str, team_prefix: str, _environment: Environment) -> None:
        input_file = tmp_path / f"{team_prefix}_calendar_2024_2025.csv"
        with input_file.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=["Date", "Start (ET)", "Place", "Opponent"],
                delimiter=";",
            )
            writer.writeheader()
            writer.writerow(
                {
                    "Date": "Thu, Oct 24, 2024",
                    "Start (ET)": "7:30p",
                    "Place": "@",
                    "Opponent": "Dallas Mavericks",
                }
            )

    monkeypatch.setattr(team_calendar_processor, "generate_calendar_for_season", _fake_generate_calendar_for_season)

    # When
    team_calendar_processor.generate_sportpress_calendar_for_season(
        season="2024_2025",
        team_prefix="sas",
        environment=Environment.LOCAL,
        teams_mapping={"sas": "San Antonio Spurs"},
    )

    # Then
    output_file = tmp_path / "sas_calendar_2024_2025_sportpress.csv"
    assert output_file.exists()

    with output_file.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file, delimiter=","))

    assert rows == [
        {
            "Date": "2024/10/24",
            "Time": "19:30:00",
            "Venue": "American Airlines Center",
            "Home": "Dallas Mavericks",
            "Away": "San Antonio Spurs",
        }
    ]


def test_should_map_home_game_to_team_home_away_and_arena_when_place_is_empty(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Given
    monkeypatch.setattr(team_calendar_processor, "BBREF_DATA_DIRECTORY", str(tmp_path))
    input_file = tmp_path / "sas_calendar_2024_2025.csv"
    with input_file.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["Date", "Start (ET)", "Place", "Opponent"],
            delimiter=";",
        )
        writer.writeheader()
        writer.writerow(
            {
                "Date": "Sat, Oct 26, 2024",
                "Start (ET)": "8:30p",
                "Place": "",
                "Opponent": "Houston Rockets",
            }
        )

    # When
    team_calendar_processor.generate_sportpress_calendar_for_season(
        season="2024_2025",
        team_prefix="sas",
        environment=Environment.LOCAL,
        teams_mapping={"sas": "San Antonio Spurs"},
    )

    # Then
    output_file = tmp_path / "sas_calendar_2024_2025_sportpress.csv"
    with output_file.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file, delimiter=","))

    assert rows == [
        {
            "Date": "2024/10/26",
            "Time": "20:30:00",
            "Venue": "Frost Bank Center",
            "Home": "San Antonio Spurs",
            "Away": "Houston Rockets",
        }
    ]


def test_should_raise_exception_when_calendar_file_is_missing_after_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Given
    monkeypatch.setattr(team_calendar_processor, "BBREF_DATA_DIRECTORY", str(tmp_path))
    monkeypatch.setattr(team_calendar_processor, "generate_calendar_for_season", lambda *_args, **_kwargs: None)

    # When / Then
    with pytest.raises(Exception) as raised_error:
        team_calendar_processor.generate_sportpress_calendar_for_season(
            season="2024_2025",
            team_prefix="sas",
            environment=Environment.LOCAL,
            teams_mapping={"sas": "San Antonio Spurs"},
        )

    assert raised_error.value.args[0] == "Missing calendar file"

