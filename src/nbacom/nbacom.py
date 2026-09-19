import base64
import json
import os
import re
import shutil
import time
import urllib.parse

import requests
from bs4 import Tag, BeautifulSoup

from config.config import Environment, get_is_stubbed
from src.common.constant import NBA_COM_IMAGES_URL, NBA_COM_URL, STUB_DATA_DIRECTORY, NBACOM_DATA_DIRECTORY
from src.common.data_collector import get_soup, get_content_from_soup
from src.common.file_processor import create_directory_if_not_exists, get_teams_mapping
from src.common.stub import get_stub_soup
from src.common.utils import wait_random_duration, get_season_from_year


def dataURI_decode(uri):
    if uri.startswith('data:'):
        uri = uri[5:]
        data_format, data = uri.split(',', 1)
        mimetype, *attrs = data_format.split(';')
        if attrs and attrs[-1] == 'base64':
            # final_image = Image.open(BytesIO(base64.b64decode(data)))
            # return mimetype, base64.decodebytes(data.encode("ascii"))
            return mimetype, base64.b64decode(data)
        else:
            return mimetype, urllib.parse.unquote_to_bytes(data)


def get_table(url: str, table_id: str) -> Tag:
    retry = 0
    table = None
    while retry < 3:
        res = requests.get(url)
        ## The next two lines get around the issue with comments breaking the parsing.
        comm = re.compile("<!--|-->")
        soup = BeautifulSoup(comm.sub("", res.text), 'lxml')
        table = soup.find('div', {'id': table_id})
        if table:
            break
        retry += 1
        print("Fail to find data, retry n°" + str(retry) + "...")
        time.sleep(3)

    if not table:
        raise RuntimeError("No data found after " + str(retry) + " retries")

    return table


def _extract_roster_from_next_data(soup: BeautifulSoup) -> list[dict]:
    script = soup.select_one('script#__NEXT_DATA__')
    if script is None or not script.string:
        return []

    try:
        payload = json.loads(script.string)
    except json.JSONDecodeError:
        return []

    roster_data = payload.get('props', {}).get('pageProps', {}).get('rosterData', {}).get('roster', [])
    return [player for player in roster_data if isinstance(player, dict)]


def extract_photo(team_prefix: str, year: str, environment: Environment) -> None:
    is_stubbed = get_is_stubbed(environment)
    team_url_slug = get_teams_mapping('prefix_1', 'prefix_long_2')[team_prefix]
    print("Extract photos for team [" + team_url_slug + "] from year [" + year + "]")
    if not is_stubbed:
        url = NBA_COM_URL + '/' + team_url_slug + '/roster'
        soup = get_soup(url)
    else:
        soup = get_stub_soup('stub_photo_roster_2')

    page_container = soup.select_one('#page, main') or soup
    roster = page_container.select('[data-testid="player-card"]')
    if not roster:
        roster = page_container.select('div.player-card')
    if not roster:
        roster = page_container.find_all('div', {'class': 'player-card'})
    if not roster:
        roster = _extract_roster_from_next_data(soup)
    if not roster:
        raise ValueError(f"No roster cards found for team [{team_url_slug}] from page HTML structure")

    for player in roster:
        if isinstance(player, dict):
            player_id = player.get('id')
            if player_id is None:
                raise ValueError(f"Missing player id in roster JSON for team [{team_url_slug}]")
            first_name = player.get('firstName', '').strip()
            last_name = player.get('lastName', '').strip()
            image_url = f"{NBA_COM_IMAGES_URL}/headshots/nba/latest/1040x760/{player_id}.png"
        else:
            image_tag = player.select_one('img[alt*="headshot"]') or player.find('img')
            if image_tag is None:
                raise ValueError(f"Missing player image in roster card for team [{team_url_slug}]")

            image_url = image_tag.get('src') or image_tag.get('data-src')
            if image_url is None:
                player_id = image_tag.get('data-testid', '').replace('player-', '', 1)
                image_url = NBA_COM_IMAGES_URL + '/headshots/nba/latest/1040x760/' + player_id + '.png'

            name_divs = player.select('div.brand-font')
            if len(name_divs) >= 2:
                first_name = name_divs[0].get_text(' ', strip=True)
                last_name = name_divs[1].get_text(' ', strip=True)
            else:
                alt = image_tag.get('alt', '').strip()
                match = re.search(r'^(.*?)\s+([^\s]+)\s+headshot$', alt)
                if not match:
                    raise ValueError(f"Unable to parse player names from image alt text: '{alt}'")
                first_name, last_name = match.groups()

        if not is_stubbed:
            res = requests.get(image_url, stream=True)
            if res.status_code != 200:
                raise Exception('Image not found : ' + image_url)
            byte_array = res.raw
            save_image(byte_array, first_name, last_name, team_prefix, year)
        else:
            with open(os.path.join(STUB_DATA_DIRECTORY, "stub_photo.png"), "rb") as byte_array:
                save_image(byte_array, first_name, last_name, team_prefix, year)
        wait_random_duration()


def save_image(byte_array, first_name: str, last_name: str, team_name: str, year: str):
    season = get_season_from_year(int(year), '_')
    data_directory = os.path.join(NBACOM_DATA_DIRECTORY, team_name + '_' + season)
    create_directory_if_not_exists(data_directory)
    file_name = os.path.join(data_directory, first_name + '_' + last_name + '.png')
    with open(file_name, 'wb') as f:
        shutil.copyfileobj(byte_array, f)
    print('Image sucessfully saved: ', file_name)
