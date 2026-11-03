import csv

import pandas as pd
from bs4 import Tag

from config.config import Environment, get_ctg_identifiers, get_is_stubbed
from src.bbref.data_processor import get_rankings
from src.common import constant
from src.common.constant import (
    NBA_TEAMS_FILE,
    BASKETBALL_REFERENCE_URL,
    CLEANING_THE_GLASS_URL,
    CLEANING_THE_GLASS_DATA_DIRECTORY,
)
from src.common.data_collector import (
    get_content_from_soup,
    get_all_content_from_soup,
    get_soup,
)
from src.common.file_processor import (
    generate_csv_from_dataframe,
    generate_csv_from_list_dicts,
    build_file_name,
)
from src.common.stub import get_stub_soup
from src.common.utils import wait_random_duration, does_franchise_exists_for_season
from src.ctg.data_processor import get_columns, get_rows


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


def _get_ctg_cookies(environment: Environment) -> dict[str, str]:
    """Get CTG authentication cookies from config.

    Args:
        environment: Configuration environment.

    Returns:
        Dictionary with authentication cookies.
    """
    ctg_identifiers = get_ctg_identifiers(environment)
    return {
        "wordpress_logged_in_cfb45adfd4102bd74a046b78d76db012": ctg_identifiers[
            "cookieValue"
        ],
        "sessionid": ctg_identifiers["sessionId"],
    }


def _get_ctg_game_logs_soup(
    team_id: str, year: int, is_stubbed: bool, cookies: dict[str, str]
) -> Tag:
    """Fetch and parse CTG game logs HTML for a team in a given year.

    Args:
        team_id: The team's CTG ID.
        year: The NBA season year (converted to prior year for CTG format).
        is_stubbed: Whether to use stub data instead of live URLs.
        cookies: Authentication cookies for CTG.

    Returns:
        BeautifulSoup Tag containing the game logs page.
    """
    if not is_stubbed:
        url = f"{CLEANING_THE_GLASS_URL}/stats/team/{team_id}/gamelogs?season={year - 1}"
        return get_soup(url, cookies)
    else:
        return get_stub_soup("stub_ctg_game_logs")


def _process_ctg_tables(
    soup: Tag,
    team: dict[str, str],
    year: int,
    ranking_data: dict[str, str],
) -> None:
    """Process all game log tables from CTG HTML for a team.

    Args:
        soup: BeautifulSoup Tag containing CTG game logs page.
        team: Team dictionary with metadata (prefix_long).
        year: The NBA season year.
        ranking_data: Dictionary mapping team IDs to their win percentages.
    """
    stat_containers = get_all_content_from_soup(
        soup, "stat_table_container", "div", "class"
    )

    for container in stat_containers:
        table = container.findChild("table")
        table_id = table.attrs["id"]

        output_file = build_file_name(
            CLEANING_THE_GLASS_DATA_DIRECTORY,
            f"{team['prefix_long'].replace('-', '_')}_{table_id.replace('team_', '')}_",
            "",
            ".csv",
            str(year),
        )

        data_table = get_content_from_soup(container, table_id, "table", "id")
        columns = get_columns(data_table)
        rows = get_rows(data_table, columns, ranking_data)
        dataframe = pd.DataFrame.from_records(rows, columns=columns)

        generate_csv_from_dataframe(
            dataframe, CLEANING_THE_GLASS_DATA_DIRECTORY, output_file
        )


def _process_team_game_logs(
    team: dict[str, str],
    year: int,
    ranking_data: dict[str, str],
    is_stubbed: bool,
    cookies: dict[str, str],
) -> None:
    """Process and save game logs for a single team.

    Args:
        team: Team dictionary with metadata (name, id, prefix_long).
        year: The NBA season year.
        ranking_data: Dictionary mapping team IDs to their win percentages.
        is_stubbed: Whether to use stub data instead of live URLs.
        cookies: Authentication cookies for CTG.
    """
    print(f"  Team: {team['name']}")
    soup = _get_ctg_game_logs_soup(team["id"], year, is_stubbed, cookies)
    _process_ctg_tables(soup, team, year, ranking_data)
    wait_random_duration()


def generate_game_logs(min_year: str, max_year: str, environment: Environment) -> None:
    """Generate and save CTG game logs for teams across multiple seasons.

    Args:
        min_year: Starting season year (inclusive).
        max_year: Ending season year (inclusive).
        environment: Configuration environment (local or prod).
    """
    print(f"Generate game logs from year [{min_year}] to year [{max_year}]")
    is_stubbed = get_is_stubbed(environment)
    cookies = _get_ctg_cookies(environment)

    with open(NBA_TEAMS_FILE, mode="r", newline="") as csvfile:
        teams = list(csv.DictReader(csvfile, delimiter=","))

        for year in range(int(min_year), int(max_year) + 1):
            print(f"Generate game logs for year [{year}]")

            ranking_html = _get_rankings_soup(year, is_stubbed)
            ranking_data = get_rankings(ranking_html, teams, "prefix_2")

            for team_iterator, team in enumerate(teams):
                if (not does_franchise_exists_for_season(team, year)) or team[
                    "generated"
                ] == "1":
                    continue

                _process_team_game_logs(team, year, ranking_data, is_stubbed, cookies)

                if year == int(max_year):
                    teams[team_iterator]["generated"] = "1"

        generate_csv_from_list_dicts(
            teams, constant.BBREF_DATA_DIRECTORY, NBA_TEAMS_FILE, "w", ","
        )
