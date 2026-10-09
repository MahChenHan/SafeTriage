import os

INCIDENTS_FILENAME = "incidents.json"


def get_data_dir() -> str:
    return os.environ.get("DATA_DIR", "data")


def get_incidents_path(data_dir: str) -> str:
    return os.path.join(data_dir, INCIDENTS_FILENAME)