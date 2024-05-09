import sys

from src.bbref.team_calendar_processor import generate_calendars
from config.config import get_environment, Environment

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


generate_calendars(argv_team, argv_year, argv_environment)
