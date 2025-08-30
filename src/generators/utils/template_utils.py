import os
import logging
from typing import Optional, Dict, List
from docx import Document

logger = logging.getLogger("tailor")

def get_template_path(template_type: str = 'resume') -> Optional[str]:
    """Get the path to a template file.
    
    Args:
        template_type: Type of template to get ('resume' or 'cover_letter')
    """
    # Define template filenames
    template_files = {
        'resume': 'resume.docx',
        'cover_letter': 'cover_letter_base.docx',
    }
    
    filename = template_files.get(template_type, 'resume.docx')
    
    # Check for custom template in data directory
    custom_template = os.path.join('data', filename)
    if os.path.exists(custom_template):
        return os.path.abspath(custom_template)

    # Try to find the default template in the package
    try:
        import docx
        package_dir = os.path.dirname(docx.__file__)
        default_template = os.path.join(package_dir, 'templates', 'default.docx')
        if os.path.exists(default_template):
            return default_template
    except Exception as e:
        logger.warning(f"Error finding default template: {e}")

    return None

def create_document(template_path: Optional[str] = None) -> Document:
    """Create a new document, optionally based on a template."""
    if template_path and os.path.exists(template_path):
        logger.info(f"Loading template from: {template_path}")
        return Document(template_path)
    
    logger.warning("No template found, creating new document")
    return Document()

def save_document(doc: Document, output_path: str) -> str:
    """Save document to the specified path with proper error handling."""
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True, mode=0o755)
        
        # Save to temp file first
        temp_path = f"{output_path}.tmp"
        doc.save(temp_path)
        
        # Then move to final location (atomic operation)
        import shutil
        shutil.move(temp_path, output_path)
        os.chmod(output_path, 0o644)  # Set appropriate permissions
        
        logger.info(f"Successfully saved document to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error saving document to {output_path}: {e}")
        raise
    finally:
        # Clean up temp file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up temp file: {cleanup_error}")

def format_skills_for_template(skills_dict: Dict[str, List[str]]) -> str:
    """Format skills dictionary for template replacement."""
    if not skills_dict:
        return ""
        
    formatted = []
    for category, skills in skills_dict.items():
        if skills:
            formatted.append(f"{category}: {', '.join(skills)}")
    
    return "\n".join(formatted)
