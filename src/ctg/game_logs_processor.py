import csv

import pandas as pd
from bs4 import Tag

from src.bbref.data_processor import get_rankings
from src.common import constant
from src.common.constant import CLEANING_THE_GLASS_DATA_DIRECTORY, NBA_TEAMS_FILE, BASKETBALL_REFERENCE_URL, \
    CLEANING_THE_GLASS_URL
from src.common.data_collector import get_content_from_soup, get_all_content_from_soup, get_soup
from src.common.file_processor import generate_csv_from_dataframe, generate_csv_from_list_dicts, build_file_name
from src.common.stub import get_stub_soup
from src.common.utils import wait_random_duration, does_franchise_exists_for_season
from config.config import Environment, get_ctg_identifiers, get_is_stubbed
from src.ctg.data_processor import get_columns, get_rows


def generate_game_logs(min_year: str, max_year: str, environment: Environment):
    print('Generate game logs from year [' + min_year + '] to year [' + max_year + ']')
    ctg_identifiers = get_ctg_identifiers(environment)
    is_stubbed = get_is_stubbed(environment)
    with open(NBA_TEAMS_FILE, mode='r', newline='') as csvfile:
        teams = list(csv.DictReader(csvfile, delimiter=','))
        for year in range(int(min_year), int(max_year) + 1):
            print('Generate game logs for year [' + str(year) + ']')
            if not is_stubbed:
                url_rankings = BASKETBALL_REFERENCE_URL + '/leagues/NBA_' + str(year) + '_standings.html'
                soup_ranking = get_soup(url_rankings)
            else:
                soup_ranking = get_stub_soup('stub_bbref_game_logs')
            ranking_html: Tag = get_content_from_soup(soup_ranking, 'expanded_standings', 'table', 'id')
            ranking_data: dict[str, str] = get_rankings(ranking_html, teams)

            for team_iterator, team in enumerate(teams):
                if (not does_franchise_exists_for_season(team, year)) or team['generated'] == '1':
                    continue
                print('Team : ' + team['name'])
                if not is_stubbed:
                    url = CLEANING_THE_GLASS_URL + '/stats/team/' + team['id'] + '/gamelogs?season=' + str(year - 1)
                    soup = get_soup(url, dict(
                        wordpress_logged_in_cfb45adfd4102bd74a046b78d76db012=ctg_identifiers['cookieValue'],
                        sessionid=ctg_identifiers['sessionId']
                    ))
                else:
                    soup = get_stub_soup('stub_ctg_game_logs')
                sections = get_all_content_from_soup(soup, 'stat_table_container', 'div', 'class')
                for section in sections:
                    table_id = section.findChild('table').attrs['id']
                    output_file: str = build_file_name(
                        CLEANING_THE_GLASS_DATA_DIRECTORY,
                        team['prefix_long'].replace('-', '_') + '_' + table_id.replace('team_', '') + '_',
                        '',
                        '.csv',
                        str(year)
                    )
                    data = get_content_from_soup(section, table_id, 'table', 'id')
                    data_columns = get_columns(data)
                    data_rows = get_rows(data, data_columns, ranking_data)
                    dataframe = pd.DataFrame.from_records(data_rows, columns=data_columns)
                    generate_csv_from_dataframe(dataframe, CLEANING_THE_GLASS_DATA_DIRECTORY, output_file)
                if year == max_year:
                    teams[team_iterator]['generated'] = 1
                wait_random_duration()
    generate_csv_from_list_dicts(teams, constant.BBREF_DATA_DIRECTORY, NBA_TEAMS_FILE, 'w', ',')
