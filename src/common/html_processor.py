from bs4 import Tag

from src.common.utils import full_strip


def get_columns_from_tag(head: Tag):
    return [th.text.strip() for th in head.select('th')]


def get_row_from_tag(row: Tag):
    return [full_strip(td.text) for td in row.select('td')]
