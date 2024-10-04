import csv
import json
import string
import unicodedata
from datetime import date
from enum import Enum
from random import randint
from time import sleep


class Duration(Enum):
    SHORT = [1, 3]
    MEDIUM = [5, 10]


def full_strip(text):
    return " ".join(text.replace('\n', '').split())


def get_season_from_year(season: int, delimiter='-') -> str:
    return str(season - 1) + delimiter + str(season)


def get_current_season_year() -> int:
    year = date.today().year
    if date.today().month > 7:
        return year + 1
    else:
        return year


def get_all_seasons_since(min_year: int, separator='_') -> list[str]:
    max_year = get_current_season_year()
    return get_all_seasons_between(min_year, max_year, separator)


def get_all_seasons_between(min_year: int, max_year: int, separator='_') -> list[str]:
    seasons = []
    for year in range(min_year - 1, max_year):
        seasons.append(str(year) + separator + str(year + 1))
    return seasons


def get_shortened_season_name(season: str, separator='_') -> str:
    years = season.split(separator)
    if len(years) < 2 or len(years[1]) != 4:
        raise Exception('Invalid season provided : ' + season)
    return years[0] + '-' + years[1][2:]


def get_year_from_season(season: str, separator='_') -> str:
    years = season.split(separator)
    if len(years) < 2:
        raise Exception("Invalid season : " + season)
    return years[1]

def remove_accents(data: str, normalization_code = 'NFKD'):
    return ''.join(
        x for x in unicodedata.normalize(normalization_code, data) if x in string.ascii_letters or x == ' ' or x == '-').lower()


def update_countries(value: str):
    if value == 'UK':
        return 'GB'
    return value


def build_years(min_year: str, max_year: str) -> str:
    if min_year is None:
        return ''
    if min_year != max_year and max_year is not None:
        return min_year + '_' + max_year
    return min_year


def wait_random_duration(duration=Duration.MEDIUM):
    sleep(randint(duration.value[0], duration.value[1]))


def get_csv_file_as_dict(file: str, delimiter=';') -> list[dict[str, str]]:
    with open(file, newline='') as file_csv:
        return list(csv.DictReader(file_csv, delimiter=delimiter))


def update_columns(columns: list[str], changes: dict[int, str]):
    for key, value in changes.items():
        if key > len(columns):
            raise Exception("Key [" + str(key) + "] does not exists in columns")
        columns[key] = value
    return columns


def does_franchise_exists_for_season(current_team: dict[str, str], current_year: int):
    return (
        (not current_team['first_year'].isnumeric()) or int(current_team['first_year']) <= current_year
    ) and (
        (not current_team['last_year'].isnumeric()) or int(current_team['last_year']) >= current_year
    )


def matrix_to_list(matrix):
    flat_list = []
    for row in matrix:
        flat_list += row
    return flat_list
