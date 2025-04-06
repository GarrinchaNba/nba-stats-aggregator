import csv
import json

import requests

from config.config import Environment, get_is_stubbed, get_nbacom_identifiers
from src.common.constant import NBA_TEAMS_FILE, NBA_COM_URL, NBA_COM_CORE_API
from src.common.data_collector import get_url_response
from src.common.file_processor import build_csv_filename
from src.common.stub import get_stub_file
from src.common.utils import get_season_from_year


def extract_playbyplay(input_team: str, year: str, environment: Environment):
    print("hello")
    output_file: str = build_csv_filename('playbyplay')
    season = get_season_from_year(int(year))
    nbacom_identifiers = get_nbacom_identifiers(environment)

    with open(NBA_TEAMS_FILE, mode='r', newline='') as nba_teams_csv:
        teams = list(csv.DictReader(nba_teams_csv, delimiter=','))
        for team in teams:
            team_name = get_team_name(team)
            if team_name == input_team:
                break
        print('Team found : ' + team_name)
    is_stubbed = get_is_stubbed(environment)
    if not is_stubbed:
        url = NBA_COM_URL + '/' + team_name + '/api/schedule?season=' + season
        response = get_url_response(url)
        if response.status_code != 200:
            raise Exception("Data not found for url : " + url)
        data = json.loads(response.content)
    else:
        with open(get_stub_file('stub_nbacom_schedule', 'json'), 'r') as file:
            data = json.load(file)
    games = data['scheduleData']['schedule']
    for game in games:
        game_id = game['gameId']
        if not is_stubbed:
            url = NBA_COM_CORE_API + '/cp/api/v1.8/gameDetails?leagueId=00&gameId=' + game_id + '&tabs=pbp'
            data = get_url_response(url, None, {
                'Accept': 'application/json',
                'Referer': NBA_COM_URL + '/',
                'ocp-apim-subscription-key': nbacom_identifiers['ocpApimSubscriptionKey']
            })
        else:
            with open(get_stub_file('stub_nbacom_game_details', 'json'), 'r') as file:
                data = json.load(file)
        pbp_actions = data['pbp']['actions']
        for action in pbp_actions:
            action_id =
    'https://stats.nba.com/stats/videoeventsasset?GameEventID=4&GameID=0012400033'

    # 'https://core-api.nba.com/cp/api/v1.8/gameDetails?leagueId=00&gameId=0012400033&tabs=pbp'
    # 'https://www.nba.com/stats/events?CFID=&CFPARAMS=&GameEventID=4&GameID=0012400033&Season=2024-25&flag=1&title=Jump%20Ball%20Green%20vs.%20Sabonis%3A%20Tip%20to%20K.%20Ellis'
    # 'https://videos.nba.com/nba/pbp/media/2024/10/11/0012400033/4/c3703b67-2abf-ee2f-b75d-ed405aaebca9_1280x720.mp4'


def get_team_name(team):
    prefix_parts = team['prefix_long'].split('-')
    if len(prefix_parts) < 2:
        raise Exception("Invalid team name")
    return prefix_parts[-1]
