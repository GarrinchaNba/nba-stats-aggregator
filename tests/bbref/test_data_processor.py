from __future__ import annotations

from src.bbref.data_processor import GameType, get_columns, get_rankings, get_rows
from src.common.stub import get_stub_soup
from src.common.utils import get_csv_file_as_dict


def test_should_extract_team_rankings_from_standings_table() -> None:
    # Given
    teams = get_csv_file_as_dict("data/common/nba_teams.csv", ",")
    standings_table = get_stub_soup("stub_bbref_standings").find("table", {"id": "expanded_standings"})
    first_row = standings_table.select_one("tbody > tr")
    first_team = first_row.select_one('td[data-stat="team_name"] > a').text.strip()
    first_team_id = next(team["prefix_1"] for team in teams if team["name"] == first_team)
    expected_first_win_pct = first_row.select_one('td[data-stat="Overall"]').attrs["csk"]

    # When
    rankings = get_rankings(standings_table, teams, "prefix_1")

    # Then
    assert first_team_id in rankings
    assert rankings[first_team_id] == expected_first_win_pct


def test_should_raise_error_when_team_is_missing_from_mapping() -> None:
    # Given
    standings_table = get_stub_soup("stub_bbref_standings").find("table", {"id": "expanded_standings"})

    # When / Then
    try:
        get_rankings(standings_table, [], "prefix_1")
        assert False, "Expected get_rankings to fail when teams mapping is empty."
    except Exception as error:
        assert "Team not found" in str(error)


def test_should_append_ranking_fields_when_building_regular_season_rows() -> None:
    # Given
    soup = get_stub_soup("stub_bbref_game_logs")
    table = soup.find("table", {"id": "tgl_basic"})
    columns = get_columns(table)

    team_ids: list[str] = []
    for row in table.select("tbody > tr:not([class*='thead'])"):
        cells = row.find_all("td")
        if len(cells) > 3:
            team_ids.append(cells[3].text.strip().lower())
    rankings = {team_id: f"0.{index + 1:03d}" for index, team_id in enumerate(dict.fromkeys(team_ids))}

    # When
    rows = get_rows(table, columns, rankings, GameType.REGULAR)

    # Then
    assert rows
    assert all(row["Game type"] == "regular_season" for row in rows)
    assert all("Opp rank" in row for row in rows)
    assert all("Opp win%" in row for row in rows)


def test_should_not_append_ranking_fields_for_playoffs_when_rankings_are_empty() -> None:
    # Given
    soup = get_stub_soup("stub_bbref_game_logs")
    table = soup.find("table", {"id": "tgl_basic_playoffs"})
    assert table is not None
    columns = get_columns(table)

    # When
    rows = get_rows(table, columns, {}, GameType.PLAYOFFS)

    # Then
    assert rows
    assert all(row["Game type"] == "playoffs" for row in rows)
    assert all("Opp rank" not in row for row in rows)
    assert all("Opp win%" not in row for row in rows)


