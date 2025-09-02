from dataclasses import dataclass

@dataclass
class JobPost:
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str
    job_id: str
