import os
from pathlib import Path

# urls
BASKETBALL_REFERENCE_URL = 'https://www.basketball-reference.com'
CLEANING_THE_GLASS_URL = 'https://cleaningtheglass.com'
NBA_COM_IMAGES_URL = 'https://cdn.nba.com'
NBA_COM_URL = 'https://www.nba.com'
BASKETBALL_INDEX_URL = 'https://www.bball-index.com'

# directories
ROOT_DIRECTORY = str(Path(__file__).parent.parent.parent.absolute())  # This is your Project Root
SRC_DIRECTORY = os.path.join(ROOT_DIRECTORY, "src")
DATA_DIRECTORY = os.path.join(ROOT_DIRECTORY, "data")
CONFIG_DIRECTORY = os.path.join(ROOT_DIRECTORY, "config")
BBREF_DATA_DIRECTORY = os.path.join(DATA_DIRECTORY, "bbref")
BBREF_GAME_LOGS_DATA_DIRECTORY = os.path.join(BBREF_DATA_DIRECTORY, "game_logs")
COMMON_DATA_DIRECTORY = os.path.join(DATA_DIRECTORY, "common")
STUB_DATA_DIRECTORY = os.path.join(DATA_DIRECTORY, "stub")
NBACOM_DATA_DIRECTORY = os.path.join(DATA_DIRECTORY, "nbacom")
TOP100_DATA_DIRECTORY = os.path.join(DATA_DIRECTORY, "top100")
CLEANING_THE_GLASS_DATA_DIRECTORY = os.path.join(DATA_DIRECTORY, "ctg")
FIVETHIRTYEIGHT_DATA_DIRECTORY = os.path.join(DATA_DIRECTORY, "538")
BBINDEX_DATA_DIRECTORY = os.path.join(DATA_DIRECTORY, "bbindex")
EXPORT_DATA_DIRECTORY = os.path.join(DATA_DIRECTORY, "export")

# files
TOP100_FILE = 'top100_'
GAMELOGS_FILE = 'gamelogs_'
BASKETLAB_FILE_BASE = '_basketlab'
BASKETLAB_COMPLETE_FILE_BASE = '_basketlab_complete'
BASKETLAB_WITH_RAPTORS_FILE = '_basketlab_with_raptors'
BASKETLAB_WITH_BBINDEX_FILE = '_basketlab_with_bbindex'
NBA_TEAMS_FILE = os.path.join(COMMON_DATA_DIRECTORY, 'nba_teams.csv')
NBA_ARENA_FILE = os.path.join(COMMON_DATA_DIRECTORY, 'nba_arena_list.csv')
COUNTRIES_FILE = os.path.join(COMMON_DATA_DIRECTORY, 'countries.csv')
