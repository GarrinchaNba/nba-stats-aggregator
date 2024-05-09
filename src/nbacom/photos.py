import sys

from config.config import Environment, get_environment
from nbacom import extract_photo

# args
if len(sys.argv) < 2 or not sys.argv[1].isalpha():
    raise Exception("Missing or invalid team name")
argv_team_name = sys.argv[1]
if len(sys.argv) < 3 or not sys.argv[2].isnumeric():
    raise Exception("Missing or invalid year")
argv_year = sys.argv[2]
if len(sys.argv) < 4:
    argv_environment = Environment.LOCAL
else:
    argv_environment = get_environment(sys.argv[3])

extract_photo(argv_team_name, argv_year, argv_environment)
