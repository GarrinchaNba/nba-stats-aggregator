from __future__ import annotations

from bs4 import BeautifulSoup

from src.sportpress.team_games_processor import build_boxscore, build_results, get_team


def test_should_aggregate_overtime_points_when_building_results() -> None:
    # Given
    html = """
    <table>
      <tr>
        <td data-stat="1">20</td>
        <td data-stat="2">21</td>
        <td data-stat="3">22</td>
        <td data-stat="4">23</td>
        <td data-stat="1OT">9</td>
        <td data-stat="2OT">5</td>
        <td data-stat="T"><strong>100</strong></td>
      </tr>
      <tr>
        <td data-stat="1">19</td>
        <td data-stat="2">20</td>
        <td data-stat="3">21</td>
        <td data-stat="4">22</td>
        <td data-stat="1OT">7</td>
        <td data-stat="2OT">4</td>
        <td data-stat="T"><strong>93</strong></td>
      </tr>
    </table>
    """
    score_table = BeautifulSoup(html, "html.parser").find("table")

    # When
    result = build_results(score_table)

    # Then
    assert result["Away"]["result"] == "20|21|22|23|14|100"
    assert result["Home"]["result"] == "19|20|21|22|11|93"
    assert result["Away"]["outcome"] == "Win"
    assert result["Home"]["outcome"] == "Loss"


def test_should_keep_metadata_only_on_first_player_row_when_building_boxscore() -> None:
    # Given
    html = """
    <table>
      <tr>
        <th scope="row">Player One</th>
        <td data-stat="mp">30:00</td>
        <td data-stat="pts">20</td>
        <td data-stat="ast">5</td>
      </tr>
      <tr>
        <th scope="row">Player Two</th>
        <td data-stat="mp">28:00</td>
        <td data-stat="pts">15</td>
        <td data-stat="ast">7</td>
      </tr>
    </table>
    """
    boxscore_table = BeautifulSoup(html, "html.parser").find("table")
    results_outcome = {"result": "20|21|22|23|0|86", "outcome": "Win"}
    calendar = {
        "Date": "2024/10/24",
        "Time": "19:30:00",
        "Venue": "Arena",
        "Home": "San Antonio Spurs",
        "Away": "Dallas Mavericks",
    }

    # When
    rows = build_boxscore(boxscore_table, results_outcome, calendar, is_home=True)

    # Then
    assert len(rows) == 2
    assert rows[0][0] == "Player One"
    assert rows[0][1:7] == ["San Antonio Spurs", "20|21|22|23|0|86", "Win", "2024/10/24", "19:30:00", "Arena"]
    assert rows[1][0] == "Player Two"
    assert rows[1][1:7] == ["", "", "", "", "", ""]


def test_should_map_clippers_name_to_basketball_reference_variant_when_getting_team() -> None:
    # Given
    input_row = {"Home": "Los Angeles Clippers"}

    # When
    team_name = get_team(input_row)

    # Then
    assert team_name == "LA Clippers"


