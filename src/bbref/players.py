import sys

from src.bbref.players_processor import generate_players
from config.config import get_environment, Environment

# args
if len(sys.argv) < 2 or not sys.argv[1].isnumeric():
    raise Exception("Missing or invalid year")
argv_year = sys.argv[1]
if len(sys.argv) < 3:
    argv_environment = Environment.LOCAL
else:
    argv_environment = get_environment(sys.argv[2])


generate_players(argv_year, argv_environment)
