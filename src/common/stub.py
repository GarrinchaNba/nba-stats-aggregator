import os.path

from bs4 import BeautifulSoup

from src.common.constant import STUB_DATA_DIRECTORY


def get_stub_soup(file_name: str) -> BeautifulSoup:
    return BeautifulSoup(open(get_stub_file(file_name), encoding="utf8"), "html.parser")


def get_stub_file(file_name: str, extension='html') -> str:
    return os.path.join(STUB_DATA_DIRECTORY, file_name + '.' + extension)
