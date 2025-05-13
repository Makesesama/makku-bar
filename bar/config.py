import yaml
import os
from platformdirs import user_config_dir
import argparse


APP_NAME = "makku_bar"

XDG_CONFIG_HOME = user_config_dir(appname=APP_NAME)
XDG_CONFIG_FILE = os.path.join(XDG_CONFIG_HOME, "config.yaml")


def load_config(config_path=XDG_CONFIG_FILE):
    """Loads configuration from a YAML file."""
    if config_path is None:
        print("No configuration file path provided or found.")
        return None

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file '{config_path}': {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred loading config file '{config_path}': {e}")
        return None


def load_args():
    parser = argparse.ArgumentParser(description="makku_bar")
    parser.add_argument(
        "-c",
        "--config",
        help="Path to a custom configuration file.",
        type=str,
    )

    args = parser.parse_args()
    return args.config


app_config = load_config() if not load_args() else load_config(load_args())

if app_config is None:
    raise Exception("Config file missing")

VINYL = app_config.get("vinyl", {"enable": False})
