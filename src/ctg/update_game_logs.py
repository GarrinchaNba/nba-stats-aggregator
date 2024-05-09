import csv
import shutil

from bs4 import Tag

from src.bbref.data_processor import get_rankings
from src.common import constant
from src.common.constant import CLEANING_THE_GLASS_DATA_DIRECTORY, NBA_TEAMS_FILE
from src.common.data_collector import get_content_from_soup, get_soup
from src.common.file_processor import build_file_name, generate_csv_from_list_dicts
from src.common.utils import does_franchise_exists_for_season
from config.config import get_config

print("start...")
min_year = 2006
max_year = 2007

config_data = get_config('local.yaml')
sections = [
    'game_log_four_factors',
    'game_log_offense_halfcourt',
    'game_log_offense_transition',
    'game_log_offense_shooting_accuracy',
    'game_log_offense_shooting_frequency',
    'game_log_defense_halfcourt',
    'game_log_defense_transition',
    'game_log_defense_shooting_accuracy',
    'game_log_defense_shooting_frequency',
]

with open(NBA_TEAMS_FILE, mode='r', newline='') as csvfile:
    teams = list(csv.DictReader(csvfile, delimiter=';'))
    for year in range(min_year, max_year + 1):
        print('year : ' + str(year))
        url_rankings = 'https://www.basketball-reference.com/leagues/NBA_' + str(year) + '_standings.html'
        soup_ranking = get_soup(url_rankings)
        # soup_ranking = BeautifulSoup(open("./scratch_bbref.html", encoding="utf8"), "html.parser")
        ranking_html: Tag = get_content_from_soup(soup_ranking, 'expanded_standings', 'table', 'id')
        ranking_data: dict[str, str] = get_rankings(ranking_html, teams)

        for team_iterator, team in enumerate(teams):
            if (not does_franchise_exists_for_season(team, year)) or team['generated'] == '1':
                continue
            for section in sections:
                print('Team : ' + team['name'])
                input_file: str = build_file_name(
                    CLEANING_THE_GLASS_DATA_DIRECTORY,
                    team['prefix_long'].replace('-', '_') + '_' + section.replace('team_', '') + '_',
                    '',
                    '.csv',
                    str(year)
                )
                with open(input_file, mode='r', newline='') as csv_input, open('temp.csv', 'w') as csv_output:
                    game_logs_reader = csv.DictReader(csv_input, delimiter=';')
                    game_logs_writer = csv.DictWriter(csv_output, delimiter=';', fieldnames=game_logs_reader.fieldnames)
                    game_logs_writer.writeheader()
                    for game_log in list(game_logs_reader):
                        count = 1
                        for name, win_loss_pct in ranking_data.items():
                            if name == game_log['Opp'].lower():
                                game_log['Opp rank'] = count
                                game_log['Opp win%'] = win_loss_pct
                            count += 1
                        game_logs_writer.writerow(game_log)
                shutil.move(csv_output.name, input_file)
generate_csv_from_list_dicts(teams, constant.COMMON_DATA_DIRECTORY, NBA_TEAMS_FILE, 'w', ';')
