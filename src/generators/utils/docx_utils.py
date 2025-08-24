import os
import logging
from typing import Optional, Dict, List, Tuple, Union
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Pt, Inches
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

logger = logging.getLogger("tailor")

def get_or_create_style(doc: Document, style_name: str, style_type=WD_STYLE_TYPE.PARAGRAPH):
    """Get existing style or create it if it doesn't exist, with fallback to Normal."""
    try:
        return doc.styles[style_name]
    except KeyError:
        return _create_style(doc, style_name, style_type)

def _create_style(doc: Document, style_name: str, style_type):
    """Create a new style with the given name and type."""
    try:
        style = doc.styles.add_style(style_name, style_type)
        style.font.name = 'Calibri'
        
        if style_name == 'Heading 1':
            style.font.size = Pt(16)
            style.font.bold = True
        elif style_name == 'Heading 2':
            style.font.size = Pt(13)
            style.font.bold = True
        elif style_name == 'Heading 3':
            style.font.size = Pt(12)
            style.font.bold = True
        elif style_name == 'List Bullet':
            style.font.size = Pt(11)
        else:
            style.font.size = Pt(11)
            
        return style
    except Exception as e:
        logger.warning(f"Could not create style '{style_name}': {e}")
        return doc.styles.get('Normal', None)

def add_paragraph_with_style(doc: Document, text: str, style_name: str = None):
    """Add paragraph with style, handling missing styles gracefully."""
    try:
        if style_name:
            style = get_or_create_style(doc, style_name)
            para = doc.add_paragraph(text, style=style) if style else doc.add_paragraph(text)
        else:
            para = doc.add_paragraph(text)
        return para
    except Exception as e:
        logger.error(f"Error adding paragraph with style '{style_name}': {e}")
        return doc.add_paragraph(text)

def add_section(doc: Document, title: str, level: int = 2):
    """
    Add a new section to the document with proper spacing.
    
    Args:
        doc: The document to add the section to
        title: The section title text
        level: The heading level (1-3)
    """
    try:
        if doc.paragraphs and doc.paragraphs[-1].text.strip() != '':
            doc.add_paragraph('')
        
        heading = doc.add_heading(title, level=min(max(1, level), 3))
        doc.add_paragraph('')
        return heading
    except Exception as e:
        logger.error(f"Error adding section '{title}': {e}")
        doc.add_paragraph(title, style='Heading 2')
        doc.add_paragraph('')

def add_bullet_points(doc: Document, items: List[str], style_name: str = 'List Bullet'):
    """Add bullet points to the document."""
    for item in items:
        para = add_paragraph_with_style(doc, item, style_name)
        _set_list_style(para)

def _set_list_style(paragraph):
    """Set the list style for a paragraph."""
    p = paragraph._p
    pPr = p.get_or_add_pPr()
    numPr = OxmlElement('w:numPr')
    
    ilvl = OxmlElement('w:ilvl')
    ilvl.set(qn('w:val'), '0')
    numId = OxmlElement('w:numId')
    numId.set(qn('w:val'), '1')
    
    numPr.append(ilvl)
    numPr.append(numId)
    pPr.append(numPr)
