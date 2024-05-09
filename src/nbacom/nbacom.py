import base64
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
from src.common.file_processor import create_directory_if_not_exists
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


def extract_photo(team_name: str, year: str, environment: Environment) -> None:
    is_stubbed = get_is_stubbed(environment)
    if not is_stubbed:
        url = NBA_COM_URL + '/' + team_name + '/roster'
        soup = get_soup(url)
    else:
        soup = get_stub_soup('stub_photos_roster')
    table = get_content_from_soup(soup, 'page')
    roster = table.findChildren('div', {'class': 'player-card'})

    for player in roster:
        class_first_name = re.compile('Player_playerLinkFirstName_(.*)')
        first_name = player.findChild('span', {'class': class_first_name}).text
        class_last_name = re.compile('Player_playerLinkLastName_(.*)')
        last_name = player.findChild('span', {'class': class_last_name}).text
        class_datalink = re.compile('Player_playerDataLinks_(.*)')
        player_id = player.findChild('div', {'class': class_datalink}).findChildren('a')[1].attrs['data-testid'][23:]
        if not is_stubbed:
            image_url = NBA_COM_IMAGES_URL + '/headshots/nba/latest/1040x760/' + player_id + '.png'
            res = requests.get(image_url, stream=True)
            if res.status_code != 200:
                raise Exception('Image not found : ' + image_url)
            byte_array = res.raw
            save_image(byte_array, first_name, last_name, team_name, year)
        else:
            with open(os.path.join(STUB_DATA_DIRECTORY, "stub_photo.png"), "rb") as byte_array:
                save_image(byte_array, first_name, last_name, team_name, year)
        wait_random_duration()


def save_image(byte_array, first_name: str, last_name: str, team_name: str, year: str):
    season = get_season_from_year(int(year), '_')
    data_directory = os.path.join(NBACOM_DATA_DIRECTORY, team_name + '_' + season)
    create_directory_if_not_exists(data_directory)
    file_name = os.path.join(data_directory, first_name + '_' + last_name + '.png')
    with open(file_name, 'wb') as f:
        shutil.copyfileobj(byte_array, f)
    print('Image sucessfully saved: ', file_name)
