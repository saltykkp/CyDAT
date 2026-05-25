from datetime import datetime
from pathlib import Path


def create_unique_output_dir(parent_dir, *, timestamp_format="%y%m%d_%H%M%S"):
    parent = Path(parent_dir)
    parent.mkdir(parents=True, exist_ok=True)

    base_name = datetime.now().strftime(timestamp_format)
    candidate = parent / base_name
    suffix = 1

    while candidate.exists():
        candidate = parent / f"{base_name}_{suffix:02d}"
        suffix += 1

    candidate.mkdir(parents=True, exist_ok=False)
    return candidate
