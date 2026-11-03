from enum import Enum

from bs4 import Tag

from src.common.utils import full_strip


class GameType(Enum):
    REGULAR = 'regular_season'
    PLAYOFFS = 'playoffs'


def get_rankings(table: Tag, teams: list[dict[str, str]], team_prefix: str) -> dict[str, str]:
    """Extract team rankings from a standings table.

    Args:
        table: BeautifulSoup Tag containing the standings table.
        teams: List of team mappings with 'name' and team_prefix fields.
        team_prefix: Dictionary key to use for team short code (e.g., 'prefix_1').

    Returns:
        Dictionary mapping team short codes to win percentages.

    Raises:
        ValueError: If a team from the table is not found in the teams mapping.
    """
    data = {}
    rows = table.select('tbody > tr')
    for row in rows:
        current_team_raw = row.select_one('td[data-stat="team_name"] > a').text
        current_team = full_strip(current_team_raw)
        team_short = _find_team_short_code(current_team, teams, team_prefix)
        if team_short is None:
            raise ValueError(f'Team not found: {current_team}')
        win_percentage = row.select_one('td[data-stat="Overall"]').attrs['csk']
        data[team_short] = win_percentage
    return data


def _find_team_short_code(
    team_name: str, teams: list[dict[str, str]], team_prefix: str
) -> str | None:
    """Find the short code for a team by name.

    Args:
        team_name: Full team name to look up.
        teams: List of team mappings.
        team_prefix: Dictionary key for the team short code.

    Returns:
        Team short code if found, None otherwise.
    """
    for team in teams:
        if team['name'] == team_name:
            return team[team_prefix]
    return None


def get_columns(table: Tag) -> list[str]:
    """Extract column headers from a table.

    Args:
        table: BeautifulSoup Tag containing the table with thead.

    Returns:
        List of column header names, excluding 'Rk' column.
    """
    columns = []
    rows = table.select('thead > tr')
    custom_column_names = {
        3: 'Place',
        6: 'Team pts',
        7: 'Opp pts',
    }
    excluded_columns = ['Rk']

    for row_index, row in enumerate(rows):
        cells = row.find_all("th")
        column_index = 0
        for cell_index, cell in enumerate(cells):
            if cell.has_attr('colspan'):
                colspan_size = int(cell.attrs['colspan'])
                _process_colspan_cell(
                    columns, cell, colspan_size, row_index, column_index
                )
                column_index += colspan_size
            else:
                _process_regular_cell(
                    columns, cell, row_index, column_index, custom_column_names, cell_index
                )
                column_index += 1

    return [col for col in columns if col not in excluded_columns]


def _process_colspan_cell(
    columns: list[str], cell: Tag, colspan_size: int, row_index: int, column_index: int
) -> None:
    """Process a table cell with colspan attribute.

    Args:
        columns: List of columns being built.
        cell: The table header cell.
        colspan_size: Number of columns this cell spans.
        row_index: Current row index in thead.
        column_index: Current column index.
    """
    for offset in range(colspan_size):
        if row_index == 0:
            columns.append(cell.text)
        else:
            columns[column_index + offset] = (
                columns[column_index + offset] + ' ' + cell.text
            ).strip()


def _process_regular_cell(
    columns: list[str],
    cell: Tag,
    row_index: int,
    column_index: int,
    custom_names: dict[int, str],
    cell_index: int,
) -> None:
    """Process a regular table header cell.

    Args:
        columns: List of columns being built.
        cell: The table header cell.
        row_index: Current row index in thead.
        column_index: Current column index.
        custom_names: Mapping of cell indices to custom column names.
        cell_index: Index of the cell in the row.
    """
    if row_index == 0:
        columns.append(cell.text)
    else:
        if cell_index in custom_names:
            columns[column_index] = custom_names[cell_index]
        else:
            columns[column_index] = (columns[column_index] + ' ' + cell.text).strip()


def get_rows(
    table: Tag, columns: list[str], teams: dict[str, str], game_type: GameType
) -> list[dict[str, str]]:
    """Extract rows from a game logs table with enriched data.

    Args:
        table: BeautifulSoup Tag containing the game logs table.
        columns: List of column headers.
        teams: Dictionary mapping team IDs to win percentages (for rankings).
        game_type: Type of games (regular season or playoffs).

    Returns:
        List of dictionaries containing game data rows.
    """
    data = []
    opp_rank_key = 'Opp rank'
    win_pct_key = 'Opp win%'
    game_type_key = 'Game type'
    rows = table.select('tbody > tr:not([class*="thead"])')

    # Add ranking columns for regular season games
    if game_type != GameType.PLAYOFFS:
        columns = columns + [opp_rank_key, win_pct_key, game_type_key]

    for row in rows:
        row_data = {game_type_key: game_type.value}
        cells = row.find_all("td")
        team_id = _extract_team_id(cells)
        _populate_row_data(row_data, cells, columns)
        _add_ranking_data(row_data, team_id, teams, opp_rank_key, win_pct_key, game_type)
        data.append(row_data)

    return data


def _extract_team_id(cells: list[Tag]) -> str:
    """Extract team ID from game row cells.

    Args:
        cells: List of table data cells.

    Returns:
        Team ID (lowercase).
    """
    if len(cells) > 3:
        return cells[3].text.strip().lower()
    return ''


def _populate_row_data(row_data: dict[str, str], cells: list[Tag], columns: list[str]) -> None:
    """Populate row data dictionary with cell values.

    Args:
        row_data: Dictionary to populate.
        cells: List of table data cells.
        columns: List of column headers.
    """
    for index, cell in enumerate(cells):
        if index < len(columns) and columns[index] != '':
            row_data[columns[index]] = str(cell.text).strip()


def _add_ranking_data(
    row_data: dict[str, str],
    team_id: str,
    teams: dict[str, str],
    opp_rank_key: str,
    win_pct_key: str,
    game_type: GameType,
) -> None:
    """Add opponent ranking data to row if available.

    Args:
        row_data: Dictionary to update with ranking data.
        team_id: Team ID to look up.
        teams: Mapping of team IDs to win percentages.
        opp_rank_key: Key for opponent rank field.
        win_pct_key: Key for opponent win percentage field.
        game_type: Type of game (regular season or playoffs).
    """
    if game_type == GameType.PLAYOFFS:
        return

    rank = 1
    for team_name, win_loss_pct in teams.items():
        if team_name == team_id:
            row_data[opp_rank_key] = str(rank)
            row_data[win_pct_key] = win_loss_pct
            break
        rank += 1
