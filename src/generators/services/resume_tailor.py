import os
import logging
from typing import Optional, Dict, List, Tuple, Any
from docx import Document

from ..models.tailored_data import TailoredResumeData
from ..utils.docx_utils import (
    add_paragraph_with_style,
    add_section,
    add_bullet_points
)
from ..utils.template_utils import (
    get_template_path,
    create_document,
    save_document
)
from src.llm import get_local_llm
from src.llm.prompts import TAILOR_PROMPT

logger = logging.getLogger("tailor")

class ResumeTailor:
    """Handles the core resume tailoring functionality."""
    
    def __init__(self, profile, job):
        """Initialize with profile and job data."""
        self.profile = profile
        self.job = job
        
    def generate_tailored_content(self) -> TailoredResumeData:
        """Generate tailored resume content using LLM."""
        # Format the prompt with job and resume data
        prompt = TAILOR_PROMPT.format(
            job_title=getattr(self.job, 'title', ''),
            company=getattr(self.job, 'company', ''),
            location=getattr(self.job, 'location', ''),
            job_url=getattr(self.job, 'url', ''),
            resume_text=getattr(self.profile, 'raw_text', ''),
            job_text=getattr(self.job, 'description', '')
        )
        
        # Get LLM response
        llm = get_local_llm()
        response = llm.generate(prompt)
        
        # Parse the response into TailoredResumeData
        return self._parse_llm_response(response)
    
    def _parse_llm_response(self, response: str) -> TailoredResumeData:
        """Parse LLM response into structured TailoredResumeData."""
        from ..utils.parsing_utils import (
            _parse_summary, _parse_experience, _parse_projects,
            _parse_skills, _parse_education, _parse_research_publications
        )
        
        tailored = TailoredResumeData()
        
        # Parse each section
        _parse_summary(response, tailored)
        _parse_experience(response, tailored)
        _parse_projects(response, tailored)
        _parse_skills(response, tailored)
        _parse_education(response, tailored)
        _parse_research_publications(response, tailored)
        
        return tailored
        
    def create_tailored_resume(
        self, 
        tailored_data: TailoredResumeData,
        output_path: str,
        template_path: Optional[str] = None
    ) -> str:
        """Create a tailored resume document."""
        try:
            # Get template path if not provided
            if template_path is None:
                template_path = get_template_path()
            
            logger.debug(f"Using template: {template_path}")
            
            try:
                # Create document from template or scratch
                if template_path and os.path.exists(template_path):
                    doc = create_document(template_path)
                    logger.info("Updating template with tailored data...")
                    try:
                        self._update_template_with_tailored_data(doc, tailored_data)
                    except Exception as update_error:
                        logger.error(f"Error updating template: {update_error}")
                        # Fall back to building from scratch if template update fails
                        logger.info("Falling back to building resume from scratch")
                        doc = self._build_resume_from_scratch(tailored_data)
                else:
                    logger.warning("No template found, creating resume from scratch")
                    doc = self._build_resume_from_scratch(tailored_data)
                
                # Save the document
                return save_document(doc, output_path)
                
            except Exception as e:
                logger.error(f"Error creating tailored DOCX: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Fatal error in create_tailored_resume: {e}")
            raise
    
    def _update_template_with_tailored_data(
        self, 
        doc: Document, 
        tailored_data: TailoredResumeData
    ) -> None:
        """Update existing template with tailored data while preserving original formatting."""
        logger.info("Updating template with tailored data...")
        
        try:
            # Preserve the first paragraph (name and contact info)
            if len(doc.paragraphs) > 0:
                # Keep the first paragraph as is (name and contact info)
                first_para = doc.paragraphs[0]
                
                # Update the summary section if it exists, otherwise add it
                summary_heading = self._find_section_heading(doc, "SUMMARY")
                if summary_heading:
                    self._update_summary_section(doc, tailored_data.summary)
                else:
                    # Add summary section after the first paragraph if it doesn't exist
                    if len(doc.paragraphs) > 1:
                        doc.paragraphs[1].insert_paragraph_before(tailored_data.summary, style='Body Text')
                    else:
                        doc.add_paragraph(tailored_data.summary, style='Body Text')
            
                # Define sections to update with their corresponding methods and data
                sections_to_update = [
                    ("EXPERIENCE", self._update_experience_section, tailored_data.experience),
                    ("PROJECTS", self._update_projects_section, tailored_data.projects),
                    ("SKILLS", self._update_skills_section, tailored_data.technical_skills),
                    ("EDUCATION", self._update_education_section, tailored_data.education),
                    ("RESEARCH PUBLICATIONS", self._update_research_publications, 
                     getattr(tailored_data, 'research_publications', None))
                ]
                
                # Update each section if the corresponding data exists
                for section_name, update_func, section_data in sections_to_update:
                    if section_data:  # Only update if we have data for this section
                        try:
                            logger.info(f"Updating {section_name} section...")
                            update_func(doc, section_data)
                        except Exception as e:
                            logger.warning(f"Failed to update {section_name} section: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error updating template: {str(e)}")
            raise
    
    def _build_resume_from_scratch(
        self, 
        tailored_data: TailoredResumeData
    ) -> Document:
        """Build complete resume from scratch when no template available."""
        doc = Document()
        
        # Add name and contact info
        if hasattr(self.profile, 'name') and self.profile.name:
            add_paragraph_with_style(doc, self.profile.name, 'Heading 1')
        
        # Add summary
        if tailored_data.summary:
            add_section(doc, "SUMMARY")
            add_paragraph_with_style(doc, tailored_data.summary)
        
        # Add experience
        if tailored_data.experience:
            add_section(doc, "EXPERIENCE")
            for exp in tailored_data.experience:
                self._add_experience_entry(doc, exp)
        
        # Add projects
        if tailored_data.projects:
            add_section(doc, "PROJECTS")
            for proj in tailored_data.projects:
                self._add_project_entry(doc, proj)
        
        # Add skills
        if tailored_data.technical_skills:
            add_section(doc, "SKILLS")
            for category, skills in tailored_data.technical_skills.items():
                add_paragraph_with_style(doc, f"{category}: {', '.join(skills)}")
        
        # Add education
        if tailored_data.education:
            add_section(doc, "EDUCATION")
            for edu in tailored_data.education:
                if isinstance(edu, dict):
                    add_paragraph_with_style(doc, f"{edu.get('degree', '')}, {edu.get('institution', '')} ({edu.get('year', '')})")
                else:
                    add_paragraph_with_style(doc, str(edu))
        
        # Add research publications if they exist
        if tailored_data.research_publications:
            add_section(doc, "RESEARCH & PUBLICATIONS")
            for pub in tailored_data.research_publications:
                add_paragraph_with_style(doc, f"• {pub}")
        
        return doc
    
    def _update_summary_section(self, doc: Document, summary: str) -> None:
        """Update the summary section in the template while preserving formatting."""
        if not summary:
            return
            
        # Find the summary section
        summary_para = self._find_section_heading(doc, "SUMMARY")
        if not summary_para:
            # If no summary section exists, add it after the first paragraph
            if len(doc.paragraphs) > 0:
                # Insert after the first paragraph (contact info)
                doc.paragraphs[0].insert_paragraph_before("SUMMARY", style='Heading 1')
                doc.paragraphs[1].insert_paragraph_before(summary, style='Body Text')
            else:
                doc.add_heading("SUMMARY", level=1)
                doc.add_paragraph(summary, style='Body Text')
            return
            
        # Clear existing content until next heading
        next_para = self._clear_until_next_heading(summary_para)
        
        # Add the new summary with preserved formatting
        if next_para:
            next_para.insert_paragraph_before(summary, style='Body Text')
        else:
            summary_para.insert_paragraph_before(summary, style='Body Text')
            
    def _update_experience_section(self, doc: Document, experience: List[Dict]) -> None:
        """Update the experience section in the template while preserving formatting."""
        if not experience:
            return
            
        exp_heading = self._find_section_heading(doc, "EXPERIENCE")
        if not exp_heading:
            # If no experience section exists, add it
            doc.add_heading("EXPERIENCE", level=1)
            for exp in experience:
                self._add_experience_entry(doc, exp)
            return
            
        # Clear existing content until next section
        next_para = self._clear_until_next_heading(exp_heading)
        
        # Add new experience entries
        for i, exp in enumerate(experience):
            # Add a blank line between entries, but not after the last one
            if i > 0:
                if next_para:
                    next_para.insert_paragraph_before('')
                else:
                    doc.add_paragraph('')
            
            # Add the experience entry
            self._add_experience_entry(doc, exp)
            
        # Ensure there's a blank line after the section
        if next_para and next_para.text.strip() != '':
            next_para.insert_paragraph_before('')
    
    def _add_experience_entry(self, doc: Document, exp: Dict) -> None:
        """Add a single experience entry to the document with proper formatting."""
        # Build job header with title, company, and duration
        job_header = []
        if 'title' in exp and exp['title']:
            job_header.append(exp['title'])
        if 'company' in exp and exp['company']:
            job_header.append(exp['company'])
        if 'location' in exp and exp['location']:
            job_header.append(exp['location'])
            
        # Add the job header with proper formatting
        if job_header:
            # Use a strong style for the job title/company line
            p = doc.add_paragraph(style='Normal')
            p.add_run(' • '.join(job_header)).bold = True
            
            # Add duration on the same line, right-aligned if available
            if 'duration' in exp and exp['duration']:
                from docx.enum.text import WD_ALIGN_PARAGRAPH
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.add_run('\t')  # Tab to push duration to the right
                p.add_run(exp['duration']).italic = True
        
        # Add bullet points with proper indentation
        bullets = exp.get('bullets', [])
        if bullets:
            for bullet in bullets:
                if bullet.strip():  # Skip empty bullet points
                    p = doc.add_paragraph(style='List Bullet')
                    p.paragraph_format.left_indent = 360000  # 0.25 inch in twips
                    p.paragraph_format.first_line_indent = -360000  # Hanging indent
                    p.add_run(bullet.strip())
    
    def _update_skills_section(self, doc: Document, skills: Dict[str, List[str]]) -> None:
        """Update the skills section in the template with improved formatting."""
        if not skills:
            return
            
        skills_heading = self._find_section_heading(doc, "SKILLS")
        if not skills_heading:
            # If no skills section exists, add it
            doc.add_heading("SKILLS", level=1)
            next_para = None
        else:
            # Clear existing content until next section
            next_para = self._clear_until_next_heading(skills_heading)
        
        # Add skills in a tabular format for better organization
        from docx.shared import Inches, Pt
        from docx.enum.table import WD_TABLE_ALIGNMENT
        
        # Create a table with 2 columns for skills
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid'  # Add borders for better visual separation
        table.autofit = False
        
        # Set column widths
        col_widths = [Inches(1.5), Inches(5.0)]  # First column for category, second for skills
        for i, width in enumerate(col_widths):
            table.columns[i].width = width
        
        # Add skills in a two-column format
        row_idx = 0
        for category, skill_list in skills.items():
            if not skill_list:
                continue
                
            # Add a new row for each category
            if row_idx > 0:
                row_cells = table.add_row().cells
            else:
                row_cells = table.rows[0].cells
                
            # Add category in the first column (bold)
            category_cell = row_cells[0]
            category_cell.paragraphs[0].add_run(category).bold = True
            
            # Add skills in the second column (comma-separated)
            skills_cell = row_cells[1]
            skills_cell.text = ', '.join(skill_list)
            
            # Adjust cell margins and alignment
            for cell in row_cells:
                cell.vertical_alignment = WD_TABLE_ALIGNMENT.CENTER
                for paragraph in cell.paragraphs:
                    paragraph_format = paragraph.paragraph_format
                    paragraph_format.space_after = Pt(0)
                    paragraph_format.space_before = Pt(0)
                    paragraph_format.line_spacing = 1.0
            
            row_idx += 1
        
        # Add a blank line after the table
        if next_para:
            next_para.insert_paragraph_before('')
        else:
            doc.add_paragraph('')
    
    def _update_education_section(self, doc: Document, education: List) -> None:
        """Update the education section in the template with improved formatting."""
        if not education:
            return
            
        edu_heading = self._find_section_heading(doc, "EDUCATION")
        if not edu_heading:
            # If no education section exists, add it
            doc.add_heading("EDUCATION", level=1)
            next_para = None
        else:
            # Clear existing content until next section
            next_para = self._clear_until_next_heading(edu_heading)
        
        # Add education entries with consistent formatting
        for i, edu in enumerate(education):
            if i > 0 and next_para:
                next_para.insert_paragraph_before('')
            
            # Create a table for each education entry to align degree and date
            from docx.shared import Inches, Pt
            from docx.enum.table import WD_TABLE_ALIGNMENT
            
            # Create a table with 2 columns (degree and date)
            table = doc.add_table(rows=1, cols=2)
            table.style = 'Table Normal'  # No borders for a clean look
            table.autofit = False
            
            # Set column widths
            table.columns[0].width = Inches(5.0)  # Degree and school
            table.columns[1].width = Inches(1.5)  # Date (right-aligned)
            
            # Add degree and school
            degree_cell = table.cell(0, 0)
            p = degree_cell.paragraphs[0]
            
            # Add degree in bold
            if 'degree' in edu and edu['degree']:
                p.add_run(edu['degree']).bold = True
                
            # Add school name
            if 'school' in edu and edu['school']:
                if p.text:  # Add a space if there's already text
                    p.add_run(', ')
                p.add_run(edu['school'])
                
            # Add location if available
            if 'location' in edu and edu['location']:
                if p.text:  # Add a space if there's already text
                    p.add_run(' | ')
                p.add_run(edu['location']).italic = True
            
            # Add date (right-aligned)
            if 'date' in edu and edu['date']:
                date_cell = table.cell(0, 1)
                date_cell.paragraphs[0].alignment = WD_TABLE_ALIGNMENT.RIGHT
                date_cell.paragraphs[0].add_run(edu['date']).italic = True
            
            # Add any additional details (GPA, honors, etc.)
            if 'details' in edu and edu['details']:
                details = edu['details']
                if isinstance(details, str):
                    doc.add_paragraph(details, style='Body Text')
                elif isinstance(details, list):
                    for detail in details:
                        if detail.strip():
                            doc.add_paragraph(detail, style='Body Text')
        
        # Add a blank line after the section
        if next_para and next_para.text.strip() != '':
            next_para.insert_paragraph_before('')
    
    def _update_research_publications(self, doc: Document, publications: List[str]) -> None:
        """Update the research publications section in the template with improved formatting."""
        if not publications:
            return
            
        # Try different possible section headings
        section_names = ["RESEARCH & PUBLICATIONS", "PUBLICATIONS", "RESEARCH"]
        pub_heading = None
        
        for name in section_names:
            pub_heading = self._find_section_heading(doc, name)
            if pub_heading:
                break
        
        if not pub_heading:
            # If no publications section exists, add it
            doc.add_heading("RESEARCH & PUBLICATIONS", level=1)
            next_para = None
        else:
            # Clear existing content until next section
            next_para = self._clear_until_next_heading(pub_heading)
        
        # Add publications with proper formatting
        for i, pub in enumerate(publications):
            if not pub.strip():
                continue
                
            # Add a blank line between publications, but not before the first one
            if i > 0 and next_para:
                next_para.insert_paragraph_before('')
            
            # Create a paragraph for the publication
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.left_indent = 360000  # 0.25 inch in twips
            p.paragraph_format.first_line_indent = -360000  # Hanging indent
            
            # Add publication text with proper formatting
            p.add_run(pub.strip())
        
        # Add a blank line after the section
        if next_para and next_para.text.strip() != '':
            next_para.insert_paragraph_before('')
    
    def _find_section_heading(self, doc: Document, section_name: str):
        """Find a section heading in the document."""
        section_name = section_name.upper()
        for para in doc.paragraphs:
            # Check if paragraph text matches the section name (case-insensitive)
            # Also check if it's a heading style
            if (para.text.upper() == section_name or 
                (hasattr(para, 'style') and 
                 para.style.name.startswith('Heading') and 
                 para.text.upper() == section_name)):
                return para
        return None
    
    def _clear_until_next_heading(self, para):
        """Clear content until the next heading or end of document."""
        if not hasattr(para, '_element') or not hasattr(para._element, 'getparent'):
            return None
            
        parent = para._element.getparent()
        if parent is None:
            return None
            
        # Get all paragraphs in the document
        all_paras = [p for p in parent.iterchildren('w:p')]
        
        try:
            # Find the index of the current paragraph
            current_idx = all_paras.index(para._element)
            
            # Iterate through following paragraphs
            for i in range(current_idx + 1, len(all_paras)):
                next_para = all_paras[i]
                
                # Get the paragraph style
                style_elem = next_para.find('.//w:pStyle', namespaces=next_para.nsmap)
                if style_elem is not None:
                    style_name = style_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if style_name and style_name.startswith('Heading'):
                        # Found the next heading, return its paragraph element
                        from docx.oxml.text.paragraph import CT_P
                        return next_para
                
                # Remove the paragraph
                parent.remove(next_para)
                
        except (ValueError, AttributeError) as e:
            logger.warning(f"Error clearing until next heading: {str(e)}")
            
        return None
