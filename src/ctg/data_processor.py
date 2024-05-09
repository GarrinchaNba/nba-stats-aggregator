from bs4 import Tag


def get_columns(table: Tag) -> list[str]:
    columns = []
    rows = table.select('thead > tr')
    table_id = table.attrs['id']
    tables_to_fix = [
        'team_game_log_four_factors',
        'team_game_log_offense_halfcourt',
        'team_game_log_defense_halfcourt',
        'team_game_log_offense_transition',
        'team_game_log_defense_transition'
    ]
    custom: dict[int, str] = {
        1: 'Place',
        3: 'Result',
    }
    for row_key, row in enumerate(rows):
        if row_key == 0 and table_id in tables_to_fix:
            columns.append('')
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
    return columns


def get_rows(table: Tag, columns: list[str], teams: dict[str, str]) -> list[dict[str, str]]:
    data = []
    win_pct = 'Opp win%'
    opp_rank = 'Opp rank'
    game_type = 'Game type'
    rows = table.select('tbody > tr')
    columns.append(opp_rank)
    columns.append(win_pct)
    columns.append(game_type)
    for row in rows:
        row_data = {game_type: "playoffs" if (
            row.has_attr("class") and "playoffs_row" in row.attrs['class']
        ) else "regular season"}
        cells = row.findAll("td")
        team_id = ''
        for index, cell in enumerate(cells):
            if index == 2:
                team_id = str(cell.text)
            row_data[columns[index]] = str(cell.text)
        count = 1
        for name, win_loss_pct in teams.items():
            if name == team_id.lower():
                row_data[opp_rank] = count
                row_data[win_pct] = win_loss_pct
            count += 1
        data.append(row_data)
    return data
