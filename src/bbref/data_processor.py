from bs4 import Tag

from src.common.utils import full_strip


def get_rankings(table: Tag, teams: list[dict[str, str]]) -> dict[str, str]:
    data = {}
    rows = table.select('tbody > tr')
    for row in rows:
        current_team_raw = row.select_one('td[data-stat="team_name"] > a').text
        current_team = full_strip(current_team_raw)
        team_short: str | None = None
        for team in teams:
            if team['name'] == current_team:
                team_short = team['prefix_2']
                break
        if team_short is None:
            raise Exception('Team not found', current_team)
        win_percentage = row.select_one('td[data-stat="Overall"]').attrs['csk']
        data[team_short] = win_percentage
    return data
