import csv

import pandas as pd
from bs4 import Tag

from config.config import Environment, get_is_stubbed
from src.bbref.data_processor import get_rankings, get_columns, get_rows, GameType
from src.common import constant
from src.common.constant import (
    NBA_TEAMS_FILE,
    BASKETBALL_REFERENCE_URL,
    BBREF_DATA_DIRECTORY,
    BBREF_GAME_LOGS_DATA_DIRECTORY,
)
from src.common.data_collector import get_content_from_soup, get_soup
from src.common.file_processor import (
    generate_csv_from_dataframe,
    generate_csv_from_list_dicts,
    build_file_name,
)
from src.common.stub import get_stub_soup
from src.common.utils import wait_random_duration, does_franchise_exists_for_season


def _get_rankings_soup(year: int, is_stubbed: bool) -> Tag:
    """Fetch and parse rankings HTML for a given year.

    Args:
        year: The NBA season year.
        is_stubbed: Whether to use stub data instead of live URLs.

    Returns:
        BeautifulSoup Tag containing the expanded standings table.
    """
    if not is_stubbed:
        url = f"{BASKETBALL_REFERENCE_URL}/leagues/NBA_{year}_standings.html"
        soup = get_soup(url)
    else:
        soup = get_stub_soup("stub_bbref_standings")
    return get_content_from_soup(soup, "expanded_standings", "table", "id")


def _get_game_logs_soup(team_prefix: str, year: int, is_stubbed: bool) -> Tag:
    """Fetch and parse game logs HTML for a team in a given year.

    Args:
        team_prefix: The team's Basketball Reference prefix.
        year: The NBA season year.
        is_stubbed: Whether to use stub data instead of live URLs.

    Returns:
        BeautifulSoup Tag containing the game logs page.
    """
    if not is_stubbed:
        url = f"{BASKETBALL_REFERENCE_URL}/teams/{team_prefix}/{year}/gamelog"
        return get_soup(url)
    else:
        return get_stub_soup("stub_bbref_game_logs")


def _extract_game_logs_from_soup(
    soup: Tag, columns: list[str], ranking_data: dict[str, str]
) -> list[dict[str, str]]:
    """Extract game logs from HTML, combining regular season and playoff games.

    Args:
        soup: BeautifulSoup Tag containing the game logs page.
        columns: List of column names extracted from the table headers.
        ranking_data: Dictionary mapping team IDs to their win percentages.

    Returns:
        List of dictionaries representing game rows.
    """
    game_rows = []

    regular_season_table = get_content_from_soup(soup, "tgl_basic", "table", "id")
    game_rows.extend(
        get_rows(regular_season_table, columns, ranking_data, GameType.REGULAR)
    )

    playoff_table = get_content_from_soup(soup, "tgl_basic_playoffs", "table", "id")
    if playoff_table is not None:
        game_rows.extend(
            get_rows(playoff_table, columns, ranking_data, GameType.PLAYOFFS)
        )

    return game_rows


def _process_team_game_logs(
    team: dict[str, str],
    year: int,
    ranking_data: dict[str, str],
    is_stubbed: bool,
) -> None:
    """Process and save game logs for a single team.

    Args:
        team: Team dictionary with metadata (name, prefix_1, prefix_long).
        year: The NBA season year.
        ranking_data: Dictionary mapping team IDs to their win percentages.
        is_stubbed: Whether to use stub data instead of live URLs.
    """
    print(f"  Team: {team['name']}")

    soup = _get_game_logs_soup(team["prefix_1"], year, is_stubbed)
    regular_season_table = get_content_from_soup(soup, "tgl_basic", "table", "id")
    columns = get_columns(regular_season_table)

    game_rows = _extract_game_logs_from_soup(soup, columns, ranking_data)

    filtered_columns = [col for col in columns if col]
    dataframe = pd.DataFrame.from_records(game_rows, columns=filtered_columns)

    output_file = build_file_name(
        BBREF_GAME_LOGS_DATA_DIRECTORY,
        f"{team['prefix_long'].replace('-', '_')}_game_logs_",
        "",
        ".csv",
        str(year),
    )
    generate_csv_from_dataframe(dataframe, BBREF_GAME_LOGS_DATA_DIRECTORY, output_file)
    wait_random_duration()


def generate_game_logs(min_year: str, max_year: str, environment: Environment) -> None:
    """Generate and save BBRef game logs for teams across multiple seasons.

    Args:
        min_year: Starting season year (inclusive).
        max_year: Ending season year (inclusive).
        environment: Configuration environment (local or prod).
    """
    print(f"Generate game logs from year [{min_year}] to year [{max_year}]")
    is_stubbed = get_is_stubbed(environment)

    with open(NBA_TEAMS_FILE, mode="r", newline="") as csvfile:
        teams = list(csv.DictReader(csvfile, delimiter=","))

        for year in range(int(min_year), int(max_year) + 1):
            print(f"Generate game logs for year [{year}]")

            ranking_html = _get_rankings_soup(year, is_stubbed)
            ranking_data = get_rankings(ranking_html, teams, "prefix_1")

            for team_iterator, team in enumerate(teams):
                if (not does_franchise_exists_for_season(team, year)) or team[
                    "generated"
                ] == "1":
                    continue

                _process_team_game_logs(team, year, ranking_data, is_stubbed)

        generate_csv_from_list_dicts(
            teams, constant.BBREF_DATA_DIRECTORY, NBA_TEAMS_FILE, "w", ","
        )
