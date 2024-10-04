import csv
import os
import shutil
from datetime import datetime, date

from pandas import DataFrame
from rich import json

from src.common.constant import NBA_TEAMS_FILE, COUNTRIES_FILE, NBA_ARENA_FILE, COMMON_DATA_DIRECTORY, \
    TOP100_DATA_DIRECTORY, TOP100_FILE, EXPORT_DATA_DIRECTORY
from src.common.utils import build_years


def get_mapping(file: str, output_key: str) -> dict[str, dict[str, str]]:
    data: dict[str, dict[str, str]] = {}
    with open(file, newline='') as teams_file_csv:
        rows: list[dict[str, str]] = list(csv.DictReader(teams_file_csv, delimiter=','))
        for row in rows:
            if output_key not in row:
                raise Exception('Unknown column name in file [' + file + '] : ' + output_key)
            data[row[output_key]] = row
    return data


def get_mapping_for_output_column(file: str, output_key: str, output_value: str) -> dict[str, str]:
    data: dict[str, str] = {}
    rows = get_mapping(file, output_key)
    for key, row in rows.items():
        if output_key not in row:
            raise Exception('Unknown column name in file [' + file + '] : ' + output_value)
        data[key] = row[output_value]
    return data


def get_teams_mapping(output_key: str, output_value: str) -> dict[str, str]:
    return get_mapping_for_output_column(NBA_TEAMS_FILE, output_key, output_value)


def get_countries_mapping(output_key: str, output_value: str) -> dict[str, str]:
    return get_mapping_for_output_column(COUNTRIES_FILE, output_key, output_value)


def create_directory_if_not_exists(data_directory) -> None:
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)
        print("Create directory : " + data_directory)


def backup_file(file: str) -> None:
    if os.path.exists(file):
        backup_file_name = file + "_backup_" + datetime.today().strftime("%Y%m%d%H%M%S")
        shutil.copyfile(file, backup_file_name)
        print("Backup file : " + backup_file_name)


def copy_file(file_directory: str, new_file_directory: str) -> None:
    if os.path.exists(file_directory):
        shutil.copyfile(file_directory, new_file_directory)
        print("Copy file : " + file_directory + " to " + new_file_directory)


def generate_csv_from_dataframe(data: DataFrame, data_directory: str, file_name: str, mode='w',
                                delimiter=';', with_backup=True) -> None:
    create_directory_if_not_exists(data_directory)
    file = os.path.join(data_directory, file_name)
    if with_backup:
        backup_file(file)
    if os.path.exists(file) and mode == 'a':
        data.to_csv(file, mode=mode, index=False, header=False, sep=delimiter)
    else:
        data.to_csv(file, index=False, sep=delimiter)
    print("File generated : " + file)


def generate_csv_from_list_dicts(data: list[dict[str, str]], directory: str, file_name: str, mode: str = 'a',
                                 delimiter: str = ';', with_backup=True) -> None:
    create_directory_if_not_exists(directory)
    file = os.path.join(directory, file_name)
    if with_backup:
        backup_file(file)
    with open(file_name, mode, newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, data[0].keys(), delimiter=delimiter)
        if mode == 'w':
            dict_writer.writeheader()
        dict_writer.writerows(data)
    print("File generated : " + file)


def generate_csv_from_list_of_list(rows: list[list[str]], columns: list[str], directory: str, file_name: str,
                                   mode: str = 'w', delimiter: str = ';') -> None:
    create_directory_if_not_exists(directory)
    file = os.path.join(directory, file_name + '.csv')
    backup_file(file)
    with open(file, mode, newline='') as output_file:
        dict_writer = csv.writer(output_file, delimiter=delimiter)
        dict_writer.writerow(columns)
        dict_writer.writerows(rows)
    print("File generated : " + file)


def build_arena_mapping():
    arena_data: dict[str, str] = {}
    with open(NBA_ARENA_FILE, newline='') as arena_file_csv:
        arena_rows = list(csv.DictReader(arena_file_csv))
        for arena_row in arena_rows:
            arena_data[arena_row['Team']] = arena_row['Arena']
    return arena_data


def build_csv_filename(file_name: str) -> str:
    return build_file_name(COMMON_DATA_DIRECTORY, file_name)


def build_file_name(directory: str, file_prefix: str, file_suffix: str = '', file_extension: str = '.csv',
                    min_year: str = None, max_year: str = None) -> str:
    years = build_years(min_year, max_year)
    return os.path.join(directory, file_prefix + years + file_suffix + file_extension)


def build_csv_filename_for_competition(competition: str, season: str):
    return competition + '_' + season + '_' + date.today().strftime("%Y%m%d") + '.csv'


def csv_to_json(csv_file_path: str, json_file_path: str):
    json_array = []

    # read csv file
    with open(csv_file_path, encoding='utf-8') as csvf:
        # load csv file data using csv library's dictionary reader
        csv_reader = csv.DictReader(csvf, delimiter=';')

        # convert each csv row into python dict
        for row in csv_reader:
            # add this python dict to json array
            json_array.append(row)

    # convert python jsonArray to JSON String and write to file
    with open(json_file_path, 'w', encoding='utf-8') as jsonf:
        json_string = json.dumps(json_array, indent=None)
        jsonf.write(json_string)
    print("File generated : " + json_file_path)


def build_top100_csv_file_name(file_name: str, min_year: str, max_year: str = None) -> str:
    return build_file_name(TOP100_DATA_DIRECTORY, TOP100_FILE, file_name, '.csv', min_year, max_year)


def build_export_json_file_name(file_name: str, min_year: str, max_year: str = None) -> str:
    return build_file_name(EXPORT_DATA_DIRECTORY, TOP100_FILE, file_name, '.json', min_year, max_year)
