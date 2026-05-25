import sys
from pathlib import Path


def get_bundle_base_dir():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def get_resource_path(*parts):
    return get_bundle_base_dir().joinpath(*parts)
