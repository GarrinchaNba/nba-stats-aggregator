import re

from bs4 import Tag


def get_columns(table: Tag) -> list[str]:
    columns = []
    rows = table.select('thead > tr')
    for row_key, row in enumerate(rows):
        cells = row.findAll("th")
        for cell_key, cell in enumerate(cells):
            columns.append(sanitize_text(cell.text))
    return columns


def sanitize_text(text: str, raw = True):
    value = re.sub(r'(\n|\([^()]*\))', ' ', text).strip()
    if raw is False:
        value = re.sub(r'([$,%])', '', text).strip()
    return value


def get_rows(table: Tag, columns: list[str], raw = True) -> list[dict[str, str]]:
    data = []
    rows = table.select('tbody > tr')
    for row in rows:
        row_data = {}
        cells = row.findAll("td")
        count = 0
        for index, cell in enumerate(cells):
            if count == 0:
                cell = cell.find('a')
            row_data[columns[index]] = str(sanitize_text(cell.text, raw))
            count += 1
        data.append(row_data)
    return data
