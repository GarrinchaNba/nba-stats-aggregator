import sys

from config.config import Environment
from config.config import get_environment
from src.ctg.transitions_processor import compute_transitions_data

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

compute_transitions_data(argv_min_year, argv_max_year, argv_environment)
