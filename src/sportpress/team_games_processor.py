import csv
import os
from datetime import datetime
from os.path import exists

import pandas as pd
from bs4 import Tag

from src.common.constant import BASKETBALL_REFERENCE_URL, BBREF_DATA_DIRECTORY
from src.common.data_collector import get_soup, get_table_body
from src.common.file_processor import generate_csv_from_dataframe, get_teams_mapping, generate_csv_from_list_dicts
from src.common.stub import get_stub_soup
from src.common.utils import wait_random_duration, full_strip, get_all_seasons_since
from config.config import Environment, get_is_stubbed
from src.sportpress.team_calendar_processor import generate_sportpress_calendar_for_season

COLUMNS_MAPPING = {'player': 'Players', 'mp': 'MP', 'pts': 'PTS', 'ast': 'AST', 'stl': 'STL',
                   'blk': 'BLK', 'fg': 'FGM', 'fga': 'FGA', 'fg_pct': 'FG%', 'fg3': '3PM', 'fg3a': '3PA',
                   'fg3_pct': '3P%', 'ft': 'FTM', 'fta': 'FTA', 'ft_pct': 'FT%', 'orb': 'OREB',
                   'drb': 'DREB', 'tov': 'TOV', 'pf': 'PF', 'plus_minus': '+/-'}
OUTPUT_COLUMNS = ['Players', 'Teams', 'Results', 'Outcome', 'Date', 'Time', 'Venue', 'MP', 'FGM', 'FGA', 'FG%', '3PM',
                  '3PA', '3P%', 'FTM', 'FTA', 'FT%', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS',
                  '+/-']
OUTPUT_COLUMNS_ORDERED = ['Date', 'Time', 'Venue', 'Teams', 'Results', 'Outcome', 'Players', 'MP', 'PTS', 'REB',
                          'AST', 'STL', 'BLK', 'FGM', 'FGA', 'FG%', '3PM', '3PA', '3P%', 'FTM', 'FTA', 'FT%', 'OREB',
                          'DREB', 'TOV', 'PF', '+/-']


def generate_games(team_prefix: str, year: str, environment=Environment.LOCAL):
    print('Generate games for team [' + team_prefix + '] from year [' + year + ']')
    seasons = get_all_seasons_since(int(year))
    print(seasons)
    is_stubbed = get_is_stubbed(environment)
    for season in seasons:
        print('Generate games for season [' + season + ']')
        input_file = os.path.join(BBREF_DATA_DIRECTORY, team_prefix + '_calendar_' + season + '_sportpress.csv')
        teams_mapping = get_teams_mapping('name', 'prefix_1')
        if not os.path.exists(input_file):
            generate_sportpress_calendar_for_season(season, team_prefix, environment)
            if not os.path.exists(input_file):
                raise Exception('Missing calendar file', input_file)
        nb_games = 0
        part_number = find_current_part_number(season, team_prefix)
        output_rows = []
        games_data = []
        with open(input_file, newline='') as input_file_csv:
            input_rows: list[dict[str, str]] = list(csv.DictReader(input_file_csv, delimiter=','))
            for input_row in input_rows:
                now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                if datetime.strptime(input_row['Date'], "%Y/%m/%d") >= now:
                    print("Game not yet played at this date : " +
                          input_row['Away'] + ' @ ' + input_row['Home'] + ' on ' + input_row['Date'])
                    input_row['Generated'] = '0'
                    output_rows.append(input_row)
                    continue
                if 'Generated' in input_row and input_row['Generated'] == '1':
                    print('Game already generated at this date : ' + input_row['Away'] + ' @ ' +
                          input_row['Home'] + ' on ' + input_row['Date'])
                    output_rows.append(input_row)
                    continue
                game_data = get_game_data(input_row, teams_mapping, is_stubbed)
                games_data += game_data
                print('Boxscore generated : ' + input_row['Away'] + ' @ ' + input_row['Home'] + ' on ' +
                      input_row['Date'])
                nb_games += 1
                if nb_games % 20 == 0:
                    output_file = os.path.join(
                        BBREF_DATA_DIRECTORY,
                        team_prefix + '_games_' + season + 'sportpress_part' + str(part_number) + '.csv'
                    )
                    dataframe = pd.DataFrame(games_data, columns=OUTPUT_COLUMNS)
                    dataframe_ordered = dataframe[OUTPUT_COLUMNS_ORDERED]
                    generate_csv_from_dataframe(dataframe_ordered, BBREF_DATA_DIRECTORY, output_file, 'w', ',')
                    part_number += 1
                    games_data = []
                wait_random_duration()
                input_row['Generated'] = '1'
                output_rows.append(input_row)
            output_file = os.path.join(
                BBREF_DATA_DIRECTORY,
                team_prefix + '_games_' + season + 'sportpress_part' + str(part_number) + '.csv'
            )
            if not games_data:
                print("No game generated")
                break
            dataframe = pd.DataFrame(games_data, columns=OUTPUT_COLUMNS)
            dataframe_ordered = dataframe[OUTPUT_COLUMNS_ORDERED]
            generate_csv_from_dataframe(dataframe_ordered, BBREF_DATA_DIRECTORY, output_file, 'w', ',')
            generate_csv_from_list_dicts(output_rows, BBREF_DATA_DIRECTORY, input_file, 'w', ',')
        print('Games generated for season : ' + season)
    print('All games generated !')


def find_current_part_number(season: str, team: str) -> int:
    part = 1
    while exists(os.path.join(BBREF_DATA_DIRECTORY, team + '_season_' + season + '_part' + str(part) + '.csv')):
        part += 1
    return part


def get_game_data(input_row: dict[str, str], teams_mapping: dict[str, str], is_stubbed=False) -> list[list[str]]:
    # score
    home_team_prefix = teams_mapping[input_row['Home']].upper()
    date = input_row['Date'].replace('/', '')
    if not is_stubbed:
        url = BASKETBALL_REFERENCE_URL + '/boxscores/' + date + '0' + home_team_prefix + '.html'
        soup = get_soup(url)
    else:
        soup = get_stub_soup('stub_bbref_boxscore')
    score_table = get_table_body(soup, 'div_line_score')
    if score_table is None:
        print("No data found for this game")
        return []
    results = build_results(score_table)
    # home
    table_id = 'div_box-' + home_team_prefix + '-game-basic'
    boxscore_table = get_table_body(soup, table_id)
    boxscore_home = build_boxscore(boxscore_table, results['Home'], input_row, True)
    # away
    away_team_prefix = teams_mapping[input_row['Away']].upper()
    table_id = 'div_box-' + away_team_prefix + '-game-basic'
    boxscore_table = get_table_body(soup, table_id)
    boxscore_away = build_boxscore(boxscore_table, results['Away'], input_row, False)
    return boxscore_home + boxscore_away


def build_boxscore(boxscore_table: Tag, results_outcome: dict[str, str],
                   calendar: dict[str, str], is_home: bool) -> list[list[str]]:
    rows = boxscore_table.select('tr')
    boxscore_columns = {'REB': 'REB'}
    all_data = []
    for index, row in enumerate(rows):
        first_cell = row.find('th', {"scope": "row"})
        if first_cell is None:
            continue
        data = [full_strip(first_cell.text)]
        team = calendar['Home'] if is_home else calendar['Away']
        data.append(team if index == 0 else '')  # teams
        data.append(results_outcome['result'] if index == 0 else '')  # results
        data.append(results_outcome['outcome'] if index == 0 else '')  # outcome
        data.append(calendar['Date'] if is_home and index == 0 else '')  # date
        data.append(calendar['Time'] if is_home and index == 0 else '')  # time
        data.append(calendar['Venue'] if is_home and index == 0 else '')  # venue
        cells = row.findAll("td")
        if len(cells) == 1:  # player did not play
            for _ in boxscore_columns:
                data.append('')
            continue
        total_rebounds = 0
        for cell in cells:
            column = cell.attrs['data-stat']
            if column not in COLUMNS_MAPPING:
                continue
            output_column = COLUMNS_MAPPING[column]
            if column not in boxscore_columns:
                boxscore_columns[column] = output_column
            value = full_strip(cell.text)
            data.append(value)
            if output_column in ['OREB', 'DREB']:
                total_rebounds += int(value)
        data.append(str(total_rebounds))  # reb
        all_data.append(data)
    return all_data


def build_results(score_table: Tag):
    rows = score_table.find_all('tr')
    data = {}
    outcome = {}
    if len(rows) != 2:
        raise Exception('Invalid columns number for score')
    for index, row in enumerate(rows):
        team = 'Away' if index == 0 else 'Home'
        cells = row.findAll("td")
        results = []
        for cell in cells:
            data_stat = cell.attrs['data-stat']
            if data_stat in ['1', '2', '3', '4', '1OT']:
                results.append(cell.text.strip())
            if data_stat in ['2OT', '3OT', '4OT', '5OT']:
                results[4] = str(int(results[4]) + int(cell.text.strip()))
            elif data_stat == 'T':
                outcome[team] = cell.find("strong").text.strip()
        if len(results) == 4:  # no overtime
            results.append('0')
        results.append(outcome[team])
        result: str = '|'.join(results)
        data[team] = {'result': result}
    data['Home']['outcome'] = 'Win' if int(outcome['Away']) < int(outcome['Home']) else 'Loss'
    data['Away']['outcome'] = 'Win' if int(outcome['Home']) < int(outcome['Away']) else 'Loss'
    return data
