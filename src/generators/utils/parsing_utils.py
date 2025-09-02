import re
import logging
from typing import List, Dict, Optional

from ..models.tailored_data import (
    TailoredResumeData,
    PublicationEntry
)

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
    """Parse summary section from LLM response with improved pattern matching."""
    summary_patterns = [
        r"##\s*SUMMARY\s*##(.*?)(?=##|$)",
        r"##\s*PROFESSIONAL[ _]?SUMMARY(.*?)(?=##|$)",
        r"##\s*ABOUT[ _]?ME(.*?)(?=##|$)",
        r"SUMMARY[\s\S]*?\n\s*([\s\S]*?)(?=\n##|$)"
    ]
    
    for pattern in summary_patterns:
        summary_match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if summary_match:
            summary_text = summary_match.group(1).strip()
            if summary_text:
                # Clean up the summary text
                summary_lines = [
                    line.strip() 
                    for line in summary_text.split('\n') 
                    if line.strip() and not line.strip().startswith('#')
                ]
                tailored.summary = '\n'.join(summary_lines)
                logger.info("Successfully parsed summary section")
                return
    
    logger.debug("No summary section found in LLM response")

def _parse_experience(response: str, tailored: TailoredResumeData) -> None:
    """Parse experience section from LLM response with improved parsing."""
    # Try multiple possible section headers
    exp_patterns = [
        r"##\s*PROFESSIONAL[ _]?EXPERIENCE\s*##(.*?)(?=##|$)",
        r"##\s*WORK[ _]?EXPERIENCE\s*##(.*?)(?=##|$)",
        r"##\s*EXPERIENCE(.*?)(?=##\s*\w|$)",
        r"##\s*WORK[\s\S]*?(?=##\s*\w|$)"
    ]
    
    exp_text = ""
    for pattern in exp_patterns:
        exp_match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if exp_match:
            exp_text = exp_match.group(1).strip()
            if exp_text:
                break
    
    if not exp_text:
        logger.debug("No experience section found in LLM response")
        return
    
    # Split into individual job entries
    job_entries = re.split(r"###\s*", exp_text)
    
    for entry in job_entries:
        if not entry.strip():
            continue
            
        lines = [line.strip() for line in entry.split("\n") if line.strip()]
        if not lines:
            continue
            
        # Parse job header (title | company | dates)
        header = lines[0]
        title, company, location, dates = "", "", "", ""
        
        # Handle different header formats:
        # 1. Title | Company | Location | Dates
        # 2. Title at Company | Location | Dates
        # 3. Title, Company | Dates
        if "|" in header:
            parts = [p.strip() for p in header.split("|")]
            if len(parts) >= 3:
                title, company, dates = parts[0], parts[1], parts[-1]
                if len(parts) > 3:
                    location = parts[2]
            elif len(parts) == 2:
                # Could be "Title | Company" or "Company | Dates"
                if any(x in parts[1].lower() for x in ['present', '20', '19', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                    title = parts[0]
                    dates = parts[1]
                else:
                    title, company = parts[0], parts[1]
        elif " at " in header:
            # Handle "Title at Company | Dates" format
            parts = header.split(" at ", 1)
            if "|" in parts[1]:
                company, dates = parts[1].split("|", 1)
                title, company, dates = parts[0].strip(), company.strip(), dates.strip()
            else:
                title, company = parts[0].strip(), parts[1].strip()
        else:
            title = header
        
        # Parse bullet points and responsibilities
        bullets = []
        current_bullet = ""
        
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
                
            # Check for bullet points
            if line.startswith(("-", "•", "*")) or re.match(r'^\d+\.', line):
                # Save previous bullet if exists
                if current_bullet:
                    bullets.append(current_bullet.strip())
                current_bullet = re.sub(r'^[\-•*\d\.]\s*', '', line)
            else:
                # Continue the current bullet point
                current_bullet += " " + line
        
        # Add the last bullet point
        if current_bullet:
            bullets.append(current_bullet.strip())
        
        # Create experience entry
        experience = {
            "title": title,
            "company": company,
            "location": location,
            "dates": dates,
            "bullets": bullets
        }
        
        # Only add if we have meaningful content
        if experience["title"] or experience["company"] or experience["bullets"]:
            tailored.experience.append(experience)
    
    logger.info(f"Parsed {len(tailored.experience)} work experiences")

def _parse_projects(response: str, tailored: TailoredResumeData) -> None:
    """Parse projects section from LLM response with improved parsing."""
    # Try multiple possible section headers
    project_patterns = [
        r"##\s*PROJECTS\s*##(.*?)(?=##|$)",
        r"##\s*PROJECTS(.*?)(?=##\s*\w|$)",
        r"##\s*SELECTED[ _]?PROJECTS(.*?)(?=##|$)"
    ]
    
    proj_text = ""
    for pattern in project_patterns:
        proj_match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if proj_match:
            proj_text = proj_match.group(1).strip()
            if proj_text:
                break
    
    if not proj_text:
        logger.debug("No projects section found in LLM response")
        return
    
    # Split into individual projects
    project_entries = re.split(r"###\s*", proj_text)
    
    for entry in project_entries:
        if not entry.strip():
            continue
            
        lines = [line.strip() for line in entry.split("\n") if line.strip()]
        if not lines:
            continue
            
        # Parse project header (name and optional technologies/dates)
        header = lines[0]
        project_name = header
        technologies = []
        
        # Extract technologies if present (e.g., "Project Name | Tech: Python, SQL")
        if "|" in header:
            parts = [p.strip() for p in header.split("|")]
            project_name = parts[0].strip()
            if len(parts) > 1 and ":" in parts[1]:
                tech_part = parts[1].split(":", 1)[1].strip()
                technologies = [t.strip() for t in re.split(r'[,\s]+', tech_part) if t.strip()]
        
        # Parse project description and achievements
        description = []
        achievements = []
        current_section = None
        
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
                
            # Check for section headers in the project
            if line.lower().startswith(("challenge:", "action:", "result:", "achievements:")):
                current_section = line.split(":")[0].strip().lower()
                line = line.split(":", 1)[1].strip() if ":" in line else ""
                if not line:
                    continue
            
            # Clean up bullet points
            line = re.sub(r'^[•\-\*\d\.]\s*', '', line)
            
            if current_section == "achievements" or line.startswith(("-", "•", "*")):
                achievements.append(line)
            else:
                description.append(line)
        
        # Create project dictionary
        project = {
            "name": project_name,
            "description": " ".join(description) if description else "",
            "achievements": achievements,
            "technologies": technologies
        }
        
        # Only add if we have meaningful content
        if project["description"] or project["achievements"]:
            tailored.projects.append(project)
    
    logger.info(f"Parsed {len(tailored.projects)} projects from LLM response")

def _parse_skills(response: str, tailored: TailoredResumeData) -> None:
    """Parse technical skills section from LLM response with improved pattern matching."""
    skills_dict = {}
    
    # Try multiple possible section headers
    skills_patterns = [
        r"##\s*TECHNICAL[ _]?SKILLS\s*##(.*?)(?=##|$)",
        r"##\s*SKILLS[\s\S]*?\n(.*?)(?=##|$)",
        r"##\s*TECHNICAL[ _]?SKILLS[\s\S]*?\n(.*?)(?=##|$)",
        r"##\s*SKILLS\s*\n(.*?)(?=##\s*\w|$)"
    ]
    
    skills_text = ""
    for pattern in skills_patterns:
        skills_match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if skills_match:
            skills_text = skills_match.group(1).strip()
            if skills_text:
                break
    
    if not skills_text:
        logger.debug("No skills section found in LLM response")
        return
    
    # Try structured parsing first (categories with skills)
    category_blocks = re.split(r'\n\s*\n', skills_text.strip())
    
    for block in category_blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            continue
            
        # Check if this is a category header
        category_match = re.match(r'^\*?([^:]+):?$', lines[0], re.IGNORECASE)
        if category_match:
            category = category_match.group(1).strip().title()
            skills = []
            
            # Parse skills in this category
            for line in lines[1:]:
                # Split by commas, semicolons, or other separators
                line_skills = re.split(r'[,;]|\s+', line)
                skills.extend([s.strip() for s in line_skills if s.strip()])
            
            if category and skills:
                skills_dict[category] = skills
    
    # If no categories found, try to extract all skills as a single category
    if not skills_dict:
        all_skills = []
        for line in skills_text.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Clean up the line and split into skills
            line = re.sub(r'^[\-•*\d\.]\s*', '', line)  # Remove bullets/numbers
            line_skills = re.split(r'[,;]|\s+', line)
            all_skills.extend([s.strip() for s in line_skills if s.strip()])
        
        if all_skills:
            skills_dict["Technical Skills"] = all_skills
    
    # Update the tailored data
    if skills_dict:
        tailored.technical_skills = skills_dict
        logger.info(f"Parsed skills: {', '.join(skills_dict.keys())}")
    else:
        logger.warning("No skills could be parsed from the response")

def _process_skills_text(skills_text: str, skills_dict: Dict[str, List[str]]) -> None:
    """Process skills text and populate skills dictionary with improved parsing."""
    current_category = "Technical Skills"  # Default category
    
    # Split into lines and clean them up
    lines = [line.strip() for line in skills_text.split('\n') if line.strip()]
    
    for line in lines:
        # Check for category headers (starts with ### or is in all caps)
        category_match = re.match(r'^###?\s*(.+?)\s*$', line)
        if category_match or (line.isupper() and len(line) < 50):  # Likely a category header
            current_category = category_match.group(1).strip() if category_match else line.strip(':# ')
            if current_category.lower() in ['skills', 'technical skills']:
                current_category = 'Technical Skills'  # Standardize
            if current_category not in skills_dict:
                skills_dict[current_category] = []
            continue
            
        # Process skill lines
        if line and not line.startswith(('-', '•', '*', '#')):  # Not a bullet point or header
            # Handle different skill formats:
            # 1. Comma/pipe separated: "Python, Java, C++"
            # 2. Bullet points without markers (already filtered)
            # 3. Lines with colons: "Languages: Python, Java"
            if ':' in line and not line.startswith('http'):
                # Handle "Category: skill1, skill2" format
                cat_part, skills_part = line.split(':', 1)
                category = cat_part.strip()
                if category and skills_part.strip():
                    if category not in skills_dict:
                        skills_dict[category] = []
                    skills = [s.strip() for s in re.split(r'[,\|]', skills_part) if s.strip()]
                    skills_dict[category].extend(skills)
            else:
                # Regular skill line
                if current_category not in skills_dict:
                    skills_dict[current_category] = []
                skills = [s.strip() for s in re.split(r'[,\|]', line) if s.strip()]
                skills_dict[current_category].extend(skills)
    
    # Clean up skills - remove duplicates and empty categories
    for category in list(skills_dict.keys()):
        if not skills_dict[category]:
            del skills_dict[category]
        else:
            # Remove duplicates while preserving order
            seen = set()
            skills_dict[category] = [x for x in skills_dict[category] 
                                   if not (x in seen or seen.add(x))]

def _fallback_skills_parsing(response: str, skills_dict: Dict[str, List[str]]) -> None:
    """Fallback method for parsing skills when structured parsing fails."""
    logger.debug("Trying fallback skills parsing...")
    
    # Try multiple patterns to find the skills section
    patterns = [
        r'(?i)##\s*(?:TECHNICAL[ _]?SKILLS|SKILLS)[\s\S]*?(?=##\s*\w|$)',
        r'(?i)##\s*SKILLS[\s\S]*?(?=##\s*\w|$)',
        r'(?i)SKILLS:[\s\S]*?(?=##\s*\w|$)'
    ]
    
    skills_text = ""
    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            skills_text = match.group(0)
            # Remove the header
            skills_text = re.sub(r'^.*?##\s*[^\n]*\n', '', skills_text, flags=re.IGNORECASE)
            if skills_text.strip():
                break
    
    if not skills_text:
        logger.debug("No skills section found in fallback parsing")
        return
    
    logger.debug(f"Fallback skills text found: {skills_text[:200]}...")
    
    # Process skills text
    current_category = "Technical Skills"
    skills_dict[current_category] = []
    
    for line in skills_text.split('\n'):
        line = line.strip()
        if not line or line.startswith(('#', '---')):
            continue
            
        # Check for category headers
        if ':' in line and not line.startswith('http'):
            parts = line.split(':', 1)
            if len(parts) == 2 and len(parts[0].split()) < 5:  # Likely a category
                current_category = parts[0].strip()
                if current_category not in skills_dict:
                    skills_dict[current_category] = []
                # Add skills after the colon if any
                skills = [s.strip() for s in re.split(r'[,\|\.]', parts[1]) if s.strip()]
                skills_dict[current_category].extend(skills)
                continue
        
        # Regular skill line
        if current_category not in skills_dict:
            skills_dict[current_category] = []
            
        # Clean up the line and split into skills
        line = re.sub(r'^[•\-\*\d\.]\s*', '', line)  # Remove bullet points
        skills = [s.strip() for s in re.split(r'[,\|\.]', line) if s.strip()]
        skills_dict[current_category].extend(skills)
    
    # Clean up empty categories and remove duplicates
    for category in list(skills_dict.keys()):
        if not skills_dict[category]:
            del skills_dict[category]
        else:
            seen = set()
            skills_dict[category] = [x for x in skills_dict[category] 
                                   if not (x in seen or seen.add(x))]
    
    if skills_dict:
        logger.info(f"Extracted {sum(len(v) for v in skills_dict.values())} skills using fallback parser")

def _extract_skills_from_raw_text(tailored: TailoredResumeData) -> None:
    """Extract skills from raw resume text when LLM response is insufficient."""
    if not hasattr(tailored, 'raw_text') or not tailored.raw_text:
        return
    
    # Common technical skills to look for
    common_skills = {
        'Programming Languages': ['Python', 'Java', 'JavaScript', 'C++', 'C#', 'Ruby', 'Go', 'Rust', 'Swift', 'Kotlin'],
        'Web Technologies': ['HTML', 'CSS', 'JavaScript', 'TypeScript', 'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'Spring', 'ASP.NET'],
        'Databases': ['SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 'SQL Server', 'DynamoDB', 'Cassandra'],
        'Cloud & DevOps': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform', 'Ansible', 'Jenkins', 'GitHub Actions', 'CI/CD'],
        'Data Science': ['Python', 'R', 'Pandas', 'NumPy', 'Scikit-learn', 'TensorFlow', 'PyTorch', 'Keras', 'NLP', 'Computer Vision']
    }
    
    skills_found = {}
    text_lower = tailored.raw_text.lower()
    
    for category, skills in common_skills.items():
        found = []
        for skill in skills:
            # Look for exact matches (case insensitive)
            if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
                found.append(skill)
        if found:
            skills_found[category] = found
    
    # If we found skills, update the tailored data
    if skills_found:
        tailored.technical_skills = skills_found


def _parse_education(response: str, tailored: TailoredResumeData) -> None:
    """Parse education section from LLM response with improved parsing."""
    # Try multiple possible section headers
    edu_patterns = [
        r"##\s*EDUCATION\s*##(.*?)(?=##|$)",
        r"##\s*EDUCATION(.*?)(?=##\s*\w|$)",
        r"##\s*EDUCATION[\s\S]*?(?=##\s*\w|$)"
    ]
    
    edu_text = ""
    for pattern in edu_patterns:
        edu_match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if edu_match:
            edu_text = edu_match.group(1).strip()
            if edu_text:
                break
    
    if not edu_text:
        logger.debug("No education section found in LLM response")
        return
    
    education_entries = []
    current_entry = {}
    
    for line in edu_text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Skip section headers
        if line.startswith(('##', '###')):
            continue
            
        # Check for degree line (typically contains degree, major, university)
        if ' in ' in line or ' at ' in line or ' from ' in line or '|' in line:
            # Save previous entry if exists
            if current_entry:
                education_entries.append(current_entry)
                current_entry = {}
                
            # Parse degree line
            parts = [p.strip() for p in re.split(r'[\|\-]', line)]
            if len(parts) >= 1:
                current_entry['degree'] = parts[0]
            if len(parts) >= 2:
                current_entry['institution'] = parts[1]
            if len(parts) >= 3:
                current_entry['date'] = parts[2]
        # Check for date range (e.g., "Sep 2015 - May 2019")
        elif re.match(r'^(?:[A-Za-z]{3,9}\s+\d{4}\s*[-–]\s*)?(?:[A-Za-z]{3,9}\s+\d{4}|Present|Current)$', line):
            current_entry['date'] = line
        # Check for location
        elif re.match(r'^[A-Z][a-z]+(?:[\s,][A-Z][a-z]+)*(?:,\s*[A-Z]{2})?$', line):
            current_entry['location'] = line
        # Check for GPA or honors
        elif any(x in line.lower() for x in ['gpa', 'grade', 'honor', 'distinction', 'thesis']):
            current_entry['details'] = current_entry.get('details', []) + [line]
        # Bullet points (achievements, coursework, etc.)
        elif line.startswith(('-', '•', '*')):
            current_entry['details'] = current_entry.get('details', []) + [line.lstrip('-•* ')]
    
    # Add the last entry if it exists
    if current_entry:
        education_entries.append(current_entry)
    
    # Convert to the expected format
    tailored.education = []
    for entry in education_entries:
        parts = []
        if 'degree' in entry:
            parts.append(entry['degree'])
        if 'institution' in entry:
            parts.append(entry['institution'])
        if 'date' in entry:
            parts.append(entry['date'])
            
        edu_str = ' | '.join(parts)
        if 'details' in entry:
            edu_str += '\n' + '\n'.join(f"• {d}" for d in entry['details'])
            
        tailored.education.append(edu_str)
    
    logger.info(f"Parsed {len(tailored.education)} education entries")

def _parse_research_publications(response: str, tailored: TailoredResumeData) -> None:
    """Parse research publications section from LLM response with improved parsing."""
    # Try multiple possible section headers
    research_patterns = [
        r"##\s*RESEARCH[ _]?PUBLICATIONS\s*##(.*?)(?=##|$)",
        r"##\s*PUBLICATIONS\s*##(.*?)(?=##|$)",
        r"##\s*RESEARCH[\s\S]*?(?=##\s*\w|$)",
        r"##\s*PUBLICATIONS[\s\S]*?(?=##\s*\w|$)",
        r"##\s*PUBLICATIONS[\s\S]*?\n(.*?)(?=##|$)"
    ]
    
    research_text = ""
    for pattern in research_patterns:
        research_match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if research_match:
            research_text = research_match.group(1).strip()
            if research_text:
                break
    
    if not research_text:
        logger.debug("No research/publications section found in LLM response")
        return
    
    # Try to split into individual publications
    publications = []
    current_pub = []
    
    # Common patterns for publication entries
    pub_start_patterns = [
        r'^\d+\.',  # Numbered entries (1., 2., etc.)
        r'^[\-•*]',  # Bullet points
        r'^\[\d+\]',  # Citation style [1], [2], etc.
        r'^[A-Z][a-z]+(?:, [A-Z]\.)+',  # Author names (e.g., "Smith, J., Johnson, A.")
        r'^[A-Z][a-z]+(?: et\.? al\.?)?\s*\d{4}[a-z]?',  # Author-year format (e.g., "Smith et al. 2020")
    ]
    
    for line in research_text.split('\n'):
        line = line.strip()
        if not line or line.startswith(('##', '###')):
            continue
        
        # Check if this line starts a new publication
        is_new_pub = False
        for pattern in pub_start_patterns:
            if re.search(pattern, line):
                is_new_pub = True
                break
        
        # If it's a new publication, save the previous one
        if is_new_pub and current_pub:
            pub_text = ' '.join(current_pub).strip()
            if pub_text:
                pub = _parse_publication_entry(pub_text)
                if pub:
                    publications.append(pub)
            current_pub = []
        
        # Clean up the line and add to current publication
        line = re.sub(r'^[\d\-•*]\s*', '', line)  # Remove numbering/bullets
        current_pub.append(line)
    
    # Add the last publication
    if current_pub:
        pub_text = ' '.join(current_pub).strip()
        if pub_text:
            pub = _parse_publication_entry(pub_text)
            if pub:
                publications.append(pub)
    
    # Filter out any empty entries
    tailored.research_publications = [p for p in publications if p]
    
    if tailored.research_publications:
        logger.info(f"Parsed {len(tailored.research_publications)} research publications")

def _parse_publication_entry(text: str) -> Optional[PublicationEntry]:
    """Parse a single publication entry into structured data."""
    if not text.strip():
        return None
    
    pub = PublicationEntry()
    
    # Try to extract title (usually in quotes or before a period)
    title_match = re.search(r'"([^"]+)"|\b([A-Z][^.!?]+\.?)(?=\s+[A-Z][a-z]+\s*\()', text)
    if title_match:
        pub.title = (title_match.group(1) or title_match.group(2)).strip()
    
    # Try to extract authors (before the title or in parentheses)
    authors_match = re.search(r'^([^"\(]+)(?=\s*"|\s*\()', text)
    if authors_match:
        authors_text = authors_match.group(1).strip()
        # Split authors by commas and clean up
        pub.authors = [a.strip() for a in re.split(r',|\band\b', authors_text) if a.strip()]
    
    # Try to extract publication venue (in parentheses or after "in")
    venue_match = re.search(r'\(([^)]+)\)|\bin\s+([^,.]+)', text)
    if venue_match:
        pub.publication = (venue_match.group(1) or venue_match.group(2)).strip()
    
    # Try to extract year
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', text)
    if year_match:
        pub.date = year_match.group(1)
    
    # Try to extract DOI or URL
    doi_match = re.search(r'\b(?:doi|DOI):?\s*([^\s,;)]+)', text)
    if doi_match:
        pub.doi = doi_match.group(1).strip()
    
    url_match = re.search(r'\b(?:https?://|www\.)\S+', text)
    if url_match and not pub.doi:
        pub.url = url_match.group(0)
    
    # If we couldn't extract a title, use the first N words as a fallback
    if not pub.title:
        words = text.split()
        if len(words) > 10:
            pub.title = ' '.join(words[:10]) + '...'
        else:
            pub.title = text
    
    return pub
