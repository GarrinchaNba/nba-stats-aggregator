import os
from datetime import datetime

from src.bbref.team_calendar_processor import generate_calendar_for_season
from src.common.constant import BBREF_DATA_DIRECTORY
from src.common.file_processor import get_teams_mapping, build_arena_mapping, generate_csv_from_list_dicts
from src.common.utils import get_csv_file_as_dict, get_all_seasons_since
from config.config import Environment


def generate_sportpress_calendars(team_prefix: str, year: str, environment=Environment.LOCAL):
    print("Generate sportpress calendar for team [" + team_prefix.upper() + "] from year [" + year + "]")
    teams_mapping = get_teams_mapping('prefix_1', 'name')
    seasons = get_all_seasons_since(int(year))
    for season in seasons:
        generate_sportpress_calendar_for_season(season, team_prefix, environment, teams_mapping)
    print("All sportpress calendars generated !")


def generate_sportpress_calendar_for_season(season: str, team_prefix: str, environment=Environment.LOCAL,
                                            teams_mapping: dict[str, str] = None):
    print("Generate sportpress calendar for season [" + season + "]")
    if teams_mapping is None:
        teams_mapping = get_teams_mapping('prefix_1', 'name')
    input_file = os.path.join(BBREF_DATA_DIRECTORY, team_prefix + '_calendar_' + season + '.csv')
    if not os.path.exists(input_file):
        generate_calendar_for_season(season, team_prefix, environment)
        if not os.path.exists(input_file):
            raise Exception('Missing calendar file', input_file)
    output_file = os.path.join(BBREF_DATA_DIRECTORY, team_prefix + '_calendar_' + season + '_sportpress.csv')
    arena_mapping = build_arena_mapping()
    calendar_data: list[dict] = []
    input_rows = get_csv_file_as_dict(input_file)
    for input_row in input_rows:
        if input_row['Place'] == '@':
            home = input_row['Opponent']
            away = teams_mapping[team_prefix]
            arena = arena_mapping[home]
        else:
            home = teams_mapping[team_prefix]
            away = input_row['Opponent']
            arena = arena_mapping[teams_mapping[team_prefix]]
        date = datetime.strptime(input_row['Date'], '%a, %b %d, %Y').date()
        time = datetime.strptime(input_row['Start (ET)'].replace('p', 'PM'), '%I:%M%p').time()
        calendar_data.append({
            'Date': date.strftime('%Y/%m/%d'),
            'Time': time.strftime('%H:%M:%S'),
            'Venue': arena,
            'Home': home,
            'Away': away
        })
    generate_csv_from_list_dicts(calendar_data, BBREF_DATA_DIRECTORY, output_file, 'w', ',')
    print("Sportpress calendar generated for season [" + season + "]")
