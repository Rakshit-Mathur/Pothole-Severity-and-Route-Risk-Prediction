from pathlib import Path

import yaml


def load_cfg(path: str = "config.yaml") -> dict:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
