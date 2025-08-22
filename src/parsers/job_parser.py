from dataclasses import dataclass

@dataclass
class ParsedJob:
    title: str
    company: str
    location: str
    description: str
