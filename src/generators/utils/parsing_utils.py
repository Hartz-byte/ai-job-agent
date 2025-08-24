import re
import logging
from typing import Dict, List, Tuple, Union
from ..models.tailored_data import TailoredResumeData

logger = logging.getLogger("tailor")

def parse_llm_response(response: str) -> TailoredResumeData:
    """Parse comprehensive LLM response into structured data."""
    tailored = TailoredResumeData()

    if not response:
        return tailored

    # Parse each section
    _parse_summary(response, tailored)
    _parse_experience(response, tailored)
    _parse_projects(response, tailored)
    _parse_skills(response, tailored)
    _parse_education(response, tailored)
    _parse_research_publications(response, tailored)

    return tailored

def _parse_summary(response: str, tailored: TailoredResumeData) -> None:
    """Parse summary section from LLM response."""
    summary_match = re.search(r"##\s*SUMMARY(.*?)(?=##|$)", response, re.DOTALL | re.IGNORECASE)
    if summary_match:
        tailored.summary = summary_match.group(1).strip()

def _parse_experience(response: str, tailored: TailoredResumeData) -> None:
    """Parse experience section from LLM response."""
    exp_match = re.search(r"##\s*EXPERIENCE(.*?)(?=##|$)", response, re.DOTALL | re.IGNORECASE)
    if not exp_match:
        return

    exp_text = exp_match.group(1).strip()
    job_entries = re.split(r"###\s*", exp_text)

    for entry in job_entries[1:]:  # Skip first empty split
        if not entry.strip():
            continue

        lines = [l.strip() for l in entry.split("\n") if l.strip()]
        if not lines:
            continue

        # Parse job header (title | company | dates)
        header = lines[0]
        title, company, duration = "", "", ""

        if "|" in header:
            parts = [p.strip() for p in header.split("|")]
            if len(parts) >= 3:
                title, company, duration = parts[0], parts[1], parts[2]
            elif len(parts) == 2:
                title, company = parts[0], parts[1]
        else:
            title = header

        # Parse bullet points
        bullets = []
        for line in lines[1:]:
            if line.startswith(("-", "•")):
                bullets.append(line.strip("- •"))

        tailored.experience.append({
            "title": title,
            "company": company,
            "duration": duration,
            "bullets": bullets
        })

def _parse_projects(response: str, tailored: TailoredResumeData) -> None:
    """Parse projects section from LLM response."""
    proj_match = re.search(r"##\s*PROJECTS(.*?)(?=##|$)", response, re.DOTALL | re.IGNORECASE)
    if not proj_match:
        return

    proj_text = proj_match.group(1).strip()
    project_entries = re.split(r"###\s*", proj_text)

    for entry in project_entries[1:]:
        if not entry.strip():
            continue

        lines = [l.strip() for l in entry.split("\n") if l.strip()]
        if not lines:
            continue

        project_name = lines[0]
        description = []

        for line in lines[1:]:
            if line.startswith(("-", "•")):
                description.append(line.strip("- •"))

        tailored.projects.append({
            "name": project_name,
            "description": description
        })

def _parse_skills(response: str, tailored: TailoredResumeData) -> None:
    """Parse technical skills section from LLM response."""
    skills_dict = {}
    
    # Try structured format first
    skills_match = re.search(r"##\s*TECHNICAL_SKILLS\s*##(.*?)(?=##|$)", response, re.DOTALL | re.IGNORECASE)
    if not skills_match:
        skills_match = re.search(r"##\s*SKILLS\s*##(.*?)(?=##|$)", response, re.DOTALL | re.IGNORECASE)
    
    if skills_match:
        skills_text = skills_match.group(1).strip()
        if not skills_text:
            logger.warning("Found empty skills section in LLM response")
        else:
            _process_skills_text(skills_text, skills_dict)
    
    # Fallback to more lenient parsing if no skills found
    if not skills_dict:
        _fallback_skills_parsing(response, skills_dict)
    
    # Clean up and assign to tailored data
    tailored.technical_skills = {k: v for k, v in skills_dict.items() if v}
    skill_count = sum(len(v) for v in tailored.technical_skills.values())
    category_count = len(tailored.technical_skills)
    
    logger.info(f"Successfully parsed {skill_count} skills across {category_count} categories")
    
    if logger.isEnabledFor(logging.DEBUG):
        for category, skills in tailored.technical_skills.items():
            logger.debug(f"{category}: {', '.join(skills)}")

def _process_skills_text(skills_text: str, skills_dict: Dict[str, List[str]]) -> None:
    """Process skills text and populate skills dictionary."""
    current_category = None
    for line in skills_text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Check for category headers (starts with ###)
        category_match = re.match(r'^###\s*(.+?)\s*$', line)
        if category_match:
            current_category = category_match.group(1).strip()
            skills_dict[current_category] = []
        # If we have a current category, add skills from this line
        elif current_category is not None:
            # Remove any bullet points or numbering
            line = re.sub(r'^[•\-\d\.]\s*', '', line).strip()
            if line:  # Only add non-empty lines
                # Split by commas and clean up each skill
                skills = [s.strip() for s in re.split(r'[,\|]', line) if s.strip()]
                skills_dict[current_category].extend(skills)

def _fallback_skills_parsing(response: str, skills_dict: Dict[str, List[str]]) -> None:
    """Fallback method for parsing skills when structured parsing fails."""
    logger.debug("Trying fallback skills parsing...")
    skills_section = re.search(
        r'(?i)##\s*(?:TECHNICAL[ _]?SKILLS|SKILLS)(?:\s*##)?(.*?)(?=##|$)', 
        response, 
        re.DOTALL
    )
    
    if skills_section:
        skills_text = skills_section.group(1).strip()
        if skills_text:
            logger.debug(f"Fallback skills text found: {skills_text[:200]}...")
            skills = []
            for line in skills_text.split('\n'):
                line = re.sub(r'^[•\-\d\.]\s*', '', line).strip()
                if line and ':' not in line:  # Skip lines that look like headers
                    skills.extend([s.strip() for s in re.split(r'[,\|]', line) if s.strip()])
            
            if skills:
                skills_dict["Technical Skills"] = skills
                logger.info(f"Extracted {len(skills)} skills using fallback parser")

def _parse_education(response: str, tailored: TailoredResumeData) -> None:
    """Parse education section from LLM response."""
    edu_match = re.search(r"##\s*EDUCATION(.*?)(?=##|$)", response, re.DOTALL | re.IGNORECASE)
    if edu_match:
        edu_text = edu_match.group(1).strip()
        edu_lines = [l.strip() for l in edu_text.split("\n") if l.strip()]
        tailored.education = edu_lines

def _parse_research_publications(response: str, tailored: TailoredResumeData) -> None:
    """Parse research publications section from LLM response."""
    research_match = re.search(r"##\s*RESEARCH_PUBLICATIONS(.*?)(?=##|$)", response, re.DOTALL | re.IGNORECASE)
    if research_match:
        research_text = research_match.group(1).strip()
        research_lines = [l.strip() for l in research_text.split("\n") if l.strip()]
        tailored.research_publications = research_lines
