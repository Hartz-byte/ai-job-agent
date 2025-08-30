from dataclasses import dataclass
from typing import Optional, Dict, List
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document
import re

@dataclass
class Experience:
    title: str
    company: str
    duration: str
    description: List[str]

@dataclass  
class Project:
    name: str
    description: List[str]
    technologies: List[str]

@dataclass
class Education:
    degree: str
    institution: str
    year: str
    details: str

@dataclass
class ResearchPublication:
    title: str
    link: Optional[str]
    description: Optional[str]

@dataclass
class ResumeProfile:
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    linkedin: Optional[str]
    github: Optional[str]
    summary: Optional[str]
    experience: List[Experience]
    projects: List[Project]
    technical_skills: Dict[str, List[str]]  # Category -> Skills
    education: List[Education]
    research_publications: List[ResearchPublication]
    raw_text: str

def _extract_text(path: str) -> str:
    """Extract text from PDF, DOCX, or TXT files."""
    if path.lower().endswith(".pdf"):
        return pdf_extract_text(path) or ""
    elif path.lower().endswith(".docx"):
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

def _extract_contact_info(text: str) -> Dict[str, Optional[str]]:
    """Extract contact information from resume text."""
    contact = {"email": None, "phone": None, "linkedin": None, "github": None, "name": None}

    # Email extraction (stricter pattern)
    email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
    if email_match:
        contact["email"] = email_match.group(0).strip()

    # Phone extraction
    phone_match = re.search(r"(?:\+?\d[\s-]?){8,15}", text)
    if phone_match:
        contact["phone"] = phone_match.group(0).strip()

    # LinkedIn extraction  
    linkedin_match = re.search(r"linkedin\.com/in/[A-Za-z0-9-_]+", text, re.IGNORECASE)
    if linkedin_match:
        contact["linkedin"] = linkedin_match.group(0)

    # GitHub extraction
    github_match = re.search(r"github\.com/[A-Za-z0-9-_]+", text, re.IGNORECASE)
    if github_match:
        contact["github"] = github_match.group(0)

    # Name extraction (first few lines, non-email lines, 2-4 words)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:10]:
        if contact["email"] and contact["email"] in line:
            continue
        words = line.split()
        if 2 <= len(words) <= 4 and all(w[0].isalpha() for w in words if w):
            contact["name"] = line
            break

    return contact

def _parse_experience_section(text: str) -> List[Experience]:
    """Parse work experience from resume text."""
    experiences = []

    # Find experience section
    exp_pattern = r"(?:EXPERIENCE|WORK EXPERIENCE|EMPLOYMENT)(.*?)(?=\n(?:EDUCATION|SKILLS|PROJECTS|KEY PROJECTS|RESEARCH|$))"
    exp_match = re.search(exp_pattern, text, re.IGNORECASE | re.DOTALL)

    if not exp_match:
        return experiences

    exp_text = exp_match.group(1).strip()

    # Split by job entries (look for patterns like "Job Title | Company" or "Company")
    job_entries = re.split(r"\n(?=[A-Z][^\n]*(?:\||–|-).*?(?:20\d{2}|\d{4}))", exp_text)

    for entry in job_entries:
        if not entry.strip():
            continue

        lines = [line.strip() for line in entry.strip().split("\n") if line.strip()]
        if not lines:
            continue

        # Parse job header (title, company, dates)
        header = lines[0]
        title, company, duration = "", "", ""

        # Try different header patterns
        if "|" in header:
            parts = [p.strip() for p in header.split("|")]
            if len(parts) >= 2:
                title = parts[0]
                company_date = parts[1]
                # Extract company and date
                date_match = re.search(r"(\w+\s+20\d{2}\s*-\s*\w+\s+20\d{2}|\w+\s+20\d{2}\s*-\s*Present)", company_date)
                if date_match:
                    duration = date_match.group(1)
                    company = company_date.replace(duration, "").strip()
                else:
                    company = company_date

        # Parse bullet points
        description = []
        for line in lines[1:]:
            if line and not re.match(r"^[A-Z][^\n]*(?:\||–|-)", line):  # Not a new job header
                description.append(line.strip("• -"))

        if title or company:  # Only add if we found something meaningful
            experiences.append(Experience(
                title=title,
                company=company, 
                duration=duration,
                description=description
            ))

    return experiences

def _parse_projects_section(text: str) -> List[Project]:
    """Parse projects from resume text."""
    projects = []

    # Find projects section
    proj_pattern = r"(?:KEY PROJECTS|PROJECTS)(.*?)(?=\n(?:EXPERIENCE|EDUCATION|SKILLS|RESEARCH|$))"
    proj_match = re.search(proj_pattern, text, re.IGNORECASE | re.DOTALL)

    if not proj_match:
        return projects

    proj_text = proj_match.group(1).strip()

    # Split by project names (usually standalone lines)
    project_entries = re.split(r"\n(?=[A-Z][^\n]*(?:–|-|:))", proj_text)

    for entry in project_entries:
        if not entry.strip():
            continue

        lines = [line.strip() for line in entry.strip().split("\n") if line.strip()]
        if not lines:
            continue

        # First line is usually project name
        name = lines[0].strip("• -–:")

        # Rest are descriptions
        description = []
        technologies = []

        for line in lines[1:]:
            clean_line = line.strip("• -")
            description.append(clean_line)

            # Extract technologies (look for parentheses or common tech terms)
            tech_match = re.findall(r"\b(?:Python|PyTorch|TensorFlow|JavaScript|React|Node|AWS|Docker|MongoDB|SQL|FastAPI|Streamlit)\b", clean_line, re.IGNORECASE)
            technologies.extend(tech_match)

        projects.append(Project(
            name=name,
            description=description,
            technologies=list(set(technologies))  # Remove duplicates
        ))

    return projects

def _parse_skills_section(text: str) -> Dict[str, List[str]]:
    """Parse skills section into categories."""
    skills = {}

    # Find skills section
    skills_pattern = r"(?:SKILLS|TECHNICAL SKILLS)(.*?)(?=\n(?:[A-Z][A-Z\s]+|$))"
    skills_match = re.search(skills_pattern, text, re.IGNORECASE | re.DOTALL)

    if not skills_match:
        return skills

    skills_text = skills_match.group(1).strip()

    # Look for categorized skills (e.g., "AI/ML: PyTorch | TensorFlow")
    category_lines = skills_text.split("\n")

    for line in category_lines:
        if not line.strip():
            continue

        # Check if line has category format
        if ":" in line or "|" in line:
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    category = parts[0].strip()
                    skill_list = [s.strip() for s in re.split(r"[|,]", parts[1]) if s.strip()]
                    skills[category] = skill_list
            else:
                # Treat as single category
                skill_list = [s.strip() for s in re.split(r"[|,]", line) if s.strip()]
                if skill_list:
                    skills["Technical Skills"] = skill_list
        else:
            # Single line of skills
            skill_list = [s.strip() for s in re.split(r"[|,]", line) if s.strip()]
            if skill_list:
                skills["Technical Skills"] = skills.get("Technical Skills", []) + skill_list

    return skills

def _parse_education_section(text: str) -> List[Education]:
    """Parse education section."""
    education = []

    # Find education section  
    edu_pattern = r"(?:EDUCATION|EDUCATION AND CERTIFICATIONS)(.*?)(?=\n(?:[A-Z][A-Z\s]+|$))"
    edu_match = re.search(edu_pattern, text, re.IGNORECASE | re.DOTALL)

    if not edu_match:
        return education

    edu_text = edu_match.group(1).strip()
    lines = [line.strip() for line in edu_text.split("\n") if line.strip()]

    for line in lines:
        # Look for degree patterns
        if any(keyword in line.lower() for keyword in ["b.tech", "bachelor", "master", "phd", "certification"]):
            education.append(Education(
                degree=line,
                institution="",
                year="",
                details=""
            ))

    return education

def _parse_research_section(text: str) -> List[ResearchPublication]:
    """Parse research publications."""
    publications = []

    # Find research section
    research_pattern = r"(?:RESEARCH|PUBLICATIONS|RESEARCH PUBLICATIONS)(.*?)(?=\n(?:[A-Z][A-Z\s]+|$))"
    research_match = re.search(research_pattern, text, re.IGNORECASE | re.DOTALL)

    if not research_match:
        return publications

    research_text = research_match.group(1).strip()
    lines = [line.strip() for line in research_text.split("\n") if line.strip()]

    for line in lines:
        # Extract publication title and link
        link_match = re.search(r"\(([^)]+)\)", line)
        link = link_match.group(1) if link_match else None
        title = re.sub(r"\([^)]+\)", "", line).strip("• -")

        if title:
            publications.append(ResearchPublication(
                title=title,
                link=link,
                description=None
            ))

    return publications

def parse_resume(path: str) -> ResumeProfile:
    """Parse resume into structured format with all sections."""
    text = _extract_text(path)

    # Extract contact information
    contact = _extract_contact_info(text)

    # Extract summary (first few sentences after name/contact)
    summary = None
    summary_match = re.search(r"(?:SUMMARY|PROFILE|OBJECTIVE)(.*?)(?=\n(?:[A-Z][A-Z\s]+|$))", text, re.IGNORECASE | re.DOTALL)
    if summary_match:
        summary = summary_match.group(1).strip()

    # Parse all sections
    experience = _parse_experience_section(text)
    projects = _parse_projects_section(text)
    technical_skills = _parse_skills_section(text)
    education = _parse_education_section(text)
    research_publications = _parse_research_section(text)

    return ResumeProfile(
        name=contact["name"],
        email=contact["email"],
        phone=contact["phone"],
        linkedin=contact["linkedin"],
        github=contact["github"],
        summary=summary,
        experience=experience,
        projects=projects,
        technical_skills=technical_skills,
        education=education,
        research_publications=research_publications,
        raw_text=text
    )
