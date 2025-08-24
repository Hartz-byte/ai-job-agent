import os
import logging
from datetime import datetime
from pathlib import Path
from docx import Document

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import after logging is configured
from src.parsers.resume_parser import parse_resume
from src.generators.services.resume_tailor import ResumeTailor
from src.models.models import TailoredResumeData

# Create output directory if it doesn't exist
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

def create_test_job():
    """Create a test job with sample requirements."""
    class TestJob:
        def __init__(self):
            self.title = "Senior Software Engineer"
            self.company = "Tech Innovations Inc."
            self.location = "San Francisco, CA (Hybrid)"
            self.url = "https://example.com/job/senior-software-engineer-123"
            self.description = """
            We are looking for an experienced Senior Software Engineer to join our team.
            
            Key Responsibilities:
            - Design and develop scalable web applications using Python and modern frameworks
            - Lead technical architecture decisions and mentor junior developers
            - Implement best practices for code quality, testing, and deployment
            - Collaborate with cross-functional teams to deliver high-quality software
            
            Requirements:
            - 5+ years of professional software development experience
            - Strong expertise in Python and web frameworks (Django, FastAPI, or Flask)
            - Experience with cloud platforms (AWS, GCP, or Azure)
            - Knowledge of containerization and orchestration (Docker, Kubernetes)
            - Experience with databases (PostgreSQL, MongoDB)
            - Strong problem-solving and communication skills
            
            Nice to Have:
            - Experience with machine learning and data pipelines
            - Knowledge of frontend technologies (React, TypeScript)
            - Experience with CI/CD pipelines
            - Open source contributions
            """
    return TestJob()

def generate_test_resume():
    """Generate a test resume document with sample content."""
    doc = Document()
    
    # Add header with name and contact info
    doc.add_heading("John Doe", level=1)
    doc.add_paragraph("john.doe@example.com | (123) 456-7890 | San Francisco, CA | linkedin.com/in/johndoe")
    
    # Add summary section
    doc.add_heading("SUMMARY", level=2)
    doc.add_paragraph("Experienced Software Engineer with 7+ years of experience in building scalable web applications using Python and modern frameworks. Proven track record of leading development teams and delivering high-quality software solutions.")
    
    # Add experience section
    doc.add_heading("EXPERIENCE", level=2)
    
    # Experience 1
    exp1 = doc.add_paragraph()
    exp1.add_run("Senior Software Engineer").bold = True
    exp1.add_run(" | Tech Solutions Inc. | San Francisco, CA | ")
    exp1.add_run("Jan 2020 - Present").italic = True
    doc.add_paragraph("Led a team of 5 developers in building a scalable microservices architecture.")
    
    # Experience 2
    exp2 = doc.add_paragraph()
    exp2.add_run("Software Engineer").bold = True
    exp2.add_run(" | Digital Innovations | San Jose, CA | ")
    exp2.add_run("Jun 2017 - Dec 2019").italic = True
    doc.add_paragraph("Developed and maintained RESTful APIs using Django and Flask.")
    
    # Add skills section
    doc.add_heading("SKILLS", level=2)
    skills = doc.add_paragraph()
    skills.add_run("Programming Languages: ").bold = True
    skills.add_run("Python, JavaScript, SQL, Java")
    
    # Add education section
    doc.add_heading("EDUCATION", level=2)
    edu = doc.add_paragraph()
    edu.add_run("MS in Computer Science").bold = True
    edu.add_run(" | Stanford University | ")
    edu.add_run("2015 - 2017").italic = True
    
    # Save the test resume
    test_resume_path = OUTPUT_DIR / "test_resume.docx"
    doc.save(test_resume_path)
    return test_resume_path

def test_resume_tailoring():
    """Test the resume tailoring functionality."""
    try:
        logger.info("Starting resume tailoring test...")
        
        # Generate a test resume if it doesn't exist
        test_resume_path = OUTPUT_DIR / "test_resume.docx"
        if not test_resume_path.exists():
            logger.info("Generating test resume...")
            test_resume_path = generate_test_resume()
        
        # Parse the test resume
        logger.info("Parsing test resume...")
        profile = parse_resume(str(test_resume_path))
        
        # Create a test job
        test_job = create_test_job()
        
        # Initialize the resume tailor
        logger.info("Initializing ResumeTailor...")
        tailor = ResumeTailor(profile, test_job)
        
        # Generate tailored content
        logger.info("Generating tailored content...")
        tailored_data = tailor.generate_tailored_content()
        
        # Print tailored content
        logger.info("\n=== TAILORED SUMMARY ===")
        print(tailored_data.summary)
        
        logger.info("\n=== TAILORED SKILLS ===")
        for category, skills in tailored_data.technical_skills.items():
            print(f"\n{category}:")
            for skill in skills:
                print(f"- {skill}")
        
        # Generate a tailored resume
        logger.info("\nGenerating tailored resume...")
        output_path = OUTPUT_DIR / f"tailored_resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        tailor.create_tailored_resume(tailored_data, str(output_path))
        
        logger.info(f"\n✅ Tailored resume generated successfully: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during resume tailoring test: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    test_resume_tailoring()
