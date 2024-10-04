import csv

import pandas as pd

from config.config import Environment, get_is_stubbed
from src.common import constant
from src.common.constant import SPOTRAC_DATA_DIRECTORY, NBA_TEAMS_FILE, SPOTRAC_URL
from src.common.data_collector import get_content_from_soup, get_soup
from src.common.file_processor import generate_csv_from_dataframe, generate_csv_from_list_dicts, build_file_name
from src.common.stub import get_stub_soup
from src.common.utils import wait_random_duration, does_franchise_exists_for_season
from src.spotrac.data_processor import get_columns, get_rows


teams_by_year_to_skip = [
    {'team': 'miami-heat', 'year': '2018'},
    {'team': 'denver-nuggets', 'year': '2018'}
]


def generate_contracts(min_year: str, max_year: str, environment: Environment):
    print('Generate contracts from year [' + min_year + '] to year [' + max_year + ']')
    is_stubbed = get_is_stubbed(environment)
    with open(NBA_TEAMS_FILE, mode='r', newline='') as csvfile:
        teams = list(csv.DictReader(csvfile, delimiter=','))
        for year in range(int(min_year), int(max_year) + 1):
            print('Generate contracts for year [' + str(year) + ']')
            for team_iterator, team in enumerate(teams):
                if (not does_franchise_exists_for_season(team, year)) or team['generated'] == '1'  or is_to_skip(team, str(year)):
                    continue
                print('Team : ' + team['name'])
                if not is_stubbed:
                    url = SPOTRAC_URL + '/nba/' + team['prefix_long'] + '/cap/_/year/' + str(year - 1)
                    soup = get_soup(url)
                else:
                    soup = get_stub_soup('stub_spotrac_team')
                data = get_content_from_soup(soup, 'table_active', 'table', 'id')

                output_file: str = build_file_name(
                    SPOTRAC_DATA_DIRECTORY,
                    team['prefix_long'].replace('-', '_') + '_active_roster_cap_',
                    '',
                    '.csv',
                    str(year)
                )
                data_columns = get_columns(data)
                data_rows = get_rows(data, data_columns)
                dataframe = pd.DataFrame.from_records(data_rows, columns=data_columns)
                generate_csv_from_dataframe(dataframe, SPOTRAC_DATA_DIRECTORY, output_file)
                if year == max_year:
                    teams[team_iterator]['generated'] = 1
                wait_random_duration()
    generate_csv_from_list_dicts(teams, constant.BBREF_DATA_DIRECTORY, NBA_TEAMS_FILE, 'w', ',')


def is_to_skip(team: str, year: str) -> bool:
    for iterator, team_by_year_to_skip in enumerate(teams_by_year_to_skip):
        if team_by_year_to_skip['team'] != team:
            continue
        if team_by_year_to_skip['year'] == year:
            return True
    return False