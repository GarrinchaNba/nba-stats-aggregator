import sys

from src.bbref.players_processor import generate_players
from config.config import get_environment, Environment

USAGE_EXAMPLE = "Example: ./run.sh bbref_players 2024 [local|prod]"


def fail(message: str):
    print(f"Error: {message}")
    print(USAGE_EXAMPLE)
    raise SystemExit(1)


if len(sys.argv) < 2 or not sys.argv[1].isnumeric():
    fail("Missing or invalid year. Expected a numeric year as first argument.")
argv_year = sys.argv[1]

if len(sys.argv) >= 3:
    environment_raw = sys.argv[2].lower()
    if environment_raw not in {item.value for item in Environment}:
        fail("Invalid environment. Expected one of: local, prod.")
    argv_environment = get_environment(environment_raw)
else:
    argv_environment = Environment.LOCAL


generate_players(argv_year, argv_environment)
