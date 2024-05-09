import os

from config.config import Environment
from src.common.constant import BASKETLAB_WITH_BBINDEX_FILE, ROOT_DIRECTORY, SRC_DIRECTORY
from src.common.file_processor import csv_to_json, build_top100_csv_file_name, build_export_json_file_name


def generate_full(min_year: str, max_year: str, environment: Environment) -> None:
    list_scripts = [['bbref', 'top100.py'], ['538', 'top100.py'], ['bbindex', 'top100.py']]
    for script in list_scripts:
        script_full_path = os.path.join(SRC_DIRECTORY, script[0], script[1])
        print("Execute script : " + script_full_path)
        __ = os.system('python3 ' + script_full_path + ' ' + min_year + ' ' + max_year + ' ' + environment.value)
    output_file: str = build_top100_csv_file_name(BASKETLAB_WITH_BBINDEX_FILE, min_year, max_year)
    output_data_file: str = build_export_json_file_name('', min_year, max_year)
    csv_to_json(output_file, output_data_file)
