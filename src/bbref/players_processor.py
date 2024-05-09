import os
from datetime import datetime

import pandas as pd

from src.common import constant
from src.common.constant import NBA_TEAMS_FILE, BBREF_DATA_DIRECTORY, BASKETBALL_REFERENCE_URL
from src.common.data_collector import get_table_body, get_soup
from src.common.file_processor import generate_csv_from_dataframe, get_countries_mapping, get_teams_mapping
from src.common.stub import get_stub_soup
from src.common.utils import get_csv_file_as_dict, wait_random_duration, full_strip, \
    does_franchise_exists_for_season, \
    update_countries, get_all_seasons_since
from src.common.utils import get_year_from_season
from config.config import Environment, get_is_stubbed

OUTPUT_COLUMNS = {'number': 'Number', 'player': 'Name', 'pos': 'Positions', 'birth_country': 'Nationality',
                  'birth_date': 'DoB'}
OUTPUT_COLUMNS_ORDERED = ['Number', 'Name', 'Positions', 'Teams', 'Leagues', 'Seasons', 'Nationality', 'DoB']
POSITION_LABELS = {'G': 'Guard', 'PG': 'Guard', 'SG': 'Guard', 'F': 'Forward', 'SF': 'Forward', 'PF': 'Forward',
                   'C': 'Center'}


def generate_players(year: str, environment: Environment):
    print("Generate players from year [" + year + "]")
    seasons = get_all_seasons_since(int(year))
    countries_mapping = get_countries_mapping('alpha-2', 'alpha-3')
    teams_mapping = get_teams_mapping('prefix_1', 'name')
    is_stubbed = get_is_stubbed(environment)
    for season in seasons:
        print("Generate players for season [" + season + "]")
        data = []
        output_file: str = os.path.join(BBREF_DATA_DIRECTORY, 'all_nba_players_' + season + '.csv')
        teams = get_csv_file_as_dict(NBA_TEAMS_FILE)
        for team in teams:
            year = get_year_from_season(season)
            if not does_franchise_exists_for_season(team, int(year)):
                continue
            team_prefix = team['prefix_1'].upper()
            team_name = team['name']
            team_players_data = get_players_data(team_prefix, season, countries_mapping, teams_mapping, is_stubbed)
            data = [*data, *team_players_data]
            print("Data fetched for team : " + team_name + ' (' + team_prefix + ')')
            wait_random_duration()
        columns = [*list(OUTPUT_COLUMNS.values()), 'Leagues', 'Teams', 'Seasons']
        dataframe = pd.DataFrame(data, columns=columns)
        dataframe_ordered = dataframe[OUTPUT_COLUMNS_ORDERED]
        generate_csv_from_dataframe(dataframe_ordered, constant.BBREF_DATA_DIRECTORY, output_file, 'w', ',')
        print("Players generated !")
    print("All players generated !")


def get_players_data(team_prefix: str, season: str, countries_mapping: dict[str, str],
                     teams_mapping: dict[str, str], is_stubbed=False) -> list[list[str]]:
    players_data = []
    year = get_year_from_season(season)
    if not is_stubbed:
        url = BASKETBALL_REFERENCE_URL + '/teams/' + team_prefix + '/' + year + '.html'
        soup = get_soup(url)
    else:
        soup = get_stub_soup('stub_bbref_team')
    body = get_table_body(soup, 'div_roster')
    rows = body.select('tr')
    for key, row in enumerate(rows):
        first_cell = row.find('th', {"scope": "row"})
        value = full_strip(first_cell.text)
        player_data = [value]
        cells = row.findAll("td")
        for cell in cells:
            column = cell.attrs['data-stat']
            if column not in OUTPUT_COLUMNS:
                continue
            output_column = OUTPUT_COLUMNS[column]
            value = cell.text.strip()
            if output_column == 'DoB':
                value = datetime.strptime(value, '%B %d, %Y').date().strftime('%Y/%m/%d')
            if output_column == 'Positions':
                value = build_positions(value)
            if output_column == 'Nationality':
                if value.upper() == 'UK':
                    print("stop")
                value = countries_mapping[update_countries(value.upper())]
            player_data.append(full_strip(value))
        # complementary data
        player_data.append('NBA')  # league
        player_data.append(teams_mapping[team_prefix.lower()])  # team name
        player_data.append(season.replace('_', '-'))  # season
        players_data.append(player_data)
    return players_data


def build_positions(value: str) -> str:
    return '-'.join(list(map(lambda val: POSITION_LABELS[val.upper()], value.split('-'))))
