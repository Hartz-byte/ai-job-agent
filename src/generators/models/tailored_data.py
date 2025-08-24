from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class TailoredResumeData:
    """Structured data container for tailored resume content."""
    summary: str = ""
    experience: List[Dict] = field(default_factory=list)
    projects: List[Dict] = field(default_factory=list)
    technical_skills: Dict[str, List[str]] = field(default_factory=dict)
    education: List[Dict] = field(default_factory=list)
    research_publications: List[str] = field(default_factory=list)
    
    def is_empty(self) -> bool:
        """Check if the tailored data container is empty."""
        return not any([
            self.summary,
            self.experience,
            self.projects,
            self.technical_skills,
            self.education,
            self.research_publications
        ])
