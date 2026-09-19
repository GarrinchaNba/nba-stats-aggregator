import sys

from src.bbref.top100_processor import generate_top100
from config.config import Environment, get_environment

USAGE_EXAMPLE = "Example: ./run.sh bbref_top100 2023 [2024] [local|prod]"


def fail(message: str):
    print(f"Error: {message}")
    print(USAGE_EXAMPLE)
    raise SystemExit(1)


if len(sys.argv) < 2 or not sys.argv[1].isnumeric():
    fail("Missing or invalid year. Expected a numeric year as first argument.")

argv_min_year = sys.argv[1]
argv_max_year = argv_min_year
if len(sys.argv) >= 3:
    if not sys.argv[2].isnumeric():
        fail("Invalid max year. Expected a numeric year as second argument.")
    argv_max_year = sys.argv[2]

if len(sys.argv) >= 4:
    environment_raw = sys.argv[3].lower()
    if environment_raw not in {item.value for item in Environment}:
        fail("Invalid environment. Expected one of: local, prod.")
    argv_environment = get_environment(environment_raw)
else:
    argv_environment = Environment.LOCAL

generate_top100(argv_min_year, argv_max_year, argv_environment)
