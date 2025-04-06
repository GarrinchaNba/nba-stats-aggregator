import sys

from config.config import Environment, get_environment
from src.nbacom.playbyplay_processor import extract_playbyplay

if len(sys.argv) < 2:
    raise Exception("Missing or invalid team")
argv_team = sys.argv[1]
if len(sys.argv) < 3 or not sys.argv[2].isnumeric():
    raise Exception("Missing or invalid year")
argv_year = sys.argv[2]
if len(sys.argv) < 4:
    argv_environment = Environment.LOCAL
else:
    argv_environment = get_environment(sys.argv[3])

extract_playbyplay(argv_team, argv_year, argv_environment)
