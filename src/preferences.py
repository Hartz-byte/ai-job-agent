from dataclasses import dataclass
from typing import List
from .config import cfg

@dataclass
class Preferences:
    keywords: List[str]
    cities: List[str]
    countries: List[str]
    remote_ok: bool
    remote_global_ok: bool

def get_preferences() -> Preferences:
    return Preferences(
        keywords=cfg.keywords,
        cities=cfg.cities,
        countries=cfg.countries,
        remote_ok=cfg.remote_ok,
        remote_global_ok=cfg.remote_global_ok,
    )
