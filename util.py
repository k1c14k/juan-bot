import json
import os

CONFIG_PATH = os.getenv('CONFIG_PATH') or '~/.config/Juan/config.json'

# if os.getenv('CONFIG_PATH'):
#     CONFIG_PATH = os.getenv('CONFIG_PATH')


def read_config():
    config_path = os.path.expanduser(CONFIG_PATH)
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        return config
    else:
        return {}


def save_config(config):
    config_path = os.path.expanduser(CONFIG_PATH)
    with open(config_path, 'w') as config_file:
        json.dump(config, config_file, indent=4)