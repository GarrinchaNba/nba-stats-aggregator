import sys

from config.config import Environment, get_environment
from src.sportpress.team_calendar_processor import generate_sportpress_calendars

# args
if len(sys.argv) < 2 or not sys.argv[1].isalpha() or not len(sys.argv[1]) == 3:
    raise Exception("Missing or invalid team")
argv_team = sys.argv[1]
if len(sys.argv) < 3 or not sys.argv[2].isnumeric():
    raise Exception("Missing or invalid year")
argv_year = sys.argv[2]
if len(sys.argv) < 4:
    argv_environment = Environment.LOCAL
else:
    argv_environment = get_environment(sys.argv[3])

generate_sportpress_calendars(argv_team.lower(), argv_year, argv_environment)
