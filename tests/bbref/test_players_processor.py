from __future__ import annotations

from collections import defaultdict

from src.bbref.players_processor import build_positions, get_players_data


def test_should_expand_position_labels_when_building_positions() -> None:
    # Given
    raw_positions = "PG-SG"

    # When
    positions = build_positions(raw_positions)

    # Then
    assert positions == "Guard-Guard"


def test_should_build_stubbed_player_rows_when_fetching_players_data() -> None:
    # Given
    countries_mapping = defaultdict(lambda: "UNK")
    countries_mapping["US"] = "USA"
    teams_mapping = {"sas": "San Antonio Spurs"}

    # When
    rows = get_players_data(
        team_prefix="SAS",
        season="2024_2025",
        countries_mapping=countries_mapping,
        teams_mapping=teams_mapping,
        is_stubbed=True,
    )

    # Then
    assert rows
    assert all(len(row) == 8 for row in rows)
    assert all(row[5] == "NBA" for row in rows)
    assert all(row[6] == "San Antonio Spurs" for row in rows)
    assert all(row[7] == "2024-2025" for row in rows)

