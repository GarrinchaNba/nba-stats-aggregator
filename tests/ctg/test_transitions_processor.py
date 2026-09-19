from __future__ import annotations

import csv

import pandas as pd
import pytest

from config.config import Environment
from src.ctg import transitions_processor
from tests.conftest import PROJECT_ROOT


EXPECTED_TRANSITIONS_FILE = PROJECT_ROOT / "data" / "ctg" / "transitions.csv"


def test_should_match_known_transition_output_when_computing_2024_data(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    # Given
    captured_dataframes: list[pd.DataFrame] = []
    teams_file = tmp_path / "nba_teams.csv"
    with teams_file.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["name", "prefix_long", "first_year", "last_year"],
            delimiter=",",
        )
        writer.writeheader()
        writer.writerow(
            {
                "name": "Boston Celtics",
                "prefix_long": "boston-celtics",
                "first_year": "1947",
                "last_year": "",
            }
        )

    monkeypatch.setattr(
        transitions_processor,
        "generate_csv_from_dataframe",
        lambda dataframe, *_args, **_kwargs: captured_dataframes.append(dataframe.copy()),
    )
    monkeypatch.setattr(transitions_processor, "NBA_TEAMS_FILE", str(teams_file))

    # When
    transitions_processor.compute_transitions_data("2024", "2024", Environment.LOCAL)

    # Then
    assert len(captured_dataframes) == 1

    actual_row = (
        captured_dataframes[0]
        .loc[lambda dataframe: dataframe["team"] == "Boston Celtics"]
        .astype(str)
        .iloc[0]
        .to_dict()
    )
    with EXPECTED_TRANSITIONS_FILE.open(encoding="utf-8", newline="") as csv_file:
        expected_row = next(
            row for row in csv.DictReader(csv_file, delimiter=";") if row["team"] == "Boston Celtics"
        )

    assert actual_row == expected_row


