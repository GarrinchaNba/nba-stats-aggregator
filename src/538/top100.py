import csv
import os
import sys

from src.common.constant import FIVETHIRTYEIGHT_DATA_DIRECTORY, BASKETLAB_COMPLETE_FILE_BASE, \
    BASKETLAB_WITH_RAPTORS_FILE
from src.common.file_processor import generate_csv_from_list_dicts, build_top100_csv_file_name
from src.common.utils import build_years

min_year = sys.argv[1]
max_year = sys.argv[2]
name = build_years(min_year, max_year)

if int(min_year) >= 2023:
    print("No RAPTOR after 2022")
    exit(0)

input_file_basketlab: str = build_top100_csv_file_name(BASKETLAB_COMPLETE_FILE_BASE, min_year, max_year)
input_file_538: str = os.path.join(FIVETHIRTYEIGHT_DATA_DIRECTORY, 'historical_RAPTOR_by_player.csv')
output_file: str = build_top100_csv_file_name(BASKETLAB_WITH_RAPTORS_FILE, min_year, max_year)
columns_538 = ['raptor_offense', 'raptor_defense', 'raptor_total', 'war_total', 'war_reg_season', 'war_playoffs',
               'predator_offense', 'predator_defense', 'predator_total', 'pace_impact']

rows_top100_with_538: list[dict[str, str]] = []
seasons_by_player_id: dict[dict[dict[str, str]]] = {}
with open(input_file_basketlab, newline='') as csvfile_basketlab:
    rows_top100 = csv.DictReader(csvfile_basketlab, delimiter=';')
    with open(input_file_538, newline='') as csvfile_538:
        rows_538 = csv.DictReader(csvfile_538, delimiter=',')
        for row_top100 in rows_top100:
            player_id = row_top100['player_id']
            player_name = row_top100['first_name'] + ' ' + row_top100['last_name']
            player_season = row_top100['season'].split('-')[1]
            print("#################################################################################")
            print("##### Processing player " + player_name + " for season " + row_top100['season'])
            print("#################################################################################")
            if player_id not in seasons_by_player_id:
                player_found = False
                for row_538 in rows_538:
                    player_id_538 = row_538['player_id']
                    if player_id != player_id_538 and player_found:
                        break
                    player_found = player_id == player_id_538
                    player_season_538 = row_538['season']
                    if player_id_538 not in seasons_by_player_id:
                        seasons_by_player_id[player_id_538] = {}
                    seasons_by_player_id[player_id_538][player_season_538] = row_538
            if player_season not in seasons_by_player_id[player_id]:
                print("No RAPTOR data for player " + player_name + " for season " + row_top100['season'])
                continue
            season_by_player_id = seasons_by_player_id[player_id][player_season]
            for column, value in season_by_player_id.items():
                if column not in columns_538:
                    continue
                row_top100[column] = value
            rows_top100_with_538.append(row_top100)
generate_csv_from_list_dicts(rows_top100_with_538, FIVETHIRTYEIGHT_DATA_DIRECTORY, output_file, 'w')
# csv_to_json(output_file, output_json_file)
if not os.path.exists(output_file):
    print("Complete players data with 538 failed")
else:
    print("Complete players data with 538 successful")
