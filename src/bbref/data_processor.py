from enum import Enum

from bs4 import Tag

from src.common.utils import full_strip


class GameType(Enum):
    REGULAR = 'regular_season'
    PLAYOFFS = 'playoffs'


def get_rankings(table: Tag, teams: list[dict[str, str]], team_prefix: str) -> dict[str, str]:
    data = {}
    rows = table.select('tbody > tr')
    for row in rows:
        current_team_raw = row.select_one('td[data-stat="team_name"] > a').text
        current_team = full_strip(current_team_raw)
        team_short: str | None = None
        for team in teams:
            if team['name'] == current_team:
                team_short = team[team_prefix]
                break
        if team_short is None:
            raise Exception('Team not found', current_team)
        win_percentage = row.select_one('td[data-stat="Overall"]').attrs['csk']
        data[team_short] = win_percentage
    return data


def get_columns(table: Tag) -> list[str]:
    columns = []
    rows = table.select('thead > tr')
    custom: dict[int, str] = {
        3: 'Place',
        6: 'Team pts',
        7: 'Opp pts',
    }
    excluded = ['Rk']
    for row_key, row in enumerate(rows):
        cells = row.findAll("th")
        count = 0
        for cell_key, cell in enumerate(cells):
            if cell.has_attr('colspan'):
                colspan_size = int(cell.attrs['colspan'])
                for cpt in range(colspan_size):
                    if row_key == 0:
                        columns.append(cell.text)
                    else:
                        columns[count] = (columns[count] + ' ' + cell.text).strip()
                    count += 1
            else:
                if row_key == 0:
                    columns.append(cell.text)
                else:
                    if cell_key in custom.keys():
                        columns[count] = custom[cell_key]
                    else:
                        columns[count] = (columns[count] + ' ' + cell.text).strip()
                count += 1
    return [column for column in columns if column not in excluded]


def get_rows(table: Tag, columns: list[str], teams: dict[str, str], game_type: GameType) -> list[dict[str, str]]:
    data = []
    win_pct_key = 'Opp win%'
    opp_rank_key = 'Opp rank'
    game_type_key = 'Game type'
    rows = table.select('tbody > tr:not([class*="thead"])')
    if game_type != GameType.PLAYOFFS:
        columns += [opp_rank_key, win_pct_key, game_type_key]
    for row in rows:
        row_data = {game_type_key: game_type.value}
        cells = row.findAll("td")
        team_id = ''
        column_index = 0
        for index, cell in enumerate(cells):
            cell_value = str(cell.text).strip()
            if index == 3:
                team_id = cell_value
            if columns[column_index] != '':
                row_data[columns[column_index]] = cell_value
            column_index += 1
        count = 1
        for name, win_loss_pct in teams.items():
            if name == team_id.lower():
                row_data[opp_rank_key] = count
                row_data[win_pct_key] = win_loss_pct
            count += 1
        data.append(row_data)
    return data
