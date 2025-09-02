from dataclasses import dataclass
from typing import Iterable
from storage.models import JobPost

@dataclass
class Provider:
    name: str

    def search(self, query: str, locations: list[str]) -> Iterable[JobPost]:
        raise NotImplementedError
