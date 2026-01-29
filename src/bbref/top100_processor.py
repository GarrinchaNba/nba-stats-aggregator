import csv
import os
import re
from datetime import datetime
from time import sleep
from typing import Any

import pandas as pd
import requests
from bs4 import Tag, BeautifulSoup
from dateutil.relativedelta import relativedelta

from config.config import Environment, get_is_stubbed
from src.common.constant import BASKETLAB_FILE_BASE, BASKETLAB_COMPLETE_FILE_BASE, TOP100_DATA_DIRECTORY, \
    BASKETBALL_REFERENCE_URL, TOP100_FILE, COMMON_DATA_DIRECTORY
from src.common.data_collector import get_content_from_soup, get_url_response, get_soup_from_response
from src.common.data_collector import get_table_body
from src.common.file_processor import generate_csv_from_dataframe, build_top100_csv_file_name, \
    generate_csv_from_list_dicts, build_file_name
from src.common.stub import get_stub_soup
from src.common.utils import remove_accents, wait_random_duration, Duration, matrix_to_list

BATCH_SIZE = 10

MAX_TRIES_PLAYER_SEARCH = 7
PLAYER_NAME_FIX = {
    'capela': 'ca',
    'ntilikina': 'la'
}
LIST_TABLE_IDS = ['advanced', 'adj_shooting', 'per_poss', 'per_game_stats', 'pbp_stats', 'per_minute_stats', 'totals_stats']
LIST_TABLE_IDS_PLAYOFFS = ['advanced', 'per_poss', 'per_game_stats', 'pbp_stats', 'per_minute_stats', 'totals_stats']
OUTPUT_COLUMNS = ['last_name', 'first_name', 'player_id', 'season']


def generate_top100(min_year: str, max_year: str, environment: Environment):
    input_file: str = build_file_name(COMMON_DATA_DIRECTORY, TOP100_FILE, BASKETLAB_FILE_BASE, '.csv', min_year, max_year)
    if not os.path.exists(input_file):
        raise Exception('Missing input file', input_file)

    output_file: str = build_top100_csv_file_name(BASKETLAB_COMPLETE_FILE_BASE, min_year, max_year)
    is_stubbed = get_is_stubbed(environment)
    all_columns: dict[str, list[str]] = {}
    player_seasons_data = []

    with (open(input_file, newline='') as csvfile):
        reader: list[dict[str, str]] = list(csv.DictReader(csvfile, delimiter=';'))
        exported_players: list[dict[str, str]] = []
        count = 1
        for player in reader:
            last_name = player['last_name'].lower()
            first_name = player['first_name'].lower()
            print('Player : ' + first_name + ' ' + last_name)
            if player['exported'] == 'Y':
                print("##### Player already exported : " + first_name + ' ' + last_name)
                exported_players.append(player)
                continue
            player_data, soup = search_player(first_name, last_name, max_year, is_stubbed)
            player |= player_data
            if not soup:
                print("!!!!! Unknown player : " + first_name + ' ' + last_name)
                exported_players.append(player)
                continue
            years = get_years(soup, min_year, max_year)
            base_data = [
                player['last_name'].lower().strip(),
                player['first_name'].lower().strip(),
                player['player_id']
            ]
            for year in years:
                season = str(year - 1) + '-' + str(year)
                player_season_data = [season]
                for table_id in LIST_TABLE_IDS:
                    regular_season_table = get_content_from_soup(soup, 'div_' + table_id)
                    if table_id not in all_columns:
                        regular_columns = get_columns(regular_season_table, table_id, str(year))
                        if len(regular_columns) == 1:
                            skipped_reason = build_players_data(regular_season_table, regular_columns, table_id, year)
                            print("Skip season " + season + " : " + skipped_reason[0])
                            player_season_data = []
                            break
                        all_columns[table_id] = regular_columns
                    regular_data = build_players_data(regular_season_table, all_columns[table_id], table_id, year)
                    player_season_data += regular_data
                    if table_id not in LIST_TABLE_IDS_PLAYOFFS:
                        continue
                    if table_id + '_post' not in all_columns:
                        playoff_columns = [column + '_post' for column in all_columns[table_id]]
                        all_columns[table_id + '_post'] = playoff_columns
                    playoffs_table = get_content_from_soup(soup, 'div_' + table_id + '_post')
                    playoffs_data = build_players_data(playoffs_table, all_columns[table_id+ '_post'],
                                                       table_id, year, True)
                    player_season_data += playoffs_data
                player_seasons_data.append(base_data + player_season_data)

            print("Export complete !")
            player: dict[str, str] = {
                'rank': player['rank'],
                'player_id': player['player_id'],
                'last_name': player['last_name'],
                'first_name': player['first_name'],
                'exported': 'Y'
            }
            exported_players.append(player)
            if count % BATCH_SIZE == 0:
                last_players = [exported_player['player_id'] for exported_player in exported_players[-BATCH_SIZE:]]
                player_seasons_data_batch = [player_season_data for player_season_data in player_seasons_data if player_season_data[2] in last_players]
                columns_dataframe = OUTPUT_COLUMNS + matrix_to_list(list(all_columns.values()))
                player_seasons_dataframe = pd.DataFrame(player_seasons_data_batch, columns=columns_dataframe)
                if count == BATCH_SIZE and not os.path.exists(output_file):
                    mode = 'w'
                else:
                    mode = 'a'
                generate_csv_from_dataframe(player_seasons_dataframe, TOP100_DATA_DIRECTORY, output_file, mode, ';',
                                            False)
            count += 1
            wait_random_duration(Duration.MEDIUM)
        LAST_BATCH_SIZE = (count - 1) % BATCH_SIZE
        last_players = [exported_player['player_id'] for exported_player in exported_players[-LAST_BATCH_SIZE:]]
        player_seasons_data_batch = [player_season_data for player_season_data in player_seasons_data if
                                     player_season_data[2] in last_players]
        columns_dataframe = OUTPUT_COLUMNS + matrix_to_list(list(all_columns.values()))
        player_seasons_dataframe = pd.DataFrame(player_seasons_data_batch, columns=columns_dataframe)
        if count < BATCH_SIZE and not os.path.exists(output_file):
            mode = 'w'
        else:
            mode = 'a'
        generate_csv_from_dataframe(player_seasons_dataframe, TOP100_DATA_DIRECTORY, output_file, mode)
        generate_csv_from_list_dicts(exported_players, TOP100_DATA_DIRECTORY, input_file, 'w')

        if not os.path.exists(output_file):
            print("Export player data failed")
        else:
            print("Export player data successful")


def search_player(first_name: str, last_name: str, year: str, is_stubbed: bool) -> tuple[dict[str, str | Any], BeautifulSoup] | None:
    count = 1
    base_url = BASKETBALL_REFERENCE_URL + '/players'
    while count < MAX_TRIES_PLAYER_SEARCH:
        player_id = build_player_id(last_name, first_name, count)
        url = base_url + '/' + last_name[:1] + '/' + player_id + '.html'
        if url_ok(url):
            response = get_url_response(url)
            soup_info = get_soup_from_response(response, True)
            info = get_content_from_soup(soup_info, 'info', 'div')
            if is_stubbed:
                soup = get_stub_soup('stub_bbref_player')
            else:
                soup = get_soup_from_response(response, False)
            full_name_raw = info.find('h1').findChild('span').text
            full_name = remove_accents(full_name_raw, 'NFKD')
            birthdate_raw = info.find('span', {'id': 'necro-birth'})
            if birthdate_raw is not None:
                birthdate_raw = birthdate_raw.attrs['data-birth']
                birthdate = datetime.strptime(birthdate_raw, '%Y-%m-%d')
                max_birthday = datetime(int(year), 1, 1) - relativedelta(years=45)
                if (full_name == first_name + ' ' + last_name) and birthdate > max_birthday:
                    player_data = {
                        'player_id': player_id
                    }
                    print("#############################################")
                    print("##### Player found : " + full_name)
                    print("#############################################")
                    return player_data, soup
            print("Not the expected player : " + full_name)
        count += 1
        wait_random_duration()
    return None


def build_players_data(table: Tag, columns: list[str], table_id: str, year: int, playoffs = False) -> list[str]:
    data_season = []
    row = None
    if table:
        if playoffs:
            id = table_id + '_post' + '.' + str(year)
        else:
            id = table_id + '.' + str(year)
        row = table.find('tr', {'id': id})
    for column in columns:
        value = '0'
        if row:
            data_stat = column.replace(table_id + '_', '')
            if playoffs:
                data_stat = data_stat.replace('_post', '')
            cell = row.find("td", {'data-stat': data_stat})
            if cell:
                value = cell.text.strip()
        data_season.append(value)
    return data_season


def get_years(soup: BeautifulSoup, min_year: str, max_year: str) -> list[int]:
    table = get_table_body(soup, 'div_per_game_stats')
    years = []
    rows = table.find_all('tr')
    for row in rows:
        if not row.has_attr('id'):
            continue
        year = int(row['id'].split('.')[1])
        if year < int(min_year) or year > int(max_year):
            continue
        if year not in years:
            years.append(year)
    return years


def get_columns(table: Tag, table_id, year: str) -> list[str]:
    columns = []
    row = table.find('tr', {'id': table_id + '.' + year})
    cells = row.findAll("td")
    for cell in cells:
        data_stat = cell.attrs['data-stat']
        if data_stat in ['DUMMY', 'trp_dbl', '']:
            continue
        columns.append(table_id + '_' + data_stat)
    return columns


def url_ok(test_url: str):
    print('url : ' + test_url)
    r = requests.head(test_url, headers={'User-Agent': 'Mozilla/5.0'})
    if r.status_code == 429:
        print("Retry after : " + r.headers["Retry-After"])
        sleep(int(r.headers["Retry-After"]))
    return r.status_code == 200


def build_player_id(last_name: str, first_name: str, cpt: int):
    last_name_url = re.sub("'|-", "", last_name)
    if last_name in PLAYER_NAME_FIX:
        first_name_url = PLAYER_NAME_FIX[last_name]
    else:
        first_name_url = re.sub("'|-", "", first_name)
    return last_name_url[:5] + first_name_url[:2] + '0' + str(cpt)


def get_seasons_by_player_id_from_file(data: list[dict[str, str]]) -> dict[str, list[str]]:
    seasons_by_player_id: dict[str, list[str]] = {}
    for row in data:
        player_id: str = row['player_id']
        if player_id not in seasons_by_player_id:
            seasons_by_player_id[player_id] = []
        season: str = row['season']
        if season not in seasons_by_player_id[player_id]:
            seasons_by_player_id[player_id].append(season)
    return seasons_by_player_id


def add_data(data: dict[str, list[str]], output_column: str, value: str) -> None:
    if output_column in data:
        data[output_column].append(value)
    else:
        data[output_column] = [value]
