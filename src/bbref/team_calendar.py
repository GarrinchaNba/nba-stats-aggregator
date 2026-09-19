import sys

from src.bbref.team_calendar_processor import generate_calendars
from config.config import get_environment, Environment

USAGE_EXAMPLE = "Example: ./run.sh bbref_team_calendar sas 2024 [local|prod]"


def fail(message: str):
    print(f"Error: {message}")
    print(USAGE_EXAMPLE)
    raise SystemExit(1)


if len(sys.argv) < 2 or not sys.argv[1].isalpha() or len(sys.argv[1]) != 3:
    fail("Missing or invalid team. Expected a 3-letter team code as first argument.")
argv_team = sys.argv[1]

if len(sys.argv) < 3 or not sys.argv[2].isnumeric():
    fail("Missing or invalid year. Expected a numeric year as second argument.")
argv_year = sys.argv[2]

if len(sys.argv) >= 4:
    environment_raw = sys.argv[3].lower()
    if environment_raw not in {item.value for item in Environment}:
        fail("Invalid environment. Expected one of: local, prod.")
    argv_environment = get_environment(environment_raw)
else:
    argv_environment = Environment.LOCAL


generate_calendars(argv_team, argv_year, argv_environment)
