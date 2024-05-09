import csv
import os.path

import pandas as pd

from config.config import Environment
from src.common.constant import CLEANING_THE_GLASS_DATA_DIRECTORY, NBA_TEAMS_FILE
from src.common.file_processor import generate_csv_from_dataframe
from src.common.utils import get_season_from_year, does_franchise_exists_for_season

GAME_LOG_FILE = '_game_log_'
data_columns = [
    'team',
    'season',
    'transition freq playoffs',
    'transition freq regular all',
    'transition freq regular best',
    'transition diff all',
    'transition diff best',
    'halfcourt freq playoffs',
    'halfcourt freq regular all',
    'halfcourt freq regular best'
]


def compute_transitions_data(min_year: str, max_year: str, environment: Environment):
    print('Compute transitions data from year [' + min_year + '] to year [' + max_year + ']')
    data_rows = []
    output_file: str = 'transitions.csv'
    with open(NBA_TEAMS_FILE, mode='r', newline='') as csvfile:
        teams = list(csv.DictReader(csvfile, delimiter=','))
        for year in range(int(min_year), int(max_year) + 1):
            print('Compute transitions data for year [' + str(year) + ']')

            for team_iterator, team in enumerate(teams):
                if (not does_franchise_exists_for_season(team, year)):
                    continue
                print('Team : ' + team['name'])
                data_row = {'team': team['name'], 'season': get_season_from_year(year, '-')}
                team_name = team['prefix_long'].replace('-', '_')
                file_type = 'offense_transition'
                file_name = get_file_name(file_type, team_name, year)
                transition_file = os.path.join(CLEANING_THE_GLASS_DATA_DIRECTORY, file_name)
                with open(transition_file, mode='r', newline='') as csvfile:
                    transition_game_logs = list(csv.DictReader(csvfile, delimiter=';'))
                    transition_frequency_playoffs = 0
                    transition_frequency_regular_all = 0
                    transition_frequency_regular_best = 0
                    count_games_playoffs = 0
                    count_games_regular_all = 0
                    count_games_regular_best = 0
                    for transition_game_log_iterator, transition_game_log in enumerate(transition_game_logs):
                        frequency = get_transition_frequency(transition_game_log)
                        if frequency is None:
                            continue
                        if transition_game_log['Game type'] == 'playoffs':
                            transition_frequency_playoffs += frequency
                            count_games_playoffs += 1
                        else:
                            transition_frequency_regular_all += frequency
                            count_games_regular_all += 1
                            if float(transition_game_log['Opp win%']) >= 0.5:
                                transition_frequency_regular_best += frequency
                                count_games_regular_best += 1
                    data_row['transition freq playoffs'] = compute_ratio(transition_frequency_playoffs,
                                                                         count_games_playoffs)
                    data_row['transition freq regular all'] = compute_ratio(transition_frequency_regular_all,
                                                                           count_games_regular_all)
                    data_row['transition freq regular best'] = compute_ratio(transition_frequency_regular_best,
                                                                             count_games_regular_best)
                    data_row['transition diff all'] = compute_ratio_diff(count_games_playoffs, count_games_regular_all,
                                                                         transition_frequency_playoffs,
                                                                         transition_frequency_regular_all)
                    data_row['transition diff best'] = compute_ratio_diff(count_games_playoffs,
                                                                          count_games_regular_best,
                                                                          transition_frequency_playoffs,
                                                                          transition_frequency_regular_best)
                file_type = 'offense_halfcourt'
                file_name = get_file_name(file_type, team_name, year)
                halfcourt_file = os.path.join(CLEANING_THE_GLASS_DATA_DIRECTORY, file_name)
                with open(halfcourt_file, mode='r', newline='') as csvfile:
                    halfcourt_game_logs = list(csv.DictReader(csvfile, delimiter=';'))
                    halfcourt_frequency_playoffs = 0
                    halfcourt_frequency_regular_all = 0
                    halfcourt_frequency_regular_best = 0
                    count_games_playoffs = 0
                    count_games_regular_all = 0
                    count_games_regular_best = 0
                    for halfcourt_game_log_iterator, halfcourt_game_log in enumerate(halfcourt_game_logs):
                        frequency = get_halfcourt_frequency(halfcourt_game_log)
                        if frequency is None:
                            continue
                        if halfcourt_game_log['Game type'] == 'playoffs':
                            halfcourt_frequency_playoffs += frequency
                            count_games_playoffs += 1
                        else:
                            halfcourt_frequency_regular_all += frequency
                            count_games_regular_all += 1
                            if float(halfcourt_game_log['Opp win%']) >= 0.5:
                                halfcourt_frequency_regular_best += frequency
                                count_games_regular_best += 1
                    data_row['halfcourt freq playoffs'] = compute_ratio(halfcourt_frequency_playoffs,
                                                                        count_games_playoffs)
                    data_row['halfcourt freq regular all'] = compute_ratio(halfcourt_frequency_regular_all,
                                                                           count_games_regular_all)
                    data_row['halfcourt freq regular best'] = compute_ratio(halfcourt_frequency_regular_best,
                                                                            count_games_regular_best)
                    if data_row['transition freq playoffs'] != '':
                        data_rows.append(data_row)
    dataframe = pd.DataFrame.from_records(data_rows, columns=data_columns)
    generate_csv_from_dataframe(dataframe, CLEANING_THE_GLASS_DATA_DIRECTORY, output_file)


def compute_ratio_diff(count_playoffs, count_regular, frequency_playoffs, frequency_regular) -> str:
    if (count_playoffs < 4):
        return ''
    value = (frequency_playoffs / count_playoffs) - (frequency_regular / count_regular)
    return "{:.2f}".format(value)


def compute_ratio(frequency, count_games) -> str:
    if (count_games < 4):
        return ''
    value = frequency / count_games
    return "{:.2f}".format(value)


def get_transition_frequency(game_log) -> float | None:
    return get_frequency(game_log, 'All Transition Freq #')


def get_halfcourt_frequency(game_log) -> float | None:
    return get_frequency(game_log, 'Halfcourt % of Plays #')


def get_frequency(game_log, field) -> float | None:
    value = game_log[field]
    if value == '':
        return None
    return float(value.replace('%', ''))


def get_file_name(file_type, team_name, year):
    return team_name + GAME_LOG_FILE + file_type + '_' + str(year) + '.csv'
