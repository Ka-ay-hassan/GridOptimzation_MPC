import json

from Code.paths import CODE


def load_config() -> dict:
    with open(CODE / f"config.json") as file:
        return json.load(file)


CONFIG = load_config()

