import os.path
from enum import Enum

import yaml

from src.common.constant import CONFIG_DIRECTORY


class Environment(Enum):
    LOCAL = 'local'
    PROD = 'prod'


def get_environment(environment_raw: str) -> Environment:
    values = set(item.value for item in Environment)
    if environment_raw in values:
        return Environment[environment_raw.upper()]
    return Environment.LOCAL


def get_ctg_identifiers(environment=Environment.LOCAL) -> dict[str, str]:
    config = get_config(environment)
    if 'ctg' not in config:
        raise Exception("Missing ctg configuration")
    return config['ctg']


def get_is_stubbed(environment=Environment.LOCAL) -> bool:
    config = get_config(environment)
    return 'is_stubbed' in config and config['is_stubbed'] == True


def get_config(environment=Environment.LOCAL):
    path = os.path.join(CONFIG_DIRECTORY, environment.value + '.yaml')
    with open(path, 'r') as yamlfile:
        return yaml.load(yamlfile, Loader=yaml.FullLoader)
