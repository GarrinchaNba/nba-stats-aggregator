import sys

from config.config import get_environment, Environment
from src.bbref.free_throws_processor import collect_free_throws_from_games, \
    collect_free_throws_from_games_with_moving_average

if len(sys.argv) < 2 or not sys.argv[1].isnumeric():
    raise Exception("Missing or invalid year")
argv_min_year = sys.argv[1]
if len(sys.argv) < 3 or not sys.argv[2].isnumeric():
    argv_max_year = argv_min_year
else:
    argv_max_year = sys.argv[2]


collect_free_throws_from_games_with_moving_average(argv_min_year, argv_max_year)