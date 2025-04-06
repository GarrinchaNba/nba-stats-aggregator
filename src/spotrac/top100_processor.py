import csv
import os

from config.config import Environment, get_is_stubbed
from src.common.constant import BASKETLAB_WITH_BBINDEX_FILE, NBA_TEAMS_FILE, SPOTRAC_URL, BASKETLAB_WITH_SPOTRAC_FILE, \
    TOP100_DATA_DIRECTORY
from src.common.data_collector import get_soup, get_content_from_soup
from src.common.file_processor import build_top100_csv_file_name, generate_csv_from_list_dicts
from src.common.stub import get_stub_soup
from src.common.utils import does_franchise_exists_for_season, get_season_from_year, wait_random_duration, Duration
from src.spotrac.contracts_processor import is_to_skip
from src.spotrac.data_processor import get_columns
from src.spotrac.data_processor import get_rows

COLUMNS_SPOTRAC = ['Type', 'Cap Hit', 'Cap Hit Pct League Cap', 'Base Salary']
FIXED_PLAYERS: dict[str, str] = {
    "herb jones": "herbert jones",
    "nicolas claxton": "nic claxton",
    "bruce brown jr": "bruce brown"
}


def generate_top100(min_year: str, max_year: str, environment: Environment):
    top100_full_file = build_top100_csv_file_name(BASKETLAB_WITH_BBINDEX_FILE, min_year, max_year)
    output_file: str = build_top100_csv_file_name(BASKETLAB_WITH_SPOTRAC_FILE, min_year, max_year)
    if not os.path.exists(top100_full_file):
        raise Exception('Missing input file', top100_full_file)
    is_stubbed = get_is_stubbed(environment)

    with (open(NBA_TEAMS_FILE, mode='r', newline='') as nba_teams_csv):
        teams = list(csv.DictReader(nba_teams_csv, delimiter=','))
        with open(top100_full_file, mode='r', newline='') as top100_full_csv:
            rows_top100: list[dict[str, str]] = list(csv.DictReader(top100_full_csv, delimiter=';'))
            rows_spotrac: dict[str, dict[str, dict[str, str]]] = {}
            for year in range(int(min_year), int(max_year) + 1):
                print('Generate contracts for year [' + str(year) + ']')
                for team_iterator, team in enumerate(teams):
                    if (not does_franchise_exists_for_season(team, year)) or team['generated'] == '1' or is_to_skip(
                            team, str(year)):
                        continue
                    print('Team : ' + team['name'])
                    if not is_stubbed:
                        url = SPOTRAC_URL + '/nba/' + team['prefix_long'] + '/cap/_/year/' + str(year - 1)
                        soup = get_soup(url)
                    else:
                        soup = get_stub_soup('stub_spotrac_team')
                    data = get_content_from_soup(soup, 'table_active', 'table', 'id')
                    data_columns = get_columns(data)
                    data_rows = get_rows(data, data_columns, False)
                    for data_row in data_rows:
                        player_name = data_row['Player'].replace('\'', '').replace('.', '').lower()
                        if player_name in FIXED_PLAYERS:
                            player_name = FIXED_PLAYERS[player_name]
                        season = get_season_from_year(year)
                        if player_name not in rows_spotrac:
                            rows_spotrac[player_name] = {}
                        rows_spotrac[player_name][season] = data_row
                    wait_random_duration(Duration.SHORT)

            rows_top100_with_spotrac: list[dict[str, str]] = []
            for row_top100 in rows_top100:
                player_name = row_top100['first_name'] + ' ' + row_top100['last_name']
                player_season = row_top100['season']
                print("# Player : " + player_name + " (season : " + player_season + ")")
                if player_name not in rows_spotrac:
                    print('Player not found : ' + player_name)
                    continue
                season_by_player_name = rows_spotrac[player_name][player_season]
                for column, value in season_by_player_name.items():
                    if column not in COLUMNS_SPOTRAC:
                        continue
                    column_updated = column.lower().replace(' ', '_').replace('-', '_')
                    row_top100[column_updated] = value
                rows_top100_with_spotrac.append(row_top100)
    generate_csv_from_list_dicts(rows_top100_with_spotrac, TOP100_DATA_DIRECTORY, output_file, 'w')
