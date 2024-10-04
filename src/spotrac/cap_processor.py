import csv
import os

import pandas as pd

from src.common.constant import NBA_TEAMS_FILE, SPOTRAC_DATA_DIRECTORY
from src.common.file_processor import generate_csv_from_dataframe
from src.common.utils import does_franchise_exists_for_season, get_season_from_year

data_columns = [
    'player',
    'team',
    'season',
    'cap hit percent',
]


def generate_cap(min_year: str, max_year: str):
    print('Compute cap data from year [' + min_year + '] to year [' + max_year + ']')
    data_rows = []
    output_file: str = 'cap_' + min_year + '_' + max_year + '.csv'
    with open(NBA_TEAMS_FILE, mode='r', newline='') as csvfile:
        teams = list(csv.DictReader(csvfile, delimiter=','))
        for year in range(int(min_year), int(max_year) + 1):
            print('Compute cap data for year [' + str(year) + ']')

            for team_iterator, team in enumerate(teams):
                if not does_franchise_exists_for_season(team, year):
                    continue
                print('Team : ' + team['name'])
                team_name = team['prefix_long'].replace('-', '_')
                file_type = 'active_roster_cap'
                file_name = get_file_name(file_type, team_name, year)
                contracts_file = str(os.path.join(SPOTRAC_DATA_DIRECTORY, file_name))
                print('file : ' + contracts_file)
                if not os.path.isfile(contracts_file):
                    print('File not found : ' + contracts_file)
                    continue
                with open(contracts_file, mode='r', newline='') as csvfile:
                    contracts_team_year = list(csv.DictReader(csvfile, delimiter=';'))
                    for iterator, contract_team_year in enumerate(contracts_team_year):
                        cap_hit_percent = get_cap_hit_percent(contract_team_year)
                        if cap_hit_percent is not None:
                            data_row = {
                                'team': team['name'],
                                'season': get_season_from_year(year, '-'),
                                'player': contract_team_year['Player'],
                                'cap hit percent': cap_hit_percent
                            }
                            data_rows.append(data_row)
    dataframe = pd.DataFrame.from_records(data_rows, columns=data_columns)
    generate_csv_from_dataframe(dataframe, SPOTRAC_DATA_DIRECTORY, output_file)


def get_file_name(file_type, team_name, year):
    return team_name + '_' + file_type + '_' + str(year) + '.csv'


def get_cap_hit_percent(game_log) -> float | None:
    return get_field_percent(game_log, 'Cap Hit Pct League Cap')


def get_field_percent(game_log, field) -> float | None:
    value = game_log[field]
    if value in ['', '-']:
        return None
    return float(value.replace('%', ''))
