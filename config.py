"""Persists the user's last-used watch folder and toggle states between launches."""

import json
import os

CONFIG_DIR = os.path.expanduser("~/Library/Application Support/TimelapseBuilder")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULTS = {
    "watch_folder": os.path.expanduser("~/Desktop/TL_Folder"),
    "delete_raw": False,
    "overlay_timestamp": False,
}


def load_config():
    config = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH) as f:
            saved = json.load(f)
        config.update({k: v for k, v in saved.items() if k in DEFAULTS})
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return config


def save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp_path = CONFIG_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(config, f, indent=2)
    os.replace(tmp_path, CONFIG_PATH)
