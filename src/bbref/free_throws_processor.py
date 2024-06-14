import csv
import os

import pandas as pd

from config.config import Environment, get_is_stubbed
from src.common.constant import BBREF_DATA_DIRECTORY, BASKETBALL_REFERENCE_URL, BBREF_GAME_LOGS_DATA_DIRECTORY, \
    NBA_TEAMS_FILE
from src.common.data_collector import get_soup, get_content_from_soup
from src.common.file_processor import generate_csv_from_dataframe, build_file_name
from src.common.stub import get_stub_soup
from src.common.utils import get_all_seasons_since, get_year_from_season, wait_random_duration, \
    does_franchise_exists_for_season, get_season_from_year

MINIMUM_GAMES = 5
DATA_COLUMNS = [
    'team',
    'season',
    'year',
    'ft_pct',
    'fta'
]


def collect_free_throws_from_seasons(min_year: str, max_year: str, environment: Environment):
    print("Collect free throws from year [" + min_year + "] to [" + max_year + "]")
    output_file: str = os.path.join(BBREF_DATA_DIRECTORY, 'free_throws_season.csv')
    seasons = get_all_seasons_since(int(min_year))
    is_stubbed = get_is_stubbed(environment)
    data = []
    for season in seasons:
        print("Collect free throws for season [" + season + "]")
        year = get_year_from_season(season)
        if is_stubbed:
            soup = get_stub_soup('stub_bbref_season')
        else:
            soup = get_soup(BASKETBALL_REFERENCE_URL + '/leagues/NBA_' + year + '.html')
        content = get_content_from_soup(soup, 'per_game-team', 'table', 'id')
        rows = content.select('tbody > tr')
        for row in rows:
            data_team = {"season": season, "year": year}
            team = row.select_one('td[data-stat="team"] > a').text
            data_team["team"] = team
            ft = row.select_one('td[data-stat="ft"]').text
            data_team["ft"] = ft
            fta = row.select_one('td[data-stat="fta"]').text
            data_team["fta"] = fta
            ft_pct = row.select_one('td[data-stat="ft_pct"]').text
            data_team["ft_pct"] = ft_pct
            data.append(data_team)
        wait_random_duration()
    dataframe = pd.DataFrame.from_records(data, columns=DATA_COLUMNS)
    generate_csv_from_dataframe(dataframe, BBREF_DATA_DIRECTORY, output_file)
    print("Data collected !")


def collect_free_throws_from_games(min_year: str, max_year: str):
    print("Collect free throws from year [" + min_year + "] to [" + max_year + "]")
    output_file: str = os.path.join(BBREF_DATA_DIRECTORY, 'free_throws_games.csv')
    data = []
    with open(NBA_TEAMS_FILE, mode='r', newline='') as csvfile:
        teams = list(csv.DictReader(csvfile, delimiter=','))
        for year in range(int(min_year), int(max_year) + 1):
            print('Compute free throws data for year [' + str(year) + ']')
            season = get_season_from_year(year)

            for team_iterator, team in enumerate(teams):
                if not does_franchise_exists_for_season(team, year):
                    continue
                game_logs_file: str = build_file_name(
                    BBREF_GAME_LOGS_DATA_DIRECTORY,
                    team['prefix_long'].replace('-', '_') + '_game_logs_',
                    '',
                    '.csv',
                    str(year)
                )
                with open(game_logs_file, mode='r', newline='') as csvfile:
                    game_logs = list(csv.DictReader(csvfile, delimiter=';'))
                    for game_log_iterator, game_log in enumerate(game_logs):
                        if game_log['Game type'] != 'regular_season':
                            break
                        data_team = {
                            "season": season,
                            "year": year,
                            "team": team['name'],
                            "ft": game_log['Team FT'],
                            "fta": game_log['Team FTA'],
                            "ft_pct": game_log['Team FT%']
                        }
                        data.append(data_team)
    dataframe = pd.DataFrame.from_records(data, columns=DATA_COLUMNS)
    generate_csv_from_dataframe(dataframe, BBREF_DATA_DIRECTORY, output_file)
    print("Data collected !")


def collect_free_throws_from_games_with_moving_average(min_year: str, max_year: str):
    print("Collect free throws from year [" + min_year + "] to [" + max_year + "]")
    output_file: str = os.path.join(BBREF_DATA_DIRECTORY, 'free_throws_games_moving_average.csv')
    data = []
    with open(NBA_TEAMS_FILE, mode='r', newline='') as csvfile:
        teams = list(csv.DictReader(csvfile, delimiter=','))
        for year in range(int(min_year), int(max_year) + 1):
            print('Compute free throws data for year [' + str(year) + ']')
            season = get_season_from_year(year)

            for team_iterator, team in enumerate(teams):
                if not does_franchise_exists_for_season(team, year):
                    continue
                game_logs_file: str = build_file_name(
                    BBREF_GAME_LOGS_DATA_DIRECTORY,
                    team['prefix_long'].replace('-', '_') + '_game_logs_',
                    '',
                    '.csv',
                    str(year)
                )
                with open(game_logs_file, mode='r', newline='') as csvfile:
                    game_logs = list(csv.DictReader(csvfile, delimiter=';'))
                    ft_list = []
                    for game_log_iterator, game_log in enumerate(game_logs):
                        ft_elt = {
                            'FT': game_log['Team FT'],
                            'FTA': game_log['Team FTA'],
                        }
                        ft_list.append(ft_elt)
                        if game_log['Game type'] != 'regular_season':
                            break
                        if len(ft_list) < MINIMUM_GAMES:
                            continue
                        ft_pct = ft_pct_last_games(ft_list)
                        data_team = {
                            "season": season,
                            "year": year,
                            "team": team['name'],
                            "ft_pct": ft_pct
                        }
                        ft_list.pop(0)
                        data.append(data_team)
    dataframe = pd.DataFrame.from_records(data, columns=DATA_COLUMNS)
    generate_csv_from_dataframe(dataframe, BBREF_DATA_DIRECTORY, output_file)
    print("Data collected !")


def ft_pct_last_games(ft_list):
    ft_total = 0
    fta_total = 0
    for elt in ft_list:
        ft_total += int(elt['FT'])
        fta_total += int(elt['FTA'])
    ft_pct = "{:.2f}".format(ft_total / fta_total)
    return ft_pct
