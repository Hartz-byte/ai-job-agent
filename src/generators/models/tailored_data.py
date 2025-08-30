from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ExperienceEntry(BaseModel):
    """Structured data for a single work experience entry."""
    title: str = ""
    company: str = ""
    location: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    dates: str = ""  # Fallback for raw date strings
    bullets: List[str] = Field(default_factory=list)
    is_current: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class ProjectEntry(BaseModel):
    """Structured data for a single project entry."""
    name: str = ""
    description: str = ""
    technologies: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    url: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class EducationEntry(BaseModel):
    """Structured data for an education entry."""
    degree: str = ""
    field_of_study: str = ""
    institution: str = ""
    location: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[float] = None
    honors: List[str] = Field(default_factory=list)
    description: str = ""

class PublicationEntry(BaseModel):
    """Structured data for a research publication."""
    title: str = ""
    authors: List[str] = Field(default_factory=list)
    publication: str = ""  # Journal/Conference name
    date: Optional[str] = None
    url: str = ""
    doi: str = ""

class SkillCategory(BaseModel):
    """Structured data for a skill category."""
    name: str
    skills: List[str] = Field(default_factory=list)
    proficiency: Optional[str] = None  # e.g., "Advanced", "Intermediate"

@dataclass
class TailoredResumeData:
    """Structured data container for tailored resume content with validation."""
    summary: str = ""
    experience: List[ExperienceEntry] = field(default_factory=list)
    projects: List[ProjectEntry] = field(default_factory=list)
    technical_skills: Dict[str, List[str]] = field(default_factory=dict)
    education: List[EducationEntry] = field(default_factory=list)
    research_publications: List[PublicationEntry] = field(default_factory=list)
    raw_text: str = ""  # Store the original text for reference
    
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
    
    def to_dict(self) -> dict:
        """Convert the resume data to a dictionary."""
        return {
            "summary": self.summary,
            "experience": [exp.dict() for exp in self.experience],
            "projects": [proj.dict() for proj in self.projects],
            "technical_skills": self.technical_skills,
            "education": [edu.dict() for edu in self.education],
            "research_publications": [pub.dict() for pub in self.research_publications]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TailoredResumeData':
        """Create a TailoredResumeData instance from a dictionary."""
        resume = cls()
        resume.summary = data.get("summary", "")
        resume.experience = [ExperienceEntry(**exp) for exp in data.get("experience", [])]
        resume.projects = [ProjectEntry(**proj) for proj in data.get("projects", [])]
        resume.technical_skills = data.get("technical_skills", {})
        resume.education = [EducationEntry(**edu) for edu in data.get("education", [])]
        resume.research_publications = [
            PublicationEntry(**pub) for pub in data.get("research_publications", [])
        ]
        return resume
