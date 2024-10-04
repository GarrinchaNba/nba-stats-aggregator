import sys

from config.config import Environment, get_environment
from src.bbindex.top100_processor_v2 import generate_top100_v2
from src.common.utils import remove_accents

print(remove_accents('Jonas Valančiūnas'))


if len(sys.argv) < 2 or not sys.argv[1].isnumeric():
    raise Exception("Missing or invalid year")
argv_min_year = sys.argv[1]
if len(sys.argv) < 3 or not sys.argv[2].isnumeric():
    argv_max_year = argv_min_year
else:
    argv_max_year = sys.argv[2]
if len(sys.argv) < 4:
    argv_environment = Environment.LOCAL
else:
    argv_environment = get_environment(sys.argv[3])

generate_top100_v2(argv_min_year, argv_max_year, argv_environment)
