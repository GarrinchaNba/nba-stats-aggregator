from src.common.constant import BASKETBALL_REFERENCE_URL, BBREF_DATA_DIRECTORY
from src.common.data_collector import get_table_body, get_table_head, get_soup
from src.common.file_processor import generate_csv_from_list_of_list
from src.common.html_processor import get_row_from_tag, get_columns_from_tag
from src.common.stub import get_stub_soup
from src.common.utils import update_columns, get_year_from_season, get_all_seasons_since
from config.config import Environment, get_is_stubbed

# constants
CHANGES = {
    5: "Place"
}


def generate_calendars(team_prefix: str, year: str, environment: Environment):
    print('Generate calendars for team [' + team_prefix + '] from year [' + year + ']')
    seasons = get_all_seasons_since(int(year))
    is_stubbed = get_is_stubbed(environment)
    for season in seasons:
        generate_calendar_for_season(season, team_prefix, environment, is_stubbed)
    print('All calendars generated !')


def generate_calendar_for_season(season: str, team_prefix: str, environment=Environment.LOCAL, is_stubbed: bool = None):
    print('Generate calendar for team [' + team_prefix + '] for season [' + season + ']')
    if is_stubbed is None:
        is_stubbed = get_is_stubbed(environment)
    if not is_stubbed:
        year = get_year_from_season(season)
        calendar_url = BASKETBALL_REFERENCE_URL + '/teams/' + team_prefix.upper() + '/' + year + '_games.html'
        soup = get_soup(calendar_url)
    else:
        soup = get_stub_soup('stub_bbref_calendar')
    head = get_table_head(soup, 'div_games')
    columns = update_columns(get_columns_from_tag(head), CHANGES)
    body = get_table_body(soup, 'div_games')
    input_rows = body.select('tr')
    output_rows = []
    count = 1
    for input_row in input_rows:
        row = get_row_from_tag(input_row)
        if row:
            output_rows.append([count, *row])
            count += 1
    generate_csv_from_list_of_list(output_rows, columns, BBREF_DATA_DIRECTORY,
                                   team_prefix.lower() + '_calendar_' + season)
    print('Calendar generated !')
