#!/bin/bash

PYTHON3=$(command -v python3)
VENV_DIR="./.venv"
REQ_FILE="requirements.txt"
REQ_HASH_FILE="$VENV_DIR/.requirements.hash"

# Create venv only if it doesn't exist
echo "VENV_DIR : $VENV_DIR"
if [ ! -d "$VENV_DIR" ]; then
    echo 'Create venv dir : $VENV_DIR'
    $PYTHON3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# Calculate current requirements hash
CUR_HASH=$(md5sum "$REQ_FILE" | awk '{print $1}')

# Check if requirements need to be installed
if [ ! -f "$REQ_HASH_FILE" ] || [ "$CUR_HASH" != "$(cat $REQ_HASH_FILE)" ]; then
  echo 'Install dependencies...'
    "$VENV_DIR/bin/pip" install -r "$REQ_FILE" --verbose 2>&1
    if [ $? -eq 0 ]; then
        echo "$CUR_HASH" > "$REQ_HASH_FILE"
        echo '...ok'
    else
        echo 'Dependency installation failed. Please check errors above.'
        exit 1
    fi
else
    echo 'Dependencies already installed.'
fi

ROOT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export PYTHONPATH=${PYTHONPATH}:${ROOT_DIR}/src/common/${ROOT_DIR}/config

if [ $# = 0 ] || [ $1 = 'help' ]; then
    echo 'Please enter a script name as follow : ./run.sh <SCRIPT_NAME> <ARG1> <ARG2> ... <ARGN>'
    echo 'with SCRIPT_NAME to chose among the following list :'
    echo ' - top100'
    echo ' - bbref_top100'
    echo ' - bbindex_top100'
    echo ' - 538_top100'
    echo ' - bbref_team_calendar'
    echo ' - bbref_players'
    echo ' - bbref_game_logs'
    echo ' - ctg_game_logs'
    echo ' - ctg_transition'
    echo ' - sportpress_team_calendar'
    echo ' - sportpress_team_games'
    echo ' - nbacom_photos'
    echo 'and ARG1, ARG2, ..., ARGN depending on selected script'
    exit 0;
fi

echo "Run script : $1 with arguments [${@:2}]..."
if [ $1 = 'top100' ]; then
    $PYTHON3 ${ROOT_DIR}/src/top100/top100.py "${@:2}"
elif [ $1 = 'bbref_top100' ]; then
    $PYTHON3 ${ROOT_DIR}/src/bbref/top100.py "${@:2}"
elif [ $1 = 'bbindex_top100' ]; then
    $PYTHON3 ${ROOT_DIR}/src/bbindex/top100.py "${@:2}"
elif [ $1 = '538_top100' ]; then
    $PYTHON3 ${ROOT_DIR}/src/538/top100.py "${@:2}"
elif [ $1 = 'sportpress_team_calendar' ]; then
    $PYTHON3 ${ROOT_DIR}/src/sportpress/team_calendar.py "${@:2}"
elif [ $1 = 'sportpress_team_games' ]; then
    $PYTHON3 ${ROOT_DIR}/src/sportpress/team_games.py "${@:2}"
elif [ $1 = 'bbref_players' ]; then
    $PYTHON3 ${ROOT_DIR}/src/bbref/players.py "${@:2}"
elif [ $1 = 'bbref_game_logs' ]; then
    $PYTHON3 ${ROOT_DIR}/src/bbref/game_logs.py "${@:2}"
elif [ $1 = 'bbref_team_calendar' ]; then
    $PYTHON3 ${ROOT_DIR}/src/bbref/team_calendar.py "${@:2}"
elif [ $1 = 'ctg_game_logs' ]; then
    $PYTHON3 ${ROOT_DIR}/src/ctg/game_logs.py "${@:2}"
elif [ $1 = 'ctg_transition' ]; then
    $PYTHON3 ${ROOT_DIR}/src/ctg/transitions.py "${@:2}"
else
    echo "Unknown script : $1"
    exit 1;
fi

exit 0;
