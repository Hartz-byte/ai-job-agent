from typing import Optional

def is_location_ok(location: str, cities: list[str], countries: list[str], remote_ok: bool, remote_global_ok: bool) -> bool:
    loc = (location or "").lower()
    if "remote" in loc:
        return True if (remote_ok or remote_global_ok) else False
    for c in cities:
        if c.lower() in loc:
            return True
    for country in countries:
        if country.lower() in loc:
            return True
    return False

def normalize_location(location: Optional[str]) -> str:
    return (location or "").strip()
