from __future__ import annotations

import csv
from pathlib import Path

from config.config import Environment
from src.bbref import team_calendar_processor


def test_should_create_calendar_csv_with_place_column_when_stubbed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    # Given
    monkeypatch.setattr(team_calendar_processor, "BBREF_DATA_DIRECTORY", str(tmp_path))

    # When
    team_calendar_processor.generate_calendar_for_season(
        season="2024_2025",
        team_prefix="sas",
        environment=Environment.LOCAL,
        is_stubbed=True,
    )

    # Then
    output_file = tmp_path / "sas_calendar_2024_2025.csv"
    assert output_file.exists()

    with output_file.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.reader(csv_file, delimiter=";"))

    assert len(rows) > 1
    assert "Place" in rows[0]
    assert rows[1][0] == "1"

