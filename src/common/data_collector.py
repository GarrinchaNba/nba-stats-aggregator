import re
import time

import requests
from bs4 import BeautifulSoup, Tag, ResultSet


def get_content_from_soup(soup: BeautifulSoup, html_element_id: str, html_element_type='div',
                          html_element_selector='id', child: str = None) -> None | Tag:
    data = soup.find(html_element_type, {html_element_selector: html_element_id})
    if not data:
        print("No data found for id : " + html_element_id)
        return None
    if child:
        data = data.findChild(child)
    if not data:
        raise RuntimeError("No data found for id " + html_element_id + " with child : " + child)
    return data


def get_all_content_from_soup(soup: BeautifulSoup, html_element_id: str, html_element_type='div',
                              html_element_selector='id') -> ResultSet[Tag] | None:
    data = soup.findAll(html_element_type, {html_element_selector: html_element_id})
    if not data:
        print("No data found for id : " + html_element_id)
        return None
    if not data:
        raise RuntimeError("No data found for id " + html_element_id)
    return data


def get_table_head(soup: BeautifulSoup, table_id: str) -> None | Tag | tuple[Tag, Tag]:
    return get_content_from_soup(soup, table_id, 'div', 'id', 'thead')


def get_table_body(soup: BeautifulSoup, table_id: str) -> None | Tag | tuple[Tag, Tag]:
    return get_content_from_soup(soup, table_id, 'div', 'id', 'tbody')


def get_soup(url: str, cookies: dict = None) -> BeautifulSoup:
    retry = 0
    res = None
    while retry < 3:
        session = requests.session()
        if cookies:
            for key, value in cookies.items():
                session.cookies.set(key, value)
        res = session.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Enconding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }, cookies=cookies)
        if res.status_code == 200:
            break
        retry += 1
        print("Fail to find data, retry n°" + str(retry) + "...")
        time.sleep(3)
    if res is None:
        raise Exception("Fail to find response for url : " + url)
    comm = re.compile("<!--|-->")
    return BeautifulSoup(comm.sub("", res.text), 'lxml')


def get_soup_from_html_content(html_content: str) -> BeautifulSoup:
    return BeautifulSoup(html_content, "html.parser")
