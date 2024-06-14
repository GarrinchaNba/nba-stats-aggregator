import csv
import os.path

import pandas as pd
from bs4 import Tag

from config.config import Environment, get_is_stubbed
from src.bbref.data_processor import get_rankings, get_columns, get_rows, GameType
from src.common import constant
from src.common.constant import CLEANING_THE_GLASS_DATA_DIRECTORY, NBA_TEAMS_FILE, BASKETBALL_REFERENCE_URL, \
    BBREF_DATA_DIRECTORY, BBREF_GAME_LOGS_DATA_DIRECTORY
from src.common.data_collector import get_content_from_soup, get_all_content_from_soup, get_soup
from src.common.file_processor import generate_csv_from_dataframe, generate_csv_from_list_dicts, build_file_name
from src.common.stub import get_stub_soup
from src.common.utils import wait_random_duration, does_franchise_exists_for_season


def generate_game_logs(min_year: str, max_year: str, environment: Environment):
    print('Generate game logs from year [' + min_year + '] to year [' + max_year + ']')
    is_stubbed = get_is_stubbed(environment)
    with open(NBA_TEAMS_FILE, mode='r', newline='') as csvfile:
        teams = list(csv.DictReader(csvfile, delimiter=','))
        for year in range(int(min_year), int(max_year) + 1):
            print('Generate game logs for year [' + str(year) + ']')
            if not is_stubbed:
                url_rankings = BASKETBALL_REFERENCE_URL + '/leagues/NBA_' + str(year) + '_standings.html'
                soup_ranking = get_soup(url_rankings)
            else:
                soup_ranking = get_stub_soup('stub_bbref_standings')
            ranking_html: Tag = get_content_from_soup(soup_ranking, 'expanded_standings', 'table', 'id')
            ranking_data: dict[str, str] = get_rankings(ranking_html, teams, 'prefix_1')

            for team_iterator, team in enumerate(teams):
                if (not does_franchise_exists_for_season(team, year)) or team['generated'] == '1':
                    continue
                print('Team : ' + team['name'])
                if not is_stubbed:
                    url = BASKETBALL_REFERENCE_URL + '/teams/' + team['prefix_1'] + '/' + str(year) + '/gamelog'
                    soup = get_soup(url)
                else:
                    soup = get_stub_soup('stub_bbref_game_logs')
                output_file: str = build_file_name(
                    BBREF_GAME_LOGS_DATA_DIRECTORY,
                    team['prefix_long'].replace('-', '_') + '_game_logs_',
                    '',
                    '.csv',
                    str(year)
                )
                data = get_content_from_soup(soup, 'tgl_basic', 'table', 'id')
                data_columns = get_columns(data)
                data_rows = get_rows(data, data_columns, ranking_data, GameType.REGULAR)
                data = get_content_from_soup(soup, 'tgl_basic_playoffs', 'table', 'id')
                if data is not None:
                    data_rows_playoffs = get_rows(data, data_columns, ranking_data, GameType.PLAYOFFS)
                    data_rows += data_rows_playoffs
                columns = [column for column in data_columns if column != '']
                dataframe = pd.DataFrame.from_records(data_rows, columns=columns)
                generate_csv_from_dataframe(dataframe, BBREF_GAME_LOGS_DATA_DIRECTORY, output_file)
                # if year == max_year:
                #     teams[team_iterator]['generated'] = 1
                wait_random_duration()
    generate_csv_from_list_dicts(teams, constant.BBREF_DATA_DIRECTORY, NBA_TEAMS_FILE, 'w', ',')
